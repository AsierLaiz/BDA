# EBAZPENA 1: KARGAGAILUAK (puntos de carga de coches eléctricos)
# Necesita kargagailuak.json en la misma carpeta y MongoDB encendido.
import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["examen1"]


def csv_idatzi(fitxategia, lerroak):
    """; como separador y coma decimal, para que Excel en español lo abra bien."""
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        for lerroa in lerroak:
            f.write(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x)
                             for x in lerroa) + "\n")


# ============================================================
# 1. IMPORTAR (1 punto): JSON -> MongoDB
# ============================================================
with open("kargagailuak.json", encoding="utf-8") as f:
    db.gordinak.drop()
    db.gordinak.insert_many(json.load(f))

print(db.gordinak.count_documents({}), "dokumentu")
print(db.gordinak.find_one())          # mirar qué campos hay y cómo vienen


# ============================================================
# 2. LIMPIAR (3 puntos): leer los datos "gordinak" y guardar los buenos en "garbiak"
# ============================================================
garbiak = []
ikusiak = set()                         # nombres ya vistos, para quitar duplicados

for d in db.gordinak.find():
    izena = d["izena"].strip()
    if izena in ikusiak:                # duplicado -> se descarta
        continue
    if not d.get("prezioa"):            # None o "" -> se descarta
        continue
    ikusiak.add(izena)

    garbiak.append({
        "izena": izena,
        "udalerria": d["udalerria"].strip().title(),                       # " BILBO" -> "Bilbo"
        "probintzia": d["probintzia"],
        "mota": d["mota"].strip().lower(),                                 # "Azkarra " -> "azkarra"
        "potentzia": float(d["potentzia"].replace("kW", "").replace(",", ".")),   # "7,4 kW" -> 7.4
        "prezioa": float(d["prezioa"].replace("€/kWh", "").replace(",", ".")),    # "0,52 €/kWh" -> 0.52
        "orduak24": d["24ordu"].strip().lower() == "bai",                  # "BAI" -> True
        "lat": float(d["lat"]),
        "lon": float(d["lon"]),
    })

db.garbiak.drop()
db.garbiak.insert_many(garbiak)
print(len(garbiak), "garbi,", db.gordinak.count_documents({}) - len(garbiak), "deskartatuta")


# ============================================================
# 3. AZTERTU (3 puntos): consultas
# ============================================================
# A) Cuántos hay de cada mota y su potencia media
A = [["mota", "kopurua", "batez besteko potentzia (kW)"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$mota", "kopurua": {"$sum": 1}, "media": {"$avg": "$potentzia"}}},
    {"$sort": {"kopurua": -1}},
]):
    A.append([d["_id"], d["kopurua"], round(d["media"], 1)])

# B) Precio medio por provincia
B = [["probintzia", "batez besteko prezioa (€/kWh)"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$probintzia", "media": {"$avg": "$prezioa"}}},
    {"$sort": {"media": -1}},
]):
    B.append([d["_id"], round(d["media"], 3)])

# C) Los 10 más potentes
C = [["izena", "udalerria", "potentzia (kW)"]]
for d in db.garbiak.aggregate([
    {"$sort": {"potentzia": -1}},
    {"$limit": 10},
]):
    C.append([d["izena"], d["udalerria"], d["potentzia"]])

# D) En cada provincia: abiertos 24h, no 24h, y % de 24h
kopuruak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"probintzia": "$probintzia", "h24": "$orduak24"}, "kopurua": {"$sum": 1}}},
]):
    kopuruak[(d["_id"]["probintzia"], d["_id"]["h24"])] = d["kopurua"]

D = [["probintzia", "24 ordu", "ez 24 ordu", "24 orduko %"]]
for p in ["Araba", "Bizkaia", "Gipuzkoa"]:
    bai = kopuruak.get((p, True), 0)
    ez = kopuruak.get((p, False), 0)
    D.append([p, bai, ez, round(100 * bai / (bai + ez), 1) if bai + ez else 0])

# E) Datos para el mapa: lon, lat, mota
E = [["lon", "lat", "mota"]]
for d in db.garbiak.find():
    E.append([d["lon"], d["lat"], d["mota"]])


# ============================================================
# 4. AURKEZTU (3 puntos): un CSV por tabla -> Excel -> gráficos
# ============================================================
csv_idatzi("taula_A_motak.csv", A)          # gráfico: columnas
csv_idatzi("taula_B_prezioa.csv", B)        # gráfico: columnas
csv_idatzi("taula_C_top10.csv", C)          # gráfico: barras
csv_idatzi("taula_D_24h.csv", D)            # gráfico: columnas apiladas (cols B y C)
csv_idatzi("taula_E_mapa.csv", E)           # gráfico: dispersión (mapa) con 2 colores
print("Listo: 5 CSV creados")
