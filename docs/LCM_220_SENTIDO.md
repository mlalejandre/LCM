# LCM 2.20 · Preguntar por el sentido: vectores aprendidos del léxico

Sigue el plan de `LCM_218_APRENDER.md` y `LCM_219_APRENDER_2.md`. La 2.19 cerró diciendo que escribir equivalencias a mano
rendía cada vez menos y que la paráfrasis seguía en el 0 % en temas nuevos. Esta vuelta cambia el método: en vez de más
reglas, el modelo aprende de su propio léxico qué palabras significan lo mismo y lo usa de forma gradual.
No depende de ningún tema y no añade hechos del mundo: solo significado de palabras.

## 1. Análisis previo (antes de tocar nada)

- **Quién contesta en las dos medidas a ciegas de la 2.19** (125 preguntas, `lab/iter220/componentes_219.json`):
  núcleo 41 % (acierta el 90 %), reglas de exposición 21 % (96 %), cita literal 19 % (88 %), abstención 19 %
  (justificada solo en el 46 %). El hueco está en lo que se abstiene sin deber: paráfrasis, combinar y deducir.
- **Qué vectores había ya en el proyecto.** `ConceptSpace` usa rasgos declarados para unos pocos conceptos y no cubre el
  vocabulario de un texto cualquiera. El léxico (`data/lexico_es.json`, 22 154 palabras sueltas) sí lo cubre, pero solo se
  consultaba como diccionario.

## 2. Qué cambia

- **Vectores de significado aprendidos del léxico** (`src/nucleo20/vectores.py`). Se factoriza la matriz «estas dos palabras
  comparten un sentido» y cada palabra queda como un vector de 96 números. Se entrena de fábrica en unos 3 segundos; no hay
  ningún modelo de texto preentrenado. El parecido es gradual: «fallecer»/«morir» 1,00, «elaborar»/«fabricar» 0,82,
  «investigar»/«estudiar» 0,56, «perro»/«gato» 0,00.
- **Preguntar por el sentido** (`sinonimia.por_sentido`). Si una pregunta no encuentra respuesta, cada palabra suya que no
  aparece en lo leído se cambia por la palabra leída de sentido más cercano, y se vuelve a preguntar al núcleo y a la cita.
  La respuesta dice qué ha entendido: «Los carteros reparten las cartas. Entiendo «entregar» como «repartir».»
- **Dos medidas del mismo léxico, las dos graduales** (`sinonimia._afin`): el parecido de los vectores y el enlace directo
  en el grafo (comparten sentidos, o una es una manera de la otra: «almacenar» → «guardar», «ingerir» → «comer»).
- **Frenos:** los contrarios del léxico no se intercambian; si dos candidatas de sentido distinto empatan, no se elige; una
  pregunta por algo que pasó («¿quién inventó…?») no la contesta una costumbre en presente.
- **Verbos que la morfología no conocía** («ingieren», «muelen») se reconocen buscando en los verbos del léxico.
- **Reglas generales nuevas, pocas:** «El lugar donde se fabrica el aceite se llama almazara» deja también que el aceite se
  fabrica en la almazara; «Allí…» es el lugar recién nombrado; «¿qué país cruza X?» se contesta con «cruza Rusia»;
  «el fruto del olivo es la aceituna» ya no sale en plural; «el lugar donde» no se toma por nombre de clase.

## 3. Lo que salió mal por el camino (y por qué el diseño es este)

Calibrado con el propio léxico (`lab/iter220/calibra.py`):

| Intento | Resultado |
|---|---|
| Vectores con los ancestros como contexto | Los «hermanos» quedan tan cerca como los sinónimos: en nombres pasan el umbral el 63 % de los sinónimos y el 50 % de los hermanos. Daba «vida» ≈ «fase», «inventar» ≈ «construir» |
| Vectores solo de sinonimia, sin más comprobación | El 33-45 % de los pares con parecido ≥ 0,6 solo están unidos por una cadena de sinónimos («gratificar» → «encantar» → «hipnotizar») |
| Solo el enlace del grafo, sin graduar | «beber» = «usar», «pesar» = «medir» (comparten un sentido raro) |
| Vector + enlace directo, los dos graduales | El que se entrega |

Un parecido simétrico no puede acercar «almacenar» a «guardar» sin acercar también a los hermanos; por eso «una manera de»
se mira en el grafo y no en el vector.

## 4. Métricas

Corrector automático salvo donde dice «auditado». «Falsas» = respuestas que afirman algo incorrecto.

**Primera medida limpia** (`test5`: el vidrio y el correo, 83 preguntas, 16 de paráfrasis y 12 trampas; escrita con el código
congelado, medida una vez):

