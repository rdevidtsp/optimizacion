from gurobipy import Model, GRB, quicksum
import time
import itertools
import numpy as np
from random import randint
from funciones import leer_puntos, leer_cantidades_iniciales, haversine
from parametros import PUNTOS_PATH, DEPOSITOS_PATH


# ------- iniciar modelo -------
inicio = time.time()
md = Model()

# -------   conjuntos    -------
puntos, P, U, D, A = leer_puntos(PUNTOS_PATH)

testing = False
if testing:
    from shapely.geometry import Point
    puntos = [Point(-27.038327, -69.736009), Point(-27.55184, -70.51589), Point(-27.387969, -70.341310), Point(-26.93326, -69.09210)]
    P = [i for i in range(4)]
    U = [1]
    D = [2]
    A = [3]
print(f"Len puntos: {len(puntos)}")
print(f"- Zonas urbanas: {len(U)}, - Depósitos de relave: {len(D)}, - Fuentes de agua: {len(A)}")

"""
Los conjuntos P, U, D, A son:
P: conjunto de posibles de depósitos de relave, zonas urbanas, entre otros.
U: subconjunto de zonas urbanas.
D: subconjunto de posiciones de depósitos de relaves iniciales.
A: subconjunto de posiciones de fuentes de agua
F: conjunto de estrategias de fitorremediación aplicables
Las variables posP, posU, ... contienen las posiciones de las coordenadas
dentro de la lista "puntos".
"""
# 0: fitoextraccion, 1: fitoestabilizacion, 2: rizorremediacion
F = [i for i in range(3)]

# -------   parametros   -------

# https://chatgpt.com/share/6902e76e-25c8-8003-bca3-a897298d21ce
T = np.array([randint(27, 21_244_362) for _ in P])
# de excel con depositos: =MAX(IF((V8:V843<>0) * (Q8:Q843={"INACTIVO","ABANDONADO"}) * (G8:G843="COPIAPO"), V8:V843))
# https://www.researchgate.net/figure/Tonnage-amount-of-tailings-stored-in-large-tailings-storage-facilities-per-region-in_fig12_364310393
CT = np.array([randint(200, 1000) for _ in P])
# https://www.subtrans.gob.cl/wp-content/uploads/2020/09/Actualizacio%CC%81n-de-Modelo-de-Costos-de-Transporte-de-Carga-para-el-Ana%CC%81lisis-de-Costos-Logi%CC%81sticos-del-Observatorio-Logi%CC%81stico.pdf
CF = [
    [randint(5, 50) for _ in P],
    [randint(25, 200) for _ in P],
    [randint(200, 800) for _ in P],
]
# https://www.mdpi.com/2071-1050/17/13/5688
CS = np.array([randint(10_000, 100_000_000) for _ in P])
# https://dnr.alaska.gov/mlw/mining/large-mines/pdf/rcindirects_dowlreport20150407.pdf
# Mapeo todas las distancias entre puntos (oh boy)
L = {(p, pp): haversine(puntos[p], puntos[pp]) for p in P for pp in P}
KI = leer_cantidades_iniciales(DEPOSITOS_PATH) + [0 for _ in range(len(P) - len(D))]  # 0 tons para cada posición nueva
MCNTU = {u: randint(90, 100) for u in U}
MCNTA = {a: randint(50, 90) for a in A}
CNT = 0.02
ALPHA = 0.2  # 0.2 de la cantidad percibida original
BETA = np.array([0.2, 0.6, 0.3])
DM = 1.5  # en kilometros
# conversion: 1.5 km = 0.02126° (latitud, longitud) ; 1° = 70.5550329 km
PS = 50_000_000
LAMBDA = np.array([0.35, 0.35, 0.30])
# big numba
M = PS

# -------   variables    -------
print("Creando variables...")
comienzo = time.time()
p_pp = list(itertools.product(P, P))
pf = list(itertools.product(P, F))

XT = md.addVars(p_pp, vtype=GRB.BINARY, name="XT")
XTR = md.addVars(P, vtype=GRB.BINARY, name="XTR")
XF = md.addVars(pf, vtype=GRB.BINARY, name="XF")
XS = md.addVars(P, vtype=GRB.BINARY, name="XS")
W = md.addVars(p_pp, vtype=GRB.CONTINUOUS, name="W")
K = md.addVars(P, vtype=GRB.CONTINUOUS, name="K")
C = md.addVars(P, vtype=GRB.CONTINUOUS, name="C")
Z = md.addVars(P, vtype=GRB.CONTINUOUS, name="Z")
ZV = md.addVars(P, vtype=GRB.CONTINUOUS, name="ZV")
KA = md.addVars(pf, vtype=GRB.CONTINUOUS, name="KA")

