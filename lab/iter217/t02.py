"""2.17 T02 · tono y contención: recibe la noticia como es y no pregunta cuando no toca."""
N = "!no lo he entendido;!no he entendido"
Q = "!¿*"
BUENO = "enhorabuena|felicidades|me alegro|que bien|que buena noticia"
MALO = "lo siento|vaya|que pena|animo"
D = [
 {"id": "b1", "cat": "tono", "turnos": [
   ("soy Aitana", "aitana"),
   ("mi hijo ha sacado un diez en matemáticas", BUENO),
   ("se me ha muerto el gato", "lo siento;" + Q + ";!enhorabuena"),
   ("me han robado el móvil", MALO + ";!sara;!robaste"),
   ("me caso en junio", BUENO),
   ("me he quedado embarazada", BUENO + ";embarazada"), ("¿estoy embarazada?", "^si"),
   ("no he aprobado el examen", MALO + ";!enhorabuena"),
   ("mañana me examino del carné", "suerte|animo"),
   ("me han operado de la rodilla", N + ";!suerte"), ("¿me han operado?", "^si"),
   ("gano 1500 euros al mes", "!enhorabuena;" + N),
   ("ayer gané el partido", BUENO),
   ("mi padre está en el hospital", N), ("le han operado de la rodilla", N + ";padre"), ("¿le han operado?", "^si"),
   ("me duele la cabeza", MALO + "|espero"),
   ("ya estoy curado", "me alegro|que bien|enhorabuena")]},
 {"id": "b2", "cat": "callar", "turnos": [
   ("me llamo Bruno", "bruno"),
   ("¿qué es un violín?", "instrumento;" + Q),
   ("deja de hacerme preguntas", N + ";" + Q),
   ("he adoptado un gato", N + ";" + Q), ("me mudo en verano", N + ";" + Q), ("estoy triste", N + ";" + Q),
   ("puedes preguntarme", N),
   ("tengo una hija", "¿*;como se llama"), ("no quiero decirlo", Q + ";" + N),
   ("tengo un hijo", Q + ";" + N),
   ("los pingüinos son aves", N + ";" + Q),
   ("recuerda que el martes tengo dentista", N + ";" + Q),
   ("Ana y Luis fueron al cine", N + ";" + Q),
   ("ayer cené con mis padres", N + ";" + Q),
   ("mi coche es rojo", N + ";" + Q),
   ("venga, hasta luego", "hasta|adios;" + Q)]},
]
