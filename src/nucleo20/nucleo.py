"""LCM 2.0 · núcleo conversacional unificado.

Un único grafo de conceptos para la conversación: ENTIDADES (personas, cosas, clases, la persona
que habla y el propio LCM), RELACIONES entre entidades (padre de, perro de, color favorito de...)
y MARCOS (quién hace qué, a quién, dónde, cuándo, cuánto, con negación y vigencia temporal).

- Cada afirmación entendida por completo se guarda una sola vez, con la frase de origen.
- Las preguntas se contestan consultando el grafo y deduciendo (herencia de clases, parentescos,
  comparaciones transitivas, sumas por categoría, efectos de acciones, valores únicos).
- Si no hay prueba, el núcleo se abstiene y lo dice. Nunca rellena con coincidencias de texto.
- Lo que no entiende por completo lo delega (devuelve None) en las capas anteriores del LCM.
"""
from __future__ import annotations

import json
import os
import re
from typing import List, Optional

from . import morfo as M
from . import conceptos as KB
from .morfo import sa
from . import lengua as G
from .lengua import SN, Clausula

ORDINALES = {"mayor", "mediano", "mediana", "menor", "pequeno", "pequena", "pequeño", "pequeña", "primero", "primera", "segundo", "segunda", "tercero", "tercera", "ultimo", "ultima"}
K_EPICENOS = {"jefe", "cliente", "estudiante", "pianista", "tigre", "elefante", "ratón", "raton"}
REL_CANON = {"madre": ("padre", "f"), "padre": ("padre", "m"), "mama": ("padre", "f"), "papa": ("padre", "m"), "hermana": ("hermano", "f"), "hija": ("hijo", "f"), "abuela": ("abuelo", "f"),
             "tia": ("tio", "f"), "prima": ("primo", "f"), "nieta": ("nieto", "f"), "sobrina": ("sobrino", "f"), "esposa": ("esposo", "f"), "mujer": ("esposo", "f"), "marido": ("esposo", "m"),
             "novia": ("novio", "f"), "amiga": ("amigo", "f"), "vecina": ("vecino", "f"), "jefa": ("jefe", "f"), "profesora": ("profesor", "f"), "compañera": ("compañero", "f"),
             "alumna": ("alumno", "f"), "suegra": ("suegro", "f"), "cuñada": ("cuñado", "f"), "nuera": ("yerno", "f"), "madrina": ("padrino", "f"), "gata": ("gato", "f"), "perra": ("perro", "f"),
             "maestra": ("maestro", "f"), "socia": ("socio", "f"), "empleada": ("empleado", "f"), "dueña": ("dueño", "f"), "bisabuela": ("bisabuelo", "f"), "hermanastra": ("hermanastro", "f"),
             "madrastra": ("padrastro", "f"), "doctora": ("doctor", "f"), "medica": ("medico", "f"), "entrenadora": ("entrenador", "f"), "mejor amiga": ("mejor amigo", "f")}
REL_DISP_BASE = {c for c, g_ in REL_CANON.values()}
REL_DISP = {("padre", "f"): "madre", ("esposo", "f"): "mujer", ("esposo", "m"): "marido", ("yerno", "f"): "nuera", ("padrino", "f"): "madrina", ("padrastro", "f"): "madrastra"}
FAMILIA = {"padre", "hijo", "hermano", "abuelo", "nieto", "tio", "sobrino", "primo", "esposo", "novio", "suegro", "cuñado", "yerno", "bisabuelo"}
SIMETRICAS = {"amigo", "vecino", "compañero", "pareja", "esposo", "novio", "primo", "hermano", "socio", "colega", "mejor amigo", "cuñado", "conocido"}
INVERSAS = {"jefe": "empleado", "empleado": "jefe", "profesor": "alumno", "alumno": "profesor", "maestro": "alumno", "padrino": "ahijado", "ahijado": "padrino", "entrenador": "jugador"}
PERSONA_CLS = FAMILIA | SIMETRICAS | set(INVERSAS) | {"niño", "chico", "hombre", "señor", "persona", "medico", "doctor", "bebe", "gemelo", "ahijado", "jugador", "dueño", "maestro"}
FUNCIONAL = {("vivir", "en"), ("estar", "en"), ("nacer", "en"), ("ser", "de"), ("residir", "en"), ("trabajar", "en"), ("estudiar", "en")}
FUNC_SIEMPRE = {("vivir", "en"), ("estar", "en"), ("nacer", "en"), ("residir", "en"), ("trabajar", "en"), ("estudiar", "en")}
V_EQ = {"residir": "vivir", "poseer": "tener", "adorar": "encantar", "amar": "querer"}
DAR = {"dar", "regalar", "entregar", "prestar", "vender", "devolver", "pasar", "ceder", "donar", "enviar", "mandar", "dejar", "traer", "llevar"}
OBTENER = {"comprar", "recibir", "encontrar", "conseguir", "coger", "adoptar", "ganar", "adquirir", "heredar"}
PERDER = {"perder", "vender", "tirar", "regalar", "romper"}
IR = {"ir", "llegar", "volver", "viajar", "entrar", "regresar", "marchar"}
COLORES = {"rojo", "azul", "verde", "amarillo", "blanco", "negro", "naranja", "gris", "rosa", "morado", "marron", "violeta", "dorado", "plateado", "beige", "turquesa", "lila", "celeste", "granate", "fucsia"}
ANTON = [("grande", "pequeño"), ("alto", "bajo"), ("gordo", "delgado"), ("rapido", "lento"), ("nuevo", "viejo"), ("joven", "viejo"), ("bueno", "malo"), ("caro", "barato"), ("largo", "corto"),
         ("feliz", "triste"), ("contento", "triste"), ("abierto", "cerrado"), ("lleno", "vacio"), ("limpio", "sucio"), ("frio", "caliente"), ("facil", "dificil"), ("fuerte", "debil"),
         ("rico", "pobre"), ("simpatico", "antipatico"), ("guapo", "feo"), ("bonito", "feo"), ("claro", "oscuro"), ("ancho", "estrecho"), ("duro", "blando"), ("seco", "mojado"),
         ("encendido", "apagado"), ("vivo", "muerto"), ("sano", "enfermo"), ("soltero", "casado"), ("despierto", "dormido"), ("tranquilo", "nervioso"), ("ordenado", "desordenado"),
         ("mayor", "menor"), ("mayor", "joven"), ("pesado", "ligero"), ("dulce", "salado"), ("dulce", "amargo"), ("alegre", "triste"), ("cansado", "descansado"), ("ocupado", "libre"),
         ("divertido", "aburrido"), ("listo", "tonto"), ("trabajador", "vago"), ("valiente", "cobarde"), ("moderno", "antiguo"), ("ruidoso", "silencioso"), ("lejano", "cercano")]
_ANT = {}
for _a, _b in ANTON:
    _ANT.setdefault(_a, set()).add(_b); _ANT.setdefault(_b, set()).add(_a)
