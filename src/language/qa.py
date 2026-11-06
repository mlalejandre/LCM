"""Preguntas y respuestas en espanol (parche-35, Fase 1). Sin LLM.

Una pregunta se reescribe como afirmacion con un hueco ("Xqx") y se lee con la MISMA escuela que lee las afirmaciones:
  "Quien escribio una novela?"   -> "Xqx escribio una novela."    (hueco = sujeto)
  "Que escribio Marta?"          -> "Marta escribio Xqx."         (hueco = objeto)
  "Vive Pedro en Madrid?"        -> "Pedro vive en Madrid."       (si/no)
Luego se busca en la memoria (con la misma tolerancia de relacion que el test de conversacion) y, si no esta, se intenta
DEDUCIR con las lecciones aprendidas. Se contesta con las palabras que uso la persona (plantillas y nombres guardados).
Cuando no se sabe, se dice "no lo se" (mundo abierto): no se inventa.
"""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .lexicon import norm

MODAL_VERBS = {"puede", "pueden", "debe", "deben", "quiere", "quieren", "podia", "queria", "pudo", "debia"}
HOLE = "Xqx"
HOLES = ("Xqx", "Zurita", "Bertoldo")      # parche-41: si la escuela no lee uno, se prueba otro nombre inventado
DETS = {"el", "la", "los", "las", "un", "una", "unos", "unas", "su", "sus", "mi", "mis", "tu", "tus"}
WH = {"quien", "quienes", "que", "cual", "cuales"}
ADV = {"donde": "en", "como": "con"}


def template_from(raw: str, s: str, o: str):
    """Plantilla "{s} es hijo de {o}" sacada de la frase tal como la dijo la persona (para frases que entiende el oido de plantillas
    o las dos mitades de una regla). Devuelve (plantilla, como_se_escribia_s, como_se_escribia_o) o None."""
    words = re.findall(r"\w+|[^\w\s]", raw)
    low = [norm(w) for w in words]
    si = [i for i, w in enumerate(low) if w == norm(s)]
    oi = [i for i, w in enumerate(low) if w == norm(o)]
    if not si or not oi or si[0] == oi[0]:
        return None
    toks = []
    for i, w in enumerate(words):
        if not re.match(r"\w", w):
            continue
        toks.append("{s}" if i == si[0] else "{o}" if i == oi[0] else (w.lower() if i == 0 else w))
    text = " ".join(toks).replace(" de el ", " del ").replace(" a el ", " al ")
    return text, words[si[0]], words[oi[0]]


def is_question(text: str) -> bool:
    t = text.strip()
    return t.startswith("¿") or t.endswith("?")


def pred_key(p: str) -> str:
    head, _, prep = norm(p).partition("_")
    head = {"tia": "tio"}.get(head, head)                       # tio/tia, hijo/hija... (parche-59)
    return head[:3] + "|" + ("" if prep == "a" else prep)      # la "a" personal (conocer a Pablo) no distingue la relacion


def same_pred(a: str, b: str) -> bool:
    if pred_key(a) != pred_key(b):
        return False
    ha, hb = a.lower().partition("_")[0], b.lower().partition("_")[0]
    if ha != hb and ha[-2:] in ("ar", "er", "ir") and hb[-2:] in ("ar", "er", "ir") and ha[-2:] != hb[-2:]:
        return False                                  # venir / vender: mismas 3 letras, verbos distintos
    return True


def _words(text: str) -> List[str]:
    return re.findall(r"\w+", text.replace("¿", " ").replace("?", " "), flags=re.U)


def rewrite(question: str, hole: str = HOLE) -> Tuple[List[str], str]:
    cands, kind = _rewrite(question, hole)
    caps = [c[:1].upper() + c[1:] for c in cands if c[:1].islower()]
    return cands + [c for c in caps if c not in cands], kind


