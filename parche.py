"""parche-85: noveno lote SIMBOLICO (no reentrena). Resultado del parche-84: definiciones_29 de nuevo al 100 %%, nuevo_ciego_cinco_13 12/13, dialogo ciego 6: 7/9.

  1. "No, Marta vive en Vigo." (tras "Marta vive en Lugo."): se leia como NEGACION de Vigo y la memoria seguia en Lugo. Un "No," inicial con coma y una frase afirmativa sin otra
     negacion es una CORRECCION: se procesa la frase sin el "No,". Verificado en replay con Ana/Madrid/Sevilla: "Vale: antes decias que Ana vive en Madrid; ahora lo tomo como pasado",
     "¿Donde vive Ana?" -> Sevilla. (Marta/Vigo no se puede verificar: esas frases no estaban grabadas.) No se aplica si hay una pregunta pendiente (pending) ni a "No, gracias".
  2. "¿Como lo sabes?" tras una pregunta ESPECIAL ("¿Para que sirve un martillo?"): las preguntas que contesta act() sin pasar por after_answer no guardaban last_question
     y respondia "¿El qué? Pregúntame algo primero". Ahora se guarda (salvo las meta-preguntas "como lo sabes/seguro/repite"). Verificado en replay: "Me lo dijiste tú el ...".
  FUERA DE ALCANCE (sin tocar): "¿Es Sara hermana de Tomas?", "se llama", "¿Escribe Gloria novelas?" -> NO.

  Dialogo CIEGO 7 nuevo (data/dialogo_ciego_siete.tsv, 8 turnos): nombre, "No," como correccion + pasado, "que sirve para", padre de, quien es X. Informativo (criterio 0 %%).

Criterios fijados ANTES de medir: 88 tests pasan (87 + 1), los 27 examenes anteriores no bajan, nuevo_ciego_dialogo_9 llega a >= 8/9.
Uso:  python -m scripts.ciclo parche-85.py     (restaura solo si algo falla). No hace commits ni pushes. No reentrena.
"""
import datetime, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CK = "scripts/check.py"
CK_OLD = '("nuevo_ciego_dialogo", "data/dialogo_ciego_seis.tsv", .0)):'
CK_NEW = '("nuevo_ciego_dialogo", "data/dialogo_ciego_seis.tsv", .0), ("nuevo_ciego_dialogo7", "data/dialogo_ciego_siete.tsv", .0)):      # parche-85: informativo'
ALL_EDITS = [('src/language/dialogue.py', '        self.topic = None\n\n    def say(self, raw: str) -> str:\n        reply, cont = self.d.act(raw, self.qa)\n        out = []\n        if reply:\n            out.append(reply)\n', '        self.topic = None\n\n    def say(self, raw: str) -> str:\n        mc = re.match(r"^\\s*no\\s*,\\s+(\\S.*)$", raw, re.I)\n        if mc and not self.d.pending and not is_question(mc.group(1)) and len(mc.group(1).split()) >= 3 \\\n                and not re.search(r"\\b(no|nunca|nadie|ni|tampoco|nada|jamas)\\b", n(mc.group(1))):\n            raw = mc.group(1)[:1].upper() + mc.group(1)[1:]             # parche-85: "No, Marta vive en Vigo." es una correccion, no una negacion de Vigo\n        reply, cont = self.d.act(raw, self.qa)\n        if reply and not cont and is_question(raw) and not re.search(r"\\b(sabes|sacas|seguro|repite)\\b", n(raw)):\n            self.d.last_question = raw                                      # parche-85: las preguntas especiales tambien se pueden justificar ("¿Como lo sabes?")\n        out = []\n        if reply:\n            out.append(reply)\n', 'parche-85: "No, Marta vive en Vigo." es una correccion')] + [(CK, CK_OLD, CK_NEW, "nuevo_ciego_dialogo7")]
NEW_FILES = {"tests/test_parche85.py": '"""parche-85: "No, X ..." es una correccion y las preguntas especiales se pueden justificar."""\nimport re\n\nfrom src.language.dialogue import Conversation\n\n\nclass _QA:\n    def answer(self, q):\n        return "ok"\n\n    def read(self, q):\n        return None, None\n\n\ndef test_no_coma_es_correccion(tmp_path):\n    from src.memory.store import MemoryStore\n    m = MemoryStore(str(tmp_path / "m.json"))\n    seen = []\n\n    class P:\n        today = None\n\n        def parse(self, s, topic=None, verbs=None):\n            seen.append(s)\n            return None\n\n    c = Conversation(m, P(), lambda mem, p: _QA())\n    c.say("No, Marta vive en Vigo.")\n    assert "Marta vive en Vigo." in seen and not any(s.startswith("No,") for s in seen)\n    seen.clear()\n    c.say("No, no vive en Vigo.")                              # con otra negacion no se toca\n    assert any(s.lower().startswith("no") for s in seen)\n', "data/dialogo_ciego_siete.tsv": '# Dialogo CIEGO 7 (parche-85): correcciones con "No,", pasado, "que sirve para", parentesco, definicion de persona. Informativo.\nU: Soy Pablo.\t\nU: ¿Cómo me llamo?\tPablo\n\nU: Ana compra pan.\t\nU: ¿Qué compra Ana?\tpan\n\nU: Rosa vive en Sevilla.\t\nU: No, Rosa vive en Cádiz.\t\nU: ¿Dónde vive Rosa?\tCádiz\nU: ¿Dónde vivía Rosa?\tSevilla\n\nU: Un tenedor sirve para comer.\t\nU: ¿Qué sirve para comer?\ttenedor\nU: ¿Cómo lo sabes?\tdijiste\n\nU: Luis es el padre de Juan.\t\nU: ¿Quién es el padre de Juan?\tLuis\n\nU: Sara es profesora.\t\nU: ¿Quién es Sara?\tprofesora\n'}


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
    print(f"parche-85 instalado. Copias en {bk}" if plan else "parche-85: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())