# Reproducir el LCM desde cero

Objetivo: que puedas reconstruir, en cualquier momento y en cualquier máquina, el proyecto **exactamente** como está hoy
(parche-59 + este paquete), reentrenar sus modelos y comprobar con números que el resultado es equivalente.

Hay tres cosas distintas, y conviene no mezclarlas:

| Qué | Cómo se reproduce | ¿Idéntico bit a bit? |
|---|---|---|
| **Código, datos de prueba, tests, documentos** | `LCM_construir_desde_cero.py` + `manifiesto --verificar` | **Sí** (huellas SHA-256) |
| **Corpus UD** (GSD, AnCora) | `scripts.get_data` con el commit fijado en el manifiesto | **Sí** si se fija el commit |
| **Pesos** (`checkpoints/*.pt`) | `scripts.reproduce` (misma semilla, mismos datos) | **No**: cambian unas décimas con otro hardware (CPU/MPS/CUDA) o versión de torch. Se exige el **criterio** (CUMPLE), no el decimal |

## 0. Una vez, ahora, en tu Mac (congelar el estado actual)

```
python parche.py                         # instala parche-60 (este paquete)
python -m scripts.get_data               # si aún no tienes data/ud/
python -m scripts.manifiesto --guardar   # escribe reproducibilidad/manifiesto.json
python -m scripts.empaquetar_todo        # escribe LCM_construir_desde_cero.py
```

`manifiesto --guardar` apunta: versiones de Python/torch/numpy, **el commit exacto de cada corpus UD que tienes clonado** (así
`get_data` bajará siempre ese mismo), la huella de cada archivo y las métricas de la última ejecución de `scripts.check`
(son la referencia con la que se compara una reproducción). Guarda `reproducibilidad/` y `LCM_construir_desde_cero.py`
donde guardes tus copias importantes (y en git, si lo usas). Repite estos dos comandos cada vez que cierres un parche.

## 0b. Todo con un solo comando (tabula rasa + reconstruir + reentrenar)

```
python limpieza.py                              # ensayo: ves qué se quitaría y qué se conserva
python limpieza.py --aplicar --reconstruir      # lo hace TODO: regenera el constructor y el manifiesto desde TU proyecto,
                                                # comprueba una reconstrucción en carpeta temporal, te pide confirmación (TABULA RASA),
                                                # limpia, crea el entorno, instala, prueba, verifica, reentrena y compara métricas
```
Variantes: `--borrar` (sin copia de seguridad), `--reconstruir menu` (abre el menú en vez de hacerlo todo), `--reconstruir archivos`
(solo escribe los archivos), `--libro RUTA`, `--rapido`, `--semilla N`, `--conservar-ud`. Si algo falla antes de la confirmación, no se toca nada.
El constructor se regenera **siempre desde el proyecto que tienes**, por eso la reconstrucción es fiel a tu copia.

## 1. Reconstruir en una carpeta vacía (con asistente)

```
mkdir LCM && cd LCM
cp /ruta/a/LCM_construir_desde_cero.py .
python LCM_construir_desde_cero.py
```

Escribe todo el código, tests, datos de prueba y documentos y abre un **menú guiado** (no hace falta recordar comandos):

```
1) Preparar el entorno (crear .venv e instalar dependencias)
2) Comprobar el código con los tests (51)
3) Verificar que el código es idéntico al original (manifiesto)
4) Reentrenar TODO desde cero (reproduce; tarda de decenas de minutos a horas)
5) Comprobar los resultados contra la referencia
6) Hablar con el modelo (think)
7) Hacer 1 -> 5 en orden, sin parar
```

Arriba del menú muestra el estado (entorno, pesos entrenados, texto encontrado). Para usarlo sin menú:
`--sin-menu` (solo escribir archivos) o `--todo --libro mi_texto.txt [--rapido] [--semilla N]` (hace 1→5 sin preguntar).
Después de `python limpieza.py` es exactamente el mismo flujo. Manual equivalente: `python -m venv .venv && source .venv/bin/activate &&
pip install -r requirements.txt && python -m pytest -q tests`. `python -m scripts.manifiesto --verificar` debe decir *Reproducción fiel*.

