"""parche-116: el lector ya no se cuelga con textos largos: la escuela puede dar arboles con ciclos de cabezas y los recorridos no acababan nunca. Se saneanan los ciclos al construir el arbol y los recorridos llevan control de visitados.
Uso: python -m scripts.ciclo parche-116.py"""
import datetime, json, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
import base64, zlib
ALL_EDITS = [('src/language/lector_ud.py', '        self.n = len(rows)\n        self.h = [x[2] - 1 for x in rows]\n        self.k: List[List[int]] = [[] for _ in rows]\n        for i, h in enumerate(self.h):\n            if 0 <= h < self.n:\n                self.k[h].append(i)\n\n    def f(self, i):\n', '        self.n = len(rows)\n        self.h = [x[2] - 1 for x in rows]\n        self._sanear()\n        self.k: List[List[int]] = [[] for _ in rows]\n        for i, h in enumerate(self.h):\n            if 0 <= h < self.n:\n                self.k[h].append(i)\n\n    def _sanear(self):\n        """La escuela predice cada cabeza por separado: puede dar ciclos (una palabra colgando de sí misma o dos de la otra).\n        Un ciclo haría que los recorridos no acaben nunca: se corta soltando una palabra del ciclo (queda como raíz suelta)."""\n        n = self.n\n        for i in range(n):\n            if not (0 <= self.h[i] < n) or self.h[i] == i:\n                self.h[i] = -1 if self.h[i] == i or not (0 <= self.h[i] < n) else self.h[i]\n        for i in range(n):\n            ruta, x = [], i\n            while 0 <= x < n and x not in ruta:\n                ruta.append(x)\n                x = self.h[x]\n            if 0 <= x < n:                                    # volvió a un nodo de la ruta: ciclo\n                self.h[ruta[-1]] = -1\n\n    def f(self, i):\n', '        """La escuela predice cada cabeza por separado: puede dar ciclos (una palabra colgando de sí misma o dos de la otra).'), ('src/language/lector_ud.py', '\n    def sub(self, i) -> List[int]:\n        out, st = [], [i]\n        while st:\n            x = st.pop()\n            out.append(x)\n            st.extend(self.k[x])\n        return sorted(out)\n\n', '\n    def sub(self, i) -> List[int]:\n        out, st, vistos = [], [i], {i}\n        while st:\n            x = st.pop()\n            out.append(x)\n            for y in self.k[x]:\n                if y not in vistos:\n                    vistos.add(y)\n                    st.append(y)\n        return sorted(out)\n\n', '        out, st, vistos = [], [i], {i}'), ('src/language/lector_ud.py', '            if not rows:\n                continue\n            hs = self.ud.oracion(rows, inicio=inicio_parrafo)\n            motivo = motivo or self.ud.motivo\n            for h in hs:\n', '            if not rows:\n                continue\n            try:\n                hs = self.ud.oracion(rows, inicio=inicio_parrafo)\n            except RecursionError:                                                # noqa  (árbol raro: se salta ese tramo, no se cuelga)\n                hs = []\n            motivo = motivo or self.ud.motivo\n            for h in hs:\n', '                hs = self.ud.oracion(rows, inicio=inicio_parrafo)')]
NEW_FILES = {'tests/test_parche116.py': '"""parche-116: el lector no se cuelga con árboles de la escuela con ciclos."""\nimport time\n\nfrom src.language.lector_ud import Arbol, ExtractorUD\n\n\ndef test_arbol_con_ciclos_no_se_cuelga():\n    casos = [\n        [("El", "DET", 1, "det", "el"), ("león", "NOUN", 3, "nsubj", "león"), ("caza", "VERB", 2, "root", "cazar"), ("presas", "NOUN", 3, "obj", "presa"), (".", "PUNCT", 9, "punct", ".")],\n        [("A", "NOUN", 2, "conj", "a"), ("B", "NOUN", 3, "conj", "b"), ("C", "VERB", 1, "conj", "c"), ("D", "NOUN", 4, "obj", "d")],\n        [("Goku", "PROPN", 1, "nsubj", "Goku"), ("vence", "VERB", 1, "root", "vencer"), ("a", "ADP", 4, "case", "a"), ("Freezer", "PROPN", 2, "obj", "Freezer")],\n    ]\n    t0 = time.time()\n    for rows in casos:\n        A = Arbol(rows)\n        for i in range(A.n):\n            assert i in A.sub(i)\n        ExtractorUD().oracion(rows)\n    assert time.time() - t0 < 2\n'}
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
    print(f"parche-116 instalado. Copias en {bk}" if plan else "parche-116: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

