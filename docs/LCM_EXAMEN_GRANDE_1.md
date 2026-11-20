# LCM · Examen grande 1, corregido, y diagnóstico por proceso (después de la 2.22)

Diez temas nuevos con el mismo reparto de tipos de pregunta en cada uno. Escrito sin ejecutar nada y sin tocar el código; medido una
sola vez en cada versión.

- Examen original: `lab/aprender/grande1.py` (358 preguntas). Corregido: `lab/aprender/grande1b.py` (352 puntuadas).
- Resultados: `lab/grande1/`. Diagnóstico: `python -m lab.grande1.diagnostico` → `lab/grande1/diagnostico_222.json`.

**Es una vara fija.** No se usa para desarrollar: lo que se saca de aquí son tipos de fallo, y los arreglos se prueban con otros temas.

## 1. Qué se ha corregido en el examen y por qué

La primera versión contaba como fallo respuestas que eran correctas. «Los castores trabajan sobre todo de noche» no dice que no
trabajen de día: contestar «No lo sé. Solo sé que trabajan de noche» es lo correcto. Cambios, todos en la clave y ninguno en el texto
ni en las preguntas:

- **4 deducciones** en las que el texto no excluye lo preguntado: ahora vale abstenerse o dar el dato que sí se sabe.
- **6 «contradicciones» que son compatibles con lo leído** (otra estación, otro sitio, otro ingrediente): no se puntúan. Aparte: la
  2.22 avisa de que es distinto de lo leído en 1 de las 6 y dice «Entendido» en las otras 5.
- **1 criterio mal escrito.**

Queda una pregunta mía mal planteada que no he quitado para no retocar más la vara («¿qué hay debajo del número más peligroso?»);
está marcada en el diagnóstico.

## 2. Resultado

| Versión | Texto pegado | Intervalo 95 % | Frase a frase | Intervalo 95 % |
|---|---|---|---|---|
| 2.19 | 75,9 % | 71,1 – 80,0 | 68,2 % | 63,1 – 72,8 |
| 2.20 | 79,5 % | 75,0 – 83,4 | 71,0 % | 66,1 – 75,5 |
| 2.21 | 80,7 % | 76,2 – 84,5 | 81,0 % | 76,5 – 84,7 |
| **2.22** | **82,7 %** | 78,4 – 86,3 | **82,1 %** | 77,8 – 85,8 |

La corrección sube todas las versiones unos dos puntos y no cambia las diferencias entre ellas: 2.19 → 2.22 gana 26 preguntas y
pierde 2 con el texto pegado, y gana 50 y pierde 1 frase a frase.

Por tipo (2.22, texto pegado; entre paréntesis la 2.19): inversas 100 (100) · herencia 100 (90) · vocabulario 96 (96) · trampas 92 (92) ·
charla 90 (90) · uso 90 (90) · literales 85 (83) · deducciones 60 (65) · paráfrasis 60 (28) · contradicciones 57 (50) · combinar 55 (25).

Por tema: hospital 91 · ballenas 92 · castores 89 · desierto 83 · arroz 83 · jabón 83 · aeropuerto 82 · orquesta 78 · circo 74 · relojes 72.

## 3. Diagnóstico: en qué paso se rompe cada fallo

El tipo de pregunta dice qué se pidió, no por qué falló. Para saberlo, cada uno de los 61 fallos de la 2.22 se ha comprobado con el
propio modelo:

- ¿hay en el núcleo un hecho con ese dato, o la frase solo quedó guardada como texto?
- ¿se acierta la pregunta literal equivalente? (para las paráfrasis)
- ¿se aciertan los dos pasos por separado? (para combinar y deducir)
- ¿qué dice el léxico de la pareja de palabras?

Un fallo que depende de un paso que ya falla solo hereda la causa de ese paso.

