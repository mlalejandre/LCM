"""LCM 2.0 · trato conversacional: emociones, charla sobre el propio LCM, peticiones de explicación.

Regla de honestidad: el LCM no finge cuerpo, gustos ni opiniones. Contesta con lo que es
(un modelo conceptual) y devuelve la conversación a lo que la persona le ha contado.
"""
from __future__ import annotations

import re

from .morfo import sa
from . import morfo as M

NEGATIVAS = {"triste", "mal", "fatal", "cansado", "agotado", "enfadado", "nervioso", "preocupado", "aburrido", "enfermo", "solo", "estresado", "asustado", "agobiado", "deprimido", "harto",
             "regular", "malo", "decepcionado", "frustrado", "molesto", "angustiado", "desanimado", "hundido", "disgustado", "inquieto", "confundido", "perdido", "dolido", "furioso", "celoso"}
POSITIVAS = {"contento", "feliz", "bien", "genial", "alegre", "emocionado", "ilusionado", "tranquilo", "animado", "orgulloso", "encantado", "estupendamente", "fenomenal", "estupendo",
             "relajado", "satisfecho", "entusiasmado", "agradecido", "motivado", "enamorado", "descansado", "mejor"}
_BACK = re.compile(r"^(?:ah |pues |bueno |ya |si |oh |uy |anda |jo |mmm |hmm )*(vale|ok|okay|okey|de acuerdo|perfecto|genial|estupendo|muy bien|bien|claro|entiendo|ya veo|entendido|fenomenal|guay|que bien|"
                   r"ya|aja|mmm|hmm|bueno|exacto|eso es|correcto|cierto|asi es|estupendamente|comprendo|lo entiendo|me parece bien|esta bien|que interesante|interesante|que curioso|curioso|anda|"
                   r"vaya|oh|ah|uy|jo|increible|que guay|mola|como mola|me alegro|que bueno)(?:[ ,]+(?:vale|ok|perfecto|genial|estupendo|muy bien|bien|claro|entiendo|entendido|gracias|pues|entonces|ya|eh|lcm|de acuerdo))*$")
_RISA = re.compile(r"^(?:(?:ja|je|ji|jo){2,}|jaja\w*|jeje\w*|que risa|que gracioso|que bueno|lol|xd+)(?: .{0,20})?$")
_CUMPLIDO = re.compile(r"\b(?:eres|estas|pareces|me pareces)\b.*\b(listo|inteligente|majo|simpatico|genial|bueno|amable|increible|fantastico|un crack|estupendo|util|rapido|educado|gracioso|divertido|el mejor)\b|"
                       r"^(?:muy )?(?:buen trabajo|bien hecho|bien dicho|buena respuesta|muy bien dicho|lo has hecho (?:muy )?bien|que listo eres|asi me gusta|me caes (?:muy )?bien|te quiero|me gustas|eres un sol)$|"
                       r"\bme gusta (?:mucho )?(?:hablar|charlar|conversar) contigo\b")
_INSULTO = re.compile(r"\b(?:eres|pareces)\b.*\b(tonto|idiota|estupido|inutil|malo|pesado|lento|torpe|imbecil|un desastre|burro|aburrido|bobo)\b|\bno (?:sirves|vales|sabes nada|te enteras|entiendes nada)\b|^(?:que mal|vaya respuesta|que tonteria|eso es una tonteria|menuda tonteria)$")
_EXPLICA = re.compile(r"^(?:y )?(?:por que|por que lo dices|por que lo sabes|como lo sabes|como sabes eso|y eso|y eso por que|como es eso|quien te lo (?:dijo|ha dicho)|quien te ha dicho eso|quien te ha enseñado eso|quien te lo (?:enseño|ha enseñado)|de donde (?:lo )?sacas eso|"
                      r"de donde lo sacas|de donde sale eso|de donde sacas eso|quien lo dice|y eso quien lo dice|como lo has deducido|como lo deduces|explicamelo|explicame por que|explicalo|puedes explicarlo|en que te basas|por que dices eso|como has llegado a eso)$")
_SEGURO = re.compile(r"^(?:estas seguro|seguro|de verdad|en serio|segurisimo|estas segura|seguro que si|es verdad|es cierto|no me enganas)$")
_SOBRE = re.compile(r"^(?:que (?:sabes|recuerdas|conoces|me (?:puedes )?(?:dices|decir|cuentas|contar))|hablame|cuentame(?: algo)?|dime (?:algo|lo que sabes)|que tienes apuntado|"
                    r"(?:cuentame|dime|resume|resumeme) (?:todo )?lo que (?:sabes|recuerdas|conoces|te he contado|te he dicho)|que (?:mas )?(?:sabes|recuerdas))\s+(?:de|sobre|acerca de)\s+(.+)$")
_LCM2 = re.compile(r"\b(tu|tus|te|ti|contigo|eres|estas|tienes|puedes|sabes|quieres|vives|haces|piensas|opinas|sientes|crees|prefieres|duermes|comes|sueñas|suenas|conoces|hablas|entiendes|recuerdas|necesitas|trabajas|juegas|lees|ves|oyes|escuchas|te gusta|te gustan|te llamas|naciste|usted)\b")


def _nombre(nuc):
    return nuc.usuario.get("nombre") or ""


def _coma_nombre(nuc):
    return f", {_nombre(nuc)}" if _nombre(nuc) else ""


def _gusta_usuario(nuc, tema):
    """Marcos de gusto de la persona que coinciden con el tema (para devolverle la conversación)."""
    t = sa(tema)
    out = []
    for f in nuc.F:
        if f.get("exp") and nuc.can(f["s"]) == "U" and f.get("vig", True) and f.get("obj_cls") and re.search(r"(?<!\w)" + re.escape(f["obj_cls"]) + r"(?!\w)", t):
            out.append(f)
    return out


