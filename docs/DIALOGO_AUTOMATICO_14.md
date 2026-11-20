# LCM 1.4 — Auditoría de diálogo por tandas y barreras de fundamentación

Este parche **no es un sistema autónomo de programación** ni acredita que el LCM
entienda el 90 % del español. Instala cuatro correcciones configurables y un
banco incremental de 2000 preguntas sintéticas para ejecutarlo en el Mac del
usuario, con la Escuela real. Ningún test modifica la memoria personal.

## Barreras comprobables

- `reloj`: una pregunta sobre la hora local pide el reloj del equipo, no texto
  recuperado de un corpus. No intenta resolver automáticamente zonas horarias.
- `edad_hipotetica`: interpreta «Si María nació en 1982, ¿cuántos años tiene?»,
  sin guardar la hipótesis como hecho. Sin día/mes da intervalo, no edad exacta.
- `citas_ajenas`: bloquea una cita que no menciona la persona explícitamente
  solicitada. Es un guardarraíl muy limitado, no verificación de todas las citas.
- `comparacion_sin_prueba`: no confunde una definición de león con demostrar
  que es más fuerte que un unicornio.

No fija listas de sinónimos de acciones ni altera embeddings, ontología, audio,
visión o memorias previas. La inferencia relacional sigue en el razonador.

## Uso

```bash
python parche_dialogo14.py --plan
python parche_dialogo14.py --aplicar
python -m pytest -q tests/test_calidad_dialogo14.py
python -m scripts.iterar_lcm --n 2000 --autorreparar --partir-sin-correcciones --guardar-config
```

- Imprime **cada tanda de 10**, incluyendo casos fallidos.
- Exige 9/10 y comprueba la primera tanda al avanzar.
- Si propone activar una corrección, repite TODAS las tandas aprobadas.
- Si no existe reparación segura, se detiene. **No inventa parches**.
- El último comando guarda flags activadas únicamente tras terminar todas
  las tandas sin suspensos. Hasta entonces la instalación usa las barreras por
  defecto activadas, salvo que exista configuración explícita.
- Los informes se encuentran en `reports/lcm_iteracion14/`.

Para explorar **todo** el banco sin bloquearse en la primera tanda fallida:

```bash
python -m scripts.iterar_lcm --n 2000 --explorar
```

Para un ensayo sin la Escuela de español (el resultado NO evalúa el LCM real):

```bash
python -m scripts.iterar_lcm --n 20 --sin-escuela --explorar
```

Las preguntas se crean mediante plantillas parametrizadas (fechas, nombres,
operaciones, color, negación e identidad), NO son 2000 preguntas humanas
independientes. Las rúbricas son verificables y cada caso tiene criterio. El
porcentaje sólo indica rendimiento en ese banco, y genera hipótesis para una
evaluación posterior independiente. El evaluador no llama a ChatGPT y no
puede escribir nuevos parches con un LLM sin un agente externo.

## Privacidad, reproducibilidad y límites

- Por defecto utiliza una memoria temporal con la semilla de fábrica. Si se
  especifica `--memoria`, lee esa copia de origen pero escribe solo a la
  carpeta temporal y a informes con las respuestas obtenidas. Con
  `--cartuchos cartuchos` monta también los cartuchos, sin modificarlos.
- La base de sentidos puede tener aprendizaje en disco; las conversaciones de
  prueba le asignan un fichero de aprendizaje temporal independiente.
- La Escuela entrenada `checkpoints/school.pt` se requiere para resultados
  integrales. Si falta, el script se niega a presentar un resultado real.
- Las respuestas con hora dependen del reloj y zona horaria del equipo.
- `--revertir` recupera `src/web/motor.py` original; antes de borrar nuevos
  módulos comprueba que sigan intactos. No toca memoria ni checkpoints.
- Los archivos preexistentes y de terceros nunca se eliminan automáticamente.

## Próxima etapa (pendiente, no prometida)

Casos no cubiertos: correferencia entre turnos, conocimiento general contradictorio,
relaciones inversas, contexto epistemológico, atribución a hablantes, seguimiento
de tareas compuestas y fallos de recuperación más sutiles. Requieren análisis y
parches validados en la instalación real, no solo superar plantillas.
