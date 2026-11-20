# LCM 1.7 — Composición discursiva y evidencia temporal

## Propósito y alcance

El módulo `src/semantics/discourse17.py` complementa a `DialogoConceptual` 1.6. Reconoce **un subconjunto limitado** de frases con coordinación, relativa explicativa, elipsis de sujeto, correferencia pronominal y referencias temporales. La intención es mejorar el flujo **texto → roles conceptuales → memoria / evidencia → razonamiento** sin convertir la cercanía vectorial de dos conceptos en una implicación lógica.

No es un nuevo analizador universal del español, no añade un LLM y no reentrena los pesos de la Escuela o del razonador. Cuando existe una Escuela entrenada se intenta utilizar su extracción de roles mediante la ruta 1.6. El respaldo gramatical se restringe a estructuras reconocibles y se abstiene cuando hay ambigüedad; no define listas cerradas de sinónimos de acciones.

## Cambios

1. **Dos cláusulas, dos roles**: `Ana ayuda a Luis y Luis saluda a Eva.` se descompone en dos proposiciones, con verificación previa de ambas. También admite sujeto compartido (`Ana ayuda a Luis y saluda a Eva.`).
2. **Relativas explicativas sencillas**: `Ana, que vive en Sevilla, ayuda a Luis.` produce una propiedad y una relación principal. No trata todas las subordinadas; las incrustaciones anidadas se rechazan.
3. **Correferencia conservadora**: después de `Ana ayuda a Luis`, `Ella lo saluda` puede relacionarse con el contexto reciente, siempre que el género superficial y los candidatos sean inequívocos. En casos dudosos pregunta y no memoriza.
4. **Tiempo / evidencia**: `Ayer Ana visitó a Luis` se guarda en `memory/lcm_discourse17.json` como declaración de la persona usuaria fechada, **no** como hecho atemporal en `MemoryStore`. `Hoy Ana no visita a Luis` puede convivir con la afirmación de ayer sin contradicción. Declaraciones incompatibles del mismo día se detectan.
5. **Cambios de estado**: `Antes Ana vivía en Madrid, ahora vive en Sevilla` guarda los dos alcances `antes` y `ahora`, con consulta temporal explícita. El método nunca infiere que `antes` sea una fecha absoluta.
6. **Atribución**: `Según Ana, Luis ayuda a Eva` se almacena como afirmación atribuida, sin autorizar que el grafo considere el hecho cierto.
7. **Eventos con nombre común**: `Un pájaro está piando en el jardín` se registra como un **acontecimiento declarado** con un identificador de mención. No se convierte en el hecho genérico `PÁJARO — PIAR`; no se asegura que dos menciones se refieran al mismo animal.
8. **Aislamiento conversacional**: `Nueva conversación` descarta el antecedente pronominal de la sesión anterior, sin borrar hechos aprendidos ni episodios.

**Ejemplo**

```
Ana ayuda a Luis y Luis saluda a Eva.
→ He registrado dos proposiciones...
Si X ayuda a Y y Y saluda a Z, entonces X admira a Z.
→ Regla adquirida (LCM 1.6)
¿A quién admira Ana?
→ Eva. Se deduce por la regla... [premisas]
```

**No inferir sin evidencia**

```
Ayer Ana ayudó a Luis.
Si X ayuda a Y, entonces Y saluda a X.
¿A quién saluda Luis?
→ No consta... (el hecho fechado NO se usa como premisa atemporal)
```

## Esquema de almacenamiento

`memory/lcm_discourse17.json` se crea solo al observar el primer acontecimiento fechado o situado. Registros con `s`, `p`, `o`, `neg`, `tiempo`, `fuente`, `canal=texto_declarado`. No contiene imágenes ni audio ni afirmaciones de que el sistema percibió directamente un sonido. Los conceptos y las identidades del núcleo siguen en sus espacios originales. Se limita a 3.000 eventos recientes por archivo (se conserva el archivo entero hasta guardar nuevos eventos). Las declaraciones incompatibles se conservan y se responde con incertidumbre.

No sustituye el soporte general de memoria temporal de LCM ni su razonador simbólico. No se ejecutan reglas condicionales automáticamente sobre todos los eventos fechados: hacerlo sin semántica de tiempo en las reglas sería incorrecto.

## Evaluaciones ejecutadas en una reconstrucción de los archivos disponibles

| Evaluación | Resultado | Significado |
|---|---:|---|
| 150 tests de regresión dirigidos | 150/150 | Incluyen Visión, Semántica, Episodios, 1.6 y 1.7 |
| Desarrollo semilla 17017 | 1.000/1.000 | 100 tandas de 10; diez familias sintéticas |
| Reserva semilla 99187 | 1.000/1.000 | 100 tandas; identidades y combinaciones distintas |
| Reserva adicional semilla 339187 | 1.000/1.000 | 100 tandas; mismas familias, parámetros distintos |
| Oráculo externo LCM 1.3, 40 frases | 7/40 estructuras persistentes | Frente a 3/40 en 1.6; 0 hechos actuales indebidos, **no** una tasa de comprensión |

La evaluación general del proyecto **NO se ha completado con éxito** en esta copia, porque `src/language/intents_modelo.json` está truncado y faltan los checkpoints originales (`school.pt`). No se ha simulado ni inventado el rendimiento del LCM entrenado en tu Mac. Las series controladas comparten una gramática de generación y no demuestran un 90 % en diálogo humano libre.

## Pruebas e instalación

Desde la raíz de una instalación **LCM 1.6**:

```
python parche_discurso17.py --plan
python parche_discurso17.py --aplicar
python -m pytest -q tests/test_discurso17.py tests/test_dialogo16.py
python -m scripts.evaluar_discurso17 --rondas 100 --semilla 17017 --guardar
python parche_discurso17.py --revertir
```

`--revertir` comprueba que los archivos no se hayan modificado tras la instalación. Nunca elimina `memory/`, `cartuchos/`, `checkpoints/` ni `reports/`. La reinstalación es idempotente. El respaldo de código se guarda fuera de esas carpetas.

## Limitaciones y siguiente investigación

- La resolución de «lo», «la» y «ella» usa una heurística morfológica superficial que falla con nombres de género no inferible; en caso de duda se abstiene.
- El sistema aún no interpreta fiables todos los adjuntos de la Escuela ni oraciones de dependencia larga; necesita una evaluación con `school.pt` real y textos independientes.
- No resuelve en general relativas restrictivas, subordinadas profundas, discursos hipotéticos de múltiples cláusulas, discurso indirecto libre, tres participantes ni relaciones de evento con intervalos completos.
- La memoria temporal guarda testimonios de usuario, **no** verdad física ni percepción directa. Los eventos de audio deben permanecer etiquetados como tales si todavía no existe un reconocedor de sonido validado.
- Una frase intransitiva con sujeto común genera un identificador de mención, evitando universalizar accidentalmente una observación.

Siguiente experimento recomendado: extraer roles y relaciones de un corpus anotado de narraciones de varios turnos con la Escuela entrenada, comparar contra anotaciones independientes y revisar manualmente los falsos hechos antes de seguir ampliando el reconocimiento.
