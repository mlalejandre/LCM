"""parche-72: un nombre propio que la escuela lee como ADJETIVO al principio de la frase ("Clara canta en el coro", "Clara no compra leche").

La escuela etiqueta "Clara" como ADJ con relacion amod (colgando del verbo). La regla de parche-43 (_name_like_adj en extract.py) solo
miraba la relacion nsubj, asi que nunca se activaba. Ahora, en src/language/school_parser.py, un arreglo posterior a la escuela
(sin reentrenar, como _fix_name_verb) convierte esa palabra en PROPN + nsubj cuando se cumple TODO esto:
  - es la primera palabra, ADJ, con mayuscula inicial y el resto en minuscula;
  - cuelga (amod o nsubj) de un VERBO que esta a su derecha, no en infinitivo;
  - entre ella y el verbo solo puede haber "no / nunca / jamas / tampoco";
  - no lleva determinante y el verbo no tiene ya otro sujeto.
No toca extract.py, la memoria ni el dialogo. NO arregla "Lucia cocina pasta y su hermana ..." (la escuela etiqueta VERB+NOUN, otro fallo)
ni los relativos ni los sujetos coordinados.

Criterios fijados ANTES de medir:
  - 57 tests pasan (55 + 2 nuevos) y los 22 examenes siguen cumpliendo su criterio.
  - "Clara canta en el coro de la iglesia." deja de aparecer en FALLO en conversacion_80 y largas_ciegas_27.
  - "Clara no compra leche." (coherencia_ciega_19) y "Háblame de Clara" / "¿Qué hemos hablado?" (dialogo_ciego_37): se informa tal cual,
    mejoren o no (dependen tambien de otras reglas).
  - Ningun examen baja mas de lo que explica una sola pregunta (una pregunta mueve 5-10 puntos en los examenes pequenos).
Despues:  python -m scripts.check   y   python -m scripts.manifiesto --guardar
No hace commits ni pushes. No reentrena.
"""
import datetime, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CALL_OLD = "        rows = self._fix_name_verb(rows)\n"
CALL_NEW = "        rows = self._fix_name_adj(self._fix_name_verb(rows))\n"

DEF_OLD = '''        return [tuple(x) for x in rows]

    def parse(self, sentence: str, topic'''
DEF_NEW = '''        return [tuple(x) for x in rows]

    @staticmethod
    def _fix_name_adj(rows):
        """parche-72: "Clara canta en el coro." / "Clara no compra leche.": la escuela lee el nombre propio como ADJ (amod del verbo).
        Si es la primera palabra, empieza en mayuscula, cuelga de un verbo a su derecha (solo "no/nunca/jamas/tampoco" entre medias),
        no lleva determinante y el verbo no tiene otro sujeto, es un nombre propio sujeto."""
        if len(rows) < 3:
            return rows
        f, u, h, r, l = rows[0][:5]
        if u != "ADJ" or r not in ("amod", "nsubj") or not (f[:1].isupper() and f[1:].islower()) or h < 2:
            return rows
        v = h - 1
        if v >= len(rows) or rows[v][1] != "VERB" or rows[v][0].lower().endswith(("ar", "er", "ir", "ando", "iendo")):
            return rows
        if any(_norm(rows[k][0]) not in ("no", "nunca", "jamas", "tampoco") for k in range(1, v)):
            return rows
        if any(x[2] == 1 and x[3] == "det" for x in rows[1:]):
            return rows
        if any(x[2] == h and x[3] in ("nsubj", "csubj") for x in rows[1:]):
            return rows
        return [(f, "PROPN", h, "nsubj", l)] + list(rows[1:])

    def parse(self, sentence: str, topic'''

