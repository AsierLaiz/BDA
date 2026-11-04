# EBAZPENA 3 / SOLUCIÓN: museoak + herriak (2 JSON -> MongoDB -> CSV)
# Necesita: museoak.json y herriak.json en la misma carpeta y MongoDB encendido.
import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["proba3"]


# ------------------------------------------------------------
# 0. Funciones pequeñas
# ------------------------------------------------------------
def garbitu(izena):
    """Minúsculas y sin espacios sobrantes, para que 'BILBO' y 'Bilbo' coincidan."""
    return (izena or "").lower().strip()


def csv_idatzi(fitxategia, lerroak):
    """; como separador y coma decimal, para que Excel en español lo abra bien."""
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        for lerroa in lerroak:
            f.write(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x)
                             for x in lerroa) + "\n")


# ------------------------------------------------------------
# 1. Cargar los dos JSON
# ------------------------------------------------------------
with open("museoak.json", encoding="utf-8") as f:
    db.museoak.drop()
    db.museoak.insert_many(json.load(f))

with open("herriak.json", encoding="utf-8") as f:
    db.herriak.drop()
    db.herriak.insert_many(json.load(f))

print(db.museoak.count_documents({}), "museo,", db.herriak.count_documents({}), "herri")
print(db.museoak.find_one())      # fíjate: "bisitak" es un diccionario DENTRO del documento


# ------------------------------------------------------------
# 2. Diccionario de municipios: nombre -> (provincia, zona)
#    (así sabemos dónde está cada museo, porque museoak no trae provincia)
# ------------------------------------------------------------
herriak = {}
for h in db.herriak.find():
    zona = "kostaldea" if h["kostaldea"] == "Bai" else "barnealdea"
    herriak[garbitu(h["udalerria"])] = (h["probintzia"], zona)

# añadimos provincia y zona a cada museo (None si su municipio no está en herriak)
for m in list(db.museoak.find()):
    probintzia, zona = herriak.get(garbitu(m["udalerria"]), (None, None))
    db.museoak.update_one({"_id": m["_id"]}, {"$set": {"probintzia": probintzia, "zona": zona}})

print(db.museoak.count_documents({"zona": None}), "museo sin zona (se descartan)")


# ------------------------------------------------------------
# 3. Las 4 tablas
# ------------------------------------------------------------
EREMUAK = ["kostaldea", "barnealdea"]

# A) Visitantes 2023 y 2024 en cada zona (columnas agrupadas)
bisitak = {}
for d in db.museoak.aggregate([
    {"$match": {"zona": {"$ne": None}}},
    {"$group": {"_id": "$zona", "b23": {"$sum": "$bisitak.2023"}, "b24": {"$sum": "$bisitak.2024"}}},
]):
    bisitak[d["_id"]] = d

A = [["eremua", "2023", "2024"]]
for e in EREMUAK:
    A.append([e, bisitak[e]["b23"], bisitak[e]["b24"]])

# B) Visitantes 2024 por habitante en cada provincia (usa LAS DOS colecciones)
bisitariak = {d["_id"]: d["b24"] for d in db.museoak.aggregate([
    {"$match": {"probintzia": {"$ne": None}}},
    {"$group": {"_id": "$probintzia", "b24": {"$sum": "$bisitak.2024"}}},
])}
biztanleak = {d["_id"]: d["biz"] for d in db.herriak.aggregate([
    {"$group": {"_id": "$probintzia", "biz": {"$sum": "$biztanleak"}}},
])}

B = [["probintzia", "bisitak 2024", "biztanleak", "bisitak biztanleko"]]
for p in ["Araba", "Bizkaia", "Gipuzkoa"]:
    B.append([p, bisitariak.get(p, 0), biztanleak[p], round(bisitariak.get(p, 0) / biztanleak[p], 2)])

# C) Evolución 2022-2024: visitantes por tipo de museo (3 líneas)
motak = {}
for d in db.museoak.aggregate([
    {"$group": {"_id": "$mota", "b22": {"$sum": "$bisitak.2022"},
                "b23": {"$sum": "$bisitak.2023"}, "b24": {"$sum": "$bisitak.2024"}}},
    {"$sort": {"_id": 1}},
]):
    motak[d["_id"]] = d

zerrenda = list(motak)                       # ['Artea', 'Historia', 'Zientzia']
C = [["urtea"] + zerrenda]
for urtea, gakoa in [("2022", "b22"), ("2023", "b23"), ("2024", "b24")]:
    C.append([urtea] + [motak[m][gakoa] for m in zerrenda])

# D) Los 5 museos con más visitantes en 2024 (solo los que tienen zona)
D = [["izena", "udalerria", "eremua", "bisitak 2024"]]
for m in db.museoak.aggregate([
    {"$match": {"zona": {"$ne": None}}},
    {"$sort": {"bisitak.2024": -1}},
    {"$limit": 5},
]):
    D.append([m["izena"], m["udalerria"], m["zona"], m["bisitak"]["2024"]])


# ------------------------------------------------------------
# 4. Guardar cada tabla en un CSV
# ------------------------------------------------------------
csv_idatzi("taula_A_eremuak.csv", A)
csv_idatzi("taula_B_probintziak.csv", B)
csv_idatzi("taula_C_urteak.csv", C)
csv_idatzi("taula_D_top5.csv", D)
print("Listo: 4 CSV creados")
