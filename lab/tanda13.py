"""Tanda 13 (desarrollo): más hilo largo. Pronombres de objeto y plural, «allí», «los dos», repasos de lo hablado,
charla intercalada y preguntas de vuelta a temas antiguos. Criterios escritos antes de ejecutar."""
from lab.banco import correr, imprime
D = [
 {"id": "t13-pron", "cat": "hilo", "turnos": [
   ("Mi prima Lucía vive en Granada.", "ACK"), ("Allí trabaja de profesora.", "ANY"), ("¿Dónde trabaja Lucía?", "granada"), ("¿Qué es Lucía?", "prima|profesora"),
   ("Lucía y su novio Raúl tienen un piso.", "ANY"), ("Ellos viven juntos.", "ANY"), ("¿Quién es el novio de Lucía?", "raul"), ("¿Tiene novio Lucía?", "^si|raul"),
   ("Raúl es bombero.", "ACK"), ("¿A qué se dedica el novio de Lucía?", "bombero"), ("¿Los bomberos son personas?", "ANY"), ("¿Lucía es mi hermana?", "^no|prima")]},
 {"id": "t13-repaso", "cat": "hilo", "turnos": [
   ("Me llamo Pau.", "pau"), ("Tengo un gato que se llama Mishi.", "ACK"), ("Me encanta el chocolate.", "ACK"), ("Mi hermana Laia vive en Girona.", "ACK"),
   ("¿Qué tal el día?", "ANY"), ("Bien, gracias.", "ANY"), ("¿De qué hemos hablado?", "mishi|chocolate|laia"), ("¿Qué te he dicho de mi hermana?", "girona"),
   ("¿Qué me encanta?", "chocolate"), ("¿El chocolate es un dulce?", "^si"), ("¿Cómo se llama mi gato?", "mishi"), ("¿Mishi es un mamífero?", "^si"),
   ("¿Laia tiene gato?", "ABST"), ("¿Quién vive en Girona?", "laia")]},
 {"id": "t13-dos", "cat": "hilo", "turnos": [
   ("Tengo dos amigos: Mario y Bea.", "ANY"), ("Los dos viven en Burgos.", "ANY"), ("Mario es arquitecto.", "ACK"), ("Bea es dentista.", "ACK"),
   ("¿Dónde vive Mario?", "burgos"), ("¿Dónde vive Bea?", "burgos"), ("¿Quién es dentista?", "bea;!mario"), ("¿Mario es dentista?", "^no|arquitecto"),
   ("¿Cuántos amigos tengo?", "dos|2|mario|bea"), ("¿Son Mario y Bea mis amigos?", "^si")]},
 {"id": "t13-vuelta", "cat": "hilo", "turnos": [
   ("Mi coche es gris.", "ACK"), ("Mi madre se llama Rocío.", "ACK"), ("Rocío vive en Jaén.", "ACK"), ("Hoy hace mucho calor.", "ANY"), ("Me apetece un helado.", "ANY"),
   ("¿Un helado es un dulce?", "^si"), ("Ayer compré un helado de fresa.", "ACK"), ("¿Qué compré ayer?", "helado"), ("¿De qué color es mi coche?", "gris"),
   ("¿Dónde vive mi madre?", "jaen"), ("¿Cómo se llama mi madre?", "rocio"), ("¿Mi madre vive en Jaén?", "^si"), ("¿Mi coche es rojo?", "^no|gris")]},
]
if __name__ == "__main__":
    import sys
    f, r = correr(D, verboso="-v" in sys.argv, salida="lab/res_tanda13.json")
    imprime(r, "TANDA 13")
