"""parche-124: texto sobre el propio documento (este articulo necesita referencias, busca fuentes, vease X) y correlativas (cuanto mas A, mas B) no son conocimiento y se omiten; infinitivos con clitico (llevarla, disponerse) dan su infinitivo (llevar, disponer) en vez de lemas rotos.
Uso: python -m scripts.ciclo parche-124.py"""
import datetime, json, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
import base64, zlib
ALL_EDITS = [('src/language/lector_ud.py', '        lm = (self.r[i][4] or "").strip()\n        lm = (lm if lm and lm != "_" else self.r[i][0]).lower()\n        if self.r[i][1] in ("VERB", "AUX") and len(lm) > 6:                          # «insuflarle» -> insuflar: el clítico no es parte del verbo\n            lm = re.sub(r"(?<=[aeií][r])(?:les|los|las|le|la|lo|se|me|te|nos)$", "", lm)\n        return lm\n\n', '        lm = (self.r[i][4] or "").strip()\n        lm = (lm if lm and lm != "_" else self.r[i][0]).lower()\n        if self.r[i][1] in ("VERB", "AUX"):                                          # «insuflarle», «llevarla», «disponerse» -> insuflar, llevar, disponer\n            m = re.fullmatch(r"(\\w{3,}?(?:ar|er|ir|ír))(?:me|te|se|nos|os|le|les|lo|los|la|las)(?:lo|la|los|las)?", self.r[i][0].lower())\n            if m:\n                return m.group(1).replace("ír", "ir")\n        return lm\n\n', '        if self.r[i][1] in ("VERB", "AUX"):                                          # «insuflarle», «llevarla», «disponerse» -> insuflar, llevar, disponer'), ('src/language/lector_ud.py', '        A = Arbol(rows)\n        self.motivo = ""\n        memo: Dict[int, Optional[List[C]]] = {}\n        out: List[dict] = []\n', '        A = Arbol(rows)\n        self.motivo = ""\n        if self._meta(A):\n            self.motivo = "es texto sobre el propio documento (avisos, enlaces), no conocimiento"\n            return []\n        memo: Dict[int, Optional[List[C]]] = {}\n        out: List[dict] = []\n', '            self.motivo = "es texto sobre el propio documento (avisos, enlaces), no conocimiento"'), ('src/language/lector_ud.py', '                self.clases.setdefault(h["s"], set()).add(h["o"])\n        return _limpiar(out)\n\n    def _hipotetico(self, A: Arbol, p: int) -> bool:\n', '                self.clases.setdefault(h["s"], set()).add(h["o"])\n        return _limpiar(out)\n\n    DOC = {"artículo", "articulo", "sección", "seccion", "página", "pagina", "aviso", "plantilla", "wikipedia", "borrador"}\n\n    def _meta(self, A: Arbol) -> bool:\n        """Texto sobre el propio documento y no sobre el mundo: «Este artículo necesita más referencias», «Busca fuentes», «véase X»,\n        y las correlativas «cuanto más A, más B» (no afirman un hecho)."""\n        for i in range(A.n):\n            l, f = A.l(i), nrm(A.f(i))\n            if l in self.DOC and any(A.l(j) in ("este", "esta", "dicho", "dicha") for j in A.hijos(i, "det")):\n                return True\n            if f in ("vease", "consultese", "compárese", "comparese") or (f == "busca" and i + 1 < A.n and nrm(A.f(i + 1)) == "fuentes"):\n                return True\n            if f == "cuanto" and i + 1 < A.n and nrm(A.f(i + 1)) in ("mas", "menos", "mayor", "menor"):\n                return True\n        return False\n\n    def _hipotetico(self, A: Arbol, p: int) -> bool:\n', '    DOC = {"artículo", "articulo", "sección", "seccion", "página", "pagina", "aviso", "plantilla", "wikipedia", "borrador"}'), ('tests/test_parche122.py', '    assert not any(h["s"] == "GOKU" for h in ex.oracion(sin_sujeto))\n', '    assert not any(h["s"] == "GOKU" for h in ex.oracion(sin_sujeto))\n\n\ndef test_texto_del_documento_y_correlativas_no_son_hechos():\n    ex = ExtractorUD()\n    aviso = _rows("1:Este/DET->2:det[este] 2:artículo/NOUN->4:nsubj[artículo] 3:necesita/VERB->0:root[necesitar] 4:referencias/NOUN->3:obj[referencia] 5:./PUNCT->3:punct[.]")\n    aviso = [("Este", "DET", 2, "det", "este"), ("artículo", "NOUN", 3, "nsubj", "artículo"), ("necesita", "VERB", 0, "root", "necesitar"), ("referencias", "NOUN", 3, "obj", "referencia"), (".", "PUNCT", 3, "punct", ".")]\n    assert ex.oracion(aviso) == []\n    cuanto = [("cuanto", "ADV", 3, "advmod", "cuanto"), ("más", "ADV", 3, "advmod", "más"), ("grande", "ADJ", 0, "root", "grande"), (".", "PUNCT", 3, "punct", ".")]\n    assert ex.oracion(cuanto) == []\n\n\ndef test_infinitivo_con_clitico_da_su_infinitivo():\n    from src.language.lector_ud import Arbol\n    for forma, esperado in (("llevarla", "llevar"), ("disponerse", "disponer"), ("insuflarle", "insuflar")):\n        assert Arbol([(forma, "VERB", 0, "root", forma + "r")]).l(0) == esperado\n', 'def test_texto_del_documento_y_correlativas_no_son_hechos():')]
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
    print(f"parche-124 instalado. Copias en {bk}" if plan else "parche-124: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

