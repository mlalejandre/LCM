# LCM 2.8 · Ronda nocturna: 260 interacciones corregidas de 10 en 10 (parche sobre LCM 2.7)

## Protocolo

1. **Antes de tocar nada, con la 2.7 congelada, escribí dos referencias nuevas:**
   - `lab/charla50c.py`: una sola conversación natural de 50 interacciones (44 puntuables). La escribí *sin* buscar a propósito los fallos conocidos.
   - `lab/examen_ciego8.py`: seis diálogos de temas que no aparecen en ninguna tanda (56 turnos puntuables).

   Medí las dos solo con el resumen y no leí las respuestas.
2. **26 tandas de 10 interacciones** (`lab/iter28/t01…t26`), con correcciones después de cada una.
   - En cada tanda pasé las regresiones completas y los exámenes de control.
   - Los aprobados falsos que dio el juez se corrigieron a mano en `lab/iter28/primer_intento.json`, con una nota en cada caso.
3. **Código congelado y medida final** en una sola pasada.

## Resultados (2.7 y 2.8 con el mismo juez)

### Las referencias nuevas: la mejora real es pequeña

| Prueba | 2.7 | 2.8 |
|---|---|---|
| Charla 50 C, juez automático | 65,9 % | 70,5 % |
| Charla 50 C, auditoría manual | 63,6 % | 63,6 % (congelada) · 68,2 % (tras corregir, **no ciega**) |
| Examen ciego 8 (n=56) | 76,8 % | 76,8 % (respuestas idénticas) |

**Advertencia.** Al leer las respuestas después de la medida final aparecieron dos regresiones que había metido la propia 2.8:

- **«estudias a Derecho»:** la «a» personal se ponía delante de cualquier nombre propio. Afectó a 5 turnos.
- **«la enferma es morada»:** el verbo «está» se leía como el demostrativo «esta», y el color de la foto se aplicaba a otra cosa.

Las corregí después de leer las respuestas. Por eso la cifra «tras corregir» ya no es una medida ciega.

**Conclusión sincera.** Las 26 tandas arreglan bien lo que tocan, pero generalizan poco a conversaciones nuevas: el examen ciego 8 no se mueve.

### Curva de aprendizaje (primer intento de cada tanda)

| Tandas | Turnos | Acierto al primer intento | Falsas |
|---|---|---|---|
| T01–09 | 86 | 65,1 % | 10 |
| T10–18 | 81 | 70,4 % | 5 |
| T19–26 | 74 | 74,3 % | 1 |

### Control: no se ha roto nada

| Prueba | 2.7 | 2.8 |
|---|---|---|
| Examen ciego 2 (n=301) | 93,69 % | 93,69 % |
| Examen ciego 6 (n=67) | 79,10 % | 80,60 % |
| Examen ciego 7 (n=43) | 69,77 % | 69,77 % |
| Exámenes del autor (n=703) | 88,05 % | 88,05 % |
| Banco generado, validación (n=12 331) | 98,49 % | 98,49 % |
| Charla 50 B (ya gastada, orientativa) | 95,0 % | 97,5 % |

- Tandas 1–15, iter26, iter27 e iter28: todas al 100 %, salvo iter26 T11 y iter28 T23.
- pytest: 761 pruebas bien; fallan solo las 3 de siempre, que dependen de mi entorno.

**Juez más estricto.** Si una respuesta empieza por «No lo tengo del todo claro», ya no aprueba un criterio «no».

## Qué entiende ahora

### Estilo indirecto, deseos y opiniones

| Frase | Se guarda como |
|---|---|
| «el médico me ha dicho que descanse» | te dice que descanses (antes: «que descansaste») |
| «mi hermana quiere que vaya a su casa», «mi jefe me pide que llegue antes» | un deseo o una petición, no un hecho |
| «Lo haré la semana que viene» | irás a su casa la próxima semana |
| «lo tengo que entregar el lunes» | el informe que te pidieron |
| «le he dicho que lo deje» | le dijiste a tu hermano que lo deje |

### Pronombres

- «mis hijos la prefieren con queso» y «¿cómo la prefieren?».
- «la he visto con mi primo», «las voy a llevar al zoo», «se lo voy a enseñar a mis padres».
- «hoy la he llamado» → a Laura; «¿para qué la he llamado?».
- «la pintaremos de blanco» → la cocina, no tu mujer.
- «me opera el doctor Ruiz» y «¿quién me opera?».
- «nos ha invitado a comer» y «¿con quién vivo?» a partir de «Carmen vive conmigo».

### Imágenes dentro de la charla

- «este es el color que le gusta a mi mujer», «el que me gusta a mí».
- «he hecho este cuenco», «es este», «esta es Mimi».
- «es el color favorito de mi novia».
- El color de una figura sobre un fondo (antes daba el del fondo).
- Colores que también son nombres: «el cuadro es naranja».

### Grupos y cantidades

- «se llaman Paula y Marta» (grupo del que se venía hablando).
- Gemelas, por tanto hermanas.
- «ha tenido cuatro» (cuatro gatitos).
- «veinte mil euros».
- «manzanas, plátanos y uvas»; «alto, rubio y simpático».

### Tiempo

- «los martes y los jueves»; «el día doce»; «tres veces por semana»; «desde el colegio».
- «las clases son los martes».
- «el sábado nos ha invitado» apunta al próximo sábado.
- «visitamos la Alhambra», en un relato, es pasado.

### Otros

- «Me duele bastante» → el tobillo.
- «hizo frío» / «¿qué tiempo hizo?».
- «antes fumaba pero lo dejé» → «¿fumo?»: ya no.
- «vivo sola desde que murió mi marido».
- «tengo tres nietos que me visitan».
- Hendidas: «el pan de centeno es el que más vendemos», «Soy Raquel, la que tiene una panadería».
- «¿Me recomiendas algo?»: dice con honradez que no aconseja y recuerda lo que le dijo el médico.

## Lo que sigue fallando (examen ciego 8 y charla 50 C, leídos tras medir)

- «Mi compañero Iván, que es el portero, se lesionó» (rol con artículo definido).
- «El domingo es el cumpleaños de mi abuelo» (el orden contrario al que se resolvió).
- «Anselmo fue carpintero toda su vida»; «¿a qué se dedicaba?».
- «¿De qué color era la furgoneta?» cuando el color iba como adjetivo («una furgoneta blanca»).
- «Comparto piso con dos amigas, Alba y Sofía»; «cuando acabe los exámenes me iré…».
- «yo no puedo dormir, mañana tengo un examen» (dos frases unidas por una coma).
- Dativos: «le están saliendo los dientes».

## Cómo repetir

```
python -m lab.charla50c         # referencia 2.8
python -m lab.examen_ciego8
python -m lab.iter28.correr N   # N = 1..26
python -m lab.medir lcm28 12 1,2,3,4,5
```
