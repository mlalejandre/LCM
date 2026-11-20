"""LCM 2.16 · LEER UN TEXTO INSERTO.

Cuando la persona pega o dicta un texto de varias frases («Te voy a leer un texto. Ayer Clara fue al mercado…»), el LCM lo LEE frase a frase
con el mismo núcleo con que entiende la charla, llevando el hilo de la narración:
  · quién hace algo «con» alguien forma con él un grupo («fue con su abuelo» -> «compraron», «volvieron» son los dos)
  · los conectores («después», «luego», «al final») ordenan las frases, no son contenido
  · una frase que no se entiende no detiene la lectura: se guarda tal cual
Al preguntar, primero contesta el núcleo con lo que entendió. Si no puede, busca en el texto la frase que responde y la cita
(«En el texto pone: …»): nunca inventa, y dice de dónde lo saca.
"""
from __future__ import annotations

import re

from . import conceptos as K
from . import morfo as M
from .morfo import sa

_INTRO = re.compile(r"^\s*(?:(?:te|os)\s+(?:voy a leer|leo|cuento|voy a contar|paso|copio|pego)\b[^.:]*|(?:lee|leete|mira|escucha|atiende a|fijate en)(?:\s+(?:esto|este texto|este cuento|esta historia|bien))?"
                    r"|(?:este es|aqui va|ahi va|aqui tienes)\s+(?:el|un|mi)\s+(?:texto|cuento|relato)|texto|historia|cuento)\s*[.:]\s*", re.I)
_CONECTOR = re.compile(r"^(?:después|despues|luego|más tarde|mas tarde|entonces|al final|por último|por ultimo|finalmente|al rato|a continuación|a continuacion|"
                       r"primero|en primer lugar|además|ademas|más adelante|al poco rato|poco después|poco despues|y|pero)\s*,?\s+", re.I)
_VACIAS = set("""que quien quienes como cuando donde adonde cual cuales cuanto cuanta cuantos cuantas por para con sin de del al a en el la los las un una unos unas lo le les se su sus
mi mis tu tus y o e u es son era fue fueron esta estan estaba hay ha han he has habia hizo hace hacen ser estar tiene tienen tenia texto segun dice pone cuenta historia cuento
algun alguna algo mas muy tan eso esto ese esa este tambien no si ya""".split())


def frases(texto):
    t = re.sub(r"\s+", " ", (texto or "").strip())
    t = re.sub(r"[«»“”\"]", "", t)
    return [p.strip() for p in re.split(r"(?<=[.!…])\s+(?=[¿¡A-ZÁÉÍÓÚÑ])", t) if p.strip()]


def es_texto(texto):
    if not texto or "?" in texto:
        return False
    m = _INTRO.match(sa(texto) + " ")
    fs = frases(texto)
    return m is not None and len(fs) >= 2


def _raiz(w):
    w = sa(w.lower())
    w = sa(M.singular(w)) if len(w) > 3 else w
    return w[:5] if len(w) > 5 else w


def _contenido(texto):
    return [w for w in re.findall(r"[a-zñ0-9]+", sa(texto.lower())) if w not in _VACIAS and len(w) > 1]