## 2. Reentrenar todo (de cero a lo que tienes hoy)

```
python -m scripts.reproduce --libro mi_texto.txt     # UN comando; --lista muestra los pasos; --desde PASO continúa; --semilla N
```

`mi_texto.txt` es un texto largo en español (tú usaste *La Regenta*; no se incluye ningún libro). Sin él se saltan los pasos
que dependen del texto (el oído no se preentrena con tu libro y saldrán otras cifras en el oído).

| # | Paso | Qué produce | Criterio (se imprime solo) |
|---|---|---|---|
| 1 | `tests_unitarios` | — | 52 passed |
| 2 | `prepare_concepts` | `data/concept_*.pkl`, `dataset_manifest.json` (espacio conceptual semilla 42) | — |
| 3 | `train_reasoner` | `checkpoints/lcm_reasoner.pt` (semilla `LCM_SEED`=0) | early stopping |
| 4 | `evaluate_reasoner` | `reports/lcm_evaluation.json` | 100 % top-1 en test |
| 5 | `read_book` | `data/libro.txt`, `libro_vocab.json` (sin oído aún: salta la medición) | (necesita `--libro`) |
| 6 | `pretrain_ear` | `checkpoints/ear_pre.pt`, `ear_lm.pt` (MLM, opcional/largo) | — |
| 7 | `train_ear` | `checkpoints/ear.pt` (usa el vocabulario y el preentrenamiento anteriores) | — |
| 8 | `evaluate_ear` | test c/d del oído | c ≈ 94 %, d ≈ 84 % |
| 9 | `read_book_medida` | repite `read_book` ya con oído: `reports/libro_muestras.txt` (informativo, opcional) | — |
| 10 | `get_data` | `data/ud/…` (commit fijado) | — |
| 11 | `train_school` | `checkpoints/school.pt`, `school_meta.json` | UPOS/UAS/lema ≈ 96,2 / 86,8 / 98,1 % |
| 12 | `eval_frases` | test de conversación (80 frases) | ≥ 75 % (referencia 91,2 %) |
| 13 | `eval_preguntas` | preguntas | ≥ 70 % |
| 14 | `check_todo` | **todas** las pruebas de los parches 44–59 (`reports/informe.txt`, `historial.json`) | `TODO CUMPLE` |
| 15–18 | `evaluate_online/negatives/inoculate/sleep` | aprendizaje al vuelo, negativos, vacuna, sueño | opcionales (`--rapido` los salta) |
| 19 | `verificar_manifiesto` | compara el código con el manifiesto | *Reproducción fiel* |

**Orden del oído desde cero:** `read_book` (saca texto y vocabulario) → `pretrain_ear` → `train_ear`. Antes (hasta el parche-61)
`read_book` exigía un `ear.pt` que todavía no existía; el primer intento real en tabula rasa lo detectó.

**El constructor debe generarse desde TU proyecto real.** `empaquetar_todo` y `manifiesto --guardar` se ejecutan en la copia
buena (la que has usado), nunca a partir de una copia ajena: si no, `manifiesto --verificar` marca DISTINTO/FALTA/SOBRA.

Cada paso deja su salida en `reports/reproduce_<paso>.log` y el resumen (códigos, tiempos, semilla) en
`reports/reproduce_resumen.json`. Si un paso falla se para y te dice cómo continuar (`--desde <paso>`).
Para comprobar métricas contra la referencia: `python -m scripts.manifiesto --verificar --metricas`
Pasa si **cada examen cumple su criterio** (el fijado antes de medir). La diferencia con la referencia (una ejecución
anterior) se muestra como información; con `--estricto` también falla si algo baja más de 3 puntos.
Motivo: dos reentrenamientos con la misma semilla dieron notas distintas (en exámenes de 10-19 preguntas, una sola
pregunta mueve 5-10 puntos), así que la referencia no puede ser un listón fijo.

## 3. Qué es determinista y qué no

- Semillas fijas: espacio conceptual `42`; datos sintéticos del oído `seed=1,2`; sintéticos de la escuela `seed=5`;
  `torch.manual_seed(LCM_SEED)` (por defecto 0) en razonador, oído y escuela; el preentrenamiento del oído usa 0.
  `reproduce` fija también `PYTHONHASHSEED=0`.
