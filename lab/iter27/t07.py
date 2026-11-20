from lab.imagenes import png, img, figura
D = [{"id": "j07", "cat": "libre", "turnos": [
 ("hola", "hola"), ("mis vecinos, que son muy simpáticos, tienen un gato", "gato;!no lo he entendido"), ("el gato se llama Bigotes y es naranja", "bigotes;naranja;!no lo he entendido"),
 ("¿cómo son mis vecinos?", "simpaticos"), ("¿qué tienen mis vecinos?", "gato"), ("¿de qué color es Bigotes?", "naranja"),
 (img("este es el color de mi bici", png("rosa")), "rosa;!no lo he entendido"), ("¿de qué color es mi bici?", "rosa"),
 ("¿Bigotes es del mismo color que mi bici?", "^no"), ("¿un gato es un animal?", "^si")]}]
