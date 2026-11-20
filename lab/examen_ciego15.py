"""EXAMEN CIEGO 15 (ronda 2.15): conceptos usados en la charla, varias clases, relaciones y procedencia. Escrito con la 2.14 congelada."""
from lab.banco import correr, imprime
D = [
 {"id": "c15-her", "cat": "herencia_charla", "turnos": [
   ("hola", "hola"), ("mi hermana tiene un hámster y dos periquitos", "hamster|periquitos;!no lo he entendido"), ("¿mi hermana tiene un mamífero?", "^si"),
   ("¿mi hermana tiene aves?", "^si"), ("¿mi hermana tiene un pez?", "^no|ABST"), ("¿cuántos animales tiene mi hermana?", "3|tres"),
   ("ayer comí lentejas y una manzana", "lentejas|manzana;!no lo he entendido"), ("¿comí fruta ayer?", "^si"), ("¿comí legumbres ayer?", "^si"),
   ("¿comí carne ayer?", "^no|ABST"), ("¿qué fruta comí?", "manzana"), ("he vendido el piano", "piano;!no lo he entendido"), ("¿he vendido un instrumento?", "^si"),
   ("¿qué instrumento he vendido?", "piano")]},
 {"id": "c15-per", "cat": "personas", "turnos": [
   ("hola", "hola"), ("mi cuñado Raúl es fontanero", "fontanero;!no lo he entendido"), ("¿Raúl es una persona?", "^si"), ("¿mi cuñado es un profesional?", "^si"),
   ("¿Raúl es un animal?", "^no"), ("¿Raúl es de mi familia?", "^si"), ("mi jefa es una mujer muy seria", "seria;!no lo he entendido"), ("¿mi jefa es una persona?", "^si"),
   ("¿mi jefa es graciosa?", "^no")]},
 {"id": "c15-var", "cat": "varias_clases", "turnos": [
   ("hola", "hola"), ("¿la comida es un alimento?", "^si"), ("¿un desayuno es una comida?", "^si"), ("¿una ensaladera es un recipiente?", "^si"),
   ("¿una rosa es una flor?", "^si"), ("¿el rosa es un color?", "^si"), ("¿una tijera es una herramienta?", "^si"), ("¿un pollo es un ave?", "^si"),
   ("¿el pollo es un alimento?", "^si|carne"), ("¿un zapato es un animal?", "^no"), ("¿un vaso es un recipiente?", "^si")]},
 {"id": "c15-rel", "cat": "relaciones", "turnos": [
   ("hola", "hola"), ("¿para qué sirve una escoba?", "barrer|limpiar"), ("¿de qué está hecho un jersey?", "lana|algodon|tela|tejido"), ("¿dónde suele estar una cama?", "dormitorio|habitacion"),
   ("¿quién usa una sartén?", "cocinero"), ("¿qué sirve para sentarse?", "silla|sofa|sillon|banco|taburete"), ("¿qué hay en un baño?", "lavabo|ducha|bañera|vater|espejo"),
   ("¿con qué se corta el pan?", "cuchillo"), ("he comprado una sierra", "sierra;!no lo he entendido"), ("¿he comprado algo para cortar?", "^si|sierra"),
   ("¿una silla sirve para sentarse?", "^si"), ("¿una silla sirve para cortar?", "^no")]},
 {"id": "c15-fab", "cat": "fabrica_y_dicho", "turnos": [
   ("hola", "hola"), ("el loro de mi abuela no habla", "habla;!no lo he entendido"), ("¿el loro de mi abuela habla?", "^no"), ("¿los loros hablan?", "^si"),
   ("Marta sabe cocinar", "marta;!no lo he entendido"), ("¿quién sabe cocinar?", "marta"), ("¿los cocineros cocinan?", "^si"), ("¿los peces vuelan?", "^no"),
   ("¿cómo lo sabes?", "fabrica"), ("mi gato tiene tres patas", "tres|3;!no lo he entendido"), ("¿cuántas patas tiene mi gato?", "tres|3"), ("¿cuántas patas tiene un gato?", "cuatro|4")]},
]


def medir(verboso=False, salida="lab/res_ciego15.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    f, r = medir()
    imprime(r, "EXAMEN CIEGO 15")
