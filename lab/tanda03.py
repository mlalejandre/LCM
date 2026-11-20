"""Tanda 3: comparaciones, datos de la persona, clases y conceptos de fábrica con formulaciones variadas."""
from lab.banco import correr, imprime
D = [
 {"id": "t3-comp1", "cat": "comparativos", "turnos": [
   ("Ana es más alta que Luis.", "ACK"), ("Luis es más alto que Pedro.", "ACK"), ("¿Quién es más alto: Pedro o Ana?", "^ana|ana es"), ("Entre Ana y Pedro, ¿quién es más alto?", "^ana|ana es"),
   ("¿Quién es el más alto?", "ana"), ("¿Quién es el más bajo?", "pedro"), ("¿Es Pedro más bajo que Ana?", "^si"), ("¿Es Luis más alto que Ana?", "^no"), ("¿Quién es más alto, Luis o Marta?", "ABST")]},
 {"id": "t3-comp2", "cat": "comparativos", "turnos": [
   ("Ana tiene 30 años.", "ACK"), ("Luis tiene 25 años.", "ACK"), ("Pedro tiene 41 años.", "ACK"), ("¿Quién tiene más años, Ana o Luis?", "^ana|ana es|ana tiene"), ("¿Quién es mayor: Luis o Ana?", "^ana|ana es"),
   ("¿Es Ana mayor que Luis?", "^si"), ("¿Es Luis mayor que Pedro?", "^no"), ("¿Quién es más joven, Ana o Luis?", "^luis|luis es"), ("¿Quién es el mayor?", "pedro"), ("¿Cuántos años le lleva Ana a Luis?", "cinco|5")]},
 {"id": "t3-comp3", "cat": "comparativos", "turnos": [
   ("Mi coche es más rápido que tu moto.", "!no he entendido"), ("Sara es menos alta que Diego.", "ACK"), ("¿Quién es más alto, Sara o Diego?", "^diego|diego es"), ("Jorge es tan alto como Diego.", "ACK"),
   ("Marta es mayor que Elena.", "ACK"), ("¿Es Elena menor que Marta?", "^si"), ("¿Quién es mayor, Marta o Elena?", "^marta|marta es"), ("¿Es Marta más joven que Elena?", "^no")]},
 {"id": "t3-usuario1", "cat": "usuario", "turnos": [
   ("Mi nombre es Lucía.", "lucia"), ("Soy ingeniera.", "ACK"), ("Vivo en Toledo desde hace dos años.", "ACK"), ("¿Recuerdas mi nombre?", "lucia"), ("¿Sabes cómo me llamo?", "lucia"),
   ("¿En qué ciudad vivo?", "toledo"), ("¿Cuál es mi profesión?", "ingenier*"), ("¿En qué trabajo?", "ingenier*"), ("¿Soy médica?", "!^si"), ("¿Qué recuerdas de mí?", "lucia;toledo;ingenier*")]},
 {"id": "t3-usuario2", "cat": "usuario", "turnos": [
   ("Soy Diego.", "diego"), ("Tengo 52 años.", "ACK"), ("Tengo una perra.", "ACK"), ("Se llama Nala.", "ACK"), ("¿Qué edad tengo?", "52"), ("¿Cuál es mi edad?", "52"),
   ("¿Cuál es el nombre de mi perra?", "nala"), ("¿Cómo se llama mi perra?", "nala"), ("Me encanta la música.", "ACK"), ("¿Sabes qué me gusta?", "musica"), ("¿Me gusta la música?", "^si"),
   ("Cuéntame lo que sabes de mí.", "diego;52|nala")]},
 {"id": "t3-usuario3", "cat": "usuario", "turnos": [
   ("Yo me llamo Elena y soy profesora.", "elena"), ("Trabajo en un colegio de Sevilla.", "ACK"), ("¿Dónde trabajo?", "colegio"), ("¿A qué me dedico?", "profesor*"), ("¿Quién soy?", "elena"),
   ("Mi marido se llama Raúl.", "ACK"), ("¿Cómo se llama mi marido?", "raul"), ("¿Quién es Raúl?", "marido"), ("¿Estoy casada?", "!^no"), ("Tengo dos hijas.", "ACK"), ("¿Tengo hijos?", "^si|dos")]},
 {"id": "t3-clases1", "cat": "clases", "turnos": [
   ("Toby es un perro.", "ACK"), ("¿Toby es un animal?", "^si"), ("¿Qué tipo de animal es Toby?", "perro"), ("¿Toby qué es?", "perro"), ("Los perros comen carne.", "ACK"), ("¿Come carne Toby?", "^si"),
   ("¿Qué come Toby?", "carne"), ("Toby es de Marta.", "ACK"), ("¿Quién es el dueño de Toby?", "marta"), ("¿De quién es Toby?", "marta"), ("¿Tiene Marta un perro?", "^si"), ("¿Es Toby una persona?", "!^si")]},
 {"id": "t3-clases2", "cat": "clases", "turnos": [
   ("Un delfín es un mamífero.", "ACK"), ("¿Es un delfín un animal?", "^si"), ("¿Es un delfín un pez?", "^no"), ("Flipper es un delfín.", "ACK"), ("¿Es Flipper un mamífero?", "^si"),
   ("Los delfines viven en el mar.", "ACK"), ("¿Dónde vive Flipper?", "mar"), ("Todos los mamíferos respiran aire.", "ACK"), ("¿Respira aire Flipper?", "^si"), ("¿Por qué?", "delfin*;mamifero*")]},
 {"id": "t3-fabrica", "cat": "fabrica", "turnos": [
   ("¿Un caballo es un animal?", "^si"), ("¿Qué es una rosa?", "flor"), ("¿Cuántos lados tiene un rectángulo?", "cuatro|4"), ("¿Es un roble una planta?", "^si"), ("¿De qué color es la sangre?", "roj*"),
   ("¿Es marzo un mes?", "^si"), ("¿Para qué sirve una silla?", "sentar*"), ("¿Tiene un coche motor?", "^si"), ("¿Es un pájaro un mamífero?", "^no"), ("¿Es una cama un mueble?", "^si"),
   ("¿Es el pan un alimento?", "^si"), ("¿Es un gato una planta?", "^no"), ("¿Qué es lo contrario de grande?", "pequeñ*"), ("¿Es un triángulo un polígono?", "^si"), ("¿Es un triángulo una figura?", "^si")]},
 {"id": "t3-nombres", "cat": "nombres", "turnos": [
   ("Rosa vive en León.", "ACK"), ("¿Dónde vive Rosa?", "leon"), ("Clara es la hermana de Rosa.", "ACK"), ("¿Quién es la hermana de Rosa?", "clara"), ("Háblame de Clara.", "hermana"),
   ("Óscar es el marido de Clara.", "ACK"), ("¿Quién es el marido de Clara?", "oscar"), ("¿Quién es la mujer de Óscar?", "clara"), ("Iván y Óscar son amigos.", "ACK"), ("¿Son amigos Iván y Óscar?", "^si"),
   ("¿Quién es amigo de Iván?", "oscar")]},
]
if __name__ == "__main__":
    f, r = correr(D, verboso=True, salida="lab/res_tanda03.json"); imprime(r, "TANDA 3")
