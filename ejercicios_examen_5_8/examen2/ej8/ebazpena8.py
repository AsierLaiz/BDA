# EBAZPENA 8: LAN-ESKAINTZAK (ofertas de empleo; rangos de salario)
# Necesita lan_eskaintzak.json en la misma carpeta y MongoDB encendido.
import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["examen8"]


def csv_idatzi(fitxategia, lerroak):
    """; como separador y coma decimal, para que Excel en español lo abra bien."""
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        for lerroa in lerroak:
            f.write(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x)
                             for x in lerroa) + "\n")


# ============================================================
# 1. IMPORTAR (1 punto)
# ============================================================
with open("lan_eskaintzak.json", encoding="utf-8") as f:
    db.gordinak.drop()
    db.gordinak.insert_many(json.load(f))

print(db.gordinak.count_documents({}), "dokumentu")
print(db.gordinak.find_one())


# ============================================================
# 2. LIMPIAR (3 puntos)
# ============================================================
garbiak = []
for d in db.gordinak.find():
    soldata = d["soldata"].strip().lower()
    if "negoziagarria" in soldata:                     # sin cifra -> se descarta
        continue

    # "1.800 - 2.400 €/hilabete" (rango)  o  "1.500 €/hilabete" (un solo valor)
    zenbakiak = soldata.replace("€/hilabete", "").replace(".", "").split("-")
    gutxienekoa = int(zenbakiak[0].strip())
    gehienekoa = int(zenbakiak[-1].strip())            # con un solo valor, el último es el mismo

    esperientzia = d["esperientzia"].strip().lower()   # "Esperientziarik gabe" | "3 urte"
    if "gabe" in esperientzia:
        urteak = 0
    else:
        urteak = int(esperientzia.split()[0])          # "3 urte" -> "3" -> 3

    garbiak.append({
        "izena": d["izena"],
        "probintzia": d["probintzia"],
        "sektorea": d["sektorea"].strip().capitalize(),             # "TEKNOLOGIA " -> "Teknologia"
        "kontratua": d["kontratua"],
        "urrunekoa": d["urrunekoa"].strip().capitalize(),           # "bai" -> "Bai" ; "EZ" -> "Ez"
        "esperientzia": urteak,
        "gutxienekoa": gutxienekoa,
        "gehienekoa": gehienekoa,
        "batezbestekoa": (gutxienekoa + gehienekoa) / 2,            # salario medio del rango
    })

db.garbiak.drop()
db.garbiak.insert_many(garbiak)
print(len(garbiak), "garbi,", db.gordinak.count_documents({}) - len(garbiak), "deskartatuta")


# ============================================================
# 3. AZTERTU (3 puntos)
# ============================================================
# A) Salario medio por sector
A = [["sektorea", "batez besteko soldata (€)"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$sektorea", "media": {"$avg": "$batezbestekoa"}}},
    {"$sort": {"media": -1}},
]):
    A.append([d["_id"], round(d["media"])])

# B) Tipo de contrato y teletrabajo (contrato x urrunekoa)
kopuruak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"kontratua": "$kontratua", "urrunekoa": "$urrunekoa"}, "kopurua": {"$sum": 1}}},
]):
    kopuruak[(d["_id"]["kontratua"], d["_id"]["urrunekoa"])] = d["kopurua"]

URRUNEKOAK = ["Bai", "Hibridoa", "Ez"]
B = [["kontratua"] + URRUNEKOAK]
for k in ["Mugagabea", "Mugatua", "Praktikak"]:
    B.append([k] + [kopuruak.get((k, u), 0) for u in URRUNEKOAK])

# C) Las 10 ofertas con el salario máximo más alto
C = [["izena", "sektorea", "gehieneko soldata (€)"]]
for d in db.garbiak.aggregate([
    {"$sort": {"gehienekoa": -1}},
    {"$limit": 10},
]):
    C.append([d["izena"], d["sektorea"], d["gehienekoa"]])

# D) % de ofertas Bai / Hibridoa / Ez en cada provincia (100% apilado)
guztiak = {}
for d in db.garbiak.aggregate([
    {"$group": {"_id": {"probintzia": "$probintzia", "urrunekoa": "$urrunekoa"}, "kopurua": {"$sum": 1}}},
]):
    guztiak[(d["_id"]["probintzia"], d["_id"]["urrunekoa"])] = d["kopurua"]

D = [["probintzia"] + [u + " %" for u in URRUNEKOAK]]
for p in ["Araba", "Bizkaia", "Gipuzkoa"]:
    total = sum(guztiak.get((p, u), 0) for u in URRUNEKOAK)
    D.append([p] + [round(100 * guztiak.get((p, u), 0) / total, 1) if total else 0 for u in URRUNEKOAK])

# E) Años de experiencia vs salario medio de cada oferta
E = [["esperientzia (urteak)", "soldata (€)"]]
for d in db.garbiak.find():
    E.append([d["esperientzia"], d["batezbestekoa"]])


# ============================================================
# 4. AURKEZTU (3 puntos)
# ============================================================
csv_idatzi("taula_A_sektoreak.csv", A)      # columnas
csv_idatzi("taula_B_kontratuak.csv", B)     # columnas apiladas
csv_idatzi("taula_C_top10.csv", C)          # barras
csv_idatzi("taula_D_urrunekoa.csv", D)      # columnas apiladas 100 %
csv_idatzi("taula_E_dispertsioa.csv", E)    # dispersión
print("Listo: 5 CSV creados")
