# LCM 1.6 — Composición del diálogo mediante hechos y condiciones

## Propósito

Conectar lenguaje, memoria y razonamiento con pruebas de procedencia, sin reducir el significado de los verbos a comandos rígidos. **No** sustituye el analizador UD de la Escuela ni entrena nuevos embeddings. Un verbo no contenido aún en el catálogo puede adquirir una clave léxica provisional a partir de la flexión, pero una relación entre verbos **no** se da por aprendida por compartir forma o cercanía vectorial.

## Componentes

- `src/semantics/dialogue16.py`: proposiciones tipadas por roles `(sujeto, predicado, objeto, negación)`, adquisición de hechos, contexto de un diálogo y motor de reglas de alcance limitado. Primero intenta usar `SchoolParser.parse` para identificar roles; si no resulta, emplea un **respaldo gramatical conservador** para cláusulas simples, no un modelo universal del español.
- `src/web/motor.py`: conecta el módulo antes de recuperación textual; las preguntas no comprendidas siguen al LCM anterior. Conserva la respuesta habitual para Visión, Semántica y otras tareas.
- `memory/lcm_condicionales16.json`: guarda reglas con fuentes y atribuciones. **No** almacena hechos hipotéticos como reales. Es independiente de `lcm_memory.json`.
- `scripts/evaluar_dialogo16.py`: examen repetible de diez familias de inferencia en tandas de diez, con datos aleatorizados y memoria aislada por caso.
- `tests/test_dialogo16.py`: prueba las propiedades de alcance, anti-inversión, negación, persistencia, roles y la ruta `Motor.chat`.

## Ejemplo

```
Usuario: Si X ayuda a Y, entonces Y saluda a X.
LCM: He aprendido la relación condicional...
Usuario: Ana ayuda a Luis.
LCM: He registrado ese hecho con su procedencia.
Usuario: ¿A quién saluda Luis?
LCM: Ana. Se deduce por la regla «Si X ayuda a Y, entonces Y saluda a X.» a partir de...
Usuario: ¿Por qué?
LCM: Se deduce por la regla ...
```

La conclusión exige una **premisa positiva explícita**; ausencia de afirmación no es negación. Si se registran simultáneamente el hecho positivo y su negación, el motor **suspende la aplicación de reglas** sobre esa premisa hasta aclararla. Si el usuario dice «Ana cree que ...», solo se guarda la atribución, no el supuesto hecho.

Los patrones permitidos de reglas admiten variables `X`, `Y`, `Z`, hasta dos premisas separadas por **y** y una conclusión con variables que aparezcan en alguna premisa. No se admite «else» inferido mediante ausencia de datos, porque eso rompería la lógica de mundo abierto. Negaciones explícitas sí pueden ser premisas. Para impedir explosiones de inferencia, el cierre se limita a tres rondas, 10.000 hechos y un máximo de 1.000 nuevas conclusiones por ronda.

## Evaluación reproducida en la reconstrucción disponible

| Examen | Aciertos | Tandas de diez | Alcance |
|---|---:|---:|---|
| Desarrollo, semilla 1745 | 2.000/2.000 | 200/200 ≥9 | Diez familias sintéticas de relaciones |
| Reserva, semilla 918271 | 2.000/2.000 | 200/200 ≥9 | Distintas identidades, verbos y combinaciones dentro de las mismas familias |
| Regresiones dirigidas del LCM y módulo nuevo | 123/123 | — | Incluye visión, semántica, relaciones, episodios y grounding |

**No son mediciones de la Escuela entrenada**, ni de diálogo humano abierto, ni acreditan precisión del 90 % en español general. La copia disponible no incluye el `school.pt` del Mac del usuario. Se ejecutaron pruebas del grafo y del motor con un analizador sustituto, conservando los fallos previos del LCM completo como asunto pendiente. El banco independiente cambia parámetros dentro de las diez familias; no cambia radicalmente la gramática.

## Comprobación externa adicional: 40 oraciones del oráculo 1.3

En el módulo **aislado y sin Escuela entrenada**, de 40 frases libres anotadas en `oraculo_eventos_es_13.jsonl`, solo **3/40** produjeron una estructura persistente (regla o atribución); **0/40** casos introdujeron un hecho real indebido cuando el oráculo lo prohibía. Este examen NO muestra cobertura suficiente del diálogo abierto: muestra que la capa conservadora se abstiene a menudo. La Escuela neuronal —ausente aquí— deberá evaluarse antes de concluir si el LCM completo interpreta correctamente esas frases.

## Limitaciones conocidas y siguientes experimentos

1. El respaldo gramatical no interpreta oraciones libres largas, relativas, citas complejas, subjuntivo general, deixis múltiple ni acciones con tres argumentos. Las que no reconoce se delegan, si no expresan una condición insegura.
2. La referencia «ella/él» solo se resuelve cuando un antecedente es inequívoco según una heurística superficial. Si hay varias personas posibles, solicita aclaración.
3. La composición de eventos con tiempos y fuentes forma parte de la memoria episódica anterior, pero todavía no está completamente enlazada con todas las inferencias temporales del nuevo motor.
4. La inferencia no depende de similitud coseno por sí sola: una proximidad de embeddings **no es una prueba** de una relación entre entidades.
5. Se debe ampliar el banco con diálogos humanos anotados por personas independientes, múltiples turnos y estructura más amplia. Los 2.000 ejemplos basados en gramática no resuelven la cobertura general.

## Uso

```
python parche_dialogo16.py --plan
python parche_dialogo16.py --aplicar
python -m pytest -q tests/test_dialogo16.py
python -m scripts.evaluar_dialogo16 --n 2000 --semilla 918271
```

El parche tiene `--revertir`, conserva la memoria y los modelos, y bloquea la reversión si los archivos de código instalados se modificaron después de su instalación. No se realizan borrados ni reentrenamientos automáticos.
