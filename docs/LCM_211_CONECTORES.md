# LCM 2.11 · Conectores lógicos

Parche sobre la 2.10. No se reentrena nada y no hay hechos del mundo: solo el valor lógico de las uniones.

## Qué entiende ahora

### Copulativas: y / e, ni… ni, tanto… como, la coma de enumeración
- «Tanto mi padre como mi madre son médicos» se entiende como dos hechos; «¿Mi madre es médica?» → «Sí».
- Las enumeraciones se guardan como varios hechos y se dicen en una sola frase: «Llevas pan, leche, huevos y fruta en la compra». También funciona cuando el complemento va delante («Para la cena compro…»).
- «Ni… ni» niega cada elemento por separado, y al responder se dice con «ni».

### Disyuntivas: o / u, o… o, bien… bien
- Cada alternativa se entiende como una frase normal, pero queda como **posible**: nunca se afirma sola ni pasa a la memoria de hechos.
- Al responder, el grupo se dice entero: «Pablo vive en Lugo o en Ourense».
- **Sí/no sobre una alternativa:** «Puede ser: me dijiste que… o…, pero no cuál».
- **Algo que no está entre las alternativas:** «No: me dijiste que…».
- **Silogismo disyuntivo:** si se niega una alternativa, se descarta; si queda una sola, se deduce y se dice por qué. Si se confirma una, las demás caen.
- **Cantidades alternativas:** «dos o tres primos».
- **Preguntas alternativas:** «¿Vive en Jaca o en Sabiñánigo?».
- **Una disyunción nunca se trata como «y».** Si no la entiende, la apunta literalmente.

### Comparativas: más… que, menos… que, tan… como, mayor/menor, superlativo
- Transitividad y superlativo («¿quién es la más alta de los tres?»), que ya existían.
- **Nuevo, igualdad:** «Nuria es tan alta como Pepa» → «¿Pepa es más alta que Nuria?» → «No: Nuria es tan alta como Pepa». También se propaga: si Pepa es más alta que Luisa, Nuria también.
- **Nuevo, preferencia:** «me gusta más / menos X que Y» se entiende como «prefiero X a Y», con su inversa («¿me gusta más el café que el té?» → «No…»).
- **Nuevo, comparación con verbo:** «¿quién corre más rápido, X o Y?».
- **Edad** con la fecha completa: año, mes y día de «nací…» y «cumplo años el…». Exacta cuando se puede; si falta el mes, da los dos valores («30 o 31, según si ya has cumplido»). También «¿cuántos años tendré en 2030?».

### Condicionales con «si»
- **Suposición, «Si P, ¿Q?».** P se supone en una copia de la memoria, se responde Q y todo vuelve a como estaba.
  - «Si nací el 5 de diciembre, ¿qué edad tengo?» → «En ese caso, tienes 30 años».
  - «Si nací el día 5…» → «30 o 31: no sé el mes».
  - «Si hubiera nacido en 1998, ¿qué edad tendría?» → «tendrías 28 años». El subjuntivo y el condicional pasan a indicativo para calcular, y se responde en condicional.
  - «Si tuviera 10 años menos…» se resta a la edad actual.
- **Regla, «Si P, Q».** Se guarda. Cuando después se dice algo que cumple P, se deduce Q (*modus ponens*) y se explica:
  - «Si mañana llueve, no iré a la playa» + «mañana va a llover» → «Entonces no irás a la playa mañana: lo deduzco porque…».
  - No se dispara si el tiempo no coincide (la regla dice «el domingo» y luego se dice «hoy llueve»).
  - «¿Qué pasa si estudio?» → «Me dijiste que si estudias, apruebas».

### Más arreglos de lengua en esta ronda
- **Complemento antepuesto:** cualquier complemento delante del verbo va detrás.
- **Verbo sobrentendido:** «Pablo tiene treinta años y yo veintiocho».
- **«Como»** al empezar una afirmación es el verbo *comer*.
- **Nombres leídos como verbo:** un nombre conocido tras un verbo conjugado ya no se lee como verbo («haré pasta»).
- **Introductores:** «ya me acuerdo:», «ahora caigo:», «al final…».

## Método y resultados
1. Antes de tocar el código, con la 2.10 congelada, se escribieron `lab/charla50f.py` (50 interacciones, 49 puntuadas) y `lab/examen_ciego11.py` (44 turnos puntuados). Se midieron sin leer las respuestas.
2. Seis tandas de desarrollo (`lab/iter211/t01`–`t06`, 82 turnos), con regresión y controles después de cada una.
3. Una sola medida final con el código congelado.
4. Auditoría manual con el mismo criterio para las dos versiones (`lab/iter211/auditoria.json`).

| Prueba | 2.10 | 2.11 (ciega) | 2.11 tras arreglos (no ciega) |
|---|---|---|---|
| charla50f, juez automático | 63,27 % · 3 «falsas» | 81,63 % · 2 | 97,96 % · 1 |
| charla50f, auditada | 42,86 % · 2 falsas | 75,51 % · 0 | 95,92 % · 0 |
| ciego 11, juez automático | 63,64 % · 1 | 93,18 % · 0 | 95,45 % · 0 |
| ciego 11, auditado | 63,64 % · 0 | 93,18 % · 0 | 95,45 % · 0 |
| exámenes del autor / ciego 2 / ciego 6 / ciego 7 | 88,05 / 94,35 / 80,60 / 76,74 | igual | igual |

**Arreglos después de la medida** (no ciegos: se hicieron después de leer las respuestas): introductores, «como» inicial, verbo sobrentendido, una regla con una sola palabra, «¿quién corre más rápido?» y que la edad use el dato más reciente. Al principio, el arreglo del verbo sobrentendido rompió la edad hipotética; se vio en la re-medida y se corrigió.

En la 2.10, el juez automático aprobó dos afirmaciones falsas: «Sí, Pablo vive en Lugo o en Ourense…» y «Pablo llevó pan en la compra». La auditoría las cuenta como falsas. Las «falsas» del juez en la 2.11 son negativas o respuestas incompletas, no datos falsos.

**Primer intento de las tandas** (corregido a mano cuando el juez fue laxo): 63,4 % en total (52 de 82 turnos). Por tanda: 57 %, 29 %, 80 %, 31 %, 100 % y 83 %, con 4 respuestas falsas en total (2 de ellas «harás pizza y pasta», la «o» tratada como «y»). Detalle en `primer_intento.json`.

## Lo que queda mal
- **Enumeración de complementos con «de»:** «hay alumnos de Perú, Chile, Cuba y Bolivia».
- **Coordinación con «yo» y tres sujetos:** «Sara, Pablo y yo iremos al cine» pierde a Pablo.
- **Disyunciones complejas:** las de más de un complemento por alternativa, o con la «o» en mitad de una frase larga, se apuntan literalmente (con honestidad, pero sin entenderlas).
- **Reglas condicionales:** se comparan por las palabras clave de la condición, sin entender del todo los sinónimos («hace bueno» y «hace sol» son reglas distintas).
