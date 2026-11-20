# LCM 2.19 · Aprender de un texto, segunda vuelta

Sigue el plan de `LCM_218_APRENDER.md`. Misma regla: nada depende del tema; todo trabaja por la forma de la frase.
Los cinco temas de las medidas anteriores pasan a ser de desarrollo y la medida se hace con temas nuevos.

## 1. Qué cambia

- **Términos de varias palabras** (`compuestos.py`). «La Torre de Hércules», «La Coruña», «Apolo 11», «el zorro volador»,
  «un café solo» entran como una sola pieza y salen con su forma.
  - Lo que se dice del zorro volador ya no se apunta al zorro, ni lo del café solo a todo el café.
  - «Está en La Coruña», después de hablar de la Torre de Hércules, sabe de quién habla.
  - El apellido suelto («Armstrong») se entiende cuando solo hay una persona conocida con ese apellido.
  - Nombre + adjetivo solo se une cuando se explica algo general; «el coche rojo es de Ana» sigue igual.
- **Preguntar con otras palabras** (`sinonimia.py` y dos secciones nuevas en la base de conceptos). Si una pregunta no
  encuentra respuesta se rehace con equivalentes: «¿de qué se alimentan?» = «¿qué comen?», «comida» = «alimento».
- **Más formas de frase:** «la mayoría de los… pero algunos…», «fue la primera persona que…», «X es el alimento de Y»,
  «…y la construyeron los romanos», «Por eso…» al empezar la frase, «son agujeros que…», dos verbos unidos por «y»,
  complemento adelantado sin sujeto («En tierra caminan despacio»).
- **Contraste con las frases leídas**, aunque no dejaran un hecho: valores contrarios («de día» / «de noche»), dos colores
  distintos, o afirmar lo que el texto negaba.
- **La charla que explica** usa ya las mismas reglas que la lectura, también con sujeto propio, y lo que no entiende queda
  guardado para poder citarlo.
- **Giros de la charla:** «volviendo a las setas, ¿…?», «cambiando de tema, …» ya no estorban.
- **Herencia de clase a individuo** con otro tiempo verbal («mi abuelo era olivarero» → cultivaba olivos).

## 2. Métricas

Corrector automático salvo donde dice «auditado». «Falsas» = respuestas que afirman algo incorrecto.

**Medida final limpia** (el olivo y los trenes, 65 preguntas; escrita con el código definitivo congelado, medida una vez):

| | 2.18 | 2.19 |
|---|---|---|
| Sin texto | — | 23,1 % |
| Texto pegado | 78,5 % · 5 falsas | **83,1 % · 4 falsas** |
| Texto pegado, auditado a mano | 78,5 % | **80,0 %** |
| Frase a frase en la charla | 70,8 % · 7 falsas | **75,4 % · 6 falsas** |

**Primera medida limpia** (pingüinos y el pan, 60 preguntas; primer intento a ciegas):

| | 2.18 | 2.19 a ciegas | 2.19 tras arreglos (no ciega) |
|---|---|---|---|
| Texto pegado | 76,7 % · 6 falsas | 81,7 % · 5 | 93,3 % · 4 |
| Frase a frase | 70,0 % · 7 falsas | 73,3 % · 7 | 81,7 % · 7 |

**Temas ya conocidos** (se usaron para desarrollar; no son medida limpia), texto pegado, 2.18 → 2.19:

| Tema | 2.18 | 2.19 |
|---|---|---|
| Faros y la Luna | 74,1 % · 6 falsas | 94,8 % · 0 |
| Murciélagos, café, animal inventado | 81,1 % · 7 | 88,4 % · 5 |
| Abejas, volcanes, ajedrez | 94,1 % · 0 | 96,0 % · 0 |
| Setas | 67,8 % · 5 | 72,9 % · 6 |

Controles: los diez exámenes anteriores quedan exactamente igual. Regresiones: solo las cuatro conocidas. pytest: 894 pasan.

## 3. Cómo leerlas: la mejora en temas nuevos es pequeña

- En los temas que ya había visto, esta vuelta sube entre 5 y 20 puntos. **En temas nuevos sube unos 5 puntos con el
  corrector y 1,5 auditada a mano.**
- La serie de medidas a ciegas con texto pegado lo confirma: +13,6 y +15,5 en la 2.18; +5,0 y +4,6 en la 2.19.
- Por tipo de pregunta, en la medida final: charla con lo aprendido 75 → 100 % y contradicción 0 → 50 %.
  **Paráfrasis y combinar dos frases siguen en 0 %**, aunque eran objetivo de esta vuelta: las equivalencias que añadí no
  eran las que hicieron falta («elaborar» / «fabricar», «llevar» / «conducir»).
- Conclusión: **añadir formas de frase y equivalencias a mano rinde cada vez menos.** Cada texto nuevo trae formas y palabras
  que no estaban previstas.
- La auditoría descubrió además un fallo mío: dos definiciones salen embarulladas («la vía es circulan sobre dos raíles de
  acero»). Lo vi después de la medida final y no lo he tocado.

## 4. Lo que sigue verde

- Paráfrasis con sinónimos no previstos y combinar dos frases.
- Definiciones con «llamado/a» mal recortadas (el fallo de arriba).
- «Dime dos tipos de aceitunas» devuelve uno solo.
- Contradicción sobre un número («tarda dos días» frente a «siete días»).
- Deducciones con un paso de sentido común («hoja perenne» → no pierde las hojas).
- La vía frase a frase sigue unos 8 puntos por debajo del texto pegado.
- Sentido común (comestible, venenoso, peligroso): sin tocar.

## 5. Propuesta para la siguiente vuelta

Cambiar de palanca en vez de seguir añadiendo reglas:
1. **Sinónimos desde el léxico del proyecto** (ya trae grupos de sinónimos para decenas de miles de palabras), en lugar de una
   lista escrita a mano. Es lo que puede mover la paráfrasis sin prever cada palabra.
2. **Reforzar la cita**, que es el mecanismo que mejor generaliza (las preguntas literales están en el 95 %): que sirva también
   para combinar dos frases, citando las dos.
3. **Medir por componente** (qué parte de cada acierto viene del núcleo, de las reglas de exposición o de la cita) para invertir
   donde generaliza.
