from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")

db = client["zinema"]
filmak = db["filmak"]

onena = filmak.find().sort("puntuazioa", -1).limit(1)[0]
print(13, onena["iraupena"])
zaaharrena = filmak.find().sort("urte", 1).limit(1)[0]
print(14, zaaharrena["iraupena"])
emaitza = list(filmak.find({}, {"_id": 0, "izenburua": 1, "urtea": 1}))
print(15, len(emaitza))

print(16, len(filmak.distinct("herrialdea")))