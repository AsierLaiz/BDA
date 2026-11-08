# EBAZPENA 6: KIROL-ZENTROAK (centros deportivos; datos ANIDADOS y una LISTA)
# Necesita kirol_zentroak.json en la misma carpeta y MongoDB encendido.
import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["examen6"]


def csv_idatzi(fitxategia, lerroak):
    """; como separador y coma decimal, para que Excel en español lo abra bien."""
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        for lerroa in lerroak:
            f.write(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x)
                             for x in lerroa) + "\n")


# ============================================================
# 1. IMPORTAR (1 punto)
# ============================================================
with open("kirol_zentroak.json", encoding="utf-8") as f:
    db.gordinak.drop()
    db.gordinak.insert_many(json.load(f))

print(db.gordinak.count_documents({}), "dokumentu")
print(db.gordinak.find_one())     # fíjate: "kokapena" es un diccionario y "zerbitzuak" una lista


# ============================================================
# 2. LIMPIAR (3 puntos)
# ============================================================
garbiak = []
ikusiak = set()                    # duplicado = mismo (izena, udalerria)

for d in db.gordinak.find():
    izena = d["izena"].strip()
    k = d["kokapena"]                                  # el diccionario anidado
    udalerria = k["udalerria"].strip().title()
    gakoa = (izena, udalerria)

    if gakoa in ikusiak:                               # duplicado -> fuera
        continue
    if not d.get("kuota"):                             # sin cuota -> fuera
        continue
    ikusiak.add(gakoa)

    zerbitzuak = [z.strip().lower() for z in d["zerbitzuak"]]     # " Sauna" -> "sauna"
    garbiak.append({
        "izena": izena,
        "udalerria": udalerria,
        "probintzia": k["probintzia"],                 # "subimos" los datos anidados al primer nivel
        "lat": float(k["lat"]),
        "lon": float(k["lon"]),
        "zerbitzuak": zerbitzuak,
        "zerbitzu_kopurua": len(zerbitzuak),
        "kuota": float(d["kuota"].replace("€/hilabete", "").replace(",", ".")),   # "35,90 €/hilabete" -> 35.9
        "bazkideak": int(str(d["bazkideak"]).replace(".", "")),                    # "1.250" -> 1250
    })

db.garbiak.drop()
db.garbiak.insert_many(garbiak)
print(len(garbiak), "garbi,", db.gordinak.count_documents({}) - len(garbiak), "deskartatuta")


# ============================================================
# 3. AZTERTU (3 puntos)
# ============================================================
# A) Cuántos centros ofrecen cada servicio ($unwind abre la lista)
A = [["zerbitzua", "zentroak"]]
for d in db.garbiak.aggregate([
    {"$unwind": "$zerbitzuak"},
    {"$group": {"_id": "$zerbitzuak", "kopurua": {"$sum": 1}}},
    {"$sort": {"kopurua": -1}},
]):
    A.append([d["_id"], d["kopurua"]])

# B) Cuota media por provincia
B = [["probintzia", "batez besteko kuota (€)"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$probintzia", "media": {"$avg": "$kuota"}}},
    {"$sort": {"media": -1}},
]):
    B.append([d["_id"], round(d["media"], 2)])

# C) Centros con y sin piscina en cada provincia
# {"zerbitzuak": "igerilekua"} en un $match = "la lista CONTIENE igerilekua"
guztira = {d["_id"]: d["kopurua"] for d in db.garbiak.aggregate([
    {"$group": {"_id": "$probintzia", "kopurua": {"$sum": 1}}},
])}
igerilekuarekin = {d["_id"]: d["kopurua"] for d in db.garbiak.aggregate([
    {"$match": {"zerbitzuak": "igerilekua"}},
    {"$group": {"_id": "$probintzia", "kopurua": {"$sum": 1}}},
])}

C = [["probintzia", "igerilekuarekin", "igerilekurik gabe"]]
for p in ["Araba", "Bizkaia", "Gipuzkoa"]:
    bai = igerilekuarekin.get(p, 0)
    C.append([p, bai, guztira.get(p, 0) - bai])

# D) Los 10 centros con más socios
D = [["izena", "udalerria", "bazkideak"]]
for d in db.garbiak.aggregate([
    {"$sort": {"bazkideak": -1}},
    {"$limit": 10},
]):
    D.append([d["izena"], d["udalerria"], d["bazkideak"]])

# E) Número de servicios vs cuota (¿cuantos más servicios, más cara?)
E = [["zerbitzu kopurua", "kuota (€)"]]
for d in db.garbiak.find():
    E.append([d["zerbitzu_kopurua"], d["kuota"]])


# ============================================================
# 4. AURKEZTU (3 puntos)
# ============================================================
csv_idatzi("taula_A_zerbitzuak.csv", A)     # barras o columnas
csv_idatzi("taula_B_kuota.csv", B)          # columnas
csv_idatzi("taula_C_igerilekua.csv", C)     # columnas apiladas
csv_idatzi("taula_D_top10.csv", D)          # barras
csv_idatzi("taula_E_dispertsioa.csv", E)    # dispersión
print("Listo: 5 CSV creados")