print(f"Done in {round(time.time() - comienzo)}s")

# -------  restricciones -------
print("Aplicando restricciones...")
comienzo = time.time()
# restricciones de variables
print("- Restricciones de variables")
md.addConstrs(XTR[p] + quicksum(XF[p, f] for f in F) + XS[p] <= 1 for p in D)
md.addConstrs(XTR[p] + quicksum(XF[p, f] for f in F) + XS[p] == 0 for p in P if p not in D)
md.addConstrs(quicksum(XT[p, pp] for pp in P) <= M * XTR[p] for p in P)
md.addConstrs(W[p, pp] <= M * XT[p, pp] for p in P for pp in P if p != pp)
md.addConstrs(M * (1 - (XTR[p] + quicksum(XF[p, f] for f in F) + XS[p])) >= quicksum(XT[pp, p] for pp in P) for p in P)
print("- Restricciones de variables: Done")
# restricciones de presupuesto
print("- Restricciones de presupuesto")
md.addConstrs(KA[p, f] <= M * XF[p, f] for p in D for f in F)
md.addConstrs(KA[p, f] <= K[p] for p in D for f in F)
md.addConstrs(KA[p, f] >= K[p] - M * (1 - XF[p, f]) for p in D for f in F)
md.addConstr(quicksum(quicksum(W[p, pp] * L[p, pp] for pp in P) * CT[p] + quicksum(KA[p, f] * CF[f][p] for f in F) + XS[p] * CS[p] for p in P) <= PS)
md.addConstrs(K[p] == KI[p] + quicksum(W[i, p] for i in P) - quicksum(W[p, j] for j in P) for p in P)
md.addConstrs(K[p] <= T[p] for p in P)
print("- Restricciones de presupuesto: Done")
# restricciones de contaminación
print("- Restricciones de contaminación")
md.addConstrs(Z[p] == K[p] * CNT for p in P)
md.addConstrs(ZV[p] - ALPHA * Z[p] <= M * (1 - XS[p]) for p in P)
md.addConstrs(ZV[p] - ALPHA * Z[p] >= -M * (1 - XS[p]) for p in P)
md.addConstrs(ZV[p] - BETA[f] * Z[p] <= M * (1 - XF[p, f]) for p in P for f in F)
md.addConstrs(ZV[p] - BETA[f] * Z[p] >= -M * (1 - XF[p, f]) for p in P for f in F)
md.addConstrs(ZV[p] - Z[p] <= M * (quicksum(XF[p, f] for f in F) + XS[p]) for p in P)
md.addConstrs(ZV[p] - Z[p] >= -M * (quicksum(XF[p, f] for f in F) + XS[p]) for p in P)
md.addConstrs(quicksum(ZV[p] / L[p, u] for p in P if p != u) <= MCNTU[u] for u in U)
md.addConstrs(quicksum(ZV[p] / L[p, a] for p in P if p != a) <= MCNTA[a] for a in A)
md.addConstrs(MCNTU[u] - quicksum(ZV[p] / L[p, u] for p in P if p != u) == C[u] for u in U)
md.addConstrs(MCNTA[a] - quicksum(ZV[p] / L[p, a] for p in P if p != a) == C[a] for a in A)
md.addConstrs(C[p] == 0 for p in P if p not in (U + A))
print("- Restricciones de contaminación: Done")
# restricciones de distancia
print("- Restricciones de distancia")
md.addConstrs(L[p, pp] + M * (1 - XT[p, pp]) >= DM for p in P for pp in P if p != pp)
md.addConstrs(L[pp, u] + M * (1 - XT[p, pp]) >= DM for p in P for pp in P if p != pp for u in U)
md.addConstrs(K[u] == 0 for u in U)
print("- Restricciones de distancia: Done")
print(f"Done in {round(time.time() - comienzo)}s")

md.update()

# -------  función obj  -------
print("Agregando función objetivo...")
md.setObjective(quicksum(LAMBDA[0] * quicksum(XF[p, f] for f in F) + LAMBDA[1] * XS[p] + LAMBDA[2] * C[p] for p in P), GRB.MAXIMIZE)
print("Optimizando...")
md.optimize()
print(f"Tiempo total: {round(time.time() - inicio)}")

# ------   resultados   ------
valor_objetivo = md.ObjVal
tiempo_ejecucion = md.Runtime

for p in D:
    for pp in P:
        if XT[p, pp].x == 1:
            print(f"El depósito en la posición {p} se movió a {pp}")

    for f in F:
        if XF[p, f].x == 1:
            print(f"Se aplicó el método {f} al depósito de relave en la posición {p}")

    if XS[p].x == 1:
        print(f"Se selló el depósito en {p}")
