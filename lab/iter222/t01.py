"""2.22 T01 · lo leído manda sobre la fábrica, puentes entre idiomas y contraste: temas de las medidas limpias y el del mercado (solo las sondas que la 2.22 acierta; red de regresión)."""
D = [{'cat': 'aprender-texto',
  'id': 'apr222-test9-la biblioteca',
  'turnos': [('Te voy a leer un texto sobre la biblioteca.\n'
              'La biblioteca es un edificio donde se guardan libros.\n'
              'Los libros se ordenan en estanterías según su tema.\n'
              'Cada libro lleva una etiqueta con un código.\n'
              'Los bibliotecarios ayudan a los lectores a encontrar libros.\n'
              'Para llevarse un libro a casa hace falta un carné.\n'
              'El préstamo dura tres semanas.\n'
              'La sala de lectura es la sala más silenciosa de la biblioteca.\n'
              'Está en el segundo piso.\n'
              'La hemeroteca es la sala donde se guardan los periódicos antiguos.\n'
              'Abre solo por la mañana.\n'
              'En la biblioteca no se puede comer.\n'
              'Los libros más antiguos se llaman incunables.\n'
              'Las personas que restauran libros se llaman encuadernadores.',
              ''),
             ('¿qué es la biblioteca?', 'edificio'),
             ('¿qué se guarda en la biblioteca?', 'libros'),
             ('¿dónde se ordenan los libros?', 'estanteria*'),
             ('¿qué lleva cada libro?', 'etiqueta'),
             ('¿quiénes ayudan a los lectores?', 'bibliotecario*'),
             ('¿qué hace falta para llevarse un libro a casa?', 'carne'),
             ('¿cuánto dura el préstamo?', 'tres semanas|3'),
             ('¿cuál es la sala más silenciosa de la biblioteca?', 'lectura'),
             ('¿dónde está la sala de lectura?', 'segundo|piso'),
             ('¿qué es la hemeroteca?', 'sala'),
             ('¿cuándo abre la hemeroteca?', 'manana'),
             ('¿se puede comer en la biblioteca?', '^no'),
             ('¿cómo se llaman los libros más antiguos?', 'incunable*'),
             ('¿cómo se llaman las personas que restauran libros?', 'encuadernador*'),
             ('¿la hemeroteca es una sala?', '^si'),
             ('¿la biblioteca es un edificio?', '^si'),
             ('¿un encuadernador es una persona?', '^si'),
             ('¿dónde se colocan los libros?', 'estanteria*'),
             ('¿qué se almacena en la biblioteca?', 'libros'),
             ('¿en qué piso está la sala más silenciosa de la biblioteca?', 'segundo'),
             ('¿cuándo abre la sala donde se guardan los periódicos antiguos?', 'manana'),
             ('¿quién fundó la biblioteca?', 'ABST'),
             ('¿cuánto cuesta el carné?', 'ABST'),
             ('¿cuántos libros hay en la hemeroteca?', 'ABST'),
             ('mi hermana es bibliotecaria', '!no lo he entendido;!no he entendido'),
             ('¿mi hermana ayuda a los lectores?', '^si|ayuda*'),
             ('birlar es lo mismo que llevarse', '!no lo he entendido;!no he entendido'),
             ('descríbeme la hemeroteca', 'sala|periodicos|manana'),
             ('el préstamo dura dos semanas', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|tres'),
             ('la hemeroteca abre por la tarde', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|manana')]},
 {'cat': 'aprender-texto',
  'id': 'apr222-test9-el huerto',
  'turnos': [('Te voy a leer un texto sobre el huerto.\n'
              'Un huerto es un terreno pequeño donde se cultivan verduras.\n'
              'Las semillas se siembran en primavera.\n'
              'Los hortelanos riegan las plantas cada tarde.\n'
              'El tomate es la verdura más cultivada del huerto.\n'
              'Necesita mucho sol y se recoge en verano.\n'
              'Las lechugas crecen muy rápido.\n'
              'El estiércol es un abono que alimenta la tierra.\n'
              'Las lombrices remueven la tierra y la hacen más fértil.\n'
              'Un espantapájaros es un muñeco que asusta a los pájaros.\n'
              'Los caracoles se comen las hojas de las lechugas.\n'
              'La azada es la herramienta con la que se cava la tierra.\n'
              'En invierno el huerto descansa.\n'
              'Las personas que cuidan un huerto se llaman hortelanos.',
              ''),
             ('¿qué es un huerto?', 'terreno'),
             ('¿qué se cultiva en un huerto?', 'verduras'),
             ('¿cuándo se siembran las semillas?', 'primavera'),
             ('¿quiénes riegan las plantas?', 'hortelano*'),
             ('¿cuándo riegan las plantas los hortelanos?', 'tarde'),
             ('¿cuál es la verdura más cultivada del huerto?', 'tomate'),
             ('¿cuándo se recoge el tomate?', 'verano'),
             ('¿qué es el estiércol?', 'abono'),
             ('¿quiénes remueven la tierra?', 'lombri*'),
             ('¿qué es un espantapájaros?', 'muneco'),
             ('¿qué se comen los caracoles?', 'hojas|lechugas'),
             ('¿qué es la azada?', 'herramienta'),
             ('¿cuándo descansa el huerto?', 'invierno'),
             ('¿cómo se llaman las personas que cuidan un huerto?', 'hortelano*'),
             ('¿el estiércol es un abono?', '^si'),
             ('¿la azada es una herramienta?', '^si'),
             ('¿un hortelano es una persona?', '^si'),
             ('¿quiénes mojan las plantas?', 'hortelano*'),
             ('¿qué devoran los caracoles?', 'hojas|lechugas'),
             ('¿cuándo se recoge la verdura más cultivada del huerto?', 'verano'),
             ('¿qué necesita la verdura más cultivada del huerto?', 'sol'),
             ('¿quién inventó la azada?', 'ABST'),
             ('¿cuánto cuesta un tomate?', 'ABST'),
             ('¿quién vende las lechugas?', 'ABST'),
             ('¿dónde duermen los caracoles?', 'ABST'),
             ('mi abuelo es hortelano', '!no lo he entendido;!no he entendido'),
             ('¿mi abuelo riega las plantas?', '^si|riega*'),
             ('descríbeme el tomate', 'verdura|sol|verano'),
             ('las semillas se siembran en otoño', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|primavera'),
             ('los hortelanos riegan las plantas cada mañana', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|tarde')]},
 {'cat': 'aprender-texto',
  'id': 'apr222-test10-el puerto',
  'turnos': [('Te voy a leer un texto sobre el puerto.\n'
              'Un puerto es un lugar de la costa donde atracan los barcos.\n'
              'Los barcos se amarran al muelle con cuerdas gruesas.\n'
              'El muelle es una plataforma de piedra junto al agua.\n'
              'Los estibadores cargan y descargan las mercancías.\n'
              'Las mercancías viajan en contenedores de metal.\n'
              'Una grúa levanta los contenedores más pesados.\n'
              'El faro avisa a los barcos durante la noche.\n'
              'El práctico es el marino que guía a los barcos grandes hasta el muelle.\n'
              'Sube a bordo antes de entrar en el puerto.\n'
              'El remolcador es un barco pequeño y muy potente.\n'
              'Empuja a los barcos grandes para que giren.\n'
              'Los pescadores salen del puerto a las cinco de la mañana.\n'
              'Las personas que arreglan las redes se llaman rederas.',
              ''),
             ('¿qué es un puerto?', 'lugar'),
             ('¿qué atraca en un puerto?', 'barcos'),
             ('¿con qué se amarran los barcos?', 'cuerdas'),
             ('¿qué es el muelle?', 'plataforma'),
             ('¿quiénes descargan las mercancías?', 'estibador*'),
             ('¿en qué viajan las mercancías?', 'contenedor*'),
             ('¿qué levanta una grúa?', 'contenedor*'),
             ('¿cuándo avisa el faro a los barcos?', 'noche'),
             ('¿qué es el práctico?', 'marino'),
             ('¿cuándo sube a bordo el práctico?', 'antes|entrar'),
             ('¿qué es el remolcador?', 'barco'),
             ('¿a quién empuja el remolcador?', 'barcos'),
             ('¿a qué hora salen los pescadores?', 'cinco|5'),
             ('¿cómo se llaman las personas que arreglan las redes?', 'redera*'),
             ('¿el remolcador es un barco?', '^si'),
             ('¿el práctico es un marino?', '^si'),
             ('¿el muelle es una plataforma?', '^si'),
             ('¿qué alza una grúa?', 'contenedor*'),
             ('¿quién construyó el puerto?', 'ABST'),
             ('¿cuánto pesa un contenedor?', 'ABST'),
             ('¿quién pinta los barcos?', 'ABST'),
             ('mi tía es redera', '!no lo he entendido;!no he entendido'),
             ('¿mi tía arregla las redes?', '^si|arregla*'),
             ('mi primo es estibador', '!no lo he entendido;!no he entendido'),
             ('¿mi primo descarga las mercancías?', '^si|descarga*'),
             ('descríbeme el remolcador', 'barco|pequeno|potente'),
             ('el faro avisa a los barcos durante el día', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|noche')]},
 {'cat': 'aprender-texto',
  'id': 'apr222-test8-el mercado',
  'turnos': [('Te voy a leer un texto sobre el mercado.\n'
              'El mercado es un lugar donde se venden alimentos frescos.\n'
              'Cada vendedor tiene un puesto.\n'
              'Los fruteros venden fruta y verdura.\n'
              'Los pescaderos limpian el pescado y lo cortan en rodajas.\n'
              'El pescado se pone sobre hielo para que no se estropee.\n'
              'Los vendedores pesan la compra en una báscula.\n'
              'El mercado abre muy temprano y cierra a mediodía.\n'
              'Los camiones traen la mercancía de madrugada.\n'
              'El mercado central es el mercado más grande de la ciudad.\n'
              'Tiene más de cien puestos.\n'
              'La lonja es el mercado donde se vende el pescado recién llegado.\n'
              'Está junto al puerto.\n'
              'Las personas que compran en el mercado se llaman clientes.',
              ''),
             ('¿qué es el mercado?', 'lugar'),
             ('¿qué se vende en el mercado?', 'alimentos'),
             ('¿qué tiene cada vendedor?', 'puesto'),
             ('¿qué venden los fruteros?', 'fruta|verdura'),
             ('¿quiénes limpian el pescado?', 'pescadero*'),
             ('¿sobre qué se pone el pescado?', 'hielo'),
             ('¿dónde pesan la compra los vendedores?', 'bascula'),
             ('¿cuándo cierra el mercado?', 'mediodia'),
             ('¿cuándo traen la mercancía los camiones?', 'madrugada'),
             ('¿cuál es el mercado más grande de la ciudad?', 'central'),
             ('¿cuántos puestos tiene el mercado central?', 'cien|100'),
             ('¿qué es la lonja?', 'mercado'),
             ('¿dónde está la lonja?', 'puerto'),
             ('¿cómo se llaman las personas que compran en el mercado?', 'cliente*'),
             ('¿la lonja es un mercado?', '^si'),
             ('¿sobre qué se coloca el pescado?', 'hielo'),
             ('¿cuántos puestos tiene el mercado más grande de la ciudad?', 'cien|100'),
             ('¿dónde está el mercado donde se vende el pescado recién llegado?', 'puerto'),
             ('¿quién construyó el mercado central?', 'ABST'),
             ('¿dónde duermen los fruteros?', 'ABST'),
             ('despachar es lo mismo que vender', '!no lo he entendido;!no he entendido'),
             ('¿qué despachan los fruteros?', 'fruta|verdura'),
             ('un chiringo es lo mismo que un puesto', '!no lo he entendido;!no he entendido'),
             ('¿qué tiene cada vendedor?', 'puesto'),
             ('mi madre es pescadera', '!no lo he entendido;!no he entendido'),
             ('¿mi madre limpia el pescado?', '^si|limpia*'),
             ('descríbeme la lonja', 'mercado|pescado|puerto'),
             ('el mercado cierra por la noche', 'pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*|mediodia')]}]
