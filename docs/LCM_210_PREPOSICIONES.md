# LCM 2.10 · Valor conceptual de las preposiciones

Parche sobre la 2.9. No se reentrena nada. No añade hechos del mundo: solo conceptos (qué papel tiene cada preposición y a qué clase pertenecen las cosas).

## Idea
Una preposición no tiene un significado fijo. Propone varios **papeles** y los decide la **clase del término**, que el núcleo conoce de fábrica, junto con el **verbo**.

| Preposición | Término | Papel | Ejemplo |
|---|---|---|---|
| con | persona | compañía | trabajo con mi primo |
| con | objeto | instrumento | corto el pan con un cuchillo |
| con | actitud | modo | trabaja con mucho cuidado |
| de | lugar (ser/venir) | origen | soy de Zamora |
| de | material | materia | un anillo de plata, la silla es de roble |
| de | persona (ser) | posesión | el anillo era de mi abuela |
| de | — (hablar, escribir…) | tema | hablamos de ciclismo |
| en | lugar | lugar | vivo en Valencia |
| en | vehículo | medio | voy en bici |
| en | mes, año | tiempo | en marzo |
| por | lugar (pasar, ir…) | recorrido | pasaremos por Jaén |
| por | fenómeno, enfermedad, actividad | causa | por la lluvia, por la fiebre |
| por | partes del día | tiempo | por las noches |
| para | infinitivo, evento | finalidad | para el examen |
| para | persona, organización | destinatario | para mi madre |
| para | lugar (trabajar…) | destinatario | trabaja para un hotel |
| para | tiempo | plazo | para el lunes |
| desde / hasta | hora, tiempo | inicio / final | desde marzo, hasta las dos, de nueve a dos |
| desde / hasta | lugar | origen / destino | desde la estación |
| durante | — | duración | durante dos horas |
| contra | persona, organización | oponente | contra el equipo de Toni |
| sin | — | carencia | sin azúcar |
| sobre | tema, persona | tema | un libro sobre mi abuelo |
| sobre | mueble, objeto | posición | sobre la mesa |
| según | — | fuente | según mi madre |
| ante, bajo, tras, cabe, so | según el término | posición o tiempo | |

**Locuciones:** encima de, debajo de, delante de, detrás de, al lado de, junto a, dentro de, fuera de, cerca de, lejos de, enfrente de, alrededor de, entre, antes de, después de.

Las preguntas buscan un **papel**, no una palabra:
- «¿dónde?» encuentra «en», «encima de» o «al lado de»;
- «¿por qué?» encuentra la causa, aunque se dijera con «por»;
- «¿cómo voy?» encuentra el medio («en bici»);
- «¿hasta qué hora abre?» encuentra el final de «de nueve a dos».

Las preguntas antiguas ahora también **filtran por papel**. «¿Con quién corto la madera?» ya no contesta «con una sierra». «¿Para qué trabaja mi tía?» ya no contesta «para un hotel».

**Espacio** (conceptos, no datos):
- A encima de B ⇔ B debajo de A;
- delante ⇔ detrás;
- al lado y cerca son simétricas;
- cerca y lejos son contrarias.

Así responde a «¿La cama está encima de la mochila?» → «Sí: lo deduzco porque tu mochila está debajo de la cama», y a «¿Mi casa está cerca de la playa?» → «No: tu casa está lejos de la playa». Si no hay nada que deducir, se abstiene.

**Multimodal:** una imagen con varias figuras se separa en regiones. Cada figura tiene su forma (se añade la estrella) y su color, y se calcula cómo están colocadas (arriba, abajo, izquierda, derecha, dentro). Responde a «¿qué figura está encima?», «¿qué hay debajo del cuadrado?», «¿de qué color es la de arriba?» y «¿el cuadrado está encima del triángulo?».

**Conceptos de fábrica añadidos** (categorías, no hechos): eventos, tiempos (días, meses, partes del día), actitudes, enfermedades, actividades, organizaciones, condimentos, medios de comunicación, maderas como material, accesorios, partes de la casa, documentos, y más lugares, aparatos y herramientas.

**Sintaxis:** el complemento de tiempo o frecuencia que va delante se pasa detrás («Después del turno ceno…», «Todas las mañanas paso…»). «Ayer jugamos» queda en pasado.

## Método
1. Antes de tocar el código, con la 2.9 congelada, se escribieron `lab/charla50e.py` (50 interacciones) y `lab/examen_ciego10.py` (46 turnos puntuados). Se midieron sin leer las respuestas.
2. Siete tandas de desarrollo (`lab/iter210/t01`–`t07`), con frases distintas de las referencias. Después de cada tanda se repasaron todas las tandas anteriores y los controles.
3. Una sola medida final con el código congelado.
4. Auditoría manual con el mismo criterio para la 2.9 y la 2.10 (`lab/iter210/auditoria.json`).

## Resultados
| Prueba | 2.9 | 2.10 (ciega) | 2.10 tras arreglo (no ciega) |
|---|---|---|---|
| charla50e, juez automático | 70,00 % · 1 falsa | 82,00 % · 0 | 84,00 % · 0 |
| charla50e, auditada | 68,00 % · 1 | 82,00 % · 0 | 84,00 % · 0 |
| ciego 10, juez automático | 82,61 % · 1 | 95,65 % · 2 | 95,65 % · 2 |
| ciego 10, auditado (criterio corregido) | 80,43 % · 0 | 97,83 % · 0 | 97,83 % · 0 |
| exámenes del autor | 88,05 % | 88,05 % | 88,05 % |
| ciego 2 | 93,69 % | 94,35 % | 94,35 % |
| ciego 6 / ciego 7 | 80,60 / 76,74 | igual | igual |

- **Criterio corregido en el ciego 10.** «¿Qué hay detrás del coche?» pedía abstenerse, pero la frase era «el coche está aparcado delante de la farmacia». La respuesta correcta es «la farmacia» (la relación inversa), y el turno siguiente del mismo examen así lo espera. Se corrigió para las dos versiones. Por eso las 2 «falsas» del juez automático en la 2.10 son, auditadas, 1 acierto y 1 respuesta incompleta («Para el examen.»).
- **Primer intento de las 7 tandas:** 80,41 % de acierto (78 de 97 turnos), con 6 respuestas marcadas MAL o ALUCINA (detalle en `primer_intento.json`). Los aciertos que el juez dio por buenos sin serlo se corrigieron a mano.

## Lo que queda mal
- **Frases con dos cláusulas y una locución.** «En mi habitación hay una mesa y encima de la mesa tengo un flexo» se apunta literal, y luego no responde dónde está el flexo.
- **«ahorro para un viaje».** «ahorro» se lee como sustantivo.
- **«¿De qué es la mesa del salón?»** No identifica «la mesa del salón» con «una mesa de madera en el salón».
- **«mi primo y yo hablamos…»** Se guarda como «Luis y tú hablan»: la persona verbal está mal y luego no responde a «¿de qué hablamos?».
- **Preguntas con oración de relativo** («¿sobre qué son las novelas que me gusta leer?»).
- **«¿para qué estudio?»** Responde «Para el examen.» y se deja «de conducir».
- **La visión sigue siendo por reglas.** Formas simples (ahora también estrellas) y hasta cuatro figuras separadas sobre un fondo liso.
