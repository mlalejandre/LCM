"""APRENDER · temas de MEDIDA LIMPIA (2.18). Escritos con el código congelado; se miden UNA vez. Mismo formato que dev.py.
Textos normales de divulgación, sin adaptar. Uno de los temas es inventado, para que el diccionario no pueda ayudar."""
N = "!no lo he entendido;!no he entendido"
K_ = "pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*"

MURCIELAGOS = {"nombre": "murciélagos", "intro": "Te voy a leer un texto sobre los murciélagos.", "frases": [
 ("Los murciélagos son los únicos mamíferos que pueden volar.", [("L", "¿los murciélagos pueden volar?", "^si")]),
 ("Sus alas son en realidad manos con dedos muy largos, unidos por una piel fina.", [("L", "¿cómo son las alas de los murciélagos?", "manos|dedos|piel")]),
 ("Duermen de día, colgados boca abajo en cuevas y árboles huecos.", [("L", "¿dónde duermen los murciélagos?", "cueva*|arbol*"), ("L", "¿cuándo duermen los murciélagos?", "dia")]),
 ("Salen a cazar por la noche.", [("L", "¿cuándo salen a cazar los murciélagos?", "noche")]),
 ("La mayoría de los murciélagos comen insectos, pero algunos comen fruta.", [("P", "¿de qué se alimenta la mayoría de los murciélagos?", "insecto*")]),
 ("Un solo murciélago puede comer mil mosquitos en una noche.", [("L", "¿cuántos mosquitos puede comer un murciélago en una noche?", "mil|1000")]),
 ("Para orientarse en la oscuridad emiten sonidos muy agudos y escuchan su eco.", [("D", "¿cómo se orientan los murciélagos en la oscuridad?", "sonido*|eco")]),
 ("Este sistema se llama ecolocalización.", [("V", "¿qué es la ecolocalización?", "sonido*|eco|sistema")]),
 ("Las personas no podemos oír esos sonidos.", []),
 ("En invierno, cuando no hay insectos, muchos murciélagos hibernan.", [("D", "¿qué hacen muchos murciélagos en invierno?", "hiberna*")]),
 ("Las crías nacen en primavera y se agarran a su madre durante las primeras semanas.", [("L", "¿cuándo nacen las crías?", "primavera")]),
 ("Un grupo de murciélagos se llama colonia.", [("I", "¿cómo se llama un grupo de murciélagos?", "colonia")]),
 ("El zorro volador es el murciélago más grande del mundo.", [("I", "¿cuál es el murciélago más grande del mundo?", "zorro volador")]),
 ("Sus alas abiertas miden más de un metro y medio.", [("L", "¿cuánto miden las alas del zorro volador?", "metro")]),
 ("El vampiro es un murciélago de América que se alimenta de sangre.", [("L", "¿de qué se alimenta el vampiro?", "sangre"), ("V", "¿qué es un vampiro?", "murcielago")]),
 ("Los murciélagos son muy útiles, porque se comen los insectos que dañan las cosechas.", [("D", "¿por qué son útiles los murciélagos?", "insectos|cosechas")]),
 ("Las personas que estudian los murciélagos se llaman quiropterólogos.", [("I", "¿cómo se llaman las personas que estudian los murciélagos?", "quiropterologo*")]),
 ("Algunos murciélagos viven más de treinta años.", [("L", "¿cuánto viven algunos murciélagos?", "treinta|30")]),
], "extra": [
 ("H", "¿un murciélago es un mamífero?", "^si"), ("H", "¿el vampiro es un animal?", "^si"), ("H", "¿los murciélagos son pájaros?", "^no"),
 ("M", "¿cuánto miden las alas del murciélago más grande del mundo?", "metro"), ("I", "¿qué murciélago se alimenta de sangre?", "vampiro"),
 ("D", "¿todos los murciélagos comen insectos?", "^no|mayoria|algunos"),
 ("N", "¿cuántas especies de murciélagos hay?", "ABST"), ("N", "¿cuánto pesa un murciélago?", "ABST"), ("N", "¿quién descubrió la ecolocalización?", "ABST"),
 ("C", "anoche vi un murciélago en mi jardín", N), ("C", "¿qué estaría haciendo?", "cazar|cazando|insecto*"),
 ("G", "dime un murciélago", "zorro volador|vampiro"), ("G", "descríbeme el zorro volador", "grande|metro|murcielago"),
 ("K", "los murciélagos duermen de noche", K_ + "|de dia"),
]}

