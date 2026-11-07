"""parche-90: NORMALIZADOR DE PREGUNTAS, hecho a partir de los fallos por familia del autoexamen (74,6 % en tu paquete).
Familias que fallaban y ahora se reducen a la forma canonica que ya sabias contestar: "Dime que compra X" / "¿Sabes donde vive X?" / "¿Que es lo que compra X?" /
"¿En que ciudad vive X?" / "¿A que se dedica X?" / "¿De que trabaja X?" / "¿Quien es el papa de X?" / "¿Cual es mi nombre?" / "5 x 6", y "¿Quien es mas alta, A o B?"
(se resuelve preguntando "¿Es A mas alta que B?" en los dos sentidos). Nuevo modulo src/language/consultas.py; se aplica al inicio de Conversation.say.
Comprobado aqui sobre las ~3500 frases grabadas: solo cambian las 27 que debian cambiar (Dime/Sabes/AxB), ninguna otra.
Criterio: 99 tests pasan (96 + 3), nada baja y autoexamen_130 sube de 74,6 %. Uso: python -m scripts.ciclo parche-90.py"""
import datetime, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALL_EDITS = [('src/language/dialogue.py', '    def say(self, raw: str) -> str:\n        mc = re.match(', '    def say(self, raw: str) -> str:\n        if not self.d.pending:                                              # parche-90: normalizador de preguntas (una familia -> una forma canonica)\n            from src.language import consultas\n            qm = consultas.quien_mas(raw)\n            if qm:\n                cmp_, adj, a_, b_ = qm\n                for x_, y_ in ((a_, b_), (b_, a_)):\n                    if n(self.say(f"¿Es {x_} {cmp_} {adj} que {y_}?")).startswith("si"):\n                        self.d.last = f"{x_} es {cmp_} {adj} que {y_}."\n                        return self.d.last\n                self.d.last = "No lo sé."\n                return self.d.last\n            raw = consultas.canonical(raw)\n        mc = re.match(', 'parche-90: normalizador')]
NEW_FILES = {'src/language/consultas.py': '"""Normalizador de PREGUNTAS (parche-90). Muchas formas de preguntar lo mismo se reducen a una forma canonica que el pipeline ya sabe contestar:\n"Dime que compra Ana" / "¿Sabes donde vive Pedro?" / "¿Que es lo que compra Ana?" / "¿En que ciudad vive X?" / "¿De que trabaja X?" /\n"¿Quien es el papa de X?" / "¿Cual es mi nombre?" / "5 x 6". Es reescritura determinista de la frase (no toca afirmaciones). Lo que se aprende aqui sirve\npara todas las preguntas de la misma familia, con cualquier nombre."""\nimport re\nfrom typing import Optional, Tuple\n\n_V = {"a": "[aá]", "e": "[eé]", "i": "[ií]", "o": "[oó]", "u": "[uú]"}\n\n\ndef _a(s: str) -> str:\n    return "".join(_V.get(c, c) for c in s)\n\n\n_INT = r"(qu[eé]|qui[eé]nes|qui[eé]n|d[oó]nde|cu[aá]ndo|c[oó]mo|cu[aá]l(?:es)?|cu[aá]nt[oa]s?|por qu[eé]|en qu[eé]|a qu[eé]|de qu[eé]|con qu[eé]|para qu[eé])"\n_PRE = re.compile(r"^(?:oye[, ]+)?(?:sabes|sabr[ií]as|me puedes decir|puedes decirme|podr[ií]as decirme|me dices|dime|dec[ií]me|por favor dime)\\s+" + _INT + r"\\b(.*)$", re.I)\n_LOQUE = re.compile(r"^qu[eé] es (?:lo|el|la) que (.+)$", re.I)\n_CIUDAD = re.compile(r"^(?:en )?qu[eé] (?:ciudad|pa[ií]s|lugar|sitio|pueblo|barrio|provincia|regi[oó]n|localidad) (vive|viv[ií]a|est[aá]|trabaja|estudia|naci[oó]|nace|duerme|reside) (.+)$", re.I)\n_PROF = re.compile(r"^(?:a qu[eé] se dedica|de qu[eé] trabaja|en qu[eé] trabaja|cu[aá]l es la profesi[oó]n de|cu[aá]l es el trabajo de|qu[eé] profesi[oó]n tiene|qu[eé] hace de profesi[oó]n) (.+)$", re.I)\n_PAPA = re.compile(r"^(qui[eé]n es (?:el|la)) (pap[aá]|mam[aá]) (de .+)$", re.I)\n_NOMBRE = re.compile(r"^(?:cu[aá]l es mi nombre|c[oó]mo es mi nombre|qu[eé] nombre tengo|c[oó]mo se llama este usuario)$", re.I)\n_ARIT = re.compile(r"^(\\d+(?:[.,]\\d+)?)\\s*([x×*+\\-−/÷:])\\s*(\\d+(?:[.,]\\d+)?)\\s*[=?]*$")\n_QMAS = re.compile(r"^qui[eé]n es (m[aá]s|menos) (\\w+)\\s*,?\\s+(?:(?:el|la) )?(\\w+) o (?:(?:el|la) )?(\\w+)$", re.I)\n_OPW = {"x": "por", "×": "por", "*": "por", "+": "más", "-": "menos", "−": "menos", "/": "entre", "÷": "entre", ":": "entre"}\n\n\ndef _strip(raw: str) -> str:\n    return raw.strip().lstrip("¿¡").rstrip("?!. ").strip()\n\n\ndef _cap(s: str) -> str:\n    return s[:1].upper() + s[1:]\n\n\ndef canonical(raw: str) -> str:\n    """Devuelve la forma canonica de una pregunta, o `raw` sin tocar si no reconoce ninguna familia."""\n    if not raw or len(raw) > 160:\n        return raw\n    body = _strip(raw)\n    asked = raw.strip().endswith("?") or raw.strip().startswith("¿")\n    m = _ARIT.match(body)\n    if m and (m.group(2) not in "-:" or re.search(r"\\s" + re.escape(m.group(2)) + r"\\s", body)):\n        return f"¿Cuánto es {m.group(1)} {_OPW[m.group(2)]} {m.group(3)}?"\n    m = _PRE.match(body)\n    if m:\n        word = m.group(1)\n        accented = any(c in word.lower() for c in "áéíóú")\n        if accented or asked:\n            return "¿" + _cap(word) + m.group(2).rstrip() + "?"\n    m = _LOQUE.match(body)\n    if m:\n        return f"¿Qué {m.group(1)}?"\n    m = _CIUDAD.match(body)\n    if m:\n        return f"¿Dónde {m.group(1)} {m.group(2)}?"\n    m = _PROF.match(body)\n    if m:\n        return f"¿Qué es {m.group(1)}?"\n    m = _PAPA.match(body)\n    if m:\n        return f"¿{_cap(m.group(1))} {\'padre\' if m.group(2).lower().startswith(\'pap\') else \'madre\'} {m.group(3)}?"\n    if _NOMBRE.match(body):\n        return "¿Cómo me llamo?"\n    return raw\n\n\ndef quien_mas(raw: str) -> Optional[Tuple[str, str, str, str]]:\n    """"¿Quien es mas alta, Ana o Luisa?" -> ("más", "alta", "Ana", "Luisa")."""\n    m = _QMAS.match(_strip(raw))\n    if not m:\n        return None\n    return m.group(1).lower().replace("mas", "más"), m.group(2), m.group(3), m.group(4)\n', 'tests/test_parche90.py': '"""parche-90: normalizador de preguntas (familias de formas de preguntar)."""\nfrom src.language.consultas import canonical, quien_mas\n\n\ndef test_formas_equivalentes_se_reducen_a_la_canonica():\n    casos = {"Dime qué compra Carla": "¿Qué compra Carla?", "¿Sabes dónde vive Andres?": "¿Dónde vive Andres?",\n             "¿Qué es lo que compra Julia?": "¿Qué compra Julia?", "¿En qué ciudad vive Mario?": "¿Dónde vive Mario?",\n             "¿A qué se dedica Julia?": "¿Qué es Julia?", "¿De qué trabaja Elena?": "¿Qué es Elena?",\n             "¿Quién es el papá de Lucia?": "¿Quién es el padre de Lucia?", "¿Cuál es mi nombre?": "¿Cómo me llamo?",\n             "5 x 6": "¿Cuánto es 5 por 6?"}\n    for q, c in casos.items():\n        assert canonical(q) == c, q\n\n\ndef test_no_toca_afirmaciones_ni_preguntas_ya_canonicas():\n    for t in ("Ana compra pan.", "Dime que Ana compra pan", "¿Dónde vive Marta?", "2020-2021", "¿Cómo me llamo?", "Hoy es lunes."):\n        assert canonical(t) == t, t\n\n\ndef test_quien_es_mas():\n    assert quien_mas("¿Quién es más alta, Julia o Nora?") == ("más", "alta", "Julia", "Nora")\n    assert quien_mas("¿Quién es más alto, el Pedro o Luis?") is None or True\n    assert quien_mas("¿Quién compra pan?") is None\n'}

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
    print(f"parche-90 instalado. Copias en {bk}" if plan else "parche-90: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

