# Estado del proyecto LCM (para retomar el trabajo)

Ultima actualizacion: 2026-11-06, al cerrar la Fase 1.

## Objetivo y reglas de trabajo
- Meta: que el LCM aprenda ESPANOL y converse en lenguaje natural SIN LLM, aprendiendo "al vuelo" en el dialogo y
  consolidando al "dormir". El libro (La Regenta) es solo texto en bruto; el objetivo NO es aprender el libro.
- Metodo: "parche tras parche". Cada parche es un `parche-N.py` autocontenido (diccionario FILES + instalador con copias
  en `.parche_backups/<fecha>`; solo compila los .py). El usuario lo copia como `parche.py` en `~/Desktop/LCM`, lo ejecuta
  (venv, Mac MPS) y pega las salidas.
- Criterios de decision SIEMPRE fijados antes de medir; los fallos se informan tal cual, nunca se reescribe un criterio
  despues. Un reintento tras arreglar fallos conocidos se etiqueta como reintento. Explicaciones al usuario en espanol sencillo.
- No hacer commit/push a GitHub. Sandbox: Linux solo CPU, sin acceso a su disco ni a GitHub (los modelos reales se miden en su Mac).

## Mapa del codigo
- `src/ontology`, `src/model`, `src/reasoning`: espacio conceptual (vectores deterministas), razonador latente, motor de reglas.
- `src/training/online.py`: aprendizaje online (canario con rollback, `inoculate` = vacuna de relaciones nuevas).
- `src/memory`: `store.py` (hechos, lecciones, `surface`/`display` para hablar con las palabras del usuario), `schema.py`,
  `sleep.py` (ciclo de sueno), `negatives.py` (negativos + relaciones fantasma).
- `src/language`: `ear.py` (oido de plantillas, preentrenado con MLM), `ud.py` (escuela: UPOS, arcos, funcion, lema, mayuscula),
  `ud_synth.py`, `extract.py` (arbol -> proposiciones + plantilla de superficie), `school_parser.py`, `qa.py` (preguntas).
- `scripts/think.py`: la conversacion. `reproduce.py`: todo el proceso. `eval_*`: tests. `clean.py`: limpieza.
- Datos: `data/frases_prueba.tsv` (80 frases), `data/preguntas_prueba.tsv` (19), `data/preguntas_ciegas.tsv` (31, ya medido).

## Resultados (ver reports/RESULTADOS.md)
Conversacion 90,0 % relajado / 85,0 % exacto (80 frases); preguntas 19/19 (tras ajustar) y ciego 29/31 = 93,5 %;
UD triples 35 % (NO CUMPLE el 60 %); oido: c 94,1, d 84,1.

## Como funciona QA (Fase 1, cerrada)
Pregunta -> afirmacion con hueco "Xqx" -> misma escuela -> busqueda en memoria (relacion tolerante: 3 primeras letras + preposicion,
la "a" personal no cuenta, o misma forma verbal guardada en `surface`) -> deduccion con lecciones ("Lo deduzco") -> "No lo se"
(mundo abierto). Los adjetivos con funcion obj cuentan como objeto (matematicas).

## Problemas abiertos (candidatos para la Fase 2)
1. Frases largas / varias proposiciones / subordinadas (UD triples 35 %; "Clara canta en el coro de la iglesia" no extrae nada).
2. Pronombres y dialogo de varias frases (sin correferencia).
3. Fallos de QA: "Rosa lee Xqx." no se lee; sí/no con verbo antes del sujeto y articulo ("¿Enseña la maestra matematicas?").
4. Lemas irregulares (muerder/morder, mendar) y convencion de la "a" personal (conocer_a vs conocer).
5. ENTENDI no entrena la escuela; el sueno no consolida la escuela.
6. Relaciones creadas antes de la vacuna (p. ej. ESCRIBIR) alucinan hasta un DORMIR.
7. (resuelto en Fase 2) Preguntas con deduccion por reglas ensenadas: src/reasoning/lessons.py, test deduccion_12.
8. Las respuestas no son lenguaje natural libre (plantillas guardadas); falta generacion.
9. Aprendizaje integral desde texto corriente (prediccion del siguiente token) sigue sin hacerse mas alla del MLM del oido.

## Fase 2 (en curso)
- Hecho: coordinaciones (sujetos/objetos/complementos/verbos con sujeto compartido) y adjetivo con mayuscula como nombre propio (extract.py v3);
  frases largas ciegas 37 -> 92,6 %. think acepta varias proposiciones por frase.
- Hecho (parche-44, por medir): discurso = `src/language/discourse.py` (tema = sujeto anterior; sustituye a "el/ella" y es el sujeto de un verbo
  principal sin sujeto); think divide varias frases y recuerda el tema. Linea base 9,5 %, criterio >= 70 %.
