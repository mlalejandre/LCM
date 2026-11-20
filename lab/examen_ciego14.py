"""EXAMEN CIEGO 14 · CONCEPTOS (ronda 2.14). Escrito con la 2.13 congelada, ANTES de añadir ningún concepto; no se lee hasta la medida final.
Muestras al azar (semilla 2114), con regla mecánica, de:
  A · 40 sustantivos del corpus UD (frecuencia ≥3, entre los 1500 primeros) que la base 2.13 no conoce y están en el léxico MCR
  B · 25 adjetivos (frec. ≥5) y 10 verbos (frec. ≥10) de UD que tienen antónimo en MCR
  C · 12 todos concretos frecuentes que la base clasifica (objeto, lugar, vehículo…) sin partes anotadas
  D · 18 clases de la base sin propiedades anotadas
  E · una charla que usa conceptos (herencia, contrarios, partes)
Criterios: categorías/contrarios aceptables escritos ahora. «ABST» = no hay respuesta sensata y abstenerse es correcto.
Las preguntas de «no» no se aprueban con «No lo sé» (el corrector exige la respuesta).
"""
from lab.banco import correr, imprime

A = [("¿un asesinato es un delito?", "^si"), ("¿un asesinato es un objeto?", "^no"), ("¿una mejora es un animal?", "^no"),
     ("¿una compañera es una persona?", "^si"), ("¿una creencia es una idea?", "^si"), ("¿una creencia es un objeto?", "^no"),
     ("¿el matrimonio es un objeto?", "^no"), ("¿qué es el matrimonio?", "union|relacion|pareja|sacramento|institucion|vinculo|casamiento|boda|contrato"),
     ("¿una adquisición es un ser vivo?", "^no"), ("¿un novio es una persona?", "^si"), ("¿un tiro es un animal?", "^no"),
     ("¿qué es un tiro?", "disparo|lanzamiento|golpe"), ("¿la seguridad es un objeto?", "^no"), ("¿una reserva es una persona?", "^no"),
     ("¿un pasajero es una persona?", "^si"), ("¿un pasajero es un vehículo?", "^no"), ("¿un insulto es una ofensa?", "^si"),
     ("¿un concejal es una persona?", "^si"), ("¿qué es un concejal?", "persona|cargo|politico|miembro|representante|ayuntamiento"),
     ("¿un avance es un animal?", "^no"), ("¿una nación es un ser vivo?", "^no"), ("¿qué es una nación?", "pais|estado|pueblo|comunidad|territorio"),
     ("¿un trato es un acuerdo?", "^si"), ("¿un símbolo es un ser vivo?", "^no"), ("¿qué es un símbolo?", "signo|señal|representacion|imagen|figura"),
     ("¿la luna es un ser vivo?", "^no"), ("¿qué es la luna?", "satelite|astro|cuerpo celeste"), ("¿un juego es un animal?", "^no"),
     ("¿qué es un juego?", "actividad|entretenimiento|diversion|pasatiempo"), ("¿un respaldo es una persona?", "^no"), ("¿el origen es un objeto?", "^no"),
     ("¿un capítulo es parte de un libro?", "^si"), ("¿un capítulo es un ser vivo?", "^no"), ("¿una sigla es un animal?", "^no"),
     ("¿un recuerdo es un animal?", "^no"), ("¿la determinación es un objeto?", "^no"), ("¿una pérdida es un ser vivo?", "^no"),
     ("¿la razón es un objeto?", "^no"), ("¿una órbita es un animal?", "^no"), ("¿qué es una órbita?", "trayectoria|camino|recorrido"),
     ("¿un ministro es una persona?", "^si"), ("¿qué es un ministro?", "persona|cargo|politico|miembro del gobierno|gobierno"),
     ("¿una fuga es un objeto?", "^no"), ("¿una parroquia es un ser vivo?", "^no"), ("¿qué es una parroquia?", "iglesia|comunidad|territorio|templo|lugar"),
     ("¿la pobreza es un objeto?", "^no"), ("¿un agente es una persona?", "^si"), ("¿un triunfo es un éxito?", "^si"),
     ("¿un judío es una persona?", "^si"), ("¿una nacionalidad es un animal?", "^no"), ("¿un testimonio es un objeto?", "^no"),
     ("¿qué es un testimonio?", "declaracion|prueba|evidencia"), ("¿una investigación es un ser vivo?", "^no"),
     ("¿qué es una investigación?", "estudio|trabajo|busqueda|indagacion|actividad|proceso"), ("¿qué es una hoja?", "parte|papel|lamina|planta|pagina|organo"),
     ("¿el destino es una persona?", "^no")]
