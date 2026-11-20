"""2.17 T03 · el hilo: correcciones, continuaciones, causas y peticiones sobre la charla."""
N = "!no lo he entendido;!no he entendido"
Q = "!¿*"
D = [
 {"id": "c1", "cat": "hilo", "turnos": [
   ("soy Maite", "maite"),
   ("los martes voy a natación", N), ("no, los miércoles", "miercoles;" + N), ("¿cuándo voy a natación?", "miercoles;!martes"),
   ("vivo en Soria", N), ("perdón, en Segovia", "segovia;" + N), ("¿dónde vivo?", "segovia;!soria"),
   ("tengo 32 años", N), ("me he equivocado, 33", "33;" + N), ("¿cuántos años tengo?", "33"),
   ("ayer fui al teatro", N), ("con mi cuñada", "cunada|cuñada;" + N), ("¿con quién fui al teatro?", "cunada|cuñada"),
   ("hoy ha sido un día estupendo", "me alegro|que bien|¿*|cuentame"), ("es que me han subido el sueldo", N), ("¿por qué ha sido un día estupendo?", "sueldo")]},
 {"id": "c2", "cat": "hilo", "turnos": [
   ("me llamo Germán", "german"), ("soy electricista", N), ("vivo en Cádiz", N),
   ("hazme una pregunta", "¿*;!como te llamas;!dedicas;!donde vives"),
   ("hazme otra pregunta", "¿*"),
   ("¿qué te falta por saber de mí?", "edad|años|gusta"),
   ("¿por dónde íbamos?", "electricista|cadiz|german"),
   ("mejor cambiamos de tema", N),
   ("¿y tú cómo estás?", "bien"),
   ("mañana tengo una entrevista de trabajo", "suerte|animo"), ("estoy agobiado", N),
   ("¿qué me agobia?", "entrevista"),
   ("gracias por todo, me voy", "de nada|hasta|adios;" + Q)]},
 {"id": "c3", "cat": "verde", "turnos": [
   ("Irene nada más rápido que Paula", N), ("Paula nada más rápido que Berta", N), ("¿quién nada más rápido, Irene o Berta?", "irene"), ("¿quién nada más rápido, Berta o Paula?", "paula"),
   ("tenía 80 euros y me gasté 35 en la compra", N), ("¿cuánto me queda?", "45"),
   ("vivo con tres compañeros, Hugo, Íñigo y Saúl", "hugo|inigo|saul;" + N), ("¿con quién vivo?", "hugo;saul"),
   ("a mi hermana le chifla el sushi", N), ("¿qué le gusta a mi hermana?", "sushi"),
   ("ayer fui al cine con mi hermano Julio", "julio;!fuiste julio"), ("¿cómo se llama mi hermano?", "julio"),
   ("el sábado tengo una comida con mis suegros", N), ("¿con quién como el sábado?", "suegros"),
   ("que sepas que mañana no trabajo", N), ("¿trabajo mañana?", "^no")]},
]
