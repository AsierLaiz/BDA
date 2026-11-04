import json
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client["turismoa"]



with open("alojamientos.json", encoding="utf-8") as f:
    ostatuak = json.load(f)
db.ostatuak.drop()
db.ostatuak.insert_many(ostatuak)
with open("mapa.csv", "w", encoding="utf-8-sig") as f:
    f.write("lon;lat\n")
    for d in db.ostatuak.find():
        lon = d["lonwgs84"].replace(".", ",") # 43.26 → 43,26
        lat = d["latwgs84"].replace(".", ",")
        f.write(f"{lon};{lat}\n")