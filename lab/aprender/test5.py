"""APRENDER · MEDIDA LIMPIA de la 2.20. Escrito con el código congelado y sin ejecutarlo; se mide UNA vez en cada versión (2.19 y 2.20).
Mismo reparto de tipos que las anteriores, con más peso de paráfrasis (P: lo mismo con otras palabras) y de trampas (N: una palabra
emparentada que el texto no contesta), que es lo que esta vuelta quiere mover."""
N = "!no lo he entendido;!no he entendido"
K_ = "pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*"

VIDRIO = {"nombre": "el vidrio", "intro": "Te voy a leer un texto sobre el vidrio.", "frases": [
 ("El vidrio es un material duro y transparente que se rompe con facilidad.", [("V", "¿qué es el vidrio?", "material"), ("L", "¿cómo es el vidrio?", "duro|transparente")]),
 ("Se fabrica con arena, que se calienta en un horno hasta que se funde.", [("L", "¿con qué se fabrica el vidrio?", "arena")]),
 ("El horno alcanza más de mil grados.", [("L", "¿cuántos grados alcanza el horno?", "mil|1000")]),
 ("Cuando el vidrio está fundido parece miel espesa.", [("D", "¿qué parece el vidrio cuando está fundido?", "miel")]),
 ("Los sopladores son los artesanos que dan forma al vidrio soplando por un tubo largo.", [("V", "¿qué son los sopladores?", "artesanos"), ("I", "¿quiénes dan forma al vidrio?", "sopladores|artesanos")]),
 ("El tubo se llama caña.", [("I", "¿cómo se llama el tubo?", "cana")]),
 ("Al enfriarse, el vidrio se vuelve duro.", [("L", "¿cuándo se vuelve duro el vidrio?", "enfriarse|enfria*")]),
 ("Con vidrio se hacen botellas, vasos, ventanas y espejos.", [("L", "¿qué se hace con vidrio?", "botellas|vasos|ventanas|espejos")]),
 ("Un espejo es un vidrio con una capa de plata por detrás.", [("V", "¿qué es un espejo?", "vidrio|plata")]),
 ("El vidrio se puede reciclar muchas veces sin perder calidad.", [("L", "¿el vidrio se puede reciclar?", "^si")]),
 ("Las botellas usadas se echan al contenedor verde.", [("L", "¿dónde se echan las botellas usadas?", "contenedor|verde")]),
 ("En la fábrica las botellas viejas se trituran y se funden otra vez.", [("L", "¿dónde se trituran las botellas viejas?", "fabrica")]),
 ("Los romanos ya usaban vasos de vidrio.", [("L", "¿quiénes usaban ya vasos de vidrio?", "romanos")]),
 ("Murano es una isla de Italia famosa por sus sopladores.", [("V", "¿qué es Murano?", "isla"), ("L", "¿por qué es famosa Murano?", "sopladores")]),
 ("El vidrio de las gafas se llama lente.", [("I", "¿cómo se llama el vidrio de las gafas?", "lente")]),
], "extra": [
 ("H", "¿un soplador es un artesano?", "^si"), ("H", "¿un espejo es un vidrio?", "^si"), ("H", "¿un soplador es una persona?", "^si|artesano"),
 ("P", "¿con qué se elabora el vidrio?", "arena"), ("P", "¿quiénes moldean el vidrio?", "sopladores|artesanos"), ("P", "¿dónde se tiran las botellas usadas?", "contenedor|verde"),
 ("P", "¿quiénes utilizaban ya vasos de vidrio?", "romanos"), ("P", "¿cuándo se endurece el vidrio?", "enfria*"), ("P", "¿qué se fabrica con vidrio?", "botellas|vasos|ventanas|espejos"),
 ("P", "¿dónde se muelen las botellas viejas?", "fabrica"), ("P", "¿el vidrio se quiebra con facilidad?", "^si|rompe"),
 ("D", "¿una botella se puede reciclar?", "^si|vidrio"), ("M", "¿de qué país es la isla famosa por sus sopladores?", "italia"),
 ("N", "¿quién inventó el vidrio?", "ABST"), ("N", "¿cuánto cuesta un espejo?", "ABST"), ("N", "¿quién limpia las ventanas?", "ABST"),
 ("N", "¿dónde se venden las botellas?", "ABST"), ("N", "¿quién pinta los vasos?", "ABST"), ("N", "¿cuánto pesa una botella?", "ABST"),
 ("C", "mi primo es soplador", N), ("C", "¿mi primo da forma al vidrio?", "^si|forma"),
 ("G", "dime dos cosas que se hacen con vidrio", "botellas|vasos|ventanas|espejos"), ("G", "descríbeme el vidrio", "material|duro|transparente|arena"),
 ("K", "las botellas usadas se echan al contenedor azul", K_ + "|verde"),
]}

