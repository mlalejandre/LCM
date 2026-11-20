"""EXAMEN CIEGO 17b · medida limpia de la 2.17. Escrito con el código congelado (9f2acbb) y medido UNA vez, sin haber probado ninguna de estas frases.
Otros contenidos y otras formas que conversa17 y las tandas. «¿*» = hay pregunta; «!¿*» = no debe haberla. Pregunta indebida = error grave (MAL)."""
from lab.banco import correr, imprime
N = "!no lo he entendido;!no he entendido"
Q = "!¿*"
BUENO = "enhorabuena|felicidades|me alegro|que bien|que buena noticia|que suerte"
MALO = "lo siento|vaya|que pena|animo|que mala suerte"
D = [
 {"id": "w-1", "cat": "P_preguntar", "turnos": [
   ("buenos días, soy Elvira", "elvira"),
   ("en Semana Santa nos vamos de escapada", "¿*;adonde|donde"),
   ("a Oporto", "oporto;" + N), ("¿adónde nos vamos en Semana Santa?", "oporto"),
   ("he adoptado un conejo", "¿*;como se llama"), ("Copito", "copito;" + N), ("¿cómo se llama mi conejo?", "copito"),
   ("me he comprado una tarzuela", "¿*;tarzuela"), ("sirve para pelar naranjas", N), ("¿para qué sirve una tarzuela?", "pelar"),
   ("ayer quedé con Fermín", "¿*;quien es fermin"), ("un compañero de la facultad", "companero|compañero;" + N), ("¿quién es Fermín?", "companero|compañero"),
   ("anoche me enfadé con mi hermano", "¿*|cuentame;que paso|por que"), ("porque me cogió el coche sin permiso", "coche|permiso;" + N), ("¿por qué me enfadé con mi hermano?", "coche|permiso")]},
 {"id": "w-2", "cat": "R_integrar", "turnos": [
   ("me llamo Octavio", "octavio"),
   ("tengo una nieta", "¿*;como se llama"), ("Martina, y tiene tres años", "martina;" + N), ("¿cuántos años tiene Martina?", "tres|3"), ("¿cómo se llama mi nieta?", "martina"),
   ("el domingo tengo una comida", N), ("con mis hermanos, en casa de mi madre", "hermanos|madre;" + N), ("¿con quién como el domingo?", "hermanos"),
   ("la semana pasada tuve una entrevista", "¿*;que tal"), ("regular", "regular;" + N), ("¿qué tal me fue la entrevista?", "regular"),
   ("estoy viendo una serie", "¿*;serie"), ("una de policías", "policias;" + N),
   ("en junio me voy de viaje", "¿*;adonde|donde"), ("todavía no lo sé", Q + ";" + N), ("¿cuándo me voy de viaje?", "junio")]},
 {"id": "w-3", "cat": "Q_callar", "turnos": [
   ("soy Remedios", "remedios"),
   ("¿cuánto es 12 por 12?", "144;" + Q), ("¿qué es una sartén?", "utensilio|cocina|freir|objeto;" + Q),
   ("los martes tengo pilates", N + ";" + Q),
   ("mi gata se llama Luna", "luna;" + Q), ("tengo una gata", N + ";" + Q),
   ("voy a Burgos el jueves", N + ";!adonde"),
   ("prefiero que no me preguntes nada", N + ";" + Q),
   ("me han regalado un cachorro", N + ";" + Q), ("mañana me voy de excursión", N + ";" + Q), ("estoy preocupada", N + ";" + Q),
   ("ya puedes hacerme preguntas", N),
   ("tengo un sobrino", "¿*;como se llama"), ("mejor no", Q + ";" + N),
   ("Rosa y Manuel se han casado", N + ";!quien es"),
   ("el hierro es un metal", N + ";" + Q),
   ("bueno, me marcho, muchas gracias", "de nada|hasta|adios;" + Q)]},
 {"id": "w-4", "cat": "S_tono", "turnos": [
   ("soy Fidel", "fidel"),
   ("me han dado la beca", BUENO), ("¿me han dado la beca?", "^si"),
   ("se ha muerto mi perra", "lo siento;" + Q + ";!enhorabuena;!que bien"),
   ("mi hija se ha graduado", BUENO),
   ("me he torcido el tobillo", MALO + ";!enhorabuena"),
   ("he perdido el trabajo", MALO + ";!enhorabuena"),
   ("pasado mañana tengo las oposiciones", "suerte|animo"),
   ("no me han cogido en el trabajo", "!enhorabuena;!que bien;" + N),
   ("vamos a tener un hijo", BUENO),
   ("mi abuela está ingresada", MALO + "|espero;!enhorabuena"),
   ("tengo tres hermanos", "!enhorabuena;!lo siento;" + N),
   ("no tengo coche", "!lo siento;!enhorabuena;" + N),
   ("hoy cumplo cuarenta años", "felicidades|feliz|enhorabuena"),
   ("estoy muy agobiado", "¿*|cuentame|lo siento"), ("es que tengo muchísimo trabajo", N), ("¿por qué estoy agobiado?", "trabajo"),
   ("ya estoy más tranquilo", "me alegro|que bien")]},
 {"id": "w-5", "cat": "T_hilo", "turnos": [
   ("me llamo Begoña", "begona"), ("soy veterinaria", N), ("tengo 29 años", N),
   ("hazme una pregunta", "¿*;!como te llamas;!dedicas;!cuantos años"),
   ("en Oviedo", "oviedo;" + N), ("¿dónde vivo?", "oviedo"),
   ("el lunes empiezo un curso de cerámica", N), ("el sábado voy a un concierto", N),
   ("¿qué planes tengo?", "curso|ceramica;concierto"),
   ("¿de qué estábamos hablando?", "curso|ceramica|concierto|oviedo|veterinaria"),
   ("los miércoles tengo yoga", N), ("perdona, los jueves", "jueves;" + N), ("¿qué día tengo yoga?", "jueves;!miercoles"),
   ("cambiemos de tema", N), ("¿qué te falta por saber de mí?", "gusta|aficion*|tiempo libre|¿*|nada"),
   ("¿y tú qué tal estás?", "bien"),
   ("me tengo que ir, gracias por la charla", "de nada|hasta|adios;" + Q)]},
 {"id": "w-6", "cat": "U_pertinencia", "turnos": [
   ("hola, soy Ramiro", "ramiro"), ("mi marido se llama Esteban", "esteban"), ("Esteban es cocinero", N),
   ("tenemos tres hijos", "¿*;como se llaman"), ("Nico, Alba y Bruno", "nico|alba|bruno;" + N), ("¿cómo se llaman mis hijos?", "nico;alba;bruno"),
   ("los niños van al colegio en autobús", N), ("¿cómo van mis hijos al colegio?", "autobus"),
   ("a Alba le he comprado una bicicleta", N), ("¿qué le he comprado a Alba?", "bicicleta"),
   ("ayer se me estropeó la lavadora", MALO), ("ha venido el técnico", N), ("¿qué le pasó a la lavadora?", "estropeo|estropeada|estropea*"),
   ("¿qué sabes de mi familia?", "esteban;alba|nico|bruno"),
   ("¿a qué se dedica Esteban?", "cocinero"),
   ("¿un cocinero es una persona?", "^si;" + Q)]},
 {"id": "w-7", "cat": "V_verde", "turnos": [
   ("soy Leire", "leire"),
   ("trabajo con dos socias, Ainhoa y Maider", "ainhoa|maider;" + N), ("¿con quién trabajo?", "ainhoa;maider"),
   ("Ainhoa cocina mejor que Maider", N), ("Maider cocina mejor que Jon", N), ("¿quién cocina mejor, Ainhoa o Jon?", "ainhoa"),
   ("tenía 120 euros y me he gastado 45 en unas botas", N), ("¿cuánto me queda?", "75"),
   ("hoy ha sido un día rarísimo", N), ("es que se ha ido la luz en la oficina", N), ("¿por qué ha sido un día raro?", "luz"),
   ("a mi sobrino le flipan los dinosaurios", N), ("¿qué le gusta a mi sobrino?", "dinosaurio*"),
   ("voy al gimnasio los lunes", N), ("no, los martes", "martes;" + N), ("¿cuándo voy al gimnasio?", "martes;!lunes"),
   ("ayer cené con mi prima Abril", "abril;!cenaste abril"), ("¿cómo se llama mi prima?", "abril"),
   ("me han puesto una multa", MALO + ";" + N), ("¿me han puesto una multa?", "^si"),
   ("venga, hasta otro día", "hasta|adios;" + Q)]},
 {"id": "w-8", "cat": "P_preguntar", "turnos": [
   ("soy Casimiro", "casimiro"),
   ("me he apuntado a clases de quendo", "¿*;quendo"), ("es un arte marcial", N), ("¿qué es el quendo?", "arte marcial|marcial"),
   ("el mes que viene me mudo", "¿*;adonde|donde"), ("a un piso más grande, en Getafe", "getafe|piso;" + N), ("¿adónde me mudo?", "getafe|piso"),
   ("tengo pareja", "¿*;como se llama"), ("se llama Noa", "noa;" + N), ("¿cómo se llama mi pareja?", "noa"),
   ("ayer fui al médico", "¿*|espero;encuentras|estas bien|paso|que te"), ("tenía fiebre", "lo siento|vaya|espero|mejor*|fiebre;" + N),
   ("el sábado tengo una boda", "¿*;quien"), ("la de mi amigo Roque", "roque;" + N), ("¿de quién es la boda?", "roque")]},
]

def medir(verboso=False, salida="lab/res_ciego17b.json"):
    return correr(D, verboso=verboso, salida=salida)

def main():
    f, r = medir(verboso=True)
    imprime(r, "EXAMEN CIEGO 17b (conversaciones, medida limpia)")

if __name__ == "__main__":
    main()
