# LCM 2.33 · Pronombres con antecedentes probables, sinónimos por concepto y concordancia

Siguiente paso de la 2.32: unir el grafo de relaciones con los conceptos del LCM para que entienda **pronombres** y **sinónimos**, y entrenar
el analizador con **preguntas**. Las tres cosas se han medido por separado; dos funcionan y una no.

## 1. Resultado

Examen limpio escrito antes de tocar el código (6 textos de temas distintos, 56 preguntas), medido una sola vez:

| Tipo de pregunta | 2.32 | 2.33 (ciega) |
|---|---|---|
| Con las mismas palabras del texto | 17 de 17 | 17 de 17 |
| Con un sinónimo («adquirir» por «comprar») | 11 de 16 | 11 de 16 |
| La respuesta está tras un pronombre («el macho **lo** protege») | 10 de 17 | **15 de 17** |
| No está en el texto: debe decir que no lo sabe | 6 de 6 | 6 de 6 |
| **Total** | **44 (78,6 %)** | **49 (87,5 %)** |
| Respuestas equivocadas | 0 | 0 |

Sin la resolución de pronombres (`LCM_SIN_PRONOMBRES=1`) vuelve a 44. Sin la concordancia sujeto-verbo, 48 y una equivocada.

Sin regresión: ninguna (tandas 01–15 e iter26…iter231: solo los 4 fallos conocidos de siempre). Controles: idénticos a la 2.32 línea por línea. Bancos de lectura del LCM, los siete textos de la 2.32, el sistema solar y la conversación de
Manuel: iguales. Pytest: 1092 pasan, 3 fallan (los 3 de entorno de siempre).

## 2. Pronombres: probabilidad según contexto

Un pronombre no se sustituye por un único antecedente. Se guardan **todos los candidatos que concuerdan en género y número**, cada uno con
su probabilidad, que depende de:

- lo reciente que es (misma frase 1, la anterior 0,7, dos antes 0,45, tres antes 0,3);
- el papel: un pronombre sujeto («ella») prefiere al que era sujeto; uno objeto («lo»), al que era objeto;
- si es persona según los conceptos del LCM: «él», «ella» y «le» van con personas («madre», «científicos», «Pablo»);
- y nunca es el sujeto de su propio verbo («el macho **lo** protege»: *lo* no es el macho).

Al preguntar, cada candidato cuenta con su probabilidad. Si el primero está mal, el bueno puede ganar igualmente cuando es el único que
encaja con lo que se pregunta. Es la idea de tu grafo: relaciones con probabilidad según contexto, no una sola lectura fija.

```
La hembra pone un solo huevo en invierno. Después se lo entrega al macho. El macho lo protege durante dos meses.
   entregar: sujeto la hembra (heredado), objeto «lo» ~ un solo huevo 0,46 / invierno 0,33 / el pingüino 0,21, [a] el macho
   proteger: sujeto el macho, objeto «lo» ~ un solo huevo 0,31 / el mar 0,22 / invierno 0,14   (el macho queda fuera: es su sujeto)
¿Quién protege el huevo?          → El macho.
¿A quién entrega la hembra el huevo? → Al macho.
```

## 3. Concordancia: el sujeto tiene que concordar con el verbo

El analizador aprendió de su corpus una costumbre: ante «X lo VERBO» marca X como *dislocado* (en AnCora es lo típico: «El coche lo conduce
su hijo»). Con «Una vecina los llamó» se perdía el sujeto. Ahora:

- un sujeto que no concuerda en número con el verbo se descarta («Su hijo lo conduce *los domingos*»: *los domingos* no puede ser sujeto de *conduce*);
- un elemento dislocado pasa a sujeto si concuerda con el verbo y no es el objeto repetido por el pronombre.

Es gramática, no un parche de tema: vale para cualquier texto.

## 4. Sinónimos: no han mejorado, y por qué

