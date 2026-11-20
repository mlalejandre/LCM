"""EXAMEN CIEGO 13: cálculo determinista, problemas de enunciado, suposiciones con comparación, dibujo y cálculo con datos de la charla.
Escrito con la 2.12 congelada; no se lee hasta la medida final."""
from lab.banco import correr, imprime
D = [
 {"id": "c13-arit", "cat": "aritmetica", "turnos": [
   ("hola", "hola"), ("¿cuánto es 48 más 52?", "100"), ("¿y 48 menos 52?", "-4|−4|menos 4"), ("multiplica 25 por 4", "100"),
   ("¿cuánto da 81 dividido entre 9?", "9"), ("¿cuál es el triple de 15?", "45"), ("¿cuánto es el 25 por ciento de 200?", "50"),
   ("¿cuánto es la raíz de 49?", "7"), ("¿cuánto es 10 menos 2 por 3?", "4"), ("¿cuánto suman 15, 25 y 35?", "75"), ("resta 18 a 50", "32"),
   ("¿cuánto es mil menos uno?", "999")]},
 {"id": "c13-prob", "cat": "problemas", "turnos": [
   ("hola", "hola"), ("tenía 50 cromos y he perdido 13, ¿cuántos me quedan?", "37"), ("en clase hay 14 chicos y 13 chicas, ¿cuántos alumnos hay?", "27"),
   ("compro 3 libros de 12 euros, ¿cuánto pago?", "36"), ("tenemos 60 caramelos para 4 niños, ¿cuántos le damos a cada uno?", "15"),
   ("un autobús lleva 40 personas, bajan 15 y suben 8, ¿cuántas personas lleva ahora?", "33"),
   ("María tiene 8 años y su padre tiene 30 más, ¿cuántos años tiene su padre?", "38")]},
 {"id": "c13-sup", "cat": "suposiciones", "turnos": [
   ("hola", "hola"), ("si un elefante es más pesado que un caballo, ¿el caballo es más ligero que el elefante?", "^si"),
   ("si Rosa es más alta que Paula, ¿quién es más baja?", "paula"), ("si hoy es viernes, ¿qué día fue ayer?", "jueves"),
   ("si un perro es más pequeño que un caballo, ¿el caballo es más grande o más pequeño que el perro?", "grande"),
   ("si tengo 15 años, ¿cuántos años tenía hace 3 años?", "12")]},
 {"id": "c13-dib", "cat": "dibujo", "turnos": [
   ("hola", "hola"), ("dibuja un triángulo", "triangulo;!entendido"), ("pinta un círculo verde", "circulo"), ("¿me dibujas un rectángulo?", "rectangulo"),
   ("enséñame el color naranja", "naranja"), ("dibuja un gato", "ABST|no puedo|solo"), ("muéstrame un cuadrado y un triángulo", "cuadrado;triangulo")]},
 {"id": "c13-mem", "cat": "calculo_memoria", "turnos": [
   ("hola", "hola"), ("tengo 4 primos y 3 primas", "primos|primas;!no lo he entendido"), ("¿cuántos primos tengo en total?", "7|siete"),
   ("mi hermano tiene 12 años y yo 9", "12|9;!no lo he entendido"), ("¿cuántos años nos llevamos?", "3|tres"), ("¿cuánto suman nuestras edades?", "21")]},
]


def medir(verboso=False, salida="lab/res_ciego13.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    f, r = medir()
    imprime(r, "EXAMEN CIEGO 13")