- Hecho (parche-47): deduccion con las lecciones del usuario (reglas con variables, explicacion "porque..."), test deduccion_12 100 %; `python -m scripts.check` lo mide todo. Ya tengo ear.pt/school.pt/school_meta.json en el sandbox (reproducen los numeros del usuario).
- Pendiente de Fase 2: ENTENDI que entrene la escuela + consolidar en DORMIR; medir preguntas con deduccion; pronombres de objeto (lo/la);
  fallos de la escuela con nombres propios que son palabras comunes.

## Fase 3: integrar conceptos nuevos desde lenguaje natural (requisito del usuario, 2026-11-06)
El usuario pide que el modelo integre por si mismo conceptos nuevos (acciones, figuras geometricas, expresiones temporales...) a partir de texto normal.
Hoy un concepto nuevo = un nombre con rasgo de identidad; el nucleo neuronal NO ve su tipo. Plan por pasos (cada uno con test ciego fijado antes):
1. HECHO (parche-50): definiciones "X es un Y", jerarquias con deduccion (ES transitiva, regla por defecto con explicacion), acciones como concepto
   ("Cocinar es una accion"), propiedades con numeral ("tres_lados"). Simbolico + QA. Test conceptos_14.
2. HECHO (parche-51, version basica): tiempo como atributo del hecho (when/when_disp) para ayer/hoy/dias/meses/estaciones/anios; preguntas cuando/si-no/quien con tiempo. Falta: orden entre fechas (antes/despues), intransitivos, duraciones. (plan original: hueco de TIEMPO en las proposiciones (ayer, manana, en 2020, el lunes, antes/despues) y deduccion de orden.
3. Herencia de propiedades ("los poligonos tienen lados" -> el triangulo los hereda) y definiciones con rasgos ("con tres lados").
4. (Dificil) que el razonador NEURONAL use los tipos: reentrenar prepare_concepts/train_reasoner con vocabulario de rasgos abierto (isa:...), para
   que un concepto nuevo tenga vector por sus rasgos y no solo por su nombre.

## Siguiente paso sugerido
Fase 2: empezar por (1) y (3) con un test ciego nuevo de frases largas pre-registrado; luego (5) y (7).

- Fase 3 paso 3 (herencia de propiedades) HECHO en parche-52: `lessons.inherit/canon/deduce_all`, test data/herencia_prueba.tsv (10/10 tras reintento; primera 9/10).

- Fase 3 paso 4 (fechas absolutas + orden) HECHO en parche-53: `src/language/fechas.py`, `when_abs` en hechos, `QA.timeline`, comando natural "Hoy es ...". Test data/fechas_prueba.tsv (18/18 tras reintento; primera 16/18).

- Bloque A de docs/NUCLEO_BASICO.md HECHO en parche-54 (`src/language/dialogue.py`, tests data/dialogo_prueba.tsv + dialogo_ciego.tsv, scripts/eval_dialogo.py). Pendiente de ese bloque: persistir el nombre del usuario; "eso/lo anterior" mas alla de borrar; registro tu/usted solo en saludos.

- Bloque B parcial en parche-55: items 10, 11, 12 y 17 de NUCLEO_BASICO hechos (ver RESULTADOS). Faltan 13-16 (cuantificadores, duracion/frecuencia, causa, lugar relativo).

- Bloque B COMPLETO (con limites) en parche-56: items 13-16 de NUCLEO_BASICO. Siguiente: bloque C (conceptos de fabrica) o D (contradicciones y cambio de estado).

- Bloque D parcial en parche-57: items 29, 30 y 33 de NUCLEO_BASICO (contradicciones, cambio de estado, procedencia). Falta del D: antes/despues entre dos sucesos y comparar quien es mayor con fechas. Siguiente: bloque C (conceptos de fabrica) o E (aprender palabras/acciones por definicion).

- parche-59: bloque C (nucleo de fabrica: data/semilla.txt, parentesco/partes, efectos de dar/vender/abrir/ir). Con el 58 (E), 57 (D), 56/55 (B) y 54 (A) quedan hechos los bloques A-E de NUCLEO_BASICO (con limites).
- parche-60: reproducibilidad. `python -m scripts.manifiesto --guardar` (huellas + commits UD + metricas), `python -m scripts.empaquetar_todo` (LCM_construir_desde_cero.py), `scripts.reproduce` ampliado (tests, check, semilla, verificacion). Guia: docs/REPRODUCIR.md. Siguiente: entrenamiento (reentrenar la escuela con las correcciones acumuladas, ver "Clara" y similares).
