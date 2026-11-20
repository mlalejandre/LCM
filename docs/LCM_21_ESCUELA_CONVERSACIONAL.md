# LCM 2.1 · Escuela conversacional y segunda ronda del núcleo

Parche: `parche_lcm21.py` (sobre LCM 2.0) · 18 de noviembre de 2026

## 1. Escuela: afinado con frases conversacionales

**Diagnóstico.** De las ~22.000 frases UD con las que se entrenó la Escuela, solo ~150 son preguntas y ~1.200 tienen siete
palabras o menos. La Escuela casi no había visto «¿Dónde vive Pablo?», «Tengo dos gatos» o «¿Es alta tu hermana?», y fallaba
justo ahí (`bebió`→NUM, `té`→PRON, `Él`→DET, `Nuria`→NOUN...).

**Qué se hace.** `src/language/ud_conv.py` genera frases conversacionales cortas con su árbol correcto en convención UD:
44 marcos (afirmaciones en 1.ª y 3.ª persona, copulativas, «tener», «gustar», «llamarse», comparativas, negación, y preguntas
de sí/no y con quién/qué/dónde/cuándo/cuánto/cómo), con vocabulario cotidiano y un 30 % de escritura descuidada (sin tildes,
sin «¿», en minúsculas). `scripts/afinar_escuela.py` **afina** la Escuela existente (no la reentrena): 3 épocas con 24.000
frases conversacionales + 12.000 frases UD reales por época para que no olvide. Tarda unos 4 minutos en CPU.

**Regla de decisión, fijada antes de medir.** La Escuela afinada se adopta solo si en frases conversacionales con vocabulario
reservado gana ≥ 3 puntos de categoría sin perder lema, y en UD test no pierde más de 0,5 (categoría), 1,0 (dependencia) y 0,5
(lema). Si no cumple, el script restaura la anterior.

**Resultado (mi ejecución, CPU, semilla 0):**

| | Categoría | Dependencia | Función | Lema | Frases con categoría y lema perfectos |
|---|---|---|---|---|---|
| Conversacional, antes | 93,76 % | 91,44 % | 81,90 % | 94,96 % | 62,5 % |
| Conversacional, después | 99,13 % | 99,70 % | 99,40 % | 99,19 % | 93,8 % |
| UD test, antes | 95,67 % | 87,53 % | 82,05 % | 97,78 % | — |
| UD test, después | 95,81 % | 87,51 % | 81,94 % | 97,80 % | — |

CUMPLE la regla. **Lectura honesta:** el examen conversacional usa palabras reservadas pero los *mismos marcos* que el
entrenamiento, así que el 99 % es optimista para frases con estructuras que el generador no cubre. Y el efecto sobre el diálogo
es pequeño (examen ciego 2: 80,4 % → 81,4 % solo con la Escuela nueva), porque el núcleo 2.0 ya compensaba casi todos esos
errores con su propia morfología. Lo que aporta es una base más limpia: desaparecen causas de fallo en vez de taparse.

## 2. Núcleo: lo que entiende ahora y antes no

Fallos encontrados con el antiguo examen ciego (ya tanda 5) y con una tanda nueva (tanda 6, 58,5 % al primer intento):

- **Existencia y cantidades**: «En mi calle hay tres bares», «¿Qué hay en el salón?»; «dos hermanas y un hermano» se cuentan por
  separado y en total; sumas por categoría que avisan de lo que no saben clasificar («Al menos dos… no sé si un hámster cuenta»).
- **Elipsis**: «más viejo que el de Pilar», «el mío o el de Pilar».
- **Comparaciones**: superlativos («el más alto», «el mayor de los dos», «el pequeño»), por medida («¿Quién mide más?»),
  diferencia de edad («¿Cuántos años se llevan?»), «¿Quién es más fuerte que Daniel?».
- **Familia**: «padre de A y de B», «¿Qué es Amparo de Pilar?», «¿De quién es hija Pilar?», «están casados», «tienen otro hijo
  llamado Ismael», «el abuelo» ya no devuelve a la abuela.
- **Persona**: «Soy X y trabajo de…» (dos cláusulas), profesión con cualquier sustantivo, «Mi cumpleaños es el 14 de marzo»,
  «tiene 47» como edad, «Me siento feliz» = «estoy feliz».
