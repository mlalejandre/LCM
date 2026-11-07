"""Normalizador de PREGUNTAS (parche-90). Muchas formas de preguntar lo mismo se reducen a una forma canonica que el pipeline ya sabe contestar:
"Dime que compra Ana" / "¿Sabes donde vive Pedro?" / "¿Que es lo que compra Ana?" / "¿En que ciudad vive X?" / "¿De que trabaja X?" /
"¿Quien es el papa de X?" / "¿Cual es mi nombre?" / "5 x 6". Es reescritura determinista de la frase (no toca afirmaciones). Lo que se aprende aqui sirve
para todas las preguntas de la misma familia, con cualquier nombre."""
import re
from typing import Optional, Tuple

_V = {"a": "[aá]", "e": "[eé]", "i": "[ií]", "o": "[oó]", "u": "[uú]"}


def _a(s: str) -> str:
    return "".join(_V.get(c, c) for c in s)


_INT = r"((?:alrededor|cerca|lejos|detr[aá]s|delante|dentro|encima|debajo|junto) de (?:qu[eé]|qui[eé]n)|qu[eé]|qui[eé]nes|qui[eé]n|d[oó]nde|cu[aá]ndo|c[oó]mo|cu[aá]l(?:es)?|cu[aá]nt[oa]s?|por qu[eé]|en qu[eé]|a qu[eé]|de qu[eé]|con qu[eé]|para qu[eé])"
_PRE = re.compile(r"^(?:oye[, ]+)?(?:sabes|sabr[ií]as|expl[ií]came|cu[eé]ntame|me puedes decir|puedes decirme|podr[ií]as decirme|me dices|dime|dec[ií]me|por favor dime)\s+" + _INT + r"\b(.*)$", re.I)
_LOQUE = re.compile(r"^qu[eé] es (?:lo|el|la) que (.+)$", re.I)
_CIUDAD = re.compile(r"^(?:en )?qu[eé] (?:ciudad|pa[ií]s|lugar|sitio|pueblo|barrio|provincia|regi[oó]n|localidad) (vive|viv[ií]a|est[aá]|trabaja|estudia|naci[oó]|nace|duerme|reside) (.+)$", re.I)
_PROF = re.compile(r"^(?:a qu[eé] se dedica|de qu[eé] trabaja|en qu[eé] trabaja|cu[aá]l es la profesi[oó]n de|cu[aá]l es el trabajo de|qu[eé] profesi[oó]n tiene|qu[eé] hace de profesi[oó]n) (.+)$", re.I)
_DIME_DE = re.compile(r"^(?:qu[eé]\s+(?:me\s+)?(?:puedes|podr[ií]as|sabes|conoces|tienes)\s+(?:decir(?:me)?|contar(?:me)?|explicar(?:me)?|saber)\s+(?:de|sobre|acerca de)"
                      r"|(?:h[aá]blame|cu[eé]ntame|expl[ií]came|inf[oó]rmame|dime)\s+(?:algo\s+)?(?:de|sobre|acerca de)"
                      r"|qu[eé]\s+(?:sabes|conoces)\s+(?:sobre|acerca de)"
                      r"|qu[eé]\s+(?:informaci[oó]n|datos|cosas)\s+(?:tienes|conoces|sabes|hay)\s+(?:de|sobre|acerca de))\s+(.+)$", re.I)
_CARACT = re.compile(r"^(?:(?:cu[aá]les son|dime|dame|d[ií]melas|nombra)\s+)?(?:las |los )?(?:caracter[ií]sticas|propiedades|datos|detalles|rasgos)\s+(de la|de los|de las|del|de|sobre)\s+(.+)$"
                     r"|^(?:describe|descr[ií]beme|descr[ií]beles|dame (?:informaci[oó]n|datos|detalles)(?: (?:de|sobre|acerca de))?)\s+(?:a |el |la |los |las )?(.+)$", re.I)
_MODAL = re.compile(r"^(?:oye[, ]+|por favor[, ]+)?(?:puedes|podr[ií]as|podr[ií]a|sabr[ií]as|me puedes|me podr[ií]as|me haces el favor de)\s+"
                    r"(?:decirme|decir|contarme|contar|explicarme|explicar|indicarme|indicar|informarme|calcular|enumerar|nombrar|listar|mostrarme|mostrar|se[nñ]alarme|averiguar)\s+(si\s+)?(.+)$", re.I)
