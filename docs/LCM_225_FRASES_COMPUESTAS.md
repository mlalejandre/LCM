# LCM 2.25 · Conversar con frases compuestas

Primera vuelta «automática» de la noche. En vez de un banco por proceso, volví a **conversar con el LCM** en diez contextos distintos
(familia, planes, estado de ánimo, enseñarle palabras, una receta, un texto mezclado con lo personal, medidas, correcciones, amigos,
dónde están las cosas) y leí las transcripciones a mano.

## 1. Resumen

| | 2.24 | 2.25 |
|---|---|---|
| Conversaciones limpias (10 nuevas, 71 turnos puntuados, medida única) | 64,8 % · 6 falsas | **88,7 % · 1 falsa** (17 ganadas, 0 perdidas) |
| Las mismas tras un arreglo posterior (no ciego) | | 91,5 % · 1 falsa |
| Conversaciones de desarrollo (10, 80 turnos) | 68,8 % · 3 falsas | 82,5 % · 1 falsa |
| Bancos de lectura y diccionario | | sin cambios |

## 2. Qué se rompía al conversar

De 80 turnos puntuados fallaban 26. Por causa:

| Causa | Turnos | Ejemplo |
|---|---|---|
| **Frases compuestas** que el núcleo leía mal o no leía | 11 | «Primero pelo las patatas y las corto en rodajas» → guardaba «fríes las corto» |
| **Medidas dichas de palabra** | 5 | «mide un metro ochenta» no se entendía; «Yo mido…» se convertía en «Estoy mido…» |
| Correcciones y cambios de estado | 4 | «el médico es a las once, no a las diez»; «ya lo he recogido» |
| Deducciones entre datos personales | 4 | «el padre de Clara» es mi marido; «¿cuántos somos en casa?» |
| Preguntas de seguimiento | 2 | «¿desde cuándo?» |

El hallazgo: **cada frase simple, el núcleo la entiende** («Pelo las patatas.» «Corto las patatas en rodajas.» → todo bien). Lo que
fallaba era la frase tal como la dice una persona. Así que el arreglo no toca el núcleo: parte la compuesta en simples.

## 3. Qué cambia

**Frases compuestas (`src/nucleo20/coordina.py`, nuevo).** Antes de entender una frase de la charla se mira si la segunda mitad calla algo
que la primera dijo, y se repone:

- el pronombre: «…y **las** corto en rodajas» → «Corto **las patatas** en rodajas»; «…y **las he** metido en el bolso»;
  con sujeto en tercera persona se repite también el sujeto («Mi madre compró una tarta y la llevó…» → «Mi madre llevó la tarta…»);
- el verbo: «A Sara le gusta el cine y **a Hugo el fútbol**» → «A Hugo le gusta el fútbol»; «Irene vive en Jaca y Noa en Cádiz»;
- el verbo y la unidad: «Pablo tiene treinta años y **yo veinticinco**» → «Yo tengo veinticinco años».

Solo interviene en esos casos; las coordinaciones que el núcleo ya entendía («Elena es médica y trabaja de noche») siguen por donde iban.

**Medidas de palabra.** «un metro ochenta» → «1,80 metros», «metro y medio», «dos kilos y medio». Con eso funcionan también las
comparaciones («¿quién es más alto, Pablo o yo?»). Y «mido», «pido», «decido» ya no se toman por participios.

**Seguir el hilo.** Una pregunta de una o dos palabras («¿desde cuándo?», «¿y cuándo?») continúa la pregunta anterior. Y «…a las
once, **no a las diez**» corrige lo último que se dijo con «a las diez».

**Un cierre al diccionario de la 2.24.** Conversando salió «¿cuánto pesa Pablo?» → «Pablo mide 1,80. Entiendo pesar como medir».
El nombre propio contaba como «apoyo en la frase». Ya no: de quién se habla no prueba que se hable de lo mismo.

## 4. Medida limpia

Diez conversaciones nuevas, mismos tipos de contexto y otro contenido, escritas con el código congelado y sin ejecutarlas.

- 2.24: 46 de 71. 2.25: 63 de 71 (medida única). Ganadas 17, perdidas 0. Respuestas falsas: 6 → 1.
- Después vi que «**Leo** pesa treinta y cinco kilos y Vera veintiocho» no se partía («Leo» se leía como el verbo «leo»). Arreglado:
  65 de 71. Ese número ya no es ciego.

Lo que sigue fallando en ellas: «¿tengo hijas?» contesta «Sí, Dani es tu hijo» (falsa: no distingue hijo de hija en esa pregunta);
«El martes ceno con mi primo Óscar» no se recuerda al preguntar; «¿de dónde saco las tablas?»; «¿desde cuándo [trabajo]?» cuando
el dato se dijo como «Empecé en marzo»; «¿dónde sirvió la paella mi padre?» (no entiende la pregunta).

## 5. Lo que he visto y NO he arreglado (para las siguientes vueltas)

- **Cambios de estado**: «Ya lo he recogido» no hace que el coche deje de estar en el taller.
- **Deducciones personales**: «el padre de Clara» (mi hija, mi marido), «¿cuántos somos en casa?», «las llaves están en el cajón y
  el cajón debajo del espejo».
- **Causas entre frases seguidas**: «estoy cansado» + «he dormido cuatro horas» → «¿por qué estoy cansado?».
- **Lo leído aplicado a alguien concreto con «cuándo»**: «¿cuándo ronronea Milo?».
- **Orden de los pasos**: «¿qué hago primero?», «¿qué es lo último que hago?».
- Verbos que el núcleo no conoce en primera persona («cuajo», «uno las tablas»).
- Expresión: «Los faros son situados y torre altos en la costa», «tu abuelo regaló una peonza a ti».

## 6. Salvedades

- Las conversaciones las escribo yo; las limpias repiten los tipos de contexto de las de desarrollo a propósito, para medir si el
  arreglo generaliza a otro contenido, no si el LCM conversa bien de cualquier cosa.
- `coordina.py` es gramática escrita a mano (unos 200 renglones), prudente: ante la duda no parte. Tres tandas antiguas se rompieron
  en la primera versión («mi suegra se llama Pilar y mi suegro Antonio», «a él le ha gustado pero a mí no», «Luis hace el pan y yo
  atiendo») y por eso ahora esos casos se dejan al núcleo.
- Las listas con comas («la lavo, la tiendo y la plancho») todavía no se parten.

## 7. Interruptores y verificación

`LCM_SIN_COORDINA=1`, `LCM_SIN_SEGUIMIENTO=1`. Ablación sobre las conversaciones limpias: con todo 91,5 %; sin frases compuestas 76,1 % (3 falsas); sin seguir el hilo 85,9 % (3 falsas).

Tandas 01–15 e iter26…iter225: fallan solo las 4 conocidas. Tanda nueva `lab/iter225/t01.py`: 206 sondas, 100 %. Controles: autor 90,18 % (=), ciego 2 95,02 (=), ciego 6 83,58 (+1 sonda), ciego 7 79,07, termómetro 97,07 (=), 16b 97,18 (+1), 16c 100, 17b 99,26, 17c 94,50, conversa17 99,33. Pytest: 958 pasan; fallan los 3 de entorno de siempre.

Para repetir: `python -m lab.iter225.charla charlas_test` (enseña cada conversación con su veredicto).
