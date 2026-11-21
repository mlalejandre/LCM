# LCM 2.24 · El diccionario: preguntar con otras palabras

Vuelta dedicada al segundo proceso que más fallaba en el examen grande: la pregunta usa una palabra y el texto dice lo mismo con otra
(«¿dónde se limpiaba la ropa?» / «la ropa se lavaba en el río»).

## 1. Resumen

| | 2.23 | 2.24 |
|---|---|---|
| Examen limpio de diccionario (101 preguntas, medida única) | 70,3 % · 11 falsas | **80,2 % · 4 falsas** |
| El mismo, tras dos arreglos posteriores (no ciego) | | 82,2 % · 4 falsas |
| Examen grande corregido, texto pegado (352) | 87,2 % · 17 falsas | 87,5 % · 18 falsas (medida única) → **88,4 % · 16 falsas** tras arreglar dos defectos vistos en ella (no ciego) |
| Examen grande, frase a frase | 86,1 % · 18 falsas | 87,2 % · 17 falsas (código final) |
| Paráfrasis del examen grande (40) | 26 | 30 |
| Fallos de diccionario en el diagnóstico | 11 | 6 |
| Banco de desarrollo de diccionario (100) | 75 % · 7 falsas | 89 % · 1 falsa |
| Temas ya conocidos, texto (959 sondas) | 91,4 % | 92,8 % (13 ganadas, 0 perdidas) |
| Temas ya conocidos, frase a frase (866) | 89,3 % | 90,5 % (11 ganadas, 0 perdidas) |

Regresiones: solo las 4 de siempre. Controles: iguales o un punto mejor (ciego 2: 94,68 → 95,02; termómetro: 96,59 → 97,07).

## 2. La auditoría: el diccionario no era (solo) el diccionario

En los temas conocidos había 109 paráfrasis y se acertaban 78 (71,6 %). Mirando las 31 falladas una a una con dos herramientas
nuevas (`lab/lexico/audita.py`, `lab/lexico/traza.py`):

| Causa | Casos (aprox.) | Ejemplo |
|---|---|---|
| El léxico SÍ daba la palabra buena y la respuesta se perdía después | 10 | «trituran» → «moler», pero se preguntaba «¿se **molen**?» (la morfología no sabe «muelen») |
| Solo se probaba UNA candidata, y era la mala | 5 | «mover» → «trasladar» (0,74) cuando el texto decía «empujan» |
| Enlace verdadero pero flojo, por debajo del umbral | 6 | «lavar»/«limpiar», «reparar»/«arreglar» (0,46–0,47 con umbral 0,50) |
| El léxico español no enlaza la pareja | 8 | «trabajar»/«funcionar», «vigilar»/«cuidar», «tardar»/«durar» |
| La forma no se reconoce como verbo | 4 | «adquieren», «distribuyen» |
| No es diccionario sino deducción | 3 | «¿cuándo se endurece el vidrio?» / «al enfriarse» |

Y un hallazgo que no esperaba: **respuestas falsas por ignorar el verbo**. «¿Dónde VENDEN el pan los panaderos?» se contestaba
«Los panaderos cuecen el pan en un horno», y «¿cuándo APAGA la lámpara?» con «…enciende la lámpara al anochecer». Dos rutas (la
respuesta por papel y la cita) aceptaban una frase que tenía todo lo demás aunque el verbo fuera otro.

## 3. Enfoques probados

**A. Varias candidatas y que decida el texto** (el que más aporta). Antes: de cada palabra desconocida se elegía la palabra aprendida
más parecida y, si pasaba un umbral, se daba por buena. Ahora se proponen hasta tres candidatas con su clase de indicio y se prueba
cada una contra lo aprendido:

- **segura** (enseñada por el usuario, o enlace directo que cubre la mitad de los sentidos): vale si hay respuesta;
- **a medias** (pasa el umbral, pero el enlace es de un sentido entre varios);
- **débil** (enlace flojo, cadena de sinónimos, coincidencia en otro idioma): solo vale si la frase trae **todo lo demás** que se
  pregunta y eso es algo más que el tema del texto.

