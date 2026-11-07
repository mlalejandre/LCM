"""Deduccion con las lecciones aprendidas (parche-47, Fase 2). Sin red neuronal: se generaliza cada leccion a una regla con variables
("Ana es madre de Luis => Luis es hijo de Ana"  ->  "?0 madre_de ?1 => ?1 hijo_de ?0") y se aplica a los hechos de la memoria,
guardando de que hechos sale cada conclusion para poder explicarla ("lo deduzco de ...")."""
from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Sequence, Tuple

Triple = Tuple[str, str, str]


def generalize(lesson: dict, is_var: Callable[[str], bool] = lambda n: True):
    mapping: Dict[str, str] = {}
    prem = []
    for p in lesson["premises"]:
        t = []
        for slot, x in enumerate(p):
            x = x.upper()
            if slot != 1 and x.startswith("?"):
                mapping.setdefault(x, x)
            elif slot != 1 and is_var(x):
                mapping.setdefault(x, f"?{len(mapping)}")
                x = mapping[x]
            t.append(x)
        prem.append(tuple(t))
    concl = tuple(mapping.get(x.upper(), x.upper()) if i != 1 else x.upper() for i, x in enumerate(lesson["conclusion"]))
    return prem, concl


def _matches(prem: Sequence[Triple], known: Sequence[Triple], bind: Dict[str, str], used: List[Triple]):
    if not prem:
        yield dict(bind), list(used)
        return
    s, p, o = prem[0]
    for f in known:
        if f[1] != p:
            continue
        new, ok = dict(bind), True
        for term, val in ((s, f[0]), (o, f[2])):
            if term.startswith("?"):
                if term in new:
                    ok &= new[term] == val
                else:
                    ok &= val not in new.values()          # variables distintas -> entidades distintas
                    new[term] = val
            else:
                ok &= term == val
            if not ok:
                break
        if ok:
            yield from _matches(prem[1:], known, new, used + [f])


# Regla general que no hace falta ensenar: la jerarquia "A es B, B es C => A es C" (parche-50)
DEFAULT_LESSONS = [{"premises": [["?A", "ES", "?B"], ["?B", "ES", "?C"]], "conclusion": ["?A", "ES", "?C"], "archived": False}]


def _r(prem, concl):
    return {"premises": [list(x) for x in prem], "conclusion": list(concl), "archived": False}


# Reglas de fabrica de parentesco y partes (parche-59): no hace falta ensenarlas
FAMILY_LESSONS = (
    [_r([("?A", x, "?B")], ("?B", "HIJO_DE", "?A")) for x in ("PADRE_DE", "MADRE_DE")]
    + [_r([("?A", x, "?B"), ("?B", y, "?C")], ("?A", "ABUELO_DE" if x == "PADRE_DE" else "ABUELA_DE", "?C"))
       for x in ("PADRE_DE", "MADRE_DE") for y in ("PADRE_DE", "MADRE_DE")]
    + [_r([("?A", x, "?B")], ("?B", "NIETO_DE", "?A")) for x in ("ABUELO_DE", "ABUELA_DE")]
    + [_r([("?A", x, "?B")], ("?B", "HERMANO_DE", "?A")) for x in ("HERMANO_DE", "HERMANA_DE")]
    + [_r([("?P", x, "?A"), ("?P", x, "?B")], ("?A", "HERMANO_DE", "?B")) for x in ("PADRE_DE", "MADRE_DE")]
    + [_r([("?A", h, "?B"), ("?B", x, "?C")], ("?A", "TIO_DE" if h == "HERMANO_DE" else "TIA_DE", "?C"))
       for h in ("HERMANO_DE", "HERMANA_DE") for x in ("PADRE_DE", "MADRE_DE")]
    + [_r([("?A", t, "?C"), ("?A", x, "?D")], ("?C", "PRIMO_DE", "?D")) for t in ("TIO_DE", "TIA_DE") for x in ("PADRE_DE", "MADRE_DE")]
    + [_r([("?A", "PRIMO_DE", "?B")], ("?B", "PRIMO_DE", "?A"))]
    + [_r([("?A", "ESPOSO_DE", "?B")], ("?B", "ESPOSA_DE", "?A")), _r([("?A", "ESPOSA_DE", "?B")], ("?B", "ESPOSO_DE", "?A")),
       _r([("?A", "MARIDO_DE", "?B")], ("?B", "ESPOSA_DE", "?A")), _r([("?A", "MUJER_DE", "?B")], ("?B", "ESPOSO_DE", "?A"))]
    + [_r([("?A", "PARTE_DE", "?B"), ("?B", "PARTE_DE", "?C")], ("?A", "PARTE_DE", "?C")),
       _r([("?A", "PARTE_DE", "?B")], ("?B", "TENER", "?A"))]
)
DEFAULT_LESSONS = DEFAULT_LESSONS + FAMILY_LESSONS


