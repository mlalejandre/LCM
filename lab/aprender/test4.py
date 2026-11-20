"""APRENDER · MEDIDA FINAL LIMPIA de la 2.19. Escrito con el código definitivo congelado; se mide UNA vez en cada versión y no se toca nada después."""
N = "!no lo he entendido;!no he entendido"
K_ = "pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*"

OLIVO = {"nombre": "el olivo", "intro": "Te voy a leer un texto sobre el olivo.", "frases": [
 ("El olivo es un árbol de hoja perenne que crece en climas cálidos y secos.", [("V", "¿qué es el olivo?", "arbol"), ("L", "¿dónde crece el olivo?", "clima*|calido*|seco*")]),
 ("Su fruto es la aceituna.", [("L", "¿cuál es el fruto del olivo?", "aceituna")]),
 ("Las aceitunas verdes se recogen antes de madurar y las negras, cuando ya están maduras.", [("L", "¿cuándo se recogen las aceitunas verdes?", "antes|madurar")]),
 ("La recogida de la aceituna se hace en otoño y en invierno.", [("L", "¿cuándo se hace la recogida de la aceituna?", "otono|invierno")]),
 ("Para recogerlas se golpean las ramas con varas largas.", [("P", "¿cómo se recogen las aceitunas?", "varas|ramas|golpean")]),
 ("De las aceitunas se saca el aceite de oliva.", [("L", "¿qué se saca de las aceitunas?", "aceite")]),
 ("El lugar donde se fabrica el aceite se llama almazara.", [("I", "¿cómo se llama el lugar donde se fabrica el aceite?", "almazara"), ("V", "¿qué es una almazara?", "lugar|aceite")]),
 ("Allí las aceitunas se trituran y se prensan.", []),
 ("El aceite de oliva virgen extra es el aceite de mayor calidad.", [("I", "¿cuál es el aceite de mayor calidad?", "virgen extra")]),
 ("Un olivo puede vivir más de mil años.", [("L", "¿cuánto puede vivir un olivo?", "mil|1000")]),
 ("Los olivos tardan unos cinco años en dar sus primeros frutos.", [("L", "¿cuánto tardan los olivos en dar frutos?", "cinco|5")]),
 ("España es el país que más aceite de oliva produce.", [("I", "¿qué país produce más aceite de oliva?", "espana")]),
 ("La madera del olivo es muy dura y se usa para hacer cucharas y cuencos.", [("L", "¿para qué se usa la madera del olivo?", "cucharas|cuencos"), ("L", "¿cómo es la madera del olivo?", "dura")]),
 ("Las personas que cultivan olivos se llaman olivareros.", [("I", "¿cómo se llaman las personas que cultivan olivos?", "olivarero*")]),
 ("Una rama de olivo es un símbolo de paz.", [("L", "¿de qué es símbolo una rama de olivo?", "paz")]),
], "extra": [
 ("H", "¿el olivo es una planta?", "^si"), ("H", "¿un olivo es un ser vivo?", "^si"), ("H", "¿un olivo es un animal?", "^no"),
 ("P", "¿dónde se elabora el aceite?", "almazara"), ("D", "¿el olivo pierde las hojas en invierno?", "^no"), ("M", "¿de dónde se saca el aceite de mayor calidad?", "aceituna*"),
 ("N", "¿cuántos olivos hay en España?", "ABST"), ("N", "¿cuánto cuesta un litro de aceite?", "ABST"), ("N", "¿quién plantó el primer olivo?", "ABST"),
 ("C", "mi abuelo era olivarero", N), ("C", "¿mi abuelo cultivaba olivos?", "^si|cultiv*"),
 ("G", "dime dos tipos de aceitunas", "verde*;negra*"), ("G", "descríbeme el olivo", "arbol|aceituna|clima*|mil"),
 ("K", "la madera del olivo es muy blanda", K_ + "|dura"),
]}

