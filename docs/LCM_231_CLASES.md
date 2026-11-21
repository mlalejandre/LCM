# LCM 2.31 · Más texto, y el sentido por la CLASE a la que pertenece

Siguiente paso de la 2.30, hecho sin que intervinieras: inyectar más texto y medir cuánto ayuda. La respuesta corta es que **el texto solo ayuda
poco, y lo que de verdad sube es usar ese texto junto con las clases de la base de conceptos**.

## 1. Resultado

Dos medidas limpias. Las palabras no las elegí yo: son las de la base de fábrica con dos sentidos que se excluyen (lista sacada por programa:
alianza, bote, caqui, cometa, cubo, estrella, flamenco, granada, lima, naranja, palmera, regla, rosa, salmón, salsa, zapatero, flecha; y en la segunda
violeta, lila, mostaza, pollo, conejo, cine, teatro, policía, chocolate, radio), más conversaciones con dos personas del mismo nombre.

| | 2.30 | 2.31 solo con más texto | 2.31 con todo |
|---|---|---|---|
| Primera medida (77 turnos) | 48,1 % | 54,5 % (ciega) | 84,4 % (**no ciega**: la usé para desarrollar) |
| Segunda medida (46 turnos) | 58,7 % | 63,0 % | **80,4 % ciega**, 76,1 % final |

Desglose de la segunda medida, hecho a mano: 2.30 acierta 27, pregunta 8, se equivoca 11. 2.31 (ciega) acierta 37, pregunta 2, se equivoca 7.

La segunda medida baja de 80,4 a 76,1 por un ajuste posterior que hice para quitar una regresión (el «banco de la plaza», abajo): con él se
equivoca en 9 en vez de 7. Lo dejo dicho porque es el número del código que entrego.

Regresiones: ninguna (solo los 4 fallos conocidos de siempre). Controles: idénticos a la 2.30 línea por línea (autor 634/703 = 90,18 %). Bancos de lectura y diccionario, examen grande (88,4 % y 87,2 %) y conversaciones de las vueltas
2.25–2.29, iguales. Las de la 2.30 suben: su examen de 66,7 % a 88,9 % y su desarrollo de 66,7 % a 94,4 %.

## 2. Qué enseña la medida sobre «inyectar texto»

Escribí unas 560 frases más (ahora son unas 830, en 63 escenas) **antes** de saber qué palabras iba a probar. Resultado ciego: de 48,1 a 54,5.
Solo mejoraron las palabras cuyos dos sentidos aparecían en el texto (lima, naranja). Las demás, nada.

Es lógico: contando compañías, «bailar» solo apoya el sentido «baile» de «salsa» si alguna frase junta «salsa» y «bailar». Haría falta un texto
enorme para cubrir cada palabra. Por ahí no se llega con un texto pequeño.

## 3. La idea que sí funcionó: la clase y sus miembros

La base de conceptos ya dice que un tango, una jota y una salsa son **bailes**; que el rojo y el azul son **colores**; que la luna es un **astro**.
Ahora una palabra del contexto apoya un sentido si va con **otros miembros de esa clase**, aunque nunca se haya visto con la palabra dudosa:

```
He pintado la habitación de rosa, un tono suave entre el rojo y el blanco.
   «rojo» y «blanco» son colores; «pintar» va con los colores      → rosa = color
El soldado lanzó una granada y explotó en la guerra.
   «soldado» va con las armas                                       → granada = arma
En la pastelería he comprado una palmera de chocolate.
   «pastelería» va con tartas y pasteles, que son dulces            → palmera = dulce
```

Es lo que pedías: conceptos y vectores trabajando juntos. El texto ya no tiene que nombrar cada palabra; basta con que conozca la clase.
Reglas que lo acompañan:

- En una clase grande hace falta que la palabra vaya con **dos miembros** al menos. Con uno solo es casualidad («tomar» va con «bar», y eso no
  hace de «tomar el sol» cosa de edificios).
- «Bailar» y «baile», «pescar» y «pesca» cuentan como la misma palabra.

## 4. Otros cuatro arreglos generales que salieron al auditar

