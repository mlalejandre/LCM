"""2.19 T01 · aprender de un texto: temas de las medidas anteriores (solo se puntúan las sondas que la 2.19 acierta; red de regresión)."""
D = [{'cat': 'aprender',
  'id': 'apr-murciélagos',
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
             ('¿los murciélagos pueden volar?', '^si'),
             ('¿cómo son las alas de los murciélagos?', 'manos|dedos|piel'),
             ('¿dónde duermen los murciélagos?', 'cueva*|arbol*'),
             ('¿cuándo duermen los murciélagos?', 'dia'),
             ('¿cuándo salen a cazar los murciélagos?', 'noche'),
             ('¿de qué se alimenta la mayoría de los murciélagos?', 'insecto*'),
             ('¿cuántos mosquitos puede comer un murciélago en una noche?', 'mil|1000'),
             ('¿cómo se orientan los murciélagos en la oscuridad?', 'sonido*|eco'),
             ('¿qué es la ecolocalización?', 'sonido*|eco|sistema'),
             ('¿qué hacen muchos murciélagos en invierno?', 'hiberna*'),
             ('¿cuándo nacen las crías?', 'primavera'),
             ('¿cómo se llama un grupo de murciélagos?', 'colonia'),
             ('¿cuál es el murciélago más grande del mundo?', 'zorro volador'),
             ('¿cuánto miden las alas del zorro volador?', ''),
             ('¿de qué se alimenta el vampiro?', 'sangre'),
             ('¿qué es un vampiro?', 'murcielago'),
             ('¿por qué son útiles los murciélagos?', 'insectos|cosechas'),
             ('¿cómo se llaman las personas que estudian los murciélagos?', 'quiropterologo*'),
             ('¿cuánto viven algunos murciélagos?', 'treinta|30'),
             ('¿un murciélago es un mamífero?', '^si'),
             ('¿el vampiro es un animal?', ''),
             ('¿los murciélagos son pájaros?', '^no'),
             ('¿cuánto miden las alas del murciélago más grande del mundo?', ''),
             ('¿qué murciélago se alimenta de sangre?', 'vampiro'),
             ('¿todos los murciélagos comen insectos?', '^no|mayoria|algunos'),
             ('¿cuántas especies de murciélagos hay?', 'ABST'),
             ('¿cuánto pesa un murciélago?', 'ABST'),
             ('¿quién descubrió la ecolocalización?', 'ABST'),
             ('anoche vi un murciélago en mi jardín', '!no lo he entendido;!no he entendido'),
             ('¿qué estaría haciendo?', ''),
             ('dime un murciélago', 'zorro volador|vampiro'),
             ('descríbeme el zorro volador', 'grande|metro|murcielago'),
             ('los murciélagos duermen de noche', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|de dia')]},
 {'cat': 'aprender',
  'id': 'apr-café',
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
             ('¿qué es el cafeto?', ''),
             ('¿dónde crece el cafeto?', 'paises|calido*|lluvios*'),
             ('¿de qué color son los frutos del cafeto?', ''),
             ('¿cuántas semillas hay dentro de cada cereza?', 'dos|2'),
             ('¿dónde se secan los granos?', 'sol'),
             ('¿qué les pasa a los granos cuando se tuestan?', 'marron|color|olor'),
             ('¿cómo se prepara la bebida?', 'agua caliente|molido'),
             ('¿qué es la cafeína?', 'sustancia|sueno'),
             ('¿qué contiene el café?', 'cafeina'),
             ('¿por qué toma mucha gente café por la mañana?', 'sueno|cafeina'),
             ('¿cómo se llama el café sin cafeína?', 'descafeinado'),
             ('¿un café solo lleva leche?', '^no'),
             ('¿qué lleva el cortado?', 'leche'),
             ('¿qué país produce más café?', 'brasil'),
             ('¿cómo se llaman las personas que preparan café en las cafeterías?', 'barista*'),
             ('¿qué sabe dibujar un buen barista?', 'figuras'),
             ('¿cuántas tazas recomiendan los médicos como máximo?', 'cuatro|4'),
             ('¿el cafeto es una planta?', '^si'),
             ('¿el cafeto es un ser vivo?', '^si'),
             ('¿el descafeinado es un café?', '^si'),
             ('¿cómo se llaman los frutos del arbusto del café?', 'cereza*'),
             ('¿el descafeinado quita el sueño?', ''),
             ('¿quién descubrió el café?', 'ABST'),
             ('¿cuánto cuesta un kilo de café?', 'ABST'),
             ('¿cuántos baristas hay en Brasil?', 'ABST'),
             ('mi prima es barista', '!no lo he entendido;!no he entendido'),
             ('¿mi prima prepara café?', '^si|prepara*'),
             ('dime dos tipos de café', 'solo|cortado|descafeinado|con leche'),
             ('descríbeme el cafeto', 'arbusto|planta|paises|frutos'),
             ('los frutos del cafeto son azules', '')]},
 {'cat': 'aprender',
  'id': 'apr-nurbos (inventado)',
  'turnos': [('Te voy a leer un texto sobre los nurbos.\n'
              'Los nurbos son unos animales pequeños que viven en las montañas de Talia.\n'
              'Tienen el pelo azul y una cola muy larga.\n'
              'Se alimentan de las hojas del árbol melco.\n'
              'El melco es un árbol que solo crece cerca de los ríos.\n'
              'Los nurbos viven en grupos llamados tirnas.\n'
              'Cada tirna tiene una jefa, que es la hembra más vieja.\n'
              'Cuando un nurbo ve un peligro, silba muy fuerte.\n'
              'Su peor enemigo es el dargo, un pájaro enorme de pico rojo.\n'
              'Los nurbos duermen durante todo el invierno en madrigueras profundas.\n'
              'Las crías se llaman nurbines y nacen con el pelo blanco.\n'
              'Los habitantes de Talia creen que ver un nurbo trae buena suerte.\n'
              'Por eso está prohibido cazarlos.\n'
              'El nurbo dorado es el más raro de todos.\n'
              'Solo vive en la cima del monte Arán.\n'
              'Las personas que cuidan a los nurbos se llaman nurberos.',
              ''),
             ('¿dónde viven los nurbos?', ''),
             ('¿qué son los nurbos?', 'animal*'),
             ('¿de qué color tienen el pelo los nurbos?', 'azul'),
             ('¿de qué se alimentan los nurbos?', 'hojas|melco'),
             ('¿dónde crece el melco?', 'rio*'),
             ('¿qué es una tirna?', 'grupo*'),
             ('¿quién es la jefa de una tirna?', 'hembra|vieja'),
             ('¿qué hace un nurbo cuando ve un peligro?', 'silba'),
             ('¿qué es un dargo?', 'pajaro'),
             ('¿cuál es el peor enemigo de los nurbos?', 'dargo'),
             ('¿dónde duermen los nurbos en invierno?', 'madriguera*'),
             ('¿cómo se llaman las crías de los nurbos?', 'nurbin*'),
             ('¿de qué color nacen los nurbines?', ''),
             ('¿qué creen los habitantes de Talia?', 'suerte'),
             ('¿por qué está prohibido cazar nurbos?', 'suerte'),
             ('¿cuál es el nurbo más raro?', 'dorado'),
             ('¿dónde vive el nurbo dorado?', 'aran|cima'),
             ('¿cómo se llaman las personas que cuidan a los nurbos?', 'nurbero*'),
             ('¿un nurbo es un animal?', '^si'),
             ('¿un nurbo es un ser vivo?', '^si'),
             ('¿el dargo es un animal?', '^si'),
             ('¿el melco es una planta?', '^si'),
             ('¿un nurbo tiene cola?', '^si'),
             ('¿de qué color es el pico del peor enemigo de los nurbos?', 'rojo'),
             ('¿cuántos nurbos quedan?', 'ABST'),
             ('¿cuánto pesa un nurbo?', 'ABST'),
             ('¿qué come el dargo?', 'ABST'),
             ('mi abuelo es nurbero', '!no lo he entendido;!no he entendido'),
             ('¿mi abuelo cuida nurbos?', '^si|cuida*'),
             ('descríbeme un nurbo', 'animal*|azul|cola|montana*'),
             ('dime un enemigo de los nurbos', ''),
             ('los nurbos tienen el pelo verde', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|azul')]},
 {'cat': 'aprender',
  'id': 'apr-faros',
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
             ('¿qué es un faro?', 'torre'),
             ('¿dónde se construyen los faros?', 'costa|rocas'),
             ('¿para qué sirven los faros?', 'guiar|barcos'),
             ('¿desde dónde se ve la luz de un faro?', 'lejos'),
             ('¿cómo saben los marineros dónde están?', 'ritmo|destellos'),
             ('¿qué hace el faro cuando hay niebla?', 'sirena'),
             ('¿con qué funcionaban los faros antiguamente?', 'fuego|aceite'),
             ('¿cómo se llamaba la persona que cuidaba un faro?', 'farero'),
             ('¿dónde vivía el farero?', 'faro'),
             ('¿cuándo encendía la luz el farero?', 'tarde'),
             ('¿cuál es el faro más antiguo del mundo?', 'hercules'),
             ('¿dónde está la Torre de Hércules?', 'coruna'),
             ('¿quién construyó la Torre de Hércules?', ''),
             ('¿en qué se han convertido algunos faros viejos?', 'hotel*|museo*'),
             ('¿qué faros se distinguen mejor de día?', 'rayas|pintados'),
             ('¿un faro es una torre?', '^si'),
             ('¿la Torre de Hércules es un faro?', '^si'),
             ('¿un faro es un animal?', '^no'),
             ('¿dónde está el faro más antiguo del mundo?', 'coruna'),
             ('¿qué faro está en La Coruña?', 'hercules'),
             ('¿cuántos faros hay en España?', 'ABST'),
             ('¿cuánto mide la Torre de Hércules?', 'ABST'),
             ('¿quién inventó el faro?', 'ABST'),
             ('mi bisabuelo era farero', '!no lo he entendido;!no he entendido'),
             ('¿mi bisabuelo cuidaba un faro?', '^si|cuidaba|faro'),
             ('dime un faro', 'hercules'),
             ('descríbeme la Torre de Hércules', 'faro|antiguo|coruna|romanos'),
             ('la Torre de Hércules está en Cádiz', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|coruna')]},
 {'cat': 'aprender',
  'id': 'apr-la Luna',
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
             ('¿qué es la Luna?', 'satelite'),
             ('¿cuánto tarda la Luna en dar una vuelta a la Tierra?', 'veintisiete|27'),
             ('¿por qué brilla la Luna?', 'refleja|sol'),
             ('¿la Luna tiene luz propia?', '^no'),
             ('¿hay aire en la Luna?', '^no'),
             ('¿por qué no puede vivir ningún ser vivo en la Luna?', 'aire|agua'),
             ('¿de qué está cubierta la superficie de la Luna?', 'polvo|crater*'),
             ('¿qué son los cráteres?', 'agujero*'),
             ('¿qué son las fases de la Luna?', 'formas'),
             ('¿cómo se llama la Luna cuando la vemos entera?', 'llena'),
             ('¿cómo se llama la Luna cuando no se ve?', 'nueva'),
             ('¿qué son las mareas?', 'subidas|bajadas|mar'),
             ('¿qué provoca la Luna?', 'marea*'),
             ('¿quién fue la primera persona que pisó la Luna?', 'armstrong'),
             ('¿en qué año llegó Armstrong a la Luna?', '1969'),
             ('¿cuánto pesan las cosas en la Luna?', 'seis|menos'),
             ('¿cómo se llaman las personas que viajan al espacio?', 'astronauta*'),
             ('¿la Luna es un satélite?', '^si'),
             ('¿Neil Armstrong era una persona?', '^si'),
             ('¿un astronauta es una persona?', '^si'),
             ('¿hay vida en la Luna?', ''),
             ('¿en qué nave llegó la primera persona que pisó la Luna?', 'apolo'),
             ('¿cuánto pesa la Luna?', 'ABST'),
             ('¿a qué distancia está la Luna?', 'ABST'),
             ('¿quién descubrió las mareas?', 'ABST'),
             ('mi vecina es astronauta', '!no lo he entendido;!no he entendido'),
             ('¿mi vecina viaja al espacio?', '^si|viaja*'),
             ('dime las fases de la Luna', ''),
             ('descríbeme la Luna', 'satelite|polvo|crater*|tierra'),
             ('la Luna tiene luz propia', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|no tiene|refleja')]},
 {'cat': 'aprender',
  'id': 'apr-pingüinos',
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
             ('¿los pingüinos pueden volar?', '^no'),
             ('¿qué son los pingüinos?', 'ave*'),
             ('¿para qué usan sus alas los pingüinos?', 'nadar'),
             ('¿dónde viven los pingüinos?', ''),
             ('¿qué comen los pingüinos?', 'peces|calamares|crustaceos'),
             ('¿qué protege a los pingüinos del frío?', 'grasa'),
             ('¿cómo son los pingüinos en el agua?', ''),
             ('¿cuál es el pingüino más grande?', 'emperador'),
             ('¿cuánto pesa el pingüino emperador?', 'cuarenta|40'),
             ('¿quién cuida el huevo?', 'macho'),
             ('¿cuántos huevos pone la hembra?', 'un|1'),
             ('¿qué es una colonia?', 'grupo*'),
             ('¿qué hacen los pingüinos cuando hace mucho frío?', 'juntan|calor'),
             ('¿de qué color es el plumón de las crías?', 'gris'),
             ('¿cuál es el peor enemigo de los pingüinos en el mar?', 'foca'),
             ('¿qué pingüino vive cerca del ecuador?', 'galapagos'),
             ('¿cómo se llaman las personas que estudian las aves?', 'ornitologo*'),
             ('¿un pingüino es un animal?', '^si'),
             ('¿el pingüino emperador es un ave?', '^si'),
             ('¿un pingüino es un pez?', '^no'),
             ('¿cuánto pesa el pingüino más grande?', 'cuarenta|40'),
             ('¿el pingüino emperador puede volar?', '^no'),
             ('¿cuántos pingüinos hay en la Antártida?', 'ABST'),
             ('¿cuánto vive un pingüino?', ''),
             ('¿quién descubrió la Antártida?', 'ABST'),
             ('mi hermana es ornitóloga', '!no lo he entendido;!no he entendido'),
             ('¿mi hermana estudia las aves?', '^si|estudia*'),
             ('dime un pingüino', 'emperador|galapagos'),
             ('descríbeme el pingüino emperador', 'grande|metro|kilos|pingüino|pinguino'),
             ('los pingüinos pueden volar', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|no pueden')]},
 {'cat': 'aprender',
  'id': 'apr-el pan',
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
             ('¿con qué se hace el pan?', 'harina;agua'),
             ('¿qué es la harina?', 'polvo'),
             ('¿cuánto se deja reposar la masa?', 'horas'),
             ('¿por qué crece la masa?', 'levadura|gas'),
             ('¿qué es la fermentación?', 'levadura|gas|masa|proceso'),
             ('¿dónde se cuece la masa?', 'horno'),
             ('¿cómo se llama la parte de fuera del pan?', 'corteza'),
             ('¿cómo es la miga?', 'blanda'),
             ('¿cómo es la corteza?', 'dura|crujiente'),
             ('¿con qué se hace el pan integral?', 'grano'),
             ('¿cómo se vende el pan de molde?', 'rebanadas|cortado'),
             ('¿qué es una baguette?', 'barra|pan'),
             ('¿de dónde es típica la baguette?', 'francia'),
             ('¿para qué sirve el pan duro?', 'torrijas|sopas'),
             ('¿cómo se llaman las personas que hacen pan?', 'panadero*'),
             ('¿cuándo empieza a trabajar un panadero?', 'madrugada'),
             ('¿el pan es un alimento?', '^si'),
             ('¿la baguette es un pan?', '^si'),
             ('¿un panadero es una persona?', '^si'),
             ('¿qué elabora un panadero?', 'pan'),
             ('¿el pan integral tiene fibra?', '^si'),
             ('¿cómo es la parte de dentro del pan?', ''),
             ('¿cuánto cuesta una barra de pan?', 'ABST'),
             ('¿quién inventó el pan?', 'ABST'),
             ('¿cuántos panaderos hay en Francia?', 'ABST'),
             ('mi padre era panadero', '!no lo he entendido;!no he entendido'),
             ('¿mi padre hacía pan?', '^si|hacia|pan'),
             ('dime dos tipos de pan', 'integral|molde|baguette'),
             ('descríbeme la corteza', 'dura|crujiente|fuera'),
             ('la miga es dura', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|blanda')]}]
