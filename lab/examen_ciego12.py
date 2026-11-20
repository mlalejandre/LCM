"""EXAMEN CIEGO 12: coordinación (tres o más sujetos con «yo», listas de lugares y complementos, verbos y adjetivos coordinados,
«también / tampoco», «ni… ni… ni», listas tras dos puntos). Escrito con la 2.11 congelada; no se lee hasta la medida final."""
from lab.banco import correr, imprime
D = [
 {"id": "c12-suj", "cat": "sujetos_yo", "turnos": [
   ("hola", "hola"), ("mi padre, mi madre y yo comemos juntos los domingos", "domingo*|comemos|com*;!no lo he entendido"),
   ("¿mi madre come los domingos?", "^si"), ("¿quién come los domingos?", "padre;madre"),
   ("Lucía, Marcos, Elena y yo trabajamos en la misma oficina", "oficina;!no lo he entendido"), ("¿dónde trabaja Elena?", "oficina"),
   ("¿Marcos trabaja en la oficina?", "^si"), ("¿dónde trabajo?", "oficina")]},
 {"id": "c12-listas", "cat": "listas", "turnos": [
   ("buenas", "hola|buenas"), ("he vivido en Toledo, Cuenca y Ávila", "toledo|cuenca|avila;!no lo he entendido"), ("¿he vivido en Cuenca?", "^si"),
   ("¿dónde he vivido?", "toledo;cuenca;avila"), ("en mi barrio hay una farmacia, dos bares y un mercado", "farmacia|bares|mercado;!no lo he entendido"),
   ("¿hay un mercado en mi barrio?", "^si"), ("¿cuántos bares hay en mi barrio?", "dos|2"),
   ("compro la fruta en el mercado, el pan en la panadería y la carne en la carnicería", "fruta|pan|carne;!no lo he entendido"),
   ("¿dónde compro el pan?", "panaderia")]},
 {"id": "c12-pred", "cat": "verbos_adjetivos", "turnos": [
   ("hola", "hola"), ("mi abuelo es alto, delgado y muy simpático", "alto|delgado|simpatico;!no lo he entendido"), ("¿mi abuelo es delgado?", "^si"),
   ("¿mi abuelo es bajo?", "^no"), ("Teresa estudia, trabaja y cuida de su madre", "estudia|trabaja|cuida;!no lo he entendido"), ("¿Teresa trabaja?", "^si"),
   ("mi tía es abogada y mi tío también", "abogad*;!no lo he entendido"), ("¿a qué se dedica mi tío?", "abogado"),
   ("mi primo no come carne y mi prima tampoco", "carne;!no lo he entendido"), ("¿mi prima come carne?", "^no")]},
 {"id": "c12-ni", "cat": "ni_dos_puntos", "turnos": [
   ("hola", "hola"), ("tengo cuatro gatos: Nube, Tizón, Canela y Rayo", "nube|tizon|canela|rayo;!no lo he entendido"), ("¿cuántos gatos tengo?", "cuatro|4"),
   ("¿Canela es mi gata?", "^si"), ("ni mi hermano ni mi hermana ni yo sabemos nadar", "nadar;!no lo he entendido"), ("¿mi hermana sabe nadar?", "^no"),
   ("¿sé nadar?", "^no"), ("¿mi hermano sabe nadar?", "^no")]},
 {"id": "c12-varios", "cat": "listas", "turnos": [
   ("hola", "hola"), ("me gustan el cine, el teatro y la música", "cine|teatro|musica;!no lo he entendido"), ("¿me gusta el teatro?", "^si"),
   ("¿qué me gusta?", "cine;teatro;musica"), ("hoy he ido al banco, a correos y al médico", "banco|correos|medico;!no lo he entendido"),
   ("¿he ido al médico hoy?", "^si")]},
]


def medir(verboso=False, salida="lab/res_ciego12.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    f, r = medir()
    imprime(r, "EXAMEN CIEGO 12")
