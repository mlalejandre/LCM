# LCM 2.22 · Lo leído manda sobre la fábrica, sinónimos por otros idiomas y contraste de cantidades

Sigue el plan de `LCM_221_FRASE_A_FRASE.md` (§6). Misma regla: nada depende del tema.

## 1. Análisis previo (antes de tocar nada)

Línea base de la 2.21 con el texto pegado en los once bancos: 732 preguntas, 98 fallos (86,6 % de acierto). Clasificados
(`lab/iter222/fallos_221.json`):

| Tipo de fallo | N.º |
|---|---|
| Se abstiene ante una paráfrasis (falta el sinónimo) | 26 |
| Se abstiene en una deducción | 12 |
| Se abstiene en una pregunta literal | 10 |
| Cita una frase que no contesta | 9 |
| No aplica a una persona lo aprendido de su oficio | 7 |
| No detecta que una afirmación contradice lo leído | 6 |
| No sabe combinar dos frases | 6 |
| La fábrica contradice o tapa lo leído | 9 |
| Otros | 13 |

## 2. Qué cambia

- **Lo leído manda sobre la fábrica en preguntas de clase** (`conceptos._padres_aprendidos`). «La lonja es el mercado donde…» hace
  que la lonja sea un mercado, aunque el diccionario la tenga como edificio. Además se encadena con lo demás: el vampiro es un
  murciélago (leído), el murciélago es un mamífero (leído), el mamífero es un animal (fábrica) → el vampiro es un animal.
- **Sinónimos por los otros idiomas** (`vectores.puentes`). La base de conceptos tiene las palabras de cada sentido en ocho idiomas.
  Si dos sentidos que el léxico español no enlaza comparten palabra en al menos dos idiomas más, es un indicio de que dicen lo mismo:
  «transformar»/«convertir», «demorar»/«tardar», «cocinar»/«cocer». Salen 15 550 parejas nuevas.
- **El indicio es débil y se trata como tal.** A ojo, solo la mitad de esas parejas son buenas. Por eso solo vale si la pregunta
  rehecha tiene respuesta, la respuesta usa ese verbo, y la frase citada trae ella misma todo lo demás que se pregunta.
- **Oficios en femenino y oficios solo leídos** (`exposicion.por_clase`). «Mi abuela es papelera» hereda lo aprendido de «los
  papeleros»; y también vale cuando la frase del oficio solo está leída y el núcleo no la convirtió en un hecho.
- **Contraste de cantidades y de momentos del día.** «El préstamo dura dos semanas» frente a «dura tres semanas»; «cierra por la
  noche» frente a «cierra a mediodía»; y frente a frases que empiezan por «Sus…».
- **Frases sin sujeto y términos de varias palabras:** el tema de «Tiene más de cien puestos» se guarda como «el mercado central»,
  no como la pieza interna; eso arregla la pregunta literal y el encadenado que dependía de ella.
- **Arreglos después de la primera medida (no ciegos):** «¿quién…?» no se contesta con una pasiva sin agente («los libros se
  ordenan…»); «¿cuánto…?» rehecha por el sentido exige una cantidad en la respuesta.
- Menores: «de madrugada», «a mediodía» cuentan como respuesta a «¿cuándo…?»; «puesto», «hecho» valen como nombres además de participios.

## 3. Lo que se probó y se descartó

- **Contestar con un «si X quiere decir Y…»** cuando solo hay parecido de vectores: de las 26 paráfrasis habría resuelto cuatro o
  cinco, con un número parecido de respuestas condicionadas equivocadas. No se hizo.
- **Exigir a toda pregunta rehecha que la frase traiga todo lo preguntado** quitaba respuestas buenas. Se dejó solo para el indicio débil.

## 4. Métricas

Corrector automático salvo donde dice «auditado». «Falsas» = respuestas que afirman algo incorrecto.

**Temas ya conocidos** (once bancos, 732 preguntas con el texto pegado; no es a ciegas):

| | 2.21 | 2.22 |
|---|---|---|
| Aciertos con el texto pegado | 634 (86,6 %) | **652 (89,1 %)** |
| Preguntas que pasan a acertarse / a fallarse | | 18 / 0 |
| Frase a frase (nueve bancos, 605 preguntas): ganadas / perdidas | | 12 / 0 |

