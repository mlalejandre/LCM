"""APRENDER · temas de DESARROLLO (2.18). Escritos antes de construir nada. Textos normales, sin adaptar al analizador.
Cada frase lleva sus sondas (tipo, pregunta, criterio); «extra» son preguntas de integración.
Tipos: L literal · P paráfrasis · I inversa · V vocabulario · H herencia · D deducción · M combinar · C charla · G uso · N no dicho · K contradicción"""
N = "!no lo he entendido;!no he entendido"
K_ = "pero|texto|contradic*|segun|no coincide|me habias|leido|lei"

ABEJAS = {"nombre": "abejas", "intro": "Te voy a leer un texto sobre las abejas.", "frases": [
 ("Las abejas son insectos que viven en grandes grupos llamados colonias.", [("L", "¿qué son las abejas?", "insecto*")]),
 ("Cada colonia vive en una colmena.", [("L", "¿dónde vive una colonia?", "colmena")]),
 ("En una colmena hay tres tipos de abejas: la reina, las obreras y los zánganos.", [("L", "¿qué tipos de abejas hay en una colmena?", "reina;obrera*;zangano*")]),
 ("La reina es la única que pone huevos.", [("L", "¿quién pone los huevos?", "reina")]),
 ("Las obreras son hembras y hacen casi todo el trabajo.", [("L", "¿quién hace el trabajo en la colmena?", "obrera*")]),
 ("Los zánganos son los machos y no tienen aguijón.", [("L", "¿los zánganos tienen aguijón?", "^no")]),
 ("Las obreras recogen el néctar de las flores y lo convierten en miel.", [("L", "¿qué recogen las obreras?", "nectar")]),
 ("La miel se guarda en el panal, una estructura de celdas de cera.", [("L", "¿dónde se guarda la miel?", "panal"), ("V", "¿qué es el panal?", "estructura|celdas|cera")]),
 ("Las celdas tienen seis lados.", [("L", "¿cuántos lados tienen las celdas?", "seis|6")]),
 ("Cuando una abeja encuentra flores, avisa a las demás con un baile.", [("D", "¿qué hace una abeja cuando encuentra flores?", "baile|avisa")]),
 ("Las abejas llevan el polen de una flor a otra, por eso son muy importantes para las plantas.", [("D", "¿por qué son importantes las abejas para las plantas?", "polen")]),
 ("Este trabajo se llama polinización.", [("V", "¿qué es la polinización?", "polen|flor*")]),
 ("Una abeja solo pica si se siente amenazada.", [("L", "¿cuándo pica una abeja?", "amenazada")]),
 ("Después de picar, la abeja obrera muere.", [("L", "¿qué le pasa a la abeja obrera después de picar?", "muere|morir")]),
 ("Las personas que cuidan las colmenas se llaman apicultores.", [("I", "¿cómo se llaman las personas que cuidan las colmenas?", "apicultor*"), ("V", "¿qué es un apicultor?", "persona|cuida*")]),
 ("El apicultor usa humo para calmar a las abejas.", [("L", "¿para qué usa humo el apicultor?", "calmar")]),
 ("Lleva un traje blanco y un velo que le protege la cara.", [("L", "¿qué lleva el apicultor?", "traje|velo")]),
 ("En invierno las abejas no salen de la colmena y se alimentan de la miel que guardaron.", [("L", "¿de qué se alimentan las abejas en invierno?", "miel")]),
 ("La jalea real es el alimento de la reina.", [("P", "¿qué come la reina?", "jalea")]),
 ("Una reina puede vivir cinco años, mientras que una obrera vive solo unas semanas.", [("L", "¿cuánto puede vivir una reina?", "cinco|5")]),
], "extra": [
 ("H", "¿una obrera es un insecto?", "^si"), ("H", "¿un zángano es un animal?", "^si"), ("H", "¿las abejas son plantas?", "^no"),
 ("I", "¿quién no tiene aguijón?", "zangano*"), ("D", "¿una obrera puede poner huevos?", "^no"), ("M", "¿qué come la que pone los huevos?", "jalea"),
 ("N", "¿cuántas abejas hay en una colmena?", "ABST"), ("N", "¿de qué color es la reina?", "ABST"), ("N", "¿quién inventó la colmena?", "ABST"),
 ("C", "mi tío es apicultor", N), ("C", "¿mi tío cuida colmenas?", "^si|colmena*"),
 ("G", "dime los tipos de abejas", "reina|obrera*|zangano*"), ("G", "descríbeme un zángano", "macho|aguijon"),
 ("K", "los zánganos tienen aguijón", K_ + "|no tienen"),
]}

