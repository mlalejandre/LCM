"""Conversacion basica SIN LLM (parche-54, bloque A de docs/NUCLEO_BASICO.md).

Reglas explicitas y comprobables, no un modelo generativo:
  A2 actos sociales (hola, gracias, perdona, adios, ...)        A5 preguntas sobre si mismo y sobre lo que sabe/se ha dicho
  A3 pedir aclaracion cuando no entiende                        A6 ordenes (repite, olvida ...)
  A4 preguntar lo que le falta (¿que es X?) y aprenderlo        A7 si/no/vale/exclamaciones, tu/usted
  A8 referencias: mi/mis, yo, este/ese, tambien/tampoco/otra vez, "eso es falso", "¿y Ana?"

`Dialogue.act(raw, qa)` devuelve (respuesta | None, texto_para_seguir | None):
  - (texto, None): ya esta contestado; - (None, raw2): continua el flujo normal con raw2 (referencias resueltas);
  - (texto, raw2): contesta y ADEMAS sigue con raw2.
`Conversation` es el bucle completo (sin oido) que usan los tests; scripts/think.py usa solo `Dialogue`.
"""
import re
import time
from datetime import date, datetime
from typing import List, Optional, Tuple

from src.language.lexicon import norm
from src.reasoning.lessons import canon
from src.reasoning import coherence

DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DET = {"el", "la", "los", "las", "un", "una", "unos", "unas"}
CAP = r"[A-ZÁÉÍÓÚÑ][\wáéíóúñ]*"
GREET = {"hola": "¡Hola", "ola": "¡Hola", "hey": "¡Hola", "saludos": "¡Saludos", "buenas": "¡Buenas", "buenos dias": "¡Buenos días",
         "buenas tardes": "¡Buenas tardes", "buenas noches": "¡Buenas noches"}
BYE = r"(adios|hasta luego|hasta pronto|hasta manana|hasta otra|chao|chau|nos vemos|me voy|hasta la vista)"
THANKS = r"((muchas|mil|muchisimas) )?gracias( por (todo|tu ayuda|su ayuda|eso|la ayuda))?|te lo agradezco|muy amable|se lo agradezco"
SORRY = r"(perdona|perdon|disculpa|disculpame|perdoname|lo siento|disculpe)( por (eso|todo|la molestia))?"
YES = r"(si|sip|claro|por supuesto|seguro|correcto|exacto|afirmativo|desde luego|adelante|si seguro|si claro)"
NO = r"(no|nop|nunca|negativo|mejor no|no gracias)"
ACK = r"(vale|ok|okay|de acuerdo|entendido|muy bien|bien|perfecto|genial|estupendo|bueno|fenomenal|comprendo|ya veo|ah|aja)"
GOOD = {"que bien": "¡Me alegro!", "que alegria": "¡Me alegro!", "que bueno": "¡Me alegro!", "genial": "¡Me alegro!",
        "que pena": "Lo siento.", "que lastima": "Lo siento.", "vaya": "Lo siento.", "ay": "Lo siento.", "que mal": "Lo siento.",
        "guau": "¿Verdad?", "uau": "¿Verdad?", "madre mia": "¿Verdad?", "increible": "¿Verdad?", "jo": "Vaya.", "ostras": "Vaya."}
GEN = {"este": "el", "ese": "el", "aquel": "el", "esta": "la", "esa": "la", "aquella": "la", "estos": "los", "esos": "los", "aquellos": "los",
       "estas": "las", "esas": "las", "aquellas": "las"}


TIEMPO_NOMBRES = {"lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                  "agosto", "septiembre", "octubre", "noviembre", "diciembre", "primavera", "verano", "otono", "invierno"}


def n(raw: str) -> str:
    """Texto comparable: sin tildes, sin signos, sin 'por favor'."""
    t = norm(raw)
    t = re.sub(r"[¡!¿?.,;:\"«»()]", " ", t)
    t = re.sub(r"\b(por favor|porfa)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _same_fact(f: dict, triple, neg: bool) -> bool:
    return (f["s"], f["p"], f["o"]) == tuple(x.upper() for x in triple) and bool(f.get("neg")) == bool(neg)


def is_question(raw: str) -> bool:
    return "?" in raw or "¿" in raw


FEM_E = {"madre", "mujer", "tarde", "noche", "clase", "calle", "suegra", "nuera"}
FEM_O = {"mano", "foto", "moto", "radio"}


def _article(noun: str) -> str:
    w = noun.lower()
    if w in FEM_E or w in FEM_O:
        return "la"
    if w.endswith("os") or w.endswith("es"):
        return "los"
    if w.endswith("as"):
        return "las"
    return "la" if w.endswith("a") and w not in ("dia", "mapa", "problema", "idioma") else "el"


class Dialogue:
    def __init__(self, memory, today=None):
        self.m = memory
        self.start = time.time()
        self.user: Optional[str] = None
        self.formal = False
        self.pending = None                 # ("define", frase) | ("confirm", [triples], texto) | ("name", frase_original)
        self.last = ""                      # ultima respuesta (para "repite")
        self.last_question = ""
        self.last_facts: List[tuple] = []   # triples guardados con la ultima frase
        self.dry = False                    # True: contesta pero no borra nada (lo usa talks)

    # ---- utilidades -------------------------------------------------------
    def _forget_pol(self, triple, neg: bool) -> None:
        if not self.dry:
            self.m.facts = [f for f in self.m.facts if not _same_fact(f, triple, neg)]

    def _forget(self, triple) -> bool:
        return True if self.dry else self.m.forget_fact(triple)

    def _today(self) -> date:
        return getattr(self.m, "today", None) or date.today()

    def _facts(self, neg=False, every=False):
        return [f for f in self.m.facts if bool(f.get("neg")) == neg and (every or f.get("source") not in ("efecto", "semilla"))]

    def _names(self, every=False):
        out = set()
        for f in self._facts(every=every):
            out.update((f["s"], f["o"]))
        return out

    def _disp(self, name: str) -> str:
        d = getattr(self.m, "display", {}).get(name.upper())
        return d or name.replace("_", " ").title()

    def _find(self, phrase: str) -> Optional[str]:
        """Nombre de la memoria que corresponde a una frase ("el perro" -> PERRO) o None."""
        words = [w for w in n(phrase).split() if w not in DET]
        if not words:
            return None
        key = canon("_".join(words).upper())
        for name in self._names(every=True):
            if canon(name) == key:
                return name
        return None

    def _about(self, name: str):
        return [f for f in self._facts(every=True) if canon(f["s"]) == canon(name) or canon(f["o"]) == canon(name)]

    def _hello(self, who: str, tail: str = "") -> str:
        return who + (f", {self.user}" if self.user else "") + "!" + tail

    def _help(self) -> str:
        return "¿En qué puedo ayudarle?" if self.formal else "¿En qué puedo ayudarte?"

    def _said(self, qa, facts) -> str:
        seen = []
        for f in facts:
            if qa is None:
                seen.append(" ".join((f["s"], f["p"], f["o"])).lower() + ".")
                continue
            s = qa.say((f["s"], f["p"], f["o"]), neg=bool(f.get("neg"))) + "."
            if s not in seen:
                seen.append(s)
        return " ".join(seen[:8])

    def talks(self, raw: str) -> bool:
        """Frase corta (1-2 palabras) que es conversacion: hola, gracias, vale, ¿y Ana?, repite..."""
        if self.pending:
            return True
        probe = Dialogue(self.m)
        probe.dry = True
        probe.user, probe.last_question, probe.last_facts = self.user, self.last_question, list(self.last_facts)
        probe.last = self.last
        reply, cont = probe.act(raw, None)
        return bool(reply) or (cont is not None and cont != raw)

    # ---- coherencia (bloque D) -------------------------------------------
    def note_new(self, triple, neg: bool, raw: str = "", when: str = "", say=None) -> str:
        """Tras guardar un hecho: si cambia un estado, el viejo pasa a pasado; si contradice, pregunta. Devuelve el aviso (o "")."""
        low = norm(raw)
        kind, old = coherence.classify([f for f in self.m.facts if not _same_fact(f, triple, neg)], triple, neg, bool(when),
                                       bool(re.search(r"\bya no\b", low)), getattr(self.m, "opposites", []))
        if not kind:
            return ""
        fmt = say or (lambda t, n=False: " ".join(t).lower())
        old_t = (old["s"], old["p"], old["o"])
        until = self._today().isoformat()
        if kind in ("supersede", "supersede_neg"):
            if kind == "supersede_neg":                      # el "ya no" no se guarda como hecho negado
                self.m.facts = [f for f in self.m.facts if not _same_fact(f, triple, True)]
            coherence.to_past(self.m, old, until)
            return f"Vale: antes decías que {fmt(old_t)}; ahora lo tomo como pasado."
        self.pending = ("conflict", old_t, tuple(x.upper() for x in triple), neg, bool(old.get("neg")))
        return (f"Ojo: antes me dijeron «{fmt(old_t, bool(old.get('neg')))}» y ahora «{fmt(tuple(x.upper() for x in triple), neg)}». "
                "¿Cuál es correcta: la nueva, la anterior o las dos?")

    def explain(self, qa, statement: Optional[str] = None) -> str:
        """"¿Como lo sabes?": de donde sale un hecho (me lo dijiste / lo deduje / lo dijo otro)."""
        s = p = o = None
        if statement:
            found = qa.parse(statement.strip(" ?¿.") + ".") or []
            if not found:
                return "No he entendido qué quieres que justifique."
            s, p, o = found[0]["s"], found[0]["p"], found[0]["o"]
        elif self.last_question:
            kind, t = qa.read(self.last_question)
            if not t and self.last:
                found = qa.parse(self.last.strip()) or []            # preguntas especiales: se justifica lo que dije
                if found:
                    t = {"s": found[0]["s"], "p": found[0]["p"], "o": found[0]["o"]}
            if not t:
                return "No sé a qué te refieres."
            s = None if t["s"] == "xqx" else t["s"]
            o = None if t["o"] == "xqx" else t["o"]
            p = t["p"]
        else:
            return "¿El qué? Pregúntame algo primero."
        hits = qa.lookup(s, p, o)
        if hits:
            f = next(x for x in self.m.facts if (x["s"], x["p"], x["o"]) == hits[0] and not x.get("neg"))
            when = datetime.fromtimestamp(f.get("t", time.time())).strftime("%d/%m/%Y")
            src = f.get("source", "usuario")
            if src == "semilla":
                return "Es parte de mi conocimiento de fábrica."
            if src == "efecto":
                return "Lo deduje de lo que pasó en la frase (quien da algo ya no lo tiene, quien lo recibe sí)."
            if f["p"].endswith("_QUE"):
                return f"Lo dijo {qa._disp(f['s'])}; yo no lo sé por mí mismo."
            return f"Me lo dijiste tú el {when}" + (f": «{src.strip().rstrip('.')}»." if src and src != "usuario" else ".")
        d = qa.derived(s, p, o)
        if d:
            return "Lo deduje: " + qa.say(d[0]) + qa._because(d[0]) + "."
        return "No lo sé, no tengo ese dato."

    # ---- entrada principal -----------------------------------------------
    def act(self, raw: str, qa=None) -> Tuple[Optional[str], Optional[str]]:
        t = n(raw)
        if not t:
            return None, None
        # 1) respuestas a algo que yo pregunte
        if self.pending:
            kind = self.pending[0]
            if kind == "confirm":
                if re.fullmatch(YES, t):
                    triples, _ = self.pending[1], self.pending[2]
                    gone = sum(self._forget(tr) for tr in triples)
                    self.pending = None
                    return f"Olvidado ({gone} hechos).", None
                if re.fullmatch(NO, t):
                    self.pending = None
                    return "Vale, no olvido nada.", None
                self.pending = None
            elif kind == "conflict":
                _, old_t, new_t, new_neg, old_neg = self.pending
                if re.fullmatch(r"(la )?(nueva|ultima|actual|ahora|esa|segunda|reciente)( es la correcta| vale)?", t):
                    self._forget_pol(old_t, old_neg)
                    self.pending = None
                    return "Vale, me quedo con la nueva.", None
                if re.fullmatch(r"(la )?(anterior|vieja|antigua|primera|antes|de antes)( es la correcta| vale)?", t):
                    self._forget_pol(new_t, new_neg)
                    self.pending = None
                    return "Vale, me quedo con la anterior.", None
                if re.fullmatch(r"(las dos|ambas|las dos valen|las dos son correctas|todas)", t):
                    self.pending = None
                    return "Vale, guardo las dos.", None
                self.pending = None
            elif kind == "define":
                phrase = self.pending[1]
                m = re.fullmatch(r"(?:es|son|era)\s+(.+)", raw.strip(" .!¡"), flags=re.I)
                bare = re.fullmatch(r"((?:un|una|el|la|unos|unas)\s+[\wáéíóúñ ]{2,40})", raw.strip(" .!¡"), flags=re.I)
                if m or bare:
                    rest = m.group(1) if m else bare.group(1)
                    self.pending = None
                    head = phrase[0].upper() + phrase[1:]
                    return None, f"{head} es {rest}."
                if re.fullmatch(r"(no lo se|no se|ni idea|nada|da igual|olvidalo)", t):
                    self.pending = None
                    return "Vale, otra vez será.", None
                self.pending = None
            elif kind == "name":
                stored = self.pending[1]
                m = re.fullmatch(r"(?:(?i:me llamo |soy |mi nombre es ))?(" + CAP + ")", raw.strip(" .!¡"))
                if m:
                    self.user = m.group(1)
                    self.pending = None
                    return f"Encantado, {self.user}.", (self.resolve(stored) if stored else None)
                self.pending = None
        # 2) actos sociales
        r = self._social(raw, t)
        if r:
            return r, None
        r = self._definitions(raw, t, qa)
        if r:
            return r
        r = self._self_and_memory(raw, t, qa)
        if r:
            return r, None
        r = self._orders(raw, t, qa)
        if r:
            return r, None
        # 3) referencias: se reescribe y se sigue
        new = self.resolve(raw)
        if isinstance(new, tuple):                      # (pregunta, None) -> hay que preguntar algo antes
            return new[0], None
        return None, new


    # ---- E: aprender conceptos por definicion (parche-58) ---------------------
    ART = r"(?:(?:un|una|el|la|los|las|unos|unas)\s+)?"

    def _bare(self, x: str) -> str:
        return re.sub(r"^(un|una|el|la|los|las|unos|unas)\s+", "", n(x)).strip()

    def _definitions(self, raw: str, t: str, qa):
        m_ = self.m
        a = self.ART
        # sinonimos
        m = re.fullmatch(r"(.+?) (?:es|son) (?:lo mismo que|sinonimo de|sinonima de|igual que|equivalente a|otro nombre de|otra palabra para)\s+(.+)|(.+?) significa (?:lo mismo que )?(.+)", t)
        if m:
            x, y = self._bare(m.group(1) or m.group(3)), self._bare(m.group(2) or m.group(4))
            if x and y and " " not in x and " " not in y:
                known = lambda w: any(w.upper() in (f["s"], f["o"]) or w.upper() == qa.canon_name(f["s"]) if False else w.upper() in (norm(f["s"]).upper(), norm(f["o"]).upper()) for f in m_.facts)
                base, other = (x, y) if known(x) or not known(y) else (y, x)
                m_.alias[other.upper()] = base.upper()
                m_.alias[norm(other).upper()] = norm(base).upper()
                return f"Vale: {other} y {base} son lo mismo.", None
        # contrarios
        m = re.fullmatch(r"(\w+) (?:es|son) (?:lo contrario|lo opuesto|el contrario|el opuesto|antonimo) de (\w+)", t)
        if m and m.group(1) not in ("cual", "que") and "?" not in raw:
            m_.opposites.append([m.group(1), m.group(2)])
            return f"Vale: {m.group(1)} es lo contrario de {m.group(2)}.", None
        # verbo = otro verbo (+ resto)
        m = re.fullmatch(r"(\w+(?:ar|er|ir)) es ((\w+(?:ar|er|ir))(?: .+)?)", t)
        if m and "?" not in raw:
            m_.verb_isa[m.group(1)] = m.group(3 if False else 2).split()[0]
            m_.defs[m.group(1)] = m.group(2)
            return f"Vale: {m.group(1)} es {m.group(2)}.", None
        # para que sirve
        use = r"(?:sirve|sirven|se usa|se usan|se utiliza|se utilizan)"
        m = re.fullmatch(r"(.+?) es (?:un|una) (\w+(?: \w+)?) (?:que|con el que|con la que) " + use + r" para (.+)", t)
        if m and "?" not in raw:
            x, g, v = self._bare(m.group(1)), m.group(2), "_".join(m.group(3).split()).upper()
            m_.add_fact((x.replace(" ", "_"), "SERVIR_PARA", v), source=raw.strip())
            m_.defs[x] = f"{self._art(g)} {g} que sirve para {m.group(3)}"
            return None, f"{self._art(x).capitalize()} es {self._art(g)} {g}."
        m = re.fullmatch(r"(.+?) " + use + r" para (.+)", t)
        if m and "?" not in raw:
            x, v = self._bare(m.group(1)), "_".join(m.group(2).split()).upper()
            m_.add_fact((x.replace(" ", "_"), "SERVIR_PARA", v), source=raw.strip())
            return f"Entendido: {self._art(x)} sirve para {m.group(2)}.", None
        m = re.fullmatch(r"para que " + use + r" (.+)", t)
        if m:
            x = self._bare(m.group(1)).replace(" ", "_").upper()
            fs = [f for f in m_.facts if f["p"] == "SERVIR_PARA" and f["s"] == x]
            if fs:
                return f"{self._art(m.group(1)).capitalize()} sirve para {fs[0]['o'].replace('_', ' ').lower()}.", None
            return None
        m = re.fullmatch(r"que " + use + r" para (.+)", t)
        if m:
            key = "_".join(m.group(1).split()).upper()
            fs = [f for f in m_.facts if f["p"] == "SERVIR_PARA" and (f["o"] == key or f["o"].startswith(key + "_"))]
            if fs:
                return f"{self._art(fs[0]['s'].replace('_', ' ').lower()).capitalize()} sirve para {m.group(1)}.", None
            return None
        r = self._meaning(raw, t)
        if r:
            return r
        # que es X
        m = re.fullmatch(r"(?:que|quien) (?:es|son|significa) (.+)", t)
        if m and self._bare(m.group(1)) in TIEMPO_NOMBRES:               # "¿Qué es el lunes?": la escuela lo lee como tiempo, no como cosa
            x = self._bare(m.group(1)).upper()
            fs = [f for f in self.m.facts if norm(f["s"]).upper() == x and f["p"] == "ES"]
            if fs:
                acc = {"dia": "día", "estacion": "estación", "miercoles": "miércoles", "sabado": "sábado", "otono": "otoño"}
                fx = lambda w: " ".join(acc.get(x, x) for x in w.split())
                return f"{fx(m.group(1).strip()).capitalize()} es {fx(fs[0]['o'].lower().replace('_', ' '))}.", None
        if m:
            x = self._bare(m.group(1))
            if x in m_.defs:
                d = m_.defs[x]
                return (f"{x.capitalize()} es {d}." if " " not in m.group(1).strip() else f"{self._art(x).capitalize()} es {d}."), None
            # "¿Que es un perro?" con hechos ES guardados: se contesta directamente, sin depender de como la escuela lea la pregunta
            if t.startswith("que ") and re.match(r"(un|una|el|la|los|las)\s", t.split(" ", 2)[2] if len(t.split(" ", 2)) > 2 else ""):
                name = self._find(m.group(1))
                if name:
                    objs = []
                    for f in self._facts(every=True):
                        if canon(f["s"]) == canon(name) and f["p"] == "ES" and f["o"] not in objs:
                            objs.append(f["o"])
                    if objs:
                        def _cls(o):
                            d = self._disp(o).lower()
                            return d if re.match(r"(un|una)\s", d) else ("una " if o.endswith("A") else "un ") + d
                        cls = [_cls(o) for o in objs[:3]]
                        return f"{self._art(self._disp(name).lower()).capitalize()} es {' y '.join(cls)}.", None
        return None

    @staticmethod
    def _art(x: str) -> str:
        x = x.strip()
        if re.match(r"(un|una|el|la|los|las)\s", x):
            return x
        return ("la " if x.endswith("a") else "el ") + x


    # ---- C: efectos de las acciones (parche-59) ----------------------------------
    def apply_effects(self, parsed) -> List[str]:
        """parsed = [(s, p, o, o_disp)] de UNA frase afirmativa. Aplica lo que cambia: quien tiene que, estados, lugares."""
        from src.reasoning.efectos import effects
        from src.reasoning import coherence
        notes = []
        today = self._today().isoformat()
        for kind, tr in effects(parsed):
            tr = tuple(x.upper() for x in tr)
            if kind == "lose":
                for f in list(self.m.facts):
                    if f["s"] == tr[0] and f["p"] == tr[1] and canon(f["o"]) == canon(tr[2]) and not f.get("neg"):
                        coherence.to_past(self.m, f, today)
                continue
            if any((f["s"], f["p"], f["o"]) == tr and not f.get("neg") for f in self.m.facts):
                continue
            k, old = coherence.classify([f for f in self.m.facts], tr, False, False, False, getattr(self.m, "opposites", []))
            if k in ("supersede", "antonym") and old:
                coherence.to_past(self.m, old, today)
            self.m.add_fact(tr, source="efecto")
        return notes

    def _meaning(self, raw: str, t: str):
        """"¿Cual es lo contrario de X?" / "¿Que significa X?" """
        from src.reasoning.coherence import ANTONYMS, stem
        m = re.fullmatch(r"(?:cual|que) es (?:lo contrario|lo opuesto|el contrario|el opuesto|el antonimo) de (.+)", t)
        if m:
            w = self._bare(m.group(1))
            disp = (re.search(r"(?:contrario|opuesto|antonimo|antónimo) de (?:el |la |lo )?([\wáéíóúñ]+)", raw, flags=re.I) or [None, w])[1]
            fix = lambda x: {"pequeno": "pequeño", "dificil": "difícil", "facil": "fácil", "rapido": "rápido", "debil": "débil", "ancho": "ancho",
                             "dia": "día", "mas": "más"}.get(x, x)
            pairs = [tuple(x) for x in ANTONYMS] + [tuple(x) for x in getattr(self.m, "opposites", [])]
            for a, b in pairs:
                if stem(norm(a)) == stem(w):
                    return f"Lo contrario de {disp} es {fix(b)}.", None
                if stem(norm(b)) == stem(w):
                    return f"Lo contrario de {disp} es {fix(a)}.", None
            return None
        m = re.fullmatch(r"que (?:significa|quiere decir) (.+)", t)
        if m:
            w = self._bare(m.group(1)).upper()
            al = self.m.alias
            other = [k for k, v in al.items() if v == w] + ([al[w]] if w in al else [])
            if other:
                return f"{m.group(1).capitalize()} significa lo mismo que {other[0].lower()}.", None
            d = self.m.defs.get(self._bare(m.group(1)))
            if d:
                return f"{m.group(1).capitalize()} es {d}.", None
        return None

    # ---- A2 / A7 ------------------------------------------------------------
    def _social(self, raw: str, t: str) -> Optional[str]:
        if re.search(r"\b(usted|ustedes)\b|\bcomo esta\b", t) and not re.search(r"\bcomo esta (el|la|mi|tu)\b", t):
            self.formal = True
        if re.search(r"\b(tuteame|tutearme|tutea|tutead)\b|puedes tutear", t):
            self.formal = False
            return "De acuerdo, te hablaré de tú."
        m = re.search(r"\b(?:[Mm]e llamo|[Mm]i nombre es|[Ss]oy|[Ll]lámame|[Pp]uedes llamarme)\s+(" + CAP + r")\s*[.!]?\s*$", raw)
        if m:
            self.user = m.group(1)
            return f"Encantado, {self.user}."
        if re.fullmatch(r"como me llamo|sabes como me llamo|cual es mi nombre|quien soy|sabes quien soy", t):
            if self.user:
                return f"Te llamas {self.user}."
            self.pending = ("name", "")
            return "Todavía no me lo has dicho. ¿Cómo te llamas?"
        m = re.fullmatch(r"(buenos dias|buenas tardes|buenas noches|hola|ola|hey|saludos|buenas)(?: a todos)?(?: (que tal|como estas|como esta|como va todo))?(?: \w+)?", t)
        if m and len(t.split()) <= 4:
            key = m.group(1)
            text = self._hello(GREET[key], "")
            if m.group(2):
                text += " Estoy bien, gracias."
            return text + " " + self._help()
        if re.fullmatch(r"(como estas|que tal|que tal estas|como te va|como va todo|como esta usted|que tal esta usted|que tal todo|como te encuentras)( hoy)?", t):
            return "Estoy bien, gracias. ¿Y usted?" if self.formal else "Estoy bien, gracias. ¿Y tú?"
        if re.fullmatch(BYE + r"( \w+)?", t):
            return "¡Hasta luego" + (f", {self.user}" if self.user else "") + "! Aquí estaré cuando quieras."
        if re.fullmatch(THANKS, t):
            return "De nada, a su disposición." if self.formal else "De nada."
        if re.fullmatch(SORRY, t):
            return "No pasa nada."
        if t in GOOD:
            return GOOD[t]
        if re.fullmatch(YES, t):
            return "Entendido."
        if re.fullmatch(NO, t):
            return "Vale."
        if re.fullmatch(ACK, t):
            return "Me alegro." if t in ("perfecto", "genial", "estupendo", "fenomenal") else "Vale."
        return None

    # ---- A5 -----------------------------------------------------------------
    def _self_and_memory(self, raw: str, t: str, qa) -> Optional[str]:
        if re.fullmatch(r"(quien eres|que eres|como te llamas|cual es tu nombre|presentate|quien eres tu|que eres tu)", t):
            return "Soy el LCM (Large Conceptual Model): aprendo español y razono con lo que me cuentas, sin ningún LLM."
        if re.fullmatch(r"(que sabes hacer|que puedes hacer|en que me puedes ayudar|para que sirves|que haces|que sabes hacer tu|ayudame)", t):
            return ("Puedo aprender los hechos y reglas que me cuentes, contestar preguntas (quién, qué, dónde, cuándo, sí o no), "
                    "deducir con lo aprendido y recordar fechas. Prueba: «Pedro compró pan ayer» y luego «¿Cuándo compró Pedro pan?».")
        if re.fullmatch(r"(que dia es hoy|que fecha es hoy|en que fecha estamos|a que dia estamos|que dia es|que fecha es|a cuantos estamos)", t):
            d = self._today()
            return f"Hoy es {DAYS[d.weekday()]}, {d.day} de {['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'][d.month-1]} de {d.year}."
        if re.fullmatch(r"(que hora es|me dices la hora|tienes hora)", t):
            return "Son las " + datetime.now().strftime("%H:%M") + "."
        if qa is not None and re.fullmatch(r"(como lo sabes|como sabes eso|por que lo sabes|de donde lo sacas|de donde sale eso|estas seguro|como lo sabes tu)", t):
            return self.explain(qa)
        m = re.fullmatch(r"(?:como|de donde) (?:sabes|sacas) que (.+)", t)
        if m and qa is not None:
            return self.explain(qa, re.sub(r"^[¿\s]*(?:[Cc]ómo|[Dd]e dónde)\s+(?:sabes|sacas)\s+que\s+", "", raw).strip(" ?¿"))
        facts = self._facts()
        if re.fullmatch(r"(que sabes|que sabes tu|cuanto sabes|que conoces|que has aprendido)", t):
            if not facts:
                return "Todavía no sé nada. Cuéntame algo."
            return f"Sé {len(facts)} hechos sobre {len(self._names())} cosas. Por ejemplo: " + self._said(qa, facts[:3])
        if re.fullmatch(r"(cuantas cosas sabes|cuantos hechos sabes|cuantos hechos tienes|cuantas cosas conoces|cuantas cosas sabes tu)", t):
            return f"Sé {len(facts)} hechos sobre {len(self._names())} cosas."
        if re.fullmatch(r"(que te he dicho( hoy)?|que te dije|que hemos hablado|de que hemos hablado|que te he contado|que recuerdas|que te he dicho hasta ahora)", t):
            mine = [f for f in facts if f.get("t", 0) >= self.start]
            if not mine:
                return "Todavía no me has contado nada."
            return "En esta conversación me has dicho: " + self._said(qa, mine)
        m = re.fullmatch(r"(?:dime |cuentame |hablame |dime algo )?(?:lo que sabes |que sabes |todo lo que sabes |algo )?(?:de|sobre|acerca de)\s+(.+)", t)
        if m and (re.match(r"(que sabes|dime|cuentame|hablame)", t)):
            who = m.group(1)
            name = self._find(who)
            about = self._about(name) if name else []
            if not about:
                phrase = re.sub(r"^(el|la|los|las|un|una)\s+", "", who)
                self.pending = ("define", phrase)
                return f"No sé nada de {phrase}. ¿Me lo explicas?"
            return self._said(qa, about)
        m = re.fullmatch(r"(que|quien) (es|son|era) ((?:el |la |los |las |un |una )?\w+)", t)
        if m and not self._find(m.group(3)):
            phrase = m.group(3)
            self.pending = ("define", phrase)
            return f"No sé {'quién' if m.group(1) == 'quien' else 'qué'} {'son' if m.group(2) == 'son' else 'es'} {phrase}. ¿Me lo explicas?"
        return None

    # ---- A6 + A8 (eso es falso) --------------------------------------------------
    def _orders(self, raw: str, t: str, qa) -> Optional[str]:
        if re.fullmatch(r"(repite|repitelo|repite lo anterior|repite lo que has dicho|que has dicho|que dijiste|como dices|que dices|otra vez|de nuevo|puedes repetir|puedes repetirlo|no te he entendido|repitemelo)", t):
            return self.last or "Todavía no he dicho nada."
        if re.fullmatch(r"(olvida|olvidate de|borra) (todo|todo lo que sabes|todo lo anterior)|olvidalo todo|borra la memoria", t):
            facts = [(f["s"], f["p"], f["o"]) for f in self.m.facts if f.get("source") not in ("semilla", "efecto")]
            if not facts:
                return "Ya no sé nada, no hay nada que olvidar."
            self.pending = ("confirm", facts, "todo")
            return f"Voy a olvidar los {len(facts)} hechos que sé. ¿Seguro?"
        if re.fullmatch(r"(olvida|olvidate de|borra) (eso|lo anterior|lo que acabo de decir|lo ultimo|lo que te he dicho)|olvidalo", t):
            return self._forget_last(qa)
        if re.fullmatch(r"(eso |lo que he dicho |lo anterior )?(es |era )?(falso|mentira|incorrecto|un error|erroneo)|(eso )?no es (cierto|verdad|asi)|te equivocas|estas equivocad[oa]|estoy equivocad[oa]|me equivoque|me he equivocado|no eso no|eso no es asi", t):
            if not self.last_facts:
                return "¿A qué te refieres? No tengo nada reciente que corregir."
            return self._forget_last(qa, "Vale, lo olvido: ")
        if re.fullmatch(r"(eso )?(es )?(cierto|correcto|exacto|verdad)|eso es|asi es|tienes razon|eso es verdad", t):
            return "Bien, lo tengo anotado." if self.last_facts else "Vale."
        m = re.match(r"\s*(?:olvida|borra|olvidate de)\s+(?:lo de |que |a |al |de |el |la )?(.+?)\s*[.!]?\s*$", raw, flags=re.I)
        if m and re.match(r"\s*(olvida|borra|olvidate)", raw, flags=re.I):
            body = m.group(1)
            parse = getattr(qa, "parse", None)
            if len(body.split()) >= 3 and parse:
                found = parse(body[0].upper() + body[1:] + ".") or []
                trips = [(x["s"], x["p"], x["o"]) for x in found]
                gone = [tr for tr in trips if any((f["s"], f["p"], f["o"]) == tuple(y.upper() for y in tr) for f in self.m.facts)]
                if gone:
                    for tr in gone:
                        self._forget(tr)
                    return "Hecho, lo he olvidado: " + body[0].upper() + body[1:] + "."
            name = self._find(body)
            about = self._about(name) if name else []
            if not about:
                return f"No sé nada de {body}, no hay nada que olvidar."
            trips = list({(f["s"], f["p"], f["o"]) for f in about})
            if len(trips) == 1:
                self._forget(trips[0])
                return "Hecho, lo he olvidado: " + self._said(qa, about)
            self.pending = ("confirm", trips, body)
            return f"Voy a olvidar {len(trips)} hechos sobre {body}. ¿Seguro?"
        return None

    def _forget_last(self, qa, prefix="Hecho, lo he olvidado: ") -> str:
        if not self.last_facts:
            return "¿A qué te refieres? No tengo nada reciente que olvidar."
        texts = [qa.say(tr) + "." for tr in self.last_facts] if qa else [" ".join(tr) for tr in self.last_facts]
        for tr in self.last_facts:
            self._forget(tr)
        self.last_facts = []
        return prefix + " ".join(texts)

    # ---- A8: referencias -----------------------------------------------------
    def resolve(self, raw: str):
        """Reescribe mi/mis/yo, este/ese..., tambien/tampoco/otra vez y "¿Y Ana?". Devuelve texto o (pregunta, None)."""
        text = raw
        m = re.fullmatch(r"\s*¿?\s*[Yy]\s+((?:a|de|con|en|para)\s+)?((?:el|la|los|las)\s+)?(" + CAP + r")\s*\?*\s*", raw)
        if m and self.last_question:
            caps = [w for w in re.findall(CAP, self.last_question)]
            caps = caps[1:] if caps and self.last_question.lstrip("¿ ").startswith(caps[0]) else caps
            if caps:
                return self.last_question.replace(caps[0], m.group(3), 1)
            return ("¿A qué te refieres? Dime la pregunta completa.", None)
        if re.search(r"\b[Mm]is?\s+\w+", text) or re.search(r"\b[Yy]o\b", text):
            if not self.user:
                self.pending = ("name", raw)
                return ("¿Cómo te llamas? Así sabré a quién te refieres con «mi» o «yo».", None)
            def sub(mo):
                noun = mo.group(1)
                out = f"{_article(noun)} {noun} de {self.user}"
                return out[0].upper() + out[1:] if mo.start() == 0 else out
            text = re.sub(r"\b[Mm]is?\s+(\w+)", sub, text)
            text = re.sub(r"\b[Yy]o\b", self.user, text)
        text = re.sub(r"\b(este|esta|estos|estas|ese|esa|esos|esas|aquel|aquella|aquellos|aquellas)\b(?!\s+(?:es|son|era|eran)\b)(?=\s+\w)",
                      self._dem, text, flags=re.I)
        text = re.sub(r"(\w+)\s+tampoco\s+(\w+)", r"\1 no \2", text)
        text = re.sub(r"\s+(también|tambien|otra vez|de nuevo|nuevamente)\b", "", text)
        return text

    @staticmethod
    def _dem(mo) -> str:
        word = mo.group(1)
        art = GEN.get(norm(word))
        if not art:
            return mo.group(0)
        return art.capitalize() if word[0].isupper() else art

    # ---- A3 / A4 -------------------------------------------------------------
    def mention(self, raw: str) -> Optional[str]:
        known = {norm(self._disp(x)).replace(" ", "_"): x for x in self._names()}
        for w in re.findall(r"\w+", norm(raw)):
            for k, x in known.items():
                if canon(w.upper()) == canon(k.upper()):
                    return self._disp(x)
        return None

    def clarify_statement(self, raw: str) -> str:
        who = self.mention(raw)
        if who:
            return (f"Creo que hablas de {who}, pero no he entendido qué quieres decirme. "
                    f"¿Puedes usar una frase más simple, por ejemplo «{who} compra pan»?")
        return f"No he entendido «{raw.strip()}». ¿Puedes decirlo con una frase más simple, por ejemplo «Ana ama a Luis»?"

    def clarify_question(self, raw: str) -> str:
        who = self.mention(raw)
        if who:
            return f"No he entendido la pregunta. Creo que preguntas por {who}: puedes probar «¿Qué sabes de {who}?»."
        return "No he entendido la pregunta. Prueba con otra forma (por ejemplo: ¿Quién compró pan?)."

    def after_answer(self, question: str, answer: str, qa) -> str:
        """Si no sabe y hay un nombre que no conoce, lo pregunta (y lo aprende con la respuesta)."""
        self.last_question = question
        if answer.startswith("No he entendido"):
            answer = self.clarify_question(question)
        elif answer.startswith("No lo sé"):
            try:
                _, t = qa.read(question)
            except Exception:
                t = None
            if t:
                for key in ("s", "o"):
                    w = t.get(key)
                    if w and w != "_" and not w.startswith("xqx") and w not in ("zurita", "bertoldo") and not self._find(w):
                        disp = (t.get(key + "_disp") or w).strip()
                        disp = re.sub(r"^(el|la|los|las|un|una)\s+", "", disp, flags=re.I)
                        self.pending = ("define", disp)
                        answer += f" No conozco «{disp}»: ¿me lo explicas?"
                        break
        self.last = answer
        return answer


class Conversation:
    """Bucle completo para tests: dialogo + QA + guardar frases (sin oido de plantillas)."""

    def __init__(self, memory, parser, qa_factory):
        from src.language.discourse import split_sentences, next_topic
        self._split, self._next = split_sentences, next_topic
        self.m, self.parser = memory, parser
        self.qa = qa_factory(memory, parser)
        self.d = Dialogue(memory)
        self.topic = None

    def say(self, raw: str) -> str:
        reply, cont = self.d.act(raw, self.qa)
        out = []
        if reply:
            out.append(reply)
        if cont:
            out.append(self._process(cont))
        text = " ".join(x for x in out if x)
        self.d.last = text or self.d.last
        return text

    def _process(self, raw: str) -> str:
        if is_question(raw):
            return self.d.after_answer(raw, self.qa.answer(raw), self.qa)
        res = []
        stored = []
        for part in self._split(raw):
            found = self.parser.parse(part, self.topic) or []
            if not found:
                res.append(self.d.clarify_statement(part))
                continue
            if not any(t["neg"] for t in found):
                self.d.apply_effects([(t["s"], t["p"], t["o"], t.get("o_disp", "")) for t in found])
            for t in found:
                tr = (t["s"], t["p"], t["o"])
                self.m.add_fact(tr, source=part, neg=t["neg"], when=t.get("when", ""), when_disp=t.get("when_disp", ""), quant=t.get("q", ""))
                self.m.note_surface(tr, t.get("template"), t.get("s_disp"), t.get("o_disp"))
                stored.append(tuple(x.upper() for x in tr))
                res.append(f"Entendido: {'NO ' if t['neg'] else ''}{' '.join(tr).upper()}.")
                note = self.d.note_new(tr, t["neg"], part, t.get("when", ""), lambda f, n=False: self.qa.say(f, neg=n))
                if note:
                    res.append(note)
            self.topic = self._next(found, self.topic)
        if stored:
            self.d.last_facts = stored
        return " ".join(res)
