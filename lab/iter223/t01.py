"""2.23 T01 · leer las frases que no se sostienen solas: temas del banco de lectura (solo las sondas que la 2.23 acierta; red de regresión)."""
D = [{'cat': 'aprender-lectura',
  'id': 'apr223-ldev-la guitarra',
  'turnos': [('Te voy a leer un texto sobre la guitarra.\n'
              'La guitarra es un instrumento de cuerda.\n'
              'Tiene seis cuerdas y una caja de madera.\n'
              'Se toca con los dedos o con una púa.\n'
              'La púa es una pieza pequeña de plástico.\n'
              'Las cuerdas se tensan con las clavijas y suenan al vibrar.\n'
              'El laúd es el antepasado de la guitarra.\n'
              'Llegó a España hace más de mil años.\n'
              'Los guitarristas afinan la guitarra antes de tocar y la guardan en una funda.\n'
              'Las personas que fabrican guitarras se llaman lutieres.\n'
              'Trabajan en un taller y tardan un mes en hacer una guitarra.',
              ''),
             ('¿qué es la guitarra?', 'instrumento'),
             ('¿cuántas cuerdas tiene la guitarra?', 'seis|6'),
             ('¿con qué se toca la guitarra?', 'dedos|pua'),
             ('¿qué es la púa?', 'pieza'),
             ('¿con qué se tensan las cuerdas?', 'clavijas'),
             ('¿cuándo suenan las cuerdas?', 'vibrar'),
             ('¿cuál es el antepasado de la guitarra?', 'laud'),
             ('¿cuándo llegó el laúd a España?', 'mil'),
             ('¿cuándo afinan la guitarra los guitarristas?', 'antes'),
             ('¿dónde guardan la guitarra los guitarristas?', 'funda'),
             ('¿cómo se llaman las personas que fabrican guitarras?', 'lutier*'),
             ('¿dónde trabajan los lutieres?', 'taller'),
             ('¿cuánto tardan los lutieres en hacer una guitarra?', 'mes'),
             ('¿cuándo llegó a España el antepasado de la guitarra?', 'mil'),
             ('la guitarra tiene cuatro cuerdas', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|seis'),
             ('¿cuánto cuesta una guitarra?', 'ABST'),
             ('¿quién inventó la púa?', 'ABST')]},
 {'cat': 'aprender-lectura',
  'id': 'apr223-ldev-los osos',
  'turnos': [('Te voy a leer un texto sobre los osos.\n'
              'Los osos son mamíferos grandes y fuertes.\n'
              'Viven en bosques y montañas.\n'
              'Comen frutos, miel y peces.\n'
              'En invierno duermen en una cueva.\n'
              'Este sueño largo se llama hibernación.\n'
              'El oso polar es el oso más grande del mundo.\n'
              'Vive en el Ártico y caza focas.\n'
              'Tiene el pelo blanco y la piel negra.\n'
              'Las crías de los osos se llaman oseznos y nacen en invierno.\n'
              'Se quedan con su madre durante dos años.\n'
              'Los osos tienen garras muy fuertes.\n'
              'Con ellas trepan a los árboles.',
              ''),
             ('¿qué son los osos?', 'mamifero*'),
             ('¿dónde viven los osos?', 'bosques|montanas'),
             ('¿qué comen los osos?', 'frutos|miel|peces'),
             ('¿dónde duermen los osos en invierno?', 'cueva'),
             ('¿cómo se llama este sueño largo?', 'hibernacion'),
             ('¿cuál es el oso más grande del mundo?', 'polar'),
             ('¿dónde vive el oso polar?', 'artico'),
             ('¿qué caza el oso polar?', 'focas'),
             ('¿de qué color tiene el pelo el oso polar?', 'blanco'),
             ('¿cómo se llaman las crías de los osos?', 'osezno*'),
             ('¿cuándo nacen los oseznos?', 'invierno'),
             ('¿cuánto tiempo se quedan los oseznos con su madre?', 'dos'),
             ('¿cómo son las garras de los osos?', 'fuertes'),
             ('¿a dónde trepan los osos?', 'arboles'),
             ('¿qué caza el oso más grande del mundo?', 'focas'),
             ('los oseznos se quedan con su madre durante cinco años', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|dos'),
             ('¿cuánto pesa un oso?', 'ABST'),
             ('¿quién cuida a los osos?', 'ABST')]},
 {'cat': 'aprender-lectura',
  'id': 'apr223-ldev-el molino',
  'turnos': [('Te voy a leer un texto sobre el molino.\n'
              'Un molino es una máquina que muele el grano.\n'
              'Los molinos de viento tienen cuatro aspas.\n'
              'Giran cuando sopla el viento.\n'
              'El grano se echa en la tolva.\n'
              'La tolva es un embudo de madera.\n'
              'Debajo hay dos piedras redondas llamadas muelas.\n'
              'Aplastan el grano y lo convierten en harina.\n'
              'La harina cae a un saco.\n'
              'El molinero es la persona que trabaja en el molino.\n'
              'Vigila las muelas y carga los sacos.\n'
              'Antiguamente cobraba una parte de la harina.',
              ''),
             ('¿qué es un molino?', 'maquina'),
             ('¿cuántas aspas tienen los molinos de viento?', 'cuatro|4'),
             ('¿dónde se echa el grano?', 'tolva'),
             ('¿qué es la tolva?', 'embudo'),
             ('¿qué hay debajo de la tolva?', 'piedras|muelas'),
             ('¿en qué convierten el grano las muelas?', 'harina'),
             ('¿dónde cae la harina?', 'saco'),
             ('¿quién es el molinero?', 'persona'),
             ('¿qué carga el molinero?', 'sacos'),
             ('¿qué cobraba el molinero antiguamente?', 'harina|parte'),
             ('los molinos de viento tienen ocho aspas', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|cuatro'),
             ('¿cuánto cuesta un saco de harina?', 'ABST'),
             ('¿quién construyó el molino?', 'ABST')]},
 {'cat': 'aprender-lectura',
  'id': 'apr223-ldev-la imprenta',
  'turnos': [('Te voy a leer un texto sobre la imprenta.\n'
              'La imprenta es una máquina que sirve para hacer muchas copias de un texto.\n'
              'Gutenberg la inventó hace más de quinientos años.\n'
              'Era un orfebre alemán.\n'
              'Antes los libros se copiaban a mano.\n'
              'Un monje tardaba un año en copiar un libro.\n'
              'Los tipos son piezas de metal con una letra cada una.\n'
              'Se colocan en fila y se cubren de tinta.\n'
              'Después se aprieta el papel contra ellos.\n'
              'La Biblia fue el primer libro impreso.\n'
              'Tenía más de mil páginas.\n'
              'Las personas que trabajaban en una imprenta se llamaban impresores.',
              ''),
             ('¿qué es la imprenta?', 'maquina'),
             ('¿quién inventó la imprenta?', 'gutenberg'),
             ('¿cómo se copiaban los libros antes?', 'mano'),
             ('¿cuánto tardaba un monje en copiar un libro?', 'ano'),
             ('¿qué son los tipos?', 'piezas'),
             ('¿de qué se cubren los tipos?', 'tinta'),
             ('¿qué se aprieta contra los tipos?', 'papel'),
             ('¿cuál fue el primer libro impreso?', 'biblia'),
             ('¿cuántas páginas tenía la Biblia?', 'mil'),
             ('¿cómo se llamaban las personas que trabajaban en una imprenta?', 'impresor*'),
             ('¿cuántas páginas tenía el primer libro impreso?', 'mil'),
             ('un monje tardaba un mes en copiar un libro', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|ano'),
             ('¿cuánto costaba un libro?', 'ABST'),
             ('¿dónde nació Gutenberg?', 'ABST')]},
 {'cat': 'aprender-lectura',
  'id': 'apr223-ldev-el té',
  'turnos': [('Te voy a leer un texto sobre el té.\n'
              'El té es una bebida que se hace con las hojas de una planta.\n'
              'Las hojas se recogen a mano y se secan al sol.\n'
              'Después se meten en agua caliente durante tres minutos.\n'
              'El té verde es el té que no se fermenta.\n'
              'Tiene un sabor suave.\n'
              'El té negro se fermenta durante varias horas.\n'
              'Es más fuerte y más oscuro.\n'
              'China es el país que más té produce.\n'
              'En Inglaterra se toma con leche.\n'
              'La tetera es el recipiente donde se prepara el té.\n'
              'Suele ser de porcelana.',
              ''),
             ('¿qué es el té?', 'bebida'),
             ('¿cómo se recogen las hojas?', 'mano'),
             ('¿dónde se secan las hojas?', 'sol'),
             ('¿cuánto tiempo se meten las hojas en agua caliente?', 'tres|3'),
             ('¿qué té no se fermenta?', 'verde'),
             ('¿qué sabor tiene el té verde?', 'suave'),
             ('¿cuánto se fermenta el té negro?', 'horas'),
             ('¿cómo es el té negro?', 'fuerte|oscuro'),
             ('¿qué país produce más té?', 'china'),
             ('¿con qué se toma el té en Inglaterra?', 'leche'),
             ('¿qué es la tetera?', 'recipiente'),
             ('¿de qué suele ser la tetera?', 'porcelana'),
             ('¿qué sabor tiene el té que no se fermenta?', 'suave'),
             ('las hojas se meten en agua caliente durante diez minutos', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|tres'),
             ('¿cuánto cuesta una tetera?', 'ABST'),
             ('¿quién descubrió el té?', 'ABST')]},
 {'cat': 'aprender-lectura',
  'id': 'apr223-ldev-los bomberos',
  'turnos': [('Te voy a leer un texto sobre los bomberos.\n'
              'Los bomberos son las personas que apagan los incendios.\n'
              'Llevan un casco y un traje que no se quema.\n'
              'Viajan en un camión rojo con una sirena.\n'
              'El camión lleva una escalera muy larga y mil litros de agua.\n'
              'La manguera es el tubo por el que sale el agua.\n'
              'Pesa mucho y la sujetan dos bomberos.\n'
              'El parque de bomberos es el edificio donde esperan los avisos.\n'
              'Allí duermen y entrenan cada día.\n'
              'Cuando suena la alarma bajan por una barra.\n'
              'También rescatan a personas atrapadas y a veces salvan animales.',
              ''),
             ('¿quiénes son los bomberos?', 'personas|apagan'),
             ('¿qué llevan los bomberos?', 'casco|traje'),
             ('¿en qué viajan los bomberos?', 'camion'),
             ('¿cuántos litros de agua lleva el camión?', 'mil'),
             ('¿qué es la manguera?', 'tubo'),
             ('¿cuántos bomberos sujetan la manguera?', 'dos|2'),
             ('¿qué es el parque de bomberos?', 'edificio'),
             ('¿cuándo entrenan los bomberos?', 'dia'),
             ('¿a quién rescatan los bomberos?', 'personas'),
             ('¿qué salvan a veces los bomberos?', 'animales'),
             ('el camión lleva cien litros de agua', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|mil'),
             ('¿cuánto cobra un bombero?', 'ABST'),
             ('¿quién fabrica las mangueras?', 'ABST')]},
 {'cat': 'aprender-lectura',
  'id': 'apr223-ltest-el violín',
  'turnos': [('Te voy a leer un texto sobre el violín.\n'
              'El violín es un instrumento de cuerda pequeño.\n'
              'Tiene cuatro cuerdas y se apoya en el hombro.\n'
              'Se toca con un arco.\n'
              'El arco es una vara de madera con crines de caballo.\n'
              'Se frota contra las cuerdas y las hace vibrar.\n'
              'Los violinistas estudian muchos años y ensayan cada día.\n'
              'Guardan el violín en un estuche.\n'
              'El Stradivarius es el violín más caro del mundo.\n'
              'Se fabricó hace trescientos años.',
              ''),
             ('¿qué es el violín?', 'instrumento'),
             ('¿cuántas cuerdas tiene el violín?', 'cuatro|4'),
             ('¿dónde se apoya el violín?', 'hombro'),
             ('¿con qué se toca el violín?', 'arco'),
             ('¿qué es el arco?', 'vara'),
             ('¿contra qué se frota el arco?', 'cuerdas'),
             ('¿cuándo ensayan los violinistas?', 'dia'),
             ('¿dónde guardan el violín los violinistas?', 'estuche'),
             ('¿cuál es el violín más caro del mundo?', 'stradivarius'),
             ('¿cuándo se fabricó el Stradivarius?', 'trescientos|300'),
             ('¿cuándo se fabricó el violín más caro del mundo?', 'trescientos|300'),
             ('el violín tiene seis cuerdas', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|cuatro'),
             ('¿cuánto cuesta un arco?', 'ABST'),
             ('¿quién inventó el violín?', 'ABST')]},
 {'cat': 'aprender-lectura',
  'id': 'apr223-ltest-los lobos',
  'turnos': [('Te voy a leer un texto sobre los lobos.\n'
              'Los lobos son mamíferos que viven en grupo.\n'
              'Cazan de noche y duermen de día.\n'
              'Un grupo de lobos se llama manada.\n'
              'Tiene un jefe y recorre muchos kilómetros.\n'
              'Las crías de los lobos se llaman lobeznos y nacen en primavera.\n'
              'Viven en una cueva durante dos meses.\n'
              'Los lobos tienen colmillos largos y afilados.\n'
              'Con ellos desgarran la carne.\n'
              'Cuando hay peligro aúllan muy fuerte.\n'
              'El lobo ártico es el lobo más blanco.\n'
              'Vive en el norte y aguanta mucho frío.',
              ''),
             ('¿qué son los lobos?', 'mamifero*'),
             ('¿cuándo cazan los lobos?', 'noche'),
             ('¿cuándo duermen los lobos?', 'dia'),
             ('¿cómo se llama un grupo de lobos?', 'manada'),
             ('¿cómo se llaman las crías de los lobos?', 'lobezno*'),
             ('¿cuándo nacen los lobeznos?', 'primavera'),
             ('¿dónde viven los lobeznos?', 'cueva'),
             ('¿cuánto tiempo viven los lobeznos en una cueva?', 'dos'),
             ('¿cómo son los colmillos de los lobos?', 'largos|afilados'),
             ('¿qué desgarran los lobos?', 'carne'),
             ('¿qué hacen los lobos cuando hay peligro?', 'aullan'),
             ('¿cuál es el lobo más blanco?', 'artico'),
             ('¿dónde vive el lobo ártico?', 'norte'),
             ('¿dónde vive el lobo más blanco?', 'norte'),
             ('los lobeznos viven en una cueva durante seis meses', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|dos'),
             ('¿cuánto pesa un lobo?', 'ABST'),
             ('¿quién cuida a los lobeznos?', 'ABST')]},
 {'cat': 'aprender-lectura',
  'id': 'apr223-ltest-la panadería',
  'turnos': [('Te voy a leer un texto sobre la panadería.\n'
              'La panadería es la tienda donde se vende el pan.\n'
              'Abre muy temprano y cierra a mediodía.\n'
              'El panadero amasa la harina y la deja reposar.\n'
              'Después mete la masa en el horno.\n'
              'El horno es de leña y alcanza doscientos grados.\n'
              'Dentro hay una pala larga de madera.\n'
              'El obrador es la sala donde se hace el pan.\n'
              'Allí trabajan tres panaderos y hace mucho calor.\n'
              'Las barras se colocan en cestas y se venden por la mañana.\n'
              'Las ensaimadas son bollos dulces en forma de espiral.\n'
              'Se cubren de azúcar.',
              ''),
             ('¿qué es la panadería?', 'tienda'),
             ('¿cuándo cierra la panadería?', 'mediodia'),
             ('¿qué amasa el panadero?', 'harina'),
             ('¿dónde mete la masa el panadero?', 'horno'),
             ('¿qué es el obrador?', 'sala'),
             ('¿cuántos panaderos trabajan en el obrador?', 'tres|3'),
             ('¿dónde se colocan las barras?', 'cestas'),
             ('¿cuándo se venden las barras?', 'manana'),
             ('¿de qué se cubren las ensaimadas?', 'azucar'),
             ('la panadería cierra por la noche', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|mediodia'),
             ('¿cuánto cuesta una barra?', 'ABST'),
             ('¿quién limpia el horno?', 'ABST')]},
 {'cat': 'aprender-lectura',
  'id': 'apr223-ltest-el telescopio',
  'turnos': [('Te voy a leer un texto sobre el telescopio.\n'
              'El telescopio es un aparato que sirve para ver objetos lejanos.\n'
              'Tiene dos lentes y un tubo largo.\n'
              'Las lentes son piezas de cristal curvo.\n'
              'Aumentan la imagen y la acercan al ojo.\n'
              'Galileo fue el primer astrónomo que miró el cielo con un telescopio.\n'
              'Los astrónomos son las personas que estudian las estrellas.\n'
              'Trabajan de noche y duermen por la mañana.\n'
              'El observatorio es el edificio donde están los telescopios grandes.\n'
              'Suele estar en una montaña y tiene una cúpula que se abre.\n'
              'El Hubble es el telescopio más famoso.\n'
              'Gira alrededor de la Tierra y pesa once toneladas.',
              ''),
             ('¿qué es el telescopio?', 'aparato'),
             ('¿cuántas lentes tiene el telescopio?', 'dos|2'),
             ('¿qué aumentan las lentes?', 'imagen'),
             ('¿quién fue el primer astrónomo que miró el cielo con un telescopio?', 'galileo'),
             ('¿cuándo trabajan los astrónomos?', 'noche'),
             ('¿qué es el observatorio?', 'edificio'),
             ('¿dónde suele estar el observatorio?', 'montana'),
             ('¿cuál es el telescopio más famoso?', 'hubble'),
             ('¿cuánto pesa el Hubble?', 'once|11'),
             ('¿cuánto pesa el telescopio más famoso?', 'once|11'),
             ('el telescopio tiene cinco lentes', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|dos'),
             ('¿cuánto cuesta un telescopio?', 'ABST'),
             ('¿quién construyó el Hubble?', 'ABST')]},
 {'cat': 'aprender-lectura',
  'id': 'apr223-ltest-el chocolate',
  'turnos': [('Te voy a leer un texto sobre el chocolate.\n'
              'El chocolate es un alimento que se hace con cacao.\n'
              'El cacao es el fruto de un árbol tropical.\n'
              'Sus semillas se secan al sol y se tuestan.\n'
              'Después se muelen hasta formar una pasta.\n'
              'La pasta se mezcla con azúcar y se vierte en moldes.\n'
              'El chocolate negro es el chocolate que lleva más cacao.\n'
              'Tiene un sabor amargo.\n'
              'El chocolate blanco no lleva cacao en polvo.\n'
              'Se hace con manteca de cacao y leche.\n'
              'Los chocolateros trabajan en un obrador fresco.\n'
              'Tardan dos días en hacer una tableta.',
              ''),
             ('¿qué es el chocolate?', 'alimento'),
             ('¿qué es el cacao?', 'fruto'),
             ('¿dónde se secan las semillas del cacao?', 'sol'),
             ('¿con qué se mezcla la pasta?', 'azucar'),
             ('¿dónde se vierte la pasta?', 'moldes'),
             ('¿qué chocolate lleva más cacao?', 'negro'),
             ('¿qué sabor tiene el chocolate negro?', 'amargo'),
             ('¿el chocolate blanco lleva cacao en polvo?', '^no'),
             ('¿con qué se hace el chocolate blanco?', 'manteca|leche'),
             ('¿dónde trabajan los chocolateros?', 'obrador'),
             ('¿cuánto tardan los chocolateros en hacer una tableta?', 'dos'),
             ('¿qué sabor tiene el chocolate que lleva más cacao?', 'amargo'),
             ('los chocolateros tardan dos horas en hacer una tableta', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|dias'),
             ('¿cuánto cuesta una tableta?', 'ABST'),
             ('¿quién descubrió el cacao?', 'ABST')]},
 {'cat': 'aprender-lectura',
  'id': 'apr223-ltest-los carpinteros',
  'turnos': [('Te voy a leer un texto sobre los carpinteros.\n'
              'Los carpinteros son las personas que trabajan la madera.\n'
              'Hacen mesas, sillas y puertas.\n'
              'Usan un serrucho y llevan un lápiz en la oreja.\n'
              'El serrucho es una sierra de mano con dientes de acero.\n'
              'Corta la madera cuando se mueve adelante y atrás.\n'
              'La carpintería es el taller donde trabajan los carpinteros.\n'
              'Huele a madera y tiene el suelo lleno de serrín.\n'
              'El serrín es el polvo que cae al cortar la madera.\n'
              'Se recoge cada tarde y se usa para hacer tableros.\n'
              'Las tablas se lijan antes de pintarlas.',
              ''),
             ('¿qué hacen los carpinteros?', 'mesas|sillas|puertas'),
             ('¿qué usan los carpinteros?', 'serrucho'),
             ('¿dónde llevan un lápiz los carpinteros?', 'oreja'),
             ('¿qué es el serrucho?', 'sierra'),
             ('¿qué corta el serrucho?', 'madera'),
             ('¿qué es la carpintería?', 'taller'),
             ('¿a qué huele la carpintería?', 'madera'),
             ('¿qué es el serrín?', 'polvo'),
             ('¿cuándo se recoge el serrín?', 'tarde'),
             ('¿para qué se usa el serrín?', 'tableros'),
             ('¿cuándo se lijan las tablas?', 'antes'),
             ('el serrín se recoge cada mañana', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|tarde'),
             ('¿cuánto cuesta un serrucho?', 'ABST'),
             ('¿quién barre la carpintería?', 'ABST')]}]
