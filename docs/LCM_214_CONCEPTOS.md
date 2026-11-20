# LCM 2.14 · Nueva tanda de conceptos

Petición: «una tanda con todos los conceptos que consideres necesarios para mejorar el LCM». Siguen valiendo las mismas condiciones:
- conceptos, no hechos del mundo;
- cuantos más mejor, para conversar con una persona.

## 1. Qué se ha añadido

| Relación en la base de fábrica | 2.13 | 2.14 |
|---|---|---|
| Términos clasificados (taxonomía) | 2516 | **3334** |
| Pares de contrarios | 84 | **538** |
| Todos con partes | 16 | **90** |
| Propiedades | 222 | **346** |
| Efectos (verbo → estado) | 27 | **53** |

**De dónde salen.**
- Del corpus UD saqué los sustantivos frecuentes que la base no conocía: 2977 con frecuencia ≥3. Hasta palabras de conversación diaria faltaban: «hombre», «mujer», «problema», «idea», «película», «canción», «regalo», «vida»…
- Los clasifiqué a mano, con el hiperónimo del léxico MCR solo como pista.
- La base era fuerte en cosas concretas y casi no tenía **categorías abstractas**. Ahora tiene:
  - acción (y delito, ofensa, juego);
  - idea, información, cualidad, magnitud, situación;
  - resultado (éxito/fracaso), relación, acuerdo, norma, cargo;
  - unidad de medida, cantidad, signo;
  - obra artística, texto, imagen;
  - grupo de personas, ser imaginario, astro, sustancia.
- **Personas**, con sus capas:
  - político (alcalde, ministro, concejal…), noble, criminal, deportista, militar, religioso;
  - roles cotidianos: pasajero, vecino, testigo, ganador…
- **Contrarios** (`[contrarios]`):
  - unos 450 pares escritos a mano: adjetivos, verbos, sustantivos y adverbios;
  - 42 pares con prefijo negativo sacados por regla del léxico MCR (activo/inactivo, consciente/inconsciente…);
  - descarté pares peligrosos en una charla: «sí/no», «este/oeste» («este» también es demostrativo), «solo/acompañado» («solo» = únicamente), «maduro/verde» (verde es un color).
- **Partes** de muebles, habitaciones, edificios, vehículos, ropa, aparatos, cuerpo, animales, alimentos…
- **Propiedades de clase:** las herramientas sirven para trabajar, los recipientes para guardar cosas, las armas son peligrosas, los lácteos vienen de la leche…
- **Efectos:** calentar → caliente, asustar → asustado…

**Lo que no se ha añadido a propósito:**
- Hechos del mundo, como «la luna gira alrededor de la Tierra» o «el sol es una estrella».
- Las palabras de familia («hermano», «novio») en la taxonomía: el núcleo las trata como relaciones. En su lugar, una regla dice que son personas.
- Propiedades de oficio del tipo «conductor: conducir». Interferían con «¿quién sabe conducir?», que debe contestarse con lo que dice la persona.
- La palabra «saco»: choca con el verbo «sacar», como ya pasó en la 2.12.

Todo está en un bloque al final de `conceptos_base.txt`, fácil de auditar, y no se borra nada de la 2.13.

## 2. Arreglos que salieron al hacerlo

- **«¿qué es lo contrario de X?» no llegaba a la base:** una regla lo mandaba a la capa antigua, que fallaba con «caro».
  - Ahora lo contesta la base.
  - Si la palabra no está, lo saca del léxico MCR y lo dice así («Según mi léxico…»). Si la palabra es un sustantivo conocido («médico») o no hay antónimo, dice que no lo sabe.
- **Se aprende «el frío es lo contrario del calor».**
- **Error antiguo:** el patrón de «¿un X es una Y?» leía «una» como «un» + «a …», así que fallaban todas las clases femeninas.
- **«una profesora muy simpática»:** el adjetivo se perdía y ya no. También «¿qué es mi hermano?» → «Tu hermano es médico».
- **«¿un martillo sirve para trabajar?»** se contesta con las propiedades de su clase.
- **Las clases de objeto por función se solapan** (recipiente, utensilio, herramienta, vajilla…): una tetera es utensilio *y* recipiente, así que ya no se niega una por ser «hermana» de la otra.
- **`lab/graba_fixture.py` no incluía iter213:** el cambio se perdió al cerrar la 2.13 (el guion de limpieza lo revirtió). Ya está corregido, y el guion de limpieza solo toca archivos de resultados.

