from lab.imagenes import png, img, figura
D = [{"id": "k17", "cat": "libre", "turnos": [
 ("hey, ¿qué tal?", "hola|bien"), ("me acabo de comprar un coche", "coche;!no lo he entendido"), (img("es de este color", png("rojo")), "roj*;!no lo he entendido"),
 ("¿de qué color es mi coche?", "roj*"), ("es un coche eléctrico", "electrico;!no lo he entendido"), ("¿mi coche es eléctrico?", "^si"),
 ("me ha costado veinte mil euros", "veinte mil|20000|20.000;!no lo he entendido"), ("¿cuánto me ha costado el coche?", "veinte mil|20000|20.000"), ("¿un coche tiene ruedas?", "^si"),
 ("se lo voy a enseñar a mis padres", "ANY")]}]
