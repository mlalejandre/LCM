"""Tanda 11 (desarrollo; antes examen ciego 4, pasado una vez a ciegas con el commit it19: 90.00 %, 3.33 % falsas).
Multimodal con formulaciones nuevas, más conversación general para vigilar regresiones."""
from lab.banco import correr, imprime
from lab.imagenes import png, figura, img
D = [
 {"id": "c4-img1", "cat": "multimodal", "turnos": [
   (img("Te paso una foto. ¿Qué color predomina?", png("amarillo")), "amarill*"), ("¿Es verde?", "^no;amarill*"), ("¿Qué frutas tienen este color?", "platano*|limon*;!fresa*"),
   ("¿Puede ser un limón?", "^si|podria"), ("¿Puede ser una lechuga?", "^no;verde*"), ("Mi bici es de este color.", "ACK|amarill*"), ("¿Qué color tiene mi bici?", "amarill*")]},
 {"id": "c4-img2", "cat": "multimodal", "turnos": [
   (img("¿Qué hay en la imagen?", figura("triangulo", "rojo", "negro")), "triangulo;roj*;negr*"), ("¿La figura es azul?", "^no;roj*"), ("¿De qué color es el fondo?", "negr*"),
   ("¿Tiene cuatro lados?", "^no|tres|3"), ("¿Es un polígono?", "^si"), (img("¿Y esta otra?", figura("circulo", "verde", "blanco")), "circulo;verde"), ("¿Cuántos lados tiene?", "ningun*|no tiene")]},
 {"id": "c4-img3", "cat": "multimodal", "turnos": [
   ("Mi perro se llama Bruno.", "ACK"), (img("Así es Bruno de color.", png("marron")), "ANY"), (img("Bruno es de este color.", png("marron")), "ACK|marron|marrón"), ("¿De qué color es Bruno?", "marron|marrón"),
   ("¿Bruno es gris?", "^no;marron|marrón"), (img("¿Bruno es de este color?", png("gris")), "^no;marron|marrón"), ("¿Bruno ladra?", "^si")]},
 {"id": "c4-img4", "cat": "multimodal", "turnos": [
   (img("Esto es una naranja.", png("naranja")), "ACK|naranja"), ("¿Qué es esto?", "naranja"), ("¿Es una fruta?", "^si"), ("¿Es un animal?", "^no"),
   (img("¿Y esto qué color es?", png("rosa")), "rosa"), (img("Esto es un cuervo.", png("blanco")), "ANY"), ("¿Los cuervos son blancos?", "^no;negr*")]},
 {"id": "c4-img5", "cat": "multimodal", "turnos": [
   (img("", figura("cuadrado", "morado", "blanco")), "cuadrado;morad*"), ("¿Es un rectángulo?", "ANY"), ("¿Es un círculo?", "^no;cuadrado"), (img("", png("turquesa")), "ABST|no determin*"),
   ("¿De qué color es?", "ABST"), ("¿Qué colores distingues?", "rojo;azul")]},
 {"id": "c4-sin", "cat": "antialucinacion", "turnos": [
   ("¿Qué ves en la foto?", "ABST|ninguna imagen|todavia no|no he"), ("¿Es roja la imagen?", "ABST|ninguna imagen|todavia no|no he"), ("Mi coche es de este color.", "ABST|que color|no he|ninguna imagen|imagen")]},
 {"id": "c4-conv1", "cat": "conversacion", "turnos": [
   ("Hola, soy Lidia.", "lidia"), ("Trabajo de veterinaria en Teruel.", "ACK"), ("Tengo un hermano que se llama Óscar.", "ACK"), ("Óscar tiene una tortuga.", "ACK"),
   ("¿En qué trabajo?", "veterinari*"), ("¿Qué mascota tiene mi hermano?", "tortuga"), ("¿La tortuga de Óscar tiene caparazón?", "^si"), ("¿Es un mamífero la tortuga?", "^no|reptil"),
   ("¿Quiénes son mis familiares?", "oscar"), ("¿Dónde trabajo?", "teruel")]},
 {"id": "c4-conv2", "cat": "conversacion", "turnos": [
   ("Mi abuelo tiene noventa y un años.", "ACK"), ("¿Cuántos años tiene mi abuelo?", "91|noventa y un*"), ("Mi abuelo no oye bien.", "ACK"), ("Nadie de mi familia habla inglés.", "ACK"),
   ("¿Habla inglés alguien de mi familia?", "^no|nadie"), ("Ayer mi abuelo perdió las gafas.", "ACK"), ("¿Qué perdió mi abuelo?", "gafas"), ("¿Mi abuelo es de mi familia?", "^si")]},
 {"id": "c4-conc", "cat": "conceptos", "turnos": [
   ("¿Qué animales tienen plumas?", "aves|pajaros"), ("¿Un pato vuela?", "^si"), ("¿Un pato es un mamífero?", "^no"), ("Dime tres herramientas.", "martillo|sierra|pala|taladro|destornillador|alicate|rastrillo|hacha|lima|tijera"),
   ("¿Qué diferencia hay entre un coche y una bicicleta?", "motor|ruedas|pedales"), ("¿Cuál es el contrario de lleno?", "vacio|vacío"), ("¿Las plantas necesitan agua?", "^si"), ("¿Una piedra necesita agua?", "ABST|^no")]},
]


def medir(verboso=False, salida="lab/res_tanda11.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "TANDA 11")
