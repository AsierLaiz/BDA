import json
import csv
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client["repaso"]

with open("ostatu_txikiak.json", encoding="utf-8") as f:
    ostatuak= json.load(f)
db.ostatuak.drop()
db.ostatuak.insert_many(ostatuak)
print(db.ostatuak.count_documents({}))
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
# 3. Guardar cada tabla en un CSV (los gráficos los haces luego en Excel)
# ------------------------------------------------------------
def csv_idatzi(fitxategia, lerroak):
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, delimiter=";").writerows(lerroak)     
 
 
csv_idatzi("taula_A_motak.csv", A)
csv_idatzi("taula_B_probintziak.csv", B)
csv_idatzi("taula_C_top5.csv", C)
csv_idatzi("taula_D_motak_probintziak.csv", D)
print("Listo: 4 CSV creados")