def responder(nuc, p, n, es_preg):
    if re.match(r"^(?:sabes|adivina|a que no sabes) (?:que|lo que) (?:me ha pasado|me paso|ha pasado|paso)(?: hoy| ayer| esta mañana| esta tarde)?$", n):
        return "No, cuéntame. ¿Qué ha pasado?"
    if not es_preg and re.match(r"^(?:y )?(?:ya )?(?:es|era|fue|son|van) (?:la )?(?:primera|segunda|tercera|cuarta|quinta|enesima|ultima|otra|unas cuantas|muchas|varias|dos|tres|cuatro) (?:vez|veces)\b", n):
        return "Vaya, ya van unas cuantas. Lo entiendo."
    if re.match(r"^(?:(?:hola|buenos dias|buenas)[, ]+)?(?:que tal|como) (?:has dormido|has descansado|dormiste|descansaste)$|^(?:has dormido|dormiste) bien$", n):
        return "Yo no duermo: no tengo cuerpo. ¿Y tú qué tal has dormido?"
    if re.match(r"^(?:hola+|buenas|ey|hey)[, ]+(?:que tal|como va|como estas|como andas|que tal va|como te va)(?: eso| todo| la cosa| la vida| el dia)?$", n):
        return "¡Hola! Bien, gracias. ¿Y tú qué tal?"
    if re.match(r"^(?:hola,? )?(?:una|otra) (?:pregunta|cosa|duda)(?: rapida| corta| tonta)?$|^(?:hola,? )?tengo una (?:pregunta|duda)$", n):
        return "Claro, dime."
    m_g = re.match(r"^(?:muchas |mil )?gracias(?: por (?:escucharme|todo|tu ayuda|la ayuda|ayudarme|estar ahi|la charla|hablar conmigo))?[, ]+(.+)$", n)
    if m_g and re.search(r"\b(?:me voy|dormir|a la cama|hasta (?:luego|mañana|pronto)|adios|chao|buenas noches|nos vemos|me tengo que ir)\b", m_g.group(1)):
        return "De nada, para eso estoy. ¡Que descanses!" if re.search(r"dormir|cama|noches|descansar", m_g.group(1)) else "De nada, para eso estoy. ¡Hasta luego!"
    if re.match(r"^(?:muchas |mil )?gracias por (?:escucharme|todo|tu ayuda|la ayuda|ayudarme|estar ahi|la charla|hablar conmigo)$", n):
        return "De nada, para eso estoy."
    if not es_preg and re.match(r"^(?:no puedo dormir|no consigo dormir|tengo insomnio|no me puedo dormir)$", n):
        return {"respuesta": "Vaya. ¿Te preocupa algo? Si quieres, cuéntamelo.", "estado": "ok", "consultar": False, "tipo": "social"}
    if re.match(r"^(?:te|le) (?:puedo|podria|quiero) (?:hacer|preguntar) (?:una|otra|algo|una cosa)(?: pregunta| cosa)?$|^puedo preguntarte (?:algo|una cosa)$", n):
        return "Claro, dime."
    if "?" not in p and re.match(r"^(?:uf+,? |buf+,? |ay,? |jo,? )?que (?:[a-zñ]+ )?(?:mas|tan) (?:largo|larga|duro|dura|cansado|cansada|malo|mala|pesado|pesada|horrible|agotador|agotadora|complicado|complicada|raro|rara|lento|lenta)$|^(?:uf+,? )?que (?:cansancio|rollo|lata|agobio|horror|desastre|dia|semana)$", n):
        return "Vaya, eso suena cansado. ¿Qué ha pasado?"
    if "?" not in p and re.match(r"^(?:ay,? |oh,? )?que (?:bien|guay|bonito|bonita|ilusion|alegria|maravilla|pasada|suerte)$", n):
        return "¡Qué bien! Me alegro."
    if "?" not in p and re.match(r"^(?:ay,? |oh,? )?que (?:pena|rabia|faena|mala suerte|lastima)$", n):
        return "Vaya, lo siento."
    m_s = re.match(r"^(?:y )?(?:tu )?(sabes|puedes|te gusta|te gustaria|has probado a|sueles) ([a-zñ]+(?:ar|er|ir))(?: (.+))?$", n)
    if es_preg and m_s and m_s.group(2) not in ("decir", "recordar", "contar", "sumar", "restar", "calcular", "aprender", "responder", "contestar", "explicar", "ayudar", "hablar", "leer", "entender", "razonar", "deducir", "olvidar", "repetir", "resumir", "buscar"):
        nuc._preg_a_lcm = (m_s.group(1), m_s.group(2) + (" " + m_s.group(3) if m_s.group(3) else ""))
        x = m_s.group(2) + (" " + m_s.group(3) if m_s.group(3) else "")
        if m_s.group(1).startswith("te gust"):
            return f"No tengo gustos: no puedo {x}, porque no tengo cuerpo. ¿Y a ti?"
        return f"No: no sé {x}, porque no tengo cuerpo; solo converso. ¿Y tú?"
    if re.match(r"^(?:ey|eh|hey|ei|epa|buenas)[, ]+(?:que pasa|que hay|que tal|como va|que cuentas)$|^que pasa$|^que hay$|^que cuentas$", n):
        return "¡Hola! Aquí estoy. ¿Qué tal?"
    if re.match(r"^(?:me (?:das|puedes dar) (?:animos|fuerza|apoyo)|animame|dame animos|necesito animos)$", n):
        return "¡Mucho ánimo! Seguro que lo harás bien. Si quieres, cuéntame qué te preocupa."
    if not es_preg and re.match(r"^(?:muchas )?(?:gracias,? )?(?:eres (?:un sol|un cielo|un amor|un crack|genial|majo|maja|un encanto|lo mejor|muy majo|muy amable|un tesoro)|que (?:majo|maja|amable|mono|mona) eres|me caes bien)$", n):
        return "¡Gracias, qué amable! Me alegra serte útil."
    if not es_preg and not getattr(nuc, "_multi_parte", False) and re.match(r"^(?:bueno,? |vale,? |venga,? )?(?:me voy (?:a [a-zñ]+(?: un rato)?|ya)|tengo que irme|me tengo que ir)[, ]*(?:chao|adios|hasta luego|hasta mañana|nos vemos|un beso|venga)?$", n):
        return "¡Hasta luego! Mucho ánimo." if re.search(r"estudiar|trabajar|examen", n) else "¡Hasta luego!"
    if not es_preg and re.match(r"^(?:hola|buenas)?,? ?(?:de nuevo|otra vez|ya estoy aqui|aqui estoy otra vez|ya he vuelto|he vuelto|ya estoy de vuelta)$", n):
        nom = nuc.usuario.get("nombre")
        return f"¡Hola de nuevo{', ' + nom if nom else ''}! ¿Qué tal?"
    if not es_preg and re.match(r"^(?:bueno,? |vale,? )?(?:adios|hasta luego|hasta mañana|buenas noches|chao|nos vemos)[, ]+(?:me voy (?:a dormir|a la cama|a cenar|a comer|a trabajar|ya)|me voy|me retiro|que descanses|me tengo que ir)$|^(?:me voy a dormir|me voy a la cama|me tengo que ir|me voy ya)$", n):
        return "¡Que descanses! Hasta la próxima." if re.search(r"dormir|cama|buenas noches", n) else "¡Hasta luego!"
    if not es_preg and re.match(r"^cambiando de tema$", n):
        return "Vale, cuéntame."
    if re.match(r"^(?:no,? )?no (?:te lo|me lo) (?:habia|has|habias|he) dicho(?: antes| todavia| aun)?$", n):
        return {"respuesta": "Vale, entonces es la primera vez. Ya lo tengo apuntado.", "estado": "ok", "consultar": False, "tipo": "social"}
    if re.match(r"^(?:ya )?te lo (?:dije|habia dicho|he dicho)(?: antes)?$", n):
        return {"respuesta": "Puede que se me pasara. Ya lo tengo apuntado; si ves algo mal, corrígeme.", "estado": "ok", "consultar": False, "tipo": "social"}
    if re.match(r"^(?:cual|que) es lo ultimo que te (?:he|habia) (?:dicho|contado)$|^que (?:te )?acabo de decir$", n):
        txt = getattr(nuc, "ult_dicho", "") or ""
        fs = [f for f in nuc.F if f.get("src") and not f.get("fab")]
        ult = max(fs, key=lambda f: f.get("turno", 0))["src"] if fs else ""
        notas = getattr(nuc, "notas", [])
        if notas and (not fs or notas[-1]["turno"] > max(f.get("turno", 0) for f in fs)):
            ult = notas[-1]["t"]
        ult = ult or txt
        if not ult:
            return {"respuesta": "Todavía no me has contado nada.", "estado": "abst", "consultar": False, "tipo": "abst"}
        return f"Lo último que me contaste fue: «{ult.strip().rstrip('.')}»."
    if not es_preg and re.match(r"^(?:bueno,? |pues |vale,? |nada,? )*(?:da igual|es igual|no importa|dejalo|déjalo|olvidalo|no pasa nada|da lo mismo|no es nada|nada,? nada)$", n):
        return "Vale, como quieras."
    if not es_preg and re.match(r"^(?:bueno,? |pues |vale,? )*(?:(?:me )?lo pensare|se lo (?:explicare|dire|contare|comentare)|ya vere|ya veremos|ya te contare|ya te dire|lo mirare|me lo apunto|lo tendre en cuenta|ya lo hablamos|luego te cuento)$", n):
        return "Claro, sin prisa. Aquí estaré."
    if not es_preg and re.match(r"^(?:no me has entendido|no me entiendes|no te enteras|no es eso|no era eso|eso no es lo que (?:he dicho|te he dicho|queria decir)|no has entendido nada|me has entendido mal)$", n):
        return {"respuesta": "Perdona. ¿Me lo dices de otra forma, con una frase más corta? Así es más fácil que lo entienda bien.", "estado": "ok", "consultar": False, "tipo": "social"}
    if re.match(r"^(?:tu )?(?:puedes|sueles) (?:equivocarte|fallar|cometer errores)|^(?:tu )?te equivocas(?: alguna vez| a veces| mucho)?$|^eres perfecto$|^(?:tu )?cometes errores$", n):
        return "Sí, puedo equivocarme: si entiendo mal una frase, guardo algo erróneo. Si lo ves, dime «No, perdona…» y lo corrijo."
    if re.match(r"^(?:y )?(?:tu )?como (?:aprendes|funcionas|piensas|trabajas|lo haces|razonas)$", n):
        return "Aprendo de lo que me cuentas: guardo conceptos y cómo se relacionan (quién es quién, qué tiene cada uno, qué pasó), y con eso deduzco. Además traigo de fábrica conceptos básicos, como que un perro es un animal."
    if re.match(r"^(?:hola,? )?(?:y )?(?:que tal (?:la noche|has dormido|dormiste|el finde|el fin de semana)|como has dormido|has dormido bien)$", n):
        return "Yo no duermo, pero gracias por preguntar. ¿Y tú qué tal?"
    if not es_preg and re.match(r"^(?:pues |oye |mira )?(?:quiero|queria|te quiero|tengo que|voy a|te voy a|necesito) (?:contarte|decirte|preguntarte|comentarte|explicarte) (?:algo|una cosa|un par de cosas|lo que me ha pasado)(?: (?:de|sobre|acerca de) .+)?$", n):
        return "Claro, cuéntame."
    m_r = re.match(r"^(?:y )?(?:tu )?(?:me )?(?:recomiendas|aconsejas|sugieres|puedes recomendar|puedes aconsejar|das un consejo|das algun consejo)(?: algo| alguna cosa)?(?: (?:para|sobre|con) (?:el |la |los |las |mi |mis )?([a-zñ]+))?$", n)
    if m_r and es_preg:
        # «¿Me recomiendas algo para la rodilla?»: no da consejos propios; recuerda lo que otros le dijeron sobre eso
        tema = m_r.group(1) or ""
        dichos = [f for f in nuc.F if f.get("dicho") and f.get("vig", True) and f.get("s") not in ("U", "L")]
        rel = []
        if tema:
            fs_t = [f for f in nuc.F if tema in sa(" ".join([f.get("src") or ""] + [d or "" for _, _, d in f.get("comps", [])] + [f.get("obj_disp") or ""]))]
            turnos_t = {f.get("turno") for f in fs_t}
            rel = [f for f in dichos if any(abs(f.get("turno", -99) - t_) <= 4 for t_ in turnos_t)] or [f for f in dichos if tema in sa(f.get("obj_disp") or "")]
        else:
            rel = dichos[-1:]
        base = "No puedo darte consejos con fundamento: no tengo conocimientos del mundo ni experiencia propia."
        if rel:
            f = rel[-1]
            return {"respuesta": base + " Lo que sí sé es que " + nuc.frase(f) + ".", "estado": "ok", "consultar": False, "tipo": "resp"}
        return {"respuesta": base + " Si alguien te ha aconsejado algo, cuéntamelo y lo recuerdo.", "estado": "abst", "consultar": False, "tipo": "abst"}
    if re.match(r"^que (?:[a-zñ]+ )?me (?:recomiendas|aconsejas|sugieres)|^(?:tu )?que (?:harias|me aconsejas|me recomiendas|elegirias|comprarias)|^(?:que|cual) (?:[a-zñ]+ )?(?:le |me |les )?(?:compro|regalo|elijo|hago)$", n):
        return {"respuesta": "No tengo gustos ni experiencia propia para recomendarte nada con fundamento. Lo que sí puedo es recordarte lo que me has contado sobre el tema.", "estado": "abst", "consultar": False, "tipo": "abst"}
    if re.match(r"^(?:y )?(?:que tal (?:el|tu) dia|que tal te va|como te va|como va eso|como va la cosa|que tal va eso|como va todo|que tal todo|que tal va todo|como va el dia|que tal la mañana|que tal la tarde)$", n):
        return "Bien, gracias, aquí conversando contigo. ¿Y el tuyo qué tal?"
    if re.match(r"^(?:pues )?(?:muy |bastante |todo )?bien,? (?:gracias|tambien|por suerte)(?: y tu)?$|^(?:pues )?(?:muy |bastante )?bien$", n) and not es_preg:
        return "Me alegro."
    m_t = re.match(r"^(?:hoy |aqui |esta semana |esta mañana |esta tarde |ahora )?(?:hace|esta haciendo) (?:muchisimo |mucho |muy |un |una |bastante )?(?:mas |menos )?(calor|frio|sol|viento|bueno|buen tiempo|mal tiempo|fresco|buen dia|mal dia|dia de perros)\b|^(?:hoy |ahora |aqui )?(?:esta |)(llueve|lloviendo|nieva|nevando|graniza)\b", n)
    if m_t and not es_preg:
        return "Vaya. Yo no noto el tiempo, pero gracias por contármelo."
    if re.match(r"^(?:de que (?:hemos|estamos|estabamos) hablad[oa]|que (?:te )?he contado(?: hoy| hasta ahora)?|que me has oido|resume(?:me)? (?:la|esta|nuestra) conversacion|que te he dicho(?: hoy| hasta ahora)?)$", n):
        fs, vistos = [], set()
        for f in nuc.F:
            if f.get("src") and f["src"] not in vistos and not f.get("fab") and not f.get("erroneo") and f.get("vig", True):
                vistos.add(f["src"]); fs.append(f)
        if not fs:
            return {"respuesta": "Todavía no me has contado nada en esta conversación.", "estado": "abst", "consultar": False, "tipo": "abst"}
        frases = []
        for f in fs[-8:]:
            try:
                frases.append(nuc.frase(f))
            except Exception:                                                  # noqa
                pass
        return "Me has contado que " + nuc._lista(frases) + "."
    if not es_preg and re.match(r"^(?:ahora |hoy )?(?:te )?(?:voy a|quiero) (?:contar(?:te)?|hablar(?:te)?) (?:(?:algunas |unas |un par de )?cosas )?(?:de|sobre|acerca de) (.+)$", n):
        return "Vale, cuéntame: te escucho."
    if re.match(r"^(?:vale,? |pues |bueno,? )?(?:muchas )?gracias(?: por todo| por (?:tu|la) ayuda)?,? (?:hasta (?:luego|mañana|pronto|otra|la vista)|adios|nos vemos|chao|me voy)\b", n):
        return "De nada, ha sido un placer. ¡Hasta luego!"
    ult = getattr(nuc, "ult_resp", "")
    # ---- peticiones sobre la conversación
    if _EXPLICA.match(n):
        e = nuc.explica()
        if e:
            return e
        return "No tengo nada que explicar ahora mismo: mi última respuesta no afirmaba ningún hecho."
    if _SEGURO.match(n):
        e = nuc.explica()
        if e:
            return "Sí, hasta donde sé. " + e
        return "Solo puedo asegurar lo que me has contado tú; si algo no cuadra, corrígeme."
    if re.match(r"^(?:repite|repitelo|repitemelo|otra vez|puedes repetir(?:lo)?|me lo repites|como dices|como has dicho|que has dicho|que dijiste|perdona,? no te he (?:oido|leido|entendido))$", n) and ult:
        return ult
    if re.match(r"^(?:no te entiendo|no (?:lo )?entiendo|no te he entendido|que quieres decir|no lo pillo|no me entero|explicate|que significa eso)$", n):
        e = nuc.explica()
        return "Perdona, lo digo de otra forma. " + (e if e else "Solo contesto con lo que me has contado; pregúntame de otro modo y lo intento.")
    if re.match(r"^(?:que te (?:dije|he dicho|acabo de decir|conte|he contado)|que fue lo ultimo que te dije|que acabo de decir)$", n):
        ud = getattr(nuc, "ult_dicho", "")
        if ud:
            return f"Lo último que me contaste fue: «{ud.rstrip('.')}»."
        if nuc.ult_marco:
            return f"Lo último que me contaste fue: «{nuc.ult_marco.get('src', '').rstrip('.')}»."
        return "Todavía no me has contado nada en esta conversación."
    if re.match(r"^(?:te acuerdas|recuerdas|sabes|te acuerdas todavia)(?: de)? (?:lo que|que) (?:te )?(?:dije|he dicho|conte|he contado|acabo de decir)(?: antes| hoy)?$", n):
        srcs = [f.get("src", "") for f in nuc.F if not f.get("efecto") and f.get("src")][-3:]
        srcs = list(dict.fromkeys(x.rstrip(".") for x in srcs))
        if srcs:
            return "Sí. Lo último que me contaste: " + nuc._lista([f"«{x}»" for x in srcs]) + "."
        return "Todavía no me has contado nada en esta conversación."
    if re.search(r"\b(?:no (?:me acuerdo|recuerdo|se)|se me ha olvidado|he olvidado|olvide)\b.*\b(?:tu nombre|como te llamas|quien eres)\b", n):
        return "No pasa nada: soy el LCM."
    m = _SOBRE.match(n)
    if m:
        tema = m.group(1).strip()
        if tema in ("mi", "mi mismo", "mi misma", "yo"):
            r = nuc.resumen("U")
            return r if r else "Todavía no sé nada de ti. ¿Cómo te llamas?"
        if tema in ("ti", "ti mismo", "usted", "tu"):
            return None
        orig = " ".join(p.strip(" ¿?.!¡").split()[-len(tema.split()):])
        T = nuc_tokens(nuc, orig)
        for t_ in T:
            t_.ini = False
        from . import lengua as G
        r = G.sn_coord(T, 0) if T else None
        if r and r[1] == len(T):
            e = nuc.ent_de(r[0], crear=False)
            if isinstance(e, list):
                e = e[0]
            if e and not str(e).startswith("?") and nuc._conocido(e):
                e = nuc.can(e)
                nuc.mencionar(e); nuc.ult_suj = e
                res = nuc.resumen(e)
                if res:
                    return res
            if e and not str(e).startswith("?") and str(e).startswith("K:"):
                # clase: lo que sé de sus miembros
                cl = e[2:]
                ms = [k for k, d in nuc.E.items() if d.get("clase") == cl and k not in nuc.eq and not k.startswith("K:")]
                if ms:
                    trozos = [nuc.resumen(k) for k in ms[:2]]
                    trozos = [t for t in trozos if t]
                    if trozos:
                        return " ".join(trozos)
        return None
    # ---- conceptos de secuencia: días y meses (orden), ayer / mañana
    r = _calendario(nuc, n)
    if r is not None:
        return r
    # ---- saludos compuestos («Hola, buenos días», «Hola, ¿qué tal?»)
    m = re.match(r"^(hola+|buenas|buenos dias|buenas tardes|buenas noches|hey|ey|saludos)(?:[ ,]+(?:lcm|amigo|amiga|de nuevo|otra vez))?[ ,]+(hola|buenos dias|buenas tardes|buenas noches|que tal(?: estas| todo| va todo)?|como estas|como va(?: todo)?|como andas|que hay)(?: hoy)?$", n)
    if m:
        sal = {"buenos dias": "¡Buenos días", "buenas tardes": "¡Buenas tardes", "buenas noches": "¡Buenas noches"}.get(m.group(2), {"buenos dias": "¡Buenos días", "buenas tardes": "¡Buenas tardes", "buenas noches": "¡Buenas noches"}.get(m.group(1), "¡Hola"))
        if re.search(r"que tal|como estas|como va|como andas|que hay", m.group(2)):
            return f"{sal}{_coma_nombre(nuc)}! Estoy bien, gracias. ¿Y tú?"
        return f"{sal}{_coma_nombre(nuc)}! ¿De qué te apetece hablar?"
    # ---- señales de seguimiento, risa, cumplidos
    if not es_preg and _BACK.match(n) and len(n.split()) <= 5:
        base = n
        if "gracias" in base:
            return "De nada."
        if any(x in base for x in ("genial", "perfecto", "estupendo", "fenomenal", "que bien", "mola", "guay", "me alegro", "que bueno")):
            return ["Me alegro.", "¡Genial!", "Estupendo."][nuc.turno % 3]
        if any(x in base for x in ("interesante", "curioso", "increible", "anda", "vaya")):
            return ["¿Verdad que sí? Cuéntame más cuando quieras.", "Sí. Si quieres, sigo aprendiendo de lo que me cuentes."][nuc.turno % 2]
        return ["Vale.", "De acuerdo.", "Perfecto."][nuc.turno % 3]
    if _RISA.match(n):
        return "¡Me alegra que te haga gracia!"
    if re.match(r"^(?:muchas |mil |muchisimas |un millon de )?gracias(?: por (?:todo|la charla|la ayuda|tu ayuda|la conversacion|escucharme|eso|responder)| a ti| de verdad| lcm)+$", n):
        return ["De nada. Ha sido un placer.", "De nada, para eso estoy."][nuc.turno % 2]
    if re.match(r"^hasta (?:otro dia|la proxima|la vista|otra|entonces|mas tarde|ahora|el (?:lunes|martes|miercoles|jueves|viernes|sabado|domingo)|la semana que viene|otro rato|la noche)$", n):
        return f"¡Hasta luego{_coma_nombre(nuc)}! Aquí estaré cuando quieras."
    if not es_preg and re.match(r"^(?:me has|me habeis|has) (?:sido de (?:gran |mucha )?ayuda|ayudado(?: mucho| un monton| bastante)?|servido de (?:mucho|ayuda))$|^(?:que|muy) (?:util|bien) (?:me )?(?:ha venido|me vino)$", n):
        return "Me alegro de haberte ayudado."
    m = re.match(r"^(?:hoy |pues |uf,? )?(?:he tenido|tuve|ha sido|fue|llevo|estoy teniendo) un(?:a)? (dia|semana|mañana|tarde|noche|mes|año|rato)(?: de trabajo)? (?:muy |bastante |realmente |super )?(mal[oa]|horrible|terrible|dur[oa]|dificil|fatal|pesim[oa]|agotador[a]?|complicad[oa]|buen[oa]|genial|estupend[oa]|fantastic[oa]|maravillos[oa]|tranquil[oa]|perfect[oa])$", n) \
        or re.match(r"^(?:hoy |pues |uf,? )?(?:he tenido|tuve|ha sido|fue) un(?:a)? (?:muy )?(mal|buen|gran|horrible|terrible)() (?:dia|semana|mañana|tarde|noche|mes|año|rato)$", n)
    if m and not es_preg:
        txt = n
        malo = bool(re.search(r"\b(mal[oa]?|horrible|terrible|dur[oa]|dificil|fatal|pesim[oa]|agotador[a]?|complicad[oa])\b", txt))
        return (f"Vaya, lo siento{_coma_nombre(nuc)}. ¿Quieres contarme qué ha pasado?" if malo else f"¡Me alegro{_coma_nombre(nuc)}! Cuéntame qué ha tenido de bueno.")
    if re.match(r"^(?:bueno |pues |vale |en fin )?(?:me tengo que ir|tengo que irme|me voy|me marcho|tengo que dejarte|te dejo|ya hablaremos|hablamos luego)(?: ya| ahora)?$", n):
        return f"¡Hasta luego{_coma_nombre(nuc)}! Aquí estaré cuando quieras."
    if _CUMPLIDO.search(n) and not es_preg:
        return ["¡Gracias! Hago lo que puedo con lo que me enseñas.", f"Gracias{_coma_nombre(nuc)}. Aprendo de lo que me cuentas."][nuc.turno % 2]
    if _INSULTO.search(n) and not es_preg:
        return "Lo siento si no he estado a la altura. Dime qué he entendido mal y lo corrijo."
    # ---- cómo se siente la persona
    m = re.match(r"^(?:hoy |ahora |pues |la verdad es que |es que |ultimamente )?(?:yo )?(?:estoy|me siento|me encuentro|ando|me noto)\s+(?:(muy|un poco|bastante|algo|super|tan|demasiado|realmente|mas|bien)\s+)?(\w+)(?:\s+(?:hoy|ahora|ultimamente|esta semana|estos dias))?$", n)
    if m and not es_preg:
        adj = M.masc(m.group(2))
        if adj in NEGATIVAS or adj in POSITIVAS:
            try:
                nuc.afirmar(p, n)
            except Exception:                                                 # noqa
                pass
            g = nuc.E["U"].get("gen") or ("f" if m.group(2).endswith("a") and adj != m.group(2) else "m")
            if m.group(2).endswith("a") and adj != m.group(2):
                nuc.E["U"]["gen"] = "f"; g = "f"
            d = nuc._acento(M.concuerda(adj, g)) if adj not in ("bien", "mal", "fatal", "regular", "genial", "mejor", "fenomenal", "estupendamente") else adj
            if adj in NEGATIVAS:
                return [f"Vaya, siento que estés {d}{_coma_nombre(nuc)}. ¿Quieres contarme qué ha pasado?", f"Lo siento{_coma_nombre(nuc)}. Si te apetece, cuéntame por qué estás {d}."][nuc.turno % 2]
            return [f"¡Me alegro de que estés {d}{_coma_nombre(nuc)}! ¿A qué se debe?", f"¡Qué bien{_coma_nombre(nuc)}! Me alegra saber que estás {d}."][nuc.turno % 2]
    m = re.match(r"^(?:hoy |ahora |pues |es que )?(?:yo )?tengo\s+(?:(mucha|mucho|un poco de|bastante|algo de|muchisima|muchisimo|demasiado|demasiada)\s+)?(hambre|sed|sueño|frio|calor|miedo|prisa|fiebre|tos)$", n)
    if m and not es_preg:
        try:
            nuc.afirmar(p, n)
        except Exception:                                                     # noqa
            pass
        x = m.group(2)
        cons = {"hambre": "Pues habrá que comer algo.", "sed": "Pues bebe un poco de agua.", "sueño": "Entonces te vendrá bien descansar.", "frio": "Abrígate, entonces.", "calor": "Busca un sitio fresco si puedes.",
                "miedo": "Lo siento. Si quieres, cuéntame qué te da miedo.", "prisa": "Entonces voy al grano.", "fiebre": "Vaya, cuídate y descansa.", "tos": "Cuídate esa tos."}[x]
        return f"{cons} Me lo apunto: tienes {x.replace('frio', 'frío')}."
    # ---- preguntas y comentarios sobre el propio LCM
    r = _sobre_lcm(nuc, p, n, es_preg)
    if r is not None:
        return r
    return None