| | 2.19 | 2.20 |
|---|---|---|
| Texto pegado: acierto (falsas) | 72,3 % (4) | **79,5 %** (5) |
| Texto pegado, auditado | 72,3 % (4) | **80,7 %** (4) |
| Frase a frase | 66,3 % (5) | **71,1 %** (5) |
| Paráfrasis, texto pegado | 12 % | **50 %** (56 % auditado) |
| Trampas (no debe contestar) | 100 % | 100 % |
| Sin leer nada | 24,1 % | 24,1 % |

Auditoría: una respuesta correcta («Sí, el vidrio se rompe con facilidad») contaba como fallo porque la nota iba delante del
«Sí»; se movió detrás (arreglo no ciego). De 8 respuestas por el sentido, 7 correctas y 1 falsa: «ordenar» entendido como
«recoger» (el léxico las da por sinónimas en «recoger la habitación»).

**Segunda medida limpia** (`test6`: la lana, 38 preguntas; código definitivo, medida una vez, nada tocado después):

| | 2.19 | 2.20 |
|---|---|---|
| Texto pegado: acierto (falsas) | 76,3 % (1) | **81,6 %** (1) |
| Frase a frase | 65,8 % (3) | **68,4 %** (3) |
| Paráfrasis, texto pegado | 25 % | **37 %** |
| Trampas | 100 % | 100 % |

**Banco de paráfrasis de desarrollo** (`pdev`: 48 paráfrasis y 20 trampas sobre nueve temas conocidos; no es a ciegas):

| | Paráfrasis | Trampas |
|---|---|---|
| 2.19 | 33 % | 100 % |
| 2.20 | **72 %** | 100 % |
| 2.20 sin la tabla a mano | 70 % | 100 % |
| 2.20 sin vectores (solo la tabla a mano) | 33 % | 100 % |
| 2.20 sin ninguna de las dos | 29 % | 100 % |

En `test5` (ya no ciego): con las dos 56 %, sin la tabla 43 %, sin vectores 12 %, sin ninguna 0 %.
El léxico aprendido hace casi todo el trabajo; la tabla a mano de la 2.19 aporta entre 2 y 13 puntos.

**Estabilidad:** con otras dos semillas de entrenamiento, `pdev` da 75 % en paráfrasis (una pregunta más) y `test5` lo mismo.
Entrenado con Python 3.11, los vectores difieren en 0,0002.

**Temas ya conocidos** (texto pegado / frase a frase): dev 96,0 / 89,1 · test 88,4 / 85,3 · test2 94,8 / 79,3 ·
test3 93,3 / 81,7 · test4 83,1 → **86,2** / 75,4 · setas 72,9. Ninguno baja.

## 5. Lectura honrada

- La mejora es real pero moderada: +7 y +5 puntos en temas nuevos, casi toda en paráfrasis. En la segunda medida solo se
  recuperó una paráfrasis más de ocho.
- **El límite ahora es el léxico, no el método.** No enlaza «vigilar»/«cuidar», «transformar»/«convertir»,
  «limpiar»/«lavar», «demorar»/«tardar» ni expresiones de varias palabras («hacer daño» = «lastimar»).
- Los vectores no son un modelo del lenguaje: comprimen un diccionario de sinónimos. No saben nada de palabras que el léxico
  no tiene (las inventadas, los nombres propios) y heredan sus errores de polisemia.
- «No determinista» se ha entendido como gradual y no basado en reglas fijas; no hay azar: la misma pregunta da siempre la
  misma respuesta.
- Combinar dos frases sigue en 0 % en `test5` (2 preguntas) y el modo frase a frase sigue 8-13 puntos por debajo del texto pegado.
- Siguen sin tocar: definiciones torpes de «llamado/a», «La lana convertir en el hilo», «dime dos cosas que se hacen con…»,
  «el buzón en España es rojo» (no detecta el contraste).

## 6. Siguiente vuelta (por impacto esperado)

1. Aprender sinónimos de lo que se lee: si el texto dice «cuidan» y el usuario pregunta «vigilan» y confirma, guardarlo.
2. Combinar dos frases con el razonador sobre los hechos aprendidos.
3. Igualar el modo frase a frase con el texto pegado.
4. Expresiones de varias palabras como unidad de sentido.

## 7. Verificación

- **Regresiones** (tandas 01-15 e iter26…iter220): todo al 100 % salvo las cuatro de siempre (iter26 t11, iter28 t23, iter210 t01,
  iter214 t05). Tanda nueva `lab/iter220/t01.py`: 163 sondas, 100 %.
- **Controles, idénticos a la 2.19:** autor 89,90 % · ciego2 94,68 % · ciego6 82,09 % · ciego7 79,07 % · termómetro 96,59 % ·
  16b 96,48 % · 16c 100 % · 17b 99,26 % · 17c 94,50 % · conversa17 99,33 %.
- **Pytest:** 906 pasan; fallan los 3 de entorno de siempre (red y dos ficheros que no están en este entorno).
- Compilado y ejecutado también con Python 3.11.