CARTEROS = {"nombre": "el correo", "intro": "Te voy a leer un texto sobre el correo.", "frases": [
 ("El correo es el servicio que lleva cartas y paquetes de un lugar a otro.", [("V", "¿qué es el correo?", "servicio"), ("L", "¿qué lleva el correo?", "cartas|paquetes")]),
 ("La persona que reparte las cartas se llama cartero.", [("I", "¿cómo se llama la persona que reparte las cartas?", "cartero")]),
 ("Para enviar una carta hay que meterla en un sobre y pegarle un sello.", [("L", "¿qué hay que pegarle al sobre?", "sello")]),
 ("El sello es una estampa pequeña que demuestra que el envío está pagado.", [("V", "¿qué es un sello?", "estampa")]),
 ("En el sobre se escribe la dirección del destinatario, que es la persona que recibe la carta.", [("V", "¿quién es el destinatario?", "recibe|persona")]),
 ("La persona que envía la carta se llama remitente.", [("I", "¿cómo se llama la persona que envía la carta?", "remitente")]),
 ("Las cartas se echan al buzón, que en España es amarillo.", [("L", "¿dónde se echan las cartas?", "buzon"), ("L", "¿de qué color es el buzón en España?", "amarillo")]),
 ("Los carteros recogen las cartas de los buzones cada mañana.", [("L", "¿cuándo recogen las cartas los carteros?", "manana")]),
 ("Después las cartas se clasifican en una oficina según su código postal.", [("L", "¿dónde se clasifican las cartas?", "oficina")]),
 ("El código postal es un número que indica la zona de destino.", [("V", "¿qué es el código postal?", "numero")]),
 ("Antiguamente el correo viajaba a caballo y tardaba semanas.", [("L", "¿cómo viajaba el correo antiguamente?", "caballo")]),
 ("Hoy las cartas viajan en furgonetas, trenes y aviones.", [("L", "¿en qué viajan hoy las cartas?", "furgonetas|trenes|aviones")]),
 ("Las palomas mensajeras llevaban mensajes atados a una pata.", [("L", "¿qué llevaban las palomas mensajeras?", "mensajes")]),
 ("Un paquete urgente llega en un solo día.", [("L", "¿cuánto tarda en llegar un paquete urgente?", "un solo dia|un dia|1")]),
 ("Las personas que coleccionan sellos se llaman filatélicos.", [("I", "¿cómo se llaman las personas que coleccionan sellos?", "filatelico*")]),
], "extra": [
 ("H", "¿un cartero es una persona?", "^si"), ("H", "¿el destinatario es una persona?", "^si"), ("H", "¿un filatélico es una persona?", "^si"),
 ("P", "¿quién entrega las cartas?", "cartero*"), ("P", "¿dónde se depositan las cartas?", "buzon"), ("P", "¿dónde se ordenan las cartas?", "oficina"),
 ("P", "¿qué transportaban las palomas mensajeras?", "mensajes"), ("P", "¿quiénes juntan sellos?", "filatelico*"), ("P", "¿cuánto demoraba el correo antiguamente?", "semanas"),
 ("P", "¿cuánto demora un paquete urgente?", "dia"), ("P", "¿qué transporta el correo?", "cartas|paquetes"),
 ("D", "¿un cartero recoge cartas?", "^si|recoge*"), ("M", "¿cómo se llama la persona que recibe la carta?", "destinatario"),
 ("N", "¿quién inventó el sello?", "ABST"), ("N", "¿cuánto cuesta un sello?", "ABST"), ("N", "¿quién fabrica los buzones?", "ABST"),
 ("N", "¿quién lee las cartas?", "ABST"), ("N", "¿dónde duermen las palomas mensajeras?", "ABST"), ("N", "¿cuánto pesa un paquete urgente?", "ABST"),
 ("C", "mi vecina es cartera", N), ("C", "¿mi vecina reparte cartas?", "^si|reparte*"),
 ("G", "dime en qué viajan hoy las cartas", "furgonetas|trenes|aviones"), ("G", "descríbeme el correo", "servicio|cartas|paquetes"),
 ("K", "el buzón en España es rojo", K_ + "|amarillo"),
]}

TEMAS = [VIDRIO, CARTEROS]
