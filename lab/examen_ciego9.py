"""EXAMEN CIEGO 9: control de la ronda 2.9. Escrito con la 2.8 congelada antes de tocar el código; se mide solo el
agregado al principio y al final. Contiene a propósito las construcciones que ataca la ronda (rol con artículo,
cumpleaños/fechas invertidas, color como adjetivo, aposición con lista, dos frases con coma, dativos) en temas y
frases que no aparecen en ninguna tanda, junto a turnos de control de otros tipos."""
from lab.banco import correr, imprime
from lab.imagenes import png, img, figura
D = [
 {"id": "c9-equipo", "cat": "libre", "turnos": [
   ("hola", "hola"), ("juego en un equipo de balonmano", "balonmano;!no lo he entendido"), ("mi amiga Celia, que es la capitana, se ha roto un dedo", "celia;dedo;!no lo he entendido"),
   ("¿qué es Celia?", "capitana"), ("¿qué se ha roto Celia?", "dedo"), ("el sábado es la final", "sabado;final;!no lo he entendido"),
   ("¿cuándo es la final?", "sabado"), ("estoy nerviosa, llevo toda la semana entrenando", "ANY"), ("¿cómo estoy?", "nerviosa"), ("¿en qué equipo juego?", "balonmano")]},
 {"id": "c9-mudanza", "cat": "libre", "turnos": [
   ("buenas", "buenas|hola"), ("me mudo a un piso con dos compañeros, Óscar y Nacho", "oscar;nacho;!no lo he entendido"),
   ("¿con quién me mudo?", "oscar|nacho"), ("¿cuántos compañeros tengo?", "dos|2"), ("Óscar es de Valencia y Nacho de Bilbao", "ANY"),
   ("¿de dónde es Nacho?", "bilbao"), ("hemos alquilado una casa amarilla cerca del río", "casa;!no lo he entendido"), ("¿de qué color es la casa?", "amarill*"),
   ("el lunes es la mudanza", "lunes;!no lo he entendido"), ("¿cuándo es la mudanza?", "lunes")]},
 {"id": "c9-bebe", "cat": "libre", "turnos": [
   ("hola", "hola"), ("mi hija Alma tiene un año", "alma;!no lo he entendido"), ("le está saliendo el primer diente", "diente;!no lo he entendido"),
   ("¿qué le está saliendo a Alma?", "diente"), ("a mi marido le duele la espalda de cogerla en brazos", "espalda;!no lo he entendido"), ("¿qué le duele a mi marido?", "espalda"),
   ("¿cuántos años tiene Alma?", "uno|un ano|1"), ("hoy no ha dormido la siesta, está muy cansada", "ANY"), ("¿cómo está Alma?", "cansada"), ("¿Alma es mi hija?", "^si")]},
 {"id": "c9-abuela", "cat": "libre", "turnos": [
   ("mañana es el santo de mi abuela", "abuela;!no lo he entendido"), ("se llama Dolores y fue maestra muchos años", "dolores;!no lo he entendido"),
   ("¿a qué se dedicaba mi abuela?", "maestra"), ("¿cuándo es el santo de mi abuela?", "mañana"), ("le vamos a regalar un pañuelo verde", "pañuelo;!no lo he entendido"),
   ("¿de qué color es el pañuelo?", "verde"), ("¿qué le vamos a regalar?", "pañuelo"), ("mi tío Félix, que es el hijo mayor, organiza la comida", "felix;!no lo he entendido"),
   ("¿quién organiza la comida?", "felix"), ("¿Félix es mi tío?", "^si")]},
 {"id": "c9-movil", "cat": "libre", "turnos": [
   ("qué rabia", "ANY"), ("se me ha roto el móvil, se me cayó al suelo", "movil;!no lo he entendido"), ("¿qué se me ha roto?", "movil"),
   ("¿dónde se me cayó?", "suelo"), ("tengo que comprar otro, el viejo tenía cinco años", "ANY"), ("¿qué tengo que comprar?", "movil|otro"),
   (img("me gusta este color para el nuevo", png("azul")), "azul;!no lo he entendido"), ("¿qué color me gusta para el nuevo?", "azul"), ("¿un móvil es un objeto?", "^si"), ("gracias", "nada|gusto|para eso")]},
]


def medir(verboso=False, salida="lab/res_ciego9.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "EXAMEN CIEGO 9")
