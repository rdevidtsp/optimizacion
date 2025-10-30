import geopandas as gpd
from shapely.geometry import Point
from shapely import distance
import time
from parametros import GRADOS_A_KM


def leer_depositos(path):
    puntos = []
    with open(path, 'r', encoding='utf-8') as archivo:
        _ = next(archivo)  # sacar primera linea
        for linea in archivo:
            coords = linea.strip().split(",")[20:22][::-1]
            punto = Point(float(coords[0]), float(coords[1]))
            puntos.append(punto)
    return puntos


def generar_puntos(comuna_path, urbano_path, parque_path, agua_path, depositos, grid_tiles):
    comienzo = time.time()
    comuna_shape = gpd.read_file(comuna_path)
    urbano_shape = gpd.read_file(urbano_path)
    parque_shapes = gpd.read_file(parque_path)
    agua_shapes = gpd.read_file(agua_path)
    urbano_shape = urbano_shape.to_crs(comuna_shape.crs)  # mismo coordinate system

    bounds = comuna_shape.total_bounds
    min_x, min_y, max_x, max_y = bounds

    dist_x = max_x - min_x
    dist_y = max_y - min_y
    distance = (dist_x / grid_tiles + dist_y / grid_tiles) / 2

    puntos = [*depositos]
    zonas_urbanas = []
    fuentes_agua = []

    # comenzar desde abajo a la izquierda pero no en el borde
    current_point = Point(min_x + distance, min_y + distance)

    i = 0
    total_i = dist_y // distance - 1
    while min_x < current_point.x < max_x and min_y < current_point.y < max_y:
        if comuna_shape.contains(current_point).bool():
            puntos.append(current_point)
        if (urbano_shape.contains(current_point).bool() or
                any([parque.contains(current_point) for parque in parque_shapes.geometry])):
            zonas_urbanas.append(current_point)
        if any([agua.contains(current_point) for agua in agua_shapes.geometry]):
            fuentes_agua.append(current_point)

        new_x = current_point.x + distance
        new_y = current_point.y
        if new_x > max_x:
            print(f"{round(i / total_i * 100, 2)}%")
            new_x = min_x + distance
            new_y = current_point.y + distance
            i += 1
        current_point = Point(new_x, new_y)

    print(f"Done in {round(time.time() - comienzo, 1)}s!")
    return puntos, zonas_urbanas, fuentes_agua


def leer_puntos(puntos_path):
    puntos = []
    P, U, D, A = ([] for _ in range(4))
    with open(puntos_path, 'r', encoding='utf-8') as archivo:
        _ = next(archivo)
        for i, linea in enumerate(archivo):
            punto = linea.strip().split(',')
            punto[0], punto[1] = float(punto[0]), float(punto[1])
            punto[2] = punto[2].split(';')
            punto_coords = Point(punto[:2])
            puntos.append(punto_coords)
            for tipo in punto[2]:
                if tipo in 'PUDA':
                    [P, U, D, A]['PUDA'.index(tipo)].append(i)
    return puntos, P, U, D, A


def leer_cantidades_iniciales(path):
    cantidades = []
    with open(path, 'r', encoding='utf-8') as archivo:
        _ = next(archivo)  # sacar primera linea
        for linea in archivo:
            cantidad = linea.strip().split(",")[27]
            if cantidad == '':
                cantidad = 0
            else:
                cantidad = int(cantidad)
            cantidades.append(cantidad)
    return cantidades


def distancia_puntos(coords1, coords2):
    p1, p2 = Point(coords1), Point(coords2)
    return distance(p1, p2) * GRADOS_A_KM
