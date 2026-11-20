"""Tanda 5 (desarrollo): es el antiguo examen final ciego de LCM 2.0. Se midió una vez a ciegas (84,9 %) y desde
entonces se usa para corregir, así que ya no es ciego."""
from lab.banco import correr, imprime

D = [
 {"id": "f-01", "cat": "persona", "turnos": [
   ("Buenas, me llamo Noelia.", "noelia"), ("Soy de Salamanca pero vivo en Lugo.", "ACK"), ("Trabajo como fisioterapeuta.", "ACK"), ("¿Me puedes decir dónde vivo?", "lugo"),
   ("¿De dónde soy?", "salamanca"), ("¿En qué trabajo?", "fisioterapeuta"), ("¿Recuerdas cómo me llamo?", "noelia"), ("¿Vivo en Salamanca?", "^no;lugo")]},
 {"id": "f-02", "cat": "persona", "turnos": [
   ("Tengo 45 años.", "ACK"), ("Mi marido tiene 47.", "ACK"), ("Se llama Gonzalo.", "ACK"), ("¿Qué edad tiene mi marido?", "47"), ("¿Cómo se llama?", "gonzalo"),
   ("¿Quién es mayor, Gonzalo o yo?", "gonzalo"), ("¿Cuántos años nos llevamos?", "dos|2"), ("¿Tengo marido?", "^si")]},
 {"id": "f-03", "cat": "familia", "turnos": [
   ("Beatriz es la madre de Tomás.", "ACK"), ("Tomás es el padre de Adriana y de Emilio.", "ACK"), ("¿Quién es la abuela de Emilio?", "beatriz"), ("¿Adriana y Emilio son hermanos?", "^si"),
   ("¿Cuántos nietos tiene Beatriz?", "dos|2"), ("¿Quiénes son los hijos de Tomás?", "adriana;emilio"), ("¿Es Beatriz la abuela de Adriana?", "^si"), ("¿Quién es el abuelo de Adriana?", "ABST"),
   ("¿Tiene hijos Adriana?", "ABST")]},
 {"id": "f-04", "cat": "familia", "turnos": [
   ("Lorena y Fabián son primos.", "ACK"), ("Olga es la madre de Lorena.", "ACK"), ("¿Quién es el primo de Lorena?", "fabian"), ("¿Es Fabián primo de Lorena?", "^si"),
   ("¿Quién es la tía de Fabián?", "olga|ABST_OK"), ("¿Cómo se llama la madre de Lorena?", "olga"), ("¿Quién es el hermano de Lorena?", "ABST"), ("Mateo es el marido de Olga.", "ACK"),
   ("¿Quién es la mujer de Mateo?", "olga"), ("¿Con quién está casada Olga?", "mateo")]},
 {"id": "f-05", "cat": "mascotas", "turnos": [
   ("Emilio tiene una tortuga.", "ACK"), ("La tortuga se llama Manuelita.", "ACK"), ("Es muy lenta.", "ACK"), ("¿Qué mascota tiene Emilio?", "tortuga"), ("¿Cuál es el nombre de la tortuga?", "manuelita"),
   ("¿Cómo es Manuelita?", "lent*"), ("¿Es rápida Manuelita?", "^no"), ("¿De quién es Manuelita?", "emilio"), ("¿Tiene Emilio un conejo?", "ABST")]},
 {"id": "f-06", "cat": "mascotas", "turnos": [
   ("Tengo dos conejos y un hámster.", "ACK"), ("¿Cuántos conejos tengo?", "dos|2"), ("¿Cuántos animales tengo en total?", "tres|3"), ("Un conejo es un animal.", "ACK"), ("Un hámster es un animal.", "ACK"),
   ("¿Cuántos animales tengo?", "tres|3"), ("¿Tengo algún hámster?", "^si"), ("¿Qué animales tengo?", "conejos;hamster"), ("¿Tengo gatos?", "ABST")]},
 {"id": "f-07", "cat": "objetos", "turnos": [
   ("La mochila de Olga es morada.", "ACK"), ("¿Qué color tiene la mochila de Olga?", "morad*"), ("¿Es gris la mochila de Olga?", "^no;morad*"), ("Mi paraguas es gris.", "ACK"),
   ("¿De qué color es mi paraguas?", "gris"), ("¿Y la mochila de Olga?", "morad*"), ("¿Quién tiene una mochila?", "olga"), ("¿De qué color es la mochila de Mateo?", "ABST")]},
 {"id": "f-08", "cat": "objetos", "turnos": [
   ("He dejado la tablet encima del sofá.", "ACK"), ("¿Dónde está la tablet?", "sofa"), ("Las gafas están en el cajón.", "ACK"), ("¿Dónde he dejado la tablet?", "sofa"), ("¿Dónde están las gafas?", "cajon"),
   ("¿Qué hay en el cajón?", "gafas"), ("Ahora las gafas están en la mesilla.", "ACK"), ("¿Dónde están las gafas?", "mesilla;!cajon"), ("¿Dónde están las llaves?", "ABST")]},
 {"id": "f-09", "cat": "lugar", "turnos": [
   ("Fabián residía en Almería.", "ACK"), ("Hace un mes se mudó a Pamplona.", "ACK"), ("¿Dónde vive Fabián actualmente?", "pamplona"), ("¿Dónde vivía antes Fabián?", "almeria"),
   ("¿Sigue viviendo Fabián en Almería?", "^no|ya no"), ("¿Fabián vive en Pamplona?", "^si"), ("¿Cuándo se mudó Fabián?", "mes"), ("¿Dónde trabaja?", "ABST")]},
 {"id": "f-10", "cat": "lugar", "turnos": [
   ("Adriana estudia en la universidad de Tarragona.", "ACK"), ("¿Dónde estudia Adriana?", "tarragona|universidad"), ("¿Qué hace Adriana?", "estudia"), ("Adriana está en Huelva esta semana.", "ACK"),
   ("¿Dónde se encuentra Adriana?", "huelva"), ("¿Está Adriana en Tarragona?", "^no;huelva"), ("¿Quién está en Huelva?", "adriana"), ("¿Dónde está Tomás?", "ABST")]},
 {"id": "f-11", "cat": "acciones", "turnos": [
   ("Mateo alquiló un camión el martes.", "ACK"), ("¿Qué alquiló Mateo?", "camion"), ("¿Qué día alquiló Mateo el camión?", "martes"), ("¿Quién alquiló un camión?", "mateo"),
   ("Lorena perdió su paraguas ayer.", "ACK"), ("¿Qué perdió Lorena?", "paraguas"), ("¿Tiene Lorena su paraguas?", "^no|ya no"), ("¿Qué hizo Lorena ayer?", "perdi*;paraguas"), ("¿Qué hizo Mateo el martes?", "alquil*;camion")]},
 {"id": "f-12", "cat": "acciones", "turnos": [
   ("Olga le envió una carta a Beatriz.", "ACK"), ("¿Quién tiene la carta?", "beatriz"), ("¿A quién le envió Olga la carta?", "beatriz"), ("¿Qué le envió Olga a Beatriz?", "carta"),
   ("Beatriz le prestó un libro a Tomás.", "ACK"), ("¿Quién tiene el libro ahora?", "tomas"), ("¿Tiene Beatriz el libro?", "^no|ya no"), ("¿Qué tiene Tomás?", "libro"), ("¿Qué tiene Olga?", "ABST")]},
 {"id": "f-13", "cat": "gustos", "turnos": [
   ("A Gonzalo le apasiona el ajedrez.", "ACK"), ("A Noelia le gusta la escalada pero no le gusta la jardinería.", "ACK"), ("¿Qué le apasiona a Gonzalo?", "ajedrez"), ("¿Le gusta a Noelia la jardinería?", "^no"),
   ("¿A Noelia le gusta la escalada?", "^si"), ("¿A quién le gusta la escalada?", "noelia"), ("¿Le gusta el ajedrez a Noelia?", "ABST"), ("¿Cuáles son las aficiones de Gonzalo?", "ajedrez")]},
 {"id": "f-14", "cat": "gustos", "turnos": [
   ("Me encanta la tortilla.", "ACK"), ("Odio las lentejas.", "ACK"), ("No me gusta el yogur.", "ACK"), ("¿Qué comida me encanta?", "tortilla"), ("¿Me gustan las lentejas?", "^no|odi*"),
   ("¿Qué odio?", "lentejas"), ("¿Me gusta el yogur?", "^no"), ("¿Me gusta la ensalada?", "ABST"), ("¿Qué me gusta?", "tortilla;!lentejas me gust")]},
 {"id": "f-15", "cat": "comparativos", "turnos": [
   ("El sofá es más ancho que la mesa.", "ACK"), ("La mesa es más ancha que la silla.", "ACK"), ("¿Qué es más ancho, el sofá o la silla?", "sofa"), ("¿Es la silla más ancha que el sofá?", "^no"),
   ("¿Es el sofá más ancho que la silla?", "^si"), ("¿Cuál es el más ancho?", "sofa"), ("¿Es la mesa más estrecha que el sofá?", "^si"), ("¿Es la mesa más ancha que la lámpara?", "ABST")]},
 {"id": "f-16", "cat": "comparativos", "turnos": [
   ("Emilio tiene 12 años y Adriana tiene 15.", "ACK"), ("¿Quién es el mayor de los dos?", "adriana"), ("¿Quién es menor, Emilio o Adriana?", "emilio"), ("¿Cuántos años tiene Emilio?", "12"),
   ("¿Es Emilio mayor que Adriana?", "^no"), ("¿Cuántos años le saca Adriana a Emilio?", "tres|3"), ("Tomás es más alto que Emilio.", "ACK"), ("¿Quién es más bajo, Tomás o Emilio?", "emilio")]},
 {"id": "f-17", "cat": "clases", "turnos": [
   ("Kira es una tortuga.", "ACK"), ("Las tortugas son reptiles.", "ACK"), ("Los reptiles son animales.", "ACK"), ("¿Kira es un reptil?", "^si"), ("¿Es Kira un animal?", "^si"),
   ("¿Por qué?", "tortuga;reptil*"), ("Las tortugas viven muchos años.", "ACK"), ("¿Vive Kira muchos años?", "^si"), ("¿Es Kira un mamífero?", "^no|ABST_OK"), ("¿Es un reptil una tortuga?", "!^si")]},
 {"id": "f-18", "cat": "clases", "turnos": [
   ("Un yate es un barco.", "ACK"), ("Un barco es un vehículo.", "ACK"), ("¿Es un yate un vehículo?", "^si"), ("El Albatros es un yate.", "!no he entendido"), ("¿Qué es el Albatros?", "yate"),
   ("Los barcos flotan.", "ACK"), ("¿Flota un yate?", "^si"), ("¿Es un coche un barco?", "^no"), ("¿Es un yate un coche?", "^no")]},
 {"id": "f-19", "cat": "negacion", "turnos": [
   ("Tomás no fuma.", "ACK"), ("¿Fuma Tomás?", "^no"), ("Tomás no tiene coche.", "ACK"), ("¿Tiene coche Tomás?", "^no"), ("Tomás tampoco bebe alcohol.", "ACK"), ("¿Bebe alcohol Tomás?", "^no"),
   ("¿Qué no hace Tomás?", "fum*"), ("¿Bebe Tomás café?", "ABST")]},
 {"id": "f-20", "cat": "correcciones", "turnos": [
   ("Lorena vive en Huelva.", "ACK"), ("Perdona, me he confundido: Lorena vive en Lugo.", "ACK"), ("¿Dónde vive Lorena?", "lugo;!huelva"), ("Mi tablet es negra.", "ACK"), ("No, es blanca.", "ACK"),
   ("¿De qué color es mi tablet?", "blanc*;!negr*"), ("Olga tiene tres hijos.", "ACK"), ("Rectifico: Olga tiene cuatro hijos.", "ACK"), ("¿Cuántos hijos tiene Olga?", "cuatro|4;!tres")]},
 {"id": "f-21", "cat": "estados", "turnos": [
   ("Gonzalo está resfriado.", "ACK"), ("¿Cómo se encuentra Gonzalo?", "resfriad*"), ("¿Está enfermo Gonzalo?", "ABST|resfriad*"), ("La ventana está abierta.", "ACK"), ("¿Está cerrada la ventana?", "^no"),
   ("Ya está cerrada.", "!no he entendido"), ("¿Cómo está la ventana?", "cerrad*"), ("Beatriz está de vacaciones.", "ACK"), ("¿Dónde está Beatriz?", "ABST|vacaciones")]},
 {"id": "f-22", "cat": "tiempo", "turnos": [
   ("Mateo va a clase de inglés los miércoles.", "ACK"), ("¿Qué hace Mateo los miércoles?", "ingles"), ("¿Cuándo va Mateo a clase de inglés?", "miercoles"), ("Noelia nació en 1990.", "ACK"),
   ("¿Qué edad tiene Noelia?", "36|35"), ("¿En qué año nació Noelia?", "1990"), ("Mañana Noelia tiene una reunión.", "ACK"), ("¿Qué tiene Noelia mañana?", "reunion"), ("¿Cuándo tiene Noelia la reunión?", "mañana|jueves")]},
 {"id": "f-23", "cat": "social", "turnos": [
   ("¡Hola! ¿Qué tal todo?", "bien|hola"), ("Yo estoy agotada.", "siento|vaya|descans*"), ("¿Tú te cansas?", "no"), ("¿Eres una máquina?", "lcm|programa|modelo"), ("¿Qué opinas de la política?", "no tengo"),
   ("¿Te caigo bien?", "!no conozco;!no he entendido"), ("Eres muy amable.", "gracias"), ("Bueno, me tengo que ir.", "!no he entendido;!no conozco"), ("Hasta pronto.", "hasta|adios")]},
 {"id": "f-24", "cat": "social", "turnos": [
   ("Me siento muy feliz hoy.", "alegr*|que bien"), ("¿Cómo estoy?", "feliz"), ("¿Por qué lo sabes?", "dijiste|me siento"), ("¿Sabes cocinar?", "!no conozco"), ("¿Cuál es tu comida favorita?", "no tengo"),
   ("¿Qué día fue ayer?", "martes"), ("¿Qué mes va antes de agosto?", "julio"), ("Jajaja", "!no he entendido"), ("Gracias por la charla.", "de nada|placer|gusto")]},
 {"id": "f-25", "cat": "desconocido", "turnos": [
   ("Adriana trabaja en una farmacia.", "ACK"), ("¿Dónde vive Adriana?", "ABST"), ("¿Cuántos años tiene Adriana?", "ABST"), ("¿Quién es el jefe de Adriana?", "ABST"), ("¿Qué le gusta a Adriana?", "ABST"),
   ("¿Quién es Bartolomé?", "ABST"), ("¿De qué color es el coche de Adriana?", "ABST"), ("¿Tiene Adriana hermanos?", "ABST"), ("¿Dónde trabaja Adriana?", "farmacia"), ("¿Trabaja Adriana en un banco?", "^no;farmacia")]},
 {"id": "f-26", "cat": "larga", "turnos": [
   ("Me llamo Emilio y tengo una hermana pequeña.", "emilio"), ("Mi hermana se llama Lorena y tiene diez años.", "ACK"), ("A ella le encanta dibujar.", "ACK"), ("Vivimos en Pamplona con nuestros padres.", "ACK"),
   ("Mi padre es carpintero.", "ACK"), ("¿Cuántos años tiene mi hermana?", "diez|10"), ("¿Qué le encanta a Lorena?", "dibujar"), ("¿Dónde vivimos?", "pamplona"), ("¿A qué se dedica mi padre?", "carpinter*"),
   ("¿Cómo se llama mi hermana?", "lorena"), ("¿Tengo hermanos?", "^si|lorena"), ("¿Quién es carpintero?", "padre")]},
 {"id": "f-27", "cat": "larga", "turnos": [
   ("Ayer fui al cine con Fabián.", "ACK"), ("Vimos una película de miedo.", "ACK"), ("A Fabián no le gustó.", "ACK"), ("¿Con quién fui al cine?", "fabian"), ("¿Qué vimos?", "pelicula"),
   ("¿Le gustó la película a Fabián?", "^no"), ("¿Cuándo fui al cine?", "ayer"), ("¿Adónde fui ayer?", "cine"), ("Después cenamos en un restaurante italiano.", "ACK"), ("¿Dónde cenamos?", "restaurante")]},
 {"id": "f-28", "cat": "sin_tildes", "turnos": [
   ("olga vive en almeria", "ACK"), ("donde vive olga?", "almeria"), ("olga tiene una hija", "ACK"), ("la hija de olga se llama irene", "ACK"), ("como se llama la hija de olga?", "irene"),
   ("irene tiene 8 años", "ACK"), ("cuantos años tiene irene?", "8|ocho"), ("quien es la madre de irene?", "olga"), ("donde vive irene?", "ABST")]},
 {"id": "f-29", "cat": "modal", "turnos": [
   ("Gonzalo quiere aprender japonés.", "ACK"), ("¿Qué quiere aprender Gonzalo?", "japones"), ("Beatriz necesita comprar pan.", "ACK"), ("¿Qué necesita Beatriz?", "pan"),
   ("Tomás sabe tocar la guitarra.", "ACK"), ("¿Sabe Tomás tocar la guitarra?", "^si"), ("¿Quién sabe tocar la guitarra?", "tomas"), ("¿Sabe Gonzalo japonés?", "ABST|quiere aprender")]},
 {"id": "f-30", "cat": "multimodal", "turnos": [
   ({"texto": "¿Qué color es?", "imagen": "ROJO", "nombre": "x.png"}, "rojo"), ("¿De qué color es?", "rojo"), ({"texto": "", "imagen": "AZUL", "nombre": "y.png"}, "azul"),
   ("¿De qué color es?", "azul;!rojo"), ({"texto": "¿Es de color verde?", "imagen": "AZUL", "nombre": "z.png"}, "!^si"), ("Mi coche es de ese color.", "!no he entendido"), ("¿De qué color es mi coche?", "azul")]},
]


def _prepara():
    from lab.generador import png, RGB
    for d in D:
        nuevos = []
        for t, c in d["turnos"]:
            if isinstance(t, dict) and isinstance(t.get("imagen"), str):
                t = dict(t); t["imagen"] = png(RGB[t["imagen"].lower()])
            # «x|ABST_OK»: vale el dato o una abstención honesta
            nuevos.append((t, c))
        d["turnos"] = nuevos
    return D


if __name__ == "__main__":
    import lab.banco as B
    orig = B.veredicto

    def veredicto(crit, resp, err=None):
        if isinstance(crit, str) and "ABST" in crit and crit not in ("ABST",):
            alts = [a for a in crit.split("|")]
            if any(a in ("ABST", "ABST_OK") for a in alts) and isinstance(resp, str) and B.abstiene(resp):
                return "OK"
            crit = "|".join(a for a in alts if a not in ("ABST", "ABST_OK"))
        return orig(crit, resp, err)
    B.veredicto = veredicto
    f, r = correr(_prepara(), verboso="-v" in __import__("sys").argv, salida="lab/res_tanda05.json")
    imprime(r, "TANDA 5")
