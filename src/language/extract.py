"""De un arbol sintactico a proposiciones (sujeto, relacion, objeto) para CUALQUIER frase (parche-30/32).

Casos:  "Ana es la madre de Luis"   -> (ana, madre_de, luis)     (sustantivo + cop + nmod con preposicion)
        "Un perro es un animal"     -> (perro, es, animal)        (sustantivo + cop, sin complemento)
        "Pedro escribio una carta"  -> (pedro, escribio, carta)   (verbo + nsubj + obj)
        "Ana vive en Madrid"        -> (ana, vive_en, madrid)     (verbo + nsubj + obl con preposicion)
v2 (parche-32): el relativo "que" se sustituye por su antecedente ("la normativa que regula X" -> normativa regula X)
y se detecta la negacion ("no", "nunca", "jamas", "tampoco" ligados al verbo).
"""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from .lexicon import norm

Tree = Sequence[Tuple]       # (forma, upos, head, deprel[, lema]) por palabra
NEG = {"no", "nunca", "jamas", "tampoco"}


def _children(tree: Tree, i: int) -> List[int]:
    return [j for j, w in enumerate(tree) if w[2] == i + 1]


def _name(tree: Tree, i: int) -> str:
    parts = [(i, tree[i][0])] + [(j, tree[j][0]) for j in _children(tree, i) if tree[j][3] in ("flat", "nummod")]
    return "_".join(norm(f) for _, f in sorted(parts))


def _lem(tree: Tree, i: int) -> str:
    """Forma base de la palabra (parche-34): escribio -> escribir. Sin lema, la propia forma."""
    w = tree[i]
    return norm(w[4]) .replace(" ", "_") if len(w) > 4 and w[4] else norm(w[0])


def _prep(tree: Tree, i: int) -> str:
    cases = [norm(tree[j][0]) for j in _children(tree, i) if tree[j][3] == "case"]
    return cases[0] if cases else ""


def _conj(tree: Tree, i: int) -> List[int]:
    """La palabra y todas las que van coordinadas con ella ("pan, queso y fruta": relacion conj), en orden."""
    out, todo = [i], [i]
    while todo:
        for j in _children(tree, todo.pop()):
            if tree[j][3] == "conj" and j not in out:
                out.append(j); todo.append(j)
    return sorted(out)


def _infinitive(tree: Tree, i: int) -> bool:
    """"Cocinar es una accion": un infinitivo con funcion de sujeto es el concepto de esa accion (parche-50)."""
    f = tree[i][0].lower()
    return tree[i][1] == "VERB" and tree[i][3] in ("nsubj", "csubj") and len(f) > 3 and f.endswith(("ar", "er", "ir", "ír"))


def _name_like_adj(tree: Tree, i: int) -> bool:
    """parche-43: "Clara canta ..." -> la escuela la etiqueta ADJ (clara). Un adjetivo con mayuscula, sin determinante, que hace de
    sujeto se trata como un nombre propio."""
    return (tree[i][1] == "ADJ" and tree[i][0][:1].isupper() and tree[i][3] == "nsubj"
            and not any(tree[j][3] == "det" for j in _children(tree, i)))


def _subjects_of(tree: Tree, i: int) -> List[int]:
    """Sujetos del verbo i; un verbo coordinado sin sujeto propio hereda el del anterior ("vive en Madrid y trabaja en Sevilla")."""
    seen = set()
    while True:
        subj = [j for j in _children(tree, i) if tree[j][3] in ("nsubj", "csubj")]
        if subj or tree[i][3] != "conj" or tree[i][2] <= 0 or i in seen:
            return subj
        seen.add(i)
        i = tree[i][2] - 1


TIME_ADV = {"ayer", "hoy", "manana", "anoche", "anteayer", "ahora", "luego", "despues", "antes", "pronto"}
TIME_NOUNS = {"lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo", "enero", "febrero", "marzo", "abril", "mayo", "junio",
              "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre", "primavera", "verano", "otono", "invierno", "manana",
              "tarde", "noche", "semana", "mes", "ano", "dia", "siglo", "veces", "dias", "noches", "tardes", "semanas", "meses", "anos"}
