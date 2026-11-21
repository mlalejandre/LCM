# LCM 2.32 · Análisis sintáctico entrenado e integración con los conceptos

Cambio de enfoque: la lectura deja de depender solo de reglas escritas a mano. Un analizador **entrenado** dice de cada palabra qué es
(determinante, preposición, verbo…), de cuál depende y con qué función (sujeto, objeto, complemento). De ahí salen las relaciones entre
conceptos, y el LCM las usa cuando por sí mismo no sabe contestar.

## 1. Resumen

| | Antes | Ahora |
|---|---|---|
| Analizador: verbo principal (examen del corpus, 2.148 frases) | 7,3 % (línea base) | 93,8 % |
| Analizador: sujeto | 0,4 % | 86,1 % |
| Analizador: frases escritas con descuido (sin tildes ni mayúsculas), cabeza y función | 83,4 % | 86,6 % |
| LCM, bancos de lectura propios (5 conjuntos, 714 preguntas) | 89,0 / 82,2 / 91,4 / 94,1 / 88,4 % | 91,0 / 84,2 / 94,6 / 94,1 / 88,9 % |
| LCM, siete textos nuevos de temas distintos (72 preguntas) | 67 | 69 |
| LCM, el texto del sistema solar tal como sale del PDF (26 preguntas) | 2 | 14 |
| LCM, la conversación de Manuel y siete parecidas (41 turnos) | 34,1 % | 95,1 % |

Regresiones: ninguna (tandas 01–15 e iter26…iter231: solo los 4 fallos conocidos de siempre). Controles: idénticos a la 2.31 línea por línea (autor 90,18 %). Pytest: 1090 pasan, 3 fallan (los 3 de entorno de siempre).

**No lo llamaría óptimo.** Es una mejora medida, sin regresión, y sobre todo cambia de qué depende el progreso: de entrenar, no de escribir reglas.

## 2. El analizador (`src/sintaxis/`)

- **Qué aprende:** categoría, cabeza y función de cada palabra. Solo gramática; ningún hecho del mundo.
- **De dónde:** 28.473 frases de español analizadas a mano (corpus públicos AnCora y GSD de Universal Dependencies).
- **Cómo:** red pequeña (vector de la palabra más los de su principio y final, dos capas recurrentes, salida de cabeza por pares). La primera pasada
  va de las frases cortas a las largas. El 30 % de las frases se le dan «con descuido»: sin tildes, sin mayúscula inicial, sin «¿» ni punto.
- **Coste:** 26 minutos en dos procesadores, sin tarjeta gráfica. El modelo ocupa 62 MB y no va en el repositorio: se entrena en tu máquina.

### Medidas por tipo de texto (segundo entrenamiento)

| Examen | Frases | Categoría | Cabeza | Cabeza y función | Verbo principal | Sujeto | Objeto |
|---|---|---|---|---|---|---|---|
| Prensa y web (corpus) | 2.148 | 97,5 | 90,1 | 85,6 | 93,8 | 86,1 | 80,0 |
| Escrito con descuido | 747 | 96,8 | 91,4 | 86,6 | 93,2 | 86,5 | 80,7 |
| PUD (otro origen: noticias y enciclopedia) | 1.000 | 94,3 | 90,5 | 83,4 | 93,7 | 88,2 | 79,5 |
| COSER (español hablado, transcrito) | 539 | 92,5 | 74,4 | 63,5 | 76,8 | 56,7 | 62,1 |

PUD y COSER no se parecen al entrenamiento y no se usaron para nada más que medir. En texto escrito generaliza bien; **en habla transcrita
(frases cortadas, muletillas) cae veinte puntos**. Determinantes y preposiciones: 99 % en todos.

Por longitud, el acierto por palabra apenas baja (de 91 % a 83 %), pero una frase de más de 40 palabras casi nunca sale perfecta entera.
Por eso todo lo que sigue trabaja oración a oración y con la seguridad que da el propio modelo.

## 3. De la sintaxis a los conceptos

**Relaciones** (`relaciones.py`). De cada oración: sujeto(s) — verbo — objeto o atributo — complementos con su preposición. Resuelve las
relativas («un amigo **que** se llama…»), reparte coordinaciones y aposiciones («los planetas, Mercurio, Venus…»), y hereda el sujeto
cuando la frase siguiente no lo dice.

**Grafo de conceptos.** Las relaciones forman un grafo: los nodos son conceptos y cada arista tiene una *dimensión* (el verbo con su papel
o preposición: «componer·de», «descubrir·objeto», «vivir·en», «ser»), un peso (la seguridad del análisis, que se suma si se repite) y el
contexto en que se dijo. `Memoria.vecinos(concepto, contexto)` da las relaciones de un concepto con su probabilidad según de qué se hable.