«¿Quiénes mueven las camillas por los pasillos?» casa con «…empujan las camillas por los pasillos» aunque «mover»/«empujar» sea un
enlace débil; «¿qué beben los pingüinos?» no casa con «usan sus alas…» solo porque el texto hable de pingüinos. Si no hay apoyo
suficiente, el modelo **pregunta** («¿«vigilar» quiere decir aquí lo mismo que «cuidar»?») en vez de adivinar; y si dos lecturas
distintas quedan igual de apoyadas, da las dos diciéndolo.

**B. Más indicios léxicos.** Puentes de un solo idioma (64 000 parejas que comparten palabra en otro idioma: «trabajar»/«funcionar»
por el inglés *work*). Solos son ruido; como indicio débil sujeto a la prueba de apoyo, sirven.

**C. Arreglos de forma.** La forma del verbo se toma del propio texto («muelen», «siembran»); más alternancias al reconocer verbos
(«adquieren», «distribuyen»); nombres en femenino («maestra»); «líquido» o «instrumento» ya no se toman por verbos en primera persona;
equivalencias de la lengua compuestas con el sentido («ingieren» → «comen» → «se alimentan de»).

**D. Locuciones verbales** (35, en la base de conceptos): «dar vueltas» = «girar», «ocuparse de» = «cuidar», «hacer reír» =
«divertir», «tener lugar» = «celebrarse». Son de la lengua, no del mundo.

**E. El verbo, anclado.** Con otro verbo en la frase, solo se contesta si dice lo mismo. Es lo que quita las respuestas falsas.

Cuánto aporta cada pieza (texto pegado; desarrollo / examen limpio; con todo: 89,0 / 82,2):

| Se quita… | Desarrollo | Examen limpio |
|---|---|---|
| varias candidatas (queda una, como en la 2.23) | 84,0 | 78,2 |
| la prueba de apoyo en la frase | 84,0 | 77,2 |
| el verbo anclado | 86,0 · 4 falsas | 78,2 · **9 falsas** |
| las locuciones | 86,0 | 82,2 |
| los puentes de un idioma | 87,0 | 82,2 |
| cambiar palabras que sí están en el texto | 88,0 | 82,2 |

Las locuciones, los puentes de un idioma y el cambio de palabras ya presentes no mueven el examen limpio: ahí no cayó ningún caso.
Se quedan porque en desarrollo y en el examen grande sí aciertan casos («divierten al público», «trabajan los relojes»).

## 4. Examen limpio (`dtest`)

Seis temas nuevos, 74 paráfrasis y 24 trampas, escrito con el código congelado y sin ejecutarlo; las palabras, como las diría una
persona, sin mirar qué enlaza el léxico.

| | 2.23 | 2.24 (medida única) | 2.24 final |
|---|---|---|---|
| Total | 70,3 % | 80,2 % | 82,2 % |
| Paráfrasis (74) | 52 | 57 | 59 |
| Trampas (24) | 17 | 22 | 22 |
| Falsas | 11 | 4 | 4 |
| Ganadas / perdidas | | 12 / 2 | 13 / 1 |

Las dos perdidas en la medida única: «¿qué lleva a los esquiadores hasta la cumbre?» (la 2.23 la acertaba citando «…sube a los
esquiadores…»; el verbo anclado la rechazaba) y «¿dónde arriendan las botas?» (la 2.23 la acertaba por la ruta que ignoraba el
verbo; «arrendar» no está en el léxico). La primera se arregló después: a un verbo con decenas de sentidos («llevar», «dar») no se
le exige ancla. La segunda queda perdida a propósito: con una palabra que no conoce, ahora dice que no la conoce.

Lo que sigue sin salir (15 paráfrasis): parejas que el léxico no enlaza de ningún modo («echar»/«tirar», «comprar»/«vender» como
dos caras del mismo hecho, «practicar»/«ensayar», «ayudar»/«auxiliar», «aplanar»/«alisar», «confeccionar»/«coser»), y preguntas que
piden un paso más («¿cuánto tarda en secarse?» / «se seca en pocos segundos»).

