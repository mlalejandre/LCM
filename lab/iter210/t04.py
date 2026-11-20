from lab.imagenes import img, escena, figura

D = [{"id": "p04", "cat": "imagen_espacio", "turnos": [
 ("hola", "hola"),
 (img("mira este dibujo", escena(("triangulo", "verde"), ("cuadrado", "naranja"))), "triangulo;cuadrado"),
 ("¿qué figura está arriba?", "triangulo;!cuadrado"),
 ("¿qué hay debajo del triángulo?", "cuadrado"),
 ("¿de qué color es la figura de abajo?", "naranja"),
 ("¿el cuadrado está encima del triángulo?", "^no"),
 (img("¿y en este?", escena(("circulo", "rojo"), ("estrella", "azul"), vertical=False)), "circulo;estrella"),
 ("¿qué figura está a la derecha?", "estrella"),
 ("¿qué hay a la izquierda de la estrella?", "circulo"),
 (img("¿qué forma es esta?", figura("estrella", "amarillo")), "estrella"),
 ("¿cuántas figuras ves?", "ABST|una|estrella"),
]}]
