"""EXAMEN CIEGO 11: conectores lógicos (y/e, ni… ni, tanto… como, o/o… o, más/menos… que, tan… como, superlativo,
condicionales con «si» e hipótesis, enumeraciones con coma). Escrito con la 2.10 congelada; no se lee hasta la medida final.
Fecha de las pruebas: 19-11-2026."""
from lab.banco import correr, imprime
D = [
 {"id": "c11-cop", "cat": "copulativas", "turnos": [
   ("hola", "hola"), ("mi tío Jorge e Inés están casados", "jorge|ines;!no lo he entendido"), ("¿con quién está casado Jorge?", "ines"),
   ("Inés no come ni carne ni pescado", "carne|pescado;!no lo he entendido"), ("¿Inés come pescado?", "^no"), ("¿Inés come carne?", "^no"),
   ("tanto Jorge como Inés trabajan en un banco", "banco;!no lo he entendido"), ("¿dónde trabaja Inés?", "banco"),
   ("Jorge habla inglés y francés", "ingles|frances;!no lo he entendido"), ("¿Jorge habla francés?", "^si"), ("¿Jorge habla alemán?", "ABST|^no")]},
 {"id": "c11-dis", "cat": "disyuntivas", "turnos": [
   ("buenas", "hola|buenas"), ("la reunión es el martes o el miércoles", "martes|miercoles;!no lo he entendido"),
   ("¿cuándo es la reunión?", "martes;miercoles"), ("¿la reunión es el martes?", "miercoles"), ("al final no es el martes", "martes|miercoles|reunion;!no lo he entendido"),
   ("¿cuándo es la reunión?", "miercoles;!no lo s*"), ("o voy en tren o voy en autobús", "tren|autobus;!no lo he entendido"),
   ("¿cómo voy?", "tren;autobus"), ("¿voy en coche?", "^no|ABST")]},
 {"id": "c11-comp", "cat": "comparativas", "turnos": [
   ("hola", "hola"), ("Marta es mayor que Raúl", "marta|raul;!no lo he entendido"), ("Raúl es mayor que Teo", "raul|teo;!no lo he entendido"),
   ("¿quién es el mayor?", "marta"), ("¿quién es el menor?", "teo"), ("¿Teo es mayor que Marta?", "^no"),
   ("Raúl corre más rápido que Marta", "raul|marta;!no lo he entendido"), ("¿quién corre más rápido, Marta o Raúl?", "raul"),
   ("mi coche es menos caro que el de Raúl", "coche;!no lo he entendido"), ("¿el coche de Raúl es más caro que el mío?", "^si"),
   ("Teo es tan simpático como Marta", "teo|marta;!no lo he entendido"), ("¿Marta es menos simpática que Teo?", "^no|igual|tan")]},
 {"id": "c11-si", "cat": "condicionales", "turnos": [
   ("hola", "hola"), ("nací el 10 de enero de 2000", "2000;!no lo he entendido"), ("¿qué edad tengo?", "26"),
   ("si hubiera nacido en 1998, ¿qué edad tendría?", "28"), ("¿qué edad tengo?", "26;!28"),
   ("si mañana hace sol, iré a correr", "sol|correr;!no lo he entendido"), ("mañana hace sol", "ANY"), ("¿qué haré mañana?", "correr"),
   ("¿cuántos años tendré en 2030?", "30")]},
 {"id": "c11-coma", "cat": "comas", "turnos": [
   ("hola", "hola"), ("en mi clase hay alumnos de Perú, Chile, Cuba y Bolivia", "peru|chile|cuba|bolivia;!no lo he entendido"),
   ("¿hay alumnos de Cuba?", "^si"), ("¿hay alumnos de México?", "ABST|^no")]},
]


def medir(verboso=False, salida="lab/res_ciego11.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    f, r = medir()
    imprime(r, "EXAMEN CIEGO 11")
