# LCM 2.12 · Coordinación de tres o más elementos y 1559 conceptos de fábrica nuevos

Parche sobre la 2.11. No se reentrena nada. Los conceptos son categorías cotidianas, no hechos del mundo.

## 1. Conceptos de fábrica: de 1122 a 2686 formas (+1564)
Añadidos en `src/nucleo20/conceptos_base.txt`, en la taxonomía con capas:
- **Animales:** mamíferos, aves, peces, insectos, crustáceos, moluscos, reptiles, gusanos.
- **Plantas:** árboles, flores, hierbas aromáticas.
- **Alimentos:** frutas, frutos secos, verduras, carnes, dulces, platos, panes, bebidas, condimentos, salsas.
- **Casa:** muebles, ropa de casa, vajilla, cubiertos, utensilios, objetos de aseo, productos de limpieza, aparatos, herramientas, material de oficina e instrumentos de escritura.
- **Ocio y personal:** juguetes, juegos de mesa y de cartas, prendas, calzado, joyas, accesorios.
- **Lugares:** edificios y comercios, elementos urbanos, paisajes, divisiones territoriales, viviendas, partes de la casa, habitaciones.
- **Transporte:** vehículos, barcos.
- **Personas:** unas 150 profesiones, más personas por edad o papel.
- **Cuerpo y salud:** partes del cuerpo, enfermedades, medicamentos.
- **Tiempo y sucesos:** eventos, tiempos, festividades.
- **Otros:** emociones, deportes, asignaturas, estilos musicales, instrumentos, idiomas, documentos, colores, formas, materiales, fenómenos, astros, elementos naturales, dinero, medios de comunicación, recipientes, armas, actividades y organizaciones.

**Cuidados:**
- Se corrigieron dos choques por tildes («carné/carne», «sábana/sabana»).
- Se evitaron nombres de pila (luna, alba, sol) y palabras que se confunden con verbos («saco») o preposiciones («bajo», «sobre»).
- Un nombre propio de la conversación manda sobre el concepto («el Albatros» es el yate del usuario, no el ave).
- Las profesiones salen ahora de toda la jerarquía de fábrica («¿a qué se dedica?» con «es dentista»).

**Nuevo razonamiento con la jerarquía:**
- «¿Un jabalí es un ser vivo?» → «Sí. Lo deduzco porque un jabalí es un mamífero, un mamífero es un animal…».
- Responde «No» solo cuando las categorías son claramente incompatibles:
  - grupos distintos (ser vivo / cosa / lugar / abstracto): «¿un rifle es un ser vivo?» → «No, un rifle es un arma»;
  - ramas que no se cruzan (mamífero / ave / pez…; animal / planta): «¿un pingüino es un pez?» → «No, es un ave».
- En los demás casos dice lo que sabe y que no está seguro.

## 2. Coordinación
- **Tres o más sujetos con «yo»:** «Nerea, Iker y yo vamos a la piscina» (antes salía «Nerea Iker», un solo nombre). La respuesta va en una sola frase: «Nerea, Iker y tú van…».
- **«su» dentro de una lista:** se refiere al anterior («mi primo Dani, su novia y yo» = la novia de Dani).
- **Listas de lugares y complementos:** «a Escocia, Irlanda y Noruega»; «niños de Rumanía, Marruecos y Ecuador», que se reparte; «había gente de Vigo, de Lugo y de León».
- **«¿Hay…?» de sí o no**, y «hay» ya no sustituye cosas distintas del mismo tipo.
- **Verbo repartido:** «Pongo los platos en la mesa, los vasos en el armario y las tazas en el cajón».
- **Atributos coordinados:** «es alto, delgado y muy simpático»; una frase por atributo cuando hace falta.
- **«y yo también / y mi tío también / y yo tampoco»:** copia el predicado con la persona y el género adecuados («mi tía es abogada y mi tío también» → «tu tío es abogado»).
- **«Ni Clara ni Rubén ni yo tenemos perro»:** un hecho negado por sujeto.
- **Listas tras dos puntos:** «tengo tres tías: Carmen, Luisa y Pilar».
- **«Tú y yo somos amigos»:** la relación es con el LCM.
- **Listas de acciones:** «me voy a trabajar» dentro de una lista ya no se toma como una despedida.

## Método y resultados
1. Antes de tocar el código, con la 2.11 congelada, se escribieron `lab/charla50g.py` (50 turnos) y `lab/examen_ciego12.py` (41 turnos). Se midieron sin leer las respuestas.
2. **Examen de conceptos** (`lab/examen_conceptos212.py`):
   - 40 sustantivos sacados **al azar** (semilla 2112) del corpus UD Spanish, entre los que la base 2.11 no conocía, filtrados de forma automática por categoría concreta en el léxico MCR. Se hizo después de escribir los conceptos y sin mirarlos.
   - Parte A, «¿qué es X?».
   - Parte B, 51 preguntas de jerarquía: «¿un rifle es un objeto?», «¿un hombre es un ser vivo?».
3. Cuatro tandas de desarrollo y una sola medida final.
4. Auditoría manual con el mismo criterio para las dos versiones (`lab/iter212/auditoria.json`).

| Prueba | 2.11 | 2.12 |
|---|---|---|
| charla50g, juez automático | 60,00 % · 2 «falsas» | 86,00 % · 0 |
| charla50g, auditada | 44,00 % · 6 falsas | 84,00 % · 0 |
| ciego 12, juez automático | 48,78 % · 2 | 85,37 % · 1 |
| ciego 12, auditado | 41,46 % · 1 | 82,93 % · 0 |
| conceptos A («¿qué es X?») | 90,0 % · 3 | 90,0 % · 3 |
| conceptos B (jerarquía) | 0,0 % · 0 | 27,5 % · 0 |
| exámenes del autor / ciego 2 / ciego 6 / ciego 7 | 88,05 / 94,35 / 80,60 / 76,74 | igual |

- **Parte A:** no mide la base nueva, porque en las dos versiones la contesta el léxico MCR de la capa antigua (el mismo del que salió la muestra). En la 2.12, 8 de esas respuestas salen ya de la base de fábrica. Las 3 falsas son del léxico (por ejemplo, «asiento» como parte del cuerpo) y siguen igual.
- **Parte B:** solo la puede contestar la base. Pasa de 0 a 14 de 51, sin ninguna falsa. El resto son abstenciones: «mineral», «proceso», «estilo», «culé», «hombre»… no están en la base. Esta cifra mide, sin trampas, cuánto cubre la base de un vocabulario elegido al azar.
- **Primer intento de las 4 tandas** (corregido a mano cuando el juez fue laxo): 44,8 % (26 de 58), con 2 falsas («Nerea Iker»).

## Lo que queda mal
- **Acciones coordinadas con verbos de una palabra:** «me levanto, desayuno y salgo a correr», «Teresa estudia, trabaja y cuida de su madre».
- **«en mi barrio hay una farmacia, dos bares y un mercado»:** solo guarda la farmacia.
- **«tengo un perro negro, una gata blanca y dos peces»:** lo captura la capa antigua de dibujo, que se trata en la 2.13.
- **«¿Mi hermana sabe nadar?»:** no lo entiende como pregunta, aunque el hecho está guardado.
- **La base sigue sin abstractos:** proceso, estilo, mezcla…
