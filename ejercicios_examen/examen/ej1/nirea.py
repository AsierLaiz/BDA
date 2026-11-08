import json
import csv
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client["repaso"]

with open("kargagailuak.json", encoding="utf-8") as f:
    kargagailuak= json.load(f)
db.kargagailuak.drop()
db.kargagailuak.insert_many(kargagailuak)
print(db.kargagailuak.count_documents({}))
print(db.kargagailuak.find_one())

garbiak = []
ikusiak = set()                         # nombres ya vistos, para quitar duplicados

for d in db.kargagailuak.find():
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
print(len(garbiak), "garbi,", db.kargagailuak.count_documents({}) - len(garbiak), "deskartatuta")

A = [["mota", "kopurua", "batez besteko potentzia (kW)"]]
for d in db.garbiak.aggregate([
    {"$group":{"_id":"$mota","kopurua":{"$sum": 1}, "media":{"$avg":"$potentzia"}}},
    {"$sort":{"kopurua":-1}},
]):
    A.append([d["_id"],d["kopurua"],round(d["media"], 1)])
B= [["probintzia","batez besteko prezioa (€/kWh)"]]
for d in db.garbiak.aggregate([
    {"$group":{"_id":"$probintzia","medio":{"$avg":"$prezioa"}}},
    {"$sort":{"medio":-1}},
]):
    B.append([d["_id"], round(d["medio"], 3)])

C=[["izena","potentzia"]]
for d in db.garbiak.aggregate([
    {"$sort":{"potentzia":-1}},
    {"$limit":10},
]):
    C.append([d["izena"],d["potentzia"]])

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

def csv_idatzi(fitxategia, lerroak):
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, delimiter=";").writerows(lerroak)     

csv_idatzi("taula_A_.csv", A)
csv_idatzi("taula_B_.csv", B)
csv_idatzi("taula_C_.csv", C)
csv_idatzi("taula_D_.csv", D)
csv_idatzi("taula_E_.csv",E)
print("Listo: 4 CSV creados")