"""parche-131 (se aplica sobre el 130): UNA PREGUNTA NUEVA NO ES LA EXPLICACION QUE EL LCM HABIA PEDIDO.
Ensayando la demo salio un fallo de dialogo: tras «No lo sé. No conozco «Mongolia»: ¿me lo explicas?» el LCM seguia esperando la explicacion y la PREGUNTA siguiente (aunque fuese clara y hubiera un texto
leido) la trataba como conversacion: «¿Cuántas horas al día está inactivo el león?» -> «Conozco 1: León.» en vez de «Veinte horas. En el texto: …». Ahora, si lo que llega es una pregunta, la espera se cancela y se
contesta como cualquier otra; una explicacion («es un país de Asia») sigue sirviendo igual. Solo cambia ese caso: los examenes de dialogo y el resto de pruebas dan lo mismo que antes.
Uso: python -m scripts.ciclo parche-131.py"""
import datetime, json, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
import base64, zlib
ALL_EDITS = [('src/language/dialogue.py', '        """parche-95: si la respuesta es un fallo y la pregunta tiene una errata corregible, reintenta con la pregunta corregida."""\n        from src.language import consultas\n        if not self.d.pending:\n            txt_ = self.es_texto_para_aprender(raw)\n', '        """parche-95: si la respuesta es un fallo y la pregunta tiene una errata corregible, reintenta con la pregunta corregida."""\n        from src.language import consultas\n        if self.d.pending and self.d.pending[0] == "define" and is_question(raw):          # parche-131: tras «No conozco X: ¿me lo explicas?» una PREGUNTA nueva no es la explicacion: se contesta como cualquier pregunta\n            self.d.pending = None\n        if not self.d.pending:\n            txt_ = self.es_texto_para_aprender(raw)\n', '        if self.d.pending and self.d.pending[0] == "define" and is_question(raw):          # parche-131: tras «No conozco X: ¿me lo explicas?» una PREGUNTA nueva no es la explicacion: se contesta como cualquier pregunta')]
NEW_FILES = {'tests/test_parche131.py': '"""parche-131: tras «No conozco X: ¿me lo explicas?» la pregunta SIGUIENTE se contesta como cualquier pregunta.\n\nAntes, mientras esperaba la explicacion («Mongolia es un pais»), cualquier mensaje -incluida una pregunta clara- se trataba como conversacion y salia\nalgo como «Conozco 1: León.» en vez de la respuesta del texto. Ahora una pregunta cancela la espera; una explicacion («es un pais de Asia») sigue sirviendo."""\nfrom src.language.dialogue import Conversation\n\n\nclass _ParserFalso:\n    today = None\n\n    def parse(self, texto, tema=None):\n        return []\n\n\ndef _conv(tmp_path):\n    from src.language.qa import QA\n    from src.memory.store import MemoryStore\n    mem = MemoryStore(str(tmp_path / "m.json"))\n    return Conversation(mem, _ParserFalso(), lambda m, p: QA(m, p.parse, lambda facts: {}))\n\n\ndef test_una_pregunta_cancela_la_espera_antes_de_contestar(tmp_path, monkeypatch):\n    c = _conv(tmp_path)\n    c.m.textos = ["texto leido"]                                                                # hay un texto leido: la pregunta debe poder contestarse con el\n    vistas = []\n    original = c._say1\n\n    def espia(raw):\n        vistas.append(c.d.pending)                                                              # lo que ve el contestador al empezar\n        return original(raw)\n\n    monkeypatch.setattr(c, "_say1", espia)\n    c.d.pending = ("define", "Mongolia")\n    c.say("¿Cuántas horas al día está inactivo el león?")\n    assert vistas and vistas[0] is None\n\n\ndef test_una_pregunta_aritmetica_tambien_se_contesta(tmp_path):\n    c = _conv(tmp_path)\n    c.d.pending = ("define", "Mongolia")\n    assert "45" in c.say("¿Cuánto es 15 por 3?")\n    assert c.d.pending is None\n\n\ndef test_sin_signos_de_pregunta_la_espera_sigue_viva(tmp_path):\n    c = _conv(tmp_path)\n    c.d.pending = ("define", "Mongolia")\n    c.say("Es un país de Asia.")\n    assert c.d.pending is None                      # la explicacion se consume como siempre\n\n\ndef test_otras_esperas_no_se_tocan(tmp_path):\n    c = _conv(tmp_path)\n    c.d.pending = ("name", "")\n    c.say("Marcos")\n    assert c.d.user == "Marcos"\n'}
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
        if new in txt:                            # ya aplicado (la marca puede repetirse en otro sitio; se mira el trozo entero)
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
    print(f"parche-131 instalado. Copias en {bk}" if plan else "parche-131: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

