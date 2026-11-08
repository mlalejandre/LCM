"""Relaciones entre los conceptos de un texto: lo que no esta escrito en una sola frase y hay que *calcular* o *comparar*.

La lectura de entidades (lectura_ent) contesta lo que una frase dice. Este modulo contesta lo que varias frases, o una frase leida
con cuidado, implican:
  * cantidades con duenyo: «la flota britanica, por 27; la combinada, por 33» -> cada cantidad sabe de quien es (tambien con elipsis y «ninguno»);
  * comparar («que flota tenia mas navios»), sumar («en total»), restar («cuantos mas»);
  * fechas: edad en un momento, anyos entre dos sucesos, duracion, a partir de las fechas que el propio texto da;
  * verificacion de si/no: contradicciones por cargo («Logrono, capital de La Rioja» ≠ capital de Aragon), por adjetivo opuesto, por complemento
    distinto de un verbo funcional y por negacion del complemento («no por la relatividad, sino por…»);
  * ubicacion encadenada («Zaragoza, capital de Aragon» -> «¿en que comunidad esta Zaragoza?»), gentilicios («almirante frances» -> nacionalidad)
    y recuento de enumeraciones.
Nada aqui conoce un texto concreto: trabaja sobre el arbol de cada frase y sobre las preguntas ya analizadas."""
from __future__ import annotations

import datetime
import re
from typing import Dict, List, Optional, Set, Tuple

from . import lectura_ent as L
from .lectura_ent import Frase, Indice, Q, nrm

# ====================================================== numeros ====================================================================
_UNI = {"cero": 0, "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
        "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiun": 21, "veintiuno": 21, "veintiuna": 21,
        "veintidos": 22, "veintitres": 23, "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26, "veintisiete": 27, "veintiocho": 28, "veintinueve": 29, "treinta": 30,
        "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90, "cien": 100, "ciento": 100, "doscientos": 200, "doscientas": 200,
        "trescientos": 300, "cuatrocientos": 400, "quinientos": 500, "seiscientos": 600, "setecientos": 700, "ochocientos": 800, "novecientos": 900,
        "ninguno": 0, "ninguna": 0, "ningun": 0}