1. **Decide la suma, no el primero.** Para «¿la carta es un juego?» ya no compiten «documento» y «medio de comunicación» (son la misma carta):
   se suma la probabilidad de los sentidos en que la respuesta es sí y la de los que es no.
2. **El léxico propone, el texto confirma.** Un sentido que solo trae el léxico entra al reparto si el texto lo respalda. Antes «salmón» tenía el
   sentido «río» y «rosa» el sentido «ventana», y robaban votos.
3. **La ficha de una persona incluye la frase en que se presentó.** «Mi primo se llama Raúl **y es mecánico**»: la segunda mitad se perdía
   desde la 2.30, y por eso «mi coche no arranca» no llevaba a Raúl el mecánico.
4. **«Vecino» o «hermano» no son tema.** Con el texto nuevo, «¿dónde vive Pedro?» apuntaba al vecino porque «los vecinos viven al lado».
   El parentesco ya no cuenta como tema; un oficio («profesor») sí. Y la persona que el modelo elige por probabilidad pesa la mitad que la que
   nombra el usuario.

## 5. Lo que sigue mal

- **No sabe quién hace qué.** «Vimos un conejo que salía de su madriguera y comía hierba» → dice que es carne, porque «comer» va con «carne».
  Contar compañías no distingue al que come del que es comido. Es el fallo más serio y es **nuevo de esta versión** (la 2.30 acertaba una de las dos preguntas).
- **Sentidos sin apoyo en el texto:** alianza como acuerdo, regla como norma, cometa como astro, chocolate como bebida. Pregunta o da el sentido de siempre.
- **Tras el ajuste del banco:** «las noticias llegan por la radio, la prensa y la televisión» → dice aparato.
- **Personas:** de 9 conversaciones acierta 3, pregunta en 5 y falla 1 («Julio» lo toma por el mes). Ya no contesta la persona equivocada.
- Los grupos de compañías grandes atraen demasiados votos. Es de la 2.30 y no lo he tocado.

## 6. Una regresión que encontré y quité

Con el código congelado, la tanda de la 2.30 fallaba una sonda: «Los abuelos toman el sol en un banco de la plaza» pasaba a ser el edificio.
Causa: apoyos de un solo miembro («sol»–«verano», que la base cuelga de «estación» y esta de «edificio»). De ahí la regla de los dos miembros.
Cuesta dos aciertos en la segunda medida y tres en la primera.

## 7. Expectativas que cambian

- Examen y tanda de la 2.29, «¿la carta es un juego?» tras «buzón de correos»: ya no pregunta, dice que no. Era correcto antes y ahora; solo
  cambié el orden del criterio (el arnés solo entiende `^no` en primera posición).
- Desarrollo de la 2.28, «¿dónde vive Pedro?» justo después de preguntar por «mi hermano»: valen las dos respuestas (contestar del hermano o
  preguntar cuál). La 2.30 contestaba por un efecto que he visto que era casual.

## 8. Qué haría ahora

1. **Papeles en la frase**: que el sujeto de «comer», «salir» o «volar» apoye el sentido de ser vivo. Arregla el conejo y es general.
2. **Aprender clases de la conversación**: si el usuario dice «la bachata es un baile», que «bachata» entre en la clase y sirva de apoyo desde ese momento.
3. Más texto, pero dirigido a las **clases** con pocos miembros conocidos (astros, acuerdos, normas), que es donde rinde.

## 9. Interruptores y verificación

`LCM_SIN_CLASE=1` deja solo el texto nuevo (54,5 % y 63,0 %). `LCM_SIN_TEMA=1` apaga también la 2.30 (28,6 % y 41,3 %: vuelve a preguntar casi siempre).

Tandas 01–15 e iter26…iter231: sin cambios (fallan las 4 sondas de siempre: iter26 t11, iter28 t23, iter210 t01, iter214 t05). Tanda nueva `lab/iter231/t01.py`: 100 sondas, 100 %. Pytest: 1085 pasan, 3 fallan (los 3 de entorno de siempre).

Para repetir: `python -m lab.iter231.charla charlas_test` y `python -m lab.iter231.charla charlas_test2`.
