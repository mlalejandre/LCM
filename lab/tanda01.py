"""Tanda exploratoria 1: 10 diálogos naturales escritos a mano (criterios escritos antes de ejecutar)."""
from lab.banco import correr, imprime
D = [
 {"id": "t1-social", "cat": "social", "turnos": [
   ("Hola, buenos días", "hola|buenos dias|buenas"), ("¿Cómo estás?", "bien|estupendamente|funcion*"), ("Me llamo Marcos", "marcos|encantado|gusto"),
   ("¿Cómo me llamo?", "marcos"), ("¿Quién eres?", "lcm"), ("¿Qué sabes hacer?", "aprend*|razon*|convers*|pregunt*|recuerd*|deduc*"),
   ("Gracias", "de nada|un placer|para eso|gusto|no hay de que"), ("Adiós", "adios|hasta|nos vemos")]},
 {"id": "t1-atributos", "cat": "atributos", "turnos": [
   ("Mi coche es rojo.", "ACK"), ("¿De qué color es mi coche?", "rojo"), ("¿Es mi coche azul?", "^no"), ("¿Es mi coche rojo?", "^si"),
   ("La casa de Ana es grande.", "ACK"), ("¿Cómo es la casa de Ana?", "grande"), ("¿Es pequeña la casa de Ana?", "^no"), ("¿De qué color es la casa de Ana?", "ABST")]},
 {"id": "t1-familia", "cat": "familia", "turnos": [
   ("Marta es la madre de Lucas.", "ACK"), ("Lucas es el padre de Irene.", "ACK"), ("¿Quién es la madre de Lucas?", "marta"), ("¿Quién es la abuela de Irene?", "marta"),
   ("¿Es Marta abuela de Irene?", "^si"), ("¿Por qué?", "madre;padre"), ("¿Quién es el hijo de Marta?", "lucas"), ("¿Quién es el padre de Marta?", "ABST")]},
 {"id": "t1-lugar", "cat": "lugar_tiempo", "turnos": [
   ("Pablo vive en Valencia.", "ACK"), ("¿Dónde vive Pablo?", "valencia"), ("Ahora Pablo vive en Bilbao.", "ACK"), ("¿Dónde vive Pablo?", "bilbao;!valencia"),
   ("¿Dónde vivía Pablo antes?", "valencia"), ("¿Vive Pablo en Madrid?", "^no"), ("¿Dónde trabaja Pablo?", "ABST")]},
 {"id": "t1-cantidad", "cat": "cantidad", "turnos": [
   ("Sara tiene tres gatos.", "ACK"), ("¿Cuántos gatos tiene Sara?", "tres|3"), ("Sara tiene dos perros.", "ACK"), ("¿Qué tiene Sara?", "gatos;perros"),
   ("¿Cuántos animales tiene Sara?", "cinco|5"), ("¿Tiene Sara un caballo?", "!^si"), ("¿Cuántos perros tiene Sara?", "dos|2")]},
 {"id": "t1-negacion", "cat": "negacion", "turnos": [
   ("Luis no come carne.", "ACK"), ("¿Come Luis carne?", "^no"), ("Luis come verdura.", "ACK"), ("¿Qué come Luis?", "verdura;!carne."),
   ("¿Qué no come Luis?", "carne"), ("¿Come Luis pescado?", "!^si")]},
 {"id": "t1-correferencia", "cat": "correferencia", "turnos": [
   ("Elena tiene un perro.", "ACK"), ("Se llama Toby.", "ACK"), ("¿Cómo se llama el perro de Elena?", "toby"), ("Ella vive en Granada.", "ACK"),
   ("¿Dónde vive Elena?", "granada"), ("¿Quién vive en Granada?", "elena"), ("¿Tiene Elena un perro?", "^si")]},
 {"id": "t1-acciones", "cat": "acciones", "turnos": [
   ("Carlos compró un libro ayer.", "ACK"), ("¿Qué compró Carlos?", "libro"), ("¿Quién compró un libro?", "carlos"), ("¿Cuándo compró Carlos el libro?", "ayer|17"),
   ("Carlos le dio el libro a Nuria.", "ACK"), ("¿Quién tiene el libro?", "nuria"), ("¿Tiene Carlos el libro?", "^no")]},
 {"id": "t1-conceptos", "cat": "conceptos", "turnos": [
   ("¿Qué es un perro?", "mamifero|animal"), ("¿Es un perro un animal?", "^si"), ("¿Para qué sirve un tenedor?", "comer"), ("¿Cuántos lados tiene un triángulo?", "tres|3"),
   ("¿De qué color es el cielo?", "azul"), ("¿Es un gato un pájaro?", "^no"), ("¿Qué día viene después del lunes?", "martes"), ("¿Qué es un zorbliano?", "ABST")]},
 {"id": "t1-charla", "cat": "charla", "turnos": [
   ("Estoy un poco triste hoy.", "siento|lamento|animo|pasa*|ocurr*|cuent*"), ("Me gusta mucho el fútbol.", "ACK"), ("¿Qué me gusta?", "futbol"),
   ("¿Qué día es hoy?", "miercoles|18"), ("¿Tú tienes hambre?", "no|soy"), ("Cuéntame algo.", "!no he entendido"), ("¿Qué opinas del fútbol?", "!no he entendido"), ("Vale, perfecto.", "!no he entendido;!no conozco")]},
]
if __name__ == "__main__":
    f, r = correr(D, verboso=True, salida="lab/res_tanda01.json"); imprime(r, "TANDA 1")
