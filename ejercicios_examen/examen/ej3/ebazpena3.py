# EBAZPENA 3: MENDI-IBILBIDEAK (rutas de montaña; incluye una LISTA dentro de cada documento)
# Necesita ibilbideak.json en la misma carpeta y MongoDB encendido.
import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["examen3"]


def csv_idatzi(fitxategia, lerroak):
    """; como separador y coma decimal, para que Excel en español lo abra bien."""
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        for lerroa in lerroak:
            f.write(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x)
                             for x in lerroa) + "\n")


def minutuak(iraupena):
    """'3h 30min' -> 210 | '2h' -> 120 | '45min' -> 45"""
    t = iraupena.lower().replace(" ", "")      # "3h30min"
    orduak = 0
    min_ = 0
    if "h" in t:
        orduak_testua, t = t.split("h")        # "3" y "30min"
        orduak = int(orduak_testua)
    if "min" in t:
        min_ = int(t.replace("min", ""))
    return orduak * 60 + min_


# ============================================================
# 1. IMPORTAR (1 punto)
# ============================================================
with open("ibilbideak.json", encoding="utf-8") as f:
    db.gordinak.drop()
    db.gordinak.insert_many(json.load(f))

print(db.gordinak.count_documents({}), "dokumentu")
print(db.gordinak.find_one())              # fíjate: "urtaroak" es una LISTA


# ============================================================
# 2. LIMPIAR (3 puntos)
# ============================================================
garbiak = []
for d in db.gordinak.find():
    urtaroak = [u.strip().lower() for u in d["urtaroak"]]     # "UDA" -> "uda"
    if not urtaroak:                                           # lista vacía -> todo el año
        urtaroak = ["urte osoa"]

    garbiak.append({
        "izena": d["izena"],
        "herria": d["herria"],
        "probintzia": d["probintzia"],
        "distantzia": float(d["distantzia"].replace("km", "").replace(",", ".")),   # "12,5 km" -> 12.5
        "minutuak": minutuak(d["iraupena"]),                                         # "3h 30min" -> 210
        "desnibela": int(d["desnibela"].replace("m", "").strip()),                   # "850 m" -> 850
        "zailtasuna": d["zailtasuna"].strip().lower(),                               # "ZAILA " -> "zaila"
        "urtaroak": urtaroak,
    })

db.garbiak.drop()
db.garbiak.insert_many(garbiak)
print(len(garbiak), "garbi")


# ============================================================
# 3. AZTERTU (3 puntos)
# ============================================================
ZAILTASUNAK = ["erraza", "ertaina", "zaila"]

# A) Rutas de cada dificultad en cada provincia
kopuruak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"probintzia": "$probintzia", "zailtasuna": "$zailtasuna"}, "kopurua": {"$sum": 1}}},
]):
    kopuruak[(d["_id"]["probintzia"], d["_id"]["zailtasuna"])] = d["kopurua"]

A = [["probintzia"] + ZAILTASUNAK]
for p in ["Araba", "Bizkaia", "Gipuzkoa"]:
    A.append([p] + [kopuruak.get((p, z), 0) for z in ZAILTASUNAK])

# B) Distancia media según dificultad
B = [["zailtasuna", "batez besteko distantzia (km)"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$zailtasuna", "media": {"$avg": "$distantzia"}}},
]):
    B.append([d["_id"], round(d["media"], 1)])

# C) Rutas recomendadas en cada estación -> $unwind "abre" la lista: 1 documento por estación
urtaroKop = {}
for d in db.garbiak.aggregate([
    {"$unwind": "$urtaroak"},
    {"$group": {"_id": "$urtaroak", "kopurua": {"$sum": 1}}},
]):
    urtaroKop[d["_id"]] = d["kopurua"]

C = [["urtaroa", "ibilbideak"]]
for u in ["udaberria", "uda", "udazkena", "negua", "urte osoa"]:
    C.append([u, urtaroKop.get(u, 0)])

# D) Las 10 rutas más largas en tiempo
D = [["izena", "herria", "minutuak"]]
for d in db.garbiak.aggregate([
    {"$sort": {"minutuak": -1}},
    {"$limit": 10},
]):
    D.append([d["izena"], d["herria"], d["minutuak"]])

# E) Distancia vs desnivel de cada ruta (para un gráfico de dispersión)
E = [["distantzia (km)", "desnibela (m)"]]
for d in db.garbiak.find():
    E.append([d["distantzia"], d["desnibela"]])


# ============================================================
# 4. AURKEZTU (3 puntos)
# ============================================================
csv_idatzi("taula_A_zailtasuna.csv", A)     # columnas apiladas
csv_idatzi("taula_B_distantzia.csv", B)     # columnas
csv_idatzi("taula_C_urtaroak.csv", C)       # columnas
csv_idatzi("taula_D_top10.csv", D)          # barras
csv_idatzi("taula_E_dispertsioa.csv", E)    # dispersión (X = distancia, Y = desnivel)
print("Listo: 5 CSV creados")