CAFE = {"nombre": "café", "intro": "Te voy a leer un texto sobre el café.", "frases": [
 ("El café se hace con las semillas de una planta llamada cafeto.", [("V", "¿qué es el cafeto?", "planta")]),
 ("El cafeto es un arbusto que crece en países cálidos y lluviosos.", [("L", "¿dónde crece el cafeto?", "paises|calido*|lluvios*")]),
 ("Sus frutos son rojos y se llaman cerezas de café.", [("L", "¿de qué color son los frutos del cafeto?", "rojo*")]),
 ("Dentro de cada cereza hay dos semillas, que son los granos de café.", [("L", "¿cuántas semillas hay dentro de cada cereza?", "dos|2")]),
 ("Los granos se secan al sol durante varias semanas.", [("L", "¿dónde se secan los granos?", "sol")]),
 ("Después se tuestan en un horno, y entonces toman su color marrón y su olor.", [("D", "¿qué les pasa a los granos cuando se tuestan?", "marron|color|olor")]),
 ("Los granos tostados se muelen hasta convertirlos en polvo.", []),
 ("Para preparar la bebida se hace pasar agua caliente por el café molido.", [("P", "¿cómo se prepara la bebida?", "agua caliente|molido")]),
 ("El café contiene cafeína, una sustancia que quita el sueño.", [("V", "¿qué es la cafeína?", "sustancia|sueno"), ("L", "¿qué contiene el café?", "cafeina")]),
 ("Por eso mucha gente lo toma por la mañana.", [("D", "¿por qué toma mucha gente café por la mañana?", "sueno|cafeina")]),
 ("El café sin cafeína se llama descafeinado.", [("I", "¿cómo se llama el café sin cafeína?", "descafeinado")]),
 ("Un café solo no lleva leche.", [("L", "¿un café solo lleva leche?", "^no")]),
 ("El cortado lleva un poco de leche y el café con leche lleva mucha.", [("L", "¿qué lleva el cortado?", "leche")]),
 ("Brasil es el país que más café produce.", [("I", "¿qué país produce más café?", "brasil")]),
 ("Las personas que preparan café en las cafeterías se llaman baristas.", [("I", "¿cómo se llaman las personas que preparan café en las cafeterías?", "barista*")]),
 ("Un buen barista sabe dibujar figuras con la espuma de la leche.", [("L", "¿qué sabe dibujar un buen barista?", "figuras")]),
 ("Los médicos recomiendan no tomar más de cuatro tazas al día.", [("L", "¿cuántas tazas recomiendan los médicos como máximo?", "cuatro|4")]),
], "extra": [
 ("H", "¿el cafeto es una planta?", "^si"), ("H", "¿el cafeto es un ser vivo?", "^si"), ("H", "¿el descafeinado es un café?", "^si"),
 ("M", "¿cómo se llaman los frutos del arbusto del café?", "cereza*"), ("D", "¿el descafeinado quita el sueño?", "^no"),
 ("N", "¿quién descubrió el café?", "ABST"), ("N", "¿cuánto cuesta un kilo de café?", "ABST"), ("N", "¿cuántos baristas hay en Brasil?", "ABST"),
 ("C", "mi prima es barista", N), ("C", "¿mi prima prepara café?", "^si|prepara*"),
 ("G", "dime dos tipos de café", "solo|cortado|descafeinado|con leche"), ("G", "descríbeme el cafeto", "arbusto|planta|paises|frutos"),
 ("K", "los frutos del cafeto son azules", K_ + "|rojo*"),
]}

NURBOS = {"nombre": "nurbos (inventado)", "intro": "Te voy a leer un texto sobre los nurbos.", "frases": [
 ("Los nurbos son unos animales pequeños que viven en las montañas de Talia.", [("L", "¿dónde viven los nurbos?", "montana*|talia"), ("V", "¿qué son los nurbos?", "animal*")]),
 ("Tienen el pelo azul y una cola muy larga.", [("L", "¿de qué color tienen el pelo los nurbos?", "azul")]),
 ("Se alimentan de las hojas del árbol melco.", [("L", "¿de qué se alimentan los nurbos?", "hojas|melco")]),
 ("El melco es un árbol que solo crece cerca de los ríos.", [("L", "¿dónde crece el melco?", "rio*")]),
 ("Los nurbos viven en grupos llamados tirnas.", [("V", "¿qué es una tirna?", "grupo*")]),
 ("Cada tirna tiene una jefa, que es la hembra más vieja.", [("L", "¿quién es la jefa de una tirna?", "hembra|vieja")]),
 ("Cuando un nurbo ve un peligro, silba muy fuerte.", [("D", "¿qué hace un nurbo cuando ve un peligro?", "silba")]),
 ("Su peor enemigo es el dargo, un pájaro enorme de pico rojo.", [("V", "¿qué es un dargo?", "pajaro"), ("I", "¿cuál es el peor enemigo de los nurbos?", "dargo")]),
 ("Los nurbos duermen durante todo el invierno en madrigueras profundas.", [("L", "¿dónde duermen los nurbos en invierno?", "madriguera*")]),
 ("Las crías se llaman nurbines y nacen con el pelo blanco.", [("I", "¿cómo se llaman las crías de los nurbos?", "nurbin*"), ("L", "¿de qué color nacen los nurbines?", "blanco")]),
 ("Los habitantes de Talia creen que ver un nurbo trae buena suerte.", [("L", "¿qué creen los habitantes de Talia?", "suerte")]),
 ("Por eso está prohibido cazarlos.", [("D", "¿por qué está prohibido cazar nurbos?", "suerte")]),
 ("El nurbo dorado es el más raro de todos.", [("I", "¿cuál es el nurbo más raro?", "dorado")]),
 ("Solo vive en la cima del monte Arán.", [("L", "¿dónde vive el nurbo dorado?", "aran|cima")]),
 ("Las personas que cuidan a los nurbos se llaman nurberos.", [("I", "¿cómo se llaman las personas que cuidan a los nurbos?", "nurbero*")]),
], "extra": [
 ("H", "¿un nurbo es un animal?", "^si"), ("H", "¿un nurbo es un ser vivo?", "^si"), ("H", "¿el dargo es un animal?", "^si"), ("H", "¿el melco es una planta?", "^si"),
 ("D", "¿un nurbo tiene cola?", "^si"), ("M", "¿de qué color es el pico del peor enemigo de los nurbos?", "rojo"),
 ("N", "¿cuántos nurbos quedan?", "ABST"), ("N", "¿cuánto pesa un nurbo?", "ABST"), ("N", "¿qué come el dargo?", "ABST"),
 ("C", "mi abuelo es nurbero", N), ("C", "¿mi abuelo cuida nurbos?", "^si|cuida*"),
 ("G", "descríbeme un nurbo", "animal*|azul|cola|montana*"), ("G", "dime un enemigo de los nurbos", "dargo"),
 ("K", "los nurbos tienen el pelo verde", K_ + "|azul"),
]}

TEMAS = [MURCIELAGOS, CAFE, NURBOS]
