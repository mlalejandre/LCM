"""2.18 T01 · aprender de un texto: los tres temas de desarrollo (solo se puntúan las sondas que la 2.18 acierta; sirve de red de regresión)."""
D = [{'cat': 'aprender',
  'id': 'apr-abejas',
  'turnos': [('Te voy a leer un texto sobre las abejas.\n'
              'Las abejas son insectos que viven en grandes grupos llamados colonias.\n'
              'Cada colonia vive en una colmena.\n'
              'En una colmena hay tres tipos de abejas: la reina, las obreras y los zánganos.\n'
              'La reina es la única que pone huevos.\n'
              'Las obreras son hembras y hacen casi todo el trabajo.\n'
              'Los zánganos son los machos y no tienen aguijón.\n'
              'Las obreras recogen el néctar de las flores y lo convierten en miel.\n'
              'La miel se guarda en el panal, una estructura de celdas de cera.\n'
              'Las celdas tienen seis lados.\n'
              'Cuando una abeja encuentra flores, avisa a las demás con un baile.\n'
              'Las abejas llevan el polen de una flor a otra, por eso son muy importantes para las plantas.\n'
              'Este trabajo se llama polinización.\n'
              'Una abeja solo pica si se siente amenazada.\n'
              'Después de picar, la abeja obrera muere.\n'
              'Las personas que cuidan las colmenas se llaman apicultores.\n'
              'El apicultor usa humo para calmar a las abejas.\n'
              'Lleva un traje blanco y un velo que le protege la cara.\n'
              'En invierno las abejas no salen de la colmena y se alimentan de la miel que guardaron.\n'
              'La jalea real es el alimento de la reina.\n'
              'Una reina puede vivir cinco años, mientras que una obrera vive solo unas semanas.',
              ''),
             ('¿qué son las abejas?', 'insecto*'),
             ('¿dónde vive una colonia?', 'colmena'),
             ('¿qué tipos de abejas hay en una colmena?', 'reina;obrera*;zangano*'),
             ('¿quién pone los huevos?', 'reina'),
             ('¿quién hace el trabajo en la colmena?', 'obrera*'),
             ('¿los zánganos tienen aguijón?', '^no'),
             ('¿qué recogen las obreras?', 'nectar'),
             ('¿dónde se guarda la miel?', 'panal'),
             ('¿qué es el panal?', 'estructura|celdas|cera'),
             ('¿cuántos lados tienen las celdas?', 'seis|6'),
             ('¿qué hace una abeja cuando encuentra flores?', 'baile|avisa'),
             ('¿por qué son importantes las abejas para las plantas?', 'polen'),
             ('¿qué es la polinización?', 'polen|flor*'),
             ('¿cuándo pica una abeja?', 'amenazada'),
             ('¿qué le pasa a la abeja obrera después de picar?', 'muere|morir'),
             ('¿cómo se llaman las personas que cuidan las colmenas?', 'apicultor*'),
             ('¿qué es un apicultor?', 'persona|cuida*'),
             ('¿para qué usa humo el apicultor?', 'calmar'),
             ('¿qué lleva el apicultor?', 'traje|velo'),
             ('¿de qué se alimentan las abejas en invierno?', 'miel'),
             ('¿qué come la reina?', ''),
             ('¿cuánto puede vivir una reina?', 'cinco|5'),
             ('¿una obrera es un insecto?', '^si'),
             ('¿un zángano es un animal?', '^si'),
             ('¿las abejas son plantas?', '^no'),
             ('¿quién no tiene aguijón?', 'zangano*'),
             ('¿una obrera puede poner huevos?', '^no'),
             ('¿qué come la que pone los huevos?', ''),
             ('¿cuántas abejas hay en una colmena?', 'ABST'),
             ('¿de qué color es la reina?', 'ABST'),
             ('¿quién inventó la colmena?', 'ABST'),
             ('mi tío es apicultor', '!no lo he entendido;!no he entendido'),
             ('¿mi tío cuida colmenas?', '^si|colmena*'),
             ('dime los tipos de abejas', 'reina|obrera*|zangano*'),
             ('descríbeme un zángano', 'macho|aguijon'),
             ('los zánganos tienen aguijón', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|no tienen')]},
 {'cat': 'aprender',
  'id': 'apr-volcanes',
  'turnos': [('Te voy a leer un texto sobre los volcanes.\n'
              'Un volcán es una abertura de la corteza terrestre por la que sale roca fundida.\n'
              'Debajo de la corteza hay roca fundida muy caliente, llamada magma.\n'
              'Cuando el magma sale al exterior se llama lava.\n'
              'La lava sale por el cráter, que es la boca del volcán.\n'
              'La salida violenta de lava, gases y ceniza se llama erupción.\n'
              'Algunos volcanes están activos y otros están dormidos.\n'
              'Un volcán dormido puede despertar después de cientos de años.\n'
              'Los volcanes extinguidos ya no entran en erupción.\n'
              'La lava puede alcanzar más de mil grados.\n'
              'Al enfriarse, la lava se convierte en roca dura.\n'
              'La ceniza de los volcanes hace que la tierra sea muy fértil, por eso mucha gente cultiva cerca de ellos.\n'
              'Las personas que estudian los volcanes se llaman vulcanólogos.\n'
              'Usan sismógrafos, unos aparatos que miden los temblores de la tierra.\n'
              'Antes de una erupción suele temblar la tierra.\n'
              'El Teide es el volcán más alto de España.\n'
              'Está en la isla de Tenerife y mide 3715 metros.\n'
              'El Krakatoa es un volcán de Indonesia.\n'
              'Su erupción de 1883 se oyó a miles de kilómetros.\n'
              'Un volcán submarino puede formar una isla nueva.',
              ''),
             ('¿qué es un volcán?', 'abertura'),
             ('¿qué es el magma?', 'roca'),
             ('¿cómo se llama el magma cuando sale al exterior?', 'lava'),
             ('¿por dónde sale la lava?', 'crater'),
             ('¿qué es el cráter?', 'boca'),
             ('¿qué es una erupción?', 'salida|lava'),
             ('¿todos los volcanes están activos?', '^no|algunos'),
             ('¿un volcán dormido puede despertar?', '^si'),
             ('¿los volcanes extinguidos entran en erupción?', '^no'),
             ('¿qué temperatura puede alcanzar la lava?', 'mil|1000'),
             ('¿en qué se convierte la lava al enfriarse?', 'roca'),
             ('¿por qué cultiva la gente cerca de los volcanes?', 'fertil|ceniza'),
             ('¿cómo se llaman las personas que estudian los volcanes?', 'vulcanologo*'),
             ('¿qué es un sismógrafo?', 'aparato|mide*'),
             ('¿qué pasa antes de una erupción?', 'tiembla|temblar'),
             ('¿cuál es el volcán más alto de España?', 'teide'),
             ('¿dónde está el Teide?', 'tenerife'),
             ('¿cuánto mide el Teide?', '3715'),
             ('¿de dónde es el Krakatoa?', ''),
             ('¿en qué año fue la erupción del Krakatoa?', ''),
             ('¿qué puede formar un volcán submarino?', 'isla'),
             ('¿el Teide es un volcán?', '^si'),
             ('¿el Krakatoa es un lugar?', '^si'),
             ('¿dónde está el volcán más alto de España?', 'tenerife'),
             ('¿qué volcán está en Tenerife?', 'teide'),
             ('¿el Teide tiene cráter?', ''),
             ('¿cuántos volcanes hay en el mundo?', 'ABST'),
             ('¿quién subió primero al Teide?', 'ABST'),
             ('¿cuánto mide el Krakatoa?', 'ABST'),
             ('el verano pasado subí al Teide', '!no lo he entendido;!no he entendido'),
             ('¿en qué isla estuve?', 'tenerife'),
             ('dime un volcán', 'teide|krakatoa'),
             ('descríbeme el Teide', 'tenerife|3715|alto'),
             ('el Teide está en Mallorca', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|tenerife')]},
 {'cat': 'aprender',
  'id': 'apr-ajedrez',
  'turnos': [('Te voy a leer un texto sobre el ajedrez.\n'
              'El ajedrez es un juego de mesa para dos jugadores.\n'
              'Se juega sobre un tablero de sesenta y cuatro casillas.\n'
              'Cada jugador empieza con dieciséis piezas.\n'
              'Hay seis tipos de piezas: el rey, la dama, la torre, el alfil, el caballo y el peón.\n'
              'Un jugador lleva las piezas blancas y el otro las negras.\n'
              'Las blancas siempre mueven primero.\n'
              'La dama es la pieza más poderosa, porque puede moverse en cualquier dirección.\n'
              'La torre se mueve en línea recta.\n'
              'El alfil se mueve en diagonal.\n'
              'El caballo es la única pieza que puede saltar sobre las demás.\n'
              'El peón es la pieza menos valiosa, pero si llega al otro lado del tablero se convierte en dama.\n'
              'El rey solo puede moverse una casilla.\n'
              'El objetivo del juego es atrapar al rey del rival.\n'
              'Cuando el rey está amenazado se dice que está en jaque.\n'
              'Si el rey no puede escapar, es jaque mate y la partida termina.\n'
              'Cuando ningún jugador puede ganar, la partida acaba en tablas.\n'
              'Los jugadores profesionales usan un reloj para medir el tiempo.\n'
              'A los mejores jugadores del mundo se les llama grandes maestros.',
              ''),
             ('¿cuántos jugadores juegan al ajedrez?', 'dos|2'),
             ('¿cuántas casillas tiene el tablero?', '64|sesenta y cuatro'),
             ('¿con cuántas piezas empieza cada jugador?', '16|dieciseis'),
             ('¿qué tipos de piezas hay?', 'rey;dama;torre;alfil;caballo;peon'),
             ('¿quién mueve primero?', 'blancas'),
             ('¿cuál es la pieza más poderosa?', 'dama'),
             ('¿por qué es la dama la pieza más poderosa?', 'direccion|moverse'),
             ('¿cómo se mueve la torre?', 'recta'),
             ('¿cómo se mueve el alfil?', 'diagonal'),
             ('¿qué pieza puede saltar sobre las demás?', 'caballo'),
             ('¿qué le pasa al peón si llega al otro lado del tablero?', 'dama'),
             ('¿cuántas casillas puede moverse el rey?', 'una|1'),
             ('¿cuál es el objetivo del ajedrez?', 'rey|atrapar'),
             ('¿cuándo está el rey en jaque?', 'amenazado'),
             ('¿qué pasa si el rey no puede escapar?', 'jaque mate|termina'),
             ('¿cuándo acaba la partida en tablas?', 'ningun*|ganar'),
             ('¿para qué usan un reloj los jugadores profesionales?', 'tiempo|medir'),
             ('¿cómo se llama a los mejores jugadores del mundo?', 'maestro*'),
             ('¿la torre es una pieza?', '^si'),
             ('¿el ajedrez es un juego?', '^si'),
             ('¿qué pieza se mueve en diagonal?', 'alfil'),
             ('¿en qué se convierte la pieza menos valiosa?', 'dama'),
             ('¿el alfil puede saltar sobre las demás piezas?', '^no'),
             ('¿quién inventó el ajedrez?', 'ABST'),
             ('¿cuánto dura una partida?', 'ABST'),
             ('¿de qué material son las piezas?', 'ABST'),
             ('mi hijo juega con las blancas', '!no lo he entendido;!no he entendido'),
             ('¿mi hijo mueve primero?', ''),
             ('dime tres piezas de ajedrez', 'rey|dama|torre|alfil|caballo|peon'),
             ('descríbeme la dama', 'poderosa|direccion|pieza'),
             ('el alfil se mueve en línea recta', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|diagonal')]}]