TRENES = {"nombre": "los trenes", "intro": "Te voy a leer un texto sobre los trenes.", "frases": [
 ("Un tren es un conjunto de vagones arrastrados por una locomotora.", [("V", "¿qué es un tren?", "vagones|locomotora")]),
 ("Los trenes circulan sobre dos raíles de acero llamados vías.", [("V", "¿qué son las vías?", "railes|acero"), ("L", "¿sobre qué circulan los trenes?", "railes|vias")]),
 ("Las primeras locomotoras funcionaban con vapor y quemaban carbón.", [("L", "¿con qué funcionaban las primeras locomotoras?", "vapor|carbon")]),
 ("Hoy la mayoría de los trenes son eléctricos, aunque algunos usan gasóleo.", [("D", "¿todos los trenes son eléctricos?", "^no|mayoria|algunos")]),
 ("Los trenes eléctricos toman la corriente de un cable llamado catenaria.", [("V", "¿qué es la catenaria?", "cable"), ("L", "¿de dónde toman la corriente los trenes eléctricos?", "cable|catenaria")]),
 ("La persona que conduce un tren se llama maquinista.", [("I", "¿cómo se llama la persona que conduce un tren?", "maquinista")]),
 ("El revisor comprueba los billetes de los viajeros.", [("L", "¿quién comprueba los billetes?", "revisor")]),
 ("Los trenes paran en las estaciones para que suban y bajen los pasajeros.", [("L", "¿dónde paran los trenes?", "estacion*")]),
 ("El tren de alta velocidad puede superar los trescientos kilómetros por hora.", [("L", "¿qué velocidad puede superar el tren de alta velocidad?", "trescientos|300")]),
 ("Un tren de mercancías no lleva personas: transporta productos y materiales.", [("L", "¿qué transporta un tren de mercancías?", "productos|materiales"), ("L", "¿un tren de mercancías lleva personas?", "^no")]),
 ("El metro es un tren que circula bajo tierra en las grandes ciudades.", [("V", "¿qué es el metro?", "tren"), ("L", "¿por dónde circula el metro?", "bajo tierra|ciudades")]),
 ("El Transiberiano es el recorrido en tren más largo del mundo.", [("I", "¿cuál es el recorrido en tren más largo del mundo?", "transiberiano")]),
 ("Cruza Rusia de oeste a este y tarda siete días.", [("L", "¿cuánto tarda el Transiberiano?", "siete|7"), ("L", "¿qué país cruza el Transiberiano?", "rusia")]),
 ("Cuando un tren se acerca a un paso a nivel, bajan las barreras.", [("D", "¿qué pasa cuando un tren se acerca a un paso a nivel?", "barreras")]),
 ("El tren contamina menos que el coche, por eso es un transporte muy ecológico.", [("D", "¿por qué es el tren un transporte ecológico?", "contamina")]),
], "extra": [
 ("H", "¿el metro es un tren?", "^si"), ("H", "¿un tren es un vehículo?", "^si"), ("H", "¿un maquinista es una persona?", "^si"),
 ("P", "¿quién lleva un tren?", "maquinista"), ("M", "¿cuánto tarda el recorrido en tren más largo del mundo?", "siete|7"), ("D", "¿el metro circula sobre vías?", "^si"),
 ("N", "¿cuántos trenes hay en España?", "ABST"), ("N", "¿cuánto cuesta un billete de tren?", "ABST"), ("N", "¿quién inventó la locomotora?", "ABST"),
 ("C", "mi tía es maquinista", N), ("C", "¿mi tía conduce un tren?", "^si|conduce*"),
 ("G", "dime dos tipos de trenes", "electrico*|mercancias|alta velocidad|metro"), ("G", "descríbeme el metro", "tren|bajo tierra|ciudades"),
 ("K", "el Transiberiano tarda dos días", K_ + "|siete"),
]}

TEMAS = [OLIVO, TRENES]
