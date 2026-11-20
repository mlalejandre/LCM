# LCM 2.16 · Campaña de entrenamiento: leer, razonar, aprender y crear

Encargo: buscar la estrategia de entrenamiento óptima y aplicarla una noche entera, con métricas y método científico; usar conversaciones
y texto inserto, introducir conceptos, enseñar a razonar y fomentar la creatividad cuando se pide.

## 1. La estrategia

1. **Un termómetro fijo por capacidades**, escrito antes de tocar nada (205 preguntas): memoria, conceptos, razonamiento, lectura de un
   texto, aprender conceptos en la charla, creatividad a petición, cálculo, charla social y robustez. Se mide en cada versión.
2. **Invertir donde más puntos se pierden.** La 2.15 perdía sobre todo en lectura (12 %), robustez (47 %) y creatividad (50 %).
3. **Un ciclo por capacidad:** sondear con ejemplos propios, buscar la causa general, construir un mecanismo (no una regla por frase),
   pasar regresiones y controles.
4. **Exámenes limpios escritos después de congelar**, con otros contenidos y otras formas, para saber cuánto de la mejora es real.
5. **Tres canales para enseñar con el mismo formato de conocimiento:**
   - la charla («un zorb es un animal que vive en cuevas»);
   - un texto pegado («Te voy a leer un texto…»);
   - la **escuela**: cartillas en castellano llano que se convierten en conocimiento de fábrica.

## 2. Qué sabe hacer ahora

- **Leer un texto** (`lectura.py`). Lo lee frase a frase con el mismo núcleo de la charla y lleva el hilo:
  - quien hace algo «con» alguien forma un grupo con él («fue con su abuelo» → «compraron», «volvieron»);
  - una frase sin sujeto sigue hablando del tema del texto;
  - dos hechos en una frase se separan («Los lunes lleva a Noa a piano y los viernes cena con sus padres»);
  - si el núcleo no sabe contestar, busca la frase del texto que responde y la cita («En el texto pone: …»). No inventa.
- **Razonar:**
  - «ningún pez tiene pulmones» es una negación universal (antes se guardaba como afirmación);
  - igualdades de medida («Leo y Max pesan lo mismo» → lo que se sepa de uno vale para el otro);
  - el orden de las cosas (`secuencias.py`): «primero…, después… y luego…» → «¿qué hice después de…?», «¿X antes de Y?»;
  - contención en cadena («el anillo en el joyero, el joyero en el cajón»);
  - cuentas contadas («tenía 20 euros, gasté 5 y me dieron 3»), que calculan las aplicaciones;
  - la causa dicha en el turno siguiente («Estoy triste.» «Es que he discutido con mi hermana.»);
  - el adjetivo del objeto cuenta: «¿tiene el pelo corto?» ya no se contesta «sí» porque tenga pelo largo.
- **Aprender conceptos en la charla:** qué es, dónde vive, para qué sirve, de qué está hecho, sus partes, su contrario y su significado.
  Lo enseñado se usa igual que lo de fábrica («tengo una pinfa» → «¿tengo algo para doblar alambre?») y dice su procedencia.
- **Crear a petición** (`crear.py`): poema, cuento, frase con una palabra, rima, adivinanza (con pistas y «me rindo»), título, nombre,
  descripción, ideas, sinónimos, animal inventado, ejemplos de una clase («dime tres frutas», «un animal que vuele»).
  - El contenido sale de la base de conceptos y de lo que la persona ha contado.
  - La rima se calcula por el sonido de la palabra, desde la vocal acentuada.
  - Solo se activa con una petición: «ayer escribí un poema» sigue siendo un hecho.
- **Entender lo mal escrito:** palabras que suenan como otra que existe («komo», «bibo», «ermana»), abreviaturas, todo en mayúsculas,
  muletillas, incisos («mi moto, la negra, está…»), jerga («me mola»).
- **Conceptos nuevos:** tamaño típico en una escala heredable («¿qué es más grande, un elefante o un ratón?»), dónde vive cada
  animal, «¿quién apaga los fuegos?» por oficio, comparar números, calendario supuesto en cualquier orden.

## 3. La escuela de conceptos

