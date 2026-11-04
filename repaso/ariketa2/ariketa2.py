import json
import csv
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client["proba2"]

with open("jatetxeak.json", encoding="utf-8") as f:
    jatetxeak= json.load(f)
db.jatetxeak.drop()
db.jatetxeak.insert_many(jatetxeak)
print(db.jatetxeak.count_documents({}))
print(db.jatetxeak.find_one())



for j in list(db.jatetxeak.find()):
    db.jatetxeak.update_one({"_id":j["_id"]},{"$set":{
        "balorazioa": float(j["balorazioa"].replace(",",".")),
        "prezioa": int(j["prezioa"].replace("€","").strip()),
        "lat": float(j["lat"]),
        "lon": float(j["lon"]),
    }})


A= [["lon","lat","terraza"]]
for j in db.jatetxeak.find():
    A.append([j["lon"],j["lat"],j["terraza"]])

B= [["mota","batezbesteko"]]
for d in db.jatetxeak.aggregate([
    {"$group":{"_id":"$mota","media":{"$avg":"$balorazioa"}}},
    {"$sort":{"media": -1}},
]):
    B.append([d["_id"],round(d["media"],2)])
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
D = [["izena", "udalerria", "prezioa", "balorazioa"]]
for j in db.jatetxeak.aggregate([
    {"$match":{"balorazioa":{"$gte": 4}}},
    {"$sort": {"prezioa": -1}},
    {"$limit":5},
]):
    D.append([j["izena"], j["udalerria"],j["prezioa"], j["balorazioa"]])

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
