"""EXAMEN CIEGO 6. Escrito con la 2.4 congelada, ANTES de las conversaciones libres de la ronda 2.5 y de mirar los fallos del ciego 5.
Charla natural: frases coloquiales, erratas, preguntas de repaso, cambios de tema. Solo se leen los agregados."""
from lab.banco import correr, imprime
from lab.imagenes import png, img
D = [
 {"id": "c6-coloquial", "cat": "coloquial", "turnos": [
   ("buenas", "hola|buenas"), ("oye, una cosa", "ANY"), ("mi hermana pequeña empieza mañana la universidad", "ACK"), ("va a estudiar biología en Salamanca", "ACK"),
   ("¿qué va a estudiar mi hermana?", "biologia"), ("¿dónde va a estudiar?", "salamanca"), ("¿cuándo empieza?", "mañana"), ("está bastante nerviosa", "ACK"),
   ("¿cómo está mi hermana?", "nerviosa"), ("yo estudié derecho", "ACK"), ("¿qué estudié yo?", "derecho"), ("¿y mi hermana estudió derecho?", "^no|ABST|biologia"),
   ("pues eso, ya te contaré", "ANY"), ("¿de qué te he hablado?", "hermana|universidad|biologia|derecho")]},
 {"id": "c6-erratas", "cat": "coloquial", "turnos": [
   ("me yamo Kike", "kike"), ("bibo en Alicante", "ACK|alicante"), ("tengo 2 gatos y 1 perro", "ACK"), ("cuantos animales tengo?", "tres|3"), ("donde vivo", "alicante"),
   ("como me llamo", "kike"), ("mi perro se yama Rocky", "ACK|rocky"), ("como se llama mi perro", "rocky"), ("rocky es un gato?", "^no;perro"), ("tengo peces?", "ABST|^no")]},
 {"id": "c6-planes", "cat": "tiempo", "turnos": [
   ("El sábado voy a ir a la playa con mis amigos.", "ACK"), ("El domingo tengo que estudiar.", "ACK"), ("¿Qué voy a hacer el sábado?", "playa"), ("¿Con quién voy a la playa?", "amigos"),
   ("¿Qué tengo que hacer el domingo?", "estudiar"), ("¿Cuándo voy a la playa?", "sabado"), ("Al final no voy a la playa.", "ACK"), ("¿Voy a ir a la playa el sábado?", "^no|ya no|al final no"),
   ("El lunes empiezo a trabajar en una tienda.", "ACK"), ("¿Cuándo empiezo a trabajar?", "lunes"), ("¿Dónde voy a trabajar?", "tienda")]},
 {"id": "c6-opinion", "cat": "social", "turnos": [
   ("¿Tú qué opinas del fútbol?", "no tengo|opinion*"), ("A mí me aburre.", "ACK"), ("¿Me gusta el fútbol?", "^no|aburre"), ("¿Sabes contar chistes?", "ANY"), ("¿Cuánto es dos más dos?", "cuatro|4"),
   ("¿Qué día es hoy?", "18|miercoles|noviembre"), ("¿Te acuerdas de mi nombre?", "ABST|no me has dicho|no se como"), ("Me llamo Julia.", "julia"), ("¿Te acuerdas de mi nombre?", "julia"),
   ("Eres muy majo.", "gracias"), ("¿Estás cansado?", "no")]},
 {"id": "c6-casa", "cat": "descripcion", "turnos": [
   ("Mi casa tiene dos plantas.", "ACK"), ("En la planta baja están la cocina y el salón.", "ACK"), ("Arriba hay tres dormitorios y un baño.", "ACK"), ("El salón es muy grande.", "ACK"),
   ("¿Cuántas plantas tiene mi casa?", "dos|2"), ("¿Dónde está la cocina?", "planta baja|abajo"), ("¿Cuántos dormitorios hay?", "tres|3"), ("¿Cómo es el salón?", "grande"),
   ("¿El salón es pequeño?", "^no;grande"), ("¿Una cocina es una habitación?", "^si"), ("¿Tengo garaje?", "ABST"), (img("Las paredes del salón son de este color.", png("blanco")), "ACK|blanc*"),
   ("¿De qué color son las paredes del salón?", "blanc*")]},
 {"id": "c6-trabajo", "cat": "relaciones", "turnos": [
   ("En mi equipo somos cuatro: Laura, Dani, Sonia y yo.", "ANY"), ("Laura es la jefa.", "ACK"), ("Dani y Sonia son programadores.", "ACK"), ("Sonia es la más joven.", "ANY"),
   ("¿Quién es la jefa?", "laura"), ("¿Qué es Dani?", "programador"), ("¿Sonia es programadora?", "^si"), ("¿Laura es programadora?", "ABST|^no|jefa"),
   ("Dani se lleva muy bien con Sonia.", "ANY"), ("Ayer Laura le dio un premio a Dani.", "ACK"), ("¿Quién recibió un premio?", "dani"), ("¿Quién le dio el premio?", "laura"),
   ("¿Qué le dio Laura a Dani?", "premio"), ("¿Cuándo?", "ayer")]},
]


def medir(verboso=False, salida="lab/res_ciego6.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "EXAMEN CIEGO 6")
