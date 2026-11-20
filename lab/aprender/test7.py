"""APRENDER · MEDIDA LIMPIA de la 2.21. Escrita con el código congelado y sin ejecutarla; se mide UNA vez en cada versión (2.20 y 2.21), con el
texto pegado y frase a frase. Mismo reparto de tipos, con más peso de lo que esta vuelta quiere mover: combinar dos frases (M) y
sinónimos que enseña el usuario (C seguida de P)."""
N = "!no lo he entendido;!no he entendido"
K_ = "pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*"

PAPEL = {"nombre": "el papel", "intro": "Te voy a leer un texto sobre el papel.", "frases": [
 ("El papel es una lámina fina que se hace con fibras de madera.", [("V", "¿qué es el papel?", "lamina"), ("L", "¿con qué se hace el papel?", "fibras|madera")]),
 ("La madera se tritura y se mezcla con agua hasta formar una pasta.", [("L", "¿con qué se mezcla la madera?", "agua")]),
 ("La pasta se extiende sobre una malla y se deja secar.", [("L", "¿sobre qué se extiende la pasta?", "malla")]),
 ("El lugar donde se fabrica el papel se llama papelera.", [("I", "¿cómo se llama el lugar donde se fabrica el papel?", "papelera"), ("L", "¿dónde se fabrica el papel?", "papelera")]),
 ("Los chinos inventaron el papel hace unos dos mil años.", [("L", "¿quiénes inventaron el papel?", "chinos")]),
 ("Antes se escribía sobre pergamino, que es piel de animal muy fina.", [("V", "¿qué es el pergamino?", "piel")]),
 ("El papel de periódico es el papel más barato.", [("I", "¿cuál es el papel más barato?", "periodico")]),
 ("Se vuelve amarillo con la luz del sol.", [("L", "¿con qué se vuelve amarillo el papel de periódico?", "luz|sol")]),
 ("El cartón es un papel grueso y resistente.", [("V", "¿qué es el cartón?", "papel")]),
 ("Con cartón se hacen cajas.", [("L", "¿qué se hace con cartón?", "cajas")]),
 ("El papel usado se echa al contenedor azul.", [("L", "¿dónde se echa el papel usado?", "contenedor|azul")]),
 ("El papel se puede reciclar unas seis veces.", [("L", "¿cuántas veces se puede reciclar el papel?", "seis|6")]),
 ("Una hoja de papel tarda unos tres meses en deshacerse en la naturaleza.", [("L", "¿cuánto tarda una hoja de papel en deshacerse?", "tres meses|3")]),
 ("Las personas que fabrican papel a mano se llaman papeleros.", [("I", "¿cómo se llaman las personas que fabrican papel a mano?", "papelero*")]),
], "extra": [
 ("H", "¿el cartón es un papel?", "^si"), ("H", "¿un papelero es una persona?", "^si"),
 ("P", "¿dónde se elabora el papel?", "papelera"), ("P", "¿dónde se tira el papel usado?", "contenedor|azul"), ("P", "¿quiénes crearon el papel?", "chinos"),
 ("P", "¿cuánto demora una hoja de papel en deshacerse?", "tres meses|3"),
 ("M", "¿con qué se vuelve amarillo el papel más barato?", "luz|sol"), ("M", "¿qué se hace con el papel grueso y resistente?", "cajas"),
 ("D", "¿una caja de cartón es de papel?", "^si|papel"),
 ("N", "¿quién inventó el cartón?", "ABST"), ("N", "¿cuánto cuesta un periódico?", "ABST"), ("N", "¿quién vende el pergamino?", "ABST"), ("N", "¿cuánto pesa una caja?", "ABST"),
 ("C", "aplastar es lo mismo que triturar", N), ("P", "¿la madera se aplasta?", "^si|tritura"),
 ("C", "mi abuela es papelera", N), ("C", "¿mi abuela fabrica papel?", "^si|fabrica*"),
 ("G", "descríbeme el cartón", "papel|grueso|resistente|cajas"), ("K", "el papel usado se echa al contenedor verde", K_ + "|azul"),
]}

QUESO = {"nombre": "el queso", "intro": "Te voy a leer un texto sobre el queso.", "frases": [
 ("El queso es un alimento que se hace con leche.", [("V", "¿qué es el queso?", "alimento"), ("L", "¿con qué se hace el queso?", "leche")]),
 ("La leche puede ser de vaca, de oveja o de cabra.", [("L", "¿de qué animales puede ser la leche?", "vaca|oveja|cabra")]),
 ("Para hacer queso se añade cuajo a la leche caliente.", [("L", "¿qué se añade a la leche caliente?", "cuajo")]),
 ("El cuajo es una sustancia que separa la parte sólida de la leche.", [("V", "¿qué es el cuajo?", "sustancia")]),
 ("La parte sólida se llama cuajada y la parte líquida se llama suero.", [("I", "¿cómo se llama la parte sólida?", "cuajada"), ("I", "¿cómo se llama la parte líquida?", "suero")]),
 ("La cuajada se prensa en moldes para darle forma.", [("L", "¿dónde se prensa la cuajada?", "moldes")]),
 ("Después el queso se guarda en una cueva fresca durante varios meses.", [("L", "¿dónde se guarda el queso?", "cueva")]),
 ("Este proceso se llama curación.", [("I", "¿cómo se llama este proceso?", "curacion")]),
 ("El queso fresco es el queso que no se cura.", [("I", "¿qué queso no se cura?", "fresco")]),
 ("Se come a los pocos días y es muy blando.", [("L", "¿cómo es el queso fresco?", "blando")]),
 ("El queso curado es duro y tiene un sabor fuerte.", [("L", "¿cómo es el queso curado?", "duro|fuerte")]),
 ("El manchego es el queso más famoso de España.", [("I", "¿cuál es el queso más famoso de España?", "manchego")]),
 ("Se hace con leche de oveja.", [("L", "¿con qué leche se hace el manchego?", "oveja")]),
 ("Las personas que hacen queso se llaman queseros.", [("I", "¿cómo se llaman las personas que hacen queso?", "quesero*")]),
], "extra": [
 ("H", "¿el queso es un alimento?", "^si"), ("H", "¿un quesero es una persona?", "^si"),
 ("P", "¿dónde se almacena el queso?", "cueva"), ("P", "¿qué se agrega a la leche caliente?", "cuajo"), ("P", "¿quiénes elaboran queso?", "quesero*"),
 ("P", "¿el queso fresco se ingiere a los pocos días?", "^si|come"),
 ("M", "¿con qué leche se hace el queso más famoso de España?", "oveja"), ("M", "¿cómo es el queso que no se cura?", "blando"),
 ("D", "¿el manchego es un queso?", "^si"),
 ("N", "¿quién inventó el queso?", "ABST"), ("N", "¿cuánto cuesta un queso curado?", "ABST"), ("N", "¿quién ordeña las cabras?", "ABST"), ("N", "¿dónde duermen los queseros?", "ABST"),
 ("C", "conservar es lo mismo que guardar", N), ("P", "¿dónde se conserva el queso?", "cueva"),
 ("C", "mi vecino es quesero", N), ("C", "¿mi vecino hace queso?", "^si|hace*"),
 ("G", "descríbeme el queso curado", "duro|fuerte"), ("K", "el queso curado es blando", K_ + "|duro"),
]}

TEMAS = [PAPEL, QUESO]
