from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")

db = client["zinema"]
filmak = db["filmak"]

print(1, filmak.count_documents({}))
print(2, filmak.count_documents({"herrialdea": "Espainia"}))
print(3, filmak.count_documents({"hizkuntza": "euskara"}))
print(4, filmak.count_documents({"zuzendaria": "Miren Agirre"}))
print(5, filmak.count_documents({"herrialdea": "Japonia"}))
film = filmak.find_one({"izenburua": "Silent Harbor"})
print(6, film["iraupena"])