VOLCANES = {"nombre": "volcanes", "intro": "Te voy a leer un texto sobre los volcanes.", "frases": [
 ("Un volcán es una abertura de la corteza terrestre por la que sale roca fundida.", [("V", "¿qué es un volcán?", "abertura")]),
 ("Debajo de la corteza hay roca fundida muy caliente, llamada magma.", [("V", "¿qué es el magma?", "roca")]),
 ("Cuando el magma sale al exterior se llama lava.", [("L", "¿cómo se llama el magma cuando sale al exterior?", "lava")]),
 ("La lava sale por el cráter, que es la boca del volcán.", [("L", "¿por dónde sale la lava?", "crater"), ("V", "¿qué es el cráter?", "boca")]),
 ("La salida violenta de lava, gases y ceniza se llama erupción.", [("V", "¿qué es una erupción?", "salida|lava")]),
 ("Algunos volcanes están activos y otros están dormidos.", [("D", "¿todos los volcanes están activos?", "^no|algunos")]),
 ("Un volcán dormido puede despertar después de cientos de años.", [("L", "¿un volcán dormido puede despertar?", "^si")]),
 ("Los volcanes extinguidos ya no entran en erupción.", [("L", "¿los volcanes extinguidos entran en erupción?", "^no")]),
 ("La lava puede alcanzar más de mil grados.", [("P", "¿qué temperatura puede alcanzar la lava?", "mil|1000")]),
 ("Al enfriarse, la lava se convierte en roca dura.", [("L", "¿en qué se convierte la lava al enfriarse?", "roca")]),
 ("La ceniza de los volcanes hace que la tierra sea muy fértil, por eso mucha gente cultiva cerca de ellos.", [("D", "¿por qué cultiva la gente cerca de los volcanes?", "fertil|ceniza")]),
 ("Las personas que estudian los volcanes se llaman vulcanólogos.", [("I", "¿cómo se llaman las personas que estudian los volcanes?", "vulcanologo*")]),
 ("Usan sismógrafos, unos aparatos que miden los temblores de la tierra.", [("V", "¿qué es un sismógrafo?", "aparato|mide*")]),
 ("Antes de una erupción suele temblar la tierra.", [("L", "¿qué pasa antes de una erupción?", "tiembla|temblar")]),
 ("El Teide es el volcán más alto de España.", [("I", "¿cuál es el volcán más alto de España?", "teide")]),
 ("Está en la isla de Tenerife y mide 3715 metros.", [("L", "¿dónde está el Teide?", "tenerife"), ("L", "¿cuánto mide el Teide?", "3715")]),
 ("El Krakatoa es un volcán de Indonesia.", [("L", "¿de dónde es el Krakatoa?", "indonesia")]),
 ("Su erupción de 1883 se oyó a miles de kilómetros.", [("L", "¿en qué año fue la erupción del Krakatoa?", "1883")]),
 ("Un volcán submarino puede formar una isla nueva.", [("L", "¿qué puede formar un volcán submarino?", "isla")]),
], "extra": [
 ("H", "¿el Teide es un volcán?", "^si"), ("H", "¿el Krakatoa es un lugar?", "^si"), ("M", "¿dónde está el volcán más alto de España?", "tenerife"),
 ("I", "¿qué volcán está en Tenerife?", "teide"), ("D", "¿el Teide tiene cráter?", "^si"),
 ("N", "¿cuántos volcanes hay en el mundo?", "ABST"), ("N", "¿quién subió primero al Teide?", "ABST"), ("N", "¿cuánto mide el Krakatoa?", "ABST"),
 ("C", "el verano pasado subí al Teide", N), ("C", "¿en qué isla estuve?", "tenerife"),
 ("G", "dime un volcán", "teide|krakatoa"), ("G", "descríbeme el Teide", "tenerife|3715|alto"),
 ("K", "el Teide está en Mallorca", K_ + "|tenerife"),
]}

