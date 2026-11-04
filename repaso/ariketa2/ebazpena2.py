# EBAZPENA 2 / SOLUCIÓN: jatetxeak (JSON -> MongoDB -> CSV)
# Necesita: jatetxeak.json en la misma carpeta y MongoDB encendido.
import csv
import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["proba2"]

# ------------------------------------------------------------
# 1. Leer el JSON y meterlo en MongoDB
# ------------------------------------------------------------
with open("jatetxeak.json", encoding="utf-8") as f:
    db.jatetxeak.drop()
    db.jatetxeak.insert_many(json.load(f))

print(db.jatetxeak.count_documents({}), "jatetxe")
print(db.jatetxeak.find_one())      # fíjate: balorazioa, prezioa, lat y lon vienen como TEXTO


# ------------------------------------------------------------
# 2. Limpiar: pasar el texto a números (se hace en Python, documento a documento)
# ------------------------------------------------------------
for j in list(db.jatetxeak.find()):
    db.jatetxeak.update_one({"_id": j["_id"]}, {"$set": {
        "balorazioa": float(j["balorazioa"].replace(",", ".")),   # "4,5"  -> 4.5
        "prezioa": int(j["prezioa"].replace("€", "").strip()),    # "28 €" -> 28
        "lat": float(j["lat"]),                                   # "43.2" -> 43.2
        "lon": float(j["lon"]),
    }})


# ------------------------------------------------------------
# 3. Las 4 tablas
# ------------------------------------------------------------
# A) Mapa: una fila por jatetxe (lon, lat, terraza)
A = [["lon", "lat", "terraza"]]
for j in db.jatetxeak.find():
    A.append([j["lon"], j["lat"], j["terraza"]])

# B) Valoración media por tipo
B = [["mota", "batez besteko balorazioa"]]
for d in db.jatetxeak.aggregate([
    {"$group": {"_id": "$mota", "media": {"$avg": "$balorazioa"}}},
    {"$sort": {"media": -1}},
]):
    B.append([d["_id"], round(d["media"], 2)])

# C) Porcentaje de locales con terraza en cada provincia
kopuruak = {}
for d in db.jatetxeak.aggregate([
    {"$group": {"_id": {"probintzia": "$probintzia", "terraza": "$terraza"}, "kopurua": {"$sum": 1}}},
]):
    kopuruak[(d["_id"]["probintzia"], d["_id"]["terraza"])] = d["kopurua"]

C = [["probintzia", "terrazarekin", "terrazarik gabe", "terrazarekin %"]]
for p in ["Araba", "Bizkaia", "Gipuzkoa"]:
    bai = kopuruak.get((p, "Bai"), 0)
    ez = kopuruak.get((p, "Ez"), 0)
    C.append([p, bai, ez, round(100 * bai / (bai + ez), 1) if bai + ez else 0])

# D) Los 5 más caros entre los que tienen valoración de 4 o más
D = [["izena", "udalerria", "prezioa", "balorazioa"]]
for j in db.jatetxeak.aggregate([
    {"$match": {"balorazioa": {"$gte": 4}}},
    {"$sort": {"prezioa": -1}},
    {"$limit": 5},
]):
    D.append([j["izena"], j["udalerria"], j["prezioa"], j["balorazioa"]])


# ------------------------------------------------------------
# 4. Guardar cada tabla en un CSV
# ------------------------------------------------------------
def csv_idatzi(fitxategia, lerroak):
    """; como separador y coma decimal, para que Excel en español lo abra bien."""
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        for lerroa in lerroak:
            f.write(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x)
                             for x in lerroa) + "\n")


csv_idatzi("taula_A_mapa.csv", A)
csv_idatzi("taula_B_media.csv", B)
csv_idatzi("taula_C_terraza.csv", C)
csv_idatzi("taula_D_top5.csv", D)
print("Listo: 4 CSV creados")
