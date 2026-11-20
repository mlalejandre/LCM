"""APRENDER · primera MEDIDA LIMPIA de la 2.19. Escrito con el código congelado; se mide UNA vez en cada versión. Mismo formato que dev.py."""
N = "!no lo he entendido;!no he entendido"
K_ = "pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*"

PINGUINOS = {"nombre": "pingüinos", "intro": "Te voy a leer un texto sobre los pingüinos.", "frases": [
 ("Los pingüinos son aves que no pueden volar.", [("L", "¿los pingüinos pueden volar?", "^no"), ("V", "¿qué son los pingüinos?", "ave*")]),
 ("Usan sus alas como aletas para nadar bajo el agua.", [("L", "¿para qué usan sus alas los pingüinos?", "nadar")]),
 ("Casi todos viven en el hemisferio sur, sobre todo en la Antártida.", [("L", "¿dónde viven los pingüinos?", "sur|antartida")]),
 ("Se alimentan de peces, calamares y pequeños crustáceos.", [("P", "¿qué comen los pingüinos?", "peces|calamares|crustaceos")]),
 ("Una gruesa capa de grasa los protege del frío.", [("D", "¿qué protege a los pingüinos del frío?", "grasa")]),
 ("En tierra caminan despacio, pero en el agua son muy rápidos.", [("L", "¿cómo son los pingüinos en el agua?", "rapidos")]),
 ("El pingüino emperador es el pingüino más grande que existe.", [("I", "¿cuál es el pingüino más grande?", "emperador")]),
 ("Mide más de un metro y pesa unos cuarenta kilos.", [("L", "¿cuánto pesa el pingüino emperador?", "cuarenta|40")]),
 ("La hembra pone un solo huevo y el macho lo cuida durante dos meses.", [("L", "¿quién cuida el huevo?", "macho"), ("L", "¿cuántos huevos pone la hembra?", "un|1")]),
 ("Durante ese tiempo el macho no come nada.", []),
 ("Los pingüinos viven en grupos muy grandes llamados colonias.", [("V", "¿qué es una colonia?", "grupo*")]),
 ("Cuando hace mucho frío, se juntan todos para darse calor.", [("D", "¿qué hacen los pingüinos cuando hace mucho frío?", "juntan|calor")]),
 ("Las crías nacen cubiertas de un plumón gris.", [("L", "¿de qué color es el plumón de las crías?", "gris")]),
 ("Su peor enemigo en el mar es la foca leopardo.", [("I", "¿cuál es el peor enemigo de los pingüinos en el mar?", "foca")]),
 ("El pingüino de las Galápagos es el único que vive cerca del ecuador.", [("I", "¿qué pingüino vive cerca del ecuador?", "galapagos")]),
 ("Las personas que estudian las aves se llaman ornitólogos.", [("I", "¿cómo se llaman las personas que estudian las aves?", "ornitologo*")]),
], "extra": [
 ("H", "¿un pingüino es un animal?", "^si"), ("H", "¿el pingüino emperador es un ave?", "^si"), ("H", "¿un pingüino es un pez?", "^no"),
 ("M", "¿cuánto pesa el pingüino más grande?", "cuarenta|40"), ("D", "¿el pingüino emperador puede volar?", "^no"),
 ("N", "¿cuántos pingüinos hay en la Antártida?", "ABST"), ("N", "¿cuánto vive un pingüino?", "ABST"), ("N", "¿quién descubrió la Antártida?", "ABST"),
 ("C", "mi hermana es ornitóloga", N), ("C", "¿mi hermana estudia las aves?", "^si|estudia*"),
 ("G", "dime un pingüino", "emperador|galapagos"), ("G", "descríbeme el pingüino emperador", "grande|metro|kilos|pingüino|pinguino"),
 ("K", "los pingüinos pueden volar", K_ + "|no pueden"),
]}

PAN = {"nombre": "el pan", "intro": "Te voy a leer un texto sobre el pan.", "frases": [
 ("El pan se hace con harina, agua, sal y levadura.", [("L", "¿con qué se hace el pan?", "harina;agua")]),
 ("La harina es el polvo que se obtiene al moler el trigo.", [("V", "¿qué es la harina?", "polvo")]),
 ("Primero se mezclan los ingredientes hasta formar una masa.", []),
 ("Después la masa se deja reposar unas horas.", [("L", "¿cuánto se deja reposar la masa?", "horas")]),
 ("Durante el reposo la levadura produce gas, y por eso la masa crece.", [("D", "¿por qué crece la masa?", "levadura|gas")]),
 ("Este proceso se llama fermentación.", [("V", "¿qué es la fermentación?", "levadura|gas|masa|proceso")]),
 ("Por último la masa se cuece en un horno muy caliente.", [("L", "¿dónde se cuece la masa?", "horno")]),
 ("La parte de fuera del pan se llama corteza y la de dentro se llama miga.", [("I", "¿cómo se llama la parte de fuera del pan?", "corteza")]),
 ("La corteza es dura y crujiente, mientras que la miga es blanda.", [("L", "¿cómo es la miga?", "blanda"), ("L", "¿cómo es la corteza?", "dura|crujiente")]),
 ("El pan integral se hace con el grano entero y tiene más fibra.", [("L", "¿con qué se hace el pan integral?", "grano")]),
 ("El pan de molde es blando y se vende cortado en rebanadas.", [("L", "¿cómo se vende el pan de molde?", "rebanadas|cortado")]),
 ("La baguette es una barra de pan larga y fina, típica de Francia.", [("V", "¿qué es una baguette?", "barra|pan"), ("L", "¿de dónde es típica la baguette?", "francia")]),
 ("El pan duro no se tira: sirve para hacer torrijas y sopas.", [("L", "¿para qué sirve el pan duro?", "torrijas|sopas")]),
 ("Las personas que hacen pan se llaman panaderos.", [("I", "¿cómo se llaman las personas que hacen pan?", "panadero*")]),
 ("Un panadero empieza a trabajar de madrugada para que el pan esté listo por la mañana.", [("L", "¿cuándo empieza a trabajar un panadero?", "madrugada")]),
], "extra": [
 ("H", "¿el pan es un alimento?", "^si"), ("H", "¿la baguette es un pan?", "^si"), ("H", "¿un panadero es una persona?", "^si"),
 ("P", "¿qué elabora un panadero?", "pan"), ("D", "¿el pan integral tiene fibra?", "^si"), ("M", "¿cómo es la parte de dentro del pan?", "blanda"),
 ("N", "¿cuánto cuesta una barra de pan?", "ABST"), ("N", "¿quién inventó el pan?", "ABST"), ("N", "¿cuántos panaderos hay en Francia?", "ABST"),
 ("C", "mi padre era panadero", N), ("C", "¿mi padre hacía pan?", "^si|hacia|pan"),
 ("G", "dime dos tipos de pan", "integral|molde|baguette"), ("G", "descríbeme la corteza", "dura|crujiente|fuera"),
 ("K", "la miga es dura", K_ + "|blanda"),
]}

TEMAS = [PINGUINOS, PAN]
