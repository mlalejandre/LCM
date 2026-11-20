from lab.imagenes import png, img, figura
D = [{"id": "j11", "cat": "libre", "turnos": [
 ("buenos días", "buenos dias|hola"), ("me llamo Inés y tengo una floristería", "ines;floristeria;!no lo he entendido"), ("abro todos los días menos los domingos", "ANY"),
 (img("estas son las rosas que más vendo", png("rojo")), "rosas;roj*;!no lo he entendido"), ("¿de qué color son las rosas que más vendo?", "roj*"),
 ("mi socia, que se llama Pilar, se encarga de las cuentas", "pilar;!no lo he entendido"), ("¿quién se encarga de las cuentas?", "pilar"), ("¿qué tengo?", "floristeria"),
 ("¿las rosas son plantas?", "^si"), ("¿abro los domingos?", "^no|ABST")]}]
