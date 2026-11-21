# LCM 2.27 · Grafo de entidades y relaciones

Tu propuesta: cada persona es un nodo con su ficha; entre dos nodos puede haber varias relaciones; las relaciones siguen reglas lógicas
(si uno es padre, el otro es hijo); si hay dos personas con el mismo nombre y no se sabe cuál, se pregunta; y la técnica vale para más
cosas que las personas. La he investigado sobre lo que ya había, la he implementado y la he medido.

## 1. Resultado

| | 2.26 (sin grafo) | 2.27 |
|---|---|---|
| Medida limpia (8 conversaciones nuevas, 45 turnos, una sola vez) | 40,0 % · 8 falsas | **88,9 % · 3 falsas** (22 ganadas, 0 perdidas) |
| La misma tras tres arreglos posteriores (no ciego) | | 100 % |
| Conversaciones de desarrollo (7, 52 turnos) | 57,7 % · 7 falsas | 100 % |
| Conversaciones de las vueltas 2.25 y 2.26 | 91,5 % · 92,9 % | iguales |

Sí hay mejoría, y grande. Apagando el grafo (`LCM_SIN_GRAFO=1`) la medida limpia vuelve a 44,4 % con 9 falsas.

## 2. Qué había y qué faltaba

El núcleo ya guardaba entidades y relaciones con su tipo, y deducía bastantes parentescos. Pero:

- **Cada deducción estaba escrita a mano**, una por relación («abuelo», «tío», «primo»…). Donde nadie había escrito el caso, no había
  respuesta: «yerno», «sobrina de Jorge», «qué es Jorge de Clara», el tío por parte de la pareja.
- **El nodo era el nombre.** La entidad se identificaba por `N:pedro`, así que dos Pedros eran UNA persona: tu hermano acababa siendo
  también tu vecino y fontanero. Es el fallo de fondo que señalas.
- **Entre dos personas solo se contaba una relación**: «¿qué es Marta de mí?» → «tu hermana», aunque también fuera compañera de piso.
- **El género del usuario se suponía masculino**: con «mi marido Luis y mi hija Clara», a «¿quién es el padre de Clara?» contestaba «Eres el padre de Clara».
- Los verbos no creaban relación: «Sara sale con Tomás», «trabajo con Iván», «vivo con…».
- La cadena de lugares solo llegaba a dos saltos.

## 3. Qué he construido (`src/nucleo20/grafo.py`)

**Nodos y aristas.** Los nodos son las entidades del núcleo; las aristas, todo lo dicho con su tipo, más las que dicen los verbos
(«salir con» → pareja, «vivir con» / «compartir piso con» → conviven, «trabajar con» → compañeros). Entre dos nodos caben varias.

**Reglas como datos.** Una tabla, no un caso por pregunta:

- simétricas (hermano, pareja, amigo, vecino, compañero, primo, cuñado…);
- inversas (padre ↔ hijo, abuelo ↔ nieto, tío ↔ sobrino, suegro ↔ yerno, jefe ↔ empleado, profesor ↔ alumno…);
- 13 composiciones del tipo «el A del B de alguien es su C»: padre del padre = abuelo; hermano del padre = tío; pareja del tío = tío;
  hijo del tío = primo; padre de la pareja = suegro; hermano de la pareja y pareja del hermano = cuñado; hijo del mismo padre = hermano…
- **supuestas**: la pareja de quien es padre o madre se supone el otro progenitor, si no se ha dicho otro. Se contesta «Que yo sepa,
  Luis es el padre de Clara. Lo supongo porque Luis es tu marido y Clara es tu hija».

Las reglas se aplican hasta que no sale nada nuevo, y cada arista deducida guarda de qué frases sale, para explicarlo.

**Camino.** Si entre dos personas no hay una relación con nombre, se da el camino por lo dicho: «hay relación: Sara es la novia de
Tomás y Tomás es el hermano de Álex».

**Tocayos.** «Mi vecino también se llama Pedro» abre un nodo nuevo, sin fundirlo con el hermano. Sin «también», pregunta: «Ya conozco a
un Sergio: tu cuñado. ¿Tu dentista es el mismo Sergio o es otra persona?». Y cuando luego se dice «Pedro» a secas: «¿Qué Pedro: tu
hermano o tu vecino?»; la respuesta («mi hermano») retoma la frase que quedó pendiente. Si se dice cuál («el vecino Pedro»), no pregunta.

