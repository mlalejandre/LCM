# LCM 2.21 · Aprender frase a frase, encadenar dos cosas y sinónimos que enseña el usuario

Sigue el plan de `LCM_220_SENTIDO.md` (§6). Misma regla: nada depende del tema.

## 1. Análisis previo (antes de tocar nada)

Línea base de la 2.20 en los siete temas ya medidos, 500 preguntas, comparando el texto pegado con las mismas frases dichas una a una:

| | Preguntas |
|---|---|
| Aciertan de las dos maneras | 397 |
| Aciertan con el texto pegado y fallan frase a frase | **49** |
| Fallan de las dos maneras | 51 |
| Solo aciertan frase a frase | 3 |

El mayor hueco medido era ese: 10 puntos perdidos solo por explicar las cosas una a una, que es como habla una persona.
La causa principal: al explicar frase a frase, lo que el núcleo no convertía en un hecho no quedaba guardado para poder citarlo.

## 2. Qué cambia

- **Lo que se explica frase a frase se puede citar** (`exposicion.charla`). Toda frase que explica algo general queda guardada como al
  leer un texto, la entienda quien la entienda, y también las frases sin sujeto que siguen el tema («Lleva un traje blanco»).
  No se guarda lo que se cuenta de una persona con nombre: eso sigue siendo del núcleo, que sabe olvidarlo y corregirlo.
- **Saber si una frase habla en general** (`_impersonal`). «Un traje», «varias semanas», «dibujar figuras», «es blando» ya no se
  toman por verbos en primera o segunda persona.
- **Encadenar dos cosas aprendidas** (`cadena.py`). Si la pregunta nombra algo por una descripción que lo aprendido identifica con un
  nombre («el Transiberiano es el recorrido en tren más largo del mundo»), se cambia la descripción por el nombre y se vuelve a
  preguntar. La respuesta dice el paso: «Transiberiano tarda siete días. Lo junto con otra cosa que aprendí: …». El segundo paso
  solo vale si sale de lo aprendido, no de lo que «suele» pasar según la fábrica.
- **Sinónimos que enseña el usuario** (`sinonimia.declara`, `aprende`). «Despachar es lo mismo que vender», «un chiringo es lo mismo
  que un puesto»: valen desde ese momento igual que un sinónimo del léxico, también para palabras que el léxico no tiene. Se guardan
  con el usuario.
- **Decir qué palabra falta.** Cuando no sabe contestar y el verbo de la pregunta no aparece en nada de lo aprendido, lo dice:
  «En lo que he aprendido no aparece «vigilar»; si es otra forma de decir algo, dímelo». Así el usuario puede enseñar el sinónimo.
- **Preguntar en vez de adivinar**, solo cuando el léxico da un enlace débil y el núcleo confirma que con esa palabra habría
  respuesta: «¿«X» quiere decir aquí lo mismo que «Y»?». Un «sí» lo aprende y contesta; un «no» se recuerda.
- **La cita, más estricta:** para un sí o un no la frase tiene que decir todo lo preguntado; «algunos pájaros vuelan» no contesta
  «¿vuelan los pájaros?»; «¿cómo es X?» pide una frase que describa a X; las palabras genéricas de la pregunta («se llama») pesan menos.
- **Lo explicado manda sobre lo que «suele» pasar:** si el núcleo solo tiene la respuesta de fábrica y lo leído dice otra cosa, se cita lo leído.
- «¿Cómo se llama la persona que recibe la carta?» ya no devuelve a quien la reparte: los verbos de las dos descripciones tienen que
  coincidir o decir lo mismo (con los vectores del léxico).

## 3. Lo que salió mal por el camino

- **Guardar todo lo que no fuera personal** rompió siete tandas antiguas: «¿Dónde vive Pedro?» se contestaba citando «Juan vive en
  Londres». Se limitó a lo que explica algo general.
- **Proponer el sinónimo por parecido de vectores** daba preguntas absurdas («¿«comprar» es lo mismo que «quitar»?»). El léxico no
  permite distinguir «vigilar»/«cuidar» (0,41, sin enlace) del ruido. Por eso lo normal es decir qué palabra falta y que enseñe el usuario.
- **Quitar el nombre que sigue a «de qué…»** de lo exigido a la cita («¿de qué país es X?») hacía contestar a «¿de qué material son las
  piezas?» con cualquier frase sobre piezas. Retirado.

## 4. Métricas

Corrector automático salvo donde dice «auditado». «Falsas» = respuestas que afirman algo incorrecto.

**Primera medida limpia** (`test7`: el papel y el queso, 70 preguntas; código congelado, medida una vez):

| | 2.20 | 2.21 a ciegas | 2.21 final (no ciego) |
|---|---|---|---|
| Texto pegado: acierto (falsas) | 94,3 % (2) | 92,9 % (2) | 94,3 % (0) |
| Frase a frase: acierto (falsas) | 74,3 % (7) | **78,6 %** (8) | 84,3 % (3) |
| Combinar dos frases | 50 % | 50 % | 75 % |

