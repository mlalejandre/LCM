"""APRENDER · SEGUNDA MEDIDA LIMPIA de la 2.21. Escrita con el código definitivo y sin ejecutarla; se mide UNA vez en cada versión (2.20 y 2.21),
con el texto pegado y frase a frase, y no se toca nada después. Las palabras que enseña el usuario son de jerga o inventadas, para
que no estén en el léxico."""
N = "!no lo he entendido;!no he entendido"
K_ = "pero|texto|contradic*|segun|no coincide|me habias|leido|lei|aprendi*"

MERCADO = {"nombre": "el mercado", "intro": "Te voy a leer un texto sobre el mercado.", "frases": [
 ("El mercado es un lugar donde se venden alimentos frescos.", [("V", "¿qué es el mercado?", "lugar"), ("L", "¿qué se vende en el mercado?", "alimentos")]),
 ("Cada vendedor tiene un puesto.", [("L", "¿qué tiene cada vendedor?", "puesto")]),
 ("Los fruteros venden fruta y verdura.", [("L", "¿qué venden los fruteros?", "fruta|verdura")]),
 ("Los pescaderos limpian el pescado y lo cortan en rodajas.", [("L", "¿quiénes limpian el pescado?", "pescadero*")]),
 ("El pescado se pone sobre hielo para que no se estropee.", [("L", "¿sobre qué se pone el pescado?", "hielo"), ("D", "¿por qué se pone el pescado sobre hielo?", "estrope*")]),
 ("Los vendedores pesan la compra en una báscula.", [("L", "¿dónde pesan la compra los vendedores?", "bascula")]),
 ("El mercado abre muy temprano y cierra a mediodía.", [("L", "¿cuándo cierra el mercado?", "mediodia")]),
 ("Los camiones traen la mercancía de madrugada.", [("L", "¿cuándo traen la mercancía los camiones?", "madrugada")]),
 ("El mercado central es el mercado más grande de la ciudad.", [("I", "¿cuál es el mercado más grande de la ciudad?", "central")]),
 ("Tiene más de cien puestos.", [("L", "¿cuántos puestos tiene el mercado central?", "cien|100")]),
 ("La lonja es el mercado donde se vende el pescado recién llegado.", [("V", "¿qué es la lonja?", "mercado")]),
 ("Está junto al puerto.", [("L", "¿dónde está la lonja?", "puerto")]),
 ("Las personas que compran en el mercado se llaman clientes.", [("I", "¿cómo se llaman las personas que compran en el mercado?", "cliente*")]),
], "extra": [
 ("H", "¿un frutero es un vendedor?", "^si|vend*"), ("H", "¿la lonja es un mercado?", "^si"),
 ("P", "¿quiénes lavan el pescado?", "pescadero*"), ("P", "¿cuándo llevan la mercancía los camiones?", "madrugada"), ("P", "¿sobre qué se coloca el pescado?", "hielo"),
 ("M", "¿cuántos puestos tiene el mercado más grande de la ciudad?", "cien|100"), ("M", "¿dónde está el mercado donde se vende el pescado recién llegado?", "puerto"),
 ("N", "¿quién construyó el mercado central?", "ABST"), ("N", "¿cuánto cuesta el pescado?", "ABST"), ("N", "¿quién conduce los camiones?", "ABST"), ("N", "¿dónde duermen los fruteros?", "ABST"),
 ("C", "despachar es lo mismo que vender", N), ("P", "¿qué despachan los fruteros?", "fruta|verdura"),
 ("C", "un chiringo es lo mismo que un puesto", N), ("P", "¿qué tiene cada vendedor?", "puesto"), ("P", "¿cuántos chiringos tiene el mercado central?", "cien|100"),
 ("C", "mi madre es pescadera", N), ("C", "¿mi madre limpia el pescado?", "^si|limpia*"),
 ("G", "descríbeme la lonja", "mercado|pescado|puerto"), ("K", "el mercado cierra por la noche", K_ + "|mediodia"),
]}

TEMAS = [MERCADO]