Por tema, texto pegado: dev 96,0 → 97,0 · test 88,4 → 90,5 · test4 89,2 → 90,8 · test5 81,9 → 84,3 · test7 94,3 → 97,1 ·
test8 60,0 → **80,0** · pdev 80,9 → 85,3; el resto igual.

**Primera medida limpia** (`test9`: la biblioteca y el huerto, 66 preguntas; código congelado, medida una vez):

| | 2.21 | 2.22 a ciegas | 2.22 final (no ciego) |
|---|---|---|---|
| Texto pegado: acierto (falsas) | 87,9 % (6) | **89,4 %** (5) | 90,9 % (3) |
| Frase a frase: acierto (falsas) | 87,9 % (6) | **89,4 %** (5) | 90,9 % (3) |
| Auditado, texto pegado | 89,4 % | 90,9 % | 92,4 % |

Auditoría: «Las lechugas crecen muy rapidas» cuenta como fallo por la concordancia; el dato es correcto, en las dos versiones.
La única pregunta ganada a ciegas es un contraste de cantidad («dura dos semanas»). Las cuatro preguntas de combinar dos frases
se aciertan en las dos versiones: es la primera vez que el encadenado de la 2.21 se confirma a ciegas.

**Segunda medida limpia** (`test10`: el puerto, 32 preguntas; código definitivo, medida una vez, nada tocado después):

| | 2.21 | 2.22 |
|---|---|---|
| Texto pegado: acierto (falsas) | 84,4 % (2) | 84,4 % (2) |
| Frase a frase: acierto (falsas) | 84,4 % (2) | 84,4 % (2) |
| Auditado | 87,5 % | 87,5 % |

Ninguna pregunta cambia. Las cinco que fallan: «¿el práctico es una persona?» (hay que pasar por «marino»), «reparar»/«arreglar»
(pregunta al usuario en vez de contestar), una respuesta de fábrica correcta que el corrector no acepta, un encadenado, y un
contraste de hora («a las ocho» frente a «a las cinco»).

## 5. Lectura honrada

- **En temas nuevos la mejora de esta vuelta es de una pregunta sobre 98.** Lo arreglado era real (18 preguntas en los temas
  conocidos, ninguna perdida), pero en los dos temas nuevos casi no aparecían esos tipos de fallo.
- **El modelo está ya entre el 84 % y el 90 % en temas nuevos**, y lo que queda es una cola larga de casos distintos. Cada arreglo
  general resuelve una o dos preguntas por tema. Con exámenes de 30-70 preguntas eso queda dentro del ruido.
- **Texto pegado y frase a frase dan ya lo mismo** en los dos temas nuevos: se confirma lo de la 2.21.
- **Los puentes entre idiomas son un indicio ruidoso.** Con las tres comprobaciones no han dado ninguna respuesta falsa en las
  medidas, pero la muestra de trampas es pequeña (unas 90 preguntas).
- Siguen dos errores por polisemia del léxico que vienen de la 2.20: «arreglar» entendido como «ordenar» y «costar» como
  «necesitar» (este último ya no sale tras el arreglo no ciego).
- Sin tocar: respuestas torpes de la capa antigua, «¿de qué color es el buzón en España?», contraste de horas.

## 6. Siguiente vuelta

Con estos números, seguir afinando tipos de fallo sueltos rinde poco. Dos caminos con más recorrido:

1. **Medir mejor antes de seguir:** un examen limpio grande (300 preguntas o más, diez temas) para que una mejora de dos puntos se
   pueda distinguir del ruido, y para saber qué tipos de fallo pesan de verdad en temas nuevos.
2. **Cambiar de frente:** la conversación larga y mezclada (charla personal más cosas aprendidas, varios temas a la vez, correcciones),
   que es el uso real y está mucho menos medido que «leer un texto y contestar».

## 7. Verificación

- **Regresiones** (tandas 01-15 e iter26…iter222): todo al 100 % salvo las cuatro de siempre. Tanda nueva `lab/iter222/t01.py`: 119 sondas, 100 %.
- **Controles, idénticos a la 2.21:** autor 90,04 % · ciego2 94,68 % · ciego6 82,09 % · ciego7 79,07 % · termómetro 96,59 % ·
  16b 96,48 % · 16c 100 % · 17b 99,26 % · 17c 94,50 % · conversa17 99,33 %.
- **Pytest:** 913 pasan; fallan los 3 de entorno de siempre.
- Compilado y ejecutado también con Python 3.11.