A ciegas la 2.21 pierde una pregunta con el texto pegado: la 2.20 acertaba «¿una caja de cartón es de papel?» con un «Sí» apoyado en
una frase que no lo dice («Con cartón se hacen cajas»); la cita estricta ahora se abstiene. El encadenado no llegó a actuar a ciegas
porque la cita contestaba antes con la frase de la identidad; se cambió el orden después de medir (no ciego).
Este examen no sirvió para medir los sinónimos enseñados: el léxico ya conocía las dos parejas que elegí.

**Segunda medida limpia** (`test8`: el mercado, 35 preguntas, con palabras de jerga enseñadas; código definitivo, medida una vez):

| | 2.20 | 2.21 |
|---|---|---|
| Texto pegado: acierto (falsas) | 54,3 % (5) | **60,0 %** (5) |
| Texto pegado, auditado | 57,1 % (4) | **62,9 %** (4) |
| Frase a frase: acierto (falsas) | 48,6 % (5) | **60,0 %** (5) |
| Frase a frase, auditado | 51,4 % (4) | **62,9 %** (4) |
| Combinar dos frases | 0 % | 0 % |

Auditoría: «Eso queda fuera de lo que sé hacer…» ante «¿cuánto cuesta el pescado?» es una abstención correcta que el corrector
cuenta como falsa, en las dos versiones. De las tres preguntas que dependían de un sinónimo enseñado acierta una («despachar»);
las otras dos («chiringo») fallan porque la pregunta literal equivalente también falla.
Es el tema más difícil medido hasta ahora: la fábrica contradice al texto («No, un frutero es un profesional»; «No, una lonja es un edificio»).

**Temas ya conocidos** (2.20 → 2.21):

| Tema | Texto pegado | Frase a frase |
|---|---|---|
| dev | 96,0 → 96,0 | 89,1 → **95,0** |
| test | 88,4 → 88,4 | 85,3 → **91,6** |
| test2 | 94,8 → 94,8 | 79,3 → **86,2** |
| test3 | 93,3 → 93,3 | 81,7 → **85,0** |
| test4 | 86,2 → **89,2** | 75,4 → **86,2** |
| test5 | 80,7 → **81,9** | 71,1 → **77,1** |
| test6 | 81,6 → 81,6 | 68,4 → **78,9** |

Banco de paráfrasis `pdev` 80,9 → 80,9; setas 72,9 → 72,9. De las 49 preguntas que solo fallaban frase a frase quedan 19.

## 5. Lectura honrada

- **Lo que mejora de verdad es el modo frase a frase:** +4 y +11 puntos en temas nuevos y entre +3 y +11 en los conocidos.
- **Con el texto pegado no hay mejora demostrada en temas nuevos:** −1,4 en la primera medida a ciegas y +5,7 en la segunda, sobre 70 y 35
  preguntas. Con muestras así, una o dos preguntas mueven el resultado.
- **Encadenar funciona en lo conocido y no se ha demostrado en lo nuevo:** 2 de 2 en `test4` y 3 de 4 en `test7` después del arreglo,
  pero 0 de 2 en la segunda medida limpia. Ahí el segundo paso («¿cuántos puestos tiene el mercado central?») falla también preguntado
  directamente: «Tiene más de cien puestos» no queda unido a su tema.
- **Los sinónimos enseñados funcionan** cuando la pregunta equivalente tiene respuesta; no arreglan una pregunta que ya fallaba.
- **El aviso «no aparece «X»»** se añade a muchas abstenciones después de leer algo. Es útil la primera vez; puede cansar.
- Sigue sin tocar: respuestas torpes de la capa antigua («La leche añadir a la leche», «El pan hacer con Harina»), la fábrica
  contradiciendo al texto en preguntas de clase, «el mercado cierra por la noche» sin detectar el contraste.

## 6. Siguiente vuelta (por impacto esperado)

1. Lo leído o explicado manda sobre la fábrica también en preguntas de clase («¿la lonja es un mercado?»).
2. Unir las frases sin sujeto a su tema dentro del núcleo, no solo en la cita («Tiene más de cien puestos»).
3. Sustituir las respuestas torpes de la capa antigua por una abstención o una cita.
4. Contraste con lo explicado cuando el complemento es de tiempo o de lugar.

## 7. Verificación

- **Regresiones** (tandas 01-15 e iter26…iter221): todo al 100 % salvo las cuatro de siempre (iter26 t11, iter28 t23, iter210 t01,
  iter214 t05). Tanda nueva `lab/iter221/t01.py`: 88 sondas, 100 %.
- **Controles:** autor 89,90 → 90,04 % (una más); ciego2 94,68 % · ciego6 82,09 % · ciego7 79,07 % · termómetro 96,59 % · 16b 96,48 % ·
  16c 100 % · 17b 99,26 % · 17c 94,50 % · conversa17 99,33 %, idénticos.
- **Pytest:** 909 pasan; fallan los 3 de entorno de siempre.
- Compilado y ejecutado también con Python 3.11.