| Paso que falla | Fallos | Qué significa |
|---|---|---|
| **Lectura: la frase no se convierte en un hecho** | **16** | Solo queda guardada como texto, y buscarla como texto tampoco la encuentra |
| **Lectura: el hecho se cuelga del tema equivocado** | **5** | «Se toca de pie» queda como «los violines se tocan de pie»; era el contrabajo |
| Diccionario | 10 | Falta el sinónimo (4), el enlace existe y no pasa el umbral (4), o enlaza con otra palabra que aquí no dice lo mismo (2) |
| Razonamiento | 8 | Sabe la premisa y no da el paso: exclusión, negación, implicación |
| Fábrica | 6 | El conocimiento de fábrica contesta por encima de lo leído |
| Consulta | 5 | El hecho está bien guardado en el núcleo y la pregunta no llega a él |
| Interconexión | 5 | Cada pieza se sabe por separado (comprobado) y no se unen |
| Expresión o corrector | 4 | Lo sabe y lo dice de una forma que no vale (2 son culpa del corrector) |
| Otros | 2 | Una cita que no contesta y una pregunta mía mal planteada |

### 3.1 Leer es un tercio de los fallos, y arrastra a los demás tipos

Los 21 fallos de lectura no son solo literales: 9 son literales, 4 de combinar, 3 paráfrasis, 3 contradicciones y 2 deducciones.
Una paráfrasis cuya pregunta literal también falla no tiene un problema de diccionario; una pregunta de combinar cuyo segundo paso
falla solo no tiene un problema de encadenar. **Es el mismo fallo visto desde varios sitios.**

Las frases que no se leen, o se leen mal, tienen formas repetidas:

| Forma de la frase | Ejemplo | Qué pasa |
|---|---|---|
| Sin sujeto, sigue hablando del tema | «Se toca de pie.» · «Se cocina en una sartén ancha y plana.» | Se cuelga de otro tema: de «los violines», de «el arroz» |
| Sin sujeto con «tiene» | «Tiene un pájaro de madera que sale cada hora.» | No se lee |
| Segunda mitad de una frase con «y» | «…se llaman ballenatos **y maman durante un año**.» | Se lee la primera mitad |
| Pronombre que remite a la frase anterior | «Con ellos cortan troncos y ramas.» | No se lee |
| Cantidad con «más de» | «Un avión grande lleva más de trescientos pasajeros.» | No se lee |
| Empieza por adverbio o preposición | «Debajo hay una red por si se caen.» · «A los relojes mecánicos hay que darles cuerda…» | No se lee |
| Complemento con «como» y «cuando» | «Los castores usan la cola como timón cuando nadan.» | No se lee |

Colgar un hecho del tema equivocado es peor que no leerlo: es un dato falso dentro del modelo. El tema que se elige es el primero
del texto o el último sujeto en plural, no el de la frase anterior.

### 3.2 Diccionario: 10 fallos, de tres clases distintas

- **Falta el enlace (4):** tardar/durar, ajustar/afinar, divertir/hacer reír, trabajar/funcionar. Solo esto se arregla con más diccionario.
- **El enlace existe y no pasa el umbral (4):** andar/caminar (0,94 de parecido), reparar/arreglar, limpiar/lavar, plantar/sembrar.
  El dato está; el criterio de decisión lo descarta.
- **Enlace falso (2):** «arreglar» como «atender», «guiar» como «conducir». Son respuestas falsas.

### 3.3 Razonamiento (8), consulta (5) e interconexión (5)

- **Razonamiento:** abiertas → no cierran; mucha → no poca; solo de día → de noche no; de pie → no sentado; un mes → no un día; dos
  semanas → no dos meses; «zona donde hay agua» → hay agua; viaja de ciudad en ciudad → no se queda siempre en la misma. En los ocho
  casos el hecho está en el núcleo. Seis son el mismo paso: saber que dos valores se excluyen.
- **Consulta:** «el cronómetro se usa en las carreras» y «el jabón tarda un mes en estar listo» están bien guardados y las preguntas
  «¿dónde se usa…?» y «¿cuánto tarda… en estar listo?» no los encuentran.