def leer(nuc, texto):
    """Lee el texto frase a frase. Devuelve la respuesta (dict)."""
    fs = frases(texto)
    m = _INTRO.match(sa(fs[0]) + " ") if fs else None
    if m:
        resto = fs[0][m.end():].strip()
        if resto:
            fs[0] = resto[:1].upper() + resto[1:]
        elif len(fs) > 1:
            fs = fs[1:]
    from . import coloquial
    fs2 = []
    for f in fs:                                        # dos hechos en una frase -> dos frases, para llevar bien el hilo de cada una
        g = coloquial._parte_narracion(f)
        fs2 += frases(g) if g != f else [f]
    orig, fs = fs, fs2
    entendidas, sueltas = 0, []
    tema = None
    from . import exposicion as X
    hilo, fresco, tema_de = X.Hilo(), False, {}
    nuc._leyendo = True
    try:
        for k, f in enumerate(fs):
            f2 = _CONECTOR.sub("", f, count=1)
            f2 = f2[:1].upper() + f2[1:]
            try:                                        # 2.19: los términos de varias palabras, como una pieza
                from . import compuestos as _C
                _C.aprende_propios(nuc, f2)
                f2 = _C.codifica(nuc, f2)
            except Exception:                           # noqa
                pass
            n0 = len(nuc.F)
            # 2.18: frase que EXPLICA (sujeto genérico, definición, regla, «algunos…») -> camino expositivo
            sn_x, _ = X.sujeto(f2)
            w_ini = f2.split()[0] if f2.split() else ""
            sin_suj = sn_x is None and (X._fin3(w_ini) or w_ini in ("Su", "Sus", "Es", "Son", "Está", "Están")) and w_ini != "Hay"
            expositiva = (sn_x is not None and re.fullmatch(X._DET, sa(sn_x.split()[0].lower())) is not None) \
                or (fresco and re.match(r"^(?:Allí|Ahí|Allá),?\s", f2) is not None) or re.match(r"^(?:Algun[oa]s|Cuando|Si|Siempre que|A los|A las|Al|Después de|Antes de|En (?:un|una|el|la|los|las) [a-záéíóúñü]+ hay|Hay)\b", f2) is not None \
                or (sin_suj and fresco and hilo.ult is not None) or (fresco and re.search(r"\bse llaman?\b", f2) is not None) or re.search(r",\s+(?:y\s+)?por eso\b", f2) is not None \
                or (re.match(r"^Por (?:eso|ello|esa razón|ese motivo)\b", f2) is not None and bool(hilo.previa)) \
                or (sn_x is not None and re.search(r"\b(?:es|son|fue|era|fueron)\s+(?:el|la|los|las)\s+(?:únic[oa]s?|primer[oa]?s?|últim[oa]s?|[a-záéíóúñü]+\s+(?:más|menos)\s+[a-záéíóúñü]+)\b", f2) is not None) \
                or (sn_x is not None and len(sn_x.split()) == 1 and sn_x[:1].isupper() and sa(sn_x.lower()) in _C.tabla(nuc))
            if expositiva:
                if sn_x is None and hilo.ult and sin_suj and w_ini not in ("Su", "Sus"):
                    tema_de[f] = hilo.para("p" if X._fin3(w_ini) == "p" or w_ini in ("Son", "Están") else "s") or hilo.ult
                try:
                    nf, nx, f1 = X.procesa(nuc, f2, hilo)
                except Exception:                       # noqa
                    nf, nx, f1 = 0, 0, None
                fresco = True
                if nf or nx:
                    entendidas += 1
                    for fr in nuc.F[n0:]:
                        fr.setdefault("leido", True)
                    s0 = next((fr.get("s") for fr in nuc.F[n0:] if fr.get("s") and fr["s"] not in ("U", "L")), None)
                    if s0 and sn_x:
                        tema = nuc.can(s0)
                else:
                    sueltas.append(f)
                nuc.pend = None
                continue
            fresco = False
            hilo.previa = f2
            if sn_x:
                hilo.pon(sn_x)
            w0 = f2.split()[0] if f2.split() else ""
            f3 = re.sub(rf"^{coloquial._T_NARR}\s+", "", f2, flags=re.I)        # «Los lunes lleva…»: el verbo va tras el complemento de tiempo
            w0 = f3.split()[0] if f3.split() else w0
            if tema and any(x[1] in ("pres", "pret", "imp", "fut") and x[2] == "3s" and x[0] not in ("ser", "estar", "parecer", "llamar") for x in M.analizar(w0)) \
                    and not K._kb_clase(sa(w0.lower())):
                try:                                    # frase sin sujeto: sigue hablando del tema del texto, no de lo último nombrado
                    nuc.mencionar(tema); nuc.ult_suj = tema
                except Exception:                       # noqa
                    pass
            try:
                r = nuc._procesar_charla(f2)
            except Exception:                           # noqa: una frase rara no detiene la lectura
                r = None
            if isinstance(r, dict) and r.get("estado") == "ok" and len(nuc.F) > n0:
                entendidas += 1
                for fr in nuc.F[n0:]:
                    fr.setdefault("leido", True)
                s0 = next((fr.get("s") for fr in nuc.F[n0:] if fr.get("s") and fr["s"] not in ("U", "L")), None)
                if s0 and not any(x[1] in ("pres", "pret", "imp", "fut") for x in M.analizar(w0)):
                    tema = nuc.can(s0)                  # sujeto explícito: es el tema hasta que se nombre otro
            else:
                sueltas.append(f)
            nuc.pend = None
    finally:
        nuc._leyendo = False
    try:                                                # un texto NARRADO también es una secuencia: sus frases van por orden (una explicación, no)
        from . import secuencias
        if len(tema_de) + sum(1 for g in fs if X.sujeto(g)[0] and re.fullmatch(X._DET, sa(X.sujeto(g)[0].split()[0].lower()))) < len(fs) / 2:
            secuencias.registrar(nuc, None, pasos=list(fs), silencioso=True)
    except Exception:                                   # noqa
        pass
    leidos = nuc.usuario.setdefault("leido", [])
    leidos.append({"turno": nuc.turno, "frases": orig, "temas": tema_de})
    del leidos[:-12]
    nuc.turno += 1
    nuc.ult_just = {"dicho": fs[:2]}
    fs = orig
    txt = f"He leído el texto ({len(fs)} frases)."
    if sueltas and entendidas:
        txt += f" He entendido bien {entendidas}; {'la otra la guardo' if len(sueltas) == 1 else 'las otras ' + str(len(sueltas)) + ' las guardo'} tal como está{'' if len(sueltas) == 1 else 'n'} escrita{'' if len(sueltas) == 1 else 's'}."
    elif sueltas:
        txt += " Lo guardo tal como está escrito."
    txt += " Pregúntame lo que quieras sobre él."
    return {"respuesta": txt, "estado": "ok", "consultar": False, "tipo": "ack"}


