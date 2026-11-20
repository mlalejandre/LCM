"""Tanda 9 (desarrollo; antes examen ciego 3, pasado una vez a ciegas con el commit it17: 94.22 %, 1.16 % falsas).
Mezcla conversación corriente con lo nuevo de la 2.2 (conceptos, capas, excepciones, negativas, cuantificadores, efectos, familia)."""
from lab.banco import correr, imprime
D = [
 {"id": "c3-concep1", "cat": "conceptos", "turnos": [
   ("¿Una vaca es un animal?", "^si"), ("¿Es una vaca un ave?", "^no"), ("¿Qué es una paloma?", "ave"), ("¿Las palomas vuelan?", "^si"), ("¿Tiene plumas una paloma?", "^si"),
   ("¿Una paloma tiene pelo?", "ABST|^no"), ("¿Un tiburón es un pez?", "^si"), ("¿Vive en el agua un tiburón?", "^si"), ("¿Un tiburón tiene patas?", "^no"), ("¿Qué es un pino?", "arbol")]},
 {"id": "c3-concep2", "cat": "conceptos", "turnos": [
   ("¿Un sofá es un mueble?", "^si"), ("¿Un sofá es una herramienta?", "^no;mueble"), ("¿Un tren es un vehículo?", "^si"), ("¿Los trenes vuelan?", "ABST|^no"), ("¿Una guitarra es un instrumento?", "^si"),
   ("¿Qué es un abrigo?", "prenda"), ("¿El oro es un metal?", "^si"), ("¿Es el tenis un deporte?", "^si"), ("¿La alegría es una emoción?", "^si"), ("¿Un zapato es una prenda?", "^no|calzado")]},
 {"id": "c3-excep", "cat": "excepciones", "turnos": [
   ("¿Un avestruz es un ave?", "^si"), ("¿Vuela un avestruz?", "^no"), ("¿Un águila vuela?", "^si"), ("¿Una ballena es un mamífero?", "^si"), ("¿Una ballena vive en el mar?", "^si"),
   ("¿Tiene pelo una ballena?", "^no"), ("¿Un gato tiene pelo?", "^si"), ("¿Pone huevos una gallina?", "^si"), ("¿Pone huevos una vaca?", "^no"), ("¿Una serpiente tiene patas?", "^no")]},
 {"id": "c3-ejemplos", "cat": "conceptos", "turnos": [
   ("Dime dos muebles.", "silla|mesa|cama|sofa|armario|estanteria|sillon"), ("¿Qué verduras conoces?", "tomate|lechuga|zanahoria|cebolla|pimiento"), ("Nombra un instrumento.", "guitarra|piano|violin|flauta|tambor"),
   ("Dime cinco animales.", "!silla;!manzana"), ("¿Qué partes tiene una flor?", "petalos"), ("¿Cuál es el contrario de rápido?", "lento"), ("¿Qué es lo contrario de abrir?", "cerrar"),
   ("¿Qué tienen en común una guitarra y un piano?", "instrumento*"), ("¿Qué tienen en común un gorrión y un águila?", "ave*|pajaro*|vuelan|plumas"), ("Dime dos zurcos.", "ABST")]},
 {"id": "c3-mezcla1", "cat": "mezcla", "turnos": [
   ("Mi hija tiene un canario que se llama Pipo.", "ACK"), ("¿Pipo es un ave?", "^si"), ("¿Pipo tiene alas?", "^si"), ("¿Pipo es un mamífero?", "^no"), ("¿De quién es Pipo?", "hija"),
   ("¿Pipo ladra?", "^no|ABST"), ("Pipo es amarillo.", "ACK"), ("¿De qué color es el canario de mi hija?", "amarill*"), ("¿Cuántos años tiene Pipo?", "ABST")]},
 {"id": "c3-mezcla2", "cat": "mezcla", "turnos": [
   ("Ayer compré una sandía y dos melones.", "ACK"), ("¿Compré fruta ayer?", "^si|sandia|melon*"), ("¿Cuántos melones compré?", "dos|2"), ("Mi tío es fontanero.", "ACK"),
   ("¿Cuál es la profesión de mi tío?", "fontanero"), ("¿Mi tío es carpintero?", "^no"), ("Mi prima toca la flauta.", "ACK"), ("¿Qué instrumento toca mi prima?", "flauta"),
   ("¿Mi prima toca el piano?", "ABST|^no")]},
 {"id": "c3-usuario-ensena", "cat": "excepciones", "turnos": [
   ("Los grufos son aves.", "ACK"), ("¿Un grufo vuela?", "^si"), ("Los grufos no vuelan.", "ACK"), ("¿Un grufo vuela?", "^no"), ("¿Un grufo tiene plumas?", "^si"), ("¿Las aves vuelan?", "^si"),
   ("Algunas arañas son venenosas.", "ACK"), ("¿Las arañas son venenosas?", "ABST|algunas"), ("¿Cuántas patas tiene una araña?", "ocho|8")]},
 {"id": "c3-neg1", "cat": "negativas", "turnos": [
   ("Carlos no tiene hijos.", "ACK"), ("¿Tiene hijos Carlos?", "^no"), ("Elena tiene dos hijos.", "ACK"), ("¿Quién no tiene hijos?", "carlos;!elena"), ("¿Quién tiene hijos?", "elena;!carlos"),
   ("¿Carlos tiene perro?", "ABST"), ("Carlos no vive en Burgos.", "ACK"), ("¿Carlos vive en Burgos?", "^no"), ("¿Dónde vive Carlos?", "ABST")]},
 {"id": "c3-neg2", "cat": "negativas", "turnos": [
   ("No me gustan las espinacas.", "ACK"), ("Tampoco me gusta el brócoli.", "ACK"), ("Me encanta la pasta.", "ACK"), ("¿Me gustan las espinacas?", "^no"), ("¿Qué no me gusta?", "espinacas;brocoli;!pasta"),
   ("¿Qué me gusta?", "pasta;!espinacas"), ("Nunca desayuno.", "ACK"), ("¿Desayuno?", "^no|nunca"), ("No bebo ni café ni té.", "ACK"), ("¿Bebo té?", "^no"), ("¿Bebo leche?", "ABST")]},
 {"id": "c3-nadie", "cat": "negativas", "turnos": [
   ("Nadie de mi familia toca el piano.", "ACK"), ("¿Toca el piano alguien de mi familia?", "^no|nadie"), ("No tengo primos.", "ACK"), ("¿Tengo primos?", "^no"), ("¿Cuántos primos tengo?", "ningun*|cero|no tienes"),
   ("No tengo ningún gato.", "ACK"), ("¿Tengo algún gato?", "^no"), ("En mi casa nadie fuma.", "ACK"), ("¿Fuma alguien en mi casa?", "^no|nadie")]},
 {"id": "c3-efectos", "cat": "efectos", "turnos": [
   ("Raúl abrió la ventana.", "ACK"), ("¿Está abierta la ventana?", "^si"), ("¿Está cerrada la ventana?", "^no"), ("Después Marta cerró la ventana.", "ACK"), ("¿Está abierta la ventana?", "^no|cerrada"),
   ("He encendido la tele.", "ACK"), ("¿Está apagada la tele?", "^no|encendida"), ("Mi hermano rompió su bici.", "ACK"), ("¿Cómo está la bici de mi hermano?", "rota"), ("Laura llegó a Bilbao.", "ACK"),
   ("¿Dónde está Laura?", "bilbao")]},
 {"id": "c3-familia", "cat": "relaciones", "turnos": [
   ("Mi padre se llama Andrés y mi abuela se llama Carmen.", "ACK"), ("Mi vecina se llama Paula.", "ACK"), ("¿Andrés es de mi familia?", "^si"), ("¿Paula es de mi familia?", "!^si"),
   ("¿Quiénes son mis familiares?", "andres;carmen;!paula"), ("¿Qué relación tengo con Carmen?", "abuela"), ("¿Qué es Paula de mí?", "vecina"), ("Mi hermano se llama Hugo.", "ACK"),
   ("Mi hermana se llama Noa.", "ACK"), ("¿Cómo se llama mi hermano?", "hugo;!noa"), ("¿Cómo se llama mi hermana?", "noa;!hugo"), ("¿Cuántos hermanos tengo?", "dos|2")]},
 {"id": "c3-correc", "cat": "correcciones", "turnos": [
   ("Mi perro se llama Rex.", "ACK"), ("No, perdona, se llama Max.", "max"), ("¿Cómo se llama mi perro?", "max;!rex"), ("Mi jefa vive en Jaén.", "ACK"), ("Me he equivocado, vive en Córdoba.", "cordoba"),
   ("¿Dónde vive mi jefa?", "cordoba;!jaen"), ("¿Max es un animal?", "^si"), ("¿Max maúlla?", "^no|ABST")]},
 {"id": "c3-persona", "cat": "persona", "turnos": [
   ("Me llamo Irene y soy enfermera.", "irene"), ("Vivo en Gijón con mi pareja.", "ACK"), ("Tengo treinta y dos años.", "ACK"), ("¿Cómo me llamo?", "irene"), ("¿En qué trabajo?", "enfermera"),
   ("¿Dónde vivo?", "gijon"), ("¿Con quién vivo?", "pareja"), ("¿Qué edad tengo?", "32|treinta y dos"), ("¿Tengo hijos?", "ABST"), ("¿Soy médica?", "^no|enfermera")]},
 {"id": "c3-larga", "cat": "larga", "turnos": [
   ("Hola, buenas.", "hola|buenas"), ("Soy Tomás.", "tomas"), ("Mi mujer se llama Inés y es profesora.", "ACK"), ("Tenemos una hija, Vera, de ocho años.", "ACK"), ("Vera tiene un hámster.", "ACK"),
   ("¿Cómo se llama mi mujer?", "ines"), ("¿A qué se dedica Inés?", "profesora"), ("¿Cuántos años tiene Vera?", "ocho|8"), ("¿Qué mascota tiene Vera?", "hamster"), ("¿El hámster de Vera es un mamífero?", "^si"),
   ("¿El hámster vuela?", "^no"), ("¿Cómo se llama el hámster?", "ABST"), ("Se llama Bolita.", "ACK"), ("¿Quién es Bolita?", "hamster"), ("¿Quién es la madre de Vera?", "ines"),
   ("¿Tengo algún hijo varón?", "ABST|^no"), ("Gracias por todo.", "de nada|gracias|placer"), ("Hasta luego.", "hasta|adios")]},
 {"id": "c3-social", "cat": "social", "turnos": [
   ("Buenos días.", "buenos dias|hola"), ("¿Cómo estás?", "bien"), ("¿Qué sabes hacer?", "ANY"), ("¿Sabes qué es un perro?", "mamifero|animal"), ("¿Quién te ha enseñado eso?", "fabrica"),
   ("¿Tú eres un animal?", "^no|ABST|no soy"), ("Estoy un poco cansado hoy.", "siento|vaya|descans*|animo"), ("¿Cuál es la capital de Mongolia?", "ABST"), ("Vale, no pasa nada.", "ANY"), ("Adiós.", "adios|hasta")]},
 {"id": "c3-anti", "cat": "antialucinacion", "turnos": [
   ("Mi compañera Olga trabaja en Lugo.", "ACK"), ("¿Dónde vive Olga?", "ABST"), ("¿Olga tiene coche?", "ABST"), ("¿Cuántos años tiene Olga?", "ABST"), ("¿Olga trabaja en Lugo?", "^si"),
   ("¿Olga trabaja en Vigo?", "^no|lugo"), ("¿Quién es el marido de Olga?", "ABST"), ("¿Qué animales tiene Olga?", "ABST"), ("¿Un drago es un árbol?", "ABST"), ("¿Cuántas patas tiene un zurco?", "ABST")]},
]


def medir(verboso=False, salida="lab/res_tanda09.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "TANDA 9")
