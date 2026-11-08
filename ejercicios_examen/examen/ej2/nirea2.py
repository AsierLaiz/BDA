import json
import csv
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client["repaso2"]

with open("ikastetxeak.json", encoding="utf-8") as f:
    ikastetxeak= json.load(f)
db.ikastetxeak.drop()
db.ikastetxeak.insert_many(ikastetxeak)
print(db.ikastetxeak.count_documents({}))
print(db.ikastetxeak.find_one())
def zenbakia(x):
    """Pasa a entero. Si no se puede ('n/a', '', None) devuelve None."""
    try:
        return int(x)
    except (ValueError, TypeError):
        return None

garbiak=[]
for d in db.ikastetxeak.find():
    ikasleak = zenbakia(d.get("ikasleak"))
    irakasleak = zenbakia(d.get("irakasleak"))
    if ikasleak is None or not irakasleak:       
        continue
    urtea=zenbakia(d.get("urtea"))
    garbiak.append({
        "izena": d["izena"],
        "udalerria": d["udalerria"],
        "probintzia": d["probintzia"],
        "mota": d["mota"].strip().lower(),                         # "PUBLIKOA" -> "publikoa"
        "ikasleak": ikasleak,
        "irakasleak": irakasleak,
        "ratioa": round(ikasleak / irakasleak, 1),                  # alumnos por profesor
        "eredua": d["eredua"].strip().upper(),                     # "b" -> "B"
        "urtea": urtea,
        "hamarkada": urtea // 10 * 10 if urtea else None,          # 1987 -> 1980
    })

db.garbiak.drop()
db.garbiak.insert_many(garbiak)

A = [["mota", "ikasle/irakasle ratioa"]]
for d in db.garbiak.aggregate([
    {"$group":{"_id":"$mota", "media": {"$avg": "$ratioa"}}},
]):
    A.append([d["_id"], round(d["media"],1)])

kopuruak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"probintzia": "$probintzia", "eredua": "$eredua"}, "kopurua": {"$sum": 1}}},
]):
    kopuruak[(d["_id"]["probintzia"], d["_id"]["eredua"])] = d["kopurua"]

B = [["probintzia", "A", "B", "D"]]
for p in ["Araba", "Bizkaia", "Gipuzkoa"]:
    B.append([p] + [kopuruak.get((p, e), 0) for e in ["A", "B", "D"]])

C = [["izena","ikasleak"]]
for d in db.garbiak.aggregate([
    {"$sort":{"ikasleak":-1}},
    {"$limit":10},
]):
    C.append([d["izena"], d["ikasleak"]])

D = [["hamarkada", "ikastetxeak"]]
for d in db.garbiak.aggregate([
    {"$match": {"hamarkada": {"$ne": None}}},
    {"$group": {"_id": "$hamarkada", "kopurua": {"$sum": 1}}},
    {"$sort": {"_id": 1}},
]):
    D.append([d["_id"], d["kopurua"]])

E=[["probintzia","ikasleak"]]
for d in db.garbiak.aggregate([
    {"$group":{"_id":"$probintzia","ikasleak":{"$sum":"$ikasleak"}}},
    {"$sort":{"_id": -1}},
]):
    E.append([d["_id"], d["ikasleak"]])

def csv_idatzi(fitxategia, lerroak):
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, delimiter=";").writerows(lerroak)     

csv_idatzi("taula_A_.csv", A)
csv_idatzi("taula_B_.csv", B)
csv_idatzi("taula_C_.csv", C)
csv_idatzi("taula_D_.csv", D)
csv_idatzi("taula_E_.csv",E)
print("Listo: 5 CSV creados")