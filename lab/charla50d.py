"""CHARLA 50 D: referencia de la ronda 2.9. UNA conversación libre de 50 interacciones (bloques con memoria compartida),
escrita con la 2.8 congelada, criterios fijados de antemano; no se lee hasta la medida final."""
from lab.banco import correr, imprime
from lab.imagenes import png, img, figura
D = [
 {"id": "ch50d-a", "cat": "presentacion", "turnos": [
   ("buenos días", "buenos dias|hola"), ("me llamo Begoña y soy farmacéutica", "begoña|begona;farmaceutica;!no lo he entendido"), ("trabajo en una farmacia del barrio, estoy cansada, hoy abrimos a las ocho", "ANY"),
   ("¿a qué me dedico?", "farmaceutica"), ("¿a qué hora abrimos hoy?", "ocho|8"), ("mi jefa, que es la dueña, se llama Pilar", "pilar;!no lo he entendido"),
   ("¿cómo se llama mi jefa?", "pilar"), ("¿qué es Pilar?", "dueña|duena|jefa"), ("el jueves es mi cumpleaños", "jueves;!no lo he entendido"), ("¿cuándo es mi cumpleaños?", "jueves")]},
 {"id": "ch50d-b", "cat": "familia", "turnos": [
   ("vivo con mi pareja y dos gatos, Lupe y Nube", "lupe;nube;!no lo he entendido"), ("¿cuántos gatos tengo?", "dos|2"), ("¿cómo se llaman mis gatos?", "lupe;nube"),
   ("Lupe es negra y Nube blanca", "ANY"), ("¿de qué color es Nube?", "blanca"), ("a Nube le encanta dormir en el sofá", "sofa;!no lo he entendido"),
   ("¿qué le encanta a Nube?", "dormir"), ("mi pareja se llama Íñigo y es bombero", "iñigo|inigo;bombero;!no lo he entendido"), ("¿a qué se dedica Íñigo?", "bombero"), ("¿Íñigo es mi pareja?", "^si")]},
 {"id": "ch50d-c", "cat": "salud", "turnos": [
   ("a Íñigo le duele el hombro desde el último incendio", "hombro;!no lo he entendido"), ("¿qué le duele a Íñigo?", "hombro"), ("mañana va al fisioterapeuta", "fisio*;!no lo he entendido"),
   ("¿adónde va Íñigo mañana?", "fisio*"), ("se le ha olvidado la tarjeta sanitaria en casa", "ANY"), ("yo le llevaré la tarjeta", "tarjeta;!no lo he entendido"),
   ("¿quién le llevará la tarjeta?", "tu|tú|llevaras"), ("el fisio le ha dicho que no coja peso", "ANY"), ("¿qué le ha dicho el fisio?", "peso"), ("¿el hombro es una parte del cuerpo?", "^si|ABST")]},
 {"id": "ch50d-d", "cat": "mezcla", "turnos": [
   ("estamos pensando en comprar un sofá nuevo", "sofa;!no lo he entendido"), (img("nos gusta este color", png("gris")), "gris;!no lo he entendido"), ("¿qué color nos gusta?", "gris"),
   ("el viejo es marrón y está roto", "ANY"), ("¿de qué color es el sofá viejo?", "marron"), ("lo compraremos en una tienda del centro", "tienda;!no lo he entendido"),
   ("¿dónde compraremos el sofá?", "tienda"), ("el sábado es el día de las rebajas", "sabado;!no lo he entendido"), ("¿cuándo son las rebajas?", "sabado"), ("¿un sofá es un mueble?", "^si")]},
 {"id": "ch50d-e", "cat": "repaso", "turnos": [
   ("¿cómo me llamo?", "begoña|begona"), ("¿cuántos gatos tengo?", "dos|2"), ("¿Lupe es blanca?", "^no|negra"), ("¿quién es Pilar?", "jefa|dueña|duena"),
   ("¿qué le pasa a Íñigo?", "hombro|duele"), ("¿qué sabes de Nube?", "gat*|blanca|sofa"), ("¿tengo hijos?", "ABST|^no"), ("¿qué te he contado del sofá?", "sofa"),
   ("bueno, me voy a trabajar", "ANY"), ("hasta luego", "hasta|adios")]},
]


def medir(verboso=False, salida="lab/res_charla50d.json"):
    return correr(D, verboso=verboso, salida=salida, continua=True)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "CHARLA 50 D")
