from gurobipy import Model, GRB, quicksum
import time
import itertools
from random import randint
import math
import pandas as pd
from funciones import leer_puntos, haversine
from parametros import PUNTOS_PATH, PUNTOS_SOL_PATH, PARAMETROS_PATH


# ------- iniciar modelo -------
inicio = time.time()
md = Model()

# -------   conjuntos    -------
puntos, P, U, D, A = leer_puntos(PUNTOS_PATH)

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
parametros_archivo = pd.read_csv(PARAMETROS_PATH)
parametros = {
    col: [float(x) for x in parametros_archivo[col].to_list() if not (pd.isna(x) or (isinstance(x, float) and math.isnan(x)))]
    for col in parametros_archivo.columns
}

T = parametros['Tp (ton)'] + [randint(108_735, 21_244_362) for _ in range(len(P) - len(D))]
CT = parametros['CTd (USD/km)'][0]
CF = parametros['CFdf (USD/ton)']
CS = parametros['CSd  (USD)'][0]
# para ahorrar runtime (no es una variable, siempre va a ser igual para el mismo p, pp)
L = lambda p, pp: haversine(puntos[p], puntos[pp])
KI = parametros['Klp (ton)'] + [0 for _ in range(len(P) - len(D))]  # 0 tons para cada posición nueva
MCNTU = parametros['MCNTu (µg/m3)'][0]
MCNTA = parametros['MCNTa (mg/l)'][0]
CNT = parametros['CNT (µg/m3)'][0]
ALPHA = parametros['alpha'][0]
BETA = parametros['beta f']
DM = parametros['DM (km)'][0]  # en kilometros, distancia entre relaves
# conversion: 1.5 km = 0.02126° (latitud, longitud) ; 1° = 70.5550329 km
LAMBDA = parametros['lambda k']
PS = parametros['PS (USD)'][0]
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
W = md.addVars(p_pp, vtype=GRB.CONTINUOUS, lb=0, name="W")
K = md.addVars(P, vtype=GRB.CONTINUOUS, lb=0, name="K")
C = md.addVars(P, lb=-GRB.INFINITY, ub=GRB.INFINITY, name="C")
Z = md.addVars(P, vtype=GRB.CONTINUOUS, lb=0, name="Z")
ZV = md.addVars(P, vtype=GRB.CONTINUOUS, lb=0, name="ZV")
KA = md.addVars(pf, vtype=GRB.CONTINUOUS, lb=0, name="KA")
Y = md.addVars(P, vtype=GRB.BINARY, name="Y")  # NEW, HAY RELAVE EN LA POSICIÓN P

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
md.addConstrs(M * Y[p] >= quicksum(XT[p, pp] for pp in P) for p in P)  # NEW
md.addConstrs(M * Y[p] >= 1 - XTR[p] for p in D)  # NEW, si no se ha transladado nada en d entonces es un relave (Y = 1)
md.addConstrs(quicksum(XT[p, pp] for pp in P) <= 1 for p in P)  # NEW, se puede transladar a lo más a 1 lugar
print("- Restricciones de variables: Done")

# restricciones de presupuesto
print("- Restricciones de presupuesto")
md.addConstrs(KA[p, f] <= M * XF[p, f] for p in D for f in F)
md.addConstrs(KA[p, f] <= K[p] for p in D for f in F)
md.addConstrs(KA[p, f] >= K[p] - M * (1 - XF[p, f]) for p in D for f in F)
md.addConstr(quicksum(quicksum(L(p, pp) * CT * XT[p, pp] for pp in P) + quicksum(KA[p, f] * CF[f] for f in F) + XS[p] * CS for p in P) <= PS)
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
md.addConstrs(quicksum(ZV[p] / L(p, u) for p in P if p != u) <= MCNTU for u in U)
md.addConstrs(quicksum(ZV[p] / L(p, a) for p in P if p != a) <= MCNTA for a in A)
md.addConstrs(MCNTU - quicksum(ZV[p] / L(p, u) for p in P if p != u) == C[u] for u in U)
md.addConstrs(MCNTA - quicksum(ZV[p] / L(p, a) for p in P if p != a) == C[a] for a in A)
md.addConstrs(C[p] == 0 for p in P if p not in (U + A))
print("- Restricciones de contaminación: Done")

# restricciones de distancia
print("- Restricciones de distancia")
md.addConstrs(L(p, pp) + M * (1 - Y[p]) >= DM for p in P for pp in P if p != pp)  # NEW
md.addConstrs(L(p, u) + M * (1 - Y[p]) >= DM for p in P for u in U)  # NEW
md.addConstrs(K[u] == 0 for u in U)
print("- Restricciones de distancia: Done")
print(f"Done in {round(time.time() - comienzo)}s")


md.update()

# -------  función obj  -------
print("Agregando función objetivo...")
md.setObjective(quicksum(LAMBDA[0] * quicksum(XF[p, f] for f in F) + LAMBDA[1] * XS[p] + LAMBDA[2] * C[p] for p in P), GRB.MAXIMIZE)
print("Optimizando...")

md.optimize()
print(f"Tiempo total: {round(time.time() - inicio)}s")

# ------   resultados   ------
valor_objetivo = md.ObjVal
tiempo_ejecucion = md.Runtime

print(f"El beneficio social alcanzado fue de {valor_objetivo}")

with open(PUNTOS_SOL_PATH, 'w', encoding='utf-8') as archivo:
    print("longitud,latitud,medida", file=archivo)  # header
    for p in P:
        hizo_algo = False
        if K[p].x != 0:
            print(f"En la posición {p} hay {K[p].x} toneladas de relave")

        for pp in P:
            if XT[p, pp].x == 1:
                hizo_algo = True
                print(f"El depósito en la posición {p} se movió a {pp}")
                print(f"{puntos[pp].x},{puntos[pp].y},T", file=archivo)

        for f in F:
            if XF[p, f].x == 1:
                hizo_algo = True
                print(f"Se aplicó el método {f} al depósito de relave en la posición {p}")
                print(f"{puntos[p].x},{puntos[p].y},F{f}", file=archivo)

        if XS[p].x == 1:
            hizo_algo = True
            print(f"Se selló el depósito en {p}")
            print(f"{puntos[p].x},{puntos[p].y},S", file=archivo)

        if not hizo_algo and p in D:
            print(f"La posición {p} se mantuvo en el mismo lugar")
            print(f"{puntos[p].x},{puntos[p].y},M", file=archivo)
