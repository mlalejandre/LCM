"""APRENDER · SEGUNDA MEDIDA LIMPIA de la 2.20. Escrita con el código definitivo congelado y sin ejecutarla; se mide UNA vez en cada versión y no
se toca nada después."""
N = "!no lo he entendido;!no he entendido"
K_ = "pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*"

LANA = {"nombre": "la lana", "intro": "Te voy a leer un texto sobre la lana.", "frases": [
 ("La lana es el pelo de las ovejas.", [("V", "¿qué es la lana?", "pelo"), ("L", "¿de qué animal es la lana?", "oveja*")]),
 ("Los pastores cuidan los rebaños en el campo.", [("L", "¿quiénes cuidan los rebaños?", "pastor*")]),
 ("Un rebaño es un grupo de ovejas.", [("V", "¿qué es un rebaño?", "grupo|ovejas")]),
 ("En primavera se corta la lana a las ovejas con unas tijeras grandes.", [("L", "¿cuándo se corta la lana?", "primavera"), ("L", "¿con qué se corta la lana?", "tijeras")]),
 ("Este trabajo se llama esquila.", [("I", "¿cómo se llama este trabajo?", "esquila")]),
 ("La esquila no hace daño al animal.", [("L", "¿la esquila hace daño al animal?", "^no")]),
 ("Después la lana se lava para quitarle la grasa.", [("L", "¿para qué se lava la lana?", "grasa|quitar*")]),
 ("La lana limpia se peina y se convierte en hilo.", [("L", "¿en qué se convierte la lana limpia?", "hilo")]),
 ("El lugar donde se teje el hilo se llama telar.", [("I", "¿cómo se llama el lugar donde se teje el hilo?", "telar"), ("L", "¿dónde se teje el hilo?", "telar")]),
 ("Con lana se hacen jerséis, bufandas y mantas.", [("L", "¿qué se hace con lana?", "jerseis|bufandas|mantas")]),
 ("La lana abriga mucho, por eso se usa en invierno.", [("D", "¿por qué se usa la lana en invierno?", "abriga")]),
 ("La oveja merina es la oveja que da la lana más fina.", [("I", "¿qué oveja da la lana más fina?", "merina")]),
 ("Una oveja da unos cuatro kilos de lana al año.", [("L", "¿cuánta lana da una oveja al año?", "cuatro|4")]),
 ("Las crías de la oveja se llaman corderos.", [("I", "¿cómo se llaman las crías de la oveja?", "cordero*")]),
], "extra": [
 ("H", "¿un pastor es una persona?", "^si"), ("H", "¿una oveja es un animal?", "^si"),
 ("P", "¿quiénes vigilan los rebaños?", "pastor*"), ("P", "¿para qué se limpia la lana?", "grasa|quitar*"), ("P", "¿en qué se transforma la lana limpia?", "hilo"),
 ("P", "¿la esquila lastima al animal?", "^no"), ("P", "¿qué se fabrica con lana?", "jerseis|bufandas|mantas"), ("P", "¿cuándo se emplea la lana?", "invierno"),
 ("P", "¿la lana calienta mucho?", "^si|abriga"), ("P", "¿cuánta lana produce una oveja al año?", "cuatro|4"),
 ("M", "¿cómo se llama el trabajo de cortar la lana?", "esquila"),
 ("N", "¿quién inventó el telar?", "ABST"), ("N", "¿cuánto cuesta un jersey?", "ABST"), ("N", "¿quién compra la lana?", "ABST"),
 ("N", "¿dónde duermen los pastores?", "ABST"), ("N", "¿qué beben las ovejas?", "ABST"), ("N", "¿quién pinta las mantas?", "ABST"),
 ("C", "mi tío es pastor", N), ("C", "¿mi tío cuida rebaños?", "^si|cuida*"),
 ("G", "dime dos cosas que se hacen con lana", "jerseis|bufandas|mantas"), ("K", "la lana se corta en otoño", K_ + "|primavera"),
]}

TEMAS = [LANA]
