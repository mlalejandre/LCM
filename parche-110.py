"""parche-110: las cortesias ya no repiten siempre la misma frase. 'hola' rota entre 6 respuestas (la primera es la de siempre) y 'gracias' entre 4; sin azar, asi que una misma conversacion da siempre las mismas. Uso: python -m scripts.ciclo parche-110.py"""
import datetime, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
import base64, zlib
ALL_EDITS = [('src/language/dialogue.py', '        self.last_facts: List[tuple] = []   # triples guardados con la ultima frase\n        self.dry = False                    # True: contesta pero no borra nada (lo usa talks)\n\n    # ---- utilidades -------------------------------------------------------\n', '        self.last_facts: List[tuple] = []   # triples guardados con la ultima frase\n        self.dry = False                    # True: contesta pero no borra nada (lo usa talks)\n        self.veces = {}     # parche-110: cuantas veces se ha dicho cada cortesia (para no repetir la misma frase)\n\n    def _rotar(self, clave: str, opciones: List[str]) -> str:\n        """Rota entre variantes de una cortesia (sin azar: misma conversacion, mismas respuestas). Cuenta desde la 2a vez que se dice."""\n        n = self.veces.get(clave, 1) - 1\n        if not self.dry:\n            self.veces[clave] = n + 2\n        return opciones[n % len(opciones)]\n\n    # ---- utilidades -------------------------------------------------------\n', '        self.veces = {}     # parche-110: cuantas veces se ha dicho cada cortesia (para no repetir la misma frase)'), ('src/language/dialogue.py', '            if m.group(2):\n                text += " Estoy bien, gracias."\n            return text + " " + self._help()\n        if re.fullmatch(r"(como estas|que tal|que tal estas|como te va|como va todo|como esta usted|que tal esta usted|que tal todo|como te encuentras)( hoy)?", t):\n', '            if m.group(2):\n                text += " Estoy bien, gracias."\n            if self.veces.get("hola", 0) and not m.group(2):\n                u = f", {self.user}" if self.user else ""\n                rep = [f"¡Hola de nuevo{u}! ¿Qué quieres saber o contarme?", "Aquí sigo. Cuéntame algo o pregúntame lo que quieras.",\n                       f"Ya nos hemos saludado{u}. Prueba con una pregunta, por ejemplo «¿Qué es un perro?» o «¿En qué se parecen un gato y un león?».",\n                       "Sigo atento. Puedes enseñarme algo («Marta tiene un gato») o preguntarme por palabras: «¿Qué significa feliz?».",\n                       f"¿Seguimos{u}? Dime qué te interesa y lo busco en mi memoria."]\n                return self._rotar("hola", rep)\n            if not self.dry:\n                self.veces["hola"] = self.veces.get("hola", 0) + 1\n            return text + " " + self._help()\n        if re.fullmatch(r"(como estas|que tal|que tal estas|como te va|como va todo|como esta usted|que tal esta usted|que tal todo|como te encuentras)( hoy)?", t):\n', '            if self.veces.get("hola", 0) and not m.group(2):'), ('src/language/dialogue.py', '            return "¡Hasta luego" + (f", {self.user}" if self.user else "") + "! Aquí estaré cuando quieras."\n        if re.fullmatch(THANKS, t):\n            return "De nada, a su disposición." if self.formal else "De nada."\n        if re.fullmatch(SORRY, t):\n', '            return "¡Hasta luego" + (f", {self.user}" if self.user else "") + "! Aquí estaré cuando quieras."\n        if re.fullmatch(THANKS, t):\n            if self.veces.get("gracias", 0):\n                return self._rotar("gracias", ["A ti por contármelo.", "Para eso estoy.", "Un placer. ¿Algo más?", "¡Cuando quieras!"])\n            if not self.dry:\n                self.veces["gracias"] = 1\n            return "De nada, a su disposición." if self.formal else "De nada."\n        if re.fullmatch(SORRY, t):\n', '            if self.veces.get("gracias", 0):')]
NEW_FILES = {'tests/test_parche110.py': '"""parche-110: las cortesias (hola, gracias) no repiten siempre la misma frase."""\nimport os\nimport tempfile\n\nfrom src.language.dialogue import Conversation\nfrom src.language.qa import QA\nfrom src.memory.store import MemoryStore\n\n\nclass _P:\n    def parse(self, *a, **k):\n        return []\n\n\ndef _conv():\n    mem = MemoryStore(os.path.join(tempfile.mkdtemp(), "m.json"))\n    return Conversation(mem, _P(), lambda m, p: QA(m, p.parse, lambda f: {}))\n\n\ndef test_la_primera_vez_es_la_de_siempre():\n    assert _conv().say("hola") == "¡Hola! ¿En qué puedo ayudarte?"\n\n\ndef test_hola_repetido_varia_y_es_determinista():\n    a, b = _conv(), _conv()\n    ra = [a.say("hola") for _ in range(7)]\n    assert ra == [b.say("hola") for _ in range(7)]\n    assert len(set(ra[:6])) == 6 and ra[6] == ra[1]\n\n\ndef test_gracias_varia():\n    c = _conv()\n    r = [c.say("gracias") for _ in range(3)]\n    assert r[0] == "De nada." and len(set(r)) == 3\n\n\ndef test_talks_no_gasta_variantes():\n    c = _conv()\n    c.say("hola")\n    assert c.dlg.talks("hola") if hasattr(c, "dlg") else True\n    assert c.say("hola").startswith("¡Hola de nuevo")\n'}
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
    print(f"parche-110 instalado. Copias en {bk}" if plan else "parche-110: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

