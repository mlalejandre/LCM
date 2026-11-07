"""parche-118: ANCLAJE DE CONCEPTOS. Lo que se lee solo sirve si cada concepto se apoya en lo que el modelo ya sabe:
 - entidad: nombre propio (Gokū, Akira Toriyama);
 - conocido: el diccionario de conceptos o la memoria ya lo conocen (con su cadena de clases: león > felino > mamífero);
 - nuevo: no lo conoce; si el texto lo clasifica (X es un Y) queda definido por esa clase; si no, queda como provisional.
Sin vocabulario de ningun campo: todo sale del diccionario y de la memoria."""
from __future__ import annotations

from typing import Dict, List, Optional

_SEP = ("_DE_", "_CON_", "_SIN_", "_EN_", "_PARA_", "_POR_")


def _nucleo(clave: str) -> str:
    k = clave
    for sep in _SEP:
        if sep in k:
            k = k.split(sep)[0]
    return k


def _palabra(clave: str) -> str:
    return _nucleo(clave).replace("_", " ").lower()


class Anclaje:
    MIN_AJUSTE = 0.0          # sin calibrar: con 0 no se marca nada como «dudoso» (medido: la puntuación sola no separa los casos mal anclados)

    def __init__(self, mem):
        self.mem = mem
        try:
            from src.language import conceptos
            self.dic = conceptos if conceptos.disponible() else None
        except Exception:                                                              # noqa
            self.dic = None
        self._cache: Dict[str, dict] = {}

    def _en_memoria(self, clave: str, antes: int) -> bool:
        n = 0
        for f in self.mem.facts[:antes]:
            if f["s"] == clave or f["o"] == clave:
                n += 1
        return n > 0

    def sentido(self, clave: str, contexto: List[str]):
        """Elige el sentido del diccionario que mejor encaja con los demás conceptos de las frases donde aparece (parecido de rasgos).
        Devuelve (concepto, puntuación) o None. La puntuación baja indica que ningún sentido del diccionario encaja con el texto."""
        cs = self.dic.conceptos(_palabra(clave))[:6]
        if not cs:
            return None
        ctxs = []
        for w in contexto[:8]:
            z = self.dic.conceptos(w)[:3]
            if z:
                ctxs.append(z)
        if not ctxs:
            return cs[0], None
        mejor = None
        for i, c in enumerate(cs):
            m = sum(max(self.dic.coseno(c, x) for x in z) for z in ctxs) / len(ctxs)
            sc = m + 0.06 / (i + 1)
            if mejor is None or sc > mejor[0]:
                mejor = (sc, c, m)
        return mejor[1], mejor[2]

    def estado(self, clave: str, propio: bool = False, antes: Optional[int] = None, contexto: Optional[List[str]] = None) -> dict:
        """{'estado': entidad|conocido|dudoso|nuevo, 'clase': [...], 'fuente': diccionario|memoria|texto}"""
        if clave in self._cache:
            return self._cache[clave]
        antes = len(self.mem.facts) if antes is None else antes
        r = {"estado": "nuevo", "clase": [], "fuente": "texto"}
        if propio:
            r = {"estado": "entidad", "clase": [], "fuente": "texto"}
        elif self.dic is not None:
            try:
                got = self.sentido(clave, contexto or [])
                if got:
                    c, pt = got
                    r = {"estado": "conocido", "clase": list(self.dic.cadena(c))[:4], "fuente": "diccionario", "ajuste": None if pt is None else round(pt, 3)}
                    if self.MIN_AJUSTE and pt is not None and pt < self.MIN_AJUSTE and len(contexto or []) >= 2 and _nucleo(clave) == clave:
                        r["estado"] = "dudoso"                                          # ningún sentido del diccionario encaja con el texto
            except Exception:                                                          # noqa
                pass
        if r["estado"] == "nuevo" and self._en_memoria(clave, antes):
            r = {"estado": "conocido", "clase": [], "fuente": "memoria"}
        self._cache[clave] = r
        return r


def anclar(mem, hechos: List[dict], antes: int) -> dict:
    """Estado de cada concepto que aparece en los hechos leidos. `antes` = nº de hechos en memoria antes de leer (lo que ya se sabia)."""
    a = Anclaje(mem)
    conc: Dict[str, dict] = {}
    clasificado = {h["s"] for h in hechos if h["p"] == "ES"}
    propios = {h["s"] for h in hechos if h.get("sd", "")[:1].isupper() and h["s"].replace("_", " ").title() == h.get("sd", "")}
    propios |= {h["o"] for h in hechos if h.get("od", "")[:1].isupper() and h["o"].replace("_", " ").title() == h.get("od", "")}
    por_frase: Dict[str, set] = {}
    for h in hechos:
        por_frase.setdefault(h["frase"], set()).update(k for k in (h["s"], h["o"]) if k not in ("_", ""))
    ctx: Dict[str, Dict[str, int]] = {}
    for ks in por_frase.values():
        for k in ks:
            for j in ks:
                if j != k and _nucleo(j) != _nucleo(k):
                    w = _palabra(j)
                    ctx.setdefault(k, {})[w] = ctx.setdefault(k, {}).get(w, 0) + 1
    for h in hechos:
        for k in (h["s"], h["o"]):
            if k in conc or k in ("_", ""):
                continue
            pal = sorted(ctx.get(k, {}), key=lambda w: -ctx[k][w])
            e = dict(a.estado(k, k in propios, antes, [w for w in pal if " " not in w or True]))
            if e["estado"] == "nuevo":
                e["definido"] = k in clasificado
            conc[k] = e
    cuenta = {"entidad": 0, "conocido": 0, "dudoso": 0, "nuevo": 0}
    for e in conc.values():
        cuenta[e["estado"]] += 1
    return {"conceptos": conc, "cuenta": cuenta}
