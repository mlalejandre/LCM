"""TERMÓMETRO GENERAL DEL LCM (escrito con la 2.15 congelada, antes de la campaña de entrenamiento 2.16+).
Examen FIJO por capacidades para medir la evolución real: se mide en cada versión y sus respuestas no se leen hasta la auditoría final.
Capacidades: A memoria de conversación · B conceptos · C razonamiento · D lectura de un texto inserto · E aprender conceptos en la charla ·
F creatividad a petición · G cálculo · H charla social y sobre sí mismo · I robustez (erratas, coloquial, frases largas).
python -m lab.termometro [-v]"""
from lab.banco import correr, imprime
N = "!no lo he entendido"
T1 = ("Te voy a leer un texto. Ayer por la tarde Clara fue al mercado con su abuelo. Compraron tomates, queso y una barra de pan. "
      "Después merendaron en una cafetería de la plaza. Clara pidió un chocolate caliente y su abuelo un café. Volvieron a casa en autobús porque empezó a llover.")
T2 = "Lee esto: El lince es un felino que vive en el monte. Tiene las orejas puntiagudas y la cola corta. Caza conejos al anochecer. Es un animal solitario y muy silencioso."
T3 = ("Escucha: Mi amiga Paula trabaja de enfermera en Bilbao. Tiene un hijo que se llama Leo y una perra que se llama Kira. Los sábados lleva a Leo a natación "
      "y los domingos pasea con Kira por la playa. El mes que viene se muda a Vitoria porque ha encontrado un trabajo mejor.")
