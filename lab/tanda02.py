"""Tanda 2: conversación natural más libre (criterios escritos antes de ejecutar)."""
from lab.banco import correr, imprime
D = [
 {"id": "t2-presentacion", "cat": "presentacion", "turnos": [
   ("Hola, soy Marcos y vivo en Madrid.", "marcos"), ("Tengo 40 años y trabajo en un banco.", "ACK"), ("Estoy casado con Laura.", "ACK"), ("Tenemos dos hijos.", "ACK"),
   ("Mi hijo mayor se llama Dani.", "ACK"), ("¿Qué sabes de mí?", "marcos;madrid;banco"), ("¿Cómo se llama mi mujer?", "laura"), ("¿Cuántos hijos tengo?", "dos|2"),
   ("¿Con quién estoy casado?", "laura"), ("¿Dónde trabajo?", "banco"), ("¿Cómo se llama mi hijo mayor?", "dani")]},
 {"id": "t2-planes", "cat": "planes", "turnos": [
   ("Mañana voy a ir al dentista.", "ACK"), ("¿Qué voy a hacer mañana?", "dentista"), ("Quiero comprar un coche nuevo.", "ACK"), ("¿Qué quiero comprar?", "coche"),
   ("El sábado voy a cenar con Ana.", "ACK"), ("¿Con quién voy a cenar el sábado?", "ana"), ("¿Cuándo voy a cenar con Ana?", "sabado"), ("¿Tengo un coche nuevo?", "!^si")]},
 {"id": "t2-mascota", "cat": "mascota", "turnos": [
   ("Mi gata Luna tiene tres años.", "ACK"), ("Es negra.", "ACK"), ("Le gusta dormir en el sofá.", "ACK"), ("¿Cuántos años tiene Luna?", "tres|3"),
   ("¿De qué color es mi gata?", "negr*"), ("¿Qué le gusta a Luna?", "dormir"), ("¿Cómo se llama mi gata?", "luna"), ("¿Es Luna blanca?", "^no;negr*")]},
 {"id": "t2-trabajo", "cat": "trabajo", "turnos": [
   ("Mi jefe se llama Roberto.", "ACK"), ("Roberto es muy exigente.", "ACK"), ("Trabajo de lunes a viernes.", "ACK"), ("¿Quién es mi jefe?", "roberto"),
   ("¿Cómo es Roberto?", "exigente"), ("¿Cómo es mi jefe?", "exigente"), ("¿Cuándo trabajo?", "lunes;viernes"), ("¿Es Roberto mi jefe?", "^si")]},
 {"id": "t2-objetos", "cat": "objetos", "turnos": [
   ("Las llaves están en la mesa.", "ACK"), ("¿Dónde están las llaves?", "mesa"), ("He puesto el libro en la estantería.", "ACK"), ("¿Dónde está el libro?", "estanteria"),
   ("El gato está debajo de la cama.", "ACK"), ("¿Dónde está el gato?", "debajo;cama"), ("¿Qué hay en la mesa?", "llaves"), ("¿Dónde está el móvil?", "ABST")]},
 {"id": "t2-causas", "cat": "causas", "turnos": [
   ("Ana está contenta porque ha aprobado el examen.", "ACK"), ("¿Por qué está contenta Ana?", "aprob*;examen"), ("No fui a trabajar porque estaba enfermo.", "ACK"),
   ("¿Por qué no fui a trabajar?", "enferm*"), ("¿Está Ana triste?", "^no;content*"), ("¿Cómo está Ana?", "content*"), ("¿Por qué está triste Luis?", "ABST")]},
 {"id": "t2-hermanos", "cat": "hermanos", "turnos": [
   ("Tengo dos hermanos.", "ACK"), ("Se llaman Pedro y Juan.", "ACK"), ("Pedro es mayor que Juan.", "ACK"), ("¿Cómo se llaman mis hermanos?", "pedro;juan"),
   ("¿Quién es mayor, Pedro o Juan?", "^pedro|pedro es"), ("¿Cuántos hermanos tengo?", "dos|2"), ("Juan vive en Londres.", "ACK"), ("¿Dónde vive mi hermano Juan?", "londres"),
   ("¿Es Pedro mi hermano?", "^si"), ("¿Dónde vive Pedro?", "ABST")]},
 {"id": "t2-preferencias", "cat": "preferencias", "turnos": [
   ("Prefiero el té al café.", "ACK"), ("¿Qué prefiero?", "te"), ("Mi comida favorita es la paella.", "ACK"), ("¿Cuál es mi comida favorita?", "paella"),
   ("Odio madrugar.", "ACK"), ("¿Qué odio?", "madrugar"), ("No me gustan las arañas.", "ACK"), ("¿Me gustan las arañas?", "^no"), ("¿Cuál es mi color favorito?", "ABST")]},
 {"id": "t2-estados", "cat": "estados", "turnos": [
   ("La puerta está abierta.", "ACK"), ("¿Está la puerta cerrada?", "^no;abiert*"), ("Ahora la puerta está cerrada.", "ACK"), ("¿Está la puerta abierta?", "^no|^ya no;cerrad*"),
   ("Luis estaba enfermo ayer.", "ACK"), ("Hoy Luis está bien.", "ACK"), ("¿Cómo está Luis?", "bien;!esta enfermo"), ("¿Cómo estaba Luis ayer?", "enfermo")]},
 {"id": "t2-charla", "cat": "charla", "turnos": [
   ("Hoy he tenido mucho trabajo.", "ACK"), ("¿Qué he tenido hoy?", "trabajo"), ("Estoy cansado.", "siento|vaya|descans*;!no he entendido"), ("Me voy a dormir.", "!no he entendido;!no conozco"),
   ("Buenas noches.", "buenas noches|hasta|descansa"), ("¿Sabes quién soy?", "!no he entendido;!no conozco"), ("¿Te acuerdas de lo que te dije?", "trabajo|cansado;!no he entendido"),
   ("No me acuerdo de tu nombre.", "lcm"), ("Eres muy simpático.", "gracias")]},
]
if __name__ == "__main__":
    f, r = correr(D, verboso=True, salida="lab/res_tanda02.json"); imprime(r, "TANDA 2")
