from lab.imagenes import png, img, figura
D = [{"id": "j03", "cat": "multimodal", "turnos": [
 ("hola", "hola"), ("estoy decorando mi habitación", "habitacion;!no lo he entendido"), (img("mira, este es el color de las cortinas", png("amarillo")), "amarill*;!no lo he entendido"),
 ("¿de qué color son las cortinas?", "amarill*"), (img("y esta es la alfombra que he comprado", figura("circulo", "rojo")), "roj*|circul*|redond*"),
 ("¿de qué color es la alfombra?", "roj*"), ("¿qué forma tiene la alfombra?", "circul*|redond*"), (img("¿qué color es este?", png("azul")), "azul"),
 ("las paredes las quiero de ese color", "ANY"), ("¿qué estoy decorando?", "habitacion")]}]