Regla: dos verbos valen por el mismo si sus vectores se parecen 0,8 o más (la de la 2.32), **o** si comparten un concepto del léxico del
LCM y se parecen 0,7 o más. La calibré con 18 parejas de sinónimos y 18 de no sinónimos que no están en el examen:

| | Sinónimos aceptados | Falsos amigos aceptados |
|---|---|---|
| Vector ≥ 0,8 (2.32) | 11 de 18 | 0 de 18 |
| Concepto compartido y ≥ 0,7, o ≥ 0,8 (2.33) | 13 de 18 | 0 de 18 |
| Concepto compartido sin umbral | 17 de 18 | 2 de 18 («entrar»/«salir», «llevar»/«traer») |

El margen es estrecho: «arrojar»/«lanzar» queda fuera con 0,68 y «salir»/«entrar» con 0,69.

En el examen no ganó nada. El diagnóstico (ya no ciego) dice que el problema son **los datos, no la regla**: «proteger»/«defender»,
«detectar»/«localizar», «diseñar»/«proyectar» y «publicar»/«editar» no están relacionados en el léxico del LCM (vector ≈ 0, sin concepto
común). Los que sí lo están ya los resolvía el LCM por su cuenta. Con estos datos, ninguna regla los encuentra sin dejar pasar falsos amigos.

Una regresión que encontré y quité: la primera versión exigía concepto compartido incluso por encima de 0,8 y dejaba fuera «dar»/«ofrecer»
(0,80 sin concepto común); dtest bajaba una pregunta. La regla final es la unión de las dos.

## 5. Preguntas en el entrenamiento: probado y descartado

El corpus casi no tiene preguntas (210 de 28.473 frases). Generé preguntas a partir de frases ya analizadas a mano, moviendo piezas del árbol
(«Rosa compró una imprenta» → «¿Qué compró Rosa?», con su análisis correcto), y reentrené con un 15 % de ellas.

| Examen | Sin preguntas | Con preguntas generadas |
|---|---|---|
| Prensa y web, cabeza y función | 85,6 % | 84,9 % |
| Preguntas reales de español hablado (131) | 63,4 % | 63,4 % |
| Siete textos de la 2.32 | 69 de 72 | 70 de 72 |
| Sistema solar | 17 de 26 | 16 de 26 |

Las preguntas reales habladas («¿Olivo por aquí hay?») no se parecen a las generadas. Sin ganancia clara, me quedo con el analizador
anterior. El código del aumento queda en `entrena.py` por si sirve con otro corpus, pero desactivado.

## 6. Lo que sigue sin resolver

- **Sinónimos que el léxico no tiene.** Hay que aprenderlos: de la conversación (la 2.24 ya permite «defender es lo mismo que proteger») o
  de textos. Sin eso no hay mejora posible por esta vía.
- **Posesivos:** «¿Dónde trabaja el hijo *de Carmen*?» cuando el texto dice «*Su* hijo…».
- **Sistema solar: 14 de 26**, igual que en la 2.32.
- Los pesos de recencia y papel de los pronombres los fijé a ojo con tres textos de desarrollo.

## 7. Siguiente paso que propongo

Aprender sinónimos de lo que se lee y se conversa: cuando dos verbos aparecen con los mismos sujetos y objetos en el grafo, son candidatos a
sinónimo, con una probabilidad que crece con cada coincidencia y que el usuario puede confirmar. Es el «reentrenamiento continuo con los
conceptos de los que ya dispone» que planteabas, aplicado donde ahora falla.

## 8. Instalación y verificación

```
python parche_lcm233.py --aplicar
python -m pytest -q
```

No hay que reentrenar: sirve el analizador que ya entrenaste con la 2.32. Si no lo entrenaste, el LCM funciona como antes.

- Medir: `python -m lab.sintaxis.mide233 -v`
- Apagar piezas: `LCM_SIN_PRONOMBRES=1`, `LCM_SIN_CONCORDANCIA=1`, `LCM_SIN_SINONIMOS=1`
