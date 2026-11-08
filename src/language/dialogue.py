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
from datetime import date, datetime, timedelta
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


_INVAR = {"saltamontes", "paraguas", "cumpleanos", "sacacorchos", "abrelatas", "cortauñas", "cortaunas", "rascacielos", "lavaplatos", "tocadiscos", "parabrisas", "cascanueces", "sacapuntas", "pasatiempos", "quitamanchas", "tiralineas", "cuentagotas", "lavavajillas", "limpiaparabrisas", "posavasos", "matamoscas", "portaaviones", "guardabosques", "hazmerreir"}


def _invariable(w: str) -> bool:
    """Palabras compuestas que no cambian en plural (saltamontes, paraguas...): no son plurales aunque acaben en -s."""
    return w in _INVAR or bool(re.match(r"(?:salta|para|saca|abre|corta|lava|porta|cuenta|rompe|limpia|guarda|quita|tira|mata|pasa|rasca|cubre|pica|lanza|cierra|aparca|posa|cuenta)\w{3,}s$", w))


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
        self.tema = ""                      # parche-111: ultima pregunta hecha (para saludar con sentido)
        self.veces = {}     # parche-110: cuantas veces se ha dicho cada cortesia (para no repetir la misma frase)

    def _rotar(self, clave: str, opciones: List[str]) -> str:
        """Rota entre variantes de una cortesia (sin azar: misma conversacion, mismas respuestas). Cuenta desde la 2a vez que se dice."""
        n = self.veces.get(clave, 1) - 1
        if not self.dry:
            self.veces[clave] = n + 2
        return opciones[n % len(opciones)]

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
        if not hits and s and p:                                   # parche-86: "sirve" ~ "servir_para": mismo verbo con preposicion, objeto libre
            head = str(p).upper().split("_")[0]
            hits = [(x["s"], x["p"], x["o"]) for x in self.m.facts
                    if not x.get("neg") and x["s"] == str(s).upper() and x["p"].split("_")[0] == head and (o in (None, "_") or x["o"] == str(o).upper())][:1]
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
        if not statement and self.last_question and self.last and not getattr(self, "_explaining_last", False):
            found = qa.parse(self.last.strip()) or []              # parche-84: si la pregunta ahora se lee pero no da hechos, se justifica lo que dije
            if found:
                self._explaining_last = True
                try:
                    return self.explain(qa, self.last.strip())
                finally:
                    self._explaining_last = False
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
        # 1b) enrutador de operaciones (parche-87): decide QUE se pide, sea cual sea la forma de decirlo
        from src.language import intents, skills
        op, _conf = intents.route(raw)
        if op in ("HORA", "FECHA", "IDENTIDAD", "CAPACIDAD"):
            t = {"HORA": "que hora es", "FECHA": "que dia es hoy", "IDENTIDAD": "quien eres", "CAPACIDAD": "que sabes hacer"}[op]
            raw = t
        elif op == "UBICACION":
            return skills.UBICACION, None
        elif op == "CALC_FECHA":
            ans = skills.calc_fecha(raw, self._today())
            if ans:
                return ans, None
        elif op in ("ARITMETICA", "DIA_SEMANA", "DIAS_HASTA", "FUERA"):      # parche-88
            if op == "FUERA":
                return skills.FUERA, None
            ans = skills.aritmetica(raw) if op == "ARITMETICA" else (skills.dia_semana(raw, self._today()) if op == "DIA_SEMANA" else skills.dias_hasta(raw, self._today()))
            if ans:
                return ans, None
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
        # nombre propio de una cosa ("El perro de Irene se llama Toby")          # parche-86
        m = re.fullmatch(r"((?:el|la|mi|su|un|una) .+?) se llama (\w+)", t)
        if m and "?" not in raw:
            key = "_".join(self._bare(m.group(1)).split()).upper()
            mr = re.match(r"\s*(.+?)\s+se\s+llama\s+(\S+?)[\s.!]*$", raw, re.I)
            val = (mr.group(2) if mr else m.group(2)).strip(".!")
            m_.add_fact((key, "LLAMARSE", norm(val).upper()), source=raw.strip())
            m_.display[key] = (mr.group(1) if mr else m.group(1)).strip()
            m_.display[norm(val).upper()] = val
            return f"Entendido: {m_.display[key]} se llama {val}.", None
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
                        def _sg(w):
                            return w[:-3] + "z" if w.endswith("ces") else (w[:-2] if re.search(r"[^aeiou]es$", w) and not w.endswith(("ides", "ones")) else (w[:-1] if w.endswith("s") else w))

                        def _core(o):
                            return re.sub(r"^(el|la|los|las|un|una|unos|unas)\s+", "", self._disp(o))
                        dn_disp = self._disp(name)
                        _c = _core(name).lower()
                        pl_disp = dn_disp.lower().startswith(("los ", "las ")) or (_c.endswith("s") and norm(_c) not in ("lunes", "martes", "miercoles", "jueves", "viernes", "crisis", "tesis", "virus") and not _invariable(norm(_c)) and bool(re.match(r"que es (un|una|el|la) ", t)))
                        if t.startswith("que son") or pl_disp and t.startswith("que son"):
                            # parche-98: "Los asteroides son rocas" (no "El asteroides es una rocas")
                            core = _core(name).lower()
                            subj = ("las " if dn_disp.lower().startswith("las ") else "los ") + core
                            pls = []
                            for o in objs[:3]:
                                c_ = _core(o).lower()
                                pls.append(c_ if c_.endswith("s") else c_ + ("es" if c_[-1] not in "aeiou" else "s"))
                            return f"{subj.capitalize()} son {' y '.join(pls)}.", None
                        if pl_disp:                                      # se pregunta en singular lo que se guardo en plural
                            art_ = "la " if dn_disp.lower().startswith("las ") else "el "
                            subj = art_ + " ".join(_sg(w) for w in _core(name).lower().split())
                        else:
                            subj = self._art(dn_disp)
                        cls = []
                        for o in objs[:3]:
                            c_ = _core(o)
                            if c_.lower().endswith("s") and not c_.lower().endswith(("is", "us")):
                                c_ = " ".join(_sg(w) for w in c_.split())
                            ar_ = re.match(r"(el|la|los|las|un|una|unos|unas)\s", self._disp(o).lower())
                            fem = (ar_.group(1) in ("la", "las", "una", "unas")) if ar_ else o.upper().endswith("A")
                            cls.append(("una " if fem else "un ") + c_.lower())
                        return f"{subj[:1].upper() + subj[1:]} es {' y '.join(cls)}.", None
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
            if self.veces.get("hola", 0) and not m.group(2):
                # parche-111: la respuesta depende de la conversacion (ya nos saludamos; de que se hablo), no de azar
                u = f", {self.user}" if self.user else ""
                pref = self._rotar("hola", [" de nuevo", " otra vez", " otra vez por aquí", " de nuevo, ¿seguimos?"])
                ctx = ""
                tema = getattr(self, "tema", "") or self.last_question
                if tema:
                    ctx = f" Antes me preguntabas «{tema.strip(' ¿?!¡.')}»."
                elif self.last_facts:
                    ctx = " Hace un momento aprendí algo nuevo contigo."
                return f"{GREET[key]}{pref}{u}!{ctx} " + self._help()
            if not self.dry:
                self.veces["hola"] = self.veces.get("hola", 0) + 1
            return text + " " + self._help()
        if re.fullmatch(r"(como estas|que tal|que tal estas|como te va|como va todo|como esta usted|que tal esta usted|que tal todo|como te encuentras)( hoy)?", t):
            return "Estoy bien, gracias. ¿Y usted?" if self.formal else "Estoy bien, gracias. ¿Y tú?"
        if re.fullmatch(BYE + r"( \w+)?", t):
            return "¡Hasta luego" + (f", {self.user}" if self.user else "") + "! Aquí estaré cuando quieras."
        if re.fullmatch(THANKS, t):
            base = "De nada, a su disposición." if self.formal else "De nada."
            if self.veces.get("gracias", 0):
                return self._rotar("gracias", ["De nada, para eso estoy.", "De nada. ¿Algo más?", "De nada, un placer.", base])
            if not self.dry:
                self.veces["gracias"] = 1
            return base
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
        self.lectura = None

    _U = {  # unidad -> (magnitud, valor base, singular, plural)
        "milimetro": ("L", 0.001, "milímetro"), "centimetro": ("L", 0.01, "centímetro"), "decimetro": ("L", 0.1, "decímetro"), "metro": ("L", 1.0, "metro"), "kilometro": ("L", 1000.0, "kilómetro"),
        "miligramo": ("M", 0.001, "miligramo"), "gramo": ("M", 1.0, "gramo"), "kilogramo": ("M", 1000.0, "kilogramo"), "kilo": ("M", 1000.0, "kilo"), "tonelada": ("M", 1e6, "tonelada"),
        "mililitro": ("V", 0.001, "mililitro"), "centilitro": ("V", 0.01, "centilitro"), "litro": ("V", 1.0, "litro"),
        "segundo": ("T", 1.0, "segundo"), "minuto": ("T", 60.0, "minuto"), "hora": ("T", 3600.0, "hora"), "dia": ("T", 86400.0, "día"), "semana": ("T", 604800.0, "semana"), "ano": ("T", 31536000.0, "año")}

    def _unidades(self, t: str) -> Optional[str]:
        """parche-104: "cuantos metros tiene un kilometro", "cuantos segundos son 2 horas" (conversion de unidades, sin analizador)."""
        from src.language import skills

        def un(w):
            w = w.strip()
            for c in (w, w[:-1], w[:-2]):
                if c in self._U:
                    return c
            return None
        m = re.match(r"^(?:y )?cuant[oa]s (\w+) (?:tiene|tienen|hay en|caben en|mide|miden|son|equivalen a|hay dentro de|son en) (un|una|uno|\w+) (\w+)$", t)
        if not m:
            return None
        a, b = un(m.group(1)), un(m.group(3))
        if not a or not b or self._U[a][0] != self._U[b][0]:
            return None
        qty = m.group(2)
        k = 1.0 if qty in ("un", "una", "uno") else (float(qty) if qty.replace(".", "", 1).isdigit() else skills.NUMS.get(qty))
        if k is None:
            return None
        v = k * self._U[b][1] / self._U[a][1]
        vs = str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:.6g}".replace(".", ",")
        sa, sb = self._U[a][2], self._U[b][2]
        pa = sa + ("es" if sa.endswith(("r", "n")) and False else "s")
        pb = sb + "s"
        fem = sb in ("hora", "semana", "tonelada")
        ksh = ("una" if fem else "un") if k == 1 else (str(int(k)) if k == int(k) else str(k).replace(".", ","))
        left = f"{ksh} {sb if k == 1 else pb}"
        return f"{left[:1].upper() + left[1:]} {'tiene' if k == 1 else 'son'} {vs} {sa if v == 1 else pa}."

    _MESES_D = {"enero": 31, "febrero": 28, "marzo": 31, "abril": 30, "mayo": 31, "junio": 30, "julio": 31, "agosto": 31, "septiembre": 30, "setiembre": 30, "octubre": 31, "noviembre": 30, "diciembre": 31}
    _LADOS = {"triangulo": 3, "cuadrado": 4, "rectangulo": 4, "rombo": 4, "trapecio": 4, "pentagono": 5, "hexagono": 6, "heptagono": 7, "octogono": 8, "eneagono": 9, "decagono": 10, "circulo": 0}

    def _hechos_fabrica(self, t: str) -> Optional[str]:
        """parche-104: conocimiento general de calendario y geometria que no hay que ensenar a nadie (calendario, figuras)."""
        m = re.match(r"^(?:y )?cuant[oa]s (dias|meses|semanas|horas) (?:tiene|tienen|hay en|son en) (?:un |el |una |la )?(\w+)$", t)
        if m:
            u, w = m.group(1), m.group(2)
            if u == "dias" and w == "ano":
                return "Un año tiene 365 días (366 si es bisiesto)."
            if u == "meses" and w == "ano":
                return "Un año tiene 12 meses."
            if u == "dias" and w == "mes":
                return "Un mes tiene entre 28 y 31 días."
            if u == "dias" and w in self._MESES_D:
                return f"{w.capitalize()} tiene {self._MESES_D[w]} días" + (" (29 si el año es bisiesto)." if w == "febrero" else ".")
            if u == "meses" and w == "semestre":
                return "Un semestre tiene 6 meses."
            if u == "meses" and w == "trimestre":
                return "Un trimestre tiene 3 meses."
            if u == "meses" and w == "bimestre":
                return "Un bimestre tiene 2 meses."
        m = re.match(r"^(?:y )?cuant[oa]s (?:lados|vertices|esquinas) tiene (?:un |el |una |la )?(\w+)$", t)
        if m and m.group(1) in self._LADOS:
            k = self._LADOS[m.group(1)]
            nom = {"triangulo": "triángulo", "rectangulo": "rectángulo", "pentagono": "pentágono", "hexagono": "hexágono", "heptagono": "heptágono", "octogono": "octógono", "eneagono": "eneágono", "decagono": "decágono", "circulo": "círculo"}.get(m.group(1), m.group(1))
            pal = {3: "tres", 4: "cuatro", 5: "cinco", 6: "seis", 7: "siete", 8: "ocho", 9: "nueve", 10: "diez"}.get(k, str(k))          # parche-105: en palabras, como contesta la memoria
            return f"Un {nom} tiene {pal} lados." if k else "Un círculo no tiene lados: es una curva cerrada."
        if re.match(r"^(?:y )?cuant[oa]s (?:continentes|oceanos) (?:hay|existen|tiene la tierra|tiene el planeta)(?: en la tierra| en el mundo| en el planeta)?$", t):
            return ("Se suelen contar 7 continentes: África, América del Norte, América del Sur, Antártida, Asia, Europa y Oceanía."
                    if "continentes" in t else "Se suelen contar 5 océanos: Pacífico, Atlántico, Índico, Antártico y Ártico.")
        return None

    def _skills_pre(self, raw: str) -> Optional[str]:
        """parche-103: habilidades que no dependen del analizador ni del enrutador: contar, aritmetica con palabras, dias relativos (hoy/ayer/manana)."""
        from src.language import skills
        t = re.sub(r"\s+", " ", re.sub(r"[¡!¿?.,;:\"«»]", " ", n(raw))).strip()
        m = re.match(r"^(?:puedes |podrias |sabes |quiero que )?(?:contar|cuentas?|cuentame|cuente)(?: del? 1)? (?:hasta|al) (\d{1,3})$", t) \
            or re.match(r"^(?:puedes |podrias )?(?:contar|cuenta) hasta (\w+)$", t)
        if m:
            raw_n = m.group(1)
            nn = int(raw_n) if raw_n.isdigit() else skills.NUMS.get(raw_n)
            if nn and 1 <= nn <= 100:
                return ", ".join(str(i) for i in range(1, nn + 1)) + "."
        if re.match(r"^(?:y )?(?:cuanto|cuantos?) (?:es|son|da|vale|sale|serian|seria)\b|^(?:calcula|dime cuanto es|cual es el resultado de)\b", t) \
                and re.search(r"\d|\b(?:uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|veinte|treinta|cuarenta|cincuenta|cien|raiz|por ciento)\b", t):
            ans = skills.aritmetica(raw)
            if ans:
                return ans
        t2 = skills._words_to_digits(t)
        mop = re.match(r"^(?:y )?(?:cuanto (?:es|son|da|vale|seria)|calcula|dime) (la mitad|el doble|el triple|el cuadruple|el cuadrado|el cubo|la tercera parte|la cuarta parte|la quinta parte|la decima parte) de (\d+(?:[.,]\d+)?)$", t2) \
            or re.match(r"^(?:y )?(?:cuanto (?:es|son|da|vale|seria)|calcula) (\d+(?:[.,]\d+)?) (?:elevado )?al (cuadrado|cubo)$", t2)
        if mop:                                                                        # parche-104: "la mitad de 50", "el cuadrado de 9", "3 al cuadrado"
            if mop.group(2) in ("cuadrado", "cubo"):
                x, oper = float(mop.group(1).replace(",", ".")), mop.group(2)
            else:
                x, oper = float(mop.group(2).replace(",", ".")), mop.group(1)
            f = {"la mitad": lambda v: v / 2, "el doble": lambda v: v * 2, "el triple": lambda v: v * 3, "el cuadruple": lambda v: v * 4, "el cuadrado": lambda v: v ** 2, "cuadrado": lambda v: v ** 2,
                 "el cubo": lambda v: v ** 3, "cubo": lambda v: v ** 3, "la tercera parte": lambda v: v / 3, "la cuarta parte": lambda v: v / 4, "la quinta parte": lambda v: v / 5, "la decima parte": lambda v: v / 10}[oper]
            r = f(x)
            fm = lambda v: str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:.6g}".replace(".", ",")
            if oper in ("cuadrado", "cubo"):
                return f"{fm(x)} al {oper} es {fm(r)}."
            return f"{oper.capitalize()} de {fm(x)} es {fm(r)}."
        fab = self._hechos_fabrica(t)
        if fab:
            return fab
        mrel = re.match(r"^(?:y )?(?:que|cual) (?:dia|fecha|dia de la semana) (?:fue|era|es|sera|seria|va a ser|toca|cae|caera|caia) (hace|dentro de|en) (\w+) (dias?|semanas?)$", t) \
            or re.match(r"^(?:y )?(hace|dentro de|en) (\w+) (dias?|semanas?) (?:que|cual) (?:dia|fecha|dia de la semana) (?:fue|era|es|sera|seria|va a ser|toca|cae|caera|caia)$", t)
        if mrel:                                                                       # parche-104: "que dia fue hace 4 dias" / "dentro de 10 dias que dia sera"
            k = int(mrel.group(2)) if mrel.group(2).isdigit() else skills.NUMS.get(mrel.group(2))
            if k is not None and 0 <= k <= 100000:
                k *= 7 if mrel.group(3).startswith("semana") else 1
                past = mrel.group(1) == "hace"
                d = self.d._today() + timedelta(days=-k if past else k)
                meses_ = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
                return f"{'Hace' if past else 'Dentro de'} {mrel.group(2)} {mrel.group(3).replace('dia', 'día')} {'fue' if past else 'será'} {DAYS[d.weekday()]}, {d.day} de {meses_[d.month - 1]} de {d.year}."
        uni = self._unidades(t)
        if uni:
            return uni
        m = re.match(r"^(?:y )?(?:que|cual) (?:dia|fecha|dia de la semana) (?:fue|era|es|sera|seria|va a ser|va a a ser|vamos a tener|toca) (hoy|ayer|anteayer|antes de ayer|manana|pasado manana)$", t) \
            or re.match(r"^(hoy|ayer|anteayer|antes de ayer|manana|pasado manana) (?:que|cual) (?:dia|fecha) (?:fue|era|es|sera|va a ser|va a a ser)$", t)
        if m:
            rel = m.group(1)
            delta = {"hoy": 0, "ayer": -1, "anteayer": -2, "antes de ayer": -2, "manana": 1, "pasado manana": 2}[rel]
            d0 = self.d._today()
            d = d0 + timedelta(days=delta)
            verb = "fue" if delta < 0 else ("es" if delta == 0 else "será")
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            return f"{rel.replace('manana', 'mañana').capitalize()} {verb} {DAYS[d.weekday()]}, {d.day} de {meses[d.month - 1]} de {d.year}."
        return None

    _APRENDE = re.compile(r"^\s*(?:por favor,?\s*)?(?:aprende|aprended|memoriza|estudia|lee|analiza|apr[eé]ndete)\s*(?:esto|lo siguiente|este texto|el siguiente texto|el texto|esta informaci[oó]n|el siguiente art[ií]culo)?\s*[:\-–]\s*(.+)$", re.I | re.S)

    def es_texto_para_aprender(self, raw: str):
        """parche-113: «aprende esto: …» o un texto largo con varias frases afirmativas -> el texto; si no, None."""
        m = self._APRENDE.match(raw or "")
        if m and len(m.group(1).strip()) > 20:
            return m.group(1).strip()
        if len(raw or "") >= 600 and not raw.strip().startswith("¿") and len(re.findall(r"[.!?](?:\s|$)", raw)) >= 4 and raw.count("?") <= 1:
            return raw.strip()
        return None

    def aprender_texto(self, texto: str) -> str:
        """parche-113: lee el texto entero (sin limite de 2000) con el LECTOR y lo guarda en la memoria. Deja el informe completo en self.lectura."""
        from src.language.lector import resumen
        from src.language.lector_ud import guardar_traza, lector_para

        def escuela(cl, tema):
            try:
                return self.parser.parse(cl, self.topic) or []
            except Exception:                                                       # noqa
                return []
        rep = lector_para(self.m, self.parser).leer(texto)
        self.lectura = rep
        guardar_traza(rep)
        out = resumen(rep)
        self.d.last = out
        return out

    def say(self, raw: str) -> str:
        """parche-95: si la respuesta es un fallo y la pregunta tiene una errata corregible, reintenta con la pregunta corregida."""
        from src.language import consultas
        if not self.d.pending:
            txt_ = self.es_texto_para_aprender(raw)
            if txt_:
                return self.aprender_texto(txt_)
        raw = re.sub(r"^([¿\s]*)[yY]\s+(?=(?:qu[eé]|cu[aá]les?|qui[eé]nes?|cu[aá]nt[oa]s?|d[oó]nde|c[oó]mo)\b)", r"\1", raw)       # parche-103: "y cual es el planeta mas pequeno?"
        if is_question(raw) and len(raw) < 140:
            self.d.tema = raw                                                                                                       # parche-111: de que se hablo (para saludar con sentido)
        if not self.d.pending:
            try:
                sp_ = self._skills_pre(raw) or self._skills_pre(consultas.canonical(raw))
            except Exception:                                                                                                  # noqa
                sp_ = None
            if sp_:
                self.d.last = sp_
                return sp_
            if getattr(self.m, "textos", None):                                     # parche-127: preguntas sobre lo leido en un texto (entidades, tipo de pregunta, arbol de la frase)
                try:
                    from src.language import lectura_ent
                    lec_ = lectura_ent.responder(self, raw) if (is_question(raw) or lectura_ent.parece_pregunta(raw) or lectura_ent.es_peticion(raw)) else None
                except Exception:                                                  # noqa
                    lec_ = None
                if lec_:
                    self.d.last, self.d.last_question = lec_, raw
                    return lec_
        pq_ = False
        if getattr(self.m, "textos", None) and not self.d.pending:                  # parche-127: «donde nacio» sin signos, con un texto leido, es una pregunta
            try:
                from src.language import lectura_ent
                pq_ = lectura_ent.parece_pregunta(raw)
            except Exception:                                                       # noqa
                pq_ = False
        if self.d.pending or not (is_question(raw) or is_question(consultas.canonical(raw)) or pq_):
            if not self.d.pending:
                try:                                                                # parche-105: "Dime cinco frutas", "gato es a felino como perro es a ?"
                    from src.language import conceptos
                    ord_ = conceptos.antes_orden(raw, self.m)
                except Exception:                                                   # noqa
                    ord_ = None
                if ord_:
                    self.d.last, self.d.pending = ord_, None
                    return ord_
            out_ = self._say1(raw)
            if getattr(self.m, "textos", None) and not self.d.pending and len(raw.split()) <= 12 and consultas.es_fallo(out_):
                try:                                                                # parche-127: «tuvo hermanos» (sin signos) que nadie entendio: se prueba como pregunta sobre lo leido
                    from src.language import lectura_ent
                    lec3_ = lectura_ent.responder(self, raw, final=True)
                except Exception:                                                   # noqa
                    lec3_ = None
                if lec3_ and not lec3_.startswith(("No he leído nada que conteste", "De ")):
                    self.d.last = lec3_
                    return lec3_
            return out_
        try:
            from src.language import conceptos                                      # parche-99: "que es un X" (la memoria solo conoce ejemplares) y "en que se parecen A y B"
            pre_ = conceptos.antes(raw, self.m) or conceptos.antes(consultas.canonical(raw), self.m)
        except Exception:                                                           # noqa
            pre_ = None
        if pre_:
            self.d.last, self.d.pending = pre_, None
            return pre_
        saved = (self.d.last, self.d.last_question, self.topic)
        out = self._say1(raw)
        if not consultas.es_fallo(out):
            try:                                                                    # parche-102: la memoria contesta y el diccionario de conceptos anade la ficha
                from src.language import conceptos
                comp_ = conceptos.complemento(raw, self.m) or conceptos.complemento(consultas.canonical(raw), self.m)
            except Exception:                                                       # noqa
                comp_ = None
            if comp_ and comp_ not in out:
                out = out + " " + comp_
                self.d.last = out
        if consultas.es_fallo(out):
            fixed = consultas.corregir(raw, self.m)
            subs_fix = list(consultas.SUBS)
            for alt_ in (fixed, consultas.sinonimizar(fixed, self.m)):             # parche-98: errata, luego sinonimo conocido por la memoria
                if alt_ != raw:
                    after = (self.d.last, self.d.last_question, self.topic, self.d.pending)
                    self.d.last, self.d.last_question, self.topic, self.d.pending = saved + (None,)
                    out2 = self._say1(alt_)
                    if not consultas.es_fallo(out2):
                        subs_all = subs_fix + [x_ for x_ in consultas.SUBS if x_ not in subs_fix] if alt_ is not fixed else subs_fix
                        nota = " ".join(f"(Entiendo «{a_}» como «{b_}».)" for a_, b_ in subs_all if a_.lower() != b_.lower())
                        return (nota + " " + out2) if nota else out2
                    self.d.last, self.d.last_question, self.topic, self.d.pending = after
            try:
                from src.language import conceptos                                  # parche-99: diccionario de conceptos (la memoria manda; esto es el fondo de fabrica)
                cx = conceptos.responder(raw, self.m) or conceptos.responder(consultas.canonical(raw), self.m)
            except Exception:                                                       # noqa
                cx = None
            if cx:
                self.d.last, self.d.pending = cx, None
                return cx
            try:
                from src.language import lexico
                lx = lexico.responder(raw) or lexico.responder(consultas.canonical(raw))                                          # parche-98: preguntas sobre palabras (sinonimo, antonimo, tipo de)
            except Exception:                                                       # noqa
                lx = None
            if lx:
                self.d.last, self.d.pending = lx, None
                return lx
            if getattr(self.m, "textos", None):                                    # parche-127: lo ultimo que se intenta es lo leido (o decir que no se leyo)
                try:
                    from src.language import lectura_ent
                    lec2_ = lectura_ent.responder(self, raw, final=True)
                except Exception:                                                  # noqa
                    lec2_ = None
                if lec2_:
                    self.d.last, self.d.pending = lec2_, None
                    return lec2_
        return out

    def _say1(self, raw: str) -> str:
        if not self.d.pending:                                              # parche-90: normalizador de preguntas (una familia -> una forma canonica)
            from src.language import consultas
            qm = consultas.quien_mas(raw)
            if qm:
                cmp_, adj, a_, b_ = qm
                for x_, y_ in ((a_, b_), (b_, a_)):
                    if n(self.say(f"¿Es {x_} {cmp_} {adj} que {y_}?")).startswith("si"):
                        self.d.last = f"{x_} es {cmp_} {adj} que {y_}."
                        return self.d.last
                self.d.last = "No lo sé."
                return self.d.last
            sg = consultas.seguimiento(raw, self.d.last_question, self.m)       # parche-97: "¿Y Venus?"
            if sg:
                raw = sg
            cmp2 = consultas.comparar(raw)
            if cmp2:                                                            # parche-97: "Compara Marte y la Tierra"
                outs = [self.say(f"¿Qué sabes de {x_}?") for x_ in cmp2]
                self.d.last = " ".join(f"{x_}: {o_}" for x_, o_ in zip(cmp2, outs))
                return self.d.last
            raw = consultas.canonical(raw)
        mc = re.match(r"^\s*no\s*,\s+(\S.*)$", raw, re.I)
        if mc and not self.d.pending and not is_question(mc.group(1)) and len(mc.group(1).split()) >= 3 \
                and not re.search(r"\b(no|nunca|nadie|ni|tampoco|nada|jamas)\b", n(mc.group(1))):
            raw = mc.group(1)[:1].upper() + mc.group(1)[1:]             # parche-85: "No, Marta vive en Vigo." es una correccion, no una negacion de Vigo
        reply, cont = self.d.act(raw, self.qa)
        if reply and not cont and is_question(raw) and not re.search(r"\b(sabes|sacas|seguro|repite)\b", n(raw)):
            self.d.last_question = raw                                      # parche-85: las preguntas especiales tambien se pueden justificar ("¿Como lo sabes?")
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