_VCUENTA = r"(?:cuenta(?:me)?|contar(?:me)?|dime|d[ií]me|dec[ií]me|calcula|averigua|dame|d[aá]me)"
_CUENTA = [re.compile(r"^" + _VCUENTA + r"\s+cu[aá]nt[oa]s\s+(?:(?:los|las)\s+)?(\w+)\s*(.*)$", re.I),
           re.compile(r"^(?:" + _VCUENTA + r"\s+)?(?:el n[uú]mero(?: total)? de|la cantidad(?: total)? de|el total de)\s+(?:(?:los|las)\s+)?(\w+)\s*(.*)$", re.I),
           re.compile(r"^(?:cuenta(?:me)?|contar(?:me)?)\s+(?:(?:los|las)\s+)?(\w+)\s*(.*)$", re.I)]
_WRAP = re.compile(r"^(oye[, ]+|por favor[, ]+|una pregunta[:, ]+|una duda[:, ]+|una cosa[:, ]+"
                   r"|(?:quisiera|quiero|necesito|me gustar[ií]a|me interesa)\s+saber\s+"
                   r"|(?:podr[ií]as decirme si|puedes decirme si|dime si|d[ií]me si|sabes si|me dices si|a ver si)\s+)(.+)$", re.I)
_IMPER = re.compile(r"^(?:dime|d[ií]me|nombra|enumera|lista|cita|menciona|mu[eé]strame|h[aá]blame|cu[eé]ntame|expl[ií]came|describe|descr[ií]beme|resume|dame|di)\b", re.I)
_INTRO = re.compile(r"^(qu[eé]|qui[eé]n|cu[aá]l|cu[aá]nt|d[oó]nde|c[oó]mo|por qu[eé]|es |son |tiene|est[aá]|gira|orbita)", re.I)
_ORDEN = re.compile(r"^(?:cuenta|cu[eé]ntame|dime|dame|d[ií]game|busca|buscame|explica|expl[ií]came|calcula|calc[uú]lame|repite|haz|hazme|pon|abre|muestra|mu[eé]strame|ens[eé][nñ]ame|ay[uú]dame|traduce|escribe|resume|res[uú]meme|reproduce|enciende|apaga)\b", re.I)


def es_orden(raw: str) -> bool:
    """parche-103: una orden ("Cuenta los planetas que existen") NO es un hecho y no se guarda en la memoria."""
    t = raw.strip()
    return bool(_ORDEN.match(t)) and not t.startswith("¿") and not t.endswith("?")


_VERBO_PRIMERO = re.compile(r"^(?:es|son|est[aá]|est[aá]n|tiene|tienen|posee|poseen|gira|giran|orbita|orbitan|contiene|contienen)\b\s+\S", re.I)
_SINSIGNO = re.compile(r"^(?:qu[eé]|qui[eé]n(?:es)?|cu[aá]l(?:es)?|cu[aá]nt[oa]s?|d[oó]nde|c[oó]mo|cu[aá]ndo|por qu[eé]|(?:de|en|a|con|para|alrededor de|cerca de|desde) qu[eé]|(?:de|en|a) qui[eé]n)\b", re.I)
_EXCLAM = re.compile(r"^(?:qu[eé]|c[oó]mo)\s+(?:bien|bueno|buena|mal|malo|alegr[ií]a|pena|l[aá]stima|bonito|bonita|guay|horror|rico|rica|susto|bien|pasada|locura|raro|extra[nñ]o|grande|genial|tarde|temprano|miedo|lindo|linda|asco|vergüenza|verg[uü]enza|fuerte)\b", re.I)
_DIME2 = re.compile(r"^(?:h[aá]blame|habla|cu[eé]ntame|expl[ií]came|inf[oó]rmame|dime|d[ií]game|resume|res[uú]meme|describe|descr[ií]beme)\s+(?:algo\s+|todo\s+|lo que sabes\s+|lo que conoces\s+)?(del|de la|de los|de las|de|sobre|acerca de|a)\s+(.+)$", re.I)
_PAPA = re.compile(r"^(qui[eé]n es (?:el|la)) (pap[aá]|mam[aá]) (de .+)$", re.I)
_NOMBRE = re.compile(r"^(?:cu[aá]l es mi nombre|c[oó]mo es mi nombre|qu[eé] nombre tengo|c[oó]mo se llama este usuario)$", re.I)
_ARIT = re.compile(r"^(\d+(?:[.,]\d+)?)\s*([x×*+\-−/÷:])\s*(\d+(?:[.,]\d+)?)\s*[=?]*$")
_QMAS = re.compile(r"^(?:qui[eé]n|cu[aá]l) es (m[aá]s|menos|mayor|menor) ?(\w+)?\s*[,:]?\s+(?:(?:el|la) )?(\w+) o (?:(?:el|la) )?(\w+)$", re.I)
_OPW = {"x": "por", "×": "por", "*": "por", "+": "más", "-": "menos", "−": "menos", "/": "entre", "÷": "entre", ":": "entre"}