## 3. Medidas: léelas con cuidado

**Examen ciego 14** (escrito con la 2.13 congelada, muestras al azar de UD/MCR): 2.13 = 32,9 % (25 falsas) → 2.14 = 79,0 % (7 falsas), auditado. **Está contaminado.**
- Vi las muestras antes de escribir los conceptos, y muchas palabras de la muestra acabaron entre las añadidas (contrarios como «previo/posterior», todos como «mesa» o «barrio»).
- No mide si lo añadido generaliza. Lo dejo registrado tal cual.
- La parte D (propiedades) se protegió: solo propiedades de clase, nunca de los miembros de la muestra, y se queda en un 39 %.

**Examen ciego 14b**, la medida que vale:
- otra semilla (2141);
- excluye toda palabra vista en el 14;
- se escribió **después de congelar la 2.14 y antes de medir ninguna versión**.

| Parte | 2.13 | 2.14 (ciega) |
|---|---|---|
| A · jerarquía (57) | 26,3 % | 45,6 % |
| B · contrarios (35) | 31,4 % | 74,3 % |
| C · partes (12) | 58,3 % | 58,3 % |
| D · propiedades (23) | 47,8 % | 65,2 % |
| E · charla (11) | 63,6 % | 90,9 % |
| **Total (138)** | **37,0 % · 7 falsas** | **60,9 % · 9 falsas** |

- **Dos falsas son nuevas y son de esta ronda:**
  - «lo contrario de retirar es invertir» (un par mal escrito);
  - «una tetera no es un recipiente» (la regla de clases hermanas).
- **Arreglos tras la medida (no ciegos):** con los dos quitados y con el contrario sacado del léxico MCR fuera de la base, el 14b sube a **67,4 % con 7 falsas**.
  - La parte B queda al 100 %, pero en parte es circular: varios criterios se escribieron con los antónimos de MCR.
- **C no mejora:** los todos de la muestra eran mayoritariamente abstractos («confianza», «equipo») o sin partes anotadas.
- **Hay falsas antiguas que vienen de la capa de diccionario:**
  - «la tierra tiene como partes aire y cielo», «un equipo tiene banquillo»;
  - «la cena no es una comida»: «cena» y «comida» están anotadas como eventos.

**Controles** (ninguno baja):

| Control | 2.13 | 2.14 |
|---|---|---|
| Exámenes del autor | 88,05 % | 88,19 % |
| Ciego 2 | 94,35 % | 94,35 % |
| Ciego 6 | 80,60 % | 80,60 % |
| Ciego 7 | 76,74 % | 79,07 % |
| charla50h | 100 % | 100 % |
| ciego13 | 100 % | 100 % |

- pytest: 840 pruebas pasan.
- Tandas de desarrollo iter214 (5 tandas, 74 interacciones): primer intento corregido a mano en la tanda 3.

## 4. Lo que queda

- **La jerarquía de la muestra limpia sigue a medias (46 %).** Faltan sustantivos frecuentes: fachada, convento, tensión, maniobra, aplauso, domicilio, protocolo… La siguiente tanda debería clasificar el resto de la lista de UD con la misma regla y medir con una muestra nueva.
- **«¿Qué es X?» para una raíz abstracta** («¿qué es una norma?») aún cae en la capa antigua, que a veces contesta raro.
- **Clases genéricas poco útiles:** «meta» → «idea», «precio» → «magnitud». Son correctas, pero dicen poco: falta una capa intermedia (objetivo, valor económico).
- **«cena» y «comida»** están anotadas solo como eventos; falta su sentido de alimento.
- **Las propiedades de oficio** quedan fuera hasta que «¿quién sabe…?» separe bien lo dicho por la persona de lo de fábrica.
