from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")

db = client["zinema"]
filmak = db["filmak"]

print(7, filmak.count_documents({"urte": {"$gte": 2010}}))
print(7, filmak.count_documents({"iraupena": {"$gt": 120}}))
print(7, filmak.count_documents({"puntuazioa": {"$gte": 8}}))
print(7, filmak.count_documents({"hizkuntza": {"$ne": "ingelesa"}}))