def _strip(raw: str) -> str:
    return raw.strip().lstrip("¿¡").rstrip("?!. ").strip()


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


_POR_FAVOR = re.compile(r"\s*,?\s*por favor\s*,?", re.I)
_TAG = re.compile(r"^(.+?),?\s*¿(?:verdad|no|cierto|es as[ií]|a que s[ií]|eh|correcto)\s*\??$", re.I)
_VERDAD = re.compile(r"^(?:dime\s+si\s+)?(?:es\s+)?(?:verdad|cierto|correcto|seguro|as[ií])\s+que\s+(.+)$", re.I)
_QUE_ME = re.compile(r"^(?:necesito|quiero|quisiera|me gustar[ií]a|te pido|deseo)\s+que\s+me\s+(?:digas|expliques|cuentes|aclares|indiques|ense[nñ]es|muestres)\s+(?:si\s+)?(.+)$", re.I)
_DEFINE = re.compile(r"^(?:define|def[ií]neme|dame la definici[oó]n de|dime la definici[oó]n de|definici[oó]n de|cu[aá]l es la definici[oó]n de|qu[eé] significa|qu[eé] quiere decir|qu[eé] entiendes por|"
                     r"a qu[eé] llamamos|a qu[eé] se llama|qu[eé] es lo que llamamos|qu[eé] significa la palabra|qu[eé] quiere decir la palabra|qu[eé] se entiende por)\s+(?:(?:el|la|los|las|un|una)\s+)?(?:palabra\s+)?(.+)$", re.I)
_LISTA = re.compile(r"^(?:dame|dime|ens[eé][nñ]ame|mu[eé]strame|escribe|haz|hazme|necesito|quiero)\s+(?:una |la |el )?(?:lista|listado|nombres?)\s+de\s+((?:los|las)\s+.+)$"
                    r"|^(?:ens[eé][nñ]ame|mu[eé]strame|dime|nombra|enumera)\s+((?:los|las)\s+\w+(?: que (?:conoces|sabes|tienes|hay|existen))?)$"
                    r"|^c[oó]mo se llaman\s+((?:los|las)\s+.+)$|^cu[aá]les son los nombres de\s+((?:los|las)\s+.+)$|^dime el nombre de\s+((?:los|las)\s+.+)$", re.I)
_TODO = re.compile(r"^(?:y\s+)?(?:(?:dime|cu[eé]ntame|mu[eé]strame|ens[eé][nñ]ame|expl[ií]came|resume|dame)\s+)?(?:todo|todo lo que (?:sepas|sabes|conoces|tengas)|lo que (?:sabes|conoces|sepas)|qu[eé] m[aá]s sabes|qu[eé] m[aá]s conoces)\s*(?:de|del|de la|de los|de las|sobre|acerca de)\s+(.+)$", re.I)
_CONOCES = re.compile(r"^(?:conoces|has o[ií]do hablar de|has escuchado hablar de|sabes qui[eé]n es|sabes qu[eé] es|sabes algo de|sabes algo sobre|conoces a)\s+(?!alg[uú]n)(?:(?:el|la|los|las)\s+)?(?:planeta |estrella |sat[eé]lite )?(.+)$", re.I)
_COMPARA = re.compile(r"^(?:compara|compar[ae]me|cu[aá]l es la diferencia entre|diferencias? entre|qu[eé] diferencias? hay entre|en qu[eé] se parecen|en qu[eé] se diferencian|qu[eé] tienen en com[uú]n)\s+(.+?)\s+(?:y|con)\s+(.+)$", re.I)


