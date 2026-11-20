"""CHARLA 50 I: referencia de la ronda 2.15 (usar los conceptos en la charla, varias clases a la vez, relaciones de función/material/lugar/usuario,
fábrica frente a lo dicho). Escrita con la 2.14 congelada; no se lee hasta la medida final."""
from lab.banco import correr, imprime
D = [
 {"id": "ch50i-a", "cat": "herencia_charla", "turnos": [
   ("hola", "hola"), ("tengo un canario y una tortuga", "canario|tortuga;!no lo he entendido"), ("¿tengo un pájaro?", "^si"), ("¿tengo un ave?", "^si"),
   ("¿tengo un reptil?", "^si"), ("¿tengo un mamífero?", "^no|ABST"), ("¿qué animales tengo?", "canario;tortuga"), ("¿mi canario tiene plumas?", "^si"),
   ("¿mi tortuga vuela?", "^no"), ("me he comprado una chaqueta y unas botas", "chaqueta|botas;!no lo he entendido"), ("¿me he comprado ropa?", "^si"),
   ("¿me he comprado calzado?", "^si"), ("¿qué prenda me he comprado?", "chaqueta")]},
 {"id": "ch50i-b", "cat": "personas", "turnos": [
   ("mi tía Carmen es enfermera", "enfermera;!no lo he entendido"), ("¿mi tía es una persona?", "^si"), ("¿Carmen es un objeto?", "^no"), ("¿Carmen trabaja?", "^si"),
   ("¿Carmen es una profesional?", "^si"), ("mi vecino es alcalde", "alcalde;!no lo he entendido"), ("¿mi vecino es un político?", "^si"), ("¿quién es político?", "vecino")]},
 {"id": "ch50i-c", "cat": "varias_clases", "turnos": [
   ("¿la cena es una comida?", "^si"), ("¿la cena es un evento?", "^si"), ("¿una tetera es un recipiente?", "^si"), ("¿una naranja es una fruta?", "^si"),
   ("¿el naranja es un color?", "^si"), ("¿un cuchillo es un cubierto?", "^si"), ("¿un cuchillo puede ser un arma?", "^si"), ("¿un cuchillo es un animal?", "^no")]},
 {"id": "ch50i-d", "cat": "relaciones", "turnos": [
   ("¿para qué sirve una nevera?", "enfriar|conservar|guardar|frio|fria"), ("¿de qué está hecha una botella?", "vidrio|cristal|plastico"),
   ("¿dónde suele estar una nevera?", "cocina"), ("¿quién usa un martillo?", "carpintero|albañil"), ("¿qué sirve para cortar?", "cuchillo|tijeras|sierra"),
   ("¿qué hay en una cocina?", "nevera|horno|fregadero|fogones|encimera"), ("¿con qué se escribe?", "boligrafo|lapiz|pluma|teclado|rotulador"),
   ("tengo unas tijeras", "tijeras;!no lo he entendido"), ("¿tengo algo para cortar?", "^si|tijeras")]},
 {"id": "ch50i-e", "cat": "fabrica_y_dicho", "turnos": [
   ("mi canario no canta", "canta;!no lo he entendido"), ("¿mi canario canta?", "^no"), ("¿los pájaros cantan?", "^si"), ("Luis sabe conducir", "luis;!no lo he entendido"),
   ("¿quién sabe conducir?", "luis"), ("¿los conductores conducen?", "^si"), ("¿cómo lo sabes?", "fabrica"), ("el perro de Luis no ladra", "ladra;!no lo he entendido"),
   ("¿el perro de Luis ladra?", "^no"), ("¿los perros ladran?", "^si"), ("¿Luis tiene un animal?", "^si"), ("gracias", "nada|gracias")]},
]


def medir(verboso=False, salida="lab/res_charla50i.json"):
    return correr(D, verboso=verboso, salida=salida, continua=True)


if __name__ == "__main__":
    import sys
    f, r = medir("-v" in sys.argv)
    imprime(r, "CHARLA 50 I")
