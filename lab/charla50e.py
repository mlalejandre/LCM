"""CHARLA 50 E: referencia de la ronda 2.10 (valor conceptual de las preposiciones).
UNA conversación libre de 50 interacciones (bloques con memoria compartida), escrita con la 2.9 congelada,
criterios fijados de antemano; no se lee hasta la medida final."""
from lab.banco import correr, imprime
from lab.imagenes import img, escena
D = [
 {"id": "ch50e-a", "cat": "origen_lugar", "turnos": [
   ("hola, me llamo Tomás", "tomas;!no lo he entendido"),
   ("soy de Zamora pero vivo en Valencia desde hace tres años", "zamora|valencia;!no lo he entendido"),
   ("¿de dónde soy?", "zamora;!valencia"), ("¿dónde vivo?", "valencia;!zamora"), ("¿desde cuándo vivo en Valencia?", "tres|3"),
   ("trabajo en un taller de bicicletas con mi primo Luis", "taller;!no lo he entendido"), ("¿con quién trabajo?", "luis|primo"),
   ("¿dónde trabajo?", "taller"), ("voy al taller en bici", "bici;!no lo he entendido"), ("¿cómo voy al taller?", "bici")]},
 {"id": "ch50e-b", "cat": "espacio", "turnos": [
   ("en mi habitación hay una mesa y encima de la mesa tengo un flexo", "flexo|mesa;!no lo he entendido"), ("¿dónde está el flexo?", "mesa"),
   ("¿qué hay encima de la mesa?", "flexo"), ("mi mochila está debajo de la cama", "mochila;!no lo he entendido"), ("¿dónde está mi mochila?", "cama"),
   ("¿qué hay debajo de la cama?", "mochila"), ("¿la cama está encima de la mochila?", "^si"),
   ("la estantería está al lado de la ventana", "estanteria;!no lo he entendido"), ("¿qué hay al lado de la ventana?", "estanteria"),
   ("¿la ventana está al lado de la estantería?", "^si")]},
 {"id": "ch50e-c", "cat": "papeles", "turnos": [
   ("estoy cansado por el trabajo", "cansado;!no lo he entendido"), ("¿por qué estoy cansado?", "trabajo"),
   ("he comprado un regalo para mi madre", "regalo;!no lo he entendido"), ("¿para quién es el regalo?", "madre"),
   ("ahorro para un viaje a Lisboa", "viaje|lisboa;!no lo he entendido"), ("¿para qué ahorro?", "viaje"),
   ("arreglo las ruedas con una llave inglesa", "llave;!no lo he entendido"), ("¿con qué arreglo las ruedas?", "llave"),
   ("Luis trabaja con mucho cuidado", "cuidado;!no lo he entendido"), ("¿cómo trabaja Luis?", "cuidado")]},
 {"id": "ch50e-d", "cat": "tiempo_tema_imagen", "turnos": [
   ("el taller abre de nueve a dos", "nueve|9;!no lo he entendido"), ("¿hasta qué hora abre el taller?", "dos|2"),
   ("ayer estuve en el gimnasio durante dos horas", "gimnasio;!no lo he entendido"), ("¿cuánto tiempo estuve en el gimnasio?", "dos|2"),
   ("antes de la cena siempre llamo a mi madre", "madre|cena;!no lo he entendido"), ("¿cuándo llamo a mi madre?", "antes;cena"),
   ("mi primo y yo hablamos mucho de ciclismo", "ciclismo;!no lo he entendido"), ("¿de qué hablamos mi primo y yo?", "ciclismo"),
   (img("en este dibujo, ¿qué figura está encima?", escena(("estrella", "amarillo"), ("circulo", "azul"))), "estrella"),
   ("¿y qué figura está debajo?", "circulo")]},
 {"id": "ch50e-e", "cat": "repaso", "turnos": [
   ("¿de dónde soy?", "zamora"), ("¿con qué arreglo las ruedas?", "llave"), ("¿qué hay debajo de la cama?", "mochila"),
   ("¿dónde está la estantería?", "ventana"), ("¿para qué ahorro?", "viaje"), ("¿con quién viajo a Lisboa?", "ABST"),
   ("¿qué hay encima del flexo?", "ABST"), ("¿por qué está cansado Luis?", "ABST"),
   ("tengo una mesa de madera en el salón", "madera|mesa;!no lo he entendido"), ("¿de qué es la mesa del salón?", "madera")]},
]


def medir(verboso=False, salida="lab/res_charla50e.json"):
    return correr(D, verboso=verboso, salida=salida, continua=True)


if __name__ == "__main__":
    f, r = medir()
    imprime(r, "CHARLA 50 E")
