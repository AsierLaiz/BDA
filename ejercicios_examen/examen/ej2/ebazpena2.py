# EBAZPENA 2: IKASTETXEAK (colegios)
# Necesita ikastetxeak.json en la misma carpeta y MongoDB encendido.
import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["examen2"]


def csv_idatzi(fitxategia, lerroak):
    """; como separador y coma decimal, para que Excel en español lo abra bien."""
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        for lerroa in lerroak:
            f.write(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x)
                             for x in lerroa) + "\n")


def zenbakia(x):
    """Pasa a entero. Si no se puede ('n/a', '', None) devuelve None."""
    try:
        return int(x)
    except (ValueError, TypeError):
        return None


# ============================================================
# 1. IMPORTAR (1 punto)
# ============================================================
with open("ikastetxeak.json", encoding="utf-8") as f:
    db.gordinak.drop()
    db.gordinak.insert_many(json.load(f))

print(db.gordinak.count_documents({}), "dokumentu")
print(db.gordinak.find_one())


# ============================================================
# 2. LIMPIAR (3 puntos)
# ============================================================
garbiak = []
for d in db.gordinak.find():
    ikasleak = zenbakia(d.get("ikasleak"))
    irakasleak = zenbakia(d.get("irakasleak"))
    if ikasleak is None or not irakasleak:       # sin alumnos válidos o sin profesores -> se descarta
        continue

    urtea = zenbakia(d.get("urtea"))              # puede quedar None (se conserva el colegio)
    garbiak.append({
        "izena": d["izena"],
        "udalerria": d["udalerria"],
        "probintzia": d["probintzia"],
        "mota": d["mota"].strip().lower(),                         # "PUBLIKOA" -> "publikoa"
        "ikasleak": ikasleak,
        "irakasleak": irakasleak,
        "ratioa": round(ikasleak / irakasleak, 1),                  # alumnos por profesor
        "eredua": d["eredua"].strip().upper(),                     # "b" -> "B"
        "urtea": urtea,
        "hamarkada": urtea // 10 * 10 if urtea else None,          # 1987 -> 1980
    })

db.garbiak.drop()
db.garbiak.insert_many(garbiak)
print(len(garbiak), "garbi,", db.gordinak.count_documents({}) - len(garbiak), "deskartatuta")


# ============================================================
# 3. AZTERTU (3 puntos)
# ============================================================
# A) Ratio medio (alumnos por profesor) según mota
A = [["mota", "ikasle/irakasle ratioa"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$mota", "media": {"$avg": "$ratioa"}}},
]):
    A.append([d["_id"], round(d["media"], 1)])

# B) Modelo lingüístico (A/B/D) en cada provincia
kopuruak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"probintzia": "$probintzia", "eredua": "$eredua"}, "kopurua": {"$sum": 1}}},
]):
    kopuruak[(d["_id"]["probintzia"], d["_id"]["eredua"])] = d["kopurua"]

B = [["probintzia", "A", "B", "D"]]
for p in ["Araba", "Bizkaia", "Gipuzkoa"]:
    B.append([p] + [kopuruak.get((p, e), 0) for e in ["A", "B", "D"]])

# C) Los 10 colegios con más alumnos
C = [["izena", "udalerria", "ikasleak"]]
for d in db.garbiak.aggregate([
    {"$sort": {"ikasleak": -1}},
    {"$limit": 10},
]):
    C.append([d["izena"], d["udalerria"], d["ikasleak"]])

# D) Colegios abiertos por década (solo los que tienen año)
D = [["hamarkada", "ikastetxeak"]]
for d in db.garbiak.aggregate([
    {"$match": {"hamarkada": {"$ne": None}}},
    {"$group": {"_id": "$hamarkada", "kopurua": {"$sum": 1}}},
    {"$sort": {"_id": 1}},
]):
    D.append([d["_id"], d["kopurua"]])

# E) Alumnos totales por provincia
E = [["probintzia", "ikasleak"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$probintzia", "ikasleak": {"$sum": "$ikasleak"}}},
    {"$sort": {"ikasleak": -1}},
]):
    E.append([d["_id"], d["ikasleak"]])


# ============================================================
# 4. AURKEZTU (3 puntos)
# ============================================================
csv_idatzi("taula_A_ratioa.csv", A)         # columnas
csv_idatzi("taula_B_eredua.csv", B)         # columnas apiladas
csv_idatzi("taula_C_top10.csv", C)          # barras
csv_idatzi("taula_D_hamarkadak.csv", D)     # líneas o columnas
csv_idatzi("taula_E_probintziak.csv", E)    # sectores (tarta)
print("Listo: 5 CSV creados")
