#Kostaldea ala mendia? (Asier) Zein mota nagusitzen da bakoitzean? Mapa: kostaldea / mendiak / biak. Grafikoa: zutabe pilatuak.
import json
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client["turismoa"]

with open("alojamientos.json", encoding="utf-8") as f:
    ostatuak = json.load(f)
db.ostatuak.drop()
db.ostatuak.insert_many(ostatuak)
print(db.ostatuak.count_documents({}))

with open("viviendas.json", encoding="utf-8") as f:
    datuak = json.load(f)
db.etxebizitzak.drop()
db.etxebizitzak.insert_many(datuak)
print(db.etxebizitzak.count_documents({}))

#############################################
# 1. ARIKETA: Kostaldea ala mendia?
#############################################
garbiketa = [
    {"$project": {
        "_id": 0,
        "mota": "$lodgingType",
        "lon": "$lonwgs84",
        "lat": "$latwgs84",
        "kostaldea": {"$in": ["Costa Vasca", {"$split": ["$marks", ","]}]},
        "mendia": {"$in": ["Montes y Valles vascos", {"$split": ["$marks", ","]}]},
    }},
    {"$project": {
        "mota": 1,
        "lon": 1,
        "lat": 1,
        "eremua": {"$switch": {
            "branches": [
                {"case": {"$and": ["$kostaldea", "$mendia"]}, "then": "biak"},
                {"case": "$kostaldea", "then": "kostaldea"},
                {"case": "$mendia", "then": "mendiak"},
            ],
            "default": None,
        }},
    }},
    {"$match": {"eremua": {"$ne": None}}},
    {"$out": "garbiak"},
]
db.ostatuak.aggregate(garbiketa)
print(db.garbiak.find_one())

def erakutsi(pipeline):
    for d in db.garbiak.aggregate(pipeline):
        print(d)

print(" \n eremu bakoitzeko ostatu kopurua")
erakutsi([
    {"$group": {"_id": "$eremua", "kopurua": {"$sum": 1}}},
    {"$sort": {"kopurua": -1}},
])

print(" \n mota nagusia eremu bakoitzean")
erakutsi([
    {"$group": {"_id": {"eremua": "$eremua", "mota": "$mota"}, "kopurua": {"$sum": 1}}},
    {"$sort": {"kopurua": -1}},
    {"$group": {"_id": "$_id.eremua", "mota": {"$first": "$_id.mota"}, "kopurua": {"$first": "$kopurua"}}},
])

motak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"eremua": "$eremua", "mota": "$mota"}, "kopurua": {"$sum": 1}}},
]):
    motak.setdefault(d["_id"]["eremua"], {})[d["_id"]["mota"]] = d["kopurua"]

mota_zerrenda = sorted({m for e in motak.values() for m in e})
with open("eremuak_motak.csv", "w", encoding="utf-8-sig") as f:
    f.write("eremua;" + ";".join(mota_zerrenda) + "\n")
    for eremua in ["kostaldea", "mendiak", "biak"]:
        f.write(eremua + ";" + ";".join(str(motak[eremua].get(m, 0)) for m in mota_zerrenda) + "\n")

with open("mapa_eremuak2.csv", "w", encoding="utf-8-sig") as f:
    f.write("lon;lat;eremua\n")
    for d in db.garbiak.find():
        lon = d["lon"].replace(".", ",")
        lat = d["lat"].replace(".", ",")
        f.write(f"{lon};{lat};{d['eremua']}\n")

#############################################
# 2. ARIKETA: Turismo masiboa (ostatuak vs etxebizitzak)
#############################################
EREMUAK = ["kostaldea", "mendiak", "biak"]


def izena(eremua):
    return {"$toLower": {"$replaceAll": {"input": eremua, "find": " / ", "replacement": "/"}}}

# 1. Udalerri bakoitzaren eremua

eremuak = [
    {"$project": {
        "_id": 0,
        "udalerria": izena("$municipality"),
        "kostaldea": {"$in": ["Costa Vasca", {"$split": ["$marks", ","]}]},
        "mendia": {"$in": ["Montes y Valles vascos", {"$split": ["$marks", ","]}]},
    }},
    {"$group": {"_id": "$udalerria", "kostaldea": {"$max": "$kostaldea"}, "mendia": {"$max": "$mendia"}}},
    {"$project": {
        "_id": 0,
        "udalerria": "$_id",
        "eremua": {"$switch": {
            "branches": [
                {"case": {"$and": ["$kostaldea", "$mendia"]}, "then": "biak"},
                {"case": "$kostaldea", "then": "kostaldea"},
                {"case": "$mendia", "then": "mendiak"},
            ],
            "default": None,
        }},
    }},
    {"$match": {"eremua": {"$ne": None}}},
    {"$out": "eremuak"},
]
db.ostatuak.aggregate(eremuak)
print(db.eremuak.count_documents({}))

