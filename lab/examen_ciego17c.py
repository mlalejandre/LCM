"""EXAMEN CIEGO 17c · medida FINAL limpia de la 2.17. Escrito con el código definitivo congelado (9d85a3b), medido UNA vez en cada versión.
Tras esta medida no se toca nada: lo que falle queda documentado. Contenidos y formas distintos de conversa17, 17b y las tandas.
«¿*» = hay pregunta; «!¿*» = no debe haberla. Una pregunta donde no toca o una afirmación falsa cuentan como error grave."""
from lab.banco import correr, imprime
N = "!no lo he entendido;!no he entendido"
Q = "!¿*"
BUENO = "enhorabuena|felicidades|me alegro|que bien|que buena noticia|que suerte"
MALO = "lo siento|vaya|que pena|animo|que mala suerte"
D = [
 {"id": "x-1", "cat": "P_preguntar", "turnos": [
   ("hola, me llamo Hortensia", "hortensia"),
   ("en octubre me voy de vacaciones", "¿*;adonde|donde"),
   ("a Sicilia con mi marido", "sicilia;" + N), ("¿con quién me voy de vacaciones?", "marido"), ("¿adónde me voy en octubre?", "sicilia"),
   ("nos hemos comprado un periquito", "¿*;como se llama"), ("Pipo", "pipo;" + N), ("¿cómo se llama mi periquito?", "pipo"),
   ("me he comprado una brusela", "¿*;brusela"), ("es una lámpara pequeña", N), ("¿qué es una brusela?", "lampara"),
   ("ayer comí con Gervasio", "¿*;quien es gervasio"), ("mi cuñado", "cunado|cuñado;" + N), ("¿quién es Gervasio?", "cunado|cuñado")]},
 {"id": "x-2", "cat": "Q_callar", "turnos": [
   ("soy Anselmo", "anselmo"),
   ("¿cuánto es 15 más 27?", "42;" + Q), ("¿para qué sirve una escoba?", "barrer;" + Q),
   ("mi perro se llama Trasto", "trasto;" + Q), ("tengo un perro", N + ";" + Q),
   ("me voy a Cuenca el domingo", N + ";!adonde"),
   ("no me preguntes más", N + ";" + Q),
   ("he adoptado una gata", N + ";" + Q), ("el jueves tengo una cena", N + ";" + Q),
   ("puedes volver a preguntarme", N),
   ("tengo dos nietos", "¿*;como se llaman"), ("da igual", Q + ";" + N),
   ("las ballenas son mamíferos", N + ";" + Q),
   ("los sábados juego al dominó", N + ";" + Q),
   ("bueno, me voy ya, gracias por todo", "de nada|hasta|adios;" + Q)]},
 {"id": "x-3", "cat": "S_tono", "turnos": [
   ("soy Milagros", "milagros"),
   ("me han concedido la hipoteca", BUENO),
   ("mi hijo ha aprobado las oposiciones", BUENO),
   ("se ha muerto mi tío", "lo siento;" + Q + ";!enhorabuena;!que bien"),
   ("me he roto la muñeca", MALO + ";!enhorabuena"),
   ("me han despedido del trabajo", MALO + ";!enhorabuena"), ("¿me han despedido?", "^si"),
   ("el lunes me operan de la vista", "suerte|animo|espero"),
   ("no he ganado el concurso", "!enhorabuena;!que bien;" + N),
   ("no tengo perro", "!lo siento;!enhorabuena;" + N),
   ("vivo en un quinto piso", "!enhorabuena;!lo siento;" + N),
   ("estoy muy triste", "¿*|cuentame|lo siento"), ("es que mi mejor amiga se ha ido a vivir a Chile", N), ("¿por qué estoy triste?", "amiga|chile"),
   ("ya me encuentro más animada", "me alegro|que bien")]},
 {"id": "x-4", "cat": "R_integrar", "turnos": [
   ("me llamo Leandro", "leandro"),
   ("tengo dos hermanas", "¿*;como se llaman"), ("Iria y Antía", "iria|antia;" + N), ("¿cómo se llaman mis hermanas?", "iria;antia"),
   ("el viernes tengo una cita", "¿*;con quien"), ("con una chica que conocí en clase", "chica;" + N), ("¿con quién tengo una cita?", "chica"),
   ("ayer tuve un partido", "¿*;que tal"), ("fatal", "fatal;" + N), ("¿qué tal me fue el partido?", "fatal"),
   ("estoy leyendo un libro", "¿*;libro"), ("uno de aventuras", "aventuras;" + N),
   ("anoche discutí con mi padre", "¿*|cuentame;que paso|por que"), ("se llama Ricardo", "ricardo;!porque se llama"), ("¿cómo se llama mi padre?", "ricardo")]},
 {"id": "x-5", "cat": "T_hilo", "turnos": [
   ("soy Azucena", "azucena"), ("vivo en Teruel", N), ("tengo 52 años", N),
   ("pregúntame lo que quieras", "¿*;!donde vives;!cuantos años"),
   ("soy farmacéutica", "farmaceutica;" + N), ("¿a qué me dedico?", "farmaceutica"),
   ("el miércoles voy al dentista", N), ("en diciembre me jubilo", N),
   ("¿qué tengo previsto?", "dentista;jubil*"),
   ("los lunes tengo inglés", N), ("me he equivocado, los martes", "martes;" + N), ("¿qué día tengo inglés?", "martes;!lunes"),
   ("¿por dónde íbamos?", "ingles|dentista|jubil*|teruel|farmaceutica"),
   ("hablemos de otra cosa", N),
   ("¿y tú cómo estás?", "bien"),
   ("pues nada, hasta luego", "hasta|adios;" + Q)]},
 {"id": "x-6", "cat": "U_pertinencia", "turnos": [
   ("buenas, soy Eusebio", "eusebio"), ("mi mujer se llama Encarna", "encarna"), ("Encarna es peluquera", N),
   ("tenemos dos hijos", "¿*;como se llaman"), ("Mateo y Jimena", "mateo|jimena;" + N),
   ("a los críos les encanta el fútbol", "mateo|jimena|hijos"), ("¿a quién le gusta el fútbol?", "mateo;jimena"),
   ("a Jimena le he regalado unos patines", N), ("¿qué le he regalado a Jimena?", "patines"),
   ("anoche se me rompió la tele", MALO), ("¿qué le pasó a la tele?", "rompio|rota"),
   ("¿qué sabes de mi familia?", "encarna;mateo;jimena"),
   ("¿a qué se dedica mi mujer?", "peluquera"),
   ("¿una peluquera es una persona?", "^si;" + Q)]},
 {"id": "x-7", "cat": "V_verde", "turnos": [
   ("soy Íñigo", "inigo"),
   ("comparto despacho con dos compañeros, Asier y Unai", "asier|unai;" + N), ("¿con quién comparto despacho?", "asier;unai"),
   ("Asier escribe más rápido que Unai", N), ("Unai escribe más rápido que Gorka", N), ("¿quién escribe más rápido, Asier o Gorka?", "asier"),
   ("tenía 200 euros y he gastado 60 en la compra", N), ("¿cuánto me queda?", "140"),
   ("hoy ha sido un día larguísimo", N), ("es que he tenido cuatro reuniones", N), ("¿por qué ha sido un día largo?", "reuniones"),
   ("a mi abuelo le chifla el dominó", N), ("¿qué le gusta a mi abuelo?", "domino"),
   ("voy a natación los viernes", N), ("perdón, los sábados", "sabados;" + N), ("¿cuándo voy a natación?", "sabados;!viernes"),
   ("ayer comí con mi tío Julio", "julio;!comiste julio"), ("¿cómo se llama mi tío?", "julio"),
   ("me han subido el alquiler", N), ("¿me han subido el alquiler?", "^si")]},
]

def medir(verboso=False, salida="lab/res_ciego17c.json"):
    return correr(D, verboso=verboso, salida=salida)

def main():
    f, r = medir(verboso=True)
    imprime(r, "EXAMEN CIEGO 17c (medida final limpia)")

if __name__ == "__main__":
    main()
