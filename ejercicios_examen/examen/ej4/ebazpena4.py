# EBAZPENA 4: SALMENTAK (ventas de una tienda: fechas y precios en formato europeo)
# Necesita salmentak.json en la misma carpeta y MongoDB encendido.
import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["examen4"]


def csv_idatzi(fitxategia, lerroak):
    """; como separador y coma decimal, para que Excel en español lo abra bien."""
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        for lerroa in lerroak:
            f.write(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x)
                             for x in lerroa) + "\n")


def prezioa_zenbaki(testua):
    """'1.250,50 €' -> 1250.5 | '12,50 €' -> 12.5  (se quita el punto de miles y la coma pasa a punto)"""
    return float(testua.replace("€", "").replace(".", "").replace(",", ".").strip())


# ============================================================
# 1. IMPORTAR (1 punto)
# ============================================================
with open("salmentak.json", encoding="utf-8") as f:
    db.gordinak.drop()
    db.gordinak.insert_many(json.load(f))

print(db.gordinak.count_documents({}), "dokumentu")
print(db.gordinak.find_one())


# ============================================================
# 2. LIMPIAR (3 puntos)
# ============================================================
garbiak = []
for d in db.gordinak.find():
    data = d["data"]                              # formato dd/mm/aaaa
    if data[6:10] != "2024":                      # sin fecha o de otro año -> se descarta
        continue
    kopurua = int(d["kopurua"])
    if kopurua <= 0:                              # devoluciones o errores -> se descarta
        continue

    prezioa = prezioa_zenbaki(d["prezioa"])
    garbiak.append({
        "hilabetea": int(data[3:5]),              # "13/07/2024" -> 7
        "produktua": d["produktua"],
        "kategoria": d["kategoria"].strip().capitalize(),       # "ARROPA" -> "Arropa"
        "kopurua": kopurua,
        "prezioa": prezioa,
        "guztira": round(kopurua * prezioa, 2),               # importe de la venta
        "herria": d["herria"],
        "ordainketa": d["ordainketa"].strip().capitalize(),     # "TXARTELA" -> "Txartela"
    })

db.garbiak.drop()
db.garbiak.insert_many(garbiak)
print(len(garbiak), "garbi,", db.gordinak.count_documents({}) - len(garbiak), "deskartatuta")


# ============================================================
# 3. AZTERTU (3 puntos)
# ============================================================
# A) Ventas totales de cada mes (meses sin ventas = 0)
hilabeteak = {d["_id"]: d["guztira"] for d in db.garbiak.aggregate([
    {"$group": {"_id": "$hilabetea", "guztira": {"$sum": "$guztira"}}},
])}
A = [["hilabetea", "salmentak (€)"]]
for h in range(1, 13):
    A.append([h, round(hilabeteak.get(h , 0), 2)])

# B) Ventas por categoría
B = [["kategoria", "salmentak (€)"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$kategoria", "guztira": {"$sum": "$guztira"}}},
    {"$sort": {"guztira": -1}},
]):
    B.append([d["_id"], round(d["guztira"], 2)])

# C) Número de ventas por forma de pago en cada categoría
kopuruak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"kategoria": "$kategoria", "ordainketa": "$ordainketa"}, "kopurua": {"$sum": 1}}},
]):
    kopuruak[(d["_id"]["kategoria"], d["_id"]["ordainketa"])] = d["kopurua"]

ordainketak = sorted({o for (k, o) in kopuruak})
kategoriak = sorted({k for (k, o) in kopuruak})
C = [["kategoria"] + ordainketak]
for k in kategoriak:
    C.append([k] + [kopuruak.get((k, o), 0) for o in ordainketak])

# D) Los 5 productos que más ingresan
D = [["produktua", "salmentak (€)"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$produktua", "guztira": {"$sum": "$guztira"}}},
    {"$sort": {"guztira": -1}},
    {"$limit": 5},
]):
    D.append([d["_id"], round(d["guztira"], 2)])

# E) Importe medio de una venta en cada pueblo
E = [["herria", "batez besteko salmenta (€)"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$herria", "media": {"$avg": "$guztira"}}},
    {"$sort": {"media": -1}},
]):
    E.append([d["_id"], round(d["media"], 2)])


# ============================================================
# 4. AURKEZTU (3 puntos)
# ============================================================
csv_idatzi("taula_A_hilabeteak.csv", A)     # líneas
csv_idatzi("taula_B_kategoriak.csv", B)     # sectores (tarta) o columnas
csv_idatzi("taula_C_ordainketak.csv", C)    # columnas apiladas
csv_idatzi("taula_D_top5.csv", D)           # barras
csv_idatzi("taula_E_herriak.csv", E)        # columnas
print("Listo: 5 CSV creados")
