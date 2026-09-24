from pymongo import MongoClient
# 1. Zerbitzarira konektatu
client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
# 2. Erantzuten duela egiaztatu
print("MongoDB bertsioa:", client.server_info()["version"])
# 3. Datu-basea eta bilduma aukeratu ("use zinema"-ren baliokidea)
db = client["zinema"]
filmak = db["filmak"]
# 4. Lehen kontsulta
print("Bildumak:", db.list_collection_names())
print("Film kopurua:", filmak.count_documents({}))