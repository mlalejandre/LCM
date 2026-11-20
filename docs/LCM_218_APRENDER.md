# LCM 2.18 · Aprender de un texto: plan de acción y primera iteración

Parte del diagnóstico `LCM_APRENDER18_DIAGNOSTICO.md`. Condición del encargo: las mejoras tienen que ser del modelo general,
no de un tema. Por eso:
- ninguna regla del código nombra un tema: todas trabajan por la FORMA de la frase;
- se desarrolla contra tres temas distintos (abejas, volcanes, ajedrez) y **ninguno es el del diagnóstico** (setas);
- se mide con temas que no existían mientras se programaba (murciélagos, café, un animal inventado; después faros y la Luna).

## 1. Plan de acción

Cada iteración ataca lo que más puntos pierde en la medida limpia anterior.

| Iteración | Qué ataca | Estado |
|---|---|---|
| 1 | Seguridad de la lectura, gramática del texto que explica, cita disciplinada | Hecha en este parche |
| 2 | Convertir lo leído en conocimiento que se usa (tipos, varias clases, peticiones, contraste) | Hecha en este parche |
| 3 | Recuperar por significado: sinónimos y paráfrasis, combinar dos frases | Siguiente |
| 4 | Nombres propios compuestos («La Torre de Hércules») y adjetivos que restringen dentro del núcleo | Siguiente |
| 5 | Sentido común (comestible, venenoso, peligroso) y que el diccionario no gane a lo aprendido | Después |
| 6 | Forma de las respuestas (concordancias, frases embarulladas) | Después |

## 2. Qué cambia en este parche

**Leer un texto que explica** (`exposicion.py`, `lectura.py`):
- Lleva el hilo por el sujeto escrito, no por lo último que entendió. Una frase sin sujeto ya no hereda un tema dudoso.
- Desdobla cada frase en afirmaciones sencillas y guarda en su forma propia lo que no es un hecho simple:
  - definiciones: «el panal, una estructura de celdas de cera», «…se llaman apicultores», «llamada magma»;
  - tipos: «hay tres tipos de abejas: …»;
  - superlativos y únicos: «el volcán más alto de España», «la única que pone huevos»;
  - afirmaciones parciales: «algunos están activos y otros dormidos»;
  - reglas y causas: «cuando A, B», «A, por eso B», «B porque A».
- Lo dicho de un subgrupo («los volcanes extinguidos…») ya no se generaliza a toda la clase.

**Citar con disciplina.** La frase citada tiene que hablar de todo lo que se pregunta y traer el tipo de dato pedido
(un número para «cuántos», un lugar para «dónde»…). Si no, el LCM dice que no lo sabe.

**Usar lo aprendido:**
- «dime un volcán», «dime los tipos de abejas», «descríbeme el Teide» se contestan con lo leído;
- una petición («dime…») ya no se apunta como si fuera un hecho;
- «el volcán más alto de España» se entiende como el Teide dentro de otra pregunta;
- «¿qué pieza se mueve en diagonal?» se contesta aunque el dato se guardara al revés;
- lo que vale para una clase vale para quien es de esa clase («mi tío es apicultor» → cuida colmenas);
- una cosa aprendida puede ser de varias clases: ya no contesta «no, es un hongo» a «¿es un alimento?».

**Contrastar.** Si lo que se le dice choca con lo leído, lo dice y conserva lo leído hasta que se le pida corregirlo.

**La charla que explica** se lee igual que un texto, frase a frase. Si no entiende una explicación general, lo dice y la guarda
tal cual para poder citarla, en vez de contestar «Entendido» a algo que no entendió.

## 3. Métricas

Todas las cifras son del corrector automático salvo donde dice «auditado». «Falsas» = respuestas que afirman algo incorrecto.

**Medida final limpia** (faros y la Luna, 58 preguntas; escrita con el código definitivo congelado, medida una vez):

| | 2.17 | 2.18 |
|---|---|---|
| Sin texto | — | 17,2 % |
| Texto pegado | 58,6 % · 17 falsas | **74,1 % · 6 falsas** |
| Frase a frase en la charla | 43,1 % · 8 falsas | **58,6 % · 6 falsas** |