_PALABRAS_N = {v: k for k, v in {"cero": 0, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
                                  "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20}.items()}
_NUM_RX = re.compile(r"^\d+(?:[.,]\d+)?$")


def _a_float(s: str) -> Optional[float]:
    s = s.replace(" ", "")
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", s):
        return float(s.replace(".", ""))
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def valor_palabras(ws: List[str]) -> Optional[float]:
    """«treinta y cinco», «cuarenta mil», «dos mil quinientos» -> numero."""
    tot, cur, vio = 0, 0, False
    for w in ws:
        if w == "y":
            continue
        if w == "mil":
            cur = (cur or 1) * 1000
            tot += cur
            cur, vio = 0, True
        elif w in ("millon", "millones"):
            cur = (cur or 1) * 1_000_000
            tot += cur
            cur, vio = 0, True
        elif w in _UNI:
            cur += _UNI[w]
            vio = True
        else:
            return None
    return float(tot + cur) if vio else None


def valor_span(f: Frase, a: int, b: int) -> Optional[float]:
    """Valor de los tokens a..b (cifras con separador de miles, palabras)."""
    ws = [t.nf for t in f.tok[a:b + 1] if t.u != "PUNCT"]
    if not ws:
        return None
    for k_, w_ in enumerate(ws):                                                      # rango: se toma el primer extremo
        if k_ > 0 and w_ in ("a", "o", "-", "–", "—") and k_ + 1 < len(ws) and (_NUM_RX.match(ws[k_ - 1]) or ws[k_ - 1] in _UNI):
            ws = ws[:k_]
            break
    if all(_NUM_RX.match(w) or re.fullmatch(r"\d{3}", w) for w in ws):
        base = ws[0]
        for w in ws[1:]:
            base += w if re.fullmatch(r"\d{3}", w) else " " + w
        return _a_float(base)
    pal = [w for w in ws if w not in ("unos", "unas", "casi", "cerca", "de", "mas", "menos", "aproximadamente", "alrededor")]
    return valor_palabras(pal)


def fmt_num(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        v = int(round(v))
        return f"{v:,}".replace(",", " ") if v >= 10000 else str(v)
    return str(v).replace(".", ",")


# ====================================================== cantidades con duenyo =======================================================
class Cant:
    __slots__ = ("f", "a", "b", "h", "val", "unit", "owner", "owner_txt", "verbo", "neg", "span")

    def __init__(self, f, a, b, h, val, unit, owner, owner_txt, verbo, neg, span):
        self.f, self.a, self.b, self.h, self.val, self.unit, self.owner, self.owner_txt, self.verbo, self.neg, self.span = f, a, b, h, val, unit, owner, owner_txt, verbo, neg, span


_RELLENO = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "con", "por", "en", "a", "y", "o", "que", "se", "su", "sus", "al"}


def _palabras_np(f: Frase, a: int, b: int) -> Set[str]:
    return {t.nl for t in f.tok[a:b + 1] if t.u in ("NOUN", "PROPN", "ADJ") and t.nl not in _RELLENO and len(t.nl) > 2}


def _sujeto_de(f: Frase, v: int) -> Optional[int]:
    for c in f.hij.get(v, ()):
        if f.tok[c].d.startswith("nsubj"):
            return c
    return None


def _verbo_sobre(f: Frase, i: int) -> Optional[int]:
    x, pasos = f.tok[i].h, 0
    while x >= 0 and pasos < 12:
        if f.tok[x].u in ("VERB", "AUX"):
            return x
        if f.tok[x].u == "NOUN" and any(f.tok[c].d == "cop" for c in f.hij.get(x, ())):          # «es la ciudad mas poblada»: la raiz nominal con copula
            return x
        x, pasos = f.tok[x].h, pasos + 1
    return None


def _grupo_numerico(f: Frase, t) -> Tuple[int, int]:
    """Cifra o numeral con sus partes («670 000», «treinta y cinco») y rangos («90 a 105», «cinco o seis», «180-190»)."""
    tk, n = f.tok, len(f.tok)
    a = b = t.i
    while a > 0 and L._es_num(tk[a - 1]):
        a -= 1
    while b + 1 < n and (L._es_num(tk[b + 1]) or (tk[b + 1].nf == "y" and b + 2 < n and L._es_num(tk[b + 2]))):
        b += 1
    while b + 2 < n and (tk[b + 1].f in ("-", "–", "—") or tk[b + 1].nf in ("a", "o")) and L._es_num(tk[b + 2]):          # rango
        b += 2
        while b + 1 < n and L._es_num(tk[b + 1]):
            b += 1
    if a > 1 and (tk[a - 1].nf == "de") and tk[a - 2].nf in ("entre",):
        a -= 2
    return a, b


def cants(f: Frase) -> List[Cant]:
    """Todas las cantidades de la frase con su unidad, su duenyo, el verbo de su oracion y si estan negadas (incluye elipsis y «ninguno»)."""
    ck = getattr(f, "_cants", None)
    if ck is not None:
        return ck
    tk, n = f.tok, len(f.tok)
    out: List[Cant] = []
    # segmentos por «;» : el segundo sin verbo hereda sujeto y unidad del primero («la britanica, por 27; la combinada, por 33»)
    cortes = [i for i, t in enumerate(tk) if t.f == ";"]
    segs, a0 = [], 0
    for c in cortes + [n]:
        segs.append((a0, c - 1))
        a0 = c + 1
    sujeto_ant: Optional[Tuple[Set[str], str, str]] = None
    unidad_ant: Optional[str] = None
    for si, (sa, sb) in enumerate(segs):
        if sa > sb:
            continue
        verbos = [i for i in range(sa, sb + 1) if tk[i].u in ("VERB", "AUX")]
        copnom = [i for i in range(sa, sb + 1) if tk[i].u == "NOUN" and any(tk[c].d == "cop" for c in f.hij.get(i, ()))]
        sin_verbo = not verbos and not copnom
        raiz_seg = next((i for i in range(sa, sb + 1) if tk[i].h < sa or tk[i].h > sb), None)
        # duenyo del segmento
        owner, owner_txt, cab_txt = set(), "", ""
        vlem = ""
        if not sin_verbo:
            cab = None
            for v in verbos + copnom:
                s = _sujeto_de(f, v)
                if s is not None:
                    cab = s
                    vlem = tk[v].nl
                    break
            if cab is None and verbos:
                vlem = tk[verbos[0]].nl
            cab_txt = ""
            if cab is not None and tk[cab].u in ("NOUN", "PROPN"):
                a, b = f.np(cab)
                owner, owner_txt, cab_txt = _palabras_np(f, a, b), f.texto_span(a, b), tk[cab].nl
            else:
                impl = sorted(f.impl)[:1]
                if impl:
                    pal_ = [w for w in re.split(r"[^a-z0-9]+", nrm(impl[0])) if w]
                    owner, owner_txt, cab_txt = set(pal_), " ".join(pal_).title(), ""
                elif sujeto_ant is not None and sa > 0 and tk[sa - 1].f != ";":
                    owner, owner_txt, cab_txt = sujeto_ant
        else:
            # «la combinada, por 33»: determinante + adjetivo/nombre, la cabeza nominal se toma del sujeto anterior
            propios = [i for i in range(sa, sb + 1) if tk[i].u in ("ADJ", "NOUN", "PROPN") and not tk[i].f.isdigit() and tk[i].nl not in _RELLENO]
            antes_num = [i for i in propios if i < next((j for j in range(sa, sb + 1) if L._es_num(tk[j])), sb + 1)]
            ws = {tk[i].nl for i in antes_num}
            if sujeto_ant is not None:
                owner = ({sujeto_ant[2]} if sujeto_ant[2] else set(sujeto_ant[0])) | ws
                det_ = next((tk[i].f for i in range(sa, sb + 1) if tk[i].u == "DET"), "")
                owner_txt = " ".join(x for x in (det_, sujeto_ant[2], " ".join(tk[i].f for i in antes_num)) if x)
            else:
                owner, owner_txt = ws, " ".join(tk[i].f for i in antes_num)
            vlem = out[-1].verbo if out else ""
        # cantidades del segmento
        vistos = set()
        for t in tk[sa:sb + 1]:
            if not L._es_num(t) and t.nf not in ("ninguno", "ninguna", "ningun"):
                continue
            if t.nf in L.MESES or t.i in vistos:
                continue
            a, b = _grupo_numerico(f, t)
            if t.nf in ("ninguno", "ninguna", "ningun"):
                a = b = t.i
            for x in range(a, b + 1):
                vistos.add(x)
            # unidad: el nombre al que cuantifica
            h = None
            for x in range(a, b + 1):
                if tk[x].d in ("nummod", "det", "amod") and tk[x].h >= 0 and tk[tk[x].h].u in ("NOUN", "PROPN") and tk[x].h > b - 1:
                    h = tk[x].h
                    break
            if h is None and b + 1 <= sb and tk[b + 1].u in ("NOUN", "X", "SYM") and tk[b + 1].nf not in L.MESES:
                h = b + 1
            if h is None and b + 2 <= sb and tk[b + 1].nf in ("de",) and tk[b + 2].u == "NOUN":
                h = b + 2
            neg = False
            if tk[t.i].nf in ("ninguno", "ninguna", "ningun"):
                neg = True
                h = h if h is not None else None
            if h is None:
                if t.nf in ("ninguno", "ninguna") and unidad_ant:
                    unit = unidad_ant
                    h = -1
                elif sin_verbo and unidad_ant:                                  # «la combinada, por 33»
                    unit, h = unidad_ant, -1
                else:
                    continue
            else:
                unit = tk[h].nl
            val = valor_span(f, a, b) if t.nf not in ("ninguno", "ninguna", "ningun") else 0.0
            if val is None:
                continue
            vl, ow, owt = vlem, owner, owner_txt
            if not sin_verbo:                                                       # el verbo y el sujeto de ESTA cantidad (una frase puede llevar varios: «destruyo 22... y no perdio ninguno»)
                vq = _verbo_sobre(f, t.i)
                if vq is not None:
                    vl = tk[vq].nl
                    x, pasos, sj = vq, 0, None
                    while x is not None and pasos < 4:
                        sj = _sujeto_de(f, x)
                        if sj is not None:
                            break
                        x = tk[x].h if (tk[x].d == "conj" and tk[x].h >= 0) else None
                        pasos += 1
                    if sj is not None and tk[sj].u in ("NOUN", "PROPN"):
                        a_, b_ = f.np(sj)
                        ow, owt = _palabras_np(f, a_, b_), f.texto_span(a_, b_)
            bb = b
            if h >= 0 and h > bb:
                bb = h
            if bb + 2 < n and tk[bb + 1].nf == "y" and tk[bb + 2].nf in ("media", "medio", "cuarto"):
                bb += 2
                val = (val or 0) + (0.5 if tk[bb].nf in ("media", "medio") else 0.25)
            span = f.texto_span(a, bb)
            if tk[a].nf in ("unos", "unas", "casi", "cerca") or (a > 0 and tk[a - 1].nf in ("unos", "unas")):
                pass
            if not neg:
                neg = any(tk[x].nf in L.NEG and tk[x].u in ("ADV", "PART", "SCONJ", "DET", "PRON") for x in range(max(sa, (h if h > 0 else t.i) - 4), t.i))
            out.append(Cant(f, a, bb, h, val, unit, ow, owt, vl, neg, span))
            unidad_ant = unit
        if not sin_verbo or sujeto_ant is None:
            if owner:
                sujeto_ant = (owner, owner_txt, cab_txt if not sin_verbo else "")
    f._cants = out
    return out


def _clave_noun(k) -> bool:
    return True


def _coincide_unidad(c: Cant, q: Q) -> bool:
    if not q.foco:
        return False
    if c.unit == q.foco.nl or L.raiz(c.unit) == q.foco.rz:
        return True
    un = L.UNIDADES.get(q.foco.nl)
    return un is not None and c.unit in un


def _puntos_duenyo(c: Cant, q: Q, ind: Indice) -> float:
    """Cuanto se parece el duenyo de la cantidad a lo que la pregunta nombra (sin contar la unidad ni el verbo)."""
    pal = {k.nl for k in q.claves if k.kind in ("cont", "foco") and k is not q.foco and k.nl not in L.GENERICOS}
    pal |= {k.rz for k in q.claves if k.kind in ("cont", "foco") and k is not q.foco}
    mi = c.owner | {L.raiz(w) for w in c.owner}
    s = sum(1.0 for w in pal if w in mi)
    for e in q.ents:
        if any(nrm(w) in nrm(c.owner_txt) for w in ind.disp[e].split() if len(w) > 2):
            s += 1.0
    return s


def _puntos_verbo(c: Cant, q: Q) -> float:
    if not q.verbo or q.verbo.nl in L.GENERICOS:
        return 0.0
    if c.verbo == q.verbo.nl:
        return 2.0
    if c.verbo and (L.raiz(c.verbo) == q.verbo.rz or c.verbo in q.verbo.alts):
        return 1.5
    return 0.0


def ext_cuanto_rico(ind: Indice, f: Frase, q: Q, anc: List[int]):
    """-> (texto, tramo, calidad) o None: elige la cantidad cuyo duenyo y verbo casan con la pregunta."""
    if not q.foco and not (q.verbo and q.verbo.nl in L.VERBO_UNIDAD):
        return None
    cs = [c for c in cants(f)]
    if q.foco:
        cs = [c for c in cs if _coincide_unidad(c, q)]
    else:
        un = L.UNIDADES[L.VERBO_UNIDAD[q.verbo.nl]]
        cs = [c for c in cs if c.unit in un]
    if not cs:
        return None
    if len(cs) == 1 and not cs[0].neg and cs[0].owner_txt == "" and not (len(f.tok) > 0 and ";" in [t.f for t in f.tok]):
        return None                                                              # nada que desambiguar: que decida el extractor corriente
    pun = []
    for c in cs:
        s = 1.5 * _puntos_duenyo(c, q, ind) + 1.2 * _puntos_verbo(c, q) - 0.04 * L._dist(c.h if c.h >= 0 else c.b, anc)
        pun.append((s, c))
    pun.sort(key=lambda x: -x[0])
    s0, c0 = pun[0]
    if len(pun) > 1 and abs(pun[0][0] - pun[1][0]) < 0.3:
        return None                                                              # no hay motivo para preferir una: que decida el extractor corriente
    if c0.neg and c0.val == 0:
        return "Ninguno", c0.span, 1.0
    return c0.span, c0.span, 1.0


# ====================================================== comparar, sumar, restar =====================================================
def _qn(q: Q) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[¿?¡!.,;:]", " ", nrm(q.raw))).strip()


def _cands_unidad(ind: Indice, unit: str, sust: Optional[str]) -> List[Cant]:
    out = []
    for f in ind.fr:
        for c in cants(f):
            if (c.unit == unit or L.raiz(c.unit) == L.raiz(unit)) and (sust is None or sust in c.owner or L.raiz(sust) in {L.raiz(w) for w in c.owner}):
                out.append(c)
    return out


def _frase_con_pares(ind: Indice, q: Q, unit: str, minimo: int = 2):
    for g, c, f in L.ranking(ind, q, 10):
        if c < 0.3:
            continue
        cs = [x for x in cants(f) if x.unit == unit or L.raiz(x.unit) == L.raiz(unit)]
        if len({(frozenset(x.owner), x.val) for x in cs}) >= minimo:
            return f, cs
    return None, []


def _dup(cs: List[Cant]) -> List[Cant]:
    vistos, out = set(), []
    for c in cs:
        k = (frozenset(c.owner), c.val)
        if k not in vistos:
            vistos.add(k)
            out.append(c)
    return out


def _txt_c(c: Cant) -> str:
    return L.cap(c.owner_txt) if c.owner_txt else "El primero"


def _cita(f: Frase) -> str:
    return " En el texto: «" + L.cita(f) + "»"


def comparar(ind: Indice, q: Q):
    """«¿Que flota tenia mas navios?» -> la de mayor cantidad entre los duenyos de esa unidad."""
    toks = q.toks
    if not toks or toks[0][0] not in ("que", "cual", "cuales", "quien", "quienes"):
        return None
    idx = next((i for i, t in enumerate(toks) if t[0] in ("mas", "menos")), None)
    if idx is None:
        return None
    sust = toks[1][2] if len(toks) > 1 and toks[1][1] == "NOUN" else None
    unit = next((toks[j][2] for j in range(idx + 1, min(idx + 3, len(toks))) if toks[j][1] == "NOUN"), None)
    if not unit:
        return None
    cs = _dup(_cands_unidad(ind, unit, sust))
    if len(cs) < 2:
        return None
    cs.sort(key=lambda c: -c.val)
    gana, otro = (cs[0], cs[-1]) if toks[idx][0] == "mas" else (cs[-1], cs[0])
    if gana.val == otro.val:
        return None
    c1 = gana.span if not re.fullmatch(r"[\d ,.]+", gana.span) else f"{fmt_num(gana.val)} {_unid_txt(gana)}"
    return f"{_txt_c(gana)}, con {c1} (frente a {fmt_num(otro.val)} de {_txt_c(otro).lower()})." + _cita(gana.f), gana.f


def _unid_txt(c: Cant) -> str:
    return c.unit + "s" if not c.unit.endswith("s") else c.unit


def diferencia(ind: Indice, q: Q):
    """«¿Cuantos navios mas tenia la flota combinada?» -> resta de las dos cantidades de la misma frase."""
    toks = q.toks
    if not toks or toks[0][0] not in ("cuantos", "cuantas", "cuanto", "cuanta"):
        return None
    if not any(t[0] in ("mas", "menos") for t in toks):
        return None
    cmp = next(t[0] for t in toks if t[0] in ("mas", "menos"))
    unit = toks[1][2] if len(toks) > 1 and toks[1][1] == "NOUN" else None
    if not unit:
        return None
    f, cs = _frase_con_pares(ind, q, unit)
    if f is None:
        return None
    cs = _dup(cs)
    pt = [(_puntos_duenyo(c, q, ind), c) for c in cs]
    pt.sort(key=lambda x: -x[0])
    if len(pt) < 2 or pt[0][0] <= pt[1][0]:
        return None
    a, b = pt[0][1], pt[1][1]
    d = a.val - b.val
    if d == 0:
        return f"Los dos tenían lo mismo ({fmt_num(a.val)})." + _cita(f), f
    if (d > 0) == (cmp == "mas"):
        return f"{fmt_num(abs(d))} {_unid_txt(a)} {cmp} ({fmt_num(a.val)} frente a {fmt_num(b.val)})." + _cita(f), f
    return f"En realidad tenía {fmt_num(abs(d))} {cmp_inv(cmp)} ({fmt_num(a.val)} frente a {fmt_num(b.val)})." + _cita(f), f


def cmp_inv(c: str) -> str:
    return "menos" if c == "mas" else "más"


def total(ind: Indice, q: Q):
    """«¿Cuantos navios tenian en total las dos flotas?» -> suma."""
    qn = _qn(q)
    if not re.search(r"\b(?:en total|entre (?:ambos|ambas|los dos|las dos)|juntos|juntas|sumando|sumados|sumadas|todos juntos)\b", qn):
        return None
    toks = q.toks
    if not toks or toks[0][0] not in ("cuantos", "cuantas", "cuanto", "cuanta"):
        return None
    unit = toks[1][2] if len(toks) > 1 and toks[1][1] == "NOUN" else None
    if not unit:
        return None
    f, cs = _frase_con_pares(ind, q, unit)
    if f is None:
        return None
    cs = _dup(cs)
    s = sum(c.val for c in cs)
    return f"{fmt_num(s)} {_unid_txt(cs[0])} en total ({' + '.join(fmt_num(c.val) for c in cs)})." + _cita(f), f


# ====================================================== fechas y edades ============================================================
_MES = {m: i + 1 for i, m in enumerate(["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"])}
_MES["setiembre"] = 9


def parse_fecha(s: str) -> Optional[Tuple[int, Optional[int], Optional[int]]]:
    n = nrm(s)
    m = re.search(r"(\d{1,2}) de ([a-z]+) de (\d{3,4})", n)
    if m and m.group(2) in _MES:
        return int(m.group(3)), _MES[m.group(2)], int(m.group(1))
    m = re.search(r"([a-z]+) de (\d{3,4})", n)
    if m and m.group(1) in _MES:
        return int(m.group(2)), _MES[m.group(1)], None
    m = re.search(r"\b(\d{1,2}) de ([a-z]+)\b", n)
    if m and m.group(2) in _MES:
        return 0, _MES[m.group(2)], int(m.group(1))
    m = re.search(r"\b(\d{3,4})\b", n)
    if m:
        return int(m.group(1)), None, None
    return None


class Hecho:
    __slots__ = ("y", "m", "d", "resp", "cita", "pregunta")

    def __init__(self, y, m, d, resp, cita, pregunta):
        self.y, self.m, self.d, self.resp, self.cita, self.pregunta = y, m, d, resp, cita, pregunta


_EXIGE = {"nació": r"naci|nace", "se fundó": r"fund", "se creó": r"cre[oóa]|creaci", "se fundaron": r"fund", "comenzó": r"comenz|inici|empez", "se inauguró": r"inaugur", "se construyó": r"constru",
          "se publicó": r"public", "murió": r"muri|falle|muert", "falleció": r"muri|falle|muert", "desapareció": r"desapare", "terminó": r"termin|final|acab",
          "se casó": r"cas[oó]|casa|boda|matrimon", "se divorció": r"divorc", "enviudó": r"viud", "se separó": r"separ"}


def _sub(ind: Indice, raw: str, ents: List[str], ctx: bool = True, exige: Optional[str] = None) -> Optional[Hecho]:
    """Contesta una pregunta auxiliar («¿Cuando nacio X?») con el mismo lector y devuelve su fecha."""
    parser = getattr(ind, "_parser", None)
    q2 = L.analizar(ind, raw, parser)
    if q2 is None:
        return None
    q2._sub = True
    if ents and not q2.ents:
        q2.ents, q2.ents_ctx = list(ents), ctx
    r = L.contestar(ind, q2, True)
    if not r:
        return None
    txt = r[0]
    cab = txt.split(". En el texto:")[0]
    if cab.startswith(("Lo más cercano", "Según el texto", "No ", "(Entiendo")):                   # «(Entiendo «fundo» como «Mundo».)»: la pregunta se leyo mal, la fecha no es de lo que se pregunta
        return None
    fe = parse_fecha(cab)
    if not fe or fe[0] == 0:
        return None
    m = re.search(r"«(.*)»", txt, re.S)
    cita_ = m.group(1) if m else ""
    palabras = [w for w in re.findall(r"[a-z]{4,}", nrm(raw)) if w not in ("cuando", "quien", "como", "donde", "para", "este", "esta", "esos", "esas")]
    ncita = nrm(cita_)
    if exige is None:
        mv = re.match(r"¿Cuándo ((?:se )?\w+)", raw)
        exige = _EXIGE.get(mv.group(1)) if mv else None
    if exige and not re.search(exige, ncita):
        return None                                                                      # la frase no habla de ese suceso («nacio», «se fundo»…)
    if palabras and not any(re.search(r"\b" + w[:4], ncita) for w in palabras):
        return None                                                                      # la fecha no es de lo que se pregunta: la frase no comparte ni una palabra con el suceso
    if ents and not ctx and len(ents) == 1 and cita_:
        c0_ = cita_.split("» / «")[0][:60]
        f_ = next((x for x in ind.fr if x.texto.strip().startswith(c0_)), None)
        if f_ is not None:
            suj_ = [t for t in f_.tok if t.u in ("VERB", "AUX") and any(f_.tok[c].d.startswith("nsubj") for c in f_.hij.get(t.i, []))]
            if suj_ and all(L._sujeto_ajeno(ind, f_, t, set(ents)) for t in suj_):
                return None                                                              # la frase habla de otra persona nombrada («nacio» con sujeto «Lamine Yamal» no es de «Pedro Sanchez»)
            if L.nivel_ent(f_, ents[0]) < 0.6:
                return None                                                              # la frase ni siquiera trata de quien se pregunta («se hizo publico su romance» no es la fecha de «Pedro Sanchez»)
    return Hecho(fe[0], fe[1], fe[2], cab, cita_, raw)


def _anyos_entre(h1: Hecho, h2: Hecho) -> Tuple[int, bool]:
    """(anyos completos, exacto): exacto cuando ambas fechas llevan mes y dia."""
    if h1.m and h1.d and h2.m and h2.d:
        a = h2.y - h1.y - (1 if (h2.m, h2.d) < (h1.m, h1.d) else 0)
        return a, True
    return h2.y - h1.y, False


def _fmt_anyos(n: int, exacto: bool) -> str:
    return f"{n} años" if exacto else f"{'unos ' if n > 1 else ''}{n} año{'s' if n != 1 else ''}"


NOMINAL = {"fundacion": "se fundo", "nacimiento": "nacio", "muerte": "murio", "fallecimiento": "murio", "llegada": "llego", "boda": "se caso", "matrimonio": "se caso", "divorcio": "se divorcio",
           "inauguracion": "se inauguro", "descubrimiento": "se descubrio", "publicacion": "se publico", "creacion": "se creo", "construccion": "se construyo", "independencia": "se independizo",
           "coronacion": "fue coronado", "apertura": "se abrio", "desaparicion": "desaparecio", "victoria": "gano", "derrota": "perdio", "salida": "salio", "partida": "partio",
           "regreso": "regreso", "ingreso": "ingreso", "eleccion": "fue elegido", "nombramiento": "fue nombrado", "estreno": "se estreno", "firma": "se firmo"}


def _nombre_ents(ind: Indice, q: Q) -> List[str]:
    return list(q.ents)


def _inicio_de(ind: Indice, fid: str) -> Optional[Hecho]:
    """Cuando empezo a existir lo que se pregunta: nacer (persona/animal) o fundar/crear (institucion)."""
    d = ind.disp[fid]
    for v in ("nació", "se fundó", "se creó", "se fundaron", "comenzó", "se inauguró", "se construyó", "se publicó"):
        h = _sub(ind, f"¿Cuándo {v} {d}?", [fid], False)
        if h:
            return h
    return None


def nacimiento_de(ind: Indice, fid: str) -> Optional[Hecho]:
    """Cuando nacio una persona (o se fundo / creo una institucion): sin «comenzo», «se inauguro»…, que no son un origen."""
    d = ind.disp[fid]
    for v in ("nació", "se fundó", "se creó", "se fundaron"):
        h = _sub(ind, f"¿Cuándo {v} {d}?", [fid], False)
        if h:
            return h
    return None


def _fin_de(ind: Indice, fid: str) -> Optional[Hecho]:
    d = ind.disp[fid]
    for v in ("murió", "falleció", "desapareció", "terminó"):
        h = _sub(ind, f"¿Cuándo {v} {d}?", [fid], False)
        if h:
            return h
    return None


def _fam_nombre_comun(ind: Indice, noun: str) -> Optional[str]:
    """«la universidad» -> la entidad que el texto llama «Universidad de X»."""
    from collections import Counter
    cnt = Counter()
    for f in ind.fr:
        for a, b, k, _, _ in f.ment:
            p = a - 1
            if p >= 1 and f.tok[p].nf in ("de", "del"):
                p -= 1
            if p >= 0 and f.tok[p].nl == noun:
                cnt[ind.familia_de(k)] += 1
    return cnt.most_common(1)[0][0] if cnt else None


def _sujeto_edad(ind: Indice, q: Q, qn: str) -> Optional[str]:
    if q.ents_ctx and q.ents:
        return q.ents[0]                                                                  # quien llama ya esta probando de quien se habla
    pre = re.split(r"\bcuando\b|\ben (?:el ano )?\d{3,4}\b", qn)[0]
    for e in q.ents:
        if any(len(w) > 3 and nrm(w) in pre for w in ind.disp[e].split()):
            return e
    for t in q.toks:
        if t[1] == "NOUN" and nrm(t[0]) in pre.split():
            fid = _fam_nombre_comun(ind, t[2])
            if fid:
                return fid
    conv = getattr(ind, "_conv", None)
    if conv is not None:
        pr = L._priors(ind, conv, True)
        if pr and pr[0]:
            return pr[0][0]
    return q.ents[0] if q.ents else L._protagonista_global(ind)


def edad(ind: Indice, q: Q):
    """«¿Cuantos anyos tenia X cuando V?», «¿...tenia la universidad en 2018?», «¿Cuantos anyos tiene X?»"""
    qn = _qn(q)
    m = re.match(r"^(?:y )?(?:a )?cuantos anos (?:tenia|tuvo|tiene|tenian|cumplia|cumple|llevaba)\b\s*(?P<resto>.*)$", qn) or re.match(r"^(?:y )?(?:con )?cuantos anos (?:murio|fallecio|se caso|se casaron)\b\s*(?P<resto>.*)$", qn) \
        or re.match(r"^(?:y )?a que edad (?P<resto>.+)$", qn) or re.match(r"^(?:y )?(?:que|cual es la) edad (?:tiene|tenia|tuvo|tendria)\b\s*(?P<resto>.*)$", qn)
    if not m:
        return None
    fid = _sujeto_edad(ind, q, qn)
    if not fid:
        return None
    resto = m.group("resto").strip()
    resto = re.sub(r"\b(?:hoy en dia|a dia de hoy|en la actualidad|actualmente|hoy|ahora mismo|ahora|ya)\b", " ", resto)         # «¿cuantos anos tiene hoy Yamal?»
    nombres_ = {nrm(w) for e_ in list(q.ents) + [fid] if e_ in ind.disp for w in ind.disp[e_].split() if len(w) > 2}
    ante_, cdo_, post_ = re.split(r"(\bcuando\b|\ben (?:el ano )?\d{3,4}\b)", resto, maxsplit=1) if re.search(r"\bcuando\b|\ben (?:el ano )?\d{3,4}\b", resto) else [resto, "", ""]
    ante_ = " ".join(w for w in ante_.split() if w not in nombres_)                                                      # el nombre de quien se pregunta (ya esta en `fid`) no es parte de lo que se pregunta
    ante_ = re.sub(r"^(?:(?:el|la|los|las|de|del|don|dona)\s+)+", "", ante_).strip()
    resto = re.sub(r"\s+", " ", (ante_ + " " + cdo_ + post_).strip()) if cdo_ else ante_
    nac = _inicio_de(ind, fid)
    if nac is None:
        if not resto and not q.ents_ctx and fid in ind.disp and not any(L.nivel_ent(f_, fid) >= 0.9 and re.search(r"\b(?:edad|anos|cumple)\b", nrm(f_.texto)) for f_ in ind.fr):
            return f"No he leído cuándo nació {ind.disp[fid]} ni qué edad tiene, así que no puedo decirlo.", None              # ninguna frase que lo nombre habla de su edad
        return None
    ev = None
    m_c = re.search(r"\bcuando (.+)$", resto)
    m_y = re.search(r"\ben (?:el ano )?(\d{3,4})\b", resto)
    if re.match(r"^(?:y )?a que edad (murio|fallecio)", qn) or re.match(r"^(?:y )?cuantos anos (murio|fallecio)", qn):
        ev = _fin_de(ind, fid)
    elif m_y:
        ev = Hecho(int(m_y.group(1)), None, None, m_y.group(1), "", "")
    elif m_c:
        clausula = m_c.group(1)
        ev = _sub(ind, "¿Cuándo " + clausula + "?", [fid], True)
    elif re.match(r"^(?:tenia|tuvo)?$", resto) or not resto:
        fin = _fin_de(ind, fid)
        if fin is not None:
            n, ex = _anyos_entre(nac, fin)
            return f"{_fmt_anyos(n, ex)} cuando murió (nació en {nac.resp.lower()} y murió en {fin.resp.lower()}).".replace("Nació en el", "Nació el") + _cita_h(nac, fin), None
        hoy = datetime.date.today()
        ev = Hecho(hoy.year, hoy.month, hoy.day, "hoy", "", "")
    elif resto in ("al morir", "cuando murio"):
        ev = _fin_de(ind, fid)
    if ev is None:
        return None
    n, ex = _anyos_entre(nac, ev)
    if n < 0:
        return None
    def _sin_en(x: str) -> str:
        x = re.sub(r"^(?:en|el año|en el año)\s+(?=\d)", "", x.strip(), flags=re.I)                    # «en 1547» -> «1547»
        return re.sub(r"^el (?=\d)", "", x)
    fin_ = _sin_en(ev.resp.lower())
    fin_ = "al " + fin_ if re.match(r"\d{1,2} de ", fin_) else "a " + fin_
    ini_ = _sin_en(nac.resp.lower())
    ini_ = ("del " + ini_ if re.match(r"\d{1,2} de ", ini_) else "de " + ini_)
    return f"{_fmt_anyos(n, ex)} ({ini_} {fin_})." + _cita_h(nac, ev), None


def _cita_h(*hs: Hecho) -> str:
    cs = []
    for h in hs:
        if h.cita and h.cita not in cs:
            cs.append(h.cita)
    return (" En el texto: " + " / ".join("«" + c + "»" for c in cs)) if cs else ""


_PRE_NOMINAL = re.compile(r"^(?:y )?cuantos (?P<u>anos|meses|dias|semanas|siglos) (?P<rel>despues|antes|pasaron|transcurrieron|pasaron|mediaron) (?:de|desde|entre)\s+(?P<nom>(?:su |la |el |sus )?[a-z]+)\s+(?:y\s+)?(?P<resto>.+)$")


def intervalo(ind: Indice, q: Q):
    """«¿Cuantos anyos despues de su fundacion recibio los primeros estatutos?» -> resta de dos fechas del texto."""
    qn = _qn(q)
    m = _PRE_NOMINAL.match(qn)
    if not m or not (q.ents or getattr(ind, "_conv", None)):
        return None
    nom = m.group("nom").split()[-1]
    v1 = NOMINAL.get(nom)
    if v1 is None:
        return None
    fid = _sujeto_edad(ind, q, qn)
    if not fid:
        return None
    d = ind.disp[fid]
    h1 = _sub(ind, f"¿Cuándo {v1} {d}?", [fid], False)
    resto = m.group("resto")
    h2 = _sub(ind, "¿Cuándo " + resto + "?", [fid], True)
    if h1 is None or h2 is None:
        return None
    n, ex = _anyos_entre(h1, h2) if m.group("rel") in ("despues", "pasaron", "transcurrieron", "mediaron") else _anyos_entre(h2, h1)
    if n < 0:
        n, ex = abs(n), ex
    unidad = m.group("u")
    if unidad != "anos":
        return None
    return f"{_fmt_anyos(n, ex)} ({h1.resp.lower()} → {h2.resp.lower()})." + _cita_h(h1, h2), None


def _anyo_de_hecho(ind: Indice, frase: str):
    """Año del hecho que nombra una frase libre («la declaracion como Patrimonio de la Humanidad»): se busca la frase que mas la cubre y se toma su unico año."""
    frase = re.sub(r"^(?:la|el|los|las|su|sus|que|cuando)\s+", "", frase.strip())
    frase = re.sub(r"^(?:ser|fue|fueron|era)\s+", "", frase)
    try:
        q2 = L.analizar(ind, "¿Cuándo " + frase + "?", getattr(ind, "_parser", None))
    except Exception:                                                                   # noqa
        return None
    if q2 is None:
        return None
    for g, c, f in L.ranking(ind, q2, 3):
        if c < 0.5:
            break
        ys = {int(t.f) for t in f.tok if t.f.isdigit() and 1000 <= int(t.f) <= 2100}
        if len(ys) == 1:
            y = ys.pop()
            return Hecho(y, None, None, str(y), "", ""), f
        break
    return None


def entre_hechos(ind: Indice, q: Q):
    """«¿Cuantos años pasaron entre su declaracion como Patrimonio y su eleccion como maravilla?» -> resta de los dos años."""
    qn = _qn(q)
    m = re.match(r"^(?:y )?cuantos (?P<u>anos|siglos) (?:pasaron|transcurrieron|mediaron|hay|separan) entre (?P<a>.+?) y (?P<b>.+)$", qn) \
        or re.match(r"^(?:y )?cuantos (?P<u>anos|siglos) (?:pasaron|transcurrieron) desde (?:que )?(?P<a>.+?) hasta (?:que )?(?P<b>.+)$", qn)
    if not m or m.group("u") != "anos":
        return None
    ra, rb = _anyo_de_hecho(ind, m.group("a")), _anyo_de_hecho(ind, m.group("b"))
    if not ra or not rb:
        return None
    (h1, f1), (h2, f2) = ra, rb
    n = abs(h2.y - h1.y)
    a, b = sorted((h1.y, h2.y))
    return f"{n} años (de {a} a {b}). En el texto: «{L.cita(f1)}»" + ("" if f1 is f2 else " / «" + L.cita(f2) + "»"), None


_MARCAS_IMPORTANCIA = [("gracias", "a"), ("es", "la", "base"), ("son", "la", "base"), ("es", "fundamental"), ("es", "esencial"), ("es", "imprescindible"), ("es", "clave"), ("permite",), ("permiten",),
                       ("es", "necesari"), ("sirve", "de", "base"), ("es", "vital")]


def importancia(ind: Indice, q: Q):
    """«¿Por que es importante la fotosintesis?» <- «Gracias a este proceso se genera casi todo el oxigeno…, y es la base de…»: la frase del tema que dice de que depende o para que sirve."""
    qn = _qn(q)
    if not re.match(r"^(?:y )?por que (?:es|son|fue|era) (?:tan )?(?:importante|fundamental|esencial|necesari|vital|relevante|clave)", qn) or len(q.ents) != 1 or q.ents_ctx:
        return None
    e = q.ents[0]
    for f in ind.fr:
        if e not in f.fams and e not in f.impl:
            continue
        for t in f.tok:
            for mk in _MARCAS_IMPORTANCIA:
                if t.i + len(mk) > len(f.tok) or not all(f.tok[t.i + k].nf.startswith(mk[k]) for k in range(len(mk))):
                    continue
                j = t.i + len(mk)
                if mk[0] == "gracias":
                    while j < len(f.tok) and f.tok[j].u in ("DET", "NOUN", "PROPN", "ADJ") and f.tok[j].f != ",":
                        j += 1
                else:
                    j = t.i
                if j >= len(f.tok) - 1:
                    continue
                sp = f.texto_span(j, len(f.tok) - 2 if f.tok[-1].f in (".", "…") else len(f.tok) - 1)
                if len(sp) > 12:
                    return f, sp[:1].upper() + sp[1:]
    return None


ESTADOS = {"casado": (["se casó con"], ["se divorció", "murió", "enviudó", "se separó"]), "casada": (["se casó con"], ["se divorció", "murió", "enviudó", "se separó"]),
           "vivio": (["nació"], ["murió", "falleció"]), "vivo": (["nació"], ["murió", "falleció"])}


def duracion(ind: Indice, q: Q):
    """«¿Cuantos anyos estuvo casado con X?», «¿cuantos anyos vivio?», «¿cuanto duro Y?» -> fin - inicio."""
    qn = _qn(q)
    m = re.match(r"^(?:y )?cuantos (?P<u>anos|meses|dias) (?:estuvo|estuvieron|permanecio|permanecieron|llevo|llevaron|vivio|duro|duraron)\s*(?P<resto>.*)$", qn)
    if not m:
        return None
    fid = _sujeto_edad(ind, q, qn)
    if not fid:
        return None
    d = ind.disp[fid]
    resto = m.group("resto")
    mm = re.match(r"^(casado|casada)(?: con (.+))?$", resto)
    h1 = h2 = None
    if mm:
        con = mm.group(2)
        cx = [e for e in q.ents[1:]]
        sujeto = d
        tail = ("con " + con) if con else ""
        h1 = _sub(ind, f"¿Cuándo se casó {tail}?".replace("  ", " "), [fid], True)
        for v in ESTADOS["casado"][1]:
            h2 = _sub(ind, f"¿Cuándo {v}?", [fid], True)
            if h2 is not None and (h1 is None or h2.y >= h1.y):
                break
    elif re.match(r"^vivio\b", qn.split(" ", 2)[2] if False else m.group(0)) or "vivio" in qn.split():
        h1, h2 = _inicio_de(ind, fid), _fin_de(ind, fid)
    else:
        h1 = _sub(ind, f"¿Cuándo comenzó {d}?", [fid], False)
        h2 = _sub(ind, f"¿Cuándo terminó {d}?", [fid], False)
    if h1 is None or h2 is None or m.group("u") != "anos":
        return None
    n, ex = _anyos_entre(h1, h2)
    if n < 0:
        return None
    return f"{_fmt_anyos(n, ex)} ({h1.resp.lower()} → {h2.resp.lower()})." + _cita_h(h1, h2), None


# ====================================================== gentilicios y antonimos ====================================================
_GENT_BASE = {
    "aleman": "Alemania", "frances": "Francia", "espanol": "España", "ingles": "Inglaterra", "britanico": "Reino Unido", "italiano": "Italia", "portugues": "Portugal", "estadounidense": "Estados Unidos",
    "norteamericano": "Estados Unidos", "americano": "Estados Unidos", "mexicano": "México", "argentino": "Argentina", "chileno": "Chile", "peruano": "Perú", "colombiano": "Colombia",
    "venezolano": "Venezuela", "cubano": "Cuba", "brasileno": "Brasil", "uruguayo": "Uruguay", "paraguayo": "Paraguay", "boliviano": "Bolivia", "ecuatoriano": "Ecuador", "ruso": "Rusia",
    "chino": "China", "japones": "Japón", "indio": "India", "serbio": "Serbia", "polaco": "Polonia", "suizo": "Suiza", "austriaco": "Austria", "belga": "Bélgica", "holandes": "Países Bajos",
    "neerlandes": "Países Bajos", "sueco": "Suecia", "noruego": "Noruega", "danes": "Dinamarca", "finlandes": "Finlandia", "griego": "Grecia", "turco": "Turquía", "egipcio": "Egipto",
    "marroqui": "Marruecos", "irlandes": "Irlanda", "escoces": "Escocia", "gales": "Gales", "hungaro": "Hungría", "checo": "Chequia", "rumano": "Rumanía", "bulgaro": "Bulgaria",
    "ucraniano": "Ucrania", "canadiense": "Canadá", "australiano": "Australia", "croata": "Croacia", "esloveno": "Eslovenia", "eslovaco": "Eslovaquia", "israeli": "Israel", "iraqui": "Irak",
    "irani": "Irán", "sudafricano": "Sudáfrica", "coreano": "Corea", "judio": "", "catalan": "Cataluña", "vasco": "País Vasco", "gallego": "Galicia", "andaluz": "Andalucía",
    "aragones": "Aragón", "navarro": "Navarra", "riojano": "La Rioja", "castellano": "Castilla", "leones": "León", "cantabro": "Cantabria", "asturiano": "Asturias", "murciano": "Murcia",
    "valenciano": "Valencia", "balear": "Islas Baleares", "canario": "Canarias", "extremeno": "Extremadura", "madrileno": "Madrid", "romano": "Roma", "ateniense": "Atenas",
    "salmantino": "Salamanca", "zaragozano": "Zaragoza", "sevillano": "Sevilla", "barcelones": "Barcelona", "bilbaino": "Bilbao", "toledano": "Toledo", "cordobes": "Córdoba",
    "granadino": "Granada", "malagueno": "Málaga", "vallisoletano": "Valladolid", "berlines": "Berlín", "parisino": "París", "londinense": "Londres", "neoyorquino": "Nueva York",
}
GENT: Dict[str, str] = {}
for _k, _v in _GENT_BASE.items():
    _vars = {_k, _k + "s", _k + "es"}
    if _k.endswith("o"):
        _vars |= {_k[:-1] + "a", _k[:-1] + "as", _k[:-1] + "os"}
    if _k.endswith(("es", "ol", "an")):
        _vars |= {_k + "a", _k + "as", _k.replace("es", "esa") if _k.endswith("es") else _k + "a"}
    if _k.endswith("es"):
        _vars |= {_k[:-2] + "esa", _k[:-2] + "esas", _k[:-2] + "eses"}
    if _k.endswith("z"):
        _vars |= {_k[:-1] + "ces"}
    for _x in _vars:
        GENT.setdefault(_x, _v)


def gentilicio(w: str) -> Optional[str]:
    """Pais o region que designa el adjetivo («serbia» -> Serbia), o None si no es un gentilicio conocido."""
    w = nrm(w)
    if w in GENT and GENT[w]:
        return GENT[w]
    return None


ANTONIMOS_BASE = [("publico", "privado"), ("grande", "pequeno"), ("antiguo", "moderno"), ("antiguo", "nuevo"), ("largo", "corto"), ("alto", "bajo"), ("rico", "pobre"), ("viejo", "joven"),
                  ("abierto", "cerrado"), ("lento", "rapido"), ("fuerte", "debil"), ("cristiano", "musulman"), ("norte", "sur"), ("este", "oeste"), ("mayor", "menor"), ("primero", "ultimo"),
                  ("ancho", "estrecho"), ("profundo", "superficial"), ("caliente", "frio"), ("seco", "humedo"), ("vivo", "muerto"), ("legal", "ilegal"), ("izquierdo", "derecho"),
                  ("civil", "militar"), ("nacional", "internacional"), ("natural", "artificial"), ("masculino", "femenino"), ("soltero", "casado"), ("alegre", "triste")]
_ANT: Dict[str, Set[str]] = {}
for _a, _b in ANTONIMOS_BASE:
    _ANT.setdefault(_a, set()).add(_b)
    _ANT.setdefault(_b, set()).add(_a)


EXCLUYENTES = [{"blanco", "negro", "rojo", "azul", "verde", "amarillo", "naranja", "morado", "violeta", "rosa", "gris", "marron", "dorado", "plateado"},
               {"norte", "sur", "este", "oeste"}, {"solido", "liquido", "gaseoso"}, {"izquierdo", "derecho"}]           # atributos que no pueden darse a la vez en lo mismo


def _lema_adj(w: str) -> str:
    n = nrm(w)
    if n.endswith(("a", "as", "os")) and not n.endswith("ia"):
        n = re.sub(r"(a|as|os)$", "o", n)
    elif n.endswith("es") and len(n) > 4:
        n = n[:-2] if n[:-2].endswith(("l", "r", "z", "n", "d", "s")) else n[:-1]
    return n


def son_antonimos(a: str, b: str) -> bool:
    a, b = _lema_adj(a), _lema_adj(b)
    if b in _ANT.get(a, ()):
        return True
    if a != b and any(a in g and b in g for g in EXCLUYENTES):
        return True
    try:
        from . import lexico
        return b in {nrm(x) for x in lexico.antonimos(a)} or _lema_adj(b) in {_lema_adj(x) for x in lexico.antonimos(a)}
    except Exception:                                                                   # noqa
        return False


# ====================================================== verificacion de si/no ======================================================
# Una pregunta de si/no es una afirmacion: «¿Es Logrono la capital de Aragon?». Se acepta si el texto la dice y se rechaza (con lo que el texto
# dice en su lugar) si el texto afirma algo incompatible: otro titular del mismo cargo, otro complemento de un verbo que solo admite uno,
# otro gentilicio u adjetivo opuesto, una negacion expresa («no por X, sino por Y», «no perdio ninguno»).
CARGOS = {"capital", "presidente", "presidenta", "rey", "reina", "emperador", "alcalde", "director", "directora", "entrenador", "capitan", "fundador", "fundadora", "autor", "autora",
          "padre", "madre", "esposa", "esposo", "marido", "mujer", "lider", "jefe", "comandante", "almirante", "general", "rector", "rectora", "ministro", "papa", "gobernador", "sucesor",
          "predecesor", "descubridor", "inventor", "arquitecto", "pintor", "escritor", "cantante", "protagonista", "propietario", "dueno", "senor", "duque", "conde", "virrey", "obispo",
          "arzobispo", "decano", "tesorero", "secretario", "canciller", "primer ministro", "monarca", "regente"}
VERBOS_UNICOS = {"nacer", "morir", "fallecer", "desembocar", "fundar", "descubrir", "inventar", "escribir", "pintar", "construir", "disenar", "componer", "crear", "dirigir", "casarse",
                 "divorciarse", "graduarse", "licenciarse", "doctorarse", "enviudar", "desembarcar", "ganar", "conceder", "otorgar", "elegir", "nombrar", "coronar", "publicar", "inaugurar",
                 "edificar", "erigir", "mandar", "comandar", "ordenar", "decretar", "firmar", "conquistar", "derrotar", "recibir", "obtener", "conseguir", "alcanzar", "terminar", "acabar"}
PREPS_EQ = {"en": {"en", "a"}, "a": {"a", "en"}, "por": {"por"}, "con": {"con"}, "desde": {"desde"}, "hasta": {"hasta"}, "contra": {"contra"}}
_DET_Q = {"algun", "alguna", "alguno", "algunos", "algunas", "ningun", "ninguna", "ninguno", "ningunos", "ningunas"}


def _fid(ind: Indice, clave) -> Optional[str]:
    try:
        return ind.familia_de(clave)
    except Exception:                                                                    # noqa
        return None


def _frase_pregunta(ind: Indice, q: Q) -> Optional[Frase]:
    parser = getattr(ind, "_parser", None)
    if parser is None:
        return None
    try:
        rows = parser.tree(q.raw)
    except Exception:                                                                    # noqa
        return None
    if not rows:
        return None
    prim = next((k for k, r in enumerate(rows) if str(r[1]) != "PUNCT"), 0)
    filas = []
    for k, r in enumerate(rows):
        u = str(r[1])
        w = str(r[0])
        if k > prim and u in ("VERB", "NOUN", "ADJ", "X", "ADV") and w[:1].isupper() and not w.isupper() and len(w) > 2:
            u = "PROPN"                                                                  # «Es Logrono la capital…»: el analizador lee el nombre como verbo
        filas.append((w, u, r[2], r[3], r[4]))
    blk = "\n".join("\t".join([str(x) for x in r]) for r in filas)
    try:
        f = Frase({"t": q.raw, "r": [blk]}, -1)
        f.menciones()
    except Exception:                                                                    # noqa
        return None
    return f


def _mencion_de(f: Frase, i: int):
    for m in f.ment:
        if m[0] <= i <= m[1]:
            return m
    return None


def _claves_ment(m) -> Set[str]:
    return set(m[2])


def _mismo_nombre(a, b, ind: Indice) -> bool:
    """Dos menciones nombran lo mismo: misma familia, o una contenida en la otra («Aragon» / «reino de Aragon»), sin numerales romanos distintos."""
    ka, kb = set(a), set(b)
    if ka == kb:
        return True
    fa, fb = _fid(ind, frozenset(ka)), _fid(ind, frozenset(kb))
    if fa and fb and fa == fb:
        return True
    return bool(ka and kb and (ka <= kb or kb <= ka))


def _titular(f: Frase, n: int):
    """Mencion que ostenta el cargo expresado por el sustantivo del token n: «Logrono, capital de La Rioja», «Zaragoza es la capital…», «la capital de Aragon es Zaragoza»."""
    t = f.tok[n]
    h = t.h
    if t.d == "appos" and h >= 0:
        m = _mencion_de(f, h)
        if m:
            return m
    for c in f.hij.get(n, []):
        if f.tok[c].d in ("nsubj", "appos") and _mencion_de(f, c):
            return _mencion_de(f, c)
    if h >= 0 and any(f.tok[c].d == "cop" for c in f.hij.get(h, [])) and _mencion_de(f, h):
        return _mencion_de(f, h)
    # lectura lineal: la mencion mas cercana a la izquierda sin cruzar un verbo, o (si el cargo abre la frase) la que sigue al «es»
    k = n - 1
    while k >= 0 and f.tok[k].u in ("DET", "ADJ", "AUX", "PUNCT", "ADV") or (k >= 0 and f.tok[k].nl in ("ser", "estar", "ciudad", "villa", "localidad", "poblacion")):
        k -= 1
    if k >= 0:
        m = _mencion_de(f, k)
        if m and n - m[1] <= 6:
            return m
    return None


def _cargo_pares(f: Frase, noun: str) -> List[Tuple[tuple, tuple]]:
    """[(titular, ambito)] para el cargo `noun` en la frase: «Logrono, capital de La Rioja» -> (Logrono, La Rioja)."""
    out = []
    for t in f.tok:
        if t.u not in ("NOUN", "PROPN") or t.nl != noun:
            continue
        j = t.i + 1
        if j < len(f.tok) and f.tok[j].nf in ("de", "del"):
            k = j + 1
            while k < len(f.tok) and (f.tok[k].u == "DET" or f.tok[k].nf in ("la", "el", "los", "las")):
                k += 1
            amb = _mencion_de(f, k) if k < len(f.tok) else None
            if amb is None and k + 1 < len(f.tok) and f.tok[k].u == "NOUN":                # «capital de la comunidad autonoma de Aragon»
                k2 = k + 1
                while k2 < len(f.tok) and f.tok[k2].nf in ("autonoma", "de", "del", "la", "el", "provincia", "region", "pais", "ciudad", "comunidad"):
                    k2 += 1
                amb = _mencion_de(f, k2) if k2 < len(f.tok) else None
            if amb is None:
                continue
            tit = _titular(f, t.i)
            if tit is None:
                # «La capital de Aragon es Zaragoza»: el titular sigue al ambito
                k = amb[1] + 1
                while k < len(f.tok) and (f.tok[k].u in ("AUX", "PUNCT", "DET") or f.tok[k].nl in ("ser", "estar")):
                    k += 1
                tit = _mencion_de(f, k) if k < len(f.tok) else None
            if tit is not None and tit is not amb and tit[2] != amb[2]:
                out.append((tit, amb))
    return out


def _verifica_cargo(ind: Indice, q: Q, fq: Frase):
    """«¿Es Logrono la capital de Aragon?»"""
    for t in fq.tok:
        if t.u != "NOUN" or t.nl not in CARGOS:
            continue
        j = t.i + 1
        if not (j < len(fq.tok) and fq.tok[j].nf in ("de", "del")):
            continue
        k = j + 1
        while k < len(fq.tok) and (fq.tok[k].u == "DET" or fq.tok[k].nf in ("la", "el", "los", "las")):
            k += 1
        amb = _mencion_de(fq, k) if k < len(fq.tok) else None
        if amb is None:
            continue
        sujetos = [m for m in fq.ment if m is not amb and not (m[0] > t.i and m[1] <= amb[1])]
        if len(sujetos) != 1:
            continue
        suj = sujetos[0]
        vistos_pos = vistos_neg = None
        for f in ind.fr:
            if not any(t2.nl == t.nl and t2.u in ("NOUN", "PROPN") for t2 in f.tok):
                continue
            for tit, amb2 in _cargo_pares(f, t.nl):
                mismo_tit, mismo_amb = _mismo_nombre(tit[2], suj[2], ind), _mismo_nombre(amb2[2], amb[2], ind)
                if mismo_tit and mismo_amb:
                    return "Sí", f
                if mismo_tit and not mismo_amb and vistos_neg is None:
                    vistos_neg = (f, "No. Según el texto, %s es %s %s %s." % (tit[3], _art(t), t.f.lower(), "de " + _con_art(f, amb2)), q)
                elif mismo_amb and not mismo_tit and vistos_neg is None:
                    vistos_neg = (f, "No. Según el texto, %s %s de %s es %s." % (_art(t), t.f.lower(), _con_art(f, amb2), tit[3]), q)
        if vistos_neg:
            return vistos_neg[1], vistos_neg[0]
    return None


def _art(t) -> str:
    return "la" if t.nl in ("capital", "madre", "esposa", "reina", "presidenta", "directora", "fundadora", "autora", "rectora") or t.nl.endswith("a") and t.nl not in ("papa", "lider") else "el"


def _con_art(f: Frase, m) -> str:
    a = m[0]
    if a > 0 and f.tok[a - 1].nf in ("la", "el", "los", "las") and (f.tok[a - 1].f[:1].islower() or a > 1):
        return f.tok[a - 1].f + " " + m[3]
    if a == 1 and f.tok[0].nf in ("la", "el", "los", "las"):
        return f.tok[0].f.lower() + " " + m[3]
    return m[3]


def _region_verbo(f: Frase, v: int) -> List[int]:
    return f.sub(v, lambda x: x.u in ("VERB", "AUX") and x.d not in ("aux", "cop", "aux:pass", "expl", "obl", "nmod"))


def _complementos(f: Frase, v: int) -> List[Tuple[str, Set[str], Set[str], tuple, str]]:
    """[(preposicion, nombres propios, anyos, mencion)] de los complementos preposicionales y de fecha del verbo v."""
    reg = set(_region_verbo(f, v))
    out = []
    for i in sorted(reg):
        t = f.tok[i]
        if t.u == "ADP" and t.nf in PREPS_EQ or t.nf in ("del", "al"):
            h = t.h
            if h < 0 or h not in reg:
                continue
            a, b = f.np(h)
            if a < i:                                                          # el sintagma de la preposicion empieza en la propia preposicion
                a = i + 1
            nombres, anyos = set(), set()
            ment = None
            for m in f.ment:
                if a <= m[0] <= b:
                    nombres |= set(m[2])
                    ment = ment or m
            for x in f.tok[a:b + 1]:
                if re.fullmatch(r"\d{3,4}", x.f):
                    anyos.add(x.f)
            if nombres or anyos:
                out.append((t.nf if t.nf not in ("del",) else "de", nombres, anyos, ment, f.texto_span(i, b)))
    anyos_v = {x.f for j in reg for x in [f.tok[j]] if re.fullmatch(r"\d{3,4}", x.f)}
    if anyos_v and not any(c[2] for c in out):
        out.append(("", set(), anyos_v, None, ""))
    return out


def _verifica_verbo(ind: Indice, q: Q, fq: Frase, rk):
    """«¿Nacio Einstein en Berna?» / «¿Desemboca el Ebro en el oceano Atlantico?» / «¿Fue fundada por Alfonso X?»"""
    if not q.verbo:
        return None
    lema = None
    for t in fq.tok:
        if t.u in ("VERB", "AUX", "ADJ") and (t.nl in VERBOS_UNICOS or t.nl.endswith(("ado", "ido")) and ind.formas.get(t.nf) in VERBOS_UNICOS):
            lema = ind.formas.get(t.nf, t.nl) if t.nl not in VERBOS_UNICOS else t.nl
            break
    if lema is None:
        k = q.verbo.nl
        if nrm(k) in VERBOS_UNICOS or k in VERBOS_UNICOS:
            lema = k
    if lema is None:
        return None
    # complementos de la pregunta: preposicion + nombres propios / anyos
    pregunta: List[Tuple[str, Set[str], Set[str]]] = []
    for t in fq.tok:
        if t.u == "ADP" and t.nf in PREPS_EQ:
            k = t.i + 1
            nombres, anyos = set(), set()
            while k < len(fq.tok) and fq.tok[k].u not in ("ADP", "VERB", "AUX", "PUNCT", "CCONJ", "SCONJ"):
                m = _mencion_de(fq, k)
                if m:
                    nombres |= set(m[2])
                    k = m[1] + 1
                    continue
                if re.fullmatch(r"\d{3,4}", fq.tok[k].f):
                    anyos.add(fq.tok[k].f)
                k += 1
            if nombres or anyos:
                pregunta.append((t.nf, nombres, anyos))
    anyos_sueltos = {t.f for t in fq.tok if re.fullmatch(r"\d{3,4}", t.f)}
    if anyos_sueltos and not any(p[2] for p in pregunta):
        pregunta.append(("", set(), anyos_sueltos))
    if not pregunta:
        return None
    comp_w = set()
    for _, nb_, _ in pregunta:
        comp_w |= {nrm(x) for x in nb_}
    sujetos = {e for e in q.ents if not (set(e.split("+")) <= comp_w)}
    for g, c, f in rk:
        if sujetos and any(nivel_ent_(f, e) < 0.6 for e in sujetos if e not in q.debiles):
            continue
        for t in f.tok:
            if t.u not in ("VERB", "AUX", "ADJ"):
                continue
            ok = (t.nl == lema or nrm(t.nl) == lema or (q.verbo and L._coincide(t, q.verbo) and L._grado(t, q.verbo) <= 2))
            if not ok:
                continue
            if t.u == "ADJ" and not re.search(r"(?:ad[oa]s?|id[oa]s?)$", t.nf):
                continue
            if sujetos and L._sujeto_ajeno(ind, f, t, set(sujetos)):
                continue
            comps = _complementos(f, t.i)
            if not comps or L._negada(f, [t.i]):
                continue
            palabras = {x.nf for x in f.tok}
            veredicto: List[Optional[str]] = []
            for prep, nombres, anyos in pregunta:
                cs = [c_ for c_ in comps if (prep == "" or c_[0] == "" or c_[0] in PREPS_EQ.get(prep, {prep}))]
                if not cs:
                    continue
                if anyos:
                    ay = set().union(*[c_[2] for c_ in comps])
                    if ay:
                        if anyos <= ay:
                            veredicto.append("Sí")
                        else:
                            return f, "No. Según el texto, fue en " + "/".join(sorted(ay)) + "."
                        continue
                if nombres:
                    alguno = [c_ for c_ in cs if c_[1]]
                    if not alguno:
                        continue
                    if nombres <= palabras:
                        veredicto.append("Sí")                                 # lo que pregunta esta en la frase (p. ej. «Ulm, Alemania»)
                        continue
                    c0 = alguno[0]
                    if any(c_[3] is not None and c_[0] in PREPS_EQ.get(prep, {prep}) and _sinromano(c_[3][2]) == _sinromano(frozenset(nombres)) and c_[3][2] != frozenset(nombres) for c_ in alguno):
                        c1 = next(c_ for c_ in alguno if c_[3] is not None and _sinromano(c_[3][2]) == _sinromano(frozenset(nombres)))
                        return f, "No. Según el texto, %s." % _verbo_resp(t, c1[4])             # «Alfonso X» frente a «Alfonso IX»
                    if c0[3] is None or any(set(c_[1]) & nombres for c_ in alguno):
                        continue
                    return f, "No. Según el texto, %s." % _verbo_resp(t, c0[4])
            if veredicto and all(v == "Sí" for v in veredicto) and len(veredicto) >= len([p_ for p_ in pregunta if p_[1] or p_[2]]):
                return f, "Sí"
    return None


LOC_VERBOS = {"ocurrir", "suceder", "situar", "localizar", "hallar"}
LOC_VERBOS_SE = {"producir"}                                                    # solo con «se»: «se produce en el estroma»


def _verifica_comp_comun(ind: Indice, q: Q, fq: Frase, rk):
    """«¿Ocurre la fase luminosa en el estroma?» <- «la fase luminosa, que ocurre en los tilacoides»;  «¿Fue construida por los españoles?» <- «construida … por orden del emperador Pachacutec»:
    el complemento de la pregunta es un nombre comun y el verbo es de los que solo admiten uno."""
    lema = None
    for t in fq.tok:
        if t.u in ("VERB", "AUX", "ADJ"):
            base = ind.formas.get(t.nf, t.nl) if t.nl not in VERBOS_UNICOS and t.nl not in LOC_VERBOS else t.nl
            if base in LOC_VERBOS_SE and t.i >= 1 and fq.tok[t.i - 1].nf == "se":
                lema, vq = base, t
                break
            if base in VERBOS_UNICOS or base in LOC_VERBOS or (q.verbo and q.verbo.nl in LOC_VERBOS | VERBOS_UNICOS and L._coincide(t, q.verbo)):
                lema = base if (base in VERBOS_UNICOS or base in LOC_VERBOS) else q.verbo.nl
                vq = t
                break
    if lema is None:
        return None
    for t in fq.tok:
        if t.u != "ADP" or t.nf not in ("en", "por"):
            continue
        k = t.i + 1
        while k < len(fq.tok) and fq.tok[k].u == "DET":
            k += 1
        if k >= len(fq.tok) or fq.tok[k].u != "NOUN" or _mencion_de(fq, k):
            continue
        prep, y = t.nf, fq.tok[k]
        sw = {x.nl for x in fq.tok[vq.i + 1:t.i] if x.u in ("NOUN", "ADJ") and x.nl not in LIGEROS_Q} if vq.i < t.i else {x.nl for x in fq.tok[:vq.i] if x.u in ("NOUN", "ADJ") and x.nl not in LIGEROS_Q}
        sujetos = [e for e in q.ents]
        if prep == "en" and not sw and not sujetos:
            continue
        for g, c, f in rk:
            if sujetos and any(nivel_ent_(f, e) < 0.6 for e in sujetos if e not in q.debiles):
                continue
            for v in f.tok:
                if v.u not in ("VERB", "AUX", "ADJ") or not (v.nl == lema or (q.verbo and L._coincide(v, q.verbo) and L._grado(v, q.verbo) <= 1)):
                    continue
                if v.u == "ADJ" and not re.search(r"(?:ad[oa]s?|id[oa]s?)$", v.nf):
                    continue
                if L._negada(f, [v.i]):
                    continue
                # el sujeto de la pregunta (palabras comunes) debe ser lo que cuelga de este verbo
                if prep == "en" and not sujetos:
                    cab = v.h if (v.d in ("acl", "acl:relcl") and v.h >= 0) else next((c_ for c_ in f.hij.get(v.i, []) if f.tok[c_].d.startswith("nsubj")), None)
                    if cab is None:
                        continue
                    pal = {f.tok[cab].nl} | {f.tok[c_].nl for c_ in f.hij.get(cab, []) if f.tok[c_].d in ("amod", "flat", "appos", "nmod")}
                    if not sw <= pal:
                        continue
                elif sujetos and L._sujeto_ajeno(ind, f, v, set(sujetos)):
                    continue
                for c_ in f.hij.get(v.i, []):
                    if not f.tok[c_].d.startswith("obl") or not any(f.tok[x].nf == prep and f.tok[x].d == "case" for x in f.hij.get(c_, [])):
                        continue
                    idx = sorted(f.sub(c_, lambda x: x.d in ("conj", "acl", "acl:relcl")))
                    pal_c = {f.tok[x].nl for x in idx} | {L.raiz(f.tok[x].nl) for x in idx}
                    if y.nl in pal_c or L.raiz(y.nl) in pal_c or (prep == "por" and gentilicio(y.f) and any(gentilicio(f.tok[x].f) == gentilicio(y.f) for x in idx if f.tok[x].u in ("ADJ", "NOUN"))):
                        return f, "Sí"
                    if prep == "por" and f.tok[c_].u == "NOUN" and not any(f.tok[x].u == "PROPN" for x in idx):
                        continue
                    sp = f.texto_span(idx[0], idx[-1])
                    sp = sp if sp.lower().startswith(prep + " ") else prep + " " + sp
                    pre_v = f.tok[v.i - 1].f.lower() + " " if v.i >= 1 and (f.tok[v.i - 1].nl == "ser" or f.tok[v.i - 1].nf == "se") else ""        # «fue construida», «se produce»
                    if prep == "por":                                           # el agente de la pregunta es un gentilicio y el texto da otro nombre: no se afirma que sea distinto, solo que no consta
                        ra = L.raiz(y.nl)
                        if any(L.raiz(a_.nl) == ra for g2, c2, f2 in rk[:6] if any(x_.d == "cop" for x_ in f2.tok) for a_ in f2.tok if a_.u in ("ADJ", "NOUN")):
                            continue
                        return f, "No consta en el texto que fuera %s %s. Según el texto, %s%s %s" % (vq.f.lower(), prep + " " + " ".join(x.f for x in fq.tok[t.i + 1:k + 1]), pre_v, v.f.lower(), sp)
                    return f, "No. Según el texto, %s%s %s." % (pre_v, v.f.lower(), sp)
    return None


def _sinromano(k) -> frozenset:
    return frozenset(w for w in k if not re.fullmatch(r"[ivxlcdm]+", w))


def nivel_ent_(f: Frase, e: str) -> float:
    return L.nivel_ent(f, e)


def _verbo_resp(t, comp: str) -> str:
    return "%s %s" % (t.f.lower(), comp)


def _descriptores(f: Frase, m) -> List[str]:
    """Adjetivos que el texto atribuye a una mencion: «Mileva Maric, fisica serbia», «es un escritor frances», «el rio Ebro es largo»."""
    out = []
    h = m[1]
    for k in range(m[1], m[0] - 1, -1):
        if f.tok[k].h < m[0] or f.tok[k].h > m[1]:
            h = k
            break
    cands = {h}
    th = f.tok[h]
    if th.d in ("appos", "flat", "flat:name", "nmod") and th.h >= 0:
        cands.add(th.h)
    for c in list(f.hij.get(h, [])):
        if f.tok[c].d == "appos":
            cands.add(c)
    if th.d == "nsubj" and th.h >= 0:
        cands.add(th.h)
        for c in f.hij.get(th.h, []):
            if f.tok[c].d in ("obj", "attr", "xcomp", "amod", "obl"):
                cands.add(c)
    for x in list(cands):
        if f.tok[x].u == "ADJ" and x not in range(m[0], m[1] + 1):
            out.append(f.tok[x].f)
        for c in f.hij.get(x, []):
            if f.tok[c].u == "ADJ" and f.tok[c].d in ("amod", "xcomp", "advcl") and c not in range(m[0], m[1] + 1):
                out.append(f.tok[c].f)
    # «Mileva Maric, fisica serbia»: sustantivo + adjetivo tras la coma
    k = m[1] + 1
    if k < len(f.tok) and f.tok[k].f == ",":
        k += 1
        while k < len(f.tok) and f.tok[k].u in ("DET",):
            k += 1
        if k < len(f.tok) and f.tok[k].u == "NOUN":
            k += 1
            while k < len(f.tok) and f.tok[k].u == "ADJ":
                out.append(f.tok[k].f)
                k += 1
    return out


def _verifica_adjetivo(ind: Indice, q: Q, fq: Frase, rk):
    """«¿Era Mileva alemana?» / «¿Es privada la Universidad de Salamanca?»"""
    adjs = [t for t in fq.tok if t.u == "ADJ" and t.d in ("root", "xcomp", "amod", "nsubj", "attr", "obj", "obl", "cop")]
    if not adjs or not q.ents:
        return None
    mq = [m for m in fq.ment]
    for a in adjs:
        for g, c, f in rk:
            if any(nivel_ent_(f, e) < 1.0 for e in q.ents if e not in q.debiles):
                continue
            for m in f.ment:
                fid = _fid(ind, m[2])
                if fid not in q.ents:
                    continue
                desc = _descriptores(f, m)
                gq = gentilicio(a.f)
                for d in desc:
                    if nrm(d) == a.nf or _lema_adj(d) == _lema_adj(a.f):
                        return f, "Sí"
                    gd = gentilicio(d)
                    if gq and gd and gq != gd:
                        return f, "No. Según el texto, %s es %s." % (m[3], d)
                    if not gq and son_antonimos(a.f, d):
                        return f, "No. Según el texto, %s es %s." % (m[3], d)
    return None


def _adj_tras_sustantivo(f: Frase, i: int) -> List[int]:
    """Indices de los adjetivos que modifican al sustantivo i (arbol o inmediatamente detras)."""
    out = [c for c in f.hij.get(i, []) if f.tok[c].u == "ADJ" and f.tok[c].d in ("amod", "xcomp")]
    k = i + 1
    while k < len(f.tok) and f.tok[k].u == "ADJ" and k not in out:
        out.append(k)
        k += 1
    return out


def _verifica_adjetivo_comun(ind: Indice, q: Q, fq: Frase, rk):
    """«¿Es la clorofila un pigmento rojo?» <- «clorofila, el pigmento verde que absorbe la luz»: el sujeto es un nombre comun y el atributo lleva un adjetivo."""
    if q.ents:
        return None
    n = len(fq.tok)
    for a in fq.tok:
        if a.u != "ADJ" or a.i < 2:
            continue
        # sustantivo que lleva el adjetivo (justo antes) y sujeto (primer sustantivo tras la copula)
        h = a.i - 1
        if fq.tok[h].u != "NOUN":
            continue
        sub = next((t for t in fq.tok[1:h] if t.u == "NOUN" and t.nl not in LIGEROS_Q and len(t.nl) > 3), None)
        c0 = next((t for t in fq.tok if t.u != "PUNCT"), None)
        if sub is None or c0 is None or c0.nl not in ("ser", "estar", "parecer"):
            continue
        for g, c, f in rk:
            for s_ in f.tok:
                if s_.u != "NOUN" or s_.nl != sub.nl:
                    continue
                cand = {s_.i} | {x for x in f.hij.get(s_.i, []) if f.tok[x].d == "appos"}
                if s_.d == "appos" and s_.h >= 0:
                    cand.add(s_.h)
                k_ = s_.i + 1                                                       # «clorofila, el pigmento verde…»: nombre en aposicion tras la coma
                if k_ < len(f.tok) and f.tok[k_].f == ",":
                    k_ += 1
                    while k_ < len(f.tok) and f.tok[k_].u == "DET":
                        k_ += 1
                    if k_ < len(f.tok) and f.tok[k_].u == "NOUN":
                        cand.add(k_)
                for x in cand:
                    if x != s_.i and f.tok[x].nl != fq.tok[h].nl:
                        continue
                    for j in _adj_tras_sustantivo(f, x):
                        d = f.tok[j].f
                        if _lema_adj(d) == _lema_adj(a.f):
                            return f, "Sí"
                        if son_antonimos(a.f, d):
                            return f, "No. Según el texto, %s es %s %s." % (_con_art_nl(fq, sub.i), ("un" if fq.tok[h].nf[-1:] != "a" else "una") + " " + f.tok[x].f, d)
    return None


def _con_art_nl(f: Frase, i: int) -> str:
    """El sintagma «la clorofila» tal como esta en la frase (articulo + nombre)."""
    if i >= 1 and f.tok[i - 1].u == "DET" and f.tok[i - 1].nf in ("el", "la", "los", "las"):
        return f.tok[i - 1].f.lower() + " " + f.tok[i].f
    return f.tok[i].f


def _verifica_obj_adj(ind: Indice, q: Q, fq: Frase, rk):
    """«¿Perdio Cervantes la mano derecha?» <- «perdio el uso de la mano izquierda»: mismo verbo y mismo sustantivo con un adjetivo que excluye al preguntado."""
    if not q.verbo or not q.ents:
        return None
    for a in fq.tok:
        if a.u != "ADJ" or a.i < 2:
            continue
        h = a.i - 1
        if fq.tok[h].u != "NOUN" or fq.tok[h].nl in LIGEROS_Q:
            continue
        for g, c, f in rk:
            if any(nivel_ent_(f, e) < 0.6 for e in q.ents if e not in q.debiles):
                continue
            vs = [v for v in f.tok if v.u in ("VERB", "AUX") and L._coincide(v, q.verbo) and L._grado(v, q.verbo) <= 1]
            for v in vs:
                for t in f.tok[v.i + 1:v.i + 9]:
                    if t.u == "NOUN" and t.nl == fq.tok[h].nl:
                        for j in _adj_tras_sustantivo(f, t.i):
                            d = f.tok[j].f
                            if _lema_adj(d) == _lema_adj(a.f):
                                return f, "Sí"
                            if son_antonimos(a.f, d):
                                return f, "No. Según el texto, %s." % f.texto_span(v.i, j)
                    if t.f in (".", ";"):
                        break
    return None


def _verifica_atributo_ausente(ind: Indice, q: Q, fq: Frase, rk):
    """«¿Fue Cervantes un pintor?» <- «Cervantes fue un novelista, poeta y dramaturgo»: el texto no dice «pintor»; se contesta con lo que si dice."""
    if len(q.ents) != 1 or q.ents_ctx:
        return None
    c0 = next((t for t in fq.tok if t.u != "PUNCT"), None)
    if c0 is None or c0.nl not in ("ser",):
        return None
    ns = [t for t in fq.tok if t.u == "NOUN" and t.i > c0.i and t.nl not in LIGEROS_Q and len(t.nl) > 3 and fq.tok[t.i - 1].nf in ("un", "una")]
    if len(ns) != 1:
        return None
    n = ns[0]
    if n.nl in ind.idf or n.nl in ind.vocab_all or L.raiz(n.nl) in ind.idf_r:
        return None
    e = q.ents[0]
    for f in ind.fr:
        if e not in f.fams:
            continue
        for t in f.tok:
            if t.u != "NOUN" or not any(f.tok[c].d == "cop" for c in f.hij.get(t.i, [])):
                continue
            sj = next((c for c in f.hij.get(t.i, []) if f.tok[c].d.startswith("nsubj")), None)
            m = _mencion_de(f, sj) if sj is not None else None
            if not m or _fid(ind, m[2]) != e:
                continue
            cop = next(f.tok[c] for c in f.hij.get(t.i, []) if f.tok[c].d == "cop")
            miembros = [t.f.lower()] + [f.tok[c].f.lower() for c in f.hij.get(t.i, []) if f.tok[c].d == "conj" and f.tok[c].u == "NOUN"]
            if len(miembros) >= 1 and nrm(miembros[0]) != n.nf:
                return f, "No consta en el texto. Lo que dice de %s es que %s %s" % (ind.disp[e], cop.f.lower(), _lista_y(miembros))
    return None


def _verifica_sino(ind: Indice, q: Q, fq: Frase, rk):
    """«¿Recibio Einstein el Nobel por la relatividad?»: «…no por la relatividad, sino por…»"""
    prop = set()
    for t in fq.tok:
        if t.u in ("NOUN", "PROPN", "ADJ") and t.nl not in LIGEROS_Q and len(t.nl) > 3:
            prop.add(t.nl)
    ent_w = set()
    for e in q.ents:
        ent_w |= set(e.split("+"))
    prop = {w for w in prop if nrm(w) not in ent_w}
    if not prop:
        return None
    for g, c, f in rk:
        if any(nivel_ent_(f, e) < 0.6 for e in q.ents if e not in q.debiles):
            continue
        for t in f.tok:
            if t.nf != "sino":
                continue
            n = None
            for j in range(t.i - 1, max(-1, t.i - 14), -1):
                if f.tok[j].nf == "no" and f.tok[j].u in ("ADV", "PART", "X", "INTJ"):
                    n = j
                    break
                if f.tok[j].f in (".", ";"):
                    break
            if n is None:
                continue
            neg = f.tok[n + 1:t.i]
            fin = t.i + 1
            while fin < len(f.tok) and f.tok[fin].f not in (".", ";", ":") and fin - t.i < 14:
                fin += 1
            pos = f.tok[t.i + 1:fin]
            antes = {x.nl for x in f.tok[:n]}
            wn = {x.nl for x in neg if x.u in ("NOUN", "PROPN", "ADJ", "VERB")}
            wp = {x.nl for x in pos if x.u in ("NOUN", "PROPN", "ADJ", "VERB")}
            k_ = {w for w in prop if w not in antes}
            if k_ & wn and not (k_ & wp):
                return f, "No. Según el texto, fue " + L.detok([x.f for x in f.tok[t.i + 1:fin]]).strip(" ,.") + "."
            if k_ & wp and not (k_ & wn):
                return f, "Sí"
    return None


LIGEROS_Q = set(L.LIGEROS) | {"cual", "quien", "como", "cuando", "donde", "cuanto", "tener", "hacer", "estar"}


def _verifica_ninguno(ind: Indice, q: Q, fq: Frase, rk):
    """«¿Perdio Nelson algun navio?»: «…no perdio ninguno»"""
    if not any(t.nf in _DET_Q for t in fq.tok):
        return None
    if not q.verbo or q.verbo.nl in L.GENERICOS:
        return None
    for g, c, f in rk:
        if q.ents and any(nivel_ent_(f, e) < 0.6 for e in q.ents if e not in q.debiles):
            continue
        for t in f.tok:
            if t.u not in ("VERB", "AUX") or not L._coincide(t, q.verbo) or L._grado(t, q.verbo) > 2:
                continue
            neg = any(f.tok[j].nf == "no" for j in range(max(0, t.i - 2), t.i)) or any(f.tok[c_].nf in ("no", "nunca", "jamas") for c_ in f.hij.get(t.i, []))
            nin = any(x.nf in ("ninguno", "ningun", "ninguna", "ningunos", "ningunas", "nada", "nadie") for x in f.tok[max(0, t.i - 3):t.i + 8])
            if (neg and nin) or (nin and any(x.nf in ("ninguno", "ningun", "ninguna") for x in f.tok[t.i + 1:t.i + 6])) and neg:
                return f, "No"
            if nin and any(f.tok[j].nf in ("ninguno", "ningun", "ninguna") and f.tok[j].d == "nsubj" for j in range(len(f.tok))):
                return f, "No"
    return None


def verificar(ind: Indice, q: Q):
    if q.tipo != "si_no" or getattr(q, "_sub", False):
        return None
    fq = _frase_pregunta(ind, q)
    if fq is None:
        return None
    rk = L.ranking(ind, q, 14)
    res = None
    for fn in (_verifica_cargo,):
        r = fn(ind, q, fq)
        if r:
            res = r
            break
    if res is None:
        for fn in (_verifica_lugar, _verifica_sino, _verifica_ninguno, _verifica_verbo, _verifica_adjetivo, _verifica_adjetivo_comun, _verifica_obj_adj, _verifica_atributo_ausente, _verifica_comp_comun):
            r = fn(ind, q, fq, rk)
            if r:
                res = (r[1], r[0])
                break
    if res is None:
        return None
    txt, f = res
    return txt.rstrip(".") + ". En el texto: «" + L.cita(f) + "»", q.ents


# ====================================================== nacionalidad, parentesco, orden y recuento ====================================
COMUNIDADES = {"Cataluña", "País Vasco", "Galicia", "Andalucía", "Aragón", "Navarra", "La Rioja", "Castilla", "León", "Cantabria", "Asturias", "Murcia", "Valencia", "Islas Baleares", "Canarias",
               "Extremadura", "Madrid", "Escocia", "Gales", "Inglaterra"}
CIUDADES = {"Roma", "Atenas", "Salamanca", "Zaragoza", "Sevilla", "Barcelona", "Bilbao", "Toledo", "Córdoba", "Granada", "Málaga", "Valladolid", "Berlín", "París", "Londres", "Nueva York", "Madrid"}
_REGIONES_FOCO = {"comunidad": COMUNIDADES, "region": COMUNIDADES, "pais": None, "estado": None, "nacion": None, "ciudad": CIUDADES}


def _es_pais(nombre: str) -> bool:
    return nombre not in COMUNIDADES and nombre not in CIUDADES


_PAISES_EXTRA = {"Costa Rica", "Panamá", "Guatemala", "Honduras", "El Salvador", "Nicaragua", "República Dominicana", "Líbano", "Siria", "Jordania", "Arabia Saudí", "Pakistán", "Indonesia", "Tailandia",
                 "Vietnam", "Filipinas", "Nigeria", "Kenia", "Etiopía", "Argelia", "Túnez", "Libia", "Nueva Zelanda", "Luxemburgo", "Lituania", "Letonia", "Estonia", "Bielorrusia", "Armenia",
                 "Albania", "Bosnia", "Montenegro", "Chipre", "Malta", "Islandia", "Mongolia", "Corea del Sur", "Corea del Norte", "Afganistán", "Nepal", "Bután", "Sri Lanka", "Bangladés", "Camboya",
                 "Birmania", "Laos", "Tanzania", "Uganda", "Ghana", "Senegal", "Camerún", "Angola", "Mozambique", "Madagascar", "Sudán", "Somalia", "Haití", "Jamaica", "Puerto Rico", "Andorra", "Mónaco",
                 "Liechtenstein", "San Marino", "Vaticano", "Kazajistán", "Uzbekistán", "Azerbaiyán", "Georgia", "Yemen", "Omán", "Catar", "Kuwait", "Emiratos Árabes Unidos"}
PAISES = {p for p in set(_GENT_BASE.values()) if p and p not in COMUNIDADES and p not in CIUDADES} | _PAISES_EXTRA
PAIS_N = {nrm(p): p for p in PAISES}
COM_N = {nrm(p): p for p in COMUNIDADES}
_MARCA_LOC = {"situar", "ubicar", "localizar", "encontrar", "estar", "hallar", "capital", "ciudad", "localidad", "municipio", "pueblo", "region", "provincia", "departamento", "sur", "norte", "este",
              "oeste", "costa", "extender", "limitar", "lindar", "cordillera", "isla", "rio", "valle", "montana", "monte", "yacimiento", "ciudadela", "territorio", "zona", "area", "comarca", "distrito"}


def _lugares_en(f: Frase, conj_n: Dict[str, str]) -> List[Tuple[int, int, str]]:
    """[(i, j, nombre)] nombres de la lista (paises, comunidades) escritos con mayuscula en la frase."""
    out, i, n = [], 0, len(f.tok)
    while i < n:
        hit = None
        if f.tok[i].f[:1].isupper():
            for ln in (3, 2, 1):
                if i + ln <= n:
                    nombre = conj_n.get(" ".join(f.tok[k].nf for k in range(i, i + ln)))
                    if nombre:
                        hit = (i, i + ln - 1, nombre)
                        break
        if hit:
            out.append(hit)
            i = hit[1] + 1
        else:
            i += 1
    return out


def _donde_esta(ind: Indice, e: str, conj_n: Dict[str, str]) -> Dict[str, Frase]:
    """Lugares de la lista donde el texto situa a la entidad: «ciudad inca situada en los Andes, … al sur de Peru» -> {Peru: frase}. Hace falta una palabra de lugar entre ambos."""
    res: Dict[str, Frase] = {}
    for f in ind.fr:
        if e not in f.fams:
            continue
        ms = [m for m in f.ment if _fid(ind, m[2]) == e]
        if not ms:
            continue
        for (i, j, nombre) in _lugares_en(f, conj_n):
            if _mencion_de(f, i) and _fid(ind, _mencion_de(f, i)[2]) == e:
                continue
            if i == 0 or f.tok[i - 1].nf not in ("en", "de", "del", "y", "a", "al"):
                continue
            m = min(ms, key=lambda x: abs(x[0] - i))
            lo, hi = (m[1] + 1, i) if m[1] < i else (j + 1, m[0])
            if hi - lo > 30:
                continue
            if any(f.tok[k].nl in _MARCA_LOC for k in range(lo, hi)):
                res.setdefault(nombre, f)
    return res


def _lista_y(nombres: List[str]) -> str:
    return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]


def _verifica_lugar(ind: Indice, q: Q, fq: Frase, rk):
    """«¿Esta Machu Picchu en Chile?» <- «…situada … al sur de Peru» -> No, esta en Peru."""
    if not any(t.nl in ("estar", "situar", "ubicar", "encontrar", "localizar", "hallar") for t in fq.tok):
        return None
    for conj in (PAIS_N, COM_N):
        for (i, j, nombre) in _lugares_en(fq, conj):
            if i == 0 or fq.tok[i - 1].nf not in ("en", "de", "del"):
                continue
            es = [x for x in q.ents if nrm(ind.disp[x]) != nrm(nombre)]
            if len(es) != 1:
                continue
            lug = _donde_esta(ind, es[0], conj)
            if not lug:
                continue
            if nombre in lug:
                return lug[nombre], "Sí"
            return next(iter(lug.values())), "No. Según el texto, %s está en %s" % (ind.disp[es[0]], _lista_y(list(lug)))
    return None


def _dueno_gent(ind: Indice, f: Frase, i: int):
    """Mencion de la que se dice un adjetivo: se sube por el arbol hasta una mencion, un nombre en aposicion a ella o un predicado cuyo sujeto es una mencion."""
    x = i
    for _ in range(7):
        t = f.tok[x]
        m = _mencion_de(f, x)
        if m and x != i:
            return m
        if t.d == "appos" and t.h >= 0 and _mencion_de(f, t.h):
            return _mencion_de(f, t.h)
        for c in f.hij.get(x, []):
            if f.tok[c].d in ("nsubj", "nsubj:pass") and _mencion_de(f, c):
                return _mencion_de(f, c)
            if f.tok[c].d in ("appos", "flat", "flat:name") and _mencion_de(f, c) and f.tok[x].u in ("NOUN", "PROPN"):
                return _mencion_de(f, c)
        if t.h < 0:
            break
        x = t.h
    return None


def gentilicios_de(ind: Indice, fid: str, maximo: int = 14) -> List[Tuple[str, str, Frase]]:
    """[(adjetivo tal como lo dice el texto, pais o region, frase)] de lo que el texto dice que es la entidad."""
    out, vistos = [], set()
    for f in ind.fr:
        if fid not in f.fams:
            continue
        for m in f.ment:
            if _fid(ind, m[2]) != fid:
                continue
            for d in _descriptores(f, m):
                g = gentilicio(d)
                if g and g not in vistos:
                    vistos.add(g)
                    out.append((d, g, f))
        for t in f.tok:
            if t.u in ("ADJ", "PROPN") and gentilicio(t.f) and t.u == "ADJ":
                g = gentilicio(t.f)
                if g in vistos:
                    continue
                m = _dueno_gent(ind, f, t.i)
                if m is not None and _fid(ind, m[2]) == fid:
                    vistos.add(g)
                    out.append((t.f, g, f))
    return out[:maximo]


_UNIDAD_NAC = re.compile(r"\b(?:nacionalidad(?:es)?|de que pais|de que origen|de donde (?:era|es|fue|eran|son)|que nacionalidad|de que nacionalidad)\b")


def nacionalidad(ind: Indice, q: Q):
    """«¿De que nacionalidad era Villeneuve?» / «¿De donde era Mileva?» / «¿Que nacionalidades tuvo Einstein?»"""
    qn = _qn(q)
    if not _UNIDAD_NAC.search(qn) or len(q.ents) != 1 or q.ents_ctx:
        return None
    lst = gentilicios_de(ind, q.ents[0])
    if not lst:
        return None
    de_donde = "de donde" in qn or "de que pais" in qn or "de que origen" in qn
    if de_donde:
        d0, g0, f0 = lst[0]
        return "De %s. En el texto: «%s»" % (g0, L.cita(f0))
    adjs = []
    for d, g, f in lst:
        if nrm(d) not in [nrm(a) for a in adjs]:
            adjs.append(d)
    plural = bool(re.search(r"nacionalidades|\bquienes\b", qn))
    txt = adjs[0] if len(adjs) == 1 else ", ".join(adjs[:-1]) + " y " + adjs[-1]
    return L.cap(txt) + ". En el texto: «" + L.cita(lst[0][2]) + "»"


def _progenitores(ind: Indice, q: Q, e: str):
    """([menciones de los padres en el orden del texto], frase) de «Hijo del cirujano Rodrigo de Cervantes y de Leonor de Cortinas»."""
    claves_e = set(e.split("+"))
    for g, c, f in L.ranking(ind, q, 14):
        for t in f.tok:
            if t.nl not in ("hijo", "hija") or t.u not in ("NOUN",):
                continue
            j = t.i + 1
            if not (j < len(f.tok) and f.tok[j].nf in ("de", "del")):
                continue
            ms = []
            k = j + 1
            while k < len(f.tok) and f.tok[k].f not in (".", ";", "—"):
                m = _mencion_de(f, k)
                if m and m not in ms:
                    ms.append(m)
                    k = m[1] + 1
                    continue
                if f.tok[k].f == "," and ms and (k + 1 >= len(f.tok) or _mencion_de(f, k + 1) is None):
                    break
                if f.tok[k].u == "VERB":
                    break
                k += 1
            if len(ms) >= 2 and not any(set(m[2]) >= claves_e and len(m[2]) > 1 and _fid(ind, m[2]) == e for m in ms):
                return ms, f
    return None, None


def parentesco(ind: Indice, q: Q):
    """«¿Quienes eran los padres de Einstein?» <- «Hijo de Hermann Einstein y Pauline Koch, nacio…»;  «¿A que se dedicaba el padre de Cervantes?» <- «Hijo del cirujano Rodrigo de Cervantes y de Leonor…»"""
    qn = _qn(q)
    if len(q.ents) != 1 or q.ents_ctx:
        return None
    e = q.ents[0]
    if re.search(r"\b(?:padres|progenitores)\b", qn):
        ms, f = _progenitores(ind, q, e)
        if ms:
            nombres = [m[3] for m in ms[:3]]
            txt = nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]
            return txt + ". En el texto: «" + L.cita(f) + "»"
        return None
    m_p = re.search(r"\b(?:el|la) (padre|madre) (?:de|del)\b", qn)
    if m_p and re.search(r"\b(?:dedic\w*|profesion|oficio|ocupacion|trabaj\w*|llamaba|llamo|nombre)\b", qn):
        ms, f = _progenitores(ind, q, e)
        if not ms:
            return None
        m = ms[0 if m_p.group(1) == "padre" else 1]                                        # «Hijo de [padre] y de [madre]»
        if re.search(r"\b(?:llamaba|llamo|nombre)\b", qn):
            return m[3] + ". En el texto: «" + L.cita(f) + "»"
        k = m[0] - 1
        prof = ""
        while k >= 0 and f.tok[k].u in ("NOUN", "ADJ") and f.tok[k].nl not in ("hijo", "hija"):
            prof = f.tok[k].f + (" " + prof if prof else "")
            k -= 1
        if prof:
            return "Era %s. En el texto: «%s»" % (prof.lower(), L.cita(f))
    return None


