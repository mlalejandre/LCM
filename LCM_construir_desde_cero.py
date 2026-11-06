"""LCM: construir el proyecto DESDE CERO (generado por scripts/empaquetar_todo.py el 2026-11-06).

Uso, en una carpeta vacia (o en la del proyecto tras limpieza.py):
    python LCM_construir_desde_cero.py              # escribe 119 archivos y abre un MENU guiado:
                                                    #   1 entorno e instalacion · 2 tests · 3 verificar codigo · 4 reentrenar todo
                                                    #   5 comparar resultados · 6 hablar con el modelo · 7 todo en orden
    python LCM_construir_desde_cero.py --sin-menu   # solo escribe los archivos (copias en .parche_backups/ si cambian)
    python LCM_construir_desde_cero.py --todo --libro tu_texto.txt [--rapido] [--semilla N]   # sin preguntar nada
(11 ficheros de tests unitarios). Guia completa: docs/REPRODUCIR.md
"""
import base64, datetime, sys
from pathlib import Path

FILES = {
    '.github/workflows/ci.yml': r'''name: tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install torch --index-url https://download.pytorch.org/whl/cpu
      - run: pip install numpy tqdm pytest
      - run: python -m pytest -q tests
''',
    '.gitignore': r'''__pycache__/
*.pyc
.venv/
venv/
.parche_backups/
.pytest_cache/
# datos descargados o con derechos de autor: cada persona los obtiene (ver README)
data/ud/
data/libro.txt
data/libro_vocab.json
*.rtf
regenta.txt
# modelos entrenados y memoria personal (se regeneran)
checkpoints/*.pt
memory/
reports/reproduce_*.log
reports/libro_*.txt
_archivo/
reports/libro_hechos.txt
reports/informe.txt
checkpoints/school.pt.bak
''',
    'LCM_EVOLUCION.md': r'''# Evolucion del LCM: tres iteraciones

Este parche prepara una base experimental mas rigurosa. No afirma que el LCM
haya alcanzado razonamiento general: eso debe demostrarse con los resultados.

## Iteracion 1 — Ontologia con estructura semantica explicita

`ConceptSpace` compone cada vector a partir de rasgos declarados y codifica las
proposiciones con roles diferenciados (sujeto, predicado y objeto). Los textos
ES/EN quedan como verbalizaciones, no como fuente oculta de los vectores.

**Limite:** sigue siendo una ontologia diseñada manualmente. Para aproximarse a
semantica abierta y amplia habra que alinear estos vectores con datos externos,
un encoder multilingue o un procedimiento contrastivo; este parche no descarga
ni presupone modelos externos.

## Iteracion 2 — Generalizacion composicional

`prepare_concepts` crea proposiciones con entidades variables y divide los
datos en train/validacion/test. En transitividad, cada par ordenado de conclusion
pertenece a un unico split y las premisas proceden solo de pares train: las
conclusiones de validacion/test no se entrenan como objetivos ni se filtran
como entradas de entrenamiento. Otras reglas reservan instancias completas
para validacion y test.

El Transformer ahora recibe una mascara de padding y selecciona la ultima
posicion valida. El entrenamiento usa validacion y early stopping. La metrica
neuronal se informa; no se fuerza un umbral ni se presenta como razonamiento
probado.

## Iteracion 3 — Evaluacion y referencia simbolica

`RuleEngine` incorpora reglas auditables de transitividad, caida, fusion con
condicion de fundibilidad y cardinalidad. La no numerabilidad exige evidencia
explicita de ausencia de biyeccion con los naturales; ser infinito por si solo
no basta.

`evaluate_reasoner` mide similitud coseno y top-1 entre objetivos de test, y
ademas ejecuta pruebas del motor simbolico con entidades nuevas. La similitud
coseno es una distancia/alineacion geometrica, no una probabilidad calibrada.

## Orden de ejecucion

```bash
python -m scripts.prepare_concepts
python -m scripts.train_reasoner
python -m scripts.evaluate_reasoner
python -m scripts.think
```

Revisa `data/dataset_manifest.json` y `reports/lcm_evaluation.json` antes de
interpretar los resultados. Si la evaluacion neuronal es baja, no la ocultes:
usa el fallo como señal para revisar la composicion, los rasgos, los ejemplos o
la arquitectura.
''',
    'LICENSE': r'''MIT License

Copyright (c) 2026 Contribuidores del proyecto LCM

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
''',
    'Makefile': r'''.PHONY: install test data reproduce quick think manifiesto verificar desde-cero
install:
	python -m pip install -r requirements.txt
check:
	python -m scripts.check
test:
	python -m pytest -q tests
data:
	python -m scripts.get_data
reproduce:
	python -m scripts.reproduce
quick:
	python -m scripts.reproduce --rapido
think:
	python -m scripts.think
manifiesto:
	python -m scripts.manifiesto --guardar
verificar:
	python -m scripts.manifiesto --verificar --metricas
desde-cero:
	python -m scripts.empaquetar_todo
''',
    'README.md': r'''# Large Conceptual Model (LCM)

Un modelo pequeno que **aprende espanol y conversa sin usar ningun LLM**: entiende frases (una "escuela" de sintaxis
entrenada con Universal Dependencies), guarda lo que aprende como proposiciones (sujeto, relacion, objeto), razona sobre
ello con un nucleo en espacio conceptual, aprende reglas nuevas al vuelo, "duerme" para consolidar y responde preguntas.

> Estado: investigacion en marcha. Todo se mide con criterios fijados antes (ver `reports/RESULTADOS.md`, que incluye
> lo que NO funciona todavia).

## Que puedes hacer

```
python -m scripts.think
> Marta escribió una novela.          # aprende una frase normal
> ¿Quién escribió una novela?         # contesta: Marta escribió una novela.
> Si X es padre de Y entonces Y es hijo de X
> AYUDA                               # lista de comandos
```

## Ejemplo de sesion (preguntas)

```
> Marta escribió una novela.        # [oido] Entendido: MARTA ESCRIBIR NOVELA
> Luis no come carne.               # se guarda como hecho negado
> ¿Quién escribió una novela?       # Marta escribió una novela.
> ¿Qué escribió Marta?              # Marta escribió una novela.
> ¿Come Luis carne?                 # No. No es cierto que luis come carne.
> ¿Vive Pedro en Madrid?            # No lo sé.   (no inventa: dice que no lo sabe)
```
Tambien contesta "Lo deduzco: ..." cuando una regla aprendida (`Si ... entonces ...`) permite concluir la respuesta.
Esa parte funciona en `think`, pero no esta medida todavia en los tests.

## Reproducirlo desde cero

Necesitas Python >= 3.10, `git` e internet (una vez). Funciona en CPU, CUDA o Mac (MPS).

```
git clone <este repositorio> && cd LCM
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m pytest -q tests                      # comprobacion rapida (no necesita datos)
python -m scripts.reproduce --libro mi_texto.txt
```

`mi_texto.txt` es cualquier texto largo en espanol (una novela de dominio publico, por ejemplo). **No** se incluye ningun
libro. El oido usa ese texto para aprender vocabulario y estilo; el proyecto no depende de un libro concreto.
`reproduce` ejecuta, en orden y parando si algo falla: conceptos -> razonador -> evaluacion -> lectura del texto ->
preentrenamiento -> oido -> descarga de UD -> escuela -> test de conversacion -> test de preguntas -> evaluaciones de
aprendizaje online / sueno. Tarda de decenas de minutos a horas segun la maquina. `--lista` muestra los pasos,
`--rapido` salta los opcionales, `--desde paso` continua donde fallo. Cada paso tambien se puede lanzar suelto
(`python -m scripts.train_school`).

Tus numeros no seran identicos a los de `reports/RESULTADOS.md` (semillas, hardware): lo que debe cumplirse son los
criterios impresos al final de cada evaluacion (`CUMPLE` / `NO CUMPLE`).

Guia completa de reproducibilidad (carpeta vacia -> mismo proyecto, manifiesto con huellas, semillas): `docs/REPRODUCIR.md`.

## Estructura

- `src/ontology`, `src/model`, `src/reasoning`: espacio conceptual, razonador, motor de reglas.
- `src/language`: oido, escuela (UD), extractor de proposiciones, preguntas y respuestas (`qa.py`).
- `src/memory`: memoria, esquemas, ciclo de sueno, negativos.
- `src/training`: aprendizaje online con canario y vacunas.
- `scripts/`: entrenamiento, evaluaciones y `think` (la conversacion).
- `data/frases_prueba.tsv`, `data/preguntas_prueba.tsv`: tests escritos a mano. Anade los tuyos con el mismo formato.
- `tests/`: pruebas unitarias sin datos. `LCM_EVOLUCION.md`: historia del diseno. `docs/ESTADO.md`: estado actual, mapa del codigo y plan.
- `python -m scripts.clean`: limpieza segura (ensayo por defecto).

## Datos y licencias

Codigo: MIT (`LICENSE`; cambia el titular si procede). Corpus UD: GSD (CC BY-SA 4.0) y AnCora (CC BY 4.0), se descargan con
`python -m scripts.get_data` y no se redistribuyen aqui. Los textos que aportes son tuyos.
''',
    'configs/__init__.py': r'''''',
    'configs/config.py': r'''from dataclasses import dataclass
import torch


def default_device() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


@dataclass
class LCMConfig:
    d_concept: int = 128
    n_layers: int = 4
    n_heads: int = 4
    max_concept_seq: int = 4
    dropout: float = 0.05
    device: str = default_device()


@dataclass
class TrainConfig:
    batch_size: int = 64
    learning_rate: float = 3e-4
    epochs: int = 40
    checkpoint_dir: str = "checkpoints"
    device: str = default_device()
    patience: int = 8
    grad_clip: float = 1.0
''',
    'data/cantidad_ciegas.tsv': r'''# TEST CIEGO bloque B parte 2 (frases distintas), escrito ANTES de medir. Criterio: >= 60 %.
H: Todos los gatos son animales.
H: Algunos peces nadan.
H: Un salmón es un pez.
H: Ninguna piedra es animal.
P: ¿Es un gato un animal?	SI
P: ¿Nadan los peces?	NOSE
P: ¿Nada un salmón?	NOSE
P: ¿Es una piedra un animal?	NO

H: Rosa tiene dos hermanos.
H: Juan ama a Sara.
H: Juan ama a Rosa.
P: ¿Cuántos hermanos tiene Rosa?	dos
P: ¿A cuántas personas ama Juan?	2

H: Sara es más baja que Rosa.
H: Rosa es más baja que Clara.
P: ¿Es Sara más baja que Clara?	SI
P: ¿Es Clara más baja que Sara?	NO
P: ¿Quién es más baja que Clara?	rosa

H: Rosa normalmente cena a las nueve.
P: ¿Cuándo cena Rosa?	nueve

H: Sara sonríe porque tiene un regalo.
H: Juan se fue porque llovía.
P: ¿Por qué sonríe Sara?	tiene un regalo
P: ¿Sonríe Sara?	SI

H: El coche está delante de la casa.
H: Juan trabaja cerca de Madrid.
P: ¿Dónde está el coche?	delante de la casa
P: ¿Dónde trabaja Juan?	cerca de Madrid
''',
    'data/cantidad_prueba.tsv': r'''# TEST DE BLOQUE B (parte 2): cuantificadores, numeros, comparaciones, frecuencia/hora, causa, lugar relativo.
# Escrito antes de medir. Criterio fijado antes: >= 70 %.
H: Todos los perros son animales.
H: Algunos pájaros vuelan.
H: Una gaviota es un pájaro.
H: Ninguna rana es mamífero.
P: ¿Es un perro un animal?	SI
P: ¿Vuelan los pájaros?	NOSE
P: ¿Vuela una gaviota?	NOSE
P: ¿Es una rana un mamífero?	NO
P: ¿Quién vuela?	pájaros

H: Ana tiene tres hijos.
H: Pedro tiene un perro.
P: ¿Cuántos hijos tiene Ana?	tres
P: ¿Tiene Ana tres hijos?	SI
P: ¿Cuántos hijos tiene Pedro?	NOSE

H: Ana ama a Luis.
H: Ana ama a Pedro.
H: Ana ama a Marta.
P: ¿A cuántos ama Ana?	3
P: ¿Quién ama a Luis?	ana

H: Luis es más alto que Pedro.
H: Pedro es más alto que Juan.
P: ¿Es Luis más alto que Pedro?	SI
P: ¿Es Luis más alto que Juan?	SI
P: ¿Es Pedro más alto que Luis?	NO
P: ¿Es Juan más alto que Luis?	NO
P: ¿Quién es más alto que Juan?	pedro

H: Ana siempre llega tarde.
H: Pedro come a las tres.
P: ¿Cuándo llega Ana?	siempre
P: ¿Cuándo come Pedro?	las tres
P: ¿Llega Ana siempre?	SI

H: Ana llora porque está triste.
H: Pedro compró pan porque tenía hambre.
P: ¿Por qué llora Ana?	está triste
P: ¿Por qué compró Pedro pan?	tenía hambre
P: ¿Llora Ana?	SI
P: ¿Está triste Ana?	NOSE

H: El libro está encima de la mesa.
H: Ana vive lejos de Madrid.
P: ¿Dónde está el libro?	encima de la mesa
P: ¿Está el libro encima de la mesa?	SI
P: ¿Está el libro debajo de la mesa?	NOSE
P: ¿Dónde vive Ana?	lejos de Madrid
''',
    'data/coherencia_ciega.tsv': r'''# TEST CIEGO de coherencia (frases distintas), escrito ANTES de medir. Criterio: >= 60 %.
HOY: 2026-11-06
U: Marta trabaja en Bilbao.	entendido
U: Marta trabaja en Sevilla.	antes
U: ¿Dónde trabaja Marta?	sevilla
U: ¿Dónde trabajaba Marta?	bilbao

U: Juan vive en París.
U: Juan ya no vive en París.	pasado
U: ¿Vive Juan en París?	no
U: ¿Dónde vivía Juan?	París

U: El coche es nuevo.
U: El coche es viejo.	cuál
U: La anterior	anterior
U: ¿Cómo es el coche?	nuevo

U: Rosa está triste.
U: Rosa está contenta.	antes
U: ¿Cómo está Rosa?	contenta

U: Clara compra leche.
U: Clara no compra leche.	cuál
U: La nueva	nueva
U: ¿Compra Clara leche?	no

U: Pedro bebe agua.
U: ¿Qué bebe Pedro?	agua
U: ¿De dónde sale eso?	dijiste
U: Luis cree que Pedro bebe vino.
U: ¿Qué cree Luis?	vino
U: ¿Cómo sabes que Pedro bebe vino?	no lo sé
''',
    'data/coherencia_prueba.tsv': r'''# TEST DE COHERENCIA (bloque D): cambio de estado, contradicciones, "¿como lo sabes?". Escrito antes de medir. Criterio fijado antes: >= 70 %.
HOY: 2026-11-06
U: Ana vive en Madrid.	entendido
U: Ana vive en Sevilla.	antes
U: ¿Dónde vive Ana?	sevilla
U: ¿Dónde vivía Ana?	madrid
U: ¿Vive Ana en Madrid?	no me consta

U: Pedro trabaja en un banco.	entendido
U: Pedro ya no trabaja en un banco.	pasado
U: ¿Dónde trabaja Pedro?	no lo sé
U: ¿Dónde trabajaba Pedro?	banco

U: La casa es grande.	entendido
U: La casa es pequeña.	cuál
U: La nueva	nueva
U: ¿Cómo es la casa?	pequeña

U: Luis ama a Ana.	entendido
U: Luis no ama a Ana.	cuál
U: La anterior	anterior
U: ¿Ama Luis a Ana?	sí

U: Marta es alta.	entendido
U: Marta es baja.	cuál
U: Las dos	las dos

U: Pedro compró pan ayer.
U: ¿Qué compró Pedro?	pan
U: ¿Cómo lo sabes?	dijiste
U: ¿Cómo sabes que Pedro compró pan?	dijiste
U: Marta dice que Luis llegó.
U: ¿Cómo sabes que Luis llegó?	no lo sé
U: ¿Qué dice Marta?	Luis llegó

U: Los polígonos tienen lados.
U: Un triángulo es un polígono.
U: ¿Tiene un triángulo lados?	deduzco
U: ¿Cómo lo sabes?	deduje

U: Ana vive en Madrid.
U: Ana trabaja en Sevilla.	!antes
U: ¿Dónde vive Ana?	madrid
''',
    'data/conceptos_prueba.tsv': r'''# TEST DE CONCEPTOS NUEVOS desde lenguaje natural (Fase 3, paso 1), escrito antes de medir. Criterio fijado antes: >= 75 %.
# Definiciones ("X es un Y"), jerarquias con deduccion (A es B, B es C => A es C), acciones como concepto ("Cocinar es una accion") y propiedades con numeral.
H: Un triángulo es una figura.
H: Un cuadrado es una figura.
H: Un perro es un animal.
P: ¿Qué es un triángulo?	figura
P: ¿Es un cuadrado una figura?	SI
P: ¿Es un perro una figura?	NOSE
P: ¿Qué es un perro?	animal

H: Un triángulo es un polígono.
H: Un polígono es una figura.
P: ¿Es un triángulo una figura?	SI
P: ¿Qué es un triángulo?	poligono
P: ¿Es una figura un triángulo?	NOSE

H: Cocinar es una acción.
H: Correr es una acción.
H: Un círculo es una figura.
P: ¿Qué es cocinar?	accion
P: ¿Es correr una acción?	SI
P: ¿Es cocinar una figura?	NOSE
P: ¿Qué es un círculo?	figura

H: Un triángulo tiene tres lados.
H: Un cuadrado tiene cuatro lados.
P: ¿Qué tiene un triángulo?	tres
P: ¿Tiene un cuadrado cuatro lados?	SI
P: ¿Tiene un triángulo cuatro lados?	NOSE
''',
    'data/correcciones_prueba.tsv': r'''# TEST DE CORRECCIONES (Fase 2), escrito antes de medir.  TEACH = frase<TAB>s|p|o que se ensena con ENTENDI.  TEST = frases NUEVAS (misma pauta) con su lectura correcta.
# Criterios fijados antes: (1) las 3 frases ensenadas quedan bien; (2) >= 50 % de las TEST bien (relajado) y mas que antes de ensenar;
# (3) sin regresion: conversacion (80) no baja mas de 1,25 puntos y largas ciegas (27) no baja mas de 3,7 puntos (una frase).
TEACH	Andrés cocina pasta.	andres|cocinar|pasta
TEACH	Lucía cocina arroz.	lucia|cocinar|arroz
TEACH	El perro muerde al cartero.	perro|morder|cartero
TEST	Carlos cocina pollo.	carlos|cocinar|pollo
TEST	Marta cocina sopa.	marta|cocinar|sopa
TEST	Álvaro cocina pescado.	alvaro|cocinar|pescado
TEST	Irene cocina verduras.	irene|cocinar|verduras
TEST	Mario cocina carne.	mario|cocinar|carne
TEST	El gato muerde al ratón.	gato|morder|raton
TEST	La serpiente muerde al niño.	serpiente|morder|nino
TEST	El perro muerde la pelota.	perro|morder|pelota
# TEST2 = frases NUEVAS anadidas ANTES de repetir la medida tras la primera (que fallo (1) y (3)); sirven para no ajustar solo a las 8 de TEST.
TEST2	Gabriel cocina lentejas.	gabriel|cocinar|lentejas
TEST2	Sara cocina tortilla.	sara|cocinar|tortilla
TEST2	Hugo cocina huevos.	hugo|cocinar|huevos
TEST2	Paula cocina patatas.	paula|cocinar|patatas
TEST2	La vaca muerde la hierba.	vaca|morder|hierba
TEST2	El lobo muerde al pastor.	lobo|morder|pastor
TEST2	El caballo muerde la manzana.	caballo|morder|manzana
TEST2	El tigre muerde al domador.	tigre|morder|domador
''',
    'data/dataset_manifest.json': r'''{
  "schema_version": 2,
  "d_concept": 128,
  "max_premises": 4,
  "concepts": 492,
  "propositions": 13869,
  "samples": {
    "train": 20121,
    "val": 1306,
    "test": 1706
  },
  "split_policy": "Transitivity: target pair sets the split; both premise pairs must belong to train, preventing val/test target edges from appearing as training inputs. Other rules hold out complete entity instances.",
  "semantic_note": "Explicit feature ontology with role-bound proposition vectors; not pretrained language semantics."
}''',
    'data/definiciones_ciegas.tsv': r'''# TEST CIEGO DE DEFINICIONES (bloque E). Escrito antes de medir. Criterio fijado antes: >= 60 %.
HOY: 2026-11-06
U: Lucía tiene una bicicleta.	entendido
U: Bici significa bicicleta.	vale
U: ¿Tiene Lucía una bici?	sí
U: ¿Quién tiene una bici?	lucía

U: Alto es lo opuesto de bajo.	vale
U: ¿Es alto lo contrario de bajo?	sí
U: La torre es alta.	entendido
U: La torre es baja.	cuál

U: Una tijera sirve para cortar.	entendido
U: Una escoba se utiliza para barrer.	entendido
U: ¿Para qué sirve una escoba?	barrer
U: ¿Qué sirve para cortar?	tijera

U: Un delfín es un animal marino.	entendido
U: ¿Cómo es un delfín?	marino
U: ¿Es un delfín un animal?	sí

U: Correr es andar deprisa.	vale
U: Marta corre.	entendido
U: ¿Qué es correr?	andar deprisa

U: Un bolígrafo es un instrumento que sirve para escribir.	entendido
U: ¿Qué es un bolígrafo?	instrumento
U: ¿Para qué sirve un bolígrafo?	escribir
''',
    'data/definiciones_prueba.tsv': r'''# TEST DE APRENDER CONCEPTOS POR DEFINICION (bloque E). Escrito antes de medir. Criterio fijado antes: >= 70 %.
HOY: 2026-11-06
U: Pedro tiene un coche.	entendido
U: Un coche es lo mismo que un automóvil.	vale
U: ¿Tiene Pedro un automóvil?	sí
U: Auto es sinónimo de coche.	vale
U: ¿Tiene Pedro un auto?	sí
U: ¿Quién tiene un automóvil?	pedro

U: Ruidoso es lo contrario de silencioso.	vale
U: ¿Es ruidoso lo contrario de silencioso?	sí
U: La calle es ruidosa.	entendido
U: La calle es silenciosa.	cuál

U: Un tenedor sirve para comer.	entendido
U: Un martillo se usa para clavar clavos.	entendido
U: ¿Para qué sirve un tenedor?	comer
U: ¿Qué sirve para comer?	tenedor
U: ¿Para qué se usa un martillo?	clavar

U: Cocinar es preparar comida con calor.	vale
U: Pedro cocina pasta.	entendido
U: ¿Prepara Pedro pasta?	sí
U: ¿Qué es cocinar?	preparar comida con calor
U: ¿Prepara Pedro pan?	no

U: Un gorrión es un pájaro pequeño.	entendido
U: ¿Cómo es un gorrión?	pequeño
U: ¿Es un gorrión un pájaro?	sí

U: ¿Qué es un tenedor?	explicas
U: Un tenedor es un cubierto que sirve para comer.	entendido
U: ¿Qué es un tenedor?	cubierto

U: Ana vive en Madrid.
U: Ana vive en Sevilla.
U: ¿Dónde vivía Ana?	vivía

U: La casa es grande.
U: ¿Cómo es la casa?	grande
U: ¿Cómo lo sabes?	dijiste
''',
    'data/dialogo_ciego.tsv': r'''# TEST CIEGO DE CONVERSACION (bloque A): frases distintas a las de dialogo_prueba.tsv, escritas ANTES de medir. Criterio: >= 60 % (es mas duro).
HOY: 2026-11-06
U: Buenas	buenas
U: Muchas gracias	de nada
U: Mil gracias	de nada
U: Disculpa	no pasa nada
U: Hasta luego	hasta
U: Hasta mañana	hasta
U: ¿Qué tal?	bien
U: Genial	alegro
U: Ok	vale
U: ¿A qué día estamos?	6 de noviembre de 2026

U: Soy Lucía	encantado
U: ¿Sabes cómo me llamo?	Lucía
U: ¿Cuál es tu nombre?	LCM
U: ¿Para qué sirves?	preguntas
U: ¿Qué has aprendido?	todavía no

U: Clara compra pan.	entendido
U: Marta compra leche.	entendido
U: Háblame de Clara	pan
U: ¿Qué sabes sobre Marta?	leche
U: ¿Qué hemos hablado?	clara
U: ¿Cuántos hechos sabes?	2
U: Cuéntame lo que sabes de Rosa	no sé nada de rosa
U: Borra todo	seguro
U: Claro	olvidado
U: ¿Qué sabes?	todavía no

U: Pedro llama a Marta.
U: ¿Quién llama a Marta?	Pedro
U: Puedes repetirlo	Pedro
U: Olvídalo	olvid
U: ¿Quién llama a Marta?	no lo sé

U: ¿Quién es el abuelo?	explicas
U: Es un señor mayor	entendido
U: Luis ama a Ana.	entendido
U: Esa mujer ama a Luis.	entendido
U: ¿Quién ama a Luis?	mujer
U: Estoy equivocado	olvid
U: Mis amigos son Pedro.	cómo te llamas
U: Me llamo Rubén	encantado
''',
    'data/dialogo_prueba.tsv': r'''# TEST DE CONVERSACION BASICA (Fase 3, bloque A), escrito antes de medir. Criterio fijado antes: >= 75 %.
# Formato: "U: turno<TAB>subcadena esperada en la respuesta" ("!x" = NO debe contener x). Sin esperado = solo prepara. Bloque = conversacion nueva.
HOY: 2026-11-06
U: Hola	hola
U: Buenos días	buenos días
U: ¿Cómo estás?	bien
U: Gracias	de nada
U: Perdona	no pasa nada
U: Vale	vale
U: Adiós	hasta
U: ¡Qué bien!	alegro
U: Muchas gracias por todo	de nada
U: Buenas tardes	buenas tardes
U: ¿Qué día es hoy?	6 de noviembre de 2026

U: Me llamo Marcos	encantado
U: ¿Cómo me llamo?	Marcos
U: Hola	Marcos
U: ¿Cómo está usted?	usted
U: Hola	ayudarle
U: Tutéame, por favor	de tú
U: Hola	ayudarte

U: ¿Quién eres?	LCM
U: ¿Qué sabes hacer?	preguntas
U: ¿Qué sabes?	todavía no
U: Pedro compró pan.	entendido
U: Ana ama a Luis.	entendido
U: ¿Qué sabes de Pedro?	pan
U: Dime lo que sabes de Ana	Luis
U: ¿Qué sabes de Zoe?	no sé nada de zoe
U: ¿Qué te he dicho?	pan
U: ¿Cuántas cosas sabes?	2 hechos

U: ¿Qué es un tenedor?	explicas
U: Es un cubierto	entendido
U: ¿Qué es un tenedor?	cubierto
U: ¿Quién es Marta?	explicas
U: Es la hermana de Luis	entendido
U: ¿Quién es hermana de Luis?	Marta

U: Pedro compró pan.
U: Ana vendió su coche.
U: Olvida que Pedro compró pan	olvid
U: ¿Quién compró pan?	no lo sé
U: Olvida lo de Ana	olvid
U: ¿Quién vendió un coche?	no lo sé
U: Olvida todo	nada que olvidar
U: Pedro compró pan.
U: Luis vendió su moto.
U: Olvida todo	seguro
U: No	no olvido
U: Olvida todo	seguro
U: Sí	olvidado
U: ¿Quién compró pan?	no lo sé

U: Pedro compró pan.
U: ¿Quién compró pan?	Pedro
U: Repite	Pedro
U: ¿Qué has dicho?	Pedro
U: ¿Cómo dices?	Pedro

U: Pedro compró pan.
U: Blablabla gnorf	no he entendido
U: Gnorf Pedro blorp zork	Pedro

U: Me llamo Marcos	encantado
U: Mi madre es Ana.	entendido
U: ¿Quién es mi madre?	Ana
U: Ese perro muerde a Pedro.	entendido
U: ¿Quién muerde a Pedro?	perro
U: Luis compró pan.
U: Ana también compró pan.	entendido
U: ¿Quién compró pan?	Ana
U: Eso es falso	olvid
U: ¿Quién compró pan?	!Ana
U: Javier tampoco compró pan.	no javier
U: Pedro compró pan ayer.
U: ¿Qué compró Pedro?	pan
U: ¿Y Luis?	pan

U: Mi hermano es Pedro.	cómo te llamas
U: Me llamo Marcos	encantado
U: ¿Quién es mi hermano?	Pedro
''',
    'data/discurso_ciego.tsv': r'''Ana vive en Madrid. Trabaja en un banco.	ana|vivir_en|madrid;ana|trabajar_en|banco
Pedro compró pan. Él lee el periódico.	pedro|comprar|pan;pedro|leer|periodico
Marta escribe cartas. Envía paquetes.	marta|escribir|cartas;marta|enviar|paquetes
Luis estudia matemáticas. También estudia historia.	luis|estudiar|matematicas;luis|estudiar|historia
Sara canta en el coro. Ella toca la guitarra.	sara|cantar_en|coro;sara|tocar|guitarra
Diego vende su coche. Compra una moto.	diego|vender|coche;diego|comprar|moto
Elena vive en Bilbao. Ella estudia en Madrid.	elena|vivir_en|bilbao;elena|estudiar_en|madrid
Hugo abre la puerta. Enciende la luz.	hugo|abrir|puerta;hugo|encender|luz
Irene lee un libro. Escribe una novela.	irene|leer|libro;irene|escribir|novela
Carlos trabaja en una fábrica. Vive en Toledo.	carlos|trabajar_en|fabrica;carlos|vivir_en|toledo
Paula pinta cuadros. Ella vende cuadros en la ciudad.	paula|pintar|cuadros;paula|vender|cuadros;paula|vender_en|ciudad
Andrés cocina pasta. Prepara ensalada.	andres|cocinar|pasta;andres|preparar|ensalada
Tomás no bebe café. Bebe agua.	~tomas|beber|cafe;tomas|beber|agua
Laura estudia música. Toca el piano.	laura|estudiar|musica;laura|tocar|piano
Mario escribe una carta. Envía la carta.	mario|escribir|carta;mario|enviar|carta
Rosa lee un libro. Ella escribe un poema.	rosa|leer|libro;rosa|escribir|poema
Álvaro vive en Sevilla. Trabaja en un hospital.	alvaro|vivir_en|sevilla;alvaro|trabajar_en|hospital
Lucía enseña matemáticas. Ella vive en Granada.	lucia|ensenar|matematicas;lucia|vivir_en|granada
Jorge abre una tienda. Vende ropa.	jorge|abrir|tienda;jorge|vender|ropa
Pedro vive en Madrid. Ana trabaja en Sevilla.	pedro|vivir_en|madrid;ana|trabajar_en|sevilla
Marta lee cartas. Luis escribe poemas.	marta|leer|cartas;luis|escribir|poemas
''',
    'data/estados_ciegas.tsv': r'''# TEST CIEGO bloque B (frases distintas), escrito ANTES de medir. Criterio: >= 60 %.
H: Rosa trabaja.
H: Carlos nada en la piscina.
H: Elena salió ayer.
H: Sara vuelve a Madrid.
P: ¿Quién trabaja?	rosa
P: ¿Trabaja Rosa?	SI
P: ¿Quién nada en la piscina?	carlos
P: ¿Salió Elena?	SI
P: ¿Cuándo salió Elena?	ayer
P: ¿Quién vuelve a Madrid?	sara

H: El coche es rojo.
H: La mesa está sucia.
H: Pablo es alto.
H: Lucía no está enferma.
P: ¿Cómo es el coche?	rojo
P: ¿Es rojo el coche?	SI
P: ¿Está sucia la mesa?	SI
P: ¿Es azul el coche?	NOSE
P: ¿Está enferma Lucía?	NO
P: ¿Quién es alto?	pablo

H: Marta sabe nadar.
H: Juan quiere dormir.
H: Teresa puede cantar.
P: ¿Quién puede cantar?	teresa
P: ¿Quién quiere dormir?	juan
P: ¿Puede cantar Teresa?	SI

H: Elena afirma que Sara vino.
H: Juan piensa que Rosa trabaja mucho.
P: ¿Qué afirma Elena?	Sara vino
P: ¿Quién piensa que Rosa trabaja mucho?	juan
P: ¿Vino Sara?	NOSE
''',
    'data/estados_prueba.tsv': r'''# TEST DE VERBOS INTRANSITIVOS, ESTADOS Y MODALES (Fase 3, bloque B), escrito antes de medir. Criterio fijado antes: >= 70 %.
H: Luis llegó ayer.
H: Ana duerme.
H: Pedro corre por el parque.
H: Marta vive en Sevilla.
P: ¿Llegó Luis?	SI
P: ¿Quién llegó?	luis
P: ¿Quién duerme?	ana
P: ¿Duerme Pedro?	NOSE
P: ¿Quién corre por el parque?	pedro
P: ¿Qué hace Ana?	duerme
P: ¿Dónde vive Marta?	sevilla
P: ¿Cuándo llegó Luis?	ayer

H: La casa es grande.
H: Ana está cansada.
H: El perro es pequeño.
H: Luis no está contento.
P: ¿Es grande la casa?	SI
P: ¿Cómo es la casa?	grande
P: ¿Cómo está Ana?	cansada
P: ¿Está cansada Ana?	SI
P: ¿Es pequeño el perro?	SI
P: ¿Es grande el perro?	NOSE
P: ¿Está contento Luis?	NO
P: ¿Quién está cansada?	ana

H: Ana quiere comer pan.
H: Pedro puede nadar.
H: Luis debe estudiar matemáticas.
P: ¿Quién quiere comer pan?	ana
P: ¿Qué quiere comer Ana?	pan
P: ¿Puede nadar Pedro?	SI
P: ¿Quién puede nadar?	pedro
P: ¿Debe estudiar Luis matemáticas?	SI
P: ¿Quiere Pedro comer pan?	NOSE

H: Pedro dice que Ana vino.
H: Marta cree que Luis es alto.
P: ¿Qué dice Pedro?	Ana vino
P: ¿Quién dice que Ana vino?	pedro
P: ¿Vino Ana?	NOSE
P: ¿Es alto Luis?	NOSE
P: ¿Qué cree Marta?	Luis es alto
''',
    'data/fechas_prueba.tsv': r'''# TEST DE FECHAS ABSOLUTAS Y ORDEN (Fase 3, paso 4), escrito antes de medir. Criterio fijado antes: >= 75 %.
# HOY: es la fecha de la conversacion (viernes 6 de noviembre de 2026). Lo relativo se guarda como fecha absoluta.
HOY: 2026-11-06
H: Pedro compró pan ayer.
H: Ana vendió su coche el lunes.
H: Luis compró un libro anteayer.
H: Marta viajó a Roma en 2020.
H: Ana llegó a Madrid el año pasado.
P: ¿Cuándo compró Pedro pan?	5 de noviembre de 2026
P: ¿Cuándo vendió Ana su coche?	2 de noviembre de 2026
P: ¿Cuándo compró Luis un libro?	4 de noviembre de 2026
P: ¿Cuándo llegó Ana a Madrid?	2025
P: ¿Compró Pedro pan el 5 de noviembre?	SI
P: ¿Compró Pedro pan el 4 de noviembre?	NO
P: ¿Vendió Ana su coche el 2 de noviembre?	SI
P: ¿Qué pasó antes del 3 de noviembre?	coche
P: ¿Qué pasó después del 4 de noviembre?	pan
P: ¿Qué pasó primero?	Roma
P: ¿Qué pasó último?	pan
P: ¿Qué pasó antes del 1 de enero de 2020?	NOSE


HOY: 2027-03-10
H: Sara compró una casa el 15 de enero de 2027.
H: Pablo vendió su moto el 20 de febrero.
H: Clara compró flores ayer.
P: ¿Cuándo compró Sara una casa?	15 de enero de 2027
P: ¿Cuándo vendió Pablo su moto?	20 de febrero de 2027
P: ¿Cuándo compró Clara flores?	9 de marzo de 2027
P: ¿Qué pasó primero?	casa
P: ¿Qué pasó último?	flores
P: ¿Vendió Pablo su moto el 20 de febrero?	SI
''',
    'data/frases_largas_ciegas.tsv': r'''Pedro y Marta viven en Madrid.	pedro|vivir_en|madrid;marta|vivir_en|madrid
Ana y Luis estudian matemáticas.	ana|estudiar|matematicas;luis|estudiar|matematicas
Luis compró pan y leche.	luis|comprar|pan;luis|comprar|leche
Sara lee libros y revistas.	sara|leer|libros;sara|leer|revistas
Pedro vive en Madrid y trabaja en Sevilla.	pedro|vivir_en|madrid;pedro|trabajar_en|sevilla
Marta escribe cartas y envía paquetes.	marta|escribir|cartas;marta|enviar|paquetes
El hombre que vive en Madrid escribe cartas.	hombre|vivir_en|madrid;hombre|escribir|cartas
La mujer que canta en el coro estudia música.	mujer|cantar_en|coro;mujer|estudiar|musica
Clara canta en el coro de la iglesia.	clara|cantar_en|coro
Diego vende su coche en la ciudad.	diego|vender|coche;diego|vender_en|ciudad
Hugo y Paula no beben café.	~hugo|beber|cafe;~paula|beber|cafe
Irene vive en Bilbao y estudia en Madrid.	irene|vivir_en|bilbao;irene|estudiar_en|madrid
Lucía cocina pasta y su hermana prepara ensalada.	lucia|cocinar|pasta;hermana|preparar|ensalada
Mi padre trabaja en un banco y mi madre trabaja en una escuela.	padre|trabajar_en|banco;madre|trabajar_en|escuela
Andrés pinta cuadros en su casa.	andres|pintar|cuadros;andres|pintar_en|casa
El niño que rompió la ventana vive en Toledo.	nino|romper|ventana;nino|vivir_en|toledo
Carmen abre la puerta y enciende la luz.	carmen|abrir|puerta;carmen|encender|luz
Raúl y Clara tienen un perro.	raul|tener|perro;clara|tener|perro
Paco toca la guitarra en un grupo.	paco|tocar|guitarra;paco|tocar_en|grupo
La profesora explica la lección y los alumnos escuchan.	profesora|explicar|leccion
Elena come pan, queso y fruta.	elena|comer|pan;elena|comer|queso;elena|comer|fruta
Javier y Ana ven la televisión en el salón.	javier|ver|television;ana|ver|television;javier|ver_en|salon;ana|ver_en|salon
Mario trabaja en una fábrica de coches.	mario|trabajar_en|fabrica
Tomás compra el periódico y lee las noticias.	tomas|comprar|periodico;tomas|leer|noticias
Alba vive en Cádiz con su abuela y su tío.	alba|vivir_en|cadiz;alba|vivir_con|abuela;alba|vivir_con|tio
Los niños juegan en el parque.	ninos|jugar_en|parque
Marina escribe una novela y publica un libro.	marina|escribir|novela;marina|publicar|libro
''',
    'data/frases_prueba.tsv': r'''Pedro vive en Madrid.	pedro|vivir_en|madrid
Ana trabaja en una escuela.	ana|trabajar_en|escuela
Luis no come carne.	~luis|comer|carne
Marta escribió una novela.	marta|escribir|novela
Sara es la profesora de Pablo.	sara|profesora_de|pablo
Juan canta en un coro.	juan|cantar_en|coro
Luisa tiene un perro.	luisa|tener|perro
Mi hermana estudia medicina.	hermana|estudiar|medicina
El profesor explicó la lección.	profesor|explicar|leccion
Carlos compró un coche.	carlos|comprar|coche
Elena lee un libro.	elena|leer|libro
Mateo no conoce a Irene.	~mateo|conocer|irene
Rosa es la madre de Hugo.	rosa|madre_de|hugo
Diego es el padre de Nuria.	diego|padre_de|nuria
Andrés vive en Valencia.	andres|vivir_en|valencia
La niña come una manzana.	nina|comer|manzana
El perro muerde al cartero.	perro|morder|cartero
Alba trabaja con Sergio.	alba|trabajar_con|sergio
Laura habla con su madre.	laura|hablar_con|madre
Raúl llegó a Sevilla.	raul|llegar_a|sevilla
Clara escribe una carta.	clara|escribir|carta
Óscar canta una canción.	oscar|cantar|cancion
Julia no vive en Bilbao.	~julia|vivir_en|bilbao
Iván es el hermano de Marina.	ivan|hermano_de|marina
El médico visitó a la paciente.	medico|visitar|paciente
Lucía pinta un cuadro.	lucia|pintar|cuadro
Pablo estudia en la universidad.	pablo|estudiar_en|universidad
La profesora corrigió el examen.	profesora|corregir|examen
Irene tiene una hermana.	irene|tener|hermana
Hugo abrió la puerta.	hugo|abrir|puerta
Nuria cocina en su casa.	nuria|cocinar_en|casa
Sergio ve una película.	sergio|ver|pelicula
Marina es la hija de Rosa.	marina|hija_de|rosa
El abuelo cuenta una historia.	abuelo|contar|historia
Carmen no tiene coche.	~carmen|tener|coche
Ana ama a Luis.	ana|amar|luis
Elena trabaja para una empresa.	elena|trabajar_para|empresa
Mateo compra pan en el mercado.	mateo|comprar|pan;mateo|comprar_en|mercado
Alba lee el periódico en el parque.	alba|leer|periodico;alba|leer_en|parque
Un gato es un animal.	gato|es|animal
Diego no es el padre de Luis.	~diego|padre_de|luis
La vecina vende flores.	vecina|vender|flores
Clara canta en el coro de la iglesia.	clara|cantar_en|coro
Luis compró flores para Ana.	luis|comprar|flores;luis|comprar_para|ana
Rosa abrió la ventana.	rosa|abrir|ventana
Los niños juegan en el jardín.	ninos|jugar_en|jardin
Mi madre prepara la cena.	madre|preparar|cena
Sara conoce a Pablo.	sara|conocer|pablo
Juan no escribe cartas.	~juan|escribir|cartas
El profesor vive en Granada.	profesor|vivir_en|granada
Marta pinta un retrato de Ana.	marta|pintar|retrato
Andrés es un médico.	andres|es|medico
Laura trabaja con Elena en Madrid.	laura|trabajar_con|elena;laura|trabajar_en|madrid
Lucía vendió su casa.	lucia|vender|casa
Pedro llamó a Marta.	pedro|llamar|marta
El cartero entrega las cartas.	cartero|entregar|cartas
Hugo no estudia matemáticas.	~hugo|estudiar|matematicas
Irene vive con su abuela.	irene|vivir_con|abuela
Nuria visita a su tío.	nuria|visitar|tio
Carlos es el jefe de Alba.	carlos|jefe_de|alba
Mi hermana trabaja en un hospital.	hermana|trabajar_en|hospital
Diego compró un coche nuevo.	diego|comprar|coche
Elena no vive en Barcelona.	~elena|vivir_en|barcelona
El niño rompió la ventana.	nino|romper|ventana
Sofía canta una canción.	sofia|cantar|cancion
Raúl es el padre de Clara.	raul|padre_de|clara
La maestra enseña matemáticas.	maestra|ensenar|matematicas
Javier no conoce a Lucía.	~javier|conocer|lucia
El gato come pescado.	gato|comer|pescado
Marina vive en Valencia.	marina|vivir_en|valencia
Tomás abrió la puerta.	tomas|abrir|puerta
Carmen es una abogada.	carmen|es|abogada
El abuelo cuenta historias.	abuelo|contar|historias
Paula ayuda a su madre.	paula|ayudar|madre
Óscar nunca bebe café.	~oscar|beber|cafe
Isabel es la hermana de Daniel.	isabel|hermana_de|daniel
El médico examina al paciente.	medico|examinar|paciente
Rosa lee un libro.	rosa|leer|libro
Álvaro vive en Sevilla con su tía.	alvaro|vivir_en|sevilla;alvaro|vivir_con|tia
Los vecinos ven la televisión.	vecinos|ver|television
''',
    'data/herencia_prueba.tsv': r'''# TEST DE HERENCIA DE PROPIEDADES (Fase 3, paso 3), escrito antes de medir. Criterio fijado antes: >= 75 %.
# "Los poligonos tienen lados" + "Un triangulo es un poligono" => el triangulo tiene lados (con explicacion). Controles: no hereda hacia ARRIBA ni entre hermanos.
H: Los polígonos tienen lados.
H: Un triángulo es un polígono.
H: Un cuadrado es un polígono.
H: Un círculo es una figura.
P: ¿Tiene un triángulo lados?	SI
P: ¿Qué tiene un cuadrado?	lados
P: ¿Tiene un círculo lados?	NOSE

H: Los animales respiran aire.
H: Un perro es un mamífero.
H: Un mamífero es un animal.
P: ¿Respira un perro aire?	SI
P: ¿Qué respira un perro?	aire

H: Un triángulo tiene tres lados.
H: Un polígono es una figura.
P: ¿Tiene una figura tres lados?	NOSE
P: ¿Tiene un polígono lados?	NOSE

H: Los pájaros tienen alas.
H: Una gaviota es un pájaro.
P: ¿Tiene una gaviota alas?	SI
P: ¿Es una gaviota un animal?	NOSE
P: ¿Tiene un pájaro alas?	SI
''',
    'data/nucleo_ciego.tsv': r'''# TEST CIEGO DEL NUCLEO (bloque C). Escrito antes de medir, con palabras distintas. Criterio fijado antes: >= 60 %.
HOY: 2026-11-06
SEMILLA: si
U: ¿Qué es el verde?	color
U: ¿Es un rectángulo un polígono?	sí
U: ¿Cuántos lados tiene un cuadrado?	cuatro
U: ¿De qué color es el cielo?	azul

U: ¿Qué es un pez?	animal
U: ¿Es una rosa una flor?	sí
U: ¿Es una rosa una planta?	sí
U: ¿Qué es el sábado?	día
U: ¿Qué es el verano?	estación

U: ¿Es una mano parte del cuerpo?	sí
U: ¿Qué es el miedo?	emoción
U: ¿Es dormir una necesidad?	sí
U: ¿Cuál es lo contrario de subir?	bajar
U: ¿Cuál es lo contrario de día?	noche

U: ¿Qué es una mesa?	mueble
U: ¿Qué es el pan?	alimento
U: ¿Para qué sirve un cuchillo?	cortar

U: Juan es padre de Rosa.
U: Rosa es madre de Sara.
U: ¿Es Juan abuelo de Sara?	sí
U: ¿Es Sara nieta de Juan?	sí

U: Luis es hermano de Clara.
U: ¿Es Clara hermana de Luis?	sí

U: Sara regala una flor a Marta.
U: ¿Tiene Marta una flor?	sí

U: Lucía entrega la carta a Pablo.
U: ¿Tiene Pablo la carta?	sí

U: Luis enciende la luz.
U: ¿Está encendida la luz?	sí
U: Luis apaga la luz.
U: ¿Está apagada la luz?	sí

U: Marta vuelve a Bilbao.
U: ¿Dónde está Marta?	bilbao
''',
    'data/nucleo_prueba.tsv': r'''# TEST DEL NUCLEO DE FABRICA (bloque C). Escrito antes de medir. Criterio fijado antes: >= 70 %.
# SEMILLA: carga el conocimiento de fabrica (data/semilla.txt) antes de empezar cada bloque.
HOY: 2026-11-06
SEMILLA: si
U: ¿Qué es el rojo?	color
U: ¿Qué es un cuadrado?	polígono
U: ¿Es un cuadrado una figura?	sí
U: ¿Cuántos lados tiene un triángulo?	tres
U: ¿De qué color es la hierba?	verde
U: ¿Es azul un color?	sí

U: ¿Es un perro un animal?	sí
U: ¿Qué es un gato?	mamífero
U: ¿Es un gato un animal?	sí
U: ¿Qué es un roble?	árbol
U: ¿Es un roble una planta?	sí
U: ¿Qué es julio?	mes
U: ¿Qué es el invierno?	estación
U: ¿Qué es el norte?	punto cardinal

U: ¿Es un ojo parte del cuerpo?	sí
U: ¿Para qué sirve un ojo?	ver
U: ¿Qué es la alegría?	emoción
U: ¿Es comer una necesidad?	sí
U: ¿Cuál es lo contrario de grande?	pequeño
U: ¿Cuál es lo contrario de abrir?	cerrar

U: ¿Qué es una silla?	mueble
U: ¿Para qué sirve una cama?	dormir
U: ¿Qué es una camisa?	prenda
U: ¿Qué es un euro?	dinero
U: ¿Para qué sirve el dinero?	comprar

U: Pedro es padre de Ana.
U: Ana es madre de Luis.
U: ¿Es Pedro abuelo de Luis?	sí
U: ¿Quién es nieto de Pedro?	luis
U: ¿Es Luis hijo de Ana?	sí

U: Marta es hermana de Rosa.
U: ¿Es Rosa hermano de Marta?	sí
U: Rosa es madre de Paco.
U: ¿Es Marta tía de Paco?	sí

U: La rueda es parte del coche.
U: El coche es parte de la flota.
U: ¿Es la rueda parte de la flota?	sí
U: ¿Qué tiene el coche?	rueda

U: Ana tiene un libro.
U: Ana da el libro a Luis.
U: ¿Tiene Luis el libro?	sí
U: ¿Tiene Ana el libro?	!sí
U: ¿Quién tiene el libro?	luis
U: ¿Tenía Ana un libro?	sí

U: Pedro vende su coche a Marta.
U: ¿Tiene Marta un coche?	sí
U: Luis compra una bicicleta.
U: ¿Tiene Luis una bicicleta?	sí

U: Ana abre la puerta.
U: ¿Está abierta la puerta?	sí
U: Luis cierra la puerta.
U: ¿Está cerrada la puerta?	sí
U: ¿Está abierta la puerta?	!sí
U: Ana rompe el vaso.
U: ¿Está roto el vaso?	sí

U: Ana va a Madrid.
U: ¿Dónde está Ana?	madrid
U: Ana llega a Sevilla.
U: ¿Dónde está Ana?	sevilla
''',
    'data/preguntas_ciegas.tsv': r'''# TEST CIEGO de la Fase 1 (escrito antes de medir; se mide UNA vez con: python -m scripts.eval_preguntas data/preguntas_ciegas.tsv)
# Criterio fijado antes: >= 80 % de acierto. Los fallos se informan y NO se ajusta el codigo para este fichero en la Fase 1.
H: Rosa lee un libro.
H: Diego compró un coche.
H: Elena no vive en Barcelona.
H: Tomás abrió la puerta.
P: ¿Quién lee un libro?	rosa
P: ¿Qué lee Rosa?	libro
P: ¿Lee Rosa un libro?	SI
P: ¿Quién compró un coche?	diego
P: ¿Qué compró Diego?	coche
P: ¿Vive Elena en Barcelona?	NO
P: ¿Qué abrió Tomás?	puerta
P: ¿Abrió Tomás la ventana?	NOSE

H: Sofía canta una canción.
H: El niño rompió la ventana.
H: La maestra enseña matemáticas.
P: ¿Quién canta una canción?	sofia
P: ¿Qué canta Sofía?	cancion
P: ¿Quién rompió la ventana?	nino
P: ¿Qué rompió el niño?	ventana
P: ¿Quién enseña matemáticas?	maestra
P: ¿Enseña la maestra matemáticas?	SI
P: ¿Canta Sofía una ópera?	NOSE

H: Marina vive en Valencia.
H: Álvaro trabaja en Sevilla.
H: Paula vive con su madre.
P: ¿Dónde vive Marina?	valencia
P: ¿Dónde trabaja Álvaro?	sevilla
P: ¿Quién vive en Valencia?	marina
P: ¿Con quién vive Paula?	madre
P: ¿Vive Marina en Valencia?	SI
P: ¿Trabaja Álvaro en Valencia?	NOSE

H: Isabel es la hermana de Daniel.
H: Raúl es el padre de Clara.
H: Carmen es una abogada.
P: ¿Quién es la hermana de Daniel?	isabel
P: ¿Quién es el padre de Clara?	raul
P: ¿Es Raúl el padre de Clara?	SI
P: ¿Es Carmen una abogada?	SI

H: Javier llamó a Lucía.
H: El médico examina al paciente.
H: Óscar nunca bebe café.
P: ¿A quién llamó Javier?	lucia
P: ¿Quién llamó a Lucía?	javier
P: ¿A quién examina el médico?	paciente
P: ¿Quién examina al paciente?	medico
P: ¿Bebe Óscar café?	NO
P: ¿Llamó Javier a Pedro?	NOSE
''',
    'data/preguntas_deduccion.tsv': r'''# TEST DE DEDUCCION (Fase 2), escrito antes de medir. "R:" = regla "Si A entonces B" ensenada. Criterio fijado antes: >= 75 %.
# Hay controles: sin regla, o en sentido contrario, la respuesta correcta es "no lo se" (NOSE), nunca una deduccion inventada.
R: Si Ana es madre de Luis entonces Luis es hijo de Ana.
H: Marta es madre de Pablo.
H: Sara es madre de Juan.
P: ¿Es Pablo hijo de Marta?	SI
P: ¿Quién es hijo de Sara?	juan
P: ¿Es Juan hijo de Sara?	SI
P: ¿Es Marta madre de Pablo?	SI
P: ¿Es Sara hijo de Juan?	NOSE

R: Si Ana trabaja en Madrid entonces Ana vive en Madrid.
H: Pedro trabaja en Bilbao.
H: Rosa vive en Cádiz.
P: ¿Vive Pedro en Bilbao?	SI
P: ¿Dónde vive Pedro?	bilbao
P: ¿Trabaja Rosa en Cádiz?	NOSE

H: Luis es hijo de Ana.
P: ¿Es Ana madre de Luis?	NOSE

R: Si Ana compra un coche entonces Ana tiene un coche.
H: Pedro compra una moto.
P: ¿Tiene Pedro una moto?	SI
P: ¿Quién tiene una moto?	pedro

H: Luis no vive en Madrid.
P: ¿Vive Luis en Madrid?	NO
''',
    'data/preguntas_prueba.tsv': r'''# Bloques separados por una linea en blanco. "H:" = hecho que se ensena (frase normal). "P:" = pregunta<TAB>respuesta esperada.
# Esperada: SI / NO / NOSE (no se sabe), o una palabra que debe aparecer en la respuesta.
H: Marta escribió una novela.
H: Pedro vive en Madrid.
H: Luis no come carne.
H: Sara es la profesora de Pablo.
P: ¿Quién escribió una novela?	marta
P: ¿Qué escribió Marta?	novela
P: ¿Vive Pedro en Madrid?	SI
P: ¿Vive Pedro en Sevilla?	NOSE
P: ¿Come Luis carne?	NO
P: ¿Quién vive en Madrid?	pedro
P: ¿Quién es la profesora de Pablo?	sara
P: ¿Dónde vive Pedro?	madrid

H: Ana llamó a Juan.
H: El perro muerde al cartero.
H: Lucía vendió su casa.
P: ¿A quién llamó Ana?	juan
P: ¿Quién llamó a Juan?	ana
P: ¿Quién muerde al cartero?	perro
P: ¿Qué vendió Lucía?	casa
P: ¿Llamó Ana a Juan?	SI
P: ¿Vendió Lucía un coche?	NOSE

H: Laura trabaja en Madrid.
H: Hugo estudia matemáticas.
H: Irene vive con su abuela.
P: ¿Dónde trabaja Laura?	madrid
P: ¿Qué estudia Hugo?	matematicas
P: ¿Con quién vive Irene?	abuela
P: ¿Trabaja Laura en Madrid?	SI
P: ¿Estudia Hugo historia?	NOSE
''',
    'data/semilla.txt': r'''# CONOCIMIENTO DE FABRICA (bloque C): frases en espanol, una por linea. Se cargan con el mismo camino que cualquier frase.
# Colores y formas
Rojo es un color.
Azul es un color.
Verde es un color.
Amarillo es un color.
Blanco es un color.
Negro es un color.
Naranja es un color.
Gris es un color.
El cielo es azul.
La hierba es verde.
El sol es amarillo.
La nieve es blanca.
La sangre es roja.
Un círculo es una figura.
Un polígono es una figura.
Un triángulo es un polígono.
Un cuadrado es un polígono.
Un rectángulo es un polígono.
Un triángulo tiene tres lados.
Un cuadrado tiene cuatro lados.
Un rectángulo tiene cuatro lados.
Un círculo es redondo.
# Naturaleza
Un perro es un mamífero.
Un gato es un mamífero.
Un caballo es un mamífero.
Un mamífero es un animal.
Un pájaro es un animal.
Un pez es un animal.
Un pájaro tiene alas.
Una rosa es una flor.
Una flor es una planta.
Un roble es un árbol.
Un pino es un árbol.
Un árbol es una planta.
Enero es un mes.
Febrero es un mes.
Marzo es un mes.
Abril es un mes.
Mayo es un mes.
Junio es un mes.
Julio es un mes.
Agosto es un mes.
Septiembre es un mes.
Octubre es un mes.
Noviembre es un mes.
Diciembre es un mes.
Lunes es un día.
Martes es un día.
Miércoles es un día.
Jueves es un día.
Viernes es un día.
Sábado es un día.
Domingo es un día.
Primavera es una estación.
Verano es una estación.
Otoño es una estación.
Invierno es una estación.
Norte es un punto cardinal.
Sur es un punto cardinal.
Este es un punto cardinal.
Oeste es un punto cardinal.
La lluvia es agua.
# Cuerpo, emociones y necesidades
Un ojo es parte del cuerpo.
Una mano es parte del cuerpo.
Un pie es parte del cuerpo.
Una cabeza es parte del cuerpo.
Un brazo es parte del cuerpo.
Una pierna es parte del cuerpo.
Una boca es parte de la cabeza.
Una nariz es parte de la cabeza.
Un ojo sirve para ver.
Una oreja sirve para oír.
Una nariz sirve para oler.
Una boca sirve para comer.
La alegría es una emoción.
La tristeza es una emoción.
El miedo es una emoción.
El enfado es una emoción.
Comer es una necesidad.
Dormir es una necesidad.
Beber es una necesidad.
# Objetos cotidianos
Una casa es un edificio.
Un coche es un vehículo.
Una bicicleta es un vehículo.
Un coche tiene motor.
Una silla es un mueble.
Una mesa es un mueble.
Una cama es un mueble.
Una cama sirve para dormir.
Una silla sirve para sentarse.
Un cuchillo sirve para cortar.
Un coche sirve para viajar.
Una camisa es una prenda.
Un pantalón es una prenda.
El pan es un alimento.
Una manzana es una fruta.
Una fruta es un alimento.
El agua es una bebida.
# Dinero y trabajo
Un euro es dinero.
El dinero sirve para comprar.
Un médico es una persona.
Un profesor es una persona.
# Verbos y opuestos
Cocinar es una acción.
Correr es una acción.
Comprar es una acción.
Vender es una acción.
Grande es lo contrario de pequeño.
Alto es lo contrario de bajo.
Abrir es lo contrario de cerrar.
Subir es lo contrario de bajar.
Entrar es lo contrario de salir.
Comprar es lo contrario de vender.
Dar es lo contrario de recibir.
Empezar es lo contrario de terminar.
Día es lo contrario de noche.
Alegre es lo contrario de triste.
Encender es lo contrario de apagar.
Coche es sinónimo de automóvil.
Casa es sinónimo de hogar.
''',
    'data/tiempo_prueba.tsv': r'''# TEST DE EXPRESIONES TEMPORALES (Fase 3, paso 2), escrito antes de medir. Criterio fijado antes: >= 75 %.
# Adverbios (ayer), dias, anios, estaciones; preguntas "cuando", si/no con tiempo, "quien ... ayer"; controles: sin tiempo guardado -> "no lo se".
H: Pedro compró pan ayer.
H: Ana vendió su coche el lunes.
H: Luis estudia música en Madrid.
P: ¿Cuándo compró Pedro pan?	ayer
P: ¿Compró Pedro pan ayer?	SI
P: ¿Compró Pedro pan hoy?	NO
P: ¿Quién compró pan ayer?	pedro
P: ¿Cuándo vendió Ana su coche?	lunes
P: ¿Quién vendió su coche el lunes?	ana
P: ¿Cuándo estudia Luis música?	NOSE
P: ¿Dónde estudia Luis música?	madrid

H: Marta viajó a Roma en 2020.
H: Marta visitó París en verano.
P: ¿Cuándo viajó Marta a Roma?	2020
P: ¿Viajó Marta a Roma en 2020?	SI
P: ¿Quién viajó a Roma?	marta
P: ¿Cuándo visitó Marta París?	verano

H: Ana llegó a Madrid el año pasado.
H: Pedro compra pan.
P: ¿Cuándo llegó Ana a Madrid?	pasado
P: ¿Cuándo compra Pedro pan?	NOSE
''',
    'docs/ESTADO.md': r'''# Estado del proyecto LCM (para retomar el trabajo)

Ultima actualizacion: 2026-11-06, al cerrar la Fase 1.

## Objetivo y reglas de trabajo
- Meta: que el LCM aprenda ESPANOL y converse en lenguaje natural SIN LLM, aprendiendo "al vuelo" en el dialogo y
  consolidando al "dormir". El libro (La Regenta) es solo texto en bruto; el objetivo NO es aprender el libro.
- Metodo: "parche tras parche". Cada parche es un `parche-N.py` autocontenido (diccionario FILES + instalador con copias
  en `.parche_backups/<fecha>`; solo compila los .py). El usuario lo copia como `parche.py` en `~/Desktop/LCM`, lo ejecuta
  (venv, Mac MPS) y pega las salidas.
- Criterios de decision SIEMPRE fijados antes de medir; los fallos se informan tal cual, nunca se reescribe un criterio
  despues. Un reintento tras arreglar fallos conocidos se etiqueta como reintento. Explicaciones al usuario en espanol sencillo.
- No hacer commit/push a GitHub. Sandbox: Linux solo CPU, sin acceso a su disco ni a GitHub (los modelos reales se miden en su Mac).

## Mapa del codigo
- `src/ontology`, `src/model`, `src/reasoning`: espacio conceptual (vectores deterministas), razonador latente, motor de reglas.
- `src/training/online.py`: aprendizaje online (canario con rollback, `inoculate` = vacuna de relaciones nuevas).
- `src/memory`: `store.py` (hechos, lecciones, `surface`/`display` para hablar con las palabras del usuario), `schema.py`,
  `sleep.py` (ciclo de sueno), `negatives.py` (negativos + relaciones fantasma).
- `src/language`: `ear.py` (oido de plantillas, preentrenado con MLM), `ud.py` (escuela: UPOS, arcos, funcion, lema, mayuscula),
  `ud_synth.py`, `extract.py` (arbol -> proposiciones + plantilla de superficie), `school_parser.py`, `qa.py` (preguntas).
- `scripts/think.py`: la conversacion. `reproduce.py`: todo el proceso. `eval_*`: tests. `clean.py`: limpieza.
- Datos: `data/frases_prueba.tsv` (80 frases), `data/preguntas_prueba.tsv` (19), `data/preguntas_ciegas.tsv` (31, ya medido).

## Resultados (ver reports/RESULTADOS.md)
Conversacion 90,0 % relajado / 85,0 % exacto (80 frases); preguntas 19/19 (tras ajustar) y ciego 29/31 = 93,5 %;
UD triples 35 % (NO CUMPLE el 60 %); oido: c 94,1, d 84,1.

## Como funciona QA (Fase 1, cerrada)
Pregunta -> afirmacion con hueco "Xqx" -> misma escuela -> busqueda en memoria (relacion tolerante: 3 primeras letras + preposicion,
la "a" personal no cuenta, o misma forma verbal guardada en `surface`) -> deduccion con lecciones ("Lo deduzco") -> "No lo se"
(mundo abierto). Los adjetivos con funcion obj cuentan como objeto (matematicas).

## Problemas abiertos (candidatos para la Fase 2)
1. Frases largas / varias proposiciones / subordinadas (UD triples 35 %; "Clara canta en el coro de la iglesia" no extrae nada).
2. Pronombres y dialogo de varias frases (sin correferencia).
3. Fallos de QA: "Rosa lee Xqx." no se lee; sí/no con verbo antes del sujeto y articulo ("¿Enseña la maestra matematicas?").
4. Lemas irregulares (muerder/morder, mendar) y convencion de la "a" personal (conocer_a vs conocer).
5. ENTENDI no entrena la escuela; el sueno no consolida la escuela.
6. Relaciones creadas antes de la vacuna (p. ej. ESCRIBIR) alucinan hasta un DORMIR.
7. (resuelto en Fase 2) Preguntas con deduccion por reglas ensenadas: src/reasoning/lessons.py, test deduccion_12.
8. Las respuestas no son lenguaje natural libre (plantillas guardadas); falta generacion.
9. Aprendizaje integral desde texto corriente (prediccion del siguiente token) sigue sin hacerse mas alla del MLM del oido.

## Fase 2 (en curso)
- Hecho: coordinaciones (sujetos/objetos/complementos/verbos con sujeto compartido) y adjetivo con mayuscula como nombre propio (extract.py v3);
  frases largas ciegas 37 -> 92,6 %. think acepta varias proposiciones por frase.
- Hecho (parche-44, por medir): discurso = `src/language/discourse.py` (tema = sujeto anterior; sustituye a "el/ella" y es el sujeto de un verbo
  principal sin sujeto); think divide varias frases y recuerda el tema. Linea base 9,5 %, criterio >= 70 %.
- Hecho (parche-47): deduccion con las lecciones del usuario (reglas con variables, explicacion "porque..."), test deduccion_12 100 %; `python -m scripts.check` lo mide todo. Ya tengo ear.pt/school.pt/school_meta.json en el sandbox (reproducen los numeros del usuario).
- Pendiente de Fase 2: ENTENDI que entrene la escuela + consolidar en DORMIR; medir preguntas con deduccion; pronombres de objeto (lo/la);
  fallos de la escuela con nombres propios que son palabras comunes.

## Fase 3: integrar conceptos nuevos desde lenguaje natural (requisito del usuario, 2026-11-06)
El usuario pide que el modelo integre por si mismo conceptos nuevos (acciones, figuras geometricas, expresiones temporales...) a partir de texto normal.
Hoy un concepto nuevo = un nombre con rasgo de identidad; el nucleo neuronal NO ve su tipo. Plan por pasos (cada uno con test ciego fijado antes):
1. HECHO (parche-50): definiciones "X es un Y", jerarquias con deduccion (ES transitiva, regla por defecto con explicacion), acciones como concepto
   ("Cocinar es una accion"), propiedades con numeral ("tres_lados"). Simbolico + QA. Test conceptos_14.
2. HECHO (parche-51, version basica): tiempo como atributo del hecho (when/when_disp) para ayer/hoy/dias/meses/estaciones/anios; preguntas cuando/si-no/quien con tiempo. Falta: orden entre fechas (antes/despues), intransitivos, duraciones. (plan original: hueco de TIEMPO en las proposiciones (ayer, manana, en 2020, el lunes, antes/despues) y deduccion de orden.
3. Herencia de propiedades ("los poligonos tienen lados" -> el triangulo los hereda) y definiciones con rasgos ("con tres lados").
4. (Dificil) que el razonador NEURONAL use los tipos: reentrenar prepare_concepts/train_reasoner con vocabulario de rasgos abierto (isa:...), para
   que un concepto nuevo tenga vector por sus rasgos y no solo por su nombre.

## Siguiente paso sugerido
Fase 2: empezar por (1) y (3) con un test ciego nuevo de frases largas pre-registrado; luego (5) y (7).

- Fase 3 paso 3 (herencia de propiedades) HECHO en parche-52: `lessons.inherit/canon/deduce_all`, test data/herencia_prueba.tsv (10/10 tras reintento; primera 9/10).

- Fase 3 paso 4 (fechas absolutas + orden) HECHO en parche-53: `src/language/fechas.py`, `when_abs` en hechos, `QA.timeline`, comando natural "Hoy es ...". Test data/fechas_prueba.tsv (18/18 tras reintento; primera 16/18).

- Bloque A de docs/NUCLEO_BASICO.md HECHO en parche-54 (`src/language/dialogue.py`, tests data/dialogo_prueba.tsv + dialogo_ciego.tsv, scripts/eval_dialogo.py). Pendiente de ese bloque: persistir el nombre del usuario; "eso/lo anterior" mas alla de borrar; registro tu/usted solo en saludos.

- Bloque B parcial en parche-55: items 10, 11, 12 y 17 de NUCLEO_BASICO hechos (ver RESULTADOS). Faltan 13-16 (cuantificadores, duracion/frecuencia, causa, lugar relativo).

- Bloque B COMPLETO (con limites) en parche-56: items 13-16 de NUCLEO_BASICO. Siguiente: bloque C (conceptos de fabrica) o D (contradicciones y cambio de estado).

- Bloque D parcial en parche-57: items 29, 30 y 33 de NUCLEO_BASICO (contradicciones, cambio de estado, procedencia). Falta del D: antes/despues entre dos sucesos y comparar quien es mayor con fechas. Siguiente: bloque C (conceptos de fabrica) o E (aprender palabras/acciones por definicion).

- parche-59: bloque C (nucleo de fabrica: data/semilla.txt, parentesco/partes, efectos de dar/vender/abrir/ir). Con el 58 (E), 57 (D), 56/55 (B) y 54 (A) quedan hechos los bloques A-E de NUCLEO_BASICO (con limites).
- parche-60: reproducibilidad. `python -m scripts.manifiesto --guardar` (huellas + commits UD + metricas), `python -m scripts.empaquetar_todo` (LCM_construir_desde_cero.py), `scripts.reproduce` ampliado (tests, check, semilla, verificacion). Guia: docs/REPRODUCIR.md. Siguiente: entrenamiento (reentrenar la escuela con las correcciones acumuladas, ver "Clara" y similares).
''',
    'docs/NUCLEO_BASICO.md': r'''# Núcleo básico: lo que el LCM tiene que saber SÍ O SÍ

Estado: ✅ ya funciona (medido) · 🟡 parcial · ❌ falta. Lista propuesta antes del parche-54; el orden de abajo es el de prioridad sugerido.

## A. Conversación (lo mínimo para hablar) — HECHO en parche-54 (ver RESULTADOS.md)
1. ✅ Afirmar hechos («Pedro compró pan ayer») y preguntar (quién, qué, dónde, cuándo, sí/no).
2. ✅ Saludos, despedidas, gracias, «perdona» (actos de habla sociales) y responder con naturalidad.
3. ✅ Pedir aclaración cuando no entiende («¿Te refieres a…?») en vez de «no he entendido».
4. ✅ «No lo sé» honesto y preguntar «¿cómo se llama X?», «¿qué es X?» para aprender lo que le falta.
5. ✅ Preguntas sobre sí mismo y sobre la conversación («¿qué sabes de Pedro?», «¿qué te he dicho hoy?»).
6. ✅ Órdenes y peticiones («Dime lo que sabes de…», «Olvida que…», «Repite»).
7. ✅ Cortesía y registro (tú/usted), exclamaciones, afirmar/negar sueltos («sí», «no», «vale»).
8. 🟡 Referencias: él/ella, mi/yo, este/ese, también/tampoco, «eso es falso», «¿y Ana?» (sí); ❌ «eso», «lo anterior», «también», «otra vez», demostrativos (este/ese/aquel), posesivos (mi, tu, su).

## B. Gramática y significado elementales
9. ✅ Verbos transitivos, ser/estar/tener, negación simple.
10. ✅ Verbos intransitivos y de movimiento («Luis llegó», «Ana duerme», «Pedro corre»).
11. 🟡 Estado y propiedad con adjetivos (✅ «La casa es grande», «Ana está cansada»); ❌ comparaciones («más alto que»).
12. ✅ Modalidad y deseo: poder, deber, querer, saber + infinitivo («Ana quiere comer»).
13. 🟡 Cantidades: todos, algunos, ninguno, muchos, poco y contar (✅); ❌ operaciones (sumar, restar).
14. 🟡 Tiempo: fechas absolutas, hora del día y frecuencia (✅); ❌ duración calculada, pasado/presente/futuro por la conjugación.
15. 🟡 Causa («porque», «¿por qué?») y condición (reglas) ✅; ❌ finalidad («para»).
16. 🟡 Lugar: «en» y encima/debajo/dentro/fuera/cerca/lejos/delante/detrás de (✅); ❌ izquierda/derecha, origen/destino.
17. ✅ Oraciones subordinadas (decir/creer/pensar que) («Pedro dice que Ana vino»): creencias y dichos de otros, distinguir «verdad» de «lo que alguien dice».

## C. Conceptos que debe traer de fábrica
18. ✅ Clases y herencia (ES / tiene), definiciones («Un triángulo es un polígono»).
19. ✅ (parche-59) Personas y parentesco completo (padre, madre, hermano, abuelo, primo, pareja) con sus inversas y reglas (ya hay algunas).
20. ✅ (parche-59) Partes y todo («parte de», «contiene») y su transitividad.
21. 🟡 (parche-59, semilla básica) Cuerpo y sentidos, emociones básicas (alegre, triste, enfadado, miedo), necesidades (comer, dormir, beber).
22. 🟡 (parche-59, semilla básica) Objetos y usos cotidianos (casa, coche, comida, ropa) con sus propiedades típicas.
23. 🟡 (parche-59, semilla básica) Colores, formas (triángulo, círculo, cuadrado…), tamaños, texturas, materiales.
24. 🟡 (parche-59, semilla básica) Naturaleza: animales, plantas, clima, estaciones, día/noche, puntos cardinales.
25. 🟡 (parche-59, quién tiene qué; sin precios) Dinero, trabajo, comprar/vender/pagar (compraventa con consecuencia: quien vende ya no lo tiene).
26. 🟡 (parche-59, dar/vender/comprar/abrir/cerrar/romper/ir/llegar) Acciones elementales con sus efectos: dar/recibir, ir/venir, abrir/cerrar, empezar/terminar, hacer/romper.
27. ✅ (parche-59) Opuestos y sinónimos (grande/pequeño, subir/bajar, abrir/cerrar).

## D. Razonamiento básico
28. ✅ Transitividad ES, herencia de propiedades, reglas enseñadas, explicación («porque…»).
29. ✅ Contradicciones: detectar «Ana es alta» vs «Ana es baja» y preguntar cuál vale.
30. ✅ Cambio de estado en el tiempo («Ana vive en Madrid» → «ahora vive en Sevilla»: el hecho viejo pasa a pasado).
31. 🟡 Orden temporal con fechas (sí); ❌ antes/después entre dos sucesos concretos y duración entre fechas.
32. ❌ Cierre de pregunta con varias respuestas, contar («¿cuántos hijos tiene Ana?»), comparar («¿quién es mayor?»).
33. 🟡 Certeza (procedencia ✅: me lo dijiste / lo deduje / lo dijo otro; falta confianza graduada): distinguir lo que sabe, lo que dedujo y lo que le dijeron (confianza por fuente).

## E. Aprendizaje (el objetivo central)
34. ✅ Aprender hechos y reglas al vuelo, ENTENDI corrige la escuela, dormir consolida.
35. ✅ (parche-58) Aprender una palabra nueva a partir de una definición o de un ejemplo («un *tenedor* es un cubierto para comer»).
36. 🟡 (parche-58) Aprender un verbo nuevo por definición («cocinar es preparar comida con calor»): se hereda al verbo más general; sin condiciones ni efectos.
37. ❌ Corregirse por conversación natural («no, te equivocas, es…») sin comandos especiales.
38. ❌ Olvidar de forma natural («olvida lo de Pedro») y pedir confirmación ante lo importante.
39. ❌ Distinguir entre hechos de la conversación (efímeros) y conocimiento general (permanente).

## Orden propuesto para los próximos parches
1. Actos sociales + aclaración + órdenes básicas (A2, A3, A5, A6, A7): sin esto no «conversa».
2. Verbos intransitivos, adjetivos y estados (B10, B11, B12): desbloquea la mayoría de frases reales.
3. Cambio de estado y contradicciones (D29, D30): memoria coherente.
4. Subordinadas y «X dice que…» (B17, D33).
5. Cantidades, comparaciones y contar (B13, D32).
6. Núcleo de conceptos de fábrica enseñado con frases (C19–C27), midiendo con tests ciegos.
7. Aprender palabras/acciones nuevas desde definiciones (E35, E36).
''',
    'docs/REPRODUCIR.md': r'''# Reproducir el LCM desde cero

Objetivo: que puedas reconstruir, en cualquier momento y en cualquier máquina, el proyecto **exactamente** como está hoy
(parche-59 + este paquete), reentrenar sus modelos y comprobar con números que el resultado es equivalente.

Hay tres cosas distintas, y conviene no mezclarlas:

| Qué | Cómo se reproduce | ¿Idéntico bit a bit? |
|---|---|---|
| **Código, datos de prueba, tests, documentos** | `LCM_construir_desde_cero.py` + `manifiesto --verificar` | **Sí** (huellas SHA-256) |
| **Corpus UD** (GSD, AnCora) | `scripts.get_data` con el commit fijado en el manifiesto | **Sí** si se fija el commit |
| **Pesos** (`checkpoints/*.pt`) | `scripts.reproduce` (misma semilla, mismos datos) | **No**: cambian unas décimas con otro hardware (CPU/MPS/CUDA) o versión de torch. Se exige el **criterio** (CUMPLE), no el decimal |

## 0. Una vez, ahora, en tu Mac (congelar el estado actual)

```
python parche.py                         # instala parche-60 (este paquete)
python -m scripts.get_data               # si aún no tienes data/ud/
python -m scripts.manifiesto --guardar   # escribe reproducibilidad/manifiesto.json
python -m scripts.empaquetar_todo        # escribe LCM_construir_desde_cero.py
```

`manifiesto --guardar` apunta: versiones de Python/torch/numpy, **el commit exacto de cada corpus UD que tienes clonado** (así
`get_data` bajará siempre ese mismo), la huella de cada archivo y las métricas de la última ejecución de `scripts.check`
(son la referencia con la que se compara una reproducción). Guarda `reproducibilidad/` y `LCM_construir_desde_cero.py`
donde guardes tus copias importantes (y en git, si lo usas). Repite estos dos comandos cada vez que cierres un parche.

## 0b. Todo con un solo comando (tabula rasa + reconstruir + reentrenar)

```
python limpieza.py                              # ensayo: ves qué se quitaría y qué se conserva
python limpieza.py --aplicar --reconstruir      # lo hace TODO: regenera el constructor y el manifiesto desde TU proyecto,
                                                # comprueba una reconstrucción en carpeta temporal, te pide confirmación (TABULA RASA),
                                                # limpia, crea el entorno, instala, prueba, verifica, reentrena y compara métricas
```
Variantes: `--borrar` (sin copia de seguridad), `--reconstruir menu` (abre el menú en vez de hacerlo todo), `--reconstruir archivos`
(solo escribe los archivos), `--libro RUTA`, `--rapido`, `--semilla N`, `--conservar-ud`. Si algo falla antes de la confirmación, no se toca nada.
El constructor se regenera **siempre desde el proyecto que tienes**, por eso la reconstrucción es fiel a tu copia.

## 1. Reconstruir en una carpeta vacía (con asistente)

```
mkdir LCM && cd LCM
cp /ruta/a/LCM_construir_desde_cero.py .
python LCM_construir_desde_cero.py
```

Escribe todo el código, tests, datos de prueba y documentos y abre un **menú guiado** (no hace falta recordar comandos):

```
1) Preparar el entorno (crear .venv e instalar dependencias)
2) Comprobar el código con los tests (51)
3) Verificar que el código es idéntico al original (manifiesto)
4) Reentrenar TODO desde cero (reproduce; tarda de decenas de minutos a horas)
5) Comprobar los resultados contra la referencia
6) Hablar con el modelo (think)
7) Hacer 1 -> 5 en orden, sin parar
```

Arriba del menú muestra el estado (entorno, pesos entrenados, texto encontrado). Para usarlo sin menú:
`--sin-menu` (solo escribir archivos) o `--todo --libro mi_texto.txt [--rapido] [--semilla N]` (hace 1→5 sin preguntar).
Después de `python limpieza.py` es exactamente el mismo flujo. Manual equivalente: `python -m venv .venv && source .venv/bin/activate &&
pip install -r requirements.txt && python -m pytest -q tests`. `python -m scripts.manifiesto --verificar` debe decir *Reproducción fiel*.

## 2. Reentrenar todo (de cero a lo que tienes hoy)

```
python -m scripts.reproduce --libro mi_texto.txt     # UN comando; --lista muestra los pasos; --desde PASO continúa; --semilla N
```

`mi_texto.txt` es un texto largo en español (tú usaste *La Regenta*; no se incluye ningún libro). Sin él se saltan los pasos
que dependen del texto (el oído no se preentrena con tu libro y saldrán otras cifras en el oído).

| # | Paso | Qué produce | Criterio (se imprime solo) |
|---|---|---|---|
| 1 | `tests_unitarios` | — | 52 passed |
| 2 | `prepare_concepts` | `data/concept_*.pkl`, `dataset_manifest.json` (espacio conceptual semilla 42) | — |
| 3 | `train_reasoner` | `checkpoints/lcm_reasoner.pt` (semilla `LCM_SEED`=0) | early stopping |
| 4 | `evaluate_reasoner` | `reports/lcm_evaluation.json` | 100 % top-1 en test |
| 5 | `read_book` | `data/libro.txt`, `libro_vocab.json` (sin oído aún: salta la medición) | (necesita `--libro`) |
| 6 | `pretrain_ear` | `checkpoints/ear_pre.pt`, `ear_lm.pt` (MLM, opcional/largo) | — |
| 7 | `train_ear` | `checkpoints/ear.pt` (usa el vocabulario y el preentrenamiento anteriores) | — |
| 8 | `evaluate_ear` | test c/d del oído | c ≈ 94 %, d ≈ 84 % |
| 9 | `read_book_medida` | repite `read_book` ya con oído: `reports/libro_muestras.txt` (informativo, opcional) | — |
| 10 | `get_data` | `data/ud/…` (commit fijado) | — |
| 11 | `train_school` | `checkpoints/school.pt`, `school_meta.json` | UPOS/UAS/lema ≈ 96,2 / 86,8 / 98,1 % |
| 12 | `eval_frases` | test de conversación (80 frases) | ≥ 75 % (referencia 91,2 %) |
| 13 | `eval_preguntas` | preguntas | ≥ 70 % |
| 14 | `check_todo` | **todas** las pruebas de los parches 44–59 (`reports/informe.txt`, `historial.json`) | `TODO CUMPLE` |
| 15–18 | `evaluate_online/negatives/inoculate/sleep` | aprendizaje al vuelo, negativos, vacuna, sueño | opcionales (`--rapido` los salta) |
| 19 | `verificar_manifiesto` | compara el código con el manifiesto | *Reproducción fiel* |

**Orden del oído desde cero:** `read_book` (saca texto y vocabulario) → `pretrain_ear` → `train_ear`. Antes (hasta el parche-61)
`read_book` exigía un `ear.pt` que todavía no existía; el primer intento real en tabula rasa lo detectó.

**El constructor debe generarse desde TU proyecto real.** `empaquetar_todo` y `manifiesto --guardar` se ejecutan en la copia
buena (la que has usado), nunca a partir de una copia ajena: si no, `manifiesto --verificar` marca DISTINTO/FALTA/SOBRA.

Cada paso deja su salida en `reports/reproduce_<paso>.log` y el resumen (códigos, tiempos, semilla) en
`reports/reproduce_resumen.json`. Si un paso falla se para y te dice cómo continuar (`--desde <paso>`).
Para comprobar métricas contra la referencia: `python -m scripts.manifiesto --verificar --metricas`
(admite hasta 3 puntos por debajo de la referencia en cada métrica).

## 3. Qué es determinista y qué no

- Semillas fijas: espacio conceptual `42`; datos sintéticos del oído `seed=1,2`; sintéticos de la escuela `seed=5`;
  `torch.manual_seed(LCM_SEED)` (por defecto 0) en razonador, oído y escuela; el preentrenamiento del oído usa 0.
  `reproduce` fija también `PYTHONHASHSEED=0`.
- Sin determinismo bit a bit entre CPU, MPS y CUDA (operaciones de punto flotante distintas): por eso el criterio es
  **CUMPLE/NO CUMPLE** y la tolerancia de 3 puntos, no la igualdad exacta.
- **Todo lo que sigue a la escuela** (extractor, preguntas, diálogo, coherencia, efectos, definiciones, semilla de fábrica)
  es código simbólico sin aleatoriedad: con la misma escuela da exactamente los mismos resultados.
- Memoria personal (`memory/lcm_memory.json`) no forma parte de la reproducción: empieza vacía y `think` carga la semilla de
  fábrica (`data/semilla.txt`) la primera vez.

## 4. Cómo se construyó (orden de los parches)

Cada fase añadió módulos y una prueba escrita **antes** de medir, con su criterio; los reintentos están etiquetados en
`reports/RESULTADOS.md`. Para rehacer el proceso paso a paso lee ese archivo en este orden:

| Fase / parche | Qué se añadió | Módulos principales | Pruebas |
|---|---|---|---|
| Fase 0 (base) | espacio conceptual con rasgos, razonador Transformer, motor simbólico, memoria y sueño | `src/ontology`, `src/model`, `src/reasoning/{engine,rule_engine}.py`, `src/memory`, `src/training` | `evaluate_reasoner/online/sleep/negatives/inoculate` |
| Fase 1 | oído (plantillas, MLM), escuela UD (UPOS, arcos, función, lema), extractor, preguntas (QA) | `src/language/{ear,ud,ud_synth,school_parser,extract,qa}.py` | `eval_frases`, `eval_preguntas`, `preguntas_ciegas` |
| Fase 2 (≤ parche-49) | coordinaciones, nombres propios ambiguos, discurso, deducción con lecciones | `discourse.py`, `reasoning/lessons.py` | `frases_largas_ciegas`, `discurso_ciego`, `preguntas_deduccion` |
| parche-50…53 | conceptos y herencia, tiempo, fechas absolutas | `lessons.inherit/canon`, `fechas.py` | `conceptos`, `tiempo`, `herencia`, `fechas` |
| parche-54 (bloque A) | conversación básica | `dialogue.py` | `dialogo`, `dialogo_ciego` |
| parche-55/56 (bloque B) | intransitivos, estados, modales, cantidad, comparaciones, causa, lugar | `extract.py`, `irregulares.py`, `qa.py` | `estados`, `cantidad` (+ciegas) |
| parche-57 (bloque D) | coherencia, cambio de estado, procedencia | `reasoning/coherence.py` | `coherencia` (+ciega) |
| parche-58 (bloque E) | definiciones: sinónimos, contrarios, «sirve para», verbos | `dialogue._definitions`, `lessons.verb_derive` | `definiciones` (+ciegas) |
| parche-59 (bloque C) | núcleo de fábrica: semilla, parentesco, partes, efectos | `semilla.py`, `data/semilla.txt`, `reasoning/efectos.py` | `nucleo` (+ciego) |
| parche-60 | este paquete: reproducibilidad | `scripts/{manifiesto,empaquetar_todo,reproduce}.py`, `get_data.py` | `tests/test_reproducibilidad.py` |

Método (se repite en cada fase): 1) escribir la prueba y el criterio **antes**; 2) medir la línea base; 3) implementar;
4) primera medida (se informa aunque no cumpla); 5) arreglar y medir de nuevo, **etiquetado como reintento**;
6) `python -m scripts.check` para vigilar regresiones; 7) pruebas ciegas con frases distintas.

## 5. Fallos conocidos (también tras reproducir)

La escuela lee «Clara» como adjetivo; «Pedro cocina pasta» como intransitivo; «Un salmón nada»; «muerde/ama … a» (convención
de la «a» personal en el test relajado); «Javier y Ana ven la televisión en el salón» (a quién cuelga el complemento);
«¿Es una figura un triángulo?» (se contesta con la deducción inversa). Están en los informes de `check`: si tu reproducción
muestra **otros**, es una diferencia real que investigar.
''',
    'docs/comoejecutarenservidor.txt': r'''A partir de este momento, ya no tienes que abrir la terminal ni escribir comandos SSH:

Atajo rápido para entrenar en la 4090:

    En tu Mac pulsa: Cmd + Shift + B

    VS Code abrirá un panel inferior, se conectará en milisegundos a la 4090 y verás la barra de tqdm corriendo en directo.

Acceder al menú de tareas:

    Pulsa Cmd + Shift + P > escribe Run Task (o en el menú superior: Terminal > Ejecutar tarea...).

    Te saldrá una lista desplegable con las opciones que definimos:

    🚀 Entrenar en RTX 4090

    ⚡ Entrenar en RTX 3090

    💬 Chat interactivo (en RTX 4090)

    📊 Ver estado GPUs (nvidia-smi)


Para detenerlo:

Simplemente pulsa el icono de la papelera o la X de la terminal integrada en VS Code, o pulsa Ctrl + C sobre ella.

Modificas tus archivos .py en VS Code, pulsas Cmd + Shift + B y tu RTX 4090 se pone a computar al instante sobre el código de tu Mac.''',
    'limpieza.py': r'''"""limpieza.py: deja el proyecto en TABULA RASA y, si quieres, lo vuelve a levantar y a entrenar TODO, con un solo comando.

  python limpieza.py                          # ENSAYO: muestra que se quitaria y que se conserva (no toca nada)
  python limpieza.py --aplicar                # limpia (MUEVE todo a ../LCM_antes_de_tabula_rasa_<fecha>/, recuperable)
  python limpieza.py --aplicar --reconstruir  # limpia y RECONSTRUYE + REENTRENA todo automaticamente (venv, dependencias, tests,
                                              # verificacion, reproduce, comparacion de metricas). No hace falta ningun otro comando.

Que hace, en orden (si algo falla, se para ANTES de quitar nada):
  1. Regenera LCM_construir_desde_cero.py y reproducibilidad/manifiesto.json DESDE TU PROYECTO ACTUAL (para que la reconstruccion
     sea fiel a tu copia, no a otra). Desactivable con --no-refrescar.
  2. Ensayo de reconstruccion: escribe el constructor en una carpeta temporal y comprueba que cada archivo sale IDENTICO al tuyo.
  3. Te pide confirmacion (escribe TABULA RASA).
  4. Mueve (o borra, con --borrar) todo lo del proyecto. Se conserva: limpieza.py, LCM_construir_desde_cero.py, reproducibilidad/,
     .git/, .venv/ y venv/, regenta.* / libro.*, y cualquier archivo de la raiz que no sea del proyecto (tus textos, parche-N.py...).
  5. Con --reconstruir: ejecuta el constructor (modo todo: entorno, tests, verificacion, reentrenamiento y comparacion con la referencia).

Opciones:
  --borrar                 borrar de verdad en vez de mover (sin copia)
  --reconstruir [MODO]     MODO = todo (por defecto) | menu | archivos (solo escribe los archivos)
  --libro RUTA             texto en espanol para el oido (por defecto regenta.rtf/.txt de la raiz)
  --rapido, --semilla N    se pasan al reentrenamiento
  --conservar-ud           no toca data/ud/ (los corpus se pueden bajar de nuevo con scripts.get_data, fijados al commit del manifiesto)
  --conservar ARCHIVO      (repetible) conserva ese archivo o carpeta de la raiz
  --no-refrescar           no regenera el constructor ni el manifiesto (usa los que hay)
  --sin-manifiesto         permite limpiar sin reproducibilidad/manifiesto.json (no recomendado)
"""
import argparse
import datetime
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GENERADOS = {"checkpoints", "memory", "reports", "data", "_archivo", ".parche_backups", ".pytest_cache", "__pycache__", ".vscode", ".github",
             ".DS_Store"}          # carpetas que crea el propio proyecto al usarse
SIEMPRE = {"limpieza.py", "LCM_construir_desde_cero.py", "reproducibilidad", ".git", ".venv", "venv", "env", ".env"}
LIBROS = ("regenta.rtf", "regenta.txt", "libro.txt", "libro.rtf")
FRASE = "TABULA RASA"
BUILDER = "LCM_construir_desde_cero.py"


def tam(p: Path) -> int:
    if p.is_file() or p.is_symlink():
        return p.stat().st_size if p.exists() else 0
    total = 0
    for base, _, files in os.walk(p):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(base, f))
            except OSError:
                pass
    return total


def mb(n: int) -> str:
    return f"{n / 1e6:,.1f} MB"


def leer_constructor(path: Path) -> dict:
    src = path.read_text(encoding="utf-8")
    compile(src, str(path), "exec")
    ns = {}
    exec(src[: src.rindex("\ndef main")] if "\ndef main" in src else src, ns)      # solo el diccionario FILES (no ejecuta main)
    files = ns.get("FILES")
    if not isinstance(files, dict):
        raise ValueError("no encuentro el diccionario FILES")
    return files


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd).returncode == 0


def refrescar(root: Path) -> None:
    """Regenera constructor + manifiesto desde el proyecto actual y comprueba una reconstruccion en una carpeta temporal."""
    if not (root / "scripts" / "empaquetar_todo.py").exists() or not (root / "scripts" / "manifiesto.py").exists():
        sys.exit("[!] Falta scripts/empaquetar_todo.py o scripts/manifiesto.py (instala el parche de reproducibilidad). "
                 "Usa --no-refrescar para limpiar con el constructor que ya tienes.")
    print("1/2 Regenerando el constructor y el manifiesto desde tu proyecto actual ...")
    if not run([sys.executable, "-m", "scripts.empaquetar_todo"], root) or not run([sys.executable, "-m", "scripts.manifiesto", "--guardar"], root):
        sys.exit("[!] No se pudo regenerar el constructor/manifiesto. No se ha tocado nada.")
    print("2/2 Ensayo de reconstruccion en una carpeta temporal ...")
    sys.path.insert(0, str(root))
    from scripts.manifiesto import tracked
    mios = [f for f in tracked(str(root)) if (root / f).is_file()]
    tmp = Path(tempfile.mkdtemp(prefix="lcm_ensayo_"))
    try:
        shutil.copy(root / BUILDER, tmp / BUILDER)
        r = subprocess.run([sys.executable, BUILDER, "--sin-menu"], cwd=tmp, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"[!] El constructor no se ejecuta en limpio:\n{r.stderr[-800:]}\nNo se ha tocado nada.")
        malos = [f for f in mios if f != BUILDER and (not (tmp / f).is_file() or (tmp / f).read_bytes() != (root / f).read_bytes())]
        if malos:
            sys.exit("[!] La reconstruccion NO es identica a tu proyecto en estos archivos (no se limpia nada):\n   " + "\n   ".join(malos[:20]))
        print(f"    OK: {len(mios)} archivos se reconstruyen identicos.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Tabula rasa del proyecto LCM (y reconstruccion opcional)")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--borrar", action="store_true", help="borrar de verdad en vez de mover a ../LCM_antes_de_tabula_rasa_<fecha>")
    ap.add_argument("--reconstruir", nargs="?", const="todo", choices=["todo", "menu", "archivos"])
    ap.add_argument("--libro")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--semilla", type=int)
    ap.add_argument("--conservar-ud", action="store_true")
    ap.add_argument("--conservar", action="append", default=[])
    ap.add_argument("--no-refrescar", action="store_true")
    ap.add_argument("--sin-manifiesto", action="store_true")
    a = ap.parse_args()

    root = Path.cwd()
    if not (root / "src").is_dir() or not (root / "scripts").is_dir():
        sys.exit("[!] Ejecuta esto desde la raiz del proyecto LCM (donde estan src/ y scripts/).")
    builder = root / BUILDER
    if a.aplicar and not a.no_refrescar:
        refrescar(root)                          # antes de quitar NADA; si falla, se para aqui
    if not builder.exists():
        sys.exit(f"[!] Falta {BUILDER} en la raiz: sin el no podrias reconstruir nada. Crealo con:  python -m scripts.empaquetar_todo")
    try:
        files = leer_constructor(builder)
    except Exception as exc:
        sys.exit(f"[!] {BUILDER} no es valido ({type(exc).__name__}: {exc}). Regeneralo con scripts.empaquetar_todo.")
    if len(files) < 50:
        sys.exit(f"[!] {BUILDER} solo contiene {len(files)} archivos: parece incompleto. Regeneralo con scripts.empaquetar_todo.")
    if not (root / "reproducibilidad" / "manifiesto.json").exists() and not a.sin_manifiesto:
        sys.exit("[!] Falta reproducibilidad/manifiesto.json. Crealo con:  python -m scripts.manifiesto --guardar     (o usa --sin-manifiesto)")

    keep_names = set(SIEMPRE) | set(LIBROS) | set(a.conservar)
    del_names = {rel.split("/")[0] for rel in files} | GENERADOS
    keep, remove = [], []
    for p in sorted(root.iterdir(), key=lambda x: x.name):
        if p.name in keep_names:
            keep.append((p, "se conserva"))
        elif p.name not in del_names:
            keep.append((p, "se conserva: no es del proyecto (tuyo)"))
        elif p.name == "data" and a.conservar_ud and (p / "ud").exists():
            keep.append((p / "ud", "se conserva (corpus UD)"))
            remove += [q for q in sorted(p.iterdir()) if q.name != "ud"]
        else:
            remove.append(p)

    print(f"\nProyecto: {root}")
    print(f"Constructor valido: {BUILDER} ({len(files)} archivos)\n")
    print("SE CONSERVA:")
    for p, why in keep:
        print(f"   = {p.relative_to(root)}{'/' if p.is_dir() else ''}   ({why})")
    print("\nSE QUITA:")
    total = 0
    for p in remove:
        s = tam(p)
        total += s
        print(f"   - {p.relative_to(root)}{'/' if p.is_dir() else ''}   {mb(s)}")
    print(f"\nTotal a quitar: {len(remove)} elementos, {mb(total)}")
    destino = None
    if not a.borrar:
        destino = root.parent / ("LCM_antes_de_tabula_rasa_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        print(f"Destino (recuperable): {destino}")
    else:
        print("MODO BORRAR: sin copia, no se puede deshacer.")
    if a.reconstruir:
        print(f"Despues se reconstruye en modo '{a.reconstruir}'" + (" y se reentrena TODO." if a.reconstruir == "todo" else "."))
    if not a.aplicar:
        print("\n[ENSAYO] No se ha tocado nada. Para hacerlo:  python limpieza.py --aplicar" + (" --borrar" if a.borrar else "")
              + " --reconstruir" * (not a.reconstruir) + "   (con --reconstruir se vuelve a levantar y entrenar todo solo)")
        return
    if not remove:
        print("[OK] Ya esta en tabula rasa.")
    else:
        print(f"\nEscribe exactamente  {FRASE}  para continuar (cualquier otra cosa cancela): ", end="")
        if input().strip() != FRASE:
            sys.exit("\n[CANCELADO] No se ha tocado nada.")
        if destino:
            destino.mkdir(parents=True, exist_ok=False)
        for p in remove:
            if destino:
                shutil.move(str(p), str(destino / p.name))
            elif p.is_dir() and not p.is_symlink():
                shutil.rmtree(p)
            else:
                p.unlink()
        print(f"\n[HECHO] {len(remove)} elementos {'movidos a ' + str(destino) if destino else 'borrados'}.")
    if not a.reconstruir:
        print("Ahora:  python LCM_construir_desde_cero.py        (escribe todo y abre el menu; la opcion 7 lo hace todo en orden)")
        return
    cmd = [sys.executable, BUILDER]
    if a.reconstruir == "archivos":
        cmd.append("--sin-menu")
    elif a.reconstruir == "todo":
        cmd.append("--todo")
        if a.libro:
            cmd += ["--libro", a.libro]
        if a.rapido:
            cmd.append("--rapido")
        if a.semilla is not None:
            cmd += ["--semilla", str(a.semilla)]
    print("\n=== Reconstruyendo: " + " ".join(os.path.basename(c) if i == 0 else c for i, c in enumerate(cmd)) + " ===\n", flush=True)
    sys.exit(subprocess.run(cmd, cwd=root).returncode)


if __name__ == "__main__":
    main()
''',
    'reports/RESULTADOS.md': r'''# Resultados de referencia

Medidos en un Mac con GPU (MPS), semilla por defecto. Con otra maquina o semilla los numeros bailan unos puntos
(el test de conversacion tiene solo 80 frases: 1 frase = 1,25 puntos). Los criterios se fijaron ANTES de medir.

| Medida | Resultado | Criterio | |
|---|---|---|---|
| Oido, test c (lenguaje del libro, tras preentrenar) | 94,1 % | - | ok |
| Oido, test d | 84,1 % | - | ok |
| Falsos positivos de negativos / fantasmas | 2 % / 2 % | <= 5 % | ok |
| Escuela v2: UPOS / UAS / lema | 96,2 / 86,8 / 98,1 % | - | ok |
| Conversacion (60 frases), escuela v1 -> v2 | 68,3 -> 90,0 % relajado (85 % exacto) | >= 75 % y +10 | ok |
| Triples en UD (prensa) | 35 % | 60 % | NO CUMPLE (frases largas/complejas siguen flojas) |
| Test de preguntas (Fase 1), 19 preguntas | 68,4 % la primera vez (NO CUMPLE); 89,5 % tras arreglar 2 fallos conocidos (reintento) | >= 70 % | ok (reintento); 19/19 tras parche-38 |
| Test de preguntas CIEGO (31 preguntas, una sola medida) | 93,5 % (29/31) | >= 80 % | ok |

## Fase 2 (frases largas y discurso)

| Medida | Resultado | Criterio | |
|---|---|---|---|
| Frases largas ciegas (27): linea base -> con coordinaciones -> + nombre ADJ | 37,0 -> 88,9 -> 92,6 % | >= 60 % | ok |
| Conversacion (80 frases) tras Fase 2 | 91,2 % relajado / 86,2 % exacto | >= 90,0 % (no regresion) | ok |
| Discurso ciego (21 textos de 2 frases): linea base -> tema/sujeto omitido -> + pronombres DET/PRON, 3 palabras, minuscula inicial | 9,5 -> 71,4 -> 95,2 % | >= 70 % | ok |
| Preguntas con deduccion por reglas "Si... entonces..." (12 preguntas, escrito antes de medir) | 91,7 % la primera medida (11/12); 100 % tras arreglar la lectura de un si/no ambiguo (post-arreglo) | >= 75 % | ok |

Correccion: hasta el parche-46 el "Lo deduzco" de las preguntas solo usaba las relaciones fijas del motor simbolico, NO las reglas que ensena el usuario;
desde el parche-47 se aplican las lecciones aprendidas (src/reasoning/lessons.py) y se explica de que hechos sale la conclusion.

## Fase 3 (integrar conceptos nuevos desde lenguaje natural)

| Medida | Resultado | Criterio | |
|---|---|---|---|
| Correcciones a la escuela con ENTENDI (3 ensenadas, 16 frases nuevas): 1a medida -> 2a (retry) | 1a: NO CUMPLE (2/3 y largas 92,6 -> 85,2) ; 2a: 3/3, 16/16, conversacion 91,2 -> 95,0 | ver data/correcciones_prueba.tsv | ok (retry) |
| Conceptos (14 preguntas: definiciones, jerarquia con deduccion, acciones "Cocinar es una accion", propiedades con numeral) | 85,7 % la 1a medida (12/14); 92,9 % tras 1 arreglo (retry: lectura con mayuscula inicial) | >= 75 % | ok |
| Expresiones temporales (14 preguntas: ayer, el lunes, en 2020, en verano, "cuando", si/no con tiempo) | 85,7 % la 1a medida (12/14); 92,9 % tras 1 arreglo (retry: orden de "donde" con verbo transitivo) | >= 75 % | ok |

Fallo que queda en tiempo: "¿Cuando compra Pedro pan?" -> la escuela lee mal "Pedro compra pan." (compra como nombre compuesto): se corrige con ENTENDI.
Limite: solo eventos con objeto/complemento (intransitivos como "Pedro llego ayer" no tienen hueco para la proposicion); sin orden entre fechas todavia.

Fallo que queda en conceptos: "¿Es una figura un triangulo?" (la escuela lee el sujeto al reves en la interrogativa invertida).
Regresion que provoque y corregi el mismo dia (la regla de "¿Quien es X?" secuestraba "¿Quien es el padre de Clara?"): la detecto `check` (preguntas 100 -> 94,7 %).

Limites vistos en la Fase 2: la escuela lee mal algunas frases (p. ej. "Lucia cocina pasta" como nombre propio compuesto); "la television en el salon"
es ambiguo (el complemento cuelga del nombre).

Fallos del test ciego: «¿Qué lee Rosa?» (la escuela no lee «Rosa lee Xqx.») y «¿Enseña la maestra matemáticas?» (la reescritura con verbo antes del sujeto falla si hay articulo).

Fracasos conocidos: frases largas o con varias proposiciones; convenciones de lema irregulares; no hay correferencia
(pronombres) ni dialogo de varias frases todavia.


### Fase 3, paso 3: herencia de propiedades (parche-52)
- "Los polígonos tienen lados" + "Un triángulo es un polígono" => "el triángulo tiene lados" (con explicación). Solo hacia abajo; no sube ni pasa entre hermanos.
- Primera medida (test escrito antes, criterio >= 75 %): 9/10 = 90 % CUMPLE. Fallo: "¿Tiene un pájaro alas?" (singular/plural).
- Reintento tras arreglar la búsqueda singular/plural (`canon`): 10/10 = 100 % (reintento, no primera medida). Sin regresiones en el resto.


### Fase 3, paso 4: fechas absolutas y orden (parche-53)
- Idea del usuario: lo relativo ("ayer", "el lunes", "el año pasado") se guarda como fecha absoluta anclada a "hoy" (`Hoy es 6 de noviembre de 2026`, o la fecha real por defecto). También se entienden fechas escritas ("el 5 de noviembre").
- Preguntas nuevas: "¿Qué pasó primero / último / antes del X / después del X?"; "¿Cuándo…?" responde con la fecha absoluta.
- Primera medida (data/fechas_prueba.tsv, escrito antes, criterio >= 75 %): 16/18 = 88,9 % CUMPLE. Fallos: "anteayer" leído como adjetivo del objeto; la fecha escrita sin año se mostraba sin año.
- Reintento tras arreglar ambos: 18/18 = 100 % (reintento, no primera medida). Sin regresiones.
- Convenios: "el lunes" = el último ya pasado; "próximo" mira al futuro; mes suelto = el más reciente; estaciones del hemisferio norte.


### Fase 3, bloque A de NUCLEO_BASICO: conversación básica (parche-54)
- Módulo `src/language/dialogue.py` (reglas explícitas, sin LLM): saludos/gracias/perdona/adiós, sí/no/vale/exclamaciones, tú/usted, nombre del usuario, "¿quién eres?", "¿qué sabes (de X)?", "¿qué te he dicho?", fecha, repite, olvida (con confirmación si son varios), aclaración al no entender, preguntar "¿qué es X?" y aprender de la respuesta, referencias (mi/yo, este/ese, también/tampoco/otra vez, "eso es falso", "¿y Ana?").
- Test propio (data/dialogo_prueba.tsv, escrito antes, criterio >= 75 %): primera medida 64/65 = 98,5 %; el fallo ("Mi hermano es Pedro" tras pedir el nombre no se reprocesaba) se arregló y el reintento da 65/65 (reintento, no primera medida). OJO: el test lo escribí yo con las mismas ideas que las reglas, así que es optimista.
- Test ciego (data/dialogo_ciego.tsv, frases distintas, escritas antes, criterio >= 60 %): primera medida 34/37 = 91,9 %. Fallos: "Háblame de Clara" (la escuela lee «Clara» como adjetivo, es un fallo del analizador, no de la conversación), "¿Qué hemos hablado?" (mismo motivo) y "Estoy equivocado" (patrón que faltaba; añadido -> reintento 35/37).
- Límites conocidos: el nombre del usuario no se guarda entre sesiones; "mi/yo" solo se resuelve con nombre conocido; las respuestas son plantillas fijas; "hoy es" vs hora real solo se usa para "¿qué hora es?".


### Fase 3, bloque B de NUCLEO_BASICO: intransitivos, estados, modales, "X dice que" (parche-55)
- Nuevo: verbos sin objeto -> (s, verbo, "_"); adjetivos con ser/estar -> (s, SER|ESTAR, adjetivo); modales -> PODER_/DEBER_/QUERER_ + infinitivo; "X dice/cree/piensa que ..." se guarda como DICE_QUE y NO como hecho (la frase subordinada no se afirma). Preguntas: ¿qué hace X?, ¿cómo es/está X?, ¿es grande X?, ¿qué dice X?, ¿quién cree que ...?
- Arreglo de la escuela sin reentrenar: "Ana duerme." / "Andrés cocina pasta." se leían como nombre compuesto (flat en minúscula); ahora el verbo se recupera (`_fix_name_verb`) y hay una lista de verbos irregulares comunes (`irregulares.py`).
- Primera medida (data/estados_prueba.tsv, escrito antes, criterio >= 70 %): 19/27 = 70,4 % (CUMPLE por muy poco). Tras corregir (reintento, no primera medida): 27/27 = 100 %.
- Test ciego (data/estados_ciegas.tsv, criterio >= 60 %): primera medida 17/18 = 94,4 %; el fallo ("vino" leído como el sustantivo) se arregló -> reintento 18/18.
- Efecto colateral medido: largas_ciegas 92,6 -> 96,3 %, tiempo 92,9 -> 100 %, discurso 95,2 -> 100 %. Sin regresiones.
- Pendiente del bloque B: cuantificadores (todos/algunos/ninguno) y números como operaciones (13), duración/frecuencia/hora (14), causa "por qué" (15), lugar relativo arriba/abajo/cerca (16), comparaciones; "Todos los perros ladran" aún se lee mal.


### Fase 3, bloque B parte 2 (parche-56): cuantificadores, números, comparaciones, frecuencia/hora, causa, lugar relativo
- Nuevo: "algunos/varios/muchos X ..." se guarda con marca (no se hereda ni se responde "sí" a la ligera); "ninguno/a" -> hecho negado; "tiene tres hijos" + "¿cuántos hijos tiene X?"; "¿a cuántos ama Ana?" cuenta; comparaciones (más/menos ... que) con inversa y transitividad ("Luis > Pedro > Juan => Luis > Juan"; "¿Es Juan más alto que Luis?" -> No); frecuencia (siempre, normalmente...) y hora ("a las tres") como tiempo; causa ("Ana llora porque está triste" guarda el hecho y la causa por separado, "¿Por qué llora Ana?"); lugar relativo (encima/debajo/delante/cerca/lejos de..., "¿Dónde está el libro?").
- Arreglos de la escuela sin reentrenar: verbos leídos como NOUN/ADV ("Un pájaro vuela", "Los peces nadan"), nombre tras "que" en comparaciones, más verbos irregulares (cenar, sonreír, volar...), "venir" ya no se confunde con "vender" en la búsqueda relajada.
- Test propio (data/cantidad_prueba.tsv, escrito antes, criterio >= 70 %): primera medida 21/26 = 80,8 %; reintento 26/26 (reintento, no primera medida).
- Test ciego (data/cantidad_ciegas.tsv, criterio >= 60 %): primera medida 7/14 = 50,0 % -> NO CUMPLIA. Tras arreglar lectura de verbos y comparaciones (reintento): 11/14 = 78,6 %. Fallos que quedan: "Un salmón nada" (nada = pronombre/verbo), y dos preguntas con "Clara" (la escuela lee Clara como adjetivo).
- Sin regresiones en el resto de métricas (38 -> 40 tests).
- Límites: "Ninguna rana es mamífero" se verbaliza como "No es cierto que ninguna rana es mamífero"; la duración ("durante tres horas") se guarda como relación normal, sin cálculo; no hay superlativos ("el más alto").


### Fase 3, bloque D de NUCLEO_BASICO: coherencia (parche-57)
- Cambio de estado: «Ana vive en Madrid» + «Ana vive en Sevilla» => el hecho viejo pasa a PASADO (no se borra): «¿Dónde vive Ana?» -> Sevilla; «¿Dónde vivía Ana?» -> Madrid (hasta el ...). También «Pedro ya no trabaja en X».
- Contradicciones que no se resuelven solas (adjetivos opuestos con «ser», afirmar y negar lo mismo): pregunta «¿Cuál es correcta: la nueva, la anterior o las dos?» y obedece.
- Procedencia: «¿Cómo lo sabes?» / «¿Cómo sabes que X?» -> me lo dijiste (con fecha y tus palabras) / lo deduje (con explicación) / lo dijo otro (no lo sé por mí) / no lo sé.
- Test propio (data/coherencia_prueba.tsv, escrito antes, criterio >= 70 %): línea base antes de implementar 18/29 = 62,1 %; primera medida con lo implementado 29/29 = 100 % (no hubo reintento). Es optimista: lo escribí yo.
- Test ciego (data/coherencia_ciega.tsv, frases distintas, criterio >= 60 %): primera medida 18/19 = 94,7 %. Único fallo: «Clara no compra leche» (la escuela no lee bien «Clara»).
- Límites: solo las relaciones vivir/trabajar/estudiar en, estar en y estar + estado cambian de estado solas; con una fecha explícita («vivió en 2020») no se sustituye; «¿Cómo lo sabes?» tras una pregunta en pasado explica el hecho vigente; lista corta de antónimos.


### Fase 3, bloque E de NUCLEO_BASICO: aprender palabras por definición (parche-58)
- Nuevo: sinónimos («Un coche es lo mismo que un automóvil», «Bici significa bicicleta») que valen al preguntar; contrarios enseñados («Alto es lo opuesto de bajo», «¿Es X lo contrario de Y?») que también avisan de contradicciones; función («Un tenedor sirve para comer», «¿Para qué sirve…?», «¿Qué sirve para…?»); verbos definidos («Cocinar es preparar comida con calor»: si Pedro cocina algo, también lo prepara; «¿Qué es cocinar?»); género + diferencia («Un gorrión es un pájaro pequeño» guarda también «pequeño»); «Un X es un Y que sirve para Z».
- Arreglos: «¿Es un gorrión un pájaro?» (dos sustantivos) ya no se lee al revés ni se toma por adjetivo; «¿Cómo lo sabes?» funciona tras preguntas especiales.
- Test propio (data/definiciones_prueba.tsv, escrito antes, criterio >= 70 %): línea base 14/29 = 48,3 %; primera medida con lo implementado 24/29 = 82,8 %; reintento tras arreglar los fallos 28/29 = 96,6 % (reintento, no primera medida). Fallo que queda: «Pedro cocina pasta» la escuela lo lee como intransitivo (con «la pasta» sí funciona).
- Test ciego (data/definiciones_ciegas.tsv, criterio >= 60 %): primera medida 21/21 = 100 %. Ojo: es optimista, lo escribí yo y es más fácil que el propio.
- Sin regresiones en el resto de métricas; 45 tests.
- Límites: sinónimos solo de una palabra; el verbo definido solo hereda el primer verbo de la definición; la definición se guarda como texto y no se razona con ella; el mismo texto sirve para una sola función por cosa al contestar.


### Fase 3, bloque C de NUCLEO_BASICO: núcleo de fábrica (parche-59)
- Conocimiento de fábrica = FRASES en español (data/semilla.txt, 110 hechos: colores, formas, naturaleza, meses/días/estaciones, cuerpo, emociones, necesidades, objetos, dinero, opuestos, sinónimos) cargadas con el mismo camino que cualquier frase (src/language/semilla.py). Quedan con fuente «semilla»: «¿Cómo lo sabes?» dice que es conocimiento de fábrica, y no cuentan como «lo que me has dicho».
- Reglas de fábrica sin enseñar: hijo (de padre/madre), abuelo/a, nieto/a, hermano/a (inversa y mismos padres), tío/a, primo/a, esposo/a, «parte de» transitivo y «parte de» => «tiene».
- Efectos de acciones (src/reasoning/efectos.py): dar/regalar/vender/prestar/entregar (quien da deja de tener, quien recibe tiene), comprar/recibir/ganar (tiene), perder; abrir/cerrar/romper/encender/apagar/terminar... (estado del objeto, con género: «la puerta está abierta»; el estado viejo pasa a pasado); ir/llegar/volver/entrar (dónde está). «Ana da un libro a Luis» ahora guarda también «dar_a Luis».
- Nuevas preguntas: «¿De qué color es X?», «¿Cuál es lo contrario de X?», «¿Qué significa X?», «¿Qué es el lunes?», y las preguntas abiertas («¿Qué tiene el coche?») incluyen lo deducido. «¿Es un cuadrado una figura?» (dos sustantivos) ya no se lee como adjetivo.
- Test propio (data/nucleo_prueba.tsv, escrito antes, criterio >= 70 %): primera medida 39/44 = 88,6 %; reintento tras arreglar 5 fallos 44/44 (reintento, no primera medida).
- Test ciego (data/nucleo_ciego.tsv, criterio >= 60 %): primera medida 22/25 = 88,0 %; reintento tras arreglar 3 fallos 25/25 (los arreglos se hicieron tras ver el ciego: ya no es del todo ciego). Ojo: ambos los escribí yo, son optimistas.
- Sin regresiones (47+ tests; un ajuste: los hechos de «efecto» y «semilla» no cuentan en «¿Cuántas cosas sabes?» ni en «Olvida todo»).
- Límites: género de hermano/tío no se distingue al deducir (Marta hermana de Rosa => Rosa «hermano» de Marta); sin precios ni cantidades de dinero; ir_a se toma como llegada; cada objeto sólo cambia de dueño en frases con «dar/vender…a alguien»; la semilla es corta (110 hechos) y se amplía añadiendo líneas a semilla.txt.

### parche-60: reproducibilidad (sin cambios de metricas)
- Arreglos vistos en una sesion real de `think`: «Ana da el libro a Luis» no movia el libro porque `think` entrega los nombres en MAYUSCULAS (los efectos ahora normalizan); los hechos de efecto/semilla se verbalizan bien («La puerta está abierta», «Ana está en Madrid», «La hierba es verde»).
- Paquete de reproducibilidad: `scripts/manifiesto.py`, `scripts/empaquetar_todo.py`, `scripts/reproduce.py` ampliado (tests, check, semilla global, resumen JSON, verificacion), `get_data` con commit fijado, `docs/REPRODUCIR.md`, `tests/test_reproducibilidad.py` (ida y vuelta del empaquetado en una carpeta vacia: archivos identicos, 48 -> 51 tests).
- Comprobado en el sandbox: carpeta vacia + LCM_construir_desde_cero.py => 116 archivos identicos al proyecto y los tests pasan. NO se ha reentrenado nada desde cero en el sandbox (sin GPU ni tu libro); ese paso (`scripts.reproduce`) hay que verificarlo en tu maquina.

### parche-61: constructor interactivo
- `LCM_construir_desde_cero.py` abre un menu guiado tras escribir los archivos (entorno, tests, verificar codigo, reentrenar, comparar resultados, hablar con el modelo, todo en orden) y admite `--sin-menu` / `--todo --libro X [--rapido] [--semilla N]`. Probado en el sandbox con un pseudo-terminal (opcion de tests: 51 passed); NO probado: las opciones 1 (instalar dependencias) y 4 (reentrenar), que necesitan red y GPU. Solo biblioteca estandar.

### parche-62: primer intento real en tabula rasa (usuario) y lo que destapo
- `python limpieza.py` + `LCM_construir_desde_cero.py` + menu 4: el razonador se reentreno bien (34 epocas, 100 % en test, 187 s). Fallo REAL: `read_book` exigia `checkpoints/ear.pt` (que se entrena despues), asi que `reproduce` nunca habria funcionado desde cero. Arreglo: `read_book` guarda libro.txt y vocabulario y salta la medicion si aun no hay oido; el orden es read_book -> pretrain_ear -> train_ear y se anade `read_book_medida` al final del oido.
- `manifiesto --verificar --metricas` ya no falla con traza si `scripts.check` no puede terminar (explica que faltan pesos).
- El verificador encontro 9 archivos distintos mas 1 FALTA y 1 SOBRA respecto al manifiesto del usuario: el constructor se habia generado en el sandbox, no en su copia real. Leccion documentada en docs/REPRODUCIR.md: generar siempre el constructor y el manifiesto en el proyecto real.

### parche-63: limpieza + reconstruccion automatica
- `limpieza.py --aplicar --reconstruir`: regenera constructor y manifiesto desde el proyecto actual, ensaya la reconstruccion en una carpeta temporal (todos los archivos deben salir identicos o se aborta antes de borrar nada), pide confirmacion, limpia y ejecuta el constructor en modo `--todo` (entorno, dependencias, tests, verificacion, reentrenamiento, comparacion de metricas). El constructor pregunta tambien, al abrir el menu sin pesos, si lo hace todo automaticamente.
- Probado en el sandbox: limpieza + reconstruir 'archivos' (118 archivos, tests y manifiesto fieles) y arranque de `--todo` (crea .venv e instala). NO probado aqui: el reentrenamiento completo posterior.
''',
    'requirements.txt': r'''torch>=2.1.0
numpy>=1.24.0
tqdm>=4.66.0
pytest>=7.0
''',
    'scripts/check.py': r'''"""UN comando para comprobarlo todo (parche-45): tests unitarios + las 6 evaluaciones + diagnostico automatico + comparacion con la
ejecucion anterior. Escribe reports/informe.txt (es lo unico que hace falta pegar/subir) y reports/historial.json.

  python -m scripts.check

Los criterios son los fijados antes de medir en cada test (ver sus docstrings); aqui solo se aplican. Para cada frase fallida se
imprime el ARBOL que lee la escuela, asi no hace falta pedirlo aparte.
"""
import datetime
import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stdout

import torch

from scripts.eval_frases import evaluate
from scripts.eval_preguntas import add_rule, blocks, make_deduce, ok
from src.language.discourse import parse_text, split_sentences
from src.language.qa import QA
from src.language.school_parser import SchoolParser
from src.language.ud import load_school
from src.memory.store import MemoryStore
import tempfile

FRASES = [("conversacion_80", "data/frases_prueba.tsv", .75), ("largas_ciegas_27", "data/frases_largas_ciegas.tsv", .60)]
PREGUNTAS = [("cantidad_26", "data/cantidad_prueba.tsv", .70), ("cantidad_ciegas_14", "data/cantidad_ciegas.tsv", .60), ("estados_27", "data/estados_prueba.tsv", .70), ("estados_ciegas_18", "data/estados_ciegas.tsv", .60), ("fechas_18", "data/fechas_prueba.tsv", .75), ("herencia_10", "data/herencia_prueba.tsv", .75), ("tiempo_14", "data/tiempo_prueba.tsv", .75), ("conceptos_14", "data/conceptos_prueba.tsv", .75), ("deduccion_12", "data/preguntas_deduccion.tsv", .75), ("preguntas_19", "data/preguntas_prueba.tsv", .70), ("preguntas_ciegas_31", "data/preguntas_ciegas.tsv", .80)]
DISCURSO = [("discurso_21", "data/discurso_ciego.tsv", .70)]


def tree_lines(parser, sentence):
    try:
        return ["      " + " ".join(f"{i + 1}:{w[0]}/{w[1]}->{w[2]}:{w[3]}" for i, w in enumerate(parser.tree(sentence)))]
    except Exception as exc:                                  # noqa
        return [f"      (sin arbol: {exc})"]


def main():
    out, metrics, ok_all = [], {}, True
    log = lambda s="": out.append(s)
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], capture_output=True, text=True)
    log("TESTS UNITARIOS: " + (r.stdout.strip().splitlines() or ["?"])[-1])
    ok_all &= r.returncode == 0
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    parser = SchoolParser(model, device, scripts)

    for name, path, limit in FRASES:
        ex, rl, pr, rc, rows = evaluate(parser, path=path)
        metrics[name] = round(rl, 4)
        good = rl >= limit
        ok_all &= good
        log(f"\n{name}: {rl:.1%} relajado / {ex:.1%} exacto, precision {pr:.1%}, cobertura {rc:.1%}  (criterio >= {limit:.0%}: {'CUMPLE' if good else 'NO CUMPLE'})")
        for sent, g, p, okk in rows:
            if not okk:
                log(f"   FALLO {sent}\n      esperado {sorted(g)}\n      obtenido {sorted(p)}")
                for l in tree_lines(parser, sent):
                    log(l)

    for name, path, limit in PREGUNTAS:
        total = good_n = 0
        bad = []
        for b in blocks(path):
            with tempfile.TemporaryDirectory() as d:
                mem = MemoryStore(os.path.join(d, "m.json"))
                from datetime import date as _date
                mem.today = parser.today = _date.fromisoformat(b["HOY"]) if b.get("HOY") else None
                for sent in b["H"]:
                    for t in parser.parse(sent) or []:
                        tr = (t["s"], t["p"], t["o"])
                        mem.add_fact(tr, source=sent, neg=t["neg"], when=t.get("when", ""), when_disp=t.get("when_disp", ""), quant=t.get("q", ""))
                        mem.note_surface(tr, t.get("template"), t.get("s_disp"), t.get("o_disp"))
                for rule in b.get("R", []):
                    add_rule(mem, parser, rule)
                qa = QA(mem, parser.parse, make_deduce(mem))
                for q, exp in b["P"]:
                    ans = qa.answer(q)
                    total += 1
                    if ok(ans, exp):
                        good_n += 1
                    else:
                        bad.append((q, exp, ans))
        rate = good_n / max(total, 1)
        metrics[name] = round(rate, 4)
        good = rate >= limit
        ok_all &= good
        log(f"\n{name}: {good_n}/{total} = {rate:.1%}  (criterio >= {limit:.0%}: {'CUMPLE' if good else 'NO CUMPLE'})")
        for q, exp, ans in bad:
            log(f"   FALLO {q} esperado={exp} obtenido={ans}")

    from scripts.eval_frases import key, load_gold
    for name, path, limit in DISCURSO:
        gold = load_gold(path)
        n = good_n = 0
        for text, g in gold:
            n += 1
            pred = {(t["s"], key(t["p"]), t["o"], t["neg"]) for t in parse_text(parser, text)}
            gk = {(s, key(p), o, ng) for s, p, o, ng in g}
            if pred == gk:
                good_n += 1
            else:
                log(f"   FALLO {text}\n      esperado {sorted(gk)}\n      obtenido {sorted(pred)}")
                for s in split_sentences(text):
                    for l in tree_lines(parser, s):
                        log(l)
        rate = good_n / max(n, 1)
        metrics[name] = round(rate, 4)
        good = rate >= limit
        ok_all &= good
        log(f"\n{name}: {good_n}/{n} = {rate:.1%}  (criterio >= {limit:.0%}: {'CUMPLE' if good else 'NO CUMPLE'})")

    from scripts.eval_dialogo import run as run_dialogo
    g, t, bad = run_dialogo("data/dialogo_prueba.tsv")
    rate = g / max(t, 1)
    metrics["dialogo_%d" % t] = round(rate, 4)
    ok_all &= rate >= .75
    log(f"\ndialogo_{t}: {g}/{t} = {rate:.1%}  (criterio >= 75%: {'CUMPLE' if rate >= .75 else 'NO CUMPLE'})")
    for turn, exp, ans in bad:
        log(f"   FALLO {turn} esperado={exp} obtenido={ans}")

    g, t, bad = run_dialogo("data/dialogo_ciego.tsv")
    rate = g / max(t, 1)
    metrics["dialogo_ciego_%d" % t] = round(rate, 4)
    ok_all &= rate >= .60
    log(f"\ndialogo_ciego_{t}: {g}/{t} = {rate:.1%}  (criterio >= 60%: {'CUMPLE' if rate >= .60 else 'NO CUMPLE'})")
    for turn, exp, ans in bad:
        log(f"   FALLO {turn} esperado={exp} obtenido={ans}")

    for name, path, limit in (("coherencia", "data/coherencia_prueba.tsv", .70), ("coherencia_ciega", "data/coherencia_ciega.tsv", .60),
                             ("definiciones", "data/definiciones_prueba.tsv", .70), ("definiciones_ciegas", "data/definiciones_ciegas.tsv", .60),
                             ("nucleo", "data/nucleo_prueba.tsv", .70), ("nucleo_ciego", "data/nucleo_ciego.tsv", .60)):
        g, t, bad = run_dialogo(path)
        rate = g / max(t, 1)
        metrics[f"{name}_{t}"] = round(rate, 4)
        ok_all &= rate >= limit
        log(f"\n{name}_{t}: {g}/{t} = {rate:.1%}  (criterio >= {limit:.0%}: {'CUMPLE' if rate >= limit else 'NO CUMPLE'})")
        for turn, exp, ans in bad:
            log(f"   FALLO {turn} esperado={exp} obtenido={ans}")

    hist_path = "reports/historial.json"
    hist = json.load(open(hist_path)) if os.path.exists(hist_path) else []
    if hist:
        prev = hist[-1]["metrics"]
        log("\nCAMBIOS respecto a la ejecucion anterior (" + hist[-1]["fecha"] + "):")
        for k, v in metrics.items():
            if k in prev and abs(v - prev[k]) > 1e-9:
                log(f"   {k}: {prev[k]:.1%} -> {v:.1%}  {'MEJORA' if v > prev[k] else 'EMPEORA'}")
        if all(abs(v - prev.get(k, v)) < 1e-9 for k, v in metrics.items()):
            log("   (sin cambios)")
    hist.append({"fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "metrics": metrics})
    os.makedirs("reports", exist_ok=True)
    json.dump(hist, open(hist_path, "w"), indent=1)
    log(f"\nRESUMEN: {'TODO CUMPLE' if ok_all else 'HAY CRITERIOS QUE NO SE CUMPLEN'}  " + json.dumps(metrics))
    text = "\n".join(out)
    open("reports/informe.txt", "w", encoding="utf-8").write(text)
    print(text)
    print("\n[Informe guardado en reports/informe.txt: pegame ese fichero entero]")


if __name__ == "__main__":
    main()
''',
    'scripts/clean.py': r'''"""Limpieza del proyecto (parche-40). Por defecto solo MUESTRA lo que haria; con --aplicar lo hace.
Nada se borra a ciegas: lo dudoso se MUEVE a _archivo/<fecha>/ (ignorado por git) y se puede recuperar.
Se borran solo cosas regenerables (__pycache__, .pytest_cache). NO toca: data/, checkpoints/, memory/, src/, tests/.

  python -m scripts.clean              # ver
  python -m scripts.clean --aplicar    # hacer
"""
import datetime
import shutil
import sys
from pathlib import Path

KEEP_BACKUPS = 3
ARCHIVE = ["scripts/learn_book.py", "reports/libro_hechos.txt"]       # abandonados: el objetivo es aprender espanol, no el libro
MOVE_DOCS = {"comoejecutarenservidor.txt": "docs/comoejecutarenservidor.txt"}


def main():
    apply = "--aplicar" in sys.argv
    root = Path.cwd()
    if not (root / "src").is_dir():
        sys.exit("[!] Ejecuta esto desde la raiz del proyecto.")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    arch = root / "_archivo" / stamp
    todo = []
    for d in list(root.rglob("__pycache__")) + list(root.rglob(".pytest_cache")):
        if ".venv" in d.parts or "venv" in d.parts or "_archivo" in d.parts:
            continue
        todo.append(("borrar", d))
    for p in sorted((root / "reports").glob("reproduce_*.log")) + sorted((root / "reports").glob("libro_muestras.txt")):
        todo.append(("archivar", p))
    for rel in ARCHIVE:
        if (root / rel).exists():
            todo.append(("archivar", root / rel))
    for p in sorted((root / "memory").glob("*.tmp")) if (root / "memory").is_dir() else []:
        todo.append(("archivar", p))
    backups = sorted(p for p in (root / ".parche_backups").glob("*") if p.is_dir()) if (root / ".parche_backups").is_dir() else []
    for p in backups[:-KEEP_BACKUPS]:
        todo.append(("archivar", p))
    for src, dst in MOVE_DOCS.items():
        if (root / src).exists() and not (root / dst).exists():
            todo.append(("a docs/", root / src))
    if not todo:
        print("[OK] Nada que limpiar.")
        return
    for action, p in todo:
        print(f"  {action:9s} {p.relative_to(root)}")
        if not apply:
            continue
        if action == "borrar":
            shutil.rmtree(p, ignore_errors=True)
        elif action == "a docs/":
            (root / "docs").mkdir(exist_ok=True)
            shutil.move(str(p), str(root / MOVE_DOCS[p.name]))
        else:
            dest = arch / p.relative_to(root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), str(dest))
    print(f"\n[{'HECHO' if apply else 'ENSAYO'}] {len(todo)} elementos." +
          ("" if apply else "  Repite con --aplicar para hacerlo."))


if __name__ == "__main__":
    main()
''',
    'scripts/compare_ear.py': r'''"""Compara el oido CON y SIN preentrenamiento con varias semillas (parche-27).

Una sola pasada no distingue efecto de ruido: entre reentrenamientos 'b' ya se movio varios puntos sin cambiar nada
relevante. Aqui se entrena y evalua  EAR_PRE=0  y  EAR_PRE=1  con 3 semillas cada uno y se comparan las MEDIAS.

REGLA DE DECISION (fijada antes de medir; es la misma de pretrain_ear, aplicada a medias):
  preentrenar se adopta si, en medias, a, b, f, g no bajan mas de 1 punto y d o e suben >= 2 puntos.
Reanudable: guarda cada resultado en reports/compare_ear.json. Tarda ~ 6 x (8-15 min) en el Mac.
"""
import json
import os
import re
import shutil
import statistics
import subprocess
import sys

OUT = "reports/compare_ear.json"
ROWS = "abecdfg"


def parse(text):
    res = {}
    for line in text.splitlines():
        m = re.match(r"\s+([a-g])\)[^\n]*?:\s+([\d.]+)%", line)
        if m:
            res[m.group(1)] = float(m.group(2))
    return res


def main():
    os.makedirs("reports", exist_ok=True)
    done = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for pre in ("0", "1"):
        for seed in ("0", "1", "2"):
            k = f"pre{pre}_seed{seed}"
            if k in done:
                continue
            print(f"--- {k}: entrenando...", flush=True)
            env = dict(os.environ, EAR_PRE=pre, LCM_SEED=seed)
            subprocess.run([sys.executable, "-m", "scripts.train_ear"], env=env, check=True, stdout=subprocess.DEVNULL)
            shutil.copy("checkpoints/ear.pt", f"checkpoints/ear_{k}.pt")
            out = subprocess.run([sys.executable, "-m", "scripts.evaluate_ear"], env=env, check=True, capture_output=True, text=True).stdout
            done[k] = parse(out)
            json.dump(done, open(OUT, "w"), indent=1)
            print("   ", done[k], flush=True)
    mean = {pre: {r: statistics.mean(done[f"pre{pre}_seed{s}"][r] for s in "012") for r in ROWS} for pre in "01"}
    spread = {pre: {r: max(done[f"pre{pre}_seed{s}"][r] for s in "012") - min(done[f"pre{pre}_seed{s}"][r] for s in "012") for r in ROWS} for pre in "01"}
    print("\nfila | sin preentrenar (media, rango) | con preentrenar (media, rango) | diferencia")
    for r in ROWS:
        print(f"  {r}  | {mean['0'][r]:5.1f}  ({spread['0'][r]:.1f}) | {mean['1'][r]:5.1f}  ({spread['1'][r]:.1f}) | {mean['1'][r]-mean['0'][r]:+.1f}")
    d = {r: mean["1"][r] - mean["0"][r] for r in ROWS}
    ok = all(d[r] >= -1.0 for r in "abfg") and (d["d"] >= 2.0 or d["e"] >= 2.0)
    print(f"\nDecision: {'PREENTRENAMIENTO ADOPTADO' if ok else 'NO ADOPTADO'}")
    best = "pre1_seed0" if ok else "pre0_seed0"
    shutil.copy(f"checkpoints/ear_{best}.pt", "checkpoints/ear.pt")
    print(f"[+] checkpoints/ear.pt = {best}")


if __name__ == "__main__":
    main()
''',
    'scripts/empaquetar_todo.py': '\0b64:IiIiR2VuZXJhIFVOIHNvbG8gYXJjaGl2byAoTENNX2NvbnN0cnVpcl9kZXNkZV9jZXJvLnB5KSBjb24gVE9ETyBlbCBjb2RpZ28sIGRhdG9zIHBlcXVlbm9zIGRlIHBydWViYSwgdGVzdHMgeSBkb2N1bWVudG9zIGRlbCBwcm95ZWN0by4KCiAgcHl0aG9uIC1tIHNjcmlwdHMuZW1wYXF1ZXRhcl90b2RvICAgICAgICAgICAgICAgICAjIGVzY3JpYmUgTENNX2NvbnN0cnVpcl9kZXNkZV9jZXJvLnB5IGVuIGxhIHJhaXoKICBweXRob24gLW0gc2NyaXB0cy5lbXBhcXVldGFyX3RvZG8gLS1zYWxpZGEgWC5weQoKUGFyYSByZWNvbnN0cnVpciBlbCBwcm95ZWN0byBlbiB1bmEgY2FycGV0YSBWQUNJQToKICBta2RpciBMQ00gJiYgY2QgTENNICYmIGNwIC9kb25kZS9lc3RlL0xDTV9jb25zdHJ1aXJfZGVzZGVfY2Vyby5weSAuICYmIHB5dGhvbiBMQ01fY29uc3RydWlyX2Rlc2RlX2Nlcm8ucHkKICBweXRob24gLW0gdmVudiAudmVudiAmJiBzb3VyY2UgLnZlbnYvYmluL2FjdGl2YXRlICYmIHBpcCBpbnN0YWxsIC1yIHJlcXVpcmVtZW50cy50eHQKICBweXRob24gLW0gcHl0ZXN0IC1xIHRlc3RzICYmIHB5dGhvbiAtbSBzY3JpcHRzLnJlcHJvZHVjZSAtLWxpYnJvIHR1X3RleHRvLnR4dCAmJiBweXRob24gLW0gc2NyaXB0cy5tYW5pZmllc3RvIC0tdmVyaWZpY2FyCgpObyBpbmNsdXllOiBwZXNvcyAoY2hlY2twb2ludHMpLCBkYXRhc2V0cyBnZW5lcmFkb3MgKC5wa2wpLCBjb3JwdXMgVUQgKHNlIGRlc2NhcmdhbiBjb24gc2NyaXB0cy5nZXRfZGF0YSksIG5pbmd1biBsaWJybywgbmkgdHUgbWVtb3JpYS4KTGFzIGh1ZWxsYXMgZGUgbG8gZW1wYXF1ZXRhZG8gc2FsZW4gZW4gcmVwcm9kdWNpYmlsaWRhZC9tYW5pZmllc3RvLmpzb24gKHB5dGhvbiAtbSBzY3JpcHRzLm1hbmlmaWVzdG8gLS1ndWFyZGFyKS4KIiIiCmltcG9ydCBhcmdwYXJzZQppbXBvcnQgYmFzZTY0CmltcG9ydCBkYXRldGltZQppbXBvcnQgb3MKaW1wb3J0IHN5cwoKc3lzLnBhdGguaW5zZXJ0KDAsIG9zLmdldGN3ZCgpKQpmcm9tIHNjcmlwdHMubWFuaWZpZXN0byBpbXBvcnQgdHJhY2tlZCAgIyBub3FhOiBFNDAyCgpIRUFERVIgPSAnJyciIiJMQ006IGNvbnN0cnVpciBlbCBwcm95ZWN0byBERVNERSBDRVJPIChnZW5lcmFkbyBwb3Igc2NyaXB0cy9lbXBhcXVldGFyX3RvZG8ucHkgZWwge2ZlY2hhfSkuCgpVc28sIGVuIHVuYSBjYXJwZXRhIHZhY2lhIChvIGVuIGxhIGRlbCBwcm95ZWN0byB0cmFzIGxpbXBpZXphLnB5KToKICAgIHB5dGhvbiBMQ01fY29uc3RydWlyX2Rlc2RlX2Nlcm8ucHkgICAgICAgICAgICAgICMgZXNjcmliZSB7bn0gYXJjaGl2b3MgeSBhYnJlIHVuIE1FTlUgZ3VpYWRvOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIyAgIDEgZW50b3JubyBlIGluc3RhbGFjaW9uIMK3IDIgdGVzdHMgwrcgMyB2ZXJpZmljYXIgY29kaWdvIMK3IDQgcmVlbnRyZW5hciB0b2RvCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAjICAgNSBjb21wYXJhciByZXN1bHRhZG9zIMK3IDYgaGFibGFyIGNvbiBlbCBtb2RlbG8gwrcgNyB0b2RvIGVuIG9yZGVuCiAgICBweXRob24gTENNX2NvbnN0cnVpcl9kZXNkZV9jZXJvLnB5IC0tc2luLW1lbnUgICAjIHNvbG8gZXNjcmliZSBsb3MgYXJjaGl2b3MgKGNvcGlhcyBlbiAucGFyY2hlX2JhY2t1cHMvIHNpIGNhbWJpYW4pCiAgICBweXRob24gTENNX2NvbnN0cnVpcl9kZXNkZV9jZXJvLnB5IC0tdG9kbyAtLWxpYnJvIHR1X3RleHRvLnR4dCBbLS1yYXBpZG9dIFstLXNlbWlsbGEgTl0gICAjIHNpbiBwcmVndW50YXIgbmFkYQooe3Rlc3RzfSkuIEd1aWEgY29tcGxldGE6IGRvY3MvUkVQUk9EVUNJUi5tZAoiIiIKaW1wb3J0IGJhc2U2NCwgZGF0ZXRpbWUsIHN5cwpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKCkZJTEVTID0ge3sKJycnCgpGT09URVIgPSAnJyd9CgoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tCiMgQXNpc3RlbnRlIGludGVyYWN0aXZvIChzb2xvIGJpYmxpb3RlY2EgZXN0YW5kYXIpLiBVc286CiMgICBweXRob24gTENNX2NvbnN0cnVpcl9kZXNkZV9jZXJvLnB5ICAgICAgICAgICAgICAgICAgLT4gZXNjcmliZSBsb3MgYXJjaGl2b3MgeSBhYnJlIGVsIG1lbnUKIyAgIHB5dGhvbiBMQ01fY29uc3RydWlyX2Rlc2RlX2Nlcm8ucHkgLS1zaW4tbWVudSAgICAgICAtPiBzb2xvIGVzY3JpYmUgbG9zIGFyY2hpdm9zCiMgICBweXRob24gTENNX2NvbnN0cnVpcl9kZXNkZV9jZXJvLnB5IC0tdG9kbyBbLS1saWJybyBtaV90ZXh0by50eHRdIFstLXJhcGlkb10gWy0tc2VtaWxsYSBOXSAgIC0+IGhhY2UgdG9kbyBlbiBvcmRlbiwgc2luIHByZWd1bnRhcgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KaW1wb3J0IGFyZ3BhcnNlCmltcG9ydCBvcwppbXBvcnQgc3VicHJvY2VzcwoKUk9PVCA9IFBhdGguY3dkKCkKTElCUk9TID0gKCJyZWdlbnRhLnJ0ZiIsICJyZWdlbnRhLnR4dCIsICJsaWJyby50eHQiLCAibGlicm8ucnRmIikKT1BUID0geyJsaWJybyI6IE5vbmUsICJyYXBpZG8iOiBGYWxzZSwgInNlbWlsbGEiOiBOb25lfQoKCmRlZiB3cml0ZV9maWxlcygpOgogICAgc3RhbXAgPSBkYXRldGltZS5kYXRldGltZS5ub3coKS5zdHJmdGltZSgiJVklbSVkLSVIJU0lUyIpCiAgICB3cm90ZSA9IHNhbWUgPSAwCiAgICBmb3IgcmVsLCBjb250ZW50IGluIEZJTEVTLml0ZW1zKCk6CiAgICAgICAgaWYgY29udGVudC5zdGFydHN3aXRoKCJcXDBiNjQ6Iik6CiAgICAgICAgICAgIGNvbnRlbnQgPSBiYXNlNjQuYjY0ZGVjb2RlKGNvbnRlbnRbNTpdKS5kZWNvZGUoInV0Zi04IikKICAgICAgICBwYXRoID0gUk9PVCAvIHJlbAogICAgICAgIGlmIHBhdGguZXhpc3RzKCk6CiAgICAgICAgICAgIGlmIHBhdGgucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpID09IGNvbnRlbnQ6CiAgICAgICAgICAgICAgICBzYW1lICs9IDEKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIGJhayA9IFJPT1QgLyAiLnBhcmNoZV9iYWNrdXBzIiAvIHN0YW1wIC8gcmVsCiAgICAgICAgICAgIGJhay5wYXJlbnQubWtkaXIocGFyZW50cz1UcnVlLCBleGlzdF9vaz1UcnVlKQogICAgICAgICAgICBiYWsud3JpdGVfdGV4dChwYXRoLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgiKSwgZW5jb2Rpbmc9InV0Zi04IikKICAgICAgICBwYXRoLnBhcmVudC5ta2RpcihwYXJlbnRzPVRydWUsIGV4aXN0X29rPVRydWUpCiAgICAgICAgcGF0aC53cml0ZV90ZXh0KGNvbnRlbnQsIGVuY29kaW5nPSJ1dGYtOCIpCiAgICAgICAgd3JvdGUgKz0gMQogICAgZm9yIGQgaW4gKCJjaGVja3BvaW50cyIsICJtZW1vcnkiLCAicmVwb3J0cyIpOgogICAgICAgIChST09UIC8gZCkubWtkaXIoZXhpc3Rfb2s9VHJ1ZSkKICAgIHByaW50KGYiW09LXSB7d3JvdGV9IGFyY2hpdm9zIGVzY3JpdG9zLCB7c2FtZX0geWEgZXN0YWJhbiBpZ3VhbC4iKQoKCmRlZiB2ZW52X3B5dGhvbigpOgogICAgZm9yIHJlbCBpbiAoIi52ZW52L2Jpbi9weXRob24iLCAiLnZlbnYvU2NyaXB0cy9weXRob24uZXhlIiwgInZlbnYvYmluL3B5dGhvbiIsICJ2ZW52L1NjcmlwdHMvcHl0aG9uLmV4ZSIpOgogICAgICAgIGlmIChST09UIC8gcmVsKS5leGlzdHMoKToKICAgICAgICAgICAgcmV0dXJuIHN0cihST09UIC8gcmVsKQogICAgcmV0dXJuIE5vbmUKCgpkZWYgcHkoKToKICAgIHJldHVybiB2ZW52X3B5dGhvbigpIG9yIHN5cy5leGVjdXRhYmxlCgoKZGVmIHJ1bihhcmdzLCBxdWlldD1GYWxzZSk6CiAgICBwcmludCgiXFxuJCAiICsgIiAiLmpvaW4oYXJncyksIGZsdXNoPVRydWUpCiAgICByID0gc3VicHJvY2Vzcy5ydW4oYXJncywgY3dkPVJPT1QpCiAgICBpZiByLnJldHVybmNvZGUgIT0gMCBhbmQgbm90IHF1aWV0OgogICAgICAgIHByaW50KGYiWyFdIEVsIGNvbWFuZG8gdGVybWlubyBjb24gY29kaWdvIHtyLnJldHVybmNvZGV9LiIpCiAgICByZXR1cm4gci5yZXR1cm5jb2RlID09IDAKCgpkZWYgaGFzX3RvcmNoKCk6CiAgICByZXR1cm4gc3VicHJvY2Vzcy5ydW4oW3B5KCksICItYyIsICJpbXBvcnQgdG9yY2gsIG51bXB5LCB0cWRtLCBweXRlc3QiXSwgY3dkPVJPT1QsIGNhcHR1cmVfb3V0cHV0PVRydWUpLnJldHVybmNvZGUgPT0gMAoKCmRlZiBmaW5kX2Jvb2soKToKICAgIGlmIE9QVFsibGlicm8iXToKICAgICAgICByZXR1cm4gT1BUWyJsaWJybyJdCiAgICBmb3IgZiBpbiBMSUJST1M6CiAgICAgICAgaWYgKFJPT1QgLyBmKS5leGlzdHMoKToKICAgICAgICAgICAgcmV0dXJuIGYKICAgIHJldHVybiBOb25lCgoKZGVmIHN0ZXBfZW50b3JubygpOgogICAgaWYgbm90IHZlbnZfcHl0aG9uKCk6CiAgICAgICAgcHJpbnQoIkNyZWFuZG8gZWwgZW50b3JubyBkZSBQeXRob24gKC52ZW52KSAuLi4iKQogICAgICAgIGlmIG5vdCBydW4oW3N5cy5leGVjdXRhYmxlLCAiLW0iLCAidmVudiIsICIudmVudiJdKToKICAgICAgICAgICAgcmV0dXJuIEZhbHNlCiAgICBwcmludCgiSW5zdGFsYW5kbyBkZXBlbmRlbmNpYXMgKHB1ZWRlIHRhcmRhciB1bm9zIG1pbnV0b3MgbGEgcHJpbWVyYSB2ZXopIC4uLiIpCiAgICByZXR1cm4gcnVuKFtweSgpLCAiLW0iLCAicGlwIiwgImluc3RhbGwiLCAiLXIiLCAicmVxdWlyZW1lbnRzLnR4dCJdKQoKCmRlZiBzdGVwX3Rlc3RzKCk6CiAgICByZXR1cm4gcnVuKFtweSgpLCAiLW0iLCAicHl0ZXN0IiwgIi1xIiwgInRlc3RzIl0pCgoKZGVmIHN0ZXBfY29kaWdvKCk6CiAgICBpZiBub3QgKFJPT1QgLyAicmVwcm9kdWNpYmlsaWRhZCIgLyAibWFuaWZpZXN0by5qc29uIikuZXhpc3RzKCk6CiAgICAgICAgcHJpbnQoIkF1biBubyBoYXkgcmVwcm9kdWNpYmlsaWRhZC9tYW5pZmllc3RvLmpzb24gKHNlIGNyZWEgY29uOiAgcHl0aG9uIC1tIHNjcmlwdHMubWFuaWZpZXN0byAtLWd1YXJkYXIgIGVuIHR1IHByb3llY3RvIG9yaWdpbmFsKS4iKQogICAgICAgIHByaW50KCJMbyBjcmVvIGFob3JhIGEgcGFydGlyIGRlIGxvIHF1ZSBhY2FibyBkZSBlc2NyaWJpcj8gIChzaXJ2ZSBwYXJhIGNvbXByb2JhciBjb3BpYXMgZnV0dXJhcykiKQogICAgICAgIHJldHVybiBydW4oW3B5KCksICItbSIsICJzY3JpcHRzLm1hbmlmaWVzdG8iLCAiLS1ndWFyZGFyIl0pCiAgICByZXR1cm4gcnVuKFtweSgpLCAiLW0iLCAic2NyaXB0cy5tYW5pZmllc3RvIiwgIi0tdmVyaWZpY2FyIl0pCgoKZGVmIHN0ZXBfcmVlbnRyZW5hcigpOgogICAgYm9vayA9IGZpbmRfYm9vaygpCiAgICBhcmdzID0gW3B5KCksICItbSIsICJzY3JpcHRzLnJlcHJvZHVjZSJdCiAgICBpZiBib29rOgogICAgICAgIGFyZ3MgKz0gWyItLWxpYnJvIiwgYm9va10KICAgIGVsc2U6CiAgICAgICAgcHJpbnQoIlthdmlzb10gTm8gaGF5IHRleHRvIGVuIGVzcGFub2wgKHJlZ2VudGEucnRmLy50eHQpIG5pIC0tbGlicm86IHNlIHNhbHRhbiBsb3MgcGFzb3MgcXVlIGRlcGVuZGVuIGRlIGVsIChlbCBvaWRvIHNhbGRyYSBkaXN0aW50bykuIikKICAgIGlmIE9QVFsicmFwaWRvIl06CiAgICAgICAgYXJncy5hcHBlbmQoIi0tcmFwaWRvIikKICAgIGlmIE9QVFsic2VtaWxsYSJdIGlzIG5vdCBOb25lOgogICAgICAgIGFyZ3MgKz0gWyItLXNlbWlsbGEiLCBzdHIoT1BUWyJzZW1pbGxhIl0pXQogICAgcmV0dXJuIHJ1bihhcmdzKQoKCmRlZiBzdGVwX3Jlc3VsdGFkb3MoKToKICAgIHJldHVybiBydW4oW3B5KCksICItbSIsICJzY3JpcHRzLm1hbmlmaWVzdG8iLCAiLS12ZXJpZmljYXIiLCAiLS1tZXRyaWNhcyJdKQoKCmRlZiBzdGVwX2hhYmxhcigpOgogICAgcmV0dXJuIHJ1bihbcHkoKSwgIi1tIiwgInNjcmlwdHMudGhpbmsiXSkKCgpkZWYgZXN0YWRvKCk6CiAgICBjayA9IFJPT1QgLyAiY2hlY2twb2ludHMiCiAgICBwZXNvcyA9IFtmIGZvciBmIGluICgibGNtX3JlYXNvbmVyLnB0IiwgImVhci5wdCIsICJzY2hvb2wucHQiKSBpZiAoY2sgLyBmKS5leGlzdHMoKV0KICAgIHByaW50KCJcXG5Fc3RhZG86IikKICAgIHByaW50KGYiICAgZW50b3JubyBQeXRob24gKC52ZW52KSAuLi4uIHsnc2knIGlmIHZlbnZfcHl0aG9uKCkgZWxzZSAnbm8nfSAgIHwgICBkZXBlbmRlbmNpYXMgLi4uLiB7J3NpJyBpZiB2ZW52X3B5dGhvbigpIGFuZCBoYXNfdG9yY2goKSBlbHNlICdubyAvIHNpbiBjb21wcm9iYXInfSIpCiAgICBwcmludChmIiAgIHBlc29zIGVudHJlbmFkb3MgLi4uLi4uLi4uLiB7bGVuKHBlc29zKX0vMyAoeycsICcuam9pbihwZXNvcykgb3IgJ25pbmd1bm8nfSkiKQogICAgcHJpbnQoZiIgICB0ZXh0byBlbiBlc3Bhbm9sIC4uLi4uLi4uLi4ge2ZpbmRfYm9vaygpIG9yICdubyBlbmNvbnRyYWRvICh1c2EgLS1saWJybyBvIHBvbiByZWdlbnRhLnJ0Zi8udHh0IGFxdWkpJ30iKQoKCk1FTlUgPSBbCiAgICAoIjEiLCAiUHJlcGFyYXIgZWwgZW50b3JubyAoY3JlYXIgLnZlbnYgZSBpbnN0YWxhciBkZXBlbmRlbmNpYXMpIiwgc3RlcF9lbnRvcm5vKSwKICAgICgiMiIsICJDb21wcm9iYXIgZWwgY29kaWdvIGNvbiBsb3MgdGVzdHMgKDUxKSIsIHN0ZXBfdGVzdHMpLAogICAgKCIzIiwgIlZlcmlmaWNhciBxdWUgZWwgY29kaWdvIGVzIGlkZW50aWNvIGFsIG9yaWdpbmFsIChtYW5pZmllc3RvKSIsIHN0ZXBfY29kaWdvKSwKICAgICgiNCIsICJSZWVudHJlbmFyIFRPRE8gZGVzZGUgY2VybyAocmVwcm9kdWNlOyB0YXJkYSBkZXNkZSBkZWNlbmFzIGRlIG1pbnV0b3MgYSBob3JhcykiLCBzdGVwX3JlZW50cmVuYXIpLAogICAgKCI1IiwgIkNvbXByb2JhciBsb3MgcmVzdWx0YWRvcyBjb250cmEgbGEgcmVmZXJlbmNpYSIsIHN0ZXBfcmVzdWx0YWRvcyksCiAgICAoIjYiLCAiSGFibGFyIGNvbiBlbCBtb2RlbG8gKHRoaW5rKSIsIHN0ZXBfaGFibGFyKSwKICAgICgiNyIsICJIYWNlciAxIC0+IDUgZW4gb3JkZW4sIHNpbiBwYXJhciIsIE5vbmUpLApdCgoKZGVmIGhhY2VyX3RvZG8oKToKICAgIGZvciBrZXksIGxhYmVsLCBmbiBpbiBNRU5VWzo1XToKICAgICAgICBwcmludChmIlxcbj09PSB7a2V5fS4ge2xhYmVsfSA9PT0iKQogICAgICAgIGlmIG5vdCBmbigpOgogICAgICAgICAgICBwcmludChmIlshXSBTZSBwYXJhIGVuIGVsIHBhc28ge2tleX0uIEFycmVnbGFsbyB5IHJlcGl0ZSBkZXNkZSBlbCBtZW51LiIpCiAgICAgICAgICAgIHJldHVybiBGYWxzZQogICAgcHJpbnQoIlxcbltPS10gVG9kbyBoZWNoby4gQWhvcmEgcHVlZGVzIHByb2JhcjogIHB5dGhvbiAtbSBzY3JpcHRzLnRoaW5rIikKICAgIHJldHVybiBUcnVlCgoKZGVmIG1lbnUoKToKICAgIGlmIG5vdCBhbnkoKFJPT1QgLyAiY2hlY2twb2ludHMiIC8gZikuZXhpc3RzKCkgZm9yIGYgaW4gKCJlYXIucHQiLCAic2Nob29sLnB0IiwgImxjbV9yZWFzb25lci5wdCIpKToKICAgICAgICB0cnk6CiAgICAgICAgICAgIHIgPSBpbnB1dCgiXFxuTm8gaGF5IHBlc29zIGVudHJlbmFkb3MuIMK/TG8gaGFnbyBUT0RPIGF1dG9tYXRpY2FtZW50ZSAoZW50b3JubywgdGVzdHMsIHZlcmlmaWNhY2lvbiwgcmVlbnRyZW5hbWllbnRvIHkgY29tcGFyYWNpb24pPyBbUy9uXTogIikuc3RyaXAoKS5sb3dlcigpCiAgICAgICAgZXhjZXB0IEVPRkVycm9yOgogICAgICAgICAgICByZXR1cm4KICAgICAgICBpZiByIGluICgiIiwgInMiLCAic2kiLCAieSIsICJ5ZXMiKToKICAgICAgICAgICAgaWYgT1BUWyJsaWJybyJdIGlzIE5vbmUgYW5kIGZpbmRfYm9vaygpIGlzIE5vbmU6CiAgICAgICAgICAgICAgICBPUFRbImxpYnJvIl0gPSBpbnB1dCgiUnV0YSBkZSB0dSB0ZXh0byBlbiBlc3Bhbm9sIChFbnRlciA9IHNpbiB0ZXh0byk6ICIpLnN0cmlwKCkgb3IgTm9uZQogICAgICAgICAgICBoYWNlcl90b2RvKCkKICAgICAgICAgICAgcmV0dXJuCiAgICB3aGlsZSBUcnVlOgogICAgICAgIGVzdGFkbygpCiAgICAgICAgcHJpbnQoIlxcbsK/UXVlIHF1aWVyZXMgaGFjZXI/IikKICAgICAgICBmb3Iga2V5LCBsYWJlbCwgXyBpbiBNRU5VOgogICAgICAgICAgICBwcmludChmIiAgIHtrZXl9KSB7bGFiZWx9IikKICAgICAgICBwcmludCgiICAgMCkgU2FsaXIiKQogICAgICAgIHRyeToKICAgICAgICAgICAgY2hvaWNlID0gaW5wdXQoIkVsaWdlIHVuIG51bWVybzogIikuc3RyaXAoKQogICAgICAgIGV4Y2VwdCBFT0ZFcnJvcjoKICAgICAgICAgICAgcmV0dXJuCiAgICAgICAgaWYgY2hvaWNlIGluICgiMCIsICJxIiwgIiIpOgogICAgICAgICAgICByZXR1cm4KICAgICAgICBpZiBjaG9pY2UgPT0gIjciOgogICAgICAgICAgICBoYWNlcl90b2RvKCkKICAgICAgICAgICAgY29udGludWUKICAgICAgICBpdGVtID0gbmV4dCgobSBmb3IgbSBpbiBNRU5VIGlmIG1bMF0gPT0gY2hvaWNlKSwgTm9uZSkKICAgICAgICBpZiBub3QgaXRlbToKICAgICAgICAgICAgcHJpbnQoIk9wY2lvbiBubyB2YWxpZGEuIikKICAgICAgICAgICAgY29udGludWUKICAgICAgICBpZiBjaG9pY2UgPT0gIjQiOgogICAgICAgICAgICBpZiBub3QgaGFzX3RvcmNoKCk6CiAgICAgICAgICAgICAgICBwcmludCgiUHJpbWVybyBoYWNlIGZhbHRhIGVsIGVudG9ybm86IGVsaWdlIGxhIG9wY2lvbiAxLiIpCiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICBpZiBPUFRbImxpYnJvIl0gaXMgTm9uZSBhbmQgZmluZF9ib29rKCkgaXMgTm9uZToKICAgICAgICAgICAgICAgIE9QVFsibGlicm8iXSA9IGlucHV0KCJSdXRhIGRlIHR1IHRleHRvIGVuIGVzcGFub2wgKEVudGVyID0gc2luIHRleHRvKTogIikuc3RyaXAoKSBvciBOb25lCiAgICAgICAgICAgIHIgPSBpbnB1dCgiwr9Nb2RvIHJhcGlkbyAoc2FsdGEgbGFzIGV2YWx1YWNpb25lcyBvcGNpb25hbGVzKT8gW3MvTl06ICIpLnN0cmlwKCkubG93ZXIoKQogICAgICAgICAgICBPUFRbInJhcGlkbyJdID0gciBpbiAoInMiLCAic2kiLCAieSIpCiAgICAgICAgaXRlbVsyXSgpCgoKZGVmIG1haW4oKToKICAgIGFwID0gYXJncGFyc2UuQXJndW1lbnRQYXJzZXIoZGVzY3JpcHRpb249IkNvbnN0cnV5ZSBlbCBwcm95ZWN0byBMQ00gZGVzZGUgY2VybyB5IHRlIGd1aWEgcGFyYSBwcm9iYXJsby4iKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLXNpbi1tZW51IiwgYWN0aW9uPSJzdG9yZV90cnVlIiwgaGVscD0ic29sbyBlc2NyaWJlIGxvcyBhcmNoaXZvcyIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tdG9kbyIsIGFjdGlvbj0ic3RvcmVfdHJ1ZSIsIGhlbHA9ImVzY3JpYmUsIGluc3RhbGEsIHBydWViYSwgcmVlbnRyZW5hIHkgdmVyaWZpY2Egc2luIHByZWd1bnRhciIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tbGlicm8iLCBoZWxwPSJ0ZXh0byBlbiBlc3Bhbm9sIHBhcmEgZWwgb2lkbyIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tcmFwaWRvIiwgYWN0aW9uPSJzdG9yZV90cnVlIikKICAgIGFwLmFkZF9hcmd1bWVudCgiLS1zZW1pbGxhIiwgdHlwZT1pbnQpCiAgICBhID0gYXAucGFyc2VfYXJncygpCiAgICBPUFQudXBkYXRlKGxpYnJvPWEubGlicm8sIHJhcGlkbz1hLnJhcGlkbywgc2VtaWxsYT1hLnNlbWlsbGEpCiAgICB3cml0ZV9maWxlcygpCiAgICBpZiBhLnNpbl9tZW51OgogICAgICAgIHByaW50KCJTaWd1aWVudGU6ICBweXRob24gLW0gdmVudiAudmVudiAmJiBzb3VyY2UgLnZlbnYvYmluL2FjdGl2YXRlICYmIHBpcCBpbnN0YWxsIC1yIHJlcXVpcmVtZW50cy50eHQgJiYgcHl0aG9uIC1tIHB5dGVzdCAtcSB0ZXN0cyIpCiAgICAgICAgcmV0dXJuCiAgICBpZiBhLnRvZG86CiAgICAgICAgc3lzLmV4aXQoMCBpZiBoYWNlcl90b2RvKCkgZWxzZSAxKQogICAgaWYgbm90IHN5cy5zdGRpbi5pc2F0dHkoKToKICAgICAgICBwcmludCgiKHNpbiB0ZXJtaW5hbCBpbnRlcmFjdGl2YTogbm8gYWJybyBlbCBtZW51OyB1c2EgLS10b2RvIG8gZWplY3V0YSBkZSBudWV2byBlbiB1bmEgdGVybWluYWwpIikKICAgICAgICByZXR1cm4KICAgIG1lbnUoKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBtYWluKCkKJycnCgoKZGVmIG1haW4oKToKICAgIGFwID0gYXJncGFyc2UuQXJndW1lbnRQYXJzZXIoKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLXNhbGlkYSIsIGRlZmF1bHQ9IkxDTV9jb25zdHJ1aXJfZGVzZGVfY2Vyby5weSIpCiAgICBhID0gYXAucGFyc2VfYXJncygpCiAgICBmaWxlcyA9IFtmIGZvciBmIGluIHRyYWNrZWQoKSBpZiBmICE9IGEuc2FsaWRhIGFuZCBvcy5wYXRoLmV4aXN0cyhmKV0KICAgIGJvZHkgPSBbXQogICAgZm9yIGYgaW4gZmlsZXM6CiAgICAgICAgdGV4dCA9IG9wZW4oZiwgZW5jb2Rpbmc9InV0Zi04IikucmVhZCgpCiAgICAgICAgaWYgIicnJyIgaW4gdGV4dCBvciB0ZXh0LmVuZHN3aXRoKCJcXCIpIG9yICJcMCIgaW4gdGV4dCBvciAiXHIiIGluIHRleHQ6CiAgICAgICAgICAgIGVuYyA9ICJcMGI2NDoiLnJlcGxhY2UoIlwwIiwgIlxcMCIpICsgYmFzZTY0LmI2NGVuY29kZSh0ZXh0LmVuY29kZSgidXRmLTgiKSkuZGVjb2RlKCJhc2NpaSIpCiAgICAgICAgICAgIGJvZHkuYXBwZW5kKGYiICAgIHtmIXJ9OiB7ZW5jIXJ9LFxuIi5yZXBsYWNlKCJcXFxcMGI2NCIsICJcXDBiNjQiKSkKICAgICAgICBlbHNlOgogICAgICAgICAgICBib2R5LmFwcGVuZChmIiAgICB7ZiFyfTogcicnJ3t0ZXh0fScnJyxcbiIpCiAgICBudGVzdHMgPSBzdW0oMSBmb3IgZiBpbiBmaWxlcyBpZiBmLnN0YXJ0c3dpdGgoInRlc3RzL3Rlc3RfIikpCiAgICBvdXQgPSBIRUFERVIuZm9ybWF0KGZlY2hhPWRhdGV0aW1lLmRhdGUudG9kYXkoKS5pc29mb3JtYXQoKSwgbj1sZW4oZmlsZXMpLCB0ZXN0cz1mIntudGVzdHN9IGZpY2hlcm9zIGRlIHRlc3RzIHVuaXRhcmlvcyIpICsgIiIuam9pbihib2R5KSArIEZPT1RFUgogICAgb3BlbihhLnNhbGlkYSwgInciLCBlbmNvZGluZz0idXRmLTgiKS53cml0ZShvdXQpCiAgICBjb21waWxlKG91dCwgYS5zYWxpZGEsICJleGVjIikKICAgIHByaW50KGYiW09LXSB7YS5zYWxpZGF9OiB7bGVuKGZpbGVzKX0gYXJjaGl2b3MsIHtsZW4ob3V0KSAvLyAxMDI0fSBLQiIpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIG1haW4oKQo=',
    'scripts/eval_correcciones.py': r'''"""Mide si la escuela APRENDE de las correcciones (parche-49). Todo en memoria: NO modifica checkpoints/school.pt.
Formato y criterios fijados antes de medir: data/correcciones_prueba.tsv.  Uso: python -m scripts.eval_correcciones"""
import copy
import sys

import torch

from scripts.eval_frases import evaluate, key
from src.language.school_learn import _key, learn_correction, replay_sentences, synthetic_replay
from src.language.school_parser import SchoolParser
from src.language.ud import load_school

FRASES, LARGAS = "data/frases_prueba.tsv", "data/frases_largas_ciegas.tsv"


def read(path="data/correcciones_prueba.tsv"):
    teach, test, test2 = [], [], []
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        kind, sent, gold = line.rstrip("\n").split("\t")
        s, p, o = gold.split("|")
        (teach if kind == "TEACH" else test2 if kind == "TEST2" else test).append((sent, (s, p, o)))
    return teach, test, test2


def score(parser, items):
    good, rows = 0, []
    for sent, (s, p, o) in items:
        found = parser.parse(sent) or []
        ok = any(t["s"] == s and t["o"] == o and _key(t["p"]) == _key(p) for t in found) and len(found) == 1
        good += ok
        rows.append((sent, ok, [(t["s"], t["p"], t["o"]) for t in found]))
    return good, rows


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    overrides = {}
    parser = SchoolParser(model, device, scripts, overrides)
    teach, test, test2 = read()
    base_test, _ = score(parser, test)
    base_test2, _ = score(parser, test2)
    base_conv = evaluate(parser, path=FRASES)[1]
    base_long = evaluate(parser, path=LARGAS)[1]
    print(f"ANTES: frases de prueba bien {base_test}/{len(test)} (TEST2: {base_test2}/{len(test2)}) | conversacion {base_conv:.1%} | largas {base_long:.1%}")
    replay = replay_sentences(n=150) + synthetic_replay(200)
    print(f"(repaso con {len(replay)} frases: texto normal + frases cortas de conversacion)")
    taught, done = [], 0
    canary = lambda: evaluate(parser, path=FRASES)[1]
    for sent, trip in teach:
        info = learn_correction(model, device, scripts, sent, trip, extra=taught, replay=replay, canary=canary, overrides=overrides)
        print(f"  ENTENDI {sent!r} -> {info}")
        if info["done"]:
            done += 1
            taught.append({"frase": sent, "triple": list(trip)})
    ok_taught, _ = score(parser, teach)
    after_test, rows = score(parser, test)
    after_test2, rows2 = score(parser, test2)
    conv = evaluate(parser, path=FRASES)[1]
    long_ = evaluate(parser, path=LARGAS)[1]
    print(f"\nDESPUES: ensenadas bien {ok_taught}/{len(teach)} | frases nuevas bien {after_test}/{len(test)} (TEST2: {after_test2}/{len(test2)}) | conversacion {conv:.1%} | largas {long_:.1%}")
    for sent, ok, found in rows + rows2:
        if not ok:
            print(f"   FALLO {sent} -> {found}")
    c1 = ok_taught == len(teach)
    c2 = (after_test + after_test2) / (len(test) + len(test2)) >= .5 and after_test + after_test2 > base_test + base_test2
    c3 = conv >= base_conv - .0125 - 1e-9 and long_ >= base_long - .037 - 1e-9
    print(f"\nCriterios: (1) ensenadas {'CUMPLE' if c1 else 'NO CUMPLE'} | (2) generaliza {'CUMPLE' if c2 else 'NO CUMPLE'} | (3) sin regresion {'CUMPLE' if c3 else 'NO CUMPLE'}")


if __name__ == "__main__":
    main()
''',
    'scripts/eval_dialogo.py': r'''"""Test de CONVERSACION (parche-54): turnos U: con subcadena esperada. Criterio fijado ANTES de medir: >= 75 % (test propio), >= 60 % (test ciego)."""
import os
import sys
import tempfile
from datetime import date

import torch

from src.language.dialogue import Conversation
from src.language.lexicon import norm
from src.language.qa import QA
from src.language.school_parser import SchoolParser
from src.language.ud import load_school
from src.memory.store import MemoryStore
from src.reasoning.lessons import deduce_all


def blocks(path):
    cur, today = [], None
    seed = [False]
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("#"):
            continue
        if line.startswith("HOY:"):
            today = line[4:].strip()
        elif line.startswith("SEMILLA:"):
            seed[0] = True
        elif not line.strip():
            if cur:
                yield cur, today, seed[0]
            cur = []
        elif line.startswith("U:"):
            body = line[2:].strip()
            turn, _, exp = body.partition("\t")
            cur.append((turn.strip(), exp.strip()))
    if cur:
        yield cur, today, seed[0]


def run(path="data/dialogo_prueba.tsv", quiet=False):
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    parser = SchoolParser(model, device, scripts)
    total = good = 0
    bad = []
    for turns, today, seeded in blocks(path):
        with tempfile.TemporaryDirectory() as d:
            mem = MemoryStore(os.path.join(d, "m.json"))
            mem.today = parser.today = date.fromisoformat(today) if today else None
            conv = Conversation(mem, parser, lambda m, p: QA(m, p.parse, lambda facts: deduce_all(facts, m.active_lessons())))
            if seeded:
                from src.language.semilla import load_seed
                load_seed(mem, parser)
            for turn, exp in turns:
                ans = conv.say(turn)
                if not exp:
                    continue
                total += 1
                a = norm(ans)
                ok = (norm(exp[1:]) not in a) if exp.startswith("!") else (norm(exp) in a)
                if ok:
                    good += 1
                else:
                    bad.append((turn, exp, ans))
    return good, total, bad


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/dialogo_prueba.tsv"
    good, total, bad = run(path)
    rate = good / max(total, 1)
    print(f"Test de conversacion: {good}/{total} = {rate:.1%}")
    for turn, exp, ans in bad:
        print(f"  FALLO {turn}  esperado={exp}  obtenido={ans}")
    limit = .60 if "ciego" in path or "ciega" in path else .70 if ("coherencia" in path or "definiciones" in path or "nucleo_prueba" in path) else .75
    print(f"\nCriterio (>= {limit:.0%}): {'CUMPLE' if rate >= limit else 'NO CUMPLE'}")


if __name__ == "__main__":
    main()
''',
    'scripts/eval_discurso.py': r'''"""Test de DISCURSO (parche-43, Fase 2): textos de 2 frases donde la segunda usa un pronombre ("Ella trabaja...") o tiene el
sujeto omitido ("Trabaja en un banco"). Formato como eval_frases: texto <TAB> s|p|o;s|p|o
Si existe src/language/discourse.py (parche siguiente) se usa su resolucion; si no, se lee cada frase por separado (LINEA BASE).

REGLA (fijada antes de medir): se da por buena la resolucion de sujetos si >= 70 % de los textos salen enteros (relajado).
"""
import sys

import torch

from scripts.eval_frases import key, load_gold
from src.language.school_parser import SchoolParser
from src.language.ud import load_school


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    parser = SchoolParser(model, device, scripts)
    try:
        from src.language.discourse import parse_text
        mode = "con resolucion de sujetos"
    except ImportError:
        import re

        def parse_text(parser, text):
            out = []
            for sent in re.split(r"(?<=[.!?])\s+", text.strip()):
                out += parser.parse(sent) or []
            return out
        mode = "LINEA BASE (cada frase por separado)"
    gold = load_gold(sys.argv[1] if len(sys.argv) > 1 else "data/discurso_ciego.tsv")
    good = tp = fp = fn = 0
    bad = []
    for text, g in gold:
        pred = {(t["s"], t["p"], t["o"], t["neg"]) for t in parse_text(parser, text)}
        gk = {(s, key(p), o, n) for s, p, o, n in g}
        pk = {(s, key(p), o, n) for s, p, o, n in pred}
        tp += len(gk & pk); fp += len(pk - gk); fn += len(gk - pk)
        if gk == pk:
            good += 1
        else:
            bad.append((text, sorted(g), sorted(pred)))
    n = len(gold)
    print(f"Test de discurso ({n} textos) [{mode}]: textos enteros bien {good / n:.1%} | "
          f"precision {tp / max(tp + fp, 1):.1%}, cobertura {tp / max(tp + fn, 1):.1%}")
    for text, g, p in bad:
        print(text)
        print("   esperado:", g)
        print("   obtenido:", p)
    print(f"\nCriterio (>= 70 %): {'CUMPLE' if good / n >= .70 else 'NO CUMPLE'}")


if __name__ == "__main__":
    main()
''',
    'scripts/eval_frases.py': r'''"""Test de CONVERSACION (parche-34): 60 frases cortas y simples con las proposiciones correctas escritas a mano
(data/frases_prueba.tsv). Es la medida directa de lo que importa para dialogar; los corpus UD son prensa.

Formato:  frase <TAB> s|p|o;s|p|o   (un ~ delante del sujeto marca negacion). Las relaciones se escriben con la forma base
(vivir_en, escribir, madre_de...).
Comparacion principal "RELAJADA": sujeto y objeto exactos y relacion igual en sus 3 primeras letras + la misma preposicion
(porque los lemas de nombres/verbos varian entre convenciones). Se informa tambien la EXACTA.

REGLA DE DECISION (fijada ANTES de medir): la escuela v2 se adopta si, en este test, acierta >= 75 % de las frases enteras
(relajado) y mejora en >= 10 puntos a la escuela v1 (que se mide con este mismo test antes de reentrenar).
"""
import sys

import torch

from src.language.school_parser import SchoolParser
from src.language.ud import load_school
from src.language.lexicon import norm


def key(p):
    head, _, prep = p.partition("_")
    return head[:3] + "|" + prep


def load_gold(path="data/frases_prueba.tsv"):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        sent, gold = line.split("\t")
        g = set()
        for t in gold.split(";"):
            neg = t.startswith("~")
            s, p, o = t.lstrip("~").split("|")
            g.add((s, p, o, neg))
        out.append((sent, g))
    return out


def evaluate(parser, verbose=False, path="data/frases_prueba.tsv"):
    gold = load_gold(path)
    exact = relaxed = tp = fp = fn = 0
    rows = []
    for sent, g in gold:
        found = parser.parse(sent) or []
        pred = {(t["s"], t["p"], t["o"], t["neg"]) for t in found}
        e = pred == g
        rl = {(s, key(p), o, n) for s, p, o, n in pred} == {(s, key(p), o, n) for s, p, o, n in g}
        exact += e; relaxed += rl
        gk = {(s, key(p), o, n) for s, p, o, n in g}; pk = {(s, key(p), o, n) for s, p, o, n in pred}
        tp += len(gk & pk); fp += len(pk - gk); fn += len(gk - pk)
        rows.append((sent, g, pred, rl))
    n = len(gold)
    return exact / n, relaxed / n, tp / max(tp + fp, 1), tp / max(tp + fn, 1), rows


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    parser = SchoolParser(model, device, scripts)
    path = sys.argv[1] if len(sys.argv) > 1 else "data/frases_prueba.tsv"
    ex, rl, pr, rc, rows = evaluate(parser, path=path)
    print(f"Test de conversacion ({len(rows)} frases): frases enteras bien {rl:.1%} (relajado) / {ex:.1%} (exacto) | "
          f"proposiciones: precision {pr:.1%}, cobertura {rc:.1%}   [lema: {'si' if scripts else 'no (escuela antigua)'}]")
    bad = [r for r in rows if not r[3]]
    print(f"\n--- {len(bad)} frases con diferencias ---")
    for sent, g, p, _ in bad[:25]:
        print(sent)
        print("   esperado:", sorted(g))
        print("   obtenido:", sorted(p))
    limit = .60 if "largas" in path else .75       # frases largas (Fase 2): criterio fijado antes de medir
    print(f"\nCriterio (>= {limit:.0%} relajado): {'CUMPLE' if rl >= limit else 'NO CUMPLE'}")


if __name__ == "__main__":
    main()
''',
    'scripts/eval_preguntas.py': r'''"""Test de PREGUNTAS (parche-35): ensena frases a una memoria vacia, hace preguntas y comprueba la respuesta.
Formato en data/preguntas_prueba.tsv. No usa el oido ni el razonador: mide escuela + QA (lo que cambia en este parche).

REGLA DE DECISION (fijada ANTES de medir): la Fase 1 se da por buena si acierta >= 70 % de las preguntas.
Con data/preguntas_ciegas.tsv (test ciego, escrito antes de medir) el criterio es >= 80 %.
Se informa tambien por tipo (si/no, quien, que/donde...) y las respuestas fallidas.
"""
import os
import sys
import tempfile

import torch

from src.language.lexicon import norm
from src.language.qa import QA
from src.language.school_parser import SchoolParser
from src.language.ud import load_school
from src.memory.store import MemoryStore


def blocks(path="data/preguntas_prueba.tsv"):
    path = sys.argv[1] if len(sys.argv) > 1 else path
    cur = {"H": [], "P": [], "R": [], "HOY": None}
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("#"):
            continue
        if not line.strip():
            if cur["H"] or cur["P"]:
                yield cur
            cur = {"H": [], "P": [], "R": [], "HOY": None}
        elif line.startswith("HOY:"):
            cur["HOY"] = line[4:].strip()
        elif line.startswith("R:"):
            cur["R"].append(line[2:].strip())
        elif line.startswith("H:"):
            cur["H"].append(line[2:].strip())
        elif line.startswith("P:"):
            q, exp = line[2:].strip().split("\t")
            cur["P"].append((q.strip(), exp.strip()))
    if cur["H"] or cur["P"]:
        yield cur


def add_rule(mem, parser, text):
    """"Si A entonces B": cada mitad se lee con la escuela y se guarda como leccion."""
    body = text.strip().rstrip(".")
    low = norm(body)
    if not low.startswith("si ") or " entonces " not in low:
        return False
    a, b = body[3:].split(" entonces ", 1) if " entonces " in body else (None, None)
    pa, pb = parser.parse(a + "."), parser.parse(b + ".")
    if not pa or not pb or len(pb) != 1:
        return False
    mem.add_lesson([(t["s"], t["p"], t["o"]) for t in pa], (pb[0]["s"], pb[0]["p"], pb[0]["o"]))
    return True


def make_deduce(mem):
    from src.reasoning.lessons import deduce_all
    return lambda facts: deduce_all(facts, mem.active_lessons())


def ok(answer, expected):
    a = norm(answer)
    if expected == "SI":
        return a.startswith("si")
    if expected == "NO":
        return a.startswith("no.")
    if expected == "NOSE":
        return "no lo se" in a or "no me consta" in a
    return norm(expected) in a


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    parser = SchoolParser(model, device, scripts)
    total = good = 0
    bad = []
    for b in blocks():
        with tempfile.TemporaryDirectory() as d:
            mem = MemoryStore(os.path.join(d, "m.json"))
            if b.get("HOY"):
                from datetime import date
                mem.today = parser.today = date.fromisoformat(b["HOY"])
            else:
                mem.today = parser.today = None
            for sent in b["H"]:
                for t in parser.parse(sent) or []:
                    tr = (t["s"], t["p"], t["o"])
                    mem.add_fact(tr, source=sent, neg=t["neg"], when=t.get("when", ""), when_disp=t.get("when_disp", ""), quant=t.get("q", ""))
                    mem.note_surface(tr, t.get("template"), t.get("s_disp"), t.get("o_disp"))
            for rule in b.get("R", []):
                add_rule(mem, parser, rule)
            qa = QA(mem, parser.parse, make_deduce(mem))
            for q, exp in b["P"]:
                ans = qa.answer(q)
                total += 1
                if ok(ans, exp):
                    good += 1
                else:
                    kind, t = qa.read(q)
                    from src.language.qa import rewrite
                    bad.append((q, exp, ans + f"\n        [diagnostico] reescrito={rewrite(q)} leido={t}"
                                f" | memoria={[(f['s'], f['p'], f['o'], f.get('neg')) for f in mem.facts]}"))
    rate = good / max(total, 1)
    print(f"Test de preguntas: {good}/{total} = {rate:.1%}")
    for q, exp, ans in bad:
        print(f"  FALLO {q}  esperado={exp}  obtenido={ans}")
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    limit = .75 if ("deduccion" in arg or "conceptos" in arg or "tiempo" in arg or "herencia" in arg or "fechas" in arg) else .80 if "ciegas" in arg else .70
    if "estados" in arg or "cantidad" in arg:
        limit = .60 if "ciegas" in arg else .70
    print(f"\nCriterio (>= {limit:.0%}): {'CUMPLE' if rate >= limit else 'NO CUMPLE'}")


if __name__ == "__main__":
    main()
''',
    'scripts/eval_school.py': r'''"""Diagnostico de la escuela de espanol (parche-31): por que las proposiciones del arbol predicho no coinciden.

No reentrena: carga checkpoints/school.pt y mide, sobre las frases de PRUEBA:
  - precision / cobertura / F1 de proposiciones SUELTAS (no de la frase entera),
  - de las proposiciones humanas que se pierden, POR QUE: no hay sujeto, otro objeto, otra relacion...,
  - 20 frases con error, con las proposiciones humanas y las predichas.
"""
import random
from collections import Counter, defaultdict

import torch

from src.language.extract import triples
from src.language.ud import find_files, load_school, predict_trees, read_conllu


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    test = []
    for f in find_files("test"):
        test += read_conllu(f)[0]
    trees = predict_trees(model, [[w[0] for w in s] for s in test], device, scripts)
    tp = fp = fn = 0
    why = Counter()
    bad = []
    for s, t in zip(test, trees):
        gold = set(triples([(w[0], w[1], w[2], w[3], w[4]) for w in s]))
        pred = set(triples([(w[0], u, h, r, lm) for w, (u, h, r, lm) in zip(s, t)]))
        tp += len(gold & pred); fp += len(pred - gold); fn += len(gold - pred)
        for g in gold - pred:
            same_s = [p for p in pred if p[0] == g[0]]
            if not pred:
                why["no predice ninguna proposicion en la frase"] += 1
            elif not same_s:
                why["sujeto distinto o no encontrado"] += 1
            elif any(p[2] == g[2] and p[1] != g[1] for p in same_s):
                why["sujeto y objeto bien, relacion distinta (verbo/preposicion)"] += 1
            elif any(p[1] == g[1] and p[2] != g[2] for p in same_s):
                why["sujeto y relacion bien, objeto distinto"] += 1
            else:
                why["sujeto bien, relacion y objeto distintos"] += 1
        if gold != pred and len(bad) < 400:
            bad.append((s, gold, pred))
    # --- extractor v1 (sin resolver "que") frente a v2, a nivel de frase ---
    def sent_match(resolve, lens):
        ok, tot = defaultdict(int), defaultdict(int)
        for s, t in zip(test, trees):
            g = set(triples([(w[0], w[1], w[2], w[3], w[4]) for w in s], resolve))
            if not g:
                continue
            p = set(triples([(w[0], u, h, r, lm) for w, (u, h, r, lm) in zip(s, t)], resolve))
            b = next(name for name, hi in lens if len(s) <= hi)
            tot[b] += 1; ok[b] += g == p
        return ok, tot
    lens = [("<= 8 palabras", 8), ("9-15", 15), ("16-25", 25), ("> 25", 99)]
    print("\nFrases enteras con proposicion iguales a las humanas, por longitud:")
    for resolve, name in ((False, "extractor v1"), (True, "extractor v2 (que resuelto)")):
        ok, tot = sent_match(resolve, lens)
        print(f"  {name}: " + " | ".join(f"{b}: {ok[b]/max(tot[b],1):.0%} (de {tot[b]})" for b, _ in lens) +
              f" | total {sum(ok.values())/max(sum(tot.values()),1):.1%}")
    # --- acierto por funcion sintactica (cabeza Y etiqueta correctas) ---
    rel_ok, rel_tot = Counter(), Counter()
    for s, t in zip(test, trees):
        for w, (u, h, r, lm) in zip(s, t):
            rel_tot[w[3]] += 1
            rel_ok[w[3]] += (h == w[2]) and (r == w[3])
    print("\nAcierto por funcion (el humano dice X: acerto cabeza y funcion?):")
    for r in ("nsubj", "obj", "obl", "nmod", "cop", "case", "flat", "acl", "advmod", "root"):
        print(f"  {r:7s} {rel_ok[r]/max(rel_tot[r],1):5.1%}  (de {rel_tot[r]})")
    prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
    print(f"Proposiciones sueltas en {len(test)} frases de prueba: precision {prec:.1%}, cobertura {rec:.1%}, F1 {2*prec*rec/max(prec+rec,1e-9):.1%}")
    print(f"  (humanas: {tp+fn}, predichas: {tp+fp}, acertadas: {tp})")
    print("\nDe las proposiciones humanas que se pierden:")
    tot = sum(why.values()) or 1
    for k, v in why.most_common():
        print(f"  {v/tot:5.1%}  {k}")
    print("\n--- 20 frases con diferencias ---")
    for s, g, p in random.Random(1).sample(bad, min(20, len(bad))):
        print(" ".join(w[0] for w in s)[:150])
        print("   humano :", sorted(g))
        print("   predicho:", sorted(p))


if __name__ == "__main__":
    main()
''',
    'scripts/evaluate_ear.py': r'''"""Mide el oido con la regla fijada de antemano (parche-16).

REGLA (parche-18, ademas: f) rechaza >= 90 % de lo que no es afirmacion y g) acepta >= 90 % de las validas): el oido se adopta si
  (a) nombres nuevos + relaciones conocidas, (b) RELACIONES NUEVAS, y (e) frases "es un"/"son"
  aciertan >= 95 % la proposicion completa (sujeto, relacion, objeto Y polaridad), y
  (c)+(d) MARCOS DE FRASE NUNCA VISTOS suben a >= 60 % (en parche-15 eran ~30 %).
"""
import torch
from src.language.corpus import (CLAUSES_TEST, HEADS_TEST, HEADS_TRAIN, VERBS_TEST, VERBS_TRAIN, PredicatePool, base_pool,
                                 es_pool, make, make_negatives)
from src.language.ear import Ear, predict


def candidates():
    seen = {}
    for p in base_pool() + es_pool() + PredicatePool(HEADS_TRAIN, VERBS_TRAIN).items + PredicatePool(HEADS_TEST, VERBS_TEST).items:
        seen[p[1]] = p[0]
    return [(n, t) for t, n in seen.items()]


def score(ear, data, cands, device):
    outs = predict(ear, [x["tokens"] for x in data], cands, device)
    n = len(data)
    full = sum((o["subject"], o["predicate"], o["object"], o["negated"]) == (*x["triple"], x["neg"]) for o, x in zip(outs, data))
    s = sum(o["subject"] == x["triple"][0] for o, x in zip(outs, data))
    p = sum(o["predicate"] == x["triple"][1] for o, x in zip(outs, data))
    o_ = sum(o["object"] == x["triple"][2] for o, x in zip(outs, data))
    g = sum(o["negated"] == x["neg"] for o, x in zip(outs, data))
    return full / n, (s / n, p / n, o_ / n, g / n)


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    ear = Ear()
    ear.load_state_dict(torch.load("checkpoints/ear.pt", map_location="cpu"))
    ear.to(device)
    cands = candidates()
    train_pool = base_pool() + PredicatePool(HEADS_TRAIN, VERBS_TRAIN).items
    test_pool = PredicatePool(HEADS_TEST, VERBS_TEST).items
    cases = {
        "a) nombres nuevos, relaciones conocidas": make(1000, train_pool, 11, "test"),
        "b) RELACIONES NUEVAS, nombres nuevos": make(1000, test_pool, 12, "test"),
        "e) 'es un' / 'son' (nombres y categorias nuevos)": make(1000, es_pool(), 15, "test"),
        "c) MARCOS NUEVOS, relaciones conocidas": make(1000, train_pool + es_pool(), 13, "test", held_frames=True),
        "d) MARCOS NUEVOS + relaciones nuevas": make(1000, test_pool, 14, "test", held_frames=True),
    }
    res = {}
    print("=== EVALUACION DEL OIDO (proposicion + polaridad, exacta) ===")
    for name, data in cases.items():
        full, (s, p, o, g) = score(ear, data, cands, device)
        res[name[0]] = full
        print(f"  {name}: {full:6.1%}   (sujeto {s:.0%}, relacion {p:.0%}, objeto {o:.0%}, polaridad {g:.0%})")
    negs = make_negatives(1500, 21, "test")
    outs = predict(ear, [x["tokens"] for x in negs], cands, device)
    rej = sum(o["confidence"] < 0.8 for o in outs) / len(negs)
    pos = cases["a) nombres nuevos, relaciones conocidas"]
    outs = predict(ear, [x["tokens"] for x in pos], cands, device)
    acc = sum(o["confidence"] >= 0.8 for o in outs) / len(pos)
    print(f"  f) RECHAZA lo que no es una afirmacion (prosa, preguntas, fragmentos; {len(CLAUSES_TEST)} clausulas reales de prueba): {rej:6.1%}")
    print(f"  g) ACEPTA (confianza >= 80 %) las afirmaciones validas de (a): {acc:6.1%}")
    ok = all(res[k] >= 0.95 for k in "abe") and all(res[k] >= 0.60 for k in "cd") and rej >= 0.90 and acc >= 0.90
    print("\nDecision:", "OIDO ADOPTADO" if ok else "NO ADOPTADO del todo (ver filas por debajo del umbral)")


if __name__ == "__main__":
    main()
''',
    'scripts/evaluate_inoculate.py': r'''"""Vacuna para relaciones NUEVAS (parche-33).

Fallo visto en tu Mac: tras  "Marta escribio una novela"  (relacion ESCRIBIO recien creada) el razonador contesto
NOVELA HIJO_DE MARTA. Una relacion nueva no tiene regla: lo correcto es SIN_CONCLUSION.

REGLA DE DECISION (fijada ANTES de medir). Tras aprender 3 reglas y dormir, se crean 6 relaciones nuevas:
  - se adopta  inoculate  si los falsos positivos con ellas bajan a <= 10 %,
  - las reglas nuevas no bajan mas de 3 puntos, la fabrica se mantiene >= 98 % y el canario no se revierte.
"""
import os
import random
import tempfile

import torch

from scripts.evaluate_online import RULES, lessons_for
from scripts.evaluate_sleep import setup
from scripts.evaluate_stress import load_model
from src.memory import MemoryStore
from src.memory.sleep import SleepCycle
from src.training.online import OnlineLearner

NEW = ["ESCRIBIO", "TRABAJA_EN", "PROFESORA_DE", "COME", "LLEGO_A", "CANTA_EN"]


def fp(learner, preds, people, n=40):
    rng = random.Random(11)
    ls = []
    for q in preds:
        for _ in range(n):
            x, y = rng.sample(people, 2)
            ls.append(([(x, q, y)], (x, "SIN_CONCLUSION", "NINGUNA")))
    return 1 - learner.exact(*learner.encode(ls))


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    base, space, people, core, canary, old = setup(device)
    torch.manual_seed(0)
    model = load_model(base, space, device)
    learner = OnlineLearner(model, space, core, canary, device=device, steps=40)
    memory = MemoryStore(os.path.join(tempfile.mkdtemp(), "mem.json"))
    rng = random.Random(7)
    tests = [learner.encode(lessons_for(r, people[90:], 40, random.Random(99))) for r in RULES]
    for rule in RULES:
        lessons = lessons_for(rule, people[:90], 3, rng)
        if learner.learn(lessons, replay_core=True, replay_lessons=False, guard=True)["accepted"]:
            for p, c in lessons:
                memory.add_lesson(p, c)
    SleepCycle(learner, memory, seed=3).run(ledger=None)
    for q in NEW:                                   # igual que hace think al crear una relacion
        space.add_concept(q, features={"predicate": 1, "relation": 1, f"identity:{q}": 0.5}, kind="predicate")
    model.set_space(space)
    model.to(device)
    acc = lambda: sum(learner.exact(*t) for t in tests) / len(tests)
    a0, f0, o0 = acc(), fp(learner, NEW, people[90:]), learner.exact(*old)
    print(f"\nANTES de la vacuna: reglas {a0:.0%} | fabrica {o0:.0%} | falsos positivos con relaciones nuevas {f0:.0%}")
    info = learner.inoculate(NEW)
    a1, f1, o1 = acc(), fp(learner, NEW, people[90:]), learner.exact(*old)
    print(f"DESPUES           : reglas {a1:.0%} | fabrica {o1:.0%} | falsos positivos con relaciones nuevas {f1:.0%}   ({info})")
    ok = info.get("done") and f1 <= 0.10 and a1 >= a0 - 0.03 and o1 >= 0.98
    print(f"\nDecision: falsos positivos {f0:.0%} -> {f1:.0%}; reglas {a0:.0%} -> {a1:.0%}; fabrica {o1:.0%} => "
          f"{'VACUNA ADOPTADA' if ok else 'NO ADOPTADA'}")


if __name__ == "__main__":
    main()
''',
    'scripts/evaluate_negatives.py': r'''"""Experimento de NEGATIVOS (parche-20).

Problema: tras ensenar "X PADRE_DE Y => Y HIJO_DE X" el modelo aplicaba la regla a cualquier
frase de dos personas (p. ej. "Paco HIJO_DE Jose" -> "Jose HIJO_DE Paco").

REGLA DE DECISION (fijada ANTES de medir): se adoptan los negativos si
  - falsos positivos con relaciones NO vistas como negativo <= 10 % (y bajan >= 20 puntos frente a no usarlos),
  - la precision de las reglas nuevas no baja mas de 3 puntos,
  - el conocimiento de fabrica se mantiene >= 98 %.
"""
import os
import random
import tempfile
import torch
from scripts.evaluate_online import RULES, lessons_for
from scripts.evaluate_sleep import setup
from scripts.evaluate_stress import load_model
from src.memory import MemoryStore
from src.memory.sleep import SleepCycle
from src.training.online import OnlineLearner

HELD = ["AMIGO_DE", "VECINO_DE"]          # relaciones sin regla, que NUNCA se usan como negativo al entrenar


def fp_sets(learner, people, held_base):
    rng = random.Random(5)
    out = {}
    for label, preds in (("conclusion como premisa", [b for _, b in RULES]), ("relaciones NO vistas", HELD + held_base)):
        lessons = []
        for q in preds:
            for _ in range(30):
                x, y = rng.sample(people, 2)
                lessons.append(([(x, q, y)], (x, "SIN_CONCLUSION", "NINGUNA")))
        out[label] = learner.encode(lessons)
    return out


def run(name, use_neg, ctx, device):
    base, space, people, core, canary, old = ctx
    for q in HELD:
        if q not in space.concept_to_id:
            space.add_concept(q, features={"predicate": 1, "relation": 1, f"identity:{q}": 0.5}, kind="predicate")
    torch.manual_seed(0)
    model = load_model(base, space, device)
    learner = OnlineLearner(model, space, core, canary, device=device, steps=40, use_negatives=use_neg)
    safe_base = [q for q in learner.safe() if q not in HELD and q not in [x for r in RULES for x in r]]
    held_base = sorted(safe_base)[:3]
    learner.neg_exclude = set(HELD) | set(held_base)
    memory = MemoryStore(os.path.join(tempfile.mkdtemp(), "mem.json"))
    rng = random.Random(7)
    tests = [learner.encode(lessons_for(r, people[90:], 40, random.Random(99))) for r in RULES]
    fps = fp_sets(learner, people[90:], held_base)
    for rule in RULES:
        lessons = lessons_for(rule, people[:90], 3, rng)
        info = learner.learn(lessons, replay_core=True, replay_lessons=False, guard=True)
        if info["accepted"]:
            for p, c in lessons:
                memory.add_lesson(p, c)
    SleepCycle(learner, memory, seed=3).run(ledger=None, use_dreams=True, use_negatives=use_neg)
    acc = sum(learner.exact(*t) for t in tests) / len(tests)
    res = {k: 1 - learner.exact(*v) for k, v in fps.items()}
    fabrica = learner.exact(*old)
    print(f"\n--- {name} ---")
    print(f"  reglas nuevas (personas nunca vistas): {acc:5.0%} | fabrica {fabrica:5.0%}")
    for k, v in res.items():
        print(f"  falsos positivos, {k}: {v:5.0%}")
    return acc, fabrica, res


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    ctx = setup(device)
    print("=== NEGATIVOS: 3 reglas nuevas, 3 ejemplos cada una, luego un sueno ===")
    a = run("sin negativos (parche-14)", False, ctx, device)
    b = run("con negativos (parche-20)", True, ctx, device)
    held = "relaciones NO vistas"
    ok = b[2][held] <= 0.10 and (a[2][held] - b[2][held]) >= 0.20 and b[0] >= a[0] - 0.03 and b[1] >= 0.98
    print(f"\nDecision: falsos positivos {a[2][held]:.0%} -> {b[2][held]:.0%}; reglas {a[0]:.0%} -> {b[0]:.0%}; fabrica {b[1]:.0%} => "
          f"{'NEGATIVOS ADOPTADOS' if ok else 'NO ADOPTADOS'}")


if __name__ == "__main__":
    main()
''',
    'scripts/evaluate_online.py': r'''"""Experimento de aprendizaje al vuelo y olvido (parche-13).

Se enseñan, UNA TRAS OTRA, tres relaciones nuevas (con 5 ejemplos cada una) y se mide
despues de cada una: (a) si aprende la nueva, (b) si recuerda las anteriores nuevas,
(c) si conserva lo que sabia de fabrica. Variantes:
  sin_repaso      : solo ejemplos nuevos  (esperable: olvido catastrofico)
  sin_repaso+guardia: igual, pero revierte si rompe lo anterior
  repaso_base     : mezcla ejemplos del entrenamiento original
  repaso_total    : base + lecciones aprendidas antes
"""
import copy
import os
import pickle
import random
import torch
from scripts.evaluate_stress import load_model
from src.training.online import OnlineLearner

RULES = [("PADRE_DE", "HIJO_DE"), ("JEFE_DE", "SUBORDINADO_DE"), ("DUENO_DE", "PERTENENCIA_DE")]
K_EXAMPLES = 5


def build_space():
    with open("data/concept_space.pkl", "rb") as handle:
        base = pickle.load(handle)
    space = copy.deepcopy(base)
    for a, b in RULES:
        for name in (a, b):
            space.add_concept(name, features={"predicate": 1, "relation": 1, f"identity:{name}": 0.5}, kind="predicate")
    people = []
    for i in range(120):
        name = f"PERSONA_{i:03d}"
        space.add_concept(name, features={"individual": 1, "person": 1, f"identity:{name}": 0.5}, kind="entity")
        people.append(name)
    return base, space, people


def lessons_for(rule, pool, n, rng):
    a, b = rule
    chosen = set()
    while len(chosen) < n:
        chosen.add(tuple(rng.sample(pool, 2)))
    return [([(x, a, y)], (y, b, x)) for x, y in sorted(chosen)]


def run_variant(name, base, space, people, core, canary, old_eval, replay_core, replay_lessons, guard, device):
    rng = random.Random(7)
    torch.manual_seed(0)
    model = load_model(base, space, device)
    learner = OnlineLearner(model, space, core, canary, device=device)
    held_out = people[90:]
    tests = [learner.encode(lessons_for(rule, held_out, 40, random.Random(99))) for rule in RULES]
    rows = []
    for step, rule in enumerate(RULES):
        info = learner.learn(lessons_for(rule, people[:90], K_EXAMPLES, rng),
                             replay_core=replay_core, replay_lessons=replay_lessons, guard=guard)
        learned = [learner.exact(*tests[i]) for i in range(step + 1)]
        rows.append((step + 1, info["accepted"], learned, learner.exact(*old_eval)))
    print(f"\n--- {name} ---")
    for step, accepted, learned, old in rows:
        txt = " ".join(f"{x:5.0%}" for x in learned)
        print(f"  tras regla {step}: {'aceptada ' if accepted else 'REVERTIDA'} | reglas nuevas [{txt}] | conocimiento de fabrica {old:5.0%}")
    return rows


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    base, space, people = build_space()
    with open("data/concept_train_dataset.pkl", "rb") as handle:
        train = pickle.load(handle).tensors
    with open("data/concept_val_dataset.pkl", "rb") as handle:
        val = pickle.load(handle).tensors
    with open("data/concept_test_dataset.pkl", "rb") as handle:
        test = pickle.load(handle).tensors
    gen = torch.Generator().manual_seed(1)
    core_idx = torch.randperm(len(train[0]), generator=gen)[:4000]
    core = tuple(t[core_idx] for t in train)
    canary_idx = torch.randperm(len(val[0]), generator=gen)[:300]
    canary = tuple(t[canary_idx] for t in val)
    old_idx = torch.randperm(len(test[0]), generator=gen)[:600]
    old_eval = tuple(t[old_idx] for t in test)

    print("=== APRENDIZAJE AL VUELO: 3 reglas nuevas, 5 ejemplos cada una ===")
    print(f"(cada columna de 'reglas nuevas' es una regla, medida con personas nunca vistas)")
    run_variant("sin_repaso", base, space, people, core, canary, old_eval, False, False, False, device)
    run_variant("sin_repaso + guardia", base, space, people, core, canary, old_eval, False, False, True, device)
    run_variant("repaso_base", base, space, people, core, canary, old_eval, True, False, True, device)
    run_variant("repaso_total (base + lecciones)", base, space, people, core, canary, old_eval, True, True, True, device)


if __name__ == "__main__":
    main()
''',
    'scripts/evaluate_reasoner.py': r'''"""Evalua generalizacion neuronal (con baselines) y reglas simbolicas.

Importante: la similitud coseno media NO sirve sola. Los vectores objetivo
comparten componentes (mismos predicados/roles) y un predictor trivial ya
supera 0.95. La metrica fiable es la recuperacion exacta de la proposicion
correcta entre TODAS las proposiciones candidatas (sujeto+predicado+objeto).
"""
import json
import os
import pickle
from collections import defaultdict
import torch
import torch.nn.functional as F
from configs.config import LCMConfig
from src.model.reasoner import LatentReasoner
from src.reasoning.rule_engine import run_reference_tests


def _load_checkpoint(path, device):
    try:
        return torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        return torch.load(path, map_location=device)


def _bank(space):
    labels = sorted(space.proposition_vectors)
    matrix = torch.stack([space.proposition_vectors[k] for k in labels])
    return labels, F.normalize(matrix, dim=-1)


def evaluate_neural(space, dataset, device, train_dataset=None):
    path = "checkpoints/lcm_reasoner.pt"
    if not os.path.exists(path):
        raise FileNotFoundError("No existe el checkpoint. Ejecuta primero scripts.train_reasoner.")
    ckpt = _load_checkpoint(path, device)
    saved = ckpt.get("config", {})
    config = LCMConfig(
        d_concept=space.d_concept,
        n_layers=int(saved.get("n_layers", 4)),
        n_heads=int(saved.get("n_heads", 4)),
        max_concept_seq=int(saved.get("max_concept_seq", 4)),
        dropout=float(saved.get("dropout", 0.05)),
        device=device,
    )
    model = LatentReasoner(config).to(device)
    model.set_space(space)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    seq, mask, target = dataset.tensors
    target = F.normalize(target, dim=-1)
    with torch.no_grad():
        pred, _ = model(seq.to(device), attention_mask=mask.to(device))
    pred = pred.cpu()

    labels, bank = _bank(space)
    true_idx = (target @ bank.T).argmax(dim=-1)
    pred_idx = (pred @ bank.T).argmax(dim=-1)
    true_parts = [space.proposition_parts[labels[i]] for i in true_idx.tolist()]
    pred_parts = [space.proposition_parts[labels[i]] for i in pred_idx.tolist()]

    n = len(true_parts)
    exact = sum(a == b for a, b in zip(true_parts, pred_parts)) / n
    role_acc = {
        name: sum(a[i] == b[i] for a, b in zip(true_parts, pred_parts)) / n
        for i, name in enumerate(("subject", "predicate", "object"))
    }
    per_rule = defaultdict(lambda: [0, 0])
    for a, b in zip(true_parts, pred_parts):
        per_rule[a[1]][0] += int(a == b)
        per_rule[a[1]][1] += 1

    tags = getattr(dataset, "tags", None)
    per_variant = defaultdict(lambda: [0, 0])
    if tags:
        for (rule, variant), a, b in zip(tags, true_parts, pred_parts):
            per_variant[variant][0] += int(a == b)
            per_variant[variant][1] += 1

    # Baselines que explican por que el coseno medio engana.
    baselines = {}
    if train_dataset is not None:
        mean_t = F.normalize(F.normalize(train_dataset.tensors[2], dim=-1).mean(0), dim=0)
        baselines["cos_mean_train_target"] = float((target @ mean_t).mean())
    last = torch.stack([seq[i, int(mask[i].sum()) - 1] for i in range(n)])
    baselines["cos_copy_last_premise"] = float(F.cosine_similarity(last, target, dim=-1).mean())
    baselines["exact_chance"] = 1.0 / len(labels)

    cos = F.cosine_similarity(pred, target, dim=-1)
    return {
        "n_test": n,
        "n_candidates": len(labels),
        "exact_match_top1": exact,
        "role_accuracy": role_acc,
        "per_variant": {k: {"exact": v[0] / v[1], "n": v[1]} for k, v in per_variant.items()},
        "per_predicate": {k: {"exact": v[0] / v[1], "n": v[1]} for k, v in per_rule.items()},
        "mean_cosine_similarity": float(cos.mean()),
        "p10_cosine_similarity": float(torch.quantile(cos, 0.10)),
        "baselines": baselines,
        "checkpoint_epoch": int(ckpt.get("epoch", -1)),
        "checkpoint_val_loss": ckpt.get("val_loss"),
        "interpretation": "Usa exact_match_top1 y per_predicate; el coseno solo es una metrica auxiliar.",
    }


def main():
    needed = ("data/concept_space.pkl", "data/concept_test_dataset.pkl")
    if not all(os.path.exists(p) for p in needed):
        raise FileNotFoundError("Ejecuta primero `python -m scripts.prepare_concepts`.")
    with open(needed[0], "rb") as h:
        space = pickle.load(h)
    with open(needed[1], "rb") as h:
        test_dataset = pickle.load(h)
    train_dataset = None
    if os.path.exists("data/concept_train_dataset.pkl"):
        with open("data/concept_train_dataset.pkl", "rb") as h:
            train_dataset = pickle.load(h)

    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    neural = evaluate_neural(space, test_dataset, device, train_dataset)
    symbolic = run_reference_tests()
    report = {"device": device, "neural_generalization": neural, "symbolic_reference_tests": symbolic}
    os.makedirs("reports", exist_ok=True)
    with open("reports/lcm_evaluation.json", "w", encoding="utf-8") as h:
        json.dump(report, h, ensure_ascii=False, indent=2)

    b = neural["baselines"]
    print("\n=== EVALUACION DE GENERALIZACION LCM ===")
    print(f"Dispositivo: {device} | muestras test: {neural['n_test']} | candidatos: {neural['n_candidates']}")
    print(f"EXACT MATCH top-1 (s,p,o):  {neural['exact_match_top1']:.2%}   (azar: {b['exact_chance']:.2%})")
    print("Acierto por rol: " + " | ".join(f"{k}={v:.1%}" for k, v in neural["role_accuracy"].items()))
    print("Por predicado:")
    for k, v in sorted(neural["per_predicate"].items()):
        print(f"  {k:<12} {v['exact']:.1%}  (n={v['n']})")
    if neural["per_variant"]:
        print("Por variante (base / swapped=orden alterado / distractor=premisa irrelevante / insufficient=sin evidencia / chain3=3 aristas / chain4=4 aristas NUNCA vistas / unseen_predicate=relacion nueva / NUEVA_*=regla y palabras nuevas (la regla viaja en las premisas) / norule=sin enunciar la regla / nojoin=premisas que no encajan):")
        for k, v in sorted(neural["per_variant"].items()):
            print(f"  {k:<13} {v['exact']:.1%}  (n={v['n']})")
    print(f"Coseno medio: {neural['mean_cosine_similarity']:.4f} | P10: {neural['p10_cosine_similarity']:.4f}")
    print(f"  baselines de coseno -> media-de-objetivos: {b.get('cos_mean_train_target', float('nan')):.4f}"
          f" | copiar-ultima-premisa: {b['cos_copy_last_premise']:.4f}")
    print(f"Pruebas simbolicas (verifican el RuleEngine, NO la red): {symbolic['passed']}/{symbolic['total']}")
    print("[+] Informe: reports/lcm_evaluation.json")
    if symbolic["passed"] != symbolic["total"]:
        raise SystemExit("Fallaron pruebas del motor simbolico de referencia.")


if __name__ == "__main__":
    main()
''',
    'scripts/evaluate_sleep.py': r'''"""Experimento del ciclo de sueno (parche-14).

REGLA DE DECISION (fijada ANTES de medir): los "suenos" (repaso generativo desde
esquemas) se adoptan si, frente al sueno que solo repasa lecciones, suben la
generalizacion media de las reglas nuevas >= 5 puntos Y el conocimiento de fabrica
se mantiene >= 98 %. Si no, se descartan.

Protocolo: se ensenan 3 reglas nuevas con 3 ejemplos cada una, aprendiendo de
forma rapida y ligera ("vigilia": 40 pasos, solo repaso de fabrica). Luego se mide,
se duerme (segun la variante) y se vuelve a medir con personas nunca vistas.
"""
import os
import random
import tempfile
import torch
from scripts.evaluate_online import RULES, build_space, lessons_for
from scripts.evaluate_stress import load_model
from src.memory import MemoryStore
from src.memory.sleep import SleepCycle
from src.training.online import OnlineLearner
import pickle

K = 3


def setup(device):
    base, space, people = build_space()
    tr = pickle.load(open("data/concept_train_dataset.pkl", "rb")).tensors
    va = pickle.load(open("data/concept_val_dataset.pkl", "rb")).tensors
    te = pickle.load(open("data/concept_test_dataset.pkl", "rb")).tensors
    g = torch.Generator().manual_seed(1)
    ci = torch.randperm(len(tr[0]), generator=g)[:4000]
    vi = torch.randperm(len(va[0]), generator=g)[:300]
    oi = torch.randperm(len(te[0]), generator=g)[:600]
    return base, space, people, tuple(t[ci] for t in tr), tuple(t[vi] for t in va), tuple(t[oi] for t in te)


def measure(learner, tests, old):
    new = [learner.exact(*t) for t in tests]
    return new, learner.exact(*old)


def run_variant(name, sleep_kwargs, ctx, device):
    base, space, people, core, canary, old = ctx
    torch.manual_seed(0)
    model = load_model(base, space, device)
    learner = OnlineLearner(model, space, core, canary, device=device, steps=40)
    memory = MemoryStore(os.path.join(tempfile.mkdtemp(), "mem.json"))
    rng = random.Random(7)
    tests = [learner.encode(lessons_for(r, people[90:], 40, random.Random(99))) for r in RULES]
    for rule in RULES:
        lessons = lessons_for(rule, people[:90], K, rng)
        info = learner.learn(lessons, replay_core=True, replay_lessons=False, guard=True)
        if info["accepted"]:
            for p, c in lessons:
                memory.add_lesson(p, c)
    new_b, old_b = measure(learner, tests, old)
    line = f"  antes de dormir : reglas nuevas {' '.join(f'{x:4.0%}' for x in new_b)} (media {sum(new_b)/3:4.0%}) | fabrica {old_b:4.0%}"
    print(f"\n--- {name} ---\n{line}")
    if sleep_kwargs is None:
        return sum(new_b) / 3, old_b, sum(new_b) / 3, old_b
    cycle = SleepCycle(learner, memory, seed=3)
    rep = cycle.run(ledger=None, **sleep_kwargs)
    new_a, old_a = measure(learner, tests, old)
    print(f"  despues de dormir: reglas nuevas {' '.join(f'{x:4.0%}' for x in new_a)} (media {sum(new_a)/3:4.0%}) | fabrica {old_a:4.0%}"
          f" | lecciones archivadas {rep['compressed']} | revertido {rep['consolidate']['rolled_back']}")
    return sum(new_b) / 3, old_b, sum(new_a) / 3, old_a


def main():
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    ctx = setup(device)
    print("=== CICLO DE SUENO: 3 reglas nuevas, 3 ejemplos cada una ===")
    print("Regla: adoptar suenos si +5 pp frente a solo-lecciones y fabrica >= 98 %.")
    res = {}
    res["sin sueno"] = run_variant("sin sueno", None, ctx, device)
    res["solo lecciones"] = run_variant("sueno: solo repaso de lecciones", dict(use_dreams=False), ctx, device)
    res["con suenos"] = run_variant("sueno: lecciones + suenos (esquemas)", dict(use_dreams=True), ctx, device)
    a, b = res["solo lecciones"][2], res["con suenos"][2]
    verdict = (b - a >= 0.05) and res["con suenos"][3] >= 0.98
    print(f"\nDecision: suenos {b:.0%} vs solo lecciones {a:.0%} (diferencia {100*(b-a):+.1f} pp); "
          f"fabrica {res['con suenos'][3]:.0%} -> {'ADOPTADOS' if verdict else 'NO ADOPTADOS'}")


if __name__ == "__main__":
    main()
''',
    'scripts/evaluate_stress.py': r'''"""Prueba de estres: catalogo ABIERTO (conceptos anadidos DESPUES de entrenar).

Se registran conceptos que el modelo nunca vio ni siquiera como palabra en el
catalogo (algunos con solo rasgo de identidad) y se comprueban reglas con ellos,
sin reentrenar. La salida se decodifica con el lector de ranuras.
"""
import copy
import json
import os
import pickle
import random
import torch
from configs.config import LCMConfig
from src.model.reasoner import LatentReasoner


def load_model(base_space, space, device):
    path = "checkpoints/lcm_reasoner.pt"
    if not os.path.exists(path):
        raise FileNotFoundError("Falta el checkpoint. Ejecuta scripts.train_reasoner.")
    try:
        ckpt = torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        ckpt = torch.load(path, map_location=device)
    saved = ckpt.get("config", {})
    config = LCMConfig(d_concept=space.d_concept, n_layers=int(saved.get("n_layers", 4)),
                       n_heads=int(saved.get("n_heads", 4)), max_concept_seq=int(saved.get("max_concept_seq", 4)),
                       dropout=float(saved.get("dropout", 0.05)), device=device)
    model = LatentReasoner(config).to(device)
    model.set_space(base_space)  # catalogo del entrenamiento: encaja con el checkpoint
    model.load_state_dict(ckpt["model_state_dict"])
    model.set_space(space)       # ahora, el catalogo ampliado
    model.eval()
    return model


def infer(model, space, premises, device):
    vectors = [space.encode_proposition(*p) for p in premises]
    seq = torch.stack(vectors).unsqueeze(0).to(device)
    mask = torch.ones(1, seq.shape[1], dtype=torch.bool, device=device)
    with torch.no_grad():
        out, _ = model(seq, attention_mask=mask)
        s, p, o = model.read_slots(out.view(1, 1, -1))[0, 0].tolist()
    return tuple(space.id_to_concept[i] for i in (s, p, o))


def main():
    with open("data/concept_space.pkl", "rb") as handle:
        base_space = pickle.load(handle)
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    space = copy.deepcopy(base_space)
    n_before = len(space.concept_to_id)
    rng = random.Random(123)

    # Conceptos nuevos: la mitad con rasgos de familia, la mitad solo con identidad.
    order, objs, inds, props = [], [], [], []
    for i in range(8):
        nm = f"NUEVO_ORDEN_{i}"
        feats = ({"abstract_entity": 1, "ordered_domain": 0.4, f"identity:{nm}": 0.5} if i % 2 == 0 else None)
        space.add_concept(nm, features=feats, kind="entity"); order.append(nm)
        nm = f"NUEVO_OBJ_{i}"
        feats = ({"physical_object": 1, "category:FRUTA": 0.8, "movable": 0.5, f"identity:{nm}": 0.5} if i % 2 == 0 else None)
        space.add_concept(nm, features=feats, kind="entity"); objs.append(nm)
        nm = f"NUEVO_IND_{i}"
        space.add_concept(nm, features=({"individual": 1, f"identity:{nm}": 0.5} if i % 2 == 0 else None), kind="entity"); inds.append(nm)
        nm = f"NUEVO_PROP_{i}"
        space.add_concept(nm, features=({"property": 1, f"identity:{nm}": 0.5} if i % 2 == 0 else None), kind="entity"); props.append(nm)

    model = load_model(base_space, space, device)
    results = {}

    def run(name, cases):
        ok = sum(infer(model, space, prem, device) == exp for prem, exp in cases)
        results[name] = {"ok": ok, "total": len(cases)}

    cases = []
    for _ in range(40):
        a, b, c = rng.sample(order, 3)
        cases.append(([(a, "MAYOR_QUE", b), (b, "MAYOR_QUE", c)], (a, "MAYOR_QUE", c)))
    run("transitividad con conceptos nuevos", cases)

    cases = []
    for _ in range(40):
        a, b, c, d = rng.sample(order, 4)
        cases.append(([(a, "MAYOR_QUE", b), (b, "MAYOR_QUE", c), (c, "MAYOR_QUE", d)], (a, "MAYOR_QUE", d)))
    run("cadena de 3 aristas con conceptos nuevos", cases)

    cases = [([(o, "LIBERADO_EN", "AIRE"), (o, "SOMETIDO_A", "GRAVEDAD")], (o, "CAE_HACIA", "SUELO")) for o in objs]
    run("caida con objetos nuevos", cases)

    cases = []
    for _ in range(40):
        x = rng.choice(inds); p, q = rng.sample(props, 2)
        cases.append(([(x, "HEREDA", p), (p, "IMPLICA", q), ("HEREDA", "REGLA_HEREDA", "IMPLICA")], (x, "HEREDA", q)))
    run("herencia con individuos y propiedades nuevos", cases)

    cases = []
    for _ in range(40):
        x = rng.choice(inds); p, q, r = rng.sample(props, 3)
        cases.append(([(x, "HEREDA", p), (r, "IMPLICA", q), ("HEREDA", "REGLA_HEREDA", "IMPLICA")], (x, "SIN_CONCLUSION", "NINGUNA")))
    run("premisas que no encajan (conceptos nuevos)", cases)

    cases = []
    for _ in range(30):
        a, b = rng.sample(order, 2)
        cases.append(([(a, "MAYOR_QUE", b), (b, "MAYOR_QUE", a)], (a, "CONTRADICE", b)))
    run("contradiccion A>B, B>A (conceptos nuevos)", cases)

    cases = []
    for _ in range(30):
        a, b, c = rng.sample(order, 3)
        cases.append(([(a, "MAYOR_QUE", b), (b, "MAYOR_QUE", c), (c, "MAYOR_QUE", a)], (a, "CONTRADICE", a)))
    run("ciclo A>B>C>A (conceptos nuevos)", cases)

    print("\n=== PRUEBA DE ESTRES: CATALOGO ABIERTO ===")
    print(f"Conceptos al entrenar: {n_before} | anadidos despues: {len(space.concept_to_id) - n_before}")
    for name, r in results.items():
        print(f"  {r['ok'] / r['total']:7.1%}  ({r['ok']}/{r['total']})  {name}")
    os.makedirs("reports", exist_ok=True)
    with open("reports/lcm_stress.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)
    print("[+] Informe: reports/lcm_stress.json")


if __name__ == "__main__":
    main()
''',
    'scripts/get_data.py': r'''"""Descarga los corpus UD en espanol (Universal Dependencies) a data/ud/. Necesita git y conexion a internet.
Licencias: GSD CC BY-SA 4.0, AnCora CC BY 4.0. NO se redistribuyen con el proyecto: cada persona los descarga.
Uso:  python -m scripts.get_data
"""
import json
import os
import subprocess
import sys

PIN = "reproducibilidad/manifiesto.json"          # si existe, fija el commit exacto de cada corpus (python -m scripts.manifiesto --guardar)

REPOS = {
    "UD_Spanish-GSD": "https://github.com/UniversalDependencies/UD_Spanish-GSD.git",
    "UD_Spanish-AnCora": "https://github.com/UniversalDependencies/UD_Spanish-AnCora.git",
}


def main():
    os.makedirs("data/ud", exist_ok=True)
    for name, url in REPOS.items():
        dest = os.path.join("data", "ud", name)
        if os.path.isdir(dest):
            print(f"[=] Ya existe {dest}")
            continue
        print(f"[+] Descargando {name} ...")
        commit = (json.load(open(PIN, encoding="utf-8")).get("ud", {}).get(name) if os.path.exists(PIN) else None)
        if commit:                                  # version EXACTA con la que se entreno (reproducible)
            steps = [["git", "init", dest], ["git", "-C", dest, "remote", "add", "origin", url],
                     ["git", "-C", dest, "fetch", "--depth", "1", "origin", commit], ["git", "-C", dest, "checkout", "FETCH_HEAD"]]
            r = None
            for cmd in steps:
                r = subprocess.run(cmd)
                if r.returncode != 0:
                    break
            print(f"    fijado al commit {commit[:10]} (reproducibilidad/manifiesto.json)")
        else:
            print("    (sin commit fijado: se baja la ultima version; ejecuta despues  python -m scripts.manifiesto --guardar  para fijarla)")
            r = subprocess.run(["git", "clone", "--depth", "1", url, dest])
        if r.returncode != 0:
            sys.exit(f"[!] Fallo al descargar {name}. Comprueba git/internet o clona a mano en {dest}.")
    print("[OK] Corpus listos en data/ud/")


if __name__ == "__main__":
    main()
''',
    'scripts/manifiesto.py': r'''"""Manifiesto de reproducibilidad (parche-60).

  python -m scripts.manifiesto --guardar     # escribe reproducibilidad/manifiesto.json (huellas de TODO el codigo/datos/tests,
                                             # versiones del entorno, commits de los corpus UD y metricas de referencia)
  python -m scripts.manifiesto --verificar   # compara tu copia con el manifiesto: archivos distintos/faltantes/sobrantes
  python -m scripts.manifiesto --verificar --metricas   # ademas ejecuta scripts.check y compara las metricas (tolerancia 0,03)

Que se vigila: src, scripts, tests, configs, data/*.tsv|txt|json (menos libro*), docs, README, Makefile, requirements, LICENSE y
reports/RESULTADOS.md. NO se vigilan los pesos (checkpoints/*.pt) porque dependen del hardware y de la semilla: de ellos se guarda
la huella solo como informacion. Sirve para saber, con certeza, que dos copias del proyecto tienen el mismo codigo.
"""
import argparse
import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys

OUT = "reproducibilidad/manifiesto.json"
TRACK_DIRS = ("src", "scripts", "tests", "configs", "docs", "data", ".github", "reproducibilidad")
TRACK_FILES = ("limpieza.py", "README.md", "LCM_EVOLUCION.md", "Makefile", "requirements.txt", "LICENSE", ".gitignore", "reports/RESULTADOS.md")
TEXT_EXT = (".py", ".tsv", ".txt", ".md", ".json", ".yml", ".yaml", ".cfg", "")
SKIP_PARTS = ("__pycache__", ".pytest_cache", "data/ud/", "data/libro", ".parche_backups", "reproducibilidad/manifiesto.json")


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked(root: str = ".") -> list:
    out = []
    for d in TRACK_DIRS:
        for base, dirs, files in os.walk(os.path.join(root, d)):
            dirs[:] = [x for x in dirs if x not in ("__pycache__", ".pytest_cache")]
            for fn in files:
                rel = os.path.relpath(os.path.join(base, fn), root).replace(os.sep, "/")
                if any(p in rel + ("/" if os.path.isdir(os.path.join(root, rel)) else "") for p in SKIP_PARTS):
                    continue
                if os.path.splitext(fn)[1] not in TEXT_EXT or fn.endswith((".pkl", ".pt", ".pyc")):
                    continue
                out.append(rel)
    out += [f for f in TRACK_FILES if os.path.exists(os.path.join(root, f))]
    return sorted(set(out))


def git_head(path: str):
    try:
        r = subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def environment() -> dict:
    env = {"python": sys.version.split()[0], "plataforma": platform.platform(), "semilla_por_defecto": os.environ.get("LCM_SEED", "0")}
    for mod in ("torch", "numpy", "tqdm", "pytest"):
        try:
            env[mod] = __import__(mod).__version__
        except Exception:
            env[mod] = None
    try:
        import torch
        env["dispositivo"] = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    except Exception:
        pass
    return env


def build() -> dict:
    ud = {}
    for name in ("UD_Spanish-GSD", "UD_Spanish-AnCora"):
        head = git_head(os.path.join("data", "ud", name))
        if head:
            ud[name] = head
    old = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    ud = ud or old.get("ud", {})
    metrics = {}
    if os.path.exists("reports/historial.json"):
        hist = json.load(open("reports/historial.json"))
        if hist:
            metrics = hist[-1]["metrics"]
    ckpt = {}
    for fn in sorted(os.listdir("checkpoints")) if os.path.isdir("checkpoints") else []:
        ckpt[fn] = sha(os.path.join("checkpoints", fn))
    return {"creado": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "entorno": environment(), "ud": ud, "metricas_referencia": metrics,
            "checkpoints_informativo": ckpt, "archivos": {f: sha(f) for f in tracked()}}


def save():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    m = build()
    json.dump(m, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"[OK] {OUT}: {len(m['archivos'])} archivos, UD: {m['ud'] or 'sin clonar (ejecuta scripts.get_data y repite)'}")
    if m["metricas_referencia"]:
        print(f"     metricas de referencia: {len(m['metricas_referencia'])} (de reports/historial.json)")


def verify(with_metrics: bool, tol: float = 0.03) -> int:
    if not os.path.exists(OUT):
        sys.exit(f"[!] Falta {OUT}. Ejecuta primero:  python -m scripts.manifiesto --guardar")
    ref = json.load(open(OUT, encoding="utf-8"))
    now = {f: sha(f) for f in tracked()}
    want = ref["archivos"]
    diff = sorted(f for f in want if f in now and now[f] != want[f])
    missing = sorted(f for f in want if f not in now)
    extra = sorted(f for f in now if f not in want)
    print(f"Archivos vigilados: {len(want)} | distintos: {len(diff)} | faltan: {len(missing)} | sobran: {len(extra)}")
    for tag, lst in (("DISTINTO", diff), ("FALTA", missing), ("SOBRA", extra)):
        for f in lst[:40]:
            print(f"   {tag}: {f}")
    env_now, env_ref = environment(), ref.get("entorno", {})
    for k in ("python", "torch", "numpy"):
        if env_now.get(k) != env_ref.get(k):
            print(f"   (aviso) {k}: manifiesto {env_ref.get(k)} / aqui {env_now.get(k)}  -> las cifras pueden moverse unos puntos")
    ud_now = {n: git_head(os.path.join("data", "ud", n)) for n in ref.get("ud", {})}
    for n, h in ref.get("ud", {}).items():
        if ud_now.get(n) and ud_now[n] != h:
            print(f"   (aviso) {n}: otro commit ({ud_now[n][:10]} en vez de {h[:10]}): la escuela no saldra identica")
    ok = not (diff or missing)
    if with_metrics:
        r = subprocess.run([sys.executable, "-m", "scripts.check"], capture_output=True, text=True)
        if not os.path.exists("reports/historial.json"):
            print("[!] No se pueden comparar metricas: scripts.check no llego a terminar (faltan pesos entrenados?). Ultimas lineas:")
            print("    " + "\n    ".join((r.stderr or r.stdout).strip().splitlines()[-6:]))
            print("    Entrena primero (python -m scripts.reproduce) y repite.")
            return 1
        hist = json.load(open("reports/historial.json"))
        cur, base = hist[-1]["metrics"], ref.get("metricas_referencia", {})
        bad = [(k, base[k], cur.get(k)) for k in base if cur.get(k) is None or cur[k] < base[k] - tol]
        print(f"Metricas: {len(base) - len(bad)}/{len(base)} dentro de la tolerancia ({tol:.0%} por debajo de la referencia)")
        for k, b, c in bad:
            print(f"   BAJA: {k}: referencia {b:.1%} -> ahora {('%.1f%%' % (c * 100)) if c is not None else 'sin dato'}")
        ok = ok and not bad
    print("[OK] Reproduccion fiel." if ok else "[!] Hay diferencias (ver arriba).")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true")
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--metricas", action="store_true")
    a = ap.parse_args()
    if a.guardar:
        save()
    elif a.verificar:
        sys.exit(verify(a.metricas))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
''',
    'scripts/prepare_concepts.py': r'''"""Construye una ontologia explicita y datos composicionales con holdouts.

Los conjuntos train/val/test separan pares de salida en transitividad y
entidades completas en reglas fisicas/cardinalidad. En transitividad, las
premisas de todos los splits proceden exclusivamente de pares train para
impedir que objetivos val/test aparezcan como entradas de entrenamiento.
El test no se utiliza para seleccionar checkpoints.
"""
import json
import os
import pickle
import random
import torch
from torch.utils.data import TensorDataset
from src.ontology.concept_space import ConceptSpace

D_CONCEPT = 128
MAX_PREMISES = 4


def _register(space, name, es, en, features, kind="concept"):
    space.register_concept(name, es, en, features=features, kind=kind)


def build_ontology():
    space = ConceptSpace(d_concept=D_CONCEPT)

    base = [
        ("MANZANA", "una manzana", "an apple", {"physical_object": 1, "fruit": 1, "edible": 0.5}),
        ("SOLTAR", "accion de soltar", "release action", {"event": 1, "release_event": 1}),
        ("GRAVEDAD", "fuerza gravitatoria", "gravitational force", {"physical_force": 1, "attraction": 1}),
        ("CAER", "movimiento descendente", "downward motion", {"motion": 1, "downward_motion": 1}),
        ("CONJUNTO_FINITO", "conjunto finito", "finite set", {"set": 1, "finite": 1}),
        ("CONJUNTO_INFINITO", "conjunto infinito", "infinite set", {"set": 1, "infinite": 1}),
        ("CONTAR", "proceso de enumeracion", "counting process", {"enumeration_process": 1}),
        ("CARDINALIDAD", "tamano de un conjunto", "set cardinality", {"mathematical_property": 1, "size": 1}),
        ("ENUMERABLE", "conjunto enumerable", "countable set", {"set_property": 1, "enumerable": 1}),
        ("INFINITO_NUMERABLE", "infinito numerable", "countably infinite", {"set_property": 1, "infinite": 1, "enumerable": 1}),
        ("INNUMERABLE", "conjunto no numerable", "uncountable set", {"set_property": 1, "infinite": 1, "not_enumerable": 1}),
        ("NO_CONTAR", "no finalizar una enumeracion", "not finishing an enumeration", {"process_property": 1, "inconclusive": 1}),
        ("HIELO", "agua en estado solido", "water in solid state", {"substance": 1, "solid": 1, "water": 1, "meltable": 1}),
        ("CALOR", "energia termica", "thermal energy", {"energy": 1, "thermal": 1}),
        ("DERRETIR", "cambio de solido a liquido", "solid-to-liquid phase change", {"phase_transition": 1, "melting": 1}),
        ("AIRE", "aire", "air", {"environment": 1, "gas": 1}),
        ("SUELO", "suelo", "ground", {"environment": 1, "solid_surface": 1}),
        ("LIQUIDO", "estado liquido", "liquid state", {"phase": 1, "liquid": 1}),
        ("FUNDIBLE", "sustancia capaz de fundirse", "meltable substance", {"material_property": 1, "meltable": 1}),
        ("NATURALES", "numeros naturales", "natural numbers", {"mathematical_set": 1, "natural_numbers": 1}),
        ("TRUE", "verdadero", "true", {"truth_value": 1}),
        ("NINGUNA", "ninguna conclusion", "no conclusion", {"truth_value": 0.3, "absence": 1}),
    ]
    for item in base:
        _register(space, *item)

    predicates = [
        "MAYOR_QUE", "LIBERADO_EN", "SOMETIDO_A", "CAE_HACIA", "EXPUESTO_A",
        "CAMBIA_A", "ES", "ES_FINITO", "ES_INFINITO", "TIENE_BIYECCION_CON",
        "NO_TIENE_BIYECCION_CON", "ES_ENUMERABLE", "TIENE_CARDINALIDAD_FINITA",
        "SIN_CONCLUSION",
        "MENOR_QUE", "SUPERIOR_A",          # predicados de orden usados tambien en entrenamiento
        "ANTERIOR_A", "POSTERIOR_A",        # predicados de orden NUNCA vistos (solo test)
        "HEREDA", "IMPLICA", "POSEE", "CAUSA", "ADQUIERE", "DERIVA_EN",
        "MUESTRA", "ORIGINA", "EXHIBE", "PROVOCA",  # herencia (train)
        "TIENE_RASGO", "PRODUCE",           # herencia de propiedades (SOLO test)
        "REGLA_HEREDA",                     # enunciado de la regla (premisa)
        "CONTRADICE",                       # conclusion ante premisas incompatibles
    ]
    ordering = {"MAYOR_QUE", "MENOR_QUE", "SUPERIOR_A", "ANTERIOR_A", "POSTERIOR_A"}
    for predicate in predicates:
        _register(
            space, predicate, predicate.lower().replace("_", " "),
            predicate.lower().replace("_", " "),
            {"predicate": 1, f"predicate_family:{predicate}": 1,
             **({"ordering_relation": 1} if predicate in ordering else {})}, kind="predicate"
        )

    # Entidades abstractas para probar composicion transitiva.
    order_entities = [f"ORDEN_{i:02d}" for i in range(18)]
    for i, name in enumerate(order_entities):
        _register(space, name, f"elemento abstracto {i}", f"abstract element {i}",
                  {"abstract_entity": 1, "ordered_domain": 0.4, f"identity:{name}": 0.5}, "entity")

    # Objetos fisicos: las instancias de test no aparecen en entrenamiento.
    object_entities = []
    categories = ["FRUTA", "PELOTA", "PIEDRA", "MONEDA", "BLOQUE", "HERRAMIENTA"]
    for category in categories:
        for j in range(16):
            name = f"OBJ_{category}_{j:02d}"
            object_entities.append((category, j, name))
            _register(space, name, f"objeto {category.lower()} {j}", f"{category.lower()} object {j}",
                      {"physical_object": 1, f"category:{category}": 0.8,
                       "movable": 0.5, f"identity:{name}": 0.5}, "entity")

    # Sustancias fundibles, con instancias no vistas en el test.
    meltables = []
    for category in ("HIELO", "CERA", "MANTEQUILLA"):
        for j in range(12):
            name = f"SUST_{category}_{j:02d}"
            meltables.append((category, j, name))
            _register(space, name, f"muestra de {category.lower()} {j}", f"{category.lower()} sample {j}",
                      {"substance": 1, "solid": 1, "meltable": 1,
                       f"substance_family:{category}": 0.8, f"identity:{name}": 0.5}, "entity")

    # Conjuntos usados para distinguir finitud, numerabilidad y no numerabilidad.
    finite_sets, countable_sets, uncountable_sets = [], [], []
    for j in range(36):
        for prefix, collection, features in (
            ("FINITO", finite_sets, {"set": 1, "finite": 1}),
            ("NUMERABLE", countable_sets, {"set": 1, "infinite": 1, "enumerable": 1}),
            ("NO_NUMERABLE", uncountable_sets, {"set": 1, "infinite": 1, "not_enumerable": 1}),
        ):
            name = f"SET_{prefix}_{j:02d}"
            collection.append((j, name))
            _register(space, name, f"conjunto {prefix.lower()} {j}", f"{prefix.lower()} set {j}",
                      {**features, f"identity:{name}": 0.5}, "entity")

    # Individuos y propiedades (parche-10). Los *_N_* solo se usan en test.
    for prefix, kind in (("IND", "individual"), ("PROP", "property")):
        for i in range(80):
            nm = f"{prefix}_{i:02d}"
            _register(space, nm, f"{kind} {i}", f"{kind} {i}", {kind: 1, f"identity:{nm}": 0.5}, "entity")
        for i in range(10):
            nm = f"{prefix}_N_{i:02d}"
            _register(space, nm, f"{kind} nuevo {i}", f"new {kind} {i}", {kind: 1, f"identity:{nm}": 0.5}, "entity")

    space.build_space(seed=42)
    return space, order_entities, object_entities, meltables, finite_sets, countable_sets, uncountable_sets


def build_datasets(space, order_entities, object_entities, meltables,
                   finite_sets, countable_sets, uncountable_sets):
    splits = {"train": [], "val": [], "test": []}
    rule_of = {}  # id(ejemplo) -> regla (para equilibrar el entrenamiento)
    current_rule = ["transitivity"]

    rng = random.Random(7)
    pools = {
        "obj": [o for _, _, o in object_entities],
        "sub": [m for _, _, m in meltables],
        "set": [n for grp in (finite_sets, countable_sets, uncountable_sets) for _, n in grp],
    }

    def distractor(subject, kind):
        """Hecho irrelevante sobre OTRA entidad (nunca encadena con la regla)."""
        entity = rng.choice([e for e in pools[kind] if e != subject])
        pred, obj = {"obj": ("LIBERADO_EN", "AIRE"), "sub": ("EXPUESTO_A", "CALOR"),
                     "set": ("ES_INFINITO", "TRUE")}[kind]
        return space.encode_proposition(entity, pred, obj)

    def emit(split, props, target, subject, kind, partials=(), sample=1.0):
        """Variante base + premisas permutadas + distractor + premisas insuficientes.

        Las insuficientes entrenan/evaluan que la red NO concluya sin evidencia
        (objetivo: SUJETO SIN_CONCLUSION NINGUNA)."""
        add(split, props, target, "base")
        if rng.random() > sample:
            return
        if len(props) == 2:
            add(split, props[::-1], target, "swapped")
        noisy = list(props)
        noisy.insert(rng.randint(0, len(noisy)), distractor(subject, kind))
        add(split, noisy, target, "distractor")
        none = space.encode_proposition(subject, "SIN_CONCLUSION", "NINGUNA")
        for partial in partials:
            add(split, [partial], none, "insufficient")

    def add(split, premises, target, variant="base"):
        premise_vectors = [torch.as_tensor(v, dtype=torch.float32) for v in premises]
        if not 1 <= len(premise_vectors) <= MAX_PREMISES:
            raise ValueError("Numero de premisas fuera de rango.")
        seq = torch.zeros(MAX_PREMISES, D_CONCEPT)
        mask = torch.zeros(MAX_PREMISES, dtype=torch.bool)
        seq[:len(premise_vectors)] = torch.stack(premise_vectors)
        mask[:len(premise_vectors)] = True
        example = (seq, mask, torch.as_tensor(target, dtype=torch.float32))
        splits[split].append(example)
        rule_of[id(example)] = (current_rule[0], variant)

    # Regla 1: transitividad. Cada arista ordenada (X,Y) pertenece a un
    # unico bucket. Las dos premisas de TODOS los splits se toman solo de
    # aristas train; la arista conclusion determina el split. De este modo,
    # una conclusion de validacion/test no se filtra como premisa en train.
    def pair_split(source_idx, target_idx):
        bucket = (source_idx * 31 + target_idx * 17) % 10
        return "test" if bucket == 0 else ("val" if bucket == 1 else "train")

    for i, a in enumerate(order_entities):
        for j, b in enumerate(order_entities):
            if i == j or pair_split(i, j) != "train":
                continue
            for k, c in enumerate(order_entities):
                if k == i or k == j:
                    continue
                if pair_split(j, k) != "train":
                    continue
                split = pair_split(i, k)
                p1 = space.encode_proposition(a, "MAYOR_QUE", b)
                p2 = space.encode_proposition(b, "MAYOR_QUE", c)
                target = space.encode_proposition(a, "MAYOR_QUE", c)
                emit(split, [p1, p2], target, a, "obj", partials=[p1], sample=0.12)
                # Mismas cadenas con otros predicados de orden (solo ~30%): ensenan que
                # la regla es "encadenar y CONSERVAR la relacion", no la palabra MAYOR_QUE.
                if rng.random() < 0.3:
                    other = rng.choice(["MENOR_QUE", "SUPERIOR_A"])
                    add(split, [space.encode_proposition(a, other, b), space.encode_proposition(b, other, c)],
                        space.encode_proposition(a, other, c), "order_variants")

    # Regla 1b (parche-7): cadenas de varios pasos. Tres aristas train A>B, B>C,
    # C>D => A>D (entrenamiento/val/test, el par A>D decide el split). Cadenas de
    # CUATRO aristas (A>E) aparecen SOLO en test: miden si la red extrapola a una
    # longitud que nunca vio.
    n = len(order_entities)
    chains3, chains4 = [], []
    for a in range(n):
        for b in range(n):
            if b == a or pair_split(a, b) != "train":
                continue
            for c in range(n):
                if c in (a, b) or pair_split(b, c) != "train":
                    continue
                for d in range(n):
                    if d in (a, b, c) or pair_split(c, d) != "train":
                        continue
                    chains3.append((a, b, c, d))
                    for e in range(n):
                        if e in (a, b, c, d) or pair_split(d, e) != "train":
                            continue
                        if pair_split(a, e) == "test":
                            chains4.append((a, b, c, d, e))
    rng.shuffle(chains3)
    rng.shuffle(chains4)
    quota = {"train": 1500, "val": 120, "test": 200}
    taken = {"train": 0, "val": 0, "test": 0}
    current_rule[0] = "chain3"
    for a, b, c, d in chains3:
        split = pair_split(a, d)
        if taken[split] >= quota[split]:
            continue
        taken[split] += 1
        names = [order_entities[x] for x in (a, b, c, d)]
        props = [space.encode_proposition(names[i], "MAYOR_QUE", names[i + 1]) for i in range(3)]
        add(split, props, space.encode_proposition(names[0], "MAYOR_QUE", names[3]), "chain3")
        # Con una premisa irrelevante la secuencia llega a 4 posiciones: asi la 4a
        # posicion se entrena SIN ensenar cadenas de 4 (chain4 sigue siendo inedita).
        if rng.random() < 0.5:
            noisy = list(props)
            noisy.insert(rng.randint(0, 3), distractor(names[0], "obj"))
            add(split, noisy, space.encode_proposition(names[0], "MAYOR_QUE", names[3]), "chain3_distractor")
    current_rule[0] = "chain4"
    for chain in chains4[:150]:
        names = [order_entities[x] for x in chain]
        props = [space.encode_proposition(names[i], "MAYOR_QUE", names[i + 1]) for i in range(4)]
        add("test", props, space.encode_proposition(names[0], "MAYOR_QUE", names[4]), "chain4")

    # Regla 1c (parche-8): predicado nunca visto. Misma estructura que la
    # transitividad pero con ANTERIOR_A / POSTERIOR_A, que NO aparecen en ningun
    # ejemplo de train/val. Solo test. Mide si la red aplico la estructura
    # ("encadenar y conservar la relacion") o memorizo la palabra MAYOR_QUE.
    current_rule[0] = "unseen_predicate"
    novel = [(a, b, c) for a in range(n) for b in range(n) for c in range(n)
             if len({a, b, c}) == 3 and pair_split(a, b) == "train" and pair_split(b, c) == "train"
             and pair_split(a, c) == "test"]
    rng.shuffle(novel)
    for k, (a, b, c) in enumerate(novel[:120]):
        pred = "POSTERIOR_A" if k % 2 == 0 else "ANTERIOR_A"
        names = [order_entities[x] for x in (a, b, c)]
        props = [space.encode_proposition(names[0], pred, names[1]),
                 space.encode_proposition(names[1], pred, names[2])]
        add("test", props, space.encode_proposition(names[0], pred, names[2]), "unseen_predicate")

    # Regla 1d (parche-10): herencia de propiedades con DOS predicados distintos.
    #   x HEREDA p, p IMPLICA q  =>  x HEREDA q      (train/val)
    # El predicado de la conclusion viene de la 1a premisa y no de la 2a, y si el
    # termino medio NO coincide ("nojoin") no hay conclusion.
    # En TEST se usa la misma estructura con predicados (TIENE_RASGO, PRODUCE) y
    # entidades (IND_N_*, PROP_N_*) que no existen en train/val.
    names = space.concept_to_id
    inds = sorted(k for k in names if k.startswith("IND_") and "_N_" not in k)
    props_old = sorted(k for k in names if k.startswith("PROP_") and "_N_" not in k)
    inds_new = sorted(k for k in names if k.startswith("IND_N_"))
    props_new = sorted(k for k in names if k.startswith("PROP_N_"))

    def inherit(split, x, p, q, hp, ha, tag, other=None):
        """La REGLA viaja como premisa: (hp REGLA_HEREDA ha) declara que, si
        x hp p  y  p ha q, entonces x hp q. Sin esa premisa no hay conclusion."""
        enc = space.encode_proposition
        first, second, rule = enc(x, hp, p), enc(p, ha, q), enc(hp, "REGLA_HEREDA", ha)
        none = enc(x, "SIN_CONCLUSION", "NINGUNA")
        label = "inherit_" + tag
        if tag == "base":
            add(split, [first, second, rule], enc(x, hp, q), label)
        elif tag == "swapped":
            props_ = [first, second, rule]
            rng.shuffle(props_)
            add(split, props_, enc(x, hp, q), label)
        elif tag == "nojoin":
            add(split, [first, enc(other, ha, q), rule], none, label)
        elif tag == "norule":
            add(split, [first, second], none, label)
        elif tag == "insufficient":
            add(split, [first, rule], none, label)

    current_rule[0] = "inherit"
    made = 0
    pair_choices = [("HEREDA", "IMPLICA"), ("POSEE", "CAUSA"), ("ADQUIERE", "DERIVA_EN"),
                    ("MUESTRA", "ORIGINA"), ("EXHIBE", "PROVOCA")]
    while made < 4500:
        x = rng.choice(inds)
        p, q, r = rng.sample(props_old, 3)
        split = "val" if (inds.index(x) * 7 + props_old.index(q) * 13) % 10 == 0 else "train"
        if split == "val" and made > 100 and rng.random() < 0.8:
            continue
        roll = rng.random()
        tag = ("base" if roll < 0.35 else "swapped" if roll < 0.5 else "nojoin" if roll < 0.75
               else "norule" if roll < 0.9 else "insufficient")
        hp, ha = rng.choice(pair_choices)
        inherit(split, x, p, q, hp, ha, tag, other=r)
        made += 1

    # nojoin tambien en transitividad (aristas train; el par a>d decide el split)
    current_rule[0] = "transitivity_nojoin"
    done, tries = 0, 0
    while done < 900 and tries < 60000:
        tries += 1
        a, b, c, d = rng.sample(range(n), 4)
        if pair_split(a, b) != "train" or pair_split(c, d) != "train":
            continue
        split = pair_split(a, d)
        add(split, [space.encode_proposition(order_entities[a], "MAYOR_QUE", order_entities[b]),
                    space.encode_proposition(order_entities[c], "MAYOR_QUE", order_entities[d])],
            space.encode_proposition(order_entities[a], "SIN_CONCLUSION", "NINGUNA"), "nojoin")
        done += 1

    current_rule[0] = "unseen_structure"
    for k in range(150):
        x = rng.choice(inds_new)
        p, q, r = rng.sample(props_new, 3)
        tag = "base" if k < 60 else "swapped" if k < 80 else "nojoin" if k < 115 else "norule"
        inherit("test", x, p, q, "TIENE_RASGO", "PRODUCE", tag, other=r)
        # etiqueta de test propia para no mezclarla con la de entrenamiento
        ex = splits["test"][-1]
        rule_of[id(ex)] = ("unseen_structure", "NUEVA_" + tag)

    # Regla 1e (parche-12): contradicciones.
    #   A>B, B>A        => A CONTRADICE B
    #   A>B, B>C, C>A   => A CONTRADICE A   (ciclo)
    # En train solo con aristas train; en val/test el par (a,b) decide el split.
    current_rule[0] = "contradiction"
    quotas = {"train": 700, "val": 70, "test": 100}
    got2 = {"train": 0, "val": 0, "test": 0}
    got3 = {"train": 0, "val": 0, "test": 0}
    enc_ = space.encode_proposition
    for _ in range(40000):
        a, b, c = rng.sample(range(n), 3)
        split = pair_split(a, b)
        if split == "train" and (pair_split(b, a) != "train"):
            continue
        A, B, C = order_entities[a], order_entities[b], order_entities[c]
        if got2[split] < quotas[split]:
            got2[split] += 1
            add(split, [enc_(A, "MAYOR_QUE", B), enc_(B, "MAYOR_QUE", A)], enc_(A, "CONTRADICE", B), "contradiction")
        if split == "train" and (pair_split(b, c) != "train" or pair_split(c, a) != "train"):
            continue
        if got3[split] < quotas[split]:
            got3[split] += 1
            add(split, [enc_(A, "MAYOR_QUE", B), enc_(B, "MAYOR_QUE", C), enc_(C, "MAYOR_QUE", A)],
                enc_(A, "CONTRADICE", A), "cycle")
        if all(got2[k] >= quotas[k] and got3[k] >= quotas[k] for k in quotas):
            break

    current_rule[0] = "fall"
    # Regla 2: objeto liberado en el aire y sometido a gravedad -> cae.
    for category, j, obj in object_entities:
        split = "test" if j % 8 == 0 else ("val" if j % 8 == 1 else "train")
        p1 = space.encode_proposition(obj, "LIBERADO_EN", "AIRE")
        p2 = space.encode_proposition(obj, "SOMETIDO_A", "GRAVEDAD")
        target = space.encode_proposition(obj, "CAE_HACIA", "SUELO")
        emit(split, [p1, p2], target, obj, "obj", partials=[p1, p2])

    current_rule[0] = "melting"
    # Regla 3: exposicion termica de una sustancia fundible -> estado liquido.
    for category, j, substance in meltables:
        split = "test" if j % 8 == 0 else ("val" if j % 8 == 1 else "train")
        p1 = space.encode_proposition(substance, "EXPUESTO_A", "CALOR")
        p2 = space.encode_proposition(substance, "ES", "FUNDIBLE")
        target = space.encode_proposition(substance, "CAMBIA_A", "LIQUIDO")
        emit(split, [p1, p2], target, substance, "sub", partials=[p1, p2])

    # Reglas de cardinalidad con evidencia explicita. No se infiere que un
    # conjunto sea no numerable por el mero hecho de ser infinito.
    current_rule[0] = "finite"
    for j, set_name in finite_sets:
        split = "test" if j % 6 == 0 else ("val" if j % 6 == 1 else "train")
        premise = space.encode_proposition(set_name, "ES_FINITO", "TRUE")
        target = space.encode_proposition(set_name, "ES", "ENUMERABLE")
        emit(split, [premise], target, set_name, "set")

    current_rule[0] = "countable"
    for j, set_name in countable_sets:
        split = "test" if j % 6 == 0 else ("val" if j % 6 == 1 else "train")
        p1 = space.encode_proposition(set_name, "ES_INFINITO", "TRUE")
        p2 = space.encode_proposition(set_name, "TIENE_BIYECCION_CON", "NATURALES")
        target = space.encode_proposition(set_name, "ES", "INFINITO_NUMERABLE")
        emit(split, [p1, p2], target, set_name, "set", partials=[p1])

    current_rule[0] = "uncountable"
    for j, set_name in uncountable_sets:
        split = "test" if j % 6 == 0 else ("val" if j % 6 == 1 else "train")
        p1 = space.encode_proposition(set_name, "ES_INFINITO", "TRUE")
        p2 = space.encode_proposition(set_name, "NO_TIENE_BIYECCION_CON", "NATURALES")
        target = space.encode_proposition(set_name, "ES", "INNUMERABLE")
        emit(split, [p1, p2], target, set_name, "set", partials=[p1])

    # Equilibrado SOLO del entrenamiento: la transitividad aporta ~2000 muestras
    # y las demas reglas decenas; se repiten las minoritarias (sin tocar val/test).
    by_rule = {}
    for ex in splits["train"]:
        by_rule.setdefault(rule_of[id(ex)][0], []).append(ex)
    target_size = max(len(v) for v in by_rule.values()) // 3
    balanced = []
    for rule, exs in by_rule.items():
        reps = 1 if rule in ("transitivity", "chain3", "inherit", "transitivity_nojoin", "contradiction") else max(1, round(target_size / len(exs)))
        balanced.extend(exs * reps)
    splits["train"] = balanced

    datasets = {}
    for split, examples in splits.items():
        if not examples:
            raise RuntimeError(f"El split {split} ha quedado vacio.")
        seqs = torch.stack([item[0] for item in examples])
        masks = torch.stack([item[1] for item in examples])
        targets = torch.stack([item[2] for item in examples])
        datasets[split] = TensorDataset(seqs, masks, targets)
        datasets[split].tags = [rule_of[id(item)] for item in examples]  # (regla, variante)
    return datasets


def main():
    print("[*] Iteracion de ontologia y datos composicionales")
    os.makedirs("data", exist_ok=True)
    (space, order_entities, object_entities, meltables,
     finite_sets, countable_sets, uncountable_sets) = build_ontology()
    datasets = build_datasets(space, order_entities, object_entities, meltables,
                              finite_sets, countable_sets, uncountable_sets)

    with open("data/concept_space.pkl", "wb") as handle:
        pickle.dump(space, handle, protocol=pickle.HIGHEST_PROTOCOL)
    filenames = {
        "train": "concept_train_dataset.pkl",
        "val": "concept_val_dataset.pkl",
        "test": "concept_test_dataset.pkl",
    }
    for split, dataset in datasets.items():
        with open(os.path.join("data", filenames[split]), "wb") as handle:
            pickle.dump(dataset, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # Alias compatible con scripts antiguos que esperaban concept_dataset.pkl.
    with open("data/concept_dataset.pkl", "wb") as handle:
        pickle.dump(datasets["train"], handle, protocol=pickle.HIGHEST_PROTOCOL)

    manifest = {
        "schema_version": 2,
        "d_concept": D_CONCEPT,
        "max_premises": MAX_PREMISES,
        "concepts": len(space.concept_to_id),
        "propositions": len(space.proposition_vectors),
        "samples": {k: len(v) for k, v in datasets.items()},
        "split_policy": "Transitivity: target pair sets the split; both premise pairs must belong to train, preventing val/test target edges from appearing as training inputs. Other rules hold out complete entity instances.",
        "semantic_note": "Explicit feature ontology with role-bound proposition vectors; not pretrained language semantics.",
    }
    with open("data/dataset_manifest.json", "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    print(f"[+] Conceptos: {manifest['concepts']} | proposiciones: {manifest['propositions']}")
    print("[+] Muestras: " + " | ".join(f"{k}={len(v)}" for k, v in datasets.items()))
    print("[+] Ontologia y datasets guardados en data/.")


if __name__ == "__main__":
    main()

''',
    'scripts/pretrain_ear.py': r'''"""Preentrena el oido leyendo el libro (palabras ocultas). Despues:  python -m scripts.train_ear

REGLA DE DECISION (fijada ANTES de medir). Se adopta el preentrenamiento si:
  1) acierto top-1 en frases NO vistas >= linea base + 10 puntos (la linea base es "siempre la palabra mas frecuente"),
  2) tras  train_ear  las filas a, b, f, g de evaluate_ear no bajan mas de 1 punto respecto a antes
     (antes: a 98.6, b 96.6, f 100, g 98.0),
  3) y mejoran d (antes 82.8) o e (antes 90.8) en >= 2 puntos.
"""
import os
import random
import time
from collections import Counter

import torch

from src.language.ear import Ear
from src.language.lm import LMHead, PUNCT, build_vocab, evaluate, is_heldout, lm_loss, load_sentences

EPOCHS = int(os.environ.get("PRE_EPOCHS", 40))
BATCH = 128


def main():
    torch.manual_seed(0)
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    data = load_sentences("data/libro.txt")
    train = [t for t in data if not is_heldout(t)]
    held = [t for t in data if is_heldout(t)]
    words = sum(len(t) for t in data)
    print(f"Libro: {len(data)} frases ({words} palabras). Entreno {len(train)}, reservadas para prueba {len(held)}.")
    if len(train) < 500:
        print("[!] Muy poco texto: ejecuta antes  python -m scripts.read_book  (genera data/libro.txt).")
        return
    vocab = build_vocab(train)
    head = LMHead(128, vocab).to(device)
    ear = Ear().to(device)
    freq = Counter(w for t in held for w in t if w not in PUNCT)
    top_word, _ = Counter(w for t in train for w in t if w not in PUNCT).most_common(1)[0]
    base = freq[top_word] / max(sum(freq.values()), 1)
    print(f"Vocabulario a adivinar: {len(vocab)} palabras. Linea base ('siempre \"{top_word}\"'): {base:.1%}")
    params = list(ear.parameters()) + list(head.parameters())
    opt = torch.optim.AdamW(params, lr=2e-3, weight_decay=0.01)
    steps = EPOCHS * (len(train) // BATCH)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=2e-3, total_steps=steps, pct_start=0.1)
    rng = random.Random(0)
    t0, step, best = time.time(), 0, (-1.0, None)
    for epoch in range(EPOCHS):
        rng.shuffle(train)
        ear.train(); head.train()
        for b in range(len(train) // BATCH):
            loss, acc, _ = lm_loss(ear, head, train[b * BATCH:(b + 1) * BATCH], rng, device)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step(); sched.step(); step += 1
        if (epoch + 1) % 5 == 0 or epoch == EPOCHS - 1:
            t1, t5, n = evaluate(ear, head, held, device)
            print(f"  epoca {epoch+1:3d}  entreno {acc:.1%} | NO vistas: top-1 {t1:.1%}, top-5 {t5:.1%} ({n} huecos)  ({time.time()-t0:.0f}s)", flush=True)
            if t1 > best[0]:
                best = (t1, ({k: v.detach().cpu().clone() for k, v in ear.state_dict().items()},
                             {k: v.detach().cpu().clone() for k, v in head.state_dict().items()}))
    t1, state = best
    ear.load_state_dict(state[0]); head.load_state_dict(state[1])
    os.makedirs("checkpoints", exist_ok=True)
    torch.save(ear.state_dict(), "checkpoints/ear_pre.pt")
    head.save("checkpoints/ear_lm.pt")
    gain = t1 - base
    print(f"\nMejor acierto en frases no vistas: {t1:.1%} (linea base {base:.1%}, +{gain*100:.1f} puntos)")
    print(f"Criterio 1 (>= +10 puntos): {'CUMPLIDO' if gain >= 0.10 else 'NO CUMPLIDO'}")
    print("[+] Guardado checkpoints/ear_pre.pt y checkpoints/ear_lm.pt. Siguiente:  python -m scripts.train_ear")


if __name__ == "__main__":
    main()
''',
    'scripts/read_book.py': r'''"""Lee un libro (RTF o TXT), saca sus frases y mide que entiende el oido de lenguaje REAL (parche-17).

Uso:  python -m scripts.read_book [archivo]        (por defecto busca regenta.rtf / regenta.txt)
Escribe: data/libro.txt (texto limpio) y reports/libro_muestras.txt (ejemplos para revisar).
No entrena nada: solo mide y descubre que relaciones usa el libro.
"""
import os
import random
import re
import sys
from collections import Counter

import torch

from src.language.book import rtf_to_text, sentences
from src.language.book_vocab import extract_vocab, save_vocab
from src.language.corpus import base_pool, es_pool
from src.language.ear import Ear, predict
from src.language.lexicon import PREPS, norm, tokenize

COP = {"es", "era", "fue", "eran", "son", "seran", "sera", "fueron"}
ARTS = {"el", "la", "los", "las", "un", "una", "unos", "unas"}


def find_file(argv):
    for cand in argv[1:] + ["regenta.rtf", "regenta.txt"]:
        if os.path.exists(cand):
            return cand
    raise SystemExit("No encuentro el libro. Ponlo en la carpeta del proyecto como regenta.rtf o pasa la ruta.")


def mine_relations(sents, top=30, min_count=3):
    c = Counter()
    for s in sents:
        t = tokenize(s)
        for i in range(len(t) - 2):
            if t[i] in COP:
                j = i + 1
                if j < len(t) and t[j] in ARTS:
                    j += 1
                if j + 1 < len(t) and t[j].isalpha() and len(t[j]) >= 4 and t[j + 1] in PREPS and t[j] not in ARTS:
                    c[(t[j], t[j + 1])] += 1
    return [(h, p, n) for (h, p), n in c.most_common(top) if n >= min_count]


def main():
    path = find_file(sys.argv)
    raw = open(path, "rb").read().decode("utf-8", errors="ignore") if not path.endswith(".rtf") else open(path, "rb").read().decode("latin-1")
    text = rtf_to_text(raw) if path.endswith(".rtf") else raw
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    open("data/libro.txt", "w", encoding="utf-8").write(text)
    sents = sentences(text)
    toks_all = tokenize(text)
    print(f"Libro: {path} | {len(text)/1e6:.2f} M caracteres | {len(toks_all)} palabras | {len(sents)} frases/clausulas utiles")
    mid = len(text) // 2
    print("\n--- Fragmento del texto convertido (compruebalo: debe leerse bien, con tildes) ---")
    print(text[mid:mid + 500].replace("\n", " / "))
    print("--- fin del fragmento ---")
    cnt = Counter(toks_all)
    print("Veces: era=%d es=%d fue=%d de=%d hijo=%d hija=%d marido=%d mujer=%d amigo=%d" % tuple(
        cnt[w] for w in ("era", "es", "fue", "de", "hijo", "hija", "marido", "mujer", "amigo")))
    nouns = Counter()
    for a, b, c in zip(toks_all, toks_all[1:], toks_all[2:]):
        if a in ARTS and len(b) >= 4 and c in ("de", "del") and b.isalpha():
            nouns[b] += 1
    print("Sustantivos mas frecuentes en 'el/la <x> de': " + ", ".join(f"{w} ({n})" for w, n in nouns.most_common(25)))
    rels = mine_relations(sents)
    print("\nRelaciones del tipo 'es/era <nombre> de ...' mas frecuentes en el libro:")
    print("  " + ", ".join(f"{h} {p} ({n})" for h, p, n in rels[:25]))
    vocab = extract_vocab(text, sents)
    save_vocab(vocab)
    print(f"\nVocabulario REAL guardado en data/libro_vocab.json: {len(vocab['names'])} nombres propios, {len(vocab['nouns'])} sustantivos, "
          f"{len(vocab['adjs'])} adjetivos, {len(vocab['advs'])} adverbios, {len(vocab['clauses'])} clausulas.")
    print("  Nombres:", ", ".join(vocab["names"][:20]))
    print("  Adjetivos:", ", ".join(vocab["adjs"][:20]))
    if not os.path.exists("checkpoints/ear.pt"):                      # reproduccion desde cero: el oido se entrena DESPUES (parche-62)
        print("\n[i] Todavia no existe checkpoints/ear.pt: se salta la medicion con el oido. Ya estan guardados data/libro.txt y data/libro_vocab.json.\n"
              "    Orden desde cero: read_book -> pretrain_ear -> train_ear. Si quieres la medicion, repite  python -m scripts.read_book  al final.")
        return
    cands = {}
    for p in base_pool() + es_pool():
        cands[p[1]] = p[0]
    for k in "hijo hija padre madre marido mujer hermano hermana amigo amiga primo prima tio tia sobrino sobrina criado criada".split():
        cands[f"{k} de"] = f"{k}_de".upper()
    cands = [(n, t) for t, n in cands.items()]
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    ear = Ear()
    ear.load_state_dict(torch.load("checkpoints/ear.pt", map_location="cpu"))
    ear.to(device)
    rng = random.Random(0)
    sample = rng.sample(sents, min(8000, len(sents)))
    outs = predict(ear, [tokenize(s) for s in sample], cands, device)
    ok = [(s, o) for s, o in zip(sample, outs) if o["confidence"] >= 0.8]
    print(f"\nDe {len(sample)} clausulas reales al azar, el oido acepta {len(ok)} ({len(ok)/len(sample):.1%}) como afirmaciones de relacion.")
    print("(En una novela casi todo es descripcion: lo esperable es que acepte muy pocas, y que las aceptadas sean de verdad relaciones.)")
    lines = ["=== ACEPTADAS (revisa si de verdad son afirmaciones de relacion) ==="]
    for s, o in rng.sample(ok, min(40, len(ok))):
        lines.append(f"{s}\n    -> {'NO ' if o['negated'] else ''}{o['subject']} {o['predicate']} {o['object']}   ({o['confidence']:.0%})")
    lines.append("\n=== RECHAZADAS AL AZAR (deberian ser prosa sin relacion) ===")
    rej = [(s, o) for s, o in zip(sample, outs) if o["confidence"] < 0.8]
    for s, o in rng.sample(rej, min(15, len(rej))):
        lines.append(f"{s}   ({o['confidence']:.0%})")
    open("reports/libro_muestras.txt", "w", encoding="utf-8").write("\n".join(lines))
    print("\n".join(lines[:30]))
    print("\n(Ejemplos completos en reports/libro_muestras.txt: pegame ese archivo o sus primeras lineas)")


if __name__ == "__main__":
    main()
''',
    'scripts/reproduce.py': r'''"""Reproduce el proyecto de principio a fin con UN comando.

  python -m scripts.reproduce                    # todo (necesita internet para UD y un libro/texto en espanol)
  python -m scripts.reproduce --libro mi_texto.txt
  python -m scripts.reproduce --desde train_school
  python -m scripts.reproduce --lista            # solo muestra los pasos
  python -m scripts.reproduce --semilla 7        # otra semilla global (LCM_SEED) para todos los entrenamientos
  python -m scripts.reproduce --rapido           # salta lo opcional y largo (pretrain_ear, evaluaciones online)

Cada paso es un modulo de scripts/. Si uno falla, se para y se dice cual (arreglalo y repite con --desde <paso>).
Las salidas se guardan en reports/reproduce_<paso>.log. Los criterios de aceptacion de cada paso estan escritos en sus
docstrings y se fijaron ANTES de medir; reports/RESULTADOS.md recoge lo que obtuvimos nosotros.
"""
import argparse
import json
import os
import subprocess
import sys
import time

# (nombre, modulo, args, opcional/largo, necesita libro)
STEPS = [
    ("tests_unitarios", "pytest", ["-q", "tests"], False, False),
    ("prepare_concepts", "scripts.prepare_concepts", [], False, False),
    ("train_reasoner", "scripts.train_reasoner", [], False, False),
    ("evaluate_reasoner", "scripts.evaluate_reasoner", [], False, False),
    ("read_book", "scripts.read_book", [], False, True),
    ("pretrain_ear", "scripts.pretrain_ear", [], True, True),
    ("train_ear", "scripts.train_ear", [], False, False),
    ("evaluate_ear", "scripts.evaluate_ear", [], False, False),
    ("read_book_medida", "scripts.read_book", [], True, True),      # ahora que el oido existe: mide cuantas frases del libro acepta (informativo)
    ("get_data", "scripts.get_data", [], False, False),
    ("train_school", "scripts.train_school", [], False, False),
    ("eval_frases", "scripts.eval_frases", [], False, False),
    ("eval_preguntas", "scripts.eval_preguntas", [], False, False),
    ("check_todo", "scripts.check", [], False, False),          # TODAS las pruebas de conversacion/razonamiento (parche-54..59)
    ("evaluate_online", "scripts.evaluate_online", [], True, False),
    ("evaluate_negatives", "scripts.evaluate_negatives", [], True, False),
    ("evaluate_inoculate", "scripts.evaluate_inoculate", [], True, False),
    ("evaluate_sleep", "scripts.evaluate_sleep", [], True, False),
    ("verificar_manifiesto", "scripts.manifiesto", ["--verificar"], False, False),    # mismo codigo que el manifiesto
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--libro", help="texto en espanol (.txt/.rtf) para el oido; por defecto regenta.rtf/.txt si existe")
    ap.add_argument("--desde", help="empezar en este paso")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--semilla", type=int, help="semilla global (LCM_SEED); por defecto 0, la de la referencia")
    ap.add_argument("--lista", action="store_true")
    a = ap.parse_args()
    names = [s[0] for s in STEPS]
    if a.desde and a.desde not in names:
        sys.exit(f"Paso desconocido. Pasos: {', '.join(names)}")
    if a.lista:
        print("\n".join(f"{i + 1:2d}. {n}" for i, n in enumerate(names)))
        return
    os.makedirs("reports", exist_ok=True)
    env = dict(os.environ, LCM_SEED=str(a.semilla if a.semilla is not None else os.environ.get("LCM_SEED", "0")), PYTHONHASHSEED="0", PYTHONUNBUFFERED="1")
    summary = []
    started = a.desde is None
    for name, mod, args, optional, needs_book in STEPS:
        if name == a.desde:
            started = True
        if not started or (a.rapido and optional):
            continue
        if needs_book and name in ("read_book", "read_book_medida"):
            if a.libro:
                args = [a.libro]
            elif not any(os.path.exists(f) for f in ("regenta.rtf", "regenta.txt")):
                print("[!] Salto read_book y los pasos que dependen del texto: pasa --libro tu_texto.txt "
                      "(cualquier novela o texto largo en espanol).")
                continue
        if needs_book and name == "pretrain_ear" and not os.path.exists("data/libro.txt"):
            continue
        print(f"\n=== {name} ===", flush=True)
        t0 = time.time()
        with open(os.path.join("reports", f"reproduce_{name}.log"), "w", encoding="utf-8") as log:
            p = subprocess.Popen([sys.executable, "-m", mod] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, env=env)
            tail = []
            for line in p.stdout:
                log.write(line)
                print(line, end="")
                tail.append(line)
            p.wait()
        summary.append({"paso": name, "codigo": p.returncode, "segundos": round(time.time() - t0, 1), "semilla": env["LCM_SEED"]})
        json.dump(summary, open("reports/reproduce_resumen.json", "w"), indent=1)
        if p.returncode != 0:
            sys.exit(f"\n[!] Fallo en '{name}' (codigo {p.returncode}). Log: reports/reproduce_{name}.log\n"
                     f"    Arreglalo y repite con:  python -m scripts.reproduce --desde {name}")
        print(f"[ok] {name} ({time.time() - t0:.0f}s)")
    print("\n[OK] Fin. Ahora prueba la conversacion:  python -m scripts.think")


if __name__ == "__main__":
    main()
''',
    'scripts/think.py': r'''import json
import os
import pickle
import re
import time
import copy
import torch
from configs.config import LCMConfig
from src.memory import MemoryStore
from src.model.reasoner import LatentReasoner
from src.reasoning.engine import ReasoningEngine
from src.reasoning.rule_engine import Fact
from src.training.online import OnlineLearner
from src.language import Ear, EarParser
from src.language.online_ear import EarLearner
from src.language.lexicon import norm
from src.language.qa import QA, is_question, template_from
from src.memory.schema import is_entity
from src.reasoning.lessons import apply_lessons, inherit, compare
from src.language.dialogue import Dialogue
from src.language.discourse import split_sentences, next_topic

BASE_CKPT = "checkpoints/lcm_reasoner.pt"
ONLINE_CKPT = "checkpoints/lcm_online.pt"

HELP = """Comandos (todo en mayusculas):
  s p o | s p o | ...            razonar con esas premisas (hasta 4)
  NUEVO a b ...                  anadir entidades nuevas al catalogo (se recuerdan)
  NUEVO_PRED a b ...             anadir relaciones nuevas
  APRENDE p1 | p2 => conclusion  ENSENAR una regla con un ejemplo (el modelo se ajusta, con repaso)
  CORRIGE s p o                  ensenar la conclusion correcta para las ultimas premisas
  HECHO s p o                    guardar un hecho en la memoria (sin ajustar el modelo)
  OLVIDA s p o                   borrar un hecho
  PREGUNTA a p c                 buscar en la memoria una cadena de hechos de a a c y razonar
  DORMIR                         ciclo de sueno: consolida lo aprendido
  ENTENDI s p o [NEGADO]         corregir lo que entendi de tu ultima frase (el oido y la escuela aprenden)
  (frases normales)              p. ej. "Pedro es padre de Sara"  |  "Si Ana es madre de Luis, entonces Luis es hijo de Ana"
  ARBOL frase                    ver como analiza la escuela cada palabra de una frase
  (pregunta)                     escribe una pregunta con ¿...? y te contesto con lo que he aprendido (p. ej. ¿Quién escribió una novela?)
  MEMORIA                        resumen de lo aprendido
  GUARDAR | SALIR
"""


def load_checkpoint(path, device):
    try:
        return torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        return torch.load(path, map_location=device)


def save_online(model, config):
    os.makedirs("checkpoints", exist_ok=True)
    torch.save({"model_state_dict": model.state_dict(),
                "config": {"d_concept": config.d_concept, "n_layers": config.n_layers, "n_heads": config.n_heads,
                           "max_concept_seq": config.max_concept_seq, "dropout": config.dropout}}, ONLINE_CKPT)


def parse_triples(text):
    groups = [part.strip().split() for part in text.split("|") if part.strip()]
    if not groups or any(len(g) != 3 for g in groups):
        return None
    return [tuple(g) for g in groups]


def main():
    if not os.path.exists(BASE_CKPT):
        print("[!] No hay checkpoint. Ejecuta primero: python -m scripts.train_reasoner")
        return
    if not os.path.exists("data/concept_space.pkl"):
        print("[!] No hay ontologia. Ejecuta primero: python -m scripts.prepare_concepts")
        return

    with open("data/concept_space.pkl", "rb") as handle:
        base_space = pickle.load(handle)
    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = load_checkpoint(BASE_CKPT, device)
    saved = checkpoint.get("config", {})
    config = LCMConfig(
        d_concept=base_space.d_concept,
        n_layers=int(saved.get("n_layers", 4)),
        n_heads=int(saved.get("n_heads", 4)),
        max_concept_seq=int(saved.get("max_concept_seq", 4)),
        dropout=float(saved.get("dropout", 0.05)),
        device=device,
    )
    model = LatentReasoner(config)
    model.set_space(base_space)
    model.load_state_dict(checkpoint["model_state_dict"])

    # Memoria: re-registra los conceptos aprendidos y, si existe, carga los pesos ajustados.
    memory = MemoryStore()
    space = copy.deepcopy(base_space)
    restored = memory.apply_concepts(space)
    model.set_space(space)
    if os.path.exists(ONLINE_CKPT):
        try:
            state = {k: v for k, v in load_checkpoint(ONLINE_CKPT, device)["model_state_dict"].items()
                     if k not in ("concepts", "roles")}       # el catalogo puede haber crecido: sus vectores son deterministas
            model.load_state_dict(state, strict=False)
            print("[+] Recuerdos cargados: pesos ajustados en sesiones anteriores.")
        except RuntimeError:
            print("[!] El checkpoint online no encaja con el catalogo actual; se usa el base.")
    model.to(device)

    engine = ReasoningEngine(model, space, device=device)
    learner = None
    if os.path.exists("data/concept_train_dataset.pkl") and os.path.exists("data/concept_val_dataset.pkl"):
        with open("data/concept_train_dataset.pkl", "rb") as h:
            train = pickle.load(h).tensors
        with open("data/concept_val_dataset.pkl", "rb") as h:
            val = pickle.load(h).tensors
        gen = torch.Generator().manual_seed(1)
        core_idx = torch.randperm(len(train[0]), generator=gen)[:4000]
        canary_idx = torch.randperm(len(val[0]), generator=gen)[:300]
        core = tuple(t[core_idx] for t in train)       # mismo indice para X, M, Y
        canary = tuple(t[canary_idx] for t in val)
        learner = OnlineLearner(model, space, core, canary, device=device)
        for l in memory.lessons:
            learner.lessons.append(([tuple(p) for p in l["premises"]], tuple(l["conclusion"])))
    else:
        print("[!] Sin datos de repaso: APRENDE queda desactivado (ejecuta prepare_concepts).")

    print("=" * 65)
    print(f" LARGE CONCEPTUAL MODEL (LCM) - RAZONAMIENTO Y APRENDIZAJE [{device.upper()}]")
    print("=" * 65)
    print(f" Memoria: {memory.summary()}" + (f" ({restored} conceptos restaurados)" if restored else ""))
    print(HELP)
    dirty = False
    last_premises = None
    ear = None
    ear_learner = None
    last_sentence = None
    ear = ear_learner = None
    for ckpt in ("checkpoints/ear_online.pt", "checkpoints/ear.pt"):
        if not os.path.exists(ckpt):
            continue
        try:
            _e = Ear()
            _e.load_state_dict(torch.load(ckpt, map_location="cpu"))
            ear = EarParser(_e, device)
            ear_learner = EarLearner(ear, device)
            print(f" [oido] Entiendo frases en espanol ({os.path.basename(ckpt)}). Si me malinterpreto: ENTENDI s p o [NEGADO].")
            break
        except Exception:
            print(f" [oido] {ckpt} no es compatible con esta version (se ignora).")
    school = None
    if os.path.exists("checkpoints/school.pt"):
        try:
            from src.language.school_parser import SchoolParser
            from src.language.ud import load_school
            from src.language.school_learn import load_overrides
            _s, _scripts = load_school(device=device)
            school = SchoolParser(_s, device, _scripts, load_overrides())
            print(" [escuela] Analizo frases libres en espanol (school.pt) cuando el oido de plantillas no las entiende.")
            from src.language.semilla import load_seed
            added = load_seed(memory, school)
            if added:
                memory.save()
                print(f" [semilla] Conocimiento de fabrica cargado: {added} hechos (colores, formas, naturaleza, cuerpo, objetos, opuestos...).")
        except Exception as exc:
            print(f" [escuela] school.pt no se pudo cargar ({type(exc).__name__}); se ignora.")
    if ear is None:
        print(" [oido] Sin oido valido: ejecuta  python -m scripts.train_ear")
    COMMANDS = {"NUEVO", "NUEVO_PRED", "APRENDE", "CORRIGE", "HECHO", "OLVIDA", "PREGUNTA", "MEMORIA",
                "GUARDAR", "SALIR", "EXIT", "QUIT", "DORMIR", "AYUDA", "ENTENDI", "ARBOL"}

    def vaccinate(preds):
        """Relacion nueva: aprende al momento que, sin regla, no concluye nada (evita conclusiones inventadas)."""
        nonlocal dirty
        if learner is None or not learner.lessons:
            return
        info = learner.inoculate(preds)
        if info.get("done"):
            dirty = True
            save_online(model, config)
            print(f"[vacuna] {', '.join(preds)}: sin regla, no concluyo nada (canario {info['canary']:.0%}).")
        else:
            print(f"[vacuna] no aplicada ({info.get('reason')}).")

    def register(names, kind):
        created = []
        for n in names:
            if n not in space.concept_to_id:
                feats = ({"predicate": 1, "relation": 1, f"identity:{n}": 0.5} if kind == "predicate"
                         else {"individual": 1, f"identity:{n}": 0.5})
                space.add_concept(n, features=feats, kind=kind)
                memory.add_concept(n, feats, kind)
                created.append(n)
        if created:
            model.set_space(space)
            model.to(device)
            if kind == "predicate":
                vaccinate(created)
        return created

    def log_dialogue(sentence, parsed):
        os.makedirs("memory", exist_ok=True)
        with open(os.path.join("memory", "dialogo.jsonl"), "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"t": time.time(), "frase": sentence, "significado": parsed}, ensure_ascii=False) + "\n")

    last_raw = {}
    topic = [None]          # sujeto de la frase anterior (parche-44): para "Ella..." y para el sujeto omitido

    def understand(clause):
        out = ear.parse(clause, ear.candidates(space)) if ear is not None else None
        last_raw["out"] = out
        if out is not None and out["confidence"] >= ear.min_conf:
            return out
        if school is not None:
            found = school.parse(clause)
            last_raw["school"] = found
            if found and len(found) == 1:
                t = found[0]
                return {"subject": t["s"].upper(), "predicate": t["p"].upper(), "object": t["o"].upper(),
                        "negated": t["neg"], "confidence": 1.0, "via": "escuela", "template": t.get("template"),
                        "s_disp": t.get("s_disp"), "o_disp": t.get("o_disp"), "when": t.get("when", ""), "when_disp": t.get("when_disp", "")}
        return None

    def understand_many(clause):
        """Una o varias proposiciones (coordinaciones, verbos con sujeto compartido, sujeto omitido)."""
        one = understand(clause)
        if one is not None and one.get("via") != "escuela":
            return [one]
        if school is None:
            return [one] if one else []
        found = school.parse(clause, topic=topic[0])
        last_raw["school"] = found
        if not found or len(found) > 6:
            return []
        return [{"subject": t["s"].upper(), "predicate": t["p"].upper(), "object": t["o"].upper(), "negated": t["neg"],
                 "confidence": 1.0, "via": "escuela", "template": t.get("template"), "s_disp": t.get("s_disp"),
                 "o_disp": t.get("o_disp"), "when": t.get("when", ""), "when_disp": t.get("when_disp", "")} for t in found]

    replay_cache = []
    backed_up = [False]

    def school_correct(sentence, trip):
        """ENTENDI tambien ensena a la escuela: ajuste pequeno con repaso, canario (conversacion) y reversion (parche-49)."""
        from src.language.school_learn import (append_log, learn_correction, read_log, replay_sentences, save_overrides,
                                               synthetic_replay)
        from src.language.ud import save_school
        canary = None
        if os.path.exists("data/frases_prueba.tsv"):
            from scripts.eval_frases import evaluate
            canary = lambda: evaluate(school, path="data/frases_prueba.tsv")[1]
        if not replay_cache:
            replay_cache.extend(replay_sentences(n=150) + synthetic_replay(200))
        info = learn_correction(school.model, device, school.scripts, sentence, trip, extra=read_log(), replay=replay_cache,
                                canary=canary, overrides=school.overrides)
        if info["done"]:
            if not backed_up[0] and os.path.exists("checkpoints/school.pt"):
                import shutil
                shutil.copy("checkpoints/school.pt", "checkpoints/school.pt.bak")
                backed_up[0] = True
            save_school(school.model, school.scripts)
            save_overrides(school.overrides)
            append_log(sentence, trip)
            c = info.get("canary") or (None, None)
            print("[escuela] Aprendido: ahora leo asi tu frase (repitela para que la guarde)." + (f" ({info['nota']})" if info.get("nota") else "") +
                  (f" Conversacion {c[0]:.0%} -> {c[1]:.0%}." if c[0] is not None else ""))
        else:
            print(f"[escuela] No he cambiado nada: {info.get('reason')}.")

    def explain_rejection():
        sc = last_raw.get("school")
        if sc:
            print("        (escuela: veo " + str(len(sc)) + " proposiciones: " + "; ".join(f"{t['s']} {t['p']} {t['o']}" for t in sc[:4]) +
                  " - solo acepto frases con UNA proposicion; simplifica la frase)")
        o = last_raw.get("out")
        if o and o.get("predicate"):
            print(f"        (mejor lectura: {o['subject']} {o['predicate']} {o['object']} | confianza {o['confidence']:.0%}, "
                  f"es-afirmacion {o['in_scope']:.0%}, umbral {ear.min_conf:.0%})")

    dialogue = Dialogue(memory)

    def answer_question(raw):
        if school is None:
            print("[pregunta] Necesito la escuela de espanol (python -m scripts.train_school).\n")
            return

        def deduce(facts):
            """Motor simbolico (relaciones fijas) + lecciones aprendidas con "Si... entonces..." (con explicacion)."""
            given = {Fact(*f) for f in facts}
            out = {(f.subject, f.predicate, f.obj): [] for f in engine.deduce(given)["facts"] - given}
            out.update(apply_lessons(facts, memory.active_lessons(), is_var=lambda n: is_entity(space, n)))
            for k, v in list(inherit(facts).items()) + list(compare(facts).items()):
                out.setdefault(k, v)
            return out

        qa = QA(memory, school.parse, deduce)
        print("[respuesta] " + dialogue.after_answer(raw, qa.answer(raw), qa) + "\n")

    def handle_natural(raw):
        nonlocal dirty, last_sentence
        reply, cont = dialogue.act(raw, QA(memory, school.parse, None) if school is not None else None)
        if reply:
            dialogue.last = reply
            print("[respuesta] " + reply + "\n")
            memory.save()
        if cont is None:
            return
        raw = cont
        if is_question(raw):
            return answer_question(raw)
        parts = split_sentences(raw)
        if len(parts) > 1 and "entonces" not in norm(raw):     # varias frases: una a una, recordando el sujeto
            for part in parts:
                handle_natural(part)
            return
        last_sentence = raw
        low = norm(raw)
        mh = re.match(r"\s*hoy(?:\s+es)?\s*(.*?)\s*[.!]?\s*$", low)
        if mh and not is_question(raw) and (mh.group(1) == "" or re.search(r"\d", mh.group(1))):
            from datetime import date as _d
            from src.language.fechas import extract_abs, fmt, parse_iv
            if mh.group(1):
                iso = re.fullmatch(r"\d{4}-\d{2}-\d{2}", mh.group(1))
                iv = (mh.group(1) + "/" + mh.group(1)) if iso else extract_abs(mh.group(1), _d.today())[1]
                if not iv:
                    print("[!] No entendi la fecha. Ejemplo: Hoy es 6 de noviembre de 2026  |  HOY 2026-11-06\n")
                    return
                memory.today = parse_iv(iv)[0]
                if school is not None:
                    school.today = memory.today
            print(f"[fecha] Hoy es {fmt(_d.isoformat(getattr(memory, 'today', None) or _d.today()) + '/' + _d.isoformat(getattr(memory, 'today', None) or _d.today()))}. "
                  "Lo relativo (ayer, el lunes...) se guarda como fecha absoluta.\n")
            return
        if "entonces" in low and not low.startswith("entonces"):
            a, b = re.split(r"\bentonces\b", low[3:] if low.startswith("si ") else low, maxsplit=1)
            pa, pb = understand(a), understand(b)
            if not pa or not pb:
                print("[oido] No he entendido bien alguna de las dos partes. Reformula la frase.\n")
                return
            if pa["negated"] or pb["negated"]:
                print("[oido] Aun no aprendo reglas con negaciones. Dime la regla en positivo.\n")
                return
            prem, concl = (pa["subject"], pa["predicate"], pa["object"]), (pb["subject"], pb["predicate"], pb["object"])
            print(f"[oido] Regla entendida: {' '.join(prem)}  =>  {' '.join(concl)}")
            if learner is None:
                print("[!] Aprendizaje desactivado.\n")
                return
            register([prem[0], prem[2], concl[0], concl[2]], "entity")
            register([x for x in (prem[1], concl[1]) if x not in space.concept_to_id], "predicate")
            info = learner.learn([([prem], concl)])
            log_dialogue(raw, {"regla": [prem, concl], "aceptada": info["accepted"]})
            if info["accepted"]:
                memory.add_lesson([prem], concl)
                ra, rb = re.split(r"\bentonces\b", re.sub(r"^\s*si\s+", "", raw, flags=re.I), maxsplit=1, flags=re.I)
                for part, trip in ((ra, prem), (rb, concl)):
                    tpl = template_from(part.strip(" ,."), trip[0], trip[2])
                    if tpl:
                        memory.note_surface(trip, *tpl)
                memory.save()
                dirty = True
                save_online(model, config)
                print(f"[+] Aprendido. Acierto en la leccion: {info['before']:.0%} -> {info['after']:.0%} | "
                      f"conocimiento previo (canario): {info['canary']:.0%}\n")
            else:
                print(f"[!] Cambio REVERTIDO (canario {info['canary']:.0%}).\n")
            return
        outs = understand_many(raw)
        if not outs:
            explain_rejection()
            print("[oido] " + dialogue.clarify_statement(raw) + " (Si usa una relacion nueva, creala antes con NUEVO_PRED.)\n")
            return
        if not any(o["negated"] for o in outs):
            dialogue.apply_effects([(o["subject"], o["predicate"], o["object"], o.get("o_disp") or "") for o in outs])      # parche-59: dar/vender/abrir/ir...
        for out in outs:
            triple = (out["subject"], out["predicate"], out["object"])
            register([triple[0], triple[2]], "entity")
            if triple[1] not in space.concept_to_id:
                register([triple[1]], "predicate")
                print(f"[escuela] Relacion nueva para mi: {triple[1]} (la he anadido al catalogo)")
            neg = out["negated"]
            how = "por la escuela de espanol" if out.get("via") else f"confianza {out['confidence']:.0%}"
            print(f"[oido] Entendido: {'NO ' if neg else ''}{' '.join(triple)}   ({how}) "
                  "- si no era eso, corrigeme con ENTENDI s p o [NEGADO]")
            memory.add_fact(triple, source=raw, neg=neg, when=out.get("when", ""), when_disp=out.get("when_disp", ""), quant=out.get("q", ""))
            if out.get("template"):
                memory.note_surface(triple, out["template"], out.get("s_disp"), out.get("o_disp"))
            elif len(outs) == 1 and not neg:                 # frase entendida por el oido de plantillas: plantilla sacada de tus palabras
                tpl = template_from(raw.strip(" ,."), triple[0], triple[2])
                if tpl:
                    memory.note_surface(triple, *tpl)
            note = dialogue.note_new(triple, neg, raw, out.get("when", ""), QA(memory, school.parse, None).say if school is not None else None)
            if note:
                print("[coherencia] " + note)
            memory.save()
            log_dialogue(raw, {"hecho": triple, "negado": neg, "confianza": out["confidence"]})
            if neg:
                print("    (guardado como hecho negado; todavia no se usa para razonar)\n")
                continue
            show_inference([triple])
        dialogue.last_facts = [(o["subject"], o["predicate"], o["object"]) for o in outs if not o["negated"]]
        topic[0] = next_topic([{"s": o["subject"].lower()} for o in outs], topic[0])

    def known(tokens):
        return sorted({t for t in tokens if t not in space.concept_to_id})

    def show_inference(groups):
        nonlocal last_premises
        premise_vectors = [space.encode_proposition(*g) for g in groups]
        result_vector = engine.think_vectors(premise_vectors, steps=1)[0]
        with torch.no_grad():
            s_i, p_i, o_i = model.read_slots(result_vector.view(1, 1, -1).to(device))[0, 0].tolist()
        decoded = "::".join(space.id_to_concept[i] for i in (s_i, p_i, o_i))
        similarity = float(torch.nn.functional.cosine_similarity(
            result_vector.view(1, -1).cpu(), space.encode_proposition(*decoded.split("::")).view(1, -1))[0])
        last_premises = groups
        print("\n[OK] Representacion conceptual generada.")
        print(f"     ├── Candidato: {decoded}")
        print(f"     └── Similitud coseno: {similarity * 100:.2f}% (no es probabilidad calibrada)")
        given = {Fact(*g) for g in groups}
        derived = engine.deduce(given)["facts"] - given
        n_s, n_p, n_o = decoded.split("::")
        if derived:
            print("     Motor simbolico deduce: " + ", ".join(f"{f.subject} {f.predicate} {f.obj}" for f in sorted(derived)))
            agree = Fact(n_s, n_p, n_o) in derived
        else:
            print("     Motor simbolico: sin conclusion con estas premisas")
            agree = n_p == "SIN_CONCLUSION"
        print(f"     Acuerdo red/simbolico: {'SI' if agree else 'NO (puede ser algo que solo sabe la red, o un fallo)'}")
        print(f"     Verbalizado: \"{n_s} {n_p} {n_o}\"\n")

    while True:
        try:
            raw = input("Premisas > ").strip()
            line = raw.upper()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if line in {"SALIR", "EXIT", "QUIT"}:
            break
        if not line:
            continue
        if line == "AYUDA":
            print(HELP)
            continue
        if line == "GUARDAR":
            memory.save()
            if dirty:
                save_online(model, config)
            print("[+] Guardado.\n")
            continue
        if line == "DORMIR":
            if learner is None:
                print("[!] Aun no hay modelo online cargado.\n")
                continue
            from src.memory.sleep import SleepCycle
            rep = SleepCycle(learner, memory).run()
            g = lambda t: (sum(r["probe"] for r in t["groups"]) / len(t["groups"])) if t["groups"] else float("nan")
            print(f"[zzz] esquemas: {len(rep['after']['groups'])} | generaliza {g(rep['before']):.0%} -> {g(rep['after']):.0%} | "
                  f"canario {rep['after']['canary']:.0%} | archivadas {rep['compressed']} | hechos olvidados {rep['decayed_facts']} | "
                  f"revertido {rep['consolidate']['rolled_back']} | pasos {rep['consolidate'].get('steps', 0)} "
                  f"(consolidacion {rep['consolidate'].get('consolidation', 1):.0%})")
            memory.save()
            save_online(model, config)
            dirty = False
            print()
            continue
        if line.startswith("ARBOL ") and school is not None:
            for i, (form, upos, head, rel, lemma) in enumerate(school.tree(raw[6:]), 1):
                print(f"   {i:2d} {form:15s} {upos:6s} -> {head:2d} {rel:7s} lema: {lemma}")
            print("   (cada palabra: categoria, numero de la palabra de la que depende (0 = raiz), funcion y forma base)\n")
            continue
        if line == "MEMORIA":
            print(f"[*] {memory.summary()}")
            for l in memory.lessons[-5:]:
                print("    leccion:", " | ".join(" ".join(p) for p in l["premises"]), "=>", " ".join(l["conclusion"]))
            for f in memory.facts[-5:]:
                print("    hecho:", f["s"], f["p"], f["o"])
            print()
            continue
        words = line.split()
        if words[0] == "ENTENDI":
            if school is not None and last_sentence is not None and len(words) in (4, 5):
                _p = words[1:-1] if words[-1] == "NEGADO" else words[1:]
                if len(_p) == 3:
                    school_correct(last_sentence, tuple(_p))
                    if _p[1] not in space.concept_to_id:      # la relacion aun no existe: el oido de plantillas no tiene nada que corregir
                        print()
                        continue
            if ear_learner is None or last_sentence is None:
                print("[!] No hay una frase reciente que corregir.\n")
                continue
            negated = words[-1] == "NEGADO"
            parts = words[1:-1] if negated else words[1:]
            if len(parts) != 3 or any(t not in space.concept_to_id for t in (parts[1],)):
                print("[!] Formato: ENTENDI sujeto RELACION objeto [NEGADO]  (la relacion debe existir)\n")
                continue
            toks = set(norm(last_sentence).split())
            aliases = [t for n, t in ear.candidates(space) if n == parts[1]]
            phrase = next((t for t in aliases if all(w in toks or w[:4] in {x[:4] for x in toks} for w in t.split())), aliases[0])
            example = ear_learner.build_example(last_sentence, tuple(parts), negated, phrase)
            if example is None:
                print("[!] No encuentro el sujeto y el objeto escritos tal cual en tu frase.\n")
                continue
            info = ear_learner.learn(example)
            if info["accepted"]:
                print(f"[+] Oido ajustado. Ahora entiende esa frase: {'si' if info['learned'] else 'todavia no (repite la correccion)'}"
                      f" | repaso {info['repaso_antes']:.0%} -> {info['repaso_despues']:.0%}\n")
            else:
                print(f"[!] Cambio del oido REVERTIDO: empeoraba lo que ya sabia ({info['repaso_antes']:.0%} -> {info['repaso_despues']:.0%}).\n")
            continue
        if (ear is not None and (words[0] not in COMMANDS or not raw.isupper()) and any(c.islower() for c in raw) and "_" not in raw
                and (len(words) >= 2 or dialogue.talks(raw))):
            handle_natural(raw)
            continue
        if words[0] in ("NUEVO", "NUEVO_PRED") and len(words) > 1:
            created = []
            for name in words[1:]:
                if name not in space.concept_to_id:
                    feats = ({"predicate": 1, "relation": 1, f"identity:{name}": 0.5} if words[0] == "NUEVO_PRED"
                             else {"individual": 1, f"identity:{name}": 0.5})
                    kind = "predicate" if words[0] == "NUEVO_PRED" else "entity"
                    space.add_concept(name, features=feats, kind=kind)
                    memory.add_concept(name, feats, kind)
                    created.append(name)
            model.set_space(space)
            model.to(device)
            if words[0] == "NUEVO_PRED" and created:
                vaccinate(created)
            memory.save()
            print(f"[+] Conceptos anadidos: {created or 'ninguno (ya existian)'}\n")
            continue
        if words[0] == "HECHO" and len(words) == 4:
            if known(words[1:]):
                print(f"[!] Conceptos desconocidos: {known(words[1:])}. Usa NUEVO.\n")
                continue
            new = memory.add_fact(tuple(words[1:]))
            memory.save()
            print(f"[+] Hecho {'guardado' if new else 'ya conocido (refuerzo)'}.\n")
            continue
        if words[0] == "OLVIDA" and len(words) == 4 and raw.isupper():
            print(f"[+] {'Olvidado' if memory.forget_fact(tuple(words[1:])) else 'No estaba en la memoria'}.\n")
            memory.save()
            continue
        if words[0] == "PREGUNTA" and len(words) == 4:
            route = memory.find_path(words[1], words[3], max_len=config.max_concept_seq)
            if not route:
                print("[!] No hay en la memoria una cadena de hechos entre esos dos conceptos.\n")
                continue
            print("[*] Premisas recuperadas de la memoria: " + " | ".join(" ".join(r) for r in route))
            show_inference(route)
            continue
        if words[0] == "APRENDE" or words[0] == "CORRIGE":
            if learner is None:
                print("[!] Aprendizaje desactivado.\n")
                continue
            if words[0] == "CORRIGE":
                if last_premises is None or len(words) != 4:
                    print("[!] Formato: CORRIGE s p o (despues de una inferencia)\n")
                    continue
                premises, concl = last_premises, [tuple(words[1:])]
            else:
                body = line[len("APRENDE"):].split("=>")
                premises = parse_triples(body[0]) if len(body) == 2 else None
                concl = parse_triples(body[1]) if len(body) == 2 else None
                if not premises or not concl or len(concl) != 1:
                    print("[!] Formato: APRENDE s p o | s p o => s p o\n")
                    continue
            tokens = [t for g in premises + concl for t in g]
            if known(tokens):
                print(f"[!] Conceptos desconocidos: {known(tokens)}. Usa NUEVO / NUEVO_PRED.\n")
                continue
            info = learner.learn([(premises, concl[0])])
            if info["accepted"]:
                memory.add_lesson(premises, concl[0])
                memory.save()
                dirty = True
                save_online(model, config)
                print(f"[+] Aprendido. Acierto en la leccion: {info['before']:.0%} -> {info['after']:.0%} | "
                      f"conocimiento previo (canario): {info['canary']:.0%}\n")
            else:
                print(f"[!] Cambio REVERTIDO: rompia el conocimiento previo (canario {info['canary']:.0%}). "
                      "Ensena mas ejemplos o revisa la regla.\n")
            continue

        groups = parse_triples(line)
        if not groups:
            print("[!] Formato: SUJETO PREDICADO OBJETO | ...   (escribe AYUDA)\n")
            continue
        if len(groups) > config.max_concept_seq:
            print(f"[!] Maximo {config.max_concept_seq} proposiciones por inferencia.\n")
            continue
        unknown = known([t for g in groups for t in g])
        if unknown:
            print(f"[!] Nodos no registrados en la ontologia: {unknown}. Usa NUEVO / NUEVO_PRED.\n")
            continue
        try:
            show_inference(groups)
        except (KeyError, ValueError, RuntimeError) as exc:
            print(f"[!] No se pudo construir la inferencia: {exc}")

    memory.save()
    if dirty:
        save_online(model, config)
        print("[+] Memoria y pesos guardados.")


if __name__ == "__main__":
    main()
''',
    'scripts/train_ear.py': r'''"""Entrena el oido con oraciones generadas (espanol -> proposicion, con negacion y 'es un')."""
import os
import random
import time
import torch
from src.language.corpus import (CLAUSES_TRAIN, HEADS_TRAIN, NAMES_TRAIN, VERBS_TRAIN, PredicatePool, base_pool, es_pool, make,
                                 make_negatives)
from src.language.ear import Ear
from src.language.training import batch_loss
from src.language.lm import LMHead, is_heldout, lm_loss, load_sentences

N = int(os.environ.get("EAR_N", 60000))
EPOCHS = int(os.environ.get("EAR_EPOCHS", 8))
BATCH = 128


def main():
    torch.manual_seed(int(os.environ.get("LCM_SEED", "0")))
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    pool = base_pool() + es_pool() + PredicatePool(HEADS_TRAIN, VERBS_TRAIN).items
    data = make(N, pool, seed=1) + make_negatives(N // 2, seed=2)
    print(f"Vocabulario: {len(NAMES_TRAIN)} nombres, {len(CLAUSES_TRAIN)} clausulas de libro (si es 0: ejecuta scripts.read_book antes).")
    ear = Ear().to(device)
    # Preentrenamiento con texto corriente (parche-26): si existe, se parte de el y se sigue leyendo el libro mientras se afina.
    lm_head, book, lr = None, [], 2e-3
    if os.environ.get("EAR_PRE", "1") != "0" and os.path.exists("checkpoints/ear_pre.pt") and os.path.exists("checkpoints/ear_lm.pt"):
        ear.load_state_dict(torch.load("checkpoints/ear_pre.pt", map_location="cpu"))
        ear.to(device)
        lm_head = LMHead.load("checkpoints/ear_lm.pt", ear.d, device)
        book = [t for t in load_sentences("data/libro.txt") if not is_heldout(t)]
        lr = 1e-3
        print(f"[+] Parto del oido preentrenado ({len(book)} frases del libro se siguen leyendo mientras se afina).")
    else:
        print("[i] Sin preentrenamiento (ejecuta  python -m scripts.pretrain_ear  para leer el libro antes).")
    params = list(ear.parameters()) + (list(lm_head.parameters()) if lm_head is not None else [])
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=0.01)
    steps = EPOCHS * (len(data) // BATCH)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps, pct_start=0.1)
    rng = random.Random(int(os.environ.get("LCM_SEED", "0")))
    texts = sorted({p[1] for p in pool})
    t0 = time.time()
    step = 0
    for epoch in range(EPOCHS):
        rng.shuffle(data)
        ear.train()
        for b in range(len(data) // BATCH):
            loss, parts = batch_loss(ear, data[b * BATCH:(b + 1) * BATCH], texts, rng, device)
            if lm_head is not None:
                l_lm, _, _ = lm_loss(ear, lm_head, rng.sample(book, 48), rng, device)
                loss = loss + 0.3 * l_lm
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step(); sched.step(); step += 1
            if step % 200 == 0:
                print(f"  epoca {epoch+1} paso {step}/{steps} tags {parts[0]:.3f} relacion {parts[1]:.3f} negacion {parts[2]:.3f} ambito {parts[3]:.3f} ({time.time()-t0:.0f}s)", flush=True)
    os.makedirs("checkpoints", exist_ok=True)
    torch.save(ear.state_dict(), "checkpoints/ear.pt")
    print("[+] Oido guardado en checkpoints/ear.pt")


if __name__ == "__main__":
    main()
''',
    'scripts/train_reasoner.py': r'''import os
import pickle
import torch
from torch.utils.data import DataLoader
from configs.config import LCMConfig, TrainConfig
from src.model.reasoner import LatentReasoner
from src.training.trainer import ConceptTrainer


def main():
    torch.manual_seed(int(os.environ.get("LCM_SEED", "0")))  # reproducibilidad
    required = ["data/concept_space.pkl", "data/concept_train_dataset.pkl"]
    missing = [path for path in required if not os.path.exists(path)]
    if missing:
        raise FileNotFoundError(
            "Faltan datos. Ejecuta primero `python -m scripts.prepare_concepts`. "
            + ", ".join(missing)
        )
    with open("data/concept_space.pkl", "rb") as handle:
        space = pickle.load(handle)
    with open("data/concept_train_dataset.pkl", "rb") as handle:
        train_dataset = pickle.load(handle)

    val_dataset = None
    if os.path.exists("data/concept_val_dataset.pkl"):
        with open("data/concept_val_dataset.pkl", "rb") as handle:
            val_dataset = pickle.load(handle)

    lcm_config = LCMConfig(
        d_concept=space.d_concept,
        max_concept_seq=4,
    )
    train_config = TrainConfig(
        batch_size=64,
        learning_rate=1e-3,
        epochs=80,
        patience=8,
    )
    train_loader = DataLoader(
        train_dataset, batch_size=train_config.batch_size, shuffle=True,
        pin_memory=(train_config.device == "cuda"),
    )
    val_loader = DataLoader(
        val_dataset, batch_size=128, shuffle=False,
        pin_memory=(train_config.device == "cuda"),
    ) if val_dataset is not None else None

    model = LatentReasoner(lcm_config)
    model.set_space(space)  # lector de ranuras: catalogo y matrices de rol
    trainer = ConceptTrainer(model, train_config, train_loader, val_loader)
    history = trainer.train()
    print(f"[+] Entrenamiento terminado. Epocas ejecutadas: {len(history)}")
    print("[+] Ejecuta `python -m scripts.evaluate_reasoner` para medir generalizacion.")


if __name__ == "__main__":
    main()

''',
    'scripts/train_school.py': r'''"""Escuela de espanol v2: entrena el oido con frases reales anotadas (UD) + frases cortas sinteticas, y mide (parche-30/34).

Necesita  data/ud/UD_Spanish-GSD/*.conllu  y  data/ud/UD_Spanish-AnCora/*.conllu.
Antes de reentrenar, mide la escuela anterior con  python -m scripts.eval_frases  (es la linea base).

REGLA DE DECISION (fijada ANTES de medir):
  1) en las frases UD de prueba: categoria >= 94 %, UAS >= 85 %  (no peor que v1 por mas de 1 punto: 94.8 / 86.0),
  2) lema (forma base) >= 90 % en esas frases,
  3) test de conversacion (scripts.eval_frases, relajado) >= 75 % y +10 puntos sobre v1.
"""
import os
import random
import time

import torch

from src.language.ear import Ear
from src.language import ud_synth
from src.language.extract import triples
from src.language.ud import (School, apply_script, build_scripts, find_files, predict_trees, read_conllu, save_school,
                             school_loss)

EPOCHS = int(os.environ.get("SCHOOL_EPOCHS", 10))
SYNTH = int(os.environ.get("SCHOOL_SYNTH", 6000))
BATCH = 64


def load(split):
    sents, skipped, n = [], 0, 0
    for f in find_files(split):
        s, k = read_conllu(f)
        sents += s; skipped += k; n += 1
    return sents, skipped, n


def evaluate(model, sents, device, scripts):
    # Se mide en la CPU con una copia del modelo: en la GPU del Mac (MPS) la medicion se quedaba parada minutos.
    # Cambiar con SCHOOL_EVAL_DEVICE=mps si se quiere medir en la GPU.
    import copy
    dev_eval = os.environ.get("SCHOOL_EVAL_DEVICE", "cpu")
    t_a = time.time()
    m_eval = copy.deepcopy(model).to(dev_eval) if dev_eval != str(device) else model
    trees = predict_trees(m_eval, [[w[0] for w in s] for s in sents], dev_eval, scripts)
    print(f"    (predecir {len(sents)} frases en {dev_eval}: {time.time()-t_a:.1f}s)", flush=True)
    t_b = time.time()
    tot = up = ua = la = lem = 0
    same = with_gold = 0
    for s, t in zip(sents, trees):
        for w, (u, h, r, lm) in zip(s, t):
            tot += 1
            up += u == w[1]
            ua += h == w[2]
            la += (h == w[2]) and (r == w[3])
            from src.language.ud import _clean
            lem += lm == _clean(w[4])
        gold = triples([(w[0], w[1], w[2], w[3], w[4]) for w in s])
        if gold:
            with_gold += 1
            pred = triples([(w[0], u, h, r, lm) for w, (u, h, r, lm) in zip(s, t)])
            same += set(pred) == set(gold)
    print(f"    (comparar con el arbol humano: {time.time()-t_b:.1f}s)", flush=True)
    model.train()
    return up / tot, ua / tot, la / tot, lem / tot, same / max(with_gold, 1), with_gold


def main():
    torch.manual_seed(int(os.environ.get("LCM_SEED", "0")))
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    train, sk, nf = load("train")
    if not train:
        raise SystemExit("No encuentro data/ud/UD_Spanish-*/*-ud-train.conllu. Clona los repositorios dentro de la carpeta del proyecto.")
    dev, _, _ = load("dev")
    test, sk_t, _ = load("test")
    scripts = build_scripts(train)
    synth = ud_synth.make(ud_synth.mine(train), SYNTH, seed=5) if SYNTH else []
    print(f"Entreno: {len(train)} frases reales ({sk} omitidas por > 40 palabras) de {nf} corpus + {len(synth)} frases cortas sinteticas | "
          f"prueba: {len(test)} frases | {len(scripts)} guiones de lema", flush=True)
    print(f"Dispositivo: {device}", flush=True)
    ear = Ear()
    if os.environ.get("SCHOOL_PRE", "1") != "0" and os.path.exists("checkpoints/ear_pre.pt"):
        ear.load_state_dict(torch.load("checkpoints/ear_pre.pt", map_location="cpu"))
        print("[+] Parto del oido que ya leyo el libro (ear_pre.pt).", flush=True)
    model = School(ear, n_scripts=len(scripts)).to(device)
    data = train + synth
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=0.01)
    steps = EPOCHS * (len(data) // BATCH)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=2e-3, total_steps=steps, pct_start=0.1)
    rng = random.Random(0)
    nb = len(data) // BATCH
    firma = {"epochs": EPOCHS, "synth": SYNTH, "datos": len(data), "batch": BATCH}
    parcial = "checkpoints/school_partial.pt"
    start = 0
    if os.environ.get("SCHOOL_RESUME", "1") != "0" and os.path.exists(parcial):
        ck = torch.load(parcial, map_location="cpu")
        if ck.get("firma") == firma:
            model.load_state_dict(ck["model"]); opt.load_state_dict(ck["opt"]); sched.load_state_dict(ck["sched"])
            start = ck["epoch"]
            for _ in range(start):
                rng.shuffle(data)  # misma baraja que en una ejecucion sin cortes
            print(f"[+] Retomo desde la epoca {start} de {EPOCHS} (checkpoints/school_partial.pt).", flush=True)
    t0 = time.time()
    print(f"{EPOCHS} epocas x {nb} lotes de {BATCH} frases. Aviso de progreso cada 20 lotes.", flush=True)
    for epoch in range(start, EPOCHS):
        rng.shuffle(data)
        model.train()
        te = time.time()
        for b in range(nb):
            loss, parts = school_loss(model, data[b * BATCH:(b + 1) * BATCH], device, scripts)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step()
            if b == 0 or (b + 1) % 20 == 0 or b == nb - 1:
                done = epoch * nb + b + 1 - start * nb
                per = (time.time() - t0) / max(done, 1)
                left = per * (EPOCHS * nb - start * nb - done)
                print(f"  epoca {epoch+1}/{EPOCHS} lote {b+1}/{nb} | perdida {loss.item():.3f} | {per:.2f} s/lote | "
                      f"quedan ~{left/60:.0f} min", flush=True)
        torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "sched": sched.state_dict(),
                    "epoch": epoch + 1, "firma": firma}, parcial)
        print(f"  [guardado punto de control: epoca {epoch+1} ({time.time()-te:.0f}s)]", flush=True)
        if dev and ((epoch + 1) % 2 == 0 or epoch == EPOCHS - 1):
            print(f"  midiendo en {len(dev)} frases de dev...", flush=True)
            te = time.time()
            u, a, l, lm, _, _ = evaluate(model, dev, device, scripts)
            print(f"  epoca {epoch+1:2d} | categoria {u:.1%} dependencia {a:.1%} +funcion {l:.1%} lema {lm:.1%} (dev) (medir: {time.time()-te:.0f}s, total {time.time()-t0:.0f}s)", flush=True)
    save_school(model, scripts)
    if os.path.exists(parcial):
        os.remove(parcial)
    print("Midiendo en las frases de prueba...", flush=True)
    u, a, l, lm, same, n = evaluate(model, test, device, scripts)
    print("\n=== ESCUELA v2: frases UD de PRUEBA (nunca vistas) ===")
    print(f"  categoria gramatical: {u:.1%}   [>= 94 %: {'CUMPLE' if u >= .94 else 'NO CUMPLE'}]")
    print(f"  a que palabra se une: {a:.1%}   [>= 85 %: {'CUMPLE' if a >= .85 else 'NO CUMPLE'}]   (+funcion {l:.1%})")
    print(f"  lema (forma base):    {lm:.1%}   [>= 90 %: {'CUMPLE' if lm >= .90 else 'NO CUMPLE'}]")
    print(f"  proposiciones iguales a las del arbol humano: {same:.1%} de {n} frases (informativo; era 35.5 % en v1)")
    print("[+] Guardado checkpoints/school.pt y checkpoints/school_meta.json. Ahora:  python -m scripts.eval_frases")


if __name__ == "__main__":
    main()
''',
    'src/__init__.py': r'''''',
    'src/language/__init__.py': r'''from .ear import Ear, EarParser

__all__ = ["Ear", "EarParser"]
''',
    'src/language/book.py': r'''"""Lectura de libros para el oido (parche-17): RTF -> texto -> frases limpias."""
import re
import unicodedata

_SKIP_DEST = {"fonttbl", "colortbl", "stylesheet", "info", "pict", "header", "footer", "expandedcolortbl", "listtable",
              "listoverridetable", "generator", "themedata", "colorschememapping", "latentstyles", "datastore"}


def rtf_to_text(data: str, codepage: str = "cp1252") -> str:
    """Convierte RTF a texto plano sin dependencias (escapes \\'hh, \\uN, grupos de destino, \\par)."""
    # En RTF, "\\" + salto de linea es un \par; aqui los libros vienen con las lineas cortadas a mano:
    # una sola es un salto duro (espacio) y una linea en blanco separa parrafos.
    data = re.sub(r"(?:\\\r?\n[ \t]*){2,}", lambda m: "\\par ", data)
    data = re.sub(r"\\\r?\n", lambda m: " ", data)
    m = re.search(r"\\ansicpg(\d+)", data[:2000])
    if m:
        codepage = "cp" + m.group(1)
    out, i, n = [], 0, len(data)
    stack = []           # (saltando, uc)
    skipping, uc = False, 1
    pending_skip = 0
    while i < n:
        c = data[i]
        if c == "{":
            stack.append((skipping, uc))
            i += 1
            # destino: {\* ...} o {\fonttbl ...}
            m = re.match(r"\\\*|\\([a-zA-Z]+)", data[i:i + 40])
            if m and (m.group(0) == "\\*" or m.group(1) in _SKIP_DEST):
                skipping = True
            continue
        if c == "}":
            if stack:
                skipping, uc = stack.pop()
            i += 1
            continue
        if c == "\\":
            i += 1
            if i >= n:
                break
            d = data[i]
            if d in "\\{}":
                if not skipping and not pending_skip:
                    out.append(d)
                pending_skip = max(0, pending_skip - 1) if pending_skip else 0
                i += 1
            elif d == "'":
                hexa = data[i + 1:i + 3]
                i += 3
                if pending_skip:
                    pending_skip -= 1
                elif not skipping:
                    try:
                        out.append(bytes([int(hexa, 16)]).decode(codepage, errors="replace"))
                    except ValueError:
                        pass
            elif d == "~":
                out.append(" "); i += 1
            elif d in "-_":
                i += 1
            elif d.isalpha():
                m = re.match(r"([a-zA-Z]+)(-?\d+)? ?", data[i:])
                word, num = m.group(1), m.group(2)
                i += m.end()
                if skipping:
                    continue
                if word in ("par", "line", "sect", "page"):
                    out.append("\n")
                elif word == "tab":
                    out.append(" ")
                elif word == "uc" and num is not None:
                    uc = int(num)
                elif word == "u" and num is not None:
                    v = int(num)
                    out.append(chr(v + 65536 if v < 0 else v))
                    pending_skip = uc
                elif word in ("emdash",):
                    out.append("—")
                elif word in ("endash",):
                    out.append("–")
                elif word in ("lquote", "rquote"):
                    out.append("'")
                elif word in ("ldblquote", "rdblquote"):
                    out.append('"')
            else:
                i += 1
            continue
        if c in "\r\n":              # salto de linea "duro" del archivo: separa palabras (no es parrafo)
            if not skipping and out and out[-1] not in (" ", "\n"):
                out.append(" ")
            i += 1
            continue
        if not skipping:
            if pending_skip:
                pending_skip -= 1
            else:
                out.append(c)
        i += 1
    return "".join(out)


def clean(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u00a0", " ").replace("«", '"').replace("»", '"').replace("“", '"').replace("”", '"')
    text = re.sub(r"[ \t]+", " ", text)
    return text


def sentences(text: str, max_words: int = 30):
    """Frases sueltas. Las muy largas (Claudin escribe periodos enormes) se parten en clausulas por , ; :"""
    out = []
    for para in re.split(r"\n+", clean(text)):
        para = para.strip()
        if not para:
            continue
        para = re.sub(r"\s*[—–]\s*", " , ", para)           # guion de dialogo -> coma (aprox.)
        for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡\"—])", para):
            s = s.strip(" ,\"")
            n = len(s.split())
            if 4 <= n <= max_words:
                out.append(s)
            elif n > max_words:
                for clause in re.split(r"\s*[,;:]\s*", s):
                    clause = clause.strip(" \"")
                    if 4 <= len(clause.split()) <= max_words:
                        out.append(clause)
    return out
''',
    'src/language/book_vocab.py': r'''"""Vocabulario REAL sacado de un libro: nombres, sustantivos, adjetivos, adverbios y clausulas de relleno (parche-18)."""
import json
import re
import zlib
from collections import Counter

from .lexicon import norm, tokenize

ARTS = {"el", "la", "los", "las", "un", "una", "unos", "unas"}
RELATION_WORDS = set("hijo hija padre madre marido mujer hermano hermana amigo amiga primo prima tio tia sobrino sobrina "
                     "abuelo abuela criado criada dueno duena".split())
NOT_NOUN = set("mismo misma otro otra todo toda cual cuales poco mucho tanto tanta mas menos algo nada esto eso aquel aquella "
               "estos esos ese esa este esta cada solo sola ambos tales tal".split())
ADJ_END = ("o", "a", "e", "al", "ar", "oso", "osa", "ico", "ica", "ble", "nte", "or", "ivo", "iva", "ido", "ida")


def _split(word):
    return zlib.crc32(word.encode()) % 5 == 0          # ~20 % reservado para medir (nunca entra en entrenamiento)


def extract_vocab(text, clauses, max_names=500, max_nouns=1500, max_adjs=600, max_advs=150, max_clauses=20000):
    words = [(m.group(0), m.start()) for m in re.finditer(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", text)]
    lower = Counter(norm(w) for w, _ in words if w[0].islower())
    caps = Counter()
    for w, pos in words:
        if len(w) >= 3 and w[0].isupper() and w[1:].islower():
            before = text[max(0, pos - 3):pos].rstrip(" \t")
            if before and before[-1] not in ".!?¿¡\"—–\n:":
                caps[norm(w)] += 1
    names = [w for w, n in caps.most_common() if n >= 3 and lower[w] <= n * 0.05 and w.isalpha()][:max_names]
    toks = [norm(w) for w, _ in words]
    freq = Counter(toks)
    top_words = {w for w, _ in freq.most_common(150)}           # palabras muy frecuentes: funcion o verbos, no vocabulario
    after_art = Counter(b for a, b in zip(toks, toks[1:]) if a in ARTS and len(b) >= 4 and b not in NOT_NOUN and b not in top_words)
    nameset = set(names)
    nouns = [w for w, n in after_art.most_common() if n >= 5 and w not in nameset and not w.endswith("mente")
             and not w.endswith(("ando", "iendo", "ar", "er", "ir"))][:max_nouns]
    nounset = set(nouns)
    after_noun = Counter(b for a, b in zip(toks, toks[1:]) if a in nounset and len(b) >= 5 and b not in NOT_NOUN
                         and b not in nameset and b.endswith(ADJ_END) and b not in ARTS and b not in top_words
                         and not b.endswith(("aba", "ia", "ian", "aban", "ando", "iendo", "ron", "mente")))
    adjs = [w for w, n in after_noun.most_common() if n >= 3][:max_adjs]
    cnt = Counter(toks)
    advs = [w for w, n in cnt.most_common() if w.endswith("mente") and len(w) >= 7 and n >= 5][:max_advs]
    keep = []
    for c in clauses:
        t = tokenize(c)
        if 4 <= len(t) <= 28 and "?" not in t:          # tambien las que mencionan padre, marido...: son negativos utiles
            keep.append(" ".join(t))
    return {
        "names": names, "advs": advs, "clauses": keep[:max_clauses],
        "nouns": [["la" if n.endswith(("a", "ion", "dad", "tud")) else "el", n] for n in nouns],
        "adjs": adjs,
    }


def save_vocab(vocab, path="data/libro_vocab.json"):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(vocab, handle, ensure_ascii=False)


def load_vocab(path="data/libro_vocab.json"):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def split_vocab(vocab):
    """Devuelve (entrenamiento, prueba) con una particion fija por palabra."""
    def part(items, keyfn):
        tr = [x for x in items if not _split(keyfn(x))]
        te = [x for x in items if _split(keyfn(x))]
        return tr, te
    out = {}
    for k, key in (("names", lambda x: x), ("advs", lambda x: x), ("adjs", lambda x: x),
                   ("clauses", lambda x: x), ("nouns", lambda x: x[1])):
        out[k] = part(vocab.get(k, []), key)
    return {k: v[0] for k, v in out.items()}, {k: v[1] for k, v in out.items()}
''',
    'src/language/corpus.py': r'''"""Generador de oraciones en espanol con su significado conocido (parche-16).

Cada oracion combina: un marco de frase (activa, inversa, pasiva, "es un"), una
polaridad (afirmativa/negada), adornos, incisos, adverbios, entidades de varios
tipos (nombres, nombres inventados, sustantivos con articulo y adjetivos, plurales).
Hay marcos, vocabulario y entidades RESERVADOS solo para medir generalizacion.
"""
import random
from .lexicon import PREPS, BASE_PHRASES

NAMES_TRAIN = ("ana luis carlos elena marta juan pedro sara pablo lucia diego rosa andres irene hugo nuria mateo alba sergio laura raul clara oscar julia ivan marina "
               "adrian beatriz cristina daniel david eva fernando gabriel guillermo javier jesus joaquin jose lorena manuel maria mario monica "
               "nicolas olga patricia paula rafael rebeca ricardo roberto rocio salvador santiago sonia susana teresa victor vicente yolanda "
               "alberto alicia amparo angel antonio aurora blanca camila carla celia dolores emilio enrique esther eugenio fatima francisco "
               "gonzalo ignacio ines jaime lidia lola lourdes manolo margarita martin natalia noa pilar quique reyes ruben sandra sofia tania "
               "uxia valeria vera violeta xavier yago zoe").split()
NAMES_TEST = "bruno carmen felix gloria hector isabel jorge leonor miguel noelia ramon silvia tomas veronica abel agustin celina elias fabian gema hilario jimena kevin leticia mauro nerea olivia ursula".split()
NOUNS_TRAIN = [("el", w) for w in "agua hielo fuego metal perro libro rio gato arbol coche camino puente cielo mar sol bosque campo pan vino lago monte barco reloj martillo jardin pueblo muro papel".split()] + \
              [("la", w) for w in "piedra lluvia luna casa nube flor mesa silla puerta ventana montana playa isla carta calle torre cuerda moneda botella lampara escuela".split()]
NOUNS_TEST = [("el", w) for w in "viento tren cristal hongo teatro volcan".split()] + [("la", w) for w in "arena ciudad cueva fabrica espada ola".split()]
CATS_TRAIN = "animal planta mineral objeto persona cosa metal fenomeno".split()
CATS_TEST = "vehiculo herramienta alimento edificio".split()
ADJ_TRAIN = ("grande fuerte comun util facil dificil veloz rojo azul verde blanco negro viejo nuevo joven alto bajo largo corto "
             "pesado ligero duro blando frio caliente dulce amargo limpio sucio rico pobre feliz triste bueno malo hermoso feo "
             "antiguo moderno publico privado").split()
ADJ_TEST = "interesante brillante capaz extrano valiente profundo sencillo misterioso oscuro".split()
HEADS_TRAIN = "padre madre hijo hermano jefe amigo vecino dueno autor creador maestro alumno lider socio rival mayor menor anterior posterior superior inferior parecido cercano lejano igual distinto mejor peor primo sobrino".split()
HEADS_TEST = "abuelo nieto tio suegro heredero sucesor aliado enemigo responsable delegado guardian tutor mentor discipulo".split()
VERBS_TRAIN = {"admira": "admirado", "visita": "visitado", "conoce": "conocido", "ayuda": "ayudado", "sigue": "seguido",
               "guia": "guiado", "protege": "protegido", "vigila": "vigilado", "construye": "construido",
               "ensena": "ensenado", "vende": "vendido", "compra": "comprado", "escribe": "escrito"}
VERBS_TEST = {"ama": "amado", "odia": "odiado", "respeta": "respetado", "teme": "temido", "busca": "buscado",
              "encuentra": "encontrado", "detecta": "detectado", "mueve": "movido", "sostiene": "sostenido",
              "contiene": "contenido"}
BASE_PART = {"CAUSA": "causado", "PRODUCE": "producido", "PROVOCA": "provocado", "ORIGINA": "originado",
             "POSEE": "poseido", "EXHIBE": "exhibido", "ADQUIERE": "adquirido", "HEREDA": "heredado",
             "IMPLICA": "implicado", "CONTRADICE": "contradicho"}
ES_ALIASES = [("es un", "E"), ("es una", "E"), ("son", "E"), ("era un", "E"), ("era una", "E"), ("eran", "E")]

# ---- marcos de entrenamiento -------------------------------------------------
A_ACTIVE = ["{S} {neg} es {p} {O}", "{S} {neg} resulta ser {p} {O}", "{S} {neg} es siempre {p} {O}",
            "se sabe que {S} {neg} es {p} {O}", "{S} , como todos saben , {neg} es {p} {O}",
            "dicen que {S} {neg} es {p} {O}", "{S} {neg} es tambien {p} {O}", "{S} , que vive cerca , {neg} es {p} {O}",
            "ahora {S} {neg} es {p} {O}", "{S} {neg} es el {p} {O}", "{S} {neg} es claramente {p} {O}",
            "creo que {S} {neg} es {p} {O} desde hace tiempo",
            "{S} {neg} era {p} {O}", "{S} {neg} fue {p} {O}", "{S} {neg} era el {p} {O}", "{S} {neg} era siempre {p} {O}",
            "{S} {neg} habia sido {p} {O}", "{S} , que ya no vivia alli , {neg} era {p} {O}"]
A_INV = ["el {head} de {O} {neg} es {S}", "{O} {neg} tiene como {head} a {S}", "dicen que el {head} de {O} {neg} es {S}",
         "{O} , segun parece , {neg} tiene como {head} a {S}", "el {head} de {O} {neg} era {S}",
         "{O} {neg} tenia como {head} a {S}"]
V_ACTIVE = ["{S} {neg} {p} {O}", "{S} siempre {neg} {p} {O}", "se sabe que {S} {neg} {p} {O}",
            "{S} , como todos saben , {neg} {p} {O}", "dicen que {S} {neg} {p} {O}",
            "{S} , que vive cerca , {neg} {p} {O}", "ahora {S} {neg} {p} {O}", "{S} {neg} {p} a {O}",
            "{S} tambien {neg} {p} {O}"]
V_PASSIVE = ["{O} {neg} es {part} por {S}", "{O} {neg} fue {part} por {S}", "dicen que {O} {neg} es {part} por {S}"]
E_ACTIVE = ["{S} {neg} {p} {O}", "se sabe que {S} {neg} {p} {O}", "{S} , como todos saben , {neg} {p} {O}",
            "dicen que {S} {neg} {p} {O}", "{S} , segun parece , {neg} {p} {O}", "ahora {S} {neg} {p} {O}"]
# ---- marcos RESERVADOS (solo evaluacion) -------------------------------------
HELD_A = ["{S} {neg} termina siendo {p} {O}", "{S} {neg} acaba por ser {p} {O}", "para mi , {S} {neg} es {p} {O}"]
HELD_A_INV = ["{O} cuenta con {S} como {head}", "{S} es el {head} que tiene {O}"]
HELD_V = ["{S} , de hecho , {neg} {p} {O}", "{S} {neg} llega a {p} {O}", "es cierto que {S} {neg} {p} {O}"]
HELD_PASSIVE = ["{O} {neg} resulta {part} por {S}", "{O} {neg} queda {part} por {S}"]
HELD_E = ["segun el libro , {S} {neg} {p} {O}", "{S} , {neg} {p} {O}", "es evidente que {S} {neg} {p} {O}"]
PREFIX = ["", "", "", "", "oye ,", "por cierto ,", "creo que", "ayer supe que", "mi amigo dice que", "fijate ,",
          "pues bien ,", "te cuento que", "ya sabes que", "resulta que", "mira ,", "dime una cosa :", "segun mi madre ,", "me han contado que",
          "no me lo creo pero", "entonces ,", "a ver ,", "pues mira ,", "te aseguro que", "estoy seguro de que", "ayer lei que", "es curioso ,",
          "hoy me han dicho que", "total ,", "bueno ,", "ya ves ,"]
SUFFIX = ["", "", ".", ".", "!", ", segun parece .", ", ya lo ves .", ", como siempre .", ", dicen ."]
FILL_TRAIN = "siempre tambien ya claramente realmente casi todavia ademas quiza aqui entonces antes hoy luego".split()
ADJ_SUFFIX = ["oso", "ico", "al", "ente", "able", "ivo"]
NEG_WORDS = ["no", "no", "no", "nunca", "jamas"]
SYL = "ba be bi bo bu ca ce co cu da de di do fa fe fo ga gi go la le li lo lu ma me mi mo na ne ni no pa pe pi po ra re ri ro sa se si so ta te ti to va ve vi vo za zo".split()


CLAUSES_TRAIN, CLAUSES_TEST = [], []
BOOK_NAMES = set()          # nombres propios del libro: salen en miles de clausulas negativas (parche-25)


_COP = {"es", "era", "son", "eran", "fue", "fueron"}
_ART = {"el", "la", "los", "las", "un", "una", "unos", "unas"}


def looks_relational(clause: str) -> bool:
    """"Mesia era el amigo de Quintanar": una afirmacion de relacion REAL. No puede ser un negativo (parche-24)."""
    t = [w for w in clause.split() if w not in ",.;:!?\u00bf\u00a1"]
    if "?" in clause or len(t) < 4 or len(t) > 9:
        return False
    for i in range(1, min(len(t) - 2, 5)):
        if t[i] in _COP and "de" in t[i + 1:]:
            return t[i + 1] in _ART or (i + 2 < len(t) and t[i + 2] == "de")
    return False


def load_book_vocab(path="data/libro_vocab.json"):
    """Si existe el vocabulario REAL de un libro (scripts.read_book), se mezcla con el sintetico.
    Un 20 % de las palabras (por hash) queda reservado para la prueba."""
    from .book_vocab import load_vocab, split_vocab
    v = load_vocab(path)
    if not v:
        return False
    tr, te = split_vocab(v)
    NAMES_TRAIN.extend(w for w in tr["names"] if w not in NAMES_TRAIN and w not in NAMES_TEST)
    NAMES_TEST.extend(w for w in te["names"] if w not in NAMES_TEST and w not in NAMES_TRAIN)
    NOUNS_TRAIN.extend(tuple(x) for x in tr["nouns"])
    NOUNS_TEST.extend(tuple(x) for x in te["nouns"])
    ADJ_TRAIN.extend(w for w in tr["adjs"] if w not in ADJ_TRAIN)
    ADJ_TEST.extend(w for w in te["adjs"] if w not in ADJ_TEST and w not in ADJ_TRAIN)
    FILL_TRAIN.extend(tr["advs"])
    BOOK_NAMES.update(tr["names"]); BOOK_NAMES.update(te["names"])
    CLAUSES_TRAIN.extend(c for c in tr["clauses"] if not looks_relational(c))
    CLAUSES_TEST.extend(c for c in te["clauses"] if not looks_relational(c))
    return True


def pseudo_name(rng):
    return "".join(rng.choice(SYL) for _ in range(rng.choice([2, 3, 3, 4])))


def pseudo_adj(rng):
    return pseudo_name(rng) + rng.choice(ADJ_SUFFIX)


def pseudo_filler(rng):
    return pseudo_name(rng) + rng.choice(["mente", "ando", "ado", "mente"])


def pseudo_periphrasis(rng):
    """Giros tipo 'termina siendo / acaba por ser' con un verbo inventado (vocabulario abierto)."""
    verb = pseudo_name(rng) + rng.choice(["a", "e", "ea", "ece"])
    return [verb] + rng.choice([["siendo"], ["por", "ser"], ["a", "ser"], ["de", "ser"]])


def pick_adj(rng, adjs):
    return rng.choice(adjs) if rng.random() < 0.5 else pseudo_adj(rng)


def plural(w):
    return w + ("es" if w[-1] not in "aeiou" else "s")


def singular(w):
    if w.endswith("es") and len(w) > 3 and w[-3] not in "aeiou":
        return w[:-2]
    return w[:-1] if w.endswith("s") else w


def base_pool():
    items = []
    for name, (text, kind) in BASE_PHRASES.items():
        words = text.split()
        items.append((name, text, kind, " ".join(words[:-1]) if kind == "A" else text,
                      words[-1] if kind == "A" else "", BASE_PART.get(name)))
    return items


def es_pool():
    return [("ES", text, "E", text, "", None) for text, _ in ES_ALIASES]


class PredicatePool:
    def __init__(self, heads, verbs, preps=None):
        preps = preps or sorted(PREPS)
        self.items = []
        for h in heads:
            for p in preps:
                self.items.append((f"{h}_{p}".upper(), f"{h} {p}", "A", h, p, None))
        for v, part in verbs.items():
            self.items.append((v.upper(), v, "V", v, "", part))


def entity(rng, mode, role, pl=False):
    """Devuelve (articulo, palabra_en_texto, adjetivos, nombre_canonico)."""
    names = NAMES_TRAIN if mode == "train" else NAMES_TEST
    nouns = NOUNS_TRAIN if mode == "train" else NOUNS_TEST
    adjs = ADJ_TRAIN if mode == "train" else ADJ_TEST
    r = rng.random()
    if not pl and r < 0.40:
        return None, rng.choice(names), [], None
    if not pl and r < 0.62:
        n = pseudo_name(rng)
        return None, n, [], None
    art, noun = rng.choice(nouns)
    if rng.random() < 0.3:
        noun = pseudo_name(rng)
    mods = [pick_adj(rng, adjs)] if rng.random() < 0.35 else []
    if pl:
        return ("los" if art == "el" else "las"), plural(noun), [(plural(m)) for m in mods], noun
    return (art if rng.random() < 0.7 else ("un" if art == "el" else "una")), noun, mods, noun


def category(rng, mode, pl):
    cats = CATS_TRAIN if mode == "train" else CATS_TEST
    adjs = ADJ_TRAIN if mode == "train" else ADJ_TEST
    c = rng.choice(cats) if rng.random() < 0.7 else pseudo_name(rng)
    mods = [pick_adj(rng, adjs)] if rng.random() < 0.35 else []
    return (None, plural(c), [plural(m) for m in mods], c) if pl else (None, c, mods, c)


def build(rng, item, frames, mode, neg_prob=0.2):
    name, text, kind, head, prep, part = item
    fa, fi, fv, fp, fe = frames
    plural_e = text in ("son", "eran")
    if kind == "A":
        template = rng.choice(fi if (prep == "de" and fi and rng.random() < 0.4) else fa)
    elif kind == "E":
        template = rng.choice(fe)
    elif part and fp and rng.random() < 0.3:
        template = rng.choice(fp)
    else:
        template = rng.choice(fv)
    if kind == "E":
        e1 = entity(rng, mode, "S", pl=plural_e)
        e2 = category(rng, mode, plural_e)
    else:
        e1, e2 = entity(rng, mode, "S"), entity(rng, mode, "O")
        while e2[1] == e1[1]:
            e2 = entity(rng, mode, "O")
    neg = rng.random() < neg_prob
    tokens, tags = [], []

    def add(tok, tag=0):
        tokens.append(tok)
        tags.append(tag)

    def fill(p=0.45):
        if rng.random() < p:
            if rng.random() < 0.3:
                for w in pseudo_periphrasis(rng):
                    add(w)
                return
            for _ in range(rng.choice([1, 1, 2])):
                add(rng.choice(FILL_TRAIN) if rng.random() < 0.6 else pseudo_filler(rng))

    clauses = CLAUSES_TRAIN if mode == "train" else CLAUSES_TEST
    pre = rng.choice(PREFIX)
    post = rng.choice(SUFFIX)
    if clauses and rng.random() < 0.25:                       # prosa real alrededor de la afirmacion
        if rng.random() < 0.5:
            pre = rng.choice(clauses) + " ,"
        else:
            post = ", " + rng.choice(clauses)
    for piece in (pre + " " + template).split():
        if piece in ("{S}", "{O}"):
            art, word, mods, canon = e1 if piece == "{S}" else e2
            if art:
                add(art)
            add(word, 1 if piece == "{S}" else 2)
            for m in mods:
                add(m)
            if piece == "{S}" and mode == "train":
                fill(0.15)
        elif piece == "{p}":
            if mode == "train":
                fill()
            for w in text.split():
                add(w)
        elif piece == "{head}":
            if mode == "train":
                fill(0.2)
            for w in head.split():
                add(w)
        elif piece == "{part}":
            if mode == "train":
                fill(0.3)
            add(part)
        elif piece == "{neg}":
            if neg:
                add(rng.choice(NEG_WORDS))
        else:
            add(piece)
    for w in post.split():
        add(w)
    s_name = (e1[3] or e1[1]).upper()
    o_name = (e2[3] or e2[1]).upper()
    return {"tokens": tokens, "tags": tags, "pred": name, "text": text, "neg": neg, "triple": (s_name, name, o_name)}


def make_negatives(n, seed, mode="train"):
    """Frases que NO afirman una relacion: prosa suelta, fragmentos, preguntas, sin relacion, sin sujeto."""
    rng = random.Random(seed)
    clauses = CLAUSES_TRAIN if mode == "train" else CLAUSES_TEST
    names = NAMES_TRAIN if mode == "train" else NAMES_TEST
    out = []
    for _ in range(n):
        r = rng.random()
        e1, e2 = entity(rng, mode, "S"), entity(rng, mode, "O")

        def ent(e):
            return ([e[0]] if e[0] else []) + [e[1]] + list(e[2])
        head = rng.choice(HEADS_TRAIN if mode == "train" else HEADS_TEST)
        if r < 0.50 and clauses:
            toks = rng.choice(clauses).split()
            if BOOK_NAMES and rng.random() < 0.85:      # que un nombre del libro no sea una pista de "basura"
                swap = {}
                toks = [swap.setdefault(w, rng.choice(names) if rng.random() < 0.6 else pseudo_name(rng))
                        if w in BOOK_NAMES else w for w in toks]
        elif r < 0.60:
            toks = ["el", head, rng.choice(["de", "a", "con"])] + ent(e2)                   # fragmento nominal
        elif r < 0.70:
            toks = ent(e1) + [rng.choice(["y", "habla con", "mira a", "pasea con", "vive cerca de"])] + ent(e2)
        elif r < 0.80:
            toks = ["quien", "es", "el", head, "de"] + ent(e2) + ["?"]                      # pregunta
        elif r < 0.88:
            toks = ["es", "el", head, "de"] + ent(e2)                                     # sin sujeto
        elif r < 0.95:
            toks = ["es"] + ent(e1) + ["el", head, "de"] + ent(e2) + ["?"]
        else:
            toks = [pseudo_name(rng) for _ in range(rng.choice([3, 4, 5]))]
        toks = [t for w in toks for t in w.split()]
        out.append({"tokens": toks, "tags": [0] * len(toks), "pred": None, "text": None, "neg": False,
                    "triple": None, "reject": True})
    return out


def make(n, pool_items, seed, mode="train", held_frames=False, neg_prob=0.2):
    rng = random.Random(seed)
    frames = ((HELD_A, HELD_A_INV, HELD_V, HELD_PASSIVE, HELD_E) if held_frames
              else (A_ACTIVE, A_INV, V_ACTIVE, V_PASSIVE, E_ACTIVE))
    return [build(rng, rng.choice(pool_items), frames, mode, neg_prob) for _ in range(n)]


load_book_vocab()
''',
    'src/language/dialogue.py': r'''"""Conversacion basica SIN LLM (parche-54, bloque A de docs/NUCLEO_BASICO.md).

Reglas explicitas y comprobables, no un modelo generativo:
  A2 actos sociales (hola, gracias, perdona, adios, ...)        A5 preguntas sobre si mismo y sobre lo que sabe/se ha dicho
  A3 pedir aclaracion cuando no entiende                        A6 ordenes (repite, olvida ...)
  A4 preguntar lo que le falta (¿que es X?) y aprenderlo        A7 si/no/vale/exclamaciones, tu/usted
  A8 referencias: mi/mis, yo, este/ese, tambien/tampoco/otra vez, "eso es falso", "¿y Ana?"

`Dialogue.act(raw, qa)` devuelve (respuesta | None, texto_para_seguir | None):
  - (texto, None): ya esta contestado; - (None, raw2): continua el flujo normal con raw2 (referencias resueltas);
  - (texto, raw2): contesta y ADEMAS sigue con raw2.
`Conversation` es el bucle completo (sin oido) que usan los tests; scripts/think.py usa solo `Dialogue`.
"""
import re
import time
from datetime import date, datetime
from typing import List, Optional, Tuple

from src.language.lexicon import norm
from src.reasoning.lessons import canon
from src.reasoning import coherence

DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DET = {"el", "la", "los", "las", "un", "una", "unos", "unas"}
CAP = r"[A-ZÁÉÍÓÚÑ][\wáéíóúñ]*"
GREET = {"hola": "¡Hola", "ola": "¡Hola", "hey": "¡Hola", "saludos": "¡Saludos", "buenas": "¡Buenas", "buenos dias": "¡Buenos días",
         "buenas tardes": "¡Buenas tardes", "buenas noches": "¡Buenas noches"}
BYE = r"(adios|hasta luego|hasta pronto|hasta manana|hasta otra|chao|chau|nos vemos|me voy|hasta la vista)"
THANKS = r"((muchas|mil|muchisimas) )?gracias( por (todo|tu ayuda|su ayuda|eso|la ayuda))?|te lo agradezco|muy amable|se lo agradezco"
SORRY = r"(perdona|perdon|disculpa|disculpame|perdoname|lo siento|disculpe)( por (eso|todo|la molestia))?"
YES = r"(si|sip|claro|por supuesto|seguro|correcto|exacto|afirmativo|desde luego|adelante|si seguro|si claro)"
NO = r"(no|nop|nunca|negativo|mejor no|no gracias)"
ACK = r"(vale|ok|okay|de acuerdo|entendido|muy bien|bien|perfecto|genial|estupendo|bueno|fenomenal|comprendo|ya veo|ah|aja)"
GOOD = {"que bien": "¡Me alegro!", "que alegria": "¡Me alegro!", "que bueno": "¡Me alegro!", "genial": "¡Me alegro!",
        "que pena": "Lo siento.", "que lastima": "Lo siento.", "vaya": "Lo siento.", "ay": "Lo siento.", "que mal": "Lo siento.",
        "guau": "¿Verdad?", "uau": "¿Verdad?", "madre mia": "¿Verdad?", "increible": "¿Verdad?", "jo": "Vaya.", "ostras": "Vaya."}
GEN = {"este": "el", "ese": "el", "aquel": "el", "esta": "la", "esa": "la", "aquella": "la", "estos": "los", "esos": "los", "aquellos": "los",
       "estas": "las", "esas": "las", "aquellas": "las"}


TIEMPO_NOMBRES = {"lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                  "agosto", "septiembre", "octubre", "noviembre", "diciembre", "primavera", "verano", "otono", "invierno"}


def n(raw: str) -> str:
    """Texto comparable: sin tildes, sin signos, sin 'por favor'."""
    t = norm(raw)
    t = re.sub(r"[¡!¿?.,;:\"«»()]", " ", t)
    t = re.sub(r"\b(por favor|porfa)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _same_fact(f: dict, triple, neg: bool) -> bool:
    return (f["s"], f["p"], f["o"]) == tuple(x.upper() for x in triple) and bool(f.get("neg")) == bool(neg)


def is_question(raw: str) -> bool:
    return "?" in raw or "¿" in raw


FEM_E = {"madre", "mujer", "tarde", "noche", "clase", "calle", "suegra", "nuera"}
FEM_O = {"mano", "foto", "moto", "radio"}


def _article(noun: str) -> str:
    w = noun.lower()
    if w in FEM_E or w in FEM_O:
        return "la"
    if w.endswith("os") or w.endswith("es"):
        return "los"
    if w.endswith("as"):
        return "las"
    return "la" if w.endswith("a") and w not in ("dia", "mapa", "problema", "idioma") else "el"


class Dialogue:
    def __init__(self, memory, today=None):
        self.m = memory
        self.start = time.time()
        self.user: Optional[str] = None
        self.formal = False
        self.pending = None                 # ("define", frase) | ("confirm", [triples], texto) | ("name", frase_original)
        self.last = ""                      # ultima respuesta (para "repite")
        self.last_question = ""
        self.last_facts: List[tuple] = []   # triples guardados con la ultima frase
        self.dry = False                    # True: contesta pero no borra nada (lo usa talks)

    # ---- utilidades -------------------------------------------------------
    def _forget_pol(self, triple, neg: bool) -> None:
        if not self.dry:
            self.m.facts = [f for f in self.m.facts if not _same_fact(f, triple, neg)]

    def _forget(self, triple) -> bool:
        return True if self.dry else self.m.forget_fact(triple)

    def _today(self) -> date:
        return getattr(self.m, "today", None) or date.today()

    def _facts(self, neg=False, every=False):
        return [f for f in self.m.facts if bool(f.get("neg")) == neg and (every or f.get("source") not in ("efecto", "semilla"))]

    def _names(self, every=False):
        out = set()
        for f in self._facts(every=every):
            out.update((f["s"], f["o"]))
        return out

    def _disp(self, name: str) -> str:
        d = getattr(self.m, "display", {}).get(name.upper())
        return d or name.replace("_", " ").title()

    def _find(self, phrase: str) -> Optional[str]:
        """Nombre de la memoria que corresponde a una frase ("el perro" -> PERRO) o None."""
        words = [w for w in n(phrase).split() if w not in DET]
        if not words:
            return None
        key = canon("_".join(words).upper())
        for name in self._names(every=True):
            if canon(name) == key:
                return name
        return None

    def _about(self, name: str):
        return [f for f in self._facts(every=True) if canon(f["s"]) == canon(name) or canon(f["o"]) == canon(name)]

    def _hello(self, who: str, tail: str = "") -> str:
        return who + (f", {self.user}" if self.user else "") + "!" + tail

    def _help(self) -> str:
        return "¿En qué puedo ayudarle?" if self.formal else "¿En qué puedo ayudarte?"

    def _said(self, qa, facts) -> str:
        seen = []
        for f in facts:
            if qa is None:
                seen.append(" ".join((f["s"], f["p"], f["o"])).lower() + ".")
                continue
            s = qa.say((f["s"], f["p"], f["o"]), neg=bool(f.get("neg"))) + "."
            if s not in seen:
                seen.append(s)
        return " ".join(seen[:8])

    def talks(self, raw: str) -> bool:
        """Frase corta (1-2 palabras) que es conversacion: hola, gracias, vale, ¿y Ana?, repite..."""
        if self.pending:
            return True
        probe = Dialogue(self.m)
        probe.dry = True
        probe.user, probe.last_question, probe.last_facts = self.user, self.last_question, list(self.last_facts)
        probe.last = self.last
        reply, cont = probe.act(raw, None)
        return bool(reply) or (cont is not None and cont != raw)

    # ---- coherencia (bloque D) -------------------------------------------
    def note_new(self, triple, neg: bool, raw: str = "", when: str = "", say=None) -> str:
        """Tras guardar un hecho: si cambia un estado, el viejo pasa a pasado; si contradice, pregunta. Devuelve el aviso (o "")."""
        low = norm(raw)
        kind, old = coherence.classify([f for f in self.m.facts if not _same_fact(f, triple, neg)], triple, neg, bool(when),
                                       bool(re.search(r"\bya no\b", low)), getattr(self.m, "opposites", []))
        if not kind:
            return ""
        fmt = say or (lambda t, n=False: " ".join(t).lower())
        old_t = (old["s"], old["p"], old["o"])
        until = self._today().isoformat()
        if kind in ("supersede", "supersede_neg"):
            if kind == "supersede_neg":                      # el "ya no" no se guarda como hecho negado
                self.m.facts = [f for f in self.m.facts if not _same_fact(f, triple, True)]
            coherence.to_past(self.m, old, until)
            return f"Vale: antes decías que {fmt(old_t)}; ahora lo tomo como pasado."
        self.pending = ("conflict", old_t, tuple(x.upper() for x in triple), neg, bool(old.get("neg")))
        return (f"Ojo: antes me dijeron «{fmt(old_t, bool(old.get('neg')))}» y ahora «{fmt(tuple(x.upper() for x in triple), neg)}». "
                "¿Cuál es correcta: la nueva, la anterior o las dos?")

    def explain(self, qa, statement: Optional[str] = None) -> str:
        """"¿Como lo sabes?": de donde sale un hecho (me lo dijiste / lo deduje / lo dijo otro)."""
        s = p = o = None
        if statement:
            found = qa.parse(statement.strip(" ?¿.") + ".") or []
            if not found:
                return "No he entendido qué quieres que justifique."
            s, p, o = found[0]["s"], found[0]["p"], found[0]["o"]
        elif self.last_question:
            kind, t = qa.read(self.last_question)
            if not t and self.last:
                found = qa.parse(self.last.strip()) or []            # preguntas especiales: se justifica lo que dije
                if found:
                    t = {"s": found[0]["s"], "p": found[0]["p"], "o": found[0]["o"]}
            if not t:
                return "No sé a qué te refieres."
            s = None if t["s"] == "xqx" else t["s"]
            o = None if t["o"] == "xqx" else t["o"]
            p = t["p"]
        else:
            return "¿El qué? Pregúntame algo primero."
        hits = qa.lookup(s, p, o)
        if hits:
            f = next(x for x in self.m.facts if (x["s"], x["p"], x["o"]) == hits[0] and not x.get("neg"))
            when = datetime.fromtimestamp(f.get("t", time.time())).strftime("%d/%m/%Y")
            src = f.get("source", "usuario")
            if src == "semilla":
                return "Es parte de mi conocimiento de fábrica."
            if src == "efecto":
                return "Lo deduje de lo que pasó en la frase (quien da algo ya no lo tiene, quien lo recibe sí)."
            if f["p"].endswith("_QUE"):
                return f"Lo dijo {qa._disp(f['s'])}; yo no lo sé por mí mismo."
            return f"Me lo dijiste tú el {when}" + (f": «{src.strip().rstrip('.')}»." if src and src != "usuario" else ".")
        d = qa.derived(s, p, o)
        if d:
            return "Lo deduje: " + qa.say(d[0]) + qa._because(d[0]) + "."
        return "No lo sé, no tengo ese dato."

    # ---- entrada principal -----------------------------------------------
    def act(self, raw: str, qa=None) -> Tuple[Optional[str], Optional[str]]:
        t = n(raw)
        if not t:
            return None, None
        # 1) respuestas a algo que yo pregunte
        if self.pending:
            kind = self.pending[0]
            if kind == "confirm":
                if re.fullmatch(YES, t):
                    triples, _ = self.pending[1], self.pending[2]
                    gone = sum(self._forget(tr) for tr in triples)
                    self.pending = None
                    return f"Olvidado ({gone} hechos).", None
                if re.fullmatch(NO, t):
                    self.pending = None
                    return "Vale, no olvido nada.", None
                self.pending = None
            elif kind == "conflict":
                _, old_t, new_t, new_neg, old_neg = self.pending
                if re.fullmatch(r"(la )?(nueva|ultima|actual|ahora|esa|segunda|reciente)( es la correcta| vale)?", t):
                    self._forget_pol(old_t, old_neg)
                    self.pending = None
                    return "Vale, me quedo con la nueva.", None
                if re.fullmatch(r"(la )?(anterior|vieja|antigua|primera|antes|de antes)( es la correcta| vale)?", t):
                    self._forget_pol(new_t, new_neg)
                    self.pending = None
                    return "Vale, me quedo con la anterior.", None
                if re.fullmatch(r"(las dos|ambas|las dos valen|las dos son correctas|todas)", t):
                    self.pending = None
                    return "Vale, guardo las dos.", None
                self.pending = None
            elif kind == "define":
                phrase = self.pending[1]
                m = re.fullmatch(r"(?:es|son|era)\s+(.+)", raw.strip(" .!¡"), flags=re.I)
                bare = re.fullmatch(r"((?:un|una|el|la|unos|unas)\s+[\wáéíóúñ ]{2,40})", raw.strip(" .!¡"), flags=re.I)
                if m or bare:
                    rest = m.group(1) if m else bare.group(1)
                    self.pending = None
                    head = phrase[0].upper() + phrase[1:]
                    return None, f"{head} es {rest}."
                if re.fullmatch(r"(no lo se|no se|ni idea|nada|da igual|olvidalo)", t):
                    self.pending = None
                    return "Vale, otra vez será.", None
                self.pending = None
            elif kind == "name":
                stored = self.pending[1]
                m = re.fullmatch(r"(?:(?i:me llamo |soy |mi nombre es ))?(" + CAP + ")", raw.strip(" .!¡"))
                if m:
                    self.user = m.group(1)
                    self.pending = None
                    return f"Encantado, {self.user}.", (self.resolve(stored) if stored else None)
                self.pending = None
        # 2) actos sociales
        r = self._social(raw, t)
        if r:
            return r, None
        r = self._definitions(raw, t, qa)
        if r:
            return r
        r = self._self_and_memory(raw, t, qa)
        if r:
            return r, None
        r = self._orders(raw, t, qa)
        if r:
            return r, None
        # 3) referencias: se reescribe y se sigue
        new = self.resolve(raw)
        if isinstance(new, tuple):                      # (pregunta, None) -> hay que preguntar algo antes
            return new[0], None
        return None, new


    # ---- E: aprender conceptos por definicion (parche-58) ---------------------
    ART = r"(?:(?:un|una|el|la|los|las|unos|unas)\s+)?"

    def _bare(self, x: str) -> str:
        return re.sub(r"^(un|una|el|la|los|las|unos|unas)\s+", "", n(x)).strip()

    def _definitions(self, raw: str, t: str, qa):
        m_ = self.m
        a = self.ART
        # sinonimos
        m = re.fullmatch(r"(.+?) (?:es|son) (?:lo mismo que|sinonimo de|sinonima de|igual que|equivalente a|otro nombre de|otra palabra para)\s+(.+)|(.+?) significa (?:lo mismo que )?(.+)", t)
        if m:
            x, y = self._bare(m.group(1) or m.group(3)), self._bare(m.group(2) or m.group(4))
            if x and y and " " not in x and " " not in y:
                known = lambda w: any(w.upper() in (f["s"], f["o"]) or w.upper() == qa.canon_name(f["s"]) if False else w.upper() in (norm(f["s"]).upper(), norm(f["o"]).upper()) for f in m_.facts)
                base, other = (x, y) if known(x) or not known(y) else (y, x)
                m_.alias[other.upper()] = base.upper()
                m_.alias[norm(other).upper()] = norm(base).upper()
                return f"Vale: {other} y {base} son lo mismo.", None
        # contrarios
        m = re.fullmatch(r"(\w+) (?:es|son) (?:lo contrario|lo opuesto|el contrario|el opuesto|antonimo) de (\w+)", t)
        if m and m.group(1) not in ("cual", "que") and "?" not in raw:
            m_.opposites.append([m.group(1), m.group(2)])
            return f"Vale: {m.group(1)} es lo contrario de {m.group(2)}.", None
        # verbo = otro verbo (+ resto)
        m = re.fullmatch(r"(\w+(?:ar|er|ir)) es ((\w+(?:ar|er|ir))(?: .+)?)", t)
        if m and "?" not in raw:
            m_.verb_isa[m.group(1)] = m.group(3 if False else 2).split()[0]
            m_.defs[m.group(1)] = m.group(2)
            return f"Vale: {m.group(1)} es {m.group(2)}.", None
        # para que sirve
        use = r"(?:sirve|sirven|se usa|se usan|se utiliza|se utilizan)"
        m = re.fullmatch(r"(.+?) es (?:un|una) (\w+(?: \w+)?) (?:que|con el que|con la que) " + use + r" para (.+)", t)
        if m and "?" not in raw:
            x, g, v = self._bare(m.group(1)), m.group(2), "_".join(m.group(3).split()).upper()
            m_.add_fact((x.replace(" ", "_"), "SERVIR_PARA", v), source=raw.strip())
            m_.defs[x] = f"{self._art(g)} {g} que sirve para {m.group(3)}"
            return None, f"{self._art(x).capitalize()} es {self._art(g)} {g}."
        m = re.fullmatch(r"(.+?) " + use + r" para (.+)", t)
        if m and "?" not in raw:
            x, v = self._bare(m.group(1)), "_".join(m.group(2).split()).upper()
            m_.add_fact((x.replace(" ", "_"), "SERVIR_PARA", v), source=raw.strip())
            return f"Entendido: {self._art(x)} sirve para {m.group(2)}.", None
        m = re.fullmatch(r"para que " + use + r" (.+)", t)
        if m:
            x = self._bare(m.group(1)).replace(" ", "_").upper()
            fs = [f for f in m_.facts if f["p"] == "SERVIR_PARA" and f["s"] == x]
            if fs:
                return f"{self._art(m.group(1)).capitalize()} sirve para {fs[0]['o'].replace('_', ' ').lower()}.", None
            return None
        m = re.fullmatch(r"que " + use + r" para (.+)", t)
        if m:
            key = "_".join(m.group(1).split()).upper()
            fs = [f for f in m_.facts if f["p"] == "SERVIR_PARA" and (f["o"] == key or f["o"].startswith(key + "_"))]
            if fs:
                return f"{self._art(fs[0]['s'].replace('_', ' ').lower()).capitalize()} sirve para {m.group(1)}.", None
            return None
        r = self._meaning(raw, t)
        if r:
            return r
        # que es X
        m = re.fullmatch(r"(?:que|quien) (?:es|son|significa) (.+)", t)
        if m and self._bare(m.group(1)) in TIEMPO_NOMBRES:               # "¿Qué es el lunes?": la escuela lo lee como tiempo, no como cosa
            x = self._bare(m.group(1)).upper()
            fs = [f for f in self.m.facts if norm(f["s"]).upper() == x and f["p"] == "ES"]
            if fs:
                acc = {"dia": "día", "estacion": "estación", "miercoles": "miércoles", "sabado": "sábado", "otono": "otoño"}
                fx = lambda w: " ".join(acc.get(x, x) for x in w.split())
                return f"{fx(m.group(1).strip()).capitalize()} es {fx(fs[0]['o'].lower().replace('_', ' '))}.", None
        if m:
            x = self._bare(m.group(1))
            if x in m_.defs:
                d = m_.defs[x]
                return (f"{x.capitalize()} es {d}." if " " not in m.group(1).strip() else f"{self._art(x).capitalize()} es {d}."), None
            # "¿Que es un perro?" con hechos ES guardados: se contesta directamente, sin depender de como la escuela lea la pregunta
            if t.startswith("que ") and re.match(r"(un|una|el|la|los|las)\s", t.split(" ", 2)[2] if len(t.split(" ", 2)) > 2 else ""):
                name = self._find(m.group(1))
                if name:
                    objs = []
                    for f in self._facts(every=True):
                        if canon(f["s"]) == canon(name) and f["p"] == "ES" and f["o"] not in objs:
                            objs.append(f["o"])
                    if objs:
                        def _cls(o):
                            d = self._disp(o).lower()
                            return d if re.match(r"(un|una)\s", d) else ("una " if o.endswith("A") else "un ") + d
                        cls = [_cls(o) for o in objs[:3]]
                        return f"{self._art(self._disp(name).lower()).capitalize()} es {' y '.join(cls)}.", None
        return None

    @staticmethod
    def _art(x: str) -> str:
        x = x.strip()
        if re.match(r"(un|una|el|la|los|las)\s", x):
            return x
        return ("la " if x.endswith("a") else "el ") + x


    # ---- C: efectos de las acciones (parche-59) ----------------------------------
    def apply_effects(self, parsed) -> List[str]:
        """parsed = [(s, p, o, o_disp)] de UNA frase afirmativa. Aplica lo que cambia: quien tiene que, estados, lugares."""
        from src.reasoning.efectos import effects
        from src.reasoning import coherence
        notes = []
        today = self._today().isoformat()
        for kind, tr in effects(parsed):
            tr = tuple(x.upper() for x in tr)
            if kind == "lose":
                for f in list(self.m.facts):
                    if f["s"] == tr[0] and f["p"] == tr[1] and canon(f["o"]) == canon(tr[2]) and not f.get("neg"):
                        coherence.to_past(self.m, f, today)
                continue
            if any((f["s"], f["p"], f["o"]) == tr and not f.get("neg") for f in self.m.facts):
                continue
            k, old = coherence.classify([f for f in self.m.facts], tr, False, False, False, getattr(self.m, "opposites", []))
            if k in ("supersede", "antonym") and old:
                coherence.to_past(self.m, old, today)
            self.m.add_fact(tr, source="efecto")
        return notes

    def _meaning(self, raw: str, t: str):
        """"¿Cual es lo contrario de X?" / "¿Que significa X?" """
        from src.reasoning.coherence import ANTONYMS, stem
        m = re.fullmatch(r"(?:cual|que) es (?:lo contrario|lo opuesto|el contrario|el opuesto|el antonimo) de (.+)", t)
        if m:
            w = self._bare(m.group(1))
            disp = (re.search(r"(?:contrario|opuesto|antonimo|antónimo) de (?:el |la |lo )?([\wáéíóúñ]+)", raw, flags=re.I) or [None, w])[1]
            fix = lambda x: {"pequeno": "pequeño", "dificil": "difícil", "facil": "fácil", "rapido": "rápido", "debil": "débil", "ancho": "ancho",
                             "dia": "día", "mas": "más"}.get(x, x)
            pairs = [tuple(x) for x in ANTONYMS] + [tuple(x) for x in getattr(self.m, "opposites", [])]
            for a, b in pairs:
                if stem(norm(a)) == stem(w):
                    return f"Lo contrario de {disp} es {fix(b)}.", None
                if stem(norm(b)) == stem(w):
                    return f"Lo contrario de {disp} es {fix(a)}.", None
            return None
        m = re.fullmatch(r"que (?:significa|quiere decir) (.+)", t)
        if m:
            w = self._bare(m.group(1)).upper()
            al = self.m.alias
            other = [k for k, v in al.items() if v == w] + ([al[w]] if w in al else [])
            if other:
                return f"{m.group(1).capitalize()} significa lo mismo que {other[0].lower()}.", None
            d = self.m.defs.get(self._bare(m.group(1)))
            if d:
                return f"{m.group(1).capitalize()} es {d}.", None
        return None

    # ---- A2 / A7 ------------------------------------------------------------
    def _social(self, raw: str, t: str) -> Optional[str]:
        if re.search(r"\b(usted|ustedes)\b|\bcomo esta\b", t) and not re.search(r"\bcomo esta (el|la|mi|tu)\b", t):
            self.formal = True
        if re.search(r"\b(tuteame|tutearme|tutea|tutead)\b|puedes tutear", t):
            self.formal = False
            return "De acuerdo, te hablaré de tú."
        m = re.search(r"\b(?:[Mm]e llamo|[Mm]i nombre es|[Ss]oy|[Ll]lámame|[Pp]uedes llamarme)\s+(" + CAP + r")\s*[.!]?\s*$", raw)
        if m:
            self.user = m.group(1)
            return f"Encantado, {self.user}."
        if re.fullmatch(r"como me llamo|sabes como me llamo|cual es mi nombre|quien soy|sabes quien soy", t):
            if self.user:
                return f"Te llamas {self.user}."
            self.pending = ("name", "")
            return "Todavía no me lo has dicho. ¿Cómo te llamas?"
        m = re.fullmatch(r"(buenos dias|buenas tardes|buenas noches|hola|ola|hey|saludos|buenas)(?: a todos)?(?: (que tal|como estas|como esta|como va todo))?(?: \w+)?", t)
        if m and len(t.split()) <= 4:
            key = m.group(1)
            text = self._hello(GREET[key], "")
            if m.group(2):
                text += " Estoy bien, gracias."
            return text + " " + self._help()
        if re.fullmatch(r"(como estas|que tal|que tal estas|como te va|como va todo|como esta usted|que tal esta usted|que tal todo|como te encuentras)( hoy)?", t):
            return "Estoy bien, gracias. ¿Y usted?" if self.formal else "Estoy bien, gracias. ¿Y tú?"
        if re.fullmatch(BYE + r"( \w+)?", t):
            return "¡Hasta luego" + (f", {self.user}" if self.user else "") + "! Aquí estaré cuando quieras."
        if re.fullmatch(THANKS, t):
            return "De nada, a su disposición." if self.formal else "De nada."
        if re.fullmatch(SORRY, t):
            return "No pasa nada."
        if t in GOOD:
            return GOOD[t]
        if re.fullmatch(YES, t):
            return "Entendido."
        if re.fullmatch(NO, t):
            return "Vale."
        if re.fullmatch(ACK, t):
            return "Me alegro." if t in ("perfecto", "genial", "estupendo", "fenomenal") else "Vale."
        return None

    # ---- A5 -----------------------------------------------------------------
    def _self_and_memory(self, raw: str, t: str, qa) -> Optional[str]:
        if re.fullmatch(r"(quien eres|que eres|como te llamas|cual es tu nombre|presentate|quien eres tu|que eres tu)", t):
            return "Soy el LCM (Large Conceptual Model): aprendo español y razono con lo que me cuentas, sin ningún LLM."
        if re.fullmatch(r"(que sabes hacer|que puedes hacer|en que me puedes ayudar|para que sirves|que haces|que sabes hacer tu|ayudame)", t):
            return ("Puedo aprender los hechos y reglas que me cuentes, contestar preguntas (quién, qué, dónde, cuándo, sí o no), "
                    "deducir con lo aprendido y recordar fechas. Prueba: «Pedro compró pan ayer» y luego «¿Cuándo compró Pedro pan?».")
        if re.fullmatch(r"(que dia es hoy|que fecha es hoy|en que fecha estamos|a que dia estamos|que dia es|que fecha es|a cuantos estamos)", t):
            d = self._today()
            return f"Hoy es {DAYS[d.weekday()]}, {d.day} de {['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'][d.month-1]} de {d.year}."
        if re.fullmatch(r"(que hora es|me dices la hora|tienes hora)", t):
            return "Son las " + datetime.now().strftime("%H:%M") + "."
        if qa is not None and re.fullmatch(r"(como lo sabes|como sabes eso|por que lo sabes|de donde lo sacas|de donde sale eso|estas seguro|como lo sabes tu)", t):
            return self.explain(qa)
        m = re.fullmatch(r"(?:como|de donde) (?:sabes|sacas) que (.+)", t)
        if m and qa is not None:
            return self.explain(qa, re.sub(r"^[¿\s]*(?:[Cc]ómo|[Dd]e dónde)\s+(?:sabes|sacas)\s+que\s+", "", raw).strip(" ?¿"))
        facts = self._facts()
        if re.fullmatch(r"(que sabes|que sabes tu|cuanto sabes|que conoces|que has aprendido)", t):
            if not facts:
                return "Todavía no sé nada. Cuéntame algo."
            return f"Sé {len(facts)} hechos sobre {len(self._names())} cosas. Por ejemplo: " + self._said(qa, facts[:3])
        if re.fullmatch(r"(cuantas cosas sabes|cuantos hechos sabes|cuantos hechos tienes|cuantas cosas conoces|cuantas cosas sabes tu)", t):
            return f"Sé {len(facts)} hechos sobre {len(self._names())} cosas."
        if re.fullmatch(r"(que te he dicho( hoy)?|que te dije|que hemos hablado|de que hemos hablado|que te he contado|que recuerdas|que te he dicho hasta ahora)", t):
            mine = [f for f in facts if f.get("t", 0) >= self.start]
            if not mine:
                return "Todavía no me has contado nada."
            return "En esta conversación me has dicho: " + self._said(qa, mine)
        m = re.fullmatch(r"(?:dime |cuentame |hablame |dime algo )?(?:lo que sabes |que sabes |todo lo que sabes |algo )?(?:de|sobre|acerca de)\s+(.+)", t)
        if m and (re.match(r"(que sabes|dime|cuentame|hablame)", t)):
            who = m.group(1)
            name = self._find(who)
            about = self._about(name) if name else []
            if not about:
                phrase = re.sub(r"^(el|la|los|las|un|una)\s+", "", who)
                self.pending = ("define", phrase)
                return f"No sé nada de {phrase}. ¿Me lo explicas?"
            return self._said(qa, about)
        m = re.fullmatch(r"(que|quien) (es|son|era) ((?:el |la |los |las |un |una )?\w+)", t)
        if m and not self._find(m.group(3)):
            phrase = m.group(3)
            self.pending = ("define", phrase)
            return f"No sé {'quién' if m.group(1) == 'quien' else 'qué'} {'son' if m.group(2) == 'son' else 'es'} {phrase}. ¿Me lo explicas?"
        return None

    # ---- A6 + A8 (eso es falso) --------------------------------------------------
    def _orders(self, raw: str, t: str, qa) -> Optional[str]:
        if re.fullmatch(r"(repite|repitelo|repite lo anterior|repite lo que has dicho|que has dicho|que dijiste|como dices|que dices|otra vez|de nuevo|puedes repetir|puedes repetirlo|no te he entendido|repitemelo)", t):
            return self.last or "Todavía no he dicho nada."
        if re.fullmatch(r"(olvida|olvidate de|borra) (todo|todo lo que sabes|todo lo anterior)|olvidalo todo|borra la memoria", t):
            facts = [(f["s"], f["p"], f["o"]) for f in self.m.facts if f.get("source") not in ("semilla", "efecto")]
            if not facts:
                return "Ya no sé nada, no hay nada que olvidar."
            self.pending = ("confirm", facts, "todo")
            return f"Voy a olvidar los {len(facts)} hechos que sé. ¿Seguro?"
        if re.fullmatch(r"(olvida|olvidate de|borra) (eso|lo anterior|lo que acabo de decir|lo ultimo|lo que te he dicho)|olvidalo", t):
            return self._forget_last(qa)
        if re.fullmatch(r"(eso |lo que he dicho |lo anterior )?(es |era )?(falso|mentira|incorrecto|un error|erroneo)|(eso )?no es (cierto|verdad|asi)|te equivocas|estas equivocad[oa]|estoy equivocad[oa]|me equivoque|me he equivocado|no eso no|eso no es asi", t):
            if not self.last_facts:
                return "¿A qué te refieres? No tengo nada reciente que corregir."
            return self._forget_last(qa, "Vale, lo olvido: ")
        if re.fullmatch(r"(eso )?(es )?(cierto|correcto|exacto|verdad)|eso es|asi es|tienes razon|eso es verdad", t):
            return "Bien, lo tengo anotado." if self.last_facts else "Vale."
        m = re.match(r"\s*(?:olvida|borra|olvidate de)\s+(?:lo de |que |a |al |de |el |la )?(.+?)\s*[.!]?\s*$", raw, flags=re.I)
        if m and re.match(r"\s*(olvida|borra|olvidate)", raw, flags=re.I):
            body = m.group(1)
            parse = getattr(qa, "parse", None)
            if len(body.split()) >= 3 and parse:
                found = parse(body[0].upper() + body[1:] + ".") or []
                trips = [(x["s"], x["p"], x["o"]) for x in found]
                gone = [tr for tr in trips if any((f["s"], f["p"], f["o"]) == tuple(y.upper() for y in tr) for f in self.m.facts)]
                if gone:
                    for tr in gone:
                        self._forget(tr)
                    return "Hecho, lo he olvidado: " + body[0].upper() + body[1:] + "."
            name = self._find(body)
            about = self._about(name) if name else []
            if not about:
                return f"No sé nada de {body}, no hay nada que olvidar."
            trips = list({(f["s"], f["p"], f["o"]) for f in about})
            if len(trips) == 1:
                self._forget(trips[0])
                return "Hecho, lo he olvidado: " + self._said(qa, about)
            self.pending = ("confirm", trips, body)
            return f"Voy a olvidar {len(trips)} hechos sobre {body}. ¿Seguro?"
        return None

    def _forget_last(self, qa, prefix="Hecho, lo he olvidado: ") -> str:
        if not self.last_facts:
            return "¿A qué te refieres? No tengo nada reciente que olvidar."
        texts = [qa.say(tr) + "." for tr in self.last_facts] if qa else [" ".join(tr) for tr in self.last_facts]
        for tr in self.last_facts:
            self._forget(tr)
        self.last_facts = []
        return prefix + " ".join(texts)

    # ---- A8: referencias -----------------------------------------------------
    def resolve(self, raw: str):
        """Reescribe mi/mis/yo, este/ese..., tambien/tampoco/otra vez y "¿Y Ana?". Devuelve texto o (pregunta, None)."""
        text = raw
        m = re.fullmatch(r"\s*¿?\s*[Yy]\s+((?:a|de|con|en|para)\s+)?((?:el|la|los|las)\s+)?(" + CAP + r")\s*\?*\s*", raw)
        if m and self.last_question:
            caps = [w for w in re.findall(CAP, self.last_question)]
            caps = caps[1:] if caps and self.last_question.lstrip("¿ ").startswith(caps[0]) else caps
            if caps:
                return self.last_question.replace(caps[0], m.group(3), 1)
            return ("¿A qué te refieres? Dime la pregunta completa.", None)
        if re.search(r"\b[Mm]is?\s+\w+", text) or re.search(r"\b[Yy]o\b", text):
            if not self.user:
                self.pending = ("name", raw)
                return ("¿Cómo te llamas? Así sabré a quién te refieres con «mi» o «yo».", None)
            def sub(mo):
                noun = mo.group(1)
                out = f"{_article(noun)} {noun} de {self.user}"
                return out[0].upper() + out[1:] if mo.start() == 0 else out
            text = re.sub(r"\b[Mm]is?\s+(\w+)", sub, text)
            text = re.sub(r"\b[Yy]o\b", self.user, text)
        text = re.sub(r"\b(este|esta|estos|estas|ese|esa|esos|esas|aquel|aquella|aquellos|aquellas)\b(?!\s+(?:es|son|era|eran)\b)(?=\s+\w)",
                      self._dem, text, flags=re.I)
        text = re.sub(r"(\w+)\s+tampoco\s+(\w+)", r"\1 no \2", text)
        text = re.sub(r"\s+(también|tambien|otra vez|de nuevo|nuevamente)\b", "", text)
        return text

    @staticmethod
    def _dem(mo) -> str:
        word = mo.group(1)
        art = GEN.get(norm(word))
        if not art:
            return mo.group(0)
        return art.capitalize() if word[0].isupper() else art

    # ---- A3 / A4 -------------------------------------------------------------
    def mention(self, raw: str) -> Optional[str]:
        known = {norm(self._disp(x)).replace(" ", "_"): x for x in self._names()}
        for w in re.findall(r"\w+", norm(raw)):
            for k, x in known.items():
                if canon(w.upper()) == canon(k.upper()):
                    return self._disp(x)
        return None

    def clarify_statement(self, raw: str) -> str:
        who = self.mention(raw)
        if who:
            return (f"Creo que hablas de {who}, pero no he entendido qué quieres decirme. "
                    f"¿Puedes usar una frase más simple, por ejemplo «{who} compra pan»?")
        return f"No he entendido «{raw.strip()}». ¿Puedes decirlo con una frase más simple, por ejemplo «Ana ama a Luis»?"

    def clarify_question(self, raw: str) -> str:
        who = self.mention(raw)
        if who:
            return f"No he entendido la pregunta. Creo que preguntas por {who}: puedes probar «¿Qué sabes de {who}?»."
        return "No he entendido la pregunta. Prueba con otra forma (por ejemplo: ¿Quién compró pan?)."

    def after_answer(self, question: str, answer: str, qa) -> str:
        """Si no sabe y hay un nombre que no conoce, lo pregunta (y lo aprende con la respuesta)."""
        self.last_question = question
        if answer.startswith("No he entendido"):
            answer = self.clarify_question(question)
        elif answer.startswith("No lo sé"):
            try:
                _, t = qa.read(question)
            except Exception:
                t = None
            if t:
                for key in ("s", "o"):
                    w = t.get(key)
                    if w and w != "_" and not w.startswith("xqx") and w not in ("zurita", "bertoldo") and not self._find(w):
                        disp = (t.get(key + "_disp") or w).strip()
                        disp = re.sub(r"^(el|la|los|las|un|una)\s+", "", disp, flags=re.I)
                        self.pending = ("define", disp)
                        answer += f" No conozco «{disp}»: ¿me lo explicas?"
                        break
        self.last = answer
        return answer


class Conversation:
    """Bucle completo para tests: dialogo + QA + guardar frases (sin oido de plantillas)."""

    def __init__(self, memory, parser, qa_factory):
        from src.language.discourse import split_sentences, next_topic
        self._split, self._next = split_sentences, next_topic
        self.m, self.parser = memory, parser
        self.qa = qa_factory(memory, parser)
        self.d = Dialogue(memory)
        self.topic = None

    def say(self, raw: str) -> str:
        reply, cont = self.d.act(raw, self.qa)
        out = []
        if reply:
            out.append(reply)
        if cont:
            out.append(self._process(cont))
        text = " ".join(x for x in out if x)
        self.d.last = text or self.d.last
        return text

    def _process(self, raw: str) -> str:
        if is_question(raw):
            return self.d.after_answer(raw, self.qa.answer(raw), self.qa)
        res = []
        stored = []
        for part in self._split(raw):
            found = self.parser.parse(part, self.topic) or []
            if not found:
                res.append(self.d.clarify_statement(part))
                continue
            if not any(t["neg"] for t in found):
                self.d.apply_effects([(t["s"], t["p"], t["o"], t.get("o_disp", "")) for t in found])
            for t in found:
                tr = (t["s"], t["p"], t["o"])
                self.m.add_fact(tr, source=part, neg=t["neg"], when=t.get("when", ""), when_disp=t.get("when_disp", ""), quant=t.get("q", ""))
                self.m.note_surface(tr, t.get("template"), t.get("s_disp"), t.get("o_disp"))
                stored.append(tuple(x.upper() for x in tr))
                res.append(f"Entendido: {'NO ' if t['neg'] else ''}{' '.join(tr).upper()}.")
                note = self.d.note_new(tr, t["neg"], part, t.get("when", ""), lambda f, n=False: self.qa.say(f, neg=n))
                if note:
                    res.append(note)
            self.topic = self._next(found, self.topic)
        if stored:
            self.d.last_facts = stored
        return " ".join(res)
''',
    'src/language/discourse.py': r'''"""Discurso (parche-44, Fase 2): varias frases seguidas. El sujeto de la frase anterior (el "tema") sustituye a "el/ella" y es el
sujeto de un verbo sin sujeto escrito ("Ana vive en Madrid. Trabaja en un banco." -> ana trabajar_en banco). Sin LLM."""
import re
from typing import Dict, List, Optional

from .extract import PRON_SUBJ


def split_sentences(text: str) -> List[str]:
    return [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]


def next_topic(found: List[Dict], topic: Optional[str]) -> Optional[str]:
    """Tema tras una frase: el sujeto de su primera proposicion (si no es un pronombre)."""
    for t in found:
        if t["s"] not in PRON_SUBJ:
            return t["s"]
    return topic


def parse_text(parser, text: str, topic: Optional[str] = None) -> List[Dict]:
    out: List[Dict] = []
    for sent in split_sentences(text):
        found = parser.parse(sent, topic=topic) or []
        topic = next_topic(found, topic)
        out += found
    return out
''',
    'src/language/ear.py': r'''"""El oido del LCM: del espanol a proposiciones (sujeto, predicado, objeto).

Es un modelo PEQUENO ENTRENADO (no un LLM, no reglas):
  - cada palabra se representa por su forma y sus trozos de letras, asi que
    palabras y nombres nunca vistos tambien tienen representacion;
  - un Transformer lee la frase entera;
  - una cabeza marca que palabra es el sujeto y cual el objeto (aprende el ORDEN:
    "Ana es madre de Luis" y "Luis tiene como madre a Ana" significan lo mismo);
  - el predicado se elige comparando la frase con la frase-etiqueta de cada
    predicado del catalogo ("padre de"). Como la comparacion es por palabras
    emparejadas, un predicado NUEVO se entiende sin reentrenar.
"""
from __future__ import annotations

import re
import zlib
from difflib import SequenceMatcher
from typing import Dict, List, Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F

from .lexicon import ES_ALIASES, NO_EAR, PREPS, norm, phrase_for, tokenize

# En MPS (Mac) el camino rapido de PyTorch para Transformers en inferencia no existe: se desactiva.
try:
    torch.backends.mha.set_fastpath_enabled(False)
except Exception:
    pass

STOPWORDS = set("el la los las un una unos unas que de a por con en y o no nunca jamas se sabe dicen es son fue ser siendo "
                "como segun ya muy mi su sus lo al del era eran fue fueron sera seran seria estaba estaban esta estan sido ha han habia".split()) | set(",.;:!?")

BUCKETS = 24000
GRAMS = 14
MAXLEN = 40


def _h(s: str) -> int:
    return zlib.crc32(s.encode()) % (BUCKETS - 1) + 1


_cache: Dict[str, List[int]] = {}


def word_features(w: str) -> List[int]:
    if w in _cache:
        return _cache[w]
    ids = [_h("w:" + w)]
    padded = f"<{w}>"
    for n in (3, 4, 5):
        for i in range(max(0, len(padded) - n + 1)):
            ids.append(_h(f"g{n}:" + padded[i:i + n]))
    ids = ids[:GRAMS] + [0] * (GRAMS - len(ids[:GRAMS]))
    _cache[w] = ids
    return ids


def key(w: str) -> str:
    """Raiz aproximada: 'causa'~'causado'~'causan', 'padre'~'padres'. Palabras cortas, enteras."""
    return w if len(w) <= 4 else w[:4]


def same_word(w: str, t: str) -> bool:
    """Misma palabra o variante cercana (padre~padres, causa~causado); 'contradice' ya no casa con 'contracayes'."""
    if w == t:
        return True
    return key(w) == key(t) and len(w) > 4 and SequenceMatcher(None, w, t).ratio() >= 0.8


def find_phrase(words, toks) -> int:
    n = len(words)
    for i in range(len(toks) - n + 1):
        if all(same_word(w, t) for w, t in zip(words, toks[i:i + n])):
            return i
    return -1


def word_id(w: str) -> int:
    return _h("w:" + key(w))


class Ear(nn.Module):
    def __init__(self, d: int = 128, layers: int = 2, heads: int = 4):
        super().__init__()
        self.d = d
        self.emb = nn.Embedding(BUCKETS, d, padding_idx=0)
        self.pos = nn.Embedding(MAXLEN, d)
        layer = nn.TransformerEncoderLayer(d, heads, 2 * d, dropout=0.1, batch_first=True)
        self.enc = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.tag = nn.Linear(d, 3)
        self.pred_vec = nn.Parameter(torch.randn(d) * 0.1)
        self.pol = nn.Linear(d, 1)
        self.scope = nn.Linear(d, 1)
        self.q = nn.Linear(d, d)
        self.k = nn.Linear(d, d)
        self.scale = nn.Parameter(torch.tensor(4.0))
        self.exact = nn.Parameter(torch.tensor(4.0))
        nn.init.normal_(self.emb.weight, std=0.1)
        with torch.no_grad():
            self.emb.weight[0].zero_()

    def embed(self, feat):                     # (..., G) -> (..., d)
        e = self.emb(feat).sum(-2)
        return e / (feat != 0).sum(-1, keepdim=True).clamp(min=1).sqrt()

    def forward(self, feat, mask, pmark=None, hide=None, extra=None):
        """pmark (B,T) bool: palabras de la relacion; se sustituyen por un marcador generico
        para que el orden de la frase no dependa de QUE relacion sea."""
        T = feat.shape[1]
        e = self.embed(feat)
        if hide is not None:                   # palabras ocultas (preentrenamiento): su vector se anula, queda solo la posicion
            e = e.masked_fill(hide[..., None], 0.0)
        if extra is not None:                  # rasgos adicionales por palabra (parche-34: mayusculas)
            e = e + extra
        if pmark is not None:
            e = torch.where(pmark[..., None], self.pred_vec.expand_as(e), e)
        x = e + self.pos(torch.arange(T, device=feat.device))[None]
        h = self.enc(x, src_key_padding_mask=~mask)
        return h, self.tag(h)

    def polarity(self, h, mask):
        m = mask[..., None].float()
        return self.pol((h * m).sum(1) / m.sum(1).clamp(min=1)).squeeze(-1)    # logit de "negada"

    def in_scope(self, h, mask):
        m = mask[..., None].float()
        return self.scope((h * m).sum(1) / m.sum(1).clamp(min=1)).squeeze(-1)  # logit: "afirma una relacion"

    def mark(self, tok_ids, phrase_ids):
        """tok_ids (B,T), phrase_ids (B,W) con -1 de relleno -> (B,T) bool"""
        return (tok_ids[:, :, None] == phrase_ids[:, None, :]).any(-1)

    def score(self, h, mask, tok_ids, cand_feat, cand_mask, cand_ids):
        qh = F.normalize(self.q(h), dim=-1)                        # (B,T,d)
        kc = F.normalize(self.k(self.embed(cand_feat)), dim=-1)    # (C,W,d)
        sim = torch.einsum("btd,cwd->bcwt", qh, kc)
        exact = (tok_ids[:, None, None, :] == cand_ids[None, :, :, None]).float()
        s = self.scale * sim + self.exact * exact
        s = s.masked_fill(~mask[:, None, None, :], -1e4).max(-1).values          # (B,C,W)
        cm = cand_mask[None].float()
        return (s * cm).sum(-1) / cm.sum(-1)


def encode_batch(sentences: Sequence[Sequence[str]], device="cpu"):
    T = min(MAXLEN, max(len(s) for s in sentences))
    feat = torch.zeros(len(sentences), T, GRAMS, dtype=torch.long)
    ids = torch.zeros(len(sentences), T, dtype=torch.long)
    mask = torch.zeros(len(sentences), T, dtype=torch.bool)
    for i, toks in enumerate(sentences):
        for j, w in enumerate(toks[:T]):
            feat[i, j] = torch.tensor(word_features(w))
            ids[i, j] = word_id(w)
            mask[i, j] = True
    return feat.to(device), ids.to(device), mask.to(device)


def encode_candidates(phrases: Sequence[str], device="cpu"):
    toks = [tokenize(p) for p in phrases]
    W = max(len(t) for t in toks)
    feat = torch.zeros(len(toks), W, GRAMS, dtype=torch.long)
    ids = torch.full((len(toks), W), -1, dtype=torch.long)
    mask = torch.zeros(len(toks), W, dtype=torch.bool)
    for i, t in enumerate(toks):
        for j, w in enumerate(t):
            feat[i, j] = torch.tensor(word_features(w))
            ids[i, j] = word_id(w)
            mask[i, j] = True
    return feat.to(device), mask.to(device), ids.to(device)


@torch.no_grad()
def predict(ear: Ear, token_lists: Sequence[Sequence[str]], candidates: Sequence[tuple], device="cpu", chunk: int = 128):
    """candidates: lista de (nombre_predicado, frase). Devuelve un dict por oracion."""
    ear.eval()
    valid = [i for i, t in enumerate(token_lists) if len([w for w in t if w not in ",.;:!?"]) >= 3]
    if len(valid) < len(token_lists):          # frases vacias o de 1-2 palabras: se rechazan sin pasar por el modelo
        sub = predict(ear, [token_lists[i] for i in valid], candidates, device, chunk) if valid else []
        res = {i: sub[k] for k, i in enumerate(valid)}
        return [res.get(i) or {"subject": "", "predicate": "", "object": "", "phrase": "", "negated": False,
                               "confidence": 0.0, "in_scope": 0.0, "tokens": list(token_lists[i])}
                for i in range(len(token_lists))]
    out = []
    texts = [t for _, t in candidates]
    cf, cm, ci = encode_candidates(texts, device)
    for a in range(0, len(token_lists), chunk):
        part = token_lists[a:a + chunk]
        feat, ids, mask = encode_batch(part, device)
        h, _ = ear(feat, mask)
        scores = ear.score(h, mask, ids, cf, cm, ci)
        for b, toks in enumerate(part):          # bonus: la frase-etiqueta aparece seguida, en orden
            for c, (_, text) in enumerate(candidates):
                ws = tokenize(text)
                if find_phrase(ws, toks) >= 0:
                    scores[b, c] += 0.3 + 0.05 * len(ws)
                    if any(list(toks[i:i + len(ws)]) == ws for i in range(len(toks) - len(ws) + 1)):
                        scores[b, c] += 0.3          # coincidencia exacta mejor que solo por raiz
        probs = F.softmax(scores * 6.0, dim=-1)
        top = probs.argmax(-1)
        pol = torch.sigmoid(ear.polarity(h, mask))
        scope = torch.sigmoid(ear.in_scope(h, mask))
        _, tags = ear(feat, mask, ear.mark(ids, ci[top]))
        tags = F.log_softmax(tags, dim=-1)
        for b, toks in enumerate(part):
            m = mask[b] & torch.tensor([t not in STOPWORDS for t in toks] + [False] * (mask.shape[1] - len(toks)),
                                       device=mask.device)[:mask.shape[1]]
            if m.sum() < 2:
                m = mask[b]
            m = m & torch.tensor(_not_in_relative(toks) + [False] * (mask.shape[1] - len(toks)), device=mask.device)[:mask.shape[1]] \
                if m.sum() > 2 else m
            s_i = _np_head(toks, int(tags[b, :, 1].masked_fill(~m, -1e4).argmax()))
            o_lg = tags[b, :, 2].masked_fill(~m, -1e4).clone()
            o_lg[s_i] = -1e4
            o_i = _np_head(toks, int(o_lg.argmax()))
            name, text = candidates[int(top[b])]
            conf = float(probs[b, top[b]])
            words = tokenize(text)
            need = words[:-1] if len(words) >= 2 and words[-1] in PREPS else words    # 'padre de': basta 'padre'
            if not all(any(same_word(w, t) for t in toks) for w in need):
                conf = 0.0                      # la relacion elegida no aparece en la frase
            subj, obj = toks[s_i], toks[o_i]
            if name == "ES":                    # "S es un O": orden obligatorio y giro seguido
                start = find_phrase(words, toks)
                if start < 0 or not (s_i < start and o_i >= start + len(words)):
                    conf = 0.0
                if text in ("son", "eran") and not (subj.endswith("s") and obj.endswith("s")):
                    conf = 0.0
            conf *= float(scope[b])
            if "?" in toks:
                conf = 0.0                          # una pregunta no es una afirmacion
            if text in ("son", "eran"):
                subj, obj = singular(subj), singular(obj)
            out.append({"subject": subj.upper(), "predicate": name, "object": obj.upper(), "phrase": text,
                        "negated": bool(pol[b] > 0.5), "confidence": conf, "in_scope": float(scope[b]), "tokens": list(toks)})
    return out


ARTICLES = {"el", "la", "los", "las", "un", "una", "unos", "unas"}


def _np_head(toks, i):
    """'el viento capaz': si se elige el adjetivo, el nucleo es la palabra que sigue al articulo."""
    if i >= 2 and toks[i - 2] in ARTICLES and toks[i - 1] not in STOPWORDS:
        return i - 1
    return i


def _not_in_relative(toks):
    """False dentro de incisos ', que ... ,' (clausulas relativas: no contienen sujeto ni objeto)."""
    keep, inside = [], False
    for i, t in enumerate(toks):
        if inside and t == ",":
            inside = False
            keep.append(False)
            continue
        if t == "," and i + 1 < len(toks) and toks[i + 1] == "que":
            inside = True
        keep.append(not inside)
    return keep


def singular(w: str) -> str:
    if w.endswith("es") and len(w) > 3 and w[-3] not in "aeiou":
        return w[:-2]
    return w[:-1] if w.endswith("s") else w


class EarParser:
    """Usa un Ear entrenado con el catalogo vivo de predicados del LCM."""

    def __init__(self, ear: Ear, device="cpu", min_conf: float = 0.8):
        self.ear = ear.to(device).eval()
        self.device = device
        self.min_conf = min_conf

    def candidates(self, space) -> List[tuple]:
        out = [(n, phrase_for(n)[0]) for n, m in space.metadata.items()
               if m.get("kind") == "predicate" and n not in NO_EAR]
        if "ES" in space.concept_to_id:
            out += [("ES", a) for a in ES_ALIASES]
        return out

    def parse(self, sentence: str, candidates: Sequence[tuple]):
        toks = tokenize(sentence)
        if len([t for t in toks if t not in ",.;:!?"]) < 3:
            return None
        return predict(self.ear, [toks], candidates, self.device)[0]
''',
    'src/language/extract.py': r'''"""De un arbol sintactico a proposiciones (sujeto, relacion, objeto) para CUALQUIER frase (parche-30/32).

Casos:  "Ana es la madre de Luis"   -> (ana, madre_de, luis)     (sustantivo + cop + nmod con preposicion)
        "Un perro es un animal"     -> (perro, es, animal)        (sustantivo + cop, sin complemento)
        "Pedro escribio una carta"  -> (pedro, escribio, carta)   (verbo + nsubj + obj)
        "Ana vive en Madrid"        -> (ana, vive_en, madrid)     (verbo + nsubj + obl con preposicion)
v2 (parche-32): el relativo "que" se sustituye por su antecedente ("la normativa que regula X" -> normativa regula X)
y se detecta la negacion ("no", "nunca", "jamas", "tampoco" ligados al verbo).
"""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from .lexicon import norm

Tree = Sequence[Tuple]       # (forma, upos, head, deprel[, lema]) por palabra
NEG = {"no", "nunca", "jamas", "tampoco"}


def _children(tree: Tree, i: int) -> List[int]:
    return [j for j, w in enumerate(tree) if w[2] == i + 1]


def _name(tree: Tree, i: int) -> str:
    parts = [(i, tree[i][0])] + [(j, tree[j][0]) for j in _children(tree, i) if tree[j][3] in ("flat", "nummod")]
    return "_".join(norm(f) for _, f in sorted(parts))


def _lem(tree: Tree, i: int) -> str:
    """Forma base de la palabra (parche-34): escribio -> escribir. Sin lema, la propia forma."""
    w = tree[i]
    return norm(w[4]) .replace(" ", "_") if len(w) > 4 and w[4] else norm(w[0])


def _prep(tree: Tree, i: int) -> str:
    cases = [norm(tree[j][0]) for j in _children(tree, i) if tree[j][3] == "case"]
    return cases[0] if cases else ""


def _conj(tree: Tree, i: int) -> List[int]:
    """La palabra y todas las que van coordinadas con ella ("pan, queso y fruta": relacion conj), en orden."""
    out, todo = [i], [i]
    while todo:
        for j in _children(tree, todo.pop()):
            if tree[j][3] == "conj" and j not in out:
                out.append(j); todo.append(j)
    return sorted(out)


def _infinitive(tree: Tree, i: int) -> bool:
    """"Cocinar es una accion": un infinitivo con funcion de sujeto es el concepto de esa accion (parche-50)."""
    f = tree[i][0].lower()
    return tree[i][1] == "VERB" and tree[i][3] in ("nsubj", "csubj") and len(f) > 3 and f.endswith(("ar", "er", "ir", "ír"))


def _name_like_adj(tree: Tree, i: int) -> bool:
    """parche-43: "Clara canta ..." -> la escuela la etiqueta ADJ (clara). Un adjetivo con mayuscula, sin determinante, que hace de
    sujeto se trata como un nombre propio."""
    return (tree[i][1] == "ADJ" and tree[i][0][:1].isupper() and tree[i][3] == "nsubj"
            and not any(tree[j][3] == "det" for j in _children(tree, i)))


def _subjects_of(tree: Tree, i: int) -> List[int]:
    """Sujetos del verbo i; un verbo coordinado sin sujeto propio hereda el del anterior ("vive en Madrid y trabaja en Sevilla")."""
    seen = set()
    while True:
        subj = [j for j in _children(tree, i) if tree[j][3] in ("nsubj", "csubj")]
        if subj or tree[i][3] != "conj" or tree[i][2] <= 0 or i in seen:
            return subj
        seen.add(i)
        i = tree[i][2] - 1


TIME_ADV = {"ayer", "hoy", "manana", "anoche", "anteayer", "ahora", "luego", "despues", "antes", "pronto"}
TIME_NOUNS = {"lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo", "enero", "febrero", "marzo", "abril", "mayo", "junio",
              "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre", "primavera", "verano", "otono", "invierno", "manana",
              "tarde", "noche", "semana", "mes", "ano", "dia", "siglo", "veces", "dias", "noches", "tardes", "semanas", "meses", "anos"}
FREQ_ADV = {"siempre", "normalmente", "generalmente", "habitualmente", "frecuentemente", "raramente", "regularmente", "diariamente", "semanalmente", "mensualmente"}
NUM_WORDS = {"una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12}
LOC_ADV = {"encima", "debajo", "dentro", "fuera", "cerca", "lejos", "delante", "detras", "junto", "enfrente", "alrededor"}
SOME_Q = {"algunos", "algunas", "varios", "varias", "muchos", "muchas", "pocos", "pocas"}
NONE_Q = {"ninguno", "ninguna", "ningun", "ningunos", "ningunas"}
TIME_MOD = {"pasado", "proximo", "siguiente", "anterior", "pasada", "proxima"}


def _subtree(tree: Tree, j: int, rels=("case", "det", "amod", "nummod", "flat")) -> List[int]:
    return sorted([j] + [k for k in _children(tree, j) if tree[k][3] in rels])


DATIVE_VERBS = {"dar", "regalar", "entregar", "prestar", "vender", "comprar", "ofrecer", "enviar", "mandar", "devolver", "pasar", "traer", "llevar"}
STRONG_TIME = {"ayer", "anteayer", "anoche", "hoy"}      # nunca son otra cosa, aunque la escuela los lea como adjetivo del objeto


def when_of(tree: Tree, i: int):
    """Expresion temporal del verbo i -> (clave normalizada, como se escribio, indices de sus palabras) o None (parche-51)."""
    near = set(_children(tree, i))
    for j in sorted(near):
        for k in _children(tree, j):
            if norm(tree[k][0]) in STRONG_TIME:
                return norm(tree[k][0]), tree[k][0], [k]
    for j in _children(tree, i):
        w = norm(tree[j][0])
        if tree[j][3] == "advmod" and w in TIME_ADV:
            return w, tree[j][0], [j]
        if tree[j][3] == "advmod" and w in FREQ_ADV:                     # "Ana siempre llega" (parche-56)
            return "frec_" + w, tree[j][0], [j]
        if tree[j][3] in ("obl", "nmod") and tree[j][1] == "NUM" and (w in NUM_WORDS or w.isdigit()) \
                and any(tree[k][3] == "case" and norm(tree[k][0]) == "a" for k in _children(tree, j)):
            idx = _subtree(tree, j)                                       # "a las tres"
            return "hora_" + str(NUM_WORDS.get(w, w)), " ".join(tree[k][0] for k in idx), idx
        if tree[j][3] in ("obl", "nmod"):
            if w in TIME_NOUNS:
                idx = _subtree(tree, j)
                mods = [norm(tree[k][0]) for k in idx if tree[k][3] == "amod" and norm(tree[k][0]) in TIME_MOD]
                return "_".join([w] + mods), " ".join(tree[k][0] for k in idx), idx
            if tree[j][1] == "NUM" and tree[j][0].isdigit() and len(tree[j][0]) == 4:
                idx = _subtree(tree, j)
                return tree[j][0], " ".join(tree[k][0] for k in idx), idx
    return None


PRON_SUBJ = {"el", "ella", "ellos", "ellas"}
MODAL_FORMS = {**{f: "poder" for f in ("puedo", "puedes", "puede", "podemos", "pueden", "podia", "podian", "pudo", "podra", "podria")},
               **{f: "deber" for f in ("debo", "debes", "debe", "debemos", "deben", "debia", "debian", "debio", "debera", "deberia")}}
SAY_LEMMAS = {"decir", "creer", "pensar", "afirmar", "opinar", "asegurar", "comentar", "contar", "explicar", "sospechar", "opinar"}
SAY_FORMS = {"dice", "dijo", "dicen", "decia", "cree", "creia", "creen", "piensa", "piensan", "opina", "afirma", "asegura", "comenta", "cuenta"}


def _desc(tree: Tree, j: int) -> List[int]:
    out, todo, seen = [], list(_children(tree, j)), {j}
    while todo:
        k = todo.pop()
        if k in seen:          # un arbol predicho puede tener ciclos: sin esto el bucle no acababa nunca
            continue
        seen.add(k)
        out.append(k)
        todo.extend(_children(tree, k))
    return out


def _is_say(tree: Tree, i: int) -> bool:
    return tree[i][1] == "VERB" and (_lem(tree, i) in SAY_LEMMAS or norm(tree[i][0]) in SAY_FORMS) \
        and any(tree[j][3] == "ccomp" for j in _children(tree, i))


def triples_full(tree: Tree, resolve_rel: bool = True, entities_only: bool = False, coordination: bool = True,
                 default_subject: str = None) -> List[Dict]:
    """v3 (parche-42): coordinacion de sujetos, objetos y complementos ("Pedro y Marta viven en Madrid") y verbos coordinados
    con sujeto compartido. coordination=False reproduce el comportamiento anterior.
    v4 (parche-44): default_subject = sujeto de la frase anterior: sustituye a "el/ella" y es el sujeto de un verbo principal
    sin sujeto escrito ("Ana vive en Madrid. Trabaja en un banco")."""
    cause = next((m for m, row in enumerate(tree) if norm(row[0]) == "porque" and m >= 2), None)
    if cause is not None:                              # "Ana llora porque esta triste": hecho principal + causa (no se afirma la causa)
        root = next((k for k, row in enumerate(tree[:cause]) if row[3] == "root" or row[2] == 0), 0)
        main = [r if r[2] <= cause else (r[0], r[1], 0, "root", *r[4:]) for r in tree[:cause]] + [(".", "PUNCT", root + 1, "punct", ".")]
        base = triples_full(main, resolve_rel, entities_only, coordination, default_subject)
        forms = [w[0] for w in tree]
        clause = [k for k in range(cause + 1, len(tree)) if tree[k][1] != "PUNCT"]
        extra = []
        for t in base:
            if not clause or t.get("p", "").endswith("_que"):
                continue
            ss = _span(tree, t["si"]) if t.get("si") is not None else []
            if ss and ss[0] == 0:
                head_txt = "{s} " + " ".join(forms[k] for k in range(cause) if k not in ss)
            else:
                head_txt = " ".join(forms[:cause])
            extra.append({"s": t["s"], "p": t["p"] + "_porque", "o": "_".join(norm(tree[k][0]) for k in clause), "neg": False, "head": t["head"],
                          "si": None, "oi": None, "when": "", "when_disp": "", "when_idx": [], "q": "",
                          "template": head_txt.strip() + " porque {o}",
                          "s_disp": " ".join(forms[k] for k in ss) if ss else t["s"], "o_disp": " ".join(forms[k] for k in clause)})
        return base + extra
    out = []
    ok = ("NOUN", "PROPN") if entities_only else ("NOUN", "PROPN", "PRON")
    obj_ok = ("NOUN", "PROPN", "PRON") + (("ADJ",) if entities_only else ())

    def group(i, allowed):
        members = _conj(tree, i) if coordination else [i]
        return [m for m in members if tree[m][1] in allowed]

    embedded = set()
    for i0 in range(len(tree)):
        if _is_say(tree, i0):
            for j0 in _children(tree, i0):
                if tree[j0][3] == "ccomp":
                    embedded.update([j0] + _desc(tree, j0))

    for i, (form, upos, head, rel, *_rest) in enumerate(tree):
        if i in embedded:
            continue                                  # lo que alguien DICE no es un hecho: se guarda solo como "X dice que ..."
        kids = _children(tree, i)
        subj = _subjects_of(tree, i) if coordination else [j for j in kids if tree[j][3] in ("nsubj", "csubj")]
        if not subj and default_subject and rel == "root" and upos == "VERB":
            sj, subjects = None, [default_subject]
        else:
            if not subj:
                continue
            sj = subj[0]
            if resolve_rel and norm(tree[sj][0]) == "que" and rel == "acl" and head > 0:
                sj = head - 1                                 # "la normativa que regula": el sujeto es la normativa
            pron = bool(default_subject) and _name(tree, sj) in PRON_SUBJ      # "Él lee..." (la escuela lo etiqueta DET) / "Ella" (PRON)
            if tree[sj][1] not in ok and not pron and not _infinitive(tree, sj) and not (entities_only and _name_like_adj(tree, sj)):
                continue
            subjects = [sj] if pron or _infinitive(tree, sj) else group(sj, ok)
            if tree[sj][1] == "ADJ":
                subjects = [sj]
            if default_subject:
                subjects = [default_subject if _name(tree, k) in PRON_SUBJ else k for k in subjects]
        neg = any(tree[j][3] == "advmod" and norm(tree[j][0]) in NEG for j in kids)
        dets = [norm(tree[d][0]) for d in _children(tree, subjects[0]) if tree[d][3] == "det"] if subjects and not isinstance(subjects[0], str) else []
        quant = ""
        if set(dets) & NONE_Q:
            neg = True                                  # "Ninguna rana es mamifero"
        elif set(dets) & SOME_Q:
            quant = next(d for d in dets if d in SOME_Q)  # "Algunos pajaros vuelan": no vale para todos
        tm = when_of(tree, i)
        skip = set(tm[2]) if tm else set()
        has_cop = any(tree[j][3] == "cop" for j in kids)

        def add(sj_, p, o_idx):
            named = isinstance(sj_, str)
            out.append({"s": sj_ if named else _name(tree, sj_), "p": p, "o": "_" if o_idx is None else _name(tree, o_idx), "neg": neg, "head": i,
                        "si": None if named else sj_, "oi": o_idx, "when": tm[0] if tm else "", "when_disp": tm[1] if tm else "",
                        "when_idx": sorted(skip), "q": quant})

        found = False
        if has_cop and upos in ("NOUN", "PROPN", "ADJ"):
            for j in kids:
                if tree[j][3] == "nmod" and tree[j][1] in ("NOUN", "PROPN"):
                    base = _prep(tree, j)
                    cmp_ = [norm(tree[j2][0]) for j2 in kids if tree[j2][3] == "advmod" and norm(tree[j2][0]) in ("mas", "menos")]
                    for k in group(j, ("NOUN", "PROPN")):
                        pr = _prep(tree, k) or base
                        for sk in subjects:
                            if cmp_ and upos == "ADJ" and any(tree[m][3] == "mark" and norm(tree[m][0]) == "que" for m in _children(tree, j) + kids):
                                add(sk, f"{cmp_[0]}_{_lem(tree, i)}_que", k)          # "Luis es mas alto que Pedro"
                            else:
                                add(sk, _lem(tree, i) + ("_" + pr if pr else ""), k)
                        found = True
            if not found and upos in ("NOUN", "PROPN") and resolve_rel:
                cop_f = next(norm(tree[j][0]) for j in kids if tree[j][3] == "cop")
                for sk in subjects:
                    # "Luis esta contento": la escuela lo etiqueta NOUN, pero "estar + palabra" es un estado, no una clase
                    add(sk, "estar" if cop_f.startswith("est") else "es", i)          # "un perro es un animal"
                    if not cop_f.startswith("est") and upos == "NOUN":
                        for a in kids:
                            if tree[a][3] == "amod" and tree[a][1] == "ADJ":
                                add(sk, "ser", a)                                  # "un gorrion es un pajaro pequeno" (parche-58)
            elif not found and upos == "ADJ" and resolve_rel:
                cop = next(norm(tree[j][0]) for j in kids if tree[j][3] == "cop")
                rel_p = "estar" if cop.startswith("est") else "ser"      # parche-55: "La casa es grande" / "Ana esta cansada"
                for a in group(i, ("ADJ",)):
                    for sk in subjects:
                        add(sk, rel_p, a)
        elif upos == "VERB":
            n0 = len(out)
            aux = [norm(tree[j][0]) for j in kids if tree[j][3] == "aux" and norm(tree[j][0]) in MODAL_FORMS]
            vl = (MODAL_FORMS[aux[0]] + "_" if aux else "") + _lem(tree, i)       # "Pedro puede nadar" -> poder_nadar
            for j in kids:
                if tree[j][3] == "obj" and tree[j][1] in obj_ok:
                    # parche-38: "estudia matematicas": la escuela la etiqueta ADJ pero hace de objeto
                    for k in group(j, obj_ok):
                        for sk in subjects:
                            add(sk, vl, k)
                elif tree[j][3] in ("obl", "iobj") and tree[j][1] in ("NOUN", "PROPN") and j not in skip:
                    base = _prep(tree, j)
                    locadv = next((norm(tree[j2][0]) for j2 in kids if tree[j2][3] == "advmod" and norm(tree[j2][0]) in LOC_ADV), None)
                    for k in group(j, ("NOUN", "PROPN")):
                        pr = _prep(tree, k) or base
                        if pr in LOC_ADV:
                            pr = pr + "_de"                                   # "trabaja cerca de Madrid" (la escuela lo lee como preposicion)
                        for sk in subjects:
                            if locadv and pr == "de":                          # "vive lejos de Madrid"
                                add(sk, vl + "_" + locadv + "_de", k)
                            else:
                                add(sk, vl + ("_" + pr if pr else ""), k)
                elif tree[j][3] == "advmod" and norm(tree[j][0]) in LOC_ADV:          # "esta encima de la mesa" (parche-56)
                    for k2 in _children(tree, j):
                        if tree[k2][3] == "obl" and tree[k2][1] in ("NOUN", "PROPN"):
                            pr = _prep(tree, k2)
                            for sk in subjects:
                                add(sk, vl + "_" + norm(tree[j][0]) + ("_" + pr if pr else ""), k2)
            if _lem(tree, i) in DATIVE_VERBS and not any(f["p"] == vl + "_a" for f in out[n0:]):   # "Ana da un libro a Luis" (la escuela cuelga "a Luis" del libro)
                for j in kids:
                    if tree[j][3] == "obj":
                        for k in _children(tree, j):
                            if tree[k][3] in ("nmod", "obl", "iobj") and tree[k][1] in ("NOUN", "PROPN") and _prep(tree, k) == "a":
                                for sk in subjects:
                                    add(sk, vl + "_a", k)
            xc = [j for j in kids if tree[j][3] == "xcomp" and tree[j][1] == "VERB"]
            for j in xc:                                       # "Ana quiere comer pan" -> querer_comer
                pre = _lem(tree, i) + "_" + _lem(tree, j)
                got = False
                for k2 in _children(tree, j):
                    if tree[k2][3] == "obj" and tree[k2][1] in obj_ok:
                        for k in group(k2, obj_ok):
                            for sk in subjects:
                                add(sk, pre, k)
                                got = True
                    elif tree[k2][3] in ("obl", "iobj") and tree[k2][1] in ("NOUN", "PROPN") and k2 not in skip:
                        base = _prep(tree, k2)
                        for k in group(k2, ("NOUN", "PROPN")):
                            pr = _prep(tree, k) or base
                            for sk in subjects:
                                add(sk, pre + ("_" + pr if pr else ""), k)
                                got = True
                if not got:
                    for sk in subjects:
                        add(sk, pre, None)
            cc = [j for j in kids if tree[j][3] == "ccomp"]
            if cc and _is_say(tree, i):                        # "Pedro dice que Ana vino": se guarda lo DICHO, no como hecho
                mk = [m for m in _children(tree, cc[0]) if tree[m][3] == "mark"]
                mark_i = mk[0] if mk else cc[0]
                clause = [k for k in range(mark_i + 1, len(tree)) if tree[k][1] != "PUNCT"]
                if clause and subjects:
                    sj0 = subjects[0]
                    if isinstance(sj0, str):
                        sname = sdisp = sj0
                    else:
                        part = [k for k in _span(tree, sj0) if k < mark_i]
                        sname = "_".join(norm(tree[k][0]) for k in part)
                        sdisp = " ".join(tree[k][0] for k in part)
                    out.append({"s": sname, "p": _lem(tree, i) + "_que", "o": "_".join(norm(tree[k][0]) for k in clause), "neg": neg,
                                "head": i, "si": None, "oi": None, "when": "", "when_disp": "", "when_idx": [],
                                "template": "{s} " + tree[i][0].lower() + " que {o}", "s_disp": sdisp,
                                "o_disp": " ".join(tree[k][0] for k in clause)})
            elif len(out) == n0 and not xc and not cc:         # verbo sin complementos: "Luis llego" -> (luis, llegar, _)
                for sk in subjects:
                    add(sk, vl, None)
    return out


def triples(tree: Tree, resolve_rel: bool = True) -> List[Tuple[str, str, str]]:
    return [(t["s"], t["p"], t["o"]) for t in triples_full(tree, resolve_rel=resolve_rel)]


NP_REL = {"det", "flat", "amod", "nummod", "compound"}


def _span(tree: Tree, i: int) -> List[int]:
    """Sintagma nominal: la palabra nucleo y sus determinantes, nombres compuestos y adjetivos."""
    out, todo = {i}, [i]
    while todo:
        for j in _children(tree, todo.pop()):
            if tree[j][3] in NP_REL and j not in out:
                out.add(j); todo.append(j)
    return sorted(out)


def surface(tree: Tree, t: Dict) -> Dict:
    """Plantilla de superficie de una proposicion ("{s} vive en {o}") y como se escribian sujeto y objeto (parche-35).
    Sirve para RESPONDER con las mismas palabras que uso la persona."""
    if t.get("si") is None or any(w[3] in ("conj", "cc") for w in tree):
        return {}                                   # con coordinaciones no hay una plantilla unica fiable
    forms = [w[0] for w in tree]
    ss, os_ = _span(tree, t["si"]), (_span(tree, t["oi"]) if t.get("oi") is not None else [])
    if set(ss) & set(os_):
        return {}
    drop = {j for j in _children(tree, t["head"]) if tree[j][3] == "advmod" and norm(tree[j][0]) in NEG} | set(t.get("when_idx", []))
    toks = []
    stop = next((m for m, row in enumerate(tree) if norm(row[0]) == "porque" and m >= 2), len(forms))
    for k, f in enumerate(forms):
        if k >= stop:
            break
        if k in drop or tree[k][1] == "PUNCT":
            continue
        if k == ss[0]:
            toks.append("{s}")
        elif os_ and k == os_[0]:
            toks.append("{o}")
        elif k in ss or k in os_:
            continue
        else:
            toks.append(f if (k > 0 and tree[k][1] == "PROPN") else (f.lower() if k == 0 else f))
    text = " ".join(toks)
    text = text.replace(" de el ", " del ").replace(" a el ", " al ")

    def disp(span):
        words = [forms[k] for k in span]
        if span[0] == 0 and tree[span[0]][1] != "PROPN":
            words[0] = words[0].lower()
        return " ".join(words).replace("de el", "del")

    return {"template": text, "s_disp": disp(ss), "o_disp": disp(os_) if os_ else ""}
''',
    'src/language/fechas.py': r'''"""Fechas ABSOLUTAS (parche-53). Idea del usuario: toda expresion temporal relativa ("ayer", "el lunes", "el ano pasado")
se convierte, al aprender el hecho, en una fecha absoluta anclada a "hoy" (la fecha de la conversacion). Asi "ayer" dicho
el 6 de noviembre sigue valiendo 5 de noviembre aunque pasen los meses, y se pueden ordenar los hechos sin confusion.

Un tiempo se guarda como intervalo ISO "AAAA-MM-DD/AAAA-MM-DD" (un dia: inicio = fin).
Convenios (documentados): un dia de la semana sin mas ("el lunes") es el ultimo que ya paso; "proximo" mira al futuro;
un mes suelto es el mas reciente que ya empezo; las estaciones usan fechas del hemisferio norte.
"""
import re
from datetime import date, timedelta
from typing import Optional, Tuple

from src.language.lexicon import norm

MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
WEEKDAYS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
SEASONS = {"primavera": ((3, 21), (6, 20)), "verano": ((6, 21), (9, 22)), "otono": ((9, 23), (12, 20)), "invierno": ((12, 21), (3, 20))}
FUTURE = {"proximo", "proxima", "siguiente"}
_ABS = re.compile(r"\b(?:el\s+|del\s+|de\s+)?(\d{1,2})\s+de\s+(" + "|".join(MONTHS) + r")(?:\s+de\s+(\d{4}))?", re.I)


def _iv(a: date, b: date) -> str:
    return f"{a.isoformat()}/{b.isoformat()}"


def parse_iv(iv: str) -> Tuple[date, date]:
    a, _, b = iv.partition("/")
    return date.fromisoformat(a), date.fromisoformat(b or a)


def resolve(key: str, today: date) -> Optional[str]:
    """Clave normalizada de extract.when_of -> intervalo ISO anclado a today, o None si no se puede fijar."""
    if not key:
        return None
    if key.startswith("abs:"):
        return key[4:]
    parts = key.split("_")
    w, mods = parts[0], set(parts[1:])
    fut = bool(mods & FUTURE)
    day = {"hoy": 0, "ayer": -1, "anteayer": -2, "anoche": -1, "manana": 1}.get(w)
    if day is not None and not mods:
        d = today + timedelta(days=day)
        return _iv(d, d)
    if w in WEEKDAYS:
        k = WEEKDAYS.index(w)
        delta = (k - today.weekday()) % 7
        d = today + timedelta(days=delta or 7) if fut else today - timedelta(days=(today.weekday() - k) % 7 or 7)
        return _iv(d, d)
    if w in MONTHS:
        m = MONTHS.index(w) + 1
        y = today.year + (1 if fut and m <= today.month else 0) if fut else (today.year if m <= today.month else today.year - 1)
        end = (date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1))
        return _iv(date(y, m, 1), end)
    if re.fullmatch(r"\d{4}", w):
        return _iv(date(int(w), 1, 1), date(int(w), 12, 31))
    if w == "ano" and mods:
        y = today.year + (1 if fut else -1)
        return _iv(date(y, 1, 1), date(y, 12, 31))
    if w == "mes" and mods:
        y, m = today.year, today.month + (1 if fut else -1)
        y, m = y + (m > 12) - (m < 1), (m - 1) % 12 + 1
        return _iv(date(y, m, 1), date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1))
    if w == "semana" and mods:
        mon = today - timedelta(days=today.weekday()) + timedelta(days=7 if fut else -7)
        return _iv(mon, mon + timedelta(days=6))
    if w in SEASONS:
        (m1, d1), (m2, d2) = SEASONS[w]
        for y in (today.year, today.year - 1, today.year - 2):
            a = date(y, m1, d1)
            b = date(y + (m2 < m1), m2, d2)
            if a <= today:
                return _iv(a, b)
    return None


def month_name(m: int) -> str:
    return MONTHS[m - 1]


def fmt(iv: str) -> str:
    """Intervalo ISO -> texto en espanol: "5 de noviembre de 2026", "octubre de 2026", "2020"."""
    a, b = parse_iv(iv)
    if a == b:
        return f"{a.day} de {month_name(a.month)} de {a.year}"
    if a.day == 1 and (b + timedelta(days=1)).day == 1 and a.month == b.month and a.year == b.year:
        return f"{month_name(a.month)} de {a.year}"
    if a == date(a.year, 1, 1) and b == date(a.year, 12, 31):
        return str(a.year)
    return f"del {a.day} de {month_name(a.month)} de {a.year} al {b.day} de {month_name(b.month)} de {b.year}"


def extract_abs(text: str, today: date):
    """Quita de la frase una fecha escrita ("el 5 de noviembre [de 2025]") -> (frase limpia, intervalo, como se escribio) o (texto, None, "").
    Sin ano, vale el ano del ancla; si eso cae en el futuro, el ano anterior (convenio del pasado)."""
    m = _ABS.search(text)
    if not m:
        return text, None, ""
    d, mo, y = int(m.group(1)), MONTHS.index(m.group(2).lower()) + 1, m.group(3)
    try:
        dt = date(int(y), mo, d) if y else date(today.year, mo, d)
        if not y and dt > today:
            dt = date(today.year - 1, mo, d)
    except ValueError:
        return text, None, ""
    clean = (text[:m.start()] + text[m.end():]).replace("  ", " ")
    clean = re.sub(r"\s+([.?!,])", r"\1", clean).strip()
    return clean, _iv(dt, dt), m.group(0).strip()


def before(iv: str, ref: str) -> bool:
    return parse_iv(iv)[1] < parse_iv(ref)[0]


def after(iv: str, ref: str) -> bool:
    return parse_iv(iv)[0] > parse_iv(ref)[1]


def contains(iv: str, ref: str) -> bool:
    a, b = parse_iv(iv)
    c, d = parse_iv(ref)
    return a <= c and d <= b or c <= a and b <= d
''',
    'src/language/irregulares.py': r'''"""Formas irregulares muy comunes -> lema (parche-55). Las deduce mal el lematizador de la escuela ("duerme" -> "duermar");
con esto la base es correcta desde el principio y ENTENDI solo tiene que corregir lo raro."""
_V = {
    "dormir": "duermo duermes duerme dormimos duermen durmio durmieron dormia",
    "poder": "puedo puedes puede podemos pueden pudo pudieron podia",
    "querer": "quiero quieres quiere queremos quieren quiso quisieron queria",
    "venir": "vengo vienes viene venimos vienen vino vinieron venia",
    "hacer": "hago haces hace hacemos hacen hizo hicieron hacia",
    "decir": "digo dices dice decimos dicen dijo dijeron decia",
    "tener": "tengo tienes tiene tenemos tienen tuvo tuvieron tenia",
    "saber": "se sabes sabe sabemos saben supo supieron sabia",
    "ver": "veo ves ve vemos ven vio vieron veia",
    "dar": "doy das da damos dan dio dieron daba",
    "poner": "pongo pones pone ponemos ponen puso pusieron ponia",
    "salir": "salgo sales sale salimos salen salio salieron salia",
    "volver": "vuelvo vuelves vuelve volvemos vuelven volvio volvieron volvia",
    "jugar": "juego juegas juega jugamos juegan jugo jugaron jugaba",
    "morir": "muero mueres muere morimos mueren murio murieron moria",
    "pedir": "pido pides pide pedimos piden pidio pidieron pedia",
    "seguir": "sigo sigues sigue seguimos siguen siguio siguieron seguia",
    "sentir": "siento sientes siente sentimos sienten sintio sintieron sentia",
    "empezar": "empiezo empiezas empieza empezamos empiezan empezo empezaron",
    "encontrar": "encuentro encuentras encuentra encontramos encuentran",
    "pensar": "pienso piensas piensa pensamos piensan",
    "contar": "cuento cuentas cuenta contamos cuentan",
    "recordar": "recuerdo recuerdas recuerda recordamos recuerdan",
    "cerrar": "cierro cierras cierra cerramos cierran",
    "abrir": "abro abres abre abrimos abren abrio abrieron",
    "correr": "corro corres corre corremos corren corrio corrieron",
    "comer": "como comes come comemos comen comio comieron",
    "vivir": "vivo vives vive vivimos viven vivio vivieron",
    "ir": "voy vas va vamos van fue fueron iba",
    "llegar": "llego llegas llega llegamos llegan llego llegaron",
    "nadar": "nado nadas nada nadamos nadan nado nadaron",
    "llover": "llueve llovio",
    "cenar": "ceno cenas cena cenamos cenan ceno cenaron",
    "sonreir": "sonrio sonries sonrie sonreimos sonrien sonrio sonrieron",
    "volar": "vuelo vuelas vuela volamos vuelan volo volaron volaba",
    "oler": "huele huelen olio",
    "llorar": "lloro lloras llora lloramos lloran",
    "caer": "caigo caes cae caemos caen cayo cayeron",
    "oir": "oigo oyes oye oimos oyen oyo oyeron",
    "traer": "traigo traes trae traemos traen trajo trajeron",
    "conocer": "conozco conoces conoce conocemos conocen conocio",
    "producir": "produzco produces produce producimos producen produjo",
}
IRREG = {}
for _lemma, _forms in _V.items():
    for _f in _forms.split():
        IRREG.setdefault(_f, _lemma)
IRREG.pop("se", None)          # "se" es casi siempre pronombre
IRREG.pop("como", None)        # "como" casi siempre es adverbio/conjuncion
IRREG.pop("nada", None)        # "nada" es pronombre en la mayoria de los casos
IRREG.pop("va", None) if False else None
''',
    'src/language/lexicon.py': r'''"""Lexico del oido: normalizacion del texto, frases de los predicados y trozos de vocabulario."""
import re
import unicodedata

PREPS = {"de", "a", "que", "con", "en", "por", "para", "sobre", "entre", "hacia"}
NO_EAR = {"ES", "SIN_CONCLUSION", "NINGUNA", "REGLA_HEREDA"}
ES_ALIASES = ["es un", "es una", "son", "era un", "era una", "eran"]   # "ES" se reconoce por estos giros

# (frase, tipo)  A = "es <frase>" (nombre/adjetivo + preposicion) | V = verbo
BASE_PHRASES = {
    "MAYOR_QUE": ("mayor que", "A"), "MENOR_QUE": ("menor que", "A"), "SUPERIOR_A": ("superior a", "A"),
    "ANTERIOR_A": ("anterior a", "A"), "POSTERIOR_A": ("posterior a", "A"),
    "CAUSA": ("causa", "V"), "PRODUCE": ("produce", "V"), "PROVOCA": ("provoca", "V"), "ORIGINA": ("origina", "V"),
    "POSEE": ("posee", "V"), "EXHIBE": ("exhibe", "V"), "MUESTRA": ("muestra", "V"), "ADQUIERE": ("adquiere", "V"),
    "HEREDA": ("hereda", "V"), "IMPLICA": ("implica", "V"), "TIENE_RASGO": ("tiene como rasgo", "V"),
    "DERIVA_EN": ("deriva en", "V"), "CAE_HACIA": ("cae hacia", "V"), "EXPUESTO_A": ("expuesto a", "A"),
    "SOMETIDO_A": ("sometido a", "A"), "LIBERADO_EN": ("liberado en", "A"), "CAMBIA_A": ("cambia a", "V"),
    "CONTRADICE": ("contradice", "V"), "TIENE_BIYECCION_CON": ("tiene biyeccion con", "V"),
}


def norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def tokenize(text: str):
    t = re.sub(r"\bdel\b", "de el", norm(text))
    t = re.sub(r"\bal\b", "a el", t)
    return re.findall(r"[a-z0-9_]+|[,.;:!?]", t)


def phrase_for(name: str):
    """Frase y tipo de un predicado. Si no esta en la tabla se deriva del nombre (PADRE_DE -> 'padre de')."""
    if name in BASE_PHRASES:
        return BASE_PHRASES[name]
    words = name.lower().split("_")
    kind = "A" if len(words) >= 2 and words[-1] in PREPS else "V"
    return " ".join(words), kind
''',
    'src/language/lm.py': r'''"""Preentrenamiento del oido con TEXTO CORRIENTE (parche-26): adivinar palabras ocultas.

Como el "siguiente token" de un LLM, pero bidireccional: se oculta ~15 % de las palabras de cada frase del libro y
el oido debe adivinarlas a partir del resto. Para hacerlo tiene que aprender que palabras se parecen, que clase
de palabra va en cada hueco (nombre, verbo, adjetivo...) y como se ordena el espanol. No necesita etiquetas.
"""
from __future__ import annotations

import json
import os
import random
import zlib
from collections import Counter
from typing import List, Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F

from .book import sentences
from .ear import MAXLEN, encode_batch
from .lexicon import tokenize

PUNCT = set(",.;:!?")


def load_sentences(path="data/libro.txt", min_tokens=5, max_tokens=MAXLEN - 2) -> List[List[str]]:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    out = []
    for s in sentences(text, max_words=30):
        t = tokenize(s)
        if min_tokens <= len(t) <= max_tokens:
            out.append(t)
    return out


def is_heldout(tokens: Sequence[str]) -> bool:
    return zlib.crc32(" ".join(tokens).encode()) % 10 == 0          # 10 % de las frases, fijo y reproducible


def build_vocab(train: Sequence[Sequence[str]], size=8000, min_count=2) -> List[str]:
    c = Counter(w for t in train for w in t if w not in PUNCT)
    return [w for w, n in c.most_common(size) if n >= min_count]


class LMHead(nn.Module):
    """Adivina la palabra oculta entre las V mas frecuentes del libro (las demas no puntuan)."""

    def __init__(self, d: int, vocab: Sequence[str]):
        super().__init__()
        self.vocab = list(vocab)
        self.index = {w: i for i, w in enumerate(self.vocab)}
        self.proj = nn.Sequential(nn.Linear(d, d), nn.GELU(), nn.Linear(d, len(self.vocab)))

    def forward(self, h):
        return self.proj(h)

    def save(self, path):
        torch.save({"vocab": self.vocab, "state": self.state_dict()}, path)

    @staticmethod
    def load(path, d, device="cpu"):
        blob = torch.load(path, map_location="cpu")
        head = LMHead(d, blob["vocab"])
        head.load_state_dict(blob["state"])
        return head.to(device)


def mask_batch(batch: Sequence[Sequence[str]], head: LMHead, rng: random.Random, p=0.15, device="cpu"):
    feat, ids, mask = encode_batch(batch, device)
    B, T = mask.shape
    hide = torch.zeros(B, T, dtype=torch.bool)
    target = torch.full((B, T), -100, dtype=torch.long)
    for i, toks in enumerate(batch):
        cand = [j for j, w in enumerate(toks[:T]) if w not in PUNCT]
        k = max(1, int(round(p * len(cand))))
        for j in rng.sample(cand, min(k, len(cand))):
            hide[i, j] = True
            target[i, j] = head.index.get(toks[j], -100)
    return feat, mask, hide.to(device), target.to(device)


def lm_loss(ear, head: LMHead, batch, rng, device="cpu", p=0.15):
    feat, mask, hide, target = mask_batch(batch, head, rng, p, device)
    h, _ = ear(feat, mask, hide=hide)
    logits = head(h)
    if (target != -100).sum() == 0:
        return logits.sum() * 0.0, 0, 0
    sel = target != -100
    loss = F.cross_entropy(logits[sel], target[sel])
    acc = (logits[sel].argmax(-1) == target[sel]).float().mean().item()
    return loss, acc, int(sel.sum())


@torch.no_grad()
def evaluate(ear, head, data, device="cpu", seed=123, batch=128, rounds=3):
    """Acierto (top-1 y top-5) adivinando palabras ocultas de frases NO vistas, y la linea base 'siempre la mas frecuente'."""
    ear.eval()
    rng = random.Random(seed)
    top1 = top5 = n = 0
    for _ in range(rounds):
        for b in range(0, len(data), batch):
            feat, mask, hide, target = mask_batch(data[b:b + batch], head, rng, 0.15, device)
            h, _ = ear(feat, mask, hide=hide)
            sel = target != -100
            if sel.sum() == 0:
                continue
            lg = head(h)[sel]
            tg = target[sel]
            top1 += (lg.argmax(-1) == tg).sum().item()
            top5 += (lg.topk(5, dim=-1).indices == tg[:, None]).any(-1).sum().item()
            n += len(tg)
    return top1 / max(n, 1), top5 / max(n, 1), n
''',
    'src/language/online_ear.py': r'''"""Correccion del oido DESDE LA CONVERSACION (parche-16).

Cuando el oido entiende mal una frase, el usuario escribe  ENTENDI s p o [NEGADO].
La pareja (frase, significado) se guarda como ejemplo real y el oido se ajusta con:
  - esos ejemplos reales (repetidos, porque son pocos),
  - un repaso de frases generadas (para no olvidar lo ya sabido),
y se REVIERTE si el repaso baja mas de 2 puntos (misma idea que el canario del razonador).
"""
import copy
import json
import os
import random
import torch
from .corpus import HEADS_TRAIN, VERBS_TRAIN, PredicatePool, base_pool, es_pool, make, make_negatives
from .ear import key, predict
from .lexicon import tokenize
from .training import batch_loss


class EarLearner:
    def __init__(self, parser, device="cpu", examples_path="memory/oido_ejemplos.jsonl", ckpt="checkpoints/ear_online.pt"):
        self.parser = parser
        self.ear = parser.ear
        self.device = device
        self.examples_path = examples_path
        self.ckpt = ckpt
        pool = base_pool() + es_pool() + PredicatePool(HEADS_TRAIN, VERBS_TRAIN).items
        self.replay = make(1500, pool, seed=777) + make_negatives(400, seed=779)
        self.probe = make(300, pool, seed=778)
        self.texts = sorted({p[1] for p in pool})
        self.cands = [(p[0], p[1]) for p in {q[1]: q for q in pool}.values()]
        self.examples = self._load()

    def _load(self):
        if not os.path.exists(self.examples_path):
            return []
        with open(self.examples_path, encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def build_example(self, sentence, triple, negated, phrase):
        toks = tokenize(sentence)
        s, p, o = triple
        tags = [0] * len(toks)
        found = False
        for i, t in enumerate(toks):
            if t == s.lower():
                tags[i] = 1
            elif t == o.lower():
                tags[i] = 2
            found = found or t in (s.lower(), o.lower())
        if "son" in phrase.split() and phrase == "son":      # plurales: el nombre aparece con 's'
            for i, t in enumerate(toks):
                if t.startswith(s.lower()) and tags[i] == 0:
                    tags[i] = 1
                elif t.startswith(o.lower()) and tags[i] == 0:
                    tags[i] = 2
        if 1 not in tags or 2 not in tags:
            return None
        return {"tokens": toks, "tags": tags, "pred": p, "text": phrase, "neg": bool(negated), "triple": [s, p, o]}

    def accuracy(self):
        outs = predict(self.ear, [x["tokens"] for x in self.probe], self.cands, self.device)
        return sum((o["subject"], o["predicate"], o["object"], o["negated"]) == (*x["triple"], x["neg"])
                   for o, x in zip(outs, self.probe)) / len(self.probe)

    def learn(self, example, steps=60, lr=3e-4):
        self.examples.append(example)
        before = self.accuracy()
        snapshot = copy.deepcopy(self.ear.state_dict())
        rng = random.Random(len(self.examples))
        opt = torch.optim.AdamW(self.ear.parameters(), lr=lr, weight_decay=0.0)
        texts = sorted(set(self.texts) | {x["text"] for x in self.examples})
        self.ear.train()
        for _ in range(steps):
            real = [rng.choice(self.examples) for _ in range(16)] + [example] * 8
            batch = real + rng.sample(self.replay, 64)
            loss, _ = batch_loss(self.ear, batch, texts, rng, self.device)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(self.ear.parameters(), 1.0)
            opt.step()
        self.ear.eval()
        after = self.accuracy()
        out = predict(self.ear, [example["tokens"]], self.cands + [(example["pred"], example["text"])], self.device)[0]
        got = (out["subject"], out["predicate"], out["object"], out["negated"]) == (*example["triple"], example["neg"])
        accepted = (before - after) <= 0.02
        if not accepted:
            self.ear.load_state_dict(snapshot)
            self.examples.pop()
        else:
            os.makedirs(os.path.dirname(self.examples_path) or ".", exist_ok=True)
            with open(self.examples_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(example, ensure_ascii=False) + "\n")
            os.makedirs(os.path.dirname(self.ckpt) or ".", exist_ok=True)
            torch.save(self.ear.state_dict(), self.ckpt)
        return {"accepted": accepted, "learned": got, "repaso_antes": before, "repaso_despues": after}
''',
    'src/language/qa.py': r'''"""Preguntas y respuestas en espanol (parche-35, Fase 1). Sin LLM.

Una pregunta se reescribe como afirmacion con un hueco ("Xqx") y se lee con la MISMA escuela que lee las afirmaciones:
  "Quien escribio una novela?"   -> "Xqx escribio una novela."    (hueco = sujeto)
  "Que escribio Marta?"          -> "Marta escribio Xqx."         (hueco = objeto)
  "Vive Pedro en Madrid?"        -> "Pedro vive en Madrid."       (si/no)
Luego se busca en la memoria (con la misma tolerancia de relacion que el test de conversacion) y, si no esta, se intenta
DEDUCIR con las lecciones aprendidas. Se contesta con las palabras que uso la persona (plantillas y nombres guardados).
Cuando no se sabe, se dice "no lo se" (mundo abierto): no se inventa.
"""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .lexicon import norm

MODAL_VERBS = {"puede", "pueden", "debe", "deben", "quiere", "quieren", "podia", "queria", "pudo", "debia"}
HOLE = "Xqx"
HOLES = ("Xqx", "Zurita", "Bertoldo")      # parche-41: si la escuela no lee uno, se prueba otro nombre inventado
DETS = {"el", "la", "los", "las", "un", "una", "unos", "unas", "su", "sus", "mi", "mis", "tu", "tus"}
WH = {"quien", "quienes", "que", "cual", "cuales"}
ADV = {"donde": "en", "como": "con"}


def template_from(raw: str, s: str, o: str):
    """Plantilla "{s} es hijo de {o}" sacada de la frase tal como la dijo la persona (para frases que entiende el oido de plantillas
    o las dos mitades de una regla). Devuelve (plantilla, como_se_escribia_s, como_se_escribia_o) o None."""
    words = re.findall(r"\w+|[^\w\s]", raw)
    low = [norm(w) for w in words]
    si = [i for i, w in enumerate(low) if w == norm(s)]
    oi = [i for i, w in enumerate(low) if w == norm(o)]
    if not si or not oi or si[0] == oi[0]:
        return None
    toks = []
    for i, w in enumerate(words):
        if not re.match(r"\w", w):
            continue
        toks.append("{s}" if i == si[0] else "{o}" if i == oi[0] else (w.lower() if i == 0 else w))
    text = " ".join(toks).replace(" de el ", " del ").replace(" a el ", " al ")
    return text, words[si[0]], words[oi[0]]


def is_question(text: str) -> bool:
    t = text.strip()
    return t.startswith("¿") or t.endswith("?")


def pred_key(p: str) -> str:
    head, _, prep = norm(p).partition("_")
    head = {"tia": "tio"}.get(head, head)                       # tio/tia, hijo/hija... (parche-59)
    return head[:3] + "|" + ("" if prep == "a" else prep)      # la "a" personal (conocer a Pablo) no distingue la relacion


def same_pred(a: str, b: str) -> bool:
    if pred_key(a) != pred_key(b):
        return False
    ha, hb = a.lower().partition("_")[0], b.lower().partition("_")[0]
    if ha != hb and ha[-2:] in ("ar", "er", "ir") and hb[-2:] in ("ar", "er", "ir") and ha[-2:] != hb[-2:]:
        return False                                  # venir / vender: mismas 3 letras, verbos distintos
    return True


def _words(text: str) -> List[str]:
    return re.findall(r"\w+", text.replace("¿", " ").replace("?", " "), flags=re.U)


def rewrite(question: str, hole: str = HOLE) -> Tuple[List[str], str]:
    cands, kind = _rewrite(question, hole)
    caps = [c[:1].upper() + c[1:] for c in cands if c[:1].islower()]
    return cands + [c for c in caps if c not in cands], kind


def _rewrite(question: str, hole: str = HOLE) -> Tuple[List[str], str]:
    """Devuelve (candidatos de afirmacion, tipo). tipo: 'sujeto' | 'objeto' | 'si_no'. Lista vacia si no se sabe."""
    w = _words(question)
    if not w:
        return [], ""
    low = [norm(x) for x in w]
    prep = ""
    i = 0
    if low[0] in ("a", "de", "con", "en", "para", "por") and len(low) > 1 and low[1] in WH:
        prep, i = w[0].lower(), 1
    if low[0] == "cuando" and len(w) >= 3:                       # "Cuando compro Pedro pan?" -> frase sin el "cuando"
        rest = w[1:]
        cands = [" ".join(rest) + "."]
        if len(rest) >= 3 and norm(rest[1]) in DETS:
            cands.append(" ".join([rest[1], rest[2], rest[0].lower()] + rest[3:]) + ".")
        cands.append(" ".join([rest[1], rest[0].lower()] + rest[2:]) + ".")
        return cands, "cuando"
    if low[i] in ADV and prep == "":
        prep, hole_at = ADV[low[i]], i
        rest = w[i + 1:]
        if len(rest) < 2:
            return [], ""
        # "Donde estudia Luis musica?" -> "Luis estudia musica en Xqx" (el verbo detras del sujeto, el hueco al final)
        return [" ".join([rest[1], rest[0]] + rest[2:] + [prep, hole]) + "."], "objeto"
    if low[i] in WH:
        rest = w[i + 1:]
        if not rest:
            return [], ""
        pre = [prep] if prep else []
        if i == 0 and low[0] in ("quien", "quienes") and low[1:2] == ["es"] and len(rest) == 2 and rest[1][:1].isupper():
            return [" ".join(rest[1:] + [rest[0], hole]) + "."], "objeto"           # "Quien es Marta?" -> definicion de Marta
        if i == 0 and not prep:
            # "Quien escribio X?" -> hueco sujeto ; "Que escribio Marta?" -> hueco objeto
            cands = []
            if low[0] in ("quien", "quienes"):
                cands.append(" ".join([hole] + rest) + ".")
            if len(rest) >= 3 and norm(rest[0]) in MODAL_VERBS and norm(rest[1])[-2:] in ("ar", "er", "ir") and low[0] not in ("quien", "quienes"):
                cands.append(" ".join([rest[2], rest[0], rest[1], hole] + rest[3:]) + ".")      # "Que quiere comer Ana?"
            if len(rest) >= 2:
                cands.append(" ".join(rest[1:] + [rest[0], hole]) + ".")
            return cands, "sujeto" if low[0] in ("quien", "quienes") else "objeto"
        if len(rest) >= 2:                                     # "A quien llamo Pedro?" -> "Pedro llamo a Xqx"
            return [" ".join(rest[1:] + [rest[0]] + pre + [hole]) + "."], "objeto"
        return [], ""
    # si / no: la frase tal cual, y la version con el verbo detras del sujeto ("Vive Pedro en Madrid")
    cands = [" ".join(w) + "."]
    if len(w) >= 3 and norm(w[1]) in DETS:                      # "Ensena la maestra matematicas" -> "la maestra ensena matematicas"
        cands.append(" ".join([w[1], w[2], w[0].lower()] + w[3:]) + ".")
    if len(w) >= 2:
        cands.append(" ".join([w[1], w[0].lower()] + w[2:]) + ".")
    if len(w) >= 3 and norm(w[0]) in ("es", "esta", "son", "estan", "era", "estaba"):                  # "Esta triste Ana" -> "Ana esta triste"
        cands.append(" ".join([w[2], w[0].lower(), w[1]] + w[3:]) + ".")
    if len(w) >= 3 and norm(w[0]) in MODAL_VERBS and norm(w[1])[-2:] in ("ar", "er", "ir"):       # "Debe estudiar Luis matematicas"
        cands.append(" ".join([w[2], w[0].lower(), w[1]] + w[3:]) + ".")
    return cands, "si_no"


from src.reasoning.lessons import canon


class QA:
    """memory: MemoryStore (con .facts, .surface, .display). parse: frase -> lista de dicts {s,p,o,neg} o None.
    deduce: opcional, (lista de hechos (s,p,o) sin negar) -> conjunto de (s,p,o) deducidos."""

    def __init__(self, memory, parse: Callable[[str], Optional[List[Dict]]],
                 deduce: Optional[Callable[[Sequence[Tuple[str, str, str]]], set]] = None):
        self.m, self.parse, self.deduce = memory, parse, deduce
        self._tpl = None
        self._alts = []
        self.support = {}

    # ---- lectura de la pregunta ------------------------------------
    def read(self, question: str):
        kind = ""
        for hole in HOLES:
            cands, kind = rewrite(question, hole)
            alts = []
            for c in cands:
                found = self.parse(c)
                if not found:
                    continue
                for t in found:
                    if kind in ("si_no", "cuando"):
                        alts.append(t)
                        if len(alts) == 1:
                            self._alts = alts            # todas las lecturas posibles; answer() prefiere la que encaja con la memoria
                        continue
                    if hole.lower() in (t["s"], t["o"]):
                        t = dict(t)
                        for k in ("s", "o"):
                            if t[k] == hole.lower():
                                t[k] = norm(HOLE)           # el resto del codigo usa un unico nombre de hueco
                        return ("sujeto" if t["s"] == norm(HOLE) else "objeto"), t
            if kind in ("si_no", "cuando"):
                if alts:
                    for a_ in alts:                          # "Un cuadrado es una figura": dos sustantivos, no adjetivo (parche-59)
                        if kind == "si_no" and a_["p"] == "ser" and all((a_.get(k) or "").lower().startswith(("un ", "una ", "el ", "la ", "los ", "las ")) for k in ("s_disp", "o_disp")):
                            a_["p"] = "es"
                    a0 = alts[0]
                    ind = lambda d: (d or "").lower().startswith(("un ", "una "))
                    if kind == "si_no" and a0["p"] in ("es", "ser") and ind(a0.get("s_disp")) and ind(a0.get("o_disp")) \
                            and a0.get("template", "").startswith("es {o} {s}"):
                        sw = dict(a0)                       # "¿Es un A un B?": A es el sujeto (parche-58)
                        sw["s"], sw["o"], sw["s_disp"], sw["o_disp"] = a0["o"], a0["s"], a0["o_disp"], a0["s_disp"]
                        sw["template"] = "{s} es {o}"
                        self._alts = [sw, a0]
                        return kind, sw
                    return kind, a0
                break
        return kind, None

    # ---- memoria ----------------------------------------------------
    def _facts(self, neg=False):
        return [(f["s"], f["p"], f["o"]) for f in self.m.facts if bool(f.get("neg", False)) == neg]

    def _whens(self, fact):
        """[(clave, como se dijo)] de las veces que se guardo ese hecho (no negado)."""
        return [(f.get("when", ""), f.get("when_disp", "")) for f in self.m.facts
                if (f["s"], f["p"], f["o"]) == tuple(fact) and not f.get("neg")]

    def _today(self):
        from datetime import date
        return getattr(self.m, "today", None) or date.today()

    def _when_ok(self, fact, when):
        """El hecho se dijo con ese tiempo: misma clave, o fechas absolutas que se contienen ("ayer" = "el 5 de noviembre")."""
        from src.language.fechas import resolve, contains
        want = resolve(when, self._today())
        for f in self.m.facts:
            if (f["s"], f["p"], f["o"]) != tuple(fact) or f.get("neg"):
                continue
            if f.get("when", "") == when:
                return True
            if want and f.get("when_abs") and contains(f["when_abs"], want):
                return True
        return False

    def _q(self, fact):
        return next((f.get("q") for f in self.m.facts if (f["s"], f["p"], f["o"]) == tuple(fact) and not f.get("neg")), "")

    def _abs_of(self, fact):
        for f in self.m.facts:
            if (f["s"], f["p"], f["o"]) == tuple(fact) and not f.get("neg") and f.get("when_abs"):
                return f["when_abs"], f.get("when", "")
        return None, ""

    # ---- estados, acciones y lo que dicen otros (parche-55) --------------
    def _subject_in(self, words):
        """Nombres de la memoria que aparecen en las palabras ("la casa" -> CASA)."""
        toks = {canon(w.upper()) for w in words if w not in DETS}
        return {f["s"] for f in self.m.facts if canon(f["s"]) in toks}

    def special(self, question):
        import re
        t = re.sub(r"\s+", " ", re.sub(r"[¡!¿?.,;:]", " ", norm(question))).strip()
        facts = [f for f in self.m.facts]
        def says(fs):
            out = []
            for f in fs:
                x = self.say((f["s"], f["p"], f["o"]), neg=bool(f.get("neg"))) + "."
                if x not in out:
                    out.append(x)
            return " ".join(out[:6])
        m = re.fullmatch(r"que (?:es|son) ((?:un|una|el|la|los|las) \w+)", t)
        if m and not getattr(self, "_in_past", False):
            # "¿Que es un triangulo?": se contesta con lo que la memoria sabe (guardado o deducido), sin depender de como la escuela lea la pregunta
            names = sorted(self._subject_in(m.group(1).split()))
            if names:
                nm = names[0]
                objs = [f["o"] for f in facts if f["s"] == nm and f["p"] == "ES" and not f.get("neg")]
                try:
                    objs += [o_ for (_, _, o_) in self.derived(nm, "ES", None)]
                except Exception:
                    pass
                objs = list(dict.fromkeys(objs))
                if objs:
                    def cls(o_):
                        d_ = self._disp(o_).lower()
                        return d_ if re.match(r"(un|una)\s", d_) else ("una " if o_.endswith("A") else "un ") + d_
                    art = m.group(1).split()[0]
                    subj = self._disp(nm).lower()
                    subj = subj if re.match(r"(un|una|el|la|los|las)\s", subj) else f"{art} {subj}"
                    return f"{subj.capitalize()} es {' y '.join(cls(o_) for o_ in objs[:3])}."
        m = re.fullmatch(r"de que color (?:es|son|era) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            colors = {f["s"] for f in facts if f["p"] == "ES" and canon(f["o"]) == "COLOR"}
            fs = [f for f in facts if f["s"] in names and f["p"] in ("SER", "ESTAR") and f["o"] in colors | {c.replace("O", "A") for c in colors}
                  or (f["s"] in names and f["p"] in ("SER", "ESTAR") and any(norm(f["o"])[:-1] == c[:-1].lower() for c in colors))]
            return says(fs) if fs else "No lo sé."
        m = re.fullmatch(r"para que (?:sirve|sirven|se usa|se usan|se utiliza|se utilizan) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and f["p"] == "SERVIR_PARA"]
            return says(fs) if fs else "No lo sé."
        m = re.fullmatch(r"que (?:sirve|sirven|se usa|se usan|se utiliza|se utilizan) para (.+)", t)
        if m:
            key = "_".join(m.group(1).split()).upper()
            fs = [f for f in facts if f["p"] == "SERVIR_PARA" and canon(f["o"]) == canon(key)]
            return says(fs) if fs else "No lo sé."
        m = re.fullmatch(r"es (\w+) (?:lo contrario|lo opuesto|el contrario|el opuesto) de (\w+)", t)
        if m:
            from src.reasoning.coherence import opposite
            if opposite(m.group(1), m.group(2), getattr(self.m, "opposites", [])):
                return f"Sí, {m.group(1)} es lo contrario de {m.group(2)}."
            return "No lo sé."
        m = re.fullmatch(r"por que (.+)", t)
        if m:
            words = m.group(1).split()
            names = self._subject_in(words)
            fs = [f for f in facts if f["s"] in names and f["p"].endswith("_PORQUE") and any(norm(w)[:3] == f["p"][:3].lower() for w in words)]
            return says(fs) if fs else "No lo sé."
        m = re.fullmatch(r"(?:a |de |con |en |para )?cuant[oa]s (.+)", t)
        if m:
            words = m.group(1).split()
            tener = [k for k, w in enumerate(words) if w in ("tiene", "tienen", "tuvo", "tenia", "tendra")]
            if tener:
                noun = words[tener[0] - 1] if tener[0] else ""
                names = self._subject_in(words[tener[0] + 1:])
                stem = lambda x: re.sub(r"(os|as|es|o|a|e|s)$", "", x.lower())
                fs = [f for f in facts if f["s"] in names and f["p"].startswith("TENER") and not f.get("neg")
                      and any(stem(part) == stem(noun) for part in norm(f["o"]).split("_"))]
                return says(fs) if fs else "No lo sé."
            for pat in (r"(?i)cuánt[oa]s(?:\s+\w+)?", r"(?i)cuánt[oa]s"):         # con o sin sustantivo ("cuantos hijos" / "cuantos")
                q2 = re.sub(pat, "qué", question, count=1)
                kind, tt = self.read(q2)
                if tt and kind in ("objeto", "sujeto"):
                    s_ = None if tt["s"] == norm(HOLE) else tt["s"]
                    o_ = None if tt["o"] == norm(HOLE) else tt["o"]
                    hits = self.lookup(s_, tt["p"], o_)
                    vals = list(dict.fromkeys(f[2] if kind == "objeto" else f[0] for f in hits))
                    if vals:
                        return f"{len(vals)}: " + ", ".join(self._disp(v) for v in vals) + "."
            return "No lo sé."
        m = re.fullmatch(r"donde \w+ (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and not f.get("neg") and any("_" + w in f["p"] for w in ("ENCIMA", "DEBAJO", "DENTRO", "FUERA", "CERCA", "LEJOS", "DELANTE", "DETRAS", "JUNTO", "ENFRENTE", "ALREDEDOR"))]
            if fs:
                return says(fs)
        m = re.fullmatch(r"que (?:hace|hizo|ha hecho|esta haciendo|hacia) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and not f.get("neg") and f["p"] not in ("ES",)]
            return says(fs) if fs else None
        m = re.fullmatch(r"como (?:es|esta|son|estan|era|estaba|fue) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and f["p"] in ("SER", "ESTAR")]
            return says(fs) if fs else None
        m = re.fullmatch(r"es|(?:es|esta|son|estan|era|estaba) (.+)", t)
        if m and m.group(1):
            words = m.group(1).split()
            names = self._subject_in(words)
            fs = [f for f in facts if f["s"] in names and f["p"] in ("SER", "ESTAR")]
            if fs:
                subj = {canon(x.upper()) for x in words if canon(x.upper()) in {canon(f["s"]) for f in fs}}
                adjs = [w for w in words if w not in DETS and canon(w.upper()) not in subj]
                stem = lambda x: re.sub(r"(os|as|es|o|a|e|s)$", "", x.lower())
                hit = [f for f in fs if any(stem(a) == stem(norm(f["o"])) for a in adjs)]
                if hit:
                    f = hit[0]
                    return ("No. " if f.get("neg") else "Sí. ") + says([f])
                if any(w in DETS for w in words[1:]):            # "¿Es un gorrión un pájaro?": no es adjetivo, que lo vea la ruta normal
                    return None
                return "Eso no me consta; solo sé " + says([f for f in fs if not f.get("neg")][:3] or fs[:3])
            return None
        m = re.fullmatch(r"quien (?:es|esta|son|estan|era|estaba) (.+)", t)
        if m:
            stem = lambda x: re.sub(r"(os|as|es|o|a|e|s)$", "", x.lower())
            words = [w for w in m.group(1).split() if w not in DETS]
            hit = [f for f in facts if f["p"] in ("SER", "ESTAR") and not f.get("neg") and any(stem(w) == stem(norm(f["o"])) for w in words)]
            if hit:
                return says(hit)
        m = re.fullmatch(r"que (?:dice|dijo|cree|creia|piensa|opina|afirma|asegura|comenta|cuenta) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and f["p"].endswith("_QUE")]
            return says(fs) if fs else None
        m = re.fullmatch(r"quien (?:dice|dijo|cree|piensa|opina|afirma|asegura|comenta|cuenta) que (.+)", t)
        if m:
            key = "_".join(m.group(1).split())
            fs = [f for f in facts if f["p"].endswith("_QUE") and f["o"].lower() == key]
            return says(fs) if fs else None
        return None

    def timeline(self, question):
        """Preguntas de orden: "que paso primero / ultimo / antes de X / despues de X" con fechas absolutas (parche-53)."""
        import re
        from src.language.fechas import extract_abs, resolve, before, after, parse_iv, fmt
        q = norm(question).strip(" ¿?.!")
        m = re.fullmatch(r"que (?:paso|ocurrio|sucedio|hice|hizo)\s*(primero|ultimo|al final|antes|despues)?(?:\s+(?:de|del)\s+(.+))?", q)
        if not m:
            return None
        mode, ref = m.group(1) or "", m.group(2)
        dated = []
        seen = set()
        for f in self.m.facts:
            if f.get("neg") or not f.get("when_abs"):
                continue
            key = ((f["s"], f["p"], f["o"]), f["when_abs"])
            if key not in seen:
                seen.add(key)
                dated.append((parse_iv(f["when_abs"])[0], f["when_abs"], (f["s"], f["p"], f["o"])))
        if mode in ("antes", "despues"):
            if not ref:
                return None
            _, iv, _ = extract_abs("el " + ref, self._today())
            iv = iv or resolve("_".join(w for w in ref.replace("el ", "").replace("la ", "").split()
                                          if w not in ("ultimo",)).replace("ano_", "ano_"), self._today())
            if not iv:
                return None
            pick = [d for d in dated if (before if mode == "antes" else after)(d[1], iv)]
            if not pick:
                return "No lo sé: no tengo nada con fecha " + mode + " de " + fmt(iv) + "."
        elif mode in ("primero", "ultimo", "al final"):
            if not dated:
                return "No lo sé: no tengo hechos con fecha."
            edge = min(d[0] for d in dated) if mode == "primero" else max(d[0] for d in dated)
            pick = [d for d in dated if d[0] == edge]
        else:
            return None
        pick.sort(key=lambda d: d[0])
        return " ".join(self.say(d[2]) + "." for d in pick)[:800]

    def lookup(self, s, p, o, neg=False, when=""):
        """Hechos de memoria que encajan; s u o pueden ser None (hueco). La relacion encaja si sus lemas se parecen o si
        se dijo con la misma forma verbal (rescata lemas irregulares: muerde -> muerder / mendar)."""
        out = []
        tpl = self._tpl
        surf = getattr(self.m, "surface", {})
        for fs, fp, fo in self._facts(neg):
            same = same_pred(fp, p) or bool(tpl and surf.get(fp.upper()) == tpl)
            al = lambda x: canon(getattr(self.m, "alias", {}).get(x.upper(), x.upper()))          # sinonimos ensenados
            if (s is None or fs == s.upper() or canon(fs) == canon(s) or al(fs) == al(s)) and \
                    (o is None or fo == o.upper() or canon(fo) == canon(o) or al(fo) == al(o)) and same \
                    and (not when or self._when_ok((fs, fp, fo), when)):
                out.append((fs, fp, fo))
        return out

    def derived(self, s, p, o):
        if self.deduce is None:
            return []
        try:
            got = self.deduce([(f["s"], f["p"], f["o"]) for f in self.m.facts if not f.get("neg") and not f.get("q")])
        except Exception:
            return []
        got = dict(got) if isinstance(got, dict) else {k: [] for k in got}
        from src.reasoning.lessons import verb_derive
        for k, v in verb_derive([(f["s"], f["p"], f["o"]) for f in self.m.facts if not f.get("neg") and not f.get("q")],
                                getattr(self.m, "verb_isa", {})).items():
            got.setdefault(k, v)
        self.support = dict(got)
        have = set(self._facts(False))
        return [f for f in got if f not in have and (s is None or f[0] == s.upper()) and (o is None or f[2] == o.upper())
                and same_pred(f[1], p)]

    # ---- decir ------------------------------------------------------
    def _disp(self, name):
        d = getattr(self.m, "display", {}).get(name.upper())
        return d or name.replace("_", " ").title()

    def say(self, fact, neg=False):
        s, p, o = fact
        tpl = None
        for k, v in getattr(self.m, "surface", {}).items():
            if k == p.upper() or same_pred(k, p):
                tpl = v
                break
        if tpl is None and p.upper().startswith(("MAS_", "MENOS_")) and p.upper().endswith("_QUE"):
            kind, _, rest = p.lower().partition("_")
            tpl = "{s} es " + kind + " " + rest[:-4] + " que {o}"
        if tpl is None:
            base, _, prep = p.lower().partition("_")
            fixed = {"ser": "{s} es {o}", "estar": "{s} está {o}", "estar_en": "{s} está en {o}", "tener": "{s} tiene {o}",
                     "parte_de": "{s} es parte de {o}"}      # hechos que salen de efectos o de la semilla (parche-59)
            tpl = fixed.get(p.lower()) or "{s} " + base + (" " + prep if prep else "") + " {o}"
        o_txt = self._disp(o)
        if p.upper() in ("SER", "ESTAR") and o.upper() not in getattr(self.m, "display", {}):
            o_txt = o.replace("_", " ").lower()                  # adjetivos en minuscula: "la puerta está abierta"
        text = tpl.format(s=self._disp(s), o=o_txt).replace(" de el ", " del ").replace(" a el ", " al ")
        text = text.replace(" _", "").strip()
        ws = [d for _, d in self._whens(fact) if d] if not neg else []
        if ws:
            text += " " + ws[0]
            iv, key = self._abs_of(fact)
            if iv and not key.isdigit():
                from src.language.fechas import fmt
                if fmt(iv) not in ws[0]:
                    text += " (" + fmt(iv) + ")"
        until = next((f.get("until") for f in self.m.facts if (f["s"], f["p"], f["o"]) == tuple(fact) and f.get("until")), None)
        if until and getattr(self, "_in_past", False):
            import re as _re
            lem = p.lower().partition("_")[0]
            if lem[-2:] in ("ar", "er", "ir") and len(lem) > 3:                # vive -> vivia, trabaja -> trabajaba
                pres, imp = (lem[:-2] + "a", lem[:-2] + "aba") if lem.endswith("ar") else (lem[:-2] + "e", lem[:-2] + "ía")
                text = _re.sub(r"\b" + pres + r"\b", imp, text, count=1)
            from src.language.fechas import fmt as _fmt
            text += f" (hasta el {_fmt(until + '/' + until)})"
        text = text[0].upper() + text[1:]
        return ("No es cierto que " + text[0].lower() + text[1:]) if neg else text

    def _because(self, fact):
        sup = self.support.get(fact)
        return (" (porque " + " y ".join(self.say(x) for x in sup) + ")") if sup else ""

    # ---- respuesta --------------------------------------------------
    def _wants_past(self, question: str) -> bool:
        """Pregunta en pasado ("antes", imperfecto de un verbo que conozco: vivia, trabajaba)."""
        import re
        t = norm(question)
        if re.search(r"\b(antes|antiguamente|anteriormente|antano)\b", t):
            return True
        heads = {f["p"].lower().partition("_")[0][:-2] for f in list(self.m.facts) + list(getattr(self.m, "past", [])) if len(f["p"]) > 4}
        for w in re.findall(r"\w+", t):
            if re.search(r"(aba|abas|aban|ia|ias|ian)$", w) and re.sub(r"(aba|abas|aban|ia|ias|ian)$", "", w) in heads:
                return True
        return False

    def answer(self, question: str) -> str:
        past = getattr(self.m, "past", [])
        if past and self._wants_past(question):
            saved = self.m.facts
            self.m.facts = list(past)
            self._in_past = True
            try:
                r = self._answer(question)
            finally:
                self.m.facts, self._in_past = saved, False
            if not r.startswith(("No lo sé", "Eso no me consta", "No he entendido")):
                return r
        return self._answer(question)

    def _answer(self, question: str) -> str:
        self._alts = []
        tl = self.timeline(question)
        if tl:
            return tl
        sp = self.special(question)
        if sp:
            return sp
        kind, t = self.read(question)
        if kind in ("si_no", "cuando") and len(self._alts) > 1:
            for alt in self._alts:                          # "Es Marta madre de Pablo" se puede leer mal; vale la que la memoria reconoce
                a_s, a_o = alt["s"], alt["o"]
                if self.lookup(a_s, alt["p"], a_o) or self.lookup(a_s, alt["p"], a_o, neg=True) or self.derived(a_s, alt["p"], a_o):
                    t = alt
                    break
        self._tpl = (t or {}).get("template")
        if t is None:
            return "No he entendido la pregunta. Prueba con otra forma (por ejemplo: ¿Quién escribió una novela?)."
        s = None if t["s"] == norm(HOLE) else t["s"]
        o = None if t["o"] == norm(HOLE) else t["o"]
        p = t["p"]
        when = t.get("when", "")
        if kind == "cuando":
            hits = self.lookup(s, p, o)
            if not hits:
                return "No lo sé."
            if any(d for f in hits for _, d in self._whens(f)):
                return " ".join(dict.fromkeys(self.say(f) + "." for f in hits))[:600]
            return "No lo sé: sé que " + self.say(hits[0]).rstrip(".") + ", pero no cuándo."
        if kind == "si_no" and when and self.lookup(s, p, o):
            if self.lookup(s, p, o, when=when):
                return "Sí. " + self.say(self.lookup(s, p, o, when=when)[0]) + "."
            hits = self.lookup(s, p, o)
            if any(d for f in hits for _, d in self._whens(f)):
                return "No. Según lo que sé: " + self.say(hits[0]) + "."
            return "No lo sé: sé que " + self.say(hits[0]).rstrip(".") + ", pero no cuándo."
        if kind == "si_no":
            hits = self.lookup(s, p, o, neg=False)
            if hits and all(self._q(f) for f in hits):
                return "No lo sé con certeza: solo sé que " + self.say(hits[0])[0].lower() + self.say(hits[0])[1:] + "."
            if hits:
                return "Sí. " + self.say(self.lookup(s, p, o)[0]) + "."
            if p.upper().startswith(("MAS_", "MENOS_")) and s and o:
                opp = ("MENOS_" if p.upper().startswith("MAS_") else "MAS_") + p.upper().split("_", 1)[1]
                inv = self.lookup(s, opp, o) or self.derived(s, opp, o)
                if inv:
                    return "No. " + self.say(inv[0]) + self._because(inv[0]) + "."
            if self.lookup(s, p, o, neg=True):
                return "No. " + self.say(self.lookup(s, p, o, neg=True)[0], neg=True) + "."
            d = self.derived(s, p, o)
            if d:
                return "Sí, lo deduzco: " + self.say(d[0]) + self._because(d[0]) + "."
            if self.lookup(s, p, None) or self.lookup(None, p, o):
                return "Eso no me consta; solo sé " + "; ".join(dict.fromkeys(self.say(f) for f in (self.lookup(s, p, None) or self.lookup(None, p, o))[:3])) + "."
            return "No lo sé."
        hits = self.lookup(s, p, o, when=when)
        ded = [] if (hits and s is not None and o is not None) else self.derived(s, p, o)
        if hits and ded and (s is None or o is None):          # pregunta abierta: lo dicho y tambien lo deducido (parche-59)
            more = [d for d in ded if d not in hits][:3]
            return " ".join(dict.fromkeys([self.say(f) + "." for f in hits] + [self.say(f) + "." for f in more]))[:600]
        if hits:
            return " ".join(dict.fromkeys(self.say(f) + "." for f in hits))[:600]
        if ded:
            return "Lo deduzco: " + " ".join(dict.fromkeys(self.say(f) + self._because(f) + "." for f in ded[:5]))
        return "No lo sé."
''',
    'src/language/school_learn.py': r'''"""La escuela aprende de tus correcciones (parche-49, Fase 2). Sin UD ni LLM.

ENTENDI sujeto relacion objeto  dice cual era la lectura correcta de tu ultima frase. De esa lectura se construye el arbol que la
escuela debio dar (sujeto -> nsubj del verbo, objeto -> obj/obl, verbo -> raiz con su lema) y se hace un ajuste PEQUENO:
  - las correcciones anteriores se repasan junto con la nueva (consolidacion),
  - para no olvidar, se repasan tambien frases de texto normal con SU PROPIA lectura anterior (autodestilacion),
  - si la frase no queda bien, o el canario (test de conversacion) baja mas de una frase, se REVIERTE.
Solo verbos con sujeto y objeto escritos en la frase; relaciones copulativas ("es madre de") aun no."""
from __future__ import annotations

import copy
import json
import os
import random
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import torch

from .lexicon import norm
from .school_parser import SchoolParser
from .ud import edit_script, predict_trees, school_loss

LOG = os.path.join("memory", "correcciones_escuela.jsonl")
LEMAS = os.path.join("memory", "lemas_irregulares.json")


def load_overrides(path: str = LEMAS) -> Dict[str, str]:
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}


def save_overrides(ov: Dict[str, str], path: str = LEMAS) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    json.dump(ov, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def _key(p: str) -> str:
    head, _, prep = norm(p).partition("_")
    return head[:3] + "|" + ("" if prep == "a" else prep)


def target_tree(model, device, scripts, sentence: str, triple: Sequence[str]) -> Tuple[Optional[list], str]:
    forms = SchoolParser._forms(sentence)
    s, p, o = (norm(x) for x in triple)
    low = [norm(f) for f in forms]
    si = [i for i, w in enumerate(low) if w == s]
    oi = [i for i, w in enumerate(low) if w == o]
    if not si or not oi:
        return None, "no encuentro el sujeto y el objeto escritos tal cual en la frase"
    si, oi = si[0], (oi[-1] if oi[-1] != si[0] else oi[0])
    base, _, prep = p.partition("_")
    if base in ("es", "ser"):
        return None, "esa relacion no es un verbo de la frase (las copulativas aun no se aprenden)"
    pred = predict_trees(model, [forms], device, scripts)[0]
    vi = [i for i, w in enumerate(low) if w.startswith(base[:4]) and i not in (si, oi)]
    if not vi:                                  # verbo irregular ("muerde" -> morder): el verbo que la escuela ya ve, el mas cercano al sujeto
        vi = sorted((i for i, t in enumerate(pred) if t[0] == "VERB" and i not in (si, oi)), key=lambda i: abs(i - si))
    if not vi:
        return None, f"no encuentro en la frase el verbo de {p}"
    vi = vi[0]
    words = [[forms[j], *pred[j]] for j in range(len(forms))]       # [forma, upos, head, rel, lema]
    words[vi][1:4] = ["VERB", 0, "root"]
    words[vi][4] = base
    words[si][2:4] = [vi + 1, "nsubj"]
    if words[si][1] not in ("NOUN", "PROPN"):
        words[si][1] = "PROPN" if forms[si][:1].isupper() else "NOUN"
    words[oi][2:4] = [vi + 1, "obl" if prep else "obj"]
    if words[oi][1] not in ("NOUN", "PROPN"):
        words[oi][1] = "NOUN"
    if prep:
        for j in range(oi - 1, -1, -1):
            if low[j] == prep:
                words[j][1:4] = ["ADP", oi + 1, "case"]
                break
    for j, w in enumerate(words):
        if j not in (vi, si, oi) and w[2] == 0:
            w[2], w[3] = vi + 1, ("punct" if w[1] == "PUNCT" else "dep")
    return [tuple(w) for w in words], ""


def read_log(path: str = LOG) -> List[dict]:
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def append_log(sentence: str, triple: Sequence[str], path: str = LOG) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as h:
        h.write(json.dumps({"frase": sentence, "triple": [norm(x) for x in triple]}, ensure_ascii=False) + "\n")


def replay_sentences(path: str = "data/libro.txt", n: int = 300, seed: int = 0) -> List[str]:
    if not os.path.exists(path):
        return []
    from .book import sentences
    pool = [s for s in sentences(open(path, encoding="utf-8").read(), max_words=25) if "?" not in s and 5 <= len(s.split())]
    random.Random(seed).shuffle(pool)
    return pool[:n]


NAMES = ["Pedro", "Ana", "Luis", "Marta", "Sara", "Diego", "Elena", "Hugo", "Irene", "Raúl", "Nuria", "Tomás", "Laura", "Mario"]
VERBS = [("compra", "pan"), ("lee", "libros"), ("escribe", "cartas"), ("pinta", "cuadros"), ("vende", "coches"), ("abre", "la puerta"),
         ("toca", "la guitarra"), ("canta", "canciones"), ("bebe", "agua"), ("tiene", "un perro"), ("estudia", "historia")]
PLACES = ["Madrid", "Sevilla", "Bilbao", "Toledo", "Granada", "Valencia"]


def synthetic_replay(n: int = 200, seed: int = 0) -> List[str]:
    """Frases cortas de conversacion (con coordinaciones) para REPASAR con la lectura anterior de la escuela; no son frases de los tests."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        a, b = rng.sample(NAMES, 2)
        (v, o), (v2, o2) = rng.sample(VERBS, 2)
        city = rng.choice(PLACES)
        out.append(rng.choice([f"{a} {v} {o}.", f"{a} vive en {city}.", f"{a} y {b} {v[:-1]}an {o}.", f"{a} {v} {o} y {o2}.",
                               f"{a} {v} {o} y {v2} {o2}.", f"{a} vive en {city} y trabaja en {rng.choice(PLACES)}.",
                               f"{a} no {v} {o}.", f"{a} {v} {o} en {city}."]))
    return out


def learn_correction(model, device, scripts, sentence: str, triple: Sequence[str], extra: Sequence[dict] = (),
                     replay: Sequence[str] = (), steps: int = 30, lr: float = 3e-5, repeat: int = 4,
                     canary: Optional[Callable[[], float]] = None, tol: float = 0.0125,
                     overrides: Optional[Dict[str, str]] = None) -> Dict:
    target, reason = target_tree(model, device, scripts, sentence, triple)
    if target is None:
        return {"done": False, "reason": reason}
    before = canary() if canary else None
    state = copy.deepcopy(model.state_dict())
    old = [t for t in (target_tree(model, device, scripts, e["frase"], e["triple"])[0] for e in extra) if t]
    pool = [SchoolParser._forms(s) for s in replay]
    pseudo = []
    if pool:
        for forms, tr in zip(pool, predict_trees(model, pool, device, scripts)):
            pseudo.append([(f, *t) for f, t in zip(forms, tr)])
    rng = random.Random(0)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.0)
    model.train()
    for _ in range(steps):
        batch = [target] * repeat + old[-12:] + (rng.sample(pseudo, min(24, len(pseudo))) if pseudo else [])
        loss, _ = school_loss(model, batch, device, scripts)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    model.eval()
    s, p, o = (norm(x) for x in triple)
    parser = SchoolParser(model, device, scripts, overrides)
    check = lambda: any(t["s"] == s and t["o"] == o and _key(t["p"]) == _key(p) for t in (parser.parse(sentence) or []))
    fixed, note = check(), ""
    if not fixed and overrides is not None:
        # lema irregular ("muerde" -> morder): no cabe en los guiones de lema; se guarda como entrada del lexico (forma -> lema)
        verb = next((w[0] for w in target if w[3] == "root"), None)
        if verb and norm(p.partition("_")[0]) != norm(verb):
            overrides[verb.lower()] = p.partition("_")[0]
            fixed, note = check(), "lema irregular guardado: " + verb.lower() + " -> " + p.partition("_")[0]
            if not fixed:
                overrides.pop(verb.lower(), None)
    after = canary() if canary else None
    if not fixed or (before is not None and after < before - tol):
        model.load_state_dict(state)
        return {"done": False, "fixed": fixed, "canary": (before, after),
                "reason": "la frase no quedo bien" if not fixed else "empeoraba lo que ya sabia (canario)"}
    return {"done": True, "fixed": True, "canary": (before, after), "nota": note}
''',
    'src/language/school_parser.py': r'''"""La escuela dentro de la conversacion (parche-32/34): frase libre -> proposiciones, sin plantillas."""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence

from .extract import surface, triples_full
from .irregulares import IRREG
from .lexicon import norm as _norm
from .ud import School, predict_trees


class SchoolParser:
    def __init__(self, model: School, device="cpu", scripts: Sequence = (), overrides: Optional[Dict[str, str]] = None):
        self.model, self.device, self.scripts = model.to(device).eval(), device, list(scripts)
        self.overrides = {**IRREG, **(overrides or {})}      # forma -> lema, ensenados con ENTENDI (verbos irregulares)

    @staticmethod
    def _forms(sentence: str):
        text = re.sub(r"\bdel\b", "de el", sentence, flags=re.I)
        text = re.sub(r"\bal\b", "a el", text, flags=re.I)
        forms = re.findall(r"\w+|[^\w\s]", text)
        if forms and forms[-1] not in ".!?;:":
            forms.append(".")                      # el entrenamiento siempre veia la frase cerrada con signo de puntuacion
        return forms

    def tree(self, sentence: str):
        """[(forma, upos, head, deprel, lema)] por palabra."""
        forms = self._forms(sentence)[:40]
        pred = predict_trees(self.model, [forms], self.device, self.scripts)[0]
        rows = [(f, u, h, r, l) for f, (u, h, r, l) in zip(forms, pred)]
        rows = self._fix_name_verb(rows)
        return [(f, u, h, r, (self.overrides.get(f.lower()) or self.overrides.get(_norm(f)) or l) if u == "VERB" else l) for f, u, h, r, l in rows]

    @staticmethod
    def _fix_name_verb(rows):
        """"Ana duerme." / "Andres cocina pasta.": la escuela lee nombre + palabra en minuscula como un nombre compuesto (flat).
        Un nombre propio no sigue en minusculas: esa palabra es el verbo (parche-55)."""
        rows = [list(x) for x in rows]
        for k in range(1, len(rows)):                      # "mas baja que Clara": un nombre tras "que" no es sujeto, es el termino comparado
            if rows[k][3] == "csubj" and rows[k - 1][3] == "mark" and rows[k - 1][0].lower() == "que":
                rows[k][3] = "nmod"
        for k, (f, u, h, r, l) in enumerate(rows):
            # "Sara vino.": "vino" (verbo) leido como NOUN raiz con sujeto nombre propio y sin determinante
            if (r == "root" and u in ("NOUN", "ADJ", "ADV") and _norm(f) in IRREG and
                    any(x[3] == "nsubj" and x[2] == k + 1 and x[1] in ("PROPN", "NOUN") for x in rows) and
                    not any(x[3] == "det" and x[2] == k + 1 for x in rows)):
                rows[k][1] = "VERB"
                continue
            if r != "flat" or not f[:1].islower() or h < 1 or h - 1 >= k or u == "PUNCT":
                continue
            name = h - 1
            if not rows[name][0][:1].isupper() or rows[name][3] not in ("root", "nsubj"):
                continue
            name_head, name_rel = rows[name][2], rows[name][3]
            if name_rel == "nsubj" and name_head != k + 1 and name_head != 0:
                continue                                    # el nombre es sujeto de OTRO verbo: no tocar
            rows[k][1], rows[k][2], rows[k][3] = "VERB", 0, "root"
            rows[name][2], rows[name][3] = k + 1, "nsubj"
            first_obj = True
            for j in range(k + 1, len(rows)):
                if rows[j][2] == name + 1 or (rows[j][3] == "flat" and rows[j][2] == k + 1):
                    if rows[j][3] == "flat" and rows[j][1] in ("NOUN", "ADJ", "PROPN") and first_obj:
                        rows[j][1] = "NOUN" if rows[j][1] == "ADJ" else rows[j][1]
                        rows[j][2], rows[j][3] = k + 1, "obj"
                        first_obj = False
                    elif rows[j][3] != "flat":
                        rows[j][2] = k + 1
                    else:
                        rows[j][2] = k + 1
            break
        return [tuple(x) for x in rows]

    def parse(self, sentence: str, topic: Optional[str] = None) -> Optional[List[Dict]]:
        """None si no es una afirmacion analizable (pregunta, demasiado corta o larga); si no, lista de proposiciones."""
        if "?" in sentence or "¿" in sentence:
            return None
        from datetime import date
        from src.language.fechas import extract_abs
        sentence, abs_iv, abs_disp = extract_abs(sentence, getattr(self, "today", None) or date.today())
        forms = self._forms(sentence)
        if not 3 <= len(forms) <= 40:         # 3 = "Envia paquetes ." (sujeto omitido)
            return None
        tree = self.tree(sentence)
        found = triples_full(tree, entities_only=True, default_subject=topic)
        if not found and topic and sentence[:1].isupper():
            # "Bebe agua.": con mayuscula inicial la escuela puede leer el verbo como nombre; se reintenta en minuscula
            tree2 = self.tree(sentence[:1].lower() + sentence[1:])
            alt = triples_full(tree2, entities_only=True, default_subject=topic)
            if alt:
                tree, found = tree2, alt
        for t in found:
            t.update(surface(tree, t))
            if abs_iv and not t.get("when"):
                t["when"], t["when_disp"] = "abs:" + abs_iv, abs_disp
        return found
''',
    'src/language/semilla.py': r'''"""Conocimiento de fabrica (parche-59, bloque C): frases en espanol (data/semilla.txt) que se cargan por el camino normal del lenguaje.
No hay hechos escritos a mano: todo pasa por la escuela, igual que si lo dijera la persona. Los hechos quedan con importancia alta
y fuente "semilla" para que "¿Como lo sabes?" diga que es conocimiento de fabrica."""
import copy
import os
import tempfile
from typing import Optional

SEED_KEY = "__semilla__"
_CACHE = {}
KEYS = ("facts", "alias", "opposites", "verb_isa", "defs", "surface", "display")


def sentences(path: str = "data/semilla.txt"):
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            yield line


def build(parser, path: str = "data/semilla.txt"):
    """Procesa las frases con un dialogo y una memoria de usar y tirar. Devuelve (snapshot, frases_sin_entender)."""
    from src.language.dialogue import Dialogue, n
    from src.memory.store import MemoryStore
    with tempfile.TemporaryDirectory() as d:
        mem = MemoryStore(os.path.join(d, "seed.json"))
        dlg = Dialogue(mem)
        miss = []
        for sent in sentences(path):
            r = dlg._definitions(sent, n(sent), None)
            cont = sent
            if r:
                cont = r[1]
                if not cont:
                    continue
            found = parser.parse(cont) or []
            if not found:
                miss.append(sent)
                continue
            for t in found:
                tr = (t["s"], t["p"], t["o"])
                mem.add_fact(tr, source="semilla", neg=t["neg"], quant=t.get("q", ""))
                mem.note_surface(tr, t.get("template"), t.get("s_disp"), t.get("o_disp"))
        for f in mem.facts:
            f["imp"] = 5.0
        mem.display = {k: v[:1].lower() + v[1:] for k, v in mem.display.items()}          # sin nombres propios: "Verde" -> "verde"
        snap = {k: copy.deepcopy(getattr(mem, k)) for k in KEYS}
    return snap, miss


def load_seed(mem, parser, path: str = "data/semilla.txt") -> int:
    """Mezcla la semilla en la memoria (una sola vez). Devuelve cuantos hechos anade."""
    if SEED_KEY in mem.defs:
        return 0
    key = id(parser)
    if key not in _CACHE:
        _CACHE[key] = build(parser, path)[0]
    snap = _CACHE[key]
    have = {(f["s"], f["p"], f["o"], bool(f.get("neg"))) for f in mem.facts}
    added = 0
    for f in snap["facts"]:
        if (f["s"], f["p"], f["o"], bool(f.get("neg"))) not in have:
            mem.facts.append(copy.deepcopy(f))
            added += 1
    for a, b in snap["alias"].items():
        mem.alias.setdefault(a, b)
    for pair in snap["opposites"]:
        if pair not in mem.opposites:
            mem.opposites.append(list(pair))
    for k, v in snap["verb_isa"].items():
        mem.verb_isa.setdefault(k, v)
    for k, v in snap["defs"].items():
        mem.defs.setdefault(k, v)
    for k, v in snap["surface"].items():
        mem.surface.setdefault(k, v)
    for k, v in snap["display"].items():
        mem.display.setdefault(k, v)
    mem.defs[SEED_KEY] = "1"
    return added
''',
    'src/language/training.py': r'''"""Pasos de entrenamiento del oido, compartidos por el entrenamiento inicial y el aprendizaje en conversacion."""
import torch
import torch.nn.functional as F
from .ear import encode_batch, encode_candidates


def batch_loss(ear, batch, pool_texts, rng, device, n_extra=24):
    """batch: dicts (tokens, tags, text, neg[, reject]). Las frases 'reject' solo entrenan el detector de ambito."""
    feat, ids, mask = encode_batch([x["tokens"] for x in batch], device)
    T = feat.shape[1]
    tags = torch.zeros(len(batch), T, dtype=torch.long)
    for i, x in enumerate(batch):
        tags[i, :min(T, len(x["tags"]))] = torch.tensor(x["tags"][:T])
    tags = tags.to(device)
    h, _ = ear(feat, mask)
    keep = torch.tensor([not x.get("reject") for x in batch], device=device)
    scope_loss = F.binary_cross_entropy_with_logits(ear.in_scope(h, mask), keep.float())
    idx = keep.nonzero().squeeze(1)
    if len(idx) == 0:
        return scope_loss, (0.0, 0.0, 0.0, scope_loss.item())
    pos = [batch[i] for i in idx.tolist()]
    hk, idk, mk, tk = h[idx], ids[idx], mask[idx], tags[idx]
    golds = sorted({x["text"] for x in pos})
    extra = [t for t in rng.sample(pool_texts, min(n_extra, len(pool_texts))) if t not in golds]
    cands = golds + extra
    cf, cm, ci = encode_candidates(cands, device)
    scores = ear.score(hk, mk, idk, cf, cm, ci)
    target = torch.tensor([cands.index(x["text"]) for x in pos], device=device)
    pred_loss = F.cross_entropy(scores * 6.0, target)
    _, logits = ear(feat[idx], mk, ear.mark(idk, ci[target]))
    tag_loss = F.cross_entropy(logits[mk], tk[mk])
    pol_target = torch.tensor([float(x["neg"]) for x in pos], device=device)
    pol_loss = F.binary_cross_entropy_with_logits(ear.polarity(hk, mk), pol_target)
    return tag_loss + pred_loss + pol_loss + scope_loss, (tag_loss.item(), pred_loss.item(), pol_loss.item(), scope_loss.item())
''',
    'src/language/ud.py': r'''"""Escuela de espanol (parche-30/34): aprender SINTAXIS con frases reales anotadas (Universal Dependencies).

Cada palabra lleva: categoria (UPOS), de que palabra depende (head), con que funcion (deprel) y su forma base (lema).
v2 (parche-34): rasgo de MAYUSCULA por palabra (Pedro / pedro) y cabeza de LEMA (escribio -> escribir) por "guion de edicion":
(cuantas letras quitar del final, que letras anadir).
"""
from __future__ import annotations

import glob
import json
import os
from collections import Counter
from typing import List, Sequence, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .ear import MAXLEN, Ear, encode_batch
from .lexicon import norm

Word = Tuple[str, str, int, str, str]            # (forma, upos, head, deprel, lemma)
UPOS = ["ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM", "PART", "PRON", "PROPN", "PUNCT", "SCONJ", "SYM", "VERB", "X"]
REL = ["acl", "advcl", "advmod", "amod", "appos", "aux", "case", "cc", "ccomp", "compound", "conj", "cop", "csubj", "dep", "det", "discourse",
       "dislocated", "expl", "fixed", "flat", "goeswith", "iobj", "mark", "nmod", "nsubj", "nummod", "obj", "obl", "orphan", "parataxis",
       "punct", "reparandum", "root", "vocative", "xcomp"]
META = "checkpoints/school_meta.json"


def token_of(form: str) -> str:
    t = norm(form).replace(" ", "_")
    return t if t.strip() else form


def cap_of(form: str, i: int) -> int:
    """0 minuscula, 1 mayuscula inicial en mitad de frase (nombre propio probable), 2 mayuscula por inicio de frase o siglas."""
    if not form[:1].isalpha():
        return 0
    if form.isupper() and len(form) > 1:
        return 2
    if form[:1].isupper():
        return 2 if i == 0 else 1
    return 0


def _clean(s: str) -> str:
    return norm(s).replace(" ", "_")


def edit_script(form: str, lemma: str) -> Tuple[int, str]:
    a, b = _clean(form), _clean(lemma)
    p = 0
    while p < min(len(a), len(b)) and a[p] == b[p]:
        p += 1
    return len(a) - p, b[p:]


def apply_script(form: str, script: Sequence) -> str:
    a = _clean(form)
    cut, add = int(script[0]), str(script[1])
    return (a[:len(a) - cut] if cut <= len(a) else a) + add


def build_scripts(sents: Sequence[Sequence[Word]], top: int = 600) -> List[list]:
    c = Counter(edit_script(w[0], w[4]) for s in sents for w in s if w[1] != "PUNCT")
    return [[k, v] for (k, v), _ in c.most_common(top)]


def read_conllu(path: str, max_len: int = MAXLEN) -> Tuple[List[List[Word]], int]:
    """Devuelve (frases de <= max_len palabras, numero de frases omitidas por largas). Usa palabras sintacticas (del = de + el)."""
    sents, cur, skipped = [], [], 0

    def close():
        nonlocal cur, skipped
        if cur:
            if len(cur) <= max_len:
                sents.append(cur)
            else:
                skipped += 1
        cur = []

    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                close()
                continue
            if line.startswith("#"):
                continue
            c = line.split("\t")
            if len(c) < 8 or "-" in c[0] or "." in c[0]:
                continue                                  # rangos (del = de+el) y nodos vacios
            rel = c[7].split(":")[0]
            cur.append((c[1], c[3] if c[3] in UPOS else "X", int(c[6]), rel if rel in REL else "dep", c[2]))
    close()
    return sents, skipped


def find_files(split: str, root: str = "data/ud") -> List[str]:
    return sorted(glob.glob(os.path.join(root, "*", f"*-ud-{split}.conllu")))


class School(nn.Module):
    """Encoder del oido + cabezas de categoria, dependencia (a quien se une), funcion y lema."""

    def __init__(self, ear: Ear | None = None, n_scripts: int = 0):
        super().__init__()
        self.ear = ear or Ear()
        d = self.ear.d
        self.upos = nn.Linear(d, len(UPOS))
        self.root = nn.Parameter(torch.randn(d) * 0.1)
        self.aq = nn.Linear(d, d)
        self.ak = nn.Linear(d, d)
        self.rel = nn.Sequential(nn.Linear(2 * d, d), nn.GELU(), nn.Linear(d, len(REL)))
        self.cap_emb = nn.Embedding(3, d)
        nn.init.zeros_(self.cap_emb.weight)               # arranca sin efecto: un checkpoint antiguo se comporta igual
        self.lemma = nn.Linear(d, n_scripts) if n_scripts else None

    def forward(self, feat, mask, cap=None):
        extra = self.cap_emb(cap) if cap is not None else None
        h, _ = self.ear(feat, mask, extra=extra)
        B, T, d = h.shape
        keys = torch.cat([self.root.expand(B, 1, d), h], 1)                       # posicion 0 = raiz
        arc = torch.einsum("bid,bjd->bij", self.aq(h), self.ak(keys)) / d ** 0.5
        kmask = torch.cat([torch.ones(B, 1, dtype=torch.bool, device=mask.device), mask], 1)
        arc = arc.masked_fill(~kmask[:, None, :], -1e4)
        eye = torch.eye(T, dtype=torch.bool, device=mask.device)
        arc[:, :, 1:] = arc[:, :, 1:].masked_fill(eye[None], -1e4)                  # una palabra no depende de si misma
        return h, self.upos(h), arc

    def rel_logits(self, h, heads):
        B, T, d = h.shape
        keys = torch.cat([self.root.expand(B, 1, d), h], 1)
        head_h = keys.gather(1, heads[..., None].expand(-1, -1, d))
        return self.rel(torch.cat([h, head_h], -1))


def save_school(model: School, scripts: Sequence, path="checkpoints/school.pt", meta=META):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    torch.save(model.state_dict(), path)
    json.dump(scripts, open(meta, "w"))


def load_school(path="checkpoints/school.pt", meta=META, device="cpu"):
    """Devuelve (modelo, guiones de lema). Funciona tambien con checkpoints antiguos (sin lema ni mayusculas)."""
    scripts = json.load(open(meta)) if os.path.exists(meta) else []
    state = torch.load(path, map_location="cpu")
    if "lemma.weight" not in state:
        scripts = []
    model = School(n_scripts=len(scripts))
    model.load_state_dict(state, strict=False)
    return model.to(device).eval(), scripts


def _tensors(forms_batch: Sequence[Sequence[str]], device):
    feat, _, mask = encode_batch([[token_of(w) for w in s] for s in forms_batch], device)
    B, T = mask.shape
    cap = torch.zeros(B, T, dtype=torch.long)
    for i, s in enumerate(forms_batch):
        for j, w in enumerate(s[:T]):
            cap[i, j] = cap_of(w, j)
    return feat, mask, cap.to(device)


def to_tensors(batch: Sequence[Sequence[Word]], device="cpu", scripts=None):
    feat, mask, cap = _tensors([[w[0] for w in s] for s in batch], device)
    B, T = mask.shape
    upos = torch.full((B, T), -100, dtype=torch.long)
    head = torch.full((B, T), -100, dtype=torch.long)
    rel = torch.full((B, T), -100, dtype=torch.long)
    lem = torch.full((B, T), -100, dtype=torch.long)
    index = {(int(a), str(b)): k for k, (a, b) in enumerate(scripts)} if scripts else {}
    for i, s in enumerate(batch):
        for j, w in enumerate(s[:T]):
            upos[i, j], head[i, j], rel[i, j] = UPOS.index(w[1]), w[2], REL.index(w[3])
            if index:
                lem[i, j] = index.get(edit_script(w[0], w[4]), -100)
    return feat, mask, cap, upos.to(device), head.to(device), rel.to(device), lem.to(device)


def school_loss(model: School, batch, device="cpu", scripts=None):
    feat, mask, cap, upos, head, rel, lem = to_tensors(batch, device, scripts)
    h, lu, arc = model(feat, mask, cap)
    l_u = F.cross_entropy(lu.reshape(-1, lu.shape[-1]), upos.reshape(-1), ignore_index=-100)
    l_h = F.cross_entropy(arc.reshape(-1, arc.shape[-1]), head.reshape(-1), ignore_index=-100)
    lr = model.rel_logits(h, head.clamp(min=0))
    l_r = F.cross_entropy(lr.reshape(-1, lr.shape[-1]), rel.reshape(-1), ignore_index=-100)
    loss, parts = l_u + l_h + l_r, [l_u.item(), l_h.item(), l_r.item()]
    if model.lemma is not None and (lem != -100).any():
        ll = model.lemma(h)
        l_l = F.cross_entropy(ll.reshape(-1, ll.shape[-1]), lem.reshape(-1), ignore_index=-100)
        loss = loss + l_l
        parts.append(l_l.item())
    return loss, tuple(parts)


@torch.no_grad()
def predict_trees(model: School, sents: Sequence[Sequence[str]], device="cpu", scripts=None, chunk=128):
    """sents: listas de formas. Devuelve por frase una lista de (upos, head, deprel, lema)."""
    model.eval()
    out = []
    with torch.no_grad():
        for b in range(0, len(sents), chunk):
            part = sents[b:b + chunk]
            feat, mask, cap = _tensors(part, device)
            h, lu, arc = model(feat, mask, cap)
            heads = arc.argmax(-1)
            rels = model.rel_logits(h, heads).argmax(-1)
            pos = lu.argmax(-1)
            lem = model.lemma(h).argmax(-1) if (model.lemma is not None and scripts) else None
            # una sola copia a la CPU por lote (leer tensor a tensor desde MPS/GPU era lentisimo)
            heads_l, rels_l, pos_l = heads.cpu().tolist(), rels.cpu().tolist(), pos.cpu().tolist()
            lem_l = lem.cpu().tolist() if lem is not None else None
            for i, s in enumerate(part):
                row = []
                for j, form in enumerate(s):
                    lemma = apply_script(form, scripts[lem_l[i][j]]) if lem_l is not None else token_of(form)
                    row.append((UPOS[pos_l[i][j]], heads_l[i][j], REL[rels_l[i][j]], lemma))
                out.append(row)
    return out
''',
    'src/language/ud_synth.py': r'''"""Frases CORTAS y simples con arbol conocido, hechas con las palabras reales del corpus (parche-34).

Los corpus UD son prensa: casi no hay frases como "Pedro vive en Madrid". Aqui se mina de las propias frases UD el
vocabulario (nombres propios, verbos conjugados con su lema, sustantivos con su articulo) y se combina en marcos simples.
Sintacticamente son correctas; semanticamente pueden ser absurdas ("Pedro abrio la lluvia"), y no importa: ensenan estructura.
Es un APOYO para el hueco de frases cortas, no un sustituto del espanol real.
"""
from __future__ import annotations

import random
from typing import List, Sequence

DET_LEMMA = {"el": "el", "la": "el", "un": "uno", "una": "uno"}


def mine(sents: Sequence[Sequence[tuple]]) -> dict:
    names, nouns, verbs_obj, verbs_obl, verbs_any = set(), {}, {}, {}, {}
    for s in sents:
        n = len(s)
        for j, (form, upos, head, rel, lemma) in enumerate(s):
            if upos == "PROPN" and rel in ("nsubj", "obj", "obl", "nmod") and form[:1].isupper() and form.isalpha() and len(form) > 2 \
                    and not any(w[3] == "flat" and w[2] == j + 1 for w in s):
                names.add(form)
            if upos == "NOUN" and j > 0 and s[j - 1][1] == "DET" and s[j - 1][2] == j + 1 and s[j - 1][3] == "det" \
                    and s[j - 1][0].lower() in DET_LEMMA and form.isalpha() and form.islower():
                nouns[(s[j - 1][0].lower(), form)] = lemma
            if upos == "VERB" and form.islower() and form.isalpha() and lemma != form and not form.endswith(("ndo", "ado", "ido", "ada", "ida", "ados", "idos", "adas", "idas")) \
                    and lemma.endswith(("ar", "er", "ir")):
                kids = [(k, w) for k, w in enumerate(s) if w[2] == j + 1]
                if any(w[3] == "aux" for _, w in kids):
                    continue
                subj = [w for _, w in kids if w[3] == "nsubj" and w[1] == "PROPN"]
                if not subj:
                    continue
                verbs_any[(form, lemma)] = 1
                if any(w[3] == "obj" and w[1] == "NOUN" for _, w in kids):
                    verbs_obj[(form, lemma)] = 1
                for k, w in kids:
                    if w[3] == "obl" and w[1] in ("PROPN", "NOUN"):
                        preps = [x[0].lower() for x in s if x[2] == k + 1 and x[3] == "case"]
                        if preps and preps[0] in ("en", "con", "para", "desde", "por", "a", "de", "hacia", "sobre"):
                            verbs_obl[(form, lemma, preps[0])] = 1
    return {"names": sorted(names), "nouns": [(d, n, l) for (d, n), l in nouns.items()], "v_obj": sorted(verbs_obj),
            "v_obl": sorted(verbs_obl), "v_any": sorted(verbs_any)}


class _B:
    """Constructor de frases con referencias por etiqueta."""

    def __init__(self):
        self.w = []
        self.lab = {}

    def add(self, label, form, upos, rel, head_label, lemma=None):
        self.lab[label] = len(self.w) + 1
        self.w.append([form, upos, head_label, rel, lemma if lemma is not None else form.lower()])

    def done(self) -> List[tuple]:
        return [(f, u, 0 if h is None else self.lab[h], r, l) for f, u, h, r, l in self.w]


def _np(b, rng, voc, label, head_label, rel, allow_det=True):
    """Anade un sintagma nominal: nombre propio o 'det nombre'. Devuelve la palabra nucleo (etiqueta)."""
    if rng.random() < 0.5 or not allow_det:
        b.add(label, rng.choice(voc["names"]), "PROPN", rel, head_label)
    else:
        d, n, l = rng.choice(voc["nouns"])
        b.add(label + "d", d, "DET", "det", label)
        b.add(label, n, "NOUN", rel, head_label, l)
    return label


def make(voc: dict, n: int, seed: int = 0) -> List[List[tuple]]:
    rng = random.Random(seed)
    out = []
    if not (voc["names"] and voc["nouns"] and voc["v_any"]):
        return out
    while len(out) < n:
        b = _B()
        frame = rng.choice(["svo", "svo", "sobl", "sobl", "neg", "cop_de", "cop", "detsubj"])
        try:
            if frame in ("svo", "neg") and voc["v_obj"]:
                v = rng.choice(voc["v_obj"])
                b.add("s", rng.choice(voc["names"]), "PROPN", "nsubj", "v")
                if frame == "neg":
                    b.add("no", "no", "ADV", "advmod", "v")
                b.add("v", v[0], "VERB", "root", None, v[1])
                d, nn, l = rng.choice(voc["nouns"])
                b.add("od", d, "DET", "det", "o")
                b.add("o", nn, "NOUN", "obj", "v", l)
            elif frame == "sobl" and voc["v_obl"]:
                v = rng.choice(voc["v_obl"])
                b.add("s", rng.choice(voc["names"]), "PROPN", "nsubj", "v")
                b.add("v", v[0], "VERB", "root", None, v[1])
                b.add("p", v[2], "ADP", "case", "o")
                _np(b, rng, voc, "o", "v", "obl")
            elif frame == "cop_de":
                d, nn, l = rng.choice(voc["nouns"])
                b.add("s", rng.choice(voc["names"]), "PROPN", "nsubj", "n")
                b.add("c", "es", "AUX", "cop", "n", "ser")
                b.add("nd", d, "DET", "det", "n")
                b.add("n", nn, "NOUN", "root", None, l)
                b.add("p", "de", "ADP", "case", "o")
                b.add("o", rng.choice(voc["names"]), "PROPN", "nmod", "n")
            elif frame == "cop":
                d, nn, l = rng.choice(voc["nouns"])
                b.add("s", rng.choice(voc["names"]), "PROPN", "nsubj", "n")
                b.add("c", "es", "AUX", "cop", "n", "ser")
                b.add("nd", d, "DET", "det", "n")
                b.add("n", nn, "NOUN", "root", None, l)
            elif frame == "detsubj" and voc["v_obj"]:
                v = rng.choice(voc["v_obj"])
                d, nn, l = rng.choice(voc["nouns"])
                b.add("sd", d.capitalize(), "DET", "det", "s")
                b.add("s", nn, "NOUN", "nsubj", "v", l)
                b.add("v", v[0], "VERB", "root", None, v[1])
                d2, n2, l2 = rng.choice(voc["nouns"])
                b.add("od", d2, "DET", "det", "o")
                b.add("o", n2, "NOUN", "obj", "v", l2)
            else:
                continue
            root = next(k for k in b.lab if b.w[b.lab[k] - 1][3] == "root")
            b.add("dot", ".", "PUNCT", "punct", root)
            out.append(b.done())
        except (IndexError, KeyError):
            continue
    return out
''',
    'src/memory/__init__.py': r'''from .store import MemoryStore

__all__ = ["MemoryStore"]
''',
    'src/memory/negatives.py': r'''"""Ejemplos NEGATIVOS para las lecciones (parche-20): "esta regla NO se aplica aqui".

Fallo que mostro la conversacion real: tras ensenar  X PADRE_DE Y => Y HIJO_DE X,
el modelo respondia  JOSE HIJO_DE PACO  a  "Paco HIJO_DE Jose"  (aplicaba la regla a
cualquier frase de dos personas). Las lecciones solo traian casos donde la regla SI
vale. Aqui se generan casos hermanos donde cambia la relacion de una premisa y la
respuesta correcta es  SUJETO SIN_CONCLUSION NINGUNA.

Solo se usan como negativos relaciones que el motor simbolico confirma que, solas,
no concluyen nada (asi no se contradice el conocimiento de fabrica).
"""
from __future__ import annotations

import random
from typing import List, Sequence, Tuple

from ..reasoning.rule_engine import Fact, RuleEngine
from .schema import induce, instantiate, is_entity

Triple = Tuple[str, str, str]
SKIP = {"SIN_CONCLUSION", "REGLA_HEREDA", "CONTRADICE", "NINGUNA"}


# Relaciones "fantasma" (parche-22): nombres que el modelo nunca ha visto. Sirven para que aprenda la regla
# general "si no tengo una leccion para esta relacion, no concluyo", y no solo "no concluyo con AMIGO_DE".
# Suenan como relaciones que el oido puede sacar de una frase en espanol (jefe de, criado de...).
GHOST_POOL = ["JEFE_DE", "CRIADO_DE", "MAESTRO_DE", "SOCIO_DE", "DUENO_DE", "AMO_DE", "CRIADA_DE", "VIUDO_DE",
              "RIVAL_DE", "SOCIA_DE", "TUTOR_DE", "HEREDERO_DE", "ALUMNO_DE", "PATRON_DE", "CONOCIDO_DE", "ENEMIGO_DE"]
_SYL = ["BA", "KO", "LU", "MI", "NE", "PO", "RA", "SU", "TE", "VI", "ZA", "DO", "FE", "GU", "HO"]


def make_ghosts(space, rng: random.Random, n: int, exclude=()) -> List[str]:
    out = []
    pool = [g for g in GHOST_POOL if g not in exclude and g not in space.concept_to_id]
    for _ in range(n):
        if pool and rng.random() < 0.5:
            name = rng.choice(pool)
        else:
            name = "".join(rng.choice(_SYL) for _ in range(rng.randint(2, 4))) + "_DE"
            if name in exclude or name in space.concept_to_id:
                continue
        register_ghost(space, name)
        out.append(name)
    return out


def register_ghost(space, name: str) -> None:
    """Vector temporal para un nombre que NO esta en el catalogo (no se guarda ni se decodifica)."""
    if name in space.proposition_vectors:
        return
    import torch
    import torch.nn.functional as F
    vec = torch.zeros(space.d_concept)
    for feat, w in (("predicate", 1.0), ("relation", 1.0), (f"identity:{name}", 0.5)):
        vec += w * (space.feature_to_vector[feat] if feat in space.feature_to_vector else space._feature_vector(feat))
    space.proposition_vectors[name] = F.normalize(vec, p=2, dim=-1)
    space.__dict__.setdefault("_ghosts", set()).add(name)


def purge_ghosts(space) -> None:
    ghosts = space.__dict__.get("_ghosts")
    if not ghosts:
        return
    for label in [l for l in list(space.proposition_vectors)
                  if l in ghosts or any(part in ghosts for part in space.proposition_parts.get(l, ()))]:
        space.proposition_vectors.pop(label, None)
        space.proposition_parts.pop(label, None)
    ghosts.clear()


def safe_predicates(space) -> List[str]:
    engine = RuleEngine()
    ents = [n for n in space.concept_to_id if is_entity(space, n)][:2]
    out = []
    if len(ents) < 2:
        return out
    for name, meta in space.metadata.items():
        if meta.get("kind") != "predicate" or name in SKIP:
            continue
        given = {Fact(ents[0], name, ents[1])}
        if not (engine.infer(given)["facts"] - given):
            out.append(name)
    return out


def make_negatives(space, lessons: Sequence[Tuple[Sequence[Triple], Triple]], n: int, rng: random.Random,
                   entities: Sequence[str], safe: Sequence[str] | None = None, ghosts: float = 0.5,
                   ghost_exclude=()):
    if not lessons:
        return []
    safe = list(safe) if safe is not None else safe_predicates(space)
    lesson_preds = {p[1] for prem, _ in lessons for p in prem}
    cands = [q for q in safe if q not in lesson_preds]
    fantasmas = make_ghosts(space, rng, max(8, n // 8), exclude=set(ghost_exclude) | lesson_preds) if ghosts > 0 else []
    if not cands and not fantasmas:
        return []
    schemas = {}
    for prem, concl in lessons:
        s = induce(space, [tuple(p) for p in prem], tuple(concl))
        schemas[s.signature] = s
    schemas = list(schemas.values())
    out = []
    for _ in range(n):
        schema = rng.choice(schemas)
        prem, _ = instantiate(space, schema, rng, entities)
        k = rng.randrange(len(prem))
        use_ghost = fantasmas and (not cands or rng.random() < ghosts)
        prem[k] = (prem[k][0], rng.choice(fantasmas if use_ghost else cands), prem[k][2])
        out.append((prem, (prem[0][0], "SIN_CONCLUSION", "NINGUNA")))
    return out
''',
    'src/memory/schema.py': r'''"""Esquemas: de varias lecciones parecidas a UNA regla general (parche-14).

Una leccion  ANA PADRE_DE LUIS => LUIS HIJO_DE ANA  se generaliza a
    ?0 PADRE_DE ?1 => ?1 HIJO_DE ?0
donde ?0 y ?1 son variables (entidades) y los predicados/valores fijos son
constantes. Con el esquema se pueden "sonar" (instanciar) ejemplos nuevos con
otras entidades: la base del repaso generativo durante el sueno.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Sequence, Tuple

Triple = Tuple[str, str, str]


def is_entity(space, name: str) -> bool:
    return space.metadata.get(name, {}).get("kind") == "entity"


def family(space, name: str) -> FrozenSet[str]:
    feats = space.metadata.get(name, {}).get("features", {})
    return frozenset(f for f in feats if not f.startswith("identity:"))


@dataclass
class Schema:
    premises: List[Tuple[str, str, str]]
    conclusion: Tuple[str, str, str]
    var_family: Dict[str, FrozenSet[str]] = field(default_factory=dict)

    @property
    def signature(self) -> str:
        return json.dumps([self.premises, self.conclusion], sort_keys=True)

    @property
    def n_vars(self) -> int:
        return len(self.var_family)


def induce(space, premises: Sequence[Triple], conclusion: Triple) -> Schema:
    mapping: Dict[str, str] = {}
    fams: Dict[str, FrozenSet[str]] = {}

    def conv(name: str, slot: int, learn: bool) -> str:
        if slot != 1 and is_entity(space, name):
            if name in mapping:
                return mapping[name]
            if learn:
                var = f"?{len(mapping)}"
                mapping[name] = var
                fams[var] = family(space, name)
                return var
        return name

    prem = [tuple(conv(x, i, True) for i, x in enumerate(p)) for p in premises]
    concl = tuple(conv(x, i, False) for i, x in enumerate(conclusion))
    return Schema(prem, concl, fams)


def instantiate(space, schema: Schema, rng: random.Random, entities: Sequence[str]) -> Tuple[List[Triple], Triple]:
    """Rellena las variables con entidades distintas de la misma familia."""
    chosen: Dict[str, str] = {}
    used = set()
    for var, fam in schema.var_family.items():
        same = [e for e in entities if family(space, e) == fam and e not in used]
        pool = same or [e for e in entities if (family(space, e) & fam) and e not in used] or [e for e in entities if e not in used]
        pick = rng.choice(pool)
        chosen[var] = pick
        used.add(pick)
    fill = lambda t: tuple(chosen.get(x, x) for x in t)
    return [fill(p) for p in schema.premises], fill(schema.conclusion)
''',
    'src/memory/sleep.py': r'''"""Ciclo de sueno del LCM (parche-14).

Inspirado en el "ciclo de sueno" del proyecto memoria-unificada (tareas rotativas:
repair, decay, dedupe, selftest, ...), adaptado a un modelo que aprende con
pesos: ademas de ordenar la memoria, CONSOLIDA el aprendizaje.

Tareas:
  repair    : archiva lecciones que mencionan conceptos desaparecidos
  selftest  : se examina: recuerda cada leccion? generaliza su esquema a entidades nuevas?
  compress  : de cada esquema conserva pocas lecciones representativas (el resto se
              archiva, de forma reversible: su informacion queda en el esquema)
  consolidate: repasa lecciones + ejemplos de fabrica + SUENOS (ejemplos generados
              desde los esquemas con otras entidades), dando mas peso a lo debil;
              revierte si el canario cae
  decay     : olvido de hechos poco importantes/usados (reversible)
"""
from __future__ import annotations

import copy
import datetime
import os
import random
from typing import Dict, List

import torch

from .schema import Schema, induce, instantiate, is_entity


class SleepCycle:
    def __init__(self, learner, memory, seed: int = 0):
        self.L = learner
        self.mem = memory
        self.rng = random.Random(seed)

    # ---- utilidades ---------------------------------------------------
    @property
    def space(self):
        return self.L.space

    def sync(self) -> None:
        self.L.lessons = [([tuple(p) for p in l["premises"]], tuple(l["conclusion"])) for l in self.mem.active_lessons()]

    def entities(self) -> List[str]:
        return [n for n in self.space.concept_to_id if is_entity(self.space, n)]

    def groups(self, include_archived: bool = True) -> Dict[str, dict]:
        out: Dict[str, dict] = {}
        for i, l in enumerate(self.mem.lessons):
            if l.get("archived") and not include_archived:
                continue
            premises = [tuple(p) for p in l["premises"]]
            schema = induce(self.space, premises, tuple(l["conclusion"]))
            g = out.setdefault(schema.signature, {"schema": schema, "idx": []})
            g["idx"].append(i)
        return out

    # ---- tareas -------------------------------------------------------
    def task_repair(self) -> int:
        fixed = 0
        for l in self.mem.lessons:
            names = [x for p in l["premises"] for x in p] + list(l["conclusion"])
            if not l.get("archived") and any(n not in self.space.concept_to_id for n in names):
                l["archived"] = True
                fixed += 1
        return fixed

    def selftest(self, probes: int = 40) -> dict:
        self.sync()
        entities = self.entities()
        rows = []
        for sig, g in self.groups(include_archived=False).items():
            lessons = [(  [tuple(p) for p in self.mem.lessons[i]["premises"]], tuple(self.mem.lessons[i]["conclusion"]))
                       for i in g["idx"]]
            recall = self.L.exact(*self.L.encode(lessons))
            fresh = [instantiate(self.space, g["schema"], self.rng, entities) for _ in range(probes)]
            probe = self.L.exact(*self.L.encode(fresh))
            rows.append({"sig": sig, "n": len(lessons), "recall": recall, "probe": probe})
        return {"groups": rows, "canary": self.L.canary_score()}

    def task_compress(self, max_keep: int = 3) -> int:
        archived = 0
        test = self.selftest(probes=10)
        recall_by_sig = {r["sig"]: r["recall"] for r in test["groups"]}
        for sig, g in self.groups(include_archived=False).items():
            idx = g["idx"]
            if len(idx) > max_keep:
                # se conservan las ultimas aprendidas (las mas frescas); el resto se archiva
                for i in idx[:-max_keep]:
                    self.mem.lessons[i]["archived"] = True
                    archived += 1
        self.sync()
        return archived

    def task_consolidate(self, steps: int = 400, lr: float = 5e-4, use_lessons: bool = True, use_dreams: bool = True,
                         bank_size: int = 300, dreams_per_step: int = 32, replay_core: bool = True,
                         use_negatives: bool = True, neg_per_step: int = 32) -> dict:
        self.sync()
        L = self.L
        entities = self.entities()
        test = self.selftest(probes=20)
        banks = []
        if use_dreams:
            all_groups = self.groups(include_archived=True)
            weak = {r["sig"]: r["probe"] for r in test["groups"]}
            for sig, g in all_groups.items():
                examples = [instantiate(self.space, g["schema"], self.rng, entities) for _ in range(bank_size)]
                weight = 1.0 + 2.0 * (1.0 - weak.get(sig, 0.5))       # mas sueños donde peor generaliza
                banks.append((L.encode(examples), max(4, int(dreams_per_step * weight / 2))))
        own = L.encode(L.lessons) if (use_lessons and L.lessons) else None
        neg = None
        if use_negatives and L.lessons:
            from .negatives import make_negatives
            negs = make_negatives(self.space, L.lessons, 400, self.rng, entities, L.safe(), ghost_exclude=L.neg_exclude)
            neg = L.encode(negs) if negs else None
        snapshot = copy.deepcopy(L.model.state_dict())
        L.model.train()
        optimizer = torch.optim.AdamW(L.model.parameters(), lr=lr, weight_decay=0.0)
        def one_step():
            parts = []
            if replay_core:
                j = torch.randint(0, len(L.core[0]), (L.replay_batch,))
                parts.append(tuple(t[j] for t in L.core))
            if own is not None:
                j = torch.randint(0, len(own[0]), (min(L.replay_batch, len(own[0])),))
                parts.append(tuple(t[j] for t in own))
            if neg is not None:
                j = torch.randint(0, len(neg[0]), (neg_per_step,))
                parts.append(tuple(t[j] for t in neg))
            for (X, M, Y), k in banks:
                j = torch.randint(0, len(X), (k,))
                parts.append((X[j], M[j], Y[j]))
            if not parts:
                return False
            X, M, Y = (torch.cat([p[i] for p in parts]).to(L.device) for i in range(3))
            _, loss = L.model(X, target=Y, attention_mask=M)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(L.model.parameters(), 1.0)
            optimizer.step()
            return True

        def consolidated():
            """Se duerme hasta estar consolidado: recuerda lecciones, generaliza sus esquemas y no inventa donde no aplica."""
            L.model.eval()
            scores = []
            if own is not None:
                scores.append(L.exact(*own))
            for sig, g in self.groups(include_archived=False).items():
                fresh = [instantiate(self.space, g["schema"], self.rng, entities) for _ in range(40)]
                scores.append(L.exact(*L.encode(fresh)))
            if use_negatives and L.lessons:
                from .negatives import make_negatives as mk
                negs = mk(self.space, L.lessons, 200, self.rng, entities, L.safe(), ghost_exclude=L.neg_exclude)
                if negs:
                    scores.append(L.exact(*L.encode(negs)))
            L.model.train()
            return (min(scores) if scores else 1.0), scores

        total, extra, score = 0, 200, 1.0
        limit = steps * 3
        while total < limit:
            n = steps if total == 0 else extra
            if not all(one_step() for _ in range(n)):
                break
            total += n
            score, _ = consolidated()
            if score >= 0.97:
                break
        L.model.eval()
        canary = L.canary_score()
        rolled_back = canary < L.canary_min
        if rolled_back:
            L.model.load_state_dict(snapshot)
        return {"canary": canary, "rolled_back": rolled_back, "groups": len(banks), "steps": total, "consolidation": score}

    # ---- ciclo completo -----------------------------------------------
    def run(self, steps: int = 400, use_lessons: bool = True, use_dreams: bool = True, use_negatives: bool = True, neg_per_step: int = 32, max_keep: int = 3,
            ledger: str | None = "reports/ledger.md") -> dict:
        self.mem.tick += 1
        report = {"repair": self.task_repair()}
        before = self.selftest()
        report["before"] = before
        report["compressed"] = self.task_compress(max_keep)
        report["consolidate"] = self.task_consolidate(steps=steps, use_lessons=use_lessons, use_dreams=use_dreams, use_negatives=use_negatives,
                                                   neg_per_step=neg_per_step)
        report["decayed_facts"] = self.mem.decay()
        after = self.selftest()
        report["after"] = after
        if ledger:
            os.makedirs(os.path.dirname(ledger) or ".", exist_ok=True)
            mean = lambda t: (sum(r["probe"] for r in t["groups"]) / len(t["groups"])) if t["groups"] else float("nan")
            with open(ledger, "a", encoding="utf-8") as handle:
                handle.write(f"| {datetime.datetime.now():%Y-%m-%d %H:%M} | tick {self.mem.tick} | esquemas {len(after['groups'])} | "
                             f"generaliza {mean(before):.0%} -> {mean(after):.0%} | canario {after['canary']:.0%} | "
                             f"archivadas {report['compressed']} | revertido {report['consolidate']['rolled_back']} |\n")
        return report
''',
    'src/memory/store.py': r'''"""Memoria persistente del LCM (parche-13).

Guarda lo que el modelo aprende DIALOGANDO:
  - conceptos nuevos (se re-registran de forma determinista en el catalogo base),
  - hechos sueltos (memoria semantica: "A MAYOR_QUE B"),
  - lecciones (premisas => conclusion) que sirven para aprender y para REPASAR.
Es la base del futuro ciclo de sueno: lo que se consolida sale de aqui.
"""
from __future__ import annotations

import json
import os
import time
from collections import deque
from datetime import date
from typing import Dict, List, Optional, Tuple

Triple = Tuple[str, str, str]


class MemoryStore:
    def __init__(self, path: str = "memory/lcm_memory.json"):
        self.path = path
        self.concepts: List[dict] = []
        self.facts: List[dict] = []
        self.alias: Dict[str, str] = {}         # sinonimos (parche-58): AUTO -> COCHE
        self.opposites: List[list] = []         # pares de contrarios ensenados: ["ruidoso", "silencioso"]
        self.verb_isa: Dict[str, str] = {}      # "cocinar" -> "preparar"
        self.defs: Dict[str, str] = {}          # definiciones tal como se dijeron
        self.past: List[dict] = []              # hechos que dejaron de valer (parche-57): "Ana vivia en Madrid"
        self.lessons: List[dict] = []
        self.surface: Dict[str, str] = {}   # predicado -> plantilla "{s} vive en {o}" (como lo dijo la persona)
        self.display: Dict[str, str] = {}   # entidad -> como se escribia ("el perro", "Marta")
        self.tick = 0  # reloj de mantenimiento: sube una unidad por cada ciclo de sueno
        if os.path.exists(path):
            self.load()

    # ---- persistencia -------------------------------------------------
    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump({"concepts": self.concepts, "facts": self.facts, "past": self.past, "alias": self.alias, "opposites": self.opposites, "verb_isa": self.verb_isa, "defs": self.defs, "lessons": self.lessons, "tick": self.tick,
                       "surface": self.surface, "display": self.display},
                      handle, ensure_ascii=False, indent=1)
        os.replace(tmp, self.path)

    def load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.concepts = data.get("concepts", [])
        self.facts = data.get("facts", [])
        self.past = data.get("past", [])
        self.alias = data.get("alias", {})
        self.opposites = data.get("opposites", [])
        self.verb_isa = data.get("verb_isa", {})
        self.defs = data.get("defs", {})
        self.lessons = data.get("lessons", [])
        self.tick = int(data.get("tick", 0))
        self.surface = data.get("surface", {})
        self.display = data.get("display", {})

    # ---- conceptos ----------------------------------------------------
    def add_concept(self, name: str, features: Optional[dict] = None, kind: str = "entity") -> None:
        name = name.upper()
        if any(c["name"] == name for c in self.concepts):
            return
        self.concepts.append({"name": name, "features": features, "kind": kind, "t": time.time()})

    def apply_concepts(self, space) -> int:
        """Re-registra los conceptos guardados en un espacio base (vectores deterministas)."""
        added = 0
        for c in self.concepts:
            if c["name"] not in space.concept_to_id:
                space.add_concept(c["name"], features=c.get("features"), kind=c.get("kind", "entity"))
                added += 1
        return added

    # ---- hechos -------------------------------------------------------
    def add_fact(self, fact: Triple, source: str = "usuario", neg: bool = False, when: str = "", when_disp: str = "", quant: str = "") -> bool:
        """neg=True guarda un hecho NEGADO ("Ana no es madre de Luis"): no se usa para razonar, pero se recuerda."""
        fact = tuple(x.upper() for x in fact)
        from src.language.fechas import resolve
        when_abs = resolve(when, getattr(self, "today", None) or date.today()) if when else None
        for f in self.facts:
            if (f["s"], f["p"], f["o"]) == fact and bool(f.get("neg", False)) == neg and f.get("when", "") == when \
                    and f.get("when_abs") == when_abs and f.get("q", "") == quant:
                f["n"] += 1
                return False
        self.facts.append({"s": fact[0], "p": fact[1], "o": fact[2], "t": time.time(), "n": 1, "source": source,
                           "imp": 1.0, "tick": self.tick, "archived": False, "neg": neg, "when": when, "when_disp": when_disp, "when_abs": when_abs, "q": quant})
        return True

    def note_surface(self, fact: Triple, template: Optional[str] = None, s_disp: Optional[str] = None,
                     o_disp: Optional[str] = None) -> None:
        """Recuerda como se dijo una proposicion para poder contestar con las mismas palabras."""
        s, p, o = (x.upper() for x in fact)
        if template and p not in self.surface:
            self.surface[p] = template
        if s_disp and s not in self.display:
            self.display[s] = s_disp
        if o_disp and o not in self.display:
            self.display[o] = o_disp

    def contradicts(self, fact: Triple, neg: bool) -> bool:
        """Hay guardado el hecho contrario (afirmado vs negado)?"""
        fact = tuple(x.upper() for x in fact)
        return any((f["s"], f["p"], f["o"]) == fact and bool(f.get("neg", False)) != neg for f in self.facts)

    def forget_fact(self, fact: Triple) -> bool:
        fact = tuple(x.upper() for x in fact)
        before = len(self.facts)
        self.facts = [f for f in self.facts if (f["s"], f["p"], f["o"]) != fact]
        return len(self.facts) < before

    def find_path(self, start: str, goal: str, max_len: int = 4) -> List[Triple]:
        """Cadena de hechos (<= max_len) que enlaza start con goal, por conceptos compartidos."""
        start, goal = start.upper(), goal.upper()
        edges: Dict[str, List[Triple]] = {}
        for f in self.facts:  # los archivados tambien cuentan: si sirven, se restauran (olvido reversible)
            if f.get("neg"):
                continue
            edges.setdefault(f["s"], []).append((f["s"], f["p"], f["o"]))
        queue = deque([(start, [])])
        seen = {start}
        while queue:
            node, route = queue.popleft()
            if node == goal and route:
                return route
            if len(route) >= max_len:
                continue
            for fact in edges.get(node, []):
                if fact[2] not in seen or fact[2] == goal:
                    seen.add(fact[2])
                    queue.append((fact[2], route + [fact]))
        return []

    # ---- lecciones ----------------------------------------------------
    def add_lesson(self, premises: List[Triple], conclusion: Triple) -> bool:
        prem = [list(x.upper() for x in p) for p in premises]
        concl = [x.upper() for x in conclusion]
        for l in self.lessons:
            if l["premises"] == prem and l["conclusion"] == concl:
                l["n"] += 1
                return False
        self.lessons.append({"premises": prem, "conclusion": concl, "t": time.time(), "n": 1, "archived": False})
        return True

    def active_lessons(self) -> List[dict]:
        return [l for l in self.lessons if not l.get("archived")]

    # ---- olvido reversible (curva de olvido, inspirada en memoria-unificada) --------
    def effective_importance(self, fact: dict, tau: float = 20.0) -> float:
        """I * exp(-edad / (tau * I^3)): lo importante o muy usado dura mucho mas."""
        import math
        imp = max(float(fact.get("imp", 1.0)), 0.05)
        age = max(self.tick - int(fact.get("tick", 0)), 0)
        return imp * math.exp(-age / (tau * imp ** 3))

    def touch(self, fact_triple: Triple) -> None:
        """Recordar un hecho lo refuerza y lo restaura si estaba archivado."""
        fact_triple = tuple(x.upper() for x in fact_triple)
        for f in self.facts:
            if (f["s"], f["p"], f["o"]) == fact_triple:
                f["imp"] = float(f.get("imp", 1.0)) + 0.5
                f["tick"] = self.tick
                f["archived"] = False

    def decay(self, tau: float = 20.0, below: float = 0.15, min_age: int = 3) -> int:
        archived = 0
        for f in self.facts:
            if f.get("archived"):
                continue
            if self.tick - int(f.get("tick", 0)) >= min_age and self.effective_importance(f, tau) < below:
                f["archived"] = True
                archived += 1
        return archived

    def summary(self) -> str:
        arch_f = sum(1 for f in self.facts if f.get("archived"))
        arch_l = sum(1 for l in self.lessons if l.get("archived"))
        extra = f" (archivados: {arch_f} hechos, {arch_l} lecciones)" if arch_f or arch_l else ""
        return f"{len(self.concepts)} conceptos, {len(self.facts)} hechos, {len(self.lessons)} lecciones{extra}"
''',
    'src/model/__init__.py': r'''from .reasoner import LatentReasoner
from .decoder import ConceptDecoder
''',
    'src/model/decoder.py': r'''import torch
from src.ontology.concept_space import ConceptSpace

class ConceptDecoder:
    # La Boca: Inactiva durante el pensamiento. Solo traduce a lenguaje si se le pide
    def __init__(self, space: ConceptSpace):
        self.space = space

    def translate_thought(self, vector: torch.Tensor, lang: str = "es") -> dict:
        name, certainty = self.space.find_nearest_concept(vector.cpu())
        human_text = self.space.verbalize(name, lang=lang)
        return {
            "concept": name,
            "certainty": round(certainty * 100, 2),
            "text": human_text,
            "lang": lang
        }
''',
    'src/model/layers.py': r'''import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        var = x.pow(2).mean(-1, keepdim=True)
        return x * torch.rsqrt(var + self.eps) * self.weight


class ContinuousAttention(nn.Module):
    """Atencion causal sobre vectores continuos con mascara de padding."""
    def __init__(self, d_concept: int, n_heads: int, max_len: int, dropout: float = 0.0):
        super().__init__()
        if d_concept % n_heads != 0:
            raise ValueError("d_concept debe ser divisible por n_heads.")
        self.n_heads = n_heads
        self.head_dim = d_concept // n_heads
        self.q = nn.Linear(d_concept, d_concept, bias=False)
        self.k = nn.Linear(d_concept, d_concept, bias=False)
        self.v = nn.Linear(d_concept, d_concept, bias=False)
        self.out = nn.Linear(d_concept, d_concept, bias=False)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, attention_mask: torch.Tensor = None) -> torch.Tensor:
        batch, length, channels = x.shape
        q = self.q(x).view(batch, length, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k(x).view(batch, length, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.v(x).view(batch, length, self.n_heads, self.head_dim).transpose(1, 2)

        scores = (q @ k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        causal = torch.tril(torch.ones(length, length, device=x.device, dtype=torch.bool))
        scores = scores.masked_fill(~causal.view(1, 1, length, length), float("-inf"))
        if attention_mask is not None:
            valid_keys = attention_mask.to(device=x.device, dtype=torch.bool).view(batch, 1, 1, length)
            scores = scores.masked_fill(~valid_keys, float("-inf"))
        probs = self.drop(F.softmax(scores, dim=-1))
        out = (probs @ v).transpose(1, 2).contiguous().view(batch, length, channels)
        return self.out(out)


class ConceptBlock(nn.Module):
    def __init__(self, d_concept: int, n_heads: int, max_len: int, dropout: float):
        super().__init__()
        self.norm1 = RMSNorm(d_concept)
        self.attn = ContinuousAttention(d_concept, n_heads, max_len, dropout)
        self.norm2 = RMSNorm(d_concept)
        self.mlp = nn.Sequential(
            nn.Linear(d_concept, d_concept * 4, bias=False),
            nn.SiLU(),
            nn.Linear(d_concept * 4, d_concept, bias=False),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor, attention_mask: torch.Tensor = None) -> torch.Tensor:
        x = x + self.attn(self.norm1(x), attention_mask=attention_mask)
        x = x + self.mlp(self.norm2(x))
        return x
''',
    'src/model/reasoner.py': r'''import torch
import torch.nn as nn
import torch.nn.functional as F
from configs.config import LCMConfig
from .layers import ConceptBlock, RMSNorm


class LatentReasoner(nn.Module):
    """Razonador con lector de ranuras (parche-11).

    1. LECTOR: cada premisa (sujeto, predicado, objeto fusionados en un vector)
       se desliga en tres ranuras y se limpia contra el catalogo de conceptos
       (resta iterativa: predicado -> sujeto/objeto). No se entrena.
    2. EMPAREJADOR: se calcula que ranuras de una premisa son IGUALES a que
       ranuras de otra (el termino medio de una cadena, la regla enunciada...).
       No depende de que palabras o entidades concretas sean.
    3. RAZONADOR: un Transformer recibe esas pistas y decide, para cada rol de
       la conclusion, de que ranura COPIAR o que constante aprendida usar.
    """
    N_CONST = 16

    def __init__(self, config: LCMConfig):
        super().__init__()
        self.config = config
        d = config.d_concept
        self.input_scale = float(d) ** 0.5
        self.pos_emb = nn.Embedding(config.max_concept_seq, d)
        nn.init.normal_(self.pos_emb.weight, mean=0.0, std=0.02)
        self.match_proj = nn.Linear(9, d, bias=False)
        self.layers = nn.ModuleList([
            ConceptBlock(d, config.n_heads, config.max_concept_seq, config.dropout)
            for _ in range(config.n_layers)
        ])
        self.norm = RMSNorm(d)
        self.slot_head = nn.Linear(d, 9, bias=True)       # por premisa: 3 roles de salida x 3 ranuras
        self.const_head = nn.Linear(d, 3 * self.N_CONST)  # por muestra: roles x constantes
        self.codebook = nn.Parameter(torch.randn(3, self.N_CONST, d) / d ** 0.5)
        # Catalogo y matrices de rol (se rellenan con set_space; viajan en el checkpoint).
        self.register_buffer("roles", torch.eye(d).unsqueeze(0).repeat(3, 1, 1))
        self.register_buffer("concepts", torch.zeros(1, d))

    def set_space(self, space):
        """Carga matrices de rol y catalogo de conceptos de la ontologia."""
        roles = torch.stack([space.role_matrices[r] for r in ("subject", "predicate", "object")])
        emb = F.normalize(space.embeddings.detach().float(), dim=-1)
        device = self.roles.device
        self.roles = roles.to(device).float()
        self.concepts = emb.to(device)

    @torch.no_grad()
    def read_slots(self, x):
        """Devuelve indices (B,L,3) de concepto para sujeto, predicado y objeto."""
        E, R = self.concepts, self.roles
        Rs, Rp, Ro = R[0], R[1], R[2]

        def nearest(vec, role):
            return (F.normalize(vec @ R[role], dim=-1) @ E.T).argmax(-1)

        def proj(vec, idx, role):
            bound = E[idx] @ R[role].T
            return (vec * bound).sum(-1, keepdim=True) * bound

        p = nearest(x, 1)
        rem = x - proj(x, p, 1)
        s = nearest(rem, 0)
        o = nearest(rem - proj(x, s, 0), 2)
        for _ in range(2):
            s = nearest(rem - proj(x, o, 2), 0)
            o = nearest(rem - proj(x, s, 0), 2)
        return torch.stack([s, p, o], dim=-1)

    def forward(self, x, target=None, attention_mask=None):
        if x.ndim != 3:
            raise ValueError("x debe tener forma [batch, secuencia, dimension].")
        batch, length, dim = x.shape
        if dim != self.config.d_concept:
            raise ValueError(f"Dimension recibida {dim}; esperada {self.config.d_concept}.")
        if length < 1 or length > self.config.max_concept_seq:
            raise ValueError(f"La longitud debe estar entre 1 y {self.config.max_concept_seq}.")
        if attention_mask is None:
            attention_mask = torch.ones(batch, length, device=x.device, dtype=torch.bool)
        else:
            attention_mask = attention_mask.to(device=x.device, dtype=torch.bool)
            if attention_mask.shape != (batch, length):
                raise ValueError("attention_mask debe tener forma [batch, secuencia].")
            if torch.any(attention_mask.sum(dim=1) == 0):
                raise ValueError("Cada muestra debe contener al menos una premisa valida.")

        idx = self.read_slots(x)                                   # (B,L,3)
        slots = self.concepts[idx]                                 # (B,L,3,d)
        # Emparejador: eq[b,i,j,a,c] = ranura a de i == ranura c de j (i != j, j valida)
        eq = idx.unsqueeze(2).unsqueeze(4) == idx.unsqueeze(1).unsqueeze(3)   # (B,L,L,3,3)
        other = attention_mask.unsqueeze(1) & ~torch.eye(length, dtype=torch.bool, device=x.device).unsqueeze(0)
        eq = eq & other.unsqueeze(-1).unsqueeze(-1)
        match = eq.any(dim=2).float().view(batch, length, 9)

        positions = torch.arange(length, device=x.device)
        h = x * self.input_scale + self.pos_emb(positions).unsqueeze(0) + self.match_proj(match) * self.input_scale
        for layer in self.layers:
            h = layer(h, attention_mask=attention_mask)
        h = self.norm(h)

        last_valid = attention_mask.long().sum(dim=1) - 1
        pooled = h[torch.arange(batch, device=x.device), last_valid]
        slot_logits = self.slot_head(h).view(batch, length, 3, 3)            # i, rol, ranura
        slot_logits = slot_logits.masked_fill(~attention_mask.view(batch, length, 1, 1), float("-inf"))
        slot_logits = slot_logits.permute(0, 2, 1, 3).reshape(batch, 3, length * 3)
        const_logits = self.const_head(pooled).view(batch, 3, self.N_CONST)
        logits = torch.cat([slot_logits, const_logits], dim=-1)               # (B,3,L*3+K)
        weights = F.softmax(logits, dim=-1)
        cand_slots = slots.reshape(batch, length * 3, dim)
        out = 0
        for role in range(3):
            cands = torch.cat([cand_slots, self.codebook[role].unsqueeze(0).expand(batch, -1, -1)], dim=1)
            role_vec = (weights[:, role].unsqueeze(-1) * cands).sum(dim=1)    # (B,d)
            out = out + role_vec @ self.roles[role].T
        pred_vector = F.normalize(out, p=2, dim=-1)

        loss = None
        if target is not None:
            target = F.normalize(target.to(device=x.device, dtype=pred_vector.dtype), p=2, dim=-1)
            loss = (1.0 - F.cosine_similarity(pred_vector, target, dim=-1)).mean()
        return pred_vector, loss
''',
    'src/ontology/__init__.py': r'''from .concept_space import ConceptSpace
''',
    'src/ontology/concept_space.py': r'''"""Ontologia conceptual con rasgos explicitos y proposiciones componibles.

Importante: los vectores ya no son identificadores aleatorios independientes.
Cada concepto se representa como una combinacion ponderada de rasgos
semanticos declarados. Las matrices de rol distinguen sujeto, predicado y
objeto al construir proposiciones.

Esta ontologia es explicita y auditable; no equivale por si sola a una
representacion semantica universal aprendida de grandes corpus.
"""
from __future__ import annotations

import hashlib
from typing import Dict, Iterable, Mapping, Optional, Tuple
import torch
import torch.nn.functional as F


class ConceptSpace:
    def __init__(self, d_concept: int = 128):
        if d_concept < 16:
            raise ValueError("d_concept debe ser >= 16 para una ontologia util.")
        self.d_concept = int(d_concept)
        self.concept_to_id: Dict[str, int] = {}
        self.id_to_concept: Dict[int, str] = {}
        self.translations: Dict[str, Dict[str, str]] = {}
        self.metadata: Dict[str, dict] = {}
        self.relations = []
        self.embeddings: Optional[torch.Tensor] = None
        self.feature_to_vector: Dict[str, torch.Tensor] = {}
        self.role_matrices: Dict[str, torch.Tensor] = {}
        self.proposition_vectors: Dict[str, torch.Tensor] = {}
        self.proposition_parts: Dict[str, Tuple[str, str, str]] = {}
        self.seed = 42

    @staticmethod
    def _normalise_features(features) -> Dict[str, float]:
        if features is None:
            return {}
        if isinstance(features, Mapping):
            result = {str(k): float(v) for k, v in features.items() if float(v) != 0.0}
        else:
            result = {str(k): 1.0 for k in features}
        if any(not torch.isfinite(torch.tensor(v)) for v in result.values()):
            raise ValueError("Los pesos de los rasgos deben ser finitos.")
        return result

    def register_concept(
        self,
        name: str,
        es_text: str = "",
        en_text: str = "",
        features=None,
        kind: str = "concept",
    ) -> None:
        name = str(name).strip().upper()
        if not name:
            raise ValueError("El nombre de un concepto no puede estar vacio.")
        feats = self._normalise_features(features)
        if not feats:
            # Compatibilidad con llamadas antiguas: no se inventa semantica
            # a partir del idioma; se conserva al menos una identidad estable.
            feats = {f"identity:{name}": 1.0}
        if name in self.concept_to_id:
            cid = self.concept_to_id[name]
            previous = self.metadata[name]["features"]
            if previous != feats:
                raise ValueError(f"El concepto {name} ya existe con otros rasgos.")
            if es_text:
                self.translations[name]["es"] = es_text
            if en_text:
                self.translations[name]["en"] = en_text
            return
        if self.embeddings is not None:
            raise RuntimeError("Registra todos los conceptos antes de build_space().")
        cid = len(self.concept_to_id)
        self.concept_to_id[name] = cid
        self.id_to_concept[cid] = name
        self.translations[name] = {"es": es_text or name, "en": en_text or name}
        self.metadata[name] = {"features": feats, "kind": str(kind)}

    def register_relation(self, subject: str, predicate: str, obj: str) -> None:
        """Registra una relacion simbolica (no crea automaticamente sus nodos)."""
        self.relations.append((str(subject).upper(), str(predicate).upper(), str(obj).upper()))

    def build_space(self, seed: int = 42) -> None:
        if not self.concept_to_id:
            raise RuntimeError("No hay conceptos registrados.")
        self.seed = int(seed)
        generator = torch.Generator(device="cpu")
        generator.manual_seed(self.seed)

        feature_names = sorted({
            feature
            for meta in self.metadata.values()
            for feature in meta["features"]
        })
        # Cada rasgo recibe un vector determinista que depende SOLO de su nombre y de
        # la semilla (parche-12). Asi se pueden anadir conceptos despues de entrenar
        # sin alterar los vectores de los ya existentes.
        self.feature_to_vector = {name: self._feature_vector(name) for name in feature_names}

        rows = []
        for cid in range(len(self.id_to_concept)):
            name = self.id_to_concept[cid]
            feats = self.metadata[name]["features"]
            vector = torch.zeros(self.d_concept)
            for feature, weight in feats.items():
                vector += float(weight) * self.feature_to_vector[feature]
            rows.append(F.normalize(vector, p=2, dim=-1))
        self.embeddings = torch.stack(rows)

        # Transformaciones ortogonales deterministas para codificar los roles.
        role_generator = torch.Generator(device="cpu")
        role_generator.manual_seed(self.seed + 104729)
        self.role_matrices = {}
        for role in ("subject", "predicate", "object"):
            raw = torch.randn(self.d_concept, self.d_concept, generator=role_generator)
            q, _ = torch.linalg.qr(raw)
            self.role_matrices[role] = q.contiguous()

        self.proposition_vectors = {}
        self.proposition_parts = {}

    def _feature_vector(self, feature: str) -> torch.Tensor:
        digest = hashlib.sha256(f"{self.seed}:{feature}".encode("utf-8")).hexdigest()
        generator = torch.Generator(device="cpu")
        generator.manual_seed(int(digest[:12], 16))
        return F.normalize(torch.randn(self.d_concept, generator=generator), p=2, dim=-1)

    def add_concept(self, name: str, es_text: str = "", en_text: str = "", features=None,
                    kind: str = "concept") -> int:
        """Anade un concepto NUEVO a un espacio ya construido (catalogo abierto).

        Los vectores existentes no cambian. Despues hay que llamar a
        model.set_space(space) para que el lector de ranuras conozca el concepto."""
        if self.embeddings is None:
            raise RuntimeError("Ejecuta build_space() antes de add_concept().")
        name = str(name).strip().upper()
        if not name:
            raise ValueError("El nombre de un concepto no puede estar vacio.")
        if name in self.concept_to_id:
            return self.concept_to_id[name]
        feats = self._normalise_features(features) or {f"identity:{name}": 1.0}
        vector = torch.zeros(self.d_concept)
        for feature, weight in feats.items():
            if feature not in self.feature_to_vector:
                self.feature_to_vector[feature] = self._feature_vector(feature)
            vector += float(weight) * self.feature_to_vector[feature]
        cid = len(self.concept_to_id)
        self.concept_to_id[name] = cid
        self.id_to_concept[cid] = name
        self.translations[name] = {"es": es_text or name, "en": en_text or name}
        self.metadata[name] = {"features": feats, "kind": str(kind)}
        self.embeddings = torch.cat([self.embeddings, F.normalize(vector, p=2, dim=-1).unsqueeze(0)], dim=0)
        return cid

    def get_vector(self, name: str) -> torch.Tensor:
        name = str(name).strip().upper()
        if name in self.concept_to_id:
            if self.embeddings is None:
                raise RuntimeError("Ejecuta build_space() antes de solicitar vectores.")
            return self.embeddings[self.concept_to_id[name]].clone()
        if name in self.proposition_vectors:
            return self.proposition_vectors[name].clone()
        raise KeyError(f"Concepto o proposicion no registrado: {name}")

    @staticmethod
    def proposition_label(subject: str, predicate: str, obj: str) -> str:
        return f"{subject.upper()}::{predicate.upper()}::{obj.upper()}"

    def encode_proposition(self, subject: str, predicate: str, obj: str) -> torch.Tensor:
        """Compone (sujeto, predicado, objeto) en un vector con roles."""
        if self.embeddings is None or not self.role_matrices:
            raise RuntimeError("Ejecuta build_space() antes de codificar proposiciones.")
        s, p, o = subject.upper(), predicate.upper(), obj.upper()
        label = self.proposition_label(s, p, o)
        if label not in self.proposition_vectors:
            vector = (
                self.role_matrices["subject"] @ self.get_vector(s)
                + self.role_matrices["predicate"] @ self.get_vector(p)
                + self.role_matrices["object"] @ self.get_vector(o)
            )
            self.proposition_vectors[label] = F.normalize(vector, p=2, dim=-1).cpu()
            self.proposition_parts[label] = (s, p, o)
        return self.proposition_vectors[label].clone()

    def find_nearest_concept(self, vector: torch.Tensor) -> tuple:
        """Devuelve la etiqueta mas proxima y su similitud coseno.

        El segundo valor es similitud geometrica, NO una probabilidad ni una
        certeza calibrada.
        """
        if self.embeddings is None:
            raise RuntimeError("Ejecuta build_space() antes de buscar conceptos.")
        query = F.normalize(vector.detach().view(1, -1).float().cpu(), p=2, dim=-1)
        candidates = [self.embeddings]
        labels = [self.id_to_concept[i] for i in range(len(self.id_to_concept))]
        if self.proposition_vectors:
            prop_labels = sorted(self.proposition_vectors)
            candidates.append(torch.stack([self.proposition_vectors[k] for k in prop_labels]))
            labels.extend(prop_labels)
        matrix = torch.cat(candidates, dim=0)
        similarities = query @ matrix.t()
        best_id = int(torch.argmax(similarities, dim=-1).item())
        return labels[best_id], float(similarities[0, best_id].item())

    def verbalize(self, name: str, lang: str = "es") -> str:
        name = str(name).upper()
        if name in self.proposition_parts:
            s, p, o = self.proposition_parts[name]
            if lang == "en":
                return f"{s} {p} {o}"
            return f"{s} {p} {o}"
        return self.translations.get(name, {}).get(lang, f"[{name}]")

    def list_concepts(self, limit: Optional[int] = None):
        names = list(self.concept_to_id)
        return names if limit is None else names[:limit]

''',
    'src/reasoning/__init__.py': r'''from .engine import ReasoningEngine
from .rule_engine import Fact, RuleEngine

__all__ = ["ReasoningEngine", "Fact", "RuleEngine"]
''',
    'src/reasoning/coherence.py': r'''"""Coherencia de la memoria (parche-57, bloque D): cambio de estado y contradicciones.
- Relaciones que solo valen para UN valor a la vez (vivir en, trabajar en, estar en, estar + estado): un hecho nuevo
  sustituye al viejo, que pasa a PASADO (no se borra: "¿donde vivia Ana?").
- Contradicciones que no se pueden resolver solas (dos adjetivos opuestos con "ser", afirmar y negar lo mismo): se pregunta.
"""
import re
from typing import List, Optional, Tuple

from src.language.lexicon import norm

ANTONYMS = [("grande", "pequeno"), ("alto", "bajo"), ("feliz", "triste"), ("contento", "triste"), ("rapido", "lento"), ("caliente", "frio"),
            ("nuevo", "viejo"), ("limpio", "sucio"), ("lleno", "vacio"), ("fuerte", "debil"), ("bueno", "malo"), ("joven", "viejo"),
            ("rico", "pobre"), ("abierto", "cerrado"), ("vivo", "muerto"), ("enfermo", "sano"), ("claro", "oscuro"), ("largo", "corto"),
            ("gordo", "delgado"), ("ancho", "estrecho"), ("duro", "blando"), ("facil", "dificil"), ("seco", "mojado"), ("cerca", "lejos")]
FUNCTIONAL = ("VIVIR_EN", "TRABAJAR_EN", "ESTAR_EN", "ESTUDIAR_EN", "ESTAR")
_STEM = re.compile(r"(os|as|es|o|a|e|s)$")


def stem(word: str) -> str:
    return _STEM.sub("", norm(word))


def opposite(a: str, b: str, extra=()) -> bool:
    sa, sb = stem(a), stem(b)
    return any({stem(x), stem(y)} == {sa, sb} for x, y in list(ANTONYMS) + [tuple(e) for e in extra])


def classify(facts: List[dict], triple: Tuple[str, str, str], neg: bool, has_time: bool = False,
             ya_no: bool = False, extra=()) -> Tuple[str, Optional[dict]]:
    """-> (tipo, hecho_viejo): 'supersede' | 'negation' | 'antonym' | ('', None)."""
    s, p, o = (x.upper() for x in triple)
    for f in facts:
        same = (f["s"], f["p"], f["o"]) == (s, p, o)
        if same and bool(f.get("neg")) != neg:
            if neg and ya_no and p in FUNCTIONAL:
                return "supersede_neg", f                     # "Pedro ya no trabaja en X": el viejo pasa a pasado
            return "negation", f
    if neg or has_time:
        return "", None
    for f in facts:
        if f["s"] != s or f.get("neg") or f.get("when") or (f["p"], f["o"]) == (p, o):
            continue
        if p in FUNCTIONAL and f["p"] == p and f["o"] != o:
            return "supersede", f
        if p in ("SER", "ESTAR") and f["p"] in ("SER", "ESTAR") and opposite(f["o"], o, extra):
            return ("supersede" if p == "ESTAR" and f["p"] == "ESTAR" else "antonym"), f
    return "", None


def to_past(mem, old: dict, until_iso: str) -> None:
    """Quita el hecho de los vigentes y lo guarda como pasado."""
    mem.facts = [f for f in mem.facts if f is not old]
    old = dict(old)
    old["until"] = until_iso
    if not hasattr(mem, "past"):
        mem.past = []
    mem.past.append(old)
''',
    'src/reasoning/efectos.py': r'''"""Efectos de las acciones elementales (parche-59, bloque C): lo que cambia cuando alguien da, vende, compra, abre, rompe, llega...
Recibe los hechos de UNA frase [(s, p, o, o_disp)] y devuelve operaciones:
   ("add", (s, p, o))   hecho nuevo (pasa por la coherencia: si cambia un estado, el viejo pasa a pasado)
   ("lose", (s, p, o))  el hecho deja de valer (pasa a pasado)
"""
from typing import List, Tuple

GAIN = {"comprar", "recibir", "ganar", "encontrar", "conseguir", "coger", "heredar"}                 # el sujeto pasa a tener el objeto
LOSE = {"perder", "tirar"}                                                                         # el sujeto deja de tenerlo
GIVE = {"dar", "regalar", "entregar", "prestar", "vender", "devolver", "ofrecer", "enviar", "mandar", "pasar"}   # el sujeto lo pierde y el destinatario lo gana
STATE = {"abrir": "abierto", "cerrar": "cerrado", "romper": "roto", "encender": "encendido", "apagar": "apagado",
         "terminar": "terminado", "arreglar": "arreglado", "llenar": "lleno", "vaciar": "vacio", "limpiar": "limpio",
         "ensuciar": "sucio", "mojar": "mojado", "secar": "seco"}
ARRIVE = {"ir_a", "llegar_a", "volver_a", "venir_a", "entrar_en", "viajar_a", "regresar_a"}
LEAVE = {"salir_de"}


def _inflect(adj: str, disp: str) -> str:
    d = (disp or "").lower().strip()
    fem = d.startswith(("la ", "una ", "las ", "unas ")) or (d.endswith("a") and not d.startswith(("el ", "un ", "los ")) and not d.endswith("ma"))
    plural = d.startswith(("las ", "los ", "unas ", "unos "))
    if adj.endswith("o"):
        adj = adj[:-1] + ("a" if fem else "o")
    return adj + ("s" if plural else "")


def effects(facts: List[Tuple[str, str, str, str]]) -> List[Tuple[str, Tuple[str, str, str]]]:
    ops = []
    facts = [(s, p.lower(), o, od) for s, p, o, od in facts]          # think da los nombres en MAYUSCULAS
    objs = {}
    for s, p, o, od in facts:
        if "_" not in p:
            objs.setdefault((s, p), (o, od))
    for s, p, o, od in facts:
        verb = p.lower().partition("_")[0] if "_" in p and p.lower() not in ARRIVE | LEAVE else p.lower()
        if p.lower() in ARRIVE:
            ops.append(("add", (s, "estar_en", o)))
            continue
        if p.lower() in LEAVE:
            ops.append(("lose", (s, "estar_en", o)))
            continue
        if "_" in p:                                    # "dar_a luis": se combina con el objeto del mismo verbo
            base, _, prep = p.lower().partition("_")
            if prep == "a" and (s, base) in objs:
                x = objs[(s, base)][0]
                if base in GIVE and base != "devolver":
                    ops.append(("add", (o, "tener", x)))
                elif base == "devolver":
                    ops.append(("add", (o, "tener", x)))
                elif base == "comprar":                 # "compra un coche a Luis": Luis lo pierde
                    ops.append(("lose", (o, "tener", x)))
            continue
        if o in ("", "_"):
            continue
        if verb in GAIN:
            ops.append(("add", (s, "tener", o)))
        elif verb in LOSE or verb in GIVE:
            ops.append(("lose", (s, "tener", o)))
        elif verb in STATE:
            ops.append(("add", (o, "estar", _inflect(STATE[verb], od))))
    return ops
''',
    'src/reasoning/engine.py': r'''import torch
from src.ontology.concept_space import ConceptSpace
from src.model.reasoner import LatentReasoner
from src.reasoning.rule_engine import Fact, RuleEngine


class ReasoningEngine:
    """Interfaz neuronal y simbolica del LCM."""
    def __init__(self, model: LatentReasoner, space: ConceptSpace, device: str = "cpu"):
        self.model = model.to(device)
        self.space = space
        self.device = device
        self.model.eval()
        self.rule_engine = RuleEngine()

    def think(self, premise_names: list, steps: int = 1) -> list:
        vectors = [self.space.get_vector(name) for name in premise_names]
        return self.think_vectors(vectors, steps=steps)

    def think_vectors(self, premise_vectors: list, steps: int = 1) -> list:
        if not premise_vectors:
            raise ValueError("Se necesita al menos una premisa.")
        if steps < 1:
            raise ValueError("steps debe ser >= 1.")
        history = []
        context = [torch.as_tensor(v, dtype=torch.float32).cpu() for v in premise_vectors]
        max_len = self.model.config.max_concept_seq
        with torch.no_grad():
            for _ in range(steps):
                selected = context[-max_len:]
                inp = torch.stack(selected).unsqueeze(0).to(self.device)
                mask = torch.ones(1, inp.shape[1], dtype=torch.bool, device=self.device)
                next_vec, _ = self.model(inp, attention_mask=mask)
                next_vec_cpu = next_vec.squeeze(0).cpu()
                history.append(next_vec_cpu)
                context.append(next_vec_cpu)
        return history

    def deduce(self, facts):
        """Cierre simbolico de hechos; util para pruebas y trazabilidad."""
        return self.rule_engine.infer(facts)
''',
    'src/reasoning/lessons.py': r'''"""Deduccion con las lecciones aprendidas (parche-47, Fase 2). Sin red neuronal: se generaliza cada leccion a una regla con variables
("Ana es madre de Luis => Luis es hijo de Ana"  ->  "?0 madre_de ?1 => ?1 hijo_de ?0") y se aplica a los hechos de la memoria,
guardando de que hechos sale cada conclusion para poder explicarla ("lo deduzco de ...")."""
from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Sequence, Tuple

Triple = Tuple[str, str, str]


def generalize(lesson: dict, is_var: Callable[[str], bool] = lambda n: True):
    mapping: Dict[str, str] = {}
    prem = []
    for p in lesson["premises"]:
        t = []
        for slot, x in enumerate(p):
            x = x.upper()
            if slot != 1 and x.startswith("?"):
                mapping.setdefault(x, x)
            elif slot != 1 and is_var(x):
                mapping.setdefault(x, f"?{len(mapping)}")
                x = mapping[x]
            t.append(x)
        prem.append(tuple(t))
    concl = tuple(mapping.get(x.upper(), x.upper()) if i != 1 else x.upper() for i, x in enumerate(lesson["conclusion"]))
    return prem, concl


def _matches(prem: Sequence[Triple], known: Sequence[Triple], bind: Dict[str, str], used: List[Triple]):
    if not prem:
        yield dict(bind), list(used)
        return
    s, p, o = prem[0]
    for f in known:
        if f[1] != p:
            continue
        new, ok = dict(bind), True
        for term, val in ((s, f[0]), (o, f[2])):
            if term.startswith("?"):
                if term in new:
                    ok &= new[term] == val
                else:
                    ok &= val not in new.values()          # variables distintas -> entidades distintas
                    new[term] = val
            else:
                ok &= term == val
            if not ok:
                break
        if ok:
            yield from _matches(prem[1:], known, new, used + [f])


# Regla general que no hace falta ensenar: la jerarquia "A es B, B es C => A es C" (parche-50)
DEFAULT_LESSONS = [{"premises": [["?A", "ES", "?B"], ["?B", "ES", "?C"]], "conclusion": ["?A", "ES", "?C"], "archived": False}]


def _r(prem, concl):
    return {"premises": [list(x) for x in prem], "conclusion": list(concl), "archived": False}


# Reglas de fabrica de parentesco y partes (parche-59): no hace falta ensenarlas
FAMILY_LESSONS = (
    [_r([("?A", x, "?B")], ("?B", "HIJO_DE", "?A")) for x in ("PADRE_DE", "MADRE_DE")]
    + [_r([("?A", x, "?B"), ("?B", y, "?C")], ("?A", "ABUELO_DE" if x == "PADRE_DE" else "ABUELA_DE", "?C"))
       for x in ("PADRE_DE", "MADRE_DE") for y in ("PADRE_DE", "MADRE_DE")]
    + [_r([("?A", x, "?B")], ("?B", "NIETO_DE", "?A")) for x in ("ABUELO_DE", "ABUELA_DE")]
    + [_r([("?A", x, "?B")], ("?B", "HERMANO_DE", "?A")) for x in ("HERMANO_DE", "HERMANA_DE")]
    + [_r([("?P", x, "?A"), ("?P", x, "?B")], ("?A", "HERMANO_DE", "?B")) for x in ("PADRE_DE", "MADRE_DE")]
    + [_r([("?A", h, "?B"), ("?B", x, "?C")], ("?A", "TIO_DE" if h == "HERMANO_DE" else "TIA_DE", "?C"))
       for h in ("HERMANO_DE", "HERMANA_DE") for x in ("PADRE_DE", "MADRE_DE")]
    + [_r([("?A", t, "?C"), ("?A", x, "?D")], ("?C", "PRIMO_DE", "?D")) for t in ("TIO_DE", "TIA_DE") for x in ("PADRE_DE", "MADRE_DE")]
    + [_r([("?A", "PRIMO_DE", "?B")], ("?B", "PRIMO_DE", "?A"))]
    + [_r([("?A", "ESPOSO_DE", "?B")], ("?B", "ESPOSA_DE", "?A")), _r([("?A", "ESPOSA_DE", "?B")], ("?B", "ESPOSO_DE", "?A")),
       _r([("?A", "MARIDO_DE", "?B")], ("?B", "ESPOSA_DE", "?A")), _r([("?A", "MUJER_DE", "?B")], ("?B", "ESPOSO_DE", "?A"))]
    + [_r([("?A", "PARTE_DE", "?B"), ("?B", "PARTE_DE", "?C")], ("?A", "PARTE_DE", "?C")),
       _r([("?A", "PARTE_DE", "?B")], ("?B", "TENER", "?A"))]
)
DEFAULT_LESSONS = DEFAULT_LESSONS + FAMILY_LESSONS


def apply_lessons(facts: Iterable[Triple], lessons: Sequence[dict], is_var: Callable[[str], bool] = lambda n: True,
                  rounds: int = 3, cap: int = 200, defaults: bool = True) -> Dict[Triple, List[Triple]]:
    """Devuelve {conclusion: [hechos de los que sale]} para lo que se deduce y no estaba ya."""
    known = {tuple(x.upper() for x in f) for f in facts}
    rules = [generalize(l, is_var) for l in list(lessons) + (DEFAULT_LESSONS if defaults else []) if not l.get("archived")]
    derived: Dict[Triple, List[Triple]] = {}
    for _ in range(rounds):
        new = {}
        for prem, concl in rules:
            for bind, used in _matches(prem, sorted(known), {}, []):
                out = tuple(bind.get(x, x) for x in concl)
                if any(x.startswith("?") for x in out) or out in known or out in derived or out in new:
                    continue
                new[out] = used
        if not new:
            break
        derived.update(new)
        known |= set(new)
        if len(derived) >= cap:
            break
    return derived


def canon(name: str) -> str:
    """Forma comparable sin plural: POLIGONOS -> POLIGONO, ANIMALES -> ANIMAL (solo para comparar clases con sus miembros)."""
    w = name.upper()
    if w.endswith("CES"):
        return w[:-3] + "Z"
    if w.endswith("ES") and len(w) > 4 and w[-3] not in "AEIOU":
        return w[:-2]
    if w.endswith("S") and len(w) > 3:
        return w[:-1]
    return w


def inherit(facts: Iterable[Triple], rounds: int = 6) -> Dict[Triple, List[Triple]]:
    """Herencia (parche-52): "Los poligonos tienen lados" + "Un triangulo es un poligono" => "el triangulo tiene lados".
    Solo hacia abajo (de la clase al miembro, tambien por cadenas de ES); el miembro hereda lo de TODAS sus clases.
    Devuelve {hecho deducido: [hecho de la clase, cadena de ES]}."""
    facts = [tuple(x.upper() for x in f) for f in facts]
    known = set(facts)
    parents: Dict[str, List[Triple]] = {}
    for f in facts:
        if f[1] == "ES":
            parents.setdefault(canon(f[0]), []).append(f)
    props: Dict[str, List[Triple]] = {}
    for f in facts:
        if f[1] != "ES":
            props.setdefault(canon(f[0]), []).append(f)
    derived: Dict[Triple, List[Triple]] = {}
    for member in {f[0] for f in facts if f[1] == "ES"}:
        stack, seen = [(canon(member), [])], {canon(member)}
        while stack:
            node, chain = stack.pop()
            for es in parents.get(node, []):
                cls = canon(es[2])
                if cls in seen:
                    continue
                seen.add(cls)
                path = chain + [es]
                for prop in props.get(cls, []):
                    new = (member, prop[1], prop[2])
                    if new not in known and new not in derived:
                        derived[new] = [prop] + path
                stack.append((cls, path))
    return derived


def compare(facts: Iterable[Triple]) -> Dict[Triple, List[Triple]]:
    """Comparaciones (parche-56): "Luis es mas alto que Pedro" = (LUIS, MAS_ALTO_QUE, PEDRO).
    Inversa (Pedro MENOS_ALTO_QUE Luis) y transitividad (Luis > Pedro > Juan => Luis > Juan)."""
    facts = [tuple(x.upper() for x in f) for f in facts]
    known = set(facts)
    pairs: Dict[str, Dict[tuple, List[Triple]]] = {}
    for f in facts:
        if f[1].startswith(("MAS_", "MENOS_")) and f[1].endswith("_QUE"):
            pairs.setdefault(f[1], {})[(f[0], f[2])] = [f]
    for p_, d in list(pairs.items()):
        kind, rest = p_.split("_", 1)
        inv = ("MENOS_" if kind == "MAS" else "MAS_") + rest
        for (a, b), sup in list(d.items()):
            pairs.setdefault(inv, {}).setdefault((b, a), sup)
    changed = True
    while changed:
        changed = False
        for p_, d in pairs.items():
            for (a, b), s1 in list(d.items()):
                for (c, e), s2 in list(d.items()):
                    if b == c and a != e and (a, e) not in d:
                        d[(a, e)] = [(a, p_, b), (b, p_, e)]
                        changed = True
    out: Dict[Triple, List[Triple]] = {}
    for p_, d in pairs.items():
        for (a, b), sup in d.items():
            if (a, p_, b) not in known:
                out[(a, p_, b)] = sup
    return out


def verb_derive(facts, verb_isa) -> Dict[Triple, List[Triple]]:
    """Verbos ensenados ("Cocinar es preparar comida"): si Pedro cocina pasta, tambien prepara pasta."""
    out: Dict[Triple, List[Triple]] = {}
    for f in facts:
        head, _, suf = f[1].partition("_")
        cur, seen = head.lower(), set()
        while cur in verb_isa and cur not in seen:
            seen.add(cur)
            cur = verb_isa[cur].lower()
            out.setdefault((f[0], cur.upper() + ("_" + suf if suf else ""), f[2]), [tuple(f)])
    return out


def deduce_all(facts: Iterable[Triple], lessons: Sequence[dict], is_var: Callable[[str], bool] = lambda n: True) -> Dict[Triple, List[Triple]]:
    facts = list(facts)
    out = apply_lessons(facts, lessons, is_var)
    for k, v in inherit(facts).items():
        out.setdefault(k, v)
    for k, v in compare(facts).items():
        out.setdefault(k, v)
    return out
''',
    'src/reasoning/rule_engine.py': r'''"""Motor simbolico minimo para contrastar las predicciones neuronales.

No sustituye al modelo neuronal: define reglas auditables y un oraculo de
referencia para comprobar que las pruebas realmente contienen inferencias.
"""
from dataclasses import dataclass
from typing import Iterable, Set


@dataclass(frozen=True, order=True)
class Fact:
    subject: str
    predicate: str
    obj: str

    def __post_init__(self):
        object.__setattr__(self, "subject", self.subject.upper())
        object.__setattr__(self, "predicate", self.predicate.upper())
        object.__setattr__(self, "obj", self.obj.upper())


class RuleEngine:
    def __init__(self, max_iterations: int = 32):
        self.max_iterations = max_iterations

    @staticmethod
    def _coerce(facts: Iterable) -> Set[Fact]:
        result = set()
        for fact in facts:
            if isinstance(fact, Fact):
                result.add(fact)
            elif isinstance(fact, (tuple, list)) and len(fact) == 3:
                result.add(Fact(*fact))
            else:
                raise TypeError(f"Formato de hecho no reconocido: {fact!r}")
        return result

    def infer(self, facts: Iterable[Fact]):
        known = self._coerce(facts)
        iterations = 0
        for iteration in range(self.max_iterations):
            additions = set()
            by_subject_predicate = {}
            by_predicate = {}
            for fact in known:
                by_subject_predicate.setdefault((fact.subject, fact.predicate), set()).add(fact.obj)
                by_predicate.setdefault(fact.predicate, []).append(fact)

            # 1) Transitividad: A > B y B > C => A > C.
            greater = by_predicate.get("MAYOR_QUE", [])
            outgoing = {}
            for fact in greater:
                outgoing.setdefault(fact.subject, set()).add(fact.obj)
            for first in greater:
                for end in outgoing.get(first.obj, ()):
                    if first.subject != end:
                        additions.add(Fact(first.subject, "MAYOR_QUE", end))

            # 2) Caida: liberado en aire + sometido a gravedad.
            released = by_predicate.get("LIBERADO_EN", [])
            gravity = by_predicate.get("SOMETIDO_A", [])
            gravity_subjects = {f.subject for f in gravity if f.obj == "GRAVEDAD"}
            for fact in released:
                if fact.obj == "AIRE" and fact.subject in gravity_subjects:
                    additions.add(Fact(fact.subject, "CAE_HACIA", "SUELO"))

            # 3) Fusion: requiere evidencia de que la sustancia es fundible.
            exposed = by_predicate.get("EXPUESTO_A", [])
            meltable = {f.subject for f in by_predicate.get("ES", []) if f.obj == "FUNDIBLE"}
            for fact in exposed:
                if fact.obj == "CALOR" and fact.subject in meltable:
                    additions.add(Fact(fact.subject, "CAMBIA_A", "LIQUIDO"))

            # 4) Cardinalidad: finito implica enumerable.
            finite = by_predicate.get("ES_FINITO", [])
            for fact in finite:
                if fact.obj == "TRUE":
                    additions.add(Fact(fact.subject, "ES", "ENUMERABLE"))
                    additions.add(Fact(fact.subject, "TIENE_CARDINALIDAD_FINITA", "TRUE"))

            # 5) Infinito numerable/no numerable: exige evidencia de biyeccion
            # (o de su inexistencia), no basta con afirmar que es infinito.
            infinite = {f.subject for f in by_predicate.get("ES_INFINITO", []) if f.obj == "TRUE"}
            bijective = {f.subject for f in by_predicate.get("TIENE_BIYECCION_CON", []) if f.obj == "NATURALES"}
            non_bijective = {f.subject for f in by_predicate.get("NO_TIENE_BIYECCION_CON", []) if f.obj == "NATURALES"}
            for subject in infinite & bijective:
                additions.add(Fact(subject, "ES", "INFINITO_NUMERABLE"))
                additions.add(Fact(subject, "ES", "ENUMERABLE"))
            for subject in infinite & non_bijective:
                additions.add(Fact(subject, "ES", "INNUMERABLE"))

            # 7) Contradicciones en MAYOR_QUE: A>B y B>A, o ciclos A>B>C>A.
            reach = {}
            for fact in greater:
                reach.setdefault(fact.subject, set()).add(fact.obj)
            for a_node, nexts in reach.items():
                for b_node in nexts:
                    if a_node in reach.get(b_node, ()):
                        additions.add(Fact(a_node, "CONTRADICE", b_node))
                    for c_node in reach.get(b_node, ()):
                        if a_node in reach.get(c_node, ()):
                            additions.add(Fact(a_node, "CONTRADICE", a_node))

            # 6) Herencia con la regla enunciada como hecho:
            #    (HP REGLA_HEREDA HA), (X HP P), (P HA Q)  =>  (X HP Q)
            for rule in by_predicate.get("REGLA_HEREDA", []):
                hp, ha = rule.subject, rule.obj
                for first in by_predicate.get(hp, []):
                    for q in by_subject_predicate.get((first.obj, ha), ()):
                        additions.add(Fact(first.subject, hp, q))

            additions -= known
            if not additions:
                break
            known.update(additions)
            iterations = iteration + 1
        return {"facts": known, "iterations": iterations}


def run_reference_tests():
    engine = RuleEngine()
    cases = {}

    result = engine.infer([
        Fact("ALFA_NUEVO", "MAYOR_QUE", "BETA_NUEVO"),
        Fact("BETA_NUEVO", "MAYOR_QUE", "GAMMA_NUEVO"),
    ])
    cases["transitivity_unseen_entities"] = Fact("ALFA_NUEVO", "MAYOR_QUE", "GAMMA_NUEVO") in result["facts"]

    result = engine.infer([
        Fact("DRON_NUEVO", "LIBERADO_EN", "AIRE"),
        Fact("DRON_NUEVO", "SOMETIDO_A", "GRAVEDAD"),
    ])
    cases["gravity_unseen_entity"] = Fact("DRON_NUEVO", "CAE_HACIA", "SUELO") in result["facts"]

    result = engine.infer([Fact("CONJUNTO_F", "ES_FINITO", "TRUE")])
    cases["finite_implies_countable"] = Fact("CONJUNTO_F", "ES", "ENUMERABLE") in result["facts"]

    result = engine.infer([
        Fact("CONJUNTO_C", "ES_INFINITO", "TRUE"),
        Fact("CONJUNTO_C", "TIENE_BIYECCION_CON", "NATURALES"),
    ])
    cases["bijection_implies_countably_infinite"] = Fact("CONJUNTO_C", "ES", "INFINITO_NUMERABLE") in result["facts"]

    result = engine.infer([
        Fact("CONJUNTO_N", "ES_INFINITO", "TRUE"),
        Fact("CONJUNTO_N", "NO_TIENE_BIYECCION_CON", "NATURALES"),
    ])
    cases["explicit_no_bijection_implies_uncountable"] = Fact("CONJUNTO_N", "ES", "INNUMERABLE") in result["facts"]

    result = engine.infer([Fact("INFINITO_SIN_MAS", "ES_INFINITO", "TRUE")])
    cases["infinite_alone_not_uncountable"] = Fact("INFINITO_SIN_MAS", "ES", "INNUMERABLE") not in result["facts"]

    result = engine.infer([
        Fact("CERA_NUEVA", "EXPUESTO_A", "CALOR"),
        Fact("CERA_NUEVA", "ES", "FUNDIBLE"),
    ])
    cases["melting_requires_fusible_evidence"] = Fact("CERA_NUEVA", "CAMBIA_A", "LIQUIDO") in result["facts"]
    result = engine.infer([Fact("MATERIAL_DESCONOCIDO", "EXPUESTO_A", "CALOR")])
    cases["heat_alone_does_not_imply_melting"] = Fact("MATERIAL_DESCONOCIDO", "CAMBIA_A", "LIQUIDO") not in result["facts"]

    return {"passed": sum(bool(v) for v in cases.values()), "total": len(cases), "cases": cases}

''',
    'src/training/__init__.py': r'''from .trainer import ConceptTrainer
''',
    'src/training/online.py': r'''"""Aprendizaje al vuelo con repaso y guardia contra el olvido (parche-13).

Medido (ver scripts/evaluate_online.py): ajustar el modelo SOLO con ejemplos
nuevos aprende la regla en pocos ejemplos pero destruye lo anterior (olvido
catastrofico). Mezclar ejemplos antiguos en cada paso (repaso) conserva todo.
La guardia comprueba un conjunto "canario" tras cada actualizacion y revierte
si algo importante se ha roto.
"""
from __future__ import annotations

import copy
from typing import List, Sequence, Tuple

import random

import torch

Triple = Tuple[str, str, str]
Lesson = Tuple[Sequence[Triple], Triple]


class OnlineLearner:
    def __init__(self, model, space, core_pool, canary, device="cpu",
                 lr: float = 1e-3, steps: int = 120, replay_batch: int = 64,
                 canary_min: float = 0.98, use_negatives: bool = True):
        self.model, self.space, self.device = model, space, device
        self.core = tuple(t.cpu() for t in core_pool)       # (X, M, Y) del entrenamiento original
        self.canary = tuple(t.to(device) for t in canary)
        self.lr, self.steps, self.replay_batch, self.canary_min = lr, steps, replay_batch, canary_min
        self.lessons: List[Lesson] = []
        self.use_negatives = use_negatives
        self.neg_exclude = set()          # relaciones que NO se usan como negativos (para medir generalizacion)
        self._safe = (-1, [])
        self.rng = random.Random(0)

    # ---- utilidades ---------------------------------------------------
    def encode(self, lessons: Sequence[Lesson]):
        length = self.model.config.max_concept_seq
        X = torch.zeros(len(lessons), length, self.space.d_concept)
        M = torch.zeros(len(lessons), length, dtype=torch.bool)
        Y = []
        for i, (premises, conclusion) in enumerate(lessons):
            for j, premise in enumerate(premises):
                X[i, j] = self.space.encode_proposition(*premise)
                M[i, j] = True
            Y.append(self.space.encode_proposition(*conclusion))
        from ..memory.negatives import purge_ghosts
        purge_ghosts(self.space)            # las relaciones fantasma solo viven durante la codificacion
        return X, M, torch.stack(Y)

    @torch.no_grad()
    def exact(self, X, M, Y) -> float:
        was_training = self.model.training
        self.model.eval()
        X, M, Y = X.to(self.device), M.to(self.device), Y.to(self.device)
        pred, _ = self.model(X, attention_mask=M)
        got = self.model.read_slots(pred.unsqueeze(1))[:, 0]
        want = self.model.read_slots(Y.unsqueeze(1))[:, 0]
        self.model.train(was_training)
        return float((got == want).all(dim=-1).float().mean().item())

    def entities(self):
        from ..memory.schema import is_entity
        return [n for n in self.space.concept_to_id if is_entity(self.space, n)]

    def safe(self):
        from ..memory.negatives import safe_predicates
        if self._safe[0] != len(self.space.concept_to_id):
            self._safe = (len(self.space.concept_to_id), safe_predicates(self.space))
        return [q for q in self._safe[1] if q not in self.neg_exclude]

    def negatives(self, lessons, n: int = 200):
        """Casos hermanos donde la regla NO aplica (parche-20). Devuelve tensores (X, M, Y) o None."""
        if not self.use_negatives or not lessons:
            return None
        from ..memory.negatives import make_negatives
        negs = make_negatives(self.space, lessons, n, self.rng, self.entities(), self.safe(), ghost_exclude=self.neg_exclude)
        return self.encode(negs) if negs else None

    def canary_score(self) -> float:
        return self.exact(*self.canary)

    # ---- aprendizaje --------------------------------------------------
    def learn(self, lessons: Sequence[Lesson], replay_core: bool = True,
              replay_lessons: bool = True, guard: bool = True) -> dict:
        new = self.encode(lessons)
        past = self.encode(self.lessons) if (replay_lessons and self.lessons) else None
        neg = self.negatives(list(self.lessons) + list(lessons))
        reps = max(1, -(-16 // len(new[0])))                  # las lecciones nuevas pesan lo mismo que sus negativos
        new_train = tuple(t.repeat(reps, *([1] * (t.dim() - 1))) for t in new)
        snapshot = copy.deepcopy(self.model.state_dict())
        before = self.exact(*new)
        self.model.train()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=0.0)
        for _round in range(6 if neg is not None else 3):  # mas rondas si aun no acierta la propia leccion
            for _ in range(self.steps):
                parts = [new_train]
                if replay_core:
                    j = torch.randint(0, len(self.core[0]), (self.replay_batch,))
                    parts.append(tuple(t[j] for t in self.core))
                if past is not None:
                    j = torch.randint(0, len(past[0]), (min(self.replay_batch, len(past[0])),))
                    parts.append(tuple(t[j] for t in past))
                if neg is not None:
                    j = torch.randint(0, len(neg[0]), (min(32, len(neg[0])),))
                    parts.append(tuple(t[j] for t in neg))
                X, M, Y = (torch.cat([p[k] for p in parts]).to(self.device) for k in range(3))
                _, loss = self.model(X, target=Y, attention_mask=M)
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
            self.model.eval()
            if self.exact(*new) >= 1.0:
                break
            self.model.train()
        self.model.eval()
        after = self.exact(*new)
        canary = self.canary_score()
        accepted = True
        if guard and canary < self.canary_min:
            self.model.load_state_dict(snapshot)   # revertir: no se rompe lo ya sabido
            accepted = False
        elif accepted:
            self.lessons.extend(lessons)
        return {"accepted": accepted, "before": before, "after": after, "canary": canary}

    def inoculate(self, preds, n: int = 240, steps: int = 60, lr: float = 5e-4) -> dict:
        """Relaciones NUEVAS (parche-33): ensena en el momento que, mientras no haya una regla, X <relacion> Y no concluye nada.
        Casos negativos con solo esas relaciones + repaso de fabrica y de lecciones; si el canario baja, se revierte."""
        preds = [q for q in preds if q in self.space.concept_to_id]
        if not preds or not self.lessons:
            return {"done": False, "reason": "sin lecciones o sin relaciones nuevas"}
        from ..memory.negatives import make_negatives
        negs = make_negatives(self.space, self.lessons, n, self.rng, self.entities(), preds, ghosts=0.0)
        if not negs:
            return {"done": False, "reason": "sin negativos"}
        neg = self.encode(negs)
        own = self.encode(self.lessons)
        from ..memory.schema import induce, instantiate
        schemas = {}
        for prem, concl in self.lessons:
            sc = induce(self.space, [tuple(x) for x in prem], tuple(concl))
            schemas[sc.signature] = sc
        ents = self.entities()
        banks = [self.encode([instantiate(self.space, sc, self.rng, ents) for _ in range(200)]) for sc in schemas.values()]
        snapshot = copy.deepcopy(self.model.state_dict())
        self.model.train()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=0.0)
        for _ in range(steps):
            parts = []
            j = torch.randint(0, len(self.core[0]), (self.replay_batch,))
            parts.append(tuple(t[j] for t in self.core))
            j = torch.randint(0, len(own[0]), (min(self.replay_batch, len(own[0])),))
            parts.append(tuple(t[j] for t in own))
            j = torch.randint(0, len(neg[0]), (min(48, len(neg[0])),))
            parts.append(tuple(t[j] for t in neg))
            for X_, M_, Y_ in banks:                    # "suenos": la regla debe seguir generalizando a gente nueva
                j = torch.randint(0, len(X_), (24,))
                parts.append((X_[j], M_[j], Y_[j]))
            X, M, Y = (torch.cat([p[k] for p in parts]).to(self.device) for k in range(3))
            _, loss = self.model(X, target=Y, attention_mask=M)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            optimizer.step()
        self.model.eval()
        canary = self.canary_score()
        if canary < self.canary_min:
            self.model.load_state_dict(snapshot)
            return {"done": False, "reason": f"revertido (canario {canary:.0%})", "canary": canary}
        return {"done": True, "canary": canary, "lessons": self.exact(*own)}
''',
    'src/training/trainer.py': r'''import os
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from configs.config import TrainConfig
from src.model.reasoner import LatentReasoner


class ConceptTrainer:
    def __init__(
        self,
        model: LatentReasoner,
        config: TrainConfig,
        loader: DataLoader,
        val_loader: DataLoader = None,
    ):
        self.config = config
        self.model = model.to(config.device)
        self.loader = loader
        self.val_loader = val_loader
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(), lr=config.learning_rate, weight_decay=1e-4
        )
        # Tasa de aprendizaje decreciente: evita los picos de perdida a mitad de entrenamiento.
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=config.epochs, eta_min=config.learning_rate * 0.02
        )
        os.makedirs(config.checkpoint_dir, exist_ok=True)
        self.best_val_loss = float("inf")

    @staticmethod
    def _unpack(batch):
        if len(batch) == 3:
            seq, mask, target = batch
        elif len(batch) == 2:  # Compatibilidad con datasets antiguos.
            seq, target = batch
            mask = torch.ones(seq.shape[:2], dtype=torch.bool)
        else:
            raise ValueError("Cada lote debe contener (secuencia, mascara, objetivo).")
        return seq, mask, target

    def _run_epoch(self, loader, training: bool) -> float:
        self.model.train(training)
        total_loss = 0.0
        total_items = 0
        context = torch.enable_grad() if training else torch.no_grad()
        with context:
            iterator = tqdm(loader, desc="Entrenando" if training else "Validando", leave=False)
            for batch in iterator:
                seq, mask, target = self._unpack(batch)
                seq = seq.to(self.config.device)
                mask = mask.to(self.config.device)
                target = target.to(self.config.device)
                _, loss = self.model(seq, target=target, attention_mask=mask)
                if loss is None or not torch.isfinite(loss):
                    raise RuntimeError("Loss no finita; revisa los datos y las mascaras.")
                if training:
                    self.optimizer.zero_grad(set_to_none=True)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.grad_clip)
                    self.optimizer.step()
                size = int(seq.shape[0])
                total_loss += float(loss.detach().item()) * size
                total_items += size
                iterator.set_postfix(loss=f"{loss.item():.4f}")
        return total_loss / max(total_items, 1)

    def save_checkpoint(self, epoch: int, train_loss: float, val_loss: float):
        path = os.path.join(self.config.checkpoint_dir, "lcm_reasoner.pt")
        tmp_path = path + ".tmp"
        torch.save({
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "train_loss": train_loss,
            "val_loss": val_loss,
            "config": {
                "d_concept": self.model.config.d_concept,
                "n_layers": self.model.config.n_layers,
                "n_heads": self.model.config.n_heads,
                "max_concept_seq": self.model.config.max_concept_seq,
                "dropout": self.model.config.dropout,
            },
        }, tmp_path)
        os.replace(tmp_path, path)

    def train(self):
        print(f"[*] Entrenamiento conceptual en [{self.config.device.upper()}]")
        history = []
        patience_left = self.config.patience
        for epoch in range(1, self.config.epochs + 1):
            train_loss = self._run_epoch(self.loader, training=True)
            val_loss = self._run_epoch(self.val_loader, training=False) if self.val_loader else train_loss
            self.scheduler.step()
            history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
            print(
                f"[E{epoch:03d}] train_loss={train_loss:.5f} | "
                f"val_loss={val_loss:.5f}"
            )
            improved = val_loss < (self.best_val_loss - 1e-6)
            if improved:
                self.best_val_loss = val_loss
                self.save_checkpoint(epoch, train_loss, val_loss)
                patience_left = self.config.patience
            else:
                patience_left -= 1
            if self.val_loader and patience_left <= 0:
                print("[*] Early stopping: la validacion no mejora.")
                break
        if not os.path.exists(os.path.join(self.config.checkpoint_dir, "lcm_reasoner.pt")):
            self.save_checkpoint(len(history), history[-1]["train_loss"], history[-1]["val_loss"])
        return history

''',
    'tests/test_cantidad.py': r'''from src.reasoning.lessons import compare, inherit


def test_comparaciones_inversa_y_transitiva():
    f = [("LUIS", "MAS_ALTO_QUE", "PEDRO"), ("PEDRO", "MAS_ALTO_QUE", "JUAN")]
    got = compare(f)
    assert ("LUIS", "MAS_ALTO_QUE", "JUAN") in got
    assert ("JUAN", "MENOS_ALTO_QUE", "LUIS") in got
    assert ("JUAN", "MAS_ALTO_QUE", "LUIS") not in got


def test_extractor_causa_y_cuantificador():
    from src.language.extract import triples_full
    t = [("Ana", "PROPN", 2, "nsubj", "ana"), ("llora", "VERB", 0, "root", "llorar"), ("porque", "SCONJ", 5, "mark", "porque"),
         ("está", "AUX", 5, "cop", "estar"), ("triste", "ADJ", 2, "advcl", "triste"), (".", "PUNCT", 2, "punct", ".")]
    out = {(x["s"], x["p"]) for x in triples_full(t)}
    assert ("ana", "llorar") in out and ("ana", "llorar_porque") in out
    t = [("Algunos", "DET", 2, "det", "alguno"), ("pájaros", "NOUN", 3, "nsubj", "pajaro"), ("vuelan", "VERB", 0, "root", "volar"), (".", "PUNCT", 3, "punct", ".")]
    assert triples_full(t)[0]["q"] == "algunos"
    t = [("Ninguna", "DET", 2, "det", "ninguno"), ("rana", "NOUN", 4, "nsubj", "rana"), ("es", "AUX", 4, "cop", "ser"), ("mamífero", "NOUN", 0, "root", "mamifero"), (".", "PUNCT", 4, "punct", ".")]
    assert triples_full(t)[0]["neg"] is True
''',
    'tests/test_coherencia.py': r'''from src.reasoning.coherence import classify, opposite, to_past
from src.memory.store import MemoryStore


def F(s, p, o, neg=False, when=""):
    return {"s": s, "p": p, "o": o, "neg": neg, "when": when}


def test_cambio_de_estado():
    k, old = classify([F("ANA", "VIVIR_EN", "MADRID")], ("ana", "vivir_en", "sevilla"), False)
    assert k == "supersede" and old["o"] == "MADRID"
    assert classify([F("ANA", "VIVIR_EN", "MADRID")], ("ana", "trabajar_en", "sevilla"), False)[0] == ""
    assert classify([F("ANA", "VIVIR_EN", "MADRID", when="2020")], ("ana", "vivir_en", "sevilla"), False)[0] == ""


def test_contradicciones():
    assert classify([F("LUIS", "AMAR_A", "ANA")], ("luis", "amar_a", "ana"), True)[0] == "negation"
    assert classify([F("CASA", "SER", "GRANDE")], ("casa", "ser", "pequena"), False)[0] == "antonym"
    assert opposite("alta", "bajo") and not opposite("alto", "rojo")
    assert classify([F("PEDRO", "VIVIR_EN", "X")], ("pedro", "vivir_en", "x"), True, ya_no=True)[0] == "supersede_neg"


def test_pasado(tmp_path):
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("ana", "vivir_en", "madrid"))
    to_past(m, m.facts[0], "2026-11-06")
    assert not m.facts and m.past[0]["until"] == "2026-11-06"
''',
    'tests/test_definiciones.py': r'''from src.reasoning.coherence import opposite
from src.reasoning.lessons import verb_derive


def test_contrarios_ensenados():
    assert not opposite("ruidoso", "silencioso")
    assert opposite("ruidoso", "silencioso", [["ruidoso", "silencioso"]])


def test_verbo_definido_se_hereda():
    out = verb_derive([("PEDRO", "COCINAR", "PASTA")], {"cocinar": "preparar"})
    assert ("PEDRO", "PREPARAR", "PASTA") in out
    out = verb_derive([("PEDRO", "COCINAR_QUE", "X")], {"cocinar": "preparar"})
    assert ("PEDRO", "PREPARAR_QUE", "X") in out
''',
    'tests/test_dialogue.py': r'''from src.language.dialogue import Dialogue, n, _article
from src.memory.store import MemoryStore


def mk(tmp_path):
    return Dialogue(MemoryStore(str(tmp_path / "m.json")))


def test_social(tmp_path):
    d = mk(tmp_path)
    assert d.act("Hola", None)[0].startswith("¡Hola")
    assert d.act("¡Gracias!", None)[0] == "De nada."
    assert d.act("Perdona", None)[0] == "No pasa nada."
    assert n("¿Qué día es hoy?") == "que dia es hoy"


def test_name_and_possessive(tmp_path):
    d = mk(tmp_path)
    reply, cont = d.act("Mi madre es Ana.", None)
    assert "cómo te llamas" in reply.lower() and cont is None
    reply, cont = d.act("Me llamo Marcos", None)
    assert cont == "La madre de Marcos es Ana."


def test_references(tmp_path):
    d = mk(tmp_path)
    d.user = "Marcos"
    assert d.act("Ese perro muerde a Pedro.", None)[1] == "El perro muerde a Pedro."
    assert d.act("Javier tampoco compró pan.", None)[1] == "Javier no compró pan."
    assert d.act("Ana también compró pan.", None)[1] == "Ana compró pan."
    assert _article("madre") == "la" and _article("hermano") == "el"


def test_ask_unknown_and_define(tmp_path):
    d = mk(tmp_path)
    assert "explicas" in d.act("¿Qué es un tenedor?", None)[0]
    assert d.act("Es un cubierto", None)[1] == "Un tenedor es un cubierto."
''',
    'tests/test_discourse.py': r'''from src.language.discourse import next_topic, parse_text, split_sentences
from src.language.extract import surface, triples_full


def test_split():
    assert split_sentences("Ana vive en Madrid. Trabaja en un banco.") == ["Ana vive en Madrid.", "Trabaja en un banco."]


def test_dropped_subject_takes_topic():
    # Trabaja en un banco .
    T = [("Trabaja", "VERB", 0, "root", "trabajar"), ("en", "ADP", 4, "case", "en"), ("un", "DET", 4, "det", "uno"),
         ("banco", "NOUN", 1, "obl", "banco"), (".", "PUNCT", 1, "punct", ".")]
    assert triples_full(T, entities_only=True) == []
    (t,) = triples_full(T, entities_only=True, default_subject="ana")
    assert (t["s"], t["p"], t["o"]) == ("ana", "trabajar_en", "banco") and surface(T, t) == {}


def test_pronoun_replaced_by_topic():
    # Ella toca la guitarra .
    T = [("Ella", "PROPN", 2, "nsubj", "ella"), ("toca", "VERB", 0, "root", "tocar"), ("la", "DET", 4, "det", "el"),
         ("guitarra", "NOUN", 2, "obj", "guitarra"), (".", "PUNCT", 2, "punct", ".")]
    assert triples_full(T, entities_only=True)[0]["s"] == "ella"
    assert triples_full(T, entities_only=True, default_subject="sara")[0]["s"] == "sara"


def test_subordinate_verb_without_subject_is_not_given_topic():
    T = [("Quiero", "VERB", 0, "root", "querer"), ("que", "SCONJ", 3, "mark", "que"), ("vengas", "VERB", 1, "ccomp", "venir"),
         (".", "PUNCT", 1, "punct", ".")]
    assert triples_full(T, entities_only=True, default_subject="ana") == []


class Stub:
    def parse(self, sent, topic=None):
        if sent.startswith("Ana"):
            return [{"s": "ana", "p": "vivir_en", "o": "madrid", "neg": False}]
        return [{"s": topic, "p": "trabajar_en", "o": "banco", "neg": False}]


def test_parse_text_carries_topic():
    out = parse_text(Stub(), "Ana vive en Madrid. Trabaja en un banco.")
    assert [t["s"] for t in out] == ["ana", "ana"]
    assert next_topic([{"s": "el"}], "ana") == "ana"


def test_pronoun_tagged_det_or_pron():
    for upos in ("DET", "PRON"):
        T = [("Él", upos, 2, "nsubj", "el"), ("lee", "VERB", 0, "root", "leer"), ("el", "DET", 4, "det", "el"),
             ("periódico", "NOUN", 2, "obj", "periodico"), (".", "PUNCT", 2, "punct", ".")]
        assert [t["s"] for t in triples_full(T, entities_only=True, default_subject="pedro")] == ["pedro"]
        assert triples_full(T, entities_only=True) == []


def test_target_tree_supports_irregular_verb_and_rejects_copular(monkeypatch):
    from src.language.school_learn import target_tree

    class M:  # modelo falso: predict_trees se sustituye
        pass
    import src.language.school_learn as sl
    monkeypatch.setattr(sl, "predict_trees", lambda model, forms, device, scripts: [[("PROPN", 0, "root", "x"), ("NOUN", 1, "flat", "x"), ("NOUN", 1, "flat", "x"), ("PUNCT", 1, "punct", ".")]])
    tree, why = target_tree(M(), "cpu", [], "Andrés cocina pasta.", ("ANDRES", "COCINAR", "PASTA"))
    assert tree is not None and tree[1][3] == "root" and tree[0][3] == "nsubj" and tree[2][3] == "obj"
    tree, why = target_tree(M(), "cpu", [], "Ana es madre de Luis.", ("ANA", "ES", "LUIS"))
    assert tree is None and "copulativas" in why
''',
    'tests/test_estados.py': r'''from src.language.extract import triples_full
from src.language.irregulares import IRREG
from src.language.school_parser import SchoolParser


def tree(rows):
    return [tuple(r) for r in rows]


def test_irregulares():
    assert IRREG["duerme"] == "dormir" and IRREG["puede"] == "poder" and IRREG["vino"] == "venir"
    assert "se" not in IRREG and "como" not in IRREG


def test_nombre_mas_verbo_en_minusculas():
    rows = [("Ana", "PROPN", 0, "root", "ana"), ("duerme", "PROPN", 1, "flat", "duerme"), (".", "PUNCT", 1, "punct", ".")]
    fixed = SchoolParser._fix_name_verb(rows)
    assert fixed[1][1] == "VERB" and fixed[1][3] == "root" and fixed[0][3] == "nsubj"


def test_intransitivo_y_adjetivo():
    t = tree([("Luis", "PROPN", 2, "nsubj", "luis"), ("llegó", "VERB", 0, "root", "llegar"), (".", "PUNCT", 2, "punct", ".")])
    assert [(x["s"], x["p"], x["o"]) for x in triples_full(t)] == [("luis", "llegar", "_")]
    t = tree([("La", "DET", 2, "det", "el"), ("casa", "NOUN", 4, "nsubj", "casa"), ("es", "AUX", 4, "cop", "ser"),
              ("grande", "ADJ", 0, "root", "grande"), (".", "PUNCT", 4, "punct", ".")])
    assert [(x["s"], x["p"], x["o"]) for x in triples_full(t)] == [("casa", "ser", "grande")]
''',
    'tests/test_extract.py': r'''from src.language.extract import surface, triples_full


def test_svo_and_negation():
    T = [("Luis", "PROPN", 3, "nsubj", "luis"), ("no", "ADV", 3, "advmod", "no"), ("come", "VERB", 0, "root", "comer"),
         ("carne", "NOUN", 3, "obj", "carne"), (".", "PUNCT", 3, "punct", ".")]
    (tr,) = triples_full(T, entities_only=True)
    assert (tr["s"], tr["p"], tr["o"], tr["neg"]) == ("luis", "comer", "carne", True)
    assert surface(T, tr)["template"] == "{s} come {o}"


def test_copular_with_preposition():
    T = [("Sara", "PROPN", 4, "nsubj", "sara"), ("es", "AUX", 4, "cop", "ser"), ("la", "DET", 4, "det", "el"),
         ("profesora", "NOUN", 0, "root", "profesora"), ("de", "ADP", 6, "case", "de"), ("Pablo", "PROPN", 4, "nmod", "pablo"),
         (".", "PUNCT", 4, "punct", ".")]
    (tr,) = triples_full(T, entities_only=True)
    assert tr["p"] == "profesora_de" and surface(T, tr)["o_disp"] == "Pablo"


def test_adjective_as_object():
    T = [("Hugo", "PROPN", 2, "nsubj", "hugo"), ("estudia", "VERB", 0, "root", "estudiar"),
         ("matemáticas", "ADJ", 2, "obj", "matematico"), (".", "PUNCT", 2, "punct", ".")]
    (tr,) = triples_full(T, entities_only=True)
    assert (tr["s"], tr["p"], tr["o"]) == ("hugo", "estudiar", "matematicas")


def _tr(T, **kw):
    return sorted((t["s"], t["p"], t["o"], t["neg"]) for t in triples_full(T, entities_only=True, **kw))


def test_coordinated_subjects():
    # Pedro y Marta viven en Madrid .
    T = [("Pedro", "PROPN", 4, "nsubj", "pedro"), ("y", "CCONJ", 3, "cc", "y"), ("Marta", "PROPN", 1, "conj", "marta"),
         ("viven", "VERB", 0, "root", "vivir"), ("en", "ADP", 6, "case", "en"), ("Madrid", "PROPN", 4, "obl", "madrid"),
         (".", "PUNCT", 4, "punct", ".")]
    assert _tr(T) == [("marta", "vivir_en", "madrid", False), ("pedro", "vivir_en", "madrid", False)]
    assert _tr(T, coordination=False) == [("pedro", "vivir_en", "madrid", False)]
    assert surface(T, triples_full(T, entities_only=True)[0]) == {}


def test_coordinated_objects_and_verbs():
    # Luis compro pan y leche y vende coches .
    T = [("Luis", "PROPN", 2, "nsubj", "luis"), ("compró", "VERB", 0, "root", "comprar"), ("pan", "NOUN", 2, "obj", "pan"),
         ("y", "CCONJ", 4, "cc", "y"), ("leche", "NOUN", 3, "conj", "leche"), ("y", "CCONJ", 7, "cc", "y"),
         ("vende", "VERB", 2, "conj", "vender"), ("coches", "NOUN", 7, "obj", "coche"), (".", "PUNCT", 2, "punct", ".")]
    assert _tr(T) == [("luis", "comprar", "leche", False), ("luis", "comprar", "pan", False), ("luis", "vender", "coches", False)]


def test_coordinated_oblique_shares_preposition():
    # Alba vive con su abuela y su tio .
    T = [("Alba", "PROPN", 2, "nsubj", "alba"), ("vive", "VERB", 0, "root", "vivir"), ("con", "ADP", 5, "case", "con"),
         ("su", "DET", 5, "det", "su"), ("abuela", "NOUN", 2, "obl", "abuela"), ("y", "CCONJ", 8, "cc", "y"),
         ("su", "DET", 8, "det", "su"), ("tío", "NOUN", 5, "conj", "tio"), (".", "PUNCT", 2, "punct", ".")]
    assert _tr(T) == [("alba", "vivir_con", "abuela", False), ("alba", "vivir_con", "tio", False)]


def test_capitalised_adjective_as_name():
    T = [("Clara", "ADJ", 2, "nsubj", "claro"), ("canta", "VERB", 0, "root", "cantar"), ("en", "ADP", 5, "case", "en"),
         ("el", "DET", 5, "det", "el"), ("coro", "NOUN", 2, "obl", "coro"), (".", "PUNCT", 2, "punct", ".")]
    assert _tr(T) == [("clara", "cantar_en", "coro", False)]
    T[0] = ("claro", "ADJ", 2, "nsubj", "claro")
    assert _tr(T) == []
''',
    'tests/test_fechas.py': r'''from datetime import date

from src.language.fechas import resolve, fmt, extract_abs, before, after

HOY = date(2026, 11, 6)      # viernes


def test_relativos():
    assert fmt(resolve("ayer", HOY)) == "5 de noviembre de 2026"
    assert fmt(resolve("anteayer", HOY)) == "4 de noviembre de 2026"
    assert fmt(resolve("lunes", HOY)) == "2 de noviembre de 2026"
    assert fmt(resolve("ano_pasado", HOY)) == "2025"
    assert fmt(resolve("diciembre", HOY)) == "diciembre de 2025"


def test_fecha_escrita_y_orden():
    clean, iv, disp = extract_abs("Ana llegó el 3 de diciembre de 2024.", HOY)
    assert clean == "Ana llegó." and fmt(iv) == "3 de diciembre de 2024"
    assert before(resolve("lunes", HOY), resolve("ayer", HOY))
    assert after(resolve("ayer", HOY), resolve("lunes", HOY))
    assert resolve("pronto", HOY) is None
''',
    'tests/test_nucleo.py': r'''from src.reasoning.efectos import effects
from src.reasoning.lessons import apply_lessons


def test_dar_y_vender():
    ops = effects([("ANA", "dar", "libro", "un libro"), ("ANA", "dar_a", "LUIS", "Luis")])
    assert ("lose", ("ANA", "tener", "libro")) in ops and ("add", ("LUIS", "tener", "libro")) in ops
    ops = effects([("LUIS", "comprar", "bicicleta", "una bicicleta")])
    assert ops == [("add", ("LUIS", "tener", "bicicleta"))]


def test_estados_con_genero():
    assert effects([("ANA", "abrir", "puerta", "la puerta")]) == [("add", ("puerta", "estar", "abierta"))]
    assert effects([("ANA", "romper", "vaso", "el vaso")]) == [("add", ("vaso", "estar", "roto"))]
    assert effects([("ANA", "ir_a", "MADRID", "Madrid")]) == [("add", ("ANA", "estar_en", "MADRID"))]


def test_parentesco_de_fabrica():
    got = apply_lessons([("PEDRO", "PADRE_DE", "ANA"), ("ANA", "MADRE_DE", "LUIS")], [])
    assert ("PEDRO", "ABUELO_DE", "LUIS") in got and ("LUIS", "NIETO_DE", "PEDRO") in got and ("LUIS", "HIJO_DE", "ANA") in got
    got = apply_lessons([("MARTA", "HERMANA_DE", "ROSA"), ("ROSA", "MADRE_DE", "PACO")], [])
    assert ("MARTA", "TIA_DE", "PACO") in got
    got = apply_lessons([("RUEDA", "PARTE_DE", "COCHE"), ("COCHE", "PARTE_DE", "FLOTA")], [])
    assert ("RUEDA", "PARTE_DE", "FLOTA") in got
''',
    'tests/test_qa.py': r'''from src.language.qa import QA, is_question, rewrite, same_pred
from src.memory.store import MemoryStore


def stub(table):
    def parse(sentence):
        return table.get(sentence)
    return parse


def mem(tmp_path):
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("marta", "escribir", "novela"))
    m.note_surface(("marta", "escribir", "novela"), "{s} escribió {o}", "Marta", "una novela")
    m.add_fact(("pedro", "vivir_en", "madrid"))
    m.note_surface(("pedro", "vivir_en", "madrid"), "{s} vive en {o}", "Pedro", "Madrid")
    m.add_fact(("luis", "comer", "carne"), neg=True)
    m.note_surface(("luis", "comer", "carne"), "{s} come {o}", "Luis", "carne")
    return m


def t(s, p, o, neg=False):
    return {"s": s, "p": p, "o": o, "neg": neg}


def test_is_question():
    assert is_question("¿Quién vive en Madrid?") and is_question("Vive Pedro en Madrid?")
    assert not is_question("Pedro vive en Madrid.")


def test_rewrite_kinds():
    assert rewrite("¿Quién escribió una novela?")[0][0] == "Xqx escribió una novela."
    assert rewrite("¿Qué escribió Marta?")[0][-1] == "Marta escribió Xqx."
    assert rewrite("¿A quién llamó Pedro?")[0][0] == "Pedro llamó a Xqx."
    c, k = rewrite("¿Vive Pedro en Madrid?")
    assert k == "si_no" and "Pedro vive en Madrid." in c


def test_same_pred():
    assert same_pred("escribir", "escribio") and same_pred("vivir_en", "VIVIR_EN")
    assert not same_pred("vivir_en", "vivir_con") and same_pred("conocer_a", "conocer")


def test_answers(tmp_path):
    m = mem(tmp_path)
    parse = stub({
        "Xqx escribió una novela.": [t("xqx", "escribir", "novela")],
        "Marta escribió Xqx.": [t("marta", "escribir", "xqx")],
        "Pedro vive en Madrid.": [t("pedro", "vivir_en", "madrid")],
        "Luis come carne.": [t("luis", "comer", "carne")],
        "Pedro vive en Sevilla.": [t("pedro", "vivir_en", "sevilla")],
        "Ana vive en Madrid.": [t("ana", "vivir_en", "madrid")],
    })
    qa = QA(m, parse)
    assert "Marta escribió una novela" in qa.answer("¿Quién escribió una novela?")
    assert "una novela" in qa.answer("¿Qué escribió Marta?")
    assert qa.answer("¿Pedro vive en Madrid?").startswith("Sí")
    assert qa.answer("¿Luis come carne?").startswith("No.")
    assert "No lo sé" in qa.answer("¿Ana vive en Madrid?") or "no me consta" in qa.answer("¿Ana vive en Madrid?")
    assert "No he entendido" in qa.answer("¿Cosa rara?")


def test_deduction_is_labelled(tmp_path):
    m = mem(tmp_path)
    parse = stub({"Pedro vive en Sevilla.": [t("pedro", "vivir_en", "sevilla")]})
    qa = QA(m, parse, deduce=lambda facts: {("PEDRO", "VIVIR_EN", "SEVILLA")})
    assert "deduzco" in qa.answer("¿Pedro vive en Sevilla?")


def test_memory_roundtrip(tmp_path):
    m = mem(tmp_path)
    m.save()
    m2 = MemoryStore(str(tmp_path / "m.json"))
    assert m2.surface["ESCRIBIR"] == "{s} escribió {o}" and m2.display["MARTA"] == "Marta"


def test_irregular_lemma_rescued_by_surface_form(tmp_path):
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("perro", "muerder_a", "cartero"))
    m.note_surface(("perro", "muerder_a", "cartero"), "{s} muerde a {o}", "el perro", "el cartero")
    q = {"s": "xqx", "p": "mendar_a", "o": "cartero", "neg": False, "template": "{s} muerde a {o}"}
    qa = QA(m, lambda x: [q] if x.startswith("Xqx") else None)
    assert "perro" in qa.answer("¿Quién muerde al cartero?")


def test_yesno_with_article_and_alternative_hole(tmp_path):
    c, k = rewrite("¿Enseña la maestra matemáticas?")
    assert "la maestra enseña matemáticas." in c
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("rosa", "leer", "libro"))
    m.note_surface(("rosa", "leer", "libro"), "{s} lee {o}", "Rosa", "un libro")
    qa = QA(m, lambda x: [t("rosa", "leer", "zurita")] if x == "Rosa lee Zurita." else None)    # Xqx no se lee, Zurita si
    assert "libro" in qa.answer("¿Qué lee Rosa?")


def test_lessons_deduction():
    from src.reasoning.lessons import apply_lessons
    lesson = {"premises": [["ANA", "MADRE_DE", "LUIS"]], "conclusion": ["LUIS", "HIJO_DE", "ANA"], "archived": False}
    d = apply_lessons([("MARTA", "MADRE_DE", "PABLO")], [lesson])
    assert d == {("PABLO", "HIJO_DE", "MARTA"): [("MARTA", "MADRE_DE", "PABLO")]}
    assert apply_lessons([("PABLO", "HIJO_DE", "MARTA")], [lesson]) == {}          # no al reves
    two = {"premises": [["A", "PADRE_DE", "B"], ["B", "PADRE_DE", "C"]], "conclusion": ["A", "ABUELO_DE", "C"]}
    assert ("X", "ABUELO_DE", "Z") in apply_lessons([("X", "PADRE_DE", "Y"), ("Y", "PADRE_DE", "Z")], [two])


def test_yesno_prefers_reading_that_memory_recognises(tmp_path):
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("marta", "madre_de", "pablo"))
    table = {"Es Marta madre de Pablo.": [t("marta", "es", "madre")], "Marta es madre de Pablo.": [t("marta", "madre_de", "pablo")]}
    assert QA(m, lambda x: table.get(x)).answer("¿Es Marta madre de Pablo?").startswith("Sí")


def test_template_from_sentence_and_names():
    from src.language.qa import template_from
    assert template_from("Luis es hijo de Ana", "LUIS", "ANA") == ("{s} es hijo de {o}", "Luis", "Ana")
    assert template_from("Pedro compró un coche", "PEDRO", "COCHE") == ("{s} compró un {o}", "Pedro", "coche")
    assert template_from("Ana es Ana", "ANA", "ANA") is None


def test_default_verbalisation_capitalised(tmp_path):
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("marta", "madre_de", "pablo"))
    assert QA(m, lambda x: None).say(("PABLO", "HIJO_DE", "MARTA")).startswith("Pablo")


def test_time_expressions_extract_and_answer(tmp_path):
    from src.language.extract import triples_full, surface
    T = [("Pedro", "PROPN", 2, "nsubj", "pedro"), ("compró", "VERB", 0, "root", "comprar"), ("pan", "NOUN", 2, "obj", "pan"),
         ("ayer", "ADV", 2, "advmod", "ayer"), (".", "PUNCT", 2, "punct", ".")]
    (tr,) = triples_full(T, entities_only=True)
    assert (tr["s"], tr["p"], tr["o"], tr["when"], tr["when_disp"]) == ("pedro", "comprar", "pan", "ayer", "ayer")
    assert surface(T, tr)["template"] == "{s} compró {o}"
    # "en enero" no es un lugar: no genera comprar_en
    T2 = [("Luis", "PROPN", 2, "nsubj", "luis"), ("visitó", "VERB", 0, "root", "visitar"), ("Roma", "PROPN", 2, "obj", "roma"),
          ("en", "ADP", 5, "case", "en"), ("enero", "NOUN", 2, "obl", "enero"), (".", "PUNCT", 2, "punct", ".")]
    found = triples_full(T2, entities_only=True)
    assert [(t["p"], t["when"]) for t in found] == [("visitar", "enero")]
    m = MemoryStore(str(tmp_path / "m.json"))
    m.add_fact(("pedro", "comprar", "pan"), when="ayer", when_disp="ayer")
    m.note_surface(("pedro", "comprar", "pan"), "{s} compró {o}", "Pedro", "pan")
    table = {"Pedro compró pan.": [t("pedro", "comprar", "pan")],
             "Pedro compró pan ayer.": [dict(t("pedro", "comprar", "pan"), when="ayer")],
             "Pedro compró pan hoy.": [dict(t("pedro", "comprar", "pan"), when="hoy")]}
    qa = QA(m, lambda x: table.get(x))
    assert "ayer" in qa.answer("¿Cuándo compró Pedro pan?")
    assert qa.answer("¿Compró Pedro pan ayer?").startswith("Sí")
    assert qa.answer("¿Compró Pedro pan hoy?").startswith("No.")


def test_canon_plural():
    from src.reasoning.lessons import canon
    assert canon("POLIGONOS") == canon("POLIGONO") == "POLIGONO"
    assert canon("ANIMALES") == "ANIMAL"


def test_inherit_down_chain_not_up():
    from src.reasoning.lessons import inherit
    f = [("POLIGONOS", "TENER", "LADOS"), ("TRIANGULO", "ES", "POLIGONO"), ("POLIGONO", "ES", "FIGURA")]
    got = inherit(f)
    assert ("TRIANGULO", "TENER", "LADOS") in got
    assert ("FIGURA", "TENER", "LADOS") not in got
''',
    'tests/test_reproducibilidad.py': r'''import os
import subprocess
import sys

from scripts.manifiesto import sha, tracked


def test_huellas_estables(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hola", encoding="utf-8")
    assert sha(str(f)) == sha(str(f)) and len(sha(str(f))) == 64


def test_se_vigila_el_codigo_y_no_los_pesos():
    files = tracked()
    assert "src/language/qa.py" in files and "data/semilla.txt" in files
    assert not any(f.startswith("checkpoints/") or f.endswith((".pkl", ".pt")) or f.startswith("data/ud/") for f in files)


def test_empaquetado_ida_y_vuelta(tmp_path):
    out = tmp_path / "todo.py"
    r = subprocess.run([sys.executable, "-m", "scripts.empaquetar_todo", "--salida", str(out)], capture_output=True, text=True, cwd=os.getcwd())
    assert r.returncode == 0, r.stderr
    dest = tmp_path / "nuevo"
    dest.mkdir()
    r = subprocess.run([sys.executable, str(out)], capture_output=True, text=True, cwd=dest)
    assert r.returncode == 0, r.stderr
    for f in ("src/language/qa.py", "data/semilla.txt", "scripts/reproduce.py", "tests/test_nucleo.py"):
        assert (dest / f).read_text(encoding="utf-8") == open(f, encoding="utf-8").read()


def test_el_constructor_trae_el_menu(tmp_path):
    out = tmp_path / "todo.py"
    subprocess.run([sys.executable, "-m", "scripts.empaquetar_todo", "--salida", str(out)], check=True, capture_output=True)
    src = out.read_text(encoding="utf-8")
    assert "def menu()" in src and "--sin-menu" in src and "--todo" in src
    r = subprocess.run([sys.executable, str(out), "--sin-menu"], capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 0 and (tmp_path / "src" / "language" / "qa.py").exists()


def test_limpieza_se_empaqueta_y_compila():
    assert "limpieza.py" in tracked()
    compile(open("limpieza.py", encoding="utf-8").read(), "limpieza.py", "exec")
''',
}


# ----------------------------------------------------------------------------------------------------------------------
# Asistente interactivo (solo biblioteca estandar). Uso:
#   python LCM_construir_desde_cero.py                  -> escribe los archivos y abre el menu
#   python LCM_construir_desde_cero.py --sin-menu       -> solo escribe los archivos
#   python LCM_construir_desde_cero.py --todo [--libro mi_texto.txt] [--rapido] [--semilla N]   -> hace todo en orden, sin preguntar
# ----------------------------------------------------------------------------------------------------------------------
import argparse
import os
import subprocess

ROOT = Path.cwd()
LIBROS = ("regenta.rtf", "regenta.txt", "libro.txt", "libro.rtf")
OPT = {"libro": None, "rapido": False, "semilla": None}


def write_files():
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    wrote = same = 0
    for rel, content in FILES.items():
        if content.startswith("\0b64:"):
            content = base64.b64decode(content[5:]).decode("utf-8")
        path = ROOT / rel
        if path.exists():
            if path.read_text(encoding="utf-8") == content:
                same += 1
                continue
            bak = ROOT / ".parche_backups" / stamp / rel
            bak.parent.mkdir(parents=True, exist_ok=True)
            bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        wrote += 1
    for d in ("checkpoints", "memory", "reports"):
        (ROOT / d).mkdir(exist_ok=True)
    print(f"[OK] {wrote} archivos escritos, {same} ya estaban igual.")


def venv_python():
    for rel in (".venv/bin/python", ".venv/Scripts/python.exe", "venv/bin/python", "venv/Scripts/python.exe"):
        if (ROOT / rel).exists():
            return str(ROOT / rel)
    return None


def py():
    return venv_python() or sys.executable


def run(args, quiet=False):
    print("\n$ " + " ".join(args), flush=True)
    r = subprocess.run(args, cwd=ROOT)
    if r.returncode != 0 and not quiet:
        print(f"[!] El comando termino con codigo {r.returncode}.")
    return r.returncode == 0


def has_torch():
    return subprocess.run([py(), "-c", "import torch, numpy, tqdm, pytest"], cwd=ROOT, capture_output=True).returncode == 0


def find_book():
    if OPT["libro"]:
        return OPT["libro"]
    for f in LIBROS:
        if (ROOT / f).exists():
            return f
    return None


def step_entorno():
    if not venv_python():
        print("Creando el entorno de Python (.venv) ...")
        if not run([sys.executable, "-m", "venv", ".venv"]):
            return False
    print("Instalando dependencias (puede tardar unos minutos la primera vez) ...")
    return run([py(), "-m", "pip", "install", "-r", "requirements.txt"])


def step_tests():
    return run([py(), "-m", "pytest", "-q", "tests"])


def step_codigo():
    if not (ROOT / "reproducibilidad" / "manifiesto.json").exists():
        print("Aun no hay reproducibilidad/manifiesto.json (se crea con:  python -m scripts.manifiesto --guardar  en tu proyecto original).")
        print("Lo creo ahora a partir de lo que acabo de escribir?  (sirve para comprobar copias futuras)")
        return run([py(), "-m", "scripts.manifiesto", "--guardar"])
    return run([py(), "-m", "scripts.manifiesto", "--verificar"])


def step_reentrenar():
    book = find_book()
    args = [py(), "-m", "scripts.reproduce"]
    if book:
        args += ["--libro", book]
    else:
        print("[aviso] No hay texto en espanol (regenta.rtf/.txt) ni --libro: se saltan los pasos que dependen de el (el oido saldra distinto).")
    if OPT["rapido"]:
        args.append("--rapido")
    if OPT["semilla"] is not None:
        args += ["--semilla", str(OPT["semilla"])]
    return run(args)


def step_resultados():
    return run([py(), "-m", "scripts.manifiesto", "--verificar", "--metricas"])


def step_hablar():
    return run([py(), "-m", "scripts.think"])


def estado():
    ck = ROOT / "checkpoints"
    pesos = [f for f in ("lcm_reasoner.pt", "ear.pt", "school.pt") if (ck / f).exists()]
    print("\nEstado:")
    print(f"   entorno Python (.venv) .... {'si' if venv_python() else 'no'}   |   dependencias .... {'si' if venv_python() and has_torch() else 'no / sin comprobar'}")
    print(f"   pesos entrenados .......... {len(pesos)}/3 ({', '.join(pesos) or 'ninguno'})")
    print(f"   texto en espanol .......... {find_book() or 'no encontrado (usa --libro o pon regenta.rtf/.txt aqui)'}")


MENU = [
    ("1", "Preparar el entorno (crear .venv e instalar dependencias)", step_entorno),
    ("2", "Comprobar el codigo con los tests (51)", step_tests),
    ("3", "Verificar que el codigo es identico al original (manifiesto)", step_codigo),
    ("4", "Reentrenar TODO desde cero (reproduce; tarda desde decenas de minutos a horas)", step_reentrenar),
    ("5", "Comprobar los resultados contra la referencia", step_resultados),
    ("6", "Hablar con el modelo (think)", step_hablar),
    ("7", "Hacer 1 -> 5 en orden, sin parar", None),
]


def hacer_todo():
    for key, label, fn in MENU[:5]:
        print(f"\n=== {key}. {label} ===")
        if not fn():
            print(f"[!] Se para en el paso {key}. Arreglalo y repite desde el menu.")
            return False
    print("\n[OK] Todo hecho. Ahora puedes probar:  python -m scripts.think")
    return True


def menu():
    if not any((ROOT / "checkpoints" / f).exists() for f in ("ear.pt", "school.pt", "lcm_reasoner.pt")):
        try:
            r = input("\nNo hay pesos entrenados. ¿Lo hago TODO automaticamente (entorno, tests, verificacion, reentrenamiento y comparacion)? [S/n]: ").strip().lower()
        except EOFError:
            return
        if r in ("", "s", "si", "y", "yes"):
            if OPT["libro"] is None and find_book() is None:
                OPT["libro"] = input("Ruta de tu texto en espanol (Enter = sin texto): ").strip() or None
            hacer_todo()
            return
    while True:
        estado()
        print("\n¿Que quieres hacer?")
        for key, label, _ in MENU:
            print(f"   {key}) {label}")
        print("   0) Salir")
        try:
            choice = input("Elige un numero: ").strip()
        except EOFError:
            return
        if choice in ("0", "q", ""):
            return
        if choice == "7":
            hacer_todo()
            continue
        item = next((m for m in MENU if m[0] == choice), None)
        if not item:
            print("Opcion no valida.")
            continue
        if choice == "4":
            if not has_torch():
                print("Primero hace falta el entorno: elige la opcion 1.")
                continue
            if OPT["libro"] is None and find_book() is None:
                OPT["libro"] = input("Ruta de tu texto en espanol (Enter = sin texto): ").strip() or None
            r = input("¿Modo rapido (salta las evaluaciones opcionales)? [s/N]: ").strip().lower()
            OPT["rapido"] = r in ("s", "si", "y")
        item[2]()


def main():
    ap = argparse.ArgumentParser(description="Construye el proyecto LCM desde cero y te guia para probarlo.")
    ap.add_argument("--sin-menu", action="store_true", help="solo escribe los archivos")
    ap.add_argument("--todo", action="store_true", help="escribe, instala, prueba, reentrena y verifica sin preguntar")
    ap.add_argument("--libro", help="texto en espanol para el oido")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--semilla", type=int)
    a = ap.parse_args()
    OPT.update(libro=a.libro, rapido=a.rapido, semilla=a.semilla)
    write_files()
    if a.sin_menu:
        print("Siguiente:  python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python -m pytest -q tests")
        return
    if a.todo:
        sys.exit(0 if hacer_todo() else 1)
    if not sys.stdin.isatty():
        print("(sin terminal interactiva: no abro el menu; usa --todo o ejecuta de nuevo en una terminal)")
        return
    menu()


if __name__ == "__main__":
    main()
