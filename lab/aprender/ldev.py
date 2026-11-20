"""APRENDER · banco de LECTURA (desarrollo, 2.23). Seis temas cortos cargados de frases que no se sostienen solas: sin sujeto, «Se…», segunda
mitad con «y», pronombres, adverbio delante, cantidades. Casi todas las preguntas son literales: lo que se mide es si la frase se LEYÓ
y se colgó del tema correcto. Es de desarrollo (se mira y se afina con él); para medir a ciegas están ltest y el examen grande."""
N = "!no lo he entendido;!no he entendido"
K_ = "pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*"

TEMAS = [
 {"nombre": "la guitarra", "intro": "Te voy a leer un texto sobre la guitarra.", "frases": [
  ("La guitarra es un instrumento de cuerda.", [("V", "¿qué es la guitarra?", "instrumento")]),
  ("Tiene seis cuerdas y una caja de madera.", [("L", "¿cuántas cuerdas tiene la guitarra?", "seis|6")]),
  ("Se toca con los dedos o con una púa.", [("L", "¿con qué se toca la guitarra?", "dedos|pua")]),
  ("La púa es una pieza pequeña de plástico.", [("V", "¿qué es la púa?", "pieza")]),
  ("Las cuerdas se tensan con las clavijas y suenan al vibrar.", [("L", "¿con qué se tensan las cuerdas?", "clavijas"), ("L", "¿cuándo suenan las cuerdas?", "vibrar")]),
  ("El laúd es el antepasado de la guitarra.", [("I", "¿cuál es el antepasado de la guitarra?", "laud")]),
  ("Llegó a España hace más de mil años.", [("L", "¿cuándo llegó el laúd a España?", "mil")]),
  ("Los guitarristas afinan la guitarra antes de tocar y la guardan en una funda.", [("L", "¿cuándo afinan la guitarra los guitarristas?", "antes"), ("L", "¿dónde guardan la guitarra los guitarristas?", "funda")]),
  ("Las personas que fabrican guitarras se llaman lutieres.", [("I", "¿cómo se llaman las personas que fabrican guitarras?", "lutier*")]),
  ("Trabajan en un taller y tardan un mes en hacer una guitarra.", [("L", "¿dónde trabajan los lutieres?", "taller"), ("L", "¿cuánto tardan los lutieres en hacer una guitarra?", "mes")]),
 ], "extra": [
  ("M", "¿cuándo llegó a España el antepasado de la guitarra?", "mil"), ("K", "la guitarra tiene cuatro cuerdas", K_ + "|seis"),
  ("N", "¿cuánto cuesta una guitarra?", "ABST"), ("N", "¿quién inventó la púa?", "ABST"),
 ]},
 {"nombre": "los osos", "intro": "Te voy a leer un texto sobre los osos.", "frases": [
  ("Los osos son mamíferos grandes y fuertes.", [("V", "¿qué son los osos?", "mamifero*")]),
  ("Viven en bosques y montañas.", [("L", "¿dónde viven los osos?", "bosques|montanas")]),
  ("Comen frutos, miel y peces.", [("L", "¿qué comen los osos?", "frutos|miel|peces")]),
  ("En invierno duermen en una cueva.", [("L", "¿dónde duermen los osos en invierno?", "cueva")]),
  ("Este sueño largo se llama hibernación.", [("I", "¿cómo se llama este sueño largo?", "hibernacion")]),
  ("El oso polar es el oso más grande del mundo.", [("I", "¿cuál es el oso más grande del mundo?", "polar")]),
  ("Vive en el Ártico y caza focas.", [("L", "¿dónde vive el oso polar?", "artico"), ("L", "¿qué caza el oso polar?", "focas")]),
  ("Tiene el pelo blanco y la piel negra.", [("L", "¿de qué color tiene el pelo el oso polar?", "blanco")]),
  ("Las crías de los osos se llaman oseznos y nacen en invierno.", [("I", "¿cómo se llaman las crías de los osos?", "osezno*"), ("L", "¿cuándo nacen los oseznos?", "invierno")]),
  ("Se quedan con su madre durante dos años.", [("L", "¿cuánto tiempo se quedan los oseznos con su madre?", "dos")]),
  ("Los osos tienen garras muy fuertes.", [("L", "¿cómo son las garras de los osos?", "fuertes")]),
  ("Con ellas trepan a los árboles.", [("L", "¿a dónde trepan los osos?", "arboles")]),
 ], "extra": [
  ("M", "¿qué caza el oso más grande del mundo?", "focas"), ("K", "los oseznos se quedan con su madre durante cinco años", K_ + "|dos"),
  ("N", "¿cuánto pesa un oso?", "ABST"), ("N", "¿quién cuida a los osos?", "ABST"),
 ]},
 {"nombre": "el molino", "intro": "Te voy a leer un texto sobre el molino.", "frases": [
  ("Un molino es una máquina que muele el grano.", [("V", "¿qué es un molino?", "maquina")]),
  ("Los molinos de viento tienen cuatro aspas.", [("L", "¿cuántas aspas tienen los molinos de viento?", "cuatro|4")]),
  ("Giran cuando sopla el viento.", [("L", "¿cuándo giran las aspas?", "viento")]),
  ("El grano se echa en la tolva.", [("L", "¿dónde se echa el grano?", "tolva")]),
  ("La tolva es un embudo de madera.", [("V", "¿qué es la tolva?", "embudo")]),
  ("Debajo hay dos piedras redondas llamadas muelas.", [("L", "¿qué hay debajo de la tolva?", "piedras|muelas")]),
  ("Aplastan el grano y lo convierten en harina.", [("L", "¿en qué convierten el grano las muelas?", "harina")]),
  ("La harina cae a un saco.", [("L", "¿dónde cae la harina?", "saco")]),
  ("El molinero es la persona que trabaja en el molino.", [("V", "¿quién es el molinero?", "persona")]),
  ("Vigila las muelas y carga los sacos.", [("L", "¿qué carga el molinero?", "sacos")]),
  ("Antiguamente cobraba una parte de la harina.", [("L", "¿qué cobraba el molinero antiguamente?", "harina|parte")]),
 ], "extra": [
  ("K", "los molinos de viento tienen ocho aspas", K_ + "|cuatro"),
  ("N", "¿cuánto cuesta un saco de harina?", "ABST"), ("N", "¿quién construyó el molino?", "ABST"),
 ]},
 {"nombre": "la imprenta", "intro": "Te voy a leer un texto sobre la imprenta.", "frases": [
  ("La imprenta es una máquina que sirve para hacer muchas copias de un texto.", [("V", "¿qué es la imprenta?", "maquina")]),
  ("Gutenberg la inventó hace más de quinientos años.", [("L", "¿quién inventó la imprenta?", "gutenberg")]),
  ("Era un orfebre alemán.", [("L", "¿qué era Gutenberg?", "orfebre")]),
  ("Antes los libros se copiaban a mano.", [("L", "¿cómo se copiaban los libros antes?", "mano")]),
  ("Un monje tardaba un año en copiar un libro.", [("L", "¿cuánto tardaba un monje en copiar un libro?", "ano")]),
  ("Los tipos son piezas de metal con una letra cada una.", [("V", "¿qué son los tipos?", "piezas")]),
  ("Se colocan en fila y se cubren de tinta.", [("L", "¿de qué se cubren los tipos?", "tinta")]),
  ("Después se aprieta el papel contra ellos.", [("L", "¿qué se aprieta contra los tipos?", "papel")]),
  ("La Biblia fue el primer libro impreso.", [("I", "¿cuál fue el primer libro impreso?", "biblia")]),
  ("Tenía más de mil páginas.", [("L", "¿cuántas páginas tenía la Biblia?", "mil")]),
  ("Las personas que trabajaban en una imprenta se llamaban impresores.", [("I", "¿cómo se llamaban las personas que trabajaban en una imprenta?", "impresor*")]),
 ], "extra": [
  ("M", "¿cuántas páginas tenía el primer libro impreso?", "mil"), ("K", "un monje tardaba un mes en copiar un libro", K_ + "|ano"),
  ("N", "¿cuánto costaba un libro?", "ABST"), ("N", "¿dónde nació Gutenberg?", "ABST"),
 ]},
 {"nombre": "el té", "intro": "Te voy a leer un texto sobre el té.", "frases": [
  ("El té es una bebida que se hace con las hojas de una planta.", [("V", "¿qué es el té?", "bebida")]),
  ("Las hojas se recogen a mano y se secan al sol.", [("L", "¿cómo se recogen las hojas?", "mano"), ("L", "¿dónde se secan las hojas?", "sol")]),
  ("Después se meten en agua caliente durante tres minutos.", [("L", "¿cuánto tiempo se meten las hojas en agua caliente?", "tres|3")]),
  ("El té verde es el té que no se fermenta.", [("I", "¿qué té no se fermenta?", "verde")]),
  ("Tiene un sabor suave.", [("L", "¿qué sabor tiene el té verde?", "suave")]),
  ("El té negro se fermenta durante varias horas.", [("L", "¿cuánto se fermenta el té negro?", "horas")]),
  ("Es más fuerte y más oscuro.", [("L", "¿cómo es el té negro?", "fuerte|oscuro")]),
  ("China es el país que más té produce.", [("I", "¿qué país produce más té?", "china")]),
  ("En Inglaterra se toma con leche.", [("L", "¿con qué se toma el té en Inglaterra?", "leche")]),
  ("La tetera es el recipiente donde se prepara el té.", [("V", "¿qué es la tetera?", "recipiente")]),
  ("Suele ser de porcelana.", [("L", "¿de qué suele ser la tetera?", "porcelana")]),
 ], "extra": [
  ("M", "¿qué sabor tiene el té que no se fermenta?", "suave"), ("K", "las hojas se meten en agua caliente durante diez minutos", K_ + "|tres"),
  ("N", "¿cuánto cuesta una tetera?", "ABST"), ("N", "¿quién descubrió el té?", "ABST"),
 ]},
 {"nombre": "los bomberos", "intro": "Te voy a leer un texto sobre los bomberos.", "frases": [
  ("Los bomberos son las personas que apagan los incendios.", [("V", "¿quiénes son los bomberos?", "personas|apagan")]),
  ("Llevan un casco y un traje que no se quema.", [("L", "¿qué llevan los bomberos?", "casco|traje")]),
  ("Viajan en un camión rojo con una sirena.", [("L", "¿en qué viajan los bomberos?", "camion")]),
  ("El camión lleva una escalera muy larga y mil litros de agua.", [("L", "¿cuántos litros de agua lleva el camión?", "mil")]),
  ("La manguera es el tubo por el que sale el agua.", [("V", "¿qué es la manguera?", "tubo")]),
  ("Pesa mucho y la sujetan dos bomberos.", [("L", "¿cuántos bomberos sujetan la manguera?", "dos|2")]),
  ("El parque de bomberos es el edificio donde esperan los avisos.", [("V", "¿qué es el parque de bomberos?", "edificio")]),
  ("Allí duermen y entrenan cada día.", [("L", "¿dónde duermen los bomberos?", "parque"), ("L", "¿cuándo entrenan los bomberos?", "dia")]),
  ("Cuando suena la alarma bajan por una barra.", [("L", "¿por dónde bajan los bomberos cuando suena la alarma?", "barra")]),
  ("También rescatan a personas atrapadas y a veces salvan animales.", [("L", "¿a quién rescatan los bomberos?", "personas"), ("L", "¿qué salvan a veces los bomberos?", "animales")]),
 ], "extra": [
  ("K", "el camión lleva cien litros de agua", K_ + "|mil"),
  ("N", "¿cuánto cobra un bombero?", "ABST"), ("N", "¿quién fabrica las mangueras?", "ABST"),
 ]},
]