_ORD = {"primero": 1, "primer": 1, "primera": 1, "segundo": 2, "segunda": 2, "tercero": 3, "tercer": 3, "tercera": 3, "cuarto": 4, "cuarta": 4, "quinto": 5, "quinta": 5}


def _superlativos(ind: Indice, adj: str) -> List[Tuple[int, Optional[tuple], Optional[tuple], Frase]]:
    """[(puesto, titular, quien va delante, frase)] de «X es el segundo mas ADJ de…, despues de Y» y «X es el mas ADJ de…»."""
    out = []
    la = _lema_adj(adj)
    for f in ind.fr:
        for t in f.tok:
            if t.nf != "mas" or t.i + 1 >= len(f.tok):
                continue
            a = f.tok[t.i + 1]
            if a.u != "ADJ" or _lema_adj(a.f) != la:
                continue
            puesto = 1
            j = t.i - 1
            if j >= 0 and f.tok[j].nf in _ORD:
                puesto = _ORD[f.tok[j].nf]
            elif j >= 1 and f.tok[j - 1].nf in _ORD:
                puesto = _ORD[f.tok[j - 1].nf]
            tit = _dueno_super(f, t.i)
            delante = None
            for k in range(a.i + 1, min(len(f.tok), a.i + 14)):
                if f.tok[k].nf in ("despues", "tras", "detras") and k + 1 < len(f.tok):
                    kk = k + 1
                    while kk < len(f.tok) and f.tok[kk].nf in ("de", "del", "la", "el", "los", "las") or (kk < len(f.tok) and f.tok[kk].u == "DET"):
                        kk += 1
                    delante = _mencion_de(f, kk) if kk < len(f.tok) else None
                    break
                if f.tok[k].f in (".", ";"):
                    break
            if tit is not None or delante is not None:
                out.append((puesto, tit, delante, f))
    return out


