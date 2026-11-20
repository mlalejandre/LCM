"""Tanda 15 (desarrollo): las cuatro conversaciones libres de la ronda 2.5 (ver lab/conversaciones_libres.md),
convertidas en pruebas con criterio. Habla coloquial, muletillas, estilo indirecto, notas literales, grupos, sujetos pospuestos."""
from lab.banco import correr, imprime
D = [
 {"id": "t15-c1", "cat": "coloquial", "turnos": [
   ("hola, qué tal?", "hola"), ("pues yo aquí, un poco liado con el trabajo", "ANY"), ("soy Marcos, por cierto", "marcos"), ("trabajo de programador en una empresa pequeña", "ACK"),
   ("somos solo seis personas", "seis;!eres persona"), ("mi jefe es bastante majo, se llama Alfonso", "ACK"), ("¿cómo se llama mi jefe?", "alfonso"), ("¿y cuántos somos en la empresa?", "seis|6"),
   ("¿a qué me dedico?", "programador"), ("el caso es que llevo toda la semana durmiendo fatal", "ANY"), ("¿cómo he dormido esta semana?", "fatal"),
   ("mi mujer dice que debería hacer deporte", "ANY"), ("¿qué dice mi mujer?", "deporte"), ("¿qué deporte me recomiendas?", "ANY"), ("de pequeño jugaba al baloncesto", "ACK"),
   ("¿a qué jugaba de pequeño?", "baloncesto"), ("¿juego al baloncesto ahora?", "ABST|antes"), ("bueno, cambiando de tema, ¿sabes algo de perros?", "mamifero|animal|ladra*"),
   ("es que mi hijo quiere uno", "ANY"), ("¿qué quiere mi hijo?", "perro"), ("vale, me lo pensaré", "ANY"), ("¿qué te he contado de mi trabajo?", "programador|liado"),
   ("¿quién es Alfonso?", "jefe"), ("¿recuerdas cómo me llamo?", "marcos")]},
 {"id": "t15-c2", "cat": "coloquial", "turnos": [
   ("Buenas noches", "buenas noches|hola"), ("Hoy he ido al médico", "ACK"), ("Me ha dicho que tengo que comer menos sal", "ANY"), ("¿Qué me ha dicho el médico?", "sal"),
   ("También me duele la espalda", "ACK"), ("¿Qué me duele?", "espalda"), ("Por cierto, mi madre cumple años el viernes", "ACK"), ("¿Cuándo es el cumpleaños de mi madre?", "viernes"),
   ("Cumple setenta", "ACK"), ("¿Cuántos años cumple mi madre?", "setenta|70"), ("Le voy a regalar un libro", "ACK"), ("A ella le gustan las novelas de misterio", "ACK"),
   ("¿Qué le gusta a mi madre?", "novelas"), ("Mi hermano dice que mejor un perfume", "ANY"), ("¿Qué opina mi hermano?", "perfume;!perfumaste"), ("Bueno, da igual", "ANY"),
   ("¿Puedes equivocarte?", "^si|puedo equivocarme"), ("No me has entendido", "ANY"), ("Mañana llueve seguro", "apunto|entendid*;!libro llueve"), ("¿Va a llover mañana?", "lluev*|ABST;!libro")]},
 {"id": "t15-c3", "cat": "coloquial", "turnos": [
   ("Hola de nuevo", "hola"), ("Estoy un poco triste hoy", "ANY"), ("Es que se ha muerto el perro de mi vecina", "entendid*|apunto;!te moriste"), ("Se llamaba Toby y tenía catorce años", "entendid*|apunto;!encantado"),
   ("¿Cómo se llamaba el perro de mi vecina?", "toby"), ("¿Cuántos años tenía?", "14|catorce"), ("¿Y yo?", "ABST|triste|años"), ("Bueno, hablemos de otra cosa", "ANY"),
   ("El mes que viene me voy de vacaciones a Portugal", "ACK"), ("¿Adónde me voy de vacaciones?", "portugal"), ("Voy con mi novia y con mis suegros", "entendid*|apunto;!un mes"),
   ("¿Con quién voy?", "novia;suegros"), ("Ella es encantadora", "ACK"), ("¿Cómo es mi novia?", "encantadora"), ("Se llama Andrea, ya te lo dije", "ACK"), ("Andrea es de Oporto", "ACK"),
   ("Oporto está en Portugal", "ACK"), ("Entonces, ¿Andrea es de Portugal?", "^si"), ("Habla portugués y español", "ACK"), ("¿Cuántos idiomas habla?", "dos|2"),
   ("Yo solo hablo español", "ACK"), ("¿Hablo portugués?", "^no"), ("¿Qué es lo último que te he dicho?", "español"), ("adiós, me voy a dormir", "descanses|hasta")]},
 {"id": "t15-c4", "cat": "coloquial", "turnos": [
   ("ey que pasa", "hola"), ("me llamo Irene y estudio enfermería", "irene"), ("vivo en un piso compartido con dos chicas", "ACK"), ("una se llama Carla y la otra Marta", "carla;marta"),
   ("Carla es de Valencia", "ACK"), ("Marta estudia medicina, como yo casi jaja", "entendid*|apunto;!estudia irene"), ("¿con cuántas personas vivo?", "dos|2"), ("¿Quién es Carla?", "valencia|vives"),
   ("ayer Carla cocinó paella para las tres", "ACK"), ("¿qué cocinó Carla?", "paella"), ("estaba buenísima", "entendid*|apunto;!carla estaba"), ("la paella es un plato típico de Valencia", "entendid*|apunto;!plata"),
   ("¿la paella es un alimento?", "^si"), ("¿Carla cocina bien?", "ABST;!^si"), ("Marta no sabe cocinar nada", "ACK"), ("¿sabe cocinar Marta?", "^no"),
   ("¿me das ánimos?", "animo"), ("gracias, eres un sol", "gracias;!soles"), ("olvida lo de la paella", "olvid*"), ("¿qué cocinó Carla ayer?", "ABST"), ("bueno me voy a estudiar, chao", "hasta")]},
]
if __name__ == "__main__":
    import sys
    f, r = correr(D, verboso="-v" in sys.argv, salida="lab/res_tanda15.json")
    imprime(r, "TANDA 15")
