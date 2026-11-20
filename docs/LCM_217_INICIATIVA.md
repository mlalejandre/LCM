# LCM 2.17 · Iniciativa: preguntar lo que falta, recibir las noticias y seguir el hilo

Hasta la 2.16 el LCM solo reaccionaba: apuntaba lo que se le decía («Entendido: …») y contestaba preguntas.
Esta ronda le da iniciativa, que era lo que más le separaba de una charla plena.

## 1. Qué hace ahora

- **Pregunta por lo que falta** (una sola pregunta por turno):
  - el hueco de lo que se cuenta: «me voy de viaje» → ¿adónde?; «tengo un gato» → ¿cómo se llama?; «ayer tuve un examen» → ¿qué tal te fue?
  - una palabra que no ha oído nunca: «tengo una pinfa» → ¿qué es una pinfa?
  - una persona nueva: «he quedado con Marta» → ¿quién es Marta?
- **Integra la respuesta en el hecho original.** «A Lisboa» se relee como «me voy de viaje a Lisboa»; «Bigotes» como «mi gato se llama Bigotes».
  No rellena casillas a mano: vuelve a leer la frase completa con el dato nuevo, y si lo que sale ya no es el mismo hecho, lo deshace.
- **Recibe las noticias con su tono:** enhorabuena, lo siento, mucha suerte, felicidades. En un duelo solo acompaña y no pregunta.
- **Sabe callarse:**
  - no pregunta si la persona acaba de preguntar o de contestarle, ni dos turnos seguidos;
  - no pregunta por lo que ya sabe (si el perro ya tiene nombre, no lo pide);
  - «no me hagas preguntas» lo apaga y «ya puedes preguntarme» lo enciende;
  - «prefiero no decirlo», «da igual» → «De acuerdo, no pasa nada».
- **Sigue el hilo:**
  - «pregúntame algo» → pregunta por lo que le falta saber; «¿qué no sabes de mí?» lo enumera;
  - «¿qué planes tengo?», «¿qué sabes de mi familia?», «¿qué le pasó a mi portátil?», «¿de qué estábamos hablando?»;
  - correcciones cortas: «perdona, los viernes, no los jueves», «no, en Segovia»;
  - continuaciones: «He encontrado trabajo.» «En una panadería.»;
  - la causa de algo que no dejó un hecho: «Hoy ha sido un día horrible.» «Es que se me ha estropeado el coche.»;
  - enlaza con lo ya contado: «me voy a Lisboa» → «Por cierto, me contaste que Elena vive en Lisboa»;
  - «¿qué me preocupa?» sin haberlo dicho: lo supone por lo malo o difícil que se ha contado, y dice que es una suposición.
- **Entiende más formas de la charla diaria:**
  - «me han despedido», «me operan mañana», «le han operado» (alguien lo hace, sin decir quién);
  - «las niñas», «los críos» son los hijos de quien habla; «le he comprado un tren» es para la persona de la que se hablaba;
  - «mi hermano Julio» (el mes como nombre), «Irene nada más rápido que Paula» (el verbo nadar), diminutivos («perrita»), «le flipa», «apunta que…».
- **Cierra lo pendiente de la 2.16:** grupos con sus nombres («con dos amigas: Sara y Noelia»), comparaciones encadenadas con verbo,
  «¿cuánto me queda?», causa entre turnos, despedidas con agradecimiento.

## 2. De dónde sale (conocimiento, no frases hechas)

Tres secciones nuevas en `conceptos_base.txt`, con herencia por la taxonomía:
- `[huecos]`: qué suele faltar por saber de cada cosa («tener animal: nombre» vale para un gato, un conejo o una perrita).
- `[tono]`: cómo se recibe cada noticia (logro, bueno, malo, duelo, reto, felicidades).
- `[acciones]`: el evento y la acción que es («cena: cenar»), para que «tengo una cena con Ana» conteste a «¿con quién ceno?».

Ampliar la iniciativa es añadir líneas ahí. La cartilla 2 (vida diaria, emociones, aficiones, lugares) suma 190 frases a la escuela:
314 frases leídas en total, 312 aprendidas (99,4 %).

Parte sigue siendo reconocimiento de formas: las peticiones sobre la charla («pregúntame algo», «cambiemos de tema») se detectan por patrón.

## 3. Método

1. Termómetro de conversaciones enteras, puntuadas turno a turno, escrito antes de construir nada (150 turnos).
   Una pregunta donde no toca cuenta como error grave, igual que una afirmación falsa.
