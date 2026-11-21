# LCM 2.29 · Probabilidad por contexto, con una caché corta

Tu indicación: cuando un nombre lleva a varios nodos, lo más probable es aquel del que se venía hablando; si la probabilidad no está
clara, se pregunta; y para eso hace falta traer lo último de la conversación en una caché pequeña.

## 1. Resultado

| | 2.28 | 2.29 |
|---|---|---|
| Medida limpia (7 conversaciones nuevas, 17 turnos, una sola vez) | 52,9 % · 8 falsas | **82,4 % · 3 falsas** |
| La misma tras los arreglos posteriores (no ciego) | | 100 % |
| Conversaciones de desarrollo (15 turnos) | 60,0 % · 5 falsas | 100 % |
| Sin la caché (`LCM_SIN_CONTEXTO=1`), sobre la medida limpia | | 47,1 % · 8 falsas |

Regresiones: solo las 4 de siempre. Controles: idénticos a la 2.28. El examen grande (88,4 %) y los bancos de lectura y diccionario, iguales.

## 2. La caché (`src/nucleo20/contexto.py`)

Guarda, de los últimos 6 turnos y con un tope de 40 apuntes, dos cosas: las **entidades** de las que se ha hablado y las **palabras de
contenido** que se han dicho. Cada turno que pasa, un apunte vale la mitad. Una definición («un cabo es una cuerda…») no se apunta: no es
«de lo que se está hablando».

Con eso se da a cada candidato unos puntos y los puntos se reparten en probabilidades. Si la del mejor llega a 0,70 se elige sin
preguntar (0,80 si lo que se dice va a quedar guardado, porque equivocarse ahí ensucia la memoria); si no, se pregunta.

## 3. Personas

Los puntos de cada tocayo salen de dos sitios:

- **de quién se venía hablando** (la última vez que apareció en la caché);
- **con la ficha de quién casa la frase**: «¿qué enseña Ramón?» casa con el profesor, del que se sabe que «enseña matemáticas», aunque
  haga rato que no se le nombra.

```
Mi dentista trabaja en una clínica.   Esta mañana he ido a ver a mi dentista.
¿dónde trabaja Laura?      → Tu dentista Laura trabaja en una clínica.        (dentista 0,8)
Luego he comido con mi hermana.
¿dónde vive Laura?         → Tu hermana Laura vive en Oviedo.                 (hermana 0,8)
```

Sin pistas sigue preguntando: «¿Qué Eva: tu cuñada o tu médica?». Y la respuesta siempre dice a cuál se refiere («tu dentista Laura»),
así que si elige mal se ve.

## 4. Palabras

Aquí el hallazgo es menos cómodo. Los vectores de fábrica son de **sinonimia**, no de tema: «torneo» y «premio» se parecen 0,14. No
sirven para saber de qué se está hablando. Lo que sí hay, y es lo que uso:

- **la base de conceptos**, que ya traía varios padres para las palabras polisémicas (ratón: mamífero y aparato; banco: mueble y
  edificio) y qué es parte de qué (el ratón es parte del ordenador). «He comprado un ratón **para el ordenador**» → aparato, sin preguntar;
- **lo que enseña el usuario** con cada sentido («una pluma es un instrumento para escribir con tinta»): luego «he comprado una pluma y
  un bote de tinta para escribir» casa con ese sentido;
- **lo que se aprende de sus respuestas**. Cuando la respuesta depende del sentido y el contexto no lo aclara, pregunta, y las palabras
  que había alrededor quedan asociadas al sentido elegido:

```
He ganado una copa en el torneo de tenis.
¿mi copa es un premio?     → «copa» tiene varios sentidos y no tengo claro de cuál hablamos: ¿recipiente o premio?
premio                     → Sí: por lo que me has contado, hablamos de «copa» en el sentido de premio.
Mi hermano ha ganado otra copa en el torneo.
¿la copa es un premio?     → Sí…   (ya no pregunta: «ganar» y «torneo» quedaron asociados a ese sentido)
```

Es decir: el modelo no trae de fábrica con qué temas va cada sentido, pero lo aprende de quien habla con él. Encaja con la idea del
proyecto (conceptos sí, hechos del mundo no), aunque significa que al principio pregunta más.

Sin nada en contra, se queda con el sentido de siempre y **no pregunta** («tengo una planta» → ser vivo). Solo pregunta cuando lo que se
pregunta encaja con un sentido distinto del más probable.

## 5. Medida limpia

Siete conversaciones nuevas, escritas con el código congelado y sin ejecutarlas. 9 de 17 → 14 de 17, y las respuestas falsas de 8 a 3.
Lo que falló y arreglé después:

- «Luego he comido con **mi hermana**» no contaba como hablar de ella (solo se apuntaba cuando se la nombraba). Ahora cuenta el papel.
- Un turno de desfase al contar el tiempo: el último turno y el anterior pesaban lo mismo.
- Las frases que enseñaban los sentidos de «pluma» entraban en la caché como contexto y confundían la elección.

Con eso, 17 de 17 (ya no es ciego).

## 6. Dos expectativas antiguas que cambian

En las medidas de la 2.27 y la 2.28 había tres turnos que esperaban una pregunta («¿Qué Sergio?», «¿Qué Ana?») justo después de hablar
de uno de ellos. Con tu criterio nuevo ya no se pregunta: se contesta del que se venía hablando. No es una regresión, es el cambio que
pedías; he puesto al día esos turnos y lo dejo anotado en los propios archivos.

## 7. Límites

- **Para las palabras, el contexto de fábrica es pobre.** Solo decide solo cuando hay una relación de parte y todo en la base de
  conceptos, o cuando el usuario ya enseñó o aclaró el sentido. En el resto, pregunta.
- El sentido se apunta por palabra y conversación, no por cada objeto: dos «copas» distintas en la misma charla comparten sentido.
- Solo entra en preguntas del tipo «¿mi X es un Y?». No cambia todavía cómo se guarda la frase.
- Los umbrales (0,70 y 0,80), el olvido (la mitad por turno) y la ventana (6 turnos) están puestos a ojo con las conversaciones de
  desarrollo. Son tres números en lo alto de `contexto.py`.
- La medida es muy pequeña (17 turnos) y escrita por mí.

## 8. Interruptores y verificación

`LCM_SIN_CONTEXTO=1` apaga la caché y las probabilidades.

Tandas 01–15 e iter26…iter229: fallan solo las 4 conocidas. Por el camino aparecieron tres regresiones y las arreglé antes de cerrar: a «¿la pasta es un alimento?» y a «¿mi primo es una persona?» preguntaba de qué sentido se hablaba. Ahora no duda cuando la pregunta encaja con el sentido de siempre, ni con palabras de parentesco, ni cuando no hay sentido de fábrica ni enseñado en que apoyarse. Tanda nueva `lab/iter229/t01.py`: 29 sondas, 100 %. Pytest: 1009 pasan; fallan los 3 de entorno de siempre.

Para repetir: `python -m lab.iter229.charla charlas_test`.