D = [
 {"id": "tm-A1", "cat": "A_memoria", "turnos": [
   ("me llamo Irene y vivo en Cuenca", "irene|cuenca;" + N), ("¿cómo me llamo?", "irene"), ("¿dónde vivo?", "cuenca"), ("tengo dos hijos, Hugo y Vera", "hugo|vera;" + N),
   ("¿cuántos hijos tengo?", "dos|2"), ("¿cómo se llaman mis hijos?", "hugo;vera"), ("Hugo tiene 8 años y Vera tiene 5", "8|5|ocho|cinco;" + N), ("¿quién es mayor, Hugo o Vera?", "hugo"),
   ("¿cuántos años tiene Vera?", "5|cinco"), ("trabajo en una panadería", "panaderia;" + N), ("no, perdona, trabajo en una librería", "libreria;" + N),
   ("¿dónde trabajo?", "libreria;!panaderia"), ("¿qué sabes de mí?", "irene|cuenca|libreria")]},
 {"id": "tm-A2", "cat": "A_memoria", "turnos": [
   ("mi madre se llama Lola y mi padre Andrés", "lola|andres;" + N), ("¿cómo se llama mi padre?", "andres"), ("a mi madre le gusta el jazz", "jazz;" + N),
   ("¿qué le gusta a mi madre?", "jazz"), ("¿a quién le gusta el jazz?", "lola|madre"), ("el martes voy al dentista", "martes|dentista;" + N), ("¿cuándo voy al dentista?", "martes"),
   ("¿qué hago el martes?", "dentista"), ("mi hermano vive en Lisboa desde 2020", "lisboa|2020;" + N), ("¿desde cuándo vive mi hermano en Lisboa?", "2020"),
   ("¿quién vive en Lisboa?", "hermano"), ("¿mi hermano vive en Madrid?", "^no")]},
 {"id": "tm-B", "cat": "B_conceptos", "turnos": [
   ("¿un delfín es un pez?", "^no"), ("¿qué es un delfín?", "mamifero|animal"), ("¿qué es lo contrario de ancho?", "estrecho"), ("¿qué partes tiene un árbol?", "tronco|ramas|raiz|raices|hojas"),
   ("¿para qué sirve un cepillo de dientes?", "dientes"), ("¿dónde suele estar un horno?", "cocina"), ("¿en qué se parecen un tren y un autobús?", "vehiculo*|transport*|pasajer*|ruedas"),
   ("¿en qué se diferencian un pájaro y un pez?", "vol*|plumas|agua|nad*|alas|escamas"), ("¿una ballena vive en el agua?", "^si"), ("¿los gatos ladran?", "^no"),
   ("¿qué animal ladra?", "perro*"), ("¿qué come una vaca?", "hierba|pasto|plantas"), ("¿de qué color es la nieve?", "blanc*"), ("¿qué es más grande, un elefante o un ratón?", "elefante"),
   ("¿el hielo está frío o caliente?", "frio"), ("dime tres frutas", "manzana*|pera*|platano*|naranja*|fresa*|uva*|melon*|sandia*|limon*|cereza*"),
   ("dime un animal que vuele", "pajaro*|aguila*|paloma*|murcielago*|mosca*|abeja*|mariposa*|ave*|gaviota*|loro*|buho*|golondrina*|canario*|gorrion*"),
   ("¿qué estación viene después del verano?", "otoño"), ("¿qué día viene antes del jueves?", "miercoles"), ("¿cuántos días tiene una semana?", "siete|7"),
   ("¿qué hace un panadero?", "pan"), ("¿quién apaga los fuegos?", "bombero*"), ("¿un coche tiene alas?", "^no"), ("¿qué se usa para barrer?", "escoba*")]},
 {"id": "tm-C1", "cat": "C_razonar", "turnos": [
   ("todos los flamencos son aves", N), ("Pinky es un flamenco", "pinky|flamenco;" + N), ("¿Pinky es un ave?", "^si"), ("¿Pinky tiene plumas?", "^si"), ("¿Pinky es un mamífero?", "^no"),
   ("¿Pinky sabe cantar ópera?", "ABST|^no"), ("ningún reptil tiene pelo", N), ("Rex es un lagarto", "rex|lagarto;" + N), ("¿Rex tiene pelo?", "^no")]},
 {"id": "tm-C2", "cat": "C_razonar", "turnos": [
   ("Marta es más alta que Julia", "marta|julia;" + N), ("Julia es más alta que Noa", "julia|noa;" + N), ("¿quién es la más alta?", "marta"), ("¿Noa es más baja que Marta?", "^si"),
   ("¿quién es la más baja?", "noa"), ("Eva y Sara tienen la misma edad", "eva|sara;" + N), ("Eva tiene 30 años", "30|treinta;" + N), ("¿cuántos años tiene Sara?", "30|treinta")]},
 {"id": "tm-C3", "cat": "C_razonar", "turnos": [
   ("si llueve, me quedo en casa", N), ("hoy llueve", N), ("¿me quedo en casa hoy?", "^si"), ("las llaves están en el bolso o en el coche", "bolso|coche;" + N),
   ("no están en el bolso", N), ("¿dónde están las llaves?", "coche"), ("llegué tarde porque perdí el autobús", "tarde|autobus;" + N), ("¿por qué llegué tarde?", "autobus")]},
 {"id": "tm-C4", "cat": "C_razonar", "turnos": [
   ("primero desayuné, después me duché y luego salí a correr", N), ("¿qué hice después de desayunar?", "duch*"), ("¿qué hice antes de salir a correr?", "duch*"),
   ("¿qué hice primero?", "desayun*"), ("el libro está dentro de la caja y la caja está en el armario", "libro|caja;" + N), ("¿dónde está el libro?", "caja|armario"),
   ("¿el libro está en el armario?", "^si"), ("Carlos es el padre de Lucía y Lucía es la madre de Teo", "carlos|lucia|teo;" + N), ("¿quién es el abuelo de Teo?", "carlos"),
   ("¿Teo es nieto de Carlos?", "^si"), ("tenía 10 euros, gasté 4 y luego me dieron 2", N), ("¿cuánto dinero tengo ahora?", "8|ocho")]},
 {"id": "tm-D1", "cat": "D_lectura", "turnos": [
   (T1, N), ("¿con quién fue Clara al mercado?", "abuelo"), ("¿qué compraron?", "tomates;queso"), ("¿dónde merendaron?", "cafeteria"), ("¿qué pidió Clara?", "chocolate"),
   ("¿qué pidió el abuelo?", "cafe"), ("¿cómo volvieron a casa?", "autobus"), ("¿por qué volvieron en autobús?", "llov*|lluvia|llover"), ("¿cuándo fue Clara al mercado?", "ayer|tarde"),
   ("¿compraron algún alimento?", "^si"), ("¿Clara pidió una bebida?", "^si"), ("¿fueron al cine?", "^no|ABST")]},
 {"id": "tm-D2", "cat": "D_lectura", "turnos": [
   (T2, N), ("¿qué es un lince?", "felino"), ("¿dónde vive el lince?", "monte"), ("¿cómo tiene las orejas el lince?", "puntiagudas"), ("¿qué caza el lince?", "conejos"),
   ("¿cuándo caza?", "anochecer"), ("¿el lince es un animal?", "^si"), ("¿cómo es el lince?", "solitario|silencioso"), ("¿el lince tiene la cola larga?", "^no")]},
 {"id": "tm-D3", "cat": "D_lectura", "turnos": [
   (T3, N), ("¿a qué se dedica Paula?", "enfermera"), ("¿dónde trabaja Paula?", "bilbao"), ("¿cómo se llama el hijo de Paula?", "leo"), ("¿quién es Kira?", "perra"),
   ("¿qué hace Paula los sábados?", "natacion"), ("¿con quién pasea Paula los domingos?", "kira"), ("¿dónde pasea Paula?", "playa"), ("¿adónde se muda Paula?", "vitoria"),
   ("¿por qué se muda?", "trabajo"), ("¿Paula tiene un animal?", "^si"), ("¿cuándo se muda?", "mes")]},
 {"id": "tm-E", "cat": "E_aprender", "turnos": [
   ("un zorb es un animal que vive en las cuevas", N), ("¿qué es un zorb?", "animal"), ("¿dónde vive un zorb?", "cueva*"), ("¿un zorb es un ser vivo?", "^si"), ("¿un zorb es un objeto?", "^no"),
   ("los zorbs comen musgo", N), ("¿qué comen los zorbs?", "musgo"), ("tengo un zorb", "zorb;" + N), ("¿tengo un animal?", "^si"),
   ("una trinca es una herramienta que sirve para pelar cables", N), ("¿para qué sirve una trinca?", "pelar|cables"), ("¿una trinca es una herramienta?", "^si"),
   ("¿qué sirve para pelar cables?", "trinca*"), ("¿una trinca es un animal?", "^no"), ("lo contrario de fleco es brumo", N), ("¿qué es lo contrario de fleco?", "brumo"),
   ("¿qué es lo contrario de brumo?", "fleco"), ("birlar significa robar", N), ("¿qué significa birlar?", "robar"), ("un glomo tiene tres partes: la base, el eje y la tapa", N),
   ("¿qué partes tiene un glomo?", "base;eje;tapa"), ("¿un glomo tiene eje?", "^si"), ("¿qué es un plucto?", "ABST")]},
 {"id": "tm-F", "cat": "F_crear", "turnos": [
   ("escribe un poema sobre el mar", "mar|olas;" + N), ("invéntate un cuento corto sobre un gato", "gato;" + N), ("escribe una frase con la palabra ventana", "ventana"),
   ("dime una palabra que rime con canción", "corazon|emocion|estacion|ilusion|razon|leon|camion|avion|melon|raton|balon|pasion|nacion|accion|leccion|habitacion|oracion|cancion"),
   ("invéntate una adivinanza", "que es|adivina|quien soy|que soy;" + N), ("cuéntame un chiste", N + ";!no se;!no puedo"), ("descríbeme un bosque", "arbol*"),
   ("ponle un título a un cuento sobre un dragón", "dragon"), ("dime un sinónimo de bonito", "hermoso|bello|lindo|precioso|guapo"), ("mi hija se llama Vera y le encantan los caballos", "vera|caballos;" + N),
   ("escribe un poema para mi hija", "vera|caballo*"), ("dame tres ideas para regalarle", "caballo*|libro|juguete|peluche"), ("invéntate un nombre para un perro", N + ";!no se;!no puedo;!no lo se"),
   ("ayer escribí un poema", "!mar;!olas;" + N), ("¿qué escribí ayer?", "poema"), ("termina la frase: el sol salió y", N + ";!no se;!no lo se")]},
 {"id": "tm-G", "cat": "G_calculo", "turnos": [
   ("¿cuánto es 37 más 48?", "85"), ("¿cuánto es el 20 % de 150?", "30"), ("tengo 15 cromos y regalo 6, ¿cuántos me quedan?", "9"), ("¿cuánto es 9 por 7 menos 3?", "60"),
   ("¿cuál es la mitad de 250?", "125"), ("si un café cuesta 2 euros, ¿cuánto cuestan 5 cafés?", "10"), ("¿cuánto es mil dividido entre 8?", "125"), ("dibuja un cuadrado rojo", "cuadrado"),
   ("¿qué día será mañana si hoy es sábado?", "domingo"), ("¿cuántos minutos son dos horas?", "120"), ("¿cuántos días hay en tres semanas?", "21|veintiun*"),
   ("somos 4 y pagamos 60 euros a medias, ¿cuánto paga cada uno?", "15"), ("¿cuánto es 12 al cuadrado?", "144"), ("¿cuál es mayor, 0,5 o 0,25?", "0,5|0.5")]},
 {"id": "tm-H", "cat": "H_social", "turnos": [
   ("hola, ¿qué tal?", "hola|bien|que tal"), ("¿quién eres?", "lcm|modelo|asistente|programa"), ("¿qué sabes hacer?", "conversar|recordar|calcul*|dibuj*|aprend*|record*|hablar"),
   ("¿eres una persona?", "^no"), ("estoy un poco triste hoy", "siento|animo|pasa|quieres|contar*;" + N), ("es que he discutido con mi hermana", "hermana|siento|discut*;" + N),
   ("¿por qué estoy triste?", "discut*|hermana"), ("gracias por escucharme", "nada|gracias|gusto|aqui"), ("¿en qué año estamos?", "2026"), ("¿qué opinas del fútbol?", N),
   ("no he entendido lo último", N), ("cuéntame algo interesante", N + ";!no se;!no lo se"), ("¿de qué hemos hablado?", "hermana|triste|futbol|discut*"), ("me voy a dormir, buenas noches", "noches|descansa|hasta|adios")]},
 {"id": "tm-I", "cat": "I_robustez", "turnos": [
   ("ola me yamo pedro", "pedro"), ("komo me yamo", "pedro"), ("oye q tengo un perro q se llama Rufo", "rufo;" + N), ("como se llama mi perro", "rufo"),
   ("mi hermana, que vive en Roma y trabaja de arquitecta, viene el viernes", "roma|arquitecta|viernes;" + N), ("¿dónde vive mi hermana?", "roma"), ("¿a qué se dedica?", "arquitecta"),
   ("¿cuándo viene?", "viernes"), ("pues eso, que al final no voy a ir a la boda de mi primo", N), ("¿voy a ir a la boda?", "^no"), ("la verdad es que me encanta el queso azul", "queso;" + N),
   ("q me gusta?", "queso"), ("mñn tengo examen de mates", "examen;" + N), ("cuando tengo el examen", "mañana"), ("mi coche, el rojo, está en el taller", "taller|coche;" + N),
   ("donde esta mi coche", "taller"), ("de que color es mi coche", "rojo"), ("NO ME GUSTA NADA MADRUGAR", "madrugar;" + N), ("¿me gusta madrugar?", "^no")]},
]


def medir(verboso=False, salida="lab/res_termometro.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "TERMÓMETRO")
