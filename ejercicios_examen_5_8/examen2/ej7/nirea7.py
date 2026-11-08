import json
import csv
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client["repaso7"]

def urtaroa(hilabetea):
    """Estación del año según el mes."""
    if hilabetea in (12, 1, 2):
        return "negua"
    if hilabetea in (3, 4, 5):
        return "udaberria"
    if hilabetea in (6, 7, 8):
        return "uda"
    return "udazkena"

with open("eguraldia.json", encoding="utf-8") as f:
    eguraldia= json.load(f)
db.eguraldia.drop()
db.eguraldia.insert_many(eguraldia)
print(db.eguraldia.count_documents({}))
print(db.eguraldia.find_one())


garbiak = []
for d in db.eguraldia.find():
    try:
        tenperatura = float(d["tenperatura"].replace("ºC", "").replace(",",".").strip())
    except ValueError:
        continue
    if tenperatura > 45 or tenperatura < -20:
        continue

    euria_testua = d["euria"].strip()
    if euria_testua == "-":
        euria = 0.0
    else:
        euria= float(euria_testua.replace("mm","").replace(",",".").strip())

    noiz= d["noiz"]
    hilabetea = int(noiz[5:7])
    garbiak.append({
        "estazioa": d["estazioa"],
        "hilabetea": hilabetea,
        "urtaroa": urtaroa(hilabetea),
        "ordua": int(noiz[11:13]),                     
        "tenperatura": tenperatura,
        "euria": euria,
        "haizea": float(d["haizea"].replace("km/h", "").strip()),        
    })
db.garbiak.drop()
db.garbiak.insert_many(garbiak)

ESTAZIOAK = ["Bilbo", "Donostia", "Gasteiz"]
batezbestekoak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"estazioa": "$estazioa", "hilabetea": "$hilabetea"}, "media": {"$avg": "$tenperatura"}}},
]):
    batezbestekoak[(d["_id"]["estazioa"], d["_id"]["hilabetea"])] = d["media"]

A = [["hilabetea"] + ESTAZIOAK]
for h in range(1, 13):
    A.append([h] + [round(batezbestekoak[(e, h)], 1) if (e, h) in batezbestekoak else "" for e in ESTAZIOAK])


euriak = {d["_id"]: d["euria"] for d in db.garbiak.aggregate([
    {"$group": {"_id": "$urtaroa", "euria": {"$sum": "$euria"}}},
])}
B = [["urtaroa", "euria (mm)"]]
for u in ["udaberria", "uda", "udazkena", "negua"]:
    B.append([u, round(euriak.get(u, 0), 1)])

C = [["estazioa", "haize maximoa (km/h)"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$estazioa", "maximoa": {"$max": "$haizea"}}},
    {"$sort": {"maximoa": -1}},
]):
    C.append([d["_id"], d["maximoa"]])

D = [["estazioa", "euritsu lekturak"]]
for d in db.garbiak.aggregate([
    {"$match": {"euria": {"$gt": 0}}},
    {"$group": {"_id": "$estazioa", "kopurua": {"$sum": 1}}},
    {"$sort": {"kopurua": -1}},
]):
    D.append([d["_id"], d["kopurua"]])

E = [["ordua", "batez besteko tenperatura"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$ordua", "media": {"$avg": "$tenperatura"}}},
    {"$sort": {"_id": 1}},
]):
    E.append([d["_id"], round(d["media"], 1)])


def csv_idatzi(fitxategia, lerroak):
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, delimiter=";").writerows(lerroak)     


csv_idatzi("taula_A_tenperatura.csv", A)    
csv_idatzi("taula_B_euria.csv", B)         
csv_idatzi("taula_C_haizea.csv", C)         
csv_idatzi("taula_D_euritsuak.csv", D)      
csv_idatzi("taula_E_orduak.csv", E)         
print("Listo: 5 CSV creados")