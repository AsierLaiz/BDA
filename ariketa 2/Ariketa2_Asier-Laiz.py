from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["liburutegia"]
liburuak = db["liburuak"]

print(liburuak.count_documents({})) 

#Bloke A
print("1",liburuak.count_documents({}))
print("2",liburuak.count_documents({"hizkuntza":"euskara"}))
print("3",liburuak.count_documents({"hizkuntza":"ingelesa"}))
print("4",liburuak.count_documents({"egilea":"Miren Etxeberria"}))
print("5",liburuak.count_documents({"argitaletxea":"Elkar"}))
itsaso = liburuak.find_one({"izenburua":"Itsaso Beltza"})
print("6",itsaso["orrialdeak"])
print("\n")
#Bloke B

print("7",liburuak.count_documents({"urtea":{"$gte":2010}}))
print("8",liburuak.count_documents({"orrialdeak":{"$gt":300}}))
print("9",liburuak.count_documents({"puntuazioa":{"$gte":8}}))
print("10",liburuak.count_documents({"urtea":{"$lt":2000}}))
print("11",liburuak.count_documents({"hizkuntza":{"$ne":"euskara"}}))
print("12",liburuak.count_documents({"maileguak":{"$gt":50}}))
print("\n")
#Bloke C
puntuazio_altuena= liburuak.find().sort("puntuazioa",-1).limit(1)
lehenengo_puntuazioa = list(puntuazio_altuena)[0]
print("13",lehenengo_puntuazioa["orrialdeak"])

zaharrena= liburuak.find().sort("urtea",1).limit(1)
lehena_zaharrena = list(zaharrena)[0]
print("14",lehena_zaharrena["orrialdeak"])

proiekzioa = list(liburuak.find({},{"_id":0,"izenburua":1,"urtea":1}))
print("15",len(proiekzioa))

argitaletxeak = liburuak.distinct("argitaletxea")
print("16", len(argitaletxeak))

print("\n")

#Bloke D
nire_liburuak = db["nire_liburuak"]

nire_liburuak.drop()

hiru_liburu = [
    {
        "izenburua": "Dune",
        "egilea": "Frank Herbert",
        "urtea": 1965,
        "orrialdeak": 704,
        "puntuazioa": 9,
    },
    {
        "izenburua": "La metamorfosis",
        "egilea": "Franz Kafka",
        "urtea": 1915,
        "orrialdeak": 128,
        "puntuazioa": 4,  # 5 baino gutxiago 20. ariketan ezabatzeko
    },
    {
        "izenburua": "El señor de los anillos",
        "egilea": "J.R.R. Tolkien",
        "urtea": 1954,
        "orrialdeak": 1200,
        "puntuazioa": 10,
    },
]

nire_liburuak.insert_many(hiru_liburu)
print("17",nire_liburuak.count_documents({}))

laugarren_liburua= {
    "izenburua": "1984",
    "egilea": "George Orwell",
    "urtea": 1949,
    "orrialdeak": 328,
    "puntuazioa": 10,
}

nire_liburuak.insert_one(laugarren_liburua)
print("18",nire_liburuak.count_documents({}))

update= nire_liburuak.update_one({"izenburua":"La metamorfosis"},{"$set":{"puntuazioa":5}})

print("19", update.modified_count)


behe_puntuazioa= list(nire_liburuak.find({"puntuazioa":{"$lt":5}}))
nire_liburuak.delete_many({"puntuazioa":{"$lt":5}})
print("20",nire_liburuak.count_documents({}))

print("\n")

# Bloke E

print("21", liburuak.count_documents({"hizkuntza":{"$in": ["euskara","ingelesa"]}}))

print("22", liburuak.count_documents({"generoak":"misterioa"}))

print("23", liburuak.count_documents({
    "$or": [
        {"urtea": { "$lt": 1990}},
        {"puntuazioa": { "$gt":8}}
    ]
}))

print("24", liburuak.count_documents({"izenburua":{"$regex":"^Z"}}))

# ============================================
# G GALDERA
# ============================================
#
# find()-ek dokumentuak ez ditu zuzenean itzultzen, emaitza asko egon daitezkeelako.
# Kurtsorea emaitzak banan-banan erakusteko eta zeharkatzeko erabiltzen den objektua da.
# Horrela, ez dira dokumentu guztiak memorian batera kargatu behar.
# Abantaila handia da bilduma oso handietan memoria gutxiago erabiltzen dela.
# Gainera, emaitzak behar diren heinean prozesatu daitezke.