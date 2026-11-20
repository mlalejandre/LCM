"""Tanda 6 (desarrollo): persona, cantidades, comparaciones, familia y charla, con formulaciones nuevas."""
from lab.banco import correr, imprime
D = [
 {"id": "t6-persona1", "cat": "persona", "turnos": [
   ("Soy Martina y trabajo de camarera en un bar.", "martina"), ("Llevo cinco años en Zamora.", "ACK"), ("Antes vivía en Lugo con mis padres.", "ACK"), ("¿Cuál es mi trabajo?", "camarer*"),
   ("¿Dónde trabajo?", "bar"), ("¿Dónde vivía antes?", "lugo"), ("¿Con quién vivía?", "padres"), ("¿Cuánto tiempo llevo en Zamora?", "cinco años"), ("¿Vivo en Lugo ahora?", "!^si")]},
 {"id": "t6-persona2", "cat": "persona", "turnos": [
   ("Estoy casada y tengo un hijo.", "ACK"), ("Mi hijo se llama Aitor y tiene seis años.", "ACK"), ("Mi marido es profesor.", "ACK"), ("¿Estoy soltera?", "^no|casad*"), ("¿Tengo hijos?", "^si|aitor"),
   ("¿Cuántos años tiene mi hijo?", "seis|6"), ("¿A qué se dedica mi marido?", "profesor"), ("¿Cómo se llama mi marido?", "ABST"), ("Dime qué sabes de mi hijo.", "aitor;seis|6")]},
 {"id": "t6-persona3", "cat": "persona", "turnos": [
   ("Mi cumpleaños es el 14 de marzo.", "ACK"), ("Mi deporte favorito es el baloncesto.", "ACK"), ("Nací en Teruel en 1988.", "ACK"), ("¿Cuándo es mi cumpleaños?", "14 de marzo"),
   ("¿Cuál es mi deporte favorito?", "baloncesto"), ("¿En qué año nací?", "1988"), ("¿Dónde nací?", "teruel"), ("¿Cuántos años tengo?", "38|37"), ("¿Cuál es mi comida favorita?", "ABST")]},
 {"id": "t6-cantidad", "cat": "cantidad", "turnos": [
   ("En mi calle hay tres bares.", "ACK"), ("¿Cuántos bares hay en mi calle?", "tres|3"), ("Tengo dos hermanas y un hermano.", "ACK"), ("¿Cuántas hermanas tengo?", "dos|2"),
   ("¿Cuántos hermanos tengo en total?", "tres|3"), ("Mi abuela tiene cinco nietos.", "ACK"), ("¿Cuántos nietos tiene mi abuela?", "cinco|5"), ("En el salón hay un sofá y dos sillones.", "ACK"),
   ("¿Qué hay en el salón?", "sofa;sillones"), ("¿Cuántos sillones hay en el salón?", "dos|2")]},
 {"id": "t6-comp1", "cat": "comparativos", "turnos": [
   ("Mi coche es más viejo que el de Pilar.", "ACK"), ("¿Qué coche es más nuevo, el mío o el de Pilar?", "pilar"), ("¿Es mi coche más viejo que el de Pilar?", "^si"),
   ("El río Tajo es más largo que el Ebro.", "ACK"), ("¿Qué río es más largo, el Tajo o el Ebro?", "tajo"), ("¿Cuál es más corto, el Ebro o el Tajo?", "ebro"), ("¿Es el Ebro más largo que el Tajo?", "^no")]},
 {"id": "t6-comp2", "cat": "comparativos", "turnos": [
   ("Aitor mide 120 centímetros.", "ACK"), ("Vega mide 135 centímetros.", "ACK"), ("¿Cuánto mide Vega?", "135"), ("¿Quién mide más, Aitor o Vega?", "vega"), ("¿Quién es más alto, Aitor o Vega?", "vega"),
   ("Vega tiene 10 años y Aitor tiene 6.", "ACK"), ("¿Cuántos años se llevan Vega y Aitor?", "cuatro|4"), ("¿Quién es la mayor?", "vega"), ("¿Quién es el pequeño?", "aitor")]},
 {"id": "t6-familia", "cat": "familia", "turnos": [
   ("Pilar es hija de Rafael.", "ACK"), ("Rafael es hijo de Amparo.", "ACK"), ("¿De quién es hija Pilar?", "rafael"), ("¿Quién es la abuela de Pilar?", "amparo"), ("¿Qué es Amparo de Pilar?", "abuela"),
   ("¿De quién es nieta Pilar?", "amparo"), ("Rafael y Susana están casados.", "ACK"), ("¿Quién es la mujer de Rafael?", "susana"), ("¿Quiénes son los padres de Pilar?", "rafael"),
   ("Tienen otro hijo llamado Ismael.", "ACK"), ("¿Quién es el hermano de Pilar?", "ismael")]},
 {"id": "t6-social", "cat": "social", "turnos": [
   ("Buenas tardes.", "buenas tardes|hola"), ("¿Qué tal estás hoy?", "bien"), ("He tenido un día muy malo.", "siento|vaya|lamento"), ("¿Tú tienes días malos?", "no"),
   ("¿Qué deporte te gusta?", "no tengo"), ("¿Has estado alguna vez en París?", "no"), ("Me has sido de gran ayuda.", "gracias|alegr*|placer"), ("¿En serio?", "!no he entendido;!no conozco"),
   ("Vale, gracias.", "de nada|vale|placer"), ("Hasta otro día.", "hasta|adios")]},
 {"id": "t6-larga", "cat": "larga", "turnos": [
   ("Te cuento: soy Rodrigo y soy fotógrafo.", "rodrigo"), ("Tengo un estudio en Vitoria con mi socia Elvira.", "ACK"), ("Elvira lleva ocho años en el estudio.", "ACK"), ("Yo empecé hace tres años.", "ACK"),
   ("¿Con quién tengo el estudio?", "elvira"), ("¿Quién es Elvira?", "socia"), ("¿Dónde está el estudio?", "vitoria"), ("¿Cuánto tiempo lleva Elvira en el estudio?", "ocho"),
   ("¿Cuándo empecé?", "tres años"), ("¿A qué me dedico?", "fotograf*")]},
 {"id": "t6-eventos", "cat": "larga", "turnos": [
   ("El domingo celebramos la boda de mi hermano.", "ACK"), ("Vinieron mis abuelos y mis tíos.", "ACK"), ("Le regalamos un viaje.", "ACK"), ("¿Qué celebramos el domingo?", "boda"),
   ("¿Quiénes vinieron?", "abuelos;tios"), ("¿Qué le regalamos a mi hermano?", "viaje"), ("¿Cuándo fue la boda?", "domingo"), ("Mi hermano cumplió 30 años en mayo.", "ACK"),
   ("¿Cuántos años cumplió mi hermano?", "30"), ("¿Cuándo cumplió años mi hermano?", "mayo")]},
]
if __name__ == "__main__":
    f, r = correr(D, verboso=True, salida="lab/res_tanda06.json"); imprime(r, "TANDA 6")
