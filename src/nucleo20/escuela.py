"""LCM 2.16 · ESCUELA DE CONCEPTOS: entrenar leyendo cartillas.

Una cartilla es un texto en castellano llano, una idea por frase («La ballena es un mamífero que vive en el mar. Las tijeras sirven para cortar.»).
La escuela la lee y convierte cada frase que entiende en conocimiento de fábrica, en el mismo formato que conceptos_base.txt:
    python -m src.nucleo20.escuela src/nucleo20/cartillas/*.txt        -> escribe src/nucleo20/conceptos_aprendidos.txt
Es la misma forma de enseñar que en la charla («un zorb es un animal que vive en cuevas»), pero para todos los usuarios y de una vez.
Lo que no entiende no lo inventa: lo lista en el informe para reescribirlo. El informe da la tasa de aprendizaje (frases aprendidas / leídas).
"""
from __future__ import annotations

import os
import re
import sys

from . import conceptos as K
from . import morfo as M
from .morfo import sa

_ART = r"(?:un|una|unos|unas|el|la|los|las)"
_N = r"[a-záéíóúñü]+(?: de [a-záéíóúñü]+)?"
_AQUI = os.path.dirname(os.path.abspath(__file__))


def _sing(t):
    t = re.sub(rf"^{_ART}\s+", "", t.strip().lower())
    return " ".join(M.singular(w) if i == 0 else w for i, w in enumerate(t.split()))


def _inf(verbo):
    an = [a for a in M.analizar(verbo) if a[1] in ("pres", "inf")]
    return an[0][0] if an else None


def _lista(t):
    return [x.strip() for x in re.split(r"\s*,\s*|\s+y\s+|\s+e\s+|\s+o\s+", t) if x.strip()]


def lee_frase(f):
    """Una frase de cartilla -> lista de (sección, clave, valor) o [] si no se entiende."""
    t = re.sub(r"\s+", " ", f.strip().rstrip(".").strip())
    low = t.lower()
    out = []
    m = re.match(rf"^lo (?:contrario|opuesto) de (\w+) es (\w+)$", low) or re.match(rf"^(\w+) es lo (?:contrario|opuesto) de (\w+)$", low)
    if m:
        return [("contrarios", m.group(1), m.group(2))]
    m = re.match(rf"^({_ART} {_N}) (?:tambi[eé]n )?(?:sirven?|se usan?|se utilizan?) para (.+)$", low)
    if m:
        return [("funcion", _sing(m.group(1)), v) for v in re.split(r"\s*,\s*|\s+y\s+(?=\w+(?:ar|er|ir)(?:se)?\b)", m.group(2))]
    m = re.match(rf"^({_ART} {_N}) (?:est[aá]n? hech[oa]s? de|se hacen? (?:de|con)|suelen? ser de) (.+)$", low)
    if m:
        return [("material", _sing(m.group(1)), v) for v in _lista(m.group(2))]
    m = re.match(rf"^({_ART} {_N}) (?:suelen? estar|se guardan?|viven?|suelen? vivir|se encuentran?|crecen?) en (.+)$", low)
    if m:
        return [("lugar", _sing(m.group(1)), re.sub(rf"^{_ART}\s+", "", v)) for v in _lista(m.group(2))]
    m = re.match(rf"^({_ART} {_N}) (?:lo|la|los|las) usan? (.+)$", low)
    if m:
        return [("usuario", _sing(m.group(1)), _sing(v)) for v in _lista(m.group(2))]
    m = re.match(rf"^({_ART} {_N}) (?:es|son) (?:una |unas )?partes? de ({_ART} {_N})$", low)
    if m:
        return [("partes", _sing(m.group(2)), _sing(m.group(1)))]
    m = re.match(rf"^las partes de ({_ART} {_N}) son (.+)$", low) or re.match(rf"^({_ART} {_N}) tienen? (?:\w+ )?partes: (.+)$", low)
    if m:
        return [("partes", _sing(m.group(1)), ", ".join(re.sub(rf"^{_ART}\s+", "", x) for x in _lista(m.group(2))))]
    m = re.match(rf"^({_ART} {_N}(?:(?:, {_ART} {_N})* y {_ART} {_N})?) (es|son) (?:(un|una|unos|unas) )?({_N}?)(?: que (.+))?$", low)
    if m and (m.group(3) or (m.group(2) == "son" and m.group(4).split()[0].endswith("s") and K._kb_clase(sa(M.singular(m.group(4).split()[0]))))):
        m = re.match(rf"^({_ART} {_N}(?:(?:, {_ART} {_N})* y {_ART} {_N})?) (?:es|son) ((?:un|una|unos|unas) )?({_N}?)(?: que (.+))?$", low)
        clase = _sing(m.group(3))
        for x in _lista(m.group(1)):
            g = "/f" if x.split()[0] in ("una", "la", "las", "unas") and not _sing(x).endswith("a") else ("/m" if x.split()[0] in ("un", "el", "los", "unos") and _sing(x).endswith("a") else "")
            out.append(("taxonomia", clase, _sing(x) + g))
            if m.group(4):
                sub = lee_frase(f"{x} {m.group(4)}")
                out += [o for o in sub if o[0] != "taxonomia"]
        return out
    m = re.match(rf"^({_ART} {_N}) (no )?(\w+)\b ?(.*)$", low)
    if m:
        inf = _inf(m.group(3))
        if inf and (sa(inf) not in ("ser", "estar") or m.group(4)):
            return [("propiedades", _sing(m.group(1)), f"{'no ' if m.group(2) else ''}{inf} {m.group(4)}".strip())]
    return []