`python -m src.nucleo20.escuela` lee `src/nucleo20/cartillas/*.txt` y escribe `conceptos_aprendidos.txt`, que se carga como parte de
la base de fábrica. Una cartilla es texto normal, una idea por frase («La ballena vive en el mar. Los médicos curan a los enfermos.»).
- Cartilla 1: 122 frases, 120 aprendidas (98,4 %), 129 datos nuevos.
- Lo que no entiende no lo inventa: lo lista para reescribirlo.
- Es la vía para que tú mismo entrenes al LCM escribiendo en castellano.

## 4. Métricas reales

Todas las cifras son del corrector automático salvo donde se indica «auditado» (leído a mano con el mismo criterio en las dos versiones).

| Prueba | 2.15 (antes) | 2.16 medida ciega | 2.16 final |
|---|---|---|---|
| Termómetro (205) | 61,5 % · 12 falsas | 92,7 % · 5 falsas | 96,6 % · 1 (no ciega) |
| Limpio 16b (142) | 64,1 % · 6 falsas | 84,5 % · 5 falsas | 96,5 % · 2 (no ciega) |
| **Limpio 16c (92), medida final** | **62,0 % · 2 falsas** | — | **94,6 % · 0 falsas (ciega)** |

Cómo leerlas:
- **El termómetro sobrestima.** Lo conocía al escribir mis ejemplos de desarrollo y se parecen a él en la forma.
- **El 16b es la medida honesta del primer intento:** +20 puntos. Lectura y creatividad generalizaron (25 → 100 %, 43 → 93 %);
  el razonamiento con formas nuevas no mejoró (73 → 73 %) y la robustez poco (15 → 38 %).
- Después arreglé lo que vi fallar en los dos, así que sus cifras finales ya no son ciegas.
- **El 16c es la medida final:** se escribió con el código definitivo congelado, se midió una vez y no se ha tocado nada después.
  Auditado a mano: 2.15 = 59,8 %, 2.16 = 93,5 % (descuento un aprobado laxo: «me voy, gracias por todo» → «Entendido: te vas
  gracias por todo»).
- Reserva de siempre: los tres exámenes los escribo yo. Las formas de preguntar son las que yo imagino.

Evolución por versión (el mismo examen pasado a cada versión; acierto y afirmaciones falsas):

| Versión | Termómetro (205) | Limpio 16c (92) |
|---|---|---|
| 2.12 | 57,6 % · 11 | 53,3 % · 5 |
| 2.13 | 60,0 % · 10 | 57,6 % · 4 |
| 2.14 | 60,0 % · 11 | 56,5 % · 4 |
| 2.15 | 61,5 % · 12 | 62,0 % · 2 |
| **2.16** | **96,6 % · 1** (no ciega; 92,7 % en la medida ciega) | **94,6 % · 0** (ciega) |

Las rondas 2.13 a 2.15 mejoraban lo suyo (cálculo, conceptos, relaciones) pero apenas movían una prueba general de conversación.

Otros datos:
- **Ablación** (código 2.16 con la base de conceptos de la 2.15): termómetro 96,1 %, 16b 95,8 %. Casi toda la mejora viene de los
  mecanismos; los datos nuevos aportan medio punto en estas pruebas, que piden capacidades más que vocabulario.
- **Controles:** exámenes del autor 88,62 → 89,76 %; ciego 2, 94,35 → 94,68 %; ciego 6 y ciego 7 iguales. Sin regresiones nuevas.
- pytest: 855 pruebas pasan.

## 5. Lo que sigue verde (fallos de la medida final y otros vistos)

- «Comparto piso con dos amigas, Sara y Noelia» → no sabe con quién.
- Transitividad con un verbo («Óscar corre más rápido que Lucas…»): solo funciona con «ser más… que».
- «Tenía 50 euros y me gasté 20 en el cine» → «¿cuánto me queda?» (sin decir la unidad).
- La causa entre turnos falla si la primera frase no dejó un hecho («hoy he tenido un día horrible»).
- Jerga no cubierta («le flipa») y despedidas mezcladas con otra cosa («me voy, gracias por todo»).
- Corregir solo el día de algo dicho antes («juego los viernes, no los jueves») no cambia el hecho original.
- «¿Un coche tiene alas?» responde «no me consta» en vez de «no».
- La calidad de poemas y cuentos es la de una composición por plantillas con conocimiento real: correctos, pero sencillos.
- En respuestas de grupo dice «Elsa vio leones» en vez de «Marcos y Elsa vieron leones».
- El LCM aún no toma la iniciativa: no pregunta por lo que no sabe de lo que le cuentas. Sería el siguiente paso para una charla plena.
