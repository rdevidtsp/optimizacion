import geopandas as gpd
from shapely.geometry import Point
from parametros import (
    PUNTOS_PATH, COMUNA_PATH, VECTOR_PATH, VECTOR_SOL_PATH,
    PUNTOS_SOL_PATH
)
from collections import defaultdict


def puntos_grid_a_vector(path, output_path, shapefile_crs_path):
    puntos = []
    print("Reading...")
    with open(path, 'r', encoding='utf-8') as archivo:
        _ = next(archivo)
        for linea in archivo:
            punto = linea.strip().split(",")[:2]
            punto[0], punto[1] = float(punto[0]), float(punto[1])
            punto = Point(punto)
            puntos.append(punto)
    print("Done!")

    print("Converting to .shp ...")
    comuna_shape = gpd.read_file(shapefile_crs_path)
    gdf = gpd.GeoDataFrame(geometry=puntos, crs=comuna_shape.crs)
    gdf.to_file(output_path)
    print("Done!")


def solucion_a_vector(path, output_path, shapefile_crs_path):
    puntos = defaultdict(list)
    print("Reading...")
    with open(path, 'r', encoding='utf-8') as archivo:
        _ = next(archivo)
        for linea in archivo:
            punto = linea.strip().split(',')
            punto[0], punto[1] = float(punto[0]), float(punto[1])
            coords = Point(punto[0], punto[1])
            puntos[punto[2]].append(coords)
    print("Done!")

    print("Converting to .shp ...")
    comuna_shape = gpd.read_file(shapefile_crs_path)
    for medida, puntos_medida in puntos.items():
        # not too sure q hace esto
        gdf = gpd.GeoDataFrame({'medida': [medida]*len(puntos_medida)}, geometry=puntos_medida, crs=comuna_shape.crs)
        gdf.to_file(output_path, layer=medida, driver='GPKG')
    print("Done!")


if __name__ == '__main__':
    generar_grid = True
    generar_sol = True

    if generar_grid:
        puntos_grid_a_vector(PUNTOS_PATH, VECTOR_PATH, COMUNA_PATH)

    if generar_sol:
        solucion_a_vector(PUNTOS_SOL_PATH, VECTOR_SOL_PATH, COMUNA_PATH)