# 2. Garbiketa: bi kolekzioak eremuarekin lotu. Eremurik gabeko udalerriak (unwind-ek kentzen ditu) kanpoan geratzen dira.
ostatu_garbiketa = [
    {"$project": {
        "_id": 0,
        "udalerria": izena("$municipality"),
        "mota": "$lodgingType",
        "plazak": {"$toInt": "$capacity"},
    }},
    {"$lookup": {"from": "eremuak", "localField": "udalerria", "foreignField": "udalerria", "as": "e"}},
    {"$unwind": "$e"},
    {"$project": {"udalerria": 1, "mota": 1, "plazak": 1, "eremua": "$e.eremua"}},
    {"$out": "ostatu_garbiak"},
]
db.ostatuak.aggregate(ostatu_garbiketa)

etxebizitza_garbiketa = [
    {"$project": {
        "_id": 0,
        "udalerria": izena("$Municipio"),
        "plazak": {"$toInt": "$Capacidad"},
        "urtea": {"$toInt": {"$substr": ["$FechainscripcionREATE", 6, 4]}},
    }},
    {"$lookup": {"from": "eremuak", "localField": "udalerria", "foreignField": "udalerria", "as": "e"}},
    {"$unwind": "$e"},
    {"$project": {"udalerria": 1, "plazak": 1, "urtea": 1, "eremua": "$e.eremua"}},
    {"$out": "etxebizitza_garbiak"},
]
db.etxebizitzak.aggregate(etxebizitza_garbiketa)

print(db.ostatu_garbiak.count_documents({}), "ostatu eremu batean sailkatuta")
print(db.etxebizitza_garbiak.count_documents({}), "etxebizitza eremu batean sailkatuta")
print(db.etxebizitzak.count_documents({}) - db.etxebizitza_garbiak.count_documents({}), "etxebizitza sailkatu gabe (udalerriak ez du ostaturik)")


def csv_idatzi(fitxategia, goiburuak, lerroak):
    with open(fitxategia, "w", encoding="utf-8-sig") as f:
        f.write(";".join(goiburuak) + "\n")
        for lerroa in lerroak:
            f.write(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x) for x in lerroa) + "\n")


# 1. Etxebizitzak ala hotelak? Plazak eremu bakoitzean eta etxebizitzen %.  Grafikoa: zutabe pilatuak
etx_plazak = {d["_id"]: d["plazak"] for d in db.etxebizitza_garbiak.aggregate([
    {"$group": {"_id": "$eremua", "plazak": {"$sum": "$plazak"}}},
])}
ost_plazak = {d["_id"]: d["plazak"] for d in db.ostatu_garbiak.aggregate([
    {"$group": {"_id": "$eremua", "plazak": {"$sum": "$plazak"}}},
])}
lerroak = []
print(" \n 1 plazak eremuka")
for e in EREMUAK:
    guztira = etx_plazak.get(e, 0) + ost_plazak.get(e, 0)
    ehunekoa = round(100 * etx_plazak.get(e, 0) / guztira, 1)
    print(e, etx_plazak.get(e, 0), ost_plazak.get(e, 0), ehunekoa)
    lerroak.append([e, etx_plazak.get(e, 0), ost_plazak.get(e, 0), ehunekoa])
csv_idatzi("plazak_eremuak.csv", ["eremua", "etxebizitzetako plazak", "establezimenduetako plazak", "etxebizitzen %"], lerroak)

# 2. Bilakaera: etxebizitza berriak urteka eremu bakoitzean.  Grafikoa: hiru lerro
urteka = {}
for d in db.etxebizitza_garbiak.aggregate([
    {"$group": {"_id": {"urtea": "$urtea", "eremua": "$eremua"}, "kopurua": {"$sum": 1}}},
]):
    urteka.setdefault(d["_id"]["urtea"], {})[d["_id"]["eremua"]] = d["kopurua"]
print(" \n 2 etxebizitza berriak urteka")
lerroak = []
for urtea in sorted(urteka):
    lerroak.append([urtea] + [urteka[urtea].get(e, 0) for e in EREMUAK])
    print(lerroak[-1])
csv_idatzi("etxebizitzak_urteka.csv", ["urtea"] + EREMUAK, lerroak)

# 3. Kostaldea eta barnealdea: ostatu motak eremu bakoitzean.  Grafikoa: zutabe pilatuak
motak = {}
for d in db.ostatu_garbiak.aggregate([
    {"$group": {"_id": {"eremua": "$eremua", "mota": "$mota"}, "kopurua": {"$sum": 1}}},
]):
    motak.setdefault(d["_id"]["eremua"], {})[d["_id"]["mota"]] = d["kopurua"]
mota_zerrenda = sorted({m for e in motak.values() for m in e})
print(" \n 3 ostatu motak eremuka")
lerroak = []
for e in EREMUAK:
    lerroak.append([e] + [motak[e].get(m, 0) for m in mota_zerrenda])
    print(lerroak[-1])
csv_idatzi("motak_eremuak.csv", ["eremua"] + mota_zerrenda, lerroak)