TEST = '''"""parche-72: un nombre propio leido como ADJ al principio de la frase pasa a ser sujeto."""
from src.language.extract import triples_full
from src.language.school_parser import SchoolParser

fix = SchoolParser._fix_name_adj


def _tr(rows):
    return [(t["s"], t["p"], t["o"], t["neg"]) for t in triples_full(rows, entities_only=True)]


def test_nombre_como_adjetivo_inicial():
    T = [("Clara", "ADJ", 2, "amod", "claro"), ("canta", "VERB", 0, "root", "cantar"), ("en", "ADP", 5, "case", "en"),
         ("el", "DET", 5, "det", "el"), ("coro", "NOUN", 2, "obl", "coro"), (".", "PUNCT", 2, "punct", ".")]
    assert fix(T)[0][1:4] == ("PROPN", 2, "nsubj")
    assert _tr(fix(T)) == [("clara", "cantar_en", "coro", False)]
    N = [("Clara", "ADJ", 3, "amod", "claro"), ("no", "ADV", 3, "advmod", "no"), ("compra", "VERB", 0, "root", "comprar"),
         ("leche", "NOUN", 3, "obj", "leche"), (".", "PUNCT", 3, "punct", ".")]
    assert _tr(fix(N)) == [("clara", "comprar", "leche", True)]


def test_no_toca_adjetivos_de_verdad():
    otro = [("Clara", "ADJ", 3, "amod", "claro"), ("Ana", "PROPN", 3, "nsubj", "ana"), ("canta", "VERB", 0, "root", "cantar"), (".", "PUNCT", 3, "punct", ".")]
    assert fix(otro)[0][1] == "ADJ"                                   # el verbo ya tiene sujeto
    minus = [("claro", "ADJ", 2, "amod", "claro"), ("canta", "VERB", 0, "root", "cantar"), (".", "PUNCT", 2, "punct", ".")]
    assert fix(minus)[0][1] == "ADJ"                                  # sin mayuscula inicial
    con_det = [("Clara", "ADJ", 2, "amod", "claro"), ("canta", "VERB", 0, "root", "cantar"), (".", "PUNCT", 2, "punct", ".")]
    assert fix(con_det[:1] + [("el", "DET", 1, "det", "el")] + con_det[1:])[0][1] == "ADJ"
'''

EDITS = [("src/language/school_parser.py", CALL_OLD, CALL_NEW, "_fix_name_adj(self._fix_name_verb"),
         ("src/language/school_parser.py", DEF_OLD, DEF_NEW, "def _fix_name_adj")]
NEW_FILES = {"tests/test_parche72.py": TEST}


def main(root: Path = ROOT) -> int:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    bk = root / ".parche_backups" / stamp
    texts, changed = {}, set()
    for rel, old, new, marca in EDITS:                              # comprobar TODO antes de escribir nada
        p = root / rel
        if not p.is_file():
            print(f"FALTA {rel}: no se toca nada."); return 1
        txt = texts.get(rel) or p.read_text(encoding="utf-8")
        if marca in txt:
            print(f"  {rel}: ya aplicado ({marca})"); texts[rel] = txt; continue
        if txt.count(old) != 1:
            print(f"ERROR {rel}: el trozo a cambiar aparece {txt.count(old)} veces (debe ser 1). No se toca nada."); return 1
        texts[rel] = txt.replace(old, new); changed.add(rel)
    plan = [(root / rel, rel, texts[rel]) for rel in sorted(changed)]
    for rel, content in NEW_FILES.items():
        p = root / rel
        if not p.exists() or p.read_text(encoding="utf-8") != content:
            plan.append((p, rel, content))
    for p, rel, txt in plan:
        if p.exists():
            (bk / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, bk / rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt, encoding="utf-8")
        py_compile.compile(str(p), doraise=True)
        print(f"  escrito {rel}")
    print(f"parche-72 instalado. Copias en {bk}" if plan else "parche-72: nada que hacer.")
    print("Ahora:  python -m pytest -q tests ;  python -m scripts.check ;  python -m scripts.manifiesto --guardar")
    return 0


if __name__ == "__main__":
    sys.exit(main())