def lee_cartillas(rutas):
    """-> (entradas, informe). entradas: {sección: {clave: [valores]}}."""
    ent, leidas, no = {}, 0, []
    for r in rutas:
        for linea in open(r, encoding="utf-8"):
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            for f in re.split(r"(?<=\.)\s+", linea):
                if not f.strip():
                    continue
                leidas += 1
                res = lee_frase(f)
                if not res:
                    no.append((os.path.basename(r), f.strip()))
                for sec, k, v in res:
                    vs = ent.setdefault(sec, {}).setdefault(k, [])
                    if v not in vs:
                        vs.append(v)
    return ent, {"frases": leidas, "aprendidas": leidas - len(no), "no_entendidas": no}


def escribe(ent, rutas, destino=None):
    destino = destino or os.path.join(_AQUI, "conceptos_aprendidos.txt")
    L = ["# CONCEPTOS APRENDIDOS EN LA ESCUELA (generado por python -m src.nucleo20.escuela; no editar a mano: edita las cartillas)",
         "# Cartillas leídas: " + ", ".join(os.path.basename(r) for r in rutas), ""]
    orden = ["taxonomia", "contrarios", "propiedades", "partes", "funcion", "material", "lugar", "usuario"]
    for sec in orden:
        if sec not in ent:
            continue
        L.append(f"[{sec}]")
        for k, vs in ent[sec].items():
            if sec == "contrarios":
                L += [f"{k}/{v}" for v in vs]
            elif sec == "propiedades":
                L.append(f"{k}: " + "; ".join(vs))
            else:
                L.append(f"{k}: " + ", ".join(vs))
        L.append("")
    open(destino, "w", encoding="utf-8").write("\n".join(L))
    return destino


def main(argv):
    import glob
    rutas = sorted(x for a in (argv or [os.path.join(_AQUI, "cartillas", "*.txt")]) for x in glob.glob(a))
    if not rutas:
        print("No hay cartillas que leer.")
        return 1
    ent, inf = lee_cartillas(rutas)
    d = escribe(ent, rutas)
    n = sum(len(vs) for s in ent.values() for vs in s.values())
    print(f"Escuela: {len(rutas)} cartillas, {inf['frases']} frases leídas, {inf['aprendidas']} aprendidas ({100 * inf['aprendidas'] / max(1, inf['frases']):.1f} %), {n} datos nuevos -> {os.path.relpath(d)}")
    for r, f in inf["no_entendidas"]:
        print(f"  no entendida [{r}]: {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