def apply_lessons(facts: Iterable[Triple], lessons: Sequence[dict], is_var: Callable[[str], bool] = lambda n: True,
                  rounds: int = 3, cap: int = 200, defaults: bool = True) -> Dict[Triple, List[Triple]]:
    """Devuelve {conclusion: [hechos de los que sale]} para lo que se deduce y no estaba ya."""
    known = {tuple(x.upper() for x in f) for f in facts}
    rules = [generalize(l, is_var) for l in list(lessons) + (DEFAULT_LESSONS if defaults else []) if not l.get("archived")]
    derived: Dict[Triple, List[Triple]] = {}
    for _ in range(rounds):
        new = {}
        for prem, concl in rules:
            for bind, used in _matches(prem, sorted(known), {}, []):
                out = tuple(bind.get(x, x) for x in concl)
                if any(x.startswith("?") for x in out) or out in known or out in derived or out in new:
                    continue
                new[out] = used
        if not new:
            break
        derived.update(new)
        known |= set(new)
        if len(derived) >= cap:
            break
    return derived


def canon(name: str) -> str:
    """Forma comparable sin plural: POLIGONOS -> POLIGONO, ANIMALES -> ANIMAL (solo para comparar clases con sus miembros)."""
    w = name.upper()
    if w.endswith("OIDES"):                      # parche-94: asteroides -> asteroide (no "asteroid")
        return w[:-1]
    if w.endswith("CES"):
        return w[:-3] + "Z"
    if w.endswith("ES") and len(w) > 4 and w[-3] not in "AEIOU":
        return w[:-2]
    if w.endswith("S") and len(w) > 3:
        return w[:-1]
    return w


def inherit(facts: Iterable[Triple], rounds: int = 6) -> Dict[Triple, List[Triple]]:
    """Herencia (parche-52): "Los poligonos tienen lados" + "Un triangulo es un poligono" => "el triangulo tiene lados".
    Solo hacia abajo (de la clase al miembro, tambien por cadenas de ES); el miembro hereda lo de TODAS sus clases.
    Devuelve {hecho deducido: [hecho de la clase, cadena de ES]}."""
    facts = [tuple(x.upper() for x in f) for f in facts]
    known = set(facts)
    parents: Dict[str, List[Triple]] = {}
    for f in facts:
        if f[1] == "ES":
            parents.setdefault(canon(f[0]), []).append(f)
    props: Dict[str, List[Triple]] = {}
    for f in facts:
        if f[1] != "ES":
            props.setdefault(canon(f[0]), []).append(f)
    derived: Dict[Triple, List[Triple]] = {}
    for member in {f[0] for f in facts if f[1] == "ES"}:
        stack, seen = [(canon(member), [])], {canon(member)}
        while stack:
            node, chain = stack.pop()
            for es in parents.get(node, []):
                cls = canon(es[2])
                if cls in seen:
                    continue
                seen.add(cls)
                path = chain + [es]
                for prop in props.get(cls, []):
                    new = (member, prop[1], prop[2])
                    if new not in known and new not in derived:
                        derived[new] = [prop] + path
                stack.append((cls, path))
    return derived


def compare(facts: Iterable[Triple]) -> Dict[Triple, List[Triple]]:
    """Comparaciones (parche-56): "Luis es mas alto que Pedro" = (LUIS, MAS_ALTO_QUE, PEDRO).
    Inversa (Pedro MENOS_ALTO_QUE Luis) y transitividad (Luis > Pedro > Juan => Luis > Juan)."""
    facts = [tuple(x.upper() for x in f) for f in facts]
    known = set(facts)
    pairs: Dict[str, Dict[tuple, List[Triple]]] = {}
    for f in facts:
        if f[1].startswith(("MAS_", "MENOS_")) and f[1].endswith("_QUE"):
            pairs.setdefault(f[1], {})[(f[0], f[2])] = [f]
    for p_, d in list(pairs.items()):
        kind, rest = p_.split("_", 1)
        inv = ("MENOS_" if kind == "MAS" else "MAS_") + rest
        for (a, b), sup in list(d.items()):
            pairs.setdefault(inv, {}).setdefault((b, a), sup)
    changed = True
    while changed:
        changed = False
        for p_, d in pairs.items():
            for (a, b), s1 in list(d.items()):
                for (c, e), s2 in list(d.items()):
                    if b == c and a != e and (a, e) not in d:
                        d[(a, e)] = [(a, p_, b), (b, p_, e)]
                        changed = True
    out: Dict[Triple, List[Triple]] = {}
    for p_, d in pairs.items():
        for (a, b), sup in d.items():
            if (a, p_, b) not in known:
                out[(a, p_, b)] = sup
    return out


def verb_derive(facts, verb_isa) -> Dict[Triple, List[Triple]]:
    """Verbos ensenados ("Cocinar es preparar comida"): si Pedro cocina pasta, tambien prepara pasta."""
    out: Dict[Triple, List[Triple]] = {}
    for f in facts:
        head, _, suf = f[1].partition("_")
        cur, seen = head.lower(), set()
        while cur in verb_isa and cur not in seen:
            seen.add(cur)
            cur = verb_isa[cur].lower()
            out.setdefault((f[0], cur.upper() + ("_" + suf if suf else ""), f[2]), [tuple(f)])
    return out


def deduce_all(facts: Iterable[Triple], lessons: Sequence[dict], is_var: Callable[[str], bool] = lambda n: True) -> Dict[Triple, List[Triple]]:
    facts = list(facts)
    out = apply_lessons(facts, lessons, is_var)
    for k, v in inherit(facts).items():
        out.setdefault(k, v)
    for k, v in compare(facts).items():
        out.setdefault(k, v)
    return out
