"""EXAMEN CIEGO 7: una conversación libre más, escrita con la 2.5 congelada y sin haberla probado antes.
Temas que no aparecen en ninguna tanda: mudanza, bodas, coche averiado, abuela en el pueblo, receta. Una sola pasada."""
from lab.banco import correr, imprime
D = [
 {"id": "c7-mudanza", "cat": "libre", "turnos": [
   ("buenos días!", "buenos dias|hola"), ("te cuento, la semana que viene me mudo de casa", "entendid*|apunto"), ("me voy a un piso más grande en el centro", "entendid*|apunto"),
   ("¿cuándo me mudo?", "proxima semana|semana"), ("¿adónde me mudo?", "piso|centro"), ("el piso nuevo tiene terraza", "entendid*|apunto"), ("¿tiene terraza el piso nuevo?", "^si"),
   ("mi hermano Pablo me va a ayudar con la mudanza", "entendid*|apunto"), ("¿quién me va a ayudar?", "pablo"), ("Pablo tiene una furgoneta", "entendid*"), ("¿una furgoneta es un vehículo?", "^si"),
   ("¿Pablo es mi hermano?", "^si"), ("¿tengo hermanas?", "ABST|^no")]},
 {"id": "c7-boda", "cat": "libre", "turnos": [
   ("este sábado se casa mi prima Lola", "entendid*|apunto"), ("se casa con un chico de Murcia que se llama Fran", "ANY"), ("¿quién se casa?", "lola"), ("¿con quién se casa Lola?", "fran"),
   ("¿cuándo es la boda?", "sabado"), ("no tengo traje para la boda", "entendid*|apunto"), ("¿tengo traje?", "^no"), ("mañana voy a comprar uno", "ANY"), ("¿qué voy a comprar mañana?", "traje"),
   ("¿Lola es mi hermana?", "^no|prima"), ("¿de dónde es Fran?", "murcia")]},
 {"id": "c7-coche", "cat": "libre", "turnos": [
   ("uf, se me ha estropeado el coche", "entendid*|apunto|vaya"), ("¿qué le pasa a mi coche?", "estropeado|estropeo|roto"), ("lo he llevado al taller", "entendid*|apunto"),
   ("¿dónde está mi coche?", "taller"), ("el mecánico dice que tardará tres días", "ANY"), ("¿qué dice el mecánico?", "tres dias|tardara"), ("mientras tanto voy en autobús", "ANY"),
   ("¿cómo voy mientras tanto?", "autobus"), ("¿un autobús tiene ruedas?", "^si"), ("¿mi coche está bien?", "^no|estropeado|roto|ABST")]},
 {"id": "c7-abuela", "cat": "libre", "turnos": [
   ("mi abuela Carmen vive en un pueblo de Teruel", "entendid*|apunto"), ("tiene noventa y dos años", "entendid*|apunto"), ("todavía hace pan en casa", "ANY"),
   ("¿cuántos años tiene mi abuela?", "92|noventa y dos"), ("¿dónde vive Carmen?", "teruel|pueblo"), ("¿qué hace mi abuela en casa?", "pan"), ("tiene gallinas y un huerto", "entendid*|apunto"),
   ("¿las gallinas ponen huevos?", "^si"), ("¿las gallinas de mi abuela vuelan?", "^no"), ("¿qué animales tiene mi abuela?", "gallinas"), ("¿Carmen es mi madre?", "^no|abuela")]},
 {"id": "c7-cierre", "cat": "libre", "turnos": [
   ("bueno, ¿de qué hemos hablado hoy?", "mudanza|piso|boda|coche|abuela|lola|pablo|carmen|mud*|cas*"), ("gracias por escucharme", "de nada|placer|gracias"), ("hasta mañana!", "hasta|adios")]},
]


def medir(verboso=False, salida="lab/res_ciego7.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "EXAMEN CIEGO 7")