def _generales(body: str, asked: bool):
    """parche-97: reescrituras de FORMA (no de contenido) que sirven para cualquier tema."""
    b = _POR_FAVOR.sub(" ", body).strip() if re.search(r"por favor", body, re.I) and not re.match(r"^por favor", body, re.I) else body
    m = _TAG.match(b)
    if m:
        return "¿" + _cap(m.group(1).strip().lstrip("¿")) + "?"
    m = _QUE_ME.match(b)
    if m:
        r = m.group(1).strip()
        return ("¿" + _cap(r) + "?") if _INTRO.match(r) else "¿" + _cap(r) + "?"
    m = _VERDAD.match(b)
    if m:
        return "¿" + _cap(m.group(1).strip()) + "?"
    m = _TODO.match(b)
    if m:
        return f"¿Qué sabes de {m.group(1).strip()}?"
    m = _DEFINE.match(b)
    if m:
        w = m.group(1).strip()
        if len(w.split()) <= 3 and not w[:1].isupper() and not re.match(r"^(el|la|los|las|un|una)\b", w, re.I):
            w = ("los " if w.lower().endswith("s") and len(w) > 3 else "el ") + w
        return f"¿Qué es {w}?"
    m = _LISTA.match(b)
    if m:
        g = next(x for x in m.groups() if x)
        return "¿Cuáles son " + re.sub(r"\bque (sabes|tienes)\b", "que conoces", g.strip()) + "?"
    m = re.match(r"^(?:dime|dame|d[ií]game|busca|cu[eé]ntame)?\s*(?:un |el |los |algun |alg[uú]n )?(?:sin[oó]nimos?|ant[oó]nimos?|otra palabra|otras palabras|palabras? (?:parecidas?|equivalentes?))\b.*$", b, re.I)
    if m:
        return "¿" + _cap(b) + "?"
    m = re.match(r"^qu[eé] (sin[oó]nimos?|ant[oó]nimos?) (?:tiene|hay para|existen para|conoces de|conoces para) (?:la palabra )?(\w+)$", b, re.I)
    if m:
        return f"¿Cuál es el {m.group(1).lower()} de {m.group(2)}?"
    m = _CONOCES.match(b)
    if m:
        return f"¿Qué sabes de {m.group(1).strip()}?"
    return None


