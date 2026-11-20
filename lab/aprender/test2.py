"""APRENDER · MEDIDA FINAL LIMPIA (2.18). Escrito con el código definitivo congelado (tras los arreglos no ciegos). Se mide UNA vez y no se toca nada después."""
N = "!no lo he entendido;!no he entendido"
K_ = "pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*"

FAROS = {"nombre": "faros", "intro": "Te voy a leer un texto sobre los faros.", "frases": [
 ("Un faro es una torre alta con una luz muy potente en la parte de arriba.", [("V", "¿qué es un faro?", "torre")]),
 ("Los faros se construyen en la costa, cerca de las rocas peligrosas.", [("L", "¿dónde se construyen los faros?", "costa|rocas")]),
 ("Sirven para guiar a los barcos durante la noche.", [("L", "¿para qué sirven los faros?", "guiar|barcos")]),
 ("La luz de un faro gira y se ve desde muy lejos.", [("L", "¿desde dónde se ve la luz de un faro?", "lejos")]),
 ("Cada faro tiene un ritmo de destellos distinto, y así los marineros saben dónde están.", [("D", "¿cómo saben los marineros dónde están?", "ritmo|destellos")]),
 ("Cuando hay niebla, la luz no se ve y el faro hace sonar una sirena.", [("D", "¿qué hace el faro cuando hay niebla?", "sirena")]),
 ("Antiguamente los faros funcionaban con fuego y aceite.", [("L", "¿con qué funcionaban los faros antiguamente?", "fuego|aceite")]),
 ("Hoy casi todos son eléctricos y se encienden solos.", []),
 ("La persona que cuidaba un faro se llamaba farero.", [("I", "¿cómo se llamaba la persona que cuidaba un faro?", "farero")]),
 ("El farero vivía en el faro con su familia y encendía la luz cada tarde.", [("L", "¿dónde vivía el farero?", "faro"), ("L", "¿cuándo encendía la luz el farero?", "tarde")]),
 ("Era un trabajo muy solitario.", []),
 ("La Torre de Hércules es el faro más antiguo del mundo que todavía funciona.", [("I", "¿cuál es el faro más antiguo del mundo?", "hercules")]),
 ("Está en La Coruña y la construyeron los romanos.", [("L", "¿dónde está la Torre de Hércules?", "coruna"), ("L", "¿quién construyó la Torre de Hércules?", "romanos")]),
 ("Algunos faros viejos se han convertido en hoteles y otros en museos.", [("D", "¿en qué se han convertido algunos faros viejos?", "hotel*|museo*")]),
 ("Los faros pintados a rayas se distinguen mejor de día.", [("L", "¿qué faros se distinguen mejor de día?", "rayas|pintados")]),
], "extra": [
 ("H", "¿un faro es una torre?", "^si"), ("H", "¿la Torre de Hércules es un faro?", "^si"), ("H", "¿un faro es un animal?", "^no"),
 ("M", "¿dónde está el faro más antiguo del mundo?", "coruna"), ("I", "¿qué faro está en La Coruña?", "hercules"),
 ("N", "¿cuántos faros hay en España?", "ABST"), ("N", "¿cuánto mide la Torre de Hércules?", "ABST"), ("N", "¿quién inventó el faro?", "ABST"),
 ("C", "mi bisabuelo era farero", N), ("C", "¿mi bisabuelo cuidaba un faro?", "^si|cuidaba|faro"),
 ("G", "dime un faro", "hercules"), ("G", "descríbeme la Torre de Hércules", "faro|antiguo|coruna|romanos"),
 ("K", "la Torre de Hércules está en Cádiz", K_ + "|coruna"),
]}

LUNA = {"nombre": "la Luna", "intro": "Te voy a leer un texto sobre la Luna.", "frases": [
 ("La Luna es el único satélite natural de la Tierra.", [("V", "¿qué es la Luna?", "satelite")]),
 ("Tarda unos veintisiete días en dar una vuelta alrededor de nuestro planeta.", [("L", "¿cuánto tarda la Luna en dar una vuelta a la Tierra?", "veintisiete|27")]),
 ("No tiene luz propia: brilla porque refleja la luz del Sol.", [("D", "¿por qué brilla la Luna?", "refleja|sol"), ("L", "¿la Luna tiene luz propia?", "^no")]),
 ("En la Luna no hay aire ni agua líquida.", [("L", "¿hay aire en la Luna?", "^no")]),
 ("Por eso allí no puede vivir ningún ser vivo.", [("D", "¿por qué no puede vivir ningún ser vivo en la Luna?", "aire|agua")]),
 ("Su superficie está cubierta de polvo gris y de cráteres.", [("L", "¿de qué está cubierta la superficie de la Luna?", "polvo|crater*")]),
 ("Los cráteres son agujeros que dejaron los meteoritos al chocar.", [("V", "¿qué son los cráteres?", "agujero*")]),
 ("La Luna siempre nos muestra la misma cara.", []),
 ("Según cuánta luz recibe, la vemos con formas distintas, llamadas fases.", [("V", "¿qué son las fases de la Luna?", "formas")]),
 ("Cuando la vemos entera se llama luna llena.", [("I", "¿cómo se llama la Luna cuando la vemos entera?", "llena")]),
 ("Cuando no se ve se llama luna nueva.", [("I", "¿cómo se llama la Luna cuando no se ve?", "nueva")]),
 ("La Luna provoca las mareas, que son las subidas y bajadas del mar.", [("V", "¿qué son las mareas?", "subidas|bajadas|mar"), ("L", "¿qué provoca la Luna?", "marea*")]),
 ("Neil Armstrong fue la primera persona que pisó la Luna.", [("I", "¿quién fue la primera persona que pisó la Luna?", "armstrong")]),
 ("Llegó en 1969 en la nave Apolo 11.", [("L", "¿en qué año llegó Armstrong a la Luna?", "1969")]),
 ("En la Luna las cosas pesan seis veces menos que en la Tierra.", [("L", "¿cuánto pesan las cosas en la Luna?", "seis|menos")]),
 ("Las personas que viajan al espacio se llaman astronautas.", [("I", "¿cómo se llaman las personas que viajan al espacio?", "astronauta*")]),
], "extra": [
 ("H", "¿la Luna es un satélite?", "^si"), ("H", "¿Neil Armstrong era una persona?", "^si"), ("H", "¿un astronauta es una persona?", "^si"),
 ("D", "¿hay vida en la Luna?", "^no"), ("M", "¿en qué nave llegó la primera persona que pisó la Luna?", "apolo"),
 ("N", "¿cuánto pesa la Luna?", "ABST"), ("N", "¿a qué distancia está la Luna?", "ABST"), ("N", "¿quién descubrió las mareas?", "ABST"),
 ("C", "mi vecina es astronauta", N), ("C", "¿mi vecina viaja al espacio?", "^si|viaja*"),
 ("G", "dime las fases de la Luna", "llena|nueva"), ("G", "descríbeme la Luna", "satelite|polvo|crater*|tierra"),
 ("K", "la Luna tiene luz propia", K_ + "|no tiene|refleja"),
]}

TEMAS = [FAROS, LUNA]
