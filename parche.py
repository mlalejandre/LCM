"""parche-86: decimo lote SIMBOLICO (no reentrena). Resultado del parche-85: todo cumple; nuevo_ciego_dialogo7_8 7/8, nuevo_ciego_dialogo_9 9/9.

  1. "¿Como lo sabes?" tras "¿Que sirve para comer?": el hecho esta guardado como SERVIR_PARA pero la pregunta se lee como "servir"; explain() ahora acepta el mismo verbo
     con preposicion (objeto libre). Verificado en replay: "Me lo dijiste tú el ...: «Un tenedor sirve para comer»".
  2. CAPACIDAD NUEVA: "El perro de Irene se llama Toby." / "Mi gato se llama Felix." se guardan como (perro_de_irene, llamarse, toby) y "¿Como se llama el perro de Irene?"
     contesta "El perro de Irene se llama Toby." (antes la escuela perdia a Irene y a Toby). Solo con nombre propio en mayuscula tras "se llama". Cambia 2 frases de las 2264 grabadas.
  Sin tocar: "¿Es Sara hermana de Tomas?" y "¿Escribe Gloria novelas?" -> NO (ver parches anteriores).

  Examen CIEGO 8 nuevo (data/ciego_ocho.tsv, 6 preguntas): "se llama" con varios animales/personas y posesivos. Informativo (criterio 0 %%).

Criterios fijados ANTES de medir: 89 tests pasan (88 + 1), los 29 examenes anteriores no bajan, nuevo_ciego_dialogo7_8 llega a 8/8 y nuevo_ciego_cuatro_14 a 14/14.
Uso:  python -m scripts.ciclo parche-86.py     (restaura solo si algo falla). No hace commits ni pushes. No reentrena.
"""
import datetime, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CK = "scripts/check.py"
CK_OLD = '("nuevo_ciego_cinco_13", "data/ciego_cinco.tsv", .0)]'
CK_NEW = '("nuevo_ciego_cinco_13", "data/ciego_cinco.tsv", .0), ("nuevo_ciego_ocho_6", "data/ciego_ocho.tsv", .0)]      # parche-86: informativo'
ALL_EDITS = [('src/language/school_parser.py', '        """None si no es una afirmacion analizable (pregunta, demasiado corta o larga); si no, lista de proposiciones."""\n        if "?" in sentence or "¿" in sentence:\n            return None\n        from datetime import date\n        from src.language.fechas import extract_abs\n        sentence, abs_iv, abs_disp = extract_abs(sentence, getattr(self, "today", None) or date.today())\n', '        """None si no es una afirmacion analizable (pregunta, demasiado corta o larga); si no, lista de proposiciones."""\n        if "?" in sentence or "¿" in sentence:\n            return None\n        mll = re.fullmatch(r"\\s*((?:el|la|mi|su|un|una)\\s+\\S+(?:\\s+(?:de|del)\\s+\\S+)?)\\s+se\\s+llama\\s+(\\S+?)\\s*[.!]?\\s*", sentence, re.I)\n        if mll and mll.group(2)[:1].isupper():       # parche-86: "El perro de Irene se llama Toby.": el nombre propio de una cosa\n            subj = mll.group(1)\n            key = "_".join(re.sub(r"^(el|la|mi|su|un|una)\\s+", "", _norm(subj)).split())\n            return [{"s": key, "p": "llamarse", "o": _norm(mll.group(2)), "neg": False, "head": 0, "si": None, "oi": None, "when": "", "when_disp": "",\n                     "when_idx": [], "q": "", "template": "{s} se llama {o}", "s_disp": subj[:1].upper() + subj[1:], "o_disp": mll.group(2)}]\n        from datetime import date\n        from src.language.fechas import extract_abs\n        sentence, abs_iv, abs_disp = extract_abs(sentence, getattr(self, "today", None) or date.today())\n', 'mll = re.fullmatch(r"\\s*((?:el|la|mi|su|un|una)\\s+\\S+(?:\\s+(?:de|del)\\s+\\S+)?)\\s+se\\s+llama\\s+(\\S+?)\\s*[.!]?\\s*", sentence, re.I)'), ('src/language/dialogue.py', '        else:\n            return "¿El qué? Pregúntame algo primero."\n        hits = qa.lookup(s, p, o)\n        if hits:\n            f = next(x for x in self.m.facts if (x["s"], x["p"], x["o"]) == hits[0] and not x.get("neg"))\n            when = datetime.fromtimestamp(f.get("t", time.time())).strftime("%d/%m/%Y")\n', '        else:\n            return "¿El qué? Pregúntame algo primero."\n        hits = qa.lookup(s, p, o)\n        if not hits and s and p:                                   # parche-86: "sirve" ~ "servir_para": mismo verbo con preposicion, objeto libre\n            head = str(p).upper().split("_")[0]\n            hits = [(x["s"], x["p"], x["o"]) for x in self.m.facts\n                    if not x.get("neg") and x["s"] == str(s).upper() and x["p"].split("_")[0] == head and (o in (None, "_") or x["o"] == str(o).upper())][:1]\n        if hits:\n            f = next(x for x in self.m.facts if (x["s"], x["p"], x["o"]) == hits[0] and not x.get("neg"))\n            when = datetime.fromtimestamp(f.get("t", time.time())).strftime("%d/%m/%Y")\n', 'if not hits and s and p:                                   # parche-86: "sirve" ~ "servir_para": mismo verbo con preposicion, objeto libre'), ('src/language/dialogue.py', '    def _definitions(self, raw: str, t: str, qa):\n        m_ = self.m\n        a = self.ART\n        # sinonimos\n        m = re.fullmatch(r"(.+?) (?:es|son) (?:lo mismo que|sinonimo de|sinonima de|igual que|equivalente a|otro nombre de|otra palabra para)\\s+(.+)|(.+?) significa (?:lo mismo que )?(.+)", t)\n        if m:\n', '    def _definitions(self, raw: str, t: str, qa):\n        m_ = self.m\n        a = self.ART\n        # nombre propio de una cosa ("El perro de Irene se llama Toby")          # parche-86\n        m = re.fullmatch(r"((?:el|la|mi|su|un|una) .+?) se llama (\\w+)", t)\n        if m and "?" not in raw:\n            key = "_".join(self._bare(m.group(1)).split()).upper()\n            mr = re.match(r"\\s*(.+?)\\s+se\\s+llama\\s+(\\S+?)[\\s.!]*$", raw, re.I)\n            val = (mr.group(2) if mr else m.group(2)).strip(".!")\n            m_.add_fact((key, "LLAMARSE", norm(val).upper()), source=raw.strip())\n            m_.display[key] = (mr.group(1) if mr else m.group(1)).strip()\n            m_.display[norm(val).upper()] = val\n            return f"Entendido: {m_.display[key]} se llama {val}.", None\n        # sinonimos\n        m = re.fullmatch(r"(.+?) (?:es|son) (?:lo mismo que|sinonimo de|sinonima de|igual que|equivalente a|otro nombre de|otra palabra para)\\s+(.+)|(.+?) significa (?:lo mismo que )?(.+)", t)\n        if m:\n', '# nombre propio de una cosa ("El perro de Irene se llama Toby")          # parche-86'), ('src/language/qa.py', '            if opposite(m.group(1), m.group(2), getattr(self.m, "opposites", [])):\n                return f"Sí, {m.group(1)} es lo contrario de {m.group(2)}."\n            return "No lo sé."\n        m = re.fullmatch(r"(?:cual|que) (?:es|seria) (?:lo contrario|lo opuesto|el contrario|el opuesto) de (\\w+)", t)\n        if m:                                                    # parche-84: el contrario es simetrico ("Alto es lo contrario de bajo" -> "¿Cual es lo contrario de bajo?")\n            x = m.group(1).upper()\n', '            if opposite(m.group(1), m.group(2), getattr(self.m, "opposites", [])):\n                return f"Sí, {m.group(1)} es lo contrario de {m.group(2)}."\n            return "No lo sé."\n        m = re.fullmatch(r"(?:como|que nombre) (?:se llama|tiene) (.+)", t)\n        if m:                                                    # parche-86: "¿Como se llama el perro de Irene?" -> hecho (PERRO_DE_IRENE, LLAMARSE, TOBY)\n            key = "_".join(re.sub(r"^(el|la|mi|su|un|una)\\s+", "", m.group(1)).split()).upper()\n            fs = [f for f in facts if f["p"] == "LLAMARSE" and f["s"] == key and not f.get("neg")]\n            if fs:\n                disp = getattr(self.m, "display", {})\n                return f"{disp.get(key, key.replace(\'_\', \' \').title())} se llama {disp.get(fs[-1][\'o\'], fs[-1][\'o\'].title())}."\n        m = re.fullmatch(r"(?:cual|que) (?:es|seria) (?:lo contrario|lo opuesto|el contrario|el opuesto) de (\\w+)", t)\n        if m:                                                    # parche-84: el contrario es simetrico ("Alto es lo contrario de bajo" -> "¿Cual es lo contrario de bajo?")\n            x = m.group(1).upper()\n', 'm = re.fullmatch(r"(?:como|que nombre) (?:se llama|tiene) (.+)", t)')] + [(CK, CK_OLD, CK_NEW, "nuevo_ciego_ocho_6")]
NEW_FILES = {"tests/test_parche86.py": '"""parche-86: nombre propio de una cosa ("se llama") y "¿Como lo sabes?" con verbo + preposicion."""\nfrom src.language.qa import QA\nfrom src.language.school_parser import SchoolParser\nfrom src.memory.store import MemoryStore\n\n\ndef test_se_llama(tmp_path):\n    p = SchoolParser.__new__(SchoolParser)\n    p.today = None\n    got = SchoolParser.parse(p, "El perro de Irene se llama Toby.")\n    assert [(t["s"], t["p"], t["o"]) for t in got] == [("perro_de_irene", "llamarse", "toby")]\n    m = MemoryStore(str(tmp_path / "m.json"))\n    for t in got:\n        tr = (t["s"], t["p"], t["o"])\n        m.add_fact(tr, source="x")\n        m.note_surface(tr, t["template"], t["s_disp"], t["o_disp"])\n    qa = QA(m, lambda s: None)\n    assert qa.answer("¿Cómo se llama el perro de Irene?") == "El perro de Irene se llama Toby."\n\n', "data/ciego_ocho.tsv": '# Examen CIEGO 8 (parche-86): "se llama", varios animales con nombre, posesivos. Informativo.\nH: Mi gato se llama Félix.\nP: ¿Cómo se llama mi gato?\tFélix\n\nH: El perro de Marta se llama Rex.\nH: El gato de Marta se llama Mía.\nP: ¿Cómo se llama el perro de Marta?\tRex\nP: ¿Cómo se llama el gato de Marta?\tMía\n\nH: La hija de Luis se llama Clara.\nP: ¿Cómo se llama la hija de Luis?\tClara\n\nH: Sofía tiene un perro.\nH: El perro de Sofía se llama Nube.\nP: ¿Tiene Sofía un perro?\tSI\nP: ¿Cómo se llama el perro de Sofía?\tNube\n'}


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
    print(f"parche-86 instalado. Copias en {bk}" if plan else "parche-86: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())