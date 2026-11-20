from lab.imagenes import png, img, figura
D = [{"id": "k08", "cat": "libre", "turnos": [
 ("hola", "hola"), ("estoy buscando un regalo para mi novia", "regalo;novia;!no lo he entendido"), ("su cumpleaños es el día doce", "doce|12;!no lo he entendido"),
 ("le encantan los libros de aventuras", "libros;!no lo he entendido"), ("¿qué le encanta a mi novia?", "libros"), ("¿cuándo es el cumpleaños de mi novia?", "doce|12"),
 (img("¿qué color es este?", figura("estrella", "amarillo")), "amarill*"), ("es el color favorito de mi novia", "amarill*;!no lo he entendido"), ("¿cuál es el color favorito de mi novia?", "amarill*"),
 ("¿qué estoy buscando?", "regalo")]}]
