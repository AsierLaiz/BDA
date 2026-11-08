import json
import csv
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client["repaso5"]

with open("ekitaldiak.json", encoding="utf-8") as f:
    ekitaldiak= json.load(f)
db.ekitaldiak.drop()
db.ekitaldiak.insert_many(ekitaldiak)
print(db.ekitaldiak.count_documents({}))
print(db.ekitaldiak.find_one())

def zenbakia(x):
    """Pasa a entero. Si no se puede ('n/a') devuelve None."""
    try:
        return int(x)
    except (ValueError, TypeError):
        return None
        
garbiak = []
for d in db.ekitaldiak.find():
    
    datak = d["datak"].split(" - ")
    hasiera = datak[0]
    amaiera = datak[-1]                         
    if hasiera[6:10] != "2024":                 
        continue
    prezioa_testua = d["prezioa"].strip().lower()
    if prezioa_testua=="zehazteko":
        continue
    if prezioa_testua=="doan":
        prezioa=0.0
    else:
        prezioa = float(prezioa_testua.replace("€", "").replace(",", ".").strip())

    aforoa = zenbakia(str(d["aforoa"]).replace(".",""))
    if aforoa is None:
        continue
    garbiak.append({
        "izena": d["izena"],
        "herria": d["herria"],
        "probintzia": d["probintzia"],
        "kategoria": d["kategoria"].strip().capitalize(),             
        "hilabetea": int(hasiera[3:5]),                               
        "egunak": int(amaiera[:2]) - int(hasiera[:2]) + 1,          
        "prezioa": prezioa,
        "doan": prezioa == 0,
        "aforoa": aforoa,
    })

db.garbiak.drop()
db.garbiak.insert_many(garbiak)

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


def csv_idatzi(fitxategia, lerroak):
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, delimiter=";").writerows(lerroak)     
# ============================================================
# 4. AURKEZTU (3 puntos)
# ============================================================
csv_idatzi("taula_A_hilabeteak.csv", A)     # líneas
csv_idatzi("taula_B_doan.csv", B)           # columnas apiladas
csv_idatzi("taula_C_egunak.csv", C)         # columnas
csv_idatzi("taula_D_top10.csv", D)          # barras
csv_idatzi("taula_E_prezioa.csv", E)        # columnas
print("Listo: 5 CSV creados")