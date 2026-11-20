"""2.17 T04 · conversaciones enteras, como las tendría una persona: todo mezclado."""
N = "!no lo he entendido;!no he entendido"
Q = "!¿*"
D = [
 {"id": "d1", "cat": "charla", "turnos": [
   ("hola", "hola"), ("soy Marcos", "marcos"), ("tengo 41 años y vivo en Zaragoza", N), ("trabajo de informático", N),
   ("mi mujer se llama Pilar", "pilar"), ("Pilar es enfermera", N), ("tenemos dos hijas", "¿*;como se llaman"), ("Carmen y Lola", "carmen|lola;" + N),
   ("Carmen tiene ocho años y Lola cinco", N), ("¿cuántos años tiene Lola?", "cinco|5"),
   ("este fin de semana vamos a la nieve", N), ("a las niñas les encanta esquiar", "carmen|hijas;!la niño"), ("¿a quién le gusta esquiar?", "carmen;lola"),
   ("ayer se me rompió el portátil", "lo siento|vaya"), ("se me cayó al suelo", N), ("¿qué le pasó a mi portátil?", "rompio|cayo"),
   ("el martes tengo dentista", N), ("¿qué planes tengo?", "nieve;dentista"),
   ("¿qué sabes de mi familia?", "pilar;carmen;lola"), ("¿a qué se dedica mi mujer?", "enfermera"),
   ("bueno, te dejo, gracias", "de nada|hasta;" + Q)]},
 {"id": "d2", "cat": "charla", "turnos": [
   ("buenas tardes", "buenas"), ("me llamo Rocío y soy profesora", "rocio|profesora"), ("doy clase en un instituto", N),
   ("hoy he tenido un día agotador", "lo siento|vaya|¿*|cuentame"), ("es que los alumnos estaban muy nerviosos", N), ("¿por qué he tenido un día agotador?", "alumnos|nerviosos"),
   ("mañana tienen un examen", N), ("este verano me voy de viaje", "¿*;adonde|donde"), ("a Japón, con mi hermana Abril", "japon|abril;" + N),
   ("¿con quién me voy de viaje?", "abril|hermana"), ("¿cómo se llama mi hermana?", "abril"), ("¿adónde me voy este verano?", "japon"),
   ("tengo un loro", "¿*;como se llama"), ("se llama Pirata y habla mucho", "pirata;" + N), ("¿quién habla mucho?", "pirata|loro"),
   ("pregúntame algo", "¿*"), ("no me apetece contestar", Q + ";" + N),
   ("¿de qué hemos hablado?", "japon|loro|instituto|examen|viaje"),
   ("hasta mañana", "hasta|adios;" + Q)]},
 {"id": "d3", "cat": "charla", "turnos": [
   ("hola, soy Julián", "julian"), ("estoy jubilado", N), ("antes era carpintero", N), ("¿a qué me dedicaba?", "carpintero"),
   ("mi nieto Leo viene a verme los domingos", N), ("¿cuándo viene Leo?", "domingos"), ("le he comprado un moflete", "¿*;moflete"),
   ("es un juguete de madera", N), ("¿qué es un moflete?", "juguete"), ("¿qué le he comprado a Leo?", "moflete|juguete"),
   ("me han operado de la cadera", N), ("ya estoy mucho mejor", "me alegro|que bien"),
   ("mi mujer murió hace dos años", "lo siento;" + Q), ("se llamaba Amparo", "amparo;" + Q),
   ("¿cómo se llamaba mi mujer?", "amparo"),
   ("gracias por escucharme", "de nada|gracias|gusto|placer|aqui;" + Q)]},
]