def _dueno_super(f: Frase, i: int):
    x = i
    for _ in range(7):
        for c in f.hij.get(x, []):
            if f.tok[c].d in ("nsubj", "nsubj:pass") and _mencion_de(f, c):
                return _mencion_de(f, c)
        t = f.tok[x]
        if t.d == "appos" and t.h >= 0 and _mencion_de(f, t.h):
            return _mencion_de(f, t.h)
        if t.h < 0:
            break
        x = t.h
    # lectura lineal: la mencion mas cercana a la izquierda
    for k in range(i - 1, -1, -1):
        m = _mencion_de(f, k)
        if m:
            return m
    return None


def _de_art(txt: str) -> str:
    """«el Tajo» -> «del Tajo»; «La Rioja» -> «de La Rioja»."""
    if txt.lower().startswith("el "):
        return "del " + txt[3:]
    return "de " + txt


def orden(ind: Indice, q: Q):
    """«¿Cual es el rio mas largo de la peninsula?» / «¿Es el Ebro mas largo que el Tajo?» con «el segundo mas largo, despues del Tajo»."""
    qn = _qn(q)
    m = re.search(r"\bmas (\w+)(?: que\b)?", qn)
    if not m:
        return None
    adj = m.group(1)
    comparativo = bool(re.search(r"\bmas \w+ que\b", qn))
    fq = _frase_pregunta(ind, q)
    if fq is None:
        return None
    sup = _superlativos(ind, adj)
    if not sup:
        return None
    noun_q = next((t.nl for t in fq.tok if t.u == "NOUN" and t.nl not in LIGEROS_Q and t.nl != adj and t.i < len(fq.tok) and any(x.nf == "mas" for x in fq.tok[t.i:t.i + 3])), None)
    if noun_q:
        ok_ = [e_ for e_ in sup if any(x.nl == noun_q for x in e_[3].tok)]
        if ok_:
            sup = ok_                                                                    # «el rio mas largo»: las frases que hablan de otra cosa (una batalla «la mas larga») no cuentan
    if q.tipo == "si_no" and comparativo and len(fq.ment) >= 2:
        a, b = fq.ment[0], fq.ment[1]
        for puesto, tit, delante, f in sup:
            if tit is None or delante is None:
                continue
            if _mismo_nombre(tit[2], a[2], ind) and _mismo_nombre(delante[2], b[2], ind) and puesto >= 2:
                return "No. Según el texto, %s es el %s más %s, después %s. En el texto: «%s»" % (_con_art(f, tit), _ordinal_txt(puesto), adj, _de_art(_con_art(f, delante)), L.cita(f)), q.ents
            if _mismo_nombre(tit[2], b[2], ind) and _mismo_nombre(delante[2], a[2], ind) and puesto >= 2:
                return "Sí. Según el texto, %s es el %s más %s, después %s. En el texto: «%s»" % (_con_art(f, tit), _ordinal_txt(puesto), adj, _de_art(_con_art(f, delante)), L.cita(f)), q.ents
        return None
    if q.tipo in ("que", "quien") and not comparativo and re.search(r"\b(?:cual|que|quien)\b.*\bmas \w+", qn):
        directos = [(p, t, d, f) for p, t, d, f in sup if p == 1 and t is not None]
        if directos:
            return None                                                                   # una frase lo dice directamente: lo contesta el recorrido habitual
        for puesto, tit, delante, f in sup:
            if puesto == 2 and delante is not None:
                return "%s. En el texto: «%s»" % (L.cap(_con_art(f, delante)), L.cita(f)), q.ents
    return None


