"""LCM 2.0 · preguntas sobre el grafo: sí/no, quién, qué, dónde, cuándo, cuánto, cómo, cuál y por qué."""
from __future__ import annotations

import datetime as dt
import re
from typing import Optional

from . import conceptos as KB
from . import morfo as M
from .morfo import sa
from . import lengua as G
from . import preposiciones as P
from .lengua import SN, Clausula
from .nucleo import (REL_DISP_BASE, REL_CANON, FAMILIA, SIMETRICAS, INVERSAS, PERSONA_CLS, FUNCIONAL, FUNC_SIEMPRE, V_EQ, COLORES, _ANT, _cap, contrae, cambia_persona)

INTRANS = {"vivir", "dormir", "trabajar", "correr", "nadar", "llegar", "salir", "venir", "ir", "estar", "ser", "volar", "caminar", "viajar", "llorar", "reir", "sonreir", "bailar", "cantar", "ladrar",
           "maullar", "morir", "nacer", "crecer", "existir", "funcionar", "descansar", "pasear", "jugar", "estudiar", "madrugar", "roncar", "toser", "respirar", "entrar", "volver", "residir"}
UNICAS = {("padre", "m"), ("padre", "f"), ("esposo", ""), ("esposo", "m"), ("esposo", "f"), ("novio", "m"), ("novio", "f"), ("novio", ""), ("jefe", ""), ("jefe", "m"), ("jefe", "f"), ("capital", ""),
          ("dueño", ""), ("color favorito", ""), ("mejor amigo", ""), ("mejor amigo", "f"), ("mejor amigo", "m")}


def _tiene_propios_v(nuc, s, v):
    return any(f.get("s") and nuc.can(f["s"]) == s and f["v"] == v for f in nuc.F)


_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


