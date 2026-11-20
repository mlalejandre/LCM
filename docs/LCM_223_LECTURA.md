# LCM 2.23 · Leer las frases que no se sostienen solas

El examen grande (`LCM_EXAMEN_GRANDE_1.md`) dijo que un tercio de los fallos venía de la lectura: frases que no se convertían en
hechos o se colgaban del tema equivocado, y que arrastraban a paráfrasis, combinaciones y contradicciones. Esta vuelta trabaja solo
eso. Misma regla de siempre: nada depende del tema.

## 1. Auditoría de lo que había

Instrumento nuevo: `python -m lab.lectura.audita`. Para cada frase con pregunta literal mira qué forma tiene, si deja un hecho en el
núcleo y por dónde se acierta la pregunta (hecho, regla de exposición, cita del texto, fábrica o nada).

En los once temas ya conocidos (322 preguntas literales) la 2.22 acertaba el 95,7 %, pero **solo el 69 % de las frases dejaba un
hecho**: el resto se salvaba citando el texto. Esos temas ya no enseñaban el problema porque se habían ido arreglando uno a uno.
Con un banco nuevo cargado de frases dependientes (`ldev`, seis temas, 95 preguntas) la 2.22 bajaba al 83,2 % con el texto pegado
y al 76,8 % frase a frase.

Fallos encontrados al auditar, por orden de peso:

| Fallo | Ejemplo |
|---|---|
| El tema de una frase sin sujeto se elegía por número (último singular o plural), pero las frases con «Se…» ni se intentaban | «Se toca de pie.» quedaba como «los violines se tocan de pie» |
| La segunda mitad de una frase con «y» se perdía | «…se llaman ballenatos **y maman durante un año**» |
| Los pronombres no se resolvían | «Con ellas trepan a los árboles», «lo cortan en rodajas», «la sujetan dos bomberos» |
| «Debajo hay…», «Allí duermen…», «Cuando suena la alarma bajan…» quedaban sin sitio o sin sujeto | |
| Frase a frase, las frases con «duro», «seco», «blando» se tomaban por personales («yo duro») y no se leían como explicación | |
| «té» se confundía con el pronombre «te»: ninguna frase sobre el té se leía como explicación | |
| Una respuesta de fábrica ganaba aunque el hecho leído estuviera en el núcleo | «¿Dónde viven los osos?» → «suelen vivir en el bosque» |
| El encadenado llegaba tarde: la cita o un sinónimo contestaban antes | |

## 2. Enfoques probados

Tres maneras de atacar lo mismo, medidas por separado con interruptores (`LCM_DISCURSO`, `LCM_FABRICA_MANDA`, `LCM_CADENA_TARDE`):

- **A. Preparar la frase antes de leerla** (`src/nucleo20/discurso.py`): un paso de texto que deja cada frase completa. El núcleo ya
  entendía bien las frases completas; lo que fallaba era que le llegaban a medias.
- **B. Mejorar la búsqueda en el texto**: que la cita sepa de qué habla cada frase (su tema) y desempate por el complemento.
- **C. Cambiar el orden de quién contesta**: lo leído por delante de la fábrica, y encadenar antes que nada.

Resultado en el examen limpio de lectura (texto pegado) y en el de desarrollo:

| Configuración | Limpio (`ltest`) | Desarrollo (`ldev`) |
|---|---|---|
| Nada de lo nuevo | 79,6 % | 86,3 % |
| Solo B y C (sin preparar frases) | 80,6 % | 88,4 % |
| A: poner el sujeto que falta | 87,1 % | 92,6 % |
| A: + partir la segunda mitad con «y» | 90,3 % | 93,7 % |
| A: + pronombres y lugar | **91,4 %** | **95,8 %** |
| A: + relativas («…, que se calienta…») | 91,4 % | 95,8 % |
| Todo menos «lo leído manda sobre la fábrica» | 90,3 % | 93,7 % |
| Todo, pero encadenando tarde | 91,4 % | 95,8 % |

**Gana A con mucha diferencia** (unos 11 de los 12 puntos). Dentro de A, poner el sujeto vale más de la mitad y partir por «y» otro
cuarto. B y C suman poco por separado; se quedan porque no restan y C quita respuestas falsas. Las relativas y encadenar antes no
mueven estos dos bancos; se dejan porque sí arreglan casos de los temas conocidos.

## 3. Qué hace el parche

- **Sujeto que falta:** «Se toca de pie» → «El contrabajo se toca de pie». Vale para verbo delante, «Se…», «No…» y adverbio delante.
- **Segunda mitad con «y»:** se separa y hereda el sujeto. Si la primera mitad pone un nombre («se llaman ballenatos»), lo que sigue
  se dice de ese nombre.
- **Pronombres:** «Con ellas trepan» (las garras), «lo cortan en rodajas» (el pescado), «la sujetan dos bomberos» (la manguera).
- **Lugar:** «Debajo hay…» → debajo de lo último nombrado; «Allí duermen» → en el sitio que se acaba de presentar.
- **«Cuando A, V…» sin sujeto** en la principal, y **relativas explicativas** («…con arena, que se calienta en un horno»).
- **Sujeto tras el complemento:** «En invierno las abejas no salen… y se alimentan…».
- **Frase a frase** se hace lo mismo que al leer un texto, con el hilo de la conversación; el hilo se corta cuando se pasa a hablar
  de uno mismo.