- **Sucesos**: sujeto pospuesto («Vinieron mis abuelos»), «Le regalamos un viaje», «¿Cuándo fue la boda?», «cumplió 30 años»,
  «Hace un mes se mudó a…».
- **Formas de preguntar**: «¿Quién es el que compra leche?», «¿Cuánto tiempo llevo en…?», «¿Qué no hace Tomás?».
- **Trato**: «He tenido un día horrible», «Me has ayudado mucho», «Hasta otro día», «¿Has estado alguna vez en…?», «¿Qué
  deporte te gusta?», «¿Tú tienes…?».
- **Robustez**: nombres que parecen verbos («Tomás», «Marcos») ya no se toman por verbos; verbos que solo conoce la Escuela
  («apasiona») se aceptan; una pregunta pendiente del diálogo de base ya no secuestra los turnos siguientes.

## 3. Resultados de diálogo

| Medición | Turnos | LCM 1.9 | LCM 2.0 | LCM 2.1 |
|---|---|---|---|---|
| **Examen ciego 2**: acierto | 301 | 48,2 % | 80,4 % | **91,4 %** |
| **Examen ciego 2**: afirmaciones falsas | 301 | 7,3 % | 5,0 % | **4,0 %** |
| Banco validación (5 semillas): acierto | 12.331 | 69,0 % | 98,8 % | 99,0 % |
| Banco validación: afirmaciones falsas | 12.331 | 6,3 % | 0,25 % | 0,32 % |
| Exámenes del autor `data/*.tsv` por el chat | 703 | 72,4 % | 85,1 % | 85,8 % |
| Tanda 5 (antiguo examen ciego 1, ya desarrollo) | 265 | 54,0 % | 84,9 % (ciego) | 99,6 % |
| Tanda 6 (desarrollo) | 94 | — | 58,5 % | 100 % |

### Cómo leerlo, sin adornos

- El **examen ciego 2** se escribió antes de empezar y sus transcripciones no se han leído: solo las cifras. Pero **no es del
  todo independiente**: lo escribió la misma persona que luego escribió la tanda 6, sobre las mismas áreas flojas, y varias
  construcciones coinciden. La mejora real con frases de otra persona estará entre el 80 % y el 91 %, más cerca de lo primero
  cuanto más distinta sea su forma de hablar. El dato de la tanda 6 al primer intento (58,5 %) es un recordatorio útil de lo que
  pasa con temas y giros que no se habían probado.
- Las **afirmaciones falsas** bajan poco (5,0 % → 4,0 %): 12 respuestas de 301 afirman algo erróneo. Es lo siguiente que hay
  que atacar, y no sé cuáles son porque no he leído ese examen.
- En el banco de validación las falsas suben de 31 a 40 de 12.331: es ruido pequeño pero no es mejora.
- Como el examen ciego 2 sigue sin leerse, **todavía sirve** para una comparación más. Cuando se lean sus fallos, pasa a tanda 7.

## 4. Cómo instalar y repetir

```bash
python parche_lcm21.py --plan
python parche_lcm21.py --aplicar
python -m scripts.afinar_escuela        # ~4 min; adopta la Escuela nueva solo si cumple la regla (necesita data/ud)
python -m pytest -q                     # los tests del núcleo usan árboles congelados: no dependen de tu Escuela
python -m lab.tanda06                   # tandas 01-06
python -m lab.medir lcm21 12 1,2,3,4,5  # banco dev + validación
python -m lab.examen_ciego2             # solo mira la línea de resumen si quieres conservarlo ciego
python -m scripts.afinar_escuela --restaurar   # vuelve a la Escuela anterior
```

Los pesos no son idénticos entre máquinas (CPU/MPS): tus cifras de la Escuela variarán unas décimas respecto a
`reports/escuela21_referencia.json`. Los tests del núcleo no cambian por eso; las tandas en vivo podrían variar en algún turno.

## 5. Lo que sigue fallando

- Afirmaciones falsas en torno al 4 % con frases nuevas.
- Categorías más flojas del ciego 2: multimodal encadenado (75 %), clases (83 %), conversación larga (84 %), persona (85 %).
- Subordinadas, condicionales, estilo indirecto y creencias siguen delegándose en las capas 1.6–1.9, con sus almacenes propios.
- Las respuestas siguen siendo plantillas.
- El generador de la Escuela cubre 44 marcos; lo que quede fuera se beneficia menos del afinado.
