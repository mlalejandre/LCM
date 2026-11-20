N = "!no lo he entendido"
D = [{"id": "a01", "cat": "aprender", "turnos": [
 ("un murlo es un animal que vive en los árboles", N), ("¿qué es un murlo?", "animal"), ("¿dónde vive un murlo?", "arbol*"), ("¿un murlo es un ser vivo?", "^si"), ("¿un murlo es un objeto?", "^no"),
 ("los murlos comen hojas", N), ("¿qué comen los murlos?", "hojas"), ("tengo un murlo", N), ("¿tengo un animal?", "^si"),
 ("una pinfa es una herramienta que sirve para doblar alambre", N), ("¿para qué sirve una pinfa?", "doblar"), ("¿qué sirve para doblar alambre?", "pinfa*"), ("¿una pinfa es un animal?", "^no"),
 ("lo contrario de rulo es tasco", N), ("¿qué es lo contrario de tasco?", "rulo"), ("chamullar significa hablar", N), ("¿qué significa chamullar?", "hablar"),
 ("un trebo tiene tres partes: el mango, la rueda y el gancho", N), ("¿qué partes tiene un trebo?", "mango;rueda;gancho"), ("¿un trebo tiene rueda?", "^si"), ("¿un trebo tiene motor?", "ABST"),
 ("los vasos también sirven para poner flores", N), ("¿qué sirve para poner flores?", "vaso*|jarron*|florero*"), ("¿qué es un flimo?", "ABST")]},
 {"id": "c01", "cat": "crear", "turnos": [
 ("escribe un poema sobre la lluvia", "lluvia;" + N), ("invéntate un cuento corto sobre un perro", "perro;" + N), ("escribe una frase con la palabra puerta", "puerta"),
 ("dime una palabra que rime con ratón", "cancion|corazon|camion|leon|melon|balon|avion|ilusion|razon"), ("invéntate una adivinanza", "que soy"), ("me rindo", "era"),
 ("cuéntame un chiste", N + ";!no se"), ("descríbeme una playa", "paisaje|arena"), ("ponle un título a un cuento sobre una tortuga", "tortuga"), ("dime tres verduras", N + ";!no se"),
 ("ayer escribí un poema", "!canto;" + N), ("¿qué escribí ayer?", "poema"), ("me gusta inventar cuentos", "!habia una vez;" + N)]}]
