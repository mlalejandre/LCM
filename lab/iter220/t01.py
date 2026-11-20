"""2.20 T01 · preguntar por el sentido: paráfrasis y trampas sobre temas ya medidos (solo las sondas que la 2.20 acierta; red de regresión)."""
D = [{'cat': 'aprender-sentido',
  'id': 'apr220-p-abejas',
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
             ('¿qué emplea el apicultor para calmar a las abejas?', 'humo'),
             ('¿dónde se almacena la miel?', 'panal'),
             ('¿qué transportan las abejas de una flor a otra?', 'polen'),
             ('¿cuándo fallece la abeja obrera?', 'picar'),
             ('¿qué utiliza el apicultor para tranquilizar a las abejas?', 'humo'),
             ('¿las abejas residen en colmenas?', '^si|colmena'),
             ('¿quién fabrica las colmenas?', 'ABST'),
             ('¿quién descubrió la miel?', 'ABST'),
             ('¿qué beben las abejas?', 'ABST')]},
 {'cat': 'aprender-sentido',
  'id': 'apr220-p-volcanes',
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
             ('¿quiénes investigan los volcanes?', 'vulcanologo*'),
             ('¿qué aparatos emplean los vulcanólogos?', 'sismografo*'),
             ('¿por dónde brota la lava?', 'crater'),
             ('¿qué miden los sismógrafos?', 'temblores'),
             ('¿cuánto mide el Teide?', '3715'),
             ('¿quién descubrió el Teide?', 'ABST'),
             ('¿cuánto pesa la lava?', 'ABST'),
             ('¿quién fabrica los sismógrafos?', 'ABST')]},
 {'cat': 'aprender-sentido',
  'id': 'apr220-p-ajedrez',
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
             ('¿con cuántas piezas comienza cada jugador?', 'dieciseis|16'),
             ('¿qué pieza se desplaza en diagonal?', 'alfil'),
             ('¿qué emplean los jugadores profesionales para medir el tiempo?', 'reloj'),
             ('¿cuándo finaliza la partida?', 'jaque mate|escapar'),
             ('¿quién inventó el ajedrez?', 'ABST'),
             ('¿cuánto cuesta un tablero?', 'ABST')]},
 {'cat': 'aprender-sentido',
  'id': 'apr220-p-murciélagos',
  'turnos': [('Te voy a leer un texto sobre los murciélagos.\n'
              'Los murciélagos son los únicos mamíferos que pueden volar.\n'
              'Sus alas son en realidad manos con dedos muy largos, unidos por una piel fina.\n'
              'Duermen de día, colgados boca abajo en cuevas y árboles huecos.\n'
              'Salen a cazar por la noche.\n'
              'La mayoría de los murciélagos comen insectos, pero algunos comen fruta.\n'
              'Un solo murciélago puede comer mil mosquitos en una noche.\n'
              'Para orientarse en la oscuridad emiten sonidos muy agudos y escuchan su eco.\n'
              'Este sistema se llama ecolocalización.\n'
              'Las personas no podemos oír esos sonidos.\n'
              'En invierno, cuando no hay insectos, muchos murciélagos hibernan.\n'
              'Las crías nacen en primavera y se agarran a su madre durante las primeras semanas.\n'
              'Un grupo de murciélagos se llama colonia.\n'
              'El zorro volador es el murciélago más grande del mundo.\n'
              'Sus alas abiertas miden más de un metro y medio.\n'
              'El vampiro es un murciélago de América que se alimenta de sangre.\n'
              'Los murciélagos son muy útiles, porque se comen los insectos que dañan las cosechas.\n'
              'Las personas que estudian los murciélagos se llaman quiropterólogos.\n'
              'Algunos murciélagos viven más de treinta años.',
              ''),
             ('¿qué ingieren los murciélagos?', 'insectos|fruta'),
             ('¿cuándo descansan los murciélagos?', 'dia'),
             ('¿quiénes investigan los murciélagos?', 'quiropterologo*'),
             ('¿cuándo salen a capturar?', 'noche'),
             ('¿quién pinta a los murciélagos?', 'ABST'),
             ('¿qué beben los murciélagos?', 'ABST')]},
 {'cat': 'aprender-sentido',
  'id': 'apr220-p-café',
  'turnos': [('Te voy a leer un texto sobre el café.\n'
              'El café se hace con las semillas de una planta llamada cafeto.\n'
              'El cafeto es un arbusto que crece en países cálidos y lluviosos.\n'
              'Sus frutos son rojos y se llaman cerezas de café.\n'
              'Dentro de cada cereza hay dos semillas, que son los granos de café.\n'
              'Los granos se secan al sol durante varias semanas.\n'
              'Después se tuestan en un horno, y entonces toman su color marrón y su olor.\n'
              'Los granos tostados se muelen hasta convertirlos en polvo.\n'
              'Para preparar la bebida se hace pasar agua caliente por el café molido.\n'
              'El café contiene cafeína, una sustancia que quita el sueño.\n'
              'Por eso mucha gente lo toma por la mañana.\n'
              'El café sin cafeína se llama descafeinado.\n'
              'Un café solo no lleva leche.\n'
              'El cortado lleva un poco de leche y el café con leche lleva mucha.\n'
              'Brasil es el país que más café produce.\n'
              'Las personas que preparan café en las cafeterías se llaman baristas.\n'
              'Un buen barista sabe dibujar figuras con la espuma de la leche.\n'
              'Los médicos recomiendan no tomar más de cuatro tazas al día.',
              ''),
             ('¿dónde se tuestan los granos?', 'horno'),
             ('¿qué sustancia tiene el café?', 'cafeina'),
             ('¿cuándo lo bebe mucha gente?', 'manana'),
             ('¿quién descubrió el café?', 'ABST'),
             ('¿cuánto cuesta un café?', 'ABST')]},
 {'cat': 'aprender-sentido',
  'id': 'apr220-p-faros',
  'turnos': [('Te voy a leer un texto sobre los faros.\n'
              'Un faro es una torre alta con una luz muy potente en la parte de arriba.\n'
              'Los faros se construyen en la costa, cerca de las rocas peligrosas.\n'
              'Sirven para guiar a los barcos durante la noche.\n'
              'La luz de un faro gira y se ve desde muy lejos.\n'
              'Cada faro tiene un ritmo de destellos distinto, y así los marineros saben dónde están.\n'
              'Cuando hay niebla, la luz no se ve y el faro hace sonar una sirena.\n'
              'Antiguamente los faros funcionaban con fuego y aceite.\n'
              'Hoy casi todos son eléctricos y se encienden solos.\n'
              'La persona que cuidaba un faro se llamaba farero.\n'
              'El farero vivía en el faro con su familia y encendía la luz cada tarde.\n'
              'Era un trabajo muy solitario.\n'
              'La Torre de Hércules es el faro más antiguo del mundo que todavía funciona.\n'
              'Está en La Coruña y la construyeron los romanos.\n'
              'Algunos faros viejos se han convertido en hoteles y otros en museos.\n'
              'Los faros pintados a rayas se distinguen mejor de día.',
              ''),
             ('¿dónde se edifican los faros?', 'costa'),
             ('¿dónde residía el farero?', 'faro'),
             ('¿para qué se utilizan los faros?', 'guiar|barcos'),
             ('¿en qué se han transformado algunos faros viejos?', 'hoteles|museos'),
             ('¿quién inventó el faro?', 'ABST'),
             ('¿quién derribó la Torre de Hércules?', 'ABST')]},
 {'cat': 'aprender-sentido',
  'id': 'apr220-p-la Luna',
  'turnos': [('Te voy a leer un texto sobre la Luna.\n'
              'La Luna es el único satélite natural de la Tierra.\n'
              'Tarda unos veintisiete días en dar una vuelta alrededor de nuestro planeta.\n'
              'No tiene luz propia: brilla porque refleja la luz del Sol.\n'
              'En la Luna no hay aire ni agua líquida.\n'
              'Por eso allí no puede vivir ningún ser vivo.\n'
              'Su superficie está cubierta de polvo gris y de cráteres.\n'
              'Los cráteres son agujeros que dejaron los meteoritos al chocar.\n'
              'La Luna siempre nos muestra la misma cara.\n'
              'Según cuánta luz recibe, la vemos con formas distintas, llamadas fases.\n'
              'Cuando la vemos entera se llama luna llena.\n'
              'Cuando no se ve se llama luna nueva.\n'
              'La Luna provoca las mareas, que son las subidas y bajadas del mar.\n'
              'Neil Armstrong fue la primera persona que pisó la Luna.\n'
              'Llegó en 1969 en la nave Apolo 11.\n'
              'En la Luna las cosas pesan seis veces menos que en la Tierra.\n'
              'Las personas que viajan al espacio se llaman astronautas.',
              ''),
             ('¿cuánto demora la Luna en dar una vuelta?', 'veintisiete|27'),
             ('¿qué causa las mareas?', 'luna'),
             ('¿cuándo arribó Armstrong a la Luna?', '1969'),
             ('¿hay vida en Marte?', 'ABST'),
             ('¿quién descubrió la Luna?', 'ABST')]},
 {'cat': 'aprender-sentido',
  'id': 'apr220-p-pingüinos',
  'turnos': [('Te voy a leer un texto sobre los pingüinos.\n'
              'Los pingüinos son aves que no pueden volar.\n'
              'Usan sus alas como aletas para nadar bajo el agua.\n'
              'Casi todos viven en el hemisferio sur, sobre todo en la Antártida.\n'
              'Se alimentan de peces, calamares y pequeños crustáceos.\n'
              'Una gruesa capa de grasa los protege del frío.\n'
              'En tierra caminan despacio, pero en el agua son muy rápidos.\n'
              'El pingüino emperador es el pingüino más grande que existe.\n'
              'Mide más de un metro y pesa unos cuarenta kilos.\n'
              'La hembra pone un solo huevo y el macho lo cuida durante dos meses.\n'
              'Durante ese tiempo el macho no come nada.\n'
              'Los pingüinos viven en grupos muy grandes llamados colonias.\n'
              'Cuando hace mucho frío, se juntan todos para darse calor.\n'
              'Las crías nacen cubiertas de un plumón gris.\n'
              'Su peor enemigo en el mar es la foca leopardo.\n'
              'El pingüino de las Galápagos es el único que vive cerca del ecuador.\n'
              'Las personas que estudian las aves se llaman ornitólogos.',
              ''),
             ('¿quiénes investigan las aves?', 'ornitologo*'),
             ('¿quién caza a los ornitólogos?', 'ABST'),
             ('¿qué beben los pingüinos?', 'ABST')]},
 {'cat': 'aprender-sentido',
  'id': 'apr220-p-el pan',
  'turnos': [('Te voy a leer un texto sobre el pan.\n'
              'El pan se hace con harina, agua, sal y levadura.\n'
              'La harina es el polvo que se obtiene al moler el trigo.\n'
              'Primero se mezclan los ingredientes hasta formar una masa.\n'
              'Después la masa se deja reposar unas horas.\n'
              'Durante el reposo la levadura produce gas, y por eso la masa crece.\n'
              'Este proceso se llama fermentación.\n'
              'Por último la masa se cuece en un horno muy caliente.\n'
              'La parte de fuera del pan se llama corteza y la de dentro se llama miga.\n'
              'La corteza es dura y crujiente, mientras que la miga es blanda.\n'
              'El pan integral se hace con el grano entero y tiene más fibra.\n'
              'El pan de molde es blando y se vende cortado en rebanadas.\n'
              'La baguette es una barra de pan larga y fina, típica de Francia.\n'
              'El pan duro no se tira: sirve para hacer torrijas y sopas.\n'
              'Las personas que hacen pan se llaman panaderos.\n'
              'Un panadero empieza a trabajar de madrugada para que el pan esté listo por la mañana.',
              ''),
             ('¿con qué se elabora el pan?', 'harina'),
             ('¿quiénes elaboran el pan?', 'panadero*'),
             ('¿cuándo comienza a trabajar un panadero?', 'madrugada'),
             ('¿qué genera la levadura?', 'gas'),
             ('¿para qué se utiliza el pan duro?', 'torrijas|sopas'),
             ('¿quién inventó el pan?', 'ABST'),
             ('¿cuánto cuesta una barra de pan?', 'ABST')]},
 {'cat': 'aprender-sentido',
  'id': 'apr220-t5-el vidrio',
  'turnos': [('Te voy a leer un texto sobre el vidrio.\n'
              'El vidrio es un material duro y transparente que se rompe con facilidad.\n'
              'Se fabrica con arena, que se calienta en un horno hasta que se funde.\n'
              'El horno alcanza más de mil grados.\n'
              'Cuando el vidrio está fundido parece miel espesa.\n'
              'Los sopladores son los artesanos que dan forma al vidrio soplando por un tubo largo.\n'
              'El tubo se llama caña.\n'
              'Al enfriarse, el vidrio se vuelve duro.\n'
              'Con vidrio se hacen botellas, vasos, ventanas y espejos.\n'
              'Un espejo es un vidrio con una capa de plata por detrás.\n'
              'El vidrio se puede reciclar muchas veces sin perder calidad.\n'
              'Las botellas usadas se echan al contenedor verde.\n'
              'En la fábrica las botellas viejas se trituran y se funden otra vez.\n'
              'Los romanos ya usaban vasos de vidrio.\n'
              'Murano es una isla de Italia famosa por sus sopladores.\n'
              'El vidrio de las gafas se llama lente.',
              ''),
             ('¿qué es el vidrio?', 'material'),
             ('¿cómo es el vidrio?', 'duro|transparente'),
             ('¿con qué se fabrica el vidrio?', 'arena'),
             ('¿cuántos grados alcanza el horno?', 'mil|1000'),
             ('¿qué parece el vidrio cuando está fundido?', 'miel'),
             ('¿qué son los sopladores?', 'artesanos'),
             ('¿quiénes dan forma al vidrio?', 'sopladores|artesanos'),
             ('¿cómo se llama el tubo?', 'cana'),
             ('¿cuándo se vuelve duro el vidrio?', 'enfriarse|enfria*'),
             ('¿qué se hace con vidrio?', 'botellas|vasos|ventanas|espejos'),
             ('¿qué es un espejo?', 'vidrio|plata'),
             ('¿el vidrio se puede reciclar?', '^si'),
             ('¿dónde se echan las botellas usadas?', 'contenedor|verde'),
             ('¿dónde se trituran las botellas viejas?', 'fabrica'),
             ('¿quiénes usaban ya vasos de vidrio?', 'romanos'),
             ('¿qué es Murano?', 'isla'),
             ('¿por qué es famosa Murano?', 'sopladores'),
             ('¿cómo se llama el vidrio de las gafas?', 'lente'),
             ('¿un soplador es un artesano?', '^si'),
             ('¿con qué se elabora el vidrio?', 'arena'),
             ('¿dónde se tiran las botellas usadas?', 'contenedor|verde'),
             ('¿quiénes utilizaban ya vasos de vidrio?', 'romanos'),
             ('¿dónde se muelen las botellas viejas?', 'fabrica'),
             ('¿el vidrio se quiebra con facilidad?', '^si|rompe'),
             ('¿quién inventó el vidrio?', 'ABST'),
             ('¿cuánto cuesta un espejo?', 'ABST'),
             ('¿quién limpia las ventanas?', 'ABST'),
             ('¿dónde se venden las botellas?', 'ABST'),
             ('¿quién pinta los vasos?', 'ABST'),
             ('¿cuánto pesa una botella?', 'ABST'),
             ('mi primo es soplador', '!no lo he entendido;!no he entendido'),
             ('¿mi primo da forma al vidrio?', '^si|forma'),
             ('descríbeme el vidrio', 'material|duro|transparente|arena')]},
 {'cat': 'aprender-sentido',
  'id': 'apr220-t5-el correo',
  'turnos': [('Te voy a leer un texto sobre el correo.\n'
              'El correo es el servicio que lleva cartas y paquetes de un lugar a otro.\n'
              'La persona que reparte las cartas se llama cartero.\n'
              'Para enviar una carta hay que meterla en un sobre y pegarle un sello.\n'
              'El sello es una estampa pequeña que demuestra que el envío está pagado.\n'
              'En el sobre se escribe la dirección del destinatario, que es la persona que recibe la carta.\n'
              'La persona que envía la carta se llama remitente.\n'
              'Las cartas se echan al buzón, que en España es amarillo.\n'
              'Los carteros recogen las cartas de los buzones cada mañana.\n'
              'Después las cartas se clasifican en una oficina según su código postal.\n'
              'El código postal es un número que indica la zona de destino.\n'
              'Antiguamente el correo viajaba a caballo y tardaba semanas.\n'
              'Hoy las cartas viajan en furgonetas, trenes y aviones.\n'
              'Las palomas mensajeras llevaban mensajes atados a una pata.\n'
              'Un paquete urgente llega en un solo día.\n'
              'Las personas que coleccionan sellos se llaman filatélicos.',
              ''),
             ('¿qué es el correo?', 'servicio'),
             ('¿qué lleva el correo?', 'cartas|paquetes'),
             ('¿cómo se llama la persona que reparte las cartas?', 'cartero'),
             ('¿qué hay que pegarle al sobre?', 'sello'),
             ('¿qué es un sello?', 'estampa'),
             ('¿quién es el destinatario?', 'recibe|persona'),
             ('¿cómo se llama la persona que envía la carta?', 'remitente'),
             ('¿dónde se echan las cartas?', 'buzon'),
             ('¿cuándo recogen las cartas los carteros?', 'manana'),
             ('¿dónde se clasifican las cartas?', 'oficina'),
             ('¿qué es el código postal?', 'numero'),
             ('¿cómo viajaba el correo antiguamente?', 'caballo'),
             ('¿en qué viajan hoy las cartas?', 'furgonetas|trenes|aviones'),
             ('¿qué llevaban las palomas mensajeras?', 'mensajes'),
             ('¿cómo se llaman las personas que coleccionan sellos?', 'filatelico*'),
             ('¿un cartero es una persona?', '^si'),
             ('¿el destinatario es una persona?', '^si'),
             ('¿un filatélico es una persona?', '^si'),
             ('¿quién entrega las cartas?', 'cartero*'),
             ('¿qué transportaban las palomas mensajeras?', 'mensajes'),
             ('¿quiénes juntan sellos?', 'filatelico*'),
             ('¿qué transporta el correo?', 'cartas|paquetes'),
             ('¿un cartero recoge cartas?', '^si|recoge*'),
             ('¿quién inventó el sello?', 'ABST'),
             ('¿cuánto cuesta un sello?', 'ABST'),
             ('¿quién fabrica los buzones?', 'ABST'),
             ('¿quién lee las cartas?', 'ABST'),
             ('¿dónde duermen las palomas mensajeras?', 'ABST'),
             ('¿cuánto pesa un paquete urgente?', 'ABST'),
             ('mi vecina es cartera', '!no lo he entendido;!no he entendido'),
             ('¿mi vecina reparte cartas?', '^si|reparte*'),
             ('dime en qué viajan hoy las cartas', 'furgonetas|trenes|aviones'),
             ('descríbeme el correo', 'servicio|cartas|paquetes')]},
 {'cat': 'aprender-sentido',
  'id': 'apr220-t6-la lana',
  'turnos': [('Te voy a leer un texto sobre la lana.\n'
              'La lana es el pelo de las ovejas.\n'
              'Los pastores cuidan los rebaños en el campo.\n'
              'Un rebaño es un grupo de ovejas.\n'
              'En primavera se corta la lana a las ovejas con unas tijeras grandes.\n'
              'Este trabajo se llama esquila.\n'
              'La esquila no hace daño al animal.\n'
              'Después la lana se lava para quitarle la grasa.\n'
              'La lana limpia se peina y se convierte en hilo.\n'
              'El lugar donde se teje el hilo se llama telar.\n'
              'Con lana se hacen jerséis, bufandas y mantas.\n'
              'La lana abriga mucho, por eso se usa en invierno.\n'
              'La oveja merina es la oveja que da la lana más fina.\n'
              'Una oveja da unos cuatro kilos de lana al año.\n'
              'Las crías de la oveja se llaman corderos.',
              ''),
             ('¿qué es la lana?', 'pelo'),
             ('¿quiénes cuidan los rebaños?', 'pastor*'),
             ('¿qué es un rebaño?', 'grupo|ovejas'),
             ('¿cuándo se corta la lana?', 'primavera'),
             ('¿con qué se corta la lana?', 'tijeras'),
             ('¿cómo se llama este trabajo?', 'esquila'),
             ('¿la esquila hace daño al animal?', '^no'),
             ('¿para qué se lava la lana?', 'grasa|quitar*'),
             ('¿en qué se convierte la lana limpia?', 'hilo'),
             ('¿cómo se llama el lugar donde se teje el hilo?', 'telar'),
             ('¿dónde se teje el hilo?', 'telar'),
             ('¿qué se hace con lana?', 'jerseis|bufandas|mantas'),
             ('¿por qué se usa la lana en invierno?', 'abriga'),
             ('¿qué oveja da la lana más fina?', 'merina'),
             ('¿cuánta lana da una oveja al año?', 'cuatro|4'),
             ('¿cómo se llaman las crías de la oveja?', 'cordero*'),
             ('¿un pastor es una persona?', '^si'),
             ('¿una oveja es un animal?', '^si'),
             ('¿en qué se transforma la lana limpia?', 'hilo'),
             ('¿cuándo se emplea la lana?', 'invierno'),
             ('¿cuánta lana produce una oveja al año?', 'cuatro|4'),
             ('¿cómo se llama el trabajo de cortar la lana?', 'esquila'),
             ('¿quién inventó el telar?', 'ABST'),
             ('¿cuánto cuesta un jersey?', 'ABST'),
             ('¿quién compra la lana?', 'ABST'),
             ('¿dónde duermen los pastores?', 'ABST'),
             ('¿qué beben las ovejas?', 'ABST'),
             ('¿quién pinta las mantas?', 'ABST'),
             ('mi tío es pastor', '!no lo he entendido;!no he entendido'),
             ('¿mi tío cuida rebaños?', '^si|cuida*')]}]
