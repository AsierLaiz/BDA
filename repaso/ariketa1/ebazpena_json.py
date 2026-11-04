# EBAZPENA / SOLUCIÓN: pasar un JSON a Excel con pymongo
# Necesita: ostatu_txikiak.json en la misma carpeta, MongoDB encendido y pip install openpyxl
import json
from pymongo import MongoClient
from openpyxl import Workbook

client = MongoClient("mongodb://localhost:27017")
db = client["proba"]

# ------------------------------------------------------------
# 1. Leer el JSON y meterlo en MongoDB
# ------------------------------------------------------------
with open("ostatu_txikiak.json", encoding="utf-8") as f:
    datuak = json.load(f)        # el JSON ya es una lista de diccionarios, con plazak como número

db.ostatuak.drop()
db.ostatuak.insert_many(datuak)
print(db.ostatuak.count_documents({}), "ostatu")
print(db.ostatuak.find_one())


# ------------------------------------------------------------
# 2. Las 4 consultas (cada una sale como lista de filas)
# ------------------------------------------------------------
# A) Cuántos alojamientos hay de cada tipo
A = [["mota", "kopurua"]]
for d in db.ostatuak.aggregate([
    {"$group": {"_id": "$mota", "kopurua": {"$sum": 1}}},
    {"$sort": {"kopurua": -1}},
]):
    A.append([d["_id"], d["kopurua"]])

# B) Plazas totales por provincia
B = [["probintzia", "plazak"]]
for d in db.ostatuak.aggregate([
    {"$group": {"_id": "$probintzia", "plazak": {"$sum": "$plazak"}}},
    {"$sort": {"plazak": -1}},
]):
    B.append([d["_id"], d["plazak"]])

# C) Los 5 municipios con más plazas
C = [["udalerria", "plazak"]]
for d in db.ostatuak.aggregate([
    {"$group": {"_id": "$udalerria", "plazak": {"$sum": "$plazak"}}},
    {"$sort": {"plazak": -1}},
    {"$limit": 5},
]):
    C.append([d["_id"], d["plazak"]])

# D) Tipos de alojamiento en cada provincia (agrupamos por DOS cosas)
kopuruak = {}
for d in db.ostatuak.aggregate([
    {"$group": {"_id": {"probintzia": "$probintzia", "mota": "$mota"}, "kopurua": {"$sum": 1}}},
]):
    kopuruak[(d["_id"]["probintzia"], d["_id"]["mota"])] = d["kopurua"]

probintziak = ["Araba", "Bizkaia", "Gipuzkoa"]
motak = sorted({mota for (probintzia, mota) in kopuruak})
D = [["probintzia"] + motak]
for p in probintziak:
    D.append([p] + [kopuruak.get((p, m), 0) for m in motak])   # 0 si no hay ninguno


# ------------------------------------------------------------
# 3. Escribir el Excel (solo tablas, los gráficos los haces tú)
# ------------------------------------------------------------
def taula(orria, lerroak, errenkada):
    """Escribe una tabla desde la fila indicada. Devuelve la primera fila libre."""
    for i, lerroa in enumerate(lerroak):
        for j, balioa in enumerate(lerroa):
            orria.cell(row=errenkada + i, column=1 + j, value=balioa)
    return errenkada + len(lerroak)


wb = Workbook()
orria = wb.active
orria.title = "Taulak"

erroa = 1
for izenburua, taulak in [("A) Ostatu kopurua motaka", A),
                          ("B) Plazak probintziaka", B),
                          ("C) Top 5 udalerri", C),
                          ("D) Motak probintziaka", D)]:
    orria.cell(row=erroa, column=1, value=izenburua)
    erroa = taula(orria, taulak, erroa + 1) + 2          # +2 = una fila en blanco

wb.save("proba.xlsx")
print("Listo: proba.xlsx")
