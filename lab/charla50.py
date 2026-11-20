"""CHARLA 50: medida de referencia de la ronda 2.6. Una conversación libre de 50 interacciones, escrita con la 2.5 congelada
y criterios fijados de antemano. NO se usa para corregir: solo se mide al principio y al final de la ronda."""
from lab.banco import correr, imprime
from lab.imagenes import png, img
D = [
 {"id": "ch50-a", "cat": "presentacion", "turnos": [
   ("Hola!! qué tal todo", "hola"), ("Yo bien, aquí liada con mil cosas", "ANY"), ("Me llamo Sonia, encantada", "sonia"), ("Tengo treinta y ocho años y soy arquitecta", "entendid*|apunto"),
   ("Trabajo en un estudio pequeño en Zaragoza", "entendid*|apunto"), ("¿Cómo me llamo?", "sonia"), ("¿A qué me dedico?", "arquitect*"), ("¿Cuántos años tengo?", "38|treinta y ocho"),
   ("¿Dónde trabajo?", "estudio|zaragoza"), ("Estoy casada con Iñaki, que es profesor de música", "ANY")]},
 {"id": "ch50-b", "cat": "familia", "turnos": [
   ("¿Cómo se llama mi marido?", "iñaki|inaki"), ("¿Qué enseña Iñaki?", "musica"), ("Tenemos dos niños, Leo y Alba", "entendid*|apunto"), ("Leo tiene siete años y Alba cuatro", "ANY"),
   ("¿Cuántos hijos tengo?", "dos|2"), ("¿Cómo se llama mi hija?", "alba"), ("¿Quién es mayor, Leo o Alba?", "leo"), ("¿Quién es el padre de Alba?", "iñaki|inaki"),
   ("Leo va a clases de natación los martes", "entendid*|apunto"), ("¿Qué hace Leo los martes?", "natacion")]},
 {"id": "ch50-c", "cat": "rutina", "turnos": [
   ("¿La natación es un deporte?", "^si"), ("A Alba le encantan los dinosaurios", "entendid*|apunto"), ("¿Qué le gusta a Alba?", "dinosaurio*"), ("Esta mañana se me ha roto la cafetera", "ANY"),
   ("¿Qué se me ha roto?", "cafetera"), ("Así que hoy no he desayunado café", "ANY"), ("He tomado un té en su lugar", "ANY"), ("¿Qué he tomado hoy?", "te|té"),
   ("¿El té es una bebida?", "^si"), ("Mañana compraré una cafetera nueva", "entendid*|apunto")]},
 {"id": "ch50-d", "cat": "mezcla", "turnos": [
   ("¿Qué voy a comprar mañana?", "cafetera"), ("Por cierto, mi madre viene a vernos el domingo", "entendid*|apunto"), ("Vive en Huesca", "entendid*|apunto"), ("¿Dónde vive mi madre?", "huesca"),
   ("¿Cuándo viene mi madre?", "domingo"), (img("Mira, este es el color de la cafetera que quiero", png("rojo")), "roj*|ANY"), ("¿De qué color es la cafetera que quiero?", "roj*|ABST"),
   ("Iñaki dice que es demasiado cara", "ANY"), ("¿Qué dice Iñaki?", "cara"), ("Tiene razón, cuesta ciento veinte euros", "ANY")]},
 {"id": "ch50-e", "cat": "repaso", "turnos": [
   ("¿Cuánto cuesta la cafetera?", "120|ciento veinte|ABST"), ("Bueno, ya veremos", "ANY"), ("¿Qué sabes de Leo?", "siete|natacion|hijo"), ("¿Tengo perro?", "ABST|^no"),
   ("¿Iñaki es arquitecto?", "^no|profesor|ABST"), ("¿Dónde trabaja Iñaki?", "ABST"), ("¿De qué hemos hablado?", "cafetera|leo|alba|madre|iñaki|inaki|natacion"), ("¿Me das un consejo?", "ANY"),
   ("Muchas gracias por todo", "de nada|placer|gracias"), ("Hasta luego!", "hasta|adios")]},
]


def medir(verboso=False, salida="lab/res_charla50.json"):
    return correr(D, verboso=verboso, salida=salida, continua=True)   # una sola conversación: los bloques comparten memoria


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "CHARLA 50")
