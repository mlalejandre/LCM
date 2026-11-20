# LCM 1.3 · Memoria episódica y evidencia multimodal

## Alcance

Superposición **no destructiva** al LCM 1.2. La memoria semántica describe clases,
relaciones y capacidades; la memoria episódica describe **qué se afirma acerca
de un suceso concreto, desde dónde, cuándo y con qué estatus epistémico**.

No se modifican los vectores ni los checkpoints. No se crea un segundo concepto
«verde» ni un segundo concepto «pájaro». La similitud coseno es una ayuda para
proponer candidatos, no una prueba de identidad ni de ocurrencia.

## Diferencias que ya preserva

| Entrada estructurada | Lo que se registra | Lo que NO se deduce |
|---|---|---|
| «Los pájaros pueden piar» | `concepto.pajaro PUEDE_REALIZAR accion.piar`, alcance tipo | Que un pájaro esté piando ahora |
| «El pájaro A piaba en el patio» | Declaración de un `REALIZAR` sobre la instancia `AVE_A` | Que un sensor haya oído al pájaro |
| «Ana cree que el pájaro A piaba» | Creencia atribuida a `ANA` | Que la acción ocurrió |
| «Quizá el pájaro A esté piando» | Hipótesis | Verificación física |
| Imagen verde clasificada | `IMAGEN_X TENER_COLOR VERDE`, con origen `clasificador_color` | Que todo objeto dentro sea verde |
| WAV sin etiqueta | Evidencia acústica sin clasificación | Que se trate de un pájaro |
| WAV etiquetado por usuario | `SONIDO_X ETIQUETA_ACCION ACCION.PIAR` | Que el LCM haya reconocido el sonido por sí solo |

Las afirmaciones se conservan con polaridad, estatus (`actual`, `posible`,
`creencia`, `hipotetico`), modalidad, contexto e instante ISO 8601 con zona.
Las negaciones contrarias del mismo contexto e instante producen `conflicto`.
Las afirmaciones en distintos instantes o creencias de distintos hablantes no
se fusionan en una contradicción artificial.

## Implementación

- `src/multimodal/episodic_memory.py`: almacén persistente con evidencia y validación.
- `src/semantics/event_bridge.py`: vínculo entre la ontología y los eventos; no infiere eventos de capacidades.
- `src/web/motor.py`: al adjuntar imagen en Conversar, conserva la observación en `memory/lcm_episodios.json`. La conversación normal continúa sin cambios.
- `scripts/episodios_lcm.py`: inspección y anotación explícita; no es un parser de texto libre.
- `scripts/evaluar_episodios.py`: banco sintético reproducible con controles negativos.
- `tests/test_episodios_lcm.py`: invariantes y regresiones.
- `data/semantica/oraculo_eventos_es_13.jsonl`: 40 frases anotadas manualmente para la próxima evaluación del extractor textual; todavía no se puntúan.

**Importante:** la integración lingüística general con la Escuela NO se ha activado.
Para evitar falsas certezas, por ahora las anotaciones de sucesos se realizan
mediante funciones estructuradas o el explorador CLI. La integración automática
de oraciones libres debe hacerse después de validar conjuntamente sintaxis,
modalidad, negación, tiempo, participantes y atribución de creencias.

## Comandos

```bash
python parche_episodios.py --plan
python parche_episodios.py --aplicar
python -m pytest -q tests/test_episodios_lcm.py
python -m scripts.evaluar_episodios --n 256 --guardar
python -m scripts.web
```

En Conversar, adjuntar una imagen crea automáticamente un registro episódico
con procedencia `clasificador_color` cuando el color es identificable. El
identificador de observación se añade al resultado del motor. Una imagen
ambigua queda registrada como observación **sin asignarle un color**.

Consultar el almacén:

```bash
python -m scripts.episodios_lcm inventario
python -m scripts.episodios_lcm anotar --sujeto AVE_1 --accion accion.piar --contexto PATIO --creencia ANA
python -m scripts.episodios_lcm consultar --sujeto AVE_1 --accion accion.piar --contexto PATIO --estatus creencia --hablante ANA
python -m scripts.episodios_lcm analizar-audio mi_grabacion.wav
```

El análisis de audio existente no reconoce sonidos animales: calcula
características de WAV; una etiqueta requiere confirmación explícita.

## Evaluación y criterios

No confundir pruebas de coherencia de una representación con comprensión
natural del español. El informe de `evaluar_episodios` mide exclusivamente
invariantes formalizados; no se usa para afirmar «99 % del idioma».

Evaluaciones siguientes recomendadas, **antes** de implementar un parser de
hechos libres:

1. Elaborar 300 frases de evaluación humanas y adversarias, independientes del código.
2. Extraer cuadros de eventos con la Escuela, identificando roles, tiempos y modalidad.
3. Comparar cada campo con la anotación de referencia y medir *falsa certeza*.
4. Ensayar correcciones, creencias contradictorias y referencias anafóricas.
5. Adquirir muestras reales de audio e imagen con etiquetas verificables;
   mantener una partición de prueba nunca vista durante el desarrollo.

Para revertir instalación:

```bash
python parche_episodios.py --revertir
```

El revertidor solo restaura archivos del código si sus hashes siguen siendo
los instalados; **no elimina** `memory/lcm_episodios.json`, porque contiene
datos adquiridos por el usuario.
