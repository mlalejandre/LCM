"""EXAMEN CIEGO 15b · muestra LIMPIA. Escrito tras congelar la 2.15 (commit ff1da63) y antes de medir ninguna versión con él.
Palabras sacadas AL AZAR (semilla 2151) de la base 2.14 (objetos, oficios, animales, prendas, alimentos, edificios), excluyendo todo lo que
aparece en charla50i, ciego15 y las tandas iter215. Los criterios se escribieron por sentido común, SIN consultar los datos de relaciones.
Los nombres admiten plural (pintor* ) porque la respuesta natural suele ir en plural."""
from lab.banco import correr, imprime
D = [
 {"id": "c15b-rel", "cat": "relaciones", "turnos": [
   ("hola", "hola"), ("¿para qué sirve una gaita?", "musica|tocar"), ("¿quién usa una gaita?", "musico*|gaitero*"), ("¿para qué sirve una piragua?", "navegar|remar|deporte|transport*|viajar"),
   ("¿dónde suele estar una piragua?", "rio|agua|mar|lago"), ("¿para qué sirve un tractor?", "arar|campo|trabajar|labrar|transport*|tirar"), ("¿quién usa un tractor?", "agricultor*|granjero*"),
   ("¿para qué sirve una cafetera?", "cafe"), ("¿dónde suele estar una cafetera?", "cocina"), ("¿para qué sirve una vitrocerámica?", "cocinar|calentar"),
   ("¿para qué sirven las damas?", "jugar"), ("¿de qué está hecho un top?", "tela|algodon|tejido"), ("¿para qué sirve un catamarán?", "navegar|viajar|transport*"),
   ("¿para qué sirve el champú?", "lavar*|pelo"), ("¿dónde suele estar el champú?", "baño|ducha"), ("¿para qué sirve una batidora?", "batir|triturar|mezclar"),
   ("¿para qué sirve una hoz?", "segar|cortar|trabajar"), ("¿quién usa una hoz?", "agricultor*|campesino*|segador*"), ("¿para qué sirve un bolígrafo?", "escribir"),
   ("¿con qué se bate?", "batidor*"), ("¿qué sirve para hacer café?", "cafetera*"), ("¿una batidora sirve para escribir?", "^no"), ("¿un bolígrafo sirve para escribir?", "^si"),
   ("¿un tractor sirve para navegar?", "^no|ABST"), ("¿para qué sirve un trofeo?", "ABST|premi*|reconoc*|recuerdo|ganador*")]},
 {"id": "c15b-cha", "cat": "relaciones_charla", "turnos": [
   ("hola", "hola"), ("tengo una hoz y una piragua", "hoz|piragua;!no lo he entendido"), ("¿tengo algo para navegar?", "^si|piragua"), ("¿tengo algo para escribir?", "^no|ABST"),
   ("¿tengo una herramienta?", "^si"), ("¿tengo un vehículo?", "^si|barco|ABST")]},
 {"id": "c15b-per", "cat": "personas", "turnos": [
   ("hola", "hola"), ("mi cuñada Elena es veterinaria", "veterinaria;!no lo he entendido"), ("¿Elena es una persona?", "^si"), ("¿Elena es una profesional?", "^si"),
   ("¿Elena trabaja?", "^si"), ("¿Elena cura animales?", "^si"), ("¿Elena es un edificio?", "^no"), ("mi sobrino es boxeador", "boxeador;!no lo he entendido"),
   ("¿mi sobrino es un deportista?", "^si"), ("¿quién es boxeador?", "sobrino"), ("mi vecina es piloto", "piloto;!no lo he entendido"), ("¿mi vecina pilota aviones?", "^si"),
   ("¿quién es piloto?", "vecina")]},
 {"id": "c15b-her", "cat": "herencia_charla", "turnos": [
   ("hola", "hola"), ("tengo un erizo y una alpaca", "erizo|alpaca;!no lo he entendido"), ("¿tengo un mamífero?", "^si"), ("¿tengo un ave?", "^no|ABST"), ("¿mi erizo es un ser vivo?", "^si"),
   ("¿qué animales tengo?", "erizo;alpaca"), ("me he comprado un poncho y un sombrero", "poncho|sombrero;!no lo he entendido"), ("¿me he comprado ropa?", "^si"),
   ("¿qué prenda me he comprado?", "poncho|sombrero"), ("ayer comí coliflor y una pera", "coliflor|pera;!no lo he entendido"), ("¿comí verdura ayer?", "^si"), ("¿qué fruta comí?", "pera"),
   ("¿comí pescado ayer?", "^no|ABST")]},
 {"id": "c15b-fab", "cat": "fabrica_y_dicho", "turnos": [
   ("hola", "hola"), ("mi pinzón no canta", "canta;!no lo he entendido"), ("¿mi pinzón canta?", "^no"), ("¿los pinzones cantan?", "^si"), ("Olga sabe pilotar", "olga;!no lo he entendido"),
   ("¿quién sabe pilotar?", "olga"), ("mi erizo tiene tres patas", "tres|3;!no lo he entendido"), ("¿cuántas patas tiene mi erizo?", "tres|3")]},
 {"id": "c15b-cla", "cat": "clases", "turnos": [
   ("hola", "hola"), ("¿una gacela es un mamífero?", "^si"), ("¿un dromedario es un ave?", "^no"), ("¿una catedral es un edificio?", "^si"), ("¿un rascacielos es un lugar?", "^si"),
   ("¿la bechamel es un alimento?", "^si"), ("¿el regaliz es un objeto?", "^no"), ("¿una droguería es un animal?", "^no"), ("¿un chándal es ropa?", "^si"),
   ("¿una lechuga es una verdura?", "^si"), ("¿un albergue es una persona?", "^no")]},
]


def medir(verboso=False, salida="lab/res_ciego15b.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    f, r = medir()
    imprime(r, "EXAMEN CIEGO 15b (muestra limpia)")