def _rewrite(question: str, hole: str = HOLE) -> Tuple[List[str], str]:
    """Devuelve (candidatos de afirmacion, tipo). tipo: 'sujeto' | 'objeto' | 'si_no'. Lista vacia si no se sabe."""
    w = _words(question)
    if not w:
        return [], ""
    low = [norm(x) for x in w]
    prep = ""
    i = 0
    if low[0] in ("a", "de", "con", "en", "para", "por") and len(low) > 1 and low[1] in WH:
        prep, i = w[0].lower(), 1
    if low[0] == "cuando" and len(w) >= 3:                       # "Cuando compro Pedro pan?" -> frase sin el "cuando"
        rest = w[1:]
        cands = [" ".join(rest) + "."]
        if len(rest) >= 3 and norm(rest[1]) in DETS:
            cands.append(" ".join([rest[1], rest[2], rest[0].lower()] + rest[3:]) + ".")
        cands.append(" ".join([rest[1], rest[0].lower()] + rest[2:]) + ".")
        return cands, "cuando"
    if low[i] in ADV and prep == "":
        prep, hole_at = ADV[low[i]], i
        rest = w[i + 1:]
        if len(rest) < 2:
            return [], ""
        # "Donde estudia Luis musica?" -> "Luis estudia musica en Xqx" (el verbo detras del sujeto, el hueco al final)
        return [" ".join([rest[1], rest[0]] + rest[2:] + [prep, hole]) + "."], "objeto"
    if low[i] in WH:
        rest = w[i + 1:]
        if not rest:
            return [], ""
        pre = [prep] if prep else []
        if i == 0 and low[0] in ("quien", "quienes") and low[1:2] == ["es"] and len(rest) == 2 and rest[1][:1].isupper():
            return [" ".join(rest[1:] + [rest[0], hole]) + "."], "objeto"           # "Quien es Marta?" -> definicion de Marta
        if i == 0 and not prep:
            # "Quien escribio X?" -> hueco sujeto ; "Que escribio Marta?" -> hueco objeto
            cands = []
            if low[0] in ("quien", "quienes"):
                cands.append(" ".join([hole] + rest) + ".")
            if len(rest) >= 3 and norm(rest[0]) in MODAL_VERBS and norm(rest[1])[-2:] in ("ar", "er", "ir") and low[0] not in ("quien", "quienes"):
                cands.append(" ".join([rest[2], rest[0], rest[1], hole] + rest[3:]) + ".")      # "Que quiere comer Ana?"
            if len(rest) >= 2:
                cands.append(" ".join(rest[1:] + [rest[0], hole]) + ".")
            return cands, "sujeto" if low[0] in ("quien", "quienes") else "objeto"
        if len(rest) >= 2:                                     # "A quien llamo Pedro?" -> "Pedro llamo a Xqx"
            return [" ".join(rest[1:] + [rest[0]] + pre + [hole]) + "."], "objeto"
        return [], ""
    # si / no: la frase tal cual, y la version con el verbo detras del sujeto ("Vive Pedro en Madrid")
    cands = [" ".join(w) + "."]
    if len(w) >= 3 and norm(w[1]) in DETS:                      # "Ensena la maestra matematicas" -> "la maestra ensena matematicas"
        cands.append(" ".join([w[1], w[2], w[0].lower()] + w[3:]) + ".")
    if len(w) >= 2:
        cands.append(" ".join([w[1], w[0].lower()] + w[2:]) + ".")
    if len(w) >= 3 and norm(w[0]) in ("es", "esta", "son", "estan", "era", "estaba"):                  # "Esta triste Ana" -> "Ana esta triste"
        cands.append(" ".join([w[2], w[0].lower(), w[1]] + w[3:]) + ".")
    if len(w) >= 3 and norm(w[0]) in MODAL_VERBS and norm(w[1])[-2:] in ("ar", "er", "ir"):       # "Debe estudiar Luis matematicas"
        cands.append(" ".join([w[2], w[0].lower(), w[1]] + w[3:]) + ".")
    return cands, "si_no"


from src.reasoning.lessons import canon


