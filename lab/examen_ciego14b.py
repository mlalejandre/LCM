"""EXAMEN CIEGO 14b · CONCEPTOS. Escrito DESPUÉS de congelar la 2.14 (commit 5af00a1) y antes de medir ninguna versión con él.
Motivo: el ciego 14 quedó contaminado (las muestras se vieron antes de escribir los conceptos nuevos). Este se saca con OTRA semilla (2141)
y EXCLUYE toda palabra que aparezca en examen_ciego14.py, con las mismas reglas mecánicas:
  A · 40 sustantivos UD (frec. ≥3, entre los 1500 primeros) desconocidos para la base 2.13 y presentes en MCR
  B · 25 adjetivos (frec. ≥5) y 10 verbos (frec. ≥10) de UD con antónimo en MCR
  C · 12 sustantivos frecuentes (≥5) clasificados en la base 2.13 sin partes anotadas (todos)
  D · 18 miembros de la base 2.13 sin propiedades anotadas (preguntas por lo típico de su clase)
  E · una charla corta con conceptos
Criterios escritos ahora, sin haber visto ninguna respuesta. «ABST» = abstenerse es correcto (no hay respuesta sensata).
"""
from lab.banco import correr, imprime

A = [("¿una fachada es parte de un edificio?", "^si"), ("¿una fachada es un ser vivo?", "^no"), ("¿el carbono es un ser vivo?", "^no"),
     ("¿qué es el carbono?", "elemento|sustancia|quimic*"), ("¿un convento es un edificio?", "^si"), ("¿la tensión es un objeto?", "^no"),
     ("¿un gigante es un objeto?", "^no"), ("¿un dios es un objeto?", "^no"), ("¿una variación es un animal?", "^no"), ("¿una maniobra es una persona?", "^no"),
     ("¿una afición es un ser vivo?", "^no"), ("¿qué es una afición?", "gusto|actividad|pasatiempo|hobby|inclinacion|interes"),
     ("¿el malestar es un objeto?", "^no"), ("¿un aplauso es un animal?", "^no"), ("¿un efecto es una persona?", "^no"),
     ("¿qué es un efecto?", "resultado|consecuencia"), ("¿una cifra es un ser vivo?", "^no"), ("¿qué es una cifra?", "numero|signo|cantidad"),
     ("¿una pieza es un ser vivo?", "^no"), ("¿qué es una pieza?", "parte|objeto|elemento|trozo"), ("¿un domicilio es un lugar?", "^si"),
     ("¿qué es un domicilio?", "casa|vivienda|lugar|direccion|residencia"), ("¿un indio es una persona?", "^si"), ("¿un departamento es un animal?", "^no"),
     ("¿la transparencia es un objeto?", "^no"), ("¿un referéndum es un ser vivo?", "^no"), ("¿qué es un referéndum?", "votacion|consulta|evento"),
     ("¿una inscripción es un animal?", "^no"), ("¿una adhesión es una persona?", "^no"), ("¿qué es la tele?", "television|aparato|medio"),
     ("¿una mención es un objeto?", "^no"), ("¿la justicia es un objeto?", "^no"), ("¿qué es la justicia?", "cualidad|virtud|valor|principio|poder|institucion"),
     ("¿un protocolo es un animal?", "^no"), ("¿una batalla es un objeto?", "^no"), ("¿qué es una batalla?", "combate|lucha|enfrentamiento|evento|pelea"),
     ("¿la especulación es un ser vivo?", "^no"), ("¿un volante es una persona?", "^no"), ("¿qué es un volante?", "pieza|parte|objeto|rueda|mando|dispositivo"),
     ("¿un abandono es un objeto?", "^no"), ("¿una definición es un animal?", "^no"), ("¿qué es una definición?", "explicacion|texto|significado|enunciado"),
     ("¿una meta es un ser vivo?", "^no"), ("¿qué es una meta?", "objetivo|fin|final|proposito|llegada"), ("¿una subvención es una persona?", "^no"),
     ("¿la totalidad es un animal?", "^no"), ("¿un precio es un objeto?", "^no"), ("¿qué es un precio?", "valor|cantidad|dinero|coste|importe"),
     ("¿un choque es un ser vivo?", "^no"), ("¿qué es un choque?", "golpe|accidente|colision|impacto|encuentro|enfrentamiento"),
     ("¿una colección es una persona?", "^no"), ("¿qué es una colección?", "conjunto|grupo|serie"), ("¿una placa es un ser vivo?", "^no"),
     ("¿una norma es un objeto?", "^no"), ("¿qué es una norma?", "regla|ley|principio|pauta"), ("¿un cura es una persona?", "^si"),
     ("¿una cotización es un animal?", "^no")]
