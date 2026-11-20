"""Tanda 14 (desarrollo; antes examen ciego 5: 2.3 = 89.55 %, 2.4 = 94.03 %): conversaciones largas (30-40 turnos). Escrito con el código congelado de la 2.3 (commit 4054dc7)
ANTES de mirar los fallos del ciego 4. Solo se leen los agregados; las transcripciones no se usan para corregir.
Mide si el LCM mantiene el hilo: correferencia (él, ella, su), cambios de tema y vuelta, cambios en el tiempo,
correcciones, resúmenes, conceptos e imágenes dentro de una charla larga."""
from lab.banco import correr, imprime
from lab.imagenes import png, figura, img
D = [
 {"id": "c5-vida", "cat": "larga_vida", "turnos": [
   ("Hola, buenas tardes.", "hola|buenas"), ("Me llamo Ramón y tengo cuarenta y cinco años.", "ramon"), ("Soy cocinero en un restaurante de Valencia.", "ACK"),
   ("Vivo en Valencia desde hace diez años.", "ACK"), ("Antes vivía en Albacete.", "ACK"), ("¿Cómo me llamo?", "ramon"), ("¿Cuántos años tengo?", "45|cuarenta y cinco"),
   ("¿A qué me dedico?", "cociner*"), ("¿Dónde vivo?", "valencia"), ("¿Dónde vivía antes?", "albacete"), ("¿Vivo en Albacete?", "^no|valencia|ya no"),
   ("Estoy casado con Pilar.", "ACK"), ("Pilar es enfermera.", "ACK"), ("Tenemos dos hijos: Hugo y Marta.", "ACK"), ("Hugo tiene doce años.", "ACK"),
   ("Marta tiene nueve años.", "ACK"), ("¿Cómo se llama mi mujer?", "pilar"), ("¿En qué trabaja Pilar?", "enfermer*"), ("¿Cuántos hijos tengo?", "dos|2"),
   ("¿Quién es mayor, Hugo o Marta?", "hugo"), ("¿Cuántos años tiene Marta?", "nueve|9"), ("Hugo juega al fútbol los sábados.", "ACK"), ("¿Qué hace Hugo los sábados?", "futbol"),
   ("¿El fútbol es un deporte?", "^si"), ("Marta toca el piano.", "ACK"), ("¿Qué instrumento toca Marta?", "piano"), ("¿Hugo toca el piano?", "ABST|^no"),
   ("¿Quién es la madre de Hugo?", "pilar"), ("¿Quién es el padre de Marta?", "ramon|tu|eres|tú"), ("¿Son hermanos Hugo y Marta?", "^si"),
   ("¿Tengo nietos?", "ABST|^no"), ("Dime qué sabes de Pilar.", "enfermer*"), ("Gracias, me voy a hacer la cena.", "ANY")]},
 {"id": "c5-coref", "cat": "larga_coref", "turnos": [
   ("Te voy a hablar de mis vecinos.", "ANY"), ("El del primero se llama Andrés.", "ACK"), ("Andrés es fontanero.", "ACK"), ("Él vive con su madre, que se llama Encarna.", "ANY"),
   ("Encarna tiene ochenta años.", "ACK"), ("Ella tiene un loro.", "ACK"), ("El loro se llama Kiko.", "ACK"), ("¿Quién es fontanero?", "andres"),
   ("¿Cuántos años tiene Encarna?", "80|ochenta"), ("¿Quién tiene un loro?", "encarna"), ("¿Cómo se llama el loro?", "kiko"), ("¿Kiko es un ave?", "^si"),
   ("¿Kiko tiene plumas?", "^si"), ("¿Kiko puede volar?", "^si"), ("La del segundo se llama Sofía.", "ANY"), ("Sofía es profesora de inglés.", "ACK"),
   ("Ella tiene dos gatos.", "ACK"), ("¿Cuántos gatos tiene Sofía?", "dos|2"), ("¿Los gatos de Sofía ladran?", "^no|maull*|maúll*"), ("¿Quién es profesora?", "sofia"),
   ("¿Andrés es profesor?", "^no|fontanero"), ("¿Encarna tiene gatos?", "ABST|^no"), ("Andrés y Sofía son amigos.", "ACK"), ("¿Es Sofía amiga de Andrés?", "^si"),
   ("¿Andrés es de mi familia?", "!^si"), ("¿Dónde vive Sofía?", "ANY"), ("¿Cómo se llama la madre de Andrés?", "encarna"), ("¿Quién es Kiko?", "loro"),
   ("¿De quién es Kiko?", "encarna"), ("Vale, ya está.", "ANY")]},
 {"id": "c5-cambios", "cat": "larga_tiempo", "turnos": [
   ("Te cuento cosas de mi amiga Clara.", "ANY"), ("Clara vive en Lugo.", "ACK"), ("Clara trabaja en una farmacia.", "ACK"), ("Clara tiene un coche rojo.", "ACK"),
   ("¿Dónde vive Clara?", "lugo"), ("¿De qué color es el coche de Clara?", "roj*"), ("El mes pasado Clara se mudó a Oviedo.", "ACK"), ("¿Dónde vive Clara ahora?", "oviedo;!lugo"),
   ("¿Dónde vivía Clara antes?", "lugo"), ("¿Clara vive en Lugo?", "^no|ya no|oviedo"), ("Clara vendió su coche.", "ACK"), ("¿Tiene coche Clara?", "^no|ya no"),
   ("Ahora Clara tiene una moto.", "ACK"), ("¿Qué tiene Clara ahora?", "moto"), ("¿Cuántas ruedas tiene una moto?", "dos|2"), ("Clara ya no trabaja en la farmacia.", "ACK"),
   ("¿Trabaja Clara en una farmacia?", "^no|ya no"), ("¿Dónde trabajaba Clara?", "farmacia"), ("Ahora Clara trabaja en un hospital.", "ACK"), ("¿Dónde trabaja Clara?", "hospital;!farmacia"),
   ("¿Un hospital es un edificio?", "^si"), ("Clara está muy contenta.", "ACK"), ("¿Cómo está Clara?", "contenta"), ("¿Clara está triste?", "^no|contenta"),
   ("Resúmeme lo que sabes de Clara.", "oviedo;hospital"), ("¿Clara tiene hijos?", "ABST"), ("Muchas gracias.", "de nada|placer|gracias")]},
 {"id": "c5-mezcla", "cat": "larga_mezcla", "turnos": [
   ("Buenos días.", "buenos dias|hola"), ("Soy Nuria.", "nuria"), ("Tengo un perro y una gata.", "ACK"), ("El perro se llama Thor.", "ACK"), ("La gata se llama Mía.", "ACK"),
   ("¿Cómo se llama mi perro?", "thor"), ("¿Cómo se llama mi gata?", "mia;!thor"), ("¿Thor es un mamífero?", "^si"), ("¿Mía ladra?", "^no|maull*|maúll*"),
   (img("Thor es de este color.", png("marron")), "ACK|marron|marrón"), ("¿De qué color es Thor?", "marron|marrón"), (img("Mía es de este color.", png("blanco")), "ACK|blanc*"),
   ("¿De qué color es Mía?", "blanc*;!marron"), ("¿Thor es blanco?", "^no|marron|marrón"), ("¿Qué tienen en común un perro y un gato?", "mamifero*|animal*"),
   ("Ayer llevé a Thor al veterinario.", "ACK"), ("¿A quién llevé al veterinario?", "thor"), ("¿Cuándo fui al veterinario?", "ayer"), ("No me gustan los veterinarios caros.", "ANY"),
   ("Mi hermano Pablo tiene una tortuga.", "ACK"), ("¿Qué mascota tiene Pablo?", "tortuga"), ("¿Una tortuga es un reptil?", "^si"), ("¿Pablo es mi hermano?", "^si"),
   ("¿Cuántas mascotas tengo?", "dos|2"), (img("¿Qué ves?", figura("circulo", "azul")), "circulo;azul"), ("¿Es un cuadrado?", "^no;circulo"), ("¿Cómo se llama mi perro?", "thor"),
   ("¿Quién tiene una tortuga?", "pablo"), ("¿Y yo tengo tortuga?", "ABST|^no"), ("Hasta mañana.", "hasta|adios")]},
 {"id": "c5-correcciones", "cat": "larga_correcciones", "turnos": [
   ("Mi jefe se llama Alberto.", "ACK"), ("Alberto tiene cincuenta años.", "ACK"), ("No, perdona, tiene cincuenta y dos.", "52|cincuenta y dos|ACK"), ("¿Cuántos años tiene Alberto?", "52|cincuenta y dos;!50 "),
   ("Alberto vive en Murcia.", "ACK"), ("Me he equivocado: vive en Cartagena.", "cartagena|ACK"), ("¿Dónde vive Alberto?", "cartagena;!murcia"), ("Alberto tiene una hija.", "ACK"),
   ("Su hija se llama Irene.", "ACK"), ("¿Cómo se llama la hija de Alberto?", "irene"), ("Irene estudia medicina.", "ACK"), ("¿Qué estudia Irene?", "medicina"),
   ("¿Quién es el padre de Irene?", "alberto"), ("Alberto no tiene coche.", "ACK"), ("¿Tiene coche Alberto?", "^no"), ("Alberto va al trabajo en bicicleta.", "ACK"),
   ("¿Cómo va Alberto al trabajo?", "bicicleta"), ("¿Una bicicleta tiene motor?", "^no"), ("¿Alberto es mi jefe?", "^si"), ("¿Es Irene mi jefa?", "!^si"),
   ("¿Alberto vive en Murcia?", "^no|cartagena"), ("Olvida lo de la bicicleta.", "ANY"), ("¿Qué sabes de Alberto?", "jefe|cartagena|52")]},
]


def medir(verboso=False, salida="lab/res_tanda14.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "TANDA 14")
