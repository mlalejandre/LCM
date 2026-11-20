# LCM Composición Conceptual 1.1

## Objetivo

Separar **comprensión conceptual de acciones y argumentos** de **ejecución**. No introducir una tabla cerrada `verbo -> función`. Los conceptos y similitudes siguen en `data/semantica/conceptos_es.json` y `ConceptSpace`. La composición añade una lectura estructural de negaciones, subordinadas, preguntas de definición, argumentos cromáticos y límites de la operación disponible.

## Archivos

- `src/semantics/composition.py`: análisis composicional; `Marco` describe la solicitud con conceptos y predicados. Las reglas son gramaticales y de seguridad de operación, no listas de verbos sinónimos.
- `src/semantics/bridge.py`: integración con el puente anterior; recurre al motor conversacional cuando el caso no se puede resolver.
- `src/multimodal/events.py`: `ObservacionConceptual` con `modalidad`, `entidad`, `conceptos` por rol, `evidencia` y `atributos`. Un mismo ID (`VERDE`) enlaza la propiedad visual y el argumento textual. El audio solo declara contenido con confirmación humana o un futuro reconocedor validado.
- `src/vision/perception.py`: añade a sus resultados la observación normalizada, sin duplicar el hecho `TENER_COLOR` ni guardar imágenes originales.
- `src/multimodal/audio_features.py`: extractor WAV PCM 16 bits, 1–2 canales, 8–192 kHz; devuelve duración, RMS, pico, cruces por cero y estimación de silencio. **No reconoce pájaros, habla ni eventos acústicos.**
- `scripts/analizar_audio_lcm.py`: prueba acústica por consola (no instala un control de audio en la interfaz web).
- `scripts/evaluar_composicion.py`, `tests/test_composicion_multimodal.py`: evaluación separada y regresión.

## Probar

```bash
python -m pytest -q tests/test_composicion_multimodal.py tests/test_semantica_lcm.py tests/test_vision_chat.py tests/test_vision_colors.py
python -m scripts.evaluar_semantica --n 12000 --desafio 4000 --guardar
python -m scripts.evaluar_composicion --guardar
python -m scripts.analizar_audio_lcm prueba.wav
python -m scripts.analizar_audio_lcm prueba.wav --etiqueta pajaro_piando
python -m scripts.web
```

El último comando de audio **solo imprime** una anotación; no modifica la memoria ni enseña automáticamente el concepto. La confirmación es explícita a través de `--etiqueta`; no debe interpretarse como predicción acústica.

## Resultados obtenidos sobre una reconstrucción de la versión compartida

| Evaluación | Semántica 1.0 | Composición 1.1 |
|---|---:|---:|
| Banco básico sintético (12.000 casos) | 12.000/12.000 | 12.000/12.000 |
| Banco adversario original (4.000 casos) | 2.011/4.000 | 3.629/4.000 |
| Banco complementario dirigido | N/A | 34/34 |
| Pruebas de regresión dirigidas + multimodalidad | N/A | 36/36 |

Son **bancos sintéticos**, algunos de los cuales contienen plantillas repetidas. No son una evaluación independiente de 99 % de cobertura del español. Los 371 errores adversarios restantes se concentran en verbos de soporte (209) y tareas compuestas (162). El benchmark adversario considera 'abstención' la salida correcta para la tarea compuesta; el LCM en algunos casos formula una aclaración. Esto es una discrepancia de criterio que se informa sin cambiar el examen original.

## Límites

- No hay modelo generativo general ni conversación comparable a un LLM. La comprensión de implicaturas, ironía, polisemia no resuelta, diálogos prolongados y generación de texto libre requiere investigación adicional.
- El reconocimiento morfológico por sufijos puede producir análisis alternativos; las interpretaciones necesitan confirmar la compatibilidad semántica de la acción con la operación.
- El puente sigue restringido a muestras **uniformes** de seis colores. No promete generar dibujos geométricos, fotografías, gradientes ni audio.
- Una similitud coseno **no es** una probabilidad; se requiere un rasgo de capacidad visual explícito antes de ejecutar acciones.
- La herramienta de audio no etiqueta sonidos de aves: se necesitarán grabaciones etiquetadas, un encoder acústico y pruebas ciegas para aprender esa relación perceptiva.
- El contrato multimodal enlaza identidades conceptuales por rol; la memoria episódica multimodal y el flujo de adjuntar audio en Conversar quedan para un parche posterior.

## Próximas investigaciones

1. Convertir los fallos de verbos de soporte y de tareas compuestas en análisis de roles (agente, paciente, instrumento, finalidad, alcance) usando de verdad el árbol de dependencias de la Escuela cuando esté disponible.
2. Resolver correferencias entre turnos ("el de antes", "ahora el mismo pero más oscuro") y producir planes con varias capacidades, con confirmación cuando sea necesario.
3. Crear un corpus independiente de conversaciones humanas reales, no derivado de las mismas plantillas de desarrollo; medir precisión por intención, falsas ejecuciones, abstención, latencia p50/p95 y regresiones.
4. Añadir un encoder de audio especializado (con datos y etiquetas verificadas) cuya salida se alinee al mismo catálogo de conceptos: `PAJARO`, `PIAR`, `SONIDO`, `AGENTE`.
5. Extender el canal visual a formas y relaciones, preferentemente con algoritmos deterministas donde resulten fiables.