FREQ_ADV = {"siempre", "normalmente", "generalmente", "habitualmente", "frecuentemente", "raramente", "regularmente", "diariamente", "semanalmente", "mensualmente"}
NUM_WORDS = {"una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12}
LOC_ADV = {"encima", "debajo", "dentro", "fuera", "cerca", "lejos", "delante", "detras", "junto", "enfrente", "alrededor"}
SOME_Q = {"algunos", "algunas", "varios", "varias", "muchos", "muchas", "pocos", "pocas"}
NONE_Q = {"ninguno", "ninguna", "ningun", "ningunos", "ningunas"}
TIME_MOD = {"pasado", "proximo", "siguiente", "anterior", "pasada", "proxima"}


def _subtree(tree: Tree, j: int, rels=("case", "det", "amod", "nummod", "flat")) -> List[int]:
    return sorted([j] + [k for k in _children(tree, j) if tree[k][3] in rels])


DATIVE_VERBS = {"dar", "regalar", "entregar", "prestar", "vender", "comprar", "ofrecer", "enviar", "mandar", "devolver", "pasar", "traer", "llevar"}
STRONG_TIME = {"ayer", "anteayer", "anoche", "hoy"}      # nunca son otra cosa, aunque la escuela los lea como adjetivo del objeto


def when_of(tree: Tree, i: int):
    """Expresion temporal del verbo i -> (clave normalizada, como se escribio, indices de sus palabras) o None (parche-51)."""
    near = set(_children(tree, i))
    for j in sorted(near):
        for k in _children(tree, j):
            if norm(tree[k][0]) in STRONG_TIME:
                return norm(tree[k][0]), tree[k][0], [k]
    for j in _children(tree, i):
        w = norm(tree[j][0])
        if tree[j][3] == "advmod" and w in TIME_ADV:
            return w, tree[j][0], [j]
        if tree[j][3] == "advmod" and w in FREQ_ADV:                     # "Ana siempre llega" (parche-56)
            return "frec_" + w, tree[j][0], [j]
        if tree[j][3] in ("obl", "nmod") and tree[j][1] == "NUM" and (w in NUM_WORDS or w.isdigit()) \
                and any(tree[k][3] == "case" and norm(tree[k][0]) == "a" for k in _children(tree, j)):
            idx = _subtree(tree, j)                                       # "a las tres"
            return "hora_" + str(NUM_WORDS.get(w, w)), " ".join(tree[k][0] for k in idx), idx
        if tree[j][3] in ("obl", "nmod"):
            if w in TIME_NOUNS:
                idx = _subtree(tree, j)
                mods = [norm(tree[k][0]) for k in idx if tree[k][3] == "amod" and norm(tree[k][0]) in TIME_MOD]
                return "_".join([w] + mods), " ".join(tree[k][0] for k in idx), idx
            if tree[j][1] == "NUM" and tree[j][0].isdigit() and len(tree[j][0]) == 4:
                idx = _subtree(tree, j)
                return tree[j][0], " ".join(tree[k][0] for k in idx), idx
    return None


PRON_SUBJ = {"el", "ella", "ellos", "ellas"}
MODAL_FORMS = {**{f: "poder" for f in ("puedo", "puedes", "puede", "podemos", "pueden", "podia", "podian", "pudo", "podra", "podria")},
               **{f: "deber" for f in ("debo", "debes", "debe", "debemos", "deben", "debia", "debian", "debio", "debera", "deberia")}}
SAY_LEMMAS = {"decir", "creer", "pensar", "afirmar", "opinar", "asegurar", "comentar", "contar", "explicar", "sospechar", "opinar"}
SAY_FORMS = {"dice", "dijo", "dicen", "decia", "cree", "creia", "creen", "piensa", "piensan", "opina", "afirma", "asegura", "comenta", "cuenta"}


def _desc(tree: Tree, j: int) -> List[int]:
    out, todo, seen = [], list(_children(tree, j)), {j}
    while todo:
        k = todo.pop()
        if k in seen:          # un arbol predicho puede tener ciclos: sin esto el bucle no acababa nunca
            continue
        seen.add(k)
        out.append(k)
        todo.extend(_children(tree, k))
    return out


def _is_say(tree: Tree, i: int) -> bool:
    return tree[i][1] == "VERB" and (_lem(tree, i) in SAY_LEMMAS or norm(tree[i][0]) in SAY_FORMS) \
        and any(tree[j][3] == "ccomp" for j in _children(tree, i))


def triples_full(tree: Tree, resolve_rel: bool = True, entities_only: bool = False, coordination: bool = True,
                 default_subject: str = None) -> List[Dict]:
    """v3 (parche-42): coordinacion de sujetos, objetos y complementos ("Pedro y Marta viven en Madrid") y verbos coordinados
    con sujeto compartido. coordination=False reproduce el comportamiento anterior.
    v4 (parche-44): default_subject = sujeto de la frase anterior: sustituye a "el/ella" y es el sujeto de un verbo principal
    sin sujeto escrito ("Ana vive en Madrid. Trabaja en un banco")."""
    cause = next((m for m, row in enumerate(tree) if norm(row[0]) == "porque" and m >= 2), None)
    if cause is not None:                              # "Ana llora porque esta triste": hecho principal + causa (no se afirma la causa)
        root = next((k for k, row in enumerate(tree[:cause]) if row[3] == "root" or row[2] == 0), 0)
        main = [r if r[2] <= cause else (r[0], r[1], 0, "root", *r[4:]) for r in tree[:cause]] + [(".", "PUNCT", root + 1, "punct", ".")]
        base = triples_full(main, resolve_rel, entities_only, coordination, default_subject)
        forms = [w[0] for w in tree]
        clause = [k for k in range(cause + 1, len(tree)) if tree[k][1] != "PUNCT"]
        extra = []
        for t in base:
            if not clause or t.get("p", "").endswith("_que"):
                continue
            ss = _span(tree, t["si"]) if t.get("si") is not None else []
            if ss and ss[0] == 0:
                head_txt = "{s} " + " ".join(forms[k] for k in range(cause) if k not in ss)
            else:
                head_txt = " ".join(forms[:cause])
            extra.append({"s": t["s"], "p": t["p"] + "_porque", "o": "_".join(norm(tree[k][0]) for k in clause), "neg": False, "head": t["head"],
                          "si": None, "oi": None, "when": "", "when_disp": "", "when_idx": [], "q": "",
                          "template": head_txt.strip() + " porque {o}",
                          "s_disp": " ".join(forms[k] for k in ss) if ss else t["s"], "o_disp": " ".join(forms[k] for k in clause)})
        return base + extra
    out = []
    ok = ("NOUN", "PROPN") if entities_only else ("NOUN", "PROPN", "PRON")
    obj_ok = ("NOUN", "PROPN", "PRON") + (("ADJ",) if entities_only else ())

    def group(i, allowed):
        members = _conj(tree, i) if coordination else [i]
        return [m for m in members if tree[m][1] in allowed]

    embedded = set()
    for i0 in range(len(tree)):
        if _is_say(tree, i0):
            for j0 in _children(tree, i0):
                if tree[j0][3] == "ccomp":
                    embedded.update([j0] + _desc(tree, j0))

    for i, (form, upos, head, rel, *_rest) in enumerate(tree):
        if i in embedded:
            continue                                  # lo que alguien DICE no es un hecho: se guarda solo como "X dice que ..."
        kids = _children(tree, i)
        subj = _subjects_of(tree, i) if coordination else [j for j in kids if tree[j][3] in ("nsubj", "csubj")]
        if not subj and default_subject and rel == "root" and upos == "VERB":
            sj, subjects = None, [default_subject]
        else:
            if not subj:
                continue
            sj = subj[0]
            if resolve_rel and norm(tree[sj][0]) == "que" and rel == "acl" and head > 0:
                sj = head - 1                                 # "la normativa que regula": el sujeto es la normativa
            pron = bool(default_subject) and _name(tree, sj) in PRON_SUBJ      # "Él lee..." (la escuela lo etiqueta DET) / "Ella" (PRON)
            if tree[sj][1] not in ok and not pron and not _infinitive(tree, sj) and not (entities_only and _name_like_adj(tree, sj)):
                continue
            subjects = [sj] if pron or _infinitive(tree, sj) else group(sj, ok)
            if tree[sj][1] == "ADJ":
                subjects = [sj]
            if default_subject:
                subjects = [default_subject if _name(tree, k) in PRON_SUBJ else k for k in subjects]
        neg = any(tree[j][3] == "advmod" and norm(tree[j][0]) in NEG for j in kids)
        dets = [norm(tree[d][0]) for d in _children(tree, subjects[0]) if tree[d][3] == "det"] if subjects and not isinstance(subjects[0], str) else []
        quant = ""
        if set(dets) & NONE_Q:
            neg = True                                  # "Ninguna rana es mamifero"
        elif set(dets) & SOME_Q:
            quant = next(d for d in dets if d in SOME_Q)  # "Algunos pajaros vuelan": no vale para todos
        tm = when_of(tree, i)
        skip = set(tm[2]) if tm else set()
        has_cop = any(tree[j][3] == "cop" for j in kids)

        def add(sj_, p, o_idx):
            named = isinstance(sj_, str)
            out.append({"s": sj_ if named else _name(tree, sj_), "p": p, "o": "_" if o_idx is None else _name(tree, o_idx), "neg": neg, "head": i,
                        "si": None if named else sj_, "oi": o_idx, "when": tm[0] if tm else "", "when_disp": tm[1] if tm else "",
                        "when_idx": sorted(skip), "q": quant})

        found = False
        if upos == "PROPN" and subjects and not isinstance(subjects[0], str) and tree[subjects[0]][1] == "NOUN" \
                and (has_cop or any(tree[c][3] == "cop" for c in _children(tree, subjects[0]))):
            # parche-76: "La madre de Marcos es Ana." (de "Mi madre es Ana."): el nombre propio es la raiz y el sujeto es el sustantivo de parentesco
            # con su "de X": (ana, madre_de, marcos), igual que "Ana es la madre de Marcos".
            nm = [j for j in _children(tree, subjects[0]) if tree[j][3] == "nmod" and tree[j][1] in ("PROPN", "NOUN") and _prep(tree, j) == "de"]
            if nm:
                for k in group(nm[0], ("PROPN", "NOUN")):
                    add(i, _lem(tree, subjects[0]) + "_de", k)
                found = True
        if has_cop and upos in ("NOUN", "PROPN", "ADJ"):
            for j in kids:
                if tree[j][3] == "nmod" and tree[j][1] in ("NOUN", "PROPN"):
                    base = _prep(tree, j)
                    cmp_ = [norm(tree[j2][0]) for j2 in kids if tree[j2][3] == "advmod" and norm(tree[j2][0]) in ("mas", "menos")]
                    for k in group(j, ("NOUN", "PROPN")):
                        pr = _prep(tree, k) or base
                        for sk in subjects:
                            if cmp_ and upos == "ADJ" and any(tree[m][3] in ("mark", "case") and norm(tree[m][0]) == "que" for m in _children(tree, j) + kids):
                                add(sk, f"{cmp_[0]}_{_lem(tree, i)}_que", k)          # "Luis es mas alto que Pedro"
                            else:
                                add(sk, _lem(tree, i) + ("_" + pr if pr else ""), k)
                        found = True
            if not found and upos in ("NOUN", "PROPN") and resolve_rel:
                cop_f = next(norm(tree[j][0]) for j in kids if tree[j][3] == "cop")
                for sk in subjects:
                    # "Luis esta contento": la escuela lo etiqueta NOUN, pero "estar + palabra" es un estado, no una clase
                    add(sk, "estar" if cop_f.startswith("est") else "es", i)          # "un perro es un animal"
                    if not cop_f.startswith("est") and upos == "NOUN":
                        for a in kids:
                            if tree[a][3] == "amod" and tree[a][1] == "ADJ":
                                add(sk, "ser", a)                                  # "un gorrion es un pajaro pequeno" (parche-58)
            elif not found and upos == "ADJ" and resolve_rel:
                cop = next(norm(tree[j][0]) for j in kids if tree[j][3] == "cop")
                rel_p = "estar" if cop.startswith("est") else "ser"      # parche-55: "La casa es grande" / "Ana esta cansada"
                for a in group(i, ("ADJ",)):
                    for sk in subjects:
                        add(sk, rel_p, a)
        elif upos == "VERB":
            n0 = len(out)
            aux = [norm(tree[j][0]) for j in kids if tree[j][3] == "aux" and norm(tree[j][0]) in MODAL_FORMS]
            vl = (MODAL_FORMS[aux[0]] + "_" if aux else "") + _lem(tree, i)       # "Pedro puede nadar" -> poder_nadar
            for j in kids:
                if tree[j][3] == "obj" and tree[j][1] in obj_ok:
                    # parche-38: "estudia matematicas": la escuela la etiqueta ADJ pero hace de objeto
                    for k in group(j, obj_ok):
                        for sk in subjects:
                            add(sk, vl, k)
                elif tree[j][3] in ("obl", "iobj") and tree[j][1] in ("NOUN", "PROPN") and j not in skip:
                    base = _prep(tree, j)
                    locadv = next((norm(tree[j2][0]) for j2 in kids if tree[j2][3] == "advmod" and norm(tree[j2][0]) in LOC_ADV), None)
                    for k in group(j, ("NOUN", "PROPN")):
                        pr = _prep(tree, k) or base
                        if pr in LOC_ADV:
                            pr = pr + "_de"                                   # "trabaja cerca de Madrid" (la escuela lo lee como preposicion)
                        for sk in subjects:
                            if locadv and pr == "de":                          # "vive lejos de Madrid"
                                add(sk, vl + "_" + locadv + "_de", k)
                            else:
                                add(sk, vl + ("_" + pr if pr else ""), k)
                elif tree[j][3] == "advmod" and norm(tree[j][0]) in LOC_ADV:          # "esta encima de la mesa" (parche-56)
                    for k2 in _children(tree, j):
                        if tree[k2][3] == "obl" and tree[k2][1] in ("NOUN", "PROPN"):
                            pr = _prep(tree, k2)
                            for sk in subjects:
                                add(sk, vl + "_" + norm(tree[j][0]) + ("_" + pr if pr else ""), k2)
            if _lem(tree, i) in DATIVE_VERBS and not any(f["p"] == vl + "_a" for f in out[n0:]):   # "Ana da un libro a Luis" (la escuela cuelga "a Luis" del libro)
                for j in kids:
                    if tree[j][3] == "obj":
                        for k in _children(tree, j):
                            if tree[k][3] in ("nmod", "obl", "iobj") and tree[k][1] in ("NOUN", "PROPN") and _prep(tree, k) == "a":
                                for sk in subjects:
                                    add(sk, vl + "_a", k)
            xc = [j for j in kids if tree[j][3] == "xcomp" and tree[j][1] == "VERB"]
            for j in xc:                                       # "Ana quiere comer pan" -> querer_comer
                pre = _lem(tree, i) + "_" + _lem(tree, j)
                got = False
                for k2 in _children(tree, j):
                    if tree[k2][3] == "obj" and tree[k2][1] in obj_ok:
                        for k in group(k2, obj_ok):
                            for sk in subjects:
                                add(sk, pre, k)
                                got = True
                    elif tree[k2][3] in ("obl", "iobj") and tree[k2][1] in ("NOUN", "PROPN") and k2 not in skip:
                        base = _prep(tree, k2)
                        for k in group(k2, ("NOUN", "PROPN")):
                            pr = _prep(tree, k) or base
                            for sk in subjects:
                                add(sk, pre + ("_" + pr if pr else ""), k)
                                got = True
                if not got:
                    for sk in subjects:
                        add(sk, pre, None)
            cc = [j for j in kids if tree[j][3] == "ccomp"]
            if cc and _is_say(tree, i):                        # "Pedro dice que Ana vino": se guarda lo DICHO, no como hecho
                mk = [m for m in _children(tree, cc[0]) if tree[m][3] == "mark"]
                mark_i = mk[0] if mk else cc[0]
                clause = [k for k in range(mark_i + 1, len(tree)) if tree[k][1] != "PUNCT"]
                if clause and subjects:
                    sj0 = subjects[0]
                    if isinstance(sj0, str):
                        sname = sdisp = sj0
                    else:
                        part = [k for k in _span(tree, sj0) if k < mark_i]
                        sname = "_".join(norm(tree[k][0]) for k in part)
                        sdisp = " ".join(tree[k][0] for k in part)
                    out.append({"s": sname, "p": _lem(tree, i) + "_que", "o": "_".join(norm(tree[k][0]) for k in clause), "neg": neg,
                                "head": i, "si": None, "oi": None, "when": "", "when_disp": "", "when_idx": [],
                                "template": "{s} " + tree[i][0].lower() + " que {o}", "s_disp": sdisp,
                                "o_disp": " ".join(tree[k][0] for k in clause)})
            elif len(out) == n0 and not xc and not cc:         # verbo sin complementos: "Luis llego" -> (luis, llegar, _)
                for sk in subjects:
                    add(sk, vl, None)
    return out


def triples(tree: Tree, resolve_rel: bool = True) -> List[Tuple[str, str, str]]:
    return [(t["s"], t["p"], t["o"]) for t in triples_full(tree, resolve_rel=resolve_rel)]


NP_REL = {"det", "flat", "amod", "nummod", "compound"}


def _span(tree: Tree, i: int) -> List[int]:
    """Sintagma nominal: la palabra nucleo y sus determinantes, nombres compuestos y adjetivos."""
    out, todo = {i}, [i]
    while todo:
        for j in _children(tree, todo.pop()):
            if tree[j][3] in NP_REL and j not in out:
                out.add(j); todo.append(j)
    return sorted(out)


def surface(tree: Tree, t: Dict) -> Dict:
    """Plantilla de superficie de una proposicion ("{s} vive en {o}") y como se escribian sujeto y objeto (parche-35).
    Sirve para RESPONDER con las mismas palabras que uso la persona."""
    if t.get("si") is None or any(w[3] in ("conj", "cc") for w in tree):
        return {}                                   # con coordinaciones no hay una plantilla unica fiable
    forms = [w[0] for w in tree]
    ss, os_ = _span(tree, t["si"]), (_span(tree, t["oi"]) if t.get("oi") is not None else [])
    if set(ss) & set(os_):
        return {}
    drop = {j for j in _children(tree, t["head"]) if tree[j][3] == "advmod" and norm(tree[j][0]) in NEG} | set(t.get("when_idx", []))
    toks = []
    stop = next((m for m, row in enumerate(tree) if norm(row[0]) == "porque" and m >= 2), len(forms))
    for k, f in enumerate(forms):
        if k >= stop:
            break
        if k in drop or tree[k][1] == "PUNCT":
            continue
        if k == ss[0]:
            toks.append("{s}")
        elif os_ and k == os_[0]:
            toks.append("{o}")
        elif k in ss or k in os_:
            continue
        else:
            toks.append(f if (k > 0 and tree[k][1] == "PROPN") else (f.lower() if k == 0 else f))
    text = " ".join(toks)
    text = text.replace(" de el ", " del ").replace(" a el ", " al ")

    def disp(span):
        words = [forms[k] for k in span]
        if span[0] == 0 and tree[span[0]][1] != "PROPN":
            words[0] = words[0].lower()
        return " ".join(words).replace("de el", "del")

    return {"template": text, "s_disp": disp(ss), "o_disp": disp(os_) if os_ else ""}
