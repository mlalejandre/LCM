# LCM 2.30 · Vectores de tema, entrenados leyendo y conversando

Lo que pediste: que el contexto no venga de fábrica como una tabla, sino que el modelo lo **aprenda** del texto que se le inyecta y de
la conversación; lo justo para conversar con soltura y seguir aprendiendo conceptos con quien habla.

## 1. Resultado

Medida limpia escrita **antes** de escribir el texto de entrenamiento (10 conversaciones, 18 turnos), medida una vez:

| | 2.29 | 2.30 (ciega) | 2.30 final (no ciega) |
|---|---|---|---|
| Acierta sin preguntar | 6 | **11** | 12 |
| Pregunta («¿qué Andrés?», «¿de qué sentido hablamos?») | 6 | 4 | 3 |
| Contesta mal o no contesta | 6 | 3 | 3 |

Con los vectores apagados (`LCM_SIN_TEMA=1`) vuelve a 6 de 18. En las conversaciones de desarrollo, de 5 a 12 de 18.

Regresiones: ninguna (solo los 4 fallos conocidos de siempre). Controles: idénticos a la 2.29 línea por línea (autor 634/703 = 90,18 %). El examen grande (88,4 %), los bancos de lectura y diccionario y las medidas de las vueltas
2.25–2.29, iguales.

Es una mejora real pero a medias: acierta el doble, y todavía pregunta o falla en una de cada tres. Abajo explico por qué.

## 2. Cómo aprende (`src/nucleo20/tema.py`)

Cuenta qué palabras de contenido aparecen **en la misma frase**. De ahí sale, para cada palabra, un vector: con qué otras aparece más
de lo esperable. Dos palabras son del mismo tema si aparecen juntas o si tienen las mismas compañías.

- No guarda hechos («Brasil produce café»), guarda compañías («café» va con «taza», «leche», «desayunar»).
- **Capa de fábrica**: el texto inyectado (`data/corpus_tema.txt`) y lo que la base de conceptos ya relacionaba (qué es parte de qué,
  dónde suele estar algo, para qué sirve). Se entrena sola en unos segundos la primera vez, y otra vez cada vez que cambia el archivo.
- **Capa del usuario**: cada frase que el modelo lee u oye suma sus cuentas y se guarda con su memoria (tope: 6.000 parejas). Lo que
  dice el usuario pesa el triple que una frase de fábrica.

## 3. El texto que he inyectado

Unas 270 frases mías en 26 escenas corrientes: la casa, comer y beber, animales, plantas, dinero y banco, el parque, el ordenador,
cartas y correo, juegos, deporte, escuela, oficios, salud, viajes, el tiempo, ropa, fiestas, escribir, herramientas, y una sección
de «clases de cosas». Con la base de conceptos: 1.632 frases, 1.212 palabras, 3.065 parejas.

Es poco, a propósito, para ver si el mecanismo funciona. Ejemplos de lo aprendido: tubería–fontanero 0,61; perro–veterinario 0,63;
pelo–peluquero 0,48; banco–dinero 0,80; ratón–queso 0,66; torneo–premio 0,20 (pocas frases).

## 4. Para qué se usa

**Personas.** La frase, y lo que se venía hablando, casa con la ficha de uno de los tocayos aunque no compartan palabra:

```
Mi tía se llama Marta y es veterinaria.   Mi jefa también se llama Marta…
Mi perro está enfermo y no quiere comer.
¿a qué se dedica Marta?    → Tu tía Marta es veterinaria.
```

**Palabras: los grupos de compañías.** Esto es lo más interesante que salió. Las compañías de una palabra con varios sentidos se
agrupan solas por sentido:

```
banco  → [dinero, ahorrar, prestar, cajero, tarjeta…]  [sentar, silla, mueble, abuelo]  [parque, columpio, fuente, sombra]
ratón  → [ordenador, teclado, pantalla, cursor, cable…]  [gato, cazar, maullar, trampa…]  [queso, roer, comer, animal]
copa   → [vaso, cristal, beber, brindar, botella…]  [campeón, torneo, ganador, medalla, premio…]
gato   → [veterinario, perro, clínica…]  [maullar, cazar, ratón…]  [pinchar, maletero, rueda, cambiar]
```

El contexto elige un grupo y el grupo dice el sentido. A cada grupo se le pone nombre si entre sus palabras está el de un sentido
(«mueble», «premio»), si la palabra es parte de algo del grupo (ratón–ordenador–aparato), o si el usuario lo aclaró. Si el grupo está
claro pero no se sabe qué sentido es, pregunta, y con la respuesta **aprende el grupo entero**, no solo esa frase.

Fíjate en «gato»: el grupo de la herramienta (maletero, rueda) aparece aunque ni la base de conceptos ni el léxico conocen ese sentido.

## 5. Por qué no llega más lejos

- **Poco texto.** Con 270 frases muchas parejas se han visto una o dos veces. «Clic» y «pantalla» bastan para el ratón; «sacar
  dinero de mi cuenta» no basta para el banco, porque el grupo del dinero no lleva el nombre de ningún sentido y hay que preguntar.
- **Los sentidos tienen nombres de clase** («mueble», «edificio», «documento») y esas palabras casi no aparecen en frases corrientes.
  Por eso enlazar grupo y sentido es el paso débil, y por eso aprender de la respuesta del usuario es lo que más vale.
- **Los ajustes son frágiles.** Cuánto pesa lo reciente frente a la ficha, o cuándo una frase suelta cuenta, lo fijé con las
  conversaciones de desarrollo y cada cambio movía otra cosa. Probé a relacionar palabras a través de una compañía común y lo
  retiré: disparaba relaciones falsas (el ratón del queso pasaba a ser un aparato). Solo queda para palabras nuevas.
- El caso de aprender de un texto del usuario («zurbos» → pastelero) no sale: aprende las compañías, pero no llega a decidir.

## 6. Dos expectativas antiguas que cambian

Como en la 2.29: «¿dónde vive Pedro?» justo después de preguntar por «mi hermano» ya no pregunta cuál; y la copa del torneo ya no
necesita preguntar. Puestas al día y anotadas en los archivos.

## 7. Qué haría ahora

Lo que más rinde es **más texto**: el mecanismo ya está y es barato de alimentar. Dos vías que no se excluyen:

1. Que yo siga escribiendo escenas (unas 1.000–2.000 frases más) y midamos cuánto sube con cada tanda.
2. Que el modelo aprenda de todo lo que lee: ya lo hace, y cada texto que le pegues suma.

Y una mejora de fondo: usar estos mismos vectores en el diccionario de la 2.24 (parejas como «vigilar»/«cuidar», que el léxico no enlaza).

## 8. Interruptores y verificación

`LCM_SIN_TEMA=1`. Para ver lo aprendido: `python -c "from src.nucleo20 import tema as T; print(T.vecinas(None,'banco',12)); print(T.grupos(None,'banco'))"`.

Tandas 01–15 e iter26…iter230: sin cambios (fallan las 4 sondas de siempre: iter26 t11, iter28 t23, iter210 t01, iter214 t05). Tanda nueva `lab/iter230/t01.py`: 24 sondas, 100 %. Pytest: 1029 pasan, 3 fallan (los 3 de entorno de siempre).

Para repetir: `python -m lab.iter230.charla charlas_test`.
