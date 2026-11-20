# LCM 2.2 · Conceptos de fábrica, capas de abstracción y negativas

## Qué añade

1. **Base de conceptos de fábrica** (`src/nucleo20/conceptos_base.txt`, texto editable; la lee `src/nucleo20/conceptos.py`).
   No contiene hechos del mundo (capitales, personas, fechas): solo conceptos cotidianos y cómo se relacionan.
   - **Taxonomía por capas**: 589 conceptos (gorrión < pájaro < ave < animal < ser vivo; silla < mueble < objeto…).
   - **Propiedades típicas** (202) que se heredan hacia abajo, con **excepciones**: manda la clase más cercana
     («las aves vuelan», «los pingüinos no vuelan»; «los mamíferos no vuelan», «los murciélagos vuelan»).
   - **Negativas explícitas** («los objetos no respiran», «los peces no tienen patas»). De lo que no hay dato, se abstiene.
   - **Partes** (coche: ruedas, motor…), **contrarios** (164 palabras), **efectos de las acciones** (romper → roto, abrir → abierto)
     y **grupos de relaciones** (familia = padre, hermano, tío…; conocidos = amigo, vecino…).
2. **Lo que dice la persona manda sobre lo de fábrica**: «Toby no ladra», «Los kiwis no vuelan», «Algunos pájaros vuelan»
   (esto último se guarda como parcial y no se convierte en regla: «¿Vuelan los pájaros?» → no lo sabe con seguridad).
3. **Preguntas nuevas**: «Dime tres frutas», «¿Qué animales (no) vuelan?», «¿Qué animal ladra?», «¿Qué tienen en común / en qué se
   diferencian X e Y?», «¿Cuál es el contrario de…?», «¿Qué partes tiene…?», «¿Puede volar un pingüino?», «¿Quiénes son mis familiares?»,
   «¿X es de mi familia?», «¿Qué relación tengo con X?». Si se le pregunta por qué, distingue lo que trae de fábrica de lo que se le dijo.
4. **Negativas en la conversación**: «Nadie de mi familia fuma» / «¿Fuma alguien…?», «No bebo ni vino ni cerveza», «¿Quién no tiene coche?»,
   «¿Qué cosas no me gustan?», «Ya no… / ¿Trabajaba…?», correcciones de nombre («No, perdona, se llama Luisa»).
5. **Errores corregidos** encontrados al medir: «mi hermano» y «mi hermana» eran la misma persona; «un loro llamado Paco» nombraba al dueño;
   «¿Es la mesa de Sara azul?» contestaba «es una mesa»; nombres propios tomados por verbo («Sara coleccionó…»).

## Cómo ampliar los conceptos

Edita `src/nucleo20/conceptos_base.txt` (el formato está en su cabecera) y vuelve a pasar `python -m pytest -q tests/test_conceptos22.py`.

## Medidas

Ver `reports/lcm22_medidas.json`. Todas con sesión de fábrica nueva por diálogo y criterios escritos antes de ejecutar.
El examen ciego 3 se escribió con el código congelado y se pasó una sola vez; sus transcripciones no se han usado para corregir.