Auditada a mano, las cifras con texto no cambian: no hay aprobados laxos relevantes en ninguna de las dos versiones.

**Primera medida limpia** (murciélagos, café y un animal inventado, 95 preguntas; primer intento a ciegas):

| | 2.17 | 2.18 a ciegas | 2.18 tras arreglos (no ciega) |
|---|---|---|---|
| Texto pegado | 63,2 % · 23 falsas | 76,8 % · 10 falsas | 81,1 % · 7 falsas |
| Texto pegado, auditado a mano | ≈ 61 % | ≈ 67 % | — |
| Frase a frase | 30,5 % · 16 falsas | 63,2 % · 15 falsas | 72,6 % · 8 falsas |

La auditoría rebaja el primer intento porque 10 aprobados tenían defecto: 7 citas correctas con una etiqueta de tema
equivocada («hablando de las alas…») y 3 respuestas embarulladas. Lo arreglé y por eso hice una segunda medida limpia.

**Desarrollo** (abejas, volcanes, ajedrez, 101 preguntas; no es medida limpia):

| | 2.17 | Iteración 1 | Iteración 2 | Final |
|---|---|---|---|---|
| Texto pegado | 58,4 % · 30 falsas | 84,2 % · 6 | 92,1 % · 1 | 94,1 % · 0 |
| Frases del texto cubiertas | 42 de 56 | 53 de 56 | 53 de 56 | 53 de 56 |
| Frase a frase | 34,7 % · 22 falsas | — | 73,3 % · 11 | 84,2 % · 8 |

**Tema del diagnóstico** (setas, 59 preguntas; conocido, pero no se desarrolló contra él): 47,5 % · 17 falsas → 67,8 % · 5 falsas.

Cómo leerlas:
- **El desarrollo sobrestima unos 20 puntos.** En temas nuevos la mejora real con texto es de unos 15 puntos.
- **Lo que más mejora es la fiabilidad:** las respuestas falsas bajan a un tercio (17 → 6 y 23 → 7).
- En la medida final, por tipo de pregunta (2.17 → 2.18, con texto):
  - mejoran: usar lo aprendido 0 → 75 %, abstenerse de lo no dicho 0 → 83 %, contradicción 0 → 50 %;
  - no cambian: literal 81 %, deducción 67 %, inversa 86 %, vocabulario 60 %, charla 50 %, combinar dos frases 0 %.
- Es decir: en temas nuevos la gramática expositiva de la iteración 1 rinde menos de lo que parecía en desarrollo. Queda mucha
  forma de frase sin cubrir.
- Reserva de siempre: los textos y las preguntas los escribo yo.

## 4. Lo que sigue verde (vistos en las medidas limpias)

- **Nombres propios compuestos.** «La Torre de Hércules» no es una entidad para el núcleo: la frase siguiente («Está en La
  Coruña…») se atribuyó al farero. Es una falsedad aprendida, la más grave que queda.
- **Paráfrasis y sinónimos:** «¿de qué se alimenta…?» no encuentra «comen insectos».
- **Combinar dos frases:** 0 % en la medida final.
- **Definiciones sin artículo:** «los cráteres son agujeros que…» no se guarda como definición.
- **El diccionario gana a veces a lo leído:** «las mareas» → «un fenómeno»; «el vampiro» → «un ser imaginario».
- **Adjetivo que restringe, dentro del núcleo:** «un café solo no lleva leche» se guarda como «el café no lleva leche».
- **Lugar entre dos complementos con «en»:** «¿dónde viven?» contesta «en grupos» en vez de «en las montañas».
- **Herencia de clase a individuo** solo con la misma forma verbal («cuidaba un faro» no funciona).
- **Sentido común** (comestible, venenoso, peligroso): sin tocar.
- **La vía frase a frase** sigue 15 puntos por debajo del texto pegado.
- **Forma:** «astronauto», «contene», órdenes de palabras embarullados.
