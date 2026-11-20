"""APRENDER 18 · ¿Cómo aprende el LCM un tema nuevo y cómo lo integra?

Escrito ANTES de ejecutar nada (texto, conversación y criterios congelados en el commit que añade este archivo).
Tema: los hongos y las setas. La base de fábrica solo sabe «seta -> hongo -> ser vivo» y «hongo -> ser vivo».

Condiciones (misma conversación en todas):
  base     sin texto: lo que sabe de fábrica
  texto    el texto pegado de una vez («Te voy a leer un texto…»)
  frases   el mismo texto dicho frase a frase en la charla
  escuela  el texto como cartilla de la escuela (conocimiento de fábrica), sesión nueva

Tipos de pregunta:
  L literal · P paráfrasis · I inversa · H herencia (integra con lo que ya sabía) · D deducción
  C charla (hechos de la persona + lo aprendido) · G uso (generar con lo aprendido) · N no dicho (debe abstenerse)
  K contradicción · R retención tras otra charla · V vocabulario · M combinar dos frases
"""
import json, os, sys

TEXTO = """Te voy a leer un texto sobre las setas.
Los hongos no son plantas ni animales: forman un reino propio.
A diferencia de las plantas, los hongos no tienen clorofila y no pueden fabricar su propio alimento.
Se alimentan de restos de otros seres vivos, como hojas muertas y madera podrida.
La parte más importante de un hongo es el micelio, una red de hilos muy finos que crece bajo la tierra.
La seta es solo el fruto del hongo, igual que una manzana es el fruto del manzano.
Una seta tiene tres partes: el sombrero, el pie y las láminas.
Las láminas están debajo del sombrero.
En las láminas se forman las esporas.
Las esporas son como semillas diminutas y el viento las lleva muy lejos.
Cuando una espora cae en un sitio húmedo, nace un nuevo micelio.
Las setas salen sobre todo en otoño, después de las lluvias.
Necesitan humedad y sombra, por eso abundan en los bosques.
Algunas setas son comestibles y otras son venenosas.
El boletus es una seta comestible muy apreciada en la cocina.
Tiene el sombrero marrón y el pie grueso.
La amanita faloides es la seta más venenosa que existe.
Su veneno destruye el hígado y puede causar la muerte.
Es de color verde pálido y a veces se confunde con setas comestibles.
Por eso nunca hay que comer una seta si no se conoce bien.
La trufa es un hongo que crece bajo tierra, junto a las raíces de las encinas.
Es negra, tiene forma de bola y huele muy fuerte.
Para encontrarla se usan perros entrenados.
La trufa es uno de los alimentos más caros del mundo.
La levadura también es un hongo, aunque es tan pequeña que no se ve a simple vista.
Sirve para hacer pan y cerveza.
El moho que aparece en el pan viejo es otro hongo.
Gracias al moho se descubrió la penicilina, un medicamento que cura infecciones.
Las personas que estudian los hongos se llaman micólogos.
Las que salen al monte a recoger setas se llaman seteros.
Un buen setero lleva una cesta de mimbre para que las esporas caigan al suelo mientras camina.
Nunca usa bolsas de plástico, porque las setas se estropean.
Los hongos son muy importantes para el bosque, porque descomponen la materia muerta y devuelven los nutrientes a la tierra."""