**Preguntas.** La pregunta pasa por el mismo analizador. Da un verbo y unas piezas; se busca una relación con ese verbo (o un sinónimo según
los vectores del LCM, con umbral 0,8) en la que encajen las piezas, y se contesta con la pieza que falta. Si varias relaciones compiten, la
respuesta lleva su probabilidad, y por debajo de 0,5 no se da.

## 4. Cómo entra en el LCM (`integra.py`)

**Manda el LCM; la memoria de relaciones rescata.** Solo interviene cuando el LCM no sabe o se limita a copiar una frase del texto.

Esto no fue la primera idea, sino lo que dijeron las medidas:

| Política | Bancos del LCM | Sistema solar |
|---|---|---|
| La memoria contesta primero | bajan los cinco (uno de 94,1 a 73,5 %) | 19 de 26 |
| Manda el LCM, la memoria rescata (**la que va**) | suben cuatro, uno igual | 14 de 26 |

El LCM ya entiende bien los textos sencillos (definiciones, deducciones, palabras inventadas); pisarlo era peor. Donde falla es en texto
real con ruido y frases largas, y ahí es donde entra el analizador.

Tres cosas que medí y descarté o ajusté:
- Rechazar las citas del LCM que no nombran lo preguntado: quitaba más citas buenas que malas. Queda apagado.
- Sinónimos de verbo con umbral 0,5: «vigilar» casaba con «poner». Subido a 0,8.
- Las regresiones destaparon cuatro respuestas inventadas (cantidades, comparaciones, repetir la pregunta, nombres propios). Corregidas.

## 5. Lo que no está resuelto

- **Sistema solar: 14 de 26.** Se abstiene en 8 y da 4 por malas; algunas las contesta el propio LCM con su base de conceptos («un sol es un astro»).
- **Sinónimos y definiciones indirectas:** «¿qué planetas contiene?» cuando el texto dice «componen»; «¿qué es Plutón?».
- **Pronombres:** «el macho **lo** cuida» no llega a «huevo».
- **Preguntas:** el corpus casi no tiene (210 de 28.473 frases). Se compensa contestando por la pieza que falta, pero conviene entrenar con preguntas.
- **Habla transcrita:** 63 %.
- **Las medidas de los siete textos y de los bancos no son ciegas del todo:** el examen de los siete textos se midió una vez a ciegas con la
  memoria sola (57 de 72, cero errores); los umbrales de la integración se eligieron después mirando tres de los cinco bancos.
- El LCM lee como mucho unos 8.000 caracteres de un texto por turno; la memoria de relaciones lee el texto entero.

## 6. Hacia dónde

1. **Entrenamiento continuo.** Cada frase que el analizador entiende con seguridad y el usuario no corrige puede volver al entrenamiento.
   El coste (26 minutos) lo permite. Falta decidir cuándo y con qué filtro.
2. **Conceptos:** fundir este grafo con el de personas (2.27) y con los vectores de tema (2.30–2.31) para sinónimos y pronombres.
3. **Generación:** componer la respuesta desde la relación (sujeto + verbo conjugado + pieza), en vez de dar la pieza suelta.

## 7. Instalación y uso

```
python parche_lcm232.py --aplicar
python -m src.sintaxis.prepara        # baja los corpus (unos 90 MB) a data/ud/
python -m src.sintaxis.entrena        # unos 30 minutos; deja src/sintaxis/analizador.pt
```

Sin el analizador entrenado el LCM funciona exactamente como antes. Se apaga con `LCM_SIN_SINTAXIS=1`.

- Analizar una frase: `python -m src.sintaxis.analiza "Mi tío Manuel vive en Navarra y le gusta cazar jabalíes."`
- Medir el analizador: `python -m lab.sintaxis.compara src/sintaxis/analizador.pt`
- Medir la comprensión: `python -m lab.sintaxis.integrado_mide` (textos generales) y `python -m lab.sintaxis.solar_mide <texto>`
- Partir frases de conversación con el analizador en vez de con reglas (opcional, 92,7 % frente a 95,1 %): `LCM_SINTAXIS=1`

## 8. También va en este parche (vuelta 2.32 anterior, que quedó aparcada)

Papeles en la frase (quién hace y a quién), clases enseñadas en la conversación, texto dirigido a clases, y los arreglos de la conversación
de Manuel. Su examen limpio propio pasó de 75,5 % a 77,4 % a ciegas (81,1 % después, no a ciegas). Va incluido porque el código está
entrelazado y las regresiones completas se han pasado con todo junto.
