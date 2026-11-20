"""Tanda 12 (desarrollo): conversaciones largas. Hilo, pronombres, cambios de tema y vuelta, cambios con el tiempo,
correcciones con números, resúmenes y preguntas de repaso. Criterios escritos antes de ejecutar."""
from lab.banco import correr, imprime
from lab.imagenes import png, img
D = [
 {"id": "t12-familia", "cat": "larga", "turnos": [
   ("Hola.", "hola"), ("Me llamo Teresa y tengo sesenta y tres años.", "teresa"), ("Estoy jubilada; antes era maestra.", "ANY"), ("Vivo en Zamora con mi marido, Luis.", "ANY"),
   ("Luis es carpintero.", "ACK"), ("Tenemos tres hijos.", "ACK"), ("El mayor se llama Rubén.", "ACK"), ("Rubén vive en Madrid.", "ACK"), ("Él es abogado.", "ACK"),
   ("La mediana se llama Elena.", "ACK"), ("Ella es médica y vive en León.", "ACK"), ("El pequeño se llama Dani.", "ACK"), ("Dani todavía estudia.", "ACK"),
   ("¿Cuántos años tengo?", "63|sesenta y tres"), ("¿Cómo se llama mi marido?", "luis"), ("¿A qué se dedica Luis?", "carpintero"), ("¿Cuántos hijos tengo?", "tres|3"),
   ("¿Dónde vive Rubén?", "madrid"), ("¿Qué es Rubén?", "abogado|hijo"), ("¿Dónde vive Elena?", "leon"), ("¿Quién es médica?", "elena"), ("¿Quién vive en Madrid?", "ruben"),
   ("¿Cómo se llama mi hija?", "elena"), ("¿Quién es el padre de Dani?", "luis"), ("¿Quién es la madre de Elena?", "tu|teresa|eres"), ("¿Rubén y Elena son hermanos?", "^si"),
   ("¿Dónde vivo?", "zamora"), ("¿Con quién vivo?", "luis|marido"), ("¿Tengo nietos?", "ABST|^no"), ("Rubén tiene una hija que se llama Carla.", "ACK"),
   ("¿Tengo nietos?", "^si|carla"), ("¿Quién es la abuela de Carla?", "tu|teresa|eres"), ("¿Quiénes son mis familiares?", "luis;ruben;elena")]},
 {"id": "t12-tema", "cat": "larga", "turnos": [
   ("Te voy a contar cosas de mi trabajo.", "ANY"), ("Trabajo en una oficina en Bilbao.", "ACK"), ("Mi jefa se llama Amaia.", "ACK"), ("Ella es muy exigente.", "ACK"),
   ("Mi compañero Iker es muy simpático.", "ANY"), ("Cambiando de tema, ayer fui al cine.", "ANY"), ("Vi una película de miedo.", "ANY"), ("¿Dónde trabajo?", "oficina|bilbao"),
   ("¿Cómo se llama mi jefa?", "amaia"), ("¿Cómo es Amaia?", "exigente"), ("¿Cómo es Iker?", "simpatic*"), ("¿Adónde fui ayer?", "cine"), ("¿Cuándo fui al cine?", "ayer"),
   ("Volviendo a lo de antes, Amaia tiene dos perros.", "ACK"), ("¿Cuántos perros tiene mi jefa?", "dos|2"), ("¿Los perros de Amaia vuelan?", "^no"), ("¿Iker tiene perros?", "ABST"),
   ("¿Quién es Iker?", "compañero"), ("¿Quién es Amaia?", "jefa")]},
 {"id": "t12-numeros", "cat": "larga", "turnos": [
   ("Mi tía Rosa tiene setenta años.", "ACK"), ("No, perdona: tiene setenta y cuatro.", "74|setenta y cuatro|ACK"), ("¿Cuántos años tiene Rosa?", "74|setenta y cuatro"),
   ("Mi primo Jorge mide ciento ochenta centímetros.", "ANY"), ("Mi casa tiene tres habitaciones.", "ACK"), ("¿Cuántas habitaciones tiene mi casa?", "tres|3"),
   ("Me he equivocado, tiene cuatro habitaciones.", "ANY"), ("¿Cuántas habitaciones tiene mi casa?", "cuatro|4;!tres"), ("Rosa vive en Toledo.", "ACK"),
   ("Perdona, Rosa vive en Cuenca.", "cuenca|ACK"), ("¿Dónde vive mi tía?", "cuenca;!toledo"), ("¿Rosa vive en Toledo?", "^no|cuenca")]},
 {"id": "t12-repaso", "cat": "larga", "turnos": [
   ("Me llamo Óliver.", "oliver"), ("Tengo una bici azul y un patinete.", "ACK"), ("Me gusta mucho nadar.", "ACK"), ("Mi mejor amigo se llama Sergio.", "ACK"),
   ("Sergio tiene un hermano gemelo, Marcos.", "ANY"), ("Sergio vive en Huesca.", "ACK"), (img("Mi patinete es de este color.", png("rojo")), "ACK|roj*"),
   ("¿De qué color es mi bici?", "azul"), ("¿De qué color es mi patinete?", "roj*"), ("¿Qué me gusta?", "nadar"), ("¿Cómo se llama mi mejor amigo?", "sergio"),
   ("¿Dónde vive Sergio?", "huesca"), ("¿Qué sabes de mí?", "oliver|bici|nadar|sergio"), ("¿Qué sabes de Sergio?", "huesca|amigo"), ("¿Tengo coche?", "ABST|^no"),
   ("¿Cuántos vehículos tengo?", "dos|2|bici|patinete"), ("Gracias, hasta luego.", "hasta|adios|de nada")]},
]
if __name__ == "__main__":
    import sys
    f, r = correr(D, verboso="-v" in sys.argv, salida="lab/res_tanda12.json")
    imprime(r, "TANDA 12")
