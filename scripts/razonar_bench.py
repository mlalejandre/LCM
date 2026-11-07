"""parche-112: BANCO DE RAZONAMIENTO del LCM. Genera problemas en 7 dominios y 8 niveles de dificultad; la respuesta correcta sale de un ORACULO
independiente (codigo directo sobre la estructura que genero el mundo, nunca del Razonador) y se mide:

  exactitud            respuestas iguales al oraculo
  prueba_valida        SI/NO cuya prueba pasa el Verificador (codigo aparte del motor)
  falsa_certeza        el motor dice SI/NO y el oraculo dice otra cosa (lo mas grave)
  abstencion_indebida  dice DESCONOCIDO cuando se podia demostrar
  ms_medio / ms_p95    latencia por pregunta
  escala               latencia y exactitud al crecer el mundo (x1, x4, x16, x64)

Niveles: 1 hecho directo | 2 inversa y simetria | 3 cadena transitiva | 4 regla simple | 5 reglas encadenadas y composicion |
         6 negacion (excepcion, unicidad, incompatibilidad, asimetria, comparacion) | 7 enumeracion, conteo y extremos | 8 gran escala y cadenas profundas

  python -m scripts.razonar_bench [--semilla 1] [--n 60] [--escala] [--json reports/razonamiento.json]
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from collections import deque, defaultdict

from src.reasoning.razonador import Razonador, Verificador

DOMINIOS = ["parentesco", "taxonomia", "geografia", "organizacion", "tiempo", "medidas", "logica"]


class Mundo:
    def __init__(self, dominio):
        self.dominio, self.hechos, self.negados, self.reglas, self.props, self.preguntas = dominio, [], [], [], {}, []

    def q(self, nivel, tipo, args, esperado, nota=""):
        self.preguntas.append({"dominio": self.dominio, "nivel": nivel, "tipo": tipo, "args": list(args), "esperado": esperado, "nota": nota})


def _muestra(rng, xs, k):
    xs = list(xs)
    rng.shuffle(xs)
    return xs[:k]


# ============================================ generadores (cada uno trae su oraculo) ============================================
def g_parentesco(rng, n, k=60):
    w = Mundo("parentesco")
    par = {}
    for i in range(1, n):
        par[i] = max(0, i - 1 - rng.randrange(min(i, 3)))
    nm = lambda i: f"P{i}"                                                                   # noqa
    hijos = defaultdict(list)
    for c, p in par.items():
        hijos[p].append(c)
        w.hechos.append((nm(p), "PROGENITOR_DE", nm(c)))
    w.props = {"PROGENITOR_DE": {"inversa": "HIJO_DE", "funcional_inv": True, "subprop": "ANTEPASADO_DE"}, "ANTEPASADO_DE": {"transitiva": True, "asimetrica": True}}
    V = lambda *a: list(a)                                                                   # noqa
    w.reglas = [
        {"id": "abuelo", "si": [V("?X", "PROGENITOR_DE", "?Y"), V("?Y", "PROGENITOR_DE", "?Z")], "entonces": V("?X", "ABUELO_DE", "?Z")},
        {"id": "hermano", "si": [V("?P", "PROGENITOR_DE", "?X"), V("?P", "PROGENITOR_DE", "?Y"), V("?X", "@DISTINTO", "?Y")], "entonces": V("?X", "HERMANO_DE", "?Y")},
        {"id": "tio", "si": [V("?X", "HERMANO_DE", "?Y"), V("?Y", "PROGENITOR_DE", "?Z")], "entonces": V("?X", "TIO_DE", "?Z")},
        {"id": "primo", "si": [V("?A", "PROGENITOR_DE", "?X"), V("?A", "HERMANO_DE", "?B"), V("?B", "PROGENITOR_DE", "?Z")], "entonces": V("?X", "PRIMO_DE", "?Z")},
    ]

    def ancs(c):
        o = []
        while c in par:
            c = par[c]
            o.append(c)
        return o

    def desc(x):
        o, cola = [], deque(hijos[x])
        while cola:
            y = cola.popleft()
            o.append(y)
            cola.extend(hijos[y])
        return o
    def herm(x, y): return x != y and x in par and y in par and par[x] == par[y]             # noqa
    cs = list(par)
    for c in _muestra(rng, cs, k):
        w.q(1, "ask", (nm(par[c]), "PROGENITOR_DE", nm(c)), "SI")
        w.q(2, "ask", (nm(c), "HIJO_DE", nm(par[c])), "SI")
        a = ancs(c)
        if len(a) >= 2:
            w.q(3, "ask", (nm(rng.choice(a[1:])), "ANTEPASADO_DE", nm(c)), "SI")
            w.q(6, "ask", (nm(c), "ANTEPASADO_DE", nm(rng.choice(a))), "NO", "asimetria")
        if len(a) >= 2:
            w.q(4, "ask", (nm(a[1]), "ABUELO_DE", nm(c)), "SI")
            w.q(4, "ask", (nm(rng.choice(cs)), "ABUELO_DE", nm(c)), "SI" if False else "DESCONOCIDO") if not (len(a) >= 2) else None
        otro = rng.choice(cs)
        if otro != par[c]:
            w.q(6, "ask", (nm(otro), "PROGENITOR_DE", nm(c)), "NO", "unicidad")
        for h in cs:
            if herm(c, h):
                w.q(4, "ask", (nm(h), "HERMANO_DE", nm(c)), "SI")
                break
        if len(a) >= 2 and par[a[0]] in par:
            for t in hijos[a[1]]:
                if t != a[0]:
                    w.q(5, "ask", (nm(t), "TIO_DE", nm(c)), "SI")
                    for pr in hijos[t]:
                        w.q(5, "ask", (nm(pr), "PRIMO_DE", nm(c)), "SI")
                        break
                    break
        # abstencion: pares que no son abuelo (el mundo es abierto: no hay motivo para decir NO)
        x = rng.choice(cs)
        if x not in ancs(c) and x != c and (len(a) < 2 or x != a[1]):
            w.q(4, "ask", (nm(x), "ABUELO_DE", nm(c)), "DESCONOCIDO", "abstencion")
    for x in _muestra(rng, [x for x in range(n) if len(desc(x)) > 0], max(8, k // 5)):
        nietos = {nm(y) for y in range(1, n) if y in par and par[y] in par and par[par[y]] == x}
        if nietos:
            w.q(7, "lista", (nm(x), "ABUELO_DE", None), sorted(nietos))
        w.q(7, "cuenta", (nm(x), "ANTEPASADO_DE", None), len(desc(x)))
        hs = {nm(y) for y in hijos.get(par.get(x, -1), []) if y != x} if x in par else set()
        if hs:
            w.q(7, "lista", (nm(x), "HERMANO_DE", None), sorted(hs))
    # nivel 8: los ancestros mas lejanos de las hojas mas profundas
    prof = {0: 0}
    for i in range(1, n):
        prof[i] = prof[par[i]] + 1
    hondos = sorted(range(n), key=lambda i: -prof[i])[: max(4, k // 6)]
    for c in hondos:
        a = ancs(c)
        if len(a) >= 3:
            w.q(8, "ask", (nm(a[-1]), "ANTEPASADO_DE", nm(c)), "SI", f"prof={len(a)}")
            w.q(8, "ruta", (nm(a[-1]), "ANTEPASADO_DE", nm(c)), len(a), "")
    return w


def g_taxonomia(rng, n, k=60):
    w = Mundo("taxonomia")
    ncl = max(8, n // 4)
    pc = {}
    for i in range(1, ncl):
        pc[i] = rng.randrange(0, i) if i > 3 else 0
    cn = lambda i: f"C{i}"                                                                   # noqa
    for c, p in pc.items():
        w.hechos.append((cn(c), "ES", cn(p)))
    tops = [c for c, p in pc.items() if p == 0]
    for a in tops:
        for b in tops:
            if a < b:
                w.hechos.append((cn(a), "DISJUNTA_CON", cn(b)))
    w.props = {"ES": {"transitiva": True}, "*": {"heredable": True}}
    dec = defaultdict(dict)
    feats = [f"F{i}" for i in range(6)]
    for f in feats:
        c = rng.randrange(0, ncl)
        dec[c][f] = True
        hij = [x for x in range(ncl) if x in pc and pc[x] == c]
        for d in hij[:1]:
            if rng.random() < .7:
                dec[d][f] = False
    for c, ds in dec.items():
        for f, v in ds.items():
            (w.hechos if v else w.negados).append((cn(c), "TIENE", f))
    ind = {}
    for j in range(n):
        ind[j] = rng.randrange(0, ncl)
        w.hechos.append((f"I{j}", "ES", cn(ind[j])))

    def cadena(c):
        o = [c]
        while c in pc:
            c = pc[c]
            o.append(c)
        return o

    def tiene(j, f):
        for c in cadena(ind[j]):
            if f in dec[c]:
                return "SI" if dec[c][f] else "NO"
        return "DESCONOCIDO"

    def topc(c):
        ch = cadena(c)
        return ch[-2] if len(ch) >= 2 else ch[-1]
    for j in _muestra(rng, list(ind), k):
        w.q(1, "ask", (f"I{j}", "ES", cn(ind[j])), "SI")
        ch = cadena(ind[j])
        if len(ch) >= 3:
            w.q(3, "ask", (f"I{j}", "ES", cn(rng.choice(ch[2:]))), "SI")
        for f in feats:
            t = tiene(j, f)
            w.q(5 if t == "SI" else 6, "ask", (f"I{j}", "TIENE", f), t, "herencia" if t != "DESCONOCIDO" else "abstencion")
        for b in tops:
            if b != topc(ind[j]) and cn(b) not in ch and len(ch) >= 2:
                w.q(6, "ask", (f"I{j}", "ES", cn(b)), "NO", "disjunta")
                break
    for c in _muestra(rng, range(ncl), max(6, k // 5)):
        miembros = sorted([f"I{j}" for j in ind if c in cadena(ind[j])] + [cn(x) for x in pc if x != c and c in cadena(x)])
        if miembros:
            w.q(7, "lista", (None, "ES", cn(c)), miembros)
            w.q(7, "cuenta", (None, "ES", cn(c)), len(miembros))
    return w


def g_geografia(rng, n, k=60):
    w = Mundo("geografia")
    npais = max(6, n // 8)
    cont = max(2, npais // 5)
    pais = {}
    for i in range(npais):
        pais[i] = i % cont
        w.hechos.append((f"PAIS{i}", "EN", f"CONT{i % cont}"))
    ady = defaultdict(set)
    for i in range(1, npais):
        j = rng.randrange(0, i)
        ady[i].add(j)
        ady[j].add(i)
    for _ in range(npais // 2):
        a, b = rng.randrange(npais), rng.randrange(npais)
        if a != b:
            ady[a].add(b)
            ady[b].add(a)
    for a in range(npais):
        for b in ady[a]:
            if a < b:
                w.hechos.append((f"PAIS{a}", "LIMITA_CON", f"PAIS{b}"))
    reg, ciu = {}, {}
    nreg = npais * 2
    for r in range(nreg):
        reg[r] = r % npais
        w.hechos.append((f"REG{r}", "EN", f"PAIS{reg[r]}"))
    for c in range(n):
        ciu[c] = c % nreg
        w.hechos.append((f"CIU{c}", "EN", f"REG{ciu[c]}"))
    w.props = {"EN": {"transitiva": True}, "LIMITA_CON": {"simetrica": True}}
    w.reglas = [{"id": "frontera", "si": [["?X", "EN", "?P"], ["?Y", "EN", "?Q"], ["?P", "LIMITA_CON", "?Q"]], "entonces": ["?X", "FRONTERIZA_CON", "?Y"]}]
    pa = lambda c: reg[ciu[c]] % npais                                                      # noqa
    pa = lambda c: reg[ciu[c]]                                                              # noqa
    for c in _muestra(rng, list(ciu), k):
        w.q(1, "ask", (f"CIU{c}", "EN", f"REG{ciu[c]}"), "SI")
        w.q(3, "ask", (f"CIU{c}", "EN", f"PAIS{pa(c)}"), "SI")
        w.q(3, "ask", (f"CIU{c}", "EN", f"CONT{pa(c) % cont}"), "SI")
        p = pa(c)
        for q_ in list(ady[p])[:1]:
            w.q(2, "ask", (f"PAIS{q_}", "LIMITA_CON", f"PAIS{p}"), "SI")
            d = rng.choice([x for x in ciu if pa(x) == q_] or [c])
            if pa(d) == q_:
                w.q(5, "ask", (f"CIU{c}", "FRONTERIZA_CON", f"CIU{d}"), "SI")
        d = rng.choice(list(ciu))
        if pa(d) != p and pa(d) not in ady[p]:
            w.q(5, "ask", (f"CIU{c}", "FRONTERIZA_CON", f"CIU{d}"), "DESCONOCIDO", "abstencion")
    for p in _muestra(rng, range(npais), max(5, k // 6)):
        cs = sorted(f"CIU{c}" for c in ciu if pa(c) == p)
        if cs:
            w.q(7, "lista", (None, "EN", f"PAIS{p}"), sorted(cs + [f"REG{r}" for r in reg if reg[r] == p]))
            w.q(7, "cuenta", (None, "EN", f"CONT{p % cont}"), len([1 for x in range(npais) if x % cont == p % cont]) + len([1 for r in reg if reg[r] % cont == p % cont]) + len([1 for c in ciu if pa(c) % cont == p % cont]))
    for _ in range(max(4, k // 6)):
        a, b = rng.randrange(npais), rng.randrange(npais)
        if a == b:
            continue
        dist = {a: 0}
        cola = deque([a])
        while cola:
            x = cola.popleft()
            for y in ady[x]:
                if y not in dist:
                    dist[y] = dist[x] + 1
                    cola.append(y)
        w.q(8, "ruta", (f"PAIS{a}", "LIMITA_CON", f"PAIS{b}"), dist[b])
    return w


def g_organizacion(rng, n, k=60):
    w = Mundo("organizacion")
    jefe = {i: max(0, i - 1 - rng.randrange(min(i, 4))) for i in range(1, n)}
    sub = defaultdict(list)
    for e, b in jefe.items():
        sub[b].append(e)
        w.hechos.append((f"E{b}", "JEFE_DE", f"E{e}"))
    sal = {i: 1000 + rng.randrange(0, 9000) * 1 + i * 0 for i in range(n)}
    vistos = set()
    for i in range(n):
        while sal[i] in vistos:
            sal[i] += 1
        vistos.add(sal[i])
        w.hechos += [(f"E{i}", "SALARIO", str(sal[i])), (f"E{i}", "ES", "EMPLEADO")]
    w.props = {"JEFE_DE": {"inversa": "INFORMA_A", "subprop": "SUPERIOR_DE"}, "SUPERIOR_DE": {"transitiva": True, "asimetrica": True},
               "MAS_CARO_QUE": {"compara": {"atributo": "SALARIO", "op": ">"}}, "BIEN_PAGADO": {"mundo_cerrado": True}}
    w.reglas = [{"id": "colega", "si": [["?B", "JEFE_DE", "?X"], ["?B", "JEFE_DE", "?Y"], ["?X", "@DISTINTO", "?Y"]], "entonces": ["?X", "COLEGA_DE", "?Y"]},
                {"id": "bienpagado", "si": [["?X", "SALARIO", "?V"], ["?V", "@MAYOR", "7000"]], "entonces": ["?X", "BIEN_PAGADO", "SI"]}]

    def sups(e):
        o = []
        while e in jefe:
            e = jefe[e]
            o.append(e)
        return o

    def subs(e):
        o, cola = [], deque(sub[e])
        while cola:
            y = cola.popleft()
            o.append(y)
            cola.extend(sub[y])
        return o
    es = list(jefe)
    for e in _muestra(rng, es, k):
        w.q(1, "ask", (f"E{jefe[e]}", "JEFE_DE", f"E{e}"), "SI")
        w.q(2, "ask", (f"E{e}", "INFORMA_A", f"E{jefe[e]}"), "SI")
        s = sups(e)
        if len(s) >= 2:
            w.q(3, "ask", (f"E{rng.choice(s[1:])}", "SUPERIOR_DE", f"E{e}"), "SI")
            w.q(6, "ask", (f"E{e}", "SUPERIOR_DE", f"E{rng.choice(s)}"), "NO", "asimetria")
        for h in sub[jefe[e]]:
            if h != e:
                w.q(4, "ask", (f"E{h}", "COLEGA_DE", f"E{e}"), "SI")
                break
        w.q(4 if sal[e] > 7000 else 6, "ask", (f"E{e}", "BIEN_PAGADO", "SI"), "SI" if sal[e] > 7000 else "NO", "" if sal[e] > 7000 else "mundo_cerrado")
        o = rng.choice(es)
        if o != e:
            w.q(6, "ask", (f"E{e}", "MAS_CARO_QUE", f"E{o}"), "SI" if sal[e] > sal[o] else "NO", "comparacion")
    for e in _muestra(rng, [e for e in range(n) if sub[e]], max(6, k // 5)):
        w.q(7, "cuenta", (f"E{e}", "SUPERIOR_DE", None), len(subs(e)))
        w.q(7, "lista", (f"E{e}", "JEFE_DE", None), sorted(f"E{x}" for x in sub[e]))
    w.q(7, "extremo", ("SALARIO", "EMPLEADO", "max"), f"E{max(sal, key=sal.get)}")
    w.q(7, "extremo", ("SALARIO", "EMPLEADO", "min"), f"E{min(sal, key=sal.get)}")
    hondos = sorted(es, key=lambda e: -len(sups(e)))[: max(3, k // 8)]
    for e in hondos:
        s = sups(e)
        if len(s) >= 3:
            w.q(8, "ask", (f"E{s[-1]}", "SUPERIOR_DE", f"E{e}"), "SI", f"prof={len(s)}")
            w.q(8, "ruta", (f"E{s[-1]}", "SUPERIOR_DE", f"E{e}"), len(s))
    return w


def g_tiempo(rng, n, k=60):
    w = Mundo("tiempo")
    rango = list(range(n))
    rng.shuffle(rango)                                                                       # rango[i] = posicion real del evento i
    pos = {i: rango[i] for i in range(n)}
    orden = sorted(range(n), key=lambda i: pos[i])
    sig = defaultdict(set)
    for a in range(len(orden) - 1):
        sig[orden[a]].add(orden[a + 1]) if rng.random() < .8 else None
    for a in range(len(orden)):
        for b in range(a + 2, min(len(orden), a + 5)):
            if rng.random() < .15:
                sig[orden[a]].add(orden[b])
    for a, bs in sig.items():
        for b in bs:
            w.hechos.append((f"T{a}", "ANTES_DE", f"T{b}"))
    w.props = {"ANTES_DE": {"transitiva": True, "inversa": "DESPUES_DE", "asimetrica": True}, "DESPUES_DE": {"transitiva": True, "asimetrica": True}}

    def alcanza(a):
        vis, cola = {a}, deque([a])
        while cola:
            x = cola.popleft()
            for y in sig[x]:
                if y not in vis:
                    vis.add(y)
                    cola.append(y)
        vis.discard(a)
        return vis
    ar = {i: alcanza(i) for i in range(n)} if n <= 1500 else {}
    ev = list(range(n))
    for a in _muestra(rng, ev, k):
        r = ar.get(a) if ar else alcanza(a)
        if not r:
            continue
        b = rng.choice(sorted(r))
        w.q(1 if b in sig[a] else 3, "ask", (f"T{a}", "ANTES_DE", f"T{b}"), "SI")
        w.q(2 if b in sig[a] else 3, "ask", (f"T{b}", "DESPUES_DE", f"T{a}"), "SI")
        w.q(6, "ask", (f"T{b}", "ANTES_DE", f"T{a}"), "NO", "asimetria")
        c = rng.choice(ev)
        if c != a and c not in r and a not in (ar.get(c) if ar else alcanza(c)):
            w.q(3, "ask", (f"T{a}", "ANTES_DE", f"T{c}"), "DESCONOCIDO", "abstencion")
    for a in _muestra(rng, ev, max(6, k // 5)):
        r = ar.get(a) if ar else alcanza(a)
        w.q(7, "cuenta", (f"T{a}", "ANTES_DE", None), len(r))
    hondos = _muestra(rng, ev, max(4, k // 8))
    for a in hondos:
        r = ar.get(a) if ar else alcanza(a)
        if r:
            b = max(r, key=lambda x: pos[x])
            dist = {a: 0}
            cola = deque([a])
            while cola:
                x = cola.popleft()
                for y in sig[x]:
                    if y not in dist:
                        dist[y] = dist[x] + 1
                        cola.append(y)
            w.q(8, "ruta", (f"T{a}", "ANTES_DE", f"T{b}"), dist[b])
    return w


def g_medidas(rng, n, k=60):
    w = Mundo("medidas")
    alt = {}
    usados = set()
    for i in range(n):
        v = 1 + rng.randrange(0, 40 * n)
        while v in usados:
            v += 1
        usados.add(v)
        alt[i] = v
    clase = {i: ("TORRE" if rng.random() < .5 else "ARBOL") for i in range(n)}
    for i in range(n):
        w.hechos += [(f"M{i}", "ALTURA", str(alt[i])), (f"M{i}", "ES", clase[i])]
    umbral = sorted(alt.values())[int(n * .8)]
    w.props = {"MAS_ALTO_QUE": {"compara": {"atributo": "ALTURA", "op": ">"}}, "MAS_BAJO_QUE": {"compara": {"atributo": "ALTURA", "op": "<"}}, "ES": {"transitiva": True}}
    w.reglas = [{"id": "gigante", "si": [["?X", "ALTURA", "?V"], ["?V", "@MAYOR", str(umbral)]], "entonces": ["?X", "CATEGORIA", "GIGANTE"]},
                {"id": "gigante_torre", "si": [["?X", "CATEGORIA", "GIGANTE"], ["?X", "ES", "TORRE"]], "entonces": ["?X", "CATEGORIA", "RASCACIELOS"]}]
    for i in _muestra(rng, range(n), k):
        j = rng.randrange(n)
        if i == j:
            continue
        w.q(6, "ask", (f"M{i}", "MAS_ALTO_QUE", f"M{j}"), "SI" if alt[i] > alt[j] else "NO", "comparacion")
        w.q(2, "ask", (f"M{i}", "MAS_BAJO_QUE", f"M{j}"), "SI" if alt[i] < alt[j] else "NO", "comparacion")
        w.q(1, "ask", (f"M{i}", "ES", clase[i]), "SI")
        if alt[i] > umbral:
            w.q(4, "ask", (f"M{i}", "CATEGORIA", "GIGANTE"), "SI")
            w.q(5 if clase[i] == "TORRE" else 5, "ask", (f"M{i}", "CATEGORIA", "RASCACIELOS"), "SI" if clase[i] == "TORRE" else "DESCONOCIDO", "" if clase[i] == "TORRE" else "abstencion")
        else:
            w.q(4, "ask", (f"M{i}", "CATEGORIA", "GIGANTE"), "DESCONOCIDO", "abstencion")
    w.q(7, "lista", (None, "CATEGORIA", "GIGANTE"), sorted(f"M{i}" for i in range(n) if alt[i] > umbral))
    w.q(7, "lista", (None, "CATEGORIA", "RASCACIELOS"), sorted(f"M{i}" for i in range(n) if alt[i] > umbral and clase[i] == "TORRE"))
    for c in ("TORRE", "ARBOL"):
        mm = [i for i in range(n) if clase[i] == c]
        if mm:
            w.q(7, "extremo", ("ALTURA", c, "max"), f"M{max(mm, key=lambda i: alt[i])}")
            w.q(7, "extremo", ("ALTURA", c, "min"), f"M{min(mm, key=lambda i: alt[i])}")
    w.q(7, "extremo", ("ALTURA", None, "max"), f"M{max(alt, key=alt.get)}")
    return w


def g_logica(rng, n, k=60):
    """Cadenas de implicaciones con conjunciones y miles de reglas de relleno: mide profundidad y distraccion."""
    w = Mundo("logica")
    prof = 12
    reglas, cierre_regla = [], []
    for d in range(prof):
        reglas.append({"id": f"c{d}", "si": [["?X", "ESTADO", f"K{d}"]], "entonces": ["?X", "ESTADO", f"K{d + 1}"]})
        cierre_regla.append(([f"K{d}"], f"K{d + 1}"))
    for d in range(0, prof - 2, 3):
        reglas.append({"id": f"y{d}", "si": [["?X", "ESTADO", f"K{d}"], ["?X", "ESTADO", f"A{d}"]], "entonces": ["?X", "ESTADO", f"Y{d}"]})
        cierre_regla.append(([f"K{d}", f"A{d}"], f"Y{d}"))
    for z in range(n):                                                                       # distractores: reglas que nunca se disparan con los objetos del problema
        reglas.append({"id": f"z{z}", "si": [["?X", "ESTADO", f"Z{z}"]], "entonces": ["?X", "ESTADO", f"ZZ{z}"]})
        cierre_regla.append(([f"Z{z}"], f"ZZ{z}"))
    w.reglas = reglas
    w.props = {}
    objs = {}
    for o in range(max(10, n // 3)):
        ini = set()
        d = rng.randrange(0, 4)
        ini.add(f"K{d}")
        if rng.random() < .6:
            ini.add(f"A{rng.randrange(0, prof - 2, 3)}")
        objs[o] = ini
        for x in ini:
            w.hechos.append((f"O{o}", "ESTADO", x))
    cl = {}
    for o, ini in objs.items():
        s, cambio = set(ini), True
        while cambio:
            cambio = False
            for pre, con in cierre_regla:
                if con not in s and all(p in s for p in pre):
                    s.add(con)
                    cambio = True
        cl[o] = s
    for o in _muestra(rng, list(objs), k):
        for d in (1, 3, 5, 8, 12):
            tgt = f"K{d}"
            lv = 4 if d <= 1 else 5 if d <= 5 else 8
            w.q(lv, "ask", (f"O{o}", "ESTADO", tgt), "SI" if tgt in cl[o] else "DESCONOCIDO", "" if tgt in cl[o] else "abstencion")
        for d in (0, 3, 6):
            tgt = f"Y{d}"
            w.q(5, "ask", (f"O{o}", "ESTADO", tgt), "SI" if tgt in cl[o] else "DESCONOCIDO", "" if tgt in cl[o] else "abstencion")
    return w


GENERADORES = {"parentesco": g_parentesco, "taxonomia": g_taxonomia, "geografia": g_geografia, "organizacion": g_organizacion, "tiempo": g_tiempo, "medidas": g_medidas, "logica": g_logica}


# ============================================ evaluacion ============================================
def evaluar_mundo(w: Mundo, presupuesto=None):
    R = Razonador(w.hechos, w.reglas, w.props, w.negados, **({"presupuesto": presupuesto} if presupuesto else {}))
    V = Verificador(w.hechos, w.reglas, w.props, w.negados)
    filas = []
    for q in w.preguntas:
        t0 = time.perf_counter()
        t = q["tipo"]
        a = q["args"]
        obt, prueba_ok, valor_cert = None, None, None
        try:
            if t == "ask":
                r = R.preguntar(*a)
                obt = r.valor
                if r.prueba is not None:
                    prueba_ok = V.ok(r.prueba)[0]
            elif t in ("lista", "cuenta"):
                sol = R.consultar(a[0], a[1], a[2], 10 ** 6)
                hueco = "o" if a[2] is None else "s"
                ent = sorted({x[hueco] for x in sol})
                obt = ent if t == "lista" else len(ent)
                prueba_ok = all(V.ok(x["prueba"])[0] for x in sol[:50]) if sol else True
            elif t == "extremo":
                e = R.extremo(a[0], a[1], a[2])
                obt = e["entidad"] if e and "entidad" in e else None
                prueba_ok = V.ok(e["prueba"])[0] if e and e.get("prueba") else False
            elif t == "ruta":
                pr = R.ruta(a[0], a[2], a[1])
                obt = None if pr is None else (len(pr.hijos) if pr.regla == "transitiva" else 1)
                prueba_ok = bool(pr) and V.ok(pr)[0]
        except Exception as e:                                                               # noqa
            obt, prueba_ok = f"ERROR {e!r}", False
        ms = (time.perf_counter() - t0) * 1000
        correcto = obt == q["esperado"]
        cert_falsa = t == "ask" and obt in ("SI", "NO") and obt != q["esperado"]
        abst = t == "ask" and obt == "DESCONOCIDO" and q["esperado"] in ("SI", "NO")
        filas.append({**q, "obtenido": obt, "ok": correcto, "prueba_ok": prueba_ok, "falsa_certeza": cert_falsa, "abstencion_indebida": abst, "ms": ms})
    return filas


def resumen(filas):
    def agg(fs):
        if not fs:
            return None
        con_prueba = [f for f in fs if f["prueba_ok"] is not None]
        ms = sorted(f["ms"] for f in fs)
        return {"n": len(fs), "exactitud": round(sum(f["ok"] for f in fs) / len(fs), 4),
                "prueba_valida": round(sum(1 for f in con_prueba if f["prueba_ok"]) / len(con_prueba), 4) if con_prueba else 1.0,
                "falsa_certeza": round(sum(f["falsa_certeza"] for f in fs) / len(fs), 4),
                "abstencion_indebida": round(sum(f["abstencion_indebida"] for f in fs) / len(fs), 4),
                "ms_medio": round(statistics.mean(ms), 3), "ms_p95": round(ms[min(len(ms) - 1, int(len(ms) * .95))], 3)}
    out = {"global": agg(filas), "por_nivel": {}, "por_dominio": {}}
    for nv in range(1, 9):
        out["por_nivel"][nv] = agg([f for f in filas if f["nivel"] == nv])
    for d in DOMINIOS:
        out["por_dominio"][d] = agg([f for f in filas if f["dominio"] == d])
    return out


def ejecutar(semilla=1, n=60, k=40, dominios=None, escala=False):
    filas = []
    for d in dominios or DOMINIOS:
        rng = random.Random(f"{semilla}-{d}")
        w = GENERADORES[d](rng, n, k)
        filas += evaluar_mundo(w)
    res = resumen(filas)
    res["fallos"] = [{k_: f[k_] for k_ in ("dominio", "nivel", "tipo", "args", "esperado", "obtenido", "nota")} for f in filas if not f["ok"]][:40]
    if escala:
        res["escala"] = []
        for mult in (1, 4, 16, 64):
            tam = n * mult
            fs = []
            for d in ("parentesco", "organizacion", "tiempo", "geografia"):
                rng = random.Random(f"esc-{semilla}-{d}-{mult}")
                fs += evaluar_mundo(GENERADORES[d](rng, tam, 12))
            a = resumen(fs)["global"]
            res["escala"].append({"n": tam, "preguntas": a["n"], "exactitud": a["exactitud"], "ms_medio": a["ms_medio"], "ms_p95": a["ms_p95"], "prueba_valida": a["prueba_valida"]})
    return res


def texto(res) -> str:
    L = []
    g = res["global"]
    L.append(f"RAZONAMIENTO  n={g['n']}  exactitud={g['exactitud']:.1%}  prueba_valida={g['prueba_valida']:.1%}  falsa_certeza={g['falsa_certeza']:.2%}  "
             f"abstencion_indebida={g['abstencion_indebida']:.2%}  ms_medio={g['ms_medio']}  p95={g['ms_p95']}")
    L.append("  por nivel:   " + "  ".join(f"L{k}={v['exactitud']:.0%}({v['n']})" for k, v in res["por_nivel"].items() if v))
    L.append("  por dominio: " + "  ".join(f"{k}={v['exactitud']:.0%}({v['n']})" for k, v in res["por_dominio"].items() if v))
    for e in res.get("escala", []):
        L.append(f"  escala n={e['n']:>6}  preguntas={e['preguntas']:>3}  exactitud={e['exactitud']:.0%}  ms_medio={e['ms_medio']}  p95={e['ms_p95']}  prueba_valida={e['prueba_valida']:.0%}")
    for f in res.get("fallos", [])[:15]:
        L.append(f"  FALLO {f['dominio']} L{f['nivel']} {f['tipo']} {f['args']} esperado={str(f['esperado'])[:60]} obtenido={str(f['obtenido'])[:60]} {f['nota']}")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--semilla", type=int, default=1)
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--k", type=int, default=40)
    ap.add_argument("--escala", action="store_true")
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    res = ejecutar(a.semilla, a.n, a.k, escala=a.escala)
    print(texto(res))
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(res, fh, indent=1, ensure_ascii=False, default=str)
    return res


if __name__ == "__main__":
    main()
