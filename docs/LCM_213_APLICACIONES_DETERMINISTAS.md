# LCM 2.13 · Aplicaciones deterministas: el LCM orienta, las aplicaciones calculan

Idea de la ronda (Marcos): «2 más 5 igual a siete se debe ejecutar a través de un programa para ejecutar sumas, no desde la memoria del
modelo; el modelo solamente debe orientar el registro hacia esa operación, recoger el resultado y mostrarlo al usuario», con una
estructura de aplicaciones paralela al LCM, sincronizada con él, que pueda crecer al mismo ritmo.

## 1. Arquitectura

```
frase ──► LCM (núcleo 2.0)                                   src/apps (aplicaciones)
          · numerales → cifras (numerales.py)               registro.py  ← registra(App(...))
          · reconoce operación y datos con el LÉXICO  ◄──── léxico, precedencia, versión, ejemplos
            que declara cada aplicación (calculo.py)
          · arma un árbol de llamadas ──────────────────►   registro.ejecuta(nombre, *args) → (valor, traza)
          · recoge valor y traza, lo dice  ◄────────────    mates.py · calendario.py · dibujo.py
          · «¿cómo lo has calculado?» → enseña la traza
```

- **`src/apps/`**: paquete independiente. Cada aplicación declara nombre, familia, función, aridad, símbolo, precedencia,
  léxico (operador, verbo, sustantivo, prefijo, sufijo, verbos de problema…), el concepto bajo el que entra en la base del LCM,
  ejemplos y versión. Hay 17 aplicaciones:
  - aritmética (exacta, con fracciones): suma, resta, multiplicación, división, potencia, raíz, porcentaje, media, doble, triple,
    mitad, diferencia, mayor y menor;
  - calendario: día de la semana y reloj;
  - dibujo: figuras en SVG.
- **`registro.ejecuta`** es la única puerta por la que el LCM obtiene un resultado. Los errores de dominio (dividir entre cero, raíz
  de un negativo) los explica la aplicación.
- **El LCM no lleva tablas de operadores**: `calculo.lexico()` las construye desde el registro y las rehace cuando cambia la huella
  del manifiesto. Una aplicación nueva con su léxico queda entendida sin tocar el LCM. La prueba
  `test_app_nueva_se_entiende_sin_tocar_el_lcm` registra «módulo» y el LCM contesta «17 módulo 5».
- **Sincronía:**
  - `src/apps/manifiesto.json` guarda lo acordado (léxico, versiones, ejemplos) con su huella;
  - `tests/test_apps_sincronia.py` falla si el manifiesto no está al día, si una aplicación no tiene léxico, ejemplos o concepto en
    la base de fábrica, o si un ejemplo no sale por el LCM completo;
  - `test_el_lcm_no_calcula_de_memoria` cambia la aplicación de suma para que dé 999: el LCM dice 999.
  - Tras cambiar una aplicación: `python -m src.apps.manifiesto`.
- Las cuentas que el núcleo ya hacía con datos de la charla («¿cuántos hermanos tengo en total?», «¿cuántos años nos llevamos?»)
  pasan ahora por las aplicaciones `suma` y `diferencia`, y su justificación lo dice.
- Conceptos de fábrica nuevos: cálculo > operación matemática > suma, resta, multiplicación…; programa > aplicación de dibujo.

## 2. Lo que entiende

- **Expresiones** con precedencia y paréntesis, números con cifras o con palabras («doscientos treinta», «mil menos uno»,
  «tres coma cinco»), decimales con coma y símbolos (+ − × ÷ / * ^ %). Se leen de varias formas:
  - con verbo: «suma 230 y 120», «resta 18 a 50»;
  - con sustantivo: «el resultado de la suma entre 230 y 420», «el producto de 9 y 12»;
  - con prefijo: «el doble de», «la raíz cuadrada de», «el 15 % de», «la media de 4, 8 y 12».
- **Seguir con el resultado anterior:** «¿y si le resto 50?», «¿y el doble?», «y eso por 10».
- **Problemas de enunciado**, por la situación:
  - cadenas de sumas y restas según los verbos del enunciado (me dan, se gastó, bajan, suben…), que salen del léxico de las
    aplicaciones;
  - «6 filas de 8 huevos»;
  - el precio de la unidad;
  - el reparto «a cada uno»;
  - «los dos juntos»;
  - «dentro de 5 años» / «hace 3 años».