def cita(nuc, pregunta):
    """Frase del último texto leído que contesta a la pregunta, o None. Solo si casa de verdad con lo que se pregunta."""
    leidos = nuc.usuario.get("leido") or []
    if not leidos or "?" not in pregunta:
        return None
    try:
        from . import compuestos as _C
        pregunta = _C.decodifica(nuc, pregunta)          # las frases guardadas están como se escribieron
    except Exception:                                    # noqa
        pass
    q = sa(pregunta.lower())
    cont = _contenido(pregunta)
    if not cont:
        return None
    raices = {_raiz(w) for w in cont}
    mejor = None
    for texto in reversed(leidos):
        fs_ = texto["frases"]
        tema = {_raiz(w) for w in _contenido(" ".join(fs_[0].split()[:4]))} if fs_ else set()   # de quién o de qué trata: está en todas las frases aunque no se repita
        if re.match(r"^\W*(?:y\s+)?como (?:es|son|era|eran)\b", q) and (raices & tema or len(raices) == 0):
            desc = [g for g in fs_ if re.match(r"^(?:es|son|era|eran)\b", sa(g.lower())) or re.search(r"\b(?:es|son|era|eran) (?:muy |bastante |un poco )?[a-zñ]+(?:o|a|e|os|as|es|l|z|r)(?: y | pero |[.,]|$)", sa(g.lower()))]
            if desc:
                return f"En el texto pone: «{desc[-1].rstrip('.')}»."
        temas_f = texto.get("temas") or {}
        cuenta = {}
        for g in fs_:
            for w in {_raiz(w) for w in _contenido(g)}:
                cuenta[w] = cuenta.get(w, 0) + 1
        fondo = {w for w, c in cuenta.items() if c >= 3}   # de lo que trata todo el texto: no hace falta que cada frase lo repita
        for i, f in enumerate(fs_):
            rf = {_raiz(w) for w in _contenido(f)}
            tema_i = ({_raiz(w) for w in _contenido(temas_f[f])} if f in temas_f else set()) | tema
            comunes = raices & rf
            n = sum(0.4 if w in tema else 1.0 for w in comunes) + (0.4 * len((raices & tema_i) - rf) if i > 0 and comunes - tema else 0)
            if f in temas_f and (raices & tema_i) - rf:
                n += 0.5                                 # la frase habla (sin nombrarlo) de aquello por lo que se pregunta
            if not _responde(q, f, raices, rf | tema_i | (fondo if len(raices - fondo) >= 1 else set())):
                continue
            if comunes and (mejor is None or n > mejor[0] + 1e-9):
                mejor = (n, i, f, fs_, len(comunes | (raices & tema_i)), temas_f.get(f))
        if mejor:
            break
    if not mejor:
        return None
    _, i, f, fs, n, tema_f = mejor
    intro = "En el texto pone" + (f", hablando de {tema_f[:1].lower() + tema_f[1:] if not any(w[:1].isupper() for w in tema_f.split()[1:]) else tema_f}" if tema_f else "")
    intro = re.sub(r"\bde el\b", "del", intro)
    si_no = not re.match(r"^\W*(?:y\s+)?(?:que|quien|quienes|como|cuando|donde|adonde|cual|cuales|cuant|por que|para que|con que|con quien|a quien|de que|de quien|a que|en que)", q)
    if si_no:
        if n == len(raices) and n >= 2:
            neg = re.search(r"\b(?:no|nunca|jamas|tampoco)\b", sa(f.lower()))
            return f"{'No' if neg else 'Sí'}: el texto dice «{f.rstrip('.')}»."
        return None
    if n < max(1, (len(raices) + 1) // 2):
        return None
    if re.match(r"^\W*(?:y\s+)?por que", q):
        cands = [f] + [g for g in fs if g is not f]
        for g in cands[:1] + [g for g in cands[1:] if raices & {_raiz(w) for w in _contenido(g)}]:
            m = re.search(r"\b(?:porque|ya que|pues|puesto que|debido a que)\s+(.+?)[.!]?$", g, re.I)
            if m:
                return f"Porque {m.group(1).rstrip('.')}. Lo dice el texto: «{g.rstrip('.')}»."
        return None
    return f"{intro}: «{f.rstrip('.')}»."


_GEN_Q = {"pasa", "pasan", "ocurr", "suced", "hace", "hacen", "llama", "llam", "sirve", "sirv", "tipo", "tipos", "clase", "parte", "puede", "pued", "suele", "cosa", "cosas", "forma", "manera", "sitio", "lugar", "epoca", "momen",
          "perso", "gente", "anima", "objet"}
_NUM_RE = re.compile(r"\b(?:\d+|unos|unas|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|dieci\w+|veint\w+|treinta|cuarenta|cincuenta|sesenta|setenta|ochenta|noventa|cien\w*|mil|"
                     r"millon\w*|medio|media|vari[oa]s|much[oa]s|poc[oa]s|un par|docena|cientos|miles)\b")


def _responde(q, f, raices, cubre):
    """¿Puede esta frase CONTESTAR a la pregunta? Tiene que hablar de todo lo que se pregunta y traer el tipo de dato que se pide."""
    fs = sa(f.lower())
    lem_f = set()
    for w in re.findall(r"[a-záéíóúñü]+", f.lower()):
        try:
            lem_f |= {a_[0] for a_ in (M.analizar(w) or [])}
        except Exception:                                # noqa
            pass
    def _por_lema(r):
        for w in re.findall(r"[a-záéíóúñü]+", q):
            if _raiz(w) == r:
                try:
                    if {a_[0] for a_ in (M.analizar(w) or [])} & lem_f:
                        return True
                except Exception:                        # noqa
                    pass
        return False
    falta = {r for r in raices if r not in cubre and r not in _GEN_Q and not _por_lema(r)}
    if falta and (len(raices) < 4 or len(falta) > 1):
        return False
    if falta and any(r[:1].isdigit() for r in falta):
        return False
    mq = re.match(r"^\W*(?:y\s+)?(?:con |de |en |a )?cuant[oa]s?\s*([a-zñ]*)", q)
    if mq:
        nom = _raiz(mq.group(1)) if mq.group(1) else ""
        if not (_NUM_RE.search(fs) or (nom and re.search(r"\b(?:un|una)\s+" + re.escape(nom[:4]), fs))):
            return False
        if re.match(r"^\W*(?:y\s+)?(?:con |de |en |a )?cuant[oa]s\s+[a-zñ]+", q) and nom and len(nom) >= 4:
            # «¿cuántas abejas…?» no lo contesta «tres tipos de abejas»: el número tiene que contar esa misma cosa
            cuenta_n = [m_.group(1) for m_ in re.finditer(_NUM_RE.pattern + r"\s+(?:y\s+\w+\s+)?(?:de\s+)?([a-zñ]+)", fs)] + re.findall(r"\b(?:un|una)\s+([a-zñ]+)", fs)
            if cuenta_n and not any(_raiz(c)[:4] == nom[:4] for c in cuenta_n):
                return False
    ms = re.match(r"^\W*(?:y\s+)?(?:cuanto|cuanta|cuantos|cuantas|que|como)\s+[a-zñ]+\s+(?:el|la|los|las)\s+([a-zñ]+)$", q.strip(" ?¿"))
    if ms and re.match(r"^(?:en|sobre|desde|para|con)\s+(?:el|la|los|las)\s+" + re.escape(ms.group(1)[:4]), fs):
        return False                                     # lo preguntado es el sujeto; en la frase solo es el lugar
    if re.match(r"^\W*(?:y\s+)?(?:donde|adonde|por donde|de donde|en que (?:sitio|lugar|isla|pais|ciudad))\b", q) \
            and not re.search(r"\b(?:en|sobre|bajo|debajo|encima|junto|cerca|lejos|dentro|fuera|entre|por|desde|hasta|hacia|al|a la|a los|de)\b", fs):
        return False
    if re.match(r"^\W*(?:y\s+)?(?:cuando|en que (?:epoca|momento|año|mes|estacion))\b", q) \
            and not re.search(r"\b(?:cuando|si|despues|antes|durante|mientras|en (?:otoño|otono|invierno|verano|primavera|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|\d{3,4})|"
                              r"de \d{3,4}|\d{3,4}|siempre|nunca|cada|al [a-z]+r(?:se)?|lunes|martes|miercoles|jueves|viernes|sabado|domingo|mañana|tarde|noche|ayer|hoy|año|años|siglo|mes|meses|semana|semanas|dia|dias|hora|horas|verano|invierno|otoño|otono|primavera|proximo|proxima|pasado|pasada|navidad|temporada|epoca)\b", fs):
        return False
    if re.match(r"^\W*(?:y\s+)?para que\b", q) and not re.search(r"\bpara\b", fs):
        return False
    if re.match(r"^\W*(?:y\s+)?(?:de que color|que color)\b", q):
        return bool(re.search(r"\b(?:color|roj|verd|azul|amarill|negr|blanc|marron|gris|naranja|rosa|morad|dorad|platead)", fs))
    return True