B = [("¿qué es lo contrario de triste?", "alegre|contento|feliz"), ("¿cuál es el contrario de mejor?", "peor"), ("¿qué es lo contrario de barato?", "caro|costoso"),
     ("dime lo opuesto de poderoso", "debil|impotente|flojo"), ("¿qué es lo contrario de médico?", "ABST"), ("¿qué es lo contrario de máximo?", "minimo"),
     ("¿qué es lo contrario de sencillo?", "complicado|complejo|dificil|elaborado|sofisticado"), ("¿qué es lo contrario de orgulloso?", "humilde|avergonzado"),
     ("¿qué es lo contrario de operativo?", "inoperativo|inoperante|ABST"), ("¿cuál es el contrario de futuro?", "pasado|presente"),
     ("¿qué es lo contrario de suave?", "duro|aspero|fuerte|rugoso|brusco"), ("¿qué es lo contrario de temporal?", "permanente|fijo|estable|definitivo|eterno"),
     ("¿qué es lo contrario de horizontal?", "vertical"), ("¿qué es lo contrario de previo?", "posterior|siguiente|ulterior"),
     ("dime lo contrario de extenso", "breve|corto|reducido|pequeño|limitado"), ("¿qué es lo contrario de artificial?", "natural"),
     ("¿qué es lo contrario de adecuado?", "inadecuado|inapropiado"), ("¿qué es lo contrario de atento?", "distraido|despistado|descuidado|desatento"),
     ("¿qué es lo contrario de lleno?", "vacio"), ("¿cuál es el opuesto de positivo?", "negativo"),
     ("¿qué es lo contrario de satisfecho?", "insatisfecho|disgustado|descontento"), ("¿qué es lo contrario de grande?", "pequeño|chico"),
     ("¿qué es lo contrario de desconocido?", "conocido|famoso|familiar"), ("¿qué es lo contrario de importante?", "insignificante|irrelevante|secundario"),
     ("¿qué es lo contrario de perfecto?", "imperfecto|defectuoso"),
     ("¿qué es lo contrario de ir?", "venir|volver|quedarse|llegar"), ("¿qué es lo contrario de unir?", "separar|desunir|dividir"),
     ("¿qué es lo contrario de pasar?", "ABST|suspender|quedarse|parar"), ("¿qué es lo contrario de eliminar?", "crear|añadir|incluir|establecer|anadir|poner|mantener"),
     ("¿qué es lo contrario de fundar?", "cerrar|disolver|abolir|eliminar|destruir"), ("¿qué es lo contrario de separar?", "unir|juntar"),
     ("¿qué es lo contrario de levantar?", "bajar|acostar|tumbar|sentar|derribar"), ("¿qué es lo contrario de colaborar?", "ABST|rechazar|resistir|obstaculizar|oponer*|entorpecer"),
     ("¿qué es lo contrario de devolver?", "ABST|quedarse|prestar|pedir|tomar|coger|quitar"), ("¿qué es lo contrario de guardar?", "perder|tirar|sacar|gastar")]
