import csv
import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["proba3"]

with open("herriak.json", encoding="utf-8") as f:
    herriak= json.load(f)
db.herriak.drop()
db.herriak.insert_many(herriak)


with open("museoak.json", encoding="utf-8") as f:
    museoak= json.load(f)
db.museoak.drop()
db.museoak.insert_many(museoak)

def garbitu(izena):
    return(izena or "").lower().strip()

herriak = {}
for h in db.herriak.find():
    zona = "kostaldea" if h["kostaldea"] == "Bai" else "barnealdea"
    herriak[garbitu(h["udalerria"])] = (h["probintzia"], zona)

for m in list(db.museoak.find()):
    probintzia, zona = herriak.get(garbitu(m["udalerria"]), (None, None))
    db.museoak.update_one({"_id": m["_id"]}, {"$set": {"probintzia": probintzia, "zona": zona}})