def canonical(raw: str) -> str:
    """Devuelve la forma canonica de una pregunta, o `raw` sin tocar si no reconoce ninguna familia."""
    if not raw or len(raw) > 160:
        return raw
    body = _strip(raw)
    if re.search(r"\bpor favor\b", body, re.I) and not re.match(r"^por favor\b", body, re.I):
        body = _POR_FAVOR.sub(" ", body).strip()
        raw = ("¿" + _cap(body) + "?") if raw.strip().endswith("?") or raw.strip().startswith("¿") else body
    asked = raw.strip().endswith("?") or raw.strip().startswith("¿")
    mcar = re.match(r"^(?:dime|dame|d[ií]game|cu[eé]ntame|busca|mu[eé]strame|ens[eé][nñ]ame)\s+(?:las |los |algunas |unas |todas las )?(?:caracter\w*|propiedades|rasgos|datos|cosas)\s+(del|de la|de los|de las|de|sobre|acerca de)\s+(.+?)[?.!]*$", body, re.I)
    if mcar:                                                                  # parche-103: "Dime características de la Tierra" (aunque lleve errata)
        pr_ = mcar.group(1).lower()
        return "¿Qué sabes " + (pr_ if pr_.startswith("de") else "de") + " " + mcar.group(2).strip() + "?"
    _LOC = r"(?:sistema solar|universo|galaxia|v[ií]a l[aá]ctea|cosmos)"
    mlo = re.match(r"^[¿\s]*(?:en|dentro d(?:el|e)|d(?:el|e)) (?:el |la )?" + _LOC + r",?\s+(cu[aá]nt[oa]s \w+) (?:hay|existen|tiene|tienen|conoces|sabes)[?\s]*$", body, re.I) \
        or re.match(r"^[¿\s]*(cu[aá]nt[oa]s \w+) (?:tiene|tienen|posee|hay en|existen en|hay dentro d(?:el|e)|conoces d(?:el|e)) (?:el |la )?" + _LOC + r"[?\s]*$", body, re.I)
    if mlo:                                                                   # parche-104: "cuantos planetas tiene el sistema solar" / "en el sistema solar cuantos planetas hay"
        return "¿" + re.sub(r"^cu[aá]nt", "Cuánt", mlo.group(1), flags=re.I) + " hay?"
    mcu = re.match(r"^(?:puedes |podr[ií]as )?(?:contar|cuenta)\s+hasta\s+(\w+)[?.!]*$", body, re.I)
    if mcu:
        return "¿Cuenta hasta " + mcu.group(1) + "?"                          # parche-103: lo contesta Conversation._skills_pre
    if not asked and 3 <= len(body.split()) <= 16 and _SINSIGNO.match(body) and not _EXCLAM.match(body):
        return canonical("¿" + _cap(body) + "?")                              # parche-96: "que planeta tiene anillos" (sin signos)
    if not asked and _VERBO_PRIMERO.match(body) and raw.strip()[:1].islower() and not raw.strip().endswith((".", "!", ":", ";")) \
            and not re.search(r"\b(?:y|e|pero|que|porque|aunque|si)\b", body, re.I) and 4 <= len(body.split()) <= 12:
        return canonical("¿" + _cap(body) + "?")                              # parche-102: "es la tierra el tercer planeta" (minuscula, sin signos ni punto) es una pregunta, no un hecho
    body2 = re.sub(r"\balrededor de qui[eé]n\b", "alrededor de qué", body, flags=re.I)
    body2 = re.sub(r"^qu[eé] hay alrededor (de la|del|de los|de las|de)\s+(.+)$", r"Qué gira alrededor \1 \2", body2, flags=re.I)
    body2 = re.sub(r"\b(es|son) (el|la) mayor\b", r"\1 \2 más grande", body2, flags=re.I)
    body2 = re.sub(r"\b(es|son) (el|la) menor\b", r"\1 \2 más pequeño", body2, flags=re.I)
    body2 = re.sub(r"\b(el|la) (\w+) que (?:est[aá]|queda|se encuentra) m[aá]s (cerca|lejos) (de la|del|de) (.+)$",
                   lambda m_: f"{m_.group(1)} {m_.group(2)} más {'cercano' if m_.group(3).lower() == 'cerca' else 'lejano'} {'a la' if m_.group(4).lower() == 'de la' else 'al' if m_.group(4).lower() == 'del' else 'a'} {m_.group(5)}",
                   body2, flags=re.I)
    body2 = re.sub(r"^(?:qu[eé]|cu[aá]l) (\w+) es m[aá]s (\w+) que (?:los dem[aá]s|todos los dem[aá]s|los otros|el resto|todos)$", r"Cuál es el \1 más \2", body2, flags=re.I)
    body2 = re.sub(r"^(?:qu[eé]|cu[aá]l) (\w+) est[aá] m[aá]s (cerca|lejos|pr[oó]ximo|cercano|lejano) (de la|del|de|a la|al|a)\s+(.+)$",
                   lambda m_: f"Cuál es el {m_.group(1)} más {'cercano' if m_.group(2).lower() in ('cerca', 'cercano', 'próximo', 'proximo') else 'lejano'} {'a la' if m_.group(3).lower() in ('de la', 'a la') else 'al' if m_.group(3).lower() in ('del', 'al') else 'a'} {m_.group(4)}", body2, flags=re.I)
    body2 = re.sub(r"^(?:qu[eé]|cu[aá]l) (\w+) est[aá] al lado (de la|del|de)\s+(.+)$",
                   lambda m_: f"Cuál es el {m_.group(1)} más cercano {'a la' if m_.group(2).lower() == 'de la' else 'al' if m_.group(2).lower() == 'del' else 'a'} {m_.group(3)}", body2, flags=re.I)
    m_ = re.match(r"^(?:(?:dime|d[ií]me|sabes|me dices)\s+)?qu[eé] (?:tipo|clase|especie) de \w+ (?:es|son) (.+)$", body2, re.I)
    if m_:
        body2 = f"Qué es {m_.group(1)}"
    if body2 != body:
        return canonical("¿" + _cap(body2) + "?")
    g_ = _generales(body, asked)
    if g_:
        return canonical(g_) if g_ != raw else g_
    mod_ = _MODAL.match(body)                                                  # parche-97: "¿Puedes decirme...?", "¿Podrías contar...?" -> la orden directa
    if mod_ and mod_.group(2).strip():
        rest_ = mod_.group(2).strip().lstrip("¿ ").rstrip("? ")
        if mod_.group(1) or asked or _INTRO.match(rest_):
            return canonical("¿" + _cap(rest_) + "?")
        return canonical(_cap(rest_))
    for rx_ in _CUENTA:                                                        # parche-97: contar / numero de / cantidad de -> "¿Cuántos X hay?"
        mc_ = rx_.match(body)
        if mc_:
            noun, tail = mc_.group(1).lower(), mc_.group(2).strip()
            cu = "Cuántas" if noun.endswith("as") and not noun.endswith(("etas", "mas", "pas")) else "Cuántos"
            mt_ = re.match(r"^(?:que )?(tiene|tienen|posee|poseen) (.+)$", tail, re.I)
            if mt_:
                return f"¿{cu} {noun} {mt_.group(1)} {mt_.group(2)}?"
            if re.match(r"^(?:(?:que )?(?:existen|existe|hay|conoces|sabes|tienes|conocemos|conoce))?(?: (?:en|del|de la|de los|de las|dentro de) .*)?$", tail, re.I):
                return f"¿{cu} {noun} hay?"
    w_ = _WRAP.match(body)                                                     # parche-96: "Oye, ...", "Por favor, ...", "Quisiera saber ...", "Dime si ..."
    if w_ and w_.group(2).strip():
        rest_ = w_.group(2).strip().lstrip("¿ ").rstrip("? ")
        pre_ = w_.group(1).lower().strip(", :")
        if pre_ in ("oye", "por favor", "una pregunta", "una duda", "una cosa"):
            if asked or _INTRO.match(rest_):                                   # solo preguntas: las afirmaciones no se tocan
                return canonical("¿" + _cap(rest_) + "?")
            if _IMPER.match(rest_):
                return canonical(_cap(rest_))
        else:
            rest_ = re.sub(r"^si\s+", "", rest_, flags=re.I)
            return canonical("¿" + _cap(rest_) + "?")
    m = _ARIT.match(body)
    if m and (m.group(2) not in "-:" or re.search(r"\s" + re.escape(m.group(2)) + r"\s", body)):
        return f"¿Cuánto es {m.group(1)} {_OPW[m.group(2)]} {m.group(3)}?"
    m = re.match(r"^(?:dime|nombra|enumera|lista|cita|menciona|mu[eé]strame|d[ií]melos|di)\s+((?:los|las)\s+\w+.*)$", body, re.I)
    if m:
        return "¿Cuáles son " + re.sub(r"\bque (sabes|tienes)\b", "que conoces", m.group(1)) + "?"      # "sabes" lo capta el enrutador de capacidades
    m = _DIME2.match(body)                                                     # parche-96: "cuéntame algo del Sol", "habla de la Luna", "describe a Saturno", "resume lo que sabes del Sistema Solar"
    if m:
        pr = m.group(1).lower()
        return f"¿Qué sabes {pr if pr in ('del', 'de la', 'de los', 'de las') else 'de'} {m.group(2)}?"
    m = _DIME_DE.match(body)
    if m:
        return f"¿Qué sabes de {m.group(1)}?"
    m = _CARACT.match(body)                                                    # parche-95: "características de Marte", "describe Marte", "dame información de Marte"
    if m:
        prep, rest = (m.group(1) or "de"), (m.group(2) or m.group(3))
        prep = "de" if prep.lower() == "sobre" else prep.lower()
        return f"¿Qué sabes {prep} {rest}?" if m.group(2) else f"¿Qué sabes de {rest}?"
    m = _PRE.match(body)
    if m:
        word = m.group(1)
        accented = any(c in word.lower() for c in "áéíóú")
        if accented or asked:
            return canonical("¿" + _cap(word) + m.group(2).rstrip() + "?")
    m = _LOQUE.match(body)
    if m:
        return f"¿Qué {m.group(1)}?"
    m = _CIUDAD.match(body)
    if m:
        return f"¿Dónde {m.group(1)} {m.group(2)}?"
    m = _PROF.match(body)
    if m:
        return f"¿Qué es {m.group(1)}?"
    m = _PAPA.match(body)
    if m:
        return f"¿{_cap(m.group(1))} {'padre' if m.group(2).lower().startswith('pap') else 'madre'} {m.group(3)}?"
    if _NOMBRE.match(body):
        return "¿Cómo me llamo?"
    return raw


