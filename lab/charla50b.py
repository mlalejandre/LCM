"""CHARLA 50 B: medida de referencia de la ronda 2.7. UNA conversación libre de 50 interacciones (cinco bloques que
comparten memoria), escrita con la 2.6 congelada y criterios fijados de antemano. NO se usa para corregir: se mide al
principio y al final de la ronda, y sus transcripciones no se leen hasta después de la medida final."""
from lab.banco import correr, imprime
from lab.imagenes import png, img, figura
D = [
 {"id": "ch50b-a", "cat": "presentacion", "turnos": [
   ("Buenas! cómo va todo", "hola|buenas"), ("Pues aquí, recién llegado del trabajo", "ANY"), ("Me llamo Tomás y soy fontanero", "tomas;fontanero"),
   ("Vivo en Logroño desde hace diez años", "logroño|logrono;!no lo he entendido"), ("Antes vivía en Burgos", "burgos;!no lo he entendido"), ("¿Dónde vivo?", "logroño|logrono;!burgos"),
   ("¿Dónde vivía antes?", "burgos"), ("¿Cuál es mi profesión?", "fontanero"), ("Mi mujer, que se llama Rocío, es enfermera", "rocio;!no lo he entendido"),
   ("¿A qué se dedica Rocío?", "enfermera")]},
 {"id": "ch50b-b", "cat": "familia", "turnos": [
   ("Tenemos dos hijos, Pablo y Nerea", "pablo;nerea;!no lo he entendido"), ("Pablo tiene quince años y Nerea doce", "ANY"), ("¿Cuántos años tiene Nerea?", "doce|12"),
   ("¿Quién es mayor, Pablo o Nerea?", "pablo"), ("¿Cómo se llama mi mujer?", "rocio"), ("Mi hermano Rubén vive en Bilbao", "ruben;bilbao;!no lo he entendido"),
   ("¿Dónde vive Rubén?", "bilbao"), ("Rubén, que es mecánico, me arregla siempre el coche", "ANY"), ("¿Qué es Rubén?", "mecanico|hermano"),
   ("¿Quién me arregla el coche?", "ruben")]},
 {"id": "ch50b-c", "cat": "rutina", "turnos": [
   ("Los sábados juego al pádel con unos amigos", "padel;!no lo he entendido"), ("¿Qué hago los sábados?", "padel"), ("Ayer me hice daño en la rodilla", "rodilla;!no lo he entendido"),
   ("Me duele bastante", "ANY"), ("¿Qué me duele?", "rodilla"), ("El médico me ha dicho que descanse una semana", "ANY"), ("¿Qué me ha dicho el médico?", "descans*"),
   ("¿El pádel es un deporte?", "^si"), ("Así que este sábado no jugaré", "ANY"), ("¿Voy a jugar al pádel este sábado?", "^no|ABST")]},
 {"id": "ch50b-d", "cat": "mezcla", "turnos": [
   ("Cambiando de tema, queremos pintar el salón", "salon;!no lo he entendido"), (img("Este es el color que le gusta a Rocío", png("verde")), "verde|ANY"),
   ("Yo prefiero el azul", "azul;!no lo he entendido"), ("¿Qué color prefiero yo?", "azul"), ("¿Qué queremos pintar?", "salon"),
   ("Nerea dice que el verde es más bonito", "ANY"), ("¿Qué dice Nerea?", "verde"), ("¿El verde es un color?", "^si"),
   ("Lo pintaremos el mes que viene", "ANY"), ("¿Cuándo pintaremos el salón?", "mes que viene")]},
 {"id": "ch50b-e", "cat": "repaso", "turnos": [
   ("¿Cómo me llamo?", "tomas"), ("¿Cuántos hijos tengo?", "dos|2"), ("¿Tengo hijas?", "^si|nerea"), ("¿Rubén es fontanero?", "^no|mecanico|ABST"),
   ("¿Dónde trabaja Rocío?", "ABST"), ("¿Qué sabes de Pablo?", "quince|15|hijo"), ("¿De qué hemos hablado?", "rodilla|padel|salon|ruben|nerea|pablo|rocio"),
   ("¿Me recomiendas algo para la rodilla?", "ANY"), ("Bueno, me voy a cenar", "ANY"), ("Gracias, hasta mañana", "hasta|de nada|adios")]},
]


def medir(verboso=False, salida="lab/res_charla50b.json"):
    return correr(D, verboso=verboso, salida=salida, continua=True)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "CHARLA 50 B")
