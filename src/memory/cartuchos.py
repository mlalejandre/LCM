"""CARTUCHOS de conocimiento (parche-91). Cada texto aprendido es un fichero propio en cartuchos/<nombre>.json (hechos + como se dijeron). La memoria que usa el
modelo se COMPONE al arrancar:  fabrica (semilla) + cartuchos activos (cartuchos/activos.json) + tu memoria personal. La memoria personal (memory/lcm_memory.json)
NUNCA contiene lo de los cartuchos (MemoryStore.save lo filtra), asi que retirar un cartucho no deja restos: se quita de la lista y listo.
Lo deducido se calcula al preguntar, de modo que tampoco queda nada deducido de un cartucho retirado."""
import copy
import json
import os
import time
from typing import Dict, List, Optional

DIR = "cartuchos"
SECCIONES = ("alias", "verb_isa", "defs", "surface", "display")


def _p(base: str, *a) -> str:
    return os.path.join(base, *a)


def activos(base: str = DIR) -> List[str]:
    try:
        return list(json.load(open(_p(base, "activos.json"), encoding="utf-8")))
    except (OSError, ValueError):
        return []


def _guardar_activos(lista: List[str], base: str) -> None:
    os.makedirs(base, exist_ok=True)
    json.dump(lista, open(_p(base, "activos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def insertar(nombre: str, base: str = DIR) -> bool:
    if not os.path.exists(_p(base, nombre + ".json")):
        return False
    a = activos(base)
    if nombre not in a:
        _guardar_activos(a + [nombre], base)
    return True


def retirar(nombre: str, base: str = DIR) -> bool:
    a = activos(base)
    if nombre not in a:
        return False
    _guardar_activos([x for x in a if x != nombre], base)
    return True


def cargar(nombre: str, base: str = DIR) -> Optional[dict]:
    try:
        return json.load(open(_p(base, nombre + ".json"), encoding="utf-8"))
    except (OSError, ValueError):
        return None


def listar(base: str = DIR):
    """[(nombre, activo, n_hechos, fuente)]"""
    act = set(activos(base))
    out = []
    if os.path.isdir(base):
        for f in sorted(os.listdir(base)):
            if f.endswith(".json") and f != "activos.json":
                c = cargar(f[:-5], base) or {}
                out.append((f[:-5], f[:-5] in act, len(c.get("hechos", [])) + len(c.get("nexos", [])) + len(c.get("reglas", [])), c.get("fuente", "")))
    return out


def borrar(nombre: str, base: str = DIR) -> bool:
    retirar(nombre, base)
    p = _p(base, nombre + ".json")
    if os.path.exists(p):
        os.remove(p)
        return True
    return False


# ---- compuesto en memoria -------------------------------------------------------------------
def _own(mem) -> Dict[str, dict]:
    if not hasattr(mem, "cart_own"):
        mem.cart_own = {}
    return mem.cart_own


def duenos(mem, seccion: str) -> set:
    """Claves de una seccion que pertenecen a algun cartucho montado (para no guardarlas en la memoria personal)."""
    out = set()
    for d in getattr(mem, "cart_own", {}).values():
        out |= set(d.get(seccion, []))
    return out


def _key(f: dict):
    return (f["s"], f["p"], f["o"], bool(f.get("neg")))


def _montar_uno(mem, nombre: str, c: dict) -> int:
    own = _own(mem)[nombre] = {s: [] for s in SECCIONES}
    own["opposites"] = []
    have = {_key(f) for f in mem.facts}
    n = 0
    for f in c.get("hechos", []):
        if _key(f) not in have:
            g = copy.deepcopy(f)
            g["cart"] = nombre
            mem.facts.append(g)
            n += 1
    if c.get("nexos"):                                                  # parche-111: los nexos (reflexion) viven APARTE de los hechos: el razonamiento y las preguntas no los ven
        if not hasattr(mem, "nexos"):
            mem.nexos = []
        for h in c["nexos"]:
            g = copy.deepcopy(h)
            g["cart"] = nombre
            mem.nexos.append(g)
            n += 1
    if c.get("reglas"):                                                 # parche-112: reglas de razonamiento (Horn) y propiedades de relacion, como datos
        if not hasattr(mem, "reglas"):
            mem.reglas = []
        ids = {r.get("id") for r in mem.reglas}
        for r in c["reglas"]:
            if r.get("id") not in ids:
                g = copy.deepcopy(r)
                g["cart"] = nombre
                mem.reglas.append(g)
                n += 1
    if c.get("propiedades"):
        if not hasattr(mem, "propiedades"):
            mem.propiedades = {}
        own["_prop"] = []
        for k, v in c["propiedades"].items():
            if k not in mem.propiedades:
                mem.propiedades[k] = v
                own["_prop"].append(k)
    for s in SECCIONES:
        d = getattr(mem, s)
        for k, v in c.get(s, {}).items():
            if k not in d:
                d[k] = v
                own[s].append(k)
    for pair in c.get("opposites", []):
        if list(pair) not in mem.opposites:
            mem.opposites.append(list(pair))
            own["opposites"].append(list(pair))
    return n


def desmontar(mem, nombre: str) -> int:
    own = getattr(mem, "cart_own", {}).pop(nombre, None)
    before = len(mem.facts)
    mem.facts = [f for f in mem.facts if f.get("cart") != nombre]
    if getattr(mem, "nexos", None):
        mem.nexos = [h for h in mem.nexos if h.get("cart") != nombre]
    if getattr(mem, "reglas", None):
        mem.reglas = [r for r in mem.reglas if r.get("cart") != nombre]
    if own:
        for k in own.get("_prop", []):
            getattr(mem, "propiedades", {}).pop(k, None)
        for s in SECCIONES:
            d = getattr(mem, s)
            for k in own.get(s, []):
                d.pop(k, None)
        mem.opposites = [p for p in mem.opposites if list(p) not in own.get("opposites", [])]
    return before - len(mem.facts)


def montar(mem, base: str = DIR, excluir: Optional[str] = None):
    """Quita lo montado antes y monta los cartuchos activos (menos `excluir`). -> [(nombre, hechos_anadidos | None si falta el fichero)]"""
    for nombre in list(getattr(mem, "cart_own", {})):
        desmontar(mem, nombre)
    res = []
    for nombre in activos(base):
        if nombre == excluir:
            continue
        c = cargar(nombre, base)
        res.append((nombre, _montar_uno(mem, nombre, c) if c else None))
    return res


# ---- crear un cartucho ----------------------------------------------------------------------
def instantanea(mem) -> dict:
    return {"facts": {_key(f) for f in mem.facts}, **{s: set(getattr(mem, s)) for s in SECCIONES}, "opposites": [list(p) for p in mem.opposites]}


def delta(mem, snap: dict) -> dict:
    d = {"hechos": [copy.deepcopy({k: v for k, v in f.items() if k != "cart"}) for f in mem.facts if _key(f) not in snap["facts"] and not f.get("cart")]}
    for s in SECCIONES:
        d[s] = {k: v for k, v in getattr(mem, s).items() if k not in snap[s]}
    d["opposites"] = [p for p in mem.opposites if list(p) not in snap["opposites"]]
    return d


def guardar_cartucho(nombre: str, contenido: dict, meta: Optional[dict] = None, base: str = DIR) -> str:
    os.makedirs(base, exist_ok=True)
    c = dict(contenido)
    c.update({"nombre": nombre, "creado": time.strftime("%Y-%m-%d %H:%M"), "version": 1})
    c.update(meta or {})
    p = _p(base, nombre + ".json")
    json.dump(c, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return p
