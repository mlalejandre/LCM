"""EXAMEN CIEGO 16c · medida FINAL limpia de la 2.16. Escrito tras congelar el código definitivo (después de los arreglos no ciegos) y medido UNA vez.
Tras esta medida no se toca nada: lo que falle aquí queda documentado como pendiente. Contenidos y formas distintos de termómetro, 16b y tandas."""
from lab.banco import correr, imprime
N = "!no lo he entendido"
Z = ("Te leo una nota. Esta mañana Berta salió de casa a las ocho con su hijo Dani. Lo dejó en la guardería y después cogió el metro para ir a la oficina. "
     "A mediodía comió una ensalada con su compañera Lidia. Por la tarde tuvo una reunión muy larga y llegó a casa cansada.")
D = [
 {"id": "c-A", "cat": "A_memoria", "turnos": [
   ("mi nombre es Celia", "celia"), ("estudio enfermería en Granada", "enfermeria|granada;" + N), ("¿qué estudio?", "enfermeria"), ("comparto piso con dos amigas, Sara y Noelia", "sara|noelia;" + N),
   ("¿con quién comparto piso?", "sara;noelia"), ("Sara toca el violín", "violin;" + N), ("¿qué instrumento toca Sara?", "violin"), ("el mes pasado estuve en Roma", "roma;" + N),
   ("¿dónde estuve el mes pasado?", "roma"), ("¿Noelia toca el piano?", "ABST")]},
 {"id": "c-B", "cat": "B_conceptos", "turnos": [
   ("¿una araña es un insecto?", "^no|aracnido"), ("¿qué es una trucha?", "pez|animal"), ("¿cuál es el contrario de encender?", "apagar"), ("¿de qué está hecho un jersey?", "lana"),
   ("¿dónde vive una vaca?", "granja|prado"), ("¿qué es más grande, una casa o un coche?", "casa"), ("¿para qué sirve un despertador?", "despertar*"), ("¿quién usa un pincel?", "pintor*"),
   ("¿qué tienen en común un cuchillo y unas tijeras?", "cortar"), ("dime dos instrumentos", "guitarra|piano|violin|flauta|tambor|trompeta"), ("¿cuántos minutos tiene una hora?", "sesenta|60"),
   ("¿los peces respiran aire?", "^no|ABST"), ("¿qué hay en un dormitorio?", "cama*|armario*")]},
 {"id": "c-C", "cat": "C_razonar", "turnos": [
   ("los delfines son mamíferos", N), ("Flipper es un delfín", N), ("¿Flipper es un mamífero?", "^si"), ("¿Flipper es un pez?", "^no"),
   ("Óscar corre más rápido que Lucas", N), ("Lucas corre más rápido que Mateo", N), ("¿quién corre más rápido, Óscar o Mateo?", "oscar"),
   ("si apruebo, me compro una bici", N), ("he aprobado", N), ("¿me compro una bici?", "^si"),
   ("antes de acostarme leí un rato", N), ("¿qué hice antes de acostarme?", "lei|leiste|leer"),
   ("el pasaporte está en la carpeta y la carpeta está en la maleta", N), ("¿dónde está el pasaporte?", "carpeta|maleta"), ("¿el pasaporte está en la maleta?", "^si"),
   ("tenía 50 euros y me gasté 20 en el cine", N), ("¿cuánto me queda?", "30")]},
 {"id": "c-D", "cat": "D_lectura", "turnos": [
   (Z, N), ("¿a qué hora salió Berta de casa?", "ocho|8"), ("¿quién es Dani?", "hijo"), ("¿dónde dejó a Dani?", "guarderia"), ("¿cómo fue a la oficina?", "metro"),
   ("¿qué comió?", "ensalada"), ("¿con quién comió?", "lidia"), ("¿quién es Lidia?", "companera|compañera"), ("¿qué tuvo por la tarde?", "reunion"), ("¿cómo llegó a casa?", "cansada"),
   ("¿fue a la oficina en coche?", "^no|ABST")]},
 {"id": "c-E", "cat": "E_aprender", "turnos": [
   ("un cuatí es un mamífero que vive en la selva", N), ("¿dónde vive un cuatí?", "selva"), ("¿un cuatí es un animal?", "^si"), ("¿un cuatí es una planta?", "^no"),
   ("un almirez sirve para machacar ajos", N), ("¿para qué sirve un almirez?", "machacar"), ("lo opuesto de chulo es soso", N), ("¿qué es lo contrario de chulo?", "soso"),
   ("currar es lo mismo que trabajar", N), ("¿qué significa currar?", "trabajar")]},
 {"id": "c-F", "cat": "F_crear", "turnos": [
   ("escríbeme un poema sobre el otoño", "otoño;" + N), ("dime algo que rime con camión", "avion|corazon|cancion|leon|melon|balon|raton|ilusion|razon|emocion|estacion"),
   ("invéntate un cuento sobre un dragón", "dragon;" + N), ("hazme una frase con la palabra silla", "silla"), ("descríbeme una cocina", "horno|nevera|fregadero|fogones|cocinar"),
   ("dame un nombre para una gata", N + ";!no se;!no lo se"), ("cuéntame otro chiste", N + ";!no se"), ("mi abuelo escribía poemas", "!van estos versos;" + N)]},
 {"id": "c-G", "cat": "G_calculo", "turnos": [
   ("¿cuánto es 64 menos 29?", "35"), ("¿cuánto es la cuarta parte de 100?", "25"), ("en un autobús van 18 personas y suben 7, ¿cuántas van ahora?", "25"), ("¿cuánto es 3 por 3 por 3?", "27"),
   ("¿cuántos segundos tiene un minuto?", "sesenta|60"), ("¿cuánto es 15 más el doble de 10?", "35"), ("si hoy es martes, ¿qué día será dentro de 3 días?", "viernes"), ("pinta una estrella roja", "estrella")]},
 {"id": "c-H", "cat": "H_social", "turnos": [
   ("hola, ¿cómo estás?", "hola|bien"), ("¿te gusta hablar conmigo?", N), ("hoy he tenido un día horrible", "siento|vaya|animo|contar*;" + N), ("es que se me ha roto el coche", "coche;" + N),
   ("¿por qué he tenido un mal día?", "coche"), ("bueno, me voy, gracias por todo", "nada|gracias|hasta|adios|gusto")]},
 {"id": "c-I", "cat": "I_robustez", "turnos": [
   ("ola kiero contarte algo", N), ("mi novio se yama alex", "alex"), ("komo se llama mi novio", "alex"), ("trabaja en 1 hospital dsd hace 2 años", "hospital;" + N),
   ("donde trabaja", "hospital"), ("Y TIENE UN HERMANO GEMELO", "hermano;" + N), ("alex tiene hermanos?", "^si"), ("le flipa el baloncesto", "baloncesto;" + N), ("que le gusta a alex", "baloncesto")]},
]


def medir(verboso=False, salida="lab/res_ciego16c.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    f, r = medir()
    imprime(r, "EXAMEN CIEGO 16c (medida final limpia)")
