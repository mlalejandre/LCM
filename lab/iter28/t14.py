from lab.imagenes import png, img, figura
D = [{"id": "k14", "cat": "libre", "turnos": [
 ("hola", "hola"), ("soy profesora de primaria", "profesora;!no lo he entendido"), ("tengo veinticinco alumnos este año", "veinticinco|25;!no lo he entendido"),
 ("hoy les he enseñado las formas geométricas", "formas;!no lo he entendido"), (img("¿qué forma es esta?", figura("triangulo", "azul")), "triangul*"),
 ("¿cuántos lados tiene?", "tres|3"), ("¿cuántos alumnos tengo?", "veinticinco|25"), ("¿qué les he enseñado hoy?", "formas"),
 ("¿a qué me dedico?", "profesora"), ("¿un triángulo es una figura?", "^si|ABST")]}]