class Preguntador:
    # ================================================================== utilidades
    def _fin(self, s):
        s = _cap(contrae(s))
        return s if s.endswith((".", "?", "!")) else s + "."

    def _porque(self, j):
        j = [x for x in dict.fromkeys(j) if x]
        return "porque " + self._lista(j) if j else ""

    def _de(self, e):
        """«de Ana» / «de ti» para mensajes."""
        e = self.can(e)
        return "de ti" if e == "U" else contrae("de " + self.disp(e))

    def _se_de(self, e, n=2, excluye=()):
        ps = [x for x in self._datos(e, sin_sujeto=True) if x not in excluye][:n]
        if not ps:
            return ""
        quien = "De ti" if self.can(e) == "U" else contrae("De " + self.disp(e))
        return f"{quien} sé que {self._lista(ps)}."

    def _datos(self, e, sin_sujeto=False):
        e = self.can(e)
        out = []
        if e == "U" and self.usuario.get("nombre"):
            out.append(f"te llamas {self.usuario['nombre']}")
        for q in self.R:
            x, y = self.can(q["x"]), self.can(q["y"])
            if x == e and not x.startswith("I:"):
                fr = self._frase_rel(q["r"], x, y)
                out.append(fr.split(" ", 1)[1] if (sin_sujeto and x != "U" and fr.startswith(self.disp(x) + " ")) else fr)
        for f in self.F:
            if self.can(f["s"]) == e and f.get("vig", True) and not f.get("efecto"):
                out.append(self.frase(f, sin_sujeto=sin_sujeto and not f.get("exp")))
        for q in self.R:
            x, y = self.can(q["x"]), self.can(q["y"])
            if y == e and x.startswith("N:"):
                out.append(self._frase_rel(q["r"], x, y))
        return list(dict.fromkeys(out))

    def resumen(self, e):
        ps = self._datos(e)
        if not ps:
            return None
        return " ".join(self._fin(x) for x in ps[:7])

    def _q_ent(self, s: SN):
        if s is None:
            return None
        e = self.ent_de(s, crear=False)
        if isinstance(e, list):
            return [self.can(x) for x in e]
        if (e is None or (isinstance(e, str) and e.startswith("?"))) and s.cab and s.de is not None and s.de.propio:
            comp = sa(s.cab + " de " + s.de.texto).lower()   # «¿Cuándo es la cena de Navidad?» con «la cena de Navidad de la empresa»
            cands = [k for k, d in self.E.items() if k not in self.eq and sa(d.get("clase") or "").lower() == comp]
            if len(cands) == 1:
                return cands[0]
        if isinstance(e, str) and e.startswith("?I:") and s.pos == "U":
            # «mi trabajo nuevo» cuando solo se dijo «empiezo en un trabajo nuevo»: el que la persona nombró
            cl = e[3:].split("@", 1)[0]
            for k in ("K:" + cl, "K:" + cl.split()[0]):
                if k in self.E and any(f.get("s") == "U" and (self.can(f.get("obj") or "") == k or any(self.can(c_[1] or "") == k for c_ in f.get("comps", []))) for f in self.F):
                    return k
        return e

    def _conocido(self, e):
        if e is None or (isinstance(e, str) and e.startswith("?")):
            return False
        e = self.can(e)
        if e in ("U", "L"):
            return True
        return any(self.can(f["s"]) == e or self.can(f.get("obj") or "") == e or any(c_[1] and self.can(c_[1]) == e for c_ in f.get("comps", [])) for f in self.F) \
            or any(self.can(q["x"]) == e or self.can(q["y"]) == e for q in self.R)

    def _no_conozco(self, s: SN, e=None):
        if s is not None and s.propio:
            return self._abst(f"No sé quién es {s.nombre}: todavía no me has hablado de {'ella' if M.genero_nombre(s.nombre) == 'f' else 'él'}.", consultar=True)
        if isinstance(e, str) and e.startswith("?I:"):
            cl, du = e[3:].split("@", 1)
            g = M.genero_sust(cl)
            pos = "tu" if du == "U" else None
            if s is not None and s.cab and not s.coord:
                cl = s.cab + (" " + " ".join(s.adjs) if s.adjs else ""); g = s.gen or M.genero_sust(s.cab)
                cl = self._acento(cl)
            nom = f"{pos} {cl}" if pos else contrae(f"{'la' if g == 'f' else 'el'} {cl} de {self.disp(du)}")
            return self._abst(f"No sé nada de {nom}: no me has hablado de {'ella' if g == 'f' else 'él'}.", consultar=False)
        return self._abst("No lo sé.", consultar=True)

    def _sin(self, a, b, pos="n"):
        """a y b nombran el mismo concepto (alias de fábrica o sinónimos del léxico)."""
        if a == b:
            return True
        try:
            al = {sa(k).lower(): sa(v).lower() for k, v in self.mem.alias.items()}
            if al.get(a, a) == al.get(b, b):
                return True
            from src.language import lexico
            return b in {sa(x) for x in lexico.sinonimos(a, pos)} and a in {sa(x) for x in lexico.sinonimos(b, pos)}
        except Exception:                                                     # noqa
            return False

    def _adjs_casan(self, f, o: SN):
        """2.16: «¿tiene el pelo corto?» no se contesta con «tiene el pelo largo». -> True casa · False no consta · "contrario" dice lo opuesto."""
        adjs = [sa(a) for a in (getattr(o, "adjs", None) or []) if sa(a) not in ("vivo", "viva")]
        if not adjs:
            return True
        if not f.get("obj_disp"):
            return None
        raiz = lambda w: re.sub(r"(?:os|as|o|a|es|s)$", "", sa(w))   # noqa: E731
        dichos = [sa(w) for w in re.findall(r"[\wáéíóúñü]+", f["obj_disp"].lower())][1:]
        fo = self.can(f["obj"]) if f.get("obj") else None
        if fo:                                           # «el pelo de tu perro es largo» también cuenta
            for g in self.F:
                if g["v"] in ("ser", "estar") and g.get("s") and self.can(g["s"]) == fo and not g.get("neg"):
                    dichos += [sa(a) for a in g.get("attr", [])]
        dichos = [w for w in dichos if w not in ("de", "del", "la", "el", "los", "las", "mi", "tu", "su")]
        if not dichos:
            return None                                  # del objeto no se ha dicho cómo es
        rd = {raiz(w) for w in dichos}
        if all(raiz(a) in rd for a in adjs):
            return True
        ant = KB.kb()["ant"]
        for a in adjs:
            for cand in (a, re.sub(r"a$", "o", a), re.sub(r"as$", "o", a), re.sub(r"os$", "o", a), re.sub(r"es$", "", a), re.sub(r"s$", "", a)):
                if any(raiz(x) in rd for x in ant.get(cand, [])):
                    return "contrario"
        return False

    def _coincide_obj(self, f, o: SN):
        if o is None:
            return True
        if o.coord:
            return any(self._coincide_obj(f, x) for x in o.coord)
        if self._adjs_casan(f, o) is not True and f.get("v") not in ("ser", "estar", "llamar"):
            return False
        qe = self._q_ent(o)
        fo = self.can(f["obj"]) if f.get("obj") else None
        if qe and not isinstance(qe, list) and not qe.startswith(("K:", "?")) and fo == qe:
            return True
        cl = self._clase_sn(o)[0] if o.cab else ""
        if cl and (f.get("obj_cls") == cl or (" " not in cl and str(f.get("obj_cls") or "").startswith(cl + " "))):
            return True                                 # «hermana pequeña» es una hermana
        if cl and f.get("obj_cls") and " " not in cl and self._sin(cl, f["obj_cls"]):
            return True
        if cl and f.get("obj_cls") and KB._kb_clase(cl) and KB.kb()["hijos"].get(KB._kb_clase(cl)) and self._de_clase(f, KB._kb_clase(cl)):
            return True                                 # 2.15: lo dicho de una manzana contesta a lo que se pregunta de «fruta» (la clase contiene al objeto)
        if cl and fo and self.E.get(fo, {}).get("clase") == cl:
            return True
        if cl and fo and not fo.startswith("K:") and self.es_clase(fo, cl)[0]:
            return True
        if cl and fo and fo.startswith("K:") and self.es_clase(fo, cl)[0]:
            return True
        if o.propio and fo == "N:" + o.cab:
            return True
        return False

    def _coincide_comps(self, f, comps):
        for p, s in comps:
            qe = self._q_ent(s)
            ok = False
            for p2, e2, d2 in f.get("comps", []):
                if p2 != p and not ({p, p2} <= {"en", "a"} and False):
                    continue
                if qe and not isinstance(qe, list) and e2 and self.can(e2) == self.can(qe):
                    ok = True
                elif s.cab and re.search(r"(?<!\w)" + re.escape(s.cab) + r"(?!\w)", sa(d2 or "")):
                    ok = True
                elif s.cab and e2 and self.E.get(self.can(e2), {}).get("clase") == self._clase_sn(s)[0]:
                    ok = True
            if not ok:
                return False
        return True

    def _tiempo_ok(self, f, C):
        if C.cuando and sa(C.cuando) not in sa(f.get("cuando", "")) and sa(C.cuando) not in ("ahora", "actualmente", "antes", "ya", "hoy") :
            a, b = self._intervalo(C.cuando), self._intervalo(f.get("cuando", ""))
            if not (a and b and a.split("/")[0] <= b.split("/")[0] and b.split("/")[1] <= a.split("/")[1]) and not (a and b and b.split("/")[0] <= a.split("/")[0] and a.split("/")[1] <= b.split("/")[1]):
                return False
        if C.freq and C.freq != "nunca" and sa(C.freq) != sa(f.get("freq", "")):
            return False
        return True

    def _sujeto_preg(self, C: Clausula, wh=None):
        """(entidad sujeto | None, SN objeto) con verbo antepuesto y sujeto pospuesto."""
        if C.suj is not None:
            return self._q_ent(C.suj), C.suj, C.obj
        if C.pers in ("1s", "1p"):
            return "U", None, C.obj
        if C.pers == "2s":
            return "L", None, C.obj
        o, o2 = C.obj, C.obj2
        if C.v == "llamar" and C.refl and o is not None and not o.propio and (o.pos or o.det or o.de is not None):
            return self._q_ent(o), o, None              # «¿Cómo se llamaba mi marido?»: el sujeto va detrás
        if C.amb1 and o is None and ("me" in C.clit or not self.ult_suj):
            return "U", None, None
        if C.amb1 and C.suj is None and (getattr(self, "_afirma_de", None) == "U" or any(f["v"] == C.v and f["s"] == "U" and f.get("t") == C.tiempo for f in self.F)) \
                and not any(f["v"] == C.v and f["s"] not in ("U", "L") and f.get("t") == C.tiempo for f in self.F):
            return "U", None, o                         # «¿Dónde tenía las llaves?»: «tenía» es yo (lo último que contó era de sí)
        cop = C.v in G.COPULAS
        if o is not None:
            if cop and o2 is not None and not o.coord and not o.det and not o.propio and not o.pos and o.de is None and not o.pron and (o2.propio or o2.det or o2.pos or o2.pron or o2.coord):
                # «¿Está contenta Ana?», «¿Es médico tu hermano?»: el primero es el atributo
                if C.v in ("estar", "parecer"):
                    C.attr = [M.masc(o.cab)]; C.obj, C.obj2 = None, None
                    return self._q_ent(o2), o2, None
                C.obj, C.obj2 = o, None
                return self._q_ent(o2), o2, o
            if cop:
                if o2 is not None or C.attr or C.comps or C.comp or C.lugar_adv or C.modo or wh:
                    C.obj, C.obj2 = o2, None
                    return self._q_ent(o), o, o2
                if o.adjs and not o.propio:
                    C.attr = [o.adjs.pop()]
                    C.obj = None
                    return self._q_ent(o), o, None
                return None, None, o
            if o2 is not None:
                if not o.coord and not o.det and not o.propio and not o.pos and not o.pron and o.de is None and (o2.propio or o2.pron or o2.det == "d" or o2.pos or (o2.coord and all(x.propio for x in o2.coord))):
                    C.obj, C.obj2 = o, None          # «¿Come carne Toby?»: objeto antes que sujeto
                    return self._q_ent(o2), o2, o
                C.obj, C.obj2 = o2, None
                return self._q_ent(o), o, o2
            es_suj = o.propio or bool(o.pron)
            if not es_suj and wh in ("que", "cuanto", "cual"):
                es_suj = True
            if not es_suj and (o.det == "d" or o.pos or o.de is not None):
                qe = self._q_ent(o)
                pers = isinstance(qe, str) and not qe.startswith("?") and self.es_persona(qe) or (o.cab in PERSONA_CLS or self._clase_sn(o)[0] in PERSONA_CLS)
                es_suj = bool(o.nsubj or pers or C.comps or C.attr or C.modo or C.v in INTRANS or (wh in ("donde", "cuando", "como", "porque") and not self.ult_suj))
            if not es_suj and o.det == "i" and not wh:
                usos = self.marcos(v=C.v, vig=None)
                es_suj = bool(usos) and not any(f.get("obj") or f.get("obj_disp") for f in usos)
            if es_suj:
                C.obj = None
                return self._q_ent(o), o, None
        s = self.can(self.ult_suj) if self.ult_suj else self.ref3()
        return s, None, o

    # ================================================================== entrada
    def preguntar(self, p: str, n: str) -> Optional[dict]:
        # «¿Cuándo tengo que entregarlo?»: el clítico pegado al infinitivo se quita (la pregunta sigue siendo por ese marco)
        def _sin_cl(m_):
            base = m_.group(1)
            return base if any(x[1] == "inf" for x in M.analizar(sa(base))) else m_.group(0)
        p2 = re.sub(r"\b([a-záéíóúñ]+[aei]r)(?:lo|la|los|las)\b", _sin_cl, p)
        if p2 != p:
            p, n = p2, re.sub(r"\b([a-zñ]+[aei]r)(?:lo|la|los|las)\b", _sin_cl, n)
        if re.search(r"\s+(?:allí|alli|allá|alla|ahí|ahi)\s*\?$", p) and re.match(r"^¿?\s*(?:[Yy]\s+)?[Cc]u[áa]nt", p.strip()):
            p = re.sub(r"\s+(?:allí|alli|allá|alla|ahí|ahi)\s*\?$", "?", p)   # «¿Cuántos días estaremos allí?»: el sitio ya está en lo dicho
            n = sa(p).strip(" ¿?.!").lower()
        mgq = re.match(r"^(¿?\s*(?:[Yy]\s+)?(?:[Aa]\s+(?:mí|mi|ti|él|ella|[A-ZÁÉÍÓÚÑ]\w+)\s+)?(?:no\s+)?(?:[Ll]e|[Tt]e|[Mm]e|[Ll]es)\s+(?:(?:ha|han)\s+)?(?:gustado|gusta|gustó|encantado|encanta|encantó))((?:\s+a\s+(?:mí|mi|ti|él|ella|[A-ZÁÉÍÓÚÑ]\w+(?:\s+\w+)?))?)\s*\?$", p.strip())
        if mgq:                                         # «¿Le ha gustado a Álex?»: lo que gustó es lo último de lo que se habló
            for f_g in reversed(self.F[-10:]):
                if f_g.get("v") in G.GUSTAR and f_g.get("obj_disp"):
                    od_g = re.sub(r"^(?:un|una)\s+", lambda x: "el " if x.group(0).strip() == "un" else "la ", cambia_persona(f_g["obj_disp"]))
                    p = f"{mgq.group(1)} {od_g}{mgq.group(2)}?"
                    if not p.startswith("¿"):
                        p = "¿" + p
                    n = sa(p).strip(" ¿?.!").lower()
                    break
        mqc = re.match(r"^(¿?\s*(?:[Yy]\s+)?(?:(?:a|de|con|en|para|por|hasta|desde)\s+)?(?:qu[ée]|c[óo]mo|cu[áa]ndo|d[óo]nde|ad[óo]nde|qui[ée]n|por qu[ée]|para qu[ée]))\s+(lo|la|los|las)\s+([a-záéíóúñ]+)\b(.*?)\s*\?$", p.strip(), re.I)
        if mqc and any(x[1] in ("pres", "pret", "imp", "fut", "cond") for x in M.analizar(sa(mqc.group(3)))):
            od_q = self._od_clitico(mqc.group(2))       # «¿Cómo la prefieren mis hijos?» -> «¿Cómo prefieren mis hijos la pasta?»
            if not od_q:
                e_q = self._ref_clitico(mqc.group(2).lower())
                if e_q:                                 # «¿Para qué la he llamado?» -> «… he llamado a Laura?»
                    od_q = ("a " if self.es_persona(e_q) else "") + cambia_persona(self.disp(e_q))
            if od_q:
                p = f"{'' if mqc.group(1).startswith('¿') else '¿'}{mqc.group(1)} {mqc.group(3)}{mqc.group(4)} {od_q}?"
                n = sa(p).strip(" ¿?.!").lower()
        T = G.tokens(self.parser, p)
        if not T or len(T) > 20:
            return None
        mrel = re.match(r"^(¿.*\b)(el|la|los|las|mi|mis|tu|tus)(\s+[a-záéíóúñ]+)\s+que\s+([^?]+)(\?)$", p.strip())
        if mrel and re.match(r"^¿\s*(?:[Yy]\s+)?(?:[Dd]e\s+)?[Qq]u[ée]\s+(?:color|forma|tamaño|marca)\b", p.strip()):
            art = mrel.group(2)
            if art in ("el", "la", "los", "las") and any(x[2] in ("1s", "1p") for w in mrel.group(4).split()[:3] for x in M.analizar(sa(w)) if x[1] in ("pres", "pret", "imp")):
                art = "mis" if art in ("los", "las") else "mi"   # «las rosas que más vendo» son las mías
            p = mrel.group(1) + art + mrel.group(3) + mrel.group(5)   # «¿De qué color son las rosas que más vendo?» -> «… mis rosas?»
            n = sa(p).strip(" ¿?.!").lower()
            T = G.tokens(self.parser, p)
        r = self._propiedad_de(p)
        if r is not None:
            return r
        r = self._color_de_sn(p)
        if r is not None:
            return r
        mcs = re.match(r"^¿?\s*(?:[Yy]\s+)?(.+?)\s+(es|son|era|eran)\s+([a-záéíóúñ]+)\s*\?$", p.strip())
        if mcs and sa(M.masc(M.singular(mcs.group(3).lower()))) in COLORES:
            r = self._color_de_sn(f"¿De qué color {mcs.group(2)} {mcs.group(1)[:1].lower() + mcs.group(1)[1:]}?")
            if r is not None and r.get("estado") == "ok":   # «¿Mis zapatillas son negras?» con «zapatillas blancas»
                pedido = sa(M.masc(M.singular(mcs.group(3).lower())))
                dicho = sa(r["respuesta"]).lower()
                si = any(sa(M.masc(M.singular(w))) == pedido for w in re.findall(r"[a-zñ]+", dicho))
                r["respuesta"] = ("Sí: " if si else "No: ") + r["respuesta"][:1].lower() + r["respuesta"][1:]
                return r
        r = self._que_le_pasa(p)
        if r is not None:
            return r
        r = self._que_hacer(p)
        if r is not None:
            return r
        r = self._forma_de(p)
        if r is not None:
            return r
        r = self._mismo_color(p)
        if r is not None:
            return r
        r = self._nombre_por_adj(p)
        if r is not None:
            return r
        r = self._cuantas_veces(p)
        if r is not None:
            return r
        r = self._mi_opinion(p)
        if r is not None:
            return r
        r = self._sigue_vivo(p)
        if r is not None:
            return r
        mca = re.match(r"^¿?\s*(?:[Yy]\s+)?(vivo|vives|vive|viven|estoy|estás|está|estas|esta)\s+(.*?)\s*con alguien\s*\?$", p.strip(), re.I)
        if mca:                                         # «¿Vivo con alguien?» con «vivo sola»
            an_ = [x for x in M.analizar(sa(mca.group(1).lower())) if x[1] == "pres"]
            s_a = {"1s": "U", "2s": "L"}.get(an_[0][2]) if an_ else None
            if not s_a and mca.group(2):
                s_a = self._sn_ent(mca.group(2))
            if s_a and an_:
                for f in reversed(self.marcos(v=an_[0][0], s=s_a, vig=True, neg=False)):
                    if set(sa(M.masc(a_)) for a_ in f.get("attr", []) + f.get("modo", [])) & {"solo"}:
                        self.ult_just = {"dicho": [f["src"]]}
                        return self._ok(self._fin("No: " + self.frase(f)))
                    if any(p2 == "con" for p2, _, _ in f.get("comps", [])):
                        self.ult_just = {"dicho": [f["src"]]}
                        return self._ok(self._fin("Sí: " + self.frase(f)))
        r = self._de_que_color_v(p)
        if r is not None:
            return r
        r = self._que_nombre(p)
        if r is not None:
            return r
        mqh = re.match(r"^¿?\s*(?:[Yy]\s+)?[Qq]u[ée]\s+(?:hay|tengo|tenemos|pasa|hacemos|hago)\s+(.+?)\s*\?$", p.strip())
        if mqh and re.search(r"\b(?:lunes|martes|miercoles|jueves|viernes|sabado|domingo|mañana|manana|hoy|fin de semana|semana)\b", sa(mqh.group(1)).lower()):
            clave = sa(mqh.group(1)).lower().replace("el ", "").replace("este ", "").strip()
            fs_h = [f for f in self.F if f.get("vig", True) and not f.get("neg") and clave in sa(f.get("cuando") or f.get("freq") or "").lower()]
            if fs_h:                                    # «¿Qué hay el viernes?»: lo que se dijo que pasa ese día
                self.ult_just = {"dicho": [f["src"] for f in fs_h]}
                return self._ok(self._fin(self._lista([_cap(self.frase(f)) for f in fs_h[-3:]])))
        while T and T[0].n in ("y", "pero", "entonces", "oye", "pues", "bueno", "dime", "sabes", "vale", "ah", "e", "o") and len(T) > 1:
            y_ini = T[0].n == "y"
            T = T[1:]
            if y_ini:
                r = self._seguimiento(T, p)
                if r is not None:
                    return r
        # «Entre Ana y Luis, ¿quién es más alto?» -> «¿Quién es más alto, Ana o Luis?»
        if T[0].n == "entre":
            kq = next((k for k, t in enumerate(T) if t.n in G.WH), None)
            if kq and kq > 2:
                cola = [t for t in T[1:kq]]
                for t in cola:
                    if t.n in ("y", "e"):
                        t.n = "o"; t.f = "o"
                T = T[kq:] + cola
        # sujeto antepuesto a la interrogativa: «¿Pablo dónde vive?», «¿A Ana qué le gusta?»
        kq = next((k for k, t in enumerate(T) if t.n in G.WH and (t.f.lower() != sa(t.f.lower()) or t.n in ("quien", "quienes", "cual", "cuales", "cuanto", "cuantos", "cuanta", "cuantas"))), None)
        if kq and kq <= 5 and not any(G._es_verbo_finito(t, T, k) for k, t in enumerate(T[:kq])):
            ini = 1 if T[0].n == "a" else 0
            r0 = G.sn_coord(T, ini)
            fin_pre = kq - (1 if T[kq - 1].n in ("a", "de", "con", "en", "para", "por") and kq - 1 > ini else 0)
            if r0 and r0[1] == fin_pre:
                T = T[fin_pre:] + T[:fin_pre]
        for k, t in enumerate(T):
            t.i = k
        ns = [t.n for t in T]
        # ---- frase interrogativa
        wh, i = None, 0
        prep = ""
        self._preg_prep_orig = ""
        if ns[0] in ("a", "de", "con", "en", "para", "por", "desde", "hasta", "sobre", "contra", "hacia", "entre", "sin", "segun", "tras", "bajo", "durante", "ante") and len(ns) > 1 and ns[1] in G.WH:
            prep = ns[0]; i = 1
        if ns[i] in G.WH:
            w = ns[i]
            tipo = {"quienes": "quien", "cuales": "cual", "cuanta": "cuanto", "cuantos": "cuanto", "cuantas": "cuanto", "adonde": "donde"}.get(w, w)
            if w == "adonde":
                prep = "a"
            i += 1
            if prep == "por" and tipo == "que":
                tipo, prep = "porque", ""
            if prep == "para" and tipo == "que":
                tipo, prep = "paraque", ""
            sust = ""
            if tipo in ("que", "cuanto") and i + 1 < len(T) and T[i].pos in ("VERB", "AUX") and T[i + 1].n not in G.ARTS and T[i + 1].n not in G.POSS \
                    and any(x[1] in ("pres", "pret", "imp", "fut") and x[2] in ("3s", "3p") for x in M.analizar(T[i + 1].f)) and (KB._kb_clase(T[i].n) or G._comun_conocida(T[i].n)):
                T[i].pos = "NOUN"; T[i].lem = sa(M.singular(T[i].n)) if T[i].n.endswith("s") else T[i].n      # «¿Qué instrumento toca…?»: la Escuela lo tomó por verbo
            hay_otro = any(G._es_verbo_finito(x, T, k_) for k_, x in enumerate(T) if k_ > i)
            es_v = i < len(T) and not hay_otro and any(x[1] in ("pres", "pret", "imp", "fut") for x in M.analizar(T[i].f)) and T[i].n not in ("color", "edad", "nombre")
            if tipo in ("que", "cuanto") and i < len(T) and T[i].pos in ("NOUN", "PROPN", "ADJ") and not es_v and not G._es_verbo_finito(T[i], T, i) and T[i].n not in G.CLIT and T[i].n not in G.NEG:
                sust = sa(M.singular(T[i].n)) if T[i].n.endswith("s") else (T[i].lem if T[i].pos == "NOUN" else T[i].n)
                if T[i].pos == "NOUN" and T[i].lem and T[i].lem != T[i].n and not (T[i].n == "año" and T[i].lem == "ano"):
                    sust = T[i].lem
                if T[i].n in ("año", "años"):
                    sust = "año"
                i += 1
                if i + 1 < len(T) and T[i].n == "de" and T[i + 1].pos == "NOUN" and sust in ("tipo", "clase"):
                    sust = T[i + 1].lem or T[i + 1].n; i += 2
            if tipo == "cual" and i < len(T) and T[i].n == "de":
                return None
            # «¿En qué ciudad vive X?» = dónde; «¿En qué año / qué día ...?» = cuándo (salvo «¿Qué día es hoy?»)
            verbo_ser = i < len(T) and T[i].n in ("es", "son", "era", "fue", "sera")
            self._preg_que_lugar = False
            if tipo == "que" and sust in ("ciudad", "lugar", "sitio", "pais", "pueblo", "calle", "barrio", "empresa", "zona", "parte", "localidad", "provincia", "region") and not verbo_ser:
                self._preg_que_lugar = not prep           # 2.20: «¿qué país cruza X?»: el sitio puede ser el objeto del verbo («cruza Rusia»)
                tipo, sust = "donde", ""
                prep = "" if prep == "en" else prep
            elif tipo == "que" and sust in ("año", "dia", "mes", "momento", "fecha", "hora", "epoca", "semana") and not verbo_ser and not (sust == "año" and i < len(T) and T[i].n in ("tiene", "tengo", "tienes", "cumple", "cumplo")):
                if prep in ("desde", "hasta", "para"):
                    self._preg_prep_orig = prep         # «¿Hasta qué hora abre…?»: el papel es el final
                tipo, sust, prep = "cuando", "", ""
            elif tipo == "que" and sust == "hora" and prep in ("a", "hasta", "desde"):
                self._preg_prep_orig = prep if prep != "a" else ""
                tipo, sust, prep = "cuando", "", ""     # «¿A qué hora es la entrevista?»
                self._preg_hora = True
            elif tipo == "que" and sust in ("dias", "años", "meses"):
                tipo, sust, prep = "cuando", "", ""
            wh = {"tipo": tipo, "prep": prep, "sust": sust, "prep_orig": getattr(self, "_preg_prep_orig", "")}
        elif prep:
            return None
        resto = T[i:] if wh else T
        if not resto:
            return None
        if any(t.n in ("que", "si", "cuando", "aunque", "mientras", "pero", "porque") for t in resto[1:]) and not any(t.n in ("mas", "menos", "mayor", "menor", "mejor", "peor", "tener", "tiene", "tengo", "tienes") for t in resto):
            return None
        # «¿Quién es más alto, Ana o Luis?»
        C = G.clausula(resto, pregunta=True)
        if C is None and wh and resto and resto[-1].pos in ("NOUN", "ADJ") and len(resto) <= 2 and any(x[1] in ("pres", "pret", "imp", "fut") and x[2] in ("1s", "2s", "3s", "1p", "3p") for x in M.analizar(resto[-1].f)) \
                and resto[-1].n in ("vivo", "trabajo", "estudio", "juego", "salgo", "como", "ceno", "hablo", "viajo", "quedo", "paseo", "bailo", "canto"):
            resto[-1].pos = "VERB"                      # «¿Con cuántas personas vivo?»: «vivo» es verbo
            C = G.clausula(resto[-1:] + resto[:-1], pregunta=True) or G.clausula(resto, pregunta=True)
        if C is None and wh and resto and resto[0].pos in ("NOUN", "ADJ", "PROPN", "X") and any(x[1] in ("pres", "pret", "imp", "fut") for x in M.analizar(resto[0].f)):
            resto[0].pos = "VERB"
            C = G.clausula(resto, pregunta=True)
        if C is None:
            return None
        self.anota_palabras(T)
        if C.pers == "1p" and C.v in ("hablar", "decir", "comentar", "conversar", "charlar", "estar", "ser") and C.suj is None \
                and not (isinstance(wh, dict) and wh.get("tipo") in ("cuanto", "donde", "cuando")):
            return None
        if C.v in ("servir", "significar") or (C.v in ("usar", "utilizar") and C.refl):
            return None
        if C.v in ("decir", "creer", "opinar", "afirmar", "suponer", "asegurar", "pasar", "ocurrir", "suceder") and not self.marcos(v=C.v, vig=None):
            return self._cronologia(n) if C.v in ("pasar", "ocurrir", "suceder") else None
        if not G.resuelve_elipsis(C, (wh or {}).get("sust", "")):
            return None
        C.wh = wh
        self.ult_preg = (p, wh)
        self._uso_posible = False
        import copy as _cp
        C_orig = _cp.deepcopy(C)                         # los manejadores de abajo necesitan la cláusula sin tocar
        r = self._preguntar_c(C, wh)
        C = C_orig
        if isinstance(r, dict) and getattr(self, "_uso_posible", False) and r.get("estado") == "ok":
            txt = r.get("respuesta") or ""
            m_ = re.match(r"^(?:Sí|Si)[,:.]?\s*(.*)$", txt)
            if m_:                                      # 2.11: una de varias posibilidades no se afirma
                cuerpo = m_.group(1).rstrip(".")
                cuerpo = re.sub(r"^lo deduzco porque\s+", "", cuerpo)
                if cuerpo.split() and sa(cuerpo.split()[0].lower()) in ("tu", "tus", "te", "el", "la", "los", "las", "un", "una", "mi", "mis", "a", "se"):
                    cuerpo = cuerpo[:1].lower() + cuerpo[1:]
                r = dict(r, respuesta=f"Puede ser: me dijiste que {cuerpo}, pero no cuál.")
        if wh is None and (r is None or r.get("estado") in ("abst", "aclara")) and C.v == "haber" and C.obj is not None and C.obj.cab:
            cl_q = self._clase_sn(C.obj)[0]             # 2.12: «¿Hay niños de Ecuador en la clase?»
            mod_q = re.search(r"\bde\s+(.+)$", sa(C.obj.texto))
            hay = [f for f in self.F if f["v"] == "haber" and f.get("vig", True) and not f.get("neg") and f.get("obj_cls") in (cl_q, cl_q.split(" de ")[0]) and self._coincide_comps(f, C.comps)
                   and (not mod_q or re.search(r"\bde\s+" + re.escape(mod_q.group(1)) + r"\b", sa(f.get("obj_disp") or "")))]
            if hay:
                r = self._ok(self._fin("Sí, " + re.sub(r"\bha\b", "hay", self.frase(hay[-1]))), {"dicho": [hay[-1]["src"]]})
            else:
                alli = [f for f in self.F if f["v"] == "haber" and f.get("vig", True) and not f.get("neg") and f.get("obj_cls") in (cl_q, cl_q.split(" de ")[0]) and self._coincide_comps(f, C.comps)]
                if alli:                                # «¿Hay niños de Chile?»: no me lo dijiste; solo sé de los otros
                    r = self._abst(self._fin("No me lo has dicho. Solo sé que " + re.sub(r"\bha\b", "hay", self._lista([self.frase(f) for f in alli[:4]]))))
        if wh is None and (r is None or r.get("estado") == "abst") and C.v == "preferir" and C.obj is not None:
            otro = [sn for p_, sn in C.comps if p_ in ("a", "al")]
            if otro:                                    # «¿Prefiero el café al té?» con «prefieres el té al café»: al revés
                for f in reversed(self.F):
                    if f["v"] == "preferir" and f.get("vig", True) and not f.get("neg") and _cabeza(f.get("obj_disp")) == _cabeza(otro[0].texto) \
                            and any(_cabeza(d2) == _cabeza(C.obj.texto) for p2, _, d2 in f.get("comps", []) if p2 in ("a", "al")):
                        r = self._ok(self._fin("No, " + self.frase(f)), {"dicho": [f["src"]]})
                        break
        if wh is None and (r is None or r.get("estado") == "abst") and getattr(self, "disy", None):
            r2 = self._no_por_disy(C)                   # 2.11: «¿El examen es el lunes?» con «es el jueves o el viernes»
            if r2 is not None:
                r = r2
        return r

    def _no_por_disy(self, C):
        try:
            s, sn_s, o = self._sujeto_preg(C)
        except Exception:                               # noqa
            return None
        if not isinstance(s, str) or s.startswith("?"):
            return None
        s = self.can(s)
        for gid in getattr(self, "disy", {}):
            ms = [x for x in self.F if x.get("posible") == gid and x["v"] == C.v and self.can(x.get("s") or "") == s and x.get("vig", True)]
            if len({x.get("alt") for x in ms}) >= 2:
                return self._ok(self._fin("No: me dijiste que " + self.frase(ms[0])), {"dicho": [ms[0]["src"]]})
        return None

    def _preguntar_c(self, C, wh):
        if wh is None:
            r = self.espacio_si_no(C)                   # 2.10: relación espacial directa, inversa o contraria
            if r is None:
                r = self._si_no(C)
        else:
            import copy as _copy
            C0 = _copy.deepcopy(C)                      # _interroga puede tocar la cláusula
            r = self.espacio_pregunta(C, wh)
            if r is None and wh.get("tipo") in ("que", "cual") and not wh.get("sust") and wh.get("prep") in ("de", "sobre", "contra", "sin", "desde", "hasta") and C.v in ("ser", "estar", "tratar", "hablar", "escribir", "leer", "jugar", "luchar"):
                r = self.por_papel(_copy.deepcopy(C), wh)   # «¿De qué es la silla?»: es una pregunta por la materia o el tema
            if r is None:
                r = self._interroga(C, wh)
            if r is None or r.get("estado") == "abst":
                r2 = self.por_papel(C0, wh)              # 2.10: la pregunta busca un papel, no una preposición literal
                if r2 is not None:
                    r = r2
        self._preg_prep_orig = ""
        return r

    def _seguimiento(self, T, p):
        """«¿Y Luis?», «¿Y el de Ana?», «¿Y tú?»: repite la última pregunta con otra entidad."""
        if not getattr(self, "ult_preg_txt", None) or len(T) > 4:
            return None
        if any(G._es_verbo_finito(t, T, k) for k, t in enumerate(T)) or T[0].n in G.WH:
            return None
        r = G.sn_coord(T, 0)
        if not r or r[1] != len(T):
            return None
        nuevo = r[0]
        viejo_sn, viejo_txt = self.ult_preg_sn
        if not viejo_sn:
            return None
        txt = self.ult_preg_txt
        pat = re.compile(re.escape(viejo_sn), re.I)
        if not pat.search(txt):
            return None
        return self._una(pat.sub(nuevo.texto, txt, count=1))

    def _recuerda_preg(self, p, sn_suj: SN):
        self.ult_preg_txt = p
        self.ult_preg_sn = (sn_suj.texto if sn_suj is not None else "", p)

    def _cronologia(self, n):
        """«¿Qué pasó primero / último / antes del 3 de noviembre?» con los acontecimientos fechados."""
        ev = []
        for f in self.F:
            if f.get("efecto") or f.get("neg") or f.get("t") not in ("pret",) or not f.get("cuando"):
                continue
            iv = self._intervalo(f["cuando"])
            if iv:
                ev.append((iv.split("/")[0], iv.split("/")[1], f))
        if not ev:
            return None
        ev.sort(key=lambda x: (x[0], x[1]))
        m = re.search(r"\b(antes|despues)\s+(?:de|del|de el)\s+(.+)$", n)
        if re.search(r"\b(primero|primera|antes que nada|en primer lugar)\b", n):
            sel = [ev[0][2]]
        elif re.search(r"\b(ultimo|ultima|al final|por ultimo|lo ultimo|mas reciente)\b", n):
            sel = [ev[-1][2]]
        elif m:
            ref = self._intervalo("el " + m.group(2) if re.match(r"\d", m.group(2)) else m.group(2))
            if not ref:
                return None
            sel = [f for a, b, f in ev if (b < ref.split("/")[0] if m.group(1) == "antes" else a > ref.split("/")[1])]
            if not sel:
                return self._abst("No lo sé: no tengo ningún acontecimiento con fecha " + ("anterior" if m.group(1) == "antes" else "posterior") + " a esa.")
        else:
            return None
        self.ult_just = {"dicho": [f["src"] for f in sel]}
        return self._ok(self._fin(self._lista([self.frase(f) + (f" ({self._fecha_abs(f['cuando'], f)})" if self._fecha_abs(f["cuando"], f) else "") for f in sel[:4]])))

    # ================================================================== sí / no
    def _si_no(self, C: Clausula) -> Optional[dict]:
        v = C.v
        if v in G.GUSTAR and (C.clit or C.dat):
            return self._gustar_q(C, None)
        if self._dat_ev_q(C, None) and [f for f in self.F if f.get("dat_ev") and f["v"] == v]:
            return self._gustar_q(C, None)
        s, sn_s, o = self._sujeto_preg(C)
        self._recuerda_preg(self.ult_preg[0], sn_s)
        if s == "L":
            return None
        if o is not None and not o.coord and getattr(o, "adjs", None) and o.cab and isinstance(s, str) and not s.startswith("?") and v not in ("ser", "estar", "parecer", "llamar"):
            cl_o = self._clase_sn(o)[0]                  # 2.16: el adjetivo del objeto es parte de lo que se pregunta
            cands = [(f, self._adjs_casan(f, o)) for f in self.marcos(v=v, s=s, neg=False, herencia=True) if f.get("obj_cls") == cl_o and f.get("vig", True)]
            if cands and not any(r is True for _, r in cands):
                contr = next((f for f, r in cands if r == "contrario"), None)
                if contr is not None:
                    self.ult_just = {"dicho": [contr["src"]]} if contr.get("src") else None
                    return self._ok(self._fin("No, " + self.frase(contr)))
                otro = next((f for f, r in cands if r is False), None)
                if otro is not None:
                    return self._abst(self._fin("No lo sé: solo sé que " + self.frase(otro)))
        if v in ("estar", "parecer") and o is not None and not o.coord and o.cab and not o.det and not o.propio and o.de is None and not o.pos and o.num is None and not C.attr:
            C.attr = [M.masc(o.cab)]; o = None; C.obj = None
        if s is None or (isinstance(s, str) and s.startswith("?")):
            if sn_s is None:
                return None
            if isinstance(s, str) and s.startswith("?") and sn_s.cab:
                # «¿Los perros de Amaia vuelan?»: no conozco a esos perros, pero sí a los perros en general
                c_ = KB._kb_clase(sn_s.cab)
                resto_ = " ".join(x for x in [(C.obj.texto if C.obj is not None else ""), " ".join(C.attr)] if x)
                e_ = KB._estado(c_, v, resto_) if c_ and v not in ("ser", "llamar") else None
                if e_ is not None:
                    d_, neg_, cl_, v_, rs_ = e_
                    return self._ok(self._fin(("No" if neg_ else "Sí") + ": " + KB._frase_prop(cl_, neg_, v_, rs_)), {"pasos": [KB._frase_prop(cl_, neg_, v_, rs_)], "fabrica": True})
                if c_ and v in KB.VOCES:
                    vz = KB.voz_de([c_] + KB.ancestros(c_))
                    if vz and vz[1] != v:
                        return self._ok(self._fin("No: " + KB._frase_prop(vz[0], False, vz[1], "")), {"pasos": [KB._frase_prop(vz[0], False, vz[1], "")], "fabrica": True})
            return self._no_conozco(sn_s, s)
        if isinstance(s, list):
            if v == "ser" and o is None and C.attr and len(s) == 2:
                o = SN(cab=C.attr[0], pl=True)
            if v == "ser" and o is not None and o.pl and o.pos in ("U", "L") and o.cab:
                cl = self._canon_rel(M.singular(o.cab))[0] if M.singular(o.cab) in REL_CANON else self._canon_rel(sa(M.singular(o.cab)))[0]
                du = o.pos
                si_ = [x for x in s if self.rels(cl, x=x, y=du)]
                if len(si_) == len(s):
                    return self._ok(self._fin(f"Sí, {self._lista([self.disp(x) for x in s])} son {'tus' if du == 'U' else 'mis'} {M.plural(self._acento(self._rel_nombre(cl, 'f' if all(self.gen(x) == 'f' for x in s) else 'm')))}"))
                if si_:
                    return self._ok(self._fin(f"Solo {self._lista([self.disp(x) for x in si_])}"))
                return self._abst(self._fin(f"No me consta que {self._lista([self.disp(x) for x in s])} sean {'tus' if du == 'U' else 'mis'} {M.plural(self._acento(cl))}"))
            if v == "ser" and o is not None and (o.pl or o.cab in FAMILIA | SIMETRICAS) and not o.det and len(s) == 2:
                cl = self._canon_rel(o.cab)[0] if o.cab in REL_CANON else self._clase_sn(o)[0]
                ps = [x for x in self.rels(cl, x=s[0], y=s[1])]
                if ps:
                    just = ps[0]["j"]
                    self.ult_just = {"pasos": just}
                    g_h = "f" if all(self.gen(x) == "f" for x in s[:2]) else "m"
                    return self._ok(self._fin(f"Sí, {self.disp(s[0])} y {self.disp(s[1])} son {M.plural(self._rel_nombre(cl, g_h))}"), tipo="resp")
                return self._abst(f"No lo sé: no me consta que {self.disp(s[0])} y {self.disp(s[1])} sean {M.plural(cl)}.")
            s = s[0]
        s = self.can(s)
        self.mencionar(s); self.ult_suj = s if s != "L" else self.ult_suj
        conocido = self._conocido(s)
        consultar = s.startswith("K:") or not conocido
        pasado = C.tiempo in ("imp", "pret")
        # ---------- llamarse
        if v == "llamar" and C.refl and o is not None and o.propio:
            real = self._nombre_de(s)
            if not real:
                return self._abst(f"No sé cómo {'te llamas' if s == 'U' else 'se llama ' + self.disp(s)}.")
            if sa(real) == o.cab or sa(real).split()[0] == o.cab:
                return self._ok(self._fin(f"Sí, {'te llamas' if s == 'U' else self.disp(s) + ' se llama'} {real}"), {"dicho": [self.E.get(s, {}).get("src_nombre", "")]})
            return self._ok(self._fin(f"No, {'te llamas' if s == 'U' else 'se llama'} {real}"), {"dicho": [self.E.get(s, {}).get("src_nombre", "")]})
        # ---------- ser + relación / identidad
        if v == "ser" and o is not None and not o.coord:
            if o.propio and (s.startswith("I:") or s.startswith("N:") or s == "U"):
                real = self._nombre_de(s)
                if s == "U" and real:
                    return self._ok(self._fin(("Sí, eres " if sa(real).split()[0] == o.cab.split()[0] else "No, eres ") + real), {"dicho": [self.E["U"].get("src_nombre", "")]})
                if s.startswith("N:"):
                    return self._ok(self._fin(("Sí" if s == "N:" + o.cab else "No") + f", es {self.disp(s)}"))
                return self._abst("No lo sé.")
            if o.cab and (o.de is not None or o.pos):
                cl, g = self._clase_sn(o)
                if cl in ("parte", "tipo", "clase", "sinonimo", "contrario", "ejemplo"):
                    return None
                dueno = "U" if o.pos == "U" else ("L" if o.pos == "L" else None)
                if o.pos == "3":
                    dueno = self.ref3(persona=True, excluye=(s,))
                if o.de is not None:
                    dueno = self._q_ent(o.de)
                if dueno is None or isinstance(dueno, list) or str(dueno).startswith("?") or dueno == "L":
                    return self._no_conozco(o.de, dueno) if o.de is not None else None
                ps = self.rels(cl, x=s, y=dueno)
                if ps:
                    j = ps[0]["j"]
                    fr = self._frase_rel(cl, s, self.can(dueno))
                    self.ult_just = {"pasos": j} if (len(j) > 1 or j[0] != fr) else {"dicho_rel": fr}
                    extra = f" Lo deduzco {self._porque(j)}" if (len(j) > 1 or j[0] != fr) else ""
                    return self._ok(self._fin(f"Sí, {fr}") + (" " + self._fin(extra.strip()) if extra else ""))
                if cl in FAMILIA:
                    for r2 in sorted(FAMILIA - {cl}):
                        ps2 = self.rels(r2, x=s, y=dueno)
                        if ps2 and not (cl, r2) in (("primo", "hermano"),):
                            self.ult_just = {"pasos": ps2[0]["j"]}
                            return self._ok(self._fin(f"No, {self._frase_rel(r2, s, self.can(dueno))}"))
                otros = [r for r in self.rels(cl, y=dueno) if (not g or self.gen(r["x"]) == g) and not r["x"].startswith("I:")]
                if otros and ((cl, g) in UNICAS or (cl, "") in UNICAS):
                    fr = self._frase_rel(cl, otros[0]["x"], self.can(dueno))
                    self.ult_just = {"pasos": otros[0]["j"]}
                    return self._ok(self._fin(f"No, {fr}"))
                return self._abst(self._fin(f"No lo sé: no me consta que {self._frase_rel(cl, s, self.can(dueno)).replace(' es ', ' sea ', 1).replace('eres ', 'seas ', 1)}"), consultar=s.startswith("K:") or str(dueno).startswith("K:"))
            if o.cab and not o.propio and not o.det and not o.pl and (M.masc(o.cab) in COLORES or M.masc(o.cab) in KB.kb()["ant"]) and not self._semilla_tiene_miembros(o.cab):
                C.attr = [M.masc(o.cab)]             # «¿Es la mesa de Sara azul?»: es una cualidad, no una clase
                return self._atributo_q(s, v, C, consultar, pasado)
            if o.cab and not o.propio:
                return self._es_un(s, o, C, consultar)
        # ---------- ser / estar + atributo
        if v in ("ser", "estar", "parecer") and (C.attr or C.comp) and not C.comps:
            if C.comp:
                return self._compara_q(C, s)
            return self._atributo_q(s, v, C, consultar, pasado)
        # ---------- tener
        if v == "tener" and o is not None:
            return self._tener_q(s, o, C, consultar)
        # ---------- genérico
        if isinstance(s, str) and s.startswith("K:") and not _tiene_propios_v(self, s, v) and not [f_ for f_ in self.marcos(v=v, s=s, vig=None, herencia=True) if not f_.get("fab")]:
            resto_ = " ".join(x for x in [(o.texto if o is not None else "")] + [p_ + " " + x_.texto for p_, x_ in C.comps if x_ is not None] if x)
            e_ = KB._estado(s[2:], v, resto_)
            if e_ is not None:                          # «¿(La ballena) vive en el agua?» con «las ballenas viven en el mar»
                d_, neg_, cl_, v_, rs_ = e_
                txt_ = KB._frase_prop(cl_, neg_, v_, rs_)
                return self._ok(self._fin(("No, " if neg_ else "Sí, ") + txt_), {"pasos": [txt_], "fabrica": True})
        vs = [v]
        if not self.marcos(v=v, s=s, vig=None, herencia=True):
            vs = list(dict.fromkeys(f["v"] for f in self.marcos(s=s, vig=None) if self._sin(v, f["v"], "v"))) or [v]
        v = vs[0]
        fs = [f for f in self.marcos(v=v, s=s, vig=None, herencia=True) if self._coincide_obj(f, o) and self._coincide_comps(f, C.comps) and self._tiempo_ok(f, C)
              and (not C.xinf or sa(C.xinf) == sa(f.get("xinf", "")) or sa(f.get("xinf", "")).startswith(sa(C.xinf) + " "))
              and (not [x for x in C.modo if sa(x) in ("bien", "mal", "mucho", "poco", "rapido", "despacio")] or {sa(x) for x in C.modo} & {sa(x) for x in f.get("modo", [])}) and (not C.lugar_adv or C.lugar_adv == f.get("lugar_adv")) and (not C.attr or set(C.attr) & set(f.get("attr", [])))]
        vig = [f for f in fs if f.get("vig", True)]
        pos = [f for f in vig if not f.get("neg")]
        neg = [f for f in vig if f.get("neg")]
        if (pos and pos[0].get("parcial")) or (neg and not pos and neg[0].get("parcial")):
            f = (pos or neg)[0]
            return self._abst(f"No lo sé con seguridad: solo me has dicho que {f['src'].strip(' .!')[:1].lower() + f['src'].strip(' .!')[1:]}, no que sea así siempre.")
        if pos and not pasado and C.tiempo == "pres" and all(f.get("t") == "imp" for f in pos):
            # lo que consta es de antes: «¿Vivo en Albacete?» con «antes vivía en Albacete» y «vivo en Valencia»
            f = pos[0]
            ahora_ = [g for g in self.marcos(v=v, s=s, neg=False) if g.get("t") == "pres" and g.get("comps") and not self._coincide_comps(g, C.comps)]
            if ahora_ and C.comps:
                return self._ok(self._fin("Ya no: ahora " + self.frase(ahora_[-1]) + "; " + self.frase(f)), {"dicho": [ahora_[-1]["src"], f["src"]]})
            dej_ = [g for g in self.marcos(v="dejar", s=s, neg=False) if any(p2 == "de" and d2 and sa(d2.split()[0]) == sa(v) for p2, _, d2 in g.get("comps", []))]
            if dej_:                                    # «antes fumaba… dejé de fumar hace dos años»: ahora no
                return self._ok(self._fin("No, ya no: " + self.frase(dej_[-1])), {"dicho": [dej_[-1]["src"], f["src"]]})
            return self._abst(self._fin("Antes sí (" + self.frase(f) + "), pero no sé si ahora también"))
        if pos and not (pasado and all(f.get("t") == "pres" for f in pos) and False):
            f = pos[0]
            just = self._just_marco(f, s)
            return self._ok(self._fin("Sí, " + self.frase(f)), just)
        if not pos and not neg and o is not None:
            solos = [f for f in self.marcos(v=v, s=s, neg=False) if f.get("solo") and f.get("obj_disp")]
            if solos:                                   # «¿Hablo portugués?» con «Solo hablo español»
                return self._ok(self._fin("No: " + self.frase(solos[-1]).replace(" ", " solo ", 1) if self.frase(solos[-1]).startswith(("Tú ", "tú ")) else "No, solo " + self.frase(solos[-1])), {"dicho": [solos[-1]["src"]]})
        if not pos and not neg and v == "ser" and any(p_ == "de" for p_, _ in C.comps):
            r_ = self._de_lugar(s, C)
            if r_ is not None:
                return r_
        viejos = [f for f in fs if not f.get("vig", True) and not f.get("neg")]
        if neg and pasado and viejos and all(f.get("t") == "pres" for f in neg):
            f = viejos[0]
            return self._ok(self._fin("Sí, " + self.frase(f, tiempo="imp" if f.get("t") == "pres" else None, antes=f.get("t") == "pres") + ", pero ya no"), {"dicho": [f["src"], neg[0]["src"]]})
        if neg:
            f = neg[0]
            por = f.get("por")
            return self._ok(self._fin("No, " + self.frase(f)) + (" " + self._fin(_cap(por)) if por else ""), {"dicho": [f["src"]]})
        actuales = [f for f in self.marcos(v=v, s=s, neg=False) if not f.get("efecto") or True]
        # valor único conocido y distinto -> «no»
        for p_, s_ in C.comps:
            if (v, p_) in FUNCIONAL:
                act = [f for f in actuales if any(p2 == p_ for p2, _, _ in f.get("comps", [])) and f.get("t") == "pres"]
                if act and (v, p_) in FUNC_SIEMPRE or act and len(act) == 1 and (v, p_) in FUNCIONAL and False:
                    f = act[0]
                    if viejos and pasado:
                        return self._ok(self._fin("Sí, " + self.frase(viejos[0], tiempo="imp", antes=True) + ", pero ahora " + self.frase(f, sin_sujeto=True)), {"dicho": [viejos[0]["src"], f["src"]]})
                    if viejos:
                        return self._ok(self._fin("Ya no: ahora " + self.frase(f)) , {"dicho": [f["src"]]})
                    return self._ok(self._fin("No, " + self.frase(f)), {"dicho": [f["src"]]})
        if viejos:
            f = viejos[0]
            return self._ok(self._fin(("Sí, " if pasado else "Antes sí: ") + self.frase(f, tiempo="imp" if f.get("t") == "pres" else None, antes=f.get("t") == "pres")), {"dicho": [f["src"]]})
        if v in KB.VOCES and o is None and not C.comps:   # «¿Mía ladra?» siendo una gata: cada animal tiene su voz
            vz = KB.voz_de([c for c, _ in self.clases(s)])
            if vz and vz[1] != v:
                return self._ok(self._fin("No: " + KB._frase_prop(vz[0], False, vz[1], "")), {"pasos": [KB._frase_prop(vz[0], False, vz[1], "")], "fabrica": True})
        rel = [self.frase(f) for f in actuales[:3]]
        if rel:
            return self._abst(self._fin("No lo sé. Solo sé que " + self._lista(rel)))
        if not conocido:
            return self._no_conozco(sn_s, s) if (sn_s is not None and sn_s.propio) else self._abst("No lo sé.", consultar=True)
        return self._abst("No lo sé: no me has dicho nada sobre eso." + (" " + self._se_de(s) if self._se_de(s) else ""), consultar=consultar)

    def _de_lugar(self, s, C):
        """«¿Andrea es de Portugal?» con «Andrea es de Oporto» y «Oporto está en Portugal»."""
        q = [self._q_ent(x) for p_, x in C.comps if p_ == "de"]
        q = self.can(q[0]) if q and q[0] and not isinstance(q[0], list) and not str(q[0]).startswith("?") else None
        if q is None:
            return None
        for f in self.marcos(v="ser", s=s, neg=False):
            for p_, e_, d_ in f.get("comps", []):
                if p_ != "de" or not e_:
                    continue
                y, cadena = self.can(e_), [f["src"]]
                for _ in range(3):
                    g = [g for g in self.marcos(v="estar", s=y, neg=False) if any(p2 == "en" and e2 for p2, e2, _ in g.get("comps", []))]
                    if not g:
                        break
                    cadena.append(g[-1]["src"])
                    y = self.can([e2 for p2, e2, _ in g[-1]["comps"] if p2 == "en" and e2][0])
                    if y == q:
                        self.ult_just = {"pasos": [self.frase(f)] + [self.frase(x) for x in self.marcos(v="estar", neg=False) if x["src"] in cadena[1:]]}
                        return self._ok(self._fin(f"Sí: {self.frase(f)}, y {self._lista([self.frase(x) for x in self.marcos(v='estar', neg=False) if x['src'] in cadena[1:]])}"))
        return None

    def _just_marco(self, f, s):
        fs = self.can(f["s"])
        if fs != s and fs.startswith("K:"):
            ok, j = self.es_clase(s, fs[2:])
            return {"pasos": j + [self.frase(f)]}
        if f.get("efecto"):
            return {"dicho": [f["src"]]}
        return {"dicho": [f["src"]]}

    def _nombre_de(self, e):
        e = self.can(e)
        if e == "U":
            return self.usuario.get("nombre") or ""
        if e.startswith("N:"):
            return self.E[e].get("nombre") or e[2:].title()
        return ""

    def _es_un(self, s, o: SN, C, consultar):
        cl = self._canon_rel(o.cab)[0] if o.cab in REL_CANON else o.cab
        if cl == "ser" and any(sa(a) in ("vivo", "viva", "vivos") for a in (o.adjs or [])):
            cl = "ser vivo"                              # 2.15: clase de dos palabras
        cl = KB.kb()["alias"].get(cl, cl)
        ok, j = self.es_clase(s, cl)
        fs = [f for f in self.marcos(v="ser", s=s) if cl in f.get("attr", []) or o.cab in f.get("attr", []) or M.masc(o.cab) in f.get("attr", [])]
        if fs:
            f = fs[0]
            return self._ok(self._fin(("No, " if f.get("neg") else "Sí, ") + self.frase(f)), {"dicho": [f["src"]]})
        if ok:
            self.ult_just = {"pasos": j}
            g = M.genero_sust(cl)
            fr = f"{self.disp(s) if s != 'U' else 'eres'} {'es ' if s != 'U' else ''}{self._un(cl, g)}"
            if s.startswith("K:"):
                fr = f"{self._un(self.E[s].get('clase', s[2:]), self.gen(s))} es {self._un(cl, g)}"
            extra = f" Lo deduzco {self._porque(j)}." if len(j) > 1 else ""
            return self._ok(self._fin("Sí, " + fr) + extra)
        prof_q = "profesional" in KB.ancestros(cl)
        if prof_q and self.es_persona(s):
            suyas = [f for f in self.marcos(v="ser", s=s, neg=False) if f.get("prof") or any("profesional" in KB.ancestros(a) for a in f.get("attr", []) + f.get("isa", []))]
            if suyas:                                   # «¿Soy médica?» con «Soy enfermera»: una profesión dicha descarta otra
                f = suyas[-1]
                return self._ok(self._fin("No, " + self.frase(f)), {"dicho": [f["src"]]})
        propias = self.clases(s)
        _rol = FAMILIA | {"padrino", "padrastro", "hermanastro", "bisabuelo", "entrenador", "amigo", "vecino", "compañero", "jefe", "novio", "esposo", "socio", "colega", "empleado", "alumno", "conocido", "pareja", "mejor amigo", "dueño"}
        if not s.startswith("K:"):
            propias = [(c, j) for c, j in propias if c not in _rol]   # ser amigo o vecino no impide ser otra cosa
            d_s = self.E.get(s, {})
            if d_s.get("dueno") and d_s.get("clase") and (not KB._kb_clase(d_s["clase"]) or "persona" in KB.ancestros(KB._kb_clase(d_s["clase"]))):
                papel = d_s["clase"]
                propias = [(c, j) for c, j in propias if c != papel and c not in KB.ancestros(papel)]
        propia0 = self.E.get(s, {}).get("clase") or s[2:] if s.startswith("K:") else (propias[0][0] if propias else "")
        if propias and propia0:
            # taxonomía: dos clases conocidas, ninguna contiene a la otra -> no
            arriba = {c for c, _ in propias}
            anc_dest = {c for c, _ in self.clases("K:" + cl)}
            dest = anc_dest | {cl}
            con_miembros = bool(anc_dest) or any(cl in f.get("isa", []) for f in self.F if f.get("vig", True)) or self._semilla_tiene_miembros(cl)
            de_fabrica = s.startswith("K:") and bool(KB._kb_clase(s[2:]))
            emparentadas = de_fabrica or bool((arriba | set(KB.ancestros(propia0))) & (anc_dest | set(KB.ancestros(KB._kb_clase(cl) or cl)))) \
                or bool(KB._kb_clase(cl) and any(KB._kb_clase(c_) and (KB._grupos_de(KB._kb_clase(c_)) & KB._grupos_de(KB._kb_clase(cl))) for c_ in arriba))
            if con_miembros and cl not in arriba and cl != propia0 and propia0 not in anc_dest and emparentadas:   # 2.18: lo aprendido puede ser varias cosas a la vez
                c0, j0 = propias[0]
                self.ult_just = {"pasos": j0}
                if s.startswith("K:"):
                    c1 = [c for c, _ in propias if c != self.E.get(s, {}).get("clase")]
                    if c1:
                        return self._ok(self._fin(f"No, {self._un(self.E[s].get('clase', s[2:]), self.gen(s))} es {self._un(c1[0], M.genero_sust(c1[0]))}"))
                else:
                    return self._ok(self._fin(f"No, {self.disp(s)} es {self._un(c0, M.genero_sust(c0))}" if s != "U" else f"No, eres {self._un(c0, M.genero_sust(c0))}"))
        if propias and (not s.startswith("K:") or not KB._kb_clase(s[2:])) and KB._kb_clase(cl):
            # 2.15: grandes ramas que no se cruzan (ser vivo / cosa / lugar / abstracto): «¿mi suegra es un lugar?» -> no, es una persona
            g_dest = KB._grupos_de(KB._kb_clase(cl))
            for c0, j0 in propias:
                g0 = KB._grupos_de(c0) if KB._kb_clase(c0) else set()
                comestible = "vivo" in g0 and "alimento" in ([KB._kb_clase(cl)] + list(KB.ancestros(KB._kb_clase(cl))))   # 2.18: un ser vivo puede ser además un alimento
                if g0 and g_dest and not (g0 & g_dest) and not comestible:
                    self.ult_just = {"pasos": j0}
                    return self._ok(self._fin(f"No, {self.disp(s)} es {self._un(c0, M.genero_sust(c0))}" if s != "U" else f"No, eres {self._un(c0, M.genero_sust(c0))}"))
        otros = [f for f in self.marcos(v="ser", s=s, neg=False) if f.get("isa")]
        if otros and not s.startswith("K:"):
            return self._abst(self._fin("No lo sé. Solo sé que " + self.frase(otros[0])))
        return self._abst("No lo sé.", consultar=True if (s.startswith("K:") or not self._conocido(s)) else False)

    @staticmethod
    def _lexico_conoce(w):
        try:
            from src.language import lexico
            return bool(lexico.sentidos(w))
        except Exception:                                                     # noqa
            return True

    def _semilla_tiene_miembros(self, c):
        C = sa(c).upper().replace(" ", "_")
        return any(f.get("p") == "ES" and not f.get("neg") and sa(f.get("o", "")).upper() == C for f in getattr(self.mem, "facts", []))

    def _atributo_q(self, s, v, C, consultar, pasado):
        qa = set(C.attr)
        if any("profesional" in KB.ancestros(a) for a in qa) and self.es_persona(s):
            suyas = [f for f in self.marcos(v="ser", s=s, neg=False) if any("profesional" in KB.ancestros(a) for a in f.get("attr", []) + f.get("isa", []))]
            if suyas and not any(qa & set(f.get("attr", [])) for f in suyas):
                f = suyas[-1]                          # «¿Soy médica?» con «Soy enfermera»
                return self._ok(self._fin("No, " + self.frase(f)), {"dicho": [f["src"]]})
        fs = self.marcos(v=v, s=s, vig=None, herencia=True)
        if v == "ser":
            fs += [f for f in self.marcos(v="estar", s=s, vig=None) if set(f.get("attr", [])) & qa]
        elif v == "estar":
            fs += [f for f in self.marcos(v="ser", s=s, vig=None) if set(f.get("attr", [])) & qa]
        vig = [f for f in fs if f.get("vig", True)]
        for f in vig:
            if qa & set(f.get("attr", [])):
                if f.get("parcial"):
                    return self._abst(f"No lo sé con seguridad: solo me has dicho que {f['src'].strip(' .!')[:1].lower() + f['src'].strip(' .!')[1:]}, no que sea así siempre.")
                return self._ok(self._fin(("No, " if f.get("neg") else "Sí, ") + self.frase(f)), self._just_marco(f, s))
        for f in vig:
            fa = set(f.get("attr", []))
            if f.get("neg") or not fa or f.get("parcial"):
                continue
            choque = (qa & COLORES and fa & COLORES) or any(a in _ANT.get(b, ()) for a in qa for b in fa)
            if choque:
                return self._ok(self._fin("No, " + self.frase(f)), self._just_marco(f, s))
        # comparaciones como prueba indirecta no se usan: se abstiene
        viejos = [f for f in fs if not f.get("vig", True) and qa & set(f.get("attr", [])) and not f.get("neg")]
        if viejos:
            f = viejos[0]
            return self._ok(self._fin(("Sí, " if pasado else "Antes sí: ") + self.frase(f, tiempo="imp")), {"dicho": [f["src"]]})
        if (qa & {"mayor", "menor"}) :
            pass
        sab = [self.frase(f) for f in vig if f.get("attr") and not f.get("neg") and self.can(f["s"]) == s][:2]
        if sab:
            return self._abst(self._fin("No lo sé. Solo sé que " + self._lista(sab)))
        if s.startswith("K:") or not self._conocido(s):
            return self._abst("No lo sé.", consultar=True)
        return self._abst(self._fin("No lo sé: no me has dicho eso " + self._de(s)))

    def _de_clase(self, f, sust):
        """¿El objeto del marco es de la clase «sust»? Con lo dicho, la base de fábrica y papeles como «mascota»."""
        oc = f.get("obj_cls") or ""
        sust = KB.kb()["alias"].get(sust, sust)          # 2.15: «ropa» es otra palabra para la clase «prenda»
        if oc == sust or (f.get("obj") and self.es_clase(f["obj"], sust)[0]):
            return True
        if oc.startswith(sust + " de ") or oc.startswith(sust + " "):
            return True                                 # «tarta de chocolate» es una tarta
        cadena = [oc] + KB.ancestros(oc) if oc else []
        if sust in cadena:
            return True
        return sust in ("mascota", "bicho") and "animal" in cadena

    def _tener_q(self, s, o: SN, C, consultar):
        if o is not None and o.pos == "3" and s not in ("U", "L") and not str(s).startswith("K:"):
            prev = self.ult_suj
            self.ult_suj = s                           # «¿Tiene Lorena su paraguas?»: «su» es de Lorena
            try:
                return self._tener_q2(s, o, C, consultar)
            finally:
                self.ult_suj = prev
        return self._tener_q2(s, o, C, consultar)

    def _tener_q2(self, s, o: SN, C, consultar):
        gq = getattr(self, "_gq_txt", "")
        if o is not None and o.adjs:
            if set(o.adjs) & {"varon", "chico", "nino", "masculino"}:
                gq = "m"
            elif set(o.adjs) & {"mujer", "chica", "nina", "femenino", "hembra"}:
                gq = "f"
        if gq and o.cab in FAMILIA:
            todos = [f for f in self.marcos(v="tener", s=s, neg=False) if f.get("obj_cls") == o.cab and f.get("obj")]
            ok = [f for f in todos if self.gen(f["obj"]) == gq]
            if ok:
                return self._ok(self._fin("Sí, " + self.frase(ok[0])), {"dicho": [ok[0]["src"]]})
            if todos:
                return self._abst(self._fin("No me consta: solo me has hablado de " + self._lista([self.disp(f["obj"]) for f in todos[:3]])))
        if o.cab in ("año", "ano") and o.num is not None:
            ed = self._edad(s)
            if ed is None:
                return self._abst(self._fin(f"No sé cuántos años {'tienes' if s == 'U' else 'tiene ' + self.disp(s)}"))
            n_, just = ed
            self.ult_just = just
            return self._ok(self._fin(("Sí" if n_ == o.num else "No") + f", {'tienes' if s == 'U' else self.disp(s) + ' tiene'} {n_} años"))
        fs = [f for f in self.marcos(v="tener", s=s, vig=None, herencia=True) if self._coincide_obj(f, o)]
        vig = [f for f in fs if f.get("vig", True)]
        pos = [f for f in vig if not f.get("neg")]
        if C.tiempo == "pres":                          # «¿Tengo las llaves?»: que las tuviera esta mañana no dice que las tenga ahora
            pos = [f for f in pos if f.get("t") not in ("imp", "pret")]
        neg = [f for f in vig if f.get("neg")]
        if pos:
            f = pos[0]
            if o.num is not None and f.get("cuant") is not None and o.num != f["cuant"]:
                return self._ok(self._fin("No, " + self.frase(f)), self._just_marco(f, s))
            return self._ok(self._fin("Sí, " + self.frase(f)), self._just_marco(f, s))
        viejos0 = [f for f in fs if not f.get("vig", True) and not f.get("neg")]
        if C.tiempo in ("imp", "pret") and viejos0:
            return self._ok(self._fin("Sí, antes sí: " + self.frase(viejos0[0], tiempo="imp")), {"dicho": [viejos0[0]["src"]]})
        if neg:
            f = neg[0]
            por = f.get("por")
            if por:
                return self._ok(self._fin("No, ya no: " + por), {"dicho": [f["src"]]})
            return self._ok(self._fin("No, " + self.frase(f)), {"dicho": [f["src"]]})
        # relaciones contadas como posesión: «¿Tiene Ana un hermano?»
        cl = (self._canon_rel(o.cab)[0] if o.cab in REL_CANON else self._clase_sn(o)[0]) if o.cab else ""
        if cl:
            xs = [r for r in self.rels(cl, y=s)]
            if xs:
                self.ult_just = {"pasos": xs[0]["j"]}
                nombres = [self.disp(r["x"]) for r in xs if not r["x"].startswith("I:")]
                return self._ok(self._fin("Sí" + (", " + self._lista([self._frase_rel(cl, r["x"], s) for r in xs if not r["x"].startswith("I:")][:3]) if nombres else f", {'tienes' if s == 'U' else self.disp(s) + ' tiene'} {self._un(cl, M.genero_sust(cl))}")))
        viejos = [f for f in fs if not f.get("vig", True) and not f.get("neg")]
        if viejos:
            return self._ok(self._fin("Ya no. Antes sí: " + self.frase(viejos[0], tiempo="imp")), {"dicho": [viejos[0]["src"]]})
        ten = [f for f in self.marcos(v="tener", s=s, neg=False) if f.get("obj_cls") != "año"]
        if ten:
            return self._abst(self._fin("No me consta. Solo sé que " + self._tener_lista(s, ten)))
        if s.startswith("K:") or not self._conocido(s):
            return self._abst("No lo sé.", consultar=True)
        return self._abst(self._fin("No lo sé: no me has dicho qué " + ("tienes" if s == "U" else "tiene " + self.disp(s))))

    def _tener_lista(self, s, ten):
        objs = [cambia_persona(f["obj_disp"]) for f in ten if f.get("obj_disp")]
        objs = list(dict.fromkeys(objs))
        return ("tienes " if s == "U" else self.disp(s) + (" tienen " if self._persona_de(s) == "3p" else " tiene ")) + self._lista(objs)

    def _edad(self, s):
        fs = [f for f in self.marcos(v="tener", s=s, neg=False) if f.get("obj_cls") == "año" and f.get("cuant") is not None]
        nac = [f for f in self.marcos(v="nacer", s=s, neg=False) if re.search(r"\b(1[0-9]\d\d|20\d\d)\b", f.get("cuando", "") or "")]
        if fs and not (nac and self.F.index(nac[-1]) > self.F.index(fs[-1])):   # 2.11: manda lo último que se ha dicho
            return int(fs[-1]["cuant"]), {"dicho": [fs[-1]["src"]]}
        y, mes, dia, pasos = self._fecha_nac(s)
        if y:
            hoy = getattr(self.mem, "today", None) or dt.date.today()
            a = hoy.year - y
            if mes and (mes < hoy.month or (mes == hoy.month and dia and dia <= hoy.day)):
                return a, {"pasos": pasos + [f"hoy es {hoy.day} de {_MESES[hoy.month - 1]} de {hoy.year}"]}
            if mes and (mes > hoy.month or (mes == hoy.month and dia and dia > hoy.day)):
                return a - 1, {"pasos": pasos + [f"hoy es {hoy.day} de {_MESES[hoy.month - 1]} de {hoy.year}", "aún no ha llegado el cumpleaños de este año"]}
            return a, {"pasos": pasos + [f"estamos en {hoy.year}"], "aprox": True}
        return None

    def _fecha_nac(self, s):
        """(año, mes, día, frases) de la fecha de nacimiento, juntando lo dicho («nací en 1988», «cumplo años el 5 de marzo»)."""
        y = mes = dia = None
        pasos = []
        for f in self.marcos(v="nacer", s=s, neg=False) + self.marcos(v="cumplir", s=s, neg=False):
            c = sa(f.get("cuando", "") or "")
            m = re.search(r"\b(1[0-9]\d\d|20\d\d)\b", c)
            if m and f["v"] == "nacer":
                y = int(m.group(1))
            mm = re.search(r"\b(\d{1,2}|primero|uno) de (" + "|".join(_MESES) + r")\b", c)
            if mm:
                dia = 1 if mm.group(1) in ("primero", "uno") else int(mm.group(1))
                mes = _MESES.index(mm.group(2)) + 1
            else:
                mm = re.search(r"\ben (" + "|".join(_MESES) + r")\b", c)
                if mm:
                    mes = _MESES.index(mm.group(1)) + 1
            if m or mm:
                pasos.append(self.frase(f))
        return y, mes, dia, pasos

    # ================================================================== comparaciones
    def _orden(self, adj):
        """Pares (mayor, menor, src) para un adjetivo, con sus contrarios y transitividad."""
        base = []
        contr = _ANT.get(adj, set())
        for f in self.F:
            if not f.get("comp") or not f.get("vig", True) or f.get("neg"):
                continue
            op, a, e2 = f["comp"]
            x, y = self.can(f["s"]), self.can(e2)
            if op == "tan":
                continue                                # la igualdad la trata _iguales
            if a == adj:
                base.append((x, y, self.frase(f)) if op == "mas" else (y, x, self.frase(f)))
            elif a in contr:
                base.append((y, x, self.frase(f)) if op == "mas" else (x, y, self.frase(f)))
        if adj in ("mayor", "viejo", "menor", "joven"):
            edades = {}
            for f in self.F:
                if f["v"] == "tener" and f.get("obj_cls") == "año" and f.get("vig", True) and f.get("cuant") is not None:
                    edades[self.can(f["s"])] = (f["cuant"], self.frase(f))
            es = list(edades.items())
            for a_, (na, fa) in es:
                for b_, (nb, fb) in es:
                    if na > nb:
                        base.append((a_, b_, fa + " y " + fb) if adj in ("mayor", "viejo") else (b_, a_, fa + " y " + fb))
        iguales = self._iguales(adj)                     # 2.11: «A es tan alta como B»: lo que vale para B vale para A
        for (p_, q_), j_ in list(iguales.items()):
            for a, b, j in list(base):
                if b == q_ and a != p_:
                    base.append((a, p_, j + "; " + j_))
                if a == q_ and b != p_:
                    base.append((p_, b, j_ + "; " + j))
        cierre = {(a, b): [j] for a, b, j in base}
        cambio = True
        while cambio:
            cambio = False
            for (a, b), j1 in list(cierre.items()):
                for (b2, c), j2 in list(cierre.items()):
                    if b == b2 and a != c and (a, c) not in cierre:
                        cierre[(a, c)] = j1 + j2; cambio = True
        return cierre

    def _iguales(self, adj):
        """Pares (A, B) con «A es tan ADJ como B» (simétrico), con la frase que lo dice."""
        out = {}
        contr = _ANT.get(adj, set())
        for f in self.F:
            if f.get("comp") and f.get("vig", True) and not f.get("neg") and f["comp"][0] == "tan" and (f["comp"][1] == adj or f["comp"][1] in contr):
                x, y = self.can(f["s"]), self.can(f["comp"][2])
                out[(x, y)] = self.frase(f); out[(y, x)] = self.frase(f)
        return out

    def _compara_q(self, C, s):
        op, adj, sn2 = C.comp
        if sn2 is None:
            return None
        e2 = self._q_ent(sn2)
        if e2 is None or isinstance(e2, list) or str(e2).startswith("?"):
            return self._no_conozco(sn2, e2)
        e2 = self.can(e2)
        ig = self._iguales(adj)
        if (s, e2) in ig:                               # 2.11: igualdad
            self.ult_just = {"dicho": []}
            if op == "tan":
                return self._ok(self._fin("Sí, " + ig[(s, e2)]))
            return self._ok(self._fin("No: " + ig[(s, e2)]))
        orden = self._orden(adj)
        g = self.gen(s)
        adj_d = self._acento(M.concuerda(adj, g))
        mas = "" if adj in ("mayor", "menor", "mejor", "peor") else "más "
        if (s, e2) in orden:
            self.ult_just = {"pasos": orden[(s, e2)]}
            if op == "mas":
                return self._ok(self._fin(f"Sí, {self.disp(s)} es {mas}{adj_d} que {self.disp(e2)}"))
            return self._ok(self._fin(f"No, {self.disp(s)} es {mas}{adj_d} que {self.disp(e2)}"))
        if (e2, s) in orden:
            self.ult_just = {"pasos": orden[(e2, s)]}
            adj2 = self._acento(M.concuerda(adj, self.gen(e2)))
            if op == "mas":
                return self._ok(self._fin(f"No, {self.disp(e2)} es {mas}{adj2} que {self.disp(s)}"))
            return self._ok(self._fin(f"Sí, {self.disp(e2)} es {mas}{adj2} que {self.disp(s)}"))
        return self._abst(self._fin(f"No lo sé: no tengo datos para comparar a {self.disp(s)} con {self.disp(e2)} en eso"))

    def _por_medida(self, verbo, op, cands):
        vals = {}
        for f in self.F:
            if f["v"] == verbo and f.get("vig", True) and not f.get("neg") and f.get("cuant") is not None and f["s"]:
                vals[self.can(f["s"])] = (f["cuant"], self.frase(f))
        ents = [e for e in (cands or list(vals)) if e in vals]
        if len(ents) < 2 or (cands and len(ents) < len(cands)):
            return None
        mejor = max(ents, key=lambda e: vals[e][0]) if op == "mas" else min(ents, key=lambda e: vals[e][0])
        self.ult_just = {"pasos": [vals[e][1] for e in ents]}
        return mejor, vals

    def _quien_mas(self, C, adj, op, cands):
        medida = {"alto": ("medir", "mas"), "bajo": ("medir", "menos"), "pesado": ("pesar", "mas"), "ligero": ("pesar", "menos"), "caro": ("costar", "mas"), "barato": ("costar", "menos"),
                  "pequeño": ("tener", "menos"), "grande": ("tener", "mas")}.get(adj)
        orden = self._orden(adj)
        if medida and not any((a in cands and b in cands) for a, b in orden) and medida[0] != "tener":
            r = self._por_medida(medida[0], medida[1] if op == "mas" else {"mas": "menos", "menos": "mas"}[medida[1]], cands)
            if r:
                mejor, vals = r
                mas = "más " if op == "mas" else "menos "
                return self._ok(self._fin(f"{self.disp(mejor)} es {mas}{self._acento(M.concuerda(adj, self.gen(mejor)))}: {vals[mejor][1]}"))
        if adj in ("pequeño", "grande") and not orden:
            return self._quien_mas(C, "menor" if adj == "pequeño" else "mayor", op, cands)
        ents = set()
        for a, b in orden:
            ents.add(a); ents.add(b)
        if cands:
            ents = [e for e in cands]
        else:
            ents = list(ents)
        if len(ents) < 2:
            return self._abst("No lo sé: no tengo comparaciones sobre eso.")
        mejor = None
        for e in ents:
            if all(e == o or ((e, o) in orden if op == "mas" else (o, e) in orden) for o in ents):
                mejor = e
        if mejor is None:
            return self._abst("No lo sé: con lo que me has dicho no puedo ordenarlos.")
        pasos = []
        for o in ents:
            if o != mejor:
                pasos += orden[(mejor, o)] if op == "mas" else orden[(o, mejor)]
        self.ult_just = {"pasos": list(dict.fromkeys(pasos))}
        mas = "" if adj in ("mayor", "menor", "mejor", "peor") else ("más " if op == "mas" else "menos ")
        adj_d = self._acento(M.concuerda(adj, self.gen(mejor)))
        resto = [o for o in ents if o != mejor]
        if len(resto) == 1:
            return self._ok(self._fin(f"{self.disp(mejor)} es {mas}{adj_d} que {self.disp(resto[0])}" if mejor != "U" else f"Tú eres {mas}{adj_d} que {self.disp(resto[0])}"))
        art = "la" if self.gen(mejor) == "f" else "el"
        return self._ok(self._fin(f"{self.disp(mejor)} es {art} {mas}{adj_d}"))

    # ================================================================== gustar
    def _dat_ev_q(self, C, prep):
        if C.v not in G.DAT_EV:
            return False
        cl = list(C.clit or [])
        if not any(c in ("me", "te", "le", "les", "nos") for c in cl):
            return False
        return "se" in cl or C.dat is not None or prep == "a" or any(p_ == "a" for p_, _ in C.comps)

    def _gustar_q(self, C, wh):
        v = C.v
        exp = None
        if C.dat is not None:
            exp = self._q_ent(C.dat)
            if exp is None or str(exp).startswith("?"):
                return self._no_conozco(C.dat, exp)
        elif any(p_ == "a" for p_, _ in C.comps):
            sn_a = [s_ for p_, s_ in C.comps if p_ == "a"][0]
            exp = self._q_ent(sn_a)
            C.comps = [(p_, s_) for p_, s_ in C.comps if p_ != "a"]
            if exp is None or str(exp).startswith("?"):
                return self._no_conozco(sn_a, exp)
        elif "me" in C.clit:
            exp = "U"
        elif "te" in C.clit:
            return None
        elif wh and wh["tipo"] == "quien" and wh["prep"] == "a":
            exp = None
        else:
            exp = self.ult_suj or self.ref3(persona=True)
        est = C.obj or C.suj
        if isinstance(exp, list):
            exp = exp[0]
        afines = {"gustar": ("gustar", "encantar", "fascinar", "apasionar", "chiflar"), "encantar": ("encantar", "fascinar", "gustar")}.get(v, (v,))
        fs = [f for f in self.F if f["v"] in afines and f.get("vig", True) and f.get("exp") and (exp is None or self.can(f["s"]) == self.can(exp))]
        if wh and wh["tipo"] == "quien":
            ms = [f for f in fs if not f.get("neg") and self._coincide_obj(f, est)]
            if not ms:
                return self._abst("No lo sé: nadie me ha dicho eso.")
            self.ult_just = {"dicho": [f["src"] for f in ms]}
            return self._ok(self._fin(self._lista_frases(ms)))
        if exp is None:
            return self._aclara()
        exp = self.can(exp)
        self.mencionar(exp); self.ult_suj = exp
        if wh and wh["tipo"] in ("que", "cual"):
            ms = [f for f in fs if bool(f.get("neg")) == bool(C.neg)]
            if wh.get("sust") and wh["sust"] not in ("cosa", "cosas", "algo"):
                filtrados = [f for f in ms if f.get("obj") and (self.es_clase(f["obj"], wh["sust"], lexico_ok=True)[0] or f.get("obj_cls") == wh["sust"])]
                ms = filtrados or [f for f in ms if not (f.get("obj") and self.clases(f["obj"]))]
            if not ms:
                return self._abst(self._fin(f"No lo sé: no me has dicho qué {'te' if exp == 'U' else 'le'} {M.conjugar(v, 'pres', '3s')}{'' if exp == 'U' else ' a ' + self.disp(exp)}"))
            self.ult_just = {"dicho": [f["src"] for f in ms]}
            return self._ok(self._fin(self._lista_frases(ms)))
        if est is None and not C.xinf and wh and wh.get("tipo") in ("donde", "cuando") and [f for f in fs if f.get("dat_ev")]:
            f = [f for f in fs if f.get("dat_ev")][-1]  # «¿Dónde se me cayó?»: lo último que se te cayó
            if wh["tipo"] == "donde" and not f.get("comps") or wh["tipo"] == "cuando" and not f.get("cuando"):
                return self._abst(self._fin(f"No me lo has dicho. Solo sé que {self.frase(f)}"))
            return self._ok(self._fin(_cap(self.frase(f))), {"dicho": [f["src"]]})
        if est is None and not C.xinf:
            return None
        ms = [f for f in fs if (self._coincide_obj(f, est) if est is not None else sa(f.get("xinf", "")) == sa(C.xinf))]
        if ms:
            f = ms[0]
            if wh and wh.get("tipo") in ("donde", "cuando", "como", "porque"):
                if wh["tipo"] == "donde" and not f.get("comps") or wh["tipo"] == "cuando" and not f.get("cuando"):
                    return self._abst(self._fin(f"No me lo has dicho. Solo sé que {self.frase(f)}"))
                return self._ok(self._fin(_cap(self.frase(f))), {"dicho": [f["src"]]})
            return self._ok(self._fin(("No, " if f.get("neg") else "Sí, ") + self.frase(f)), {"dicho": [f["src"]]})
        if est is not None and v in ("gustar", "encantar"):
            # «Odio las lentejas» / «Adoro el té» también responden a «¿Me gustan…?»
            for f in self.marcos(v=None, s=exp, neg=False):
                if f["v"] in ("odiar", "detestar", "aborrecer") and self._coincide_obj(f, est):
                    return self._ok(self._fin("No, " + self.frase(f)), {"dicho": [f["src"]]})
                if f["v"] in ("adorar", "amar") and self._coincide_obj(f, est) and not self.es_persona(f.get("obj") or ""):
                    return self._ok(self._fin("Sí, " + self.frase(f)), {"dicho": [f["src"]]})
            if est.det == "d" and est.cab:
                cl_e = self._clase_sn(est)[0]
                mismos = [f for f in fs if f.get("obj_cls") == cl_e or str(f.get("obj_cls") or "").startswith(cl_e + " ")]
                if len(mismos) == 1:            # «¿Le gustó la película?» tras «no le gustó una película de miedo»
                    f = mismos[0]
                    return self._ok(self._fin(("No, " if f.get("neg") else "Sí, ") + self.frase(f)), {"dicho": [f["src"]]})
        if fs:
            return self._abst(self._fin("No lo sé. Solo sé que " + self._lista_frases([f for f in fs][:3])))
        return self._abst(self._fin(f"No lo sé: no me has dicho qué {'te' if exp == 'U' else 'le'} gusta{'' if exp == 'U' else ' a ' + self.disp(exp)}"))

    _T_EXPR = re.compile(r"\b(?:lunes|martes|miercoles|jueves|viernes|sabados?|domingos?|fines? de semana|por la (?:mañana|tarde|noche)|de (?:lunes|martes|miercoles|jueves|viernes|sabado|domingo) a|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|verano|invierno|otoño|primavera|a las \d+|todos los dias|cada (?:dia|semana|mes)|navidad)\b")

    def _cuando_por_texto(self, C, s):
        """«¿Cuándo trabajo?» con «trabajas de lunes a viernes»: el tiempo va como complemento."""
        fs = [f for f in self.marcos(v=C.v, s=s, vig=True, neg=False) if not f.get("cuando") and not f.get("freq")]
        fs = [f for f in fs if self._T_EXPR.search(sa(self.frase(f))) and self._coincide_obj(f, C.obj if C.obj is not None and not (C.obj.propio and self._q_ent(C.obj) == s) else None)]
        if not fs:
            return None
        self.ult_just = {"dicho": [f["src"] for f in fs]}
        return self._ok(self._fin(self._lista([self.frase(f) for f in fs[:2]])))

    def _lista_frases(self, fs):
        """Une marcos del mismo sujeto y verbo en una sola oración."""
        if not fs:
            return ""
        if any(f.get("posible") for f in fs):
            return self._lista([self.frase(f) for f in fs])   # 2.11: el grupo «X o Y» se dice una vez
        miembros = {f.get("src") for f in fs if f.get("miembro")}
        if miembros:
            fs = [f for f in fs if not f.get("grupo_de")] or fs
        claves = {(self.can(f["s"]), f["v"], bool(f.get("neg")), f.get("t"), bool(f.get("exp"))) for f in fs}
        mismos_cc = len({(str([(p, d) for p, e, d in f.get("comps", [])]), f.get("cuando") or "", f.get("freq") or "") for f in fs}) == 1
        if len(claves) == 1 and all(f.get("obj_disp") for f in fs) and mismos_cc and len(fs) > 1:   # «compras tomates, cebollas y ajos para la cena»
            h = dict(fs[0])
            h["obj_disp"] = self._lista(list(dict.fromkeys(f["obj_disp"] for f in fs)))
            h["pl_obj"] = True
            return self.frase(h)
        if len({(f["v"], bool(f.get("neg")), f.get("obj_disp"), str([(p, d) for p, e, d in f.get("comps", [])]), f.get("t"), tuple(f.get("attr", []))) for f in fs}) == 1 and len(fs) > 1 and not fs[0].get("exp"):
            h = dict(fs[0]); h["pl_suj"] = True
            suj = [self.disp(f["s"]) for f in fs]
            if "tú" in suj:                             # 2.12: «Nerea, Iker y tú van a la piscina»
                suj = [x for x in suj if x != "tú"] + ["tú"]
                if len(suj) == 1:
                    return self._lista([self.frase(f) for f in fs])
            return self._lista(suj) + " " + self.frase(h, sin_sujeto=True)
        return self._lista([self.frase(f) for f in fs[:4]])

    # ================================================================== interrogativas parciales
    _PROPS_N = ("marca", "año", "modelo", "talla", "raza", "piso", "planta", "numero")

    _FORMAS = {"redondo", "cuadrado", "triangular", "rectangular", "ovalado", "alargado", "plano", "esferico"}

    def _xinf_q(self, C, tipo, prep, s, v):
        """«¿Adónde quiero ir?», «¿Con quién quiero ir?»: el dato está dentro del infinitivo («quiero ir a Italia con mi hermana»)."""
        if not (C.xinf and isinstance(s, str) and not s.startswith("?") and tipo in ("donde", "quien", "cuando", "que")):
            return None
        inf0 = sa(C.xinf.split()[0])
        for f in reversed(self.marcos(v=v, s=s, vig=True, neg=bool(C.neg))):
            xi = sa(f.get("xinf") or "")
            if not xi.startswith(inf0) or xi == inf0:
                continue
            resto = " " + xi[len(inf0):] + " "
            if (tipo == "donde" and re.search(r" (?:a|al|en|hasta|hacia) ", resto)) or (tipo == "quien" and prep and re.search(" " + prep + " ", resto)) \
                    or (tipo == "cuando" and (f.get("cuando") or re.search(r" (?:este|esta|el|la|en|mañana|hoy|pasado|proximo|que viene)\b", resto))):
                self.ult_just = {"dicho": [f["src"]]}
                extra = self._fecha_abs(f.get("cuando", ""), f) if tipo == "cuando" and f.get("cuando") else ""
                return self._ok(self._fin(_cap(self.frase(f)) + (f" ({extra})" if extra else "")))
        return None

    def _que_nombre(self, p):
        """«¿Qué clases he empezado?» con «empecé a ir a clases de cerámica»: el nombre aparece dentro de lo que se dijo."""
        m = re.match(r"^¿?\s*(?:[Yy]\s+)?[Qq]u[ée]\s+([a-záéíóúñ]+)\s+((?:he|has|ha|hemos|me|te|se)\s+)?([a-záéíóúñ]+)\s*\?$", p.strip())
        if not m:
            return None
        nom = sa(m.group(1))
        if M.analizar(nom) or nom in ("color", "forma", "hora", "dia", "tal", "marca", "año", "tipo"):
            return None
        vb = m.group(3)
        an = [x for x in M.analizar(sa(vb)) if x[1] in ("pres", "pret", "imp", "fut", "part")]
        aux = sa(m.group(2) or "").strip()
        per = {"he": "1s", "has": "2s", "hemos": "1p", "me": "1s", "te": "2s"}.get(aux) or (an[0][2] if an else "")
        if not an or per not in ("1s", "1p", "2s"):
            return None
        v, s_ = an[0][0], ("U" if per in ("1s", "1p") else "L")
        raiz = sa(M.singular(nom))
        for f in reversed(self.marcos(v=v, s=s_, vig=True, neg=False)):
            txt_ = sa(" ".join([f.get("obj_disp") or "", f.get("xinf") or ""] + [d2 or "" for _, _, d2 in f.get("comps", [])]))
            if re.search(r"\b" + re.escape(raiz) + r"(?:s|es)?\b", txt_):
                self.ult_just = {"dicho": [f["src"]]}
                return self._ok(self._fin(_cap(self.frase(f))))
        return None

    def _de_que_color_v(self, p):
        """«¿De qué color pintaremos la cocina?» con «la pintaremos de blanco»: el «de + color» de esa acción."""
        m = re.match(r"^¿?\s*(?:[Yy]\s+)?[Dd]e qu[ée] color\s+([a-záéíóúñ]+)\s+(.+?)\s*\?$", p.strip())
        if not m:
            return None
        an = [x for x in M.analizar(sa(m.group(1))) if x[1] in ("pres", "pret", "imp", "fut", "cond") and x[0] not in ("ser", "estar", "tener")]
        if not an:
            return None
        v = an[0][0]
        s = {"1s": "U", "1p": "U", "2s": "L"}.get(an[0][2])
        e_o = self._sn_ent(m.group(2))
        from . import vista as V
        for f in reversed(self.F):
            if f.get("v") != v or (s and self.can(f.get("s") or "") != s) or not f.get("vig", True):
                continue
            if e_o and f.get("obj") and self.can(f["obj"]) != e_o:
                continue
            col = [d2 for p2, _, d2 in f.get("comps", []) if p2 == "de" and d2 and sa(M.masc(d2.split()[-1])) in V.NOMBRES_SA]
            if col:
                self.ult_just = {"dicho": [f["src"]]}
                return self._ok(self._fin(_cap(self.frase(f))))
        return None

    def _sigue_vivo(self, p):
        """«¿Mi abuelo vive?» / «¿Sigue vivo?» con «mi abuelo murió hace dos años»."""
        m = re.match(r"^¿?\s*(?:[Yy]\s+)?(.+?)\s+(?:vive|sigue vivo|sigue viva|está vivo|está viva|esta vivo|esta viva)\s*\?$", p.strip())
        if not m:
            return None
        e = self._sn_ent(m.group(1))
        if not e or e in ("U", "L"):
            return None
        fs = [f for f in self.marcos(v="morir", s=e, vig=True, neg=False)]
        if fs:
            self.ult_just = {"dicho": [fs[-1]["src"]]}
            return self._ok(self._fin("No: " + self.frase(fs[-1])))
        return None

    def _mi_opinion(self, p):
        """«¿Qué creo?», «¿Qué pienso de Mario?»: las opiniones que la persona ha dado (no son hechos)."""
        m = re.match(r"^¿?\s*(?:[Yy]\s+)?[Qq]u[ée]\s+(?:creo|pienso|opino)(?:\s+(?:de|sobre)\s+(.+?))?(?:\s+yo)?\s*\?$", p.strip())
        if not m:
            return None
        fs = [f for f in self.F if f.get("v") == "creer" and f.get("s") == "U" and f.get("dicho") and f.get("vig", True)]
        if m.group(1):
            clave = sa(m.group(1).split()[-1].lower())
            fs = [f for f in fs if clave in sa(f.get("obj_disp", "").lower())]
        if not fs:
            return self._abst("No lo sé: no me has dado tu opinión sobre eso.")
        self.ult_just = {"dicho": [f["src"] for f in fs]}
        return self._ok(self._fin("Me dijiste que crees " + self._lista([f["obj_disp"] for f in fs[-2:]])))

    def _cuantas_veces(self, p):
        """«¿Cuántas veces voy al gimnasio?» con «voy tres veces por semana» (el sitio puede ir implícito)."""
        m = re.match(r"^¿?\s*(?:[Yy]\s+)?[Cc]u[áa]ntas veces\s+(?:(?:a la|al|por)\s+\w+\s+)?([a-záéíóúñ]+)\b(.*?)\s*\?$", p.strip())
        if not m:
            return None
        an = [x for x in M.analizar(sa(m.group(1))) if x[1] in ("pres", "pret", "imp")]
        if not an or an[0][2] not in ("1s", "2s"):
            return None
        v, s = an[0][0], ("U" if an[0][2] == "1s" else "L")
        fs = [f for f in self.marcos(v=v, s=s, vig=True, neg=False) if re.search(r"\b(?:veces|vez)\b", sa(f.get("freq") or "") + " " + " ".join(f.get("modo", [])))]
        if fs:
            self.ult_just = {"dicho": [fs[-1]["src"]]}
            return self._ok(self._fin(_cap(self.frase(fs[-1]))))
        return None

    def _nombre_por_adj(self, p):
        """«¿Cómo se llama el perro pequeño?»: entre los de esa clase, el que tiene ese adjetivo."""
        m = re.match(r"^¿?\s*(?:[Yy]\s+)?[Cc][óo]mo se llama\s+(?:el|la|mi|tu)\s+([a-záéíóúñ]+)\s+([a-záéíóúñ]+)\s*\?$", p.strip())
        if not m:
            return None
        cl, adj = sa(M.masc(m.group(1))) if m.group(1) not in REL_DISP_BASE else sa(m.group(1)), sa(M.masc(m.group(2)))
        cands = [k for k, d in self.E.items() if k.startswith("N:") and k not in self.eq and (d.get("clase") == cl or d.get("clase") == sa(m.group(1)))]
        if len(cands) < 2:
            return None
        con = [k for k in cands if any(adj in [sa(M.masc(a_)) for a_ in f.get("attr", [])] for f in self.marcos(v="ser", s=k, vig=True, neg=False))]
        if len(con) == 1:
            k = con[0]
            self.ult_just = {"dicho": [f["src"] for f in self.marcos(v="ser", s=k, vig=True, neg=False)]}
            return self._ok(self._fin(f"Se llama {self._nombre_de(k)}: {self.frase(self.marcos(v='ser', s=k, vig=True, neg=False)[-1])}"))
        return self._abst(f"No lo sé: no me has dicho cuál de tus {M.plural(m.group(1))} es {m.group(2)}.") if not con else None

    def _mismo_color(self, p):
        """«¿Bigotes es del mismo color que mi bici?»: los dos colores dichos (o vistos), comparados."""
        m = re.match(r"^¿?\s*(?:[Yy]\s+)?(.+?)\s+(?:es|son|tiene|tienen)\s+(?:del mismo color|el mismo color|igual de color)\s+que\s+(.+?)\s*\?$", p.strip())
        if not m:
            return None
        from . import vista as V
        e1, e2 = self._sn_ent(m.group(1)), self._sn_ent(m.group(2))
        if not e1 or not e2:
            return None
        c1, c2 = V._colores_ent(self, e1), V._colores_ent(self, e2)
        if not c1 or not c2:
            falta = self.disp(e1) if not c1 else self.disp(e2)
            return self._abst(f"No lo sé: no me has dicho de qué color es {falta}.")
        g1, g2 = self.gen(e1), self.gen(e2)
        d1 = f"{self.disp(e1)} es {V.color_adj(c1[-1], g1)}"; d2 = f"{self.disp(e2)} es {V.color_adj(c2[-1], g2)}"
        if set(c1) & set(c2):
            return self._ok(self._fin(f"Sí: {d1} y {d2}"))
        return self._ok(self._fin(f"No: {d1} y {d2}"))

    def _forma_de(self, p):
        """«¿Qué forma tiene la alfombra?» / «¿De qué forma es…?»: el adjetivo de forma que se dijo (o que se vio en una imagen)."""
        m = re.match(r"^¿?\s*(?:[Yy]\s+)?(?:[Qq]u[ée] forma tiene|[Dd]e qu[ée] forma (?:es|son)|[Qq]u[ée] forma tienen)\s+(.+?)\s*\?$", p.strip())
        if not m:
            return None
        e = self._sn_ent(m.group(1))
        if not e or e in ("U", "L"):
            return None
        for f in reversed(self.marcos(v="ser", s=e, vig=True, neg=False)):
            fa = [a_ for a_ in f.get("attr", []) if sa(M.masc(a_)) in self._FORMAS]
            if fa:
                self.ult_just = {"dicho": [f["src"]]}
                g, pl = self.gen(e), bool(self.E.get(e, {}).get("pl"))
                return self._ok(self._fin(f"{_cap(self.disp(e))} {'son' if pl else 'es'} {M.concuerda(M.masc(fa[0]), g, pl)}"))
        if self.marcos(s=e, vig=True):
            return self._abst(f"No lo sé: no me has dicho qué forma tiene {self.disp(e)}.")
        return None

    def _que_hacer(self, p):
        """«¿Qué (no) quiere hacer mi novia?»: el infinitivo que acompaña a querer/poder/necesitar/preferir/odiar."""
        m = re.match(r"^¿?\s*(?:[Yy]\s+)?[Qq]u[ée]\s+(no\s+)?(quiere|quieren|quería|querían|quieres|quiero|necesita|necesitan|prefiere|prefieren|odia|odian|piensa|piensan|"
                     r"puede|pueden|sabe|saben|suele|suelen|intenta|intentan)\s+hacer\s+(.+?)\s*\?$", p.strip())
        if not m:
            return None
        v = M.analizar(m.group(2))[0][0] if M.analizar(m.group(2)) else None
        e = self._sn_ent(m.group(3))
        if not v or not e:
            return None
        neg = bool(m.group(1))
        fs = [f for f in self.marcos(v=v, s=e, vig=True) if bool(f.get("neg")) == neg and (
            f.get("xinf") or (f.get("obj_cls") and any(x[1] == "inf" for x in M.analizar(sa(re.sub(r"(?:se|lo|la|le)$", "", f["obj_cls"]))))))]
        if fs:
            self.ult_just = {"dicho": [f["src"] for f in fs]}
            return self._ok(self._fin(_cap(self._lista([self.frase(f) for f in fs[-2:]]))))
        return None

    def _color_de_sn(self, p):
        """«¿De qué color era la moto?» con «vi una moto roja», «¿… son mis zapatillas?» con «me compré unas zapatillas blancas»:
        el color dicho como adjetivo del nombre en cualquier frase."""
        m = re.match(r"^¿?\s*(?:[Yy]\s+)?[Dd]e qu[ée] color\s+(es|son|era|eran|fue|fueron)\s+(.+?)\s*\?$", p.strip())
        if not m:
            return None
        sn_ = self._sn_de(m.group(2))
        if sn_ is None or not sn_.cab:
            return None
        cab = sa(M.singular(sn_.cab.split()[0]))
        e = self._sn_ent(m.group(2))
        if e:
            from . import vista as V
            if V._colores_ent(self, e):
                return None                             # ya hay un color dicho para esa cosa: lo contesta el camino de siempre
        dueno = None
        if sn_.pos == "U":
            dueno = "U"
        elif sn_.de is not None:
            dueno = self._sn_ent(sn_.de.texto)
        cands = []
        for f in self.F:
            if not f.get("vig", True) or f.get("neg") or not f.get("obj_disp"):
                continue
            od = sa(f["obj_disp"]).lower().split()
            if not od or sa(M.singular(f.get("obj_cls") or "")) != cab and cab not in [sa(M.singular(w)) for w in od]:
                continue
            if not any(sa(M.masc(M.singular(w))) in COLORES for w in od):
                continue
            if dueno and self.can(f.get("s") or "") != self.can(dueno) and not str(f.get("obj") or "").endswith("@" + str(dueno)):
                continue
            cands.append(f)
        if cands:
            self.ult_just = {"dicho": [cands[-1]["src"]]}
            return self._ok(self._fin(_cap(self.frase(cands[-1]))))
        return None

    def _que_le_pasa(self, p):
        """«¿Qué le pasa a mi coche?»: lo que se ha dicho que hace o tiene de malo."""
        m = re.match(r"^¿?\s*(?:[Yy]\s+)?[Qq]u[ée]\s+(?:le|les)\s+(?:pasa|ocurre|sucede|pasaba|pasó|ocurrió|ha pasado)\s+a\s+(.+?)\s*\?$", p.strip())
        if not m:
            return None
        e = self._sn_ent(m.group(1))
        if not e or e in ("U", "L"):
            return None
        malos = []
        for f in self.marcos(vig=True):
            if f.get("v") == "tener" and self.can(f.get("s") or "") != e and any(self.can(c_[1] or "") == e for c_ in f.get("comps", [])) \
                    and sa(f.get("obj_disp") or "").split()[-1:] in (["problema"], ["averia"], ["fallo"], ["golpe"]):
                malos.append(f)
            elif self.can(f.get("s") or "") == e and f.get("v") not in ("ser", "llamar") and not f.get("neg") and not (f.get("v") == "tener" and f.get("obj_cls") in ("año", "ano")):
                malos.append(f)
        if not malos:
            if self.marcos(s=e, vig=True):
                return self._abst(f"No me has dicho que le pase nada a {self.disp(e)}.")
            return None
        concretos = [f for f in malos if f.get("v") != "tener" or self.can(f.get("s") or "") == e]
        fs = concretos or malos
        self.ult_just = {"dicho": [f["src"] for f in fs]}
        return self._ok(self._fin(_cap(self._lista([self.frase(f) for f in fs[-2:]]))))

    def _propiedad_de(self, p):
        """«¿De qué marca es mi coche?», «¿Qué año tiene / de qué año es?»: un dato dicho como «X es de la marca Y»."""
        m = re.match(r"^¿?\s*(?:[Yy]\s+)?(?:[Dd]e\s+)?[Qq]u[ée]\s+(\w+)\s+(?:es|son|era)\s+(.+?)\s*\?$", p.strip())
        if not m or sa(m.group(1)) not in {sa(x) for x in self._PROPS_N}:
            return None
        prop = sa(m.group(1))
        sn_ = self._sn_de(m.group(2))
        e = self.ent_de(sn_, crear=False) if sn_ is not None else None
        if not isinstance(e, str) or e.startswith("?"):
            return None
        e = self.can(e)
        for f in reversed(self.marcos(v="ser", s=e, vig=True, neg=False)):
            for p_, x_, d_ in f.get("comps", []):
                if d_ and re.search(r"\b" + prop + r"\b", sa(d_)) or prop == "ano" and d_ and re.search(r"\b(?:19|20)\d\d\b", d_):
                    self.ult_just = {"dicho": [f["src"]]}
                    return self._ok(self._fin(_cap(self.frase(f))))
        if self.marcos(s=e, vig=True):
            art = "qué " + m.group(1).lower()
            return self._abst(f"No lo sé: no me has dicho de {art} es {self.disp(e)}.")
        return None

    def _interroga(self, C: Clausula, wh) -> Optional[dict]:
        tipo, prep, sust = wh["tipo"], wh["prep"], wh["sust"]
        if tipo == "cuando" and getattr(self, "_preg_hora", False):
            self._preg_hora = False
            s_h, sn_h, o_h = self._sujeto_preg(C, wh=tipo)
            if isinstance(s_h, str) and not s_h.startswith("?"):
                fs_h = [f for f in self.marcos(s=s_h, vig=True, neg=False) if re.search(r"\ba las? \w+|\ba la una\b|\d+:\d+", sa(f.get("cuando") or ""))]
                if fs_h:                                # la hora concreta, no solo el día
                    self.ult_just = {"dicho": [fs_h[-1]["src"]]}
                    return self._ok(self._fin(_cap(self.frase(fs_h[-1]))))
        if tipo == "paraque":
            s_, sn_s, o_ = self._sujeto_preg(C, wh="que")
            if C.obj is not None and C.obj2 is not None:  # «¿Para qué me hace la comida mi novio?»: el sujeto es la persona
                for x_ in (C.obj2, C.obj):
                    e_ = self._q_ent(x_)
                    if isinstance(e_, str) and not e_.startswith("?") and self.es_persona(e_):
                        s_ = e_
                        break
            q_txt = sa(getattr(self, "ult_preg", ("", None))[0] or "")
            if not (isinstance(s_, str) and not s_.startswith("?") and self.es_persona(s_)):
                for f in reversed(self.marcos(v=C.v, vig=None, neg=False)):
                    nom_ = sa(self.disp(f["s"])).split()[-1] if f.get("s") else ""
                    if nom_ and re.search(r"\b" + re.escape(nom_) + r"\b", q_txt) and any(p2 == "para" for p2, _, _ in f.get("comps", [])):
                        s_ = self.can(f["s"])           # «¿Para qué me hace la comida mi novio?»
                        break
            if isinstance(s_, str) and not s_.startswith("?"):
                def _qc(f):                             # «a Laura» en la pregunta es el objeto del marco
                    return [c_ for c_ in C.comps if c_[0] != "para" and not (c_[0] == "a" and f.get("obj") and self._q_ent(c_[1]) == self.can(f["obj"]))]
                fs_p = [f for f in self.marcos(v=C.v, s=s_, vig=None, neg=False) if any(p2 == "para" for p2, _, _ in f.get("comps", [])) and self._coincide_comps(f, _qc(f))
                        and self.prep_con_papel(f, "para", {"finalidad"})]   # «trabaja para un hotel» no dice para qué
                if fs_p:                                # «¿Para qué he quedado con Natalia?» con «…para tomar un café»
                    f = fs_p[-1]
                    d_ = [d2 or self.disp(e2) for p2, e2, d2 in f["comps"] if p2 == "para"][0]
                    self.ult_just = {"dicho": [f["src"]]}
                    return self._ok(self._fin("Para " + cambia_persona(d_)))
            return None
        if C.v == "ir" and C.xinf and not any(p_ == "a" for p_, _ in C.comps):
            vx = [x for x in M.analizar(C.xinf.split()[0]) if x[1] == "inf"]
            if vx:                                      # «¿Qué vamos a adoptar?» = «¿Qué adoptaremos?»
                resto_x = C.xinf.split()[1:]
                C.v = vx[0][0]; C.xinf = " ".join(resto_x); C.tiempo = "fut"
                if C.pers == "1p":
                    C.pers = "1s"
        if tipo == "donde" and C.v == "ser" and C.tiempo == "pret":
            C.v = "ir"                                   # «¿Adónde fui?»: «fui» es de «ir», no de «ser»
        v = C.v
        if tipo == "que" and sust in ("dia", "hora", "fecha", "mes", "año", "tiempo", "tal", "significado", "diferencia", "tipo", "clase", "numero", "estacion") and not (sust == "año" and False):
            return None
        if v in G.GUSTAR and (C.clit or C.dat or prep == "a"):
            return self._gustar_q(C, wh)
        if self._dat_ev_q(C, prep) and [f for f in self.F if f.get("dat_ev") and f["v"] == v]:
            return self._gustar_q(C, wh)                # «¿Qué le está saliendo a mi hija?», «¿A quién se le rompió el móvil?»
        if tipo == "porque":
            return self._por_que(C)
        if tipo == "que" and ((v == "dedicar" and prep == "a") or (v == "trabajar" and prep in ("en", "de")) and not sust):
            s, sn_s, o = self._sujeto_preg(C, wh="que")
            if s in (None, "L") or isinstance(s, list) or str(s).startswith("?"):
                return self._no_conozco(sn_s, s) if (sn_s is not None and s != "L") else None
            s = self.can(s)
            self._recuerda_preg(self.ult_preg[0], sn_s)
            return self._que_hace(None, s, lambda extra="": self._abst(self._fin(f"No lo sé: no me has dicho a qué {'te dedicas' if s == 'U' else 'se dedica ' + self.disp(s)}") + (" " + self._se_de(s) if self._se_de(s) else "")), False, solo_trabajo=True)
        if v == "haber" and tipo in ("que", "quien", "cuanto") and C.comps:
            hay = [f for f in self.F if f["v"] == "haber" and f.get("vig", True) and not f.get("neg") and self._coincide_comps(f, C.comps)]
            if sust and tipo == "cuanto":
                hay = [f for f in hay if f.get("obj_cls") == (self._canon_rel(sust)[0] if sust in REL_CANON else sust)]
            fs = [f for f in self.F if f["v"] == "estar" and f.get("vig", True) and not f.get("neg") and self._coincide_comps(f, C.comps)] if tipo != "cuanto" else []
            if hay or fs:
                self.ult_just = {"dicho": [f["src"] for f in hay + fs]}
                lug = contrae(" ".join(p_.replace("_", " ") + " " + cambia_persona(d) for p_, e, d in (hay or fs)[0]["comps"]))
                trozos = ([f"{lug} hay {self._lista([cambia_persona(f['obj_disp']) for f in hay])}"] if hay else []) + ([self._lista_frases(fs)] if fs else [])
                return self._ok(self._fin(". ".join(_cap(t) for t in trozos)))
            return self._abst("No lo sé: no me has dicho qué hay ahí.")
        if tipo == "quien" and not prep:
            return self._quien(C)
        if tipo in ("que", "cual") and not prep and v in ("ser", "estar") and (C.comp or (C.attr and C.attr[0] in ("mayor", "menor", "mejor", "peor") and C.obj is None)):
            return self._quien(C)
        if tipo == "quien" and prep:
            if C.xinf:
                s_x = self._sujeto_preg(C, wh="quien")[0]
                r_x = self._xinf_q(C, tipo, prep, self.can(s_x) if isinstance(s_x, str) else s_x, v)
                if r_x is not None:
                    return r_x
            if prep == "con" and v in ("vivir", "trabajar", "salir", "jugar", "viajar", "estudiar", "casar", "hablar", "quedar", "cenar", "comer", "bailar"):
                s_c = "U" if (C.suj is None and C.pers == "1s") else ("L" if (C.suj is None and C.pers == "2s") else None)   # sin efectos secundarios
                if s_c and not [f for f in self.marcos(v=v, s=s_c, vig=True, neg=False) if any(p2 == "con" for p2, _, _ in f.get("comps", []))]:
                    rec = [f for f in self.F if f.get("v") == v and f.get("vig", True) and not f.get("neg") and any(p2 == "con" and self.can(e2 or "") == s_c for p2, e2, _ in f.get("comps", []))]
                    if rec:                             # «Carmen vive conmigo» -> «¿Con quién vivo?»: con Carmen
                        self.ult_just = {"dicho": [f["src"] for f in rec]}
                        return self._ok(self._fin(self._lista([_cap(self.frase(f)) for f in rec[-2:]])))
            return self._prep_quien(C, prep)
        s, sn_s, o = self._sujeto_preg(C, wh=tipo)
        self._recuerda_preg(self.ult_preg[0], sn_s)
        if s == "L":
            return None
        self._suj_lista = s if isinstance(s, list) else None
        if tipo == "cuanto" and prep == "con" and isinstance(s, str) and not s.startswith("?"):
            fs_c = [f for f in self.marcos(v=v, s=s, neg=False) if any(p2 == "con" for p2, _, _ in f.get("comps", []))]
            gr = [d2 for f in fs_c for p2, e2, d2 in f.get("comps", []) if p2 == "con" and d2 and re.match(r"^(?:\w+ )?(?:dos|tres|cuatro|cinco|seis|\d+) ", sa(d2))]
            if gr:                                      # «¿Con cuántas personas vivo?» con «vivo con dos chicas»
                self.ult_just = {"dicho": [fs_c[0]["src"]]}
                return self._ok(self._fin("Con " + cambia_persona(gr[0])))
        if tipo == "que" and prep in ("a", "de", "con", "en", "para", "sobre") and not sust and isinstance(s, str) and not s.startswith("?") and v not in ("ser", "estar", "dedicar", "trabajar"):
            fs_p = [f for f in self.marcos(v=v, s=s, vig=None, neg=False) if any(p2 == prep for p2, _, _ in f.get("comps", []))]
            if fs_p:                                    # «¿A qué jugaba?» con «jugabas al baloncesto»
                self.ult_just = {"dicho": [fs_p[-1]["src"]]}
                return self._ok(self._fin(_cap(self.frase(fs_p[-1]))))
        if isinstance(s, list) and tipo == "cuanto" and v == "llevar":
            return self._cuanto(C, self.can(s[0]), sn_s, o, sust, lambda extra="": self._abst("No lo sé."))
        if isinstance(s, list):
            if tipo == "como" and v == "llamar" and C.refl and sn_s is not None and len(s) > 1 and all(str(x).startswith("N:") for x in s):
                self.ult_just = {"dicho": list(dict.fromkeys(self.E.get(x, {}).get("src_nombre", "") for x in s))}
                quien = cambia_persona(sn_s.texto)
                return self._ok(self._fin(f"{quien} se llaman {self._lista([self.disp(x) for x in s])}"))
            s = s[0] if len(s) == 1 else None
            if s is None:
                return None
        if s is None or (isinstance(s, str) and s.startswith("?")):
            if tipo in ("cual", "que") and v == "ser" and sn_s is not None and sn_s.cab and (sn_s.pos or sn_s.de is not None) and not sust:
                return self._papel(sn_s, None)
            elif sn_s is not None:
                return self._no_conozco(sn_s, s)
            else:
                return None
        if s is not None:
            s = self.can(s)
            self.mencionar(s); self.ult_suj = s
        consultar = s is None or s.startswith("K:") or not self._conocido(s)
        pasado = C.tiempo in ("imp", "pret") or "antes" in sa(C.cuando)

        def nada(extra=""):
            if s is not None and not consultar:
                sab = self._se_de(s)
                return self._abst(self._fin("No lo sé" + (": " + extra if extra else "")) + (" " + sab if sab else ""))
            if sn_s is not None and sn_s.propio and not self._conocido(s):
                return self._no_conozco(sn_s, s)
            return self._abst("No lo sé.", consultar=True)

        # ---------- cómo
        if tipo == "como":
            if v == "llamar" and C.refl:
                if s is None:
                    return None
                nom = self._nombre_de(s)
                if s == "U":
                    if nom:
                        return self._ok(f"Te llamas {nom}.", {"dicho": [self.E["U"].get("src_nombre", "")]})
                    return self._abst("Todavía no me has dicho cómo te llamas.")
                g_q = (sn_s.gen or (M.genero_sust(sn_s.cab.split()[0]) if sn_s.cab else "")) if sn_s is not None else ""
                if nom and s.startswith("N:") and sn_s is not None and not sn_s.propio and g_q and self.gen(s) and g_q != self.gen(s) \
                        and self.E.get(s, {}).get("clase") in FAMILIA | PERSONA_CLS and not self.E.get(s, {}).get("gen") \
                        and re.search(r"\bse llaman\b", self.E.get(s, {}).get("src_nombre") or "", re.I):      # solo si el género salió del nombre, en un grupo
                    # «¿Cómo se llama mi sobrina?» y solo hay sobrinos que no constan como chicas
                    d0 = self.E[s]
                    otros = [k for k, d in self.E.items() if k.startswith("N:") and k not in self.eq and d.get("clase") == d0.get("clase")
                             and self.can(d.get("dueno") or "") == self.can(d0.get("dueno") or "") and self.gen(k) == g_q]
                    if len(otros) == 1:                 # «Tengo dos hijos, Pablo y Nerea» -> «¿Cómo se llama mi hija?» = Nerea
                        k = otros[0]; du = self.can(self.E[k]["dueno"])
                        desc = ("tu " + self._rel_nombre(self.E[k]["clase"], g_q)) if du == "U" else contrae(f"{'la' if g_q == 'f' else 'el'} {self._rel_nombre(self.E[k]['clase'], g_q)} de {self.disp(du)}")
                        return self._ok(self._fin(f"{desc} se llama {self._nombre_de(k)}"), {"dicho": [self.E[k].get("src_nombre", "")]})
                    return self._abst(f"No lo sé: no me has dicho que tengas {'una' if g_q == 'f' else 'un'} {self._rel_nombre(self.E[s]['clase'], g_q)}.")
                if nom and s.startswith("N:"):
                    d = self.E.get(s, {})
                    if d.get("clase") and d.get("dueno") and sn_s is not None and not sn_s.propio:
                        cl = d["clase"]; du = self.can(d["dueno"])
                        desc = ("tu " + self._rel_nombre(cl, self.gen(s))) if du == "U" else contrae(f"{'la' if self.gen(s) == 'f' else 'el'} {self._rel_nombre(cl, self.gen(s))} de {self.disp(du)}")
                        return self._ok(self._fin(f"{desc} se llama {nom}"), {"dicho": [d.get("src_nombre", "")]})
                    return self._ok(self._fin(f"Se llama {nom}"), {"dicho": [d.get("src_nombre", "")]})
                if s.startswith("I:"):
                    return self._abst(self._fin(f"Sé que existe {self.disp(s)}, pero no me has dicho cómo se llama"))
                return nada()
            if v in ("ser", "estar"):
                todos = [f for f in self.marcos(v=v, s=s, vig=not pasado or None, neg=False, herencia=True) if f.get("attr")]
                fs = [f for f in todos if not (set(f["attr"]) <= set(f.get("isa", [])))]
                if not fs and todos:
                    solo = [f for f in todos if self.can(f["s"]) == s and not any(f.get("isa_art", {}).get(a) for a in f["attr"])]
                    if solo:
                        self.ult_just = {"dicho": [f["src"] for f in solo]}
                        return self._ok(self._fin(self._lista_frases(solo)))
                if pasado:
                    fs = [f for f in fs if (not f.get("vig", True) or f.get("t") in ("imp", "pret")) and self._tiempo_ok(f, C)] or [f for f in fs if not f.get("vig", True) or f.get("t") in ("imp", "pret")]
                else:
                    pres = [f for f in fs if f.get("t") not in ("imp", "pret")]
                    if pres and v == "estar":
                        pres = pres[-1:] if any(set(pres[-1]["attr"]) & {"bien", "mal", "mejor", "peor", "regular", "fatal", "genial"} for _ in [0]) else pres
                    if not pres and fs:
                        f = fs[-1]
                        return self._abst(self._fin("No sé cómo " + M.conjugar(v, "pres", self._persona_de(s)) + " ahora. Lo último que sé es que " + self.frase(f)))
                    fs = pres
                if not fs:
                    return nada(f"no me has dicho cómo {M.conjugar(v, 'pres', self._persona_de(s))} {self.disp(s) if s != 'U' else ''}".strip())
                h = dict(fs[0]); h["attr"] = list(dict.fromkeys(a for f in fs for a in f["attr"] if a not in f.get("isa", []))); h["grado"] = fs[0].get("grado", "") if len(fs) == 1 else ""
                h["s"] = s
                self.ult_just = {"dicho": [f["src"] for f in fs]}
                return self._ok(self._fin(self.frase(h, tiempo="imp" if pasado else None)))
            fs = [f for f in self.marcos(v=v, s=s, neg=False) if f.get("modo") or f.get("comps") or f.get("attr")]   # «dormí fatal» guarda «fatal» como atributo
            fs = [f for f in fs if self._coincide_obj(f, o)]
            if fs:
                self.ult_just = {"dicho": [fs[-1]["src"]]}
                return self._ok(self._fin(self.frase(fs[-1])))
            return nada()
        # ---------- cuál / qué + ser + papel («¿Cuál es el color de mi coche?», «¿Cuál es mi nombre?»)
        if tipo in ("cual", "que") and v == "ser" and not sust:
            objetivo = sn_s
            if objetivo is not None and objetivo.cab and (objetivo.de is not None or objetivo.pos) and not objetivo.propio:
                return self._papel(objetivo, s)
            if tipo == "cual":
                return None
        if tipo == "que" and sust and v in ("ser", "estar") and s is not None and not C.comps:
            # «¿De qué color es mi coche?», «¿Qué edad tiene...?» va por tener
            return self._prop(s, sust, sn_s, nada)
        if tipo == "que" and sust == "edad" and v == "tener":
            tipo, sust = "cuanto", "año"
        if tipo == "que" and sust == "color" and v == "tener" and s is not None:
            return self._prop(s, "color", sn_s, nada)
        if tipo == "que" and sust == "nombre" and v == "tener" and s is not None:
            C.v, C.refl, tipo, sust, v = "llamar", True, "como", "", "llamar"
        if tipo == "como" and v in ("sentir", "encontrar") and C.refl:
            v = C.v = "estar"
        if tipo == "que" and sust and v == "ser" and s is not None and not s.startswith("K:") and sust not in ("color", "edad", "nombre"):
            sust = ""            # «¿Qué tipo de animal es Toby?», «¿Qué animal es Toby?» -> ¿qué es Toby?
        # ---------- cuánto
        if tipo == "cuanto":
            return self._cuanto(C, s, sn_s, o, sust, nada)
        if s is None:
            return None
        r_x = self._xinf_q(C, tipo, prep, s, v)
        if r_x is not None:
            return r_x
        # ---------- dónde
        if tipo == "donde" and prep == "para" and v == "ser" and isinstance(s, str) and not s.startswith("?"):
            cl_s = self.E.get(s, {}).get("clase") or (s[2:] if s.startswith("K:") else "")
            for f in reversed(self.F):                  # «¿Para dónde es el cuadro?» con «he pintado un cuadro para el salón»
                if f.get("vig", True) and (self.can(f.get("obj") or "") == s or (cl_s and f.get("obj_cls") == cl_s)) and any(p2 == "para" for p2, _, _ in f.get("comps", [])):
                    self.ult_just = {"dicho": [f["src"]]}
                    return self._ok(self._fin(_cap(self.frase(f))))
        if tipo in ("cuando", "donde") and not prep and (v == "ser" or (v == "estar" and tipo == "donde")) and isinstance(s, str) and not s.startswith("?") and not self.marcos(v=v, s=s, neg=False):
            cl_s = self.E.get(s, {}).get("clase") or (s[2:] if s.startswith("K:") else "")
            for f in reversed(self.F):                  # «¿Dónde es la fiesta?» con «haremos una fiesta en casa»
                if not f.get("vig", True) or not (self.can(f.get("obj") or "") == s or (cl_s and f.get("obj_cls") == cl_s)):
                    continue
                if tipo == "donde" and any(p2 in ("en",) for p2, _, _ in f.get("comps", [])):
                    self.ult_just = {"dicho": [f["src"]]}
                    return self._ok(self._fin(_cap(self.frase(f))))
                if tipo == "cuando" and f.get("cuando"):
                    self.ult_just = {"dicho": [f["src"]]}
                    return self._ok(self._fin(_cap(self.frase(f))))
        if tipo == "donde":
            pr = prep or "en"
            fs = self.marcos(v=v, s=s, vig=None, neg=False, herencia=False)
            if not [f for f in fs if f.get("comps") or f.get("lugar_adv")]:
                fs = self.marcos(v=v, s=s, vig=None, neg=False, herencia=True)
            fs = [f for f in fs if (any(p2 == pr or (not prep and p2 in ("en", "cerca_de", "al_lado_de", "junto_a", "dentro_de", "encima_de", "debajo_de", "delante_de", "detras_de", "enfrente_de", "lejos_de", "sobre", "entre", "bajo")) for p2, _, _ in f.get("comps", [])) or f.get("lugar_adv")) and self._coincide_obj(f, o)]
            if not fs and v == "trabajar" and not prep and isinstance(s, str):
                # «¿Dónde trabajo?» con «soy enfermero en el hospital»: la profesión dicha con el sitio
                fs = [f for f in self.marcos(v="ser", s=s, vig=True, neg=False) if (f.get("isa") or f.get("prof") or f.get("attr")) and any(p2 == "en" for p2, _, _ in f.get("comps", []))]
            if v == "ir" and not prep:
                fs += [f for f in self.marcos(v=v, s=s, vig=None, neg=False) if any(p2 == "a" for p2, _, _ in f.get("comps", []))]
            vig = [f for f in fs if f.get("vig", True) and (not pasado or f.get("t") in ("pret", "imp"))]
            viejos = [f for f in fs if not f.get("vig", True)]
            if not pasado and v in ("vivir", "estar", "trabajar", "estudiar", "residir"):
                pres = [f for f in vig if f.get("t") not in ("imp",)]
                viejos += [f for f in vig if f.get("t") == "imp"]
                vig = pres
            if pasado and viejos and v in ("vivir", "estar", "trabajar", "estudiar", "residir"):
                f = viejos[-1]
                self.ult_just = {"dicho": [f["src"]]}
                return self._ok(self._fin(self.frase(f, tiempo="imp", antes=True)))
            if pasado and not vig:
                vig = [f for f in fs if f.get("vig", True)]
                if vig and v in ("vivir", "estar", "trabajar", "estudiar", "residir") and not viejos:
                    return self._abst(self._fin("No sé dónde " + M.conjugar(v, "imp", self._persona_de(s)) + " antes. Solo sé que ahora " + self.frase(vig[-1])))
            if vig:
                f = vig[-1]
                self.ult_just = self._just_marco(f, s)
                if self.can(f["s"]) != s:
                    h = dict(f); h["s"] = s; h["pl_suj"] = False
                    return self._ok(self._fin(self.frase(h)) + " " + self._fin("Lo deduzco " + self._porque(self.ult_just.get("pasos", []))))
                return self._ok(self._fin(self.frase(f)))
            if v == "estar":
                # objeto que alguien tiene
                ten = [f for f in self.F if f["v"] == "tener" and f.get("vig", True) and not f.get("neg") and self.can(f.get("obj") or "") == s]
                if ten:
                    self.ult_just = {"dicho": [ten[-1]["src"]]}
                    return self._ok(self._fin("Lo último que sé es que " + self.frase(ten[-1])))
            if v == "estar" and isinstance(s, str) and s not in ("U", "L"):
                nom_ = sa(self.disp(s))
                pistas = [f for f in self.F if f.get("vig", True) and self.can(f["s"]) != s and nom_ and nom_.split()[-1] in sa(self.frase(f))
                          and any(p2 in ("a", "en") and (d2 or e2) for p2, e2, d2 in f.get("comps", []))]
                if pistas:                              # «¿Dónde está mi abuelo?» con «fui a ver a mi abuelo al hospital»
                    self.ult_just = {"dicho": [pistas[-1]["src"]]}
                    return self._abst(self._fin("No me lo has dicho directamente, pero " + self.frase(pistas[-1])))
            if viejos:
                f = viejos[-1]
                return self._abst(self._fin("No sé dónde " + M.conjugar(v, "pres", self._persona_de(s)) + " ahora. " + _cap(self.frase(f, tiempo="imp", antes=True))))
            if getattr(self, "_preg_que_lugar", False):
                con_obj = [f for f in self.marcos(v=v, s=s, vig=True, neg=False) if f.get("obj") or f.get("obj_cls")]
                if con_obj:
                    self.ult_just = {"dicho": [con_obj[-1]["src"]]}
                    return self._ok(self._fin(_cap(self.frase(con_obj[-1]))))
            return nada(f"no me has dicho dónde {M.conjugar(v, 'pres' if not pasado else 'pret', self._persona_de(s))}{'' if s == 'U' else ' ' + self.disp(s)}")
        if tipo == "que" and C.xinf and isinstance(s, str) and not s.startswith("?"):
            inf_ = sa(C.xinf.split()[0])
            fs_x = [f for f in self.marcos(v=v, s=s, vig=None, neg=False) if inf_ in sa(f.get("xinf", "") + " " + " ".join(d2 or "" for _, _, d2 in f.get("comps", [])))]
            if fs_x:                                    # «¿Qué estoy pensando adoptar?» con «pienso en adoptar un gato»
                self.ult_just = {"dicho": [fs_x[-1]["src"]]}
                return self._ok(self._fin(_cap(self.frase(fs_x[-1]))))
        if tipo == "como" and v not in ("ser", "estar", "llamar", "encontrar", "sentir") and isinstance(s, str) and not s.startswith("?"):
            fs_m = [f for f in self.marcos(v=v, s=s, vig=None, neg=False) if f.get("attr") or f.get("modo") or any(p2 in ("con", "sin") for p2, _, _ in f.get("comps", []))
                    or (v in ("acabar", "terminar", "quedar", "salir", "llegar", "volver", "acabar") and f.get("obj_disp") and not f.get("obj_cls") in KB.kb()["isa"])]
            if fs_m:                                    # «¿Cómo acabé?» con «acabé muertísima»
                self.ult_just = {"dicho": [fs_m[-1]["src"]]}
                return self._ok(self._fin(_cap(self.frase(fs_m[-1]))))
        # ---------- cuándo
        if tipo == "cuando" and prep == "para" and v in ("ser", "estar") and isinstance(s, str) and not s.startswith("?"):
            cl_s = self.E.get(s, {}).get("clase") or (s[2:] if s.startswith("K:") else "")
            for f in reversed(self.F):                  # «¿Para cuándo es el informe?» con «me pidió un informe para el lunes»
                if (self.can(f.get("obj") or "") == s or (cl_s and f.get("obj_cls") == cl_s)) and any(p2 == "para" for p2, _, _ in f.get("comps", [])):
                    d_ = [d2 or self.disp(e2) for p2, e2, d2 in f["comps"] if p2 == "para"][0]
                    self.ult_just = {"dicho": [f["src"]]}
                    return self._ok(self._fin(f"Para {cambia_persona(d_)}: {self.frase(f)}"))
        if tipo == "cuando" and s and not isinstance(s, list):
            r_ = self._cuando_por_texto(C, s)
            if r_ is not None:
                return r_
            if v == "ir" and C.comps:
                for f in self.marcos(s=s, vig=None, neg=False):
                    if f["v"] in ("llevar", "acompañar", "traer") and f.get("cuando") and any(p2 == "a" and self._coincide_comps(dict(f, comps=[c2 for c2 in f["comps"] if c2[0] == "a" and not (c2[1] and self.es_persona(c2[1]))]), C.comps) for p2, _, _ in f.get("comps", [])):
                        return self._ok(self._fin(_cap(self.frase(f))), {"dicho": [f["src"]]})
        if tipo == "cuando":
            fs = [f for f in self.marcos(v=v, s=s, vig=None, neg=False) if (f.get("cuando") or f.get("freq")) and self._coincide_comps(f, C.comps) and (self._coincide_obj(f, o)
                  or (v == "ser" and o is not None and o.cab and sa(M.masc(o.cab)) in [sa(M.masc(x)) for x in f.get("attr", []) + f.get("isa", [])]))]   # «¿Desde cuándo soy celador?»
            if not fs and v in ("ser", "estar") and s is not None:
                cl_s = self.E.get(s, {}).get("clase") or (s[2:] if s.startswith("K:") else "")
                ev = [f for f in self.F if (f.get("cuando") or f.get("freq")) and not f.get("neg") and ((f.get("obj") and self.can(f["obj"]) == s) or (cl_s and f.get("obj_cls") == cl_s))]
                if ev:
                    f = ev[-1]
                    self.ult_just = {"dicho": [f["src"]]}
                    extra = self._fecha_abs(f.get("cuando", ""), f)
                    return self._ok(self._fin(self.frase(f) + (f" ({extra})" if extra else "")))
            if not fs:
                otros = [f for f in self.marcos(v=v, s=s, vig=None, neg=False) if self._coincide_obj(f, o)]
                def _laxo(f):                           # «¿Cuándo saco a pasear a mis perros?» con «saco a mis perros a pasear todas las mañanas»
                    for p_q, sn_q in C.comps:
                        w_q = sa((sn_q.texto or sn_q.cab or "").split()[0]) if (sn_q.texto or sn_q.cab) else ""
                        if not any(p2 == p_q and w_q and sa((d2 or "").split()[0] if d2 else "") == w_q for p2, _, d2 in f.get("comps", [])):
                            return False
                    return True
                laxos = [f for f in self.marcos(v=v, s=s, vig=None, neg=False) if (f.get("cuando") or f.get("freq")) and C.comps and _laxo(f)]
                if laxos:
                    f = laxos[-1]
                    self.ult_just = {"dicho": [f["src"]]}
                    return self._ok(self._fin(_cap(self.frase(f))))
                if otros:
                    return self._abst(self._fin("No me has dicho cuándo. Solo sé que " + self.frase(otros[-1])))
                return nada()
            f = fs[-1]
            self.ult_just = {"dicho": [f["src"]]}
            extra = self._fecha_abs(f.get("cuando", ""), f)
            return self._ok(self._fin(self.frase(f) + (f" ({extra})" if extra else "")))
        # ---------- qué
        if tipo in ("que", "cual"):
            if v == "saber" and any(p_ in ("de", "sobre") for p_, _ in C.comps):
                return None
            if v == "hacer":
                return self._que_hace(C, s, nada, pasado)
            if C.xinf and sa(C.xinf).split()[0] == "hacer" and s is not None:
                fs = [f for f in self.marcos(v=v, s=s, neg=False) if f.get("xinf") and (not C.modal or f.get("modal") == C.modal)]
                C2 = Clausula(cuando=C.cuando or " ".join(sa(C.xinf).split()[1:]), freq=C.freq)
                con_t = [f for f in fs if (sa(C2.cuando) in sa(f.get("xinf", "")) or self._tiempo_ok(f, C2))] if C2.cuando else fs
                fs = con_t or ([] if C2.cuando else fs)
                if fs:
                    self.ult_just = {"dicho": [f["src"] for f in fs]}
                    return self._ok(self._fin(self._lista([self.frase(f) for f in fs[:3]])))
                return nada()
            if v == "ser" and not sust and s is not None and len(C.comps) == 1 and C.comps[0][0] == "de":
                y = self._q_ent(C.comps[0][1])
                if y is None or isinstance(y, list) or str(y).startswith("?"):
                    return self._no_conozco(C.comps[0][1], y)
                y = self.can(y)
                nombres = list(dict.fromkeys([q["r"] for q in self.R] + ["padre", "hijo", "hermano", "abuelo", "nieto", "tio", "sobrino", "primo", "esposo", "suegro", "cuñado"]))
                for r_ in nombres:
                    ps = self.rels(r_, x=s, y=y)
                    if ps:
                        fr = self._frase_rel(r_, s, y)
                        self.ult_just = {"pasos": ps[0]["j"]}
                        ded = len(ps[0]["j"]) > 1 or ps[0]["j"][0] != fr
                        return self._ok(self._fin(fr) + (" " + self._fin("Lo deduzco " + self._porque(ps[0]["j"])) if ded else ""))
                return self._abst(self._fin(f"No lo sé: no conozco ninguna relación entre {self.disp(s)} y {self.disp(y)}"))
            if v == "ser" and not sust:
                if s is None:
                    return None
                cs = self.clases(s)
                if not s.startswith("K:"):               # 2.15: que sea persona se deduce de cómo se habla de él; no es una respuesta a «¿qué es?»
                    cs = [(c, j) for c, j in cs if not (c in ("persona", "ser vivo") and j and "es una persona" in j[0])]
                fs = [f for f in self.marcos(v="ser", s=s, neg=False) if f.get("isa")]
                if s.startswith("K:"):
                    if fs:
                        self.ult_just = {"dicho": [fs[0]["src"]]}
                        return self._ok(self._fin(self._lista_frases(fs)))
                    return self._abst("No lo sé.", consultar=True)
                if self.es_persona(s) and s != "U":
                    # «¿Qué es Rubén?»: su relación contigo y lo que es (profesión, etc.)
                    trozos, srcs = [], []
                    for r_ in ("esposo", "padre", "hijo", "hermano", "abuelo", "nieto", "tio", "sobrino", "primo", "suegro", "cuñado", "novio", "amigo", "vecino", "jefe", "compañero"):
                        ps = self.rels(r_, x=s, y="U")
                        if ps:
                            trozos.append(self._frase_rel(r_, s, "U").split(" es ", 1)[1]); srcs += ps[0]["j"]
                            break
                    for r_ in [x for x in self.R if self.can(x["x"]) == s and self.can(x["y"]) != "U" and x["r"] not in ("hermano",)][-2:]:
                        try:                            # «Raúl es el cocinero del restaurante»: los papeles respecto a otras cosas
                            trozos.append(self._frase_rel(r_["r"], s, self.can(r_["y"])).split(" es ", 1)[1])
                        except Exception:               # noqa
                            pass
                    atr = [f for f in self.marcos(v="ser", s=s, neg=False) if f.get("attr") or f.get("isa")]
                    trozos += [self.frase(f, sin_sujeto=True)[3:] if self.frase(f, sin_sujeto=True).startswith("es ") else self.frase(f, sin_sujeto=True) for f in atr[-2:]]
                    if trozos:
                        self.ult_just = {"pasos": srcs} if srcs and not atr else {"dicho": [f["src"] for f in atr[-2:]]}
                        return self._ok(self._fin(f"{self.disp(s)} es " + self._lista(list(dict.fromkeys(trozos)))))
                if fs:
                    self.ult_just = {"dicho": [f["src"] for f in fs]}
                    return self._ok(self._fin(self._lista_frases(fs)))
                if cs:
                    self.ult_just = {"pasos": cs[0][1]}
                    return self._ok(self._fin(cs[0][1][0]))
                negs = [f for f in self.marcos(v="ser", s=s, neg=True) if f.get("attr")]
                pos_ = [f for f in self.marcos(v="ser", s=s, neg=False) if f.get("attr")]
                if negs and not pos_:
                    return self._abst(self._fin("No lo sé. Solo sé que " + self._lista([self.frase(f) for f in negs[:2]])))
                r = self.resumen(s)
                return self._ok(r) if r else nada()
            if v == "tener":
                fs = [f for f in self.marcos(v="tener", s=s, neg=bool(C.neg)) if f.get("obj_cls") != "año"]
                if sust:
                    fs = [f for f in fs if self._de_clase(f, sust)]
                if not fs:
                    return nada(f"no me has dicho qué {'tienes' if s == 'U' else 'tiene ' + self.disp(s)}")
                self.ult_just = {"dicho": list(dict.fromkeys(f["src"] for f in fs))}
                return self._ok(self._fin(_cap(self._tener_lista(s, fs))))
            fs = [f for f in self.marcos(v=v, s=s, vig=None, neg=bool(C.neg), herencia=True) if (f.get("obj_disp") or f.get("xinf")
                  or any(c_[1] is None and c_[2] and c_[0] in ("a", "de") and any(x[1] == "inf" for x in M.analizar(sa(c_[2].split()[0]))) for c_ in f.get("comps", [])))   # «aprendo a tocar la guitarra»
                  and self._coincide_comps(f, C.comps) and self._tiempo_ok(f, C)]
            if sust:
                fs = [f for f in fs if self._de_clase(f, sust)]
            vig = [f for f in fs if f.get("vig", True)]
            if pasado:
                vig = [f for f in vig if f.get("t") in ("pret", "imp")] or [f for f in fs if not f.get("vig", True)] or vig
            elif C.tiempo == "pres":
                vig = [f for f in vig if f.get("t") in ("pres",)] or vig
            if not vig:
                otros = [f for f in self.marcos(v=v, s=s, neg=not bool(C.neg)) if f.get("obj_disp")]
                if otros and not C.neg:
                    return self._abst(self._fin("No lo sé. Solo sé que " + self._lista_frases(otros[:3])))
                return nada(f"no me has dicho qué {'no ' if C.neg else ''}{M.conjugar(v, 'pret' if C.tiempo == 'pret' else 'pres', self._persona_de(s))}{'' if s == 'U' else ' ' + self.disp(s)}")
            self.ult_just = {"dicho": list(dict.fromkeys(f["src"] for f in vig))}
            return self._ok(self._fin(self._lista_frases(vig)))
        return None

    def _intervalo(self, cuando):
        """Intervalo absoluto 'AAAA-MM-DD/AAAA-MM-DD' de una expresión temporal, con el resolutor de fechas del proyecto."""
        if not cuando:
            return None
        hoy = getattr(self.mem, "today", None) or dt.date.today()
        c = sa(cuando).replace("ñ", "n")
        cands = [c, re.sub(r"^(?:el|la|en|este|esta|ese|esa|los|las)\s+", "", c), re.sub(r"^(?:el|la|en)\s+", "", c).replace(" pasado", "").replace(" pasada", "")]
        try:
            from src.language import fechas
            for k in cands:
                iv = fechas.resolve(k, hoy)
                if iv:
                    return iv
            ab = fechas.extract_abs(cuando, hoy)
            if ab:
                iv = ab[0] if isinstance(ab, (tuple, list)) else ab
                if isinstance(iv, str) and "/" in iv:
                    return iv
        except Exception:                                                     # noqa
            pass
        m = re.search(r"\b(1[0-9]\d\d|20\d\d)\b", c)
        if m and re.fullmatch(r"(?:en |el año |en el año )?\d{4}", c):
            return f"{m.group(1)}-01-01/{m.group(1)}-12-31"
        if "año pasado" in sa(cuando):
            return f"{hoy.year - 1}-01-01/{hoy.year - 1}-12-31"
        d = {"hoy": 0, "ayer": -1, "anteayer": -2, "mañana": 1, "pasado mañana": 2, "anoche": -1}.get(sa(cuando))
        if d is not None:
            f = hoy + dt.timedelta(days=d)
            return f"{f.isoformat()}/{f.isoformat()}"
        return None

    def _fecha_abs(self, cuando, f=None):
        if f is not None and f.get("posible"):
            return ""                                   # 2.11: de una de varias posibilidades no se da la fecha
        iv = self._intervalo(cuando)
        if not iv or re.search(r"\b(1[0-9]\d\d|20\d\d)\b", cuando):
            return ""
        try:
            from src.language import fechas
            a, b = iv.split("/")
            hoy = getattr(self.mem, "today", None) or dt.date.today()
            if f is not None and f.get("t") in ("pres", "fut") and dt.date.fromisoformat(b) < hoy and re.search(r"\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|verano|invierno|primavera|otono|navidad|navidades|vacaciones)\b", sa(cuando)):
                # «se casa en junio» dicho en noviembre: el próximo junio
                a = str(dt.date.fromisoformat(a).replace(year=dt.date.fromisoformat(a).year + 1))
                b = str(dt.date.fromisoformat(b).replace(year=dt.date.fromisoformat(b).year + 1))
                iv = a + "/" + b
            a_inf = f is not None and f.get("t") == "pret" and any(p2 == "a" and d2 and any(x[1] == "inf" for x in M.analizar(sa(d2.split()[0]))) for p2, _, d2 in f.get("comps", []))
            if f is not None and (f.get("t") in ("pres", "fut") or a_inf) and dt.date.fromisoformat(b) < hoy and \
                    re.search(r"\b(?:lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b", sa(cuando)) and not re.search(r"\bpasado\b", sa(cuando)):
                # «el sábado nos ha invitado a comer»: el sábado es el de la comida, que aún no ha llegado
                # «viene el viernes» dicho un miércoles: el viernes que viene, no el pasado
                a = str(dt.date.fromisoformat(a) + dt.timedelta(days=7)); b = str(dt.date.fromisoformat(b) + dt.timedelta(days=7))
                iv = a + "/" + b
            if a == b:
                f = dt.date.fromisoformat(a)
                dias = "lunes martes miércoles jueves viernes sábado domingo".split()
                return f"{dias[f.weekday()]} " + fechas.fmt(iv)
            return fechas.fmt(iv)
        except Exception:                                                     # noqa
            return ""

    def _papel(self, objetivo: SN, s):
        """«el N de X» -> valor: nombre, edad, color o relación."""
        cl, g = self._clase_sn(objetivo)
        dueno = "U" if objetivo.pos == "U" else ("L" if objetivo.pos == "L" else None)
        if objetivo.pos == "3":
            dueno = self.ult_suj or self.ref3(persona=True)
        if objetivo.de is not None:
            dueno = self._q_ent(objetivo.de)
        if dueno == "L":
            return None
        if dueno is None or isinstance(dueno, list) or str(dueno).startswith("?"):
            return self._no_conozco(objetivo.de, dueno) if objetivo.de is not None else None
        dueno = self.can(dueno)
        self.mencionar(dueno); self.ult_suj = dueno
        if cl == "nombre":
            nom = self._nombre_de(dueno)
            if nom:
                return self._ok(self._fin(f"{'Te llamas' if dueno == 'U' else 'Se llama'} {nom}"), {"dicho": [self.E.get(dueno, {}).get("src_nombre", "")]})
            return self._abst("Todavía no me has dicho cómo te llamas." if dueno == "U" else self._fin(f"No sé cómo se llama {self.disp(dueno)}"))
        if cl == "edad":
            ed = self._edad(dueno)
            if ed:
                self.ult_just = ed[1]
                return self._ok(self._fin(f"{'Tienes' if dueno == 'U' else self.disp(dueno) + ' tiene'} {ed[0]} años"))
            return self._abst(self._fin(f"No sé cuántos años {'tienes' if dueno == 'U' else 'tiene ' + self.disp(dueno)}"))
        if cl in ("aficion", "gusto", "hobby", "pasion", "interes", "pasatiempo"):
            fs = [f for f in self.F if f.get("exp") and self.can(f["s"]) == dueno and f.get("vig", True) and not f.get("neg")]
            if fs:
                self.ult_just = {"dicho": [f["src"] for f in fs]}
                return self._ok(self._fin(self._lista_frases(fs)))
            return self._abst(self._fin(f"No lo sé: no me has dicho qué {'te' if dueno == 'U' else 'le'} gusta{'' if dueno == 'U' else ' a ' + self.disp(dueno)}"))
        if cl in ("profesion", "trabajo", "oficio", "ocupacion", "empleo"):
            return self._que_hace(None, dueno, lambda extra="": self._abst(self._fin(f"No sé a qué {'te dedicas' if dueno == 'U' else 'se dedica ' + self.disp(dueno)}")), False, solo_trabajo=True)
        if cl in ("dueño", "dueno", "amo", "propietario") and not dueno.startswith("K:"):
            dn = [self.can(q["y"]) for q in self.R if self.can(q["x"]) == dueno and q["r"] not in FAMILIA and q["r"] not in SIMETRICAS and q["r"] not in INVERSAS]
            if dn:
                y = dn[-1]
                return self._ok(self._fin(f"{'Tú eres' if y == 'U' else self.disp(y) + ' es'} {'la dueña' if self.gen(y) == 'f' and y != 'U' else 'el dueño'} de {self.disp(dueno)}"))
        if cl == "color":
            return self._prop(dueno, "color", None, lambda extra="": self._abst(self._fin(f"No sé de qué color es {self.disp(dueno)}")))
        if cl in ("profesion", "trabajo", "oficio", "ocupacion"):
            return self._que_hace(None, dueno, lambda extra="": self._abst(self._fin(f"No sé a qué {'te dedicas' if dueno == 'U' else 'se dedica ' + self.disp(dueno)}")), False, solo_trabajo=True)
        if not g and objetivo.gen == "m" and not objetivo.pl and cl in ("padre", "abuelo", "hermano", "hijo", "tio", "primo", "nieto", "sobrino", "esposo", "novio", "suegro", "cuñado", "bisabuelo"):
            g = "m"                      # «el abuelo» pide un varón; «los abuelos» no
        xs = [r for r in self.rels(cl, y=dueno) if not g or self.gen(r["x"]) == g or not (r["x"].startswith("N:") or self.E.get(r["x"], {}).get("gen"))]
        con_nombre = [r for r in xs if not r["x"].startswith("I:")]
        if con_nombre:
            j = []
            for r in con_nombre:
                j += r["j"]
            frs = [self._frase_rel(cl, r["x"], dueno) for r in con_nombre]
            deducido = any(len(r["j"]) > 1 or r["j"][0] != self._frase_rel(cl, r["x"], dueno) for r in con_nombre)
            self.ult_just = {"pasos": list(dict.fromkeys(j))} if deducido else {"dicho_rel": frs[0], "src": [q.get("src", "") for q in self.R if q["r"] == cl and self.can(q["y"]) == dueno]}
            nom = self._rel_nombre(cl, self.gen(con_nombre[0]["x"]))
            if len(con_nombre) == 1:
                x = con_nombre[0]["x"]
                if x.startswith("K:"):
                    quien = ("tu " + nom) if dueno == "U" else contrae(f"{'la' if M.genero_sust(nom) == 'f' else 'el'} {nom} de {self.disp(dueno)}")
                    d_x = self.disp(x)
                    if self.E.get(x, {}).get("pl") and not self.E.get(x, {}).get("sinart"):
                        cl_x = self.E[x].get("clase") or x[2:]   # 2.20: «el fruto es la aceituna»: una clase, dicha en singular aunque luego se hable de «las aceitunas»
                        d_x = f"{'la' if self.gen(x) == 'f' else 'el'} {self._acento(cl_x)}"
                    return self._ok(self._fin(f"{quien} es {d_x}"))
                txt = frs[0]
            else:
                noms = self._lista([self.disp(r["x"]) for r in con_nombre])
                txt = f"{noms} son {'tus' if dueno == 'U' else 'los'} {M.plural(self._rel_nombre(cl, 'm' if any(self.gen(r['x']) == 'm' for r in con_nombre) else 'f'))}" + ("" if dueno == "U" else " " + contrae(f"de {self.disp(dueno)}"))
            return self._ok(self._fin(txt) + (" " + self._fin("Lo deduzco " + self._porque(list(dict.fromkeys(j)))) if deducido else ""))
        if xs:
            x0 = self.can(xs[0]["x"])
            if x0.startswith("I:") and re.match(r"^\W*(?:y\s+)?qu[ée]\s+(?:es|era)\b", (self.ult_preg[0] if self.ult_preg else "") or "", re.I):
                # 2.14: «¿qué es mi hermano?» con «mi hermano es médico»: lo que es, no quién es
                fs_ = [f for f in self.F if f["v"] == "ser" and self.can(f.get("s") or "") == x0 and f.get("vig", True) and not f.get("neg") and (f.get("isa") or f.get("attr"))]
                if fs_:
                    self.ult_just = {"dicho": [f["src"] for f in fs_[-2:]]}
                    return self._ok(self._fin(self._lista_frases(fs_[-2:])))
            if x0.startswith("I:") and self.es_persona(x0):   # «¿Quién es el presidente de la comunidad?» -> «Es tu vecino»
                self.ult_just = {"dicho": [xs[0].get("src", "")]}
                return self._ok(self._fin(f"Es {self.disp(x0)} (no me has dicho cómo se llama)"))
            return self._abst(self._fin(f"Sé que existe {self.disp(xs[0]['x'])}, pero no me has dicho {'quién es' if cl in PERSONA_CLS else 'cómo se llama'}"))
        nom = self._rel_nombre(cl, g or M.genero_sust(cl))
        quien = ("tu " + nom) if dueno == "U" else contrae(f"{'la' if (g or M.genero_sust(nom)) == 'f' else 'el'} {nom} de {self.disp(dueno)}")
        verbo = "quién es" if cl in PERSONA_CLS else "cuál es"
        return self._abst(self._fin(f"No lo sé: no me has dicho {verbo} {quien}"), consultar=dueno.startswith("K:") or not self._conocido(dueno))

    def _prop(self, s, sust, sn_s, nada):
        if sust == "color":
            fs = [f for f in self.marcos(v="ser", s=s, neg=False, herencia=True) if set(f.get("attr", [])) & COLORES]
            if not fs and s.startswith("K:"):           # «¿De qué color son los globos?» con «mis globos son azules»
                cl_k = s[2:]
                fs = [f for f in self.F if f["v"] == "ser" and f.get("vig", True) and not f.get("neg") and set(f.get("attr", [])) & COLORES
                      and self.E.get(self.can(f["s"]), {}).get("clase") == cl_k and not str(f["s"]).startswith("K:")]
            if fs:
                f = fs[-1]
                h = dict(f); h["attr"] = [a for a in f["attr"] if a in COLORES]; h["grado"] = ""
                h["s"] = f["s"] if (s.startswith("K:") and not str(f["s"]).startswith("K:")) else s   # «los globos» = tus globos
                self.ult_just = self._just_marco(f, s)
                return self._ok(self._fin(self.frase(h)))
            if s.startswith("K:") or not self._conocido(s):
                return self._abst("No lo sé.", consultar=True)
            return self._abst(self._fin(f"No lo sé: no me has dicho de qué color es {self.disp(s)}"))
        if sust in ("tamaño",):
            return nada()
        return None

    def _cuanto(self, C, s, sn_s, o, sust, nada):
        v = C.v
        if s is None:
            return None
        if sust and v == "ser" and (sn_s is None or not sn_s.cab):
            # «¿Cuántos compañeros son?» con «salgo a cenar con dos compañeros»: el número va en un complemento
            pl_ = sa(M.plural(sust)).replace("ñ", "n")
            for f in reversed(self.F[-40:]):
                if not f.get("vig", True) or f.get("neg"):
                    continue
                for _, _, d2 in f.get("comps", []):
                    mm = re.match(r"^(?:(?:mis|tus|sus|unos|unas|los|las) )?(dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|\d+) " + re.escape(pl_) + r"$", sa(d2 or "").replace("ñ", "n"))
                    if mm:
                        self.ult_just = {"dicho": [f["src"]]}
                        return self._ok(self._fin(f"Son {mm.group(1)}: " + self.frase(f)))
        if sust:
            for f in reversed(self.marcos(v=v, neg=False)):  # «¿Cuántos niños vendrán?» con «vendrán ocho niños de su clase»
                if f.get("suj_txt") and sa(M.plural(sust)).replace("ñ", "n") in sa(f["suj_txt"]).replace("ñ", "n") and self._tiempo_ok(f, C):
                    self.ult_just = {"dicho": [f["src"]]}
                    return self._ok(self._fin(_cap(self.frase(f))))
        if sust and isinstance(s, str) and not s.startswith("?"):
            # «¿Cuántos kilómetros hice?» con «hice una ruta de cuarenta kilómetros»: el número va dentro de lo dicho
            pl_ = sa(M.plural(sust))
            for f in reversed(self.marcos(v=v if v not in ("ser", "estar") else None, s=s, neg=False)):
                if not self._tiempo_ok(f, C):
                    continue
                mm = re.search(r"\b(\d+|" + "|".join(["un", "una", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce", "quince", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa", "cien", "mil"]) + r")\s+" + re.escape(pl_) + r"\b", sa(self.frase(f)))
                if mm and f.get("obj_cls") != sust:
                    self.ult_just = {"dicho": [f["src"]]}
                    return self._ok(self._fin(_cap(self.frase(f))))
        if v == "llevar" and sust in ("tiempo", "año", "ano", "mes", "dia") and isinstance(s, str):
            fs_l = [f for f in self.marcos(v="llevar", s=s, neg=False) if f.get("obj_cls") in ("año", "mes", "dia", "semana", "hora")]
            if fs_l:                                    # «¿Cuánto tiempo llevo de fontanero?» con «llevo veinte años en el oficio»
                self.ult_just = {"dicho": [fs_l[-1]["src"]]}
                return self._ok(self._fin(_cap(self.frase(fs_l[-1]))))
        if v not in ("tener", "ser", "estar", "haber") and sust and isinstance(s, str) and KB.kb()["hijos"].get(KB._kb_clase(sust) or ""):
            cl_q = KB._kb_clase(sust)
            fs_ = [f for f in self.marcos(v=v, s=s, neg=False) if f.get("obj_cls") and self._de_clase(f, cl_q)]
            objs = []
            for f in fs_:
                objs += [x.strip() for x in re.split(r",| y | e ", cambia_persona(f.get("obj_disp") or "")) if x.strip()]
            objs = list(dict.fromkeys(objs))
            if objs:                                    # «¿Cuántos idiomas habla?»
                self.ult_just = {"dicho": [f["src"] for f in fs_]}
                tot = len(objs)
                return self._ok(self._fin(f"{_cap(M.num_pal(tot, M.genero_sust(cl_q))).replace('Un', 'Uno').replace('Unoa', 'Una') if tot == 1 else _cap(M.num_pal(tot, M.genero_sust(cl_q)))}, que yo sepa: " + self._lista(objs)))
        if v == "tener" and sust and isinstance(s, str) and (sust in ("mascota", "bicho") or KB.kb()["hijos"].get(KB._kb_clase(sust) or "")):
            cl_q = KB._kb_clase(sust) or sust
            fs_ = [f for f in self.marcos(v="tener", s=s, neg=False) if f.get("obj_cls") and f.get("obj_cls") != cl_q and self._de_clase(f, cl_q)]
            if fs_:
                if any(f.get("cuant") is None for f in fs_):
                    return self._abst(self._fin("No sé el número exacto. Solo sé que " + self._tener_lista(s, fs_)))
                tot = self._entero(self._suma_app(f["cuant"] for f in fs_))
                self.ult_just = {"dicho": [f["src"] for f in fs_], "app_traza": self._traza_app}
                return self._ok(self._fin(f"{_cap(M.num_pal(tot, M.genero_sust(cl_q))) if tot < 30 else tot}, que yo sepa: " + self._lista([cambia_persona(f["obj_disp"]) for f in fs_])))
        if sust in ("año", "ano") and v == "llevar" and not C.comps:
            par = None
            if isinstance(getattr(self, "_suj_lista", None), list) and len(self._suj_lista) == 2:
                par = self._suj_lista
            elif C.pers == "1p":
                otro = self.ref3(persona=True)
                par = ["U", otro] if otro else None
            if par:
                a, b = self._edad(par[0]), self._edad(par[1])
                if a is None or b is None:
                    return self._abst("No lo sé: me falta la edad de alguno de los dos.")
                d = self._entero(self._app("diferencia", a[0], b[0]))
                self.ult_just = {"pasos": [f"{self.disp(par[0]) if par[0] != 'U' else 'tú'} tiene{'s' if par[0] == 'U' else ''} {a[0]} años", f"{self.disp(par[1])} tiene {b[0]} años"], "app_traza": self._traza_app}
                return self._ok(self._fin(f"{M.num_pal(d).capitalize()} año{'s' if d != 1 else ''}"))
        if sust in ("año", "ano") and v in ("llevar", "sacar") and C.comps:
            e2 = self._q_ent(C.comps[0][1])
            if e2 is None or isinstance(e2, list) or str(e2).startswith("?"):
                return self._no_conozco(C.comps[0][1], e2)
            a, b = self._edad(s), self._edad(e2)
            if a is None or b is None:
                return self._abst("No lo sé: me falta la edad de alguno de los dos.")
            d = self._entero(self._app("diferencia", a[0], b[0]))
            self.ult_just = {"pasos": [f"{self.disp(s)} tiene {a[0]} años", f"{self.disp(e2)} tiene {b[0]} años"], "app_traza": self._traza_app}
            may, men = (s, e2) if a[0] >= b[0] else (e2, s)
            return self._ok(self._fin(f"{self.disp(may)} le lleva {M.num_pal(d)} años a {self.disp(men)}".replace("un años", "un año")))
        if sust in ("año", "ano") and v == "cumplir":
            cs = [f for f in self.marcos(v="cumplir", s=s, vig=None, neg=False) if f.get("cuant") is not None]
            if cs:
                self.ult_just = {"dicho": [cs[-1]["src"]]}
                return self._ok(self._fin(self.frase(cs[-1])))
        if sust in ("año", "ano") and v in ("tener", "cumplir"):
            ed = self._edad(s)
            if ed is None:
                return self._abst(self._fin(f"No sé cuántos años {'tienes' if s == 'U' else 'tiene ' + self.disp(s)}: no me lo has dicho"), consultar=not self._conocido(s))
            n_, just = ed
            self.ult_just = just
            fut = re.search(r"\b(20\d\d|19\d\d)\b", C.cuando or "") if C.tiempo == "fut" else None
            if fut:                                     # «¿Cuántos años tendré en 2030?»
                hoy = getattr(self.mem, "today", None) or dt.date.today()
                y_ = self._fecha_nac(s)[0]
                if y_:
                    n2 = int(fut.group(1)) - y_
                    return self._ok(self._fin(f"En {fut.group(1)} {'cumplirás' if s == 'U' else 'cumplirá'} {n2} años"))
            if just.get("aprox"):                        # 2.11: sin el mes no se sabe si ya ha cumplido: las dos posibilidades
                quien = "Tienes" if s == "U" else self.disp(s) + " tiene"
                return self._ok(self._fin(f"{quien} {n_ - 1} o {n_} años: depende de si ya {'has' if s == 'U' else 'ha'} cumplido este año (no sé el mes)"))
            return self._ok(self._fin(f"{'Tienes' if s == 'U' else self.disp(s) + ' tiene'} {n_} años"))
        if sust in ("tiempo", "rato"):
            fs = [f for f in self.marcos(v=v, s=s, neg=False) if (f.get("obj_disp") or f.get("cuando")) and self._coincide_comps(f, C.comps)]
            if fs:
                self.ult_just = {"dicho": [fs[-1]["src"]]}
                return self._ok(self._fin(self.frase(fs[-1])))
            return nada()
        if not sust and C.wh and C.wh.get("prep") == "a":
            objs = list({self.can(f["obj"]): f for f in self.marcos(v=v, s=s, neg=False) if f.get("obj") and self.es_persona(f["obj"])}.values())
            objs += [f for f in self.marcos(v=v, s=s, neg=False) if not f.get("obj") and any(p == "a" and e for p, e, d in f.get("comps", []))]
            if objs:
                nombres = list(dict.fromkeys(self.disp(f["obj"]) if f.get("obj") else self.disp([e for p, e, d in f["comps"] if p == "a" and e][0]) for f in objs))
                self.ult_just = {"dicho": [f["src"] for f in objs]}
                return self._ok(self._fin(f"A {M.num_pal(len(nombres)) if len(nombres) != 1 else 'una persona'}: {self._lista(nombres)}"))
        if not sust:
            fs = [f for f in self.marcos(v=v, s=s, neg=False) if f.get("obj_disp") or f.get("comps") or f.get("modo")]
            if fs:
                self.ult_just = {"dicho": [fs[-1]["src"]]}
                return self._ok(self._fin(self.frase(fs[-1])))
            return nada()
        cl = self._canon_rel(sust)[0] if sust in REL_CANON else sust
        if v != "tener":
            objs = [f for f in self.marcos(v=v, s=s, neg=False) if f.get("obj") and not str(f["obj"]).startswith("K:") and f.get("cuant") is None
                    and (cl in ("persona", "cosa", "gente") and (cl == "cosa" or self.es_persona(f["obj"])) or self.es_clase(f["obj"], cl)[0] or self.E.get(self.can(f["obj"]), {}).get("clase") == cl)]
            objs = list({self.can(f["obj"]): f for f in objs}.values())
            if objs:
                self.ult_just = {"dicho": [f["src"] for f in objs]}
                g = M.genero_sust(cl)
                return self._ok(self._fin(f"{M.num_pal(len(objs), g).capitalize() if len(objs) != 1 else ('Una' if g == 'f' else 'Uno')}: {self._lista([self.disp(f['obj']) for f in objs])}"))
        fs = [f for f in self.marcos(v=v, s=s, neg=False, herencia=True) if f.get("obj_cls") == cl and self._tiempo_ok(f, C) and self._coincide_comps(f, C.comps)]
        con_n = [f for f in fs if f.get("cuant") is not None]
        propios_ = [f for f in con_n if f.get("s") and self.can(f["s"]) == s]
        if propios_ and len(propios_) < len(con_n):      # 2.15: lo dicho de ESTE individuo manda sobre lo típico de su clase («mi gato tiene tres patas»)
            con_n = propios_

        def _gen(f_):                                   # 2.13: «3 primas» sin género anotado: lo dice la forma («primas» frente a la clase «primo»)
            if f_.get("obj_gen"):
                return f_["obj_gen"]
            w = sa(M.singular((f_.get("obj_disp") or "").split()[-1].lower())) if f_.get("obj_disp") else ""
            return "f" if w.endswith("a") and not sa(cl).endswith("a") else ""
        if v == "tener" and con_n and any(_gen(f) for f in con_n) and len(con_n) > 1:
            fem_q = C.wh and sa(M.singular(self.ult_preg[0].split()[1] if len(self.ult_preg[0].split()) > 1 else "")).endswith("a")
            if fem_q:
                con_n = [f for f in con_n if _gen(f) == "f"] or con_n
            else:
                tot = self._entero(self._suma_app(f["cuant"] for f in con_n))
                self.ult_just = {"dicho": list(dict.fromkeys(f["src"] for f in con_n)), "app_traza": self._traza_app}
                return self._ok(self._fin(f"{M.num_pal(tot).capitalize()} en total: {self._lista([cambia_persona(f['obj_disp']) for f in con_n])}"))
        if con_n:
            f = con_n[-1]
            if len(con_n) > 1 and v != "tener":
                tot = self._entero(self._suma_app(x["cuant"] for x in con_n))
                self.ult_just = {"dicho": [x["src"] for x in con_n], "app_traza": self._traza_app}
                return self._ok(self._fin(f"{M.num_pal(tot, M.genero_sust(cl)).capitalize()} en total: " + self._lista([self.frase(x) for x in con_n])))
            self.ult_just = self._just_marco(f, s)
            return self._ok(self._fin(self.frase(f)))
        if v == "tener":
            # suma por categoría: «¿Cuántos animales tiene Sara?»
            partes, pasos, total, dudosos = [], [], 0, []
            for f in self.marcos(v="tener", s=s, neg=False):
                if f.get("cuant") is None or not f.get("obj_cls") or f.get("obj_cls") == "año":
                    continue
                ok, j = (False, [])
                if f.get("obj"):
                    ok, j = self.es_clase(f["obj"], cl)
                if not ok:
                    ok, j = self.es_clase("K:" + f["obj_cls"], cl, lexico_ok=True)
                if ok:
                    total += f["cuant"]; partes.append(cambia_persona(f["obj_disp"])); pasos += [self.frase(f)] + j[-2:]
                elif not self.clases("K:" + f["obj_cls"]) and not self._lexico_conoce(f["obj_cls"]):
                    dudosos.append(cambia_persona(f["obj_disp"]))      # no sé qué clase de cosa es: no puedo contarla ni descartarla
            if partes and dudosos:
                self.ult_just = {"pasos": list(dict.fromkeys(pasos))}
                return self._ok(self._fin(f"Al menos {M.num_pal(total, M.genero_sust(cl))}: {self._lista(partes)}. No sé si {self._lista(dudosos)} cuenta como {self._acento(cl)}"))
            if partes:
                self.ult_just = {"pasos": list(dict.fromkeys(pasos))}
                g = M.genero_sust(cl)
                tot_txt = M.num_pal(total, g).capitalize() if total != 1 else ("Una" if g == "f" else "Uno")
                if len(partes) == 1:
                    return self._ok(self._fin(f"{tot_txt}: {partes[0]}"))
                return self._ok(self._fin(f"{tot_txt}: {self._lista(partes)}"))
            # personas relacionadas contadas una a una
            xs = [r for r in self.rels(cl, y=s) if not r["x"].startswith("I:")]
            if xs:
                self.ult_just = {"pasos": [x for r in xs for x in r["j"]]}
                n_ = len(xs)
                g = "f" if all(self.gen(r["x"]) == "f" for r in xs) else "m"
                nom = self._rel_nombre(cl, g)
                return self._ok(self._fin(f"Que yo sepa, {M.num_pal(n_, g)}: {self._lista([self.disp(r['x']) for r in xs])}") if n_ > 0 else "No lo sé.")
            sin_n = [f for f in fs if f.get("cuant") is None]
            if sin_n:
                return self._abst(self._fin("No sé cuántos exactamente. Solo sé que " + self.frase(sin_n[-1])))
            if any(f.get("neg") and f.get("obj_cls") == cl for f in self.marcos(v="tener", s=s)):
                return self._ok(self._fin(f"Ninguno: {self.frase([f for f in self.marcos(v='tener', s=s) if f.get('neg') and f.get('obj_cls') == cl][0])}"))
            ten = [f for f in self.marcos(v="tener", s=s, neg=False) if f.get("obj_cls") != "año" and f.get("obj_disp")]
            if ten:
                return self._abst(self._fin(f"No lo sé. Solo sé que " + self._tener_lista(s, ten)))
        return nada(f"no me has dicho cuánt{'a' if M.genero_sust(cl) == 'f' else 'o'}s {M.plural(cl)} {M.conjugar(v, 'pres', self._persona_de(s))}{'' if s == 'U' else ' ' + self.disp(s)}")

    def _que_hace(self, C, s, nada, pasado, solo_trabajo=False):
        if s is None:
            return None
        if C is not None and C.neg:
            negs = [f for f in self.marcos(s=s, neg=True) if f["v"] not in ("ser", "estar") and not f.get("efecto")]
            if negs:
                self.ult_just = {"dicho": [f["src"] for f in negs]}
                return self._ok(self._fin(self._lista([self.frase(f) for f in negs[:4]])))
            return nada()
        trab = [f for f in self.marcos(s=s, neg=False) if (f["v"] in ("trabajar", "dedicar", "estudiar") or f.get("prof") or (f["v"] == "ser" and (set(f.get("isa", [])) | set(f.get("attr", []))) & (self._profesiones() - FAMILIA - SIMETRICAS - {"gato", "perro", "niño", "chico", "alumno", "empleado", "hombre", "persona"})))]
        if solo_trabajo:
            if trab:
                self.ult_just = {"dicho": [f["src"] for f in trab]}
                return self._ok(self._fin(self._lista([self.frase(f) for f in trab[:2]])))
            return nada()
        acts = [f for f in self.marcos(s=s, vig=None, neg=False) if f["v"] not in ("ser", "estar", "tener", "llamar", "parecer", "vivir", "nacer") and not f.get("exp") and not f.get("efecto")]
        if C is not None and (C.cuando or C.freq):
            acts = [f for f in acts if self._tiempo_ok(f, C)]
        elif pasado:
            acts = [f for f in acts if f.get("t") in ("pret", "imp")]
        elif C is not None and C.tiempo == "pres":
            pres = [f for f in acts if f.get("t") == "pres"]
            acts = pres or ([] if not trab else [])
            acts = (trab if not pres else [f for f in trab if f not in pres] + pres) if not (C.cuando or C.freq) else acts
        elif C is not None and C.tiempo == "fut":
            acts = [f for f in acts if f.get("t") == "fut"]
        if not acts:
            return nada(f"no me has dicho qué {M.conjugar('hacer', 'pret' if pasado else 'pres', self._persona_de(s))}{'' if s == 'U' else ' ' + self.disp(s)}")
        self.ult_just = {"dicho": list(dict.fromkeys(f["src"] for f in acts))}
        return self._ok(self._fin(self._lista([self.frase(f, sin_sujeto=bool(i and f.get("fab") and acts[0].get("fab") and f["s"] == acts[0]["s"])) for i, f in enumerate(acts[:4])])))

    def _quien(self, C: Clausula):
        v = C.v
        o = C.obj
        if v == "ser" and C.suj is None and o is None and not C.attr and not C.comp and not C.comps:
            if C.pers == "1s":
                r = self.resumen("U")
                return self._ok(r) if r else self._abst("Todavía no sé casi nada de ti. ¿Cómo te llamas?")
            return None
        # copulativas
        if v == "ser" and C.suj is None and o is not None and not C.attr and not C.comp:
            self._recuerda_preg(self.ult_preg[0], o)
            if o.cab and (o.de is not None or o.pos) and not o.propio:
                return self._papel(o, None)
            if o.cab and not o.det and not o.coord and (not o.propio or ("N:" + o.cab) not in self.E):
                qa_ = {o.cab, M.masc(o.cab), M.masc(sa(o.cab))}                 # «¿Quién es profesora?» con «Sofía es profesora de inglés»
                fs_ = [f for f in self.F if f["v"] == "ser" and f.get("vig", True) and not f.get("neg") and not f.get("erroneo") and qa_ & set(f.get("attr", [])) and not str(f["s"]).startswith("K:")]
                if fs_:
                    self.ult_just = {"dicho": [f["src"] for f in fs_]}
                    return self._ok(self._fin(self._lista_frases(fs_)))
            e = self._q_ent(o)
            if isinstance(e, list):
                e = e[0]
            if e == "L":
                return None
            if e is None or str(e).startswith("?") or not self._conocido(e):
                return self._no_conozco(o, e) if o.propio or str(e).startswith("?") else self._abst("No lo sé.", consultar=True)
            e = self.can(e)
            self.mencionar(e); self.ult_suj = e
            if e == "U":
                r = self.resumen("U")
                return self._ok(r) if r else self._abst("Todavía no sé casi nada de ti. ¿Cómo te llamas?")
            r = self.resumen(e)
            if not r:                                   # solo aparece como complemento: «vives con Carla»
                fs_c = [f for f in self.F if f.get("vig", True) and not f.get("erroneo") and any(c_[1] and self.can(c_[1]) == e for c_ in f.get("comps", []))]
                if fs_c:
                    self.ult_just = {"dicho": [f["src"] for f in fs_c]}
                    r = self._fin(_cap(self._lista([self.frase(f) for f in fs_c[-2:]])))
            return self._ok(r) if r else self._no_conozco(o, e)
        if v == "tener" and o is not None and o.cab in ("año", "ano") and o.cuant in ("mas", "menos") or (v == "tener" and o is not None and o.coord and o.coord[0].cab in ("año", "ano")):
            partes = o.coord[1:] if o.coord else []
            if not partes and C.obj2 is not None:
                partes = C.obj2.coord or [C.obj2]
            menos = (o.cuant == "menos") if not o.coord else (o.coord[0].cuant == "menos")
            cands = []
            for sn_ in partes:
                e = self._q_ent(sn_)
                if e is None or str(e).startswith("?"):
                    return self._no_conozco(sn_, e)
                cands.append(self.can(e))
            return self._quien_mas(C, "mayor", "menos" if menos else "mas", cands)
        if v in ("ser", "estar") and C.comp and C.comp[2] is not None and o is None and not C.comp[2].coord:
            op, adj, sn2 = C.comp
            e2 = self._q_ent(sn2)
            if e2 is None or isinstance(e2, list) or str(e2).startswith("?"):
                return self._no_conozco(sn2, e2)
            e2 = self.can(e2)
            orden = self._orden(adj)
            xs = [a for (a, b) in orden if b == e2] if op == "mas" else [b for (a, b) in orden if a == e2]
            if not xs:
                return self._abst(self._fin(f"No lo sé: no me consta nadie así respecto a {self.disp(e2)}"))
            pasos = []
            for x in xs:
                pasos += orden[(x, e2)] if op == "mas" else orden[(e2, x)]
            self.ult_just = {"pasos": list(dict.fromkeys(pasos))}
            mas = "" if adj in ("mayor", "menor", "mejor", "peor") else ("más " if op == "mas" else "menos ")
            pl = len(xs) > 1
            adj_d = self._acento(M.concuerda(adj, "f" if all(self.gen(x) == "f" for x in xs) else "m", pl))
            return self._ok(self._fin(f"{self._lista([self.disp(x) for x in xs])} {'son' if pl else 'es'} {mas}{adj_d} que {self.disp(e2)}"))
        if v in ("ser", "estar") and C.comp:
            op, adj, sn2 = C.comp
            cands = []
            for sn_ in ([sn2] if sn2 is not None else []) + ([o] if o is not None else []):
                e = self._q_ent(sn_)
                if e is None or (isinstance(e, str) and e.startswith("?")):
                    return self._no_conozco(sn_, e)
                cands += e if isinstance(e, list) else [e]
            return self._quien_mas(C, adj, op, [self.can(e) for e in cands])
        if v in ("ser", "estar") and C.attr and len(C.attr) == 1 and C.attr[0] in ("mayor", "menor", "mejor", "peor") and (o is None or o.coord):
            cands = []
            if o is not None:
                e = self._q_ent(o)
                if e is None:
                    return self._no_conozco(o.coord[0] if o.coord else o)
                cands = e if isinstance(e, list) else [e]
            if any(c is None or str(c).startswith("?") for c in cands):
                return self._abst("No lo sé: no conozco a alguno de ellos.")
            return self._quien_mas(C, C.attr[0], "mas", [self.can(e) for e in cands])
        if v in ("ser", "estar", "parecer") and (C.attr or o is not None):
            qa = set(C.attr)
            if o is not None and o.cab and not o.propio:
                qa.add(self._canon_rel(o.cab)[0] if o.cab in REL_CANON else o.cab)
                qa.add(M.masc(o.cab))
            qa |= {M.masc(a_) for a_ in qa}
            fs = [f for f in self.F if f["v"] in ("ser", "estar") and f.get("vig", True) and not f.get("neg") and (qa & set(f.get("attr", [])) or qa & {str(a_).split(" ")[0] for a_ in f.get("attr", [])}) and self._coincide_comps(f, C.comps)]
            fs = [f for f in fs if not str(f["s"]).startswith("K:")] or fs
            if fs:
                self.ult_just = {"dicho": [f["src"] for f in fs]}
                return self._ok(self._fin(self._lista_frases(fs)))
            # 2.15: «¿quién es político?» con «mi vecino es alcalde»: quien pertenece a esa clase por lo que es (cierre de clases)
            cl_q = next((KB._kb_clase(a_) for a_ in qa if KB._kb_clase(a_)), None)
            if cl_q:
                hall = []
                for e_ in list(self.E):
                    if e_.startswith("K:") or e_ in ("L",):
                        continue
                    for c_, j_ in self.clases(e_):
                        if c_ == cl_q and not (j_ and "es una persona" in j_[0]):
                            hall.append((e_, j_)); break
                if hall:
                    self.ult_just = {"pasos": hall[0][1]}
                    g_ = M.genero_sust(cl_q)
                    def _fr(e_):
                        d_ = self.disp(e_) if e_ != "U" else "tú"
                        return f"{d_} {'eres' if e_ == 'U' else 'es'} {self._un(cl_q, g_)}"
                    extra = f" Lo deduzco {self._porque(hall[0][1])}." if len(hall[0][1]) > 1 else ""
                    return self._ok(self._fin(_cap(self._lista([_fr(e_) for e_, _ in hall]))) + extra)
            return self._abst("No lo sé: nadie que yo conozca, por lo que me has contado.")
        # «¿Quién mide más, Aitor o Vega?», «¿Quién pesa menos?»
        if o is not None and (o.cab in ("mas", "menos") or (o.coord and o.coord[0].cab in ("mas", "menos"))) or (C.modo and sa(C.modo[0]) in ("mas", "menos")) or (C.comp and C.comp[1] in ("mas", "menos")):
            op = "menos" if "menos" in (sa(" ".join(C.modo)) + " " + (o.texto if o is not None else "")) else "mas"
            partes = []
            for sn_ in ([o] if o is not None else []) + ([C.obj2] if C.obj2 is not None else []):
                partes += [x for x in (sn_.coord or [sn_]) if x.propio or x.det or x.pos]
            cands = []
            for sn_ in partes:
                e = self._q_ent(sn_)
                if e is None or isinstance(e, list) or str(e).startswith("?"):
                    return self._no_conozco(sn_, e)
                cands.append(self.can(e))
            r = self._por_medida(v, op, cands)
            if r:
                mejor, vals = r
                return self._ok(self._fin(vals[mejor][1]))
            if len(cands) == 2:                          # 2.11: «¿Quién corre más rápido, Marta o Raúl?» con «Raúl corre más rápido que Marta»
                for f in reversed(self.F):
                    if f["v"] == v and f.get("comp") and f.get("vig", True) and not f.get("neg") and f["comp"][0] in ("mas", "menos") \
                            and {self.can(f["s"]), self.can(f["comp"][2] or "")} == set(cands):
                        self.ult_just = {"dicho": [f["src"]]}
                        return self._ok(self._fin(self.frase(f)))
            if len(cands) == 2:                          # 2.17: la comparación con un verbo también se encadena («A corre más que B», «B corre más que C»)
                pares = {}
                for f in self.F:
                    if f["v"] == v and f.get("comp") and f.get("vig", True) and not f.get("neg") and f["comp"][0] in ("mas", "menos") and f["comp"][2]:
                        x_, y_ = self.can(f["s"]), self.can(f["comp"][2])
                        clave_ = f["comp"][1]
                        pares.setdefault(clave_, {})[(x_, y_) if f["comp"][0] == "mas" else (y_, x_)] = [f]
                for clave_, cierre in pares.items():
                    cambio = True
                    while cambio:
                        cambio = False
                        for (a_, b_), j1 in list(cierre.items()):
                            for (b2, c_), j2 in list(cierre.items()):
                                if b_ == b2 and a_ != c_ and (a_, c_) not in cierre:
                                    cierre[(a_, c_)] = j1 + j2; cambio = True
                    for gana, pierde in ((cands[0], cands[1]), (cands[1], cands[0])):
                        if (gana, pierde) in cierre:
                            js = cierre[(gana, pierde)]
                            self.ult_just = {"dicho": [f["src"] for f in js]}
                            g2 = gana if op == "mas" else pierde
                            p2 = pierde if op == "mas" else gana
                            base_f = dict(js[0]); base_f["s"] = g2; base_f["comp"] = [op, clave_, p2]; base_f["suj_txt"] = ""
                            return self._ok(self._fin(self.frase(base_f)) + " Lo deduzco porque " + " y ".join(self.frase(f) for f in js) + ".")
            return self._abst("No lo sé: me faltan datos para comparar.")
        # verbos: la incógnita es el sujeto
        o_ = o
        if o_ is not None:
            self._recuerda_preg(self.ult_preg[0], o_)
        fs = [f for f in self.marcos(v=v, vig=None) if not f.get("exp") and self._coincide_obj(f, o_) and self._coincide_comps(f, C.comps) and self._tiempo_ok(f, C) and bool(f.get("neg")) == bool(C.neg)
              and (not C.lugar_adv or f.get("lugar_adv") == C.lugar_adv) and (not C.xinf or sa(C.xinf) == sa(f.get("xinf", "")))]
        if ("me" in C.clit or "te" in C.clit) and C.pers in ("3s", "3p") and not C.refl:
            yo_ = "U" if "me" in C.clit else "L"         # «¿Quién me opera?»: otra persona que me opera, no «me opero»
            fs_o = [f for f in fs if self.can(f.get("s") or "") != yo_ and not f.get("refl")]
            fs = [f for f in fs_o if self.can(f.get("obj") or "") == yo_ or any(self.can(c_[1] or "") == yo_ for c_ in f.get("comps", []))] or fs_o
        if o_ is not None and not (o_.cab or o_.propio or o_.pron or o_.coord):
            return None
        vig = [f for f in fs if f.get("vig", True)]
        if C.tiempo in ("imp",) and not vig:
            vig = [f for f in fs if not f.get("vig", True)]
        if v == "tener" and o_ is not None and not C.neg:
            vig = [f for f in vig if not f.get("neg")]
        vig = [f for f in vig if f["s"] and not self.E.get(self.can(f["s"]), {}).get("nadie")]
        if vig:
            vig = list({(self.can(f["s"])): f for f in vig}.values())
            self.ult_just = {"dicho": list(dict.fromkeys(f["src"] for f in vig))}
            for f in vig:
                self.mencionar(f["s"])
            self.ult_suj = self.can(vig[-1]["s"])
            return self._ok(self._fin(self._lista_frases(vig)))
        if v == "tener" and o_ is not None and o_.cab:
            cl = self._clase_sn(o_)[0]
            xs = [(self.can(q["x"]), self.can(q["y"])) for q in self.R if q["r"] == cl]
            if xs:
                return self._ok(self._fin(self._lista(list(dict.fromkeys(self.disp(y) for _, y in xs))) + f" tiene {self._un(cl, M.genero_sust(cl))}".replace("tú tiene", "tú tienes")))
        return self._abst("No lo sé: nadie me ha dicho eso.", consultar=not self.F and not self.R)

    def _prep_quien(self, C: Clausula, prep):
        v = C.v
        if prep == "con" and ((v == "estar" and "casado" in C.attr) or (v == "casar" and C.refl)):
            s_, sn_s, _o = self._sujeto_preg(C, wh="quien")
            if s_ and not isinstance(s_, list) and not str(s_).startswith("?"):
                ps = self.rels("esposo", x=s_) or self.rels("esposo", y=s_)
                if ps:
                    otro = ps[0]["y"] if self.can(ps[0]["x"]) == self.can(s_) else ps[0]["x"]
                    self.ult_just = {"pasos": ps[0]["j"]}
                    return self._ok(self._fin(f"{self.disp(s_) if s_ != 'U' else 'Estás'} {'está ' if s_ != 'U' else ''}{M.concuerda('casado', self.gen(s_))} con {self.disp(otro)}"))
        if v == "ser" and prep == "de" and C.obj is not None and (C.obj2 is not None or C.suj is not None):
            a, b = (C.obj, C.obj2) if C.suj is None else (C.obj, C.suj)
            rel_sn, ent_sn = (a, b) if (not a.propio and not a.det and not a.pos) else (b, a)
            if rel_sn is not None and ent_sn is not None and rel_sn.cab and not rel_sn.propio:
                cl, g = self._clase_sn(rel_sn)
                x = self._q_ent(ent_sn)
                if x is None or isinstance(x, list) or str(x).startswith("?"):
                    return self._no_conozco(ent_sn, x)
                x = self.can(x)
                ps = self.rels(cl, x=x)
                if ps:
                    j = [y for r in ps for y in r["j"]]
                    self.ult_just = {"pasos": list(dict.fromkeys(j))}
                    return self._ok(self._fin(self._lista([self._frase_rel(cl, x, r["y"]) for r in ps[:3]])))
                return self._abst(self._fin(f"No lo sé: no me has dicho de quién es {self._acento(self._rel_nombre(cl, self.gen(x)))} {self.disp(x)}"))
        if v == "ser" and prep == "de":
            # dueño: «¿De quién es el coche?»
            s, sn_s, o = self._sujeto_preg(C, wh="quien")
            obj = sn_s
            if obj is None or not obj.cab:
                return None
            if isinstance(s, str) and not s.startswith(("K:", "?")):
                s = self.can(s)
                dn = [self.can(q["y"]) for q in self.R if self.can(q["x"]) == s and q["r"] not in FAMILIA and q["r"] not in SIMETRICAS and q["r"] not in INVERSAS]
                act = self.E.get(s, {}).get("dueno_act")
                if act:
                    dn = [self.can(act)]
                if dn:
                    y = dn[-1]
                    self.ult_just = None
                    return self._ok(self._fin(f"{self.disp(s)} es {'tuyo' if y == 'U' and self.gen(s) == 'm' else ('tuya' if y == 'U' else 'de ' + self.disp(y))}"))
                ten = [f for f in self.F if f["v"] == "tener" and f.get("vig", True) and not f.get("neg") and self.can(f.get("obj") or "") == s]
                if ten:
                    return self._ok(self._fin(self.frase(ten[-1])))
                return self._abst(self._fin(f"No sé de quién es {self.disp(s)}"))
            cl = self._clase_sn(obj)[0]
            due = [(self.can(q["x"]), self.can(q["y"])) for q in self.R if q["r"] == cl]
            if due:
                x, y = due[-1]
                act = self.E.get(x, {}).get("dueno_act")
                y = self.can(act) if act else y
                self.ult_just = None
                art = "la" if M.genero_sust(cl) == "f" else "el"
                return self._ok(self._fin(f"{art} {cl} es {'tuyo' if y == 'U' and art == 'el' else ('tuya' if y == 'U' else 'de ' + self.disp(y))}"))
            return self._abst(self._fin(f"No sé de quién es {obj.texto}"))
        s, sn_s, o = self._sujeto_preg(C, wh="quien")
        if s is None or isinstance(s, list) or str(s).startswith("?"):
            return self._no_conozco(sn_s, s) if sn_s is not None else None
        if s == "L":
            return None
        s = self.can(s)
        self._recuerda_preg(self.ult_preg[0], sn_s)
        fs = [f for f in self.marcos(v=v, s=s, vig=None, neg=False) if any(p2 == prep and e2 for p2, e2, _ in f.get("comps", [])) and self._coincide_obj(f, o)
              and self.prep_con_papel(f, prep, P.papeles_de_pregunta("quien", prep))]   # «¿con quién corto?» no lo responde «con una sierra»
        if prep == "a":
            fs += [f for f in self.marcos(v=v, s=s, vig=None, neg=False) if f.get("obj") and self.es_persona(f["obj"]) and f not in fs]
        vig = [f for f in fs if f.get("vig", True)] or fs
        if vig:
            self.ult_just = {"dicho": [f["src"] for f in vig]}
            return self._ok(self._fin(self._lista_frases(vig)))
        if prep in ("con", "para"):
            # «salgo a cenar con dos compañeros» (+ «se llaman Rafa y Toni»): el grupo va como texto
            fg = [f for f in self.marcos(v=v, s=s, vig=True, neg=False) if any(p2 == prep and d2 for p2, _, d2 in f.get("comps", [])) and self.prep_con_papel(f, prep, P.papeles_de_pregunta("quien", prep))]
            if fg:
                f = fg[-1]
                d2 = [d2 for p2, _, d2 in f["comps"] if p2 == prep and d2][0]
                mm = re.search(r"([a-záéíóúñ]+s)$", sa(d2))
                noms = []
                if mm:
                    cl0 = M.masc(sa(M.singular(mm.group(1))))
                    noms = [r_["x"] for r_ in self.R if r_["r"] == cl0 and self.can(r_["y"]) == s and str(r_["x"]).startswith("N:")]
                self.ult_just = {"dicho": [f["src"]]}
                txt = _cap(self.frase(f))
                if noms:
                    txt += ": " + self._lista([self.disp(x) for x in noms])
                return self._ok(self._fin(txt))
        sab = self._se_de(s)
        return self._abst("No lo sé." + (" " + sab if sab else ""), consultar=not self._conocido(s))

    def _por_que(self, C: Clausula):
        s, sn_s, o = self._sujeto_preg(C, wh="porque")
        if s is None or isinstance(s, list) or str(s).startswith("?"):
            return self._no_conozco(sn_s, s) if sn_s is not None else None
        if s == "L":
            return None
        s = self.can(s)
        fs = [f for f in self.marcos(v=C.v, s=s, vig=None) if self._coincide_obj(f, o) and (not C.attr or set(C.attr) & set(f.get("attr", []))) and bool(f.get("neg")) == bool(C.neg)]
        if C.v in G.GUSTAR:
            fs = [f for f in self.F if f["v"] == C.v and self.can(f["s"]) == s]
        con = [f for f in fs if f.get("causa")]
        if con:
            f = con[-1]
            self.ult_just = {"dicho": [f["src"]]}
            from .nucleo import causa_tu
            return self._ok(self._fin("Porque " + causa_tu(f["causa"])))
        if fs:
            f = fs[-1]
            if f.get("por"):
                return self._ok(self._fin("Porque " + f["por"]))
            if f.get("v") == "estar" and f.get("attr"):  # «agobiado con el trabajo», «preocupada por su madre»: el complemento es el motivo
                mot = [(p2, d2) for p2, e2, d2 in f.get("comps", []) if p2 in ("con", "por") and d2]
                if mot:
                    self.ult_just = {"dicho": [f["src"]]}
                    return self._ok(self._fin(f"Por lo que me dijiste, {mot[0][0]} {cambia_persona(mot[0][1])}: " + self.frase(f)))
            return self._abst(self._fin("No me has dicho por qué. Solo sé que " + self.frase(f)))
        return self._abst("No lo sé: no me consta eso.", consultar=not self._conocido(s))

    # ================================================================== explicación de la última respuesta
    # 2.13: las cuentas con datos de la conversación también las hacen las aplicaciones (src/apps), no el núcleo
    def _app(self, nombre, *xs):
        from src.apps import registro as RA
        v, tr = RA.ejecuta(nombre, *xs)
        self._traza_app = list(getattr(self, "_traza_app", None) or []) + [tr]
        return v

    def _suma_app(self, xs):
        xs = list(xs)
        return xs[0] if len(xs) == 1 else self._app("suma", *xs)

    @staticmethod
    def _entero(v):
        try:
            return int(v) if v == int(v) else float(v)
        except (TypeError, ValueError):
            return v

    def explica(self):
        r = self._explica_base()
        j = self.ult_just or {}
        if j.get("app") and j.get("texto"):
            return j["texto"]
        if r and j.get("app_traza"):
            from . import calculo as CA
            r = r.rstrip() + " " + CA.justificacion(j["app_traza"], breve=True)
        return r

    def _explica_base(self):
        j = self.ult_just
        if not j or j.get("app"):
            return None
        if j.get("pasos") and not j.get("fabrica") and all(x in self._pasos_fab for x in j["pasos"] if x):
            j = dict(j, fabrica=True)
        elif j.get("pasos") and any(x in self._pasos_fab for x in j["pasos"] if x):
            pasos = [x for x in dict.fromkeys(j["pasos"]) if x]
            return self._fin("Lo deduzco " + self._porque(pasos)) + " Parte me lo has dicho tú y parte lo traigo aprendido de fábrica."
        if j.get("fabrica") and j.get("pasos"):
            return self._fin("Lo traigo aprendido de fábrica: " + self._lista([x for x in dict.fromkeys(j["pasos"]) if x][:3])) + " No viene de lo que me has contado."
        if j.get("dicho") and all(x == "fábrica" for x in j["dicho"]):
            return "Es un concepto que traigo aprendido de fábrica; no viene de lo que me has contado."
        if j.get("pasos"):
            pasos = [x for x in dict.fromkeys(j["pasos"]) if x]
            return self._fin("Lo deduzco " + self._porque(pasos)) if len(pasos) > 1 else self._fin("Porque " + pasos[0])
        if j.get("dicho"):
            srcs = [x for x in dict.fromkeys(j["dicho"]) if x]
            if srcs:
                return "Porque me lo dijiste tú: " + self._lista([f"«{x.rstrip('.')}»" for x in srcs[:3]]) + "."
        if j.get("dicho_rel"):
            srcs = [x for x in j.get("src", []) if x]
            if srcs:
                return "Porque me lo dijiste tú: " + self._lista([f"«{x.rstrip('.')}»" for x in srcs[:2]]) + "."
            return self._fin("Porque me dijiste que " + j["dicho_rel"])
        return None


