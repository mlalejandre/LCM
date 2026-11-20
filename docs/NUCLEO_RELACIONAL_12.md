# LCM · Núcleo relacional 1.2 (auditoría y refuerzo conceptual)

## Por qué se ha elegido esta vía

El catálogo `lcm-semantica-1.0` anterior contiene 1.875 sentidos, pero la mayor parte de las entradas se asignan a familias amplias con rasgos parecidos, sin aportar una relación comprobada. Tiene 14 triples explícitos. La proximidad coseno en el espacio de 128 dimensiones **no equivale** a subsunción, causalidad, pertenencia, parte-de, ni equivalencia semántica.

**Decisión:** reforzar significados y relaciones, no añadir inmediatamente más planificadores o capacidades gráficas. Se instala una superposición revisable y no destructiva que conserva la base anterior y sus embeddings.

## Entregables

- `data/semantica/nucleo_relacional_12.json`: glosas revisadas, conceptos faltantes y triples de relación con procedencia editorial `curacion_asistida`.
- `src/semantics/nucleo_relacional.py`: grafo tipado, resolución de identidades, búsqueda de pruebas y abstención.
- `src/semantics/relational_dialogue.py`: consultas del tipo «¿Qué relación hay entre X e Y?» por el mismo chat; no convierte verbos en comandos ni infiere por coseno.
- `src/multimodal/grounding_relacional.py`: evento `agente` + `accion` + modalidad, solo mediante anotación explícitamente confirmada; **sin reconocimiento automático de audio**.
- `scripts/consultar_relaciones.py` y `scripts/auditar_nucleo_relacional.py`: exploración y auditoría.
- `tests/test_nucleo_relacional.py`: regresiones, negativas y compatibilidad con vectores anteriores.

Las nuevas definiciones se consultan también desde `PuenteSemantico` y, por tanto, desde la conversación del LCM. Las nuevas identidades comparten el algoritmo de representación `ConceptSpace`. Los vectores de conceptos previos permanecen **numéricamente iguales**; una proyección contextual es solo una vista adicional de consulta, no pesos entrenados.

## Inferencia deliberadamente limitada

Solo `ES_UN` permite cadenas transitivas: `pájaro → ave → vertebrado → animal → ser vivo`. Se conservan las aristas y su procedencia como prueba, sin declarar que el valor coseno sea certeza.

`PUEDE_REALIZAR`, `PRODUCE`, `PARTE_TIPICA_DE`, `SE_PERCIBE_POR` y otras relaciones no se heredan. Esto evita que «algunas aves vuelan» se transforme en «todos los pingüinos vuelan»; también impide deducir que un pájaro **está** piando solo porque **puede** piar.

La ausencia de un triple produce `no_consta`, no una negación categórica. La ambigüedad léxica (p. ej. *banco*) produce `no_resuelto`.

## Comandos

```bash
python parche_relaciones.py --plan
python parche_relaciones.py --aplicar
python -m pytest -q tests/test_nucleo_relacional.py tests/test_semantica_lcm.py tests/test_composicion_multimodal.py
python -m scripts.auditar_nucleo_relacional --guardar
python -m scripts.consultar_relaciones pájaro animal
python -m scripts.consultar_relaciones pájaro piar --predicado PUEDE_REALIZAR
python -m scripts.consultar_relaciones pájaro --vecinos 5
python -m scripts.web
```

En Conversar: «¿Qué es un pájaro?» y «¿Qué relación hay entre un pájaro y un animal?». Las consultas relacionales sin prueba se derivan a la conversación original, que puede disponer de conocimiento adicional.

## Multimodalidad

- Imagen: una percepción visual confirmada para `VERDE` comparte identidad con el concepto textual `VERDE`.
- Audio: la anotación **humana** «pájaro piando» puede guardarse con roles `agente=CONCEPTO.PAJARO`, `accion=ACCION.PIAR`; las relaciones del núcleo verifican compatibilidad conceptual. **No analiza un WAV para inferir el animal**.
- Futuro: reconocedor de audio con aprendizaje supervisado y pruebas independientes, produciendo estas mismas identidades y roles.

## Límites y evaluación honesta

Estos triples y glosas constituyen **curación asistida inicial**, no conocimiento verificado por expertos ni una estimación de cobertura del idioma. Un grafo pequeño no sustituye a un parser robusto, a la memoria entre turnos, a la pragmática ni a la generación de lenguaje natural. `auditar_nucleo_relacional.py` mide inventario y verificabilidad de pruebas, **no** precisión sobre conversaciones reales.

Para mejorar en serio, hay que utilizar corpus de expresiones humanas y contrastar la capacidad de resolver preguntas sin respuesta, contradictorias, ambiguas y multi-modalidad con una validación ciega antes de añadir rutas de ejecución automáticas.
