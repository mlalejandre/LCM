# Diagnóstico · ¿Cómo aprende el LCM un tema nuevo? (sobre LCM 2.17)

Experimento `lab/aprender18.py`: el texto, la conversación y los criterios se congelaron en un commit antes de ejecutar nada.
No se ha cambiado código: esto es solo medida y diagnóstico.

## Diseño

- **Tema:** hongos y setas. De fábrica solo sabía «seta → hongo → ser vivo». El diccionario de 71 807 conceptos sí trae algunas
  palabras (micelio, trufa, penicilina, micólogo), a veces con el sentido equivocado.
- **Texto:** 32 frases expositivas normales, escritas como las de un libro divulgativo, sin adaptarlas al analizador.
- **Conversación:** 66 turnos, de los que 59 son preguntas puntuables de 12 tipos (literal, paráfrasis, inversa, vocabulario,
  herencia, deducción, combinar dos frases, charla con lo aprendido, uso generativo, no dicho, contradicción y retención).
- **Cuatro condiciones con la misma conversación:**
  - `base`: sin texto;
  - `texto`: el texto pegado de una vez;
  - `frases`: el texto dicho frase a frase en la charla;
  - `escuela`: el texto como cartilla de fábrica, en una sesión nueva.
- **Medidas añadidas:**
  - auditoría a mano de las 236 respuestas;
  - fidelidad frase a frase de lo que se guarda;
  - sondeo de recuperación con paráfrasis sobre los hechos que sí se guardaron bien;
  - persistencia entre sesiones y olvido.

## Resultados

Acierto auditado, con el número de afirmaciones falsas detrás de cada cifra:

| Tipo (n) | base | texto | frases | escuela |
|---|---|---|---|---|
| Literal (7) | 0 % | **71 %** | 57 % | 29 % |
| Paráfrasis (6) | 17 % · 1F | 17 % · 1F | 17 % | 17 % |
| Inversa (6) | 0 % | 33 % | 0 % | 17 % |
| Vocabulario (4) | 50 % · 1F | 100 % | 75 % | 75 % · 1F |
| Herencia (6) | 33 % | 83 % · 1F | 83 % · 1F | 50 % · 1F |
| Deducción (7) | 0 % | 57 % · 1F | 29 % | 0 % |
| Combinar dos frases (2) | 0 % | 0 % | 0 % | 0 % |
| Charla + lo aprendido (6) | 33 % | 33 % | 33 % | 33 % |
| Usar / generar (5) | 20 % · 2F | 20 % · 2F | 20 % · 2F | 40 % · 2F |
| No dicho: abstenerse (4) | 100 % | 50 % | 100 % | 100 % |
| Contradicción (2) | 0 % | 0 % | 0 % | 0 % |
| Retención (4) | 0 % | 0 % | 0 % | 0 % |
| **Total (59)** | **20 %** · 4F | **44 %** · 5F | **37 %** · 3F | **31 %** · 4F |

Corrector automático: base 18,6 %, texto 47,5 %, frases 42,4 %, escuela 28,8 %.

Cómo leer la tabla:
- El texto pegado más que duplica el acierto (20 → 44 %), pero en ninguna condición llega a la mitad.
- La retención sale 0 % por la forma de las preguntas, no por olvido. Dentro de la sesión no se pierde nada: lo que se acertó antes
  se vuelve a acertar. Falla porque «volviendo a las setas, ¿…?» no se entiende y porque se repiten preguntas que ya fallaban.

**Comprensión frase a frase** (fidelidad auditada a mano: ¿lo guardado dice lo mismo que la frase?):

| Vía | Fiel | Parcial | **Falso** | No entendida | Dice haber entendido |
|---|---|---|---|---|---|
| Texto pegado | 9 (28 %) | 5 | **1** | 17 | 14 (honesto) |
| Frase a frase en la charla | 9 (28 %) | 11 | **6** | 6 | 28 («Entendido» en casi todo) |
| Escuela (cartilla) | 2 estructuradas + 9 como texto opaco | — | 1 | 21 | 11 |

**Recuperación de lo bien guardado** (sondeo de 25 preguntas):
- con las mismas palabras del texto: 100 %;
- con otras palabras: 68 %, con 4 respuestas que no corresponden.

**Persistencia:**
- Lo entendido sobrevive a una sesión nueva.
- Lo no entendido solo se guarda tal cual, en una lista que conserva los **tres últimos textos**. Tras leer otros tres desaparece y
  vuelve el sentido equivocado del diccionario («micelio: parte de una planta»).

## Debilidades, de la más grave a la menos

1. **Aprende cosas falsas por arrastre de sujeto.** Si una frase no se entiende, la siguiente sin sujeto se atribuye al tema
   anterior. «La amanita faloides es la seta más venenosa…» no se entendió, así que «Su veneno destruye el hígado» se guardó como
   *el veneno del boletus*, que es la seta comestible. En la charla pasa lo mismo: «Sirve para hacer pan» se atribuyó a la amanita.
   Es el error más peligroso, porque se dice con seguridad.
2. **Comprensión baja del texto expositivo: solo el 28 % de las frases se guarda fielmente.** No cubre:
   - aposición como definición («el micelio, una red de hilos»; «la penicilina, un medicamento»);
   - superlativos («la seta más venenosa», «uno de los alimentos más caros»);
   - nombrar clases («se llaman seteros»);
   - cuantificadores parciales («algunas… otras…»: en la charla quedan como «las setas son comestibles» y «son venenosas», sin
     detectar la contradicción);
   - símiles («como semillas» se guarda como «una espora es una semilla»);
   - concesivas («aunque»), condicionales («cuando cae…»), «por eso», relativas sobre el sujeto y negación coordinada («ni… ni»).
