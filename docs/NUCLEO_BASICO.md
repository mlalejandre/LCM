# Núcleo básico: lo que el LCM tiene que saber SÍ O SÍ

Estado: ✅ ya funciona (medido) · 🟡 parcial · ❌ falta. Lista propuesta antes del parche-54; el orden de abajo es el de prioridad sugerido.

## A. Conversación (lo mínimo para hablar) — HECHO en parche-54 (ver RESULTADOS.md)
1. ✅ Afirmar hechos («Pedro compró pan ayer») y preguntar (quién, qué, dónde, cuándo, sí/no).
2. ✅ Saludos, despedidas, gracias, «perdona» (actos de habla sociales) y responder con naturalidad.
3. ✅ Pedir aclaración cuando no entiende («¿Te refieres a…?») en vez de «no he entendido».
4. ✅ «No lo sé» honesto y preguntar «¿cómo se llama X?», «¿qué es X?» para aprender lo que le falta.
5. ✅ Preguntas sobre sí mismo y sobre la conversación («¿qué sabes de Pedro?», «¿qué te he dicho hoy?»).
6. ✅ Órdenes y peticiones («Dime lo que sabes de…», «Olvida que…», «Repite»).
7. ✅ Cortesía y registro (tú/usted), exclamaciones, afirmar/negar sueltos («sí», «no», «vale»).
8. 🟡 Referencias: él/ella, mi/yo, este/ese, también/tampoco, «eso es falso», «¿y Ana?» (sí); ❌ «eso», «lo anterior», «también», «otra vez», demostrativos (este/ese/aquel), posesivos (mi, tu, su).

## B. Gramática y significado elementales
9. ✅ Verbos transitivos, ser/estar/tener, negación simple.
10. ✅ Verbos intransitivos y de movimiento («Luis llegó», «Ana duerme», «Pedro corre»).
11. 🟡 Estado y propiedad con adjetivos (✅ «La casa es grande», «Ana está cansada»); ❌ comparaciones («más alto que»).
12. ✅ Modalidad y deseo: poder, deber, querer, saber + infinitivo («Ana quiere comer»).
13. 🟡 Cantidades: todos, algunos, ninguno, muchos, poco y contar (✅); ❌ operaciones (sumar, restar).
14. 🟡 Tiempo: fechas absolutas, hora del día y frecuencia (✅); ❌ duración calculada, pasado/presente/futuro por la conjugación.
15. 🟡 Causa («porque», «¿por qué?») y condición (reglas) ✅; ❌ finalidad («para»).
16. 🟡 Lugar: «en» y encima/debajo/dentro/fuera/cerca/lejos/delante/detrás de (✅); ❌ izquierda/derecha, origen/destino.
17. ✅ Oraciones subordinadas (decir/creer/pensar que) («Pedro dice que Ana vino»): creencias y dichos de otros, distinguir «verdad» de «lo que alguien dice».

## C. Conceptos que debe traer de fábrica
18. ✅ Clases y herencia (ES / tiene), definiciones («Un triángulo es un polígono»).
19. ✅ (parche-59) Personas y parentesco completo (padre, madre, hermano, abuelo, primo, pareja) con sus inversas y reglas (ya hay algunas).
20. ✅ (parche-59) Partes y todo («parte de», «contiene») y su transitividad.
21. 🟡 (parche-59, semilla básica) Cuerpo y sentidos, emociones básicas (alegre, triste, enfadado, miedo), necesidades (comer, dormir, beber).
22. 🟡 (parche-59, semilla básica) Objetos y usos cotidianos (casa, coche, comida, ropa) con sus propiedades típicas.
23. 🟡 (parche-59, semilla básica) Colores, formas (triángulo, círculo, cuadrado…), tamaños, texturas, materiales.
24. 🟡 (parche-59, semilla básica) Naturaleza: animales, plantas, clima, estaciones, día/noche, puntos cardinales.
25. 🟡 (parche-59, quién tiene qué; sin precios) Dinero, trabajo, comprar/vender/pagar (compraventa con consecuencia: quien vende ya no lo tiene).
26. 🟡 (parche-59, dar/vender/comprar/abrir/cerrar/romper/ir/llegar) Acciones elementales con sus efectos: dar/recibir, ir/venir, abrir/cerrar, empezar/terminar, hacer/romper.
27. ✅ (parche-59) Opuestos y sinónimos (grande/pequeño, subir/bajar, abrir/cerrar).

## D. Razonamiento básico
28. ✅ Transitividad ES, herencia de propiedades, reglas enseñadas, explicación («porque…»).
29. ✅ Contradicciones: detectar «Ana es alta» vs «Ana es baja» y preguntar cuál vale.
30. ✅ Cambio de estado en el tiempo («Ana vive en Madrid» → «ahora vive en Sevilla»: el hecho viejo pasa a pasado).
31. 🟡 Orden temporal con fechas (sí); ❌ antes/después entre dos sucesos concretos y duración entre fechas.
32. ❌ Cierre de pregunta con varias respuestas, contar («¿cuántos hijos tiene Ana?»), comparar («¿quién es mayor?»).
33. 🟡 Certeza (procedencia ✅: me lo dijiste / lo deduje / lo dijo otro; falta confianza graduada): distinguir lo que sabe, lo que dedujo y lo que le dijeron (confianza por fuente).

## E. Aprendizaje (el objetivo central)
34. ✅ Aprender hechos y reglas al vuelo, ENTENDI corrige la escuela, dormir consolida.
35. ✅ (parche-58) Aprender una palabra nueva a partir de una definición o de un ejemplo («un *tenedor* es un cubierto para comer»).
36. 🟡 (parche-58) Aprender un verbo nuevo por definición («cocinar es preparar comida con calor»): se hereda al verbo más general; sin condiciones ni efectos.
37. ❌ Corregirse por conversación natural («no, te equivocas, es…») sin comandos especiales.
38. ❌ Olvidar de forma natural («olvida lo de Pedro») y pedir confirmación ante lo importante.
39. ❌ Distinguir entre hechos de la conversación (efímeros) y conocimiento general (permanente).

## Orden propuesto para los próximos parches
1. Actos sociales + aclaración + órdenes básicas (A2, A3, A5, A6, A7): sin esto no «conversa».
2. Verbos intransitivos, adjetivos y estados (B10, B11, B12): desbloquea la mayoría de frases reales.
3. Cambio de estado y contradicciones (D29, D30): memoria coherente.
4. Subordinadas y «X dice que…» (B17, D33).
5. Cantidades, comparaciones y contar (B13, D32).
6. Núcleo de conceptos de fábrica enseñado con frases (C19–C27), midiendo con tests ciegos.
7. Aprender palabras/acciones nuevas desde definiciones (E35, E36).
