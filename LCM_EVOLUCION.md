# Evolucion del LCM: tres iteraciones

Este parche prepara una base experimental mas rigurosa. No afirma que el LCM
haya alcanzado razonamiento general: eso debe demostrarse con los resultados.

## Iteracion 1 — Ontologia con estructura semantica explicita

`ConceptSpace` compone cada vector a partir de rasgos declarados y codifica las
proposiciones con roles diferenciados (sujeto, predicado y objeto). Los textos
ES/EN quedan como verbalizaciones, no como fuente oculta de los vectores.

**Limite:** sigue siendo una ontologia diseñada manualmente. Para aproximarse a
semantica abierta y amplia habra que alinear estos vectores con datos externos,
un encoder multilingue o un procedimiento contrastivo; este parche no descarga
ni presupone modelos externos.

## Iteracion 2 — Generalizacion composicional

`prepare_concepts` crea proposiciones con entidades variables y divide los
datos en train/validacion/test. En transitividad, cada par ordenado de conclusion
pertenece a un unico split y las premisas proceden solo de pares train: las
conclusiones de validacion/test no se entrenan como objetivos ni se filtran
como entradas de entrenamiento. Otras reglas reservan instancias completas
para validacion y test.

El Transformer ahora recibe una mascara de padding y selecciona la ultima
posicion valida. El entrenamiento usa validacion y early stopping. La metrica
neuronal se informa; no se fuerza un umbral ni se presenta como razonamiento
probado.

## Iteracion 3 — Evaluacion y referencia simbolica

`RuleEngine` incorpora reglas auditables de transitividad, caida, fusion con
condicion de fundibilidad y cardinalidad. La no numerabilidad exige evidencia
explicita de ausencia de biyeccion con los naturales; ser infinito por si solo
no basta.

`evaluate_reasoner` mide similitud coseno y top-1 entre objetivos de test, y
ademas ejecuta pruebas del motor simbolico con entidades nuevas. La similitud
coseno es una distancia/alineacion geometrica, no una probabilidad calibrada.

## Orden de ejecucion

```bash
python -m scripts.prepare_concepts
python -m scripts.train_reasoner
python -m scripts.evaluate_reasoner
python -m scripts.think
```

Revisa `data/dataset_manifest.json` y `reports/lcm_evaluation.json` antes de
interpretar los resultados. Si la evaluacion neuronal es baja, no la ocultes:
usa el fallo como señal para revisar la composicion, los rasgos, los ejemplos o
la arquitectura.
