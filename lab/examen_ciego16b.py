"""EXAMEN CIEGO 16b · muestra LIMPIA de la campaña 2.16. Escrito tras congelar la 2.16 (commit 6ed1dcc) y antes de leer ninguna respuesta del termómetro.
Mismas capacidades que el termómetro, pero con otros contenidos y OTRAS FORMAS de decir las cosas (no las que usé al desarrollar)."""
from lab.banco import correr, imprime
N = "!no lo he entendido"
X1 = ("Voy a pegarte un texto. El verano pasado Rubén y su hermana Olga viajaron a Lisboa en tren. Se alojaron en un hostal cerca del río. "
      "Por las mañanas visitaban museos y por las tardes paseaban por el puerto. El último día Olga perdió su cartera en un tranvía, pero un policía se la devolvió.")
X2 = "Mira este texto: La tuba es un instrumento de viento muy grande. Está hecha de metal y pesa bastante. Se toca soplando por una boquilla. Suena grave y se usa en las bandas de música."
D = [
 {"id": "b-A", "cat": "A_memoria", "turnos": [
   ("soy Tomás y tengo 42 años", "tomas|42;" + N), ("¿qué edad tengo?", "42"), ("vivo con mi mujer, Nuria, en un piso de Zaragoza", "nuria|zaragoza;" + N), ("¿con quién vivo?", "nuria|mujer"),
   ("¿en qué ciudad vivo?", "zaragoza"), ("nuestro gato se llama Fideo", "fideo;" + N), ("¿cómo se llama el gato?", "fideo"), ("los jueves juego al pádel con Sergio", "padel|sergio;" + N),
   ("¿con quién juego al pádel?", "sergio"), ("¿qué día juego al pádel?", "jueves"), ("me he equivocado: juego los viernes, no los jueves", "viernes;" + N), ("¿cuándo juego al pádel?", "viernes;!jueves"),
   ("a Nuria le dan miedo las arañas", "aranas|arañas;" + N), ("¿a quién le dan miedo las arañas?", "nuria|mujer"), ("¿Nuria tiene miedo de las serpientes?", "ABST")]},
 {"id": "b-B", "cat": "B_conceptos", "turnos": [
   ("¿un murciélago es un pájaro?", "^no"), ("¿qué es un tiburón?", "pez|animal"), ("¿cuál es el contrario de lleno?", "vacio"), ("¿qué partes tiene una bicicleta?", "ruedas|pedales|manillar|sillin"),
   ("¿para qué sirve una toalla?", "secar*"), ("¿dónde se guarda la ropa?", "armario"), ("¿en qué se parecen una mesa y una silla?", "mueble*|patas"), ("¿las vacas vuelan?", "^no"),
   ("¿qué animal maúlla?", "gato*"), ("¿qué come un caballo?", "hierba|heno"), ("¿qué es más pequeño, un gato o un elefante?", "gato"), ("¿el fuego está frío o caliente?", "caliente"),
   ("dime dos colores", "rojo|azul|verde|amarillo|negro|blanco|naranja|rosa|gris|marron|morado"), ("¿qué mes va después de junio?", "julio"), ("¿cuántos meses tiene un año?", "doce|12"),
   ("¿qué hace un profesor?", "ensena*|enseña*"), ("¿quién conduce un taxi?", "taxista*"), ("¿un pez tiene patas?", "^no"), ("¿con qué se corta el papel?", "tijera*|cuter*")]},
 {"id": "b-C", "cat": "C_razonar", "turnos": [
   ("cualquier gato es un felino", N), ("Misi es una gata", N), ("¿Misi es un felino?", "^si"), ("¿Misi es un reptil?", "^no"),
   ("Jaime es mayor que Elena", N), ("Elena es mayor que Raúl", N), ("¿quién es el más joven?", "raul"), ("¿Jaime es mayor que Raúl?", "^si"),
   ("cuando hace sol, voy a la playa", N), ("hoy hace sol", N), ("¿voy a la playa hoy?", "^si"),
   ("me duché antes de cenar", N), ("después de cenar vi una película", N), ("¿qué hice después de ducharme?", "cen*"), ("¿qué hice después de cenar?", "pelicula"),
   ("Irene y yo medimos lo mismo", N), ("yo mido 170 centímetros", N), ("¿cuánto mide Irene?", "170"),
   ("el anillo está en el joyero y el joyero está en el cajón", N), ("¿el anillo está en el cajón?", "^si"),
   ("compré 6 huevos y se me rompieron 2", N), ("¿cuántos huevos me quedan?", "4|cuatro")]},
 {"id": "b-D1", "cat": "D_lectura", "turnos": [
   (X1, N), ("¿adónde viajaron Rubén y Olga?", "lisboa"), ("¿cómo viajaron?", "tren"), ("¿quién es Olga?", "hermana"), ("¿dónde se alojaron?", "hostal"),
   ("¿qué hacían por las mañanas?", "museos"), ("¿qué hacían por las tardes?", "puerto|pase*"), ("¿qué perdió Olga?", "cartera"), ("¿dónde la perdió?", "tranvia"),
   ("¿quién le devolvió la cartera?", "policia"), ("¿viajaron en avión?", "^no|ABST"), ("¿cuándo viajaron?", "verano")]},
 {"id": "b-D2", "cat": "D_lectura", "turnos": [
   (X2, N), ("¿qué es una tuba?", "instrumento"), ("¿de qué está hecha la tuba?", "metal"), ("¿cómo se toca la tuba?", "sopl*"), ("¿cómo suena la tuba?", "grave"),
   ("¿dónde se usa la tuba?", "banda*"), ("¿la tuba es pequeña?", "^no"), ("¿la tuba es un instrumento?", "^si")]},
 {"id": "b-E", "cat": "E_aprender", "turnos": [
   ("los grelos son verduras", N), ("¿qué son los grelos?", "verdura*"), ("¿un grelo es un alimento?", "^si"), ("¿un grelo es un mueble?", "^no"),
   ("un candil se usa para dar luz", N), ("¿para qué sirve un candil?", "luz"), ("¿qué sirve para dar luz?", "candil*|lampara*|bombilla*|linterna*"),
   ("las albarcas están hechas de madera", N), ("¿de qué están hechas las albarcas?", "madera"), ("fetén quiere decir estupendo", N), ("¿qué significa fetén?", "estupendo"),
   ("pocho es lo contrario de sano", N), ("¿qué es lo contrario de pocho?", "sano"), ("un botijo es un recipiente que sirve para enfriar el agua", N), ("¿qué es un botijo?", "recipiente"),
   ("tengo un botijo", N), ("¿tengo un recipiente?", "^si"), ("¿tengo algo para enfriar el agua?", "^si|botijo")]},
 {"id": "b-F", "cat": "F_crear", "turnos": [
   ("hazme una rima con sol", "girasol|caracol|farol|español|futbol|col|alcohol|arrebol|rol|bemol"), ("escríbeme un cuento sobre una tortuga", "tortuga;" + N),
   ("¿puedes escribir un poema sobre la luna?", "luna;" + N), ("dime una frase con la palabra río", "rio"), ("describe un coche", "ruedas|motor|vehiculo"),
   ("invéntate un título para un poema sobre el otoño", "otoño"), ("mi perro se llama Rex y le encanta la playa", "rex|playa;" + N), ("invéntate un cuento sobre Rex", "rex"),
   ("ponme un acertijo", "que soy|adivina"), ("me rindo, ¿qué era?", "era|es"), ("me encanta leer cuentos", "!habia una vez;" + N), ("¿qué me encanta?", "leer|cuentos"),
   ("quiero que me escribas unos versos sobre el mar", "mar;" + N), ("otro distinto", "mar;" + N)]},
 {"id": "b-G", "cat": "G_calculo", "turnos": [
   ("¿cuánto es 125 más 75?", "200"), ("¿cuánto es el 10 por ciento de 90?", "9"), ("había 30 alumnos y faltaron 4, ¿cuántos alumnos fueron?", "26"), ("¿cuánto es 8 por 6 más 2?", "50"),
   ("¿cuál es el triple de 12?", "36"), ("si un bolígrafo cuesta 3 euros, ¿cuánto cuestan 4 bolígrafos?", "12"), ("¿cuántas horas son 180 minutos?", "3|tres"),
   ("¿qué día fue ayer si hoy es lunes?", "domingo"), ("¿cuál es menor, 0,3 o 0,03?", "0,03|0.03"), ("dibuja dos triángulos verdes", "triangulo*"), ("¿cuánto es 100 entre 8?", "12,5|12.5")]},
 {"id": "b-H", "cat": "H_social", "turnos": [
   ("buenas tardes", "buenas|hola"), ("¿cómo te llamas?", "lcm"), ("¿eres un robot?", N), ("hoy estoy muy contento", "alegr*|me alegro|genial|que bien|estupendo;" + N),
   ("es que me han dado el trabajo", "trabajo|enhorabuena|felicidades|alegr*;" + N), ("¿por qué estoy contento?", "trabajo"), ("¿tú tienes sentimientos?", N),
   ("perdona, me he liado", N), ("¿qué recuerdas de mí?", "contento|trabajo"), ("hasta mañana", "mañana|hasta|adios|luego")]},
 {"id": "b-I", "cat": "I_robustez", "turnos": [
   ("wenas soy marta", "marta"), ("kien soy", "marta"), ("mi ermana se yama Julia i bibe en Vigo", "julia|vigo;" + N), ("donde vive mi hermana", "vigo"),
   ("pues mira, que me he comprado una moto", "moto;" + N), ("que me he comprado", "moto"), ("xfa dime cuanto es 5 mas 5", "10"), ("EL SÁBADO VOY AL CINE CON PABLO", "cine|pablo;" + N),
   ("con kien voy al cine", "pablo"), ("mi gato, el pequeño, se llama Tizón", "tizon;" + N), ("como se llama mi gato pequeño", "tizon"), ("no me mola nada el brócoli", "brocoli;" + N),
   ("¿me gusta el brócoli?", "^no")]},
]


def medir(verboso=False, salida="lab/res_ciego16b.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    f, r = medir()
    imprime(r, "EXAMEN CIEGO 16b (muestra limpia)")
