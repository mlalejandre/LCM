"""EXAMEN CIEGO 8: control de la ronda 2.8. Escrito con la 2.7 congelada, sin probarlo antes; se mide solo el agregado
al principio y al final. Temas que no aparecen en las tandas: jardín, mudanza de un amigo, fútbol, médico de cabecera,
compra de un piano, cumpleaños de un abuelo, vecino ruidoso, trabajo en un taller."""
from lab.banco import correr, imprime
from lab.imagenes import png, img, figura
D = [
 {"id": "c8-jardin", "cat": "libre", "turnos": [
   ("hola, ¿qué tal?", "hola|bien"), ("me llamo Ramón y tengo un jardín pequeño", "ramon;jardin;!no lo he entendido"),
   ("en el jardín tengo un limonero y dos rosales", "limonero;rosales;!no lo he entendido"), ("¿qué tengo en el jardín?", "limonero"),
   ("¿cuántos rosales tengo?", "dos|2"), ("el limonero lo plantó mi abuelo", "abuelo;!no lo he entendido"), ("¿quién plantó el limonero?", "abuelo"),
   ("los rosales necesitan mucha agua", "agua;!no lo he entendido"), ("¿qué necesitan los rosales?", "agua"), ("¿un limonero es una planta?", "^si")]},
 {"id": "c8-futbol", "cat": "libre", "turnos": [
   ("buenas", "buenas|hola"), ("ayer jugué un partido de fútbol con mis compañeros de trabajo", "futbol;!no lo he entendido"),
   ("ganamos tres a uno", "ANY"), ("yo marqué un gol", "gol;!no lo he entendido"), ("¿qué jugué ayer?", "futbol|partido"),
   ("¿con quién jugué?", "compañeros"), ("¿marqué algún gol?", "^si"), ("mi compañero Iván, que es el portero, se lesionó", "ivan;!no lo he entendido"),
   ("¿quién se lesionó?", "ivan"), ("¿qué es Iván?", "portero|compañero")]},
 {"id": "c8-piano", "cat": "libre", "turnos": [
   ("hola", "hola"), ("mi hija Irene quiere aprender a tocar el piano", "irene;piano;!no lo he entendido"), ("tiene ocho años", "ocho;!no lo he entendido"),
   ("¿qué quiere aprender Irene?", "piano"), ("¿cuántos años tiene mi hija?", "ocho|8"), ("hemos comprado un piano de segunda mano", "piano;!no lo he entendido"),
   (img("este es el piano", png("negro")), "negr*;!no lo he entendido"), ("¿de qué color es el piano?", "negr*"),
   ("su profesora se llama Marisa", "marisa;!no lo he entendido"), ("¿cómo se llama la profesora de Irene?", "marisa")]},
 {"id": "c8-vecino", "cat": "libre", "turnos": [
   ("estoy harto de mi vecino", "vecino;!no lo he entendido"), ("pone la música muy alta todas las noches", "musica;!no lo he entendido"),
   ("¿qué hace mi vecino todas las noches?", "musica"), ("ya he hablado con él dos veces", "ANY"), ("se llama Gonzalo y vive en el tercero", "gonzalo;!no lo he entendido"),
   ("¿cómo se llama mi vecino?", "gonzalo"), ("¿en qué piso vive Gonzalo?", "tercero"), ("mañana hablaré con el presidente de la comunidad", "presidente;!no lo he entendido"),
   ("¿con quién hablaré mañana?", "presidente"), ("¿estoy contento con mi vecino?", "^no|harto|ABST")]},
 {"id": "c8-abuelo", "cat": "libre", "turnos": [
   ("el domingo es el cumpleaños de mi abuelo", "abuelo;domingo;!no lo he entendido"), ("cumple ochenta y cinco años", "ANY"), ("¿cuántos años cumple mi abuelo?", "85|ochenta y cinco"),
   ("le vamos a regalar un reloj", "reloj;!no lo he entendido"), ("¿qué le vamos a regalar?", "reloj"), ("mi abuelo se llama Anselmo", "anselmo;!no lo he entendido"),
   ("Anselmo fue carpintero toda su vida", "carpinter*;!no lo he entendido"), ("¿a qué se dedicaba mi abuelo?", "carpinter*"),
   ("¿cuándo es el cumpleaños de mi abuelo?", "domingo"), ("¿un reloj es un objeto?", "^si")]},
 {"id": "c8-taller", "cat": "libre", "turnos": [
   ("trabajo en un taller de coches", "taller;!no lo he entendido"), ("mi jefe, que se llama Paco, es muy serio", "paco;serio;!no lo he entendido"),
   ("¿dónde trabajo?", "taller"), ("¿cómo es mi jefe?", "serio"), ("hoy hemos arreglado una furgoneta blanca", "furgoneta;!no lo he entendido"),
   ("¿qué hemos arreglado hoy?", "furgoneta"), ("¿de qué color era la furgoneta?", "blanc*"), ("Paco dice que mañana habrá mucho trabajo", "ANY"),
   ("¿qué dice Paco?", "trabajo"), ("¿Paco es mi jefe?", "^si")]},
]


def medir(verboso=False, salida="lab/res_ciego8.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "EXAMEN CIEGO 8")