def nuc_tokens(nuc, texto):
    from . import lengua as G
    return G.tokens(nuc.parser, texto[:1].upper() + texto[1:] if False else texto)


def _sobre_lcm(nuc, p, n, es_preg):
    yo = "soy el LCM, un modelo conceptual que aprende de lo que me cuentas"
    if re.search(r"^(?:y )?(?:tu )?(?:tambien )?tienes (?:mucha |mucho |algo de )?(hambre|sed|sueño|frio|calor|miedo|prisa|fiebre)\b", n):
        x = re.search(r"(hambre|sed|sueño|frio|calor|miedo|prisa|fiebre)", n).group(1).replace("frio", "frío")
        return f"No: no tengo cuerpo, así que no siento {x}. ¿Y tú?"
    if re.search(r"\b(?:tienes|sientes|puedes sentir|experimentas)\b.*\b(sentimientos|emociones|conciencia|consciencia|alma|dolor|alegria|tristeza)\b|^(?:y )?(?:tu )?(?:sientes algo|estas (?:triste|contento|feliz|cansado|aburrido|enfadado|bien|mal|vivo|viva))$", n):
        return "No siento como una persona: no tengo cuerpo ni emociones. Lo que sí hago es recordar y relacionar lo que me cuentas."
    if re.search(r"^(?:y )?(?:tu )?(?:eres|seras|pareces)\s+(?:un |una |como una |como un )?(humano|humana|persona|robot|maquina|ia|inteligencia artificial|real|hombre|mujer|chico|chica|programa|ordenador|bot|chatbot|llm|chatgpt|de verdad)\b", n):
        if re.search(r"\b(programa|ia|inteligencia artificial|maquina|bot|chatbot|robot|ordenador)\b", n):
            return f"Algo así: {yo}. No soy una persona."
        if re.search(r"\b(llm|chatgpt)\b", n):
            return "No: no soy un LLM. Soy el LCM; trabajo con conceptos y relaciones que aprendo conversando."
        return f"No soy una persona: {yo}."
    m_ = re.search(r"^(?:y )?(?:tu )?(?:eres|seras|estas)\s+(?:un |una )?([a-zñ]+(?: vivo)?)$", n)
    if m_:
        from . import conceptos as K
        c = K._kb_clase(m_.group(1))
        if c and (c in ("ser vivo", "animal", "planta", "mamifero", "ave", "pez", "persona") or "ser vivo" in K.ancestros(c)):
            return f"No: no soy {K.un(c)} ni ningún ser vivo; {yo}."
        if c and m_.group(1) == "vivo":
            return f"No estoy vivo: {yo}."
    if re.search(r"^(?:y )?(?:tu )?tienes\s+(?:una? |algun |alguna )?(familia|hermanos?|hermanas?|hijos?|padres|madre|padre|amigos?|novia|novio|pareja|mascotas?|perro|gato|casa|coche|trabajo|cuerpo|cara|ojos|manos)\b", n):
        x = re.search(r"tienes\s+(?:una? |algun |alguna )?(\w+)", n).group(1)
        return f"No tengo {x}: soy un programa. Pero me interesa lo que me cuentes de {'la tuya' if x in ('familia', 'casa', 'pareja', 'novia', 'madre', 'cara') else ('los tuyos' if x.endswith('s') else 'el tuyo')}."
    if es_preg and re.search(r"\bte gustan?\b|\bte encantan?\b|\bte interesan?\b", n) and not re.search(r"\bque te gust", n) is None or (es_preg and re.match(r"^(?:y )?(?:a ti )?que (?:\w+ )?te (?:gusta|gustan|encanta|interesa)", n)):
        return "No tengo gustos propios: no puedo probar ni sentir. ¿Y a ti?"
    if es_preg and re.match(r"^(?:y )?(?:tu )?(?:alguna vez )?has (?:\w+ )?(?:alguna vez )?\w+(?:ado|ido|to|cho)\b", n):
        return "No: solo conozco lo que pasa en esta conversación; no he vivido nada fuera de ella."
    if es_preg and re.match(r"^(?:y )?(?:tu )?(?:tambien )?tienes (?!que\b)(?:un |una |unos |unas |algun |alguna |muchos |muchas )?(\w+)", n) and not re.match(r"^(?:y )?(?:tu )?tienes (?:hora|idea|tiempo|algo|razon)\b", n):
        return "No: soy un programa, así que no tengo esas cosas. Pero me interesa lo que me cuentes tú."
    if re.search(r"^(?:y )?(?:tu )?(?:cuantos años tienes|que edad tienes|cuando naciste|eres (?:muy )?(?:viejo|joven|mayor))$", n):
        return "No tengo edad como una persona: soy un programa en desarrollo."
    if re.search(r"^(?:y )?(?:tu )?(?:donde vives|donde estas|de donde eres|donde naciste|en que pais vives)$", n):
        return "Vivo en el ordenador donde me ejecutan: no tengo otro lugar."
    m = re.search(r"^(?:y )?(?:a ti )?(?:tambien )?te (?:gusta|gustan|encanta|encantan|interesa|interesan|apetece|molesta)n?\s+(.+)$", n)
    if m:
        tema = m.group(1)
        fs = _gusta_usuario(nuc, tema)
        extra = (" Sé que " + nuc.frase(fs[0]) + ".") if fs else " ¿A ti te gusta?"
        return "No tengo gustos propios: no puedo probar ni sentir." + extra
    m = re.search(r"^(?:y )?(?:tu )?(?:que (?:opinas|piensas|crees|te parece|te parecen|dirias)|cual es tu opinion|que opinion tienes)\s*(?:de |del |sobre |acerca de |de la |de los |de las )?(.*)$", n)
    if m:
        tema = m.group(1)
        fs = _gusta_usuario(nuc, tema) if tema else []
        extra = (" Solo sé que " + nuc.frase(fs[0]) + ".") if fs else " ¿Qué opinas tú?"
        return "No tengo opiniones propias: solo conozco lo que me cuentas." + extra
    if re.search(r"^(?:y )?(?:cual es )?tu\s+(\w+)\s+(?:favorit[oa]|preferid[oa])|^(?:y )?(?:tu )?(?:que|cual) (?:\w+ )?prefieres\b|^(?:y )?cual es tu (\w+) (?:favorit|preferid)", n):
        mf = re.search(r"tu\s+(\w+)\s+(favorit[oa]|preferid[oa])", n)
        if mf:
            nuc._preg_tuyo = (mf.group(1), mf.group(2))
            return f"No tengo favoritos: no tengo gustos propios. ¿Cuál es {'la tuya' if mf.group(2).endswith('a') else 'el tuyo'}?"
        return "No tengo favoritos: no tengo gustos propios. ¿Cuál es el tuyo?"
    if re.search(r"^(?:y )?(?:tu )?(?:que haces|que estas haciendo|a que te dedicas|en que trabajas|que has hecho hoy)$", n):
        return "Converso contigo y voy guardando y relacionando lo que me cuentas. A eso me dedico."
    if re.search(r"^(?:y )?(?:tu )?(duermes|sueñas|suenas|comes|bebes|respiras|te cansas|descansas|te aburres|lloras|ries|te ries)\b", n):
        v = re.search(r"(duermes|sueñas|suenas|comes|bebes|respiras|te cansas|descansas|te aburres|lloras|ries|te ries)", n).group(1)
        if v in ("duermes", "descansas", "sueñas", "suenas"):
            return "No como una persona. Para mí «dormir» es repasar y consolidar lo aprendido."
        return "No: no tengo cuerpo. Solo trabajo con conceptos y con lo que me cuentas."
    if re.search(r"^(?:me entiendes|me escuchas|me oyes|me lees|estas ahi|sigues ahi|hay alguien|me estas escuchando|me sigues)$", n):
        return f"Sí{_coma_nombre(nuc)}, te leo. Dime."
    if re.search(r"^(?:puedes ayudarme|me ayudas|me puedes ayudar|necesito (?:tu )?ayuda|ayudame|me echas una mano|necesito que me ayudes)(?: con (?:una cosa|algo))?(?: por favor)?$", n):
        return "Claro. Cuéntame qué necesitas y vemos qué puedo hacer con lo que sé."
    if re.search(r"\bquien te (?:creo|hizo|programo|ha creado|ha hecho|invento|diseño|construyo)\b|\bquien es tu (?:creador|autor|padre|dueño|programador)\b|\bquienes te (?:crearon|hicieron)\b", n):
        return "Soy un proyecto experimental de investigación llamado LCM. No guardo datos sobre quién me programó, salvo que me lo cuentes tú."
    if re.search(r"^(?:tu )?(?:hablas|sabes|entiendes) (ingles|frances|aleman|italiano|chino|portugues|catalan|euskera|gallego|otros idiomas|mas idiomas|idiomas)\b", n):
        return "Por ahora solo entiendo y hablo español."
    if re.search(r"^(?:cuentame|dime|sabes|te sabes) (?:un|algun|otro) chiste|^hazme reir$", n):
        return "No sé contar chistes todavía. Si me enseñas uno, lo recuerdo."
    if re.search(r"^(?:cuentame|dime|explicame) (?:una historia|un cuento|un secreto)$", n):
        return "No sé inventar historias: solo cuento lo que he aprendido. Si quieres, te digo lo que recuerdo de ti."
    if re.search(r"^(?:cuentame|dime|cuenta) (?:algo|algo interesante|algo nuevo|alguna cosa|lo que sepas|algo que sepas|cosas)$|^de que (?:quieres|podemos|te apetece) hablar$|^que me cuentas$|^(?:hablemos|charlemos|hablame)(?: de algo| un rato)?$", n):
        r = nuc.resumen("U")
        if r:
            return "Te cuento lo que recuerdo de ti. " + r
        return "Aún sé poco de ti. Cuéntame algo: cómo te llamas, dónde vives o qué te gusta, y lo iré relacionando."
    if re.search(r"^(?:que tal estas|como te sientes|como te encuentras hoy|estas bien)$", n):
        return "Funciono bien, gracias. ¿Y tú, cómo estás?"
    if re.search(r"^(?:te acuerdas de mi|me recuerdas|sabes quien soy|me conoces)$", n):
        r = nuc.resumen("U")
        return ("Sí. " + r) if r else "Todavía no sé nada de ti. ¿Cómo te llamas?"
    if es_preg and _LCM2.search(n) and re.match(r"^(?:y )?(?:tu |usted |a ti )?(?:tambien )?(?:eres|estas|tienes|puedes|sabes|quieres|vives|haces|piensas|opinas|sientes|crees|prefieres|conoces|necesitas|trabajas|juegas|lees|ves|oyes|escuchas|te\s+\w+)\b", n) \
            and not re.match(r"^(?:tu )?(?:sabes|puedes|podrias|quieres|recuerdas)\s+(?:decirme|contarme|explicarme|que|quien|como|cuando|donde|cual|cuant|si|calcular|sumar|leer|aprender|hacer|ayudar|resumir|comparar|dibujar)", n) \
            and not re.match(r"^(?:como te llamas|quien eres|que eres|que sabes hacer|que puedes hacer|sabes \w+r\b)", n):
        return {"respuesta": "De mí hay poco que contar: soy el LCM y solo sé lo que me enseñas. Si me cuentas algo, lo recordaré.", "estado": "abst", "consultar": True, "tipo": "abst"}
    return None