2. Desarrollo con cuatro tandas propias (177 turnos). Primer intento: 92,9 %, 97,1 %, 86,7 %, 98,2 %.
3. Código congelado → examen limpio 17b, escrito sin probar sus frases, medido una vez.
4. Arreglos de lo visto (ya no ciegos) → código definitivo congelado → examen limpio 17c, medido una vez. No se ha tocado nada después.
5. Auditoría a mano de las dos versiones con el mismo criterio.

## 4. Métricas reales

| Prueba | 2.16 (antes) | 2.17 medida ciega | 2.17 final |
|---|---|---|---|
| Termómetro de conversaciones (150) | 51,3 % · 31 graves | — | 99,3 % · 0 (no ciega) |
| Limpio 17b (136) | 41,2 % · 36 graves | 83,1 % · 10 graves | 99,3 % · 0 (no ciega) |
| **Limpio 17c (109), medida final** | **45,0 % · 23 graves** | **94,5 % · 2 graves** | (no se tocó nada) |

Auditado a mano (los aprobados laxos cuentan como fallo):

| Prueba | 2.16 | 2.17 a ciegas |
|---|---|---|
| Limpio 17b | 34,6 % | 77,2 % |
| Limpio 17c (final) | 39,4 % | 94,5 % |

Cómo leerlas:
- **El 17b es la medida honesta del primer intento:** el corrector daba 83 %, pero leyendo las respuestas eran 77 %.
  Ocho aprobados decían algo mal (una fusión de frases rota, una causa contada en primera persona, dos nombres pegados).
- **El 17c es la medida final.** Los dos «graves» son omisiones (una enhorabuena y una pregunta que faltan):
  no hay ninguna afirmación falsa ni ninguna pregunta indebida.
- Los tres exámenes los escribo yo. Las formas son las que yo imagino; contigo fallará más.

Por capacidad en el 17c (2.16 → 2.17):

| Capacidad | 2.16 | 2.17 |
|---|---|---|
| Preguntar lo que falta | 14,3 % | 100 % |
| Callar cuando no toca | 73,3 % | 100 % |
| Integrar la respuesta | 20,0 % | 86,7 % |
| Tono | 46,7 % | 93,3 % |
| Hilo de la charla | 56,2 % | 87,5 % |
| Pertinencia general | 42,9 % | 92,9 % |
| Pendientes de la 2.16 | 55,0 % | 100 % |

Controles:
- Exámenes antiguos sin cambios: autor 89,76 %, ciego 2 94,68 %, ciego 6 80,60 %, ciego 7 79,07 %, termómetro de la 2.16 96,59 %, limpio 16b 96,48 %.
- Regresiones: solo las cuatro conocidas de rondas anteriores. pytest: 884 pruebas pasan.
- **Cuánto pregunta:** en 293 afirmaciones de exámenes antiguos, la 2.16 preguntaba en 9 y la 2.17 en 15.
  De las seis nuevas, cinco son razonables y una es indebida («no me gusta nada madrugar» → «¿qué es un madrugar?»).

## 5. Lo que sigue verde

Fallos de la medida final:
- «Me han concedido la hipoteca» no recibe enhorabuena: la tabla de tono aún es pequeña (unas 70 entradas).
- «Uno de aventuras», como respuesta a «¿Qué libro es?», no se integra.
- «Pregúntame lo que quieras» lo toma como permiso y no pregunta.
- «Pues nada, hasta luego» no lo entiende.
- «¿Una peluquera es una persona?» no lo sabe.
- Tras dos cosas seguidas con hueco solo pregunta por la primera; es la regla de no preguntar dos turnos seguidos.

Otros vistos:
- Pregunta indebida por un verbo que no está en su léxico («madrugar»).
- «Tengo una hermana y dos hermanos» → pregunta «¿cómo se llama?» en singular.
- Alguna causa se cuenta de vuelta en primera persona («porque ayer no dormí nada»).
- No retoma un tema otro día («¿qué tal fue el examen?»): los hechos no guardan la fecha en que se dijeron.
- «No me han ascendido» seguido de «me han ascendido» se queda con lo primero.
- «¿Cómo van mis hijos al colegio?» no se contesta aunque se haya dicho.
- «¿Un coche tiene alas?» sigue diciendo «no me consta».
- Las reacciones son pocas y se repiten.
- La multimodalidad no se ha tocado en esta ronda; sus pruebas siguen pasando.
