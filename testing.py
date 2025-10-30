import shapely
from parametros import DEPOSITOS_PATH
from funciones import leer_cantidades_iniciales

a = shapely.Point(-70.3198296161068, -27.4172452730571)
b = shapely.Point(-70.3245208165072, -27.4166372115481)

print(shapely.distance(a, b) * 70.5550329)

KI = leer_cantidades_iniciales(DEPOSITOS_PATH)
