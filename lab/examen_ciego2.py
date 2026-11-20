"""EXAMEN CIEGO 2. Escrito ANTES de empezar la iteración 2.1 (Escuela conversacional), con vocabulario y formulaciones
nuevos. Se mide dos veces sin leer sus transcripciones: una con el estado previo (LCM 2.0) y otra al terminar.
Solo se miran las cifras agregadas; cuando se lean sus fallos para corregir, dejará de ser ciego."""
from lab.banco import correr, imprime

D = [
 {"id": "g-01", "cat": "persona", "turnos": [
   ("Hola, soy Valeria.", "valeria"), ("Vivo en Cuenca desde hace tres años.", "ACK"), ("Antes vivía en Gijón.", "ACK"), ("¿Dónde vivo ahora?", "cuenca"), ("¿Dónde vivía yo antes?", "gijon"),
   ("¿Cuál es mi nombre?", "valeria"), ("¿Vivo en Gijón?", "^no|ya no"), ("¿Desde cuándo vivo en Cuenca?", "tres años")]},
 {"id": "g-02", "cat": "persona", "turnos": [
   ("Mi nombre es Ignacio y soy electricista.", "ignacio"), ("Tengo 38 años.", "ACK"), ("Estoy soltero.", "ACK"), ("¿Cuál es mi oficio?", "electricista"), ("¿Estoy casado?", "^no|solter*"),
   ("¿Qué edad tengo?", "38"), ("¿Soy fontanero?", "!^si"), ("Dime quién soy.", "ignacio")]},
 {"id": "g-03", "cat": "persona", "turnos": [
   ("Tengo una hermana y dos hermanos.", "ACK"), ("Mi hermana se llama Rocío.", "ACK"), ("Rocío es enfermera y vive en Alicante.", "ACK"), ("¿Cuántos hermanos varones tengo?", "dos|2"),
   ("¿Cómo se llama mi hermana?", "rocio"), ("¿En qué trabaja mi hermana?", "enfermer*"), ("¿Dónde vive Rocío?", "alicante"), ("¿Tengo alguna hermana?", "^si|rocio"), ("¿Cómo se llaman mis hermanos?", "ABST")]},
 {"id": "g-04", "cat": "persona", "turnos": [
   ("Mi cumpleaños es el 3 de mayo.", "ACK"), ("Nací en Badajoz.", "ACK"), ("Mi número favorito es el siete.", "ACK"), ("¿Cuándo es mi cumpleaños?", "3 de mayo|tres de mayo"),
   ("¿Dónde nací?", "badajoz"), ("¿Cuál es mi número favorito?", "siete|7"), ("¿En qué ciudad nací?", "badajoz"), ("¿Cuál es mi color favorito?", "ABST")]},
 {"id": "g-05", "cat": "familia", "turnos": [
   ("Samuel es hijo de Aitana.", "ACK"), ("Aitana es hija de Bruno.", "ACK"), ("¿Quién es el abuelo de Samuel?", "bruno"), ("¿Quién es la madre de Samuel?", "aitana"),
   ("¿De quién es nieto Samuel?", "bruno"), ("¿Es Bruno el padre de Aitana?", "^si"), ("¿Tiene nietos Bruno?", "^si|samuel"), ("¿Quién es el padre de Samuel?", "ABST")]},
 {"id": "g-06", "cat": "familia", "turnos": [
   ("Celia y Darío están casados.", "ACK"), ("Tienen una hija llamada Fátima.", "ACK"), ("¿Quién es el marido de Celia?", "dario"), ("¿Quiénes son los padres de Fátima?", "celia;dario"),
   ("¿Quién es la madre de Fátima?", "celia"), ("¿Están casados Celia y Darío?", "^si"), ("¿Cómo se llama la hija de Darío?", "fatima"), ("¿Tiene Fátima hermanos?", "ABST")]},
 {"id": "g-07", "cat": "familia", "turnos": [
   ("Esteban es hermano de Gabriel.", "ACK"), ("Gabriel es el padre de Helena.", "ACK"), ("¿Qué es Esteban de Helena?", "tio"), ("¿Quién es el tío de Helena?", "esteban"),
   ("¿Es Helena sobrina de Esteban?", "^si"), ("¿Quién es la sobrina de Esteban?", "helena"), ("¿Son hermanos Esteban y Gabriel?", "^si"), ("¿Quién es la madre de Helena?", "ABST")]},
 {"id": "g-08", "cat": "familia", "turnos": [
   ("Mi abuela se llama Lidia.", "ACK"), ("Mi abuelo se llamaba Ramón.", "ACK"), ("Mi madre es Patricia.", "ACK"), ("¿Cómo se llama mi abuela?", "lidia"), ("¿Quién es mi madre?", "patricia"),
   ("¿Cómo se llamaba mi abuelo?", "ramon"), ("¿Quién es Lidia?", "abuela"), ("¿Cómo se llama mi padre?", "ABST")]},
 {"id": "g-09", "cat": "comparativos", "turnos": [
   ("Marcelo es más rápido que Nerea.", "ACK"), ("Nerea es más rápida que Joaquín.", "ACK"), ("¿Quién corre más, Marcelo o Joaquín?", "marcelo|ABST_OK"), ("¿Quién es el más rápido de los tres?", "marcelo"),
   ("¿Quién es el más lento?", "joaquin"), ("¿Es Joaquín más rápido que Marcelo?", "^no"), ("¿Es Nerea más lenta que Marcelo?", "^si"), ("¿Quién es más rápido que Nerea?", "marcelo")]},
 {"id": "g-10", "cat": "comparativos", "turnos": [
   ("Helena tiene 9 años.", "ACK"), ("Samuel tiene 14 años.", "ACK"), ("Fátima tiene 11 años.", "ACK"), ("¿Quién es el mayor de los tres?", "samuel"), ("¿Quién es la más pequeña?", "helena"),
   ("¿Es Fátima mayor que Helena?", "^si"), ("¿Cuántos años se llevan Helena y Samuel?", "cinco|5"), ("¿Quién es más joven, Fátima o Samuel?", "fatima"), ("¿Es Samuel menor que Fátima?", "^no")]},
 {"id": "g-11", "cat": "comparativos", "turnos": [
   ("Mi casa es más grande que la de Bruno.", "ACK"), ("La casa de Bruno es más grande que la de Celia.", "ACK"), ("¿Cuál es la casa más grande?", "tu casa|mi casa|la tuya"),
   ("¿Es la casa de Celia más pequeña que la mía?", "^si"), ("El tren es más rápido que el autobús.", "ACK"), ("¿Qué es más lento, el tren o el autobús?", "autobus"),
   ("¿Es el autobús más rápido que el tren?", "^no"), ("¿Es el tren más rápido que el avión?", "ABST")]},
 {"id": "g-12", "cat": "comparativos", "turnos": [
   ("Lidia es tan alta como Patricia.", "ACK"), ("Patricia es más alta que Rocío.", "ACK"), ("¿Es Lidia más alta que Rocío?", "^si|ABST_OK"), ("¿Quién es más baja, Rocío o Patricia?", "rocio"),
   ("Ramón pesa 80 kilos.", "ACK"), ("Gabriel pesa 72 kilos.", "ACK"), ("¿Cuánto pesa Ramón?", "80"), ("¿Quién pesa más, Ramón o Gabriel?", "ramon")]},
 {"id": "g-13", "cat": "atributos", "turnos": [
   ("La bufanda de Nerea es naranja.", "ACK"), ("Es de lana.", "ACK"), ("¿De qué color es la bufanda de Nerea?", "naranja"), ("¿De qué está hecha la bufanda?", "lana"),
   ("¿Es verde la bufanda de Nerea?", "^no;naranja"), ("Mi abrigo es largo y oscuro.", "ACK"), ("¿Cómo es mi abrigo?", "largo;oscuro"), ("¿Es corto mi abrigo?", "^no")]},
 {"id": "g-14", "cat": "atributos", "turnos": [
   ("El piso de Joaquín tiene tres habitaciones.", "ACK"), ("Está en el centro de Santander.", "ACK"), ("Es bastante caro.", "ACK"), ("¿Cuántas habitaciones tiene el piso de Joaquín?", "tres|3"),
   ("¿Dónde está el piso de Joaquín?", "santander|centro"), ("¿Es barato el piso de Joaquín?", "^no"), ("¿Quién tiene un piso?", "joaquin"), ("¿Tiene terraza el piso?", "ABST")]},
 {"id": "g-15", "cat": "lugar", "turnos": [
   ("Patricia trabajaba en Logroño.", "ACK"), ("Ahora trabaja en Ávila.", "ACK"), ("¿Dónde trabaja Patricia?", "avila;!logroño"), ("¿Dónde trabajaba Patricia antes?", "logroño"),
   ("¿Trabaja Patricia en Logroño?", "^no|ya no"), ("Patricia vive cerca del río.", "ACK"), ("¿Dónde vive Patricia?", "rio"), ("¿Quién trabaja en Ávila?", "patricia")]},
 {"id": "g-16", "cat": "lugar", "turnos": [
   ("Marcelo está de viaje en Girona.", "ACK"), ("Vuelve el domingo.", "ACK"), ("¿Dónde está Marcelo?", "girona"), ("¿Cuándo vuelve Marcelo?", "domingo"),
   ("¿Está Marcelo en casa?", "^no|ABST_OK"), ("Lidia ha ido al mercado.", "ACK"), ("¿Adónde ha ido Lidia?", "mercado"), ("¿Dónde está Lidia?", "mercado")]},
 {"id": "g-17", "cat": "acciones", "turnos": [
   ("Gabriel pintó la valla el sábado.", "ACK"), ("¿Quién pintó la valla?", "gabriel"), ("¿Qué pintó Gabriel?", "valla"), ("¿Qué día pintó Gabriel la valla?", "sabado"),
   ("Rocío cocinó lentejas anoche.", "ACK"), ("¿Qué cocinó Rocío?", "lentejas"), ("¿Cuándo cocinó Rocío lentejas?", "anoche|ayer"), ("¿Qué hizo Gabriel el sábado?", "pint*;valla"), ("¿Qué cocinó Gabriel?", "ABST")]},
 {"id": "g-18", "cat": "acciones", "turnos": [
   ("Aitana le regaló una pulsera a Nerea.", "ACK"), ("¿Qué le regaló Aitana a Nerea?", "pulsera"), ("¿Quién tiene la pulsera?", "nerea"), ("¿Quién le regaló la pulsera a Nerea?", "aitana"),
   ("Nerea perdió la pulsera.", "ACK"), ("¿Tiene Nerea la pulsera?", "^no|ya no"), ("¿Qué perdió Nerea?", "pulsera"), ("¿A quién le regaló Aitana la pulsera?", "nerea")]},
 {"id": "g-19", "cat": "gustos", "turnos": [
   ("A Bruno le encanta pescar.", "ACK"), ("A Celia le aburre el fútbol.", "ACK"), ("¿Qué le encanta a Bruno?", "pescar"), ("¿Le gusta el fútbol a Celia?", "^no|aburr*"),
   ("¿Qué le aburre a Celia?", "futbol"), ("¿A quién le encanta pescar?", "bruno"), ("¿Le gusta pescar a Celia?", "ABST"), ("A mí me gusta el senderismo.", "ACK"), ("¿Qué me gusta a mí?", "senderismo")]},
 {"id": "g-20", "cat": "gustos", "turnos": [
   ("Prefiero la playa a la montaña.", "ACK"), ("¿Qué prefiero, la playa o la montaña?", "playa"), ("Mi fruta favorita es la sandía.", "ACK"), ("¿Cuál es mi fruta favorita?", "sandia"),
   ("No soporto el ruido.", "ACK"), ("¿Qué no soporto?", "ruido"), ("Me dan miedo las tormentas.", "ACK"), ("¿Qué me da miedo?", "tormentas")]},
 {"id": "g-21", "cat": "mascotas", "turnos": [
   ("Helena tiene un loro que se llama Pipo.", "ACK"), ("Pipo es verde y habla mucho.", "ACK"), ("¿Cómo se llama el loro de Helena?", "pipo"), ("¿De qué color es Pipo?", "verde"),
   ("¿Quién es la dueña de Pipo?", "helena"), ("¿Habla Pipo?", "^si"), ("¿Qué animal tiene Helena?", "loro"), ("¿Tiene Helena un gato?", "ABST")]},
 {"id": "g-22", "cat": "cantidad", "turnos": [
   ("En mi clase hay veinte alumnos.", "ACK"), ("¿Cuántos alumnos hay en mi clase?", "veinte|20"), ("Tengo cuatro primos.", "ACK"), ("¿Cuántos primos tengo?", "cuatro|4"),
   ("Samuel tiene tres camisetas y dos pantalones.", "ACK"), ("¿Cuántas camisetas tiene Samuel?", "tres|3"), ("¿Cuántas prendas tiene Samuel?", "cinco|5"), ("¿Cuántos zapatos tiene Samuel?", "ABST")]},
 {"id": "g-23", "cat": "clases", "turnos": [
   ("Un colibrí es un pájaro.", "ACK"), ("¿Es un colibrí un animal?", "^si"), ("¿Tiene alas un colibrí?", "^si"), ("Chispa es un colibrí.", "ACK"), ("¿Tiene alas Chispa?", "^si"),
   ("¿Es Chispa un mamífero?", "^no"), ("¿Qué clase de animal es Chispa?", "colibri|pajaro"), ("¿Es Chispa un animal?", "^si"), ("¿Por qué?", "colibri;pajaro")]},
 {"id": "g-24", "cat": "clases", "turnos": [
   ("Una guitarra es un instrumento.", "ACK"), ("Un violín también es un instrumento.", "ACK"), ("Los instrumentos suenan.", "ACK"), ("¿Suena una guitarra?", "^si"),
   ("¿Es un violín una guitarra?", "^no"), ("¿Es un violín un instrumento?", "^si"), ("Marcelo toca el violín.", "ACK"), ("¿Qué instrumento toca Marcelo?", "violin"), ("¿Toca Marcelo la guitarra?", "ABST")]},
 {"id": "g-25", "cat": "negacion", "turnos": [
   ("Darío no sabe conducir.", "ACK"), ("¿Sabe conducir Darío?", "^no"), ("Darío no tiene carné.", "ACK"), ("¿Tiene carné Darío?", "^no"), ("Fátima nunca come dulces.", "ACK"),
   ("¿Come dulces Fátima?", "^no|nunca"), ("¿Quién no sabe conducir?", "dario"), ("¿Sabe conducir Fátima?", "ABST")]},
 {"id": "g-26", "cat": "correcciones", "turnos": [
   ("Esteban tiene 50 años.", "ACK"), ("Bueno, no, tiene 51.", "ACK"), ("¿Cuántos años tiene Esteban?", "51;!50"), ("Su coche es blanco.", "ACK"), ("Perdón, quería decir que su coche es gris.", "ACK"),
   ("¿De qué color es el coche de Esteban?", "gris;!blanco"), ("Esteban vive en Ávila.", "ACK"), ("Me equivoqué: vive en Girona.", "ACK"), ("¿Dónde vive Esteban?", "girona;!avila")]},
 {"id": "g-27", "cat": "estados", "turnos": [
   ("Joaquín está muy ocupado esta semana.", "ACK"), ("¿Cómo está Joaquín?", "ocupad*"), ("¿Está libre Joaquín?", "^no"), ("La tienda está cerrada los lunes.", "ACK"),
   ("¿Cuándo está cerrada la tienda?", "lunes"), ("El horno está encendido.", "ACK"), ("¿Está apagado el horno?", "^no"), ("He apagado el horno.", "ACK"), ("¿Está encendido el horno?", "^no|ya no|ABST_OK")]},
 {"id": "g-28", "cat": "tiempo", "turnos": [
   ("Tengo cita con el dentista el jueves a las cinco.", "ACK"), ("¿Cuándo tengo cita con el dentista?", "jueves"), ("¿A qué hora es la cita?", "cinco|5"), ("Rocío nació en 2001.", "ACK"),
   ("¿Cuántos años tiene Rocío?", "25|24"), ("Los martes voy a yoga.", "ACK"), ("¿Qué hago los martes?", "yoga"), ("¿Qué día voy a yoga?", "martes")]},
 {"id": "g-29", "cat": "social", "turnos": [
   ("Buenas noches.", "buenas noches|hola"), ("¿Qué tal estás hoy?", "bien"), ("Yo he tenido un día horrible.", "siento|vaya|lamento"), ("¿Tú tienes días malos?", "no"),
   ("¿Eres una inteligencia artificial?", "lcm|programa|modelo"), ("¿Qué música te gusta?", "no tengo"), ("Me has ayudado mucho.", "gracias|alegr*|placer"), ("Hasta mañana.", "hasta|adios|buenas noches")]},
 {"id": "g-30", "cat": "social", "turnos": [
   ("Estoy muy ilusionada con mi viaje.", "alegr*|que bien"), ("Me voy a Japón en abril.", "ACK"), ("¿Adónde me voy?", "japon"), ("¿Cuándo me voy a Japón?", "abril"),
   ("¿Tú has viajado alguna vez?", "no"), ("¿Cómo estoy?", "ilusionad*"), ("¿De verdad?", "!no he entendido;!no conozco"), ("Vale, gracias.", "de nada|vale|placer")]},
 {"id": "g-31", "cat": "desconocido", "turnos": [
   ("Lidia tiene un huerto.", "ACK"), ("¿Qué cultiva Lidia?", "ABST"), ("¿Dónde está el huerto de Lidia?", "ABST"), ("¿Cuántos años tiene Lidia?", "ABST"), ("¿Quién es el marido de Lidia?", "ABST"),
   ("¿Es grande el huerto de Lidia?", "ABST"), ("¿Tiene Lidia un perro?", "ABST"), ("¿Quién es Anselmo?", "ABST"), ("¿Tiene Lidia un huerto?", "^si")]},
 {"id": "g-32", "cat": "larga", "turnos": [
   ("Te cuento: me llamo Nerea y soy veterinaria.", "nerea"), ("Trabajo en una clínica de Gijón con mi socio Marcelo.", "ACK"), ("Marcelo lleva diez años en la clínica.", "ACK"),
   ("Yo empecé hace dos años.", "ACK"), ("¿A qué me dedico?", "veterinari*"), ("¿Con quién trabajo?", "marcelo"), ("¿Quién es Marcelo?", "socio"), ("¿Dónde está la clínica?", "gijon"),
   ("¿Cuánto tiempo lleva Marcelo en la clínica?", "diez|10"), ("¿Cuándo empecé yo?", "dos años")]},
 {"id": "g-33", "cat": "larga", "turnos": [
   ("El sábado celebramos el cumpleaños de mi madre.", "ACK"), ("Cumplió 70 años.", "ACK"), ("Vinieron mis tíos y mis primos.", "ACK"), ("Le regalamos un reloj.", "ACK"),
   ("¿Qué celebramos el sábado?", "cumpleaños"), ("¿Cuántos años cumplió mi madre?", "70"), ("¿Qué le regalamos a mi madre?", "reloj"), ("¿Quiénes vinieron?", "tios;primos"), ("¿Cuándo fue el cumpleaños?", "sabado")]},
 {"id": "g-34", "cat": "sin_tildes", "turnos": [
   ("mi perro se llama rocky", "ACK"), ("como se llama mi perro?", "rocky"), ("rocky tiene 4 años", "ACK"), ("cuantos años tiene rocky?", "4|cuatro"), ("bruno es mi vecino", "ACK"),
   ("quien es bruno?", "vecino"), ("bruno tiene una moto roja", "ACK"), ("de que color es la moto de bruno?", "roj*"), ("donde vive bruno?", "ABST")]},
 {"id": "g-35", "cat": "modal", "turnos": [
   ("Aitana quiere ser arquitecta.", "ACK"), ("¿Qué quiere ser Aitana?", "arquitect*"), ("Tengo que comprar leche.", "ACK"), ("¿Qué tengo que comprar?", "leche"),
   ("Samuel no puede salir hoy.", "ACK"), ("¿Puede salir Samuel hoy?", "^no"), ("Helena debería estudiar más.", "!no he entendido"), ("¿Quién quiere ser arquitecta?", "aitana")]},
 {"id": "g-36", "cat": "multimodal", "turnos": [
   ({"texto": "¿Qué color ves aquí?", "imagen": "VERDE", "nombre": "a.png"}, "verde"), ("Mi bici es de ese color.", "!no he entendido"), ("¿De qué color es mi bici?", "verde"),
   ({"texto": "", "imagen": "NEGRO", "nombre": "b.png"}, "negro"), ("¿De qué color es?", "negro"), ("El coche de Bruno es de este color.", "!no he entendido"), ("¿De qué color es el coche de Bruno?", "negro"),
   ("¿De qué color es mi bici?", "verde;!negr*")]},
]


def _prepara():
    from lab.generador import png, RGB
    for d in D:
        d["turnos"] = [((dict(t, imagen=png(RGB[t["imagen"].lower()])) if isinstance(t, dict) and isinstance(t.get("imagen"), str) else t), c) for t, c in d["turnos"]]
    return D


def medir(verboso=False, salida="lab/res_ciego2.json"):
    import lab.banco as B
    orig = B.veredicto

    def veredicto(crit, resp, err=None):
        if isinstance(crit, str) and "ABST_OK" in crit:
            if isinstance(resp, str) and B.abstiene(resp):
                return "OK"
            crit = "|".join(a for a in crit.split("|") if a != "ABST_OK")
        return orig(crit, resp, err)
    B.veredicto = veredicto
    try:
        return correr(_prepara(), verboso=verboso, salida=salida)
    finally:
        B.veredicto = orig


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "EXAMEN CIEGO 2")
