# LCM 2.26 · El hilo de la conversación: el orden de los pasos y lo que deja de ser verdad

Segunda vuelta automática. Sale de la lista de «visto y no arreglado» de la 2.25.

## 1. Resumen

| | 2.25 | 2.26 |
|---|---|---|
| Primera medida limpia (6 conversaciones, 28 turnos, medida única) | 35,7 % · 1 falsa | **75,0 % · 2 falsas** (11 ganadas, 0 perdidas) |
| Segunda medida limpia, escrita tras arreglar lo que falló en la primera (3 conversaciones, 14 turnos) | 7,1 % · 3 falsas | **92,9 % · 1 falsa** |
| Conversaciones de desarrollo (7, 33 turnos) | 63,6 % · 3 falsas | 87,9 % · 2 falsas |
| Conversaciones limpias de la 2.25 | 91,5 % | 91,5 % |

Son medidas pequeñas (28 y 14 turnos): dicen que el mecanismo funciona con contenido nuevo, no dan un porcentaje fino.

## 2. Qué se rompía

Conversé sobre tres cosas que una persona da por supuestas al hablar:

| Qué | Antes |
|---|---|
| «Primero caliento el agua. Luego muelo el café… Al final añado azúcar.» y después «¿qué hago primero?» | Soltaba todos los pasos juntos, o «no tengo gustos ni experiencia propia para recomendarte nada» |
| «Tengo que comprar pan y llamar a mi madre.» «Ya he comprado el pan.» «¿qué me falta?» | «No me has dicho qué te falta» |
| «Mi coche está en el taller.» «Ya lo he recogido.» «¿sigue en el taller?» | «No lo sé… sé que está en el taller» |

Y un fallo de lectura: «Ya **lo he** recogido» se guardaba como «has tu coche recogido».

Nada de esto es saber cosas del mundo. Es saber cómo se cuenta: las marcas de orden, «tengo que» frente a «ya he», y que «ya» anuncia un cambio.

## 3. Qué cambia (`src/nucleo20/hilo.py`, nuevo)

- **Pasos en orden.** Una frase que empieza por «primero / luego / después / a continuación / más tarde / por último / al final /
  finalmente» se apunta como un paso. Se contesta a «¿qué hago primero?», «¿por dónde empiezo?», «¿qué hago después de X?», «¿y antes de
  X?», «¿cuál es el último paso?», «¿cuántos pasos son?», «¿y luego?». El paso se devuelve en segunda persona («calientas el agua»),
  también con verbos que la morfología no conoce («muelo» → «mueles»).
- **Tareas.** De «tengo que A, B y C» salen tres tareas. Una se da por hecha cuando después se dice el mismo verbo en pasado («ya he
  regado las plantas», «pagué el alquiler») con el mismo objeto. «¿Qué me falta?» es la diferencia.
- **«Ya no».** A «¿sigue X…?» o «¿sigo…?»: se busca el estado que se dijo; si después se dijo algo con «ya» sobre lo mismo (como
  sujeto, objeto o destinatario), la respuesta es «No, ya no: …»; si el propio núcleo ya lo había sustituido («estoy enfadado» → «ya
  estoy tranquilo»), también; y si no hay nada posterior, «Que yo sepa, sí».
- **«Ya lo he recogido»** se lee como «ya lo recogí» y el objeto queda bien puesto. Solo en esa forma («ya lo/la he…»): al aplicarlo a
  cualquier «la he llamado…» se rompía una tanda antigua, así que el resto sigue como estaba.

## 4. Medidas limpias

**Primera** (escrita con el código congelado, sin ejecutar): 10 de 28 → 21 de 28. Lo que falló y por qué:

- La lista «Hoy tengo que pagar el alquiler, regar las plantas y escribir a Marcos» no dejaba hecho en el núcleo, y yo sacaba las
  tareas de los hechos. Ahora salen de lo dicho tal cual.
- «¿sigo enfadado?» tras «ya estoy tranquilo»: el núcleo había retirado «enfadado» y no lo encontraba.
- «Ya **le** han dado el alta»: mi padre es el destinatario, no el sujeto.
- «¿sigue en el taller el coche?» casaba con un hecho derivado («el taller tiene el coche»).

Los arreglé (21 → 28 de 28 en esas mismas, que ya no vale como medida) y escribí una **segunda** tanda nueva sin ejecutarla: 1 de 14 →
13 de 14. La que falla: «Ya lo he traído al piso nuevo» no se enlaza con «mi gato está en casa de mi madre», y contesta «que yo sepa, sí».

## 5. Lo que sigue pendiente

- Deducciones entre datos personales: «el padre de Clara» (mi hija, mi marido), «¿cuántos somos en casa?».
- «¿en qué habitación están las llaves?» (el cajón está en la cocina).
- Causas entre frases seguidas («estoy cansado» + «he dormido poco» → «¿por qué?»); cuando se dice con «porque» en la misma frase ya funciona.
- Pasos dichos sin marca de orden, o varios en una sola frase.
- «¿sigue…?» depende de que el cambio se diga con «ya». «He recogido el coche» a secas no cierra el estado.

## 6. Salvedades

- Las preguntas reconocidas son formas fijas («¿qué hago después de…?», «¿qué me falta por hacer?»). Dichas de otra manera caen al
  camino normal y fallan como antes.
- «Que yo sepa, sí» es una respuesta nueva donde antes había un «no lo sé». Es más útil, pero es una afirmación: si el estado cambió
  sin que se dijera con «ya», será falsa (pasa una vez en la segunda medida).

## 7. Interruptor y verificación

`LCM_SIN_HILO=1` (con él, las medidas vuelven a 35,7 % y 7,1 %).

Tandas 01–15 e iter26…iter226: fallan solo las 4 conocidas. Tanda nueva `lab/iter226/t01.py`: 70 sondas, 100 %. Controles: idénticos a la 2.25 (autor 90,18 %, ciego 2 95,02, ciego 6 83,58, ciego 7 79,07, termómetro 97,07, 16b 97,18, 16c 100, 17b 99,26, 17c 94,50, conversa17 99,33). Pytest: 974 pasan; fallan los 3 de entorno de siempre.

Para repetir: `python -m lab.iter226.charla charlas_test` y `python -m lab.iter226.charla charlas_test2`.
