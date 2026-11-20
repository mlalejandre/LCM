"""CHARLA 50 F: referencia de la ronda 2.11 (conectores lógicos: copulativas, disyuntivas, comparativas, condicionales y comas).
UNA conversación libre de 50 interacciones (bloques con memoria compartida), escrita con la 2.10 congelada,
criterios fijados de antemano; no se lee hasta la medida final. Fecha de las pruebas: 19-11-2026."""
from lab.banco import correr, imprime
D = [
 {"id": "ch50f-a", "cat": "copulativas", "turnos": [
   ("hola, soy Irene", "irene;!no lo he entendido"), ("tengo un perro y dos gatos", "perro;gato*;!no lo he entendido"),
   ("¿tengo perro?", "^si"), ("¿cuántos gatos tengo?", "dos|2"), ("no tengo ni coche ni moto", "coche|moto;!no lo he entendido"),
   ("¿tengo coche?", "^no"), ("¿tengo moto?", "^no"), ("tanto mi padre como mi madre son médicos", "medic*;!no lo he entendido"),
   ("¿mi madre es médica?", "^si"), ("¿a qué se dedica mi padre?", "medico")]},
 {"id": "ch50f-b", "cat": "disyuntivas", "turnos": [
   ("mi hermano Pablo vive en Lugo o en Ourense, no me acuerdo", "lugo|ourense;!no lo he entendido"), ("¿dónde vive Pablo?", "lugo;ourense"),
   ("¿Pablo vive en Lugo?", "ourense"), ("ahora me acuerdo: no vive en Lugo", "lugo|ourense;!no lo he entendido"), ("¿dónde vive Pablo?", "ourense;!no lo s*"),
   ("los domingos como pescado o carne", "pescado|carne;!no lo he entendido"), ("¿qué como los domingos?", "pescado;carne"),
   ("¿Pablo es mayor o menor que yo?", "ABST"), ("Pablo tiene treinta años y yo veintiocho", "treinta|30|veintiocho|28;!no lo he entendido"),
   ("¿quién es mayor, Pablo o yo?", "pablo")]},
 {"id": "ch50f-c", "cat": "comparativas", "turnos": [
   ("¿soy mayor que Pablo?", "^no"), ("mi prima Sara es más alta que yo", "sara;!no lo he entendido"),
   ("yo soy más alta que Pablo", "pablo|alta;!no lo he entendido"), ("¿quién es la más alta de los tres?", "sara"),
   ("¿Pablo es más alto que Sara?", "^no"), ("¿soy más baja que Sara?", "^si"), ("el té me gusta más que el café", "te|cafe;!no lo he entendido"),
   ("¿qué me gusta más, el té o el café?", "^el te|te gusta mas el te|prefieres el te"), ("¿me gusta menos el café que el té?", "^si"),
   ("¿Pablo es más bajo que yo?", "^si")]},
 {"id": "ch50f-d", "cat": "condicionales", "turnos": [
   ("nací en 1995", "1995;!no lo he entendido"), ("si nací el 5 de diciembre, ¿qué edad tengo?", "30;!31"),
   ("y si nací el 5 de marzo, ¿qué edad tengo?", "31;!30"), ("si nací el día 5, ¿qué edad tengo?", "30;31"),
   ("si mañana llueve, no iré a la playa", "llueve|llover|playa;!no lo he entendido"), ("mañana va a llover", "ANY"),
   ("¿iré mañana a la playa?", "^no"), ("si estudio, apruebo", "estudi*|aprueb*;!no lo he entendido"), ("¿qué pasa si estudio?", "aprueb*"),
   ("¿he aprobado?", "ABST")]},
 {"id": "ch50f-e", "cat": "comas_repaso", "turnos": [
   ("en la compra llevo pan, leche, huevos y fruta", "pan|leche;!no lo he entendido"), ("¿llevo leche?", "^si"), ("¿llevo queso?", "ABST|^no"),
   ("¿qué llevo en la compra?", "pan;leche;huevos;fruta"), ("Sara, Pablo y yo iremos al cine el viernes", "cine;!no lo he entendido"),
   ("¿quién va a ir al cine?", "sara;pablo"), ("¿tengo moto?", "^no"), ("¿dónde vive Pablo?", "ourense"),
   ("¿quién es más alto, Sara o Pablo?", "sara"), ("gracias, hasta luego", "hasta|adios|nada")]},
]


def medir(verboso=False, salida="lab/res_charla50f.json"):
    return correr(D, verboso=verboso, salida=salida, continua=True)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "CHARLA 50 F")