N = "!no lo he entendido;!no he entendido"
# (tipo, frase, criterio). Criterio vacío = turno de charla sin nota.
CONV = [
 ("-", "hola, soy Marcos", ""),
 ("-", "hoy quiero aprender cosas sobre las setas", ""),
 ("V", "¿qué es el micelio?", "red|hilos"),
 ("L", "¿qué partes tiene una seta?", "sombrero;pie;laminas"),
 ("L", "¿dónde se forman las esporas?", "laminas"),
 ("P", "¿los hongos son plantas?", "^no"),
 ("P", "¿pueden los hongos fabricar su propia comida?", "^no"),
 ("L", "¿de qué se alimentan los hongos?", "restos|hojas|madera"),
 ("L", "¿cuándo salen las setas?", "otono"),
 ("P", "¿qué necesitan las setas para salir?", "humedad|sombra|lluvia*"),
 ("D", "¿por qué abundan las setas en los bosques?", "humedad|sombra"),
 ("D", "¿qué pasa cuando una espora cae en un sitio húmedo?", "micelio"),
 ("I", "¿qué seta es la más venenosa?", "amanita"),
 ("M", "¿de qué color es la seta más venenosa?", "verde"),
 ("P", "¿qué le pasa a quien se come una amanita faloides?", "higado|muerte|morir|muere"),
 ("D", "¿se puede comer la amanita faloides?", "^no"),
 ("D", "¿el boletus es comestible?", "^si"),
 ("I", "¿qué seta tiene el sombrero marrón?", "boletus"),
 ("H", "¿el boletus es una seta?", "^si"),
 ("H", "¿el boletus tiene pie?", "^si"),
 ("H", "¿la trufa es un ser vivo?", "^si"),
 ("H", "¿la trufa es un alimento?", "^si"),
 ("V", "¿qué es una trufa?", "hongo"),
 ("L", "¿de qué color es la trufa?", "negra"),
 ("I", "¿qué hongo crece junto a las encinas?", "trufa"),
 ("P", "¿cómo se encuentra una trufa?", "perro*"),
 ("I", "¿qué hongo encuentran los perros?", "trufa"),
 ("P", "¿es cara la trufa?", "^si|cara*|caro*"),
 ("M", "¿dónde crece el alimento más caro del mundo?", "encina*|bajo tierra"),
 ("H", "¿la levadura es un hongo?", "^si"),
 ("I", "¿qué hongo sirve para hacer pan?", "levadura"),
 ("L", "¿para qué sirve la levadura?", "pan|cerveza"),
 ("H", "¿el moho es un animal?", "^no"),
 ("L", "¿qué se descubrió gracias al moho?", "penicilina"),
 ("V", "¿qué es la penicilina?", "medicamento"),
 ("I", "¿cómo se llaman las personas que recogen setas?", "setero*"),
 ("V", "¿qué es un micólogo?", "persona*|estudia*"),
 ("D", "¿por qué no hay que llevar bolsas de plástico?", "estropea*"),
 ("D", "¿por qué son importantes los hongos para el bosque?", "descompon*|nutrientes"),
 ("D", "¿una amanita tiene esporas?", "^si"),
 ("N", "¿cuántas especies de hongos hay?", "ABST"),
 ("N", "¿cuánto cuesta un kilo de trufa?", "ABST"),
 ("N", "¿quién descubrió la penicilina?", "ABST"),
 ("N", "¿de qué color es el pie de la amanita?", "ABST"),
 ("C", "ayer encontré un boletus en el monte", N),
 ("C", "¿me lo puedo comer?", "^si|comestible"),
 ("C", "mi vecino ha cogido una amanita faloides", N),
 ("C", "¿es peligrosa la seta de mi vecino?", "^si|venenos*|peligros*"),
 ("C", "quiero salir a buscar setas, ¿qué me llevo?", "cesta"),
 ("C", "¿en qué época del año salgo a buscarlas?", "otono"),
 ("G", "dime una seta comestible", "boletus"),
 ("G", "dime una seta venenosa", "amanita"),
 ("G", "dime tres hongos", "trufa|levadura|moho|boletus|amanita"),
 ("G", "descríbeme una trufa", "negra|bola|huele|olor|tierra|encina*"),
 ("G", "invéntate una adivinanza sobre la trufa", "negra|bola|huel*|tierra|encina*"),
 ("K", "la amanita faloides se puede comer", "venenos*|no se puede|contradic*|pero|segun|texto"),
 ("K", "¿se puede comer la amanita faloides?", "^no|texto|segun|pero"),
 ("-", "cambiando de tema, mi hermana se llama Lucía", ""),
 ("-", "¿cuánto es 7 por 6?", "42"),
 ("-", "mañana tengo una reunión", ""),
 ("-", "Lucía vive en Burgos", ""),
 ("-", "¿dónde vive Lucía?", "burgos"),
 ("R", "volviendo a las setas, ¿qué es una trufa?", "hongo"),
 ("R", "¿dónde se forman las esporas?", "laminas"),
 ("R", "¿qué seta es la más venenosa?", "amanita"),
 ("R", "¿para qué sirve la levadura?", "pan|cerveza"),
]


def dialogo(cond):
    turnos = []
    if cond == "texto":
        turnos.append((TEXTO, ""))
    elif cond == "frases":
        for f in TEXTO.split("\n")[1:]:
            turnos.append((f, ""))
    turnos += [(f, c) for _, f, c in CONV]
    return [{"id": "aprender-" + cond, "cat": "aprender", "turnos": turnos}]


def tipos():
    return {f: t for t, f, _ in CONV}


def main():
    from lab.banco import correr, imprime
    cond = sys.argv[1] if len(sys.argv) > 1 else "texto"
    f, r = correr(dialogo(cond), verboso=True, salida=f"lab/res_aprender18_{cond}.json")
    imprime(r, f"APRENDER 18 · condición {cond}")


if __name__ == "__main__":
    main()