def _ordinal_txt(n: int) -> str:
    return {1: "primero", 2: "segundo", 3: "tercero", 4: "cuarto", 5: "quinto"}.get(n, str(n) + ".º")


_NUM_PAL = {1: "uno", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis", 7: "siete", 8: "ocho", 9: "nueve", 10: "diez"}


def recuento(ind: Indice, q: Q):
    """«¿Cuantas comunidades atraviesa antes de entrar en Cataluna?» <- «atraviesa La Rioja, Navarra y Aragon antes de…»"""
    qn = _qn(q)
    if q.tipo != "cuanto" or not re.match(r"cuant[oa]s\b", qn) or not q.verbo or q.verbo.nl in L.GENERICOS:
        return None
    for g, c, f in L.ranking(ind, q, 6):
        if c < 0.4:
            break
        if any(t.u == "NUM" for t in f.tok):
            continue
        for v in f.tok:
            if v.u not in ("VERB", "AUX") or not L._coincide(v, q.verbo) or L._grado(v, q.verbo) > 3:
                continue
            for c_ in f.hij.get(v.i, []):
                o = f.tok[c_]
                if o.d not in ("obj", "obl") or o.u not in ("PROPN", "NOUN"):
                    continue
                cadena, pila = [o.i], [o.i]
                while pila:
                    x = pila.pop()
                    for y in f.hij.get(x, []):
                        if f.tok[y].d == "conj" and f.tok[y].u in ("PROPN", "NOUN") and y not in cadena:
                            cadena.append(y)
                            pila.append(y)
                cadena.sort()
                ms = [_mencion_de(f, i) for i in cadena]
                if len(cadena) >= 2 and all(m is not None for m in ms):
                    n = len(cadena)
                    nombres = [_con_art(f, m) for m in ms]
                    lista = ", ".join(nombres[:-1]) + " y " + nombres[-1]
                    return "%s (%s). En el texto: «%s»" % (L.cap(_NUM_PAL.get(n, str(n))), lista, L.cita(f)), q.ents
    return None


_KIND_PALABRA = {"comunidad": "comunidad", "region": "comunidad", "pais": "pais", "estado": "pais", "nacion": "pais", "provincia": "provincia"}


def ubicacion(ind: Indice, q: Q):
    """«¿En que comunidad esta Zaragoza?» <- «Zaragoza, capital de Aragon»;  «¿En que comunidad nace el Ebro?» <- «…municipio cantabro de…»"""
    if q.tipo not in ("que", "donde") or len(q.ents) != 1 or q.ents_ctx:
        return None
    foco = q.foco.nl if q.foco else ""
    foco = nrm(foco)
    if foco not in _KIND_PALABRA and not any(nrm(t[2]) in _KIND_PALABRA for t in q.toks):
        return None
    if foco not in _KIND_PALABRA:
        foco = next(nrm(t[2]) for t in q.toks if nrm(t[2]) in _KIND_PALABRA)
    kind = _KIND_PALABRA[foco]
    e = q.ents[0]
    # 1) «E, capital de [la comunidad autonoma de] Y»
    for f in ind.fr:
        if e not in f.fams:
            continue
        for tit, amb in _cargo_pares(f, "capital"):
            if _fid(ind, tit[2]) != e:
                continue
            palabra = ""
            for k in range(amb[0] - 1, max(-1, amb[0] - 4), -1):
                if f.tok[k].nl in ("comunidad", "provincia", "pais", "region", "estado", "ciudad", "municipio"):
                    palabra = _KIND_PALABRA.get(f.tok[k].nl, f.tok[k].nl) if f.tok[k].nl != "region" else "comunidad"
                    break
            if palabra == kind or (not palabra and ((kind == "comunidad" and amb[3] in COMUNIDADES) or (kind == "pais" and _es_pais(amb[3])))):
                return "%s. En el texto: «%s»" % (_con_art(f, amb)[:1].upper() + _con_art(f, amb)[1:], L.cita(f)), q.ents
    # 1b) «situada … al sur de Peru»: el lugar de ese tipo que el texto nombra junto a una palabra de lugar
    lug = _donde_esta(ind, e, PAIS_N if kind == "pais" else COM_N) if kind in ("pais", "comunidad") else {}
    if lug:
        return "%s. En el texto: «%s»" % (_lista_y(list(lug)), L.cita(next(iter(lug.values())))), q.ents
    # 2) un gentilicio de la propia frase («el municipio cantabro de Hermandad…») nombra la comunidad
    for g, c, f in L.ranking(ind, q, 4):
        if c < 0.5:
            break
        for t in f.tok:
            if t.u == "ADJ" and gentilicio(t.f):
                gv = gentilicio(t.f)
                if (kind == "comunidad" and gv in COMUNIDADES) or (kind == "pais" and _es_pais(gv)):
                    if t.d == "amod" and f.tok[t.h].nl in ("municipio", "pueblo", "localidad", "paraje", "ciudad", "villa", "region", "provincia", "comarca", "valle"):
                        return "%s. En el texto: «%s»" % (gv, L.cita(f)), q.ents
    return None


# ====================================================== entrada ===================================================================
def intentar(ind: Indice, q: Q, final: bool = False):
    """-> (texto, familias) o None. Solo contesta cuando la pregunta pide calcular o comparar y el texto da con que."""
    if getattr(q, "_sub", False):
        return None
    for fn in (comparar, diferencia, total):
        r = fn(ind, q)
        if r:
            return r[0], q.ents
    if q.tipo == "si_no":
        r = verificar(ind, q)
        if r:
            return r
    r_imp = importancia(ind, q)
    if r_imp:
        return r_imp[1] + ". En el texto: «" + L.cita(r_imp[0]) + "»", q.ents
    for fn in (nacionalidad, parentesco, orden, recuento, ubicacion):
        r = fn(ind, q)
        if r:
            return r if isinstance(r, tuple) else (r, q.ents)
    for fn in (edad, intervalo, duracion, entre_hechos):
        r = fn(ind, q)
        if r:
            return r[0], q.ents
    return None
