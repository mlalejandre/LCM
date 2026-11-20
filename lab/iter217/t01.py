"""2.17 T01 · curiosidad por huecos: pregunta lo que falta e integra la respuesta."""
N = "!no lo he entendido;!no he entendido"
Q = "!¿*"
D = [
 {"id": "a1", "cat": "huecos", "turnos": [
   ("buenas, me llamo Lola", "lola"),
   ("nos vamos de vacaciones en agosto", "¿*;adonde|donde"),
   ("a Menorca", "menorca;" + N), ("¿adónde nos vamos de vacaciones?", "menorca"),
   ("hemos adoptado una perrita", "¿*;como se llama"), ("Nala", "nala;" + N), ("¿cómo se llama mi perrita?", "nala"),
   ("ayer me peleé con mi mejor amiga", "¿*;que paso|por que"), ("por una tontería", "tonteria;" + N), ("¿por qué me peleé con mi mejor amiga?", "tonteria"),
   ("tengo novio", "¿*;como se llama;!llaman"), ("Dani", "dani;" + N), ("¿cómo se llama mi novio?", "dani")]},
 {"id": "a2", "cat": "huecos", "turnos": [
   ("me he apuntado a clases de frupe", "¿*;frupe"), ("es un baile", N + ";" + Q), ("¿qué es el frupe?", "baile"),
   ("ayer vi una película", "¿*;pelicula"), ("una de miedo", "miedo;" + N),
   ("he quedado con Marta", "¿*;quien es marta"), ("una amiga del trabajo", "amiga;" + N), ("¿quién es Marta?", "amiga"),
   ("ayer tuve un examen", "¿*;que tal"), ("muy bien", "bien;" + N), ("¿qué tal me fue el examen?", "bien"),
   ("he encontrado trabajo", "enhorabuena|que bien|me alegro"), ("en una panadería", "panaderia;" + N), ("¿dónde he encontrado trabajo?", "panaderia")]},
 {"id": "a3", "cat": "huecos", "turnos": [
   ("soy Quique", "quique"),
   ("tengo tres gatos", "¿*;como se llaman"), ("Miso, Pelusa y Tom", "miso|pelusa|tom;" + N), ("¿cómo se llaman mis gatos?", "miso;pelusa;tom"),
   ("mañana voy al hospital", "¿*|espero"), ("van a operar a mi madre", N), 
   ("he comprado un trasto", "!que es un trasto"),
   ("me voy de excursión el domingo", "¿*;adonde|donde"), ("a la sierra con mis primos", "sierra|primos;" + N), ("¿con quién me voy de excursión?", "primos"),
   ("mi prima Elena vive en Lisboa", N), ("juego al tenis", N), ("me voy a Lisboa en mayo", "elena"),
   ("estoy leyendo un libro", "¿*;libro"), ("no me acuerdo", Q + ";" + N)]},
]
