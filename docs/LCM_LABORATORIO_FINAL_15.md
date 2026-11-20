# LCM — laboratorio de conversación 1.5 (noviembre 2026)

## Principio

El sistema resuelve el significado mediante el espacio conceptual y el analizador ya existentes. Las operaciones que tienen definición precisa —reloj, aritmética, edad desde un hecho fechado— se ejecutan determinísticamente. Las respuestas procedentes de recuperación documental se someten a un control de pertinencia y, sin evidencia suficiente, se abstienen. La confirmación de una acción visual negada emplea el compositor conceptual, sin una tabla rígida de verbos equivalentes.

## Qué añade

- `src/quality/evidencia15.py`: consulta de edad desde hechos `NACER` almacenados; validación conservadora de citas; raíz cuadrada como operación matemática; confirmación de peticiones visuales negadas a través de `analizar`.
- `src/web/motor.py`: tres puntos de conexión acotados (antes de la percepción, después de la composición y después de responder con la conversación general).
- `scripts/lab_calidad15.py`: 200 tandas de 10 preguntas con aislación de memoria y reutilización de un catálogo semántico de solo lectura. *No necesita* un checkpoint de Escuela: es deliberadamente un examen parcial, no un reemplazo del examen integral.
- `scripts/iterar_lcm.py`: optimización de la evaluación integral; un catálogo vectorial de solo lectura por proceso y sesiones de memoria separadas por caso. Si aparece una tarea de enseñanza, instancia el léxico exclusivo.

## Medidas observadas en la reconstrucción disponible

| Evaluación | Resultado | Qué mide |
|---|---|---|
| Banco controlado, semilla 20261118 | 2000 / 2000; 200/200 tandas 10/10 | Diez familias de funciones que pueden verificarse sin Escuela |
| Banco de control, semilla 93742 | 2000 / 2000; 200/200 tandas 10/10 | Generalización dentro de las mismas familias a parámetros nuevos |
| Banco heredado, 2000 casos, Escuela ausente | 907 / 2000; 0 tandas aprobadas | Diagnóstico, **no** medida del LCM real |
| Regresión de visión, semántica, relaciones, episodios y calidad | 94 / 94 | No ruptura de las piezas disponibles |
| Banco semántico anterior | 12000 / 12000 | Repetición del banco léxico-sintético |
| Banco adversario anterior | 3629 / 4000 | Composición semántica: fallan verbos de soporte y tareas compuestas |
| Composición dirigida | 34 / 34 | Invariantes de alcance en composición |

**Atención**: los dos bancos de 2.000 tienen plantillas generadas, repetibles, con las respuestas determinadas por los datos de prueba; no prueban diálogo humano general, comprensión libre ni semejanza con un LLM. La simulación *sin Escuela* reemplaza tanto el modelo UD ausente como un archivo de enrutador que está truncado en la copia aportada. El checkpoint `checkpoints/school.pt` de tu Mac **no está disponible** aquí. No se ha entrenado uno nuevo ni se ha accedido a los datos privados de tu memoria.

## Límites y pendientes

1. Persistencia de hechos extraídos de texto libre, especialmente fechas y predicados con objeto elíptico.
2. Interrogativas con múltiples participantes, roles dirigidos y contexto hipotético: «si Manuel acompaña a Carla, ¿a quién acompaña Carla?» no justifica invertir la relación.
3. Composición de preguntas subordinadas, citas que comparten palabras sin sostener la conclusión y negación de eventos episódicos.
4. Multimodalidad real de audio: el proyecto almacena características y etiquetas, pero **no reconoce sonidos automáticamente**.
5. Medición en diálogos humanos independientes y sobre `school.pt` con un conjunto de casos reservado antes de desarrollar parches.

## Protocolo recomendado de regresión (en una instalación completa)

```
python -m pytest -q tests/test_evidencia15.py tests/test_semantica_lcm.py tests/test_composicion_multimodal.py
python -m scripts.lab_calidad15 --n 2000
python -m scripts.iterar_lcm --n 2000 --explorar --salida reports/iteracion15_integral
```

La última línea no aprende ni modifica código. Solo evalúa `Motor.chat` en condiciones completas cuando exista una Escuela entrenada. Si una tanda no alcanza 9/10, el evaluador no debe llamarla aprobada. El modo `--autorreparar` del laboratorio anterior solo permite cuatro correcciones revisadas; no reemplaza la programación, el control de sesgos ni la revisión de regresiones.
