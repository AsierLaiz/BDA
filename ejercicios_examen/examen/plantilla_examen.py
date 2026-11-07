# PLANTILLA PARA EL EXAMEN: copia esto y rellena los huecos (ZUZENDU = cambia esto)
import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["examena"]


def csv_idatzi(fitxategia, lerroak):
    """; como separador y coma decimal, para que Excel en español lo abra bien."""
    with open(fitxategia, "w", encoding="utf-8-sig", newline="") as f:
        for lerroa in lerroak:
            f.write(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x)
                             for x in lerroa) + "\n")


# ============================================================
# 1. IMPORTAR (1 punto)
# ============================================================
with open("ZUZENDU.json", encoding="utf-8") as f:
    db.gordinak.drop()
    db.gordinak.insert_many(json.load(f))
print(db.gordinak.count_documents({}))
print(db.gordinak.find_one())               # ¡mira los campos antes de seguir!


# ============================================================
# 2. LIMPIAR (3 puntos): gordinak -> garbiak
# ============================================================
garbiak = []
ikusiak = set()                              # solo si hay que quitar duplicados
for d in db.gordinak.find():
    # a) descartar lo que no sirve (vacíos, duplicados, años o valores malos)
    if not d.get("ZUZENDU"):
        continue
    # b) construir el documento limpio
    garbiak.append({
        "ZUZENDU": d["ZUZENDU"].strip().lower(),                  # texto: strip / lower / title
        "ZUZENDU2": float(d["ZUZENDU2"].replace(",", ".")),       # número con coma decimal
    })
db.garbiak.drop()
db.garbiak.insert_many(garbiak)
print(len(garbiak), "garbi")


# ============================================================
# 3. AZTERTU (3 puntos): consultas -> listas de filas (con títulos en la primera)
# ============================================================
A = [["ZUZENDU", "kopurua"]]
for d in db.garbiak.aggregate([
    {"$group": {"_id": "$ZUZENDU", "kopurua": {"$sum": 1}}},
    {"$sort": {"kopurua": -1}},
]):
    A.append([d["_id"], d["kopurua"]])


# ============================================================
# 4. AURKEZTU (3 puntos): CSV -> abrir en Excel -> gráficos
# ============================================================
csv_idatzi("taula_A.csv", A)
print("Listo")