C = [("¿qué partes tiene una mesa?", "patas|tablero|superficie|pata"), ("¿qué partes tiene una caja?", "tapa|fondo|lados|paredes|base"),
     ("¿qué partes tiene una habitación?", "paredes|puerta|ventana|techo|suelo"), ("¿qué partes tiene un barrio?", "calles|casas|plazas|edificios"),
     ("¿qué partes tiene una región?", "ABST|provincias|pueblos|ciudades|municipios|comarcas"), ("¿de qué partes se compone un vehículo?", "ruedas|motor|puertas|asientos"),
     ("¿qué partes tiene una puerta?", "pomo|picaporte|manilla|bisagras|cerradura|marco|hoja"), ("¿qué partes tiene una montaña?", "cima|cumbre|ladera|falda|pico|base"),
     ("¿qué partes tiene una entrada?", "ABST|puerta|recibidor"), ("¿qué partes tiene un contrato?", "ABST|clausulas|firma|partes"),
     ("¿qué partes tiene una fábrica?", "maquinas|naves|almacen|oficinas|maquinaria|taller"), ("¿qué partes tiene una medalla?", "ABST|cinta|anverso|reverso")]
Dp = [("¿una hiena es un animal salvaje?", "^si"), ("¿las hienas vuelan?", "^no"), ("¿el tenedor sirve para comer?", "^si|para comer|pinchar"),
      ("¿un tenedor tiene púas?", "^si|dientes"), ("¿un galápago tiene caparazón?", "^si"), ("¿los galápagos tienen plumas?", "^no"),
      ("¿un girasol necesita sol?", "^si|luz"), ("¿un girasol tiene pétalos?", "^si"), ("¿un estadio es un edificio?", "^si|recinto|instalacion"),
      ("¿en un estadio se hacen partidos?", "^si"), ("¿un banjo es un instrumento?", "^si"), ("¿un banjo tiene cuerdas?", "^si"),
      ("¿un contenedor sirve para guardar cosas?", "^si|basura|guardar"), ("¿el suavizante se usa para lavar la ropa?", "^si|ropa|lavar"),
      ("¿un banquero trabaja en un banco?", "^si|banco"), ("¿los científicos investigan?", "^si"), ("¿una ensaladera es un recipiente?", "^si|recipiente|cuenco"),
      ("¿el estómago sirve para digerir?", "^si|digerir|digestion"), ("¿una riñonera se lleva en la cintura?", "^si|cintura"),
      ("¿un matadero es un lugar?", "^si"), ("¿el gris es un color?", "^si"), ("¿un gallinero es para las gallinas?", "^si|gallina*"),
      ("¿una americana es una prenda?", "^si")]
E = [("hola", "hola"), ("tengo un loro", "loro;!no lo he entendido"), ("¿tengo un pájaro?", "^si"), ("¿mi loro tiene plumas?", "^si"),
     ("me he comprado unos vaqueros", "vaqueros;!no lo he entendido"), ("¿me he comprado ropa?", "^si|prenda"),
     ("he comprado un sofá", "sofa;!no lo he entendido"), ("¿he comprado un mueble?", "^si"),
     ("mi coche es viejo", "viejo;!no lo he entendido"), ("¿mi coche es nuevo?", "^no"), ("la sopa está fría", "fria;!no lo he entendido"),
     ("¿la sopa está caliente?", "^no"), ("el examen fue fácil", "facil;!no lo he entendido"), ("¿el examen fue difícil?", "^no"),
     ("mi novia es enfermera", "enfermera;!no lo he entendido"), ("¿a qué se dedica mi novia?", "enfermera"), ("¿mi novia es una persona?", "^si")]

D = [{"id": "c14-A", "cat": "A_jerarquia", "turnos": [(q, c + ";!no conozco") for q, c in A]},
     {"id": "c14-B", "cat": "B_contrarios", "turnos": B},
     {"id": "c14-C", "cat": "C_partes", "turnos": C},
     {"id": "c14-D", "cat": "D_propiedades", "turnos": Dp},
     {"id": "c14-E", "cat": "E_charla", "turnos": E}]


def medir(verboso=False, salida="lab/res_ciego14.json"):
    return correr(D, verboso=verboso, salida=salida)


if __name__ == "__main__":
    f, r = medir()
    imprime(r, "EXAMEN CIEGO 14 (conceptos)")
