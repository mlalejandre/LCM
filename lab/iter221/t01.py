"""2.21 T01 · encadenar y sinónimos enseñados: temas de las dos medidas limpias, con el texto pegado (solo las sondas que la 2.21 acierta; red de regresión)."""
D = [{'cat': 'aprender-texto',
  'id': 'apr221-test7-texto-el papel',
  'turnos': [('Te voy a leer un texto sobre el papel.\n'
              'El papel es una lámina fina que se hace con fibras de madera.\n'
              'La madera se tritura y se mezcla con agua hasta formar una pasta.\n'
              'La pasta se extiende sobre una malla y se deja secar.\n'
              'El lugar donde se fabrica el papel se llama papelera.\n'
              'Los chinos inventaron el papel hace unos dos mil años.\n'
              'Antes se escribía sobre pergamino, que es piel de animal muy fina.\n'
              'El papel de periódico es el papel más barato.\n'
              'Se vuelve amarillo con la luz del sol.\n'
              'El cartón es un papel grueso y resistente.\n'
              'Con cartón se hacen cajas.\n'
              'El papel usado se echa al contenedor azul.\n'
              'El papel se puede reciclar unas seis veces.\n'
              'Una hoja de papel tarda unos tres meses en deshacerse en la naturaleza.\n'
              'Las personas que fabrican papel a mano se llaman papeleros.',
              ''),
             ('¿qué es el papel?', 'lamina'),
             ('¿con qué se hace el papel?', 'fibras|madera'),
             ('¿con qué se mezcla la madera?', 'agua'),
             ('¿sobre qué se extiende la pasta?', 'malla'),
             ('¿cómo se llama el lugar donde se fabrica el papel?', 'papelera'),
             ('¿dónde se fabrica el papel?', 'papelera'),
             ('¿quiénes inventaron el papel?', 'chinos'),
             ('¿qué es el pergamino?', 'piel'),
             ('¿cuál es el papel más barato?', 'periodico'),
             ('¿con qué se vuelve amarillo el papel de periódico?', 'luz|sol'),
             ('¿qué es el cartón?', 'papel'),
             ('¿qué se hace con cartón?', 'cajas'),
             ('¿dónde se echa el papel usado?', 'contenedor|azul'),
             ('¿cuántas veces se puede reciclar el papel?', 'seis|6'),
             ('¿cuánto tarda una hoja de papel en deshacerse?', 'tres meses|3'),
             ('¿cómo se llaman las personas que fabrican papel a mano?', 'papelero*'),
             ('¿un papelero es una persona?', '^si'),
             ('¿dónde se elabora el papel?', 'papelera'),
             ('¿dónde se tira el papel usado?', 'contenedor|azul'),
             ('¿quiénes crearon el papel?', 'chinos'),
             ('¿cuánto demora una hoja de papel en deshacerse?', 'tres meses|3'),
             ('¿con qué se vuelve amarillo el papel más barato?', 'luz|sol'),
             ('¿qué se hace con el papel grueso y resistente?', 'cajas'),
             ('¿quién inventó el cartón?', 'ABST'),
             ('¿cuánto cuesta un periódico?', 'ABST'),
             ('¿quién vende el pergamino?', 'ABST'),
             ('¿cuánto pesa una caja?', 'ABST'),
             ('aplastar es lo mismo que triturar', '!no lo he entendido;!no he entendido'),
             ('¿la madera se aplasta?', '^si|tritura'),
             ('mi abuela es papelera', '!no lo he entendido;!no he entendido'),
             ('descríbeme el cartón', 'papel|grueso|resistente|cajas')]},
 {'cat': 'aprender-texto',
  'id': 'apr221-test7-texto-el queso',
  'turnos': [('Te voy a leer un texto sobre el queso.\n'
              'El queso es un alimento que se hace con leche.\n'
              'La leche puede ser de vaca, de oveja o de cabra.\n'
              'Para hacer queso se añade cuajo a la leche caliente.\n'
              'El cuajo es una sustancia que separa la parte sólida de la leche.\n'
              'La parte sólida se llama cuajada y la parte líquida se llama suero.\n'
              'La cuajada se prensa en moldes para darle forma.\n'
              'Después el queso se guarda en una cueva fresca durante varios meses.\n'
              'Este proceso se llama curación.\n'
              'El queso fresco es el queso que no se cura.\n'
              'Se come a los pocos días y es muy blando.\n'
              'El queso curado es duro y tiene un sabor fuerte.\n'
              'El manchego es el queso más famoso de España.\n'
              'Se hace con leche de oveja.\n'
              'Las personas que hacen queso se llaman queseros.',
              ''),
             ('¿qué es el queso?', 'alimento'),
             ('¿con qué se hace el queso?', 'leche'),
             ('¿de qué animales puede ser la leche?', 'vaca|oveja|cabra'),
             ('¿qué se añade a la leche caliente?', 'cuajo'),
             ('¿qué es el cuajo?', 'sustancia'),
             ('¿cómo se llama la parte sólida?', 'cuajada'),
             ('¿cómo se llama la parte líquida?', 'suero'),
             ('¿dónde se prensa la cuajada?', 'moldes'),
             ('¿dónde se guarda el queso?', 'cueva'),
             ('¿cómo se llama este proceso?', 'curacion'),
             ('¿qué queso no se cura?', 'fresco'),
             ('¿cómo es el queso fresco?', 'blando'),
             ('¿cómo es el queso curado?', 'duro|fuerte'),
             ('¿cuál es el queso más famoso de España?', 'manchego'),
             ('¿con qué leche se hace el manchego?', 'oveja'),
             ('¿cómo se llaman las personas que hacen queso?', 'quesero*'),
             ('¿el queso es un alimento?', '^si'),
             ('¿un quesero es una persona?', '^si'),
             ('¿dónde se almacena el queso?', 'cueva'),
             ('¿qué se agrega a la leche caliente?', 'cuajo'),
             ('¿quiénes elaboran queso?', 'quesero*'),
             ('¿el queso fresco se ingiere a los pocos días?', '^si|come'),
             ('¿con qué leche se hace el queso más famoso de España?', 'oveja'),
             ('¿el manchego es un queso?', '^si'),
             ('¿quién inventó el queso?', 'ABST'),
             ('¿cuánto cuesta un queso curado?', 'ABST'),
             ('¿quién ordeña las cabras?', 'ABST'),
             ('¿dónde duermen los queseros?', 'ABST'),
             ('conservar es lo mismo que guardar', '!no lo he entendido;!no he entendido'),
             ('¿dónde se conserva el queso?', 'cueva'),
             ('mi vecino es quesero', '!no lo he entendido;!no he entendido'),
             ('¿mi vecino hace queso?', '^si|hace*'),
             ('descríbeme el queso curado', 'duro|fuerte')]},
 {'cat': 'aprender-texto',
  'id': 'apr221-test8-texto-el mercado',
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
             ('¿cuál es el mercado más grande de la ciudad?', 'central'),
             ('¿qué es la lonja?', 'mercado'),
             ('¿dónde está la lonja?', 'puerto'),
             ('¿cómo se llaman las personas que compran en el mercado?', 'cliente*'),
             ('¿sobre qué se coloca el pescado?', 'hielo'),
             ('¿quién construyó el mercado central?', 'ABST'),
             ('¿dónde duermen los fruteros?', 'ABST'),
             ('despachar es lo mismo que vender', '!no lo he entendido;!no he entendido'),
             ('¿qué despachan los fruteros?', 'fruta|verdura'),
             ('un chiringo es lo mismo que un puesto', '!no lo he entendido;!no he entendido'),
             ('¿qué tiene cada vendedor?', 'puesto'),
             ('mi madre es pescadera', '!no lo he entendido;!no he entendido'),
             ('descríbeme la lonja', 'mercado|pescado|puerto')]}]