3. **En la charla dice «Entendido» sobre lo que no ha entendido** («Viento llevar Las», «Las personas están en Setas»).
   Al leer un texto es honesto («he entendido bien 14»); frase a frase, no.
4. **Lo leído no se convierte en conocimiento de conceptos: se queda como «cosas que me has contado».** Por eso:
   - «dime tres hongos» → seta, champiñón y moho (ignora trufa, levadura y boletus);
   - «descríbeme una trufa» → «no sé lo bastante», aunque sabe que es negra, con forma de bola y que huele fuerte;
   - la adivinanza sobre la trufa habla de una lámpara: el tema pedido se ignora;
   - las propiedades no bajan por la taxonomía: «los hongos no tienen clorofila» no vale para las setas, ni «las setas tienen
     láminas con esporas» para la amanita.
5. **Supone que una cosa solo pertenece a una clase.** Tras aprender «la trufa es un hongo», contesta «¿la trufa es un alimento?»
   con «No, una trufa es un hongo». En la escuela lo hace aunque sabe que es «uno de los alimentos más caros».
6. **La recuperación depende de las palabras exactas.**
   - Tiene «no pueden fabricar su propio alimento» y no contesta «¿pueden fabricar su propia **comida**?»; «¿qué **comen**?» no
     encuentra «se alimentan de…».
   - Las preguntas inversas por un atributo («¿qué hongo es negro?», «¿qué seta tiene el sombrero marrón?») fallan aunque tenga
     el dato.
7. **La cita de respaldo busca por palabras sueltas, sin comprobar que la frase responda.** De 20 citas, solo 7 respondían. Cita
   frases sin sujeto («Para encontrarla se usan perros») y cita en lugar de abstenerse («¿quién descubrió la penicilina?»).
8. **Faltan puentes de sentido común:** comestible ⇔ se puede comer; venenosa ⇒ peligrosa, no se come. Por eso «¿se puede comer
   la amanita?» no tiene respuesta en ninguna condición.
9. **No contrasta lo que le dicen con lo que ha aprendido.** «La amanita faloides se puede comer» se acepta sin más y además se
   pega a la amanita del vecino. Desde ese momento contesta con ese dato falso.
10. **Correferencia en la charla:** «¿me lo puedo comer?» (el boletus) y «la seta de mi vecino» (la amanita) no se resuelven.
11. **El diccionario se impone con el sentido equivocado:** micelio → parte de planta; trufa → caramelo; «¿es cara la trufa?» →
    «cara y trufa son conceptos distintos».
12. **Lo general se trata como un suceso:** «las setas salen en otoño» se contesta con las fechas del otoño de 2026.
13. **Peticiones que fallan:**
    - «dime una seta comestible» → «Entendido: tu vecino dime una seta comestible»: lo apunta como un hecho falso;
    - «dime una seta venenosa» → «Sí, eso ya me lo habías dicho»;
    - «quiero salir a buscar setas, ¿qué me llevo?» (una afirmación y una pregunta juntas) no se entiende.
14. **Fallos de forma:** «Las láminas se forman las esporas en las láminas», «mundas», «destrue», «laminas» sin tilde.

Lo que funciona bien:
- herencia hacia arriba con justificación («la trufa es un ser vivo: lo deduzco porque es un hongo»);
- persistencia de lo entendido entre sesiones;
- abstención en lo no dicho (salvo cuando lo tapa una cita);
- recuperación exacta al 100 %;
- la lectura de un texto es honesta sobre lo que no entendió.

## Áreas de mejora (impacto = frecuencia × gravedad)

1. **Seguridad de la lectura.** Si una frase falla, la siguiente sin sujeto no hereda un tema dudoso: se guarda tal cual.
   Y la charla no debe decir «Entendido» si lo guardado no se parece a lo dicho.
   *Métrica:* falsas inducidas por la lectura (texto 1, frases 6) → 0.
2. **Gramática expositiva**: aposición, «se llaman», superlativos, cuantificadores parciales, símil frente a pertenencia, concesivas,
   condicionales, «por eso».
   *Métrica:* comprensión fiel por frase, 28 % → más del 70 %.
3. **Consolidar lo leído en memoria de conceptos**, con varias clases por cosa, propiedades heredables hacia abajo y disponible para
   describir, dar ejemplos y crear.
   *Métrica:* tipos G y H del experimento.
4. **Recuperación por significado:** sinónimos (comida/alimento, comer/alimentarse), preguntas inversas por atributo, y comprobar que
   la cita contiene una respuesta del tipo pedido o abstenerse.
   *Métrica:* sondeo con paráfrasis, 68 % → más del 90 %, con 0 respuestas que no corresponden.
5. **Puentes de sentido común** (comestible, venenoso, peligroso) y **contraste de contradicciones** citando la fuente.
6. **Lo aprendido manda sobre el diccionario**, y el sentido de una palabra se elige por el tema de la charla.
7. **Lo leído sin entender no se pierde**: sin límite de tres textos, con un índice.

Para medir la siguiente ronda sin contaminarla: repetir `aprender18` (ya es conocido), escribir un tema nuevo
(p. ej. volcanes o quesos) con el mismo diseño después de congelar el código, y medir ambos.
