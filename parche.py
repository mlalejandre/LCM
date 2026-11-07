"""parche-78: tercer lote SIMBOLICO (no reentrena). Cierra el unico fallo real del ciclo anterior y abre un examen ciego nuevo.

  1. Comparativos: "Rosa es mas baja que Clara." -> la escuela lee "Clara" como csubj/nmod (a veces con etiqueta ADJ) y se perdia la comparacion
     (rosa, ser, baja). Ahora el termino tras "que" con "mas/menos" en el mismo nucleo es siempre (rosa, mas_bajo_que, clara). Es lo que hacia fallar
     "¿Es Sara mas baja que Clara?" (no encadenaba la transitividad). Reproducido y corregido con los arboles reales de reports/arboles.json.
  2. data/comparativos_ciegos.tsv: examen CIEGO nuevo (12 preguntas, nombres y adjetivos no usados al afinar). Se registra en scripts/check.py como
     INFORMATIVO (criterio 0 %): muestra fallos pero no hace que el ciclo restaure nada. Sus fallos son la materia prima del parche-79.

Sin tocar: largas_ciegas_27 ("La profesora explica la leccion y los alumnos escuchan."): el sistema extrae ademas (alumnos, escuchar), que es CORRECTO;
el gold omite esa proposicion. Se deja como esta para no ajustar el examen a la salida.

Criterios fijados ANTES de medir: 74 tests pasan (72 + 2 nuevos), los 22 examenes anteriores no bajan, cantidad_ciegas_14 vuelve a >= 92.9 %.
Uso:  python -m scripts.ciclo parche-78.py     (restaura solo si algo falla). No hace commits ni pushes. No reentrena.
"""
import datetime, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SP = "src/language/school_parser.py"
CK = "scripts/check.py"

OLD = '        for r, x in enumerate(rows):\n            if x[3] != "nsubj" or x[1] not in ("PROPN", "NOUN") or r < 1:\n                continue\n            q = rows[r - 1]\n            if _norm(q[0]) == "que" and q[2] == r + 1 and q[3] == "mark" and x[2] > 0 and rows[x[2] - 1][1] == "ADJ" \\\n                    and any(y[2] == x[2] and y[3] == "nsubj" and j != r for j, y in enumerate(rows)) \\\n                    and any(_norm(y[0]) in ("mas", "menos") and y[2] == x[2] for y in rows):\n                x[3] = "nmod"\n                q[3] = "case"\n'
NEW = '        for r, x in enumerate(rows):\n            if x[3] not in ("nsubj", "csubj", "acl", "obl", "amod", "xcomp", "nmod") or (x[1] not in ("PROPN", "NOUN") and not (x[1] == "ADJ" and x[0][:1].isupper())) or r < 1:      # parche-78: tambien csubj/acl/..., y nombre leido como ADJ\n                continue\n            q = rows[r - 1]\n            if _norm(q[0]) == "que" and q[2] == r + 1 and q[3] in ("mark", "case") and x[2] > 0 and x[2] != r + 1 \\\n                    and any(_norm(y[0]) in ("mas", "menos") and y[2] == x[2] for y in rows) \\\n                    and (rows[x[2] - 1][1] == "ADJ" or any(y[2] == x[2] and y[3] == "cop" for y in rows)) \\\n                    and (x[3] != "nsubj" or any(y[2] == x[2] and y[3] == "nsubj" and j != r for j, y in enumerate(rows))):\n                x[3] = "nmod"\n                q[3] = "case"\n                if x[1] == "ADJ":\n                    x[1] = "PROPN"\n'

CK_OLD = '("preguntas_ciegas_31", "data/preguntas_ciegas.tsv", .80)]'
CK_NEW = '("preguntas_ciegas_31", "data/preguntas_ciegas.tsv", .80), ("nuevo_ciego_comparativos_12", "data/comparativos_ciegos.tsv", .0)]      # parche-78: informativo'

ALL_EDITS = [
    (SP, OLD, NEW, "parche-78: tambien csubj"),
    (CK, CK_OLD, CK_NEW, "nuevo_ciego_comparativos_12"),
]
NEW_FILES = {"tests/test_parche78.py": '"""parche-78: el termino de la comparacion se reconoce aunque la escuela lo etiquete csubj/nmod/ADJ (nombre leido como adjetivo)."""\nfrom src.language.extract import triples_full\nfrom src.language.school_parser import SchoolParser\n\nS = SchoolParser\n\n\ndef _tr(rows):\n    return [(t["s"], t["p"], t["o"], t["neg"]) for t in triples_full(rows, entities_only=True)]\n\n\ndef test_comparativo_con_termino_csubj_o_adjetivo():\n    for dep, pos in (("csubj", "PROPN"), ("nmod", "ADJ"), ("csubj", "ADJ")):\n        R = [("Rosa", "PROPN", 4, "nsubj", "rosa"), ("es", "AUX", 4, "cop", "ser"), ("más", "ADV", 4, "advmod", "mas"), ("baja", "ADJ", 0, "root", "bajo"),\n             ("que", "SCONJ", 6, "mark", "que"), ("Clara", pos, 4, dep, "clara"), (".", "PUNCT", 4, "punct", ".")]\n        assert _tr(S._fix_comparative(R)) == [("rosa", "mas_bajo_que", "clara", False)], (dep, pos)\n\n\ndef test_comparativo_no_toca_otras_frases():\n    N = [("Rosa", "PROPN", 2, "nsubj", "rosa"), ("sabe", "VERB", 0, "root", "saber"), ("que", "SCONJ", 5, "mark", "que"), ("Clara", "PROPN", 2, "ccomp", "clara"),\n         ("vino", "VERB", 2, "ccomp", "venir"), (".", "PUNCT", 2, "punct", ".")]\n    assert S._fix_comparative(N) == [tuple(x) for x in N]\n', "data/comparativos_ciegos.tsv": '# Examen CIEGO nuevo (parche-78): comparativos encadenados con nombres y adjetivos que NO se usaron para afinar. Informativo: no frena el ciclo.\nH: Marta es más alta que Lucía.\nH: Lucía es más alta que Nuria.\nP: ¿Es Marta más alta que Nuria?\tSI\nP: ¿Es Nuria más alta que Marta?\tNO\nP: ¿Es Marta más alta que Lucía?\tSI\n\nH: Pablo es menos rápido que Hugo.\nH: Hugo es menos rápido que Iván.\nP: ¿Es Pablo menos rápido que Iván?\tSI\nP: ¿Es Iván menos rápido que Pablo?\tNO\n\nH: Elena es más joven que Rosa.\nP: ¿Es Elena más joven que Marta?\tNOSE\nP: ¿Es Rosa más joven que Elena?\tNO\n\nH: Carlos es más fuerte que Andrés.\nH: Andrés es más fuerte que Daniel.\nP: ¿Quién es más fuerte que Daniel?\tAndrés\nP: ¿Es Carlos más fuerte que Daniel?\tSI\n\nH: Irene es más lista que Sofía.\nH: Sofía es más lista que Eva.\nH: Eva es más lista que Alba.\nP: ¿Es Irene más lista que Alba?\tSI\nP: ¿Es Alba más lista que Irene?\tNO\nP: ¿Es Sofía más lista que Alba?\tSI\n'}


def main(root: Path = ROOT) -> int:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    bk = root / ".parche_backups" / stamp
    texts, changed = {}, set()
    for rel, old, new, marca in ALL_EDITS:                              # comprobar TODO antes de escribir nada
        p = root / rel
        if not p.is_file():
            print(f"FALTA {rel}: no se toca nada."); return 1
        txt = texts[rel] if rel in texts else p.read_text(encoding="utf-8")
        if marca in txt:
            texts[rel] = txt; continue
        if txt.count(old) != 1:
            print(f"ERROR {rel}: un trozo a cambiar aparece {txt.count(old)} veces (debe ser 1): {old[:70]!r}. No se toca nada."); return 1
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
        if rel.endswith(".py"):
            py_compile.compile(str(p), doraise=True)
        print(f"  escrito {rel}")
    print(f"parche-78 instalado. Copias en {bk}" if plan else "parche-78: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())