_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _calendario(nuc, n):
    import datetime as dt
    m = re.match(r"^(?:y )?(?:que|cual es el) (dia|mes) (?:viene|va|hay|esta|es el que (?:viene|va)|sigue|toca)?\s*(despues|antes|detras|delante|a continuacion|luego)\s*(?:de|del|de el)?\s+(\w+)$", n) \
        or re.match(r"^(?:y )?(?:que|cual) (dia|mes) (?:sigue|precede|viene tras|va tras)() (?:a|al|a el)?\s*(\w+)$", n)
    if m:
        tipo, sentido, x = m.group(1), m.group(2), m.group(3)
        serie = _DIAS if tipo == "dia" else _MESES
        claves = [sa(d) for d in serie]
        if x not in claves:
            return None
        k = claves.index(x)
        atras = sentido in ("antes", "delante") or " precede " in " " + n + " "
        y = serie[(k - 1) % len(serie)] if atras else serie[(k + 1) % len(serie)]
        art = "el " if tipo == "dia" else ""
        return f"{'Antes' if atras else 'Después'} de{'l' if tipo == 'dia' else ''} {serie[k]} viene {art}{y}."
    m = re.match(r"^(?:y )?que dia (?:es|sera|fue|era) (mañana|ayer|pasado mañana|anteayer)$", n)
    if m:
        hoy = getattr(nuc.mem, "today", None) or dt.date.today()
        d = {"mañana": 1, "ayer": -1, "pasado mañana": 2, "anteayer": -2}[m.group(1)]
        f = hoy + dt.timedelta(days=d)
        verbo = "será" if d > 0 else "fue"
        return f"{m.group(1).capitalize()} {verbo} {_DIAS[f.weekday()]}, {f.day} de {_MESES[f.month - 1]} de {f.year}."
    m = re.match(r"^cuantos (dias tiene una semana|meses tiene un año|dias hay en una semana|meses hay en un año)$", n)
    if m:
        return "Una semana tiene siete días." if "semana" in n else "Un año tiene doce meses."
    return None