B = [("¿qué es lo contrario de fresco?", "rancio|podrido|caluroso|calido|pasado|seco"), ("¿qué es lo contrario de parecido?", "diferente|distinto"),
     ("¿qué es lo contrario de muerto?", "vivo"), ("¿qué es lo contrario de actual?", "futuro|pasado|antiguo"), ("¿qué es lo contrario de estrecho?", "amplio|ancho"),
     ("¿cuál es el contrario de nulo?", "valido"), ("¿qué es lo contrario de similar?", "diferente|distinto"),
     ("¿qué es lo contrario de constitucional?", "inconstitucional"), ("¿qué es lo contrario de temprano?", "tardio|tarde"),
     ("¿qué es lo contrario de semejante?", "diferente|distinto"), ("¿qué es lo contrario de evidente?", "dudoso|oculto|invisible|discreto|incierto"),
     ("dime lo contrario de ocupado", "libre|desocupado|disponible|vacio"), ("¿qué es lo contrario de ilegal?", "legal|licito|legitimo"),
     ("¿qué es lo contrario de normal?", "raro|anormal|extraordinario|excepcional|insolito"), ("¿qué es lo contrario de trasero?", "delantero"),
     ("¿qué es lo contrario de joven?", "viejo|mayor|anciano"), ("¿qué es lo contrario de definido?", "indefinido|vago|confuso|impreciso"),
     ("¿qué es lo contrario de abierto?", "cerrado"), ("¿qué es lo contrario de productivo?", "improductivo|esteril|infructuoso"),
     ("¿cuál es el opuesto de cómodo?", "incomodo"), ("¿qué es lo contrario de simple?", "complejo|complicado|elaborado|sofisticado"),
     ("¿qué es lo contrario de gran?", "pequeño|menudo"), ("¿qué es lo contrario de divertido?", "aburrido|serio|solemne"),
     ("¿qué es lo contrario de válido?", "nulo|invalido"), ("¿qué es lo contrario de excepcional?", "comun|normal|habitual|usual|corriente"),
     ("¿qué es lo contrario de abrir?", "cerrar"), ("¿qué es lo contrario de participar?", "abstenerse|abandonar|desistir|retirarse|ABST"),
     ("¿qué es lo contrario de comprar?", "vender"), ("¿qué es lo contrario de fallecer?", "nacer"),
     ("¿qué es lo contrario de seguir?", "parar|cesar|dejar|preceder|abandonar"), ("¿qué es lo contrario de ampliar?", "reducir|disminuir"),
     ("¿qué es lo contrario de impedir?", "permitir|dejar|facilitar"), ("¿qué es lo contrario de gustar?", "disgustar|desagradar|detestar|odiar"),
     ("¿qué es lo contrario de retirar?", "añadir|poner|agregar|depositar|meter|anadir"), ("¿qué es lo contrario de dar?", "quitar|tomar|recibir")]
C = [("¿qué partes tiene una operación?", "ABST|fases|pasos|etapas"), ("¿qué partes tiene la tierra?", "ABST|continentes|oceanos|corteza|nucleo|manto"),
     ("¿qué partes tiene una revista?", "paginas|portada|articulos|secciones"), ("¿qué partes tiene un empresario?", "ABST"),
     ("¿qué partes tiene la confianza?", "ABST"), ("¿qué partes tiene un compañero?", "ABST"),
     ("¿qué partes tiene un ejército?", "ABST|soldados|tropas|regimientos|unidades|divisiones"),
     ("¿qué partes tiene un restaurante?", "cocina|comedor|mesas|barra|aseos|baño|salon"), ("¿qué partes tiene un elemento?", "ABST"),
     ("¿qué partes tiene un equipo?", "ABST|jugadores|miembros"), ("¿qué partes tiene una fiesta?", "ABST|invitados|musica"),
     ("¿qué partes tiene una oficina?", "mesas|despachos|sillas|ordenadores|escritorios|mesa")]
Dp = [("¿el pan es comestible?", "^si"), ("¿el pan es un ser vivo?", "^no"), ("¿en una óptica venden gafas?", "^si|gafas"),
      ("¿una grosella es comestible?", "^si"), ("¿las grosellas crecen en plantas?", "^si"), ("¿una pradera está al aire libre?", "^si"),
      ("¿el requesón viene de la leche?", "^si"), ("¿las lentejas son comestibles?", "^si"), ("¿una fractura hace daño?", "^si"),
      ("¿una semana tiene días?", "^si|siete|7"), ("¿un batido se bebe?", "^si"), ("¿la cena es una comida?", "^si"),
      ("¿una conferencia es un evento?", "^si"), ("¿una escopeta es peligrosa?", "^si"), ("¿una escopeta sirve para atacar?", "^si|disparar|cazar"),
      ("¿un túnel es un lugar?", "^si"), ("¿la barriga es parte del cuerpo?", "^si"), ("¿un pollo tiene plumas?", "^si"),
      ("¿los pollos tienen pelo?", "^no"), ("¿el taekwondo es un deporte?", "^si"), ("¿en el taekwondo se hace ejercicio?", "^si"),
      ("¿el terror es una emoción?", "^si"), ("¿una tetera es un recipiente?", "^si|utensilio")]
E = [("hola", "hola"), ("mi primo es alcalde", "alcalde;!no lo he entendido"), ("¿mi primo es un político?", "^si"),
     ("tengo una tortuga", "tortuga;!no lo he entendido"), ("¿tengo un reptil?", "^si"), ("¿mi tortuga tiene caparazón?", "^si"),
     ("mi casa es pequeña", "pequeña;!no lo he entendido"), ("¿mi casa es grande?", "^no"),
     ("mi tía es una mujer muy alegre", "alegre;!no lo he entendido"), ("¿mi tía es triste?", "^no"), ("¿mi tía es una persona?", "^si")]

D = [{"id": "c14b-A", "cat": "A_jerarquia", "turnos": [(q, c + ";!no conozco") for q, c in A]},
     {"id": "c14b-B", "cat": "B_contrarios", "turnos": B},
     {"id": "c14b-C", "cat": "C_partes", "turnos": C},
     {"id": "c14b-D", "cat": "D_propiedades", "turnos": Dp},
     {"id": "c14b-E", "cat": "E_charla", "turnos": E}]


def medir(verboso=False, salida="lab/res_ciego14b.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    f, r = medir()
    imprime(r, "EXAMEN CIEGO 14b (conceptos, muestra limpia)")
