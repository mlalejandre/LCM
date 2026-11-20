"""APRENDER · SEGUNDA MEDIDA LIMPIA de la 2.22. Escrita con el código definitivo y sin ejecutarla; se mide UNA vez en cada versión (2.21 y 2.22),
con el texto pegado y frase a frase, y no se toca nada después."""
N = "!no lo he entendido;!no he entendido"
K_ = "pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*"

PUERTO = {"nombre": "el puerto", "intro": "Te voy a leer un texto sobre el puerto.", "frases": [
 ("Un puerto es un lugar de la costa donde atracan los barcos.", [("V", "¿qué es un puerto?", "lugar"), ("L", "¿qué atraca en un puerto?", "barcos")]),
 ("Los barcos se amarran al muelle con cuerdas gruesas.", [("L", "¿con qué se amarran los barcos?", "cuerdas")]),
 ("El muelle es una plataforma de piedra junto al agua.", [("V", "¿qué es el muelle?", "plataforma")]),
 ("Los estibadores cargan y descargan las mercancías.", [("L", "¿quiénes descargan las mercancías?", "estibador*")]),
 ("Las mercancías viajan en contenedores de metal.", [("L", "¿en qué viajan las mercancías?", "contenedor*")]),
 ("Una grúa levanta los contenedores más pesados.", [("L", "¿qué levanta una grúa?", "contenedor*")]),
 ("El faro avisa a los barcos durante la noche.", [("L", "¿cuándo avisa el faro a los barcos?", "noche")]),
 ("El práctico es el marino que guía a los barcos grandes hasta el muelle.", [("V", "¿qué es el práctico?", "marino")]),
 ("Sube a bordo antes de entrar en el puerto.", [("L", "¿cuándo sube a bordo el práctico?", "antes|entrar")]),
 ("El remolcador es un barco pequeño y muy potente.", [("V", "¿qué es el remolcador?", "barco")]),
 ("Empuja a los barcos grandes para que giren.", [("L", "¿a quién empuja el remolcador?", "barcos")]),
 ("Los pescadores salen del puerto a las cinco de la mañana.", [("L", "¿a qué hora salen los pescadores?", "cinco|5")]),
 ("Las personas que arreglan las redes se llaman rederas.", [("I", "¿cómo se llaman las personas que arreglan las redes?", "redera*")]),
], "extra": [
 ("H", "¿el remolcador es un barco?", "^si"), ("H", "¿el práctico es un marino?", "^si"), ("H", "¿el muelle es una plataforma?", "^si"), ("H", "¿el práctico es una persona?", "^si"),
 ("P", "¿quiénes reparan las redes?", "redera*"), ("P", "¿con qué se atan los barcos?", "cuerdas"), ("P", "¿qué alza una grúa?", "contenedor*"),
 ("M", "¿cuándo sube a bordo el marino que guía a los barcos grandes?", "antes|entrar"),
 ("N", "¿quién construyó el puerto?", "ABST"), ("N", "¿cuánto pesa un contenedor?", "ABST"), ("N", "¿quién pinta los barcos?", "ABST"),
 ("C", "mi tía es redera", N), ("C", "¿mi tía arregla las redes?", "^si|arregla*"),
 ("C", "mi primo es estibador", N), ("C", "¿mi primo descarga las mercancías?", "^si|descarga*"),
 ("G", "descríbeme el remolcador", "barco|pequeno|potente"),
 ("K", "los pescadores salen del puerto a las ocho de la mañana", K_ + "|cinco"), ("K", "el faro avisa a los barcos durante el día", K_ + "|noche"),
]}

TEMAS = [PUERTO]
