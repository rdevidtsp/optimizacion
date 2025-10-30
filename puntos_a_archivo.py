import time
from funciones import generar_puntos, leer_depositos
from parametros import (
    PARQUE_PATH, AGUA_PATH, PUNTOS_PATH, COMUNA_PATH, URBANO_PATH, DEPOSITOS_PATH, GRID_TILES_AVG
)

print("Cargando las posiciones de los depósitos antiguos")
D = leer_depositos(DEPOSITOS_PATH)
print("Done!")

# conjunto de todas las posiciones, zonas urbanas y fuentes de agua
print("Cargando todos los conjuntos a partir de shapefiles")

P, U, A = generar_puntos(COMUNA_PATH, URBANO_PATH, PARQUE_PATH, AGUA_PATH, D, GRID_TILES_AVG)
print(f"Cantidad de puntos: {len(P)}")
print(f"Cantidad de zonas urbanas: {len(U)}")
print(f"Cantidad de fuentes de agua: {len(A)}")

print("Escribiendo en archivo...")
comienzo = time.time()
with open(PUNTOS_PATH, 'w', encoding='utf-8') as archivo:
    print("longitud,latitud,tipo", file=archivo)  # header

    for i, punto in enumerate(P):
        if i % 1000 == 0:
            print(f"{i} puntos escritos...")
        tipo = 'P'
        if punto in U:
            tipo += ';U'
        if punto in A:
            tipo += ';A'
        if punto in D:
            tipo += ';D'
        print(f'{punto.x},{punto.y},{tipo}', file=archivo)
print(f"Done in {round(time.time() - comienzo, 1)}s")