AJEDREZ = {"nombre": "ajedrez", "intro": "Te voy a leer un texto sobre el ajedrez.", "frases": [
 ("El ajedrez es un juego de mesa para dos jugadores.", [("L", "¿cuántos jugadores juegan al ajedrez?", "dos|2")]),
 ("Se juega sobre un tablero de sesenta y cuatro casillas.", [("L", "¿cuántas casillas tiene el tablero?", "64|sesenta y cuatro")]),
 ("Cada jugador empieza con dieciséis piezas.", [("L", "¿con cuántas piezas empieza cada jugador?", "16|dieciseis")]),
 ("Hay seis tipos de piezas: el rey, la dama, la torre, el alfil, el caballo y el peón.", [("L", "¿qué tipos de piezas hay?", "rey;dama;torre;alfil;caballo;peon")]),
 ("Un jugador lleva las piezas blancas y el otro las negras.", []),
 ("Las blancas siempre mueven primero.", [("L", "¿quién mueve primero?", "blancas")]),
 ("La dama es la pieza más poderosa, porque puede moverse en cualquier dirección.", [("I", "¿cuál es la pieza más poderosa?", "dama"), ("D", "¿por qué es la dama la pieza más poderosa?", "direccion|moverse")]),
 ("La torre se mueve en línea recta.", [("L", "¿cómo se mueve la torre?", "recta")]),
 ("El alfil se mueve en diagonal.", [("L", "¿cómo se mueve el alfil?", "diagonal")]),
 ("El caballo es la única pieza que puede saltar sobre las demás.", [("I", "¿qué pieza puede saltar sobre las demás?", "caballo")]),
 ("El peón es la pieza menos valiosa, pero si llega al otro lado del tablero se convierte en dama.", [("D", "¿qué le pasa al peón si llega al otro lado del tablero?", "dama")]),
 ("El rey solo puede moverse una casilla.", [("L", "¿cuántas casillas puede moverse el rey?", "una|1")]),
 ("El objetivo del juego es atrapar al rey del rival.", [("P", "¿cuál es el objetivo del ajedrez?", "rey|atrapar")]),
 ("Cuando el rey está amenazado se dice que está en jaque.", [("D", "¿cuándo está el rey en jaque?", "amenazado")]),
 ("Si el rey no puede escapar, es jaque mate y la partida termina.", [("D", "¿qué pasa si el rey no puede escapar?", "jaque mate|termina")]),
 ("Cuando ningún jugador puede ganar, la partida acaba en tablas.", [("D", "¿cuándo acaba la partida en tablas?", "ningun*|ganar")]),
 ("Los jugadores profesionales usan un reloj para medir el tiempo.", [("L", "¿para qué usan un reloj los jugadores profesionales?", "tiempo|medir")]),
 ("A los mejores jugadores del mundo se les llama grandes maestros.", [("I", "¿cómo se llama a los mejores jugadores del mundo?", "maestro*")]),
], "extra": [
 ("H", "¿la torre es una pieza?", "^si"), ("H", "¿el ajedrez es un juego?", "^si"), ("I", "¿qué pieza se mueve en diagonal?", "alfil"),
 ("M", "¿en qué se convierte la pieza menos valiosa?", "dama"), ("D", "¿el alfil puede saltar sobre las demás piezas?", "^no"),
 ("N", "¿quién inventó el ajedrez?", "ABST"), ("N", "¿cuánto dura una partida?", "ABST"), ("N", "¿de qué material son las piezas?", "ABST"),
 ("C", "mi hijo juega con las blancas", N), ("C", "¿mi hijo mueve primero?", "^si"),
 ("G", "dime tres piezas de ajedrez", "rey|dama|torre|alfil|caballo|peon"), ("G", "descríbeme la dama", "poderosa|direccion|pieza"),
 ("K", "el alfil se mueve en línea recta", K_ + "|diagonal"),
]}

TEMAS = [ABEJAS, VOLCANES, AJEDREZ]
