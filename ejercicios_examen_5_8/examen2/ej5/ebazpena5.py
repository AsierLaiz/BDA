# EBAZPENA 5: EKITALDIAK (eventos, fiestas y ferias)
# Necesita ekitaldiak.json en la misma carpeta y MongoDB encendido.
import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["examen5"]


def csv_idatzi(fitxategia, lerroak):
    """; como separador y coma decimal, para que Excel en español lo abra bien."""
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        for lerroa in lerroak:
            f.write(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x)
                             for x in lerroa) + "\n")


def zenbakia(x):
    """Pasa a entero. Si no se puede ('n/a') devuelve None."""
    try:
        return int(x)
    except (ValueError, TypeError):
        return None


# ============================================================
# 1. IMPORTAR (1 punto)
# ============================================================
with open("ekitaldiak.json", encoding="utf-8") as f:
    db.gordinak.drop()
    db.gordinak.insert_many(json.load(f))

print(db.gordinak.count_documents({}), "dokumentu")
print(db.gordinak.find_one())


# ============================================================
# 2. LIMPIAR (3 puntos)
# ============================================================
garbiak = []
for d in db.gordinak.find():
    # "12/07/2024 - 15/07/2024" (varios días)  o  "12/07/2024" (un día)
    datak = d["datak"].split(" - ")
    hasiera = datak[0]
    amaiera = datak[-1]                         # si solo hay un día, el último es el mismo
    if hasiera[6:10] != "2024":                 # otros años -> se descartan
        continue

    prezioa_testua = d["prezioa"].strip().lower()
    if prezioa_testua == "zehazteko":           # precio sin determinar -> se descarta
        continue
    if prezioa_testua == "doan":                # "Doan" = gratis
        prezioa = 0.0
    else:
        prezioa = float(prezioa_testua.replace("€", "").replace(",", ".").strip())

    aforoa = zenbakia(str(d["aforoa"]).replace(".", ""))      # "1.500" -> 1500 ; 800 -> 800 ; "n/a" -> None
    if aforoa is None:
        continue

    garbiak.append({
        "izena": d["izena"],
        "herria": d["herria"],
        "probintzia": d["probintzia"],
        "kategoria": d["kategoria"].strip().capitalize(),             # "MUSIKA" -> "Musika"
        "hilabetea": int(hasiera[3:5]),                               # número de mes
        "egunak": int(amaiera[:2]) - int(hasiera[:2]) + 1,            # duración en días (mismo mes)
        "prezioa": prezioa,
        "doan": prezioa == 0,
        "aforoa": aforoa,
    })

db.garbiak.drop()
db.garbiak.insert_many(garbiak)
print(len(garbiak), "garbi,", db.gordinak.count_documents({}) - len(garbiak), "deskartatuta")


# ============================================================
# 3. AZTERTU (3 puntos)
# ============================================================
# A) Eventos de cada mes (los 12 meses; 0 si no hay)
hilabeteak = {d["_id"]: d["kopurua"] for d in db.garbiak.aggregate([
    {"$group": {"_id": "$hilabetea", "kopurua": {"$sum": 1}}},
])}
A = [["hilabetea", "ekitaldiak"]]
for h in range(1, 13):
    A.append([h, hilabeteak.get(h, 0)])

# B) Gratis y de pago en cada provincia
kopuruak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"probintzia": "$probintzia", "doan": "$doan"}, "kopurua": {"$sum": 1}}},
]):
    kopuruak[(d["_id"]["probintzia"], d["_id"]["doan"])] = d["kopurua"]

B = [["probintzia", "doan", "ordainpekoak"]]
for p in ["Araba", "Bizkaia", "Gipuzkoa"]:
    B.append([p, kopuruak.get((p, True), 0), kopuruak.get((p, False), 0)])

# C) Duración media (días) por categoría
C = [["kategoria", "batez besteko egunak"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$kategoria", "media": {"$avg": "$egunak"}}},
    {"$sort": {"media": -1}},
]):
    C.append([d["_id"], round(d["media"], 2)])

# D) Los 10 eventos con más aforo
D = [["izena", "herria", "aforoa"]]
for d in db.garbiak.aggregate([
    {"$sort": {"aforoa": -1}},
    {"$limit": 10},
]):
    D.append([d["izena"], d["herria"], d["aforoa"]])

# E) Precio medio de los eventos DE PAGO por categoría ($gt = "mayor que")
E = [["kategoria", "batez besteko prezioa (€)"]]
for d in db.garbiak.aggregate([
    {"$match": {"prezioa": {"$gt": 0}}},
    {"$group": {"_id": "$kategoria", "media": {"$avg": "$prezioa"}}},
    {"$sort": {"media": -1}},
]):
    E.append([d["_id"], round(d["media"], 2)])


# ============================================================
# 4. AURKEZTU (3 puntos)
# ============================================================
csv_idatzi("taula_A_hilabeteak.csv", A)     # líneas
csv_idatzi("taula_B_doan.csv", B)           # columnas apiladas
csv_idatzi("taula_C_egunak.csv", C)         # columnas
csv_idatzi("taula_D_top10.csv", D)          # barras
csv_idatzi("taula_E_prezioa.csv", E)        # columnas
print("Listo: 5 CSV creados")
