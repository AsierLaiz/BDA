# EBAZPENA 7: EGURALDIA (lecturas de estaciones meteorológicas; fechas ISO y valores erróneos)
# Necesita eguraldia.json en la misma carpeta y MongoDB encendido.
import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["examen7"]


def csv_idatzi(fitxategia, lerroak):
    """; como separador y coma decimal, para que Excel en español lo abra bien."""
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        for lerroa in lerroak:
            f.write(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x)
                             for x in lerroa) + "\n")


def urtaroa(hilabetea):
    """Estación del año según el mes."""
    if hilabetea in (12, 1, 2):
        return "negua"
    if hilabetea in (3, 4, 5):
        return "udaberria"
    if hilabetea in (6, 7, 8):
        return "uda"
    return "udazkena"


# ============================================================
# 1. IMPORTAR (1 punto)
# ============================================================
with open("eguraldia.json", encoding="utf-8") as f:
    db.gordinak.drop()
    db.gordinak.insert_many(json.load(f))

print(db.gordinak.count_documents({}), "dokumentu")
print(db.gordinak.find_one())


# ============================================================
# 2. LIMPIAR (3 puntos)
# ============================================================
garbiak = []
for d in db.gordinak.find():
    # temperatura: "12,5 °C" -> 12.5 ; "ERR" -> falla -> se descarta
    try:
        tenperatura = float(d["tenperatura"].replace("°C", "").replace(",", ".").strip())
    except ValueError:
        continue
    if tenperatura > 45 or tenperatura < -20:          # valores imposibles (sensor roto) -> fuera
        continue

    euria_testua = d["euria"].strip()
    if euria_testua == "-":                            # "-" = no ha llovido
        euria = 0.0
    else:
        euria = float(euria_testua.replace("mm", "").replace(",", ".").strip())

    noiz = d["noiz"]                                   # "2024-03-15T14:30:00"
    hilabetea = int(noiz[5:7])
    garbiak.append({
        "estazioa": d["estazioa"],
        "hilabetea": hilabetea,
        "urtaroa": urtaroa(hilabetea),
        "ordua": int(noiz[11:13]),                     # la hora (0-23)
        "tenperatura": tenperatura,
        "euria": euria,
        "haizea": float(d["haizea"].replace("km/h", "").strip()),
    })

db.garbiak.drop()
db.garbiak.insert_many(garbiak)
print(len(garbiak), "garbi,", db.gordinak.count_documents({}) - len(garbiak), "deskartatuta")


# ============================================================
# 3. AZTERTU (3 puntos)
# ============================================================
ESTAZIOAK = ["Bilbo", "Donostia", "Gasteiz"]

# A) Temperatura media de cada mes en cada estación (3 líneas)
batezbestekoak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"estazioa": "$estazioa", "hilabetea": "$hilabetea"}, "media": {"$avg": "$tenperatura"}}},
]):
    batezbestekoak[(d["_id"]["estazioa"], d["_id"]["hilabetea"])] = d["media"]

A = [["hilabetea"] + ESTAZIOAK]
for h in range(1, 13):
    A.append([h] + [round(batezbestekoak[(e, h)], 1) if (e, h) in batezbestekoak else "" for e in ESTAZIOAK])

# B) Lluvia total (mm) por estación del año
euriak = {d["_id"]: d["euria"] for d in db.garbiak.aggregate([
    {"$group": {"_id": "$urtaroa", "euria": {"$sum": "$euria"}}},
])}
B = [["urtaroa", "euria (mm)"]]
for u in ["udaberria", "uda", "udazkena", "negua"]:
    B.append([u, round(euriak.get(u, 0), 1)])

# C) Viento máximo registrado en cada estación ($max)
C = [["estazioa", "haize maximoa (km/h)"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$estazioa", "maximoa": {"$max": "$haizea"}}},
    {"$sort": {"maximoa": -1}},
]):
    C.append([d["_id"], d["maximoa"]])

# D) Lecturas con lluvia en cada estación (solo euria > 0)
D = [["estazioa", "euritsu lekturak"]]
for d in db.garbiak.aggregate([
    {"$match": {"euria": {"$gt": 0}}},
    {"$group": {"_id": "$estazioa", "kopurua": {"$sum": 1}}},
    {"$sort": {"kopurua": -1}},
]):
    D.append([d["_id"], d["kopurua"]])

# E) Temperatura media según la hora del día
E = [["ordua", "batez besteko tenperatura"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$ordua", "media": {"$avg": "$tenperatura"}}},
    {"$sort": {"_id": 1}},
]):
    E.append([d["_id"], round(d["media"], 1)])


# ============================================================
# 4. AURKEZTU (3 puntos)
# ============================================================
csv_idatzi("taula_A_tenperatura.csv", A)    # 3 líneas
csv_idatzi("taula_B_euria.csv", B)          # columnas o sectores
csv_idatzi("taula_C_haizea.csv", C)         # columnas
csv_idatzi("taula_D_euritsuak.csv", D)      # columnas
csv_idatzi("taula_E_orduak.csv", E)         # líneas
print("Listo: 5 CSV creados")
