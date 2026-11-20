# LCM 2.9 · Construcciones que fallaban en las pruebas ciegas

Parche sobre la 2.8. No se reentrena nada: todo es comprensión de la frase y del diálogo, sin hechos del mundo.

## Método
1. Antes de tocar el código, con la 2.8 congelada, se escribieron dos referencias: `lab/charla50d.py` (una charla de 50 interacciones) y `lab/examen_ciego9.py`. Se midieron sin leer las respuestas.
2. Después se hicieron 7 tandas de unos 10 turnos (`lab/iter29/t01`–`t07`), arreglando los fallos entre una tanda y la siguiente. Tras cada tanda se repasaron todas las tandas anteriores (01–15, iter26–29) y los controles (exámenes del autor y ciegos 2, 6 y 7).
3. Al final, con el código congelado, se hizo **una sola medida** de las dos referencias. Solo después se leyeron las transcripciones.
4. Las transcripciones se auditaron a mano con el mismo criterio para la 2.8 y la 2.9. Un acierto del juez automático pasa a fallo si la frase es falsa, está rota o pierde el dato. Los detalles están en `lab/iter29/auditoria.json`.

## Qué se ha atacado
| Construcción | Ejemplo | Ahora |
|---|---|---|
| Papel con artículo | «Iván, que es el portero» | «Iván es tu vecino y el portero…» |
| Fecha delante | «El domingo es el cumpleaños de mi abuelo» | el suceso es el domingo; «¿Qué hay el viernes?» |
| Color como adjetivo | «unas zapatillas blancas» → «¿de qué color son?» | contesta, también en preguntas de sí o no |
| Aposición con lista | «con dos compañeros, Rafa y Toni» | los nombra; «¿con quién?», «¿cuántos son?» |
| Aposición de SN | «mi tío Andrés, el hermano de mi padre, es fontanero» | dos hechos |
| Dos frases con coma | «estoy agotado, hoy he trabajado doce horas» | dos frases (no parte subordinadas ni correcciones) |
| Elegir por género en un grupo | «mis abuelos, Paco y Juana» → «¿mi abuela?» | Juana |
| Dativo de suceso | «a mi hija le salen los dientes», «se me ha roto el móvil», «se me cayó al suelo» | afectado + cosa + lugar; «¿qué se me ha roto?», «¿dónde se me cayó?» |
| Duración sin «durante» | «fue maestra muchos años» | ya no sale «maestra y año» |
| «lo» por el objeto de un infinitivo | «pensamos comprar un sofá… Lo compraremos en…» | el sofá |
| «Se llama X» tras un suceso | «Mañana es el santo de mi abuela. Se llama Dolores» | la abuela, no el santo |

## Resultados (mismo juez para 2.8 y 2.9)
| Prueba | 2.8 | 2.9 congelada (ciega) | 2.9 tras arreglos (no ciega) |
|---|---|---|---|
| charla50d, juez automático | 52,27 % · 10 falsas | 61,36 % · 7 | 63,64 % · 7 |
| charla50d, auditada | 47,73 % · 12 | 59,09 % · 8 | 63,64 % · 7 |
| examen ciego 9, juez automático | 51,11 % · 1 | 68,89 % · 2 | 75,56 % · 2 |
| examen ciego 9, auditado | 42,22 % · 2 | 57,78 % · 5 | 73,33 % · 2 |
| exámenes del autor | 88,05 % | 88,05 % | 88,05 % |
| ciego 2 / ciego 6 | 93,69 / 80,60 | igual | igual |
| ciego 7 (ya no ciego) | 69,77 % | 76,74 % | 76,74 % |

El primer intento de las 7 tandas dio 54,17 % de acierto con 5 falsas en 72 turnos. Los tres casos en que el juez fue demasiado laxo se corrigieron a mano y están anotados en `primer_intento.json`.

## Lo que queda mal (visto en la auditoría)
- **Género de animales y personas sin pista.** Sale «Nube es blanco» y «Íñigo es bombera».
- **«Mi jefa, que es la dueña, se llama Pilar».** Después no responde «¿cómo se llama mi jefa?».
- **«Vivo con mi pareja y dos gatos, Lupe y Nube».** Los gatos no quedan como grupo nombrado, así que falla «¿cuántos gatos tengo?».
- **Color señalado en una imagen.** «nos gusta este color» con una foto no recoge el color de la imagen.
- **Respuestas de la capa antigua.** Cuando el núcleo 2.0 no entiende, la capa antigua todavía puede soltar frases rotas. La 2.9 tapó el caso concreto («comprarem»), no la causa.
- **La falsa nueva de la ciega se arregló después de verla.** Por eso la cifra de 73,33 % no es ciega.
