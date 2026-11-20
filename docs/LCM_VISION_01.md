<!-- LCM_VISION_01_GENERATED -->
# LCM Vision 0.1 — Percepción cromática

**Objetivo**: PNG/JPEG/WebP predominantemente uniforme -> categoría cromática -> **misma clave conceptual** que el LCM usa en sus hechos -> memoria con procedencia.

## Instalación

`python parche.py --plan` para inspeccionar la limpieza; `python parche.py` para aplicar (pide confirmar los borrados); `python parche.py --si` para aplicar sin preguntas. El parche nunca borra `data/`, `checkpoints/`, `memory/`, `cartuchos/`, `reports/`, `reproducibilidad/`, los exámenes o `tests/test_parche*.py`. Los tests históricos son pruebas de regresión, **no** parches ejecutables. Se eliminan únicamente cachés conocidas, `.parche_backups/` y scripts `parche-*.py`, `parche_*.py`, `parche123.py` de la raíz. Otros sobrantes requieren revisión humana.

`python -m pip install -r requirements-vision.txt`

## Probar

- `python -m scripts.vision mi_verde.png` identifica sin modificar memoria.
- `python -m scripts.vision mi_verde.png --guardar` añade hecho con `source=vision:imagen:<hash>`.
- `python -m scripts.web` y abrir **http://127.0.0.1:8765/**. En la conversación: pulsa el clip o arrastra una imagen, pregunta «¿De qué color es?» y recibe la respuesta. Prueba «Muéstrame un ejemplo de color verde»: aparece una muestra PNG real dentro de los mensajes.
- `python -m pytest -q tests/test_vision_colors.py`
- `python -m scripts.evaluate_colors` genera pruebas RGB, gris y mezcla (sin entrar en datos de entrenamiento).
- **Opcional**: `python -m scripts.train_colors` entrena un MLP a partir de RGB sintético. `python -m scripts.evaluate_colors` lo evalúa en un conjunto separado por semilla.

## Semántica y límites

- Los seis identificadores (ROJO, VERDE, AZUL, AMARILLO, BLANCO, NEGRO) se registran en `MemoryStore` respetando los ya existentes. `asegurar_conceptos_en_espacio(ConceptSpace)` devuelve los vectores existentes, **sin cambiarlos**.
- Un hecho tiene forma `(IMAGEN_<hash>, TENER_COLOR, VERDE)` y su procedencia visual se conserva. La imagen binaria **no se guarda**.
- Modo de producción: regla HSV conservadora; imágenes de dos colores, grises intermedios, turquesa, naranja, violeta, materiales con reflejos y fotografías naturales no tienen reconocimiento fiable y suelen producir abstención.
- `fraccion` es la proporción de píxeles clasificados como color dominante; **no** es una probabilidad calibrada.
- El MLP de entrenamiento sintético **no** es todavía un encoder multimodal entrenado con imágenes reales ni se usa en el chat. Constituye una línea base opcional para el experimento siguiente.
- No modifica el razonador ni realiza reentrenamientos generales.

## Conversación multimodal integrada

- El botón **Adjuntar imagen** junto al cuadro de texto permite PNG, JPEG y WebP de hasta 8 MB; también se puede arrastrar y soltar en la vista **Conversar**. Antes de enviar se muestra una previsualización con opción de quitarla.
- Un mensaje puede contener **imagen**, **texto**, o **ambos**. Se envían en una única llamada a `/api/chat` y se interpreta primero la imagen; una pregunta cromática tiene respuesta en ese mismo turno o en el siguiente.
- «Dame un ejemplo de color verde» responde con una **imagen PNG** que se sirve por `/api/vision/muestra?color=VERDE`. Se representa dentro de la conversación y puede volver a verse tras recargar el historial.
- El historial del navegador guarda solamente el **nombre del archivo adjunto**, nunca los bytes de la imagen del usuario. Los bytes viajan a la API local y solo se conserva el concepto observado y su huella en la memoria.
- `/vision` se redirige al chat por compatibilidad. Las APIs antiguas `/api/vision` siguen disponibles.
- **Límite:** no identifica objetos, no reconoce colores de una región concreta ni describe escenas. No se debe interpretar la fracción de píxeles como una probabilidad calibrada.
