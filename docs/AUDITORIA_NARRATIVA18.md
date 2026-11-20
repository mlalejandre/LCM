# LCM 1.8 — Narrativa de eventos y auditoría pareada

## Hipótesis previa

Una capa de eventos **con tres roles semánticos** (agente, tema y destinatario) puede mejorar la comprensión y la recuperación de información en narraciones de transferencias, sin modificar el catálogo vectorial existente ni confundir posesión con propiedad. Se exige trazabilidad y abstención con premisas disputadas.

Esta hipótesis **no** afirma que LCM comprenda el español general. Se construye una prueba separada de **español abierto**, expresamente para contrastar esa extrapolación.

## Arquitectura

- `src/semantics/acciones18.json`: define **sentidos de acción**, formas, valencia y marcos de efecto. Entregar, prestar y devolver no son sinónimos; comparten el marco `TRANSFERENCIA_CONTROL`. El conocimiento de propiedad no se infiere de estas acciones.
- `src/semantics/narrativa18.py`: extrae roles de un conjunto restringido de estructuras (voz activa, pasiva explícita, perífrasis sencillas, recepción con origen, clíticos de objeto, preguntas de control). Conserva el texto original como testimonio; nunca afirma percepción visual/acústica.
- `src/web/motor.py`: se añade el procesador narrativo **antes** de `Discurso17` y `DialogoConceptual`, sin reemplazar esos módulos.
- `memory/lcm_narrativa18.json`: registro persistente separado. Se crea al registrar el primer episodio; no se modifica `MemoryStore` de hechos atemporales, ni checkpoints.
- Regla de seguridad: una segunda transferencia por un agente que no coincide con el último poseedor conocido genera un conflicto; el modelo se abstiene. Los pronombres se resuelven únicamente cuando existe un antecedente que permite identificarlos. No se infiere propiedad.

### Limitaciones de esta representación

Un objeto se identifica provisionalmente por su lema. Dos ejemplares distintos de «libro» pueden colisionar; ante testimonios incompatibles, el módulo prefiere abstenerse. No resuelve de forma general elipsis, voz pasiva compleja, identidad de entidades de larga duración, propiedad legal, intervalos temporales ni implicaturas. Para una semántica abierta debe extraer roles desde la Escuela entrenada y mejorar su correferencia.

## Protocolo científico de evaluación

1. Se creó una reconstrucción de LCM 1.7, con memoria aislada por caso y un analizador UD *stub* que devuelve listas vacías; falta `school.pt` y `intents_modelo.json` está truncado. Por tanto **no se evaluó el LCM entrenado de la máquina del usuario**.
2. Antes de implementar el parser se redactaron 23 casos de desarrollo y una primera reserva de 56 casos, cuyo SHA-256 se fijó antes de ejecutar el candidato.
3. Se corrigieron errores examinando desarrollo. Se abrió la reserva 56 (51/56), por lo que las mejoras posteriores sobre ella se tratan **solo como regresión** (56/56).
4. Se creó una segunda reserva de 36 diálogos (23/36 al primer uso), que también se utilizó después para diagnosticar y corregir errores (28/36 retrospectivo).
5. Se fijó una nueva reserva de 40 casos; su primera ejecución final dio **37/40 (92,5%)**, con tandas de **10, 10, 10, 7**. No se modificó esa reserva después de medir.
6. Para una nueva ampliación gramatical se fijó otra reserva, de 50 casos. La primera ejecución dio **43/50 (86%)**, con tandas de **10, 10, 10, 9, 4**. Tampoco se modificó esa reserva después de medir. En los últimos diez casos de narrativa libre solo hubo **4/10**.
7. Los tests de regresión disponibles de Visión, Semántica, Composición, Episodios, Núcleo Relacional, 1.6, 1.7 y 1.8: **173/173**. Simulación semántica controlada: **12.000/12.000**; adversaria: **3.629/4.000**. Oráculo anotado de 40 frases: **7/40** estructuras y cero hechos indebidos; no mejora aquí.

| Corpus | Casos | LCM 1.7 reconstruido | LCM 1.8 | Uso de la reserva |
|---|---:|---:|---:|---|
| Reserva 1 | 56 | 0 | 56 | Regresión tras inspeccionar fallos |
| Reserva 2 | 36 | 0 | 28 | Regresión tras inspeccionar fallos |
| Reserva 3 | 40 | 0 | 37 | Primera ejecución sin ver respuestas |
| Reserva 4 | 50 | 0 | 43 | Primera ejecución sin ver respuestas |

**Interpretación crítica:** la cifra cero de 1.7 es **una línea de base inválida para el LCM completo**: la mayoría de sus casos fallan por `JSONDecodeError` del clasificador truncado al delegar preguntas que el módulo 1.7 no reconoce. Como control de plausibilidad, un sistema que se abstuviera siempre respondería correctamente 11 de 40 casos en Reserva 3 y 11 de 50 en Reserva 4. La mejora del nuevo marco de transferencias está comprobada en la reconstrucción, pero **el efecto incremental real sobre el LCM entrenado exige repetir la evaluación en ese entorno**. Los intervalos de Wilson y contrastes de McNemar del JSON cuantifican únicamente la incertidumbre de *estos casos*, no de una población aleatoria de español humano.

No se han utilizado las respuestas del conjunto de reserva para modificar su etiqueta de verdad. Se detectó una rúbrica excesivamente literal para citas de origen; se corrigió el evaluador por igual para ambos sistemas, y se conservan logs de la primera ejecución.

## Meta de aceptación

**El objetivo estricto 9/10 por tanda NO está logrado en las tandas de español libre.** La capa puede ser instalada como mejora experimental parcial, pero no es un certificado de comprensión general del 90 %.

La próxima iteración debe usar el checkpoint UD real y un corpus humano anotado con roles y correferencia por un evaluador independiente. Reportar por separado: cobertura, precisión de los hechos aceptados, falsas certezas, abstención, trazabilidad, exactitud de preguntas y latencia p50/p95. Una regla que evita responder puede aumentar precisión y disminuir cobertura; ambas métricas importan.

## Uso del evaluador

```bash
python -m scripts.evaluar_narrativa18 --casos data/evaluacion/narrativa18_reserva4.json --salida reports/narrativa18_reserva4.json
python -m pytest -q tests/test_narrativa18.py
```

Este procedimiento aísla la memoria y guarda las respuestas de todos los casos. Se debe preservar la copia anterior al instalar cada versión si se pretende realizar comparaciones pareadas futuras.
