"""CHARLA 50 G: referencia de la ronda 2.12 (coordinación de tres o más elementos, con «yo»; listas de complementos;
verbos y adjetivos coordinados; «yo también / tampoco»; «ni… ni… ni»; listas tras dos puntos).
UNA conversación libre de 50 interacciones, escrita con la 2.11 congelada; no se lee hasta la medida final."""
from lab.banco import correr, imprime
D = [
 {"id": "ch50g-a", "cat": "sujetos_yo", "turnos": [
   ("hola, me llamo Marina", "marina;!no lo he entendido"), ("Sara, Pablo y yo iremos al cine el viernes", "sara;pablo;cine;!no lo he entendido"),
   ("¿quién irá al cine?", "sara;pablo;tu|iras"), ("¿Pablo irá al cine?", "^si"), ("¿iré yo al cine?", "^si"),
   ("mi hermano, mi cuñada y yo vivimos en Murcia", "murcia;!no lo he entendido"), ("¿dónde vive mi cuñada?", "murcia"),
   ("¿dónde vivo?", "murcia"), ("Ana y yo somos primas", "ana|prima*;!no lo he entendido"), ("¿quién es Ana?", "prima")]},
 {"id": "ch50g-b", "cat": "listas_complementos", "turnos": [
   ("he estado en Francia, Italia y Grecia", "francia|italia|grecia;!no lo he entendido"), ("¿he estado en Grecia?", "^si"), ("¿he estado en Japón?", "ABST|^no"),
   ("tengo amigos en Madrid, Sevilla y Bilbao", "madrid|sevilla|bilbao;!no lo he entendido"), ("¿tengo amigos en Sevilla?", "^si"),
   ("¿dónde tengo amigos?", "madrid;sevilla;bilbao"), ("en la reunión había gente de Vigo, de Lugo y de León", "vigo|lugo|leon;!no lo he entendido"),
   ("¿había gente de León en la reunión?", "^si"), ("hablo inglés, francés y un poco de alemán", "ingles|frances|aleman;!no lo he entendido"),
   ("¿hablo francés?", "^si")]},
 {"id": "ch50g-c", "cat": "verbos_adjetivos", "turnos": [
   ("me levanto, desayuno y salgo a correr", "correr|desayun*;!no lo he entendido"), ("¿desayuno?", "^si"),
   ("mi casa es grande, luminosa y barata", "grande|luminosa|barata;!no lo he entendido"), ("¿mi casa es luminosa?", "^si"),
   ("¿cómo es mi casa?", "grande;luminosa;barata"), ("Pablo canta y baila muy bien", "canta|baila;!no lo he entendido"), ("¿Pablo baila?", "^si"),
   ("tengo un perro negro, una gata blanca y dos peces", "perro|gata|peces;!no lo he entendido"), ("¿de qué color es mi gata?", "blanca"),
   ("¿cuántos peces tengo?", "dos|2")]},
 {"id": "ch50g-d", "cat": "tambien_ni_lista", "turnos": [
   ("Sara es enfermera y yo también", "enfermera;!no lo he entendido"), ("¿soy enfermera?", "^si"),
   ("Pablo no fuma y yo tampoco", "fum*;!no lo he entendido"), ("¿fumo?", "^no"), ("ni Sara ni Pablo ni yo tenemos coche", "coche;!no lo he entendido"),
   ("¿Sara tiene coche?", "^no"), ("¿tengo coche?", "^no"), ("tengo tres sobrinos: Leo, Hugo y Mía", "leo|hugo|mia;!no lo he entendido"),
   ("¿cómo se llaman mis sobrinos?", "leo;hugo;mia"), ("¿cuántos sobrinos tengo?", "tres|3")]},
 {"id": "ch50g-e", "cat": "repaso", "turnos": [
   ("¿quién irá al cine?", "sara;pablo"), ("¿dónde vive mi hermano?", "murcia"), ("¿he estado en Italia?", "^si"),
   ("¿dónde tengo amigos?", "madrid;sevilla;bilbao"), ("¿cómo es mi casa?", "grande;luminosa;barata"), ("¿quién es enfermera?", "sara;tu|eres"),
   ("¿Pablo fuma?", "^no"), ("¿cuántos peces tengo?", "dos|2"), ("¿Leo es mi sobrino?", "^si"), ("gracias, hasta mañana", "hasta|adios|nada")]},
]


def medir(verboso=False, salida="lab/res_charla50g.json"):
    return correr(D, verboso=verboso, salida=salida, continua=True)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "CHARLA 50 G")
