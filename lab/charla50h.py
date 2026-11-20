"""CHARLA 50 H: referencia de la ronda 2.13 (matemáticas deterministas por aplicaciones, problemas de enunciado,
suposiciones con comparación y órdenes de dibujar). Escrita con la 2.12 congelada; no se lee hasta la medida final."""
from lab.banco import correr, imprime
D = [
 {"id": "ch50h-a", "cat": "aritmetica", "turnos": [
   ("hola", "hola"), ("¿cuánto es 2 más 5?", "7;!no lo s*"), ("cuánto es el resultado de la suma entre 230 y 420", "650"),
   ("¿y si le resto 50?", "600"), ("¿cuánto es 12 por 15?", "180"), ("divide 144 entre 12", "12"), ("¿cuál es la raíz cuadrada de 225?", "15"),
   ("¿cuánto es el 15 % de 80?", "12"), ("calcula 3 más 4 por 5", "23"), ("¿cuánto es (3 más 4) por 5?", "35")]},
 {"id": "ch50h-b", "cat": "formatos", "turnos": [
   ("¿cuánto es doscientos treinta más ciento veinte?", "350"), ("¿cuánto es el doble de 37?", "74"), ("¿y la mitad de 90?", "45"),
   ("¿cuánto es 7 al cuadrado?", "49"), ("¿cuánto es 2 elevado a 10?", "1024|1.024"), ("¿cuál es la media de 4, 8 y 12?", "8"),
   ("¿cuánto es 10 entre 4?", "2,5|2.5"), ("¿cuánto es 5 menos 9?", "-4|−4|menos 4"), ("¿cuánto es 1 entre 0?", "ABST|cero"),
   ("¿cuánto es 3,5 más 1,25?", "4,75|4.75")]},
 {"id": "ch50h-c", "cat": "problemas", "turnos": [
   ("tengo 12 caramelos y me dan 5 más, ¿cuántos caramelos tengo?", "17"), ("Ana tenía 30 euros y se gastó 12, ¿cuánto dinero le queda?", "18"),
   ("en una caja hay 6 filas de 8 huevos, ¿cuántos huevos hay?", "48"), ("repartimos 45 cromos entre 5 niños, ¿cuántos le tocan a cada uno?", "9"),
   ("un tren sale con 120 pasajeros, bajan 35 y suben 20, ¿cuántos pasajeros lleva?", "105"),
   ("tengo 3 hermanos y 2 hermanas", "hermanos|hermanas;!no lo he entendido"), ("¿cuántos hermanos tengo en total?", "5|cinco"),
   ("una camiseta cuesta 15 euros, ¿cuánto cuestan 4 camisetas?", "60"), ("si un kilo de manzanas cuesta 2 euros, ¿cuánto cuestan 3 kilos?", "6"),
   ("¿cómo lo has calculado?", "multiplic*|por|×|aplicacion")]},
 {"id": "ch50h-d", "cat": "suposiciones", "turnos": [
   ("si un conejo es más grande que una liebre, ¿la liebre será más pequeña o más grande que el conejo?", "pequeña"),
   ("si Ana es mayor que Luis y Luis es mayor que Eva, ¿quién es la menor?", "eva"),
   ("si un coche es más rápido que una bici, ¿la bici es más lenta que el coche?", "^si"),
   ("si mi casa es más grande que la tuya, ¿la tuya es más pequeña?", "^si"),
   ("si Pedro tiene más años que Juan, ¿Juan es más joven que Pedro?", "^si"), ("si hoy es lunes, ¿qué día será mañana?", "martes"),
   ("si tengo 20 años, ¿cuántos años tendré dentro de 5 años?", "25"), ("¿un conejo es más grande que una liebre?", "ABST"),
   ("si el tren sale a las 10 y tarda 3 horas, ¿a qué hora llega?", "13|una"),
   ("si un lápiz cuesta 2 euros y una goma 1, ¿cuánto cuestan los dos juntos?", "3|tres")]},
 {"id": "ch50h-e", "cat": "dibujo", "turnos": [
   ("dibuja un círculo", "circulo;!entendido"), ("quiero que dibujes un cuadrado", "cuadrado;!no lo he entendido"), ("pinta un triángulo rojo", "triangulo"),
   ("muéstrame una estrella azul", "estrella"), ("dibuja el color verde", "verde"), ("¿qué has dibujado antes?", "estrella|verde"),
   ("dibuja dos círculos", "circulo*"), ("¿puedes dibujar un perro?", "ABST|no puedo|solo"), ("dibuja un cuadrado azul y un círculo amarillo", "cuadrado;circulo"),
   ("gracias", "nada|gracias")]},
]


def medir(verboso=False, salida="lab/res_charla50h.json"):
    return correr(D, verboso=verboso, salida=salida, continua=True)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "CHARLA 50 H")