## 5. Examen grande

Medido una vez: 87,2 → 87,5 % con texto pegado, con 5 ganadas (cuatro paráfrasis y «divierten al público») y 4 perdidas, dos de
ellas respuestas falsas nuevas. Eran defectos generales y los arreglé; el número de después ya no es ciego:

- «¿quién vende el champú?» → «…un jabón **líquido**…, entiendo vender como liquidar»: «líquido» contaba como verbo;
- «¿quién inventó el jabón?» → «los jaboneros fabrican jabón»: al componer con la tabla se saltaba la comprobación del tiempo;
- «¿qué instrumento da la nota…?»: «instrumento» tomado por verbo;
- «¿cuándo se cosecha el arroz?»: sigue perdida (cita una frase con «la cosecha»; antes acertaba por «recoger»).

Tras ellos: 88,4 % (texto) y 87,2 % (frases). Diagnóstico por proceso, 2.23 → 2.24: diccionario 11 → 6; lectura 12, razonamiento
6, interconexión 5, expresión 4, fábrica 3, consulta 2: sin cambios.

## 6. Salvedades

- El examen limpio lo escribí yo conociendo qué tipo de cosa había arreglado; la 2.23 partía de 70 % porque es un examen difícil
  a propósito. El examen grande, que no se usó para desarrollar, sube poco (+0,3 en la medida única): el diccionario eran 11 de 45 fallos.
- Los dos números «finales» (82,2 y 88,4) incluyen arreglos hechos después de ver los fallos. Los ciegos son 80,2 y 87,5.
- La prueba de apoyo depende de que la pregunta traiga algo más que el tema. Con preguntas muy cortas («¿dónde surge el río?») un
  indicio débil no basta y el modelo pregunta. Eso cuenta como fallo en el banco, aunque en conversación se resuelve con un «sí».
- El léxico español tiene huecos reales (palabras que no están: «remolcar», «peldaño», «moldear», «arrendar»). Ahí la única vía es
  que el usuario lo enseñe; el modelo ya dice qué palabra no conoce.
- Las 35 locuciones están escritas a mano. Es conocimiento de la lengua, pero es una lista.

## 7. Interruptores para medir

`LCM_SENTIDO_UNA=1` (una sola candidata), `LCM_SENTIDO_SIN_APOYO=1`, `LCM_SIN_ANCLA=1`, `LCM_SIN_LOCUCIONES=1`, `LCM_SIN_PUENTE1=1`,
`LCM_SENTIDO_FUERA=1` (no cambiar palabras que están en el texto), `LCM_SIN_TABLA_CITA=1`, `LCM_SIN_TIPO_QUE=1`.

## 8. Verificación

Tandas 01–15 e iter26…iter224: fallan solo las 4 conocidas (iter26 t11, iter28 t23, iter210 t01, iter214 t05). Tanda nueva
`lab/iter224/t01.py`: 187 sondas, 100 %. Controles: autor 90,18 % (=), ciego 2 95,02 (+1 sonda), ciego 6 82,09, ciego 7 79,07,
termómetro 97,07 (+1), 16b 96,48, 16c 100, 17b 99,26, 17c 94,50, conversa17 99,33. Pytest: 938 pasan; fallan los 3 de entorno de siempre.

## 9. Archivos

`src/nucleo20/sinonimia.py` (evidencia, candidatas, propuestas, apoyo, ancla, locuciones, conjuga), `dialogo.py` (`_sentido`),
`vectores.py` (puentes de un idioma, `tipo_de`), `lectura.py` y `preguntas.py` (verbo anclado), `conceptos.py` y
`conceptos_base.txt` ([locuciones]), `src/web/motor.py` (el «no lo sé» del núcleo ante preguntas sobre lo leído),
`lab/lexico/` (auditoría), `lab/aprender/ddev.py` y `dtest.py`, `lab/iter224/`.