def quien_mas(raw: str) -> Optional[Tuple[str, str, str, str]]:
    """"¿Quien es mas alta, Ana o Luisa?" -> ("más", "alta", "Ana", "Luisa")."""
    m = _QMAS.match(_strip(raw))
    if not m:
        return None
    c_, adj = m.group(1).lower().replace("mas", "más"), m.group(2)
    if c_ == "mayor":
        c_, adj = "más", "grande"
    elif c_ == "menor":
        c_, adj = "más", "pequeño"
    if not adj:
        return None
    return c_, adj, m.group(3), m.group(4)


# ---- parche-95: tolerancia a erratas en preguntas ---------------------------------------------------------------
def _nrm(w: str) -> str:
    import unicodedata
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if unicodedata.category(c) != "Mn")


_VOC = None


def _vocab(mem=None):
    """Palabras conocidas: data/vocabulario.txt + todo lo que aparece en la memoria (sujetos, predicados, objetos, nombres a mostrar)."""
    global _VOC
    if _VOC is None:
        import os
        _VOC = set()
        f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "vocabulario.txt")
        try:
            for ln in open(f, encoding="utf-8"):
                ln = ln.strip()
                if ln and not ln.startswith("#"):
                    _VOC.add(_nrm(ln))
        except OSError:
            pass
    voc = set(_VOC)
    if mem is not None:
        for f_ in getattr(mem, "facts", []):
            for x in (f_["s"], f_["p"], f_["o"]):
                for w in str(x).split("_"):
                    voc.add(_nrm(w))
        for d in getattr(mem, "display", {}).values():
            for w in str(d).split():
                voc.add(_nrm(w))
    return voc


