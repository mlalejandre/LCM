"""Tanda 10 (desarrollo): multimodal. Lo que el LCM ve (color, forma) unido a los conceptos y a la conversación.
Criterios escritos antes de implementar la ronda 2.3."""
from lab.banco import correr, imprime
from lab.imagenes import png, figura, img
D = [
 {"id": "t10-color1", "cat": "color", "turnos": [
   (img("¿De qué color es esta imagen?", png("rojo")), "roj*"), ("¿Es azul?", "^no;roj*"), ("¿Es roja?", "^si"),
   ("¿Qué frutas son de este color?", "fresa*|cereza*;!platano*"), ("¿Podría ser un plátano?", "^no;amarillo*"), ("¿Podría ser una fresa?", "^si|podria|puede"),
   ("¿Qué es esto?", "ABST|imagen roj*|color rojo")]},
 {"id": "t10-color2", "cat": "color", "turnos": [
   (img("", png("naranja")), "naranja"), ("¿De qué color es?", "naranja"), (img("", png("morado")), "morado"), ("¿De qué color es?", "morado;!naranja"),
   (img("¿Y esta?", png("rosa")), "rosa"), (img("¿Qué color ves?", png("marron")), "marron|marrón"), (img("¿Qué color ves?", png("gris")), "gris"),
   (img("¿De qué color es?", png("turquesa")), "ABST|no determin*")]},
 {"id": "t10-color3", "cat": "color", "turnos": [
   (img("Mira esta imagen.", png("verde")), "verde"), ("Mi coche es de este color.", "ACK|verde"), ("¿De qué color es mi coche?", "verde"),
   (img("", png("azul")), "azul"), ("¿Es del mismo color que mi coche?", "^no;verde|azul"), ("La casa de Ana es de este color.", "ACK|azul"),
   ("¿De qué color es la casa de Ana?", "azul;!verde"), ("¿Mi coche es azul?", "^no;verde")]},
 {"id": "t10-forma1", "cat": "forma", "turnos": [
   (img("¿Qué ves?", figura("circulo", "rojo")), "circulo;roj*"), ("¿Qué forma tiene?", "circulo"), ("¿Es un cuadrado?", "^no;circulo"), ("¿De qué color es la figura?", "roj*"),
   ("¿Y el fondo?", "blanc*"), ("¿Es un polígono?", "^no"), (img("¿Y ahora?", figura("cuadrado", "azul")), "cuadrado;azul"), ("¿Es un polígono?", "^si"),
   ("¿Cuántos lados tiene?", "cuatro|4")]},
 {"id": "t10-forma2", "cat": "forma", "turnos": [
   (img("¿Qué forma es esta?", figura("triangulo", "verde")), "triangulo"), ("¿Cuántos lados tiene un triángulo?", "tres|3"), ("¿Es verde?", "^si"),
   (img("¿Y esto?", figura("rectangulo", "amarillo", aspecto=2.0, escala=0.8)), "rectangulo"), (img("¿Qué figura ves?", figura("estrella", "negro")), "ABST|estrella|no reconozco"),
   (img("¿Qué ves?", figura("circulo", "azul", fondo="amarillo")), "circulo;azul;amarill*")]},
 {"id": "t10-conceptos", "cat": "conceptos", "turnos": [
   (img("Esto es una fresa.", png("rojo")), "ACK|fresa"), ("¿Qué es esto?", "fresa"), ("¿De qué color es la fresa?", "roj*"), ("¿Es una fruta?", "^si"),
   (img("Esto es un plátano.", png("azul")), "ANY"), ("¿Los plátanos son azules?", "^no;amarillo*"), ("¿Qué colores sabes ver?", "rojo;azul;verde")]},
 {"id": "t10-mascota", "cat": "mezcla", "turnos": [
   ("Tengo una gata que se llama Luna.", "ACK"), (img("Luna es de este color.", png("negro")), "ACK|negr*"), ("¿De qué color es Luna?", "negr*"), ("¿Luna es blanca?", "^no;negr*"),
   ("¿Luna es un animal?", "^si"), (img("¿Este es el color de Luna?", png("negro")), "^si"), (img("¿Y este?", png("blanco")), "^no;negr*")]},
 {"id": "t10-muestra", "cat": "salida", "turnos": [
   ("Muéstrame el color verde.", "verde"), ("¿De qué color es la hierba?", "verde"), ("¿Qué color tienen los plátanos?", "amarillo*"), ("¿De qué color es un cuervo?", "negr*")]},
 {"id": "t10-sin-imagen", "cat": "antialucinacion", "turnos": [
   ("¿De qué color es esta imagen?", "ABST|todavia no|ninguna imagen"), ("¿Qué forma tiene?", "ABST|ninguna imagen|no he visto|todavia no|no se"),
   ("¿Qué ves?", "ANY")]},
]
if __name__ == "__main__":
    import sys
    f, r = correr(D, verboso="-v" in sys.argv, salida="lab/res_tanda10.json")
    imprime(r, "TANDA 10")