- **Suposiciones con comparación** (`comparativos.py`):
  - «si un conejo es más grande que una liebre, ¿la liebre será más pequeña o más grande?»;
  - «¿quién es la menor?».
  - Cada adjetivo es un sentido sobre una escala (grande +, pequeño − en «tamaño»). El orden es transitivo y no hace falta saber nada
    del mundo. Sin la suposición («¿un conejo es más grande que una liebre?») sigue sin saberlo.
- **Calendario y reloj supuestos:** «si hoy es viernes, ¿qué día fue ayer?», «sale a las 10 y tarda 3 horas».
- **Órdenes de dibujar, pintar y mostrar** (`dibujar.py`):
  - figuras (círculo, cuadrado, triángulo, rectángulo, estrella, rombo, pentágono, hexágono, óvalo, línea, corazón), con color y
    cantidad, y muestras de color;
  - la imagen va en el campo `imagen` de la respuesta (SVG + `data:` URL);
  - recuerda lo dibujado;
  - si se pide algo que no sabe dibujar («un perro»), lo dice;
  - «haz la cama», «enséñame a cocinar» o «pinto cuadros los domingos» no son órdenes de dibujo.
- **De paso:** listas de tres elementos con coma y un complemento al final («tengo un perro negro, una gata blanca y dos peces»,
  «en mi calle hay una farmacia, dos bares y un mercado»), que la capa antigua tomaba por una «solicitud visual ambigua».

## 3. Método y resultados

Referencias ciegas (charla50h, examen_ciego13) escritas y medidas con la 2.12 congelada, sin leer sus respuestas.

| Prueba | 2.12 auditada | 2.13 ciega, auditada |
|---|---|---|
| charla50h (50) | 44,0 % · 8 falsas | **100 % · 0 falsas** |
| examen_ciego13 (38) | 44,7 % · 8 falsas | **97,4 % · 1 falsa** |

Auditoría a mano, con los mismos criterios en las dos versiones:
- En la 2.12 dos aprobados eran laxos: «Es una condición…» pasó porque contenía «una»; «Una camiseta dibujar Dos Circulos».
- Dos criterios eran demasiado estrictos: «En ese caso, sí, la bici es más lenta» es correcto.
- En la 2.13 leí las 88 respuestas: todas correctas salvo una falsa real («¿cuántos primos tengo en total?» → «Tienes 3 primas»).
  Después de la medida (no ciega) arreglé el género de «primas» y la concordancia «una estrella…, hecha»: 100 % / 100 %.

Un 100 % en charla50h pide desconfianza: la escribí yo y cubre lo que tenía previsto construir. El banco y la variación de semillas
la complementan, pero un examen ciego escrito por otra persona sería la prueba de verdad.

Banco de entrenamiento `lab/banco_mates213.py`:
- 51 plantillas × números al azar, a veces dichos con palabras; el resultado lo calcula el corrector, no el LCM.
- Primera pasada: 95,4 % con 3 falsas. Una era grave: perdía un paréntesis pegado a un numeral.
- Tras los arreglos: 100 % con 4 semillas distintas (204 frases cada una).
- Es de desarrollo, no ciego.

Otros resultados:
- Controles iguales: autor 88,05 %, ciego2 94,35 %, ciego6 80,60 %, ciego7 76,74 %.
- Tandas iter213 (5, 67 interacciones): primer intento corregido 97,0 %. Informa poco porque se escribieron con el enrutador ya
  avanzado.

## 4. Lo que queda mal

- **Las regresiones iter26 t11, iter28 t23 e iter210 t01** (un caso cada una) fallan igual con el código 2.12 congelado: no las
  provoca esta ronda, y queda investigarlas.
- **Los problemas de enunciado se reconocen por situaciones típicas**, no por comprensión general. Un problema de dos pasos con
  distinta estructura (p. ej. «tengo el triple de cromos que Ana, que tiene 4 más que Luis…») no se entiende.
- **Las edades a partir de la fecha de nacimiento** aún las calcula el núcleo, no una aplicación de calendario.
- **Formato:** potencias como «7^2», y el signo negativo del resultado con guion («-4»).
- **Dibujo:** solo figuras geométricas y muestras de color. No compone escenas («un círculo dentro de un cuadrado»).
