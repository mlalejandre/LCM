# LCM 2.7 · Relativas, elipsis e imágenes dentro de la charla (parche sobre LCM 2.6)

## Protocolo

1. **Referencia nueva antes de tocar nada.** Escribí `lab/charla50b.py` con la 2.6 congelada: una sola conversación de 50 interacciones, 40 puntuables, con los criterios fijados de antemano. La medí una vez, solo el resumen, y no leí las transcripciones hasta la medida final.
   - Advertencia: la charla incluye a propósito los fenómenos que se iban a atacar (relativas, elipsis, listas de nombres, una imagen acompañada de una frase). Que mejore en ella es esperable; los exámenes ciegos de control son los que dicen si los cambios generalizan.
2. **14 tandas de 10 interacciones** (`lab/iter27/t01…t14`, 140 interacciones), corrigiendo después de cada una.
   - El primer intento de cada tanda está en `lab/iter27/primer_intento.json`, con notas en los casos corregidos a mano.
3. **Código congelado.** Después, medida final.

## Resultados (mismo juez para 2.6 y 2.7)

### Charla 50 B

| | 2.6 | 2.7 |
|---|---|---|
| Juez automático | 77,5 % (1 falsa) | **95,0 %** (1 falsa) |
| Auditoría manual (leyendo cada respuesta) | 70,0 %, 4 turnos con algo falso | **90,0 %**, 3 turnos con algo falso |

La auditoría manual suspende los turnos que el juez aprobó aunque contenían algo falso:
- en las dos versiones, «el médico dice que descansaste una semana» (era «que descanse») y el resumen final que lo repite;
- en la 2.6, además, «Pablo nerear Doce».

### Curva de aprendizaje (primer intento de cada tanda)

| Tandas | Turnos | Acierto al primer intento | Falsas |
|---|---|---|---|
| T01–07 | 65 | 60,0 % | 1 |
| T08–14 | 58 | 77,6 % | 3 |

### Control

| Prueba | 2.6 | 2.7 |
|---|---|---|
| Examen ciego 2 (n=301) | 93,36 % | 93,69 % |
| Examen ciego 6 (n=67) | 77,61 % | 79,10 % |
| Examen ciego 7 (n=43) | 69,77 % | 69,77 % |
| Exámenes del autor (n=703) | 88,05 % | 88,05 % |
| Banco generado, validación (n=12 331) | 98,49 % | 98,49 % |
| Charla 50 antigua (ya gastada, solo orientativa) | 85,0 % | 92,5 % |

- Las tandas 1–15 y las de la ronda 2.6 siguen igual: todas al 100 % menos iter26 T11, que se queda en el 90 %.
- Durante la ronda aparecieron dos regresiones y se corrigieron antes de congelar el código:
  - dos fallos nuevos en los exámenes del autor;
  - una caída en la categoría «familia» del banco ciego. Se localizó solo con agregados, sin leer los ítems ciegos.

### Juez más estricto en 2.7

Si una respuesta empieza por «No sé…», nada de lo que diga después aprueba un criterio positivo. Antes, «No sé quién es Pablo» aprobaba «¿Quién es mayor, Pablo o Nerea?».

## Qué entiende ahora

### Oraciones de relativo

| Frase | Se guarda como |
|---|---|
| «Mi novio, que se llama Hugo, es cocinero» | dos hechos |
| «… con Iñaki, que es profesor» | Iñaki es profesor |
| «un restaurante que está en el centro» | el restaurante está en el centro |
| «la alfombra que he comprado» | relativa de objeto: he comprado la alfombra |

### Elipsis y listas

- «Iker tiene diez años, Ane ocho y Jon cinco»
- «Ane juega al fútbol y Jon al baloncesto»
- «Tengo tres sobrinos: Iker, Ane y Jon»
- «Tenemos dos hijos, Pablo y Nerea»

### Género por nombre

- «¿Cómo se llama mi hija?» busca, dentro del grupo, al miembro con ese género.
- Si ninguno consta como tal, lo dice; antes contestaba con el hijo.

### Imágenes dentro de la charla

- «Este es el color de las cortinas» → las cortinas son amarillas.
- «Esta es la alfombra que he comprado» → tu alfombra es roja y redonda.
- «Las paredes las quiero de ese color» → las paredes azules.
- Preguntas nuevas: «¿Qué forma tiene la alfombra?» y «¿Bigotes es del mismo color que mi bici?».

### Referencias

- «Lola me ha invitado a su boda»: «me» es quien habla y «su» es de Lola.
- «conmigo», «para mí».
- «Los saco a pasear»: los perros, no «dos años».
- «Todos sus amigos ya tienen uno»: un móvil.
- «El padre de Mario dice que sí», dicho por su madre: no es quien habla.

### Otros cambios

- Correcciones: «No era mi jefe, era mi jefa».
- Opiniones de quien habla: «Yo creo que es muy pequeño» y «¿Qué opino de Mario?».
- «Tengo dos perros, uno grande y otro pequeño» → «¿Cómo se llama el perro pequeño?».
- Tiempo:
  - «abro todos los días menos los domingos»;
  - «tres veces por semana»;
  - «hasta las cuatro» y «desde hace cinco años»;
  - «viene el viernes» es el próximo viernes;
  - «este verano», dicho en noviembre, es el próximo.
- Preguntas sobre un infinitivo: «¿Adónde / con quién quiero ir?», «¿Qué estoy aprendiendo?».
- Otras preguntas: «¿Con quién vivo?» a partir de «Carmen vive conmigo», y «¿Mi abuelo vive?» a partir de «murió».

## Lo que sigue fallando (charla 50 B)

- «Me duele bastante» → «te duele daño»: toma por objeto el «daño» de la frase anterior.
- «Que descanse una semana» (subjuntivo) → «descansaste»: el subjuntivo en el estilo indirecto se lee como pasado.
- «Lo pintaremos el mes que viene» (clítico más futuro de 1.ª plural) no se entiende.
- «Este es el color que le gusta a Rocío» con imagen: describe el color, pero no guarda que a Rocío le gusta.
- «¿Me recomiendas algo para la rodilla?»: no da consejos. Es coherente con no tener conocimiento del mundo, pero podría decirlo mejor.

## Cómo repetir

```
python -m lab.charla50b          # referencia 2.7
python -m lab.iter27.correr N    # N = 1..14
python -m lab.examen_ciego2|6|7
python -m lab.examenes_usuario
python -m lab.medir lcm27 12 1,2,3,4,5
```