def _memwords(mem) -> set:
    out = set()
    for f_ in getattr(mem, "facts", []):
        for x in (f_["s"], f_["p"], f_["o"]):
            for w in str(x).split("_"):
                out.add(_nrm(w))
    return out


def _near(w: str, voc) -> list:
    """Candidatas a distancia 1 (sustitucion, insercion, borrado, trasposicion) con la misma letra inicial."""
    out = set()
    L = "abcdefghijklmnopqrstuvwxyzñ"
    for i in range(len(w) + 1):
        if i < len(w):
            out.add(w[:i] + w[i + 1:])
            for c in L:
                out.add(w[:i] + c + w[i + 1:])
        if i < len(w) - 1:
            out.add(w[:i] + w[i + 1] + w[i] + w[i + 2:])
        for c in L:
            out.add(w[:i] + c + w[i:])
    return sorted(c for c in out if c in voc and c != w and c[:1] == w[:1])


SUBS = []                                                                       # (palabra original, palabra usada) de la ultima correccion/sinonimo


def corregir(raw: str, mem=None) -> str:
    """Corrige erratas de UNA letra en palabras que no conoce, solo si hay una unica candidata conocida. Los nombres propios (con mayuscula) no se tocan."""
    voc = _vocab(mem)
    del SUBS[:]
    parts = re.split(r"([A-Za-zÁÉÍÓÚáéíóúñÑüÜ]+)", raw)
    changed = False
    for i in range(1, len(parts), 2):
        w = parts[i]
        n_ = _nrm(w)
        if len(n_) < 5 or n_ in voc or (w[:1].isupper() and i > 1) or _lex_conoce(n_):
            continue
        c = _near(n_, voc)
        if len(c) > 1 and mem is not None:                                      # empate ("plaeta": planeta/planta): gana la que esta en la memoria
            inmem = _memwords(mem)
            c2 = [x for x in c if x in inmem]
            if c2:
                c = c2
        if len(c) == 1:
            new = c[0]
            parts[i] = new.capitalize() if w[:1].isupper() else new
            SUBS.append((w, parts[i]))
            changed = True
    return "".join(parts) if changed else raw


