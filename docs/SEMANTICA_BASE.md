<!-- LCM_SEMANTICA_V1_GENERADO -->
# LCM · Núcleo semántico conversacional 1.0

La semántica conversacional complementa el diccionario de sentidos que ya usa LCM (`src/language/conceptos.py`) y **reutiliza** `src/ontology/concept_space.py` para los vectores. No reemplaza checkpoints entrenados ni prueba comprensión general.

## Arquitectura

- **Inventario:** `data/semantica/conceptos_es.json`; entradas por sentido y no por palabra. Las agrupaciones temáticas no son sinónimos. Se preservan ambigüedades como `banco` (asiento/institución). La categoría `agrupacion_inicial` es solo una ubicación provisional y nunca se verbaliza como una definición fiable.
- **Identidades compartidas:** `COLOR` y `AZUL`, `ROJO`, `VERDE`, `AMARILLO`, `NEGRO`, `BLANCO` tienen las mismas claves y rasgos que LCM Visión 0.1.
- **Acciones:** `MOSTRAR`, `DIBUJAR`, `PINTAR` y `DISEÑAR` son sentidos diferenciados, agrupados por rasgos semánticos; la capacidad visual se elige por similitud con prototipos conceptuales, no por una tabla de verbos directamente asociada a una función. La morfología usa flexiones conocidas como *formas de acceso*, no como reglas de significado.
- **Aprendizaje:** ante un verbo desconocido en una solicitud cromática, pide aclaración. Tras vincularlo el usuario con una acción existente, registra un nuevo concepto con rasgos compartidos más identidad propia, persiste en `memory/semantica_aprendida.json` y lo incorpora a `MemoryStore`. Ningún significado se aprende solo por proximidad ni por suposición del LCM.
- **Compatibilidad:** la memoria y los checkpoints existentes quedan intactos. Los conceptos añadidos residen en una instancia del mismo tipo `ConceptSpace` y pueden migrarse en el futuro a un catálogo común más amplio. No se reconstruyen automáticamente los pesos del razonador neuronal.

## Instalar

Desde la raíz, con Visión 0.1 integrada en Conversar:

```bash
python parche_semantica.py --plan
python parche_semantica.py --aplicar
python -m pytest -q tests/test_semantica_lcm.py
python -m scripts.consultar_semantica dibujar
python -m scripts.evaluar_semantica --n 12000 --desafio 4000 --guardar
python -m scripts.web
```

Prueba en Conversar: «Dibuja el color azul», «Muéstrame el color verde», «¿Qué es el color azul?», «Trazulea una imagen azul». Para la última, responde «Es como dibujar» y reinicia el LCM: la nueva asociación debería conservarse.

## Qué está medido y qué no

`evaluar_semantica.py` **no** simula toda la Escuela ni el Razonador: evalúa el puente léxico-semántico en 12.000 peticiones controladas y 4.000 expresiones adversarias. Son muestras sintéticas, no habla humana independiente ni un 99 % de español real. Los errores se agrupan por familias en `reports/semantica_evaluacion.json`.

Esta base posee muchas **entradas nominales ubicadas solo por dominio**, que requieren glosas/sentidos más precisos. La implantación actual solo conecta automáticamente las capacidades visuales cromáticas. El resto de operaciones siguen a cargo del LCM preexistente. Las preguntas de polisemia sin evidencia de desambiguación deben producir incertidumbre.

## Próximos experimentos

1. Unificar las representaciones de la ontología conversacional y la del razonador, sin cambiar checkpoints silenciosamente.
2. Extraer estructura de petición (modalidad, negación, subordina­ción, propósito, paciente, atributo) a partir del análisis de dependencias de la Escuela.
3. Añadir conjuntos de conversaciones reales anonimizadas y redactar evaluaciones independientes.
4. Mejorar las glosas y los sentidos polisémicos por revisión humana; registrar fuentes y cambios de confianza.
5. Incorporar geometría cuando las peticiones visuales compuestas y la abstención sean sólidas.

### Evaluación integral en tu instalación (con modelos entrenados)

```bash
python -m scripts.evaluar_conversaciones_lcm --n 1000
```

Usa una memoria temporal, no la memoria personal. Necesita `checkpoints/school.pt` y genera `reports/semantica_conversaciones_integral.json`. En la reconstrucción proporcionada no está ese checkpoint, por lo que **no se atribuye ningún resultado de conversación general a un entrenamiento real**.
