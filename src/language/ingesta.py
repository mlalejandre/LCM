"""Ingesta de TEXTOS (parche-91): lee un texto en lenguaje natural (p. ej. sobre el sistema solar), lo prepara frase a frase y lo pasa por la conversacion
real (la misma que usas en scripts.think: escuela, discurso con tema, correcciones, memoria). Despues se AUTOEXAMINA: por cada sujeto aprendido pregunta
"¿Qué sabes de X?" y comprueba que sus datos salen en la respuesta. Devuelve un informe de lo aprendido / no entendido / recordado.
No hay LLM: si una frase no se entiende, se dice cual es y por que familia fallan (para arreglarlas por familias en el siguiente parche)."""
import re
from typing import Dict, List, Tuple

from .lexicon import norm

CONECTORES = r"(?:adem[aá]s|asimismo|por otro lado|sin embargo|por eso|por ello|as[ií]|por lo tanto|en resumen|en consecuencia|adem[aá]s de eso|de hecho|entonces|igualmente|tambi[eé]n)"


def limpiar(frase: str) -> str:
    f = re.sub(r"\([^)]*\)", " ", frase)                                  # (aclaraciones entre parentesis)
    f = re.sub(r"\[[^\]]*\]|\bpag\.\s*\d+", " ", f)
    f = re.sub(r"\s*[—–]\s*[^—–]*?\s*[—–]\s*", ", ", f)                  # incisos entre rayas
    f = re.sub(r"^\s*" + CONECTORES + r"\s*,?\s+", "", f, flags=re.I)      # "Además, ..." -> "..."
    f = re.sub(r"\s+([.,;:!?])", r"\1", re.sub(r"\s+", " ", f)).strip(" ,;")
    if f and f[0].islower():
        f = f[0].upper() + f[1:]
    return f


def preparar(texto: str) -> Tuple[List[str], List[str]]:
    """-> (frases, titulos_ignorados). Una linea corta sin punto final es un titulo; '#' son comentarios."""
    frases, titulos = [], []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        if not re.search(r"[.!?:]$", linea) and len(linea.split()) <= 6:
            titulos.append(linea)
            continue
        for trozo in re.split(r"(?<=[.!?])\s+", linea):
            for parte in re.split(r";\s+", trozo):                         # "A es B; C es D." -> dos frases
                f = limpiar(parte)
                if len(f.split()) >= 2:
                    frases.append(f if re.search(r"[.!?]$", f) else f + ".")
    return frases, titulos


def clasificar(respuesta: str) -> str:
    r = norm(respuesta or "")
    if "no he entendido" in r or "puedes decirlo" in r or "frase mas simple" in r:
        return "no_entendida"
    if "entendido:" in r:
        return "aprendida"
    return "otra"


def leer(conv, mem, frases: List[str]) -> Dict:
    """Pasa las frases por la conversacion. Devuelve {aprendidas, no_entendidas, otras, hechos_nuevos}."""
    rep = {"aprendidas": [], "no_entendidas": [], "otras": [], "hechos_nuevos": []}
    for f in frases:
        antes = len(mem.facts)
        resp = conv.say(f)
        if getattr(conv.d, "pending", None):                              # en lectura por lotes no se puede contestar a preguntas de aclaracion
            conv.d.pending = None
            rep["otras"].append((f, "pregunta de aclaracion (conflicto con lo que ya sabia): " + resp[:120]))
        c = clasificar(resp)
        nuevos = [x for x in mem.facts[antes:] if not x.get("neg")]
        rep["hechos_nuevos"] += nuevos
        if c == "aprendida":
            rep["aprendidas"].append((f, resp))
        elif c == "no_entendida":
            rep["no_entendidas"].append((f, resp))
        else:
            rep["otras"].append((f, resp))
    return rep


def comprobar(conv, mem, hechos: List[dict]) -> Tuple[int, int, List[Tuple[str, str, str]]]:
    """Autoexamen de retencion: por sujeto, '¿Qué sabes de X?' debe nombrar cada objeto aprendido. -> (ok, total, fallos[(sujeto, objeto, respuesta)])"""
    por: Dict[str, List[str]] = {}
    for h in hechos:
        por.setdefault(h["s"], [])
        o_ = h["o"].split("_")[0] if h.get("p", "").startswith("SER_EL_") else h["o"]          # superlativos/ordinales: basta con que salga la clase ("planeta")
        if o_ not in por[h["s"]]:
            por[h["s"]].append(o_)
    ok = total = 0
    fallos = []
    for s, objs in por.items():
        disp = mem.display.get(s, s.lower())
        resp = norm(conv.say(f"¿Qué sabes de {disp}?"))
        for o in objs:
            total += 1
            od = norm(mem.display.get(o, o.lower()))
            if od and od in resp:
                ok += 1
            else:
                fallos.append((disp, od, resp[:100]))
    return ok, total, fallos


def informe(rep: Dict, titulos: List[str], chk: Tuple[int, int, list]) -> str:
    a, n_, o = len(rep["aprendidas"]), len(rep["no_entendidas"]), len(rep["otras"])
    tot = a + n_ + o
    L = [f"LECTURA: {tot} frases -> {a} aprendidas, {n_} no entendidas, {o} otras  ({a / max(tot, 1):.0%} entendido). Hechos nuevos: {len(rep['hechos_nuevos'])}."]
    if titulos:
        L.append("Títulos ignorados: " + " | ".join(titulos))
    ok, total, fallos = chk
    L.append(f"RETENCIÓN (¿Qué sabes de X?): {ok}/{total} = {ok / max(total, 1):.0%}")
    if rep["no_entendidas"]:
        L.append("\nFRASES NO ENTENDIDAS:")
        L += [f"  - {f}" for f, _ in rep["no_entendidas"]]
    if rep["otras"]:
        L.append("\nOTRAS RESPUESTAS:")
        L += [f"  - {f}  ->  {r[:110]}" for f, r in rep["otras"]]
    if fallos:
        L.append("\nDATOS APRENDIDOS QUE NO SALEN AL PREGUNTAR:")
        L += [f"  - {s}: falta «{o}»  (respuesta: {r!r})" for s, o, r in fallos]
    L.append("\nLO APRENDIDO:")
    seen = set()
    for h in rep["hechos_nuevos"]:
        k = (h["s"], h["p"], h["o"])
        if k not in seen:
            seen.add(k)
            L.append(f"  {h['s']} {h['p']} {h['o']}")
    return "\n".join(L)