def es_fallo(text: str) -> bool:
    t = _nrm(text or "").strip()
    return t.startswith(("no lo se", "no conozco", "no he entendido", "no se ", "creo que hablas", "creo que preguntas", "eso no me consta"))


def comparar(raw: str):
    """"Compara Marte y la Tierra" / "¿Qué diferencias hay entre A y B?" -> (A, B) para describir las dos."""
    m = _COMPARA.match(_strip(raw))
    if not m:
        return None
    return tuple(re.sub(r"^(?:el|la|los|las|un|una|unos|unas)\s+", "", x.strip(), flags=re.I) for x in (m.group(1), m.group(2)))


def seguimiento(raw: str, last_q: str, mem) -> Optional[str]:
    """"¿Y Venus?" tras "¿De que color es Marte?" -> "¿De que color es Venus?": sustituye la entidad de la pregunta anterior por la nueva."""
    m = re.match(r"^¿?\s*y\s+(?:(?:el|la|los|las)\s+)?(.+?)\s*\??$", raw.strip(), re.I)
    if not m or not last_q or len(m.group(1).split()) > 3:
        return None
    nuevo = m.group(1).strip()
    if re.match(r"^(qu[eé]|c[oó]mo|cu[aá]l|cu[aá]nt|d[oó]nde|por)", nuevo, re.I):
        return None
    lq = _strip(last_q)
    names = sorted({str(getattr(mem, "display", {}).get(f_["s"].upper(), f_["s"].replace("_", " "))) for f_ in getattr(mem, "facts", [])}, key=len, reverse=True)
    for nm in names:
        nm_ = re.sub(r"^(el|la|los|las)\s+", "", nm, flags=re.I)
        mm = re.search(r"\b" + re.escape(nm_) + r"\b", lq, re.I)
        if mm and nm_.lower() != nuevo.lower():
            art = re.match(r"(el|la|los|las)\s+", nm, re.I)
            pre = lq[:mm.start()]
            had_art = bool(re.search(r"\b(el|la|los|las)\s+$", pre, re.I))
            sub = (nuevo if not had_art or re.match(r"^(el|la|los|las)\b", nuevo, re.I) else (art.group(1) + " " + nuevo if art else nuevo))
            return "¿" + _cap(pre + sub + lq[mm.end():]) + "?"
    return None


def _lex_conoce(n_):
    try:
        from src.language import lexico
        return lexico.conoce(n_)
    except Exception:                                               # noqa
        return False


def sinonimizar(raw: str, mem=None) -> str:
    """parche-98: palabras que no conozco (ni la memoria ni el vocabulario) se cambian por un sinonimo del lexico que SI esta en la memoria, si es unico."""
    from src.language import lexico
    if not lexico.disponible() or mem is None:
        return raw
    subs0 = list(SUBS)
    base = {lexico.st(w) for w in _vocab(None)}
    memst = {lexico.st(w) for w in _memwords(mem)}
    parts = re.split(r"([A-Za-zÁÉÍÓÚáéíóúñÑüÜ]+)", raw)
    changed = False
    for i in range(1, len(parts), 2):
        w = parts[i]
        n_ = _nrm(w)
        if len(n_) < 5 or lexico.st(n_) in memst or lexico.st(n_) in base or (w[:1].isupper() and i > 1) or not lexico.conoce(n_):
            continue
        cands = {}
        for lem in lexico.sinonimos(n_):
            if " " not in lem and lexico.st(lem) in memst:
                cands.setdefault(lexico.st(lem), lem)
        if len(cands) == 1:
            new = next(iter(cands.values()))
            parts[i] = new.capitalize() if w[:1].isupper() else new
            SUBS.append((w, parts[i]))
            changed = True
    return "".join(parts) if changed else raw