for _a, _bs in KB.kb()["ant"].items():                 # los contrarios de la base de conceptos amplían la tabla
    if not _a.endswith(("ar", "er", "ir")) or _a in ("mayor", "menor", "mejor", "peor"):
        for _b in _bs:
            _ANT.setdefault(_a, set()).add(_b)
ESTADO_TENER = {"hambre", "sed", "sueño", "frio", "calor", "miedo", "prisa", "razon", "suerte", "fiebre", "ganas", "tos", "dolor", "tiempo", "trabajo", "dinero", "clase", "cuidado", "paciencia", "vergüenza", "envidia", "celos"}
ACK = ["Entendido"]


def _cap(s: str) -> str:
    s = s.strip()
    return s[:1].upper() + s[1:] if s else s


def contrae(s: str) -> str:
    s = re.sub(r"\ba el\b", "al", s)
    s = re.sub(r"\bde el\b", "del", s)
    s = re.sub(r"\bcon ti\b", "contigo", s); s = re.sub(r"\bcon mí\b", "conmigo", s)
    return re.sub(r"\s+", " ", s).strip()


_SWAP = {"mi": "tu", "mis": "tus", "mio": "tuyo", "mia": "tuya", "mios": "tuyos", "mias": "tuyas", "conmigo": "contigo", "me": "te", "yo": "tú", "nuestro": "vuestro", "nuestra": "vuestra",
         "nuestros": "vuestros", "nuestras": "vuestras", "tu": "mi", "tus": "mis", "contigo": "conmigo", "te": "me", "tuyo": "mío", "tuya": "mía", "nos": "os", "mí": "ti", "ti": "mí"}