- Sin determinismo bit a bit entre CPU, MPS y CUDA (operaciones de punto flotante distintas): por eso el criterio es
  **CUMPLE/NO CUMPLE** de cada examen, no la igualdad exacta.
- **Todo lo que sigue a la escuela** (extractor, preguntas, diálogo, coherencia, efectos, definiciones, semilla de fábrica)
  es código simbólico sin aleatoriedad: con la misma escuela da exactamente los mismos resultados.
- Memoria personal (`memory/lcm_memory.json`) no forma parte de la reproducción: empieza vacía y `think` carga la semilla de
  fábrica (`data/semilla.txt`) la primera vez.

## 4. Cómo se construyó (orden de los parches)

Cada fase añadió módulos y una prueba escrita **antes** de medir, con su criterio; los reintentos están etiquetados en
`reports/RESULTADOS.md`. Para rehacer el proceso paso a paso lee ese archivo en este orden:

| Fase / parche | Qué se añadió | Módulos principales | Pruebas |
|---|---|---|---|
| Fase 0 (base) | espacio conceptual con rasgos, razonador Transformer, motor simbólico, memoria y sueño | `src/ontology`, `src/model`, `src/reasoning/{engine,rule_engine}.py`, `src/memory`, `src/training` | `evaluate_reasoner/online/sleep/negatives/inoculate` |
| Fase 1 | oído (plantillas, MLM), escuela UD (UPOS, arcos, función, lema), extractor, preguntas (QA) | `src/language/{ear,ud,ud_synth,school_parser,extract,qa}.py` | `eval_frases`, `eval_preguntas`, `preguntas_ciegas` |
| Fase 2 (≤ parche-49) | coordinaciones, nombres propios ambiguos, discurso, deducción con lecciones | `discourse.py`, `reasoning/lessons.py` | `frases_largas_ciegas`, `discurso_ciego`, `preguntas_deduccion` |
| parche-50…53 | conceptos y herencia, tiempo, fechas absolutas | `lessons.inherit/canon`, `fechas.py` | `conceptos`, `tiempo`, `herencia`, `fechas` |
| parche-54 (bloque A) | conversación básica | `dialogue.py` | `dialogo`, `dialogo_ciego` |
| parche-55/56 (bloque B) | intransitivos, estados, modales, cantidad, comparaciones, causa, lugar | `extract.py`, `irregulares.py`, `qa.py` | `estados`, `cantidad` (+ciegas) |
| parche-57 (bloque D) | coherencia, cambio de estado, procedencia | `reasoning/coherence.py` | `coherencia` (+ciega) |
| parche-58 (bloque E) | definiciones: sinónimos, contrarios, «sirve para», verbos | `dialogue._definitions`, `lessons.verb_derive` | `definiciones` (+ciegas) |
| parche-59 (bloque C) | núcleo de fábrica: semilla, parentesco, partes, efectos | `semilla.py`, `data/semilla.txt`, `reasoning/efectos.py` | `nucleo` (+ciego) |
| parche-60 | este paquete: reproducibilidad | `scripts/{manifiesto,empaquetar_todo,reproduce}.py`, `get_data.py` | `tests/test_reproducibilidad.py` |

Método (se repite en cada fase): 1) escribir la prueba y el criterio **antes**; 2) medir la línea base; 3) implementar;
4) primera medida (se informa aunque no cumpla); 5) arreglar y medir de nuevo, **etiquetado como reintento**;
6) `python -m scripts.check` para vigilar regresiones; 7) pruebas ciegas con frases distintas.

## 5. Fallos conocidos (también tras reproducir)

La escuela lee «Clara» como adjetivo; «Pedro cocina pasta» como intransitivo; «Un salmón nada»; «muerde/ama … a» (convención
de la «a» personal en el test relajado); «Javier y Ana ven la televisión en el salón» (a quién cuelga el complemento);
«¿Es una figura un triángulo?» (se contesta con la deducción inversa). Están en los informes de `check`: si tu reproducción
muestra **otros**, es una diferencia real que investigar.
