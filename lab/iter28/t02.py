from lab.imagenes import png, img, figura
D = [{"id": "k02", "cat": "libre", "turnos": [
 ("buenas tardes", "buenas|hola"), ("vamos a pintar la cocina", "cocina;!no lo he entendido"), (img("este es el color que le gusta a mi mujer", png("amarillo")), "amarill*;mujer;!no lo he entendido"),
 ("¿qué color le gusta a mi mujer?", "amarill*"), (img("y este es el que me gusta a mí", png("azul")), "azul;!no lo he entendido"), ("¿qué color me gusta?", "azul;!amarill*"),
 ("al final la pintaremos de blanco", "blanc*;!no lo he entendido"), ("¿de qué color pintaremos la cocina?", "blanc*"), ("¿el blanco es un color?", "^si"),
 ("¿qué vamos a pintar?", "cocina")]}]
