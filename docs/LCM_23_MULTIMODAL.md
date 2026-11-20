# LCM 2.3 · Lo que ve, unido a lo que sabe

## Qué añade

1. **Percepción ampliada** (por reglas auditables, sin modelo entrenado):
   - 11 colores: rojo, verde, azul, amarillo, blanco, negro y, nuevos, naranja, rosa, morado, marrón y gris.
     Entre colores hay zonas muertas: un tono dudoso (turquesa, gris muy claro) no se clasifica.
   - **Formas simples** (`src/vision/formas.py`): círculo, óvalo, cuadrado, rectángulo y triángulo de un color sobre un fondo
     de otro; separa el color de la figura y el del fondo. Lo que no encaja (una estrella) lo dice.
2. **La imagen entra en la conversación** (`src/nucleo20/vista.py`): cada imagen pasa a ser un referente del núcleo.
   - «¿Qué ves?», «¿Qué forma tiene?», «¿Es azul?», «¿Y el fondo?», «¿Cuántos lados tiene?», «¿Es un polígono?».
   - Con los conceptos de fábrica: «¿Qué frutas son de este color?», «¿Podría ser un plátano?» (por el color: no, los plátanos son amarillos),
     «Esto es una fresa» (y si el color no cuadra, lo dice), «¿Es una fruta?».
   - Con lo que cuenta la persona: «Luna es de este color», «Mi coche es de este color», «¿Es del mismo color que mi coche?»,
     «¿Este es el color de Luna?» … «¿Y este?».
   - La imagen deja de ser el tema cuando se habla de otra cosa; sin imagen, no inventa.
3. **Otros arreglos** encontrados al convertir el examen ciego 3 en tanda 9: «su» referido al sujeto («Mi hermano rompió su bici»),
   «treinta y dos», «Tenemos una hija, Vera, de ocho años» (y que Vera sea también hija de la pareja), «¿Tengo algún hijo varón?»,
   «¿Qué mascota tiene…?», «¿Eres un animal?», plurales como «muebles» o «clases», «una gata» en vez de «una gato».

## Límites honestos

- No reconoce objetos en fotos reales: solo colores dominantes y figuras geométricas simples sobre fondo liso.
- «¿Podría ser una fresa?» se responde solo por el color, y lo dice.
