import os
import geopandas as gpd
from shapely.geometry import Point

DIR_PATH = os.getcwd()
DATA_PATH = os.path.join(DIR_PATH, 'data')
PUNTOS_PATH = os.path.join(DATA_PATH, 'conjunto-puntos.csv')
COMUNA_PATH = os.path.join(DATA_PATH, 'division-territorial', 'division-territorial.shp')  # para sacar su CRS
VECTOR_PATH = os.path.join(DATA_PATH, 'vector-layer', 'vector-layer.shp')


puntos = []
with open(PUNTOS_PATH, 'r', encoding='utf-8') as archivo:
    _ = next(archivo)
    for linea in archivo:
        punto = linea.strip().split(",")[:2]
        punto[0], punto[1] = float(punto[0]), float(punto[1])
        punto = Point(punto)
        puntos.append(punto)

print("Starting ...")
comuna_shape = gpd.read_file(COMUNA_PATH)
gdf = gpd.GeoDataFrame(geometry=puntos, crs=comuna_shape.crs)

gdf.to_file(VECTOR_PATH)
print("Done!")
