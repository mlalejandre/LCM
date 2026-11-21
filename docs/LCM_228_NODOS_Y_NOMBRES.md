# LCM 2.28 · El nodo no es el nombre: tocayos con nodo propio y palabras con varios sentidos

Tu observación: el problema de los tocayos es el mismo que el de las palabras polisémicas. Un nombre («Pedro», «banco») puede llevar a
varios nodos, y el modelo tenía uno solo por nombre. Lo he abordado en los dos sitios, con tu condición: si rompe algo de lo conseguido,
no se aplica.

## 1. Veredicto

**No hay regresión; se puede aplicar.** Las tandas de regresión fallan solo en las 4 de siempre; el examen grande sigue en 88,4 %; los bancos de lectura y diccionario y las conversaciones de las vueltas anteriores, iguales. Controles: idénticos a la 2.27 (autor 90,18 %, ciego 2 95,02, ciego 6 83,58, ciego 7 79,07, termómetro 97,07, 16b 97,18, 16c 100, 17b 99,26, 17c 94,50, conversa17 99,33).

| | 2.27 | 2.28 |
|---|---|---|
| Medida limpia (5 conversaciones nuevas, 28 turnos, una sola vez) | 78,6 % · 2 falsas | **92,9 % · 0 falsas** (4 ganadas, 0 perdidas) |
| Conversaciones de desarrollo (24 turnos) | 83,3 % · 4 falsas | 100 % |
| Medida limpia de la 2.27 (grafo de relaciones) | 100 % | 100 % |

## 2. Qué pasaba con las palabras

Lo mismo que con los Pedros. El núcleo tenía un nodo por palabra:

- «¿un banco es una institución?» → «No, un banco es un mueble».
- «¿una vela es una tela?» → «No, una vela es un objeto».
- «Mi primo es cabo» + «un cabo es una cuerda» → «Sí, tu primo es una cuerda».
- «Mi hermana es una estrella» + «una estrella es un astro» → «Sí, tu hermana es un astro».

## 3. Qué cambia

**Personas: un nodo propio por tocayo.** En la 2.27 el segundo Pedro vivía como «tu vecino», sin nombre. Ahora cada uno tiene su nodo
(`N:pedro#1`, `N:pedro#2`, `N:pedro#3`…) con su nombre, y «Pedro» a secas queda solo como nombre: lleva al nodo que toque en cada frase.

- Se nombran distinguiéndolos: «Tu vecino Pedro es fontanero», «Tu hermano Pedro vive en Cádiz».
- Caben tres o más («¿cuántas Anas conozco?» → tres).
- Sigue preguntando cuando no se sabe cuál («¿Qué Pedro: tu hermano o tu vecino?») y cuando no se sabe si es otro («¿Tu médica es la
  misma Ana o es otra persona?»). Si se contesta que es el mismo, las dos relaciones quedan en un solo nodo.
- El cambio en el corazón del núcleo son seis líneas: la función que resuelve identidades admite que un nombre apunte, durante una
  frase, a otro nodo; y la que nombra a una entidad añade su papel cuando tiene tocayos. Nada más del núcleo se ha tocado, y por eso no
  hay regresión.

**Palabras: varios sentidos (`src/nucleo20/acepciones.py`, nuevo).** Cada palabra tiene los sentidos que trae el léxico de fábrica (con
sus clases) y los que enseñe el usuario.

- Una pregunta sobre la palabra en general vale si la cumple **alguno** de sus sentidos, y se dice: «Sí, en uno de sus sentidos:
  «banco» tiene varios, y en uno un banco es una institución. En otro, un banco es un mueble».
- De alguien concreto se elige el sentido que casa con lo que ya se sabe: una persona que «es cabo» es el militar, no la cuerda. «No.
  «cabo» tiene varios sentidos y tu primo es una persona».

Solo enmienda al núcleo en esos dos casos (cuando dijo «No» mirando un único sentido, y cuando dedujo algo de una persona por un
sentido que no es de persona). Lo demás sigue igual.

## 4. Medida limpia

Cinco conversaciones nuevas, escritas con el código congelado y sin ejecutarlas: tres Anas, mismo nombre y misma persona, tocayos
nombrados con su papel, palabras con varios sentidos, y oficios.

- 22 de 28 → 26 de 28. Las dos respuestas falsas de la 2.27 («una vela no es una tela», «tu hermana es un astro») desaparecen.
- Las cuatro ganadas son todas de **acepciones**. En los tocayos, la 2.27 ya acertaba estas preguntas con su solución provisional: el
  nodo propio no sube el porcentaje aquí; lo que da es que se les nombre bien, que quepan más de dos y una base correcta para lo que venga.
- Las dos que fallan no son de esta vuelta: «¿una hoja es un vehículo?» → «No lo sé» (debería decir que no), y «botones» lo lee como «botón».

## 5. Límites

- **Elegir el sentido por el contexto de la frase** («tengo un gato en el maletero para cambiar la rueda» → la herramienta) no está
  hecho. Ahora solo se elige por el tipo de aquello de lo que se habla (persona o no). Es el paso siguiente natural, y el léxico trae
  las definiciones de cada sentido para intentarlo.
- El léxico no conoce todos los sentidos: «banco» como empresa no sale (sí como institución o entidad); «sierra» como montaña, tampoco.
- «¿qué es un banco?» sigue contestando un solo sentido. No lo he cambiado porque muchas pruebas antiguas esperan esa respuesta.
- Los tocayos se siguen detectando solo al presentar a alguien con «mi X se llama N».
- Medida pequeña (28 turnos) y escrita por mí.

## 6. Interruptores y verificación

`LCM_SIN_ACEPCIONES=1` (la medida limpia vuelve a 78,6 % con 2 falsas), `LCM_SIN_TOCAYOS=1` (53,6 % con 8 falsas), `LCM_SIN_GRAFO=1`.

Tandas 01–15 e iter26…iter228: fallan solo las 4 conocidas (iter26 t11, iter28 t23, iter210 t01, iter214 t05). Tanda nueva `lab/iter228/t01.py`: 47 sondas, 100 %. Pytest: 997 pasan; fallan los 3 de entorno de siempre.

Para repetir: `python -m lab.iter228.charla charlas_test`.
