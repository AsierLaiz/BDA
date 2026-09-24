from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")

db = client["zinema"]
filmak = db["filmak"]
nireak = db["nire_filmak"]
nireak.drop()


nireak.insert_many([ { "izenburua": "Alfa",  "urtea": 1999, "iraupena": 100, "puntuazioa": 6.0 },
  { "izenburua": "Beta",  "urtea": 2005, "iraupena": 120, "puntuazioa": 4.5 },
  { "izenburua": "Gamma", "urtea": 2012, "iraupena": 90,  "puntuazioa": 8.0 } ])

print(17 , nireak.count_documents({}))
nireak.insert_one({ "izenburua": "Delta", "urtea": 2020, "iraupena": 110, "puntuazioa": 3.5 })
print(18 , nireak.count_documents({}))
res= nireak.update_one({"izenburua": "Beta"}, {"$set": {"puntuazioa": 7.0}})
print(19 , res.modified_count)
for f in nireak.find({"puntuazioa": {"$lt": 5}}):
    print("5 baino gutxiagoko puntuazioa duten filmak:", f["izenburua"], f["puntuazioa"])
nireak.delete_many({"puntuazioa": {"$lt": 5}})
print (20, nireak.count_documents({}))