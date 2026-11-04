import json
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client["turismoa"]

with open("viviendas.json", encoding="utf-8") as f:
    datuak = json.load(f)
db.etxebizitzak.drop()
db.etxebizitzak.insert_many(datuak)
print(db.etxebizitzak.count_documents({}))  


garbiketa = [
    {"$project": {
        "_id": 0,
        "probintzia": "$Provincia",
        "udalerria": "$Municipio",
        "ingurunea": "$Modalidad",
        "plazak": {"$toInt": "$Capacidad"},
        "urtea": {"$toInt": {"$substr": ["$FechainscripcionREATE", 6, 4]}},
    }},
{"$out": "garbiak"},
]
db.etxebizitzak.aggregate(garbiketa)
print(db.garbiak.find_one())

def erakutsi(pipeline):
    for d in db.garbiak.aggregate(pipeline):
        print(d)
''''
erakutsi([
    {"$group": {"_id": "$probintzia", "kopurua": {"$sum": 1}}},
    {"$sort": {"kopurua": -1}},
])
print(" \n plazak probintzietan")
erakutsi([
    {"$group": {"_id": "$probintzia", "plazak": {"$sum": "$plazak"}}},
    {"$sort": {"plazak": -1}},
])

erakutsi([
    {"$group": {"_id": "$udalerria", "kopurua": {"$sum": 1}}},
    {"$sort": {"kopurua": -1}},
    {"$limit": 5},
])

erakutsi([
    {"$match": {"probintzia": "Bizkaia"}},
    {"$group": {"_id": "$udalerria", "kopurua": {"$sum": 1}}},
    {"$sort": {"kopurua": -1}},
    {"$limit": 5},
])

urteka = [
{"$group": {"_id": "$urtea", "kopurua": {"$sum": 1}}},
{"$sort": {"_id": 1}},
]
erakutsi(urteka)
'''

print(" \n 1")

#Zein dira gipuzkoan etxebizitza gehien dituzten 5 udalerriak
erakutsi([
    {"$match":{"probintzia":"Gipuzkoa"}},
    {"$group":{"_id": "$udalerria","kopurua":{"$sum":1}}},
    {"$sort":{"kopurua":-1}},
    {"$limit":5},
])
print(" \n 2")

#Zein da batez besteko plaza kopurua probintzia bakoitzean?
erakutsi([
    {"$group": {"_id": "$probintzia", "plazak": {"$avg": "$plazak"}}},
    {"$sort": {"plazak": -1}},
])

print(" \n 3")

#Zein 5 udalerrik dute plaza gehien?
erakutsi([
    {"$group":{"_id": "$udalerria","plazak":{"$sum":1}}},
    {"$sort":{"plazak": -1}},
    {"$limit":5},
])
#Zenbat etxebizitza inskribatu dira 2020tik aurrera, urteka?
print ("\n 4")
urteka = [
    {"$match": {"urtea": {"$gte": 2020}}},
    {"$group": {"_id": "$urtea", "kopurua": {"$sum": 1}}},
    {"$sort": {"_id": 1}},
]
erakutsi(urteka)

with open("urteka.csv", "w", encoding="utf-8-sig") as f:
    f.write("urtea;kopurua\n")
    for d in db.garbiak.aggregate(urteka):
        f.write(f"{d['_id']};{d['kopurua']}\n")

