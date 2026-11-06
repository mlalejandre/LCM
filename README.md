# LCM · Large Conceptual Model

[![tests](https://github.com/mlalejandre/LCM/actions/workflows/ci.yml/badge.svg)](https://github.com/mlalejandre/LCM/actions/workflows/ci.yml)
![licencia MIT](https://img.shields.io/badge/licencia-MIT-blue)
![estado](https://img.shields.io/badge/estado-investigaci%C3%B3n%20en%20marcha-orange)

**Una IA que aprende español conversando, sin ningún LLM.**
Piensa en *conceptos* (vectores con sentido) y no en tokens, deduce con reglas legibles, explica por qué responde lo que responde y «duerme» para consolidar lo aprendido. Es pequeña, corre en un portátil y se puede reconstruir desde cero con un solo comando.

> **Estado: experimento de investigación.** Todo se mide con criterios fijados *antes* de medir, y las cifras de este
> README son de exámenes escritos por nosotros, así que son optimistas. En [Limitaciones](#limitaciones-honestas) y en
> `reports/RESULTADOS.md` está lo que **no** funciona todavía.

---

## Qué tiene de distinto

| Los LLM clásicos | LCM |
|---|---|
| Se entrenan una vez con medio internet y sus pesos quedan congelados | Aprende **en la propia conversación**, sin reentrenar |
| Trabajan con tokens (trozos de texto) | Trabajan con **conceptos**: cada concepto es un vector y cada frase, otro vector |
| La respuesta sale de una red opaca | Cada respuesta tiene un **porqué legible** («lo deduzco porque…») |
| Corregir un error exige reentrenar | Se corrige **cambiando un hecho** o una regla |
| No consolidan lo vivido | **Duermen**: refuerzan lo importante y sueltan el ruido |

No pretende competir con un LLM en conocimiento ni en fluidez. Explora otra receta: poco material, memoria abierta y razonamiento que se puede inspeccionar.

## Una conversación de ejemplo

Salidas reales de las pruebas del proyecto (`data/*.tsv`):

```
> La hierba es verde.
Entendido.
> ¿De qué color es la hierba?
La hierba es verde.

> Pedro es padre de Juan.
> Juan es padre de Luis.
> ¿Es Pedro abuelo de Luis?
Sí, lo deduzco.
> ¿Por qué?
Porque Pedro es padre de Juan, Juan es padre de Luis, y el padre del padre es el abuelo.

> Ana vive en Madrid.
> Ana vive en Sevilla.
> ¿Dónde vivía Ana?
Ana vivía en Madrid.

> Un tenedor sirve para comer.
> ¿Para qué sirve un tenedor?
Un tenedor sirve para comer.
```

Para probarlo tú: `python -m scripts.think` (escribe `AYUDA` para ver los comandos).

## Cómo funciona

```
 texto ──► Oído ──► Escuela ──► Memoria ──► Razonador ──► Diálogo ──► respuesta
          (plantillas) (sintaxis)  (hechos)   (deducción)   (plantillas)
```

- **Escuela** (`src/language/ud.py`): analizador de dependencias entrenado con *Universal Dependencies* en español (GSD + AnCora). Para cada palabra calcula categoría, a quién se une, función y lema. Un extractor (`extract.py`) convierte la frase en proposiciones *(sujeto, relación, objeto)*.
- **Espacio conceptual** (`src/ontology/concept_space.py`): cada concepto es un vector (128 dimensiones por defecto) construido como combinación ponderada de rasgos semánticos declarados y normalizado. Una proposición es otro vector: sujeto, predicado y objeto pasan por su **matriz de rol** y se suman, de modo que el mismo concepto cuenta distinto según el papel que ocupe.
- **Razonador** (`src/model/reasoner.py`): un *lector* separa cada premisa en tres ranuras restando el predicado, el sujeto y el objeto contra el catálogo de conceptos; un *emparejador* marca qué ranuras coinciden entre premisas (el término medio de una cadena); un transformer decide, para cada rol de la conclusión, de qué ranura copiar. El vector resultante se traduce al concepto más cercano.
- **Memoria** (`src/memory`): cada hecho guarda importancia, fuente (tú, conocimiento de fábrica o efecto de una acción), alias, contrarios, verbos hermanos y definiciones. Incluye el ciclo de **sueño**, que consolida lo importante, y **negativos** («Luis no come carne»).
- **Lecciones** (`src/reasoning/lessons.py`): reglas pequeñas y legibles (herencia entre categorías, comparaciones, transitividad, parentescos). Se pueden añadir con frases como `Si X es padre de Y entonces Y es hijo de X`.
- **Efectos de las acciones** (`src/reasoning/efectos.py`): si Ana da un libro a Luis, Ana deja de tenerlo; si Pedro abre la puerta, queda abierta.
- **Coherencia** (`src/reasoning/coherence.py`): distingue una contradicción de un cambio con el paso del tiempo.
- **Núcleo de fábrica** (`data/semilla.txt`): unas 110 frases normales (familia, días, para qué sirven los objetos) que entran por el mismo camino que lo que tú digas, etiquetadas como `semilla`. «Olvida todo» no las borra.
- **Diálogo** (`src/language/dialogue.py`): reglas y plantillas, sin LLM. Pregunta lo que no entiende y lo aprende.

Detalle de cada pieza y del plan: [`docs/ESTADO.md`](docs/ESTADO.md), [`docs/NUCLEO_BASICO.md`](docs/NUCLEO_BASICO.md) e historia del diseño en [`LCM_EVOLUCION.md`](LCM_EVOLUCION.md).

## Resultados

Ejecución completa **desde cero** en un Mac (MPS), con los criterios fijados antes de medir.

**Escuela**, sobre frases UD de prueba que nunca vio:

| Medida | Resultado | Umbral |
|---|---|---|
| Categoría gramatical | 96,2 % | ≥ 94 % |
| A qué palabra se une | 86,8 % | ≥ 85 % |
| Lema (forma base) | 98,1 % | ≥ 90 % |

**Exámenes por áreas** (`python -m scripts.check`; «ciego» = frases no vistas al escribir las reglas):

| Examen | Resultado | Criterio |
|---|---|---|
| Conversación (80 frases) | 90,0 % | ≥ 75 % |
| Frases largas ciegas | 85,2 % | ≥ 60 % |
| Cantidades / ciegas | 84,6 % / 78,6 % | ≥ 70 % / ≥ 60 % |
| Estados / ciegas | 96,3 % / 88,9 % | ≥ 70 % / ≥ 60 % |
| Fechas · Tiempo | 100 % · 100 % | ≥ 75 % |
| Herencia | 80,0 % | ≥ 75 % |
| Conceptos | 92,9 % | ≥ 75 % |
| Deducción | 100 % | ≥ 75 % |
| Preguntas / ciegas | 100 % / 96,8 % | ≥ 70 % / ≥ 80 % |
| Discurso | 90,5 % | ≥ 70 % |
| Diálogo / ciego | 96,9 % / 94,6 % | ≥ 75 % / ≥ 60 % |
| Coherencia / ciega | 96,6 % / 84,2 % | ≥ 70 % / ≥ 60 % |
| Definiciones / ciegas | 96,6 % / 100 % | ≥ 70 % / ≥ 60 % |
| Núcleo de fábrica / ciego | 100 % / 100 % | ≥ 70 % / ≥ 60 % |

Más 53 pruebas unitarias. **Las notas cambian de un reentrenamiento a otro** (en exámenes de 10–19 preguntas, una sola pregunta mueve 5–10 puntos). Por eso lo que se exige es que cada examen **cumpla su criterio**, no que coincida al decimal.

## Instalación y uso rápido

Necesitas Python ≥ 3.10 y `git`. Funciona en CPU, CUDA o Mac (MPS).

```bash
git clone https://github.com/mlalejandre/LCM.git
cd LCM
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q tests          # comprobación rápida, no necesita datos ni modelos
```

Los modelos entrenados **no se incluyen** en el repositorio: se generan con el paso siguiente.

## Reproducirlo desde cero

```bash
python -m scripts.reproduce --libro mi_texto.txt
```

`mi_texto.txt` es cualquier texto largo en español (una novela de dominio público, por ejemplo). **No** se incluye ningún libro: el oído lo usa para aprender vocabulario y estilo, y el proyecto no depende de uno concreto.

`reproduce` ejecuta, en orden y parando si algo falla: conceptos → razonador → lectura del texto → preentrenamiento → oído → descarga de UD → escuela → exámenes → evaluaciones de aprendizaje online y sueño → verificación del manifiesto. Tarda de decenas de minutos a horas según la máquina.

Opciones útiles: `--lista` (ver los pasos), `--rapido` (salta lo opcional), `--desde PASO` (continúa donde falló), `--semilla N`. Cada paso deja su registro en `reports/reproduce_<paso>.log`. `train_school` muestra el progreso y guarda un punto de control por época, así que si lo cortas se retoma solo.

**Todo en un solo comando** (borrar el proyecto a «tabula rasa», reconstruirlo y reentrenarlo):

```bash
python limpieza.py                          # ensayo: ves qué se quitaría y qué se conserva
python limpieza.py --aplicar --reconstruir  # hace todo, con confirmación previa
```

Guía completa (carpeta vacía → mismo proyecto, huellas, semillas, qué es determinista y qué no): [`docs/REPRODUCIR.md`](docs/REPRODUCIR.md).

### Qué es reproducible

| Qué | Cómo | ¿Idéntico? |
|---|---|---|
| Código, datos de prueba, tests, documentos | `python -m scripts.manifiesto --verificar` (huellas SHA-256) | Sí |
| Corpus UD | `scripts.get_data` con el commit fijado en el manifiesto | Sí |
| Pesos entrenados | `scripts.reproduce` (misma semilla y datos) | **No**, varían entre CPU, MPS y CUDA; se exige que los exámenes **cumplan** |

## Estructura

```
src/ontology    espacio conceptual (vectores, matrices de rol)
src/model       razonador latente y capas
src/reasoning   lecciones, coherencia, efectos de acciones, motor de reglas
src/language    oído, escuela (UD), extractor, preguntas (qa.py), diálogo, semilla
src/memory      memoria, esquemas, ciclo de sueño, negativos
src/training    aprendizaje online con canario y vacunas
scripts/        entrenamiento, evaluaciones, check, think (la conversación)
data/           exámenes (.tsv), núcleo de fábrica (semilla.txt)
tests/          pruebas unitarias sin datos
docs/           estado, núcleo básico, reproducibilidad
reproducibilidad/  manifiesto con huellas y commits de los corpus
reports/        RESULTADOS.md (con lo que falla) e historial
```

## Limitaciones honestas

- Los exámenes los escribimos nosotros: las notas son una cota optimista, no una medida independiente.
- La **escuela** aún lee mal algunos casos: nombres propios que son palabras comunes («Háblame de Clara»), verbos sin complemento («Pedro cocina pasta»), sujetos coordinados («Javier y Ana ven la tele») y la «a» personal en el lema («conoce a» → `conocer_a`).
- Las respuestas usan plantillas, no generación libre de texto.
- El entrenamiento no es reproducible al decimal entre máquinas; algunas notas de conversación bajan o suben unos puntos entre reentrenamientos.
- El cierre de `evaluate_negatives` («negativos») sale «NO ADOPTADO» por un margen mínimo con la regla fijada de antemano (reglas 100 % → 97 %); se informa tal cual.
- Es un experimento en español. Que la receta sirva para otros idiomas es una hipótesis, no un resultado.

## Hoja de ruta

- Reentrenar y mejorar la escuela (más datos o épocas, mejores frases sintéticas).
- Recordar el nombre del usuario entre sesiones.
- Entender el *antes y el después* entre sucesos.
- Más asignaturas para el currículo (cantidades, lugares, causas).

## Contribuir

Se agradece revisar, compartir y mejorar. Lo más útil:

1. **Abre una *issue*** con una frase que el sistema entienda mal y lo que esperabas.
2. **Añade exámenes** con el mismo formato de los `.tsv` de `data/`. Para que cuenten como ciegos, escríbelos *antes* de ver cómo responde.
3. Si mejoras algo, **fija el criterio antes de medir** y pasa `python -m scripts.check`. Los fallos se informan tal cual, sin reescribir criterios.
4. Ejecuta `python -m pytest -q tests` antes de proponer un cambio.

## Datos y licencias

Código: licencia **MIT** (ver [`LICENSE`](LICENSE)). Corpus *Universal Dependencies*: **GSD** (CC BY-SA 4.0) y **AnCora** (CC BY 4.0). Se descargan con `python -m scripts.get_data` en una versión fija y **no se redistribuyen** aquí. Los textos que aportes son tuyos.