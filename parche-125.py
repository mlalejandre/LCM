"""parche-125: el termino de una comparacion ('al igual que Mercurio, carece de...') no es sujeto ni tema; el tema del discurso es el sujeto mas constante de las ultimas 6 frases, no el ultimo (en un texto sobre Venus, 'el Sol sale por el oeste' ya no cambia de tema).
Uso: python -m scripts.ciclo parche-125.py"""
import datetime, json, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
import base64, zlib
ALL_EDITS = [('src/language/lector_ud.py', '    def __init__(self):\n        self.principal_plural: Optional[bool] = None\n        self.principal_edad = 0                      # frases desde que se fijó el tema: un tema viejo ya no es «el sujeto de esta frase»\n        self.principal: Optional[C] = None          # sujeto de la oracion principal anterior (sujeto omitido, «él», «Su X»)\n', '    def __init__(self):\n        self.principal_plural: Optional[bool] = None\n        self.recientes: List[C] = []\n        self.principal_edad = 0                      # frases desde que se fijó el tema: un tema viejo ya no es «el sujeto de esta frase»\n        self.principal: Optional[C] = None          # sujeto de la oracion principal anterior (sujeto omitido, «él», «Su X»)\n', '        self.recientes: List[C] = []'), ('src/language/lector_ud.py', '            cs: List[C] = []\n            for n_ in ns:\n                if A.d(n_) == "csubj" or A.u(n_) == "VERB":\n                    continue\n                if A.u(n_) == "PRON" and A.l(n_) in PRON_REL:\n', '            cs: List[C] = []\n            for n_ in ns:\n                if A.d(n_) == "csubj" or A.u(n_) == "VERB" or self._comparado(A, n_):\n                    continue\n                if A.u(n_) == "PRON" and A.l(n_) in PRON_REL:\n', '                if A.d(n_) == "csubj" or A.u(n_) == "VERB" or self._comparado(A, n_):'), ('src/language/lector_ud.py', '\n    EDAD_MAX = 1\n\n    PARTITIVOS = {"mayoría", "mayoria", "mitad", "tercio", "parte", "resto", "porcentaje", "minoría", "minoria", "cuarto"}\n', '\n    EDAD_MAX = 1\n    VENTANA = 6\n    COMPARATIVAS = ("al igual que", "igual que", "a diferencia de", "asi como", "tal como", "como", "tanto como", "lo mismo que", "de igual modo que")\n\n    @staticmethod\n    def _comparado(A: Arbol, n: int) -> bool:\n        """«Al igual que Mercurio, carece de satélites»: Mercurio es el término de la comparación, no el sujeto."""\n        previas = []\n        j = n - 1\n        while j >= 0 and A.u(j) not in ("PUNCT",) and len(previas) < 4:\n            if A.u(j) == "DET" and A.d(j) == "det" and A.h[j] == n:\n                j -= 1\n                continue\n            previas.insert(0, nrm(A.f(j)))\n            j -= 1\n        txt = re.sub(r"\\bde el\\b", "del", re.sub(r"\\ba el\\b", "al", " ".join(previas)))       # la escuela separa «al» y «del»\n        return any(txt.endswith(c) and (txt == c or txt[: -len(c)].endswith(" ")) for c in ExtractorUD.COMPARATIVAS)\n\n    PARTITIVOS = {"mayoría", "mayoria", "mitad", "tercio", "parte", "resto", "porcentaje", "minoría", "minoria", "cuarto"}\n', '    COMPARATIVAS = ("al igual que", "igual que", "a diferencia de", "asi como", "tal como", "como", "tanto como", "lo mismo que", "de igual modo que")'), ('src/language/lector_ud.py', '        if principal_nuevo is not None:\n            self.principal_edad = 0\n            self.principal = principal_nuevo\n            self.principal_plural = self._plural_nombre(A, principal_nuevo.idx) if 0 <= principal_nuevo.idx < A.n else None\n', '        if principal_nuevo is not None:\n            self.principal_edad = 0\n            self.recientes.append(principal_nuevo)\n            del self.recientes[:-self.VENTANA]\n            veces = {}\n            for c_ in self.recientes:\n                veces[c_.key] = veces.get(c_.key, 0) + 1\n            tope = max(veces.values())\n            principal_nuevo = next(c_ for c_ in reversed(self.recientes) if veces[c_.key] == tope)      # el tema es el sujeto más constante, no el último\n            self.principal = principal_nuevo\n            self.principal_plural = self._plural_nombre(A, principal_nuevo.idx) if 0 <= principal_nuevo.idx < A.n else None\n', '            self.recientes.append(principal_nuevo)'), ('tests/test_parche122.py', '        assert Arbol([(forma, "VERB", 0, "root", forma + "r")]).l(0) == esperado\n', '        assert Arbol([(forma, "VERB", 0, "root", forma + "r")]).l(0) == esperado\n\n\ndef test_termino_de_comparacion_no_es_sujeto_ni_tema():\n    ex = ExtractorUD()\n    ex.oracion([("Venus", "PROPN", 3, "nsubj", "venus"), ("es", "AUX", 3, "cop", "ser"), ("planeta", "NOUN", 0, "root", "planeta"), (".", "PUNCT", 3, "punct", ".")])\n    rows = [("a", "ADP", 7, "advmod", "a"), ("el", "DET", 1, "fixed", "el"), ("igual", "ADJ", 1, "fixed", "igual"), ("que", "SCONJ", 1, "fixed", "que"),\n            ("Mercurio", "PROPN", 7, "nsubj", "mercurio"), (",", "PUNCT", 5, "punct", ","), ("carece", "VERB", 0, "root", "carecer"), ("de", "ADP", 9, "case", "de"),\n            ("satélites", "NOUN", 7, "obl", "satélite"), (".", "PUNCT", 7, "punct", ".")]\n    hs = {(h["s"], h["p"], h["o"]) for h in ex.oracion(rows)}\n    assert not any(s == "MERCURIO" for s, _, _ in hs)\n    assert ex.principal.key == "VENUS"\n', 'def test_termino_de_comparacion_no_es_sujeto_ni_tema():')]
NEW_FILES = {}
SOFT = []

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


    for rel, marca, bloque, antes in SOFT:                              # documentacion: tolerante, nunca bloquea
        p = root / rel
        try:
            t = p.read_text(encoding="utf-8") if p.exists() else ""
            if marca in t:
                continue
            if antes and antes in t:
                t = t.replace(antes, bloque + antes, 1)
            else:
                t = t + ("" if t.endswith("\n") or not t else "\n") + bloque
            if p.exists():
                (bk / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, bk / rel)
            p.write_text(t, encoding="utf-8"); print(f"  actualizado {rel}")
        except Exception as e:
            print(f"  (aviso) no se pudo actualizar {rel}: {e!r}")
    print(f"parche-125 instalado. Copias en {bk}" if plan else "parche-125: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