def cambia_persona(s: str) -> str:
    def r(m):
        w = m.group(0)
        k = w.lower()
        if k == "mí":
            return "ti"
        if k in ("té", "sé", "sí", "más", "qué"):
            return w
        if k == "ti":
            return "mí"
        if k in ("tú", "él"):
            return "yo" if k == "tú" else w
        if sa(k) in _SWAP:
            return _SWAP[sa(k)]
        if (k.endswith(("é", "í")) and len(k) > 3) or k.endswith(("aste", "iste")):   # 2.17: «llegué tarde» <-> «llegaste tarde»
            try:
                an = M.analizar(k)
                if an and all(a[1] == "pret" and a[2] == ("2s" if k.endswith("ste") else "1s") for a in an):
                    return M.conjugar(an[0][0], "pret", "1s" if k.endswith("ste") else "2s") or w
            except Exception:                            # noqa
                pass
        return w
    return re.sub(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", r, s)


_NO_VERBO_1S = {"como", "para", "sobre", "entre", "bajo", "vino", "traje", "nada", "cara", "rio", "cocina", "casa", "camino", "cuenta", "compra", "trabajo", "juego", "paso", "cambio", "pago", "uso", "canto", "baile",
                "sueño", "paseo", "amo", "ayuno", "desayuno", "almuerzo", "regalo", "dibujo", "estudio", "cuido", "peso", "calzo", "abrigo", "fumo", "saludo", "recibo", "corte", "toco", "techo", "seco", "limpio", "lleno"}


def causa_tu(causa: str) -> str:
    """Una causa dicha en primera persona («tengo mucho trabajo», «llegué tarde») contada de vuelta en segunda («tienes mucho trabajo»)."""
    ws = causa.split()
    for i, w in enumerate(ws[:3]):
        k = w.lower().strip(",.")
        if i and ws[i - 1].lower() not in ("no", "ya", "me", "hoy", "ayer", "siempre", "nunca", "también", "casi", "aún", "todavía"):
            break
        if k in ("no", "ya", "me", "hoy", "ayer", "siempre", "nunca", "también", "casi", "aún", "todavía", "es", "que"):
            continue
        if sa(k) in _SWAP or sa(k) in _NO_VERBO_1S and i == 0 and len(ws) > 1 and ws[1].lower() in ("de", "del", "en", "con", "y", "es", "era"):
            break
        try:
            an = M.analizar(k)
        except Exception:                                # noqa
            an = []
        if an and all(len(a) > 2 and a[2] == "1s" and a[1] in ("pres", "pret", "imp", "fut") for a in an) and (sa(k) not in _NO_VERBO_1S or i == 0):
            conv = M.conjugar(an[0][0], an[0][1], "2s")
            if conv:
                ws[i] = conv
        break
    return cambia_persona(" ".join(ws))


class Nucleo:
    def __init__(self, mem, parser, ruta=None):
        self.mem, self.parser = mem, parser
        base = getattr(mem, "path", None) or "memory/lcm_memory.json"
        self.ruta = ruta or os.path.join(os.path.dirname(str(base)) or ".", "lcm_nucleo20.json")
        self.E, self.R, self.F = {}, [], []
        self._fab = None
        self._pasos_fab = set()
        self.eq = {}
        self.turno = 0
        self.menc: List[str] = []
        self.ult_suj = None
        self.ult_nuevo = None
        self.ult_preg = None            # (texto, Clausula) de la última pregunta entendida
        self.ult_just = None            # justificación de la última respuesta
        self.ult_marco = None
        self.usuario = {"nombre": ""}
        self.pal = {}                   # forma sin acentos -> forma con acentos vista en la conversación
        self.E["U"] = {"tipo": "usuario", "nombre": "", "clase": "", "dueno": None, "gen": "", "pl": False}
        self.E["L"] = {"tipo": "lcm", "nombre": "LCM", "clase": "", "dueno": None, "gen": "m", "pl": False}
        self._cargar()

    # ------------------------------------------------------------------ persistencia
    def _cargar(self):
        try:
            with open(self.ruta, encoding="utf-8") as fh:
                d = json.load(fh)
            self.E.update(d.get("E", {})); self.R = d.get("R", []); self.F = d.get("F", []); self.eq = d.get("eq", {}); self.turno = d.get("turno", 0)
            self.usuario = d.get("usuario", self.usuario); self.pal = d.get("pal", {}); self.notas = d.get("notas", [])
        except (OSError, ValueError):
            pass

    def guardar(self):
        try:
            os.makedirs(os.path.dirname(self.ruta) or ".", exist_ok=True)
            tmp = self.ruta + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump({"v": 1, "E": self.E, "R": self.R, "F": self.F, "eq": self.eq, "turno": self.turno, "usuario": self.usuario, "pal": self.pal, "notas": getattr(self, "notas", [])}, fh, ensure_ascii=False)
            os.replace(tmp, self.ruta)
        except OSError:
            pass

    def olvidar_todo(self):
        self.E = {k: v for k, v in self.E.items() if k in ("U", "L")}
        self.E["U"]["nombre"] = ""; self.usuario = {"nombre": ""}
        self.R, self.F, self.eq, self.menc = [], [], {}, []
        self.notas = []
        self.ult_suj = self.ult_nuevo = self.ult_preg = self.ult_just = None
        self.guardar()

    # ------------------------------------------------------------------ entidades
    def can(self, e):
        while e in self.eq:
            e = self.eq[e]
        return e

    def _ent(self, eid, **kw):
        if eid not in self.E:
            self.E[eid] = {"tipo": eid[0], "nombre": "", "clase": "", "dueno": None, "gen": "", "pl": False}
        for k, v in kw.items():
            if v not in (None, "") and not self.E[eid].get(k):
                self.E[eid][k] = v
        return eid

    def unir(self, viejo, nuevo):
        """viejo pasa a ser nuevo (p. ej. «el perro de Ana» = Toby)."""
        viejo, nuevo = self.can(viejo), self.can(nuevo)
        if viejo == nuevo or viejo in ("U", "L"):
            return nuevo
        self.eq[viejo] = nuevo
        ev, en = self.E.get(viejo, {}), self.E.get(nuevo, {})
        for k in ("clase", "dueno", "gen", "orden"):
            if ev.get(k) and not en.get(k):
                en[k] = ev[k]
        for r in self.R:
            for k in ("x", "y"):
                if r[k] == viejo:
                    r[k] = nuevo
        for f in self.F:
            for k in ("s", "obj"):
                if f.get(k) == viejo:
                    f[k] = nuevo
            f["comps"] = [[p, (nuevo if e == viejo else e), d] for p, e, d in f.get("comps", [])]
        self.menc = [nuevo if x == viejo else x for x in self.menc]
        if self.ult_suj == viejo:
            self.ult_suj = nuevo
        if self.ult_nuevo == viejo:
            self.ult_nuevo = nuevo
        return nuevo

    def gen(self, e):
        e = self.can(e)
        d = self.E.get(e, {})
        if d.get("gen"):
            return d["gen"]
        if e.startswith("N:"):
            return M.genero_nombre(d.get("nombre") or e[2:])
        if d.get("clase"):
            return M.genero_sust(d["clase"])
        if e.startswith("K:"):
            return KB.genero(e[2:])
        return "m"

    def es_persona(self, e):
        e = self.can(e)
        if e in ("U", "L"):
            return True
        d = self.E.get(e, {})
        cl = d.get("clase", "")
        if cl:
            return cl in PERSONA_CLS
        return e.startswith("N:") and not d.get("cosa") and not d.get("lugar")

    def disp(self, e, sujeto=False):
        e = self.can(e)
        d = self.E.get(e, {})
        if e == "U":
            return "tú"
        if e == "L":
            return "yo"
        if e.startswith("N:"):
            return d.get("nombre") or e[2:].title()
        cl = d.get("clase") or e.split(":", 1)[1].split("@")[0]
        g = d.get("gen") or M.genero_sust(cl)
        pl = d.get("pl")
        if e.startswith("I:") or e.startswith("G:"):
            du = self.can(d.get("dueno") or "")
            if " " not in cl:
                nom = self._acento(self._rel_nombre(cl, g))
            else:
                c0, resto_c = cl.split(" ", 1)
                if " " not in resto_c and not resto_c.startswith("de"):
                    resto_c = M.concuerda(resto_c, g) if g == "f" else resto_c      # «hermana pequeña»
                nom = self._acento(self._rel_nombre(c0, g) + " " + resto_c)
            if d.get("orden"):
                nom += " " + {"pequeno": "pequeño", "pequena": "pequeña"}.get(M.concuerda(d["orden"], g) if d["orden"] not in ("mayor", "menor") else d["orden"], M.concuerda(d["orden"], g) if d["orden"] not in ("mayor", "menor") else d["orden"])
            if pl:
                nom = " ".join([M.plural(nom.split()[0])] + nom.split()[1:])
            if du == "U":
                return ("tus " if pl else "tu ") + nom
            if du == "L":
                return ("mis " if pl else "mi ") + nom
            art = {("m", False): "el", ("f", False): "la", ("m", True): "los", ("f", True): "las"}[(g, bool(pl))]
            return contrae(f"{art} {nom} de {self.disp(du)}") if du else f"{art} {nom}"
        if e.startswith("K:"):
            cl = self._acento(self._rel_nombre(cl, g) if d.get("gen") == "f" and cl in REL_DISP_BASE else cl)
            if d.get("sinart"):
                return cl
            art = {("m", False): "el", ("f", False): "la", ("m", True): "los", ("f", True): "las"}[(g, bool(pl))]
            return f"{art} {self._acento(sa(M.plural(cl))) if pl else cl}"
        return cl

    @staticmethod
    def _rel_nombre(r, g):
        if " " in r and (r, g) not in REL_DISP and g == "f":       # «hermano pequeño» -> «hermana pequeña»
            c0, resto_c = r.split(" ", 1)
            if " " not in resto_c and not resto_c.startswith("de"):
                resto_c = M.concuerda(resto_c, "f")
            return Nucleo._rel_nombre(c0, g) + " " + resto_c
        if (r, g) in REL_DISP:
            return REL_DISP[(r, g)]
        if g == "f":
            for fem, (c, gg) in REL_CANON.items():
                if c == r and gg == "f" and fem not in ("mama", "mujer", "esposa") :
                    return fem
            if r.endswith("o") and r not in ("moto", "foto", "radio", "mano", "disco", "libido", "seo", "dinamo", "polio"):
                return r[:-1] + "a"             # «moto», «foto», «mano»: ya son femeninos tal cual
        return r

    def mencionar(self, e):
        e = self.can(e)
        if e in ("L",):
            return
        if e in self.menc:
            self.menc.remove(e)
        self.menc.append(e)
        self.menc = self.menc[-12:]

    def ref3(self, genero=None, persona=None, excluye=()):
        for e in reversed(self.menc):
            e = self.can(e)
            if e in ("U", "L") or e in excluye or e.startswith("K:"):
                continue
            if persona is True and not self.es_persona(e):
                continue
            if genero and self.E.get(e, {}).get("gen") and self.gen(e) != genero:
                continue
            if genero and not self.E.get(e, {}).get("gen") and e.startswith("N:") and self.gen(e) != genero:
                continue
            return e
        return None

    def _canon_rel(self, cab, gen_art=""):
        c = cab
        if c in REL_CANON:
            return REL_CANON[c]
        if c.endswith("a") and (c[:-1] + "o") in (FAMILIA | SIMETRICAS | set(INVERSAS) | {"empleado", "alumno", "ahijado", "dueño", "maestro", "socio", "niño", "chico", "gato", "perro"}):
            return c[:-1] + "o", "f"
        return c, ("f" if gen_art == "f" and c in (FAMILIA | SIMETRICAS) else "")

    def _clase_sn(self, s: SN):
        cab = s.cab
        if cab == "ser" and any(sa(a) in ("vivo", "viva", "vivos") for a in (s.adjs or [])):
            return "ser vivo", "m"                       # 2.15: «un ser vivo» es una clase de dos palabras
        if cab in ("mujer", "marido", "mama", "papa") and not s.pos and s.de is None:
            return cab, ("f" if cab in ("mujer", "mama") else "m")
        extra = [a for a in s.adjs if a in ("favorito", "preferido", "mejor", "mayor", "menor", "pequeño", "primero", "ultimo", "nuevo", "viejo")]
        r, g = self._canon_rel(cab, s.gen)
        r = KB.kb()["alias"].get(r, r)                   # 2.15: «ropa» -> la clase «prenda»
        if extra:
            if extra[0] in ("mejor",):
                r = extra[0] + " " + r
            else:
                r = r + " " + extra[0]
        return r, g

    def ent_de(self, s: SN, crear=True, papel="suj", verbo=""):
        """Entidad (o lista) que nombra un SN. None si no se puede resolver."""
        if s is None:
            return None
        if s.coord:
            xs = []
            ant_cl = getattr(self, "_suj_cl", None)
            for p in s.coord:                           # 2.12: «mi primo Dani, su novia y yo»: «su» es del anterior de la lista
                x_ = self.ent_de(p, crear, papel, verbo)
                xs.append(x_)
                if isinstance(x_, str) and x_ not in ("U", "L") and self.es_persona(x_):
                    self._suj_cl = x_
            self._suj_cl = ant_cl
            if any(x is None for x in xs):
                return None
            out = []
            for x in xs:
                out.extend(x if isinstance(x, list) else [x])
            return out
        if s.pron:
            if s.pron == "U":
                return "U"
            if s.pron == "L":
                return "L"
            g = "f" if "f" in s.pron else ("m" if "m" in s.pron else None)
            if s.pron == "3n":
                return self.ult_nuevo or self.ref3()
            return self.ref3(genero=g, persona=True) or self.ref3(genero=g, persona=None)
        if s.propio:
            eid = "N:" + s.cab
            existe = eid in self.E or eid in self.eq
            if not existe and not crear:
                # ¿coincide con el nombre de pila de alguien conocido?
                for k, d in self.E.items():
                    if k.startswith("N:") and k[2:].split()[0] == s.cab and k not in self.eq:
                        return k
                return None
            if not existe:
                for k, d in self.E.items():
                    if k.startswith("N:") and (k[2:].split()[0] == s.cab or s.cab.split()[0] == k[2:]) and k not in self.eq:
                        return k
            self._ent(eid, nombre=s.nombre)
            if getattr(s, "art_nombre", False):
                self.E[eid]["cosa"] = True
            return self.can(eid)
        if not s.cab:
            return None
        ords = [a for a in (s.adjs or []) if sa(a) in ORDINALES]
        if ords and (s.pos or s.de is not None) and not s.pl:
            import copy as _copy
            s2 = _copy.copy(s); s2.adjs = [a for a in s.adjs if a not in ords]
            base = self.ent_de(s2, crear=False, papel=papel, verbo=verbo)
            cl0 = self._clase_sn(s2)[0]
            du0 = self.can(base.split("@", 1)[1]) if isinstance(base, str) and base.startswith("?I:") else None
            for k, d in self.E.items():
                if k not in self.eq and d.get("clase") == cl0 and M.masc(sa(d.get("orden") or "")) == M.masc(sa(ords[0])) and (du0 is None or self.can(d.get("dueno") or "") == du0):
                    return self.can(k)
        cl, g = self._clase_sn(s)
        dueno = None
        if s.pos == "U":
            dueno = "U"
        elif s.pos == "L":
            dueno = "L"
        elif s.pos == "3":
            # «su» nunca es la persona que habla (eso sería «mi») ni el LCM (sería «tu»)
            dueno = getattr(self, "_suj_cl", None) or None   # «Lola me invitó a su boda»: la de Lola
            dueno = dueno or (self.ult_suj if (self.ult_suj and self.can(self.ult_suj) not in ("L", "U")) else self.ref3(persona=True))
            hd_ = getattr(self, "_hablante_dicho", None)
            if dueno and hd_ and self.can(dueno) == self.can(hd_) and not getattr(self, "_suj_cl", None):
                dueno = self.ref3(persona=True, excluye=(self.can(hd_),)) or dueno   # quien solo opinó («su padre dice que sí») no suele ser el tema
            if dueno is None:
                return None
        elif s.de is not None:
            dueno = self.ent_de(s.de, crear, "de")
            if isinstance(dueno, list):
                dueno = dueno[0]
            if dueno is None:
                return None
        if dueno is not None:
            dueno = self.can(dueno)
            if not g and not s.pl and s.cab == cl and cl in FAMILIA and cl.endswith("o") and s.det != "i":
                g = "m"                                # «mi hermano» (singular) es un varón; «mis hermanos» puede incluir hermanas
            xs = [r["x"] for r in self.rels(cl, y=dueno) if (not g or self.gen(r["x"]) == g or not self.E.get(r["x"], {}).get("gen"))]
            xs = list(dict.fromkeys(self.can(x) for x in xs))
            if not xs and " " not in cl and not s.pl:     # «mi piso» = «mi piso nuevo»
                xs = list(dict.fromkeys(self.can(r["x"]) for c2 in {d.get("clase") for d in self.E.values() if str(d.get("clase") or "").startswith(cl + " ")} for r in self.rels(c2, y=dueno)))
            if xs:
                if s.apos:
                    for x in xs:
                        if x == "N:" + sa(s.apos):
                            return x
                elif len(xs) == 1 or not s.pl:
                    return xs[0] if not s.pl else xs
                else:
                    return xs
            if s.apos:
                eid = self._ent("N:" + sa(s.apos), nombre=s.apos, clase=cl, dueno=dueno, gen=g or None)
                if crear:
                    self._rel(cl, eid, dueno, "", g)
                return eid
            gid = "G:" + cl + "@" + dueno
            if s.pl and gid in self.E:
                return gid
            if not crear:
                return "?I:" + cl + "@" + dueno        # entidad consultada pero desconocida
            if s.pl:                                  # «mis padres», «nuestros vecinos»: un grupo, no una persona
                return self._ent(gid, clase=cl, dueno=dueno, gen=g or s.gen or M.genero_sust(cl), pl=True)
            eid0 = "I:" + cl + "@" + dueno
            previo = self.E.get(self.can(eid0)) if (eid0 in self.E or eid0 in self.eq) else None
            if previo is not None and g and previo.get("gen") and previo["gen"] != g:
                eid0 = "I:" + cl + "~" + g + "@" + dueno      # «mi hermano» ya existe y ahora habla de «mi hermana»: es otra persona
            eid = self._ent(eid0, clase=cl, dueno=dueno, gen=g or s.gen or M.genero_sust(cl), pl=s.pl)
            self._rel(cl, eid, dueno, "", g)
            return eid
        if s.apos:
            return self._ent("N:" + sa(s.apos), nombre=s.apos, clase=cl, gen=g or s.gen or None)
        # «Tenemos tres hijos. El mayor se llama Rubén. La mediana…»: uno de los del grupo recién nombrado
        if s.det == "d" and not s.pl and sa(s.cab) in ORDINALES and not s.pos and s.de is None and crear is not None:
            e_ord = self._del_grupo(sa(s.cab), s.gen or (g if g else ""), crear)
            if e_ord is not None:
                return e_ord
        # sin poseedor
        if s.det == "d" and not s.pl:
            cands = [k for k, d in self.E.items() if k not in self.eq and d.get("clase") == cl and (k.startswith("I:") or k.startswith("N:"))]
            if not cands:                              # «la entrevista» = «tu entrevista de trabajo»
                cands = [k for k, d in self.E.items() if k not in self.eq and str(d.get("clase") or "").startswith(cl + " de ") and (k.startswith("I:") or k.startswith("N:"))]
            if not cands:
                cands = [k for k, d in self.E.items() if k not in self.eq and d.get("clase") and (k.startswith("I:") or k.startswith("N:")) and d.get("clase") not in PERSONA_CLS
                         and any(c == cl for c, _ in self.clases(k))]
            if len(cands) == 1:
                return cands[0]
            if len(cands) > 1:
                for e in reversed(self.menc):
                    if self.can(e) in cands:
                        return self.can(e)
                return cands[-1]
        eid = self._ent("K:" + cl, clase=cl, gen=s.gen or g or M.genero_sust(cl))
        return eid

    def _del_grupo(self, orden, g, crear=True):
        """Instancia de un grupo contado hace poco («tres hijos»), identificada por su orden («el mayor»)."""
        cands = [f for f in self.F[-30:] if f["v"] == "tener" and f.get("pl_obj") and (f.get("cuant") or 0) >= 2 and f.get("obj_cls") and f.get("vig", True) and not f.get("neg")]
        if not cands:
            return None
        fr = cands[-1]
        cl, du = fr["obj_cls"], self.can(fr["s"])
        ya = [k for k, d in self.E.items() if k.startswith("I:") and d.get("clase") == cl and self.can(d.get("dueno") or "") == du and d.get("orden") == orden and k not in self.eq]
        if ya:
            return self.can(ya[0])
        for k, d in self.E.items():
            if d.get("clase") == cl and self.can(d.get("dueno") or "") == du and d.get("orden") == orden:
                return self.can(k)
        if not crear:
            return None
        n = sum(1 for k, d in self.E.items() if d.get("clase") == cl and d.get("dueno") == du and d.get("orden")) + 1
        eid = self._ent(f"I:{cl}#{orden}@{du}", clase=cl, dueno=du, gen=g or "m", orden=orden)
        self._rel(cl, eid, du, fr["src"], g or "m")
        if fr.get("nos") and du == "U":
            pareja = [r["x"] for r in self.rels("esposo", y="U")]
            if len(pareja) == 1:
                self._rel(cl, eid, pareja[0], fr["src"], g or "m")
        self.E[eid]["t_nuevo"] = self.turno
        self.ult_nuevo = eid
        return eid

    # ------------------------------------------------------------------ relaciones
    def _rel(self, r, x, y, src, g=""):
        x, y = self.can(x), self.can(y)
        if g and not self.E.get(x, {}).get("gen"):
            self.E.setdefault(x, {})["gen"] = g
        for q in self.R:
            if q["r"] == r and self.can(q["x"]) == x and self.can(q["y"]) == y:
                return False
        self.R.append({"r": r, "x": x, "y": y, "src": src, "t": self.turno})
        return True

    def _base(self, r):
        return [(self.can(q["x"]), self.can(q["y"]), q) for q in self.R if q["r"] == r]

    def _frase_rel(self, r, x, y):
        nom = self._acento(self._rel_nombre(r, self.gen(x)))
        if x == "U":
            return contrae(f"eres {self._art(nom, self.gen(x))} {nom} de {self.disp(y)}")
        if y == "U":
            return f"{self.disp(x)} es tu {nom}"
        return contrae(f"{self.disp(x)} es {self._art(nom, self.gen(x))} {nom} de {self.disp(y)}")

    @staticmethod
    def _art(nom, g):
        return "la" if g == "f" else "el"

    def pares(self, r, prof=0):
        """[(x, y, [justificación])] : x es r de y, con lo dicho y lo deducible."""
        out, visto = [], set()

        def add(x, y, j):
            if x != y and (x, y) not in visto:
                visto.add((x, y)); out.append((x, y, j))
        for x, y, q in self._base(r):
            add(x, y, [self._frase_rel(r, x, y)])
        if r in SIMETRICAS:
            for x, y, q in self._base(r):
                add(y, x, [self._frase_rel(r, x, y)])
        if r in INVERSAS:
            for x, y, q in self._base(INVERSAS[r]):
                add(y, x, [self._frase_rel(INVERSAS[r], x, y)])
        if prof > 2:
            return out
        if r == "padre":
            for x, y, q in self._base("hijo"):
                add(y, x, [self._frase_rel("hijo", x, y)])
        elif r == "hijo":
            for x, y, q in self._base("padre"):
                add(y, x, [self._frase_rel("padre", x, y)])
        elif r == "hermano":
            pa = self.pares("padre", prof + 1)
            for p, a, j1 in pa:
                for p2, b, j2 in pa:
                    if p == p2 and a != b:
                        add(a, b, j1 + j2)
        elif r == "abuelo":
            pa = self.pares("padre", prof + 1)
            for x, y, j1 in pa:
                for y2, z, j2 in pa:
                    if y == y2:
                        add(x, z, j1 + j2)
            for x, y, q in self._base("nieto"):
                add(y, x, [self._frase_rel("nieto", x, y)])
        elif r == "nieto":
            for x, z, j in self.pares("abuelo", prof + 1):
                add(z, x, j)
        elif r == "tio":
            he, pa = self.pares("hermano", prof + 1), self.pares("padre", prof + 1)
            for x, y, j1 in he:
                for y2, z, j2 in pa:
                    if y == y2 and x != z:
                        add(x, z, j1 + j2)
            for x, y, q in self._base("sobrino"):
                add(y, x, [self._frase_rel("sobrino", x, y)])
        elif r == "sobrino":
            for x, z, j in self.pares("tio", prof + 1):
                add(z, x, j)
        elif r == "primo":
            he, pa = self.pares("hermano", prof + 1), self.pares("padre", prof + 1)
            for p, a, j1 in pa:
                for q_, b, j2 in pa:
                    if p != q_ and a != b:
                        for h1, h2, j3 in he:
                            if h1 == p and h2 == q_:
                                add(a, b, j1 + j2 + j3)
        elif r == "bisabuelo":
            ab, pa = self.pares("abuelo", prof + 1), self.pares("padre", prof + 1)
            for x, y, j1 in pa:
                for y2, z, j2 in ab:
                    if y == y2:
                        add(x, z, j1 + j2)
        elif r == "suegro":
            es, pa = self.pares("esposo", prof + 1), self.pares("padre", prof + 1)
            for x, y, j1 in pa:
                for y2, z, j2 in es:
                    if y == y2:
                        add(x, z, j1 + j2)
        elif r == "cuñado":
            es, he = self.pares("esposo", prof + 1), self.pares("hermano", prof + 1)
            for x, y, j1 in he:
                for y2, z, j2 in es:
                    if y == y2 and x != z:
                        add(x, z, j1 + j2); add(z, x, j1 + j2)
        return out

    def rels(self, r, x=None, y=None):
        x = self.can(x) if x else None
        y = self.can(y) if y else None
        return [{"x": a, "y": b, "j": j} for a, b, j in self.pares(r) if (x is None or a == x) and (y is None or b == y)]

    # ------------------------------------------------------------------ clases / herencia
    def _persona_por_rol(self, e):
        if e == "U" or self.es_persona(e):
            return True
        cl = sa(self.E.get(e, {}).get("clase") or "")
        if not cl:
            return False
        roles = {r for g in KB.kb()["grupos"].values() for r in g} | PERSONA_CLS
        masc = cl[:-1] + "o" if cl.endswith("a") else cl
        return cl in roles or masc in roles or "persona" in KB.ancestros(KB._kb_clase(cl) or "")

    def clases(self, e, con_just=False):
        """Cadena de clases de e: [(clase, justificación)] con lo dicho por la persona y la semilla de fábrica."""
        e = self.can(e)
        out, visto, cola = [], set(), []
        d = self.E.get(e, {})
        if e.startswith("K:"):
            cola.append((d.get("clase") or e[2:], []))
            visto.add(cola[0][0])
        else:
            if d.get("clase"):
                cola.append((d["clase"].split(" ")[0] if d["clase"] not in self._clases_conocidas() else d["clase"], [f"{self.disp(e)} es {self._un_g(d['clase'], self.gen(e))}"]))
            for f in self.F:
                if f["v"] == "ser" and self.can(f["s"]) == e and f.get("vig", True) and not f.get("neg"):
                    for c in f.get("isa", []):
                        cola.append((c, [self.frase(f)]))
                    for a_ in f.get("attr", []):         # 2.15: «es enfermera», «es boxeador»: el oficio o el papel también es su clase
                        ca = KB._kb_clase(a_)
                        if ca and ca not in [x for x, _ in cola] and "persona" in KB.ancestros(ca) and not f.get("grado") \
                                and set(KB.kb()["isa"].get(ca, [])) != {"persona"}:   # «es muy trabajador» es una cualidad, no un oficio
                            cola.append((ca, [self.frase(f)]))
            for c, j in cola:
                visto.add(c)
            # 2.15: quien entra en la charla por una relación entre personas (tía, jefa, vecino) o es persona por cómo se habla de ella, es una persona
            if "persona" not in visto and e not in ("L",) and self._persona_por_rol(e):
                rol = d.get("clase") or ""
                just = [f"{self.disp(e)} es una persona" + (f" (se habla de {'ella' if self.gen(e) == 'f' else 'él'} como «{self._rel_nombre(rol, self.gen(e)) if hasattr(self, '_rel_nombre') else rol}»)" if rol else "")] if e != "U" else ["eres una persona"]
                cola.append(("persona", just)); visto.add("persona")
            out.extend(cola)
        while cola:
            c, j = cola.pop(0)
            for f in self.F:
                if f["v"] == "ser" and self.can(f["s"]) == "K:" + c and f.get("vig", True) and not f.get("neg"):
                    for c2 in f.get("isa", []):
                        if c2 not in visto:
                            visto.add(c2); it = (c2, j + [self.frase(f)]); out.append(it); cola.append(it)
            for c2 in self._semilla_isa(c):
                if c2 not in visto:
                    visto.add(c2); it = (c2, j + [f"{self._un(c, M.genero_sust(c))} es {self._un(c2, M.genero_sust(c2))}"]); out.append(it); cola.append(it)
            for c2 in KB.kb()["isa"].get(c, []):
                if c2 not in visto:
                    paso = f"{KB.un(c)} es {KB.un(c2)}"
                    self._pasos_fab.add(paso)
                    visto.add(c2); it = (c2, j + [paso]); out.append(it); cola.append(it)
        return out

    def _clases_conocidas(self):
        return {d.get("clase") for d in self.E.values() if d.get("clase")}

    def _un_g(self, c, g):
        """«una gata» para una entidad femenina de clase «gato»; «una profesora»…"""
        if g == "f" and M.genero_sust(c) == "m" and " " not in c:
            if c in REL_DISP_BASE or c in FAMILIA:
                return "una " + self._acento(self._rel_nombre(c, "f"))
            if c.endswith("o"):
                return "una " + self._acento(c[:-1] + "a")
            if c.endswith(("or", "on", "in")) and c not in K_EPICENOS:
                return "una " + self._acento(sa(c)) + "a"
        return self._un(c, g)

    def _un(self, c, g):
        return ("una " if g == "f" else "un ") + self._acento(c)

    def _semilla_isa(self, c):
        out = []
        C = sa(c).upper().replace(" ", "_")
        for f in getattr(self.mem, "facts", []):
            if f.get("p") == "ES" and not f.get("neg") and not f.get("archived") and sa(f.get("s", "")).upper() == C:
                out.append(sa(f["o"]).lower().replace("_", " "))
        return out

    def es_clase(self, e, c, lexico_ok=False):
        """(True, just) si e pertenece a la clase c."""
        cs = self.clases(e)
        for c2, j in cs:
            if c2 == c:
                return True, j
        if lexico_ok:
            try:
                from src.language import lexico
                e = self.can(e)
                base = [self.E.get(e, {}).get("clase") or (e[2:] if e.startswith("K:") else "")] + [c2 for c2, _ in cs]
                for b in base:
                    if b and " " not in b and lexico.es_un_tipo_de(b, c, 12):
                        return True, [f"{self._un(b, M.genero_sust(b))} es un tipo de {self._acento(c)} (diccionario de conceptos)"]
            except Exception:                                                 # noqa
                pass
        return False, []

    # ------------------------------------------------------------------ marcos
    def _nuevo(self, **kw):
        f = {"v": "", "s": None, "neg": False, "refl": False, "t": "pres", "attr": [], "isa": [], "grado": "", "obj": None, "obj_disp": "", "obj_cls": "", "cuant": None, "comps": [],
             "cuando": "", "freq": "", "modo": [], "xinf": "", "exp": False, "src": "", "turno": self.turno, "vig": True, "lugar_adv": "", "comp": None, "pl_obj": False, "causa": ""}
        f.update(kw)
        return f

    def marcos(self, v=None, s=None, vig=True, neg=None, herencia=False):
        v = V_EQ.get(v, v)
        ss = None
        if s is not None:
            s = self.can(s)
            ss = {s: []}
            if herencia:
                for c, j in self.clases(s):
                    ss.setdefault("K:" + c, j)
        out = []
        for f in (self.F + self.fabrica() if ss is not None else self.F):
            if f.get("erroneo"):
                continue                               # corregido por la persona: no fue verdad nunca
            if v is not None and V_EQ.get(f["v"], f["v"]) != v:
                continue
            fs = self.can(f["s"]) if f["s"] else None
            if ss is not None and fs not in ss:
                continue
            if vig is not None and bool(f.get("vig", True)) != vig:
                continue
            out.append(f)
        if ss is not None and len(ss) > 1:
            # la clase más cercana manda: una excepción («un pingüino no vuela») tapa la regla general («las aves vuelan»)
            rango = {k: i for i, k in enumerate(ss)}
            out.sort(key=lambda f: rango.get(self.can(f["s"]), 99))
            visto, limpio = {}, []
            for f in out:
                if not f.get("vig", True):
                    limpio.append(f); continue
                r = rango.get(self.can(f["s"]), 99)
                k = self._clave_prop(f)
                if k in visto and (visto[k][2] or (visto[k][0] < r and visto[k][1] != bool(f.get("neg")))):
                    continue                           # manda la excepción cercana o lo que la persona dijo solo de «algunos»
                visto.setdefault(k, (r, bool(f.get("neg")), bool(f.get("parcial"))))
                limpio.append(f)
            out = limpio
        if neg is not None:
            out = [f for f in out if bool(f.get("neg")) == neg]
        return out

    @staticmethod
    def _clave_prop(f):
        return (V_EQ.get(f["v"], f["v"]), f.get("obj_cls") or "", tuple(sorted(f.get("attr", []))), tuple((p_, d_ or "") for p_, e_, d_ in f.get("comps", []) if not e_))

    def fabrica(self):
        if self._fab is None:
            try:
                self._fab = KB.marcos_fabrica(self._nuevo)
            except Exception:                                                 # noqa
                self._fab = []
        return self._fab

    def _persona_de(self, e, pl=False):
        e = self.can(e) if e else None
        if e == "U":
            return "2s"
        if e == "L":
            return "1s"
        if pl or (e and self.E.get(e, {}).get("pl")):
            return "3p"
        return "3s"

    def frase(self, f, tiempo=None, sin_sujeto=False, antes=False):
        """Verbaliza un marco como oración (sin punto final)."""
        if f.get("posible") and not getattr(self, "_en_disy", False):
            gid = f["posible"]                          # 2.11: una alternativa nunca se dice sola: «X o Y»
            prin = {}
            for x in self.F:
                if x.get("posible") == gid and x.get("vig", True) and x.get("alt") not in prin:
                    prin[x.get("alt")] = x
            if prin:
                from . import conectores
                self._en_disy = True
                try:
                    textos = [self.frase(x, tiempo, sin_sujeto, antes) for _, x in sorted(prin.items(), key=lambda kv: kv[0] or 0)]
                finally:
                    self._en_disy = False
                self._uso_posible = True
                return conectores.une_o(textos)
        s = self.can(f["s"]) if f["s"] else None
        t = tiempo or f.get("t", "pres")
        if t == "cond":
            t = "pres"
        v = f["v"]
        partes = []
        if f.get("dicho") and s == "U" and f.get("comps") and f["comps"][0][0] == "a" and (f.get("obj_disp") or "").startswith("que "):
            dest = cambia_persona(f["comps"][0][2]) if f["comps"][0][2] else self.disp(f["comps"][0][1])
            pl_d = bool(self.E.get(self.can(f["comps"][0][1] or ""), {}).get("pl"))
            return contrae(f"{'les' if pl_d else 'le'} {M.conjugar(v, t, '2s')} a {dest} {f['obj_disp']}")   # «le dijiste a tu hermano que lo deje»
        if f.get("exp"):
            pl = bool(f.get("pl_obj"))
            if s == "U":
                partes.append("te")
            elif s == "L":
                partes.append("me")
            else:
                partes = ["a", self.disp(s), "le" if not self.E.get(s, {}).get("pl") else "les"]
            if f.get("se_dat"):
                partes.insert(len(partes) - 1, "se")      # «se te rompió el móvil», «a tu abuela se le murió el gato»
            if f.get("neg"):
                partes.insert(len(partes) - (2 if f.get("se_dat") else 1), "no")
            partes.append(M.conjugar(v, t, "3p" if pl else "3s"))
            partes.extend(f.get("modo", []))
        else:
            if s and s not in ("U", "L") and not sin_sujeto:
                partes.append(KB.suj(s[2:]) if f.get("fab") else (cambia_persona(f["suj_txt"]) if f.get("suj_txt") else self.disp(s)))
            if f.get("neg") and not (s and self.E.get(s, {}).get("nadie") and not sin_sujeto):
                partes.append("nunca" if f.get("freq") == "nunca" else "no")
            if f.get("refl"):
                partes.append({"2s": "te", "1s": "me", "3p": "se", "3s": "se"}[self._persona_de(s, f.get("pl_suj"))])
            if f.get("clit_obj") and f.get("obj") in ("U", "L"):
                partes.append("te" if self.can(f["obj"]) == "U" else "me")      # «Lola te invitó a su boda»
            if f.get("modal") == "tener que":
                partes.append(M.conjugar("tener", t, self._persona_de(s, f.get("pl_suj"))) + " que")
            else:
                partes.append(M.conjugar(v, t, self._persona_de(s, f.get("pl_suj"))))
        if f.get("grado"):
            partes.append(f["grado"])
        if f.get("attr"):
            g = self.gen(s) if s else "m"
            pl = bool(s and self.E.get(s, {}).get("pl")) or bool(f.get("pl_suj"))
            usados = {x for xs in f.get("isa_adj", {}).values() for x in xs}
            aa = [self._attr_disp(a, f, g, pl) for a in f["attr"] if a not in usados or a in f.get("isa", [])]
            partes.append(self._lista(aa))
        if f.get("comp"):
            op, adj, e2 = f["comp"]
            g = self.gen(s) if s else "m"
            partes.append(({"mas": "más", "menos": "menos", "tan": "tan"}[op] + " " if adj not in ("mayor", "menor", "mejor", "peor") else "") + (self._acento(M.concuerda(adj, g) if v in ("ser", "estar", "parecer", "quedar", "sentir") else adj) if hasattr(self, "_acento") else M.concuerda(adj, g)) + (" como " if op == "tan" else " que ") + self.disp(e2))
        if f.get("obj_disp"):
            od_ = cambia_persona(f["obj_disp"]).replace(" y ", " ni ") if f.get("neg") else cambia_persona(f["obj_disp"])
            o_e = self.can(f.get("obj") or "")
            if o_e and o_e not in ("U", "L") and not o_e.startswith("K:") and v not in ("ser", "estar", "tener", "parecer", "haber") and not (v == "llamar" and f.get("refl")) and not f.get("exp") \
                    and self.es_persona(o_e) and not re.match(r"^(?:a|al)\s", od_) and not f.get("dicho") \
                    and (not o_e.startswith("N:") or self.E.get(o_e, {}).get("clase") or self.E.get(o_e, {}).get("src_nombre") or any(
                        self.can(r_["x"]) == o_e for r_ in self.R)):   # «estudias Derecho»: un nombre propio sin más datos no es por fuerza una persona
                od_ = contrae("a " + od_)                # «llevarás a Hugo al pediatra»: complemento directo de persona
            partes.append(od_)
        if f.get("xinf"):
            partes.append(cambia_persona(f["xinf"]))
        grupos_c = []                                   # 2.12: «a Escocia, Irlanda y Noruega»: mismos complementos, una lista
        for p, e, d in f.get("comps", []):
            txt_c = cambia_persona(d) if d else self.disp(e)
            if len(re.findall(r"\s(?:y|e)\s", txt_c)) >= 2:
                trozos_c = re.split(r"\s(?:y|e)\s", txt_c)
                txt_c = self._lista(trozos_c)
            pers_c = bool(e) and (str(e).startswith("N:") or self.es_persona(e))
            # 2.16: «lleva a Noa a clase de piano»: una persona y un sitio con la misma preposición no son una lista (hacen papeles distintos)
            if grupos_c and grupos_c[-1][0] == p and grupos_c[-1][2] == pers_c:
                grupos_c[-1][1].append(txt_c)
            else:
                grupos_c.append((p, [txt_c], pers_c))
        for p, txts, _pc in grupos_c:
            partes.append({"despues_de": "después de", "detras_de": "detrás de", "segun": "según"}.get(p, p.replace("_", " ")) + " " + self._lista(txts))
        if f.get("lugar_adv"):
            partes.append(f["lugar_adv"].replace("aqui", "aquí").replace("alli", "allí").replace("alla", "allá").replace("ahi", "ahí"))
        if not f.get("exp"):
            partes.extend(f.get("modo", []))
        if f.get("freq") and f.get("freq") != "nunca":
            partes.append(f["freq"])
        if f.get("cuando") and not antes and f["cuando"] not in ("ahora", "actualmente", "ya"):
            partes.append(f["cuando"])
        out = contrae(" ".join(x for x in partes if x))
        if antes:
            out = "antes " + out
        return out

    def _attr_disp(self, a, f, g, pl):
        if f.get("isa_txt") and a in f.get("isa", []):
            return cambia_persona(f["isa_txt"])
        if a in f.get("isa", []):
            nom = a
            if g == "f" and (a in getattr(self, "_profesiones", lambda: set())() or a in REL_DISP_BASE):
                nom = self._rel_nombre(a, "f") if (a.endswith("o") or a in ("profesor", "doctor", "pintor", "escritor", "actor")) else a
                if nom == a and a.endswith(("or",)):
                    nom = a + "a"
                if a == "actor":
                    nom = "actriz"
            adjs = f.get("isa_adj", {}).get(a, [])
            if adjs:
                nom = nom + " " + " ".join(self._acento(M.concuerda(x, g, pl)) for x in adjs)
            art = f.get("isa_art", {}).get(a, "")
            if art:
                art = ("una" if M.genero_sust(nom) == "f" or g == "f" and nom != a else "un") if not pl else ""
                if g == "f" and nom == a and M.genero_sust(a) == "m":
                    art = "un"
            return (art + " " + self._acento(sa(M.plural(nom)) if pl else nom)).strip()
        return self._acento(M.concuerda(a, g, pl))

    _AC = {"simpatico": "simpático", "simpatica": "simpática", "rapido": "rápido", "rapida": "rápida", "facil": "fácil", "dificil": "difícil", "marron": "marrón", "debil": "débil", "frio": "frío",
           "fria": "fría", "vacio": "vacío", "vacia": "vacía", "timido": "tímido", "timida": "tímida", "comodo": "cómodo", "comoda": "cómoda", "medico": "médico", "medica": "médica",
           "electrico": "eléctrico", "electrica": "eléctrica", "util": "útil", "feliz": "feliz", "jovenes": "jóvenes", "antipatico": "antipático", "antipatica": "antipática", "ingles": "inglés",
           "frances": "francés", "aleman": "alemán", "japones": "japonés", "pequeno": "pequeño", "economico": "económico", "practico": "práctico", "practica": "práctica", "unico": "único",
           "tipico": "típico", "magico": "mágico", "magica": "mágica", "fantastico": "fantástico", "fantastica": "fantástica", "simpaticos": "simpáticos", "simpaticas": "simpáticas"}

    def _acento(self, w):
        if " " in w:
            return " ".join(self._acento(x) for x in w.split())
        if w in self.pal:
            return self.pal[w]
        if w in self._AC:
            return self._AC[w]
        fk = KB.kb()["forma"].get(w)
        if fk:
            return fk
        try:
            d = self.mem.display.get(w.upper())
            if d and sa(d) == w and (d == d.lower() or ("N:" + w) in self.E):
                return d
        except Exception:                                                     # noqa
            pass
        return w

    def anota_palabras(self, T):
        for t in T:
            for forma in (t.f.lower(), getattr(t, "lo", "")):
                if forma and forma != sa(forma) and " " not in forma:
                    self.pal.setdefault(sa(forma), forma)

    @staticmethod
    def _lista(xs):
        xs = list(dict.fromkeys(x for x in xs if x))       # 2.11: una disyunción dicha dos veces es la misma
        if len(xs) <= 1:
            return "".join(xs)
        ult = xs[-1]
        conj = "e" if re.match(r"h?i(?![aeou])", sa(ult)) else "y"
        return ", ".join(xs[:-1]) + f" {conj} " + ult

    # ------------------------------------------------------------------ espejo en la memoria clásica
    def _clave_legado(self, e):
        e = self.can(e)
        if e == "U":
            return (self.usuario.get("nombre") or "USUARIO").upper().replace(" ", "_")
        d = self.E.get(e, {})
        if e.startswith("N:"):
            return sa(d.get("nombre") or e[2:]).upper().replace(" ", "_")
        cl = sa(d.get("clase") or e.split(":", 1)[1].split("@")[0]).upper().replace(" ", "_")
        if e.startswith("I:") and d.get("dueno"):
            return cl + "_DE_" + self._clave_legado(d["dueno"])
        return cl

    def _espejo(self, f, quitar=False):
        try:
            s = self._clave_legado(f["s"])
            filas = []
            v = sa(f["v"]).upper()
            for a in f.get("attr", []):
                filas.append((s, "ES" if a in f.get("isa", []) else v, sa(a).upper().replace(" ", "_")))
            if f.get("obj"):
                o = self._clave_legado(f["obj"])
                oe = self.can(f["obj"])
                if oe.startswith("I:") and self.can(self.E.get(oe, {}).get("dueno") or "") == self.can(f["s"]) and f.get("obj_cls"):
                    o = sa(f["obj_cls"]).upper().replace(" ", "_")
                if f.get("cuant") is not None and f.get("obj_cls"):
                    o = sa(f.get("obj_disp", "")).upper().replace(" ", "_") or o
                filas.append((s, v, o) if not f.get("exp") else (o, v + "_A", s))
            for p, e, d in f.get("comps", []):
                if e:
                    filas.append((s, v + "_" + sa(p).upper(), self._clave_legado(e)))
            for tr in filas:
                if quitar:
                    self.mem.forget_fact(tr)
                else:
                    self.mem.add_fact(tr, source=f.get("src") or "usuario", neg=bool(f.get("neg")), when=sa(f.get("cuando", "")) if f.get("cuando") else "", when_disp=f.get("cuando", ""))
                    if f["s"] and self.can(f["s"]) != "U":
                        self.mem.display.setdefault(tr[0], self.disp(f["s"]))
        except Exception:                                                     # noqa
            pass
