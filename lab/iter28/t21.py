from lab.imagenes import png, img, figura
D = [{"id": "k21", "cat": "libre", "turnos": [
 ("buenas tardes", "buenas|hola"), ("mi gata ha tenido gatitos", "gatitos;!no lo he entendido"), ("ha tenido cuatro, dos negros y dos blancos", "ANY"),
 ("¿cuántos gatitos ha tenido mi gata?", "cuatro|4"), ("mi gata se llama Mimi", "mimi;!no lo he entendido"), ("¿cómo se llama mi gata?", "mimi"),
 (img("esta es Mimi", png("gris")), "gris;!no lo he entendido"), ("¿de qué color es Mimi?", "gris"), ("voy a regalar dos gatitos a mis vecinos", "vecinos;!no lo he entendido"),
 ("¿a quién voy a regalar los gatitos?", "vecinos")]}]
