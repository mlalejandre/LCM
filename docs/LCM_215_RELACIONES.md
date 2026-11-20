# LCM 2.15 · Relaciones entre conceptos, varias clases y conceptos usados en la charla

Objetivo de la ronda (puntos 1 y 2 acordados): que la conversación **use** los conceptos que ya tiene, y que cada concepto tenga más
relaciones que «X es un Y». Condición: ser estricto y preferir mecanismos conceptuales generales a reglas caso por caso.

## 1. Qué cambia

**Un motor de relaciones, no una regla por pregunta** (`src/nucleo20/relaciones.py`).
- La base declara cuatro relaciones como datos, en secciones de `conceptos_base.txt`:
  - `[funcion]` para qué sirve (272 conceptos);
  - `[material]` de qué suele ser (83);
  - `[lugar]` dónde suele estar (75);
  - `[usuario]` quién lo usa (52).
- El mismo mecanismo vale para las cuatro:
  - **Herencia:** lo que vale para una clase vale para lo que tiene debajo, y manda la clase más cercana. Una gaita «sirve para hacer
    música» porque es un instrumento, aunque nadie haya anotado «gaita».
  - **Sentido directo:** «¿para qué sirve una escoba?», «¿de qué está hecha una botella?», «¿dónde suele estar una cama?».
  - **Sentido inverso:** «¿qué sirve para cortar?», «¿con qué se barre?», «¿qué hay en una cocina?», «¿qué usa un jardinero?».
  - **Sí/no:** «¿una silla sirve para cortar?» → «No, las sillas sirven para sentarse».
  - **Con lo que la persona ha contado:** «tengo unas tijeras» → «¿tengo algo para cortar?» → «Sí: tienes unas tijeras, y las tijeras
    sirven para cortar». Lo que se compra, se tiene.
  - **Composición:** «¿qué tienen en común una nevera y un horno?» → son aparatos, funcionan con electricidad y suelen estar en la cocina.
- Si alguien ha dicho quién usa algo («Ana usa gafas»), manda lo dicho y no lo de fábrica.

**Varias clases a la vez y alias.**
- Un concepto puede estar en más de una clase: la cena es comida y evento; una tetera es utensilio y recipiente; el pollo es ave y
  carne; un cuchillo es cubierto, herramienta y arma.
- Sección `[sinonimos]`: «ropa» nombra la clase «prenda» (igual «mobiliario», «instrumento musical»…). Un alias nunca tapa un concepto
  que ya existe.

**Las personas de la charla tienen clase.**
- Quien entra por una relación entre personas (tía, jefa, vecino) es una persona, y de ahí un ser vivo: «¿mi suegra es un lugar?» →
  «No, tu suegra es una persona».
- El oficio dicho («es enfermera», «es boxeador») es su clase: «¿Carmen es una profesional?», «¿mi sobrino es un deportista?»,
  «¿Carmen trabaja?», «¿quién es político?» se contestan por el cierre de clases, con la cadena de deducción.
- «Es muy trabajador» es una cualidad, no un oficio.

**Fábrica frente a lo dicho.**
- Vuelven las propiedades de oficio («los cocineros cocinan»), que en la 2.14 tuve que quitar. La causa era una reescritura de
  «¿quién sabe conducir?» como si fuera una pregunta de capacidad general; ya no se aplica a «¿quién…?» ni cuando la persona ha
  contado quién sabe hacerlo.
- Lo dicho de un individuo manda sobre lo típico de su clase: «mi gato tiene tres patas» → tres; «un gato» → cuatro.

**Conceptos en el análisis de la frase.**
- Tras un interrogativo, una palabra que la base conoce es el nombre: «¿qué fruta comí?», «¿qué prenda me he comprado?» fallaban
  porque el analizador leía «fruta» y «prenda» como verbos.
- La clase contiene al objeto en el emparejamiento general: lo dicho de una pera contesta a lo que se pregunta de «fruta».

## 2. Medidas

Antes de tocar nada se escribieron y midieron charla50i y ciego15 con la 2.14 congelada. Tras congelar la 2.15 se escribió el 15b,
con palabras **al azar** de la base, excluyendo lo ya visto, y con los criterios puestos sin consultar los datos de relaciones.
Todas las cifras están auditadas a mano con el mismo criterio en las dos versiones.

| Prueba | 2.14 | 2.15 ciega | 2.15 tras arreglos (no ciega) |
|---|---|---|---|
| charla50i (50) | 62,0 % · 3 falsas | 88,0 % · 1 falsa | 98,0 % · 0 |
| ciego15 (58) | 72,4 % · 5 falsas | 96,6 % · 1 falsa | 100 % · 0 |
| **ciego15b, muestra limpia (76)** | **56,6 % · 4 falsas** | **88,2 % · 3 falsas** | 93,4 % · 1 |

Por partes en la muestra limpia (2.14 → 2.15 ciega): relaciones 20 % → 96 %; relaciones en la charla 83 % → 100 %; personas 62 % → 77 %;
herencia en la charla 69 % → 85 %; clases 82 % → 91 %; fábrica y dicho 88 % → 88 %.

Decisiones de auditoría, en las dos direcciones:
- Cuento como acierto cinco respuestas correctas en plural que el corrector automático marcaba mal («los carpinteros y los albañiles»).
- Cuento como **fallo** dos que el corrector aprobaba: «¿con qué se escribe?» (la lista incluía «cuadernos») y «un tractor sirve para
  transportar y viajar» (heredado de vehículo; «viajar» no es propio de un tractor).

Controles: exámenes del autor 88,19 → 88,62 %; ciego2, ciego6 y ciego7 iguales. Sin regresiones nuevas. pytest pasa entero.

## 3. Lo que sigue verde

- **Posesión dicha con «de»:** «el perro de Luis no ladra» no hace que Luis tenga un perro.
- **Oficios de género común:** «mi vecina es piloto» se guarda como «pilota» (falsa), y «¿mi vecina pilota aviones?» no se entiende.
- **Función heredada demasiado general:** un miembro atípico hereda el uso de su clase. Corregí el tractor y otros vehículos de
  trabajo a mano; habrá más casos. La salida conceptual sería marcar en la base qué usos son «típicos» y cuáles «definitorios».
- **Respuestas vagas cuando solo hay dato de clase:** «una hoz sirve para trabajar» (ya anotada como «segar»).
- **Forma:** «una damas» (nombres solo plurales), «Carmen es un profesional» (concordancia).
- **La capa antigua** todavía contesta «No conozco tractor» ante alguna forma de pregunta que el motor no cubre.
- **«¿Quién sabe nadar?»** sigue fallando (viene de antes de esta ronda).
- El examen limpio lo escribo yo: las palabras son al azar, pero las formas de preguntar son las que yo imagino. Un examen escrito por
  otra persona seguiría siendo la mejor prueba.
