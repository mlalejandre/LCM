# LCM 1.9 — Auditoría experimental de roles conceptuales con Escuela UD

## Pregunta experimental

¿Mejora la interpretación de un mismo acontecimiento expresado en diferentes estructuras del español, manteniendo la procedencia de los hechos, sin convertir hipótesis o árboles malformados en afirmaciones?

El parche introduce `src/semantics/ud19.py`, que utiliza **la API real** `SchoolParser.tree(texto)` cuando existe un checkpoint de Escuela disponible. Lee lema, sujeto, complemento directo, oblicuos y casos introducidos por preposición, y resuelve únicamente acontecimientos cuyo verbo tiene un marco conceptual de transferencia documentado en `acciones18.json`. La puntuación de coseno no se interpreta como confianza; ninguna relación se inventa por similitud.

**La auditoría NO evalúa el checkpoint neuronal de la instalación del usuario.** Aquí solo se dispone del código de `SchoolParser`, no de `checkpoints/school.pt` ni de su entorno completo de entrenamiento. Se han empleado árboles de dependencias anotados sintéticamente (oráculo) y perturbaciones controladas para examinar el *procesamiento posterior* de la Escuela. Es una **cota superior condicionada a que la Escuela entregue el análisis correcto**, no una medida de comprensión general del español.

## Protocolo

1. Se conserva el módulo 1.8 para la comparación. Los dos sistemas reciben las mismas oraciones y preguntas. La versión 1.9 recibe, adicionalmente, un árbol UD oráculo que representa la interfaz esperada de la Escuela; la 1.8 utiliza su analizador anterior.
2. Desarrollo: 400 casos; se revisaron errores de acentuación superficial y participios. No se utilizaron para declarar generalización.
3. Reserva de combinaciones: 2.400 casos con semilla 374893, nombres, objetos y verbos recombinados. Ocho familias de 300 casos, cinco positivas, dos de abstención y una de árboles inválidos. **El generador y las construcciones gramaticales son conocidos**, aunque las combinaciones de esta semilla no se usaron en desarrollo.
4. Se calculan por separado 2.100 casos comparables y 300 casos de árbol inválido. No es metodológicamente válido penalizar a 1.8 por un árbol sintáctico que nunca consume.
5. Robustez: 2.000 entradas con diez perturbaciones, con semilla 19261118 (nueve clases de alteración y el caso correcto). Este conjunto prueba el rechazo de errores definidos en el simulador, no de todos los errores posibles de una red neuronal.
6. Regresión: pruebas de visión, semántica, composición, narrativa y memoria; no cambian checkpoints, embeddings, cartuchos ni hechos anteriores.

## Resultados

| Experimento | LCM 1.8 | Puente 1.9 | Interpretación |
|---|---:|---:|---|
| Casos comparables | 1.234/2.100 (58,76 %) | 2.100/2.100 (100 %) | Extracción y respuesta bajo gramática controlada |
| Árboles inválidos | No aplicable | 300/300 abstenciones | Control de calidad sintáctica |
| Perturbaciones independientes | No aplicable | 2.000/2.000 según rúbrica | No se observaron afirmaciones indebidas ante estas perturbaciones |
| Regresiones dirigidas | — | 192/192 | Sin regresiones detectadas en módulos probados |

La puntuación de 100 % es propia de un dominio reducido, ejemplos sintéticos y un oráculo de sintaxis. No significa que LCM haya alcanzado 90 % o 99 % en conversaciones abiertas. No se ha validado con el modelo Escuela entrenado. El conjunto de perturbaciones solo comprueba las alteraciones que genera; un fallo de la Escuela que produzca un árbol **válido pero semánticamente incorrecto** puede seguir ocasionando errores.

La batería total de la copia reconstruida contiene al menos un archivo de `intents_modelo.json` truncado. La ejecución global se detiene ahí (JSONDecodeError), defecto del material reconstruido ajeno a este parche. La batería dirigida puede ejecutarse sin ese modelo corrupto.

## Garantías de comportamiento verificadas

- No convertir una negación, hipótesis, predicción de futuro o declaración modal en un traspaso consumado.
- Interpretar `Luis recibió el libro de Ana` y `El libro fue entregado a Luis por Ana` como la misma orientación de roles cuando la sintaxis es fiable.
- Conservar la fuente como `texto_declarado`: narrarlo no equivale a observarlo.
- No inferir quién es el dueño legal a partir de una entrega.
- No deducir la posesión actual a partir de una transferencia etiquetada como «ayer».
- Abstenerse con un pronombre sin antecedente o género compatible, o con objetos conflictivos.
- Conservar los datos de 1.8 y delegar cuando 1.9 no dispone de información suficiente.

## Limitaciones restantes y prioridades

1. El paso principal pendiente es ejecutar **la Escuela neuronal real** sobre textos humanos independientes, computando exactitud y calibración de papeles gramaticales. Es imposible estimar ese rendimiento a partir de árboles oráculo.
2. La extracción nueva aborda un marco conceptual de transferencia, no todas las clases de verbos, subjetivas, discursos indirectos, coordinación profunda ni conversaciones abiertas arbitrarias.
3. Persisten dos memorias narrativas en paralelo (1.8 y 1.9): hay delegación conservadora a episodios anteriores, pero aún no una fusión temporal de ambos registros. Evitar adjudicar posesión actual cuando hay historias divergentes.
4. Si la Escuela produce una estructura UD formalmente válida pero con roles intercambiados de manera coherente, los validadores formales pueden no detectar ese error.
5. Debe establecerse un corpus humano externo bloqueado antes de ampliar gramática; las pruebas actuales recombinan plantillas y no cuantifican cobertura de español espontáneo.

## Reproducir

Desde la raíz del LCM:

```bash
python -m pytest -q tests/test_ud19.py
python -m scripts.evaluar_ud19 --n 2400 --semilla 374893 --guardar reports/ud19_auditoria.json
python -m scripts.evaluar_ruido_ud19 --n 2000 --semilla 19261118 --guardar reports/ud19_ruido.json
python -m pytest -q tests/test_narrativa18.py tests/test_discurso17.py tests/test_dialogo16.py tests/test_ud19.py
```

No se debe sumar la salida de estos exámenes al resultado del LCM global como si midieran lo mismo.