class QA:
    """memory: MemoryStore (con .facts, .surface, .display). parse: frase -> lista de dicts {s,p,o,neg} o None.
    deduce: opcional, (lista de hechos (s,p,o) sin negar) -> conjunto de (s,p,o) deducidos."""

    def __init__(self, memory, parse: Callable[[str], Optional[List[Dict]]],
                 deduce: Optional[Callable[[Sequence[Tuple[str, str, str]]], set]] = None):
        self.m, self.parse, self.deduce = memory, parse, deduce
        self._tpl = None
        self._alts = []
        self.support = {}

    # ---- lectura de la pregunta ------------------------------------
    def read(self, question: str):
        kind = ""
        for hole in HOLES:
            cands, kind = rewrite(question, hole)
            alts = []
            for c in cands:
                found = self.parse(c)
                if not found:
                    continue
                for t in found:
                    if kind in ("si_no", "cuando"):
                        alts.append(t)
                        if len(alts) == 1:
                            self._alts = alts            # todas las lecturas posibles; answer() prefiere la que encaja con la memoria
                        continue
                    if hole.lower() in (t["s"], t["o"]):
                        t = dict(t)
                        for k in ("s", "o"):
                            if t[k] == hole.lower():
                                t[k] = norm(HOLE)           # el resto del codigo usa un unico nombre de hueco
                        return ("sujeto" if t["s"] == norm(HOLE) else "objeto"), t
            if kind in ("si_no", "cuando"):
                if alts:
                    for a_ in alts:                          # "Un cuadrado es una figura": dos sustantivos, no adjetivo (parche-59)
                        if kind == "si_no" and a_["p"] == "ser" and all((a_.get(k) or "").lower().startswith(("un ", "una ", "el ", "la ", "los ", "las ")) for k in ("s_disp", "o_disp")):
                            a_["p"] = "es"
                    a0 = alts[0]
                    ind = lambda d: (d or "").lower().startswith(("un ", "una "))
                    if kind == "si_no" and a0["p"] in ("es", "ser") and ind(a0.get("s_disp")) and ind(a0.get("o_disp")) \
                            and a0.get("template", "").startswith("es {o} {s}"):
                        sw = dict(a0)                       # "¿Es un A un B?": A es el sujeto (parche-58)
                        sw["s"], sw["o"], sw["s_disp"], sw["o_disp"] = a0["o"], a0["s"], a0["o_disp"], a0["s_disp"]
                        sw["template"] = "{s} es {o}"
                        self._alts = [sw, a0]
                        return kind, sw
                    return kind, a0
                break
        return kind, None

    # ---- memoria ----------------------------------------------------
    def _facts(self, neg=False):
        return [(f["s"], f["p"], f["o"]) for f in self.m.facts if bool(f.get("neg", False)) == neg]

    def _whens(self, fact):
        """[(clave, como se dijo)] de las veces que se guardo ese hecho (no negado)."""
        return [(f.get("when", ""), f.get("when_disp", "")) for f in self.m.facts
                if (f["s"], f["p"], f["o"]) == tuple(fact) and not f.get("neg")]

    def _today(self):
        from datetime import date
        return getattr(self.m, "today", None) or date.today()

    def _when_ok(self, fact, when):
        """El hecho se dijo con ese tiempo: misma clave, o fechas absolutas que se contienen ("ayer" = "el 5 de noviembre")."""
        from src.language.fechas import resolve, contains
        want = resolve(when, self._today())
        for f in self.m.facts:
            if (f["s"], f["p"], f["o"]) != tuple(fact) or f.get("neg"):
                continue
            if f.get("when", "") == when:
                return True
            if want and f.get("when_abs") and contains(f["when_abs"], want):
                return True
        return False

    def _q(self, fact):
        return next((f.get("q") for f in self.m.facts if (f["s"], f["p"], f["o"]) == tuple(fact) and not f.get("neg")), "")

    def _abs_of(self, fact):
        for f in self.m.facts:
            if (f["s"], f["p"], f["o"]) == tuple(fact) and not f.get("neg") and f.get("when_abs"):
                return f["when_abs"], f.get("when", "")
        return None, ""

    # ---- estados, acciones y lo que dicen otros (parche-55) --------------
    def _subject_in(self, words):
        """Nombres de la memoria que aparecen en las palabras ("la casa" -> CASA)."""
        toks = {canon(w.upper()) for w in words if w not in DETS}
        return {f["s"] for f in self.m.facts if canon(f["s"]) in toks}

    def special(self, question):
        import re
        t = re.sub(r"\s+", " ", re.sub(r"[¡!¿?.,;:]", " ", norm(question))).strip()
        facts = [f for f in self.m.facts]
        def says(fs):
            out = []
            for f in fs:
                x = self.say((f["s"], f["p"], f["o"]), neg=bool(f.get("neg"))) + "."
                if x not in out:
                    out.append(x)
            return " ".join(out[:6])
        m = re.fullmatch(r"que (?:es|son) ((?:un|una|el|la|los|las) \w+)", t)
        if m and not getattr(self, "_in_past", False):
            # "¿Que es un triangulo?": se contesta con lo que la memoria sabe (guardado o deducido), sin depender de como la escuela lea la pregunta
            names = sorted(self._subject_in(m.group(1).split()))
            if names:
                nm = names[0]
                objs = [f["o"] for f in facts if f["s"] == nm and f["p"] == "ES" and not f.get("neg")]
                try:
                    objs += [o_ for (_, _, o_) in self.derived(nm, "ES", None)]
                except Exception:
                    pass
                objs = list(dict.fromkeys(objs))
                if objs:
                    def cls(o_):
                        d_ = self._disp(o_).lower()
                        return d_ if re.match(r"(un|una)\s", d_) else ("una " if o_.endswith("A") else "un ") + d_
                    art = m.group(1).split()[0]
                    subj = self._disp(nm).lower()
                    subj = subj if re.match(r"(un|una|el|la|los|las)\s", subj) else f"{art} {subj}"
                    return f"{subj.capitalize()} es {' y '.join(cls(o_) for o_ in objs[:3])}."
        m = re.fullmatch(r"de que color (?:es|son|era) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            colors = {f["s"] for f in facts if f["p"] == "ES" and canon(f["o"]) == "COLOR"}
            fs = [f for f in facts if f["s"] in names and f["p"] in ("SER", "ESTAR") and f["o"] in colors | {c.replace("O", "A") for c in colors}
                  or (f["s"] in names and f["p"] in ("SER", "ESTAR") and any(norm(f["o"])[:-1] == c[:-1].lower() for c in colors))]
            return says(fs) if fs else "No lo sé."
        m = re.fullmatch(r"para que (?:sirve|sirven|se usa|se usan|se utiliza|se utilizan) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and f["p"] == "SERVIR_PARA"]
            return says(fs) if fs else "No lo sé."
        m = re.fullmatch(r"que (?:sirve|sirven|se usa|se usan|se utiliza|se utilizan) para (.+)", t)
        if m:
            key = "_".join(m.group(1).split()).upper()
            fs = [f for f in facts if f["p"] == "SERVIR_PARA" and canon(f["o"]) == canon(key)]
            return says(fs) if fs else "No lo sé."
        m = re.fullmatch(r"es (\w+) (?:lo contrario|lo opuesto|el contrario|el opuesto) de (\w+)", t)
        if m:
            from src.reasoning.coherence import opposite
            if opposite(m.group(1), m.group(2), getattr(self.m, "opposites", [])):
                return f"Sí, {m.group(1)} es lo contrario de {m.group(2)}."
            return "No lo sé."
        m = re.fullmatch(r"por que (.+)", t)
        if m:
            words = m.group(1).split()
            names = self._subject_in(words)
            fs = [f for f in facts if f["s"] in names and f["p"].endswith("_PORQUE") and any(norm(w)[:3] == f["p"][:3].lower() for w in words)]
            return says(fs) if fs else "No lo sé."
        m = re.fullmatch(r"(?:a |de |con |en |para )?cuant[oa]s (.+)", t)
        if m:
            words = m.group(1).split()
            tener = [k for k, w in enumerate(words) if w in ("tiene", "tienen", "tuvo", "tenia", "tendra")]
            if tener:
                noun = words[tener[0] - 1] if tener[0] else ""
                names = self._subject_in(words[tener[0] + 1:])
                stem = lambda x: re.sub(r"(os|as|es|o|a|e|s)$", "", x.lower())
                fs = [f for f in facts if f["s"] in names and f["p"].startswith("TENER") and not f.get("neg")
                      and any(stem(part) == stem(noun) for part in norm(f["o"]).split("_"))]
                return says(fs) if fs else "No lo sé."
            for pat in (r"(?i)cuánt[oa]s(?:\s+\w+)?", r"(?i)cuánt[oa]s"):         # con o sin sustantivo ("cuantos hijos" / "cuantos")
                q2 = re.sub(pat, "qué", question, count=1)
                kind, tt = self.read(q2)
                if tt and kind in ("objeto", "sujeto"):
                    s_ = None if tt["s"] == norm(HOLE) else tt["s"]
                    o_ = None if tt["o"] == norm(HOLE) else tt["o"]
                    hits = self.lookup(s_, tt["p"], o_)
                    vals = list(dict.fromkeys(f[2] if kind == "objeto" else f[0] for f in hits))
                    if vals:
                        return f"{len(vals)}: " + ", ".join(self._disp(v) for v in vals) + "."
            return "No lo sé."
        m = re.fullmatch(r"donde \w+ (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and not f.get("neg") and any("_" + w in f["p"] for w in ("ENCIMA", "DEBAJO", "DENTRO", "FUERA", "CERCA", "LEJOS", "DELANTE", "DETRAS", "JUNTO", "ENFRENTE", "ALREDEDOR"))]
            if fs:
                return says(fs)
        m = re.fullmatch(r"que (?:hace|hizo|ha hecho|esta haciendo|hacia) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and not f.get("neg") and f["p"] not in ("ES",)]
            return says(fs) if fs else None
        m = re.fullmatch(r"como (?:es|esta|son|estan|era|estaba|fue) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and f["p"] in ("SER", "ESTAR")]
            return says(fs) if fs else None
        m = re.fullmatch(r"es|(?:es|esta|son|estan|era|estaba) (.+)", t)
        if m and m.group(1):
            words = m.group(1).split()
            names = self._subject_in(words)
            fs = [f for f in facts if f["s"] in names and f["p"] in ("SER", "ESTAR")]
            if fs:
                subj = {canon(x.upper()) for x in words if canon(x.upper()) in {canon(f["s"]) for f in fs}}
                adjs = [w for w in words if w not in DETS and canon(w.upper()) not in subj]
                stem = lambda x: re.sub(r"(os|as|es|o|a|e|s)$", "", x.lower())
                hit = [f for f in fs if any(stem(a) == stem(norm(f["o"])) for a in adjs)]
                if hit:
                    f = hit[0]
                    return ("No. " if f.get("neg") else "Sí. ") + says([f])
                if any(w in DETS for w in words[1:]):            # "¿Es un gorrión un pájaro?": no es adjetivo, que lo vea la ruta normal
                    return None
                return "Eso no me consta; solo sé " + says([f for f in fs if not f.get("neg")][:3] or fs[:3])
            return None
        m = re.fullmatch(r"quien (?:es|esta|son|estan|era|estaba) (.+)", t)
        if m:
            stem = lambda x: re.sub(r"(os|as|es|o|a|e|s)$", "", x.lower())
            words = [w for w in m.group(1).split() if w not in DETS]
            hit = [f for f in facts if f["p"] in ("SER", "ESTAR") and not f.get("neg") and any(stem(w) == stem(norm(f["o"])) for w in words)]
            if hit:
                return says(hit)
        m = re.fullmatch(r"que (?:dice|dijo|cree|creia|piensa|opina|afirma|asegura|comenta|cuenta) (.+)", t)
        if m:
            names = self._subject_in(m.group(1).split())
            fs = [f for f in facts if f["s"] in names and f["p"].endswith("_QUE")]
            return says(fs) if fs else None
        m = re.fullmatch(r"quien (?:dice|dijo|cree|piensa|opina|afirma|asegura|comenta|cuenta) que (.+)", t)
        if m:
            key = "_".join(m.group(1).split())
            fs = [f for f in facts if f["p"].endswith("_QUE") and f["o"].lower() == key]
            return says(fs) if fs else None
        return None

    def timeline(self, question):
        """Preguntas de orden: "que paso primero / ultimo / antes de X / despues de X" con fechas absolutas (parche-53)."""
        import re
        from src.language.fechas import extract_abs, resolve, before, after, parse_iv, fmt
        q = norm(question).strip(" ¿?.!")
        m = re.fullmatch(r"que (?:paso|ocurrio|sucedio|hice|hizo)\s*(primero|ultimo|al final|antes|despues)?(?:\s+(?:de|del)\s+(.+))?", q)
        if not m:
            return None
        mode, ref = m.group(1) or "", m.group(2)
        dated = []
        seen = set()
        for f in self.m.facts:
            if f.get("neg") or not f.get("when_abs"):
                continue
            key = ((f["s"], f["p"], f["o"]), f["when_abs"])
            if key not in seen:
                seen.add(key)
                dated.append((parse_iv(f["when_abs"])[0], f["when_abs"], (f["s"], f["p"], f["o"])))
        if mode in ("antes", "despues"):
            if not ref:
                return None
            _, iv, _ = extract_abs("el " + ref, self._today())
            iv = iv or resolve("_".join(w for w in ref.replace("el ", "").replace("la ", "").split()
                                          if w not in ("ultimo",)).replace("ano_", "ano_"), self._today())
            if not iv:
                return None
            pick = [d for d in dated if (before if mode == "antes" else after)(d[1], iv)]
            if not pick:
                return "No lo sé: no tengo nada con fecha " + mode + " de " + fmt(iv) + "."
        elif mode in ("primero", "ultimo", "al final"):
            if not dated:
                return "No lo sé: no tengo hechos con fecha."
            edge = min(d[0] for d in dated) if mode == "primero" else max(d[0] for d in dated)
            pick = [d for d in dated if d[0] == edge]
        else:
            return None
        pick.sort(key=lambda d: d[0])
        return " ".join(self.say(d[2]) + "." for d in pick)[:800]

    def lookup(self, s, p, o, neg=False, when=""):
        """Hechos de memoria que encajan; s u o pueden ser None (hueco). La relacion encaja si sus lemas se parecen o si
        se dijo con la misma forma verbal (rescata lemas irregulares: muerde -> muerder / mendar)."""
        out = []
        tpl = self._tpl
        surf = getattr(self.m, "surface", {})
        for fs, fp, fo in self._facts(neg):
            same = same_pred(fp, p) or bool(tpl and surf.get(fp.upper()) == tpl)
            al = lambda x: canon(getattr(self.m, "alias", {}).get(x.upper(), x.upper()))          # sinonimos ensenados
            if (s is None or fs == s.upper() or canon(fs) == canon(s) or al(fs) == al(s)) and \
                    (o is None or fo == o.upper() or canon(fo) == canon(o) or al(fo) == al(o)) and same \
                    and (not when or self._when_ok((fs, fp, fo), when)):
                out.append((fs, fp, fo))
        return out

    def derived(self, s, p, o):
        if self.deduce is None:
            return []
        try:
            got = self.deduce([(f["s"], f["p"], f["o"]) for f in self.m.facts if not f.get("neg") and not f.get("q")])
        except Exception:
            return []
        got = dict(got) if isinstance(got, dict) else {k: [] for k in got}
        from src.reasoning.lessons import verb_derive
        for k, v in verb_derive([(f["s"], f["p"], f["o"]) for f in self.m.facts if not f.get("neg") and not f.get("q")],
                                getattr(self.m, "verb_isa", {})).items():
            got.setdefault(k, v)
        self.support = dict(got)
        have = set(self._facts(False))
        return [f for f in got if f not in have and (s is None or f[0] == s.upper()) and (o is None or f[2] == o.upper())
                and same_pred(f[1], p)]

    # ---- decir ------------------------------------------------------
    def _disp(self, name):
        d = getattr(self.m, "display", {}).get(name.upper())
        return d or name.replace("_", " ").title()

    def say(self, fact, neg=False):
        s, p, o = fact
        tpl = None
        for k, v in getattr(self.m, "surface", {}).items():
            if k == p.upper() or same_pred(k, p):
                tpl = v
                break
        if tpl is None and p.upper().startswith(("MAS_", "MENOS_")) and p.upper().endswith("_QUE"):
            kind, _, rest = p.lower().partition("_")
            tpl = "{s} es " + kind + " " + rest[:-4] + " que {o}"
        if tpl is None:
            base, _, prep = p.lower().partition("_")
            fixed = {"ser": "{s} es {o}", "estar": "{s} está {o}", "estar_en": "{s} está en {o}", "tener": "{s} tiene {o}",
                     "parte_de": "{s} es parte de {o}"}      # hechos que salen de efectos o de la semilla (parche-59)
            tpl = fixed.get(p.lower()) or "{s} " + base + (" " + prep if prep else "") + " {o}"
        o_txt = self._disp(o)
        if p.upper() in ("SER", "ESTAR") and o.upper() not in getattr(self.m, "display", {}):
            o_txt = o.replace("_", " ").lower()                  # adjetivos en minuscula: "la puerta está abierta"
        text = tpl.format(s=self._disp(s), o=o_txt).replace(" de el ", " del ").replace(" a el ", " al ")
        text = text.replace(" _", "").strip()
        ws = [d for _, d in self._whens(fact) if d] if not neg else []
        if ws:
            text += " " + ws[0]
            iv, key = self._abs_of(fact)
            if iv and not key.isdigit():
                from src.language.fechas import fmt
                if fmt(iv) not in ws[0]:
                    text += " (" + fmt(iv) + ")"
        until = next((f.get("until") for f in self.m.facts if (f["s"], f["p"], f["o"]) == tuple(fact) and f.get("until")), None)
        if until and getattr(self, "_in_past", False):
            import re as _re
            lem = p.lower().partition("_")[0]
            if lem[-2:] in ("ar", "er", "ir") and len(lem) > 3:                # vive -> vivia, trabaja -> trabajaba
                pres, imp = (lem[:-2] + "a", lem[:-2] + "aba") if lem.endswith("ar") else (lem[:-2] + "e", lem[:-2] + "ía")
                text = _re.sub(r"\b" + pres + r"\b", imp, text, count=1)
            from src.language.fechas import fmt as _fmt
            text += f" (hasta el {_fmt(until + '/' + until)})"
        text = text[0].upper() + text[1:]
        return ("No es cierto que " + text[0].lower() + text[1:]) if neg else text

    def _because(self, fact):
        sup = self.support.get(fact)
        return (" (porque " + " y ".join(self.say(x) for x in sup) + ")") if sup else ""

    # ---- respuesta --------------------------------------------------
    def _wants_past(self, question: str) -> bool:
        """Pregunta en pasado ("antes", imperfecto de un verbo que conozco: vivia, trabajaba)."""
        import re
        t = norm(question)
        if re.search(r"\b(antes|antiguamente|anteriormente|antano)\b", t):
            return True
        heads = {f["p"].lower().partition("_")[0][:-2] for f in list(self.m.facts) + list(getattr(self.m, "past", [])) if len(f["p"]) > 4}
        for w in re.findall(r"\w+", t):
            if re.search(r"(aba|abas|aban|ia|ias|ian)$", w) and re.sub(r"(aba|abas|aban|ia|ias|ian)$", "", w) in heads:
                return True
        return False

    def answer(self, question: str) -> str:
        past = getattr(self.m, "past", [])
        if past and self._wants_past(question):
            saved = self.m.facts
            self.m.facts = list(past)
            self._in_past = True
            try:
                r = self._answer(question)
            finally:
                self.m.facts, self._in_past = saved, False
            if not r.startswith(("No lo sé", "Eso no me consta", "No he entendido")):
                return r
        return self._answer(question)

    def _answer(self, question: str) -> str:
        self._alts = []
        tl = self.timeline(question)
        if tl:
            return tl
        sp = self.special(question)
        if sp:
            return sp
        kind, t = self.read(question)
        if kind in ("si_no", "cuando") and len(self._alts) > 1:
            for alt in self._alts:                          # "Es Marta madre de Pablo" se puede leer mal; vale la que la memoria reconoce
                a_s, a_o = alt["s"], alt["o"]
                if self.lookup(a_s, alt["p"], a_o) or self.lookup(a_s, alt["p"], a_o, neg=True) or self.derived(a_s, alt["p"], a_o):
                    t = alt
                    break
        self._tpl = (t or {}).get("template")
        if t is None:
            return "No he entendido la pregunta. Prueba con otra forma (por ejemplo: ¿Quién escribió una novela?)."
        s = None if t["s"] == norm(HOLE) else t["s"]
        o = None if t["o"] == norm(HOLE) else t["o"]
        p = t["p"]
        when = t.get("when", "")
        if kind == "cuando":
            hits = self.lookup(s, p, o)
            if not hits:
                return "No lo sé."
            if any(d for f in hits for _, d in self._whens(f)):
                return " ".join(dict.fromkeys(self.say(f) + "." for f in hits))[:600]
            return "No lo sé: sé que " + self.say(hits[0]).rstrip(".") + ", pero no cuándo."
        if kind == "si_no" and when and self.lookup(s, p, o):
            if self.lookup(s, p, o, when=when):
                return "Sí. " + self.say(self.lookup(s, p, o, when=when)[0]) + "."
            hits = self.lookup(s, p, o)
            if any(d for f in hits for _, d in self._whens(f)):
                return "No. Según lo que sé: " + self.say(hits[0]) + "."
            return "No lo sé: sé que " + self.say(hits[0]).rstrip(".") + ", pero no cuándo."
        if kind == "si_no":
            hits = self.lookup(s, p, o, neg=False)
            if hits and all(self._q(f) for f in hits):
                return "No lo sé con certeza: solo sé que " + self.say(hits[0])[0].lower() + self.say(hits[0])[1:] + "."
            if hits:
                return "Sí. " + self.say(self.lookup(s, p, o)[0]) + "."
            if p.upper().startswith(("MAS_", "MENOS_")) and s and o:
                opp = ("MENOS_" if p.upper().startswith("MAS_") else "MAS_") + p.upper().split("_", 1)[1]
                inv = self.lookup(s, opp, o) or self.derived(s, opp, o)
                if inv:
                    return "No. " + self.say(inv[0]) + self._because(inv[0]) + "."
            if self.lookup(s, p, o, neg=True):
                return "No. " + self.say(self.lookup(s, p, o, neg=True)[0], neg=True) + "."
            d = self.derived(s, p, o)
            if d:
                return "Sí, lo deduzco: " + self.say(d[0]) + self._because(d[0]) + "."
            if self.lookup(s, p, None) or self.lookup(None, p, o):
                return "Eso no me consta; solo sé " + "; ".join(dict.fromkeys(self.say(f) for f in (self.lookup(s, p, None) or self.lookup(None, p, o))[:3])) + "."
            return "No lo sé."
        hits = self.lookup(s, p, o, when=when)
        ded = [] if (hits and s is not None and o is not None) else self.derived(s, p, o)
        if hits and ded and (s is None or o is None):          # pregunta abierta: lo dicho y tambien lo deducido (parche-59)
            more = [d for d in ded if d not in hits][:3]
            return " ".join(dict.fromkeys([self.say(f) + "." for f in hits] + [self.say(f) + "." for f in more]))[:600]
        if hits:
            return " ".join(dict.fromkeys(self.say(f) + "." for f in hits))[:600]
        if ded:
            return "Lo deduzco: " + " ".join(dict.fromkeys(self.say(f) + self._because(f) + "." for f in ded[:5]))
        return "No lo sé."