**Fuera de las personas.** La misma idea de relación transitiva, para lo que está dentro de algo: «las fotos están en una caja, la caja
en el armario, el armario en el dormitorio» → «¿están en el dormitorio?» sí, con la cadena; «¿en qué habitación están?» busca en la
cadena el primer sitio que sea una habitación según la base de conceptos.

**Convivencia.** «¿cuántos somos en casa?», «¿con quién vivo?».

El grafo no sustituye al núcleo: contesta cuando el núcleo no sabe, y lo enmienda en tres casos concretos (cuando contestó «Eres el
padre…» habiendo un candidato mejor, cuando nombró solo una de varias relaciones, y en «¿en qué habitación…?»).

## 4. Medida limpia

Ocho conversaciones nuevas (tres generaciones, tíos y primos, relaciones dobles, dos tocayas con «también», dos tocayos sin «también»,
cajas dentro de armarios, oficina y piso, parejas), escritas con el código congelado y sin ejecutarlas.

- 2.26: 18 de 45, con 8 respuestas falsas. 2.27: 40 de 45, con 3. Ganadas 22, perdidas 0.
- Lo que falló y arreglé después (ya no ciego, 45 de 45): «mi **dentista** se llama Sergio» no preguntaba porque «dentista» no es
  parentesco (ahora vale cualquier papel); «¿en qué habitación…?» lo contestaba antes el núcleo con «en una caja»; «**comparto piso**
  con Noelia y Fran» no contaba como convivir.

## 5. Límites

- **El nodo sigue colgando del nombre por dentro.** El segundo tocayo vive como «tu vecino», sin nombre propio en el núcleo; se le
  nombra con su papel. Funciona, pero no es todavía un identificador independiente del nombre, que es lo que pediría tu diseño completo:
  cambiarlo toca unas 25 funciones del núcleo y lo dejaría para una vuelta propia.
- Los tocayos se detectan cuando se presenta a alguien con «mi X se llama N». Dos Pedros introducidos de otra manera («ayer vi a
  Pedro, el de la tienda») no se separan.
- La ficha de cada nodo (teléfono, domicilio, anécdotas) ya la guarda el núcleo como hechos sueltos; no he añadido un vector por persona.
  Para recuperar por parecido («¿quién era el que vivía cerca del mar?») sí tendría sentido, y es un paso natural siguiente.
- La regla «la pareja es el otro progenitor» es una suposición y se dice como tal; se retira sola si se nombra a otro padre o madre.
- Las preguntas reconocidas son formas fijas («¿quién es el R de X?», «¿qué es X de Y?», «¿qué soy yo de X?», «¿cuántos somos en casa?»).
- Medida pequeña (45 turnos) y escrita por mí.

## 6. Dónde más se puede aplicar

Lo mismo (nodos, aristas con tipo, reglas de composición y de transitividad) sirve para: partes de un objeto («la rueda es parte de la
bici»), jerarquías de trabajo (jefe del jefe), pertenencia a grupos, antes/después en el tiempo, y las clases de la base de conceptos.
En esta vuelta están hechos el parentesco, el trabajo, la convivencia y los lugares.

## 7. Interruptores y verificación

`LCM_SIN_GRAFO=1` (todo), `LCM_SIN_TOCAYOS=1` (solo los tocayos: 86,7 % · 4 falsas en la medida limpia).

Tandas 01–15 e iter26…iter227: fallan solo las 4 conocidas. Tanda nueva `lab/iter227/t01.py`: 95 sondas, 100 %. Controles: idénticos a la 2.26 (autor 90,18 %, ciego 2 95,02, ciego 6 83,58, ciego 7 79,07, termómetro 97,07, 16b 97,18, 16c 100, 17b 99,26, 17c 94,50, conversa17 99,33). Pytest: 989 pasan; fallan los 3 de entorno de siempre.

Para repetir: `python -m lab.iter227.charla charlas_test`.