- **La cita sabe el tema** de cada frase dependiente, también cuando el núcleo no la convirtió en un hecho.
- **Lo leído manda sobre la fábrica** en preguntas abiertas; no en las de sí o no ni en «¿qué es…?».
- **Encadenar es lo primero** que se intenta cuando la pregunta nombra algo por su descripción.
- **Contraste de duraciones** («un mes» / «un año»), «¿quién es X?» pide la definición, «¿dónde…?» acepta «cae **a** un saco».

Lo que el preparador **no** toca, a propósito: frases que empiezan por un nombre propio, «Se llama…», «Ya está…» (cambio de estado),
«Solo vive…», «Era un trabajo solitario» (puede hablar del tema o de lo recién contado) y «Antes se escribía…» (impersonal).

## 4. Métricas

Corrector automático. «Falsas» = respuestas que afirman algo incorrecto.

**Examen limpio de lectura** (`ltest`: seis temas nuevos, 93 preguntas; código congelado, medido una vez):

| | 2.22 | 2.23 |
|---|---|---|
| Texto pegado: acierto (falsas) | 78,5 % (8) | **91,4 %** (4) |
| Frase a frase: acierto (falsas) | 82,8 % (8) | **91,4 %** (4) |
| Literales | 75 % | 91 % |
| Contradicciones | 50 % | 100 % |
| Combinar dos frases | 75 % | 100 % |

**Examen grande** (`grande1b`: diez temas, 352 preguntas; escrito antes de esta vuelta y no usado para desarrollarla; medido una vez):

| | 2.22 | 2.23 | Intervalo 95 % de la 2.23 |
|---|---|---|---|
| Texto pegado: acierto (falsas) | 82,7 % (24) | **87,2 %** (17) | 83,3 – 90,3 |
| Frase a frase: acierto (falsas) | 82,1 % (26) | **86,1 %** (18) | 82,1 – 89,3 |
| Preguntas ganadas / perdidas, texto pegado | | 16 / 0 | |
| Preguntas ganadas / perdidas, frase a frase | | 15 / 1 | |

Por tipo, texto pegado: literales 85 → 93 · contradicciones 57 → 78 · combinar 55 → 70 · paráfrasis 60 → 65 · deducciones 60 → 60.

El mismo diagnóstico por proceso, antes y después (`python -m lab.grande1.diagnostico 223`):

| Paso que falla | 2.22 | 2.23 |
|---|---|---|
| Lectura (no se lee, o se cuelga de otro tema) | 21 | **12** |
| Consulta (el hecho está y la pregunta no llega) | 5 | 2 |
| Diccionario | 10 | 11 |
| Razonamiento | 8 | 6 |
| Fábrica tapa el texto | 6 | 3 |
| Interconexión | 5 | 5 |
| Expresión, corrector y otros | 6 | 6 |
| **Total** | **61** | **45** |

**Temas ya conocidos** (2.22 → 2.23): con el texto pegado 5 preguntas ganadas y ninguna perdida; frase a frase 15 ganadas y ninguna
perdida. Frase a frase: test 92,6 → 93,7 · test3 85,0 → 90,0 · test5 79,5 → 84,3 · test7 87,1 → 92,9 · test8 74,3 → 80,0.
Banco de desarrollo `ldev`: 83,2 → 95,8 (texto) y 76,8 → 93,7 (frase a frase).

## 5. Lectura honrada

- **La hipótesis del diagnóstico se confirma:** arreglar la lectura mueve literales, contradicciones y combinaciones a la vez, en un
  examen que no se usó para desarrollar. Es la mayor mejora en temas nuevos desde la 2.20.
- **Del examen grande conocía las formas de frase que fallaban**, porque de ahí salió el diagnóstico. No lo usé para afinar, pero
  no es una medida tan ciega como `ltest`. La cifra más limpia de esta vuelta es la de `ltest`.
- **Quedan 12 fallos de lectura** en el examen grande: «más de trescientos pasajeros», «usan la cola como timón cuando nadan»,
  «hay que darles cuerda», y la premisa «la ballena azul es una ballena».
- **El preparador se equivoca a veces.** En los 323 enunciados de los temas conocidos cambia 58 frases; auditadas una a una, quedaban
  cuatro errores que se corrigieron. En textos nuevos habrá otros: elige el tema por número y cercanía, sin entender.
- **Frases que empiezan por nombre propio no se tocan frase a frase**, así que «Gutenberg la inventó… Era un orfebre» sigue sin leerse.
- **Lo que no se ha movido:** deducciones (60 %) y diccionario (11 fallos). Son ahora los dos grupos mayores junto con la lectura.

## 6. Siguiente vuelta (según el diagnóstico de la 2.23)

1. Lectura que queda: cantidades con «más de», «como» + «cuando», «hay que», y que «el X adjetivo» sea un X.
2. Diccionario: decidir mejor con lo que ya hay (4 enlaces que existen y se descartan, 2 falsos).
3. Excluir: contrarios, «solo», mucho/poco.

## 7. Verificación

- **Regresiones** (tandas 01-15 e iter26…iter223): todo al 100 % salvo las cuatro de siempre. Tanda nueva `lab/iter223/t01.py`: 188 sondas, 100 %.
- **Controles:** autor 90,04 → 90,18 % (una más); ciego2 94,68 % · ciego6 82,09 % · ciego7 79,07 % · termómetro 96,59 % · 16b 96,48 % ·
  16c 100 % · 17b 99,26 % · 17c 94,50 % · conversa17 99,33 %, idénticos a la 2.22.
- **Pytest:** 925 pasan; fallan los 3 de entorno de siempre.
- Compilado y ejecutado también con Python 3.11.
