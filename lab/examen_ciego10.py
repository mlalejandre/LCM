"""EXAMEN CIEGO 10: preposiciones y locuciones (lugar, inversas, dirección, recorrido, tiempo, causa, finalidad,
instrumento, modo, tema, materia, posesión, compañía, imagen). Escrito con la 2.9 congelada; no se lee hasta la medida final."""
from lab.banco import correr, imprime
from lab.imagenes import img, escena
D = [
 {"id": "c10-lugar", "cat": "lugar", "turnos": [
   ("hola", "hola"), ("las llaves están dentro del cajón", "llaves;!no lo he entendido"), ("¿dónde están las llaves?", "cajon"),
   ("¿qué hay dentro del cajón?", "llaves"), ("el coche está aparcado delante de la farmacia", "coche;!no lo he entendido"),
   ("¿dónde está el coche?", "farmacia"), ("¿qué hay detrás del coche?", "ABST"), ("¿la farmacia está detrás del coche?", "^si"),
   ("el parque está cerca de mi casa", "parque;!no lo he entendido"), ("¿mi casa está lejos del parque?", "^no|cerca"),
   ("el colegio está entre la iglesia y el mercado", "colegio;!no lo he entendido"), ("¿dónde está el colegio?", "iglesia;mercado")]},
 {"id": "c10-viaje", "cat": "direccion", "turnos": [
   ("buenas", "hola|buenas"), ("mañana viajo a Granada con mi hermana Eva", "granada;!no lo he entendido"), ("¿adónde viajo mañana?", "granada"),
   ("¿con quién viajo?", "eva|hermana"), ("pasaremos por Jaén", "jaen;!no lo he entendido"), ("¿por dónde pasaremos?", "jaen"),
   ("nos quedaremos hasta el domingo", "domingo;!no lo he entendido"), ("¿hasta cuándo nos quedaremos?", "domingo"),
   ("volvemos en tren", "tren;!no lo he entendido"), ("¿cómo volvemos?", "tren"),
   ("salimos desde la estación del norte", "estacion;!no lo he entendido"), ("¿desde dónde salimos?", "estacion")]},
 {"id": "c10-papeles", "cat": "papeles", "turnos": [
   ("hola", "hola"), ("mi vecino no vino a la reunión por la lluvia", "lluvia|reunion;!no lo he entendido"),
   ("¿por qué no vino mi vecino a la reunión?", "lluvia"), ("escribo un libro sobre mi abuelo", "libro;!no lo he entendido"),
   ("¿sobre qué escribo?", "abuelo"), ("tomo el café sin azúcar", "cafe;!no lo he entendido"), ("¿cómo tomo el café?", "sin azucar"),
   ("mi hermano juega contra el equipo de Toni", "toni|equipo;!no lo he entendido"), ("¿contra quién juega mi hermano?", "toni"),
   ("corto el pan con un cuchillo", "pan;!no lo he entendido"), ("¿con qué corto el pan?", "cuchillo"),
   ("estudio por las noches para el examen de conducir", "examen;!no lo he entendido"), ("¿para qué estudio?", "examen;conducir"),
   ("¿cuándo estudio?", "noche*")]},
 {"id": "c10-materia", "cat": "materia_imagen", "turnos": [
   ("hola", "hola"), ("tengo un anillo de plata", "anillo;!no lo he entendido"), ("¿de qué es mi anillo?", "plata"),
   ("el anillo era de mi abuela", "abuela;!no lo he entendido"), ("¿de quién era el anillo?", "abuela"),
   (img("mira este dibujo: ¿qué hay debajo del cuadrado?", escena(("cuadrado", "rojo"), ("triangulo", "azul"))), "triangulo"),
   ("¿de qué color es la figura de arriba?", "roj*"), ("¿con quién vive mi abuela?", "ABST")]},
]


def medir(verboso=False, salida="lab/res_ciego10.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    f, r = medir()
    imprime(r, "EXAMEN CIEGO 10")
