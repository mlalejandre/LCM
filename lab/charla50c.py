"""CHARLA 50 C: medida de referencia de la ronda 2.8. UNA conversación libre de 50 interacciones (cinco bloques que
comparten memoria), escrita con la 2.7 congelada, sin buscar a propósito fallos conocidos y con criterios fijados de
antemano. NO se usa para corregir: se mide al principio y al final, y sus transcripciones no se leen hasta la medida final."""
from lab.banco import correr, imprime
from lab.imagenes import png, img, figura
D = [
 {"id": "ch50c-a", "cat": "presentacion", "turnos": [
   ("holaa", "hola"), ("¿qué tal la noche?", "ANY"), ("yo no puedo dormir, mañana tengo un examen", "examen;!no lo he entendido"),
   ("me llamo Lucía y estudio Derecho en Salamanca", "lucia;derecho;!no lo he entendido"), ("estoy en cuarto curso", "cuarto;!no lo he entendido"),
   ("¿qué estudio?", "derecho"), ("¿dónde estudio?", "salamanca"), ("¿qué tengo mañana?", "examen"),
   ("el examen es de Derecho Penal", "penal;!no lo he entendido"), ("¿de qué es el examen?", "penal")]},
 {"id": "ch50c-b", "cat": "casa", "turnos": [
   ("comparto piso con dos amigas, Alba y Sofía", "alba;sofia;!no lo he entendido"), ("Alba es de Zamora y Sofía de León", "ANY"), ("¿de dónde es Sofía?", "leon"),
   ("¿con cuántas personas comparto piso?", "dos|2"), ("Sofía estudia Medicina", "medicina;!no lo he entendido"), ("¿quién estudia Medicina?", "sofia"),
   ("Alba cocina muy bien", "ANY"), ("anoche nos hizo una tortilla de patatas", "tortilla;!no lo he entendido"), ("¿qué nos hizo Alba anoche?", "tortilla"),
   ("¿la tortilla lleva huevo?", "^si")]},
 {"id": "ch50c-c", "cat": "planes", "turnos": [
   ("cuando acabe los exámenes me iré a Portugal", "portugal;!no lo he entendido"), ("iré con mi novio, que se llama Diego", "diego;!no lo he entendido"),
   ("¿adónde me iré?", "portugal"), ("¿cómo se llama mi novio?", "diego"), ("Diego trabaja en una librería", "libreria;!no lo he entendido"),
   ("¿dónde trabaja Diego?", "libreria"), ("queremos ir en coche", "coche;!no lo he entendido"), ("¿cómo queremos ir?", "coche"),
   ("el coche es de su padre", "ANY"), ("¿un coche es un vehículo?", "^si")]},
 {"id": "ch50c-d", "cat": "mezcla", "turnos": [
   (img("mira, esta es la mochila que me regaló Diego", png("morado")), "morad*;!no lo he entendido"), ("¿de qué color es mi mochila?", "morad*"),
   ("¿quién me regaló la mochila?", "diego"), ("por cierto, mi madre está enferma", "madre;enferm*;!no lo he entendido"), ("tiene gripe", "gripe;!no lo he entendido"),
   ("¿qué le pasa a mi madre?", "gripe|enferm*"), ("la llamaré mañana", "ANY"), ("¿a quién llamaré mañana?", "madre"),
   ("mi madre vive en Ávila", "avila;!no lo he entendido"), ("¿dónde vive mi madre?", "avila")]},
 {"id": "ch50c-e", "cat": "repaso", "turnos": [
   ("¿cómo me llamo?", "lucia"), ("¿en qué curso estoy?", "cuarto"), ("¿Alba es de León?", "^no|zamora"), ("¿tengo hermanos?", "ABST|^no"),
   ("¿qué sabes de Diego?", "novio|libreria"), ("¿Sofía estudia Derecho?", "^no|medicina"), ("¿qué te he contado de mi madre?", "enferm*|gripe|avila"),
   ("bueno, voy a intentar dormir", "ANY"), ("¿me deseas suerte?", "suerte|ANY"), ("buenas noches", "buenas noches|descans*|hasta")]},
]


def medir(verboso=False, salida="lab/res_charla50c.json"):
    return correr(D, verboso=verboso, salida=salida, continua=True)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "CHARLA 50 C")
