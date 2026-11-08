import json
import csv
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client["repaso3"]

with open("ibilbideak.json", encoding="utf-8") as f:
    ibilbideak= json.load(f)
db.ibilbideak.drop()
db.ibilbideak.insert_many(ibilbideak)
print(db.ibilbideak.count_documents({}))
print(db.ibilbideak.find_one())
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

garbiak = []
for d in db.ibilbideak.find():
    urtaroak=[u.strip().lower() for u in d["urtaroak"]]
    if not urtaroak:
        urtaroak=["urte osoa"]

    garbiak.append({
        "izena": d["izena"],
        "herria": d["herria"],
        "probintzia": d["probintzia"],
        "distantzia": float(d["distantzia"].replace("km", "").replace(",",".")),
        "minutuak": minutuak(d["iraupena"]),     
        "desnibela": float(d["desnibela"].replace("m","")),
        "zailtasuna": d["zailtasuna"].strip().lower(),
        "urtaroak": urtaroak,
    })

db.garbiak.drop()
db.garbiak.insert_many(garbiak)

ZAILTASUNAK = ["erraza", "ertaina", "zaila"]

kopuruak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"probintzia": "$probintzia", "zailtasuna": "$zailtasuna"}, "kopurua": {"$sum": 1}}},
]):
    kopuruak[(d["_id"]["probintzia"], d["_id"]["zailtasuna"])] = d["kopurua"]

A = [["probintzia"] + ZAILTASUNAK]
for p in ["Araba", "Bizkaia", "Gipuzkoa"]:
    A.append([p] + [kopuruak.get((p, z), 0) for z in ZAILTASUNAK])


B=[["zailtasuna","distantzia"]]
for d in db.garbiak.aggregate([
    {"$group":{"_id":"$zailtasuna","media":{"$avg":"$distantzia"}}},

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

D=[["izena","minutuak"]]
for d in db.garbiak.aggregate([
    {"$sort":{"minutuak": -1}},
    {"$limit": 10},
]):
    D.append([d["izena"], d["minutuak"]])

E=[["distantzia","desnibela"]]
for d in db.garbiak.find():
    E.append([d["distantzia"], d["desnibela"]])



def csv_idatzi(fitxategia, lerroak):
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, delimiter=";").writerows(lerroak)     

csv_idatzi("taula_A_.csv", A)
csv_idatzi("taula_B_.csv", B)
csv_idatzi("taula_C_.csv", C)
csv_idatzi("taula_D_.csv", D)
csv_idatzi("taula_E_.csv",E)
print("Listo: 5 CSV creados")