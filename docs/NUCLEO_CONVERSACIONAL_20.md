# LCM 2.0 · Núcleo conversacional unificado

Parche: `parche_nucleo20.py` · Fecha: 18 de noviembre de 2026 · Punto de partida: LCM 1.9 de fábrica (sin `memory/` ni cartuchos).

## Qué problema resuelve

En LCM 1.9 cada capa (1.6 diálogo, 1.7 discurso, 1.8 narrativa, 1.9 UD y el conversador de base) guardaba lo que entendía en
**su propio almacén** y contestaba solo con él. Una frase entendida por una capa era invisible para las demás, y una capa que no
encontraba un dato respondía «No consta» aunque otra lo tuviera. Las relaciones entre conceptos no llegaban a afianzarse porque
no había un sitio único donde vivieran.

LCM 2.0 añade un **grafo único** para la conversación (`src/nucleo20/`):

- **Entidades**: la persona que habla, el propio LCM, personas y cosas con nombre, cosas de alguien («el perro de Elena»,
  «tu coche»), grupos («tus padres») y clases («los perros»).
- **Relaciones** entre entidades: parentescos, amistad, pertenencia, papeles con valor («tu color favorito es el azul»).
- **Marcos**: quién hace qué, a quién, dónde, cuándo, cuánto; con negación, tiempo verbal, vigencia (lo que era antes y lo que
  es ahora), causa («porque…») y la frase exacta de la que salió cada dato.

Sobre ese grafo se deduce: herencia de clases (lo dicho + semilla de fábrica), parentescos (abuelo, tío, primo, nieto, cuñado…),
relaciones simétricas e inversas, comparaciones transitivas y por edad, sumas por categoría, efectos de acciones (dar, vender,
perder, poner, mudarse), valores únicos (vivir en, estar en, edad, color) y contrarios (grande/pequeño…).

Reglas de honestidad del núcleo:

1. Solo guarda una afirmación si la ha entendido **entera**. Si no, delega el turno en las capas anteriores sin tocar nada.
2. Si no tiene prueba, **se abstiene y lo dice**, indicando lo que sí sabe. No rellena con coincidencias de texto.
3. Cada respuesta guarda su justificación: «¿Por qué?» / «¿Cómo lo sabes?» devuelven la frase original o la cadena de deducción.
4. El LCM no finge cuerpo, gustos ni opiniones cuando se le pregunta por sí mismo.

## Cómo encaja con lo anterior

`Motor.chat` → **núcleo 2.0** → (si no entiende o no sabe) capas 1.4–1.9 → conversador de base.

- El núcleo trabaja con las categorías y lemas de la **Escuela** (`parser.tree`) y un análisis propio de sintagmas. Solo se activa
  con la Escuela real; con los analizadores de prueba de los tests antiguos no interviene, así que **esos tests siguen midiendo
  las capas 1.4–1.9 tal cual**. Se puede apagar con `LCM_NUCLEO20=0`.
- Lo que guarda el núcleo se **refleja** en `memory/lcm_memory.json` como tripletas clásicas, de modo que el explorador de
  conceptos, los cartuchos y las capas anteriores lo ven. Su grafo completo se guarda en `memory/lcm_nucleo20.json`.
- **Arbitraje de capas** (`src/quality/arbitraje20.py`): una abstención de una capa ya no cierra el turno; se retiene y solo se
  emite si ninguna otra aporta una respuesta fundada.
- **Pertinencia documental** (`grounding.py`, `evidencia15.py`): una cita de un texto leído es pertinente si la entidad consultada
  consta en el *documento* de la cita, no necesariamente en la frase (los textos usan pronombres y sujetos omitidos). Esto arregla
  las 5 regresiones de `tests/test_parche129.py` sin reabrir el caso «María / Lamine Yamal».
- **Multimodal**: el flujo de imagen no cambia. Además, «mi coche es de ese color» enlaza con el color de la última imagen vista.
- «Olvida que…» y «Olvida todo» (con su confirmación) borran lo mismo en el grafo y en la memoria clásica.

## Método de evaluación

Cada diálogo es una sesión nueva de fábrica (memoria vacía + `data/semilla.txt`). Cada turno lleva un criterio escrito antes de
ejecutar: `ACK`, `ABST` (debe abstenerse; afirmar algo cuenta como **afirmación falsa**) o grupos `a|b;!c;^d`.
Veredictos: acierto · afirmación falsa (dato erróneo o alucinación) · abstención indebida · error.

Conjuntos (carpeta `lab/`):

| Conjunto | Qué es | Uso |
|---|---|---|
| Tandas 1–4 | 40 diálogos escritos a mano, de 8 a 18 turnos | Desarrollo: analizar causa de cada fallo y parchear |
| Banco *dev* | Generado: 19 categorías, vocabulario A | Desarrollo |
| Banco *validación* | Generado: vocabulario B disjunto y, la mitad de las veces, formulaciones que no existen en *dev* | Solo cifras agregadas |
| **Examen final ciego** | 30 diálogos escritos con el código congelado, vocabulario y formulaciones nuevos | Se ejecutó **una vez** |
| Exámenes del autor | Los 28 `data/*.tsv` del proyecto pasados por `Motor.chat` | Medida independiente (no escrita por quien parchea) |

## Resultados

Medición a gran escala (5 semillas, 1.140 diálogos por conjunto):

| Conjunto | Turnos | LCM 1.9 acierto | LCM 1.9 afirm. falsas | LCM 2.0 acierto | LCM 2.0 afirm. falsas |
|---|---|---|---|---|---|
| Banco dev | 12.335 | 72,61 % | 6,42 % | 99,94 % | 0,06 % |
| Banco validación | 12.331 | 69,02 % | 6,27 % | 98,77 % | 0,25 % |

Examen final ciego (265 turnos, una sola ejecución con el código congelado):

| | Acierto | Afirmaciones falsas | Abstención indebida |
|---|---|---|---|
| LCM 1.9 | 53,96 % | 6,79 % | 104 |
| **LCM 2.0** | **84,91 %** | **2,64 %** | 33 |

Exámenes del autor (703 preguntas de `data/*.tsv`, reproducción aproximada por el chat): 72,40 % → 85,06 %.

Tests: `tests/test_parche129.py` vuelve a pasar entero; se añaden 44 pruebas en `tests/test_nucleo20.py` (árboles congelados).

### Cómo leer estas cifras (sin adornos)

- El **84,9 %** del examen final es la cifra que mejor estima una conversación con frases nuevas. El 98,8 % de validación está
  inflado: aunque su vocabulario es distinto, comparte plantillas con el banco de desarrollo.
- Tras medirlo, los fallos del examen final se usaron para una última ronda de arreglos (ahora da 92,8 %), pero **ese número ya no
  es ciego** y no debe citarse como tal. La siguiente iteración necesita un examen nuevo.
- El criterio `ACK` es benévolo: acepta cualquier respuesta que no sea un fallo, sin comprobar que el dato quedó bien guardado
  (eso se comprueba en las preguntas posteriores del mismo diálogo).
- Los exámenes del autor se han pasado por `Motor.chat` con la semilla cargada, no con sus scripts originales; sirven para
  comparar 1.9 y 2.0 en igualdad de condiciones, no como nota oficial de esos exámenes.

## Lo que todavía falla

- **Formulaciones no previstas**: categorías más flojas del examen final ciego: comparativos (62 %), datos de la persona (56 %),
  familia (74 %). Casos reales: «¿Cuántos años nos llevamos?», «¿Quién de los dos…?», «Tomás es el padre de A y de B» (este ya
  arreglado), sujetos elípticos encadenados.
- **Errores de la Escuela** en frases cortas (p. ej. `bebió`→NUM, `té`→PRON, `Él`→DET, nombres propios como sustantivos). El núcleo
  compensa muchos con morfología propia, pero no todos; reentrenar la Escuela con frases conversacionales cortas ayudaría más que
  seguir compensando.
- **Nombres propios que son palabras comunes** (Rosa, Clara, León) en minúscula o a mitad de frase.
- **Subordinadas, condicionales, estilo indirecto, creencias**: el núcleo no las interpreta; las delega en las capas 1.6–1.9.
- **Deducciones con género supuesto por el nombre** («Luis es hijo de Ana» → «Ana es la madre de Luis»). El examen del autor
  esperaba abstención; se ha dejado la deducción, pero es una suposición.
- **Respuestas por plantillas**: correctas pero poco variadas; no hay generación libre.
- El núcleo usa sinónimos e hiperónimos del léxico (WordNet) solo como apoyo para confirmar, y puede heredar sus ambigüedades.

## Cómo repetir las mediciones

```bash
python -m pytest -q tests/test_nucleo20.py tests/test_parche129.py
python -m lab.tanda01            # ... tanda02, tanda03, tanda04 (con -v implícito: muestra cada turno)
python -m lab.medir etiqueta 12 1,2,3,4,5          # banco dev + validación (≈ 3–4 min en CPU)
LCM_NUCLEO20=0 python -m lab.medir base19 12 1     # la misma medición sin el núcleo
python -m lab.examenes_usuario -v                  # exámenes data/*.tsv por el chat
python -m lab.examen_final -v                      # ya no es ciego: úsalo como tanda 5
```

Para seguir entrenando: escribir una tanda nueva de 10 diálogos con sus criterios **antes** de ejecutarla, medir, buscar la causa
de cada fallo (`python -m lab.sonda2 -t` muestra qué capa contestó y cómo etiquetó la Escuela cada palabra), corregir, y volver a
pasar todas las tandas, el banco y `pytest`. Cuando una tanda ciega se usa para corregir, deja de ser ciega.
