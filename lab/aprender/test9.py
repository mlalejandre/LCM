"""APRENDER · MEDIDA LIMPIA de la 2.22. Escrita con el código congelado y sin ejecutarla; se mide UNA vez en cada versión (2.21 y 2.22), con el
texto pegado y frase a frase. Mismo reparto de tipos que las anteriores."""
N = "!no lo he entendido;!no he entendido"
K_ = "pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*"

BIBLIO = {"nombre": "la biblioteca", "intro": "Te voy a leer un texto sobre la biblioteca.", "frases": [
 ("La biblioteca es un edificio donde se guardan libros.", [("V", "¿qué es la biblioteca?", "edificio"), ("L", "¿qué se guarda en la biblioteca?", "libros")]),
 ("Los libros se ordenan en estanterías según su tema.", [("L", "¿dónde se ordenan los libros?", "estanteria*")]),
 ("Cada libro lleva una etiqueta con un código.", [("L", "¿qué lleva cada libro?", "etiqueta")]),
 ("Los bibliotecarios ayudan a los lectores a encontrar libros.", [("L", "¿quiénes ayudan a los lectores?", "bibliotecario*")]),
 ("Para llevarse un libro a casa hace falta un carné.", [("L", "¿qué hace falta para llevarse un libro a casa?", "carne")]),
 ("El préstamo dura tres semanas.", [("L", "¿cuánto dura el préstamo?", "tres semanas|3")]),
 ("La sala de lectura es la sala más silenciosa de la biblioteca.", [("I", "¿cuál es la sala más silenciosa de la biblioteca?", "lectura")]),
 ("Está en el segundo piso.", [("L", "¿dónde está la sala de lectura?", "segundo|piso")]),
 ("La hemeroteca es la sala donde se guardan los periódicos antiguos.", [("V", "¿qué es la hemeroteca?", "sala")]),
 ("Abre solo por la mañana.", [("L", "¿cuándo abre la hemeroteca?", "manana")]),
 ("En la biblioteca no se puede comer.", [("L", "¿se puede comer en la biblioteca?", "^no")]),
 ("Los libros más antiguos se llaman incunables.", [("I", "¿cómo se llaman los libros más antiguos?", "incunable*")]),
 ("Las personas que restauran libros se llaman encuadernadores.", [("I", "¿cómo se llaman las personas que restauran libros?", "encuadernador*")]),
], "extra": [
 ("H", "¿la hemeroteca es una sala?", "^si"), ("H", "¿la biblioteca es un edificio?", "^si"), ("H", "¿un encuadernador es una persona?", "^si"),
 ("P", "¿dónde se colocan los libros?", "estanteria*"), ("P", "¿quiénes auxilian a los lectores?", "bibliotecario*"), ("P", "¿qué se almacena en la biblioteca?", "libros"),
 ("P", "¿quiénes arreglan libros?", "encuadernador*"),
 ("M", "¿en qué piso está la sala más silenciosa de la biblioteca?", "segundo"), ("M", "¿cuándo abre la sala donde se guardan los periódicos antiguos?", "manana"),
 ("N", "¿quién fundó la biblioteca?", "ABST"), ("N", "¿cuánto cuesta el carné?", "ABST"), ("N", "¿quién escribe los libros?", "ABST"), ("N", "¿cuántos libros hay en la hemeroteca?", "ABST"),
 ("C", "mi hermana es bibliotecaria", N), ("C", "¿mi hermana ayuda a los lectores?", "^si|ayuda*"),
 ("C", "birlar es lo mismo que llevarse", N),
 ("G", "descríbeme la hemeroteca", "sala|periodicos|manana"), ("K", "el préstamo dura dos semanas", K_ + "|tres"), ("K", "la hemeroteca abre por la tarde", K_ + "|manana"),
]}

HUERTO = {"nombre": "el huerto", "intro": "Te voy a leer un texto sobre el huerto.", "frases": [
 ("Un huerto es un terreno pequeño donde se cultivan verduras.", [("V", "¿qué es un huerto?", "terreno"), ("L", "¿qué se cultiva en un huerto?", "verduras")]),
 ("Las semillas se siembran en primavera.", [("L", "¿cuándo se siembran las semillas?", "primavera")]),
 ("Los hortelanos riegan las plantas cada tarde.", [("L", "¿quiénes riegan las plantas?", "hortelano*"), ("L", "¿cuándo riegan las plantas los hortelanos?", "tarde")]),
 ("El tomate es la verdura más cultivada del huerto.", [("I", "¿cuál es la verdura más cultivada del huerto?", "tomate")]),
 ("Necesita mucho sol y se recoge en verano.", [("L", "¿cuándo se recoge el tomate?", "verano")]),
 ("Las lechugas crecen muy rápido.", [("L", "¿cómo crecen las lechugas?", "rapido")]),
 ("El estiércol es un abono que alimenta la tierra.", [("V", "¿qué es el estiércol?", "abono")]),
 ("Las lombrices remueven la tierra y la hacen más fértil.", [("L", "¿quiénes remueven la tierra?", "lombri*")]),
 ("Un espantapájaros es un muñeco que asusta a los pájaros.", [("V", "¿qué es un espantapájaros?", "muneco")]),
 ("Los caracoles se comen las hojas de las lechugas.", [("L", "¿qué se comen los caracoles?", "hojas|lechugas")]),
 ("La azada es la herramienta con la que se cava la tierra.", [("V", "¿qué es la azada?", "herramienta")]),
 ("En invierno el huerto descansa.", [("L", "¿cuándo descansa el huerto?", "invierno")]),
 ("Las personas que cuidan un huerto se llaman hortelanos.", [("I", "¿cómo se llaman las personas que cuidan un huerto?", "hortelano*")]),
], "extra": [
 ("H", "¿el estiércol es un abono?", "^si"), ("H", "¿la azada es una herramienta?", "^si"), ("H", "¿un hortelano es una persona?", "^si"),
 ("P", "¿cuándo se plantan las semillas?", "primavera"), ("P", "¿quiénes mojan las plantas?", "hortelano*"), ("P", "¿qué se siembra en un huerto?", "verduras"),
 ("P", "¿qué devoran los caracoles?", "hojas|lechugas"),
 ("M", "¿cuándo se recoge la verdura más cultivada del huerto?", "verano"), ("M", "¿qué necesita la verdura más cultivada del huerto?", "sol"),
 ("N", "¿quién inventó la azada?", "ABST"), ("N", "¿cuánto cuesta un tomate?", "ABST"), ("N", "¿quién vende las lechugas?", "ABST"), ("N", "¿dónde duermen los caracoles?", "ABST"),
 ("C", "mi abuelo es hortelano", N), ("C", "¿mi abuelo riega las plantas?", "^si|riega*"),
 ("G", "descríbeme el tomate", "verdura|sol|verano"), ("K", "las semillas se siembran en otoño", K_ + "|primavera"), ("K", "los hortelanos riegan las plantas cada mañana", K_ + "|tarde"),
]}

TEMAS = [BIBLIO, HUERTO]
