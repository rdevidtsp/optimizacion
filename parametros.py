import os


DIR_PATH = os.getcwd()
DATA_PATH = os.path.join(DIR_PATH, 'data')
COMUNA_PATH = os.path.join(DATA_PATH, 'division-territorial', 'division-territorial.shp')
URBANO_PATH = os.path.join(DATA_PATH, 'zona-urbana', 'zona-urbana.shp')
PARQUE_PATH = os.path.join(DATA_PATH, 'zona-urbana-parque', 'zona-urbana-parque.shp')
DEPOSITOS_PATH = os.path.join(DATA_PATH, 'depositos.csv')
AGUA_PATH = os.path.join(DATA_PATH, 'fuentes-agua', 'fuentes-agua.shp')

PUNTOS_PATH = os.path.join(DATA_PATH, 'puntos-grid', 'conjunto-puntos.csv')
PUNTOS_SOL_PATH = os.path.join(DATA_PATH, 'puntos-solucion', 'conjunto-puntos.csv')

VECTOR_PATH = os.path.join(DATA_PATH, 'vector-layer', 'vector-layer.shp')
VECTOR_SOL_PATH = os.path.join(DATA_PATH, 'vector-layer-sol', 'vector-layer.gpkg')

PARAMETROS_PATH = os.path.join(DATA_PATH, 'parametros.csv')
# usado para separar los grids una cierta cantidad (higher = closer points)
GRID_TILES_AVG = 50

DEBUG = True
