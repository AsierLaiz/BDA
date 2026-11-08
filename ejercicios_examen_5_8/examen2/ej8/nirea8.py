import json
import csv
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client["repaso8"]

with open("lan_eskaintzak.json", encoding="utf-8") as f:
    lan_eskaintzak= json.load(f)
db.lan_eskaintzak.drop()
db.lan_eskaintzak.insert_many(lan_eskaintzak)
print(db.lan_eskaintzak.count_documents({}))
print(db.lan_eskaintzak.find_one())

garbiak = []
for d in db.lan_eskaintzak.find():
    soldata = d["soldata"].strip().lower()
    if "negoziagarria" in soldata:                     
        continue
    zenbakiak = soldata.replace("€/hilabete", "").replace(".", "").split("-")
    gutxienekoa = int(zenbakiak[0].strip())
    gehienekoa = int(zenbakiak[-1].strip())
    esperientzia = d["esperientzia"].strip().lower()    
    if "gabe" in esperientzia:
        urteak = 0
    else:
        urteak = int(esperientzia.split()[0])   
    garbiak.append({
        "izena": d["izena"],
        "enpresa": d["enpresa"],
        "probintzia": d["probintzia"],
        "sektorea": d["sektorea"].strip().capitalize(),
        "kontratua":d["kontratua"],
        "urrunekoa": d["urrunekoa"].strip().capitalize(),
        "esperientzia": urteak,
        "gutxienekoa": gutxienekoa,
        "gehienekoa": gehienekoa,
        "batezbestekoa": (gutxienekoa + gehienekoa) / 2,

    })

db.garbiak.drop()
db.garbiak.insert_many(garbiak)

A = [["sektore","soldata"]]
for d in db.garbiak.aggregate([
    {"$group":{"_id":"$sektorea","media":{"$avg": "$batezbestekoa"}}},
    {"$sort":{"media":-1}},
]):
    A.append([d["_id"], round(d["media"])])

kopuruak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"kontratua": "$kontratua", "urrunekoa": "$urrunekoa"}, "kopurua": {"$sum": 1}}},
]):
    kopuruak[(d["_id"]["kontratua"], d["_id"]["urrunekoa"])] = d["kopurua"]

URRUNEKOAK = ["Bai", "Hibridoa", "Ez"]
B = [["kontratua"] + URRUNEKOAK]
for k in ["Mugagabea", "Mugatua", "Praktikak"]:
    B.append([k] + [kopuruak.get((k, u), 0) for u in URRUNEKOAK])

C = [["izena","soldata_max"]]
for d in db.garbiak.aggregate([
    {"$sort":{"gehienekoa":-1}},
    {"$limit":10},
]):
    C.append([d["izena"], d["sektorea"], d["gehienekoa"]])

guztiak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"probintzia": "$probintzia", "urrunekoa": "$urrunekoa"}, "kopurua": {"$sum": 1}}},
]):
    guztiak[(d["_id"]["probintzia"], d["_id"]["urrunekoa"])] = d["kopurua"]

D = [["probintzia"] + [u + " %" for u in URRUNEKOAK]]
for p in ["Araba", "Bizkaia", "Gipuzkoa"]:
    total = sum(guztiak.get((p, u), 0) for u in URRUNEKOAK)
    D.append([p] + [round(100 * guztiak.get((p, u), 0) / total, 1) if total else 0 for u in URRUNEKOAK])

E = [["esperientzia","soldata"]]
for d in db.garbiak.find():
    E.append([d["esperientzia"], d["batezbestekoa"]])


def csv_idatzi(fitxategia, lerroak):
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, delimiter=";").writerows(lerroak)     


csv_idatzi("taula_A_.csv", A)
csv_idatzi("taula_B_.csv", B)
csv_idatzi("taula_C_.csv", C)
csv_idatzi("taula_D_.csv", D)
csv_idatzi("taula_E_.csv",E)