# ====================================================================== 2.10 · papeles de las preposiciones
_FIG_OBJ = {"tener", "haber", "poner", "dejar", "guardar", "colocar", "meter", "aparcar", "esconder", "olvidar", "encontrar"}


def _cabeza(txt):
    ws = [w for w in re.findall(r"[a-zñ]+", sa((txt or "").lower())) if w not in P._DET]
    if not ws:
        return ""
    w = ws[0]
    return sa(M.singular(w)) if w.endswith("s") and len(w) > 3 else w


class Papeles:
    """Mezcla para Preguntador: las preguntas buscan papeles (lugar, causa, compañía…), no la preposición literal."""

    def papeles_marco(self, f):
        comps = f.get("comps", []) or []
        preps = [c[0] for c in comps]
        out = []
        for p, e, d in comps:
            cat = P.categoria(d, e, self)
            if p == "a" and "de" in preps and cat in ("hora", "tiempo", ""):
                pap = "t_fin"                              # «abre de nueve a dos»
            else:
                pap = P.papel(p, cat, f.get("v", ""), d, hay_obj=bool(f.get("obj")), otra_prep="a" if p == "de" and "a" in preps else None)
            out.append((pap, p, e, d, False))
        # lo que va dentro del objeto: «un anillo de plata», «un libro sobre mi abuelo», «un viaje a Lisboa»
        od = f.get("obj_disp") or ""
        for m in re.finditer(r"\b(de|sobre|para|con|sin|contra)\s+((?:(?:el|la|los|las|un|una|mi|tu|su|mis|tus|sus)\s+)?[^\s,.;]+(?:\s+[A-ZÁÉÍÓÚÑ][^\s,.;]*)?)", od):
            p, d = m.group(1), m.group(2)
            cat = P.categoria(d)
            v_ = f.get("v", "")
            pap = P.papel(p, cat, v_, d)
            if p == "de" and cat == "material":
                pap = "materia"
            elif p == "sobre":
                pap = "tema"
            if pap in ("de", "con", "sobre", "para", "sin", "contra"):
                continue
            out.append((pap, p, None, d, True))
        return out

    def prep_con_papel(self, f, prep, papeles):
        """¿Tiene el marco un complemento con esa preposición cuyo papel casa (o no está claro)? Si todos tienen otro papel claro, no."""
        if not papeles:
            return True
        ps = [x for x in self.papeles_marco(f) if not x[4] and x[1] == prep]
        if not ps:
            return True
        return any(P.casa_papel(x[0], papeles) or x[0] == prep for x in ps)

    # ------------------------------------------------------------ espacio
    def relaciones_espacio(self):
        out = []
        for f in self.F:
            if not f.get("vig", True) or f.get("neg"):
                continue
            for pap, p, e, d, _int in self.papeles_marco(f):
                if not pap.startswith("posicion:"):
                    continue
                rel = pap.split(":", 1)[1]
                if f["v"] in _FIG_OBJ and f.get("obj"):
                    fig, ft = f["obj"], f.get("obj_disp") or self.disp(f["obj"])
                else:
                    fig, ft = f["s"], (cambia_persona(f["suj_txt"]) if f.get("suj_txt") else self.disp(f["s"]))
                out.append({"fig": fig, "ft": ft, "rel": rel, "fondo": e, "fdt": d, "f": f})
        return out

    def _mismo(self, e, txt, sn):
        if sn is None:
            return False
        try:
            q = self._q_ent(sn)
        except Exception:                                  # noqa
            q = None
        if q and e and isinstance(q, str) and not q.startswith("?") and self.can(q) == self.can(e):
            return True
        h = _cabeza(sn.texto)
        return bool(h) and h == _cabeza(txt or (self.disp(e) if e else ""))

    def _decir_rel(self, ft, rel, fdt):
        return _cap(contrae(f"{cambia_persona(ft)} {'están' if _cabeza(ft) != sa((ft or '').split()[-1]) and (ft or '').split()[-1].endswith('s') else 'está'} {P.DECIR_REL.get(rel, rel)} {cambia_persona(fdt)}"))

    def espacio_pregunta(self, C, wh):
        """«¿Qué hay debajo de la cama?», «¿Qué tengo encima de la mesa?» (directo o por la relación inversa)."""
        if wh is None or wh.get("tipo") not in ("que", "quien", "cual") or wh.get("prep"):
            return None
        loc = [(p, sn) for p, sn in C.comps if p in P.REL_DE_PREP]
        if len(loc) != 1:
            return None
        p, sn = loc[0]
        rel = P.REL_DE_PREP[p]
        rels = self.relaciones_espacio()
        directas = [r for r in rels if r["rel"] == rel and self._mismo(r["fondo"], r["fdt"], sn)]
        if directas:
            vistos, sel = set(), []
            for r in directas:                          # una por figura: la frase original, no la derivada
                h = _cabeza(r["ft"])
                if h not in vistos:
                    vistos.add(h); sel.append(r)
            self.ult_just = {"dicho": [r["f"]["src"] for r in sel]}
            return self._ok(self._fin(". ".join(_cap(self.frase(r["f"])) for r in sel[-3:])))
        inv = P.INVERSA.get(rel)
        inversas = [r for r in rels if inv and r["rel"] == inv and self._mismo(r["fig"], r["ft"], sn)]
        if inversas:
            r = inversas[-1]
            self.ult_just = {"dicho": [r["f"]["src"]]}
            return self._ok(self._fin(f"{self._decir_rel(r['fdt'], rel, r['ft'])}. Lo deduzco porque {self.frase(r['f'])}"))
        return self._abst(self._fin(f"No me has dicho qué hay {P.DECIR_REL.get(rel, rel)} {cambia_persona(sn.texto)}"))

    def espacio_si_no(self, C):
        """«¿La cama está encima de la mochila?» con «la mochila está debajo de la cama»: la relación inversa."""
        if C.v not in ("estar", "haber", "quedar", "encontrar") or C.suj is None:
            return None
        loc = [(p, sn) for p, sn in C.comps if p in P.REL_DE_PREP]
        if len(loc) != 1:
            return None
        p, sn = loc[0]
        rel = P.REL_DE_PREP[p]
        rels = self.relaciones_espacio()
        A = C.suj

        def busca(rel_x, fig_sn, fondo_sn):
            return [r for r in rels if r["rel"] == rel_x and self._mismo(r["fig"], r["ft"], fig_sn) and self._mismo(r["fondo"], r["fdt"], fondo_sn)]
        si = busca(rel, A, sn)
        if si:
            self.ult_just = {"dicho": [si[-1]["f"]["src"]]}
            return self._ok(self._fin(("No, " if C.neg else "Sí, ") + self.frase(si[-1]["f"])))
        inv = P.INVERSA.get(rel)
        si_inv = busca(inv, sn, A) if inv else []
        if si_inv:
            r = si_inv[-1]
            self.ult_just = {"dicho": [r["f"]["src"]]}
            return self._ok(self._fin(f"{'No' if C.neg else 'Sí'}: lo deduzco porque {self.frase(r['f'])}"))
        for r2 in P.CONTRARIA.get(rel, ()):
            no = busca(r2, A, sn) or (busca(P.INVERSA[r2], sn, A) if r2 in P.INVERSA else [])
            if no:
                r = no[-1]
                self.ult_just = {"dicho": [r["f"]["src"]]}
                return self._ok(self._fin(f"{'Sí' if C.neg else 'No'}: {self.frase(r['f'])}"))
        return None

    # ------------------------------------------------------------ pregunta por papel
    def por_papel(self, C, wh):
        tipo, prep, sust = wh.get("tipo"), wh.get("prep", ""), wh.get("sust", "")
        prep = wh.get("prep_orig") or prep
        busc = P.papeles_de_pregunta(tipo, prep, C.v, sust)
        if not busc:
            return None
        try:
            s, sn_s, o = self._sujeto_preg(C, wh=tipo)
        except Exception:                                  # noqa
            return None
        if s is None or isinstance(s, list) or str(s).startswith("?") or s == "L":
            return None
        if C.suj is not None and C.suj.cab and not C.suj.pron and s not in ("U",) and not self._mismo(s, None, C.suj):
            return None                                 # el sujeto de la pregunta no es la entidad resuelta
        if sn_s is not None and sn_s.cab and not sn_s.pron:
            q_ = self._q_ent(sn_s)                      # «la hermana de Óscar» sin conocerla: no vale contestar con Óscar
            if q_ is None or isinstance(q_, list) or str(q_).startswith("?") or self.can(q_) != self.can(s):
                return None
        s = self.can(s)
        if o is not None and (o is C.obj and (C.suj is None) or self._mismo(s, None, o)):
            o = None                                    # «¿hasta qué hora abre la biblioteca?»: el SN pospuesto es el sujeto
        neg = bool(C.neg)
        pasado = C.tiempo in ("pret", "imp")
        cand = []
        for f in reversed(self.F):
            if bool(f.get("neg")) != neg and f["v"] == C.v:
                continue
            if not f.get("vig", True) and not pasado:
                continue                                # lo que ya no vale no responde a una pregunta en presente
            sujeto = f.get("s") and self.can(f["s"]) == s
            objeto = f.get("obj") and self.can(f["obj"]) == s
            if not (sujeto or objeto):
                continue
            if f["v"] != C.v and not (C.v in ("ser", "estar", "haber") or objeto):
                continue
            if o is not None and sujeto and f["v"] == C.v and not self._coincide_obj(f, o):
                continue
            for pap, p, e, d, interno in self.papeles_marco(f):
                if P.casa_papel(pap, busc):
                    if interno and not objeto and not (tipo in ("que", "cual") and prep in ("de", "sobre")) and tipo not in ("quien",):
                        pass
                    cand.append((0 if f["v"] == C.v else 1, f))
                    break
        if not cand:
            return None
        cand.sort(key=lambda x: x[0])
        f = cand[0][1]
        self.ult_just = {"dicho": [f["src"]]}
        return self._ok(self._fin(_cap(self.frase(f))))


for _k, _v in list(Papeles.__dict__.items()):
    if not _k.startswith("__"):
        setattr(Preguntador, _k, _v)
