"""EXAMEN DE CONCEPTOS 2.12: 40 sustantivos sacados AL AZAR (semilla 2112) del corpus UD Spanish (AnCora+GSD), entre los que la base 2.11
no conocía y cuyo hiperónimo directo en el léxico MCR es una categoría concreta (ver lab/iter212/muestra_conceptos.json).
De la muestra solo se quitaron, por regla mecánica, numerales, preposiciones, adjetivos y plurales repetidos («tres», «sobre», «pos»,
«especial», «media», «fines», «culés»). Los criterios (categorías aceptables) se escribieron antes de ver ninguna respuesta.
Se mide igual en la 2.11 y en la 2.12."""
from lab.banco import correr, imprime
P = [("¿qué es un bote?", "recipiente|barco|embarcacion|vehiculo"), ("¿qué es una mezcla?", "combinacion|sustancia|accion|union|conjunto"),
     ("¿qué es un emisor?", "aparato|persona|emisora|transmisor|dispositivo"), ("¿qué es un educador?", "persona|profesional|profesor|maestro|educa*"),
     ("¿qué es un proyectil?", "arma|objeto|bala|misil|municion"), ("¿qué es un apoyo?", "ayuda|soporte|sosten|respaldo"),
     ("¿qué es un bulto?", "paquete|objeto|bolsa|carga|equipaje|volumen"), ("¿qué son las medias?", "prenda*|ropa|calcetin*"),
     ("¿qué es un menú?", "lista|carta|documento|comida|platos|opciones"), ("¿qué es el almidón?", "sustancia|hidrato*|carbohidrato|alimento|polisacarido|compuesto"),
     ("¿qué es un mineral?", "sustancia|material|roca|elemento|compuesto"), ("¿qué es un fondo?", "parte|dinero|capital|base"),
     ("¿qué son las vísperas?", "dia anterior|tiempo|momento|antes|oracion"), ("¿qué es un estilo?", "manera|forma|modo|caracter"),
     ("¿qué es un palo?", "objeto|madera|vara|baston|herramienta"), ("¿qué es un culé?", "aficionado|seguidor|hincha|persona|barcelon*"),
     ("¿qué es un rancho?", "granja|finca|comida|vivienda|casa|campamento|lugar"), ("¿qué es una vara?", "palo|rama|objeto|baston|medida"),
     ("¿qué es un bufete?", "despacho|oficina|abogad*|establecimiento"), ("¿qué es un proceso?", "serie|conjunto|procedimiento|accion|juicio|etapa*"),
     ("¿qué es un asiento?", "mueble|silla|lugar|plaza|objeto"), ("¿qué es una presa?", "embalse|construccion|muro|animal|captura"),
     ("¿qué es una recta?", "linea|forma|tramo"), ("¿qué es la luz?", "energia|radiacion|claridad|fenomeno|lampara|iluminacion|onda"),
     ("¿qué es el lomo?", "carne|espalda|parte|alimento"), ("¿qué es la seda?", "tela|tejido|material|fibra"),
     ("¿qué es un ancestro?", "antepasado|persona|pariente|familiar"), ("¿qué es un campamento?", "lugar|asentamiento|instalacion|acampada"),
     ("¿qué es un residuo?", "resto|basura|desecho|sustancia|material"), ("¿qué es un gigante?", "persona|ser|criatura|personaje"),
     ("¿qué es un rifle?", "arma|fusil|escopeta"), ("¿qué es la colonización?", "proceso|accion|ocupacion|asentamiento|establecimiento"),
     ("¿qué es la alimentación?", "accion|proceso|nutricion|comida|alimento*"), ("¿qué es un hombre?", "persona|ser humano|varon|adulto|ser vivo|mamifero"),
     ("¿qué es la basura?", "residuo*|desecho*|resto*|suciedad"), ("¿qué es la confección?", "elaboracion|fabricacion|ropa|costura|actividad|prenda"),
     ("¿qué es la cerámica?", "material|arte|arcilla|barro|artesania"), ("¿qué es una pistola?", "arma"),
     ("¿qué es un ingrediente?", "alimento|componente|elemento|sustancia|producto"), ("¿qué es un familiar?", "pariente|persona|miembro")]
D = [{"id": f"cpt{k:02d}", "cat": "concepto", "turnos": [(q, c + ";!no lo s*;!no conozco")]} for k, (q, c) in enumerate(P)]
# Parte B (añadida antes de medir nada de ella, al ver que la parte A la contesta el léxico MCR de la capa antigua):
# pertenencia a categorías de varios niveles (lo que da la base de fábrica: herencia), con preguntas de sí y de no.
T = [("¿un bote es un objeto?", "^si"), ("¿un bote es un ser vivo?", "^no"), ("¿una mezcla es un ser vivo?", "^no"), ("¿una mezcla es una persona?", "^no"),
     ("¿un emisor es un alimento?", "^no"), ("¿un educador es una persona?", "^si"), ("¿un educador es un objeto?", "^no"), ("¿un proyectil es un objeto?", "^si"),
     ("¿un proyectil es un ser vivo?", "^no"), ("¿un apoyo es un animal?", "^no"), ("¿un bulto es un objeto?", "^si"), ("¿un bulto es un alimento?", "^no"),
     ("¿las medias son una prenda?", "^si"), ("¿las medias son un ser vivo?", "^no"), ("¿un menú es un animal?", "^no"), ("¿el almidón es un animal?", "^no"),
     ("¿un mineral es un ser vivo?", "^no"), ("¿un fondo es una persona?", "^no"), ("¿un estilo es un objeto?", "^no"), ("¿un palo es un objeto?", "^si"),
     ("¿un palo es un ser vivo?", "^no"), ("¿un culé es una persona?", "^si"), ("¿un rancho es un lugar?", "^si"), ("¿una vara es un objeto?", "^si"),
     ("¿un bufete es un lugar?", "^si"), ("¿un bufete es un ser vivo?", "^no"), ("¿un proceso es un animal?", "^no"), ("¿un asiento es un objeto?", "^si"),
     ("¿un asiento es un ser vivo?", "^no"), ("¿una recta es un animal?", "^no"), ("¿la luz es un ser vivo?", "^no"), ("¿el lomo es un alimento?", "^si"),
     ("¿el lomo es una persona?", "^no"), ("¿la seda es un material?", "^si"), ("¿la seda es un ser vivo?", "^no"), ("¿un ancestro es una persona?", "^si"),
     ("¿un campamento es un lugar?", "^si"), ("¿un residuo es un ser vivo?", "^no"), ("¿un rifle es un arma?", "^si"), ("¿un rifle es un objeto?", "^si"),
     ("¿un rifle es un ser vivo?", "^no"), ("¿la colonización es un objeto?", "^no"), ("¿la alimentación es un animal?", "^no"), ("¿un hombre es un ser vivo?", "^si"),
     ("¿un hombre es un objeto?", "^no"), ("¿la basura es un ser vivo?", "^no"), ("¿la cerámica es un material?", "^si"), ("¿una pistola es un objeto?", "^si"),
     ("¿una pistola es un ser vivo?", "^no"), ("¿un ingrediente es una persona?", "^no"), ("¿un familiar es una persona?", "^si")]
D += [{"id": f"tax{k:02d}", "cat": "taxonomia", "turnos": [(q, c)]} for k, (q, c) in enumerate(T)]


def medir(verboso=False, salida="lab/res_conceptos212.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    f, r = medir()
    imprime(r, "EXAMEN DE CONCEPTOS 2.12")