- **Interconexión:** en cuatro preguntas de combinar los dos pasos se aciertan por separado y no se unen; en tres de ellas la búsqueda
  por texto contesta antes con la frase de la identidad. La quinta es un oficio de varias palabras («directora de orquesta»).

### 3.4 Fábrica (6)

«¿Con qué se golpean los timbales?» → «un martillo» (el texto: mazas). «¿Qué son las dunas?» → «un paisaje». Son pocas, pero son
respuestas falsas o inútiles dichas con seguridad cuando el texto tenía la buena.

## 4. Respuesta a las preguntas de fondo

**¿Faltan conceptos?** No. Ningún fallo se debe a que falte un concepto. Al contrario: seis se deben a que un concepto de fábrica
tapa lo que se acaba de leer.

**¿Falta diccionario?** Poco: 4 fallos de 61. Hay otros 4 en los que el diccionario ya tiene el dato y se descarta, y 2 en los que
el diccionario sobra. Ampliar el léxico a ciegas daría más de los últimos.

**¿Faltan capas de razonamiento?** Hace falta una, pequeña y concreta: saber que dos valores se excluyen (contrarios, cantidades
distintas de lo mismo, «solo»). Son 8 fallos, 6 de ellos el mismo paso. No es una capa general de lógica.

**¿Es un problema de interconexión entre conceptos?** Sí, pero no donde parecía. Unir dos hechos ya guardados falla poco (5). Lo que
falla es **unir cada frase con aquello de lo que se viene hablando**: sin sujeto, con pronombre, la segunda mitad de una coordinada.
Es interconexión en el momento de leer, no en el de razonar.

**Entonces, ¿qué es lo que más le cuesta?** Convertir en hechos, y colgar del tema correcto, las frases que no se sostienen solas.
Es un tercio de los fallos, está debajo de fallos que parecían de paráfrasis, de combinar y de contradicción, y nunca se ha
trabajado como tal: las vueltas anteriores mejoraron cómo se pregunta (sinónimos, encadenar, citar), no cómo se lee.

## 5. Orden que sale del diagnóstico

| Prioridad | Qué | Fallos que toca |
|---|---|---|
| 1 | **Leer las frases dependientes y colgarlas del tema de la frase anterior:** sin sujeto, segunda mitad con «y», «con ellos», «más de…», adverbio delante | 21 |
| 2 | **Excluir:** contrarios, cantidades distintas de lo mismo, «solo» | 8 |
| 3 | **Decidir mejor con el diccionario que ya hay:** aceptar cuando el parecido es alto y rechazar cuando la frase tiene un verbo mejor | 6 |
| 4 | **Lo leído manda sobre la fábrica** también en «¿con qué…?», «¿qué es…?» y «descríbeme…» | 6 |
| 5 | **Consultar los hechos que ya están:** «¿dónde se usa…?», «¿cuánto tarda en…?» | 5 |
| 6 | **Encadenar antes de citar la identidad** | 4 |
| 7 | Ampliar el diccionario | 4 |

Dos reservas. La comprobación de «hay un hecho en el núcleo» es automática (busca un hecho con el verbo y el dato) y puede fallar en
algún caso. Y 61 fallos repartidos en nueve causas dejan cifras pequeñas: el orden de las tres primeras es fiable, el de las demás no.

## 5 bis. Después de la 2.23 (lectura)

La vuelta siguiente trabajó solo la prioridad 1. Medido una vez, sin usar este examen para desarrollar:

| | 2.22 | 2.23 |
|---|---|---|
| Texto pegado | 82,7 % | **87,2 %** (16 preguntas ganadas, 0 perdidas) |
| Frase a frase | 82,1 % | **86,1 %** (15 ganadas, 1 perdida) |
| Fallos de lectura y de consulta | 26 | 14 |
| Fallos en total | 61 | 45 |

Detalle en `LCM_223_LECTURA.md`.

## 6. Cómo repetirlo

```
python -m lab.aprender.banco grande1b texto
python -m lab.aprender.banco grande1b frases
python -m lab.grande1.diagnostico
```
