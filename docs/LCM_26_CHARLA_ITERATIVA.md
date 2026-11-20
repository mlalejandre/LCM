# LCM 2.6 · Charla iterativa (parche sobre LCM 2.5)

## Qué se hizo

1. **Referencia antes de tocar nada.** Se escribió `lab/charla50.py`: una conversación libre de 50 interacciones (40 puntuables), con criterios fijados de antemano y la 2.5 congelada. No se usó para corregir.
2. **23 tandas de 10 interacciones** (`lab/iter26/t01.py` … `t23.py`, 230 interacciones). Después de cada tanda se analizaron los fallos y se corrigieron antes de la siguiente. Las correcciones se fueron acumulando.
   - El resultado del primer intento de cada tanda queda en `lab/iter26/primer_intento.json`.
   - Cuando un criterio laxo aprobó una respuesta falsa, el registro se corrigió a mano. Cada caso lleva una nota.
3. **Medida final.** Con el código congelado se repitió la charla de 50, junto con los exámenes de control.

## Resultados (mismo juez para 2.5 y 2.6)

### Charla de 50 interacciones

| Medida | 2.5 | 2.6 | Afirmaciones falsas (2.5 / 2.6) |
|---|---|---|---|
| Preregistrada (5 bloques con memoria separada) | 77,5 % | 77,5 % | 0 / 0 |
| Corregida (una sola conversación) | **80,0 %** | **85,0 %** | 0 / 0 |

**Advertencia sobre la segunda fila.** El arnés reiniciaba la memoria entre los 5 bloques. La charla, en cambio, era una sola conversación: el bloque b pregunta por cosas dichas en el a.

- Este error se vio al leer las transcripciones *después* de la medida preregistrada.
- Se repitió la medida con las dos versiones sin cambiar el código (`banco.correr(..., continua=True)`).
- Desde ese momento la charla de 50 ya está leída y deja de ser una prueba ciega.

**Lo que mejora 2.6 en la charla:** ahora entiende «Tenemos dos niños, Leo y Alba» y responde «¿Cuántos hijos tengo?».

**Lo que sigue fallando:**
- Cláusula de relativo: «Estoy casada con Iñaki, que es profesor de música». No se guarda, así que fallan las preguntas por el marido, por lo que enseña y por el padre de Alba.
- Elipsis con nombres propios: «Leo tiene siete años y Alba cuatro».
- Deducir «hija» a partir del nombre «Alba».
- Una imagen presentada como «este es el color de la cafetera que quiero»: se toma como una pregunta.

### Curva de aprendizaje (primer intento de cada tanda)

| Tandas | Puntuables | Acierto en el primer intento | Falsas |
|---|---|---|---|
| T01–08 | 72 | 59,7 % | 8 |
| T09–16 | 72 | 61,1 % | 5 |
| T17–23 | 63 | 65,1 % | 7 |

La mejora es lenta: cada tanda trae fenómenos nuevos. Es la medida más sincera de cómo se comporta el modelo ante frases que no ha visto.

### Control: no se ha roto nada

| Prueba | n | 2.5 | 2.6 |
|---|---|---|---|
| Examen ciego 2 | 301 | 93,02 % (7 falsas) | 93,36 % (6 falsas) |
| Examen ciego 6 | 67 | 76,12 % | 77,61 % |
| Examen ciego 7 | 43 | 69,77 % | 69,77 % |
| Exámenes del autor | 703 | 88,05 % | 88,05 % |
| Banco generado (validación) | 12 331 | 98,49 % | 98,49 % |

- Tandas 1–15 (1570) y tandas iter26 01–23: todas al 100 %, salvo T11 (90 %, una inferencia «¿cuándo es la fiesta?» que no se resuelve).
- Durante la medida aparecieron dos regresiones en los exámenes del autor. Se corrigieron antes de congelar el código:
  - «¿Nada un salmón?» tras «Algunos peces nadan»: la fábrica no debe pisar lo que dijo el usuario sobre la clase superior.
  - «Hola/Buenas»: lo vuelve a llevar el diálogo de base, que sabe si se habla de usted.

### Juez más estricto en 2.6

- Una nota literal («No lo he entendido del todo, pero me lo apunto…») cuenta como abstención indebida.
- En una abstención solo cuenta lo anterior a «Solo sé que», «De X sé que» o **«pero me dijiste»**. Citar literalmente lo que dijo el usuario no es entenderlo.
- Por eso los ciegos 6 y 7 de la 2.5 bajan respecto a lo publicado en la 2.5: 83,6 → 76,1 y 76,7 → 69,8. Las dos versiones están medidas aquí con este juez.

## Qué entiende ahora (resumen de cambios)

### Habla coloquial (`coloquial.py`)

- «yo un poco agobiado con el trabajo» → «Estoy un poco agobiado con el trabajo».
- «llevo toda la semana durmiendo fatal» y «llevo dos meses estudiando inglés»: se guarda con «desde hace».
- Impersonal con dativo: «me han ofrecido un puesto en Bilbao» → «He recibido una oferta de un puesto en Bilbao». Lo mismo en las preguntas.
- Se quitan muletillas como «te quería contar que», «¿sabes qué?», «al final» o «sobre todo».
- «¿por qué…?» en minúscula se analiza igual que «¿Por qué…?».

### Referencias

- «Lo llevo al taller» y «mañana lo llevo»: el clítico va a lo último que se nombró. Con verbos de manipular (llevar, arreglar, lavar…) se prefiere el objeto físico: el coche, no el problema.
- «Les ha encantado»: se resuelve como «a tus suegros les encantó la paella».
- «Hace un ruido raro cuando freno»: el sujeto es el coche y se guarda «cuando frenas».
- «Va de unos detectives»: es el tema de la serie.
- Elipsis del verbo: «mi suegra se llama Pilar y mi suegro Antonio».
- Un plural impersonal («pagan mejor») ya no se atribuye a un lugar en singular.

### Preguntas nuevas

- «¿Qué le pasa a mi coche?»
- «¿De qué año / qué marca es mi coche?», a partir de «es un Seat de 2015».
- «¿Qué (no) quiere hacer mi novia?»
- «¿Hasta qué hora bailé?» y «¿A qué hora es la entrevista?», que dan la hora y no solo el día.
- «¿Cuándo tengo que entregarlo?»: se quita el clítico del infinitivo.
- «¿Por qué estoy agobiado?»: se responde con el complemento «con el trabajo».

### Fábrica

- Ingredientes típicos de platos como concepto («la paella lleva arroz»). No son hechos del mundo.
- «moto», «foto» y «mano» ya no se feminizan a «mota».

## Cómo repetir las medidas

```
python -m lab.charla50                 # charla de 50 (una sola conversación)
python -m lab.iter26.correr N          # tanda N de la ronda (no sobrescribe el primer intento)
python -m lab.examen_ciego2|6|7
python -m lab.examenes_usuario
python -m lab.medir lcm26 12 1,2,3,4,5
```

Las cifras están en `reports/lcm26_medidas.json`. Los fallos de la charla de cada versión están en `lab/iter26/charla50_fallos_25.txt` y `charla50_fallos_26.txt`.
