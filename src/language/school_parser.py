"""La escuela dentro de la conversacion (parche-32/34): frase libre -> proposiciones, sin plantillas."""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence

from .extract import surface, triples_full
from .irregulares import IRREG
from .lexicon import norm as _norm
from .ud import School, predict_trees


class SchoolParser:
    def __init__(self, model: School, device="cpu", scripts: Sequence = (), overrides: Optional[Dict[str, str]] = None):
        self.model, self.device, self.scripts = model.to(device).eval(), device, list(scripts)
        self.overrides = {**IRREG, **(overrides or {})}      # forma -> lema, ensenados con ENTENDI (verbos irregulares)

    @staticmethod
    def _forms(sentence: str):
        text = re.sub(r"\bdel\b", "de el", sentence, flags=re.I)
        text = re.sub(r"\bal\b", "a el", text, flags=re.I)
        forms = re.findall(r"\w+|[^\w\s]", text)
        if forms and forms[-1] not in ".!?;:":
            forms.append(".")                      # el entrenamiento siempre veia la frase cerrada con signo de puntuacion
        return forms

    def tree(self, sentence: str):
        """[(forma, upos, head, deprel, lema)] por palabra."""
        forms = self._forms(sentence)[:40]
        pred = predict_trees(self.model, [forms], self.device, self.scripts)[0]
        rows = [(f, u, h, r, l) for f, (u, h, r, l) in zip(forms, pred)]
        rows = self._fix_name_adj(self._fix_name_verb(rows))
        rows = self._fix_verb_complement(self._fix_relative(self._fix_name_noun_inverted(rows)))      # parche-76
        rows = self._fix_flat_across_verb(self._fix_subject_verb_appos(self._fix_verb_name_inverted(rows)))      # parche-76 (B)
        rows = self._fix_comparative(self._fix_participle_state(rows))      # parche-77
        rows = self._fix_lo_contrario(self._fix_temporal_appos(rows))      # parche-82 / parche-83
        return [(f, u, h, r, (self.overrides.get(f.lower()) or self.overrides.get(_norm(f)) or self._lema_regular(f, l)) if u == "VERB" else l)
                for f, u, h, r, l in rows]

    @staticmethod
    def _fix_name_verb(rows):
        """"Ana duerme." / "Andres cocina pasta.": la escuela lee nombre + palabra en minuscula como un nombre compuesto (flat).
        Un nombre propio no sigue en minusculas: esa palabra es el verbo (parche-55)."""
        rows = [list(x) for x in rows]
        for k in range(1, len(rows)):                      # "mas baja que Clara": un nombre tras "que" no es sujeto, es el termino comparado
            if rows[k][3] == "csubj" and rows[k - 1][3] == "mark" and rows[k - 1][0].lower() == "que":
                rows[k][3] = "nmod"
        for k, (f, u, h, r, l) in enumerate(rows):
            # "Sara vino.": "vino" (verbo) leido como NOUN raiz con sujeto nombre propio y sin determinante
            if (r == "root" and u in ("NOUN", "ADJ", "ADV") and _norm(f) in IRREG and
                    any(x[3] == "nsubj" and x[2] == k + 1 and x[1] in ("PROPN", "NOUN") for x in rows) and
                    not any(x[3] == "det" and x[2] == k + 1 for x in rows)):
                rows[k][1] = "VERB"
                continue
            if r != "flat" or not f[:1].islower() or h < 1 or h - 1 >= k or u == "PUNCT":
                continue
            name = h - 1
            if not rows[name][0][:1].isupper() or rows[name][3] not in ("root", "nsubj"):
                continue
            name_head, name_rel = rows[name][2], rows[name][3]
            if name_rel == "nsubj" and name_head != k + 1 and name_head != 0:
                continue                                    # el nombre es sujeto de OTRO verbo: no tocar
            rows[k][1], rows[k][2], rows[k][3] = "VERB", 0, "root"
            rows[name][2], rows[name][3] = k + 1, "nsubj"
            first_obj = True
            for j in range(k + 1, len(rows)):
                if rows[j][2] == name + 1 or (rows[j][3] == "flat" and rows[j][2] == k + 1):
                    if rows[j][3] == "flat" and rows[j][1] in ("NOUN", "ADJ", "PROPN") and first_obj:
                        rows[j][1] = "NOUN" if rows[j][1] == "ADJ" else rows[j][1]
                        rows[j][2], rows[j][3] = k + 1, "obj"
                        first_obj = False
                    elif rows[j][3] != "flat":
                        rows[j][2] = k + 1
                    else:
                        rows[j][2] = k + 1
            break
        return [tuple(x) for x in rows]

    @staticmethod
    def _fix_name_adj(rows):
        """parche-72: "Clara canta en el coro." / "Clara no compra leche.": la escuela lee el nombre propio como ADJ (amod del verbo).
        Si es la primera palabra, empieza en mayuscula, cuelga de un verbo a su derecha (solo "no/nunca/jamas/tampoco" entre medias),
        no lleva determinante y el verbo no tiene otro sujeto, es un nombre propio sujeto."""
        if len(rows) < 3:
            return rows
        f, u, h, r, l = rows[0][:5]
        if u != "ADJ" or r not in ("amod", "nsubj") or not (f[:1].isupper() and f[1:].islower()) or h < 2:
            return rows
        v = h - 1
        if v < len(rows) and rows[v][1] == "NOUN" and rows[v][3] == "root" and rows[v][0][:1].islower() \
                and any(y[2] == h and y[3] == "obj" for y in rows) \
                and not any(y[2] == h and y[3] in ("nsubj", "csubj", "det") for y in rows[1:]) \
                and not rows[v][0].lower().endswith(("ar", "er", "ir", "ando", "iendo")):
            rows = list(rows)                                  # parche-77: "Clara compra pan.": el verbo leido como NOUN raiz con objeto
            rows[v] = (rows[v][0], "VERB") + tuple(rows[v][2:])
        if v >= len(rows) or rows[v][1] != "VERB" or rows[v][0].lower().endswith(("ar", "er", "ir", "ando", "iendo")):
            return rows
        if any(_norm(rows[k][0]) not in ("no", "nunca", "jamas", "tampoco") for k in range(1, v)):
            return rows
        if any(x[2] == 1 and x[3] == "det" for x in rows[1:]):
            return rows
        if any(x[2] == h and x[3] in ("nsubj", "csubj") for x in rows[1:]):
            return rows
        return [(f, "PROPN", h, "nsubj", l)] + list(rows[1:])

    @staticmethod
    def _fix_name_noun_inverted(rows):
        """parche-76: "Lucia cocina pasta y su hermana prepara ensalada.": la escuela lee el nombre como VERB (amod) y el verbo como NOUN (obj),
        con un ciclo entre las dos primeras palabras. Se devuelve el nombre como sujeto y el verbo como verbo (coordinado con la raiz si la hay)."""
        if len(rows) < 4:
            return rows
        f0, u0, h0, r0 = rows[0][:4]
        f1, u1, h1, r1 = rows[1][:4]
        if not (u0 == "VERB" and h0 == 2 and f0[:1].isupper() and f0[1:].islower() and u1 == "NOUN" and h1 == 1 and r1 == "obj"):
            return rows
        rows = [list(x) for x in rows]
        root = next((k for k, x in enumerate(rows) if x[2] == 0 and k > 1), None)
        rows[0][1], rows[0][2], rows[0][3] = "PROPN", 2, "nsubj"
        rows[1][1] = "VERB"
        rows[1][2], rows[1][3] = (0, "root") if root is None else (root + 1, "conj")
        if len(rows[1]) > 4 and _norm(rows[1][4]) == _norm(f1) and f1.lower().endswith("a"):
            rows[1][4] = f1.lower()[:-1] + "ar"                      # cocina -> cocinar (la escuela lo lemaba como el sustantivo)
        for j in range(2, len(rows)):
            if rows[j][2] == 2 and rows[j][3] in ("amod", "compound") and rows[j][1] in ("NOUN", "ADJ"):
                rows[j][1], rows[j][3] = "NOUN", "obj"
        return [tuple(x) for x in rows]

    @staticmethod
    def _fix_relative(rows):
        """parche-76: "El nino que rompio la ventana vive en Toledo.": la escuela etiqueta "que" como mark de la subordinada (acl) y no como su
        sujeto; el extractor solo resuelve el relativo si "que" es el sujeto. Se relabela "que" (justo antes del verbo, sin otro sujeto)."""
        rows = [list(x) for x in rows]
        for k, x in enumerate(rows):
            if x[3] != "acl" or x[1] != "VERB" or x[2] <= 0 or k < 1:
                continue
            q = rows[k - 1]
            if _norm(q[0]) == "que" and q[3] == "mark" and q[2] == k + 1 and \
                    not any(y[2] == k + 1 and y[3] in ("nsubj", "csubj") for y in rows):
                q[1], q[3] = "PRON", "nsubj"
        return [tuple(x) for x in rows]

    @staticmethod
    def _fix_verb_complement(rows):
        """parche-76: "Pedro cocina pasta." / "Andres cocina pasta.": la escuela cuelga "pasta" del verbo como amod (NOUN) o compound (ADJ) en vez
        de obj. Un sustantivo (o adjetivo compound) en minuscula, a la derecha de un verbo sin ningun complemento, es su objeto directo."""
        from .extract import FREQ_ADV, TIME_ADV, TIME_NOUNS
        rows = [list(x) for x in rows]
        for v, x in enumerate(rows):
            if x[1] != "VERB":
                continue
            kids = [j for j, y in enumerate(rows) if y[2] == v + 1]
            if any(rows[j][3] in ("obj", "obl", "iobj", "ccomp", "xcomp", "cop", "nmod") for j in kids):
                continue
            for j in kids:
                y = rows[j]
                forma = _norm(y[0])
                if j > v and y[0][:1].islower() and forma not in TIME_NOUNS and forma not in TIME_ADV and forma not in FREQ_ADV \
                        and ((y[1] == "NOUN" and y[3] in ("amod", "compound")) or (y[1] == "ADJ" and y[3] == "compound")) \
                        and not any(z[2] == j + 1 and z[3] == "det" for z in rows):
                    y[1], y[3] = "NOUN", "obj"
                    break
        return [tuple(x) for x in rows]

    @staticmethod
    def _fix_verb_first(rows, verbs):
        """parche-76: "Tomas no bebe cafe. Bebe agua.": la escuela lee "Bebe" como NOUN sujeto y "agua" como verbo. Si la forma ya se vio como VERBO
        antes en el mismo texto (verbs = {forma: lema}), la frase empieza por el verbo (sujeto omitido) y la segunda palabra es su objeto."""
        if not verbs or len(rows) < 3:
            return rows
        f0, u0, h0, r0 = rows[0][:4]
        f1, u1, h1, r1 = rows[1][:4]
        if not (u0 in ("NOUN", "ADJ") and r0 == "nsubj" and h0 == 2 and f0[:1].isupper() and u1 == "VERB" and h1 == 0 and _norm(f0) in verbs):
            return rows
        if any(y[2] == 1 for y in rows[1:]):
            return rows
        rows = [list(x) for x in rows]
        rows[0][1], rows[0][2], rows[0][3] = "VERB", 0, "root"
        if len(rows[0]) > 4:
            rows[0][4] = verbs[_norm(f0)]
        rows[1][1], rows[1][2], rows[1][3] = "NOUN", 1, "obj"
        for j in range(2, len(rows)):
            if rows[j][2] == 2:
                rows[j][2] = 1
        return [tuple(x) for x in rows]

    _VERB_EXTRA = {"nada", "nadan"}          # "nada" se quito de IRREG (casi siempre pronombre); detras de un sustantivo si es verbo

    @staticmethod
    def _fix_verb_name_inverted(rows):
        """parche-76: "Vino Sara." (pregunta "¿Vino Sara?"): la escuela lee "Vino Sara" como un nombre compuesto (PROPN + flat). Si la primera palabra es
        una forma verbal conocida (IRREG), es el VERBO y la segunda su sujeto."""
        if len(rows) < 3:
            return rows
        f0, u0, h0, r0 = rows[0][:4]
        f1, u1, h1, r1 = rows[1][:4]
        if not (u0 == "PROPN" and r0 == "root" and f0[:1].isupper() and _norm(f0) in IRREG and u1 == "PROPN" and r1 == "flat" and h1 == 1
                and not any(y[2] == 1 and y[1] != "PUNCT" for y in rows[2:])):
            return rows
        rows = [list(x) for x in rows]
        rows[0][1] = "VERB"
        if len(rows[0]) > 4:
            rows[0][4] = IRREG[_norm(f0)]
        rows[1][3] = "nsubj"
        return [tuple(x) for x in rows]

    @staticmethod
    def _fix_subject_verb_appos(rows):
        """parche-76: "Una gaviota vuela." / "Xqx nada en la piscina.": sin ningun verbo, la escuela deja el sustantivo como raiz y el verbo como
        appos (NOUN/PRON). Si esa palabra es una forma verbal conocida (IRREG o nada/nadan), pasa a ser el verbo y el sustantivo su sujeto."""
        if len(rows) < 3 or any(x[1] == "VERB" for x in rows):
            return rows
        root = next((k for k, x in enumerate(rows) if x[2] == 0), None)
        if root is None or rows[root][1] not in ("NOUN", "PROPN"):
            return rows
        cand = [k for k, x in enumerate(rows) if ((x[2] == root + 1 and x[3] in ("appos", "flat")) or (x[2] == 0 and k == root + 1))
                and x[1] in ("NOUN", "PRON", "ADV", "ADJ")
                and x[0][:1].islower() and (_norm(x[0]) in IRREG or _norm(x[0]) in SchoolParser._VERB_EXTRA)]
        if len(cand) != 1 or cand[0] < root:
            return rows
        k = cand[0]
        rows = [list(x) for x in rows]
        rows[k][1], rows[k][2], rows[k][3] = "VERB", 0, "root"
        if len(rows[k]) > 4:
            rows[k][4] = IRREG.get(_norm(rows[k][0]), "nadar")
        rows[root][2], rows[root][3] = k + 1, "nsubj"
        for j, y in enumerate(rows):
            if j in (root, k):
                continue
            if y[2] == root + 1 and y[3] in ("det", "amod", "flat", "nummod"):
                continue                                           # los determinantes siguen colgando del sustantivo
            if y[2] == root + 1 or (y[2] == k + 1 and y[3] == "nmod" and y[1] in ("NOUN", "PROPN")):
                y[2] = k + 1
                if y[3] == "nmod":
                    y[3] = "obl"
            if y[3] == "punct":
                y[2] = k + 1
        return [tuple(x) for x in rows]

    @staticmethod
    def _fix_flat_across_verb(rows):
        """parche-76: "Rosa lee Xqx.": la escuela cuelga el nombre de la derecha (flat) del sujeto, saltando el verbo. Un flat nunca cruza un verbo:
        es el objeto de ese verbo."""
        rows = [list(x) for x in rows]
        for j, x in enumerate(rows):
            if x[3] == "flat" and x[2] >= 1 and x[2] - 1 < j:
                v = next((k for k in range(x[2], j) if rows[k][1] == "VERB"), None)
                if v is not None:
                    x[2], x[3] = v + 1, "obj"
        return [tuple(x) for x in rows]

    @staticmethod
    def _lema_regular(form, lema):
        """parche-76: un VERBO cuyo lema es la propia forma o solo su raiz ("cocina"->"cocina", "respira"->"respir") se regulariza a -ar si la forma
        acaba en -a/-an (3.a persona de los verbos en -ar)."""
        f = _norm(form)
        l = _norm(lema)
        if f.endswith("an") and len(f) > 4 and l in (f, f[:-2]):
            return f[:-2] + "ar"
        if f.endswith("a") and len(f) > 3 and l in (f, f[:-1]):
            return f[:-1] + "ar"
        return lema
    @staticmethod
    def _fix_participle_state(rows):
        """parche-77: "Ana esta cansada.": la escuela etiqueta el participio como VERB raiz con la copula "esta". Con "estar" + participio es un
        estado (adjetivo): (ana, estar, cansada) y no (ana, cansar). Con "ser" seria una pasiva y no se toca."""
        rows = [list(x) for x in rows]
        for v, x in enumerate(rows):
            if x[1] == "VERB" and _norm(x[0]).endswith(("ado", "ada", "ados", "adas", "ido", "ida", "idos", "idas")) \
                    and any(y[2] == v + 1 and y[3] == "cop" and _norm(y[0]).startswith("est") for y in rows):
                x[1] = "ADJ"
                if len(x) > 4:
                    x[4] = x[0].lower()
        return [tuple(x) for x in rows]

    @staticmethod
    def _fix_comparative(rows):
        """parche-77/78: "Sara es mas baja que Rosa.": el termino de la comparacion (nombre tras "que", con "mas/menos" + adjetivo en la frase) es siempre
        un nmod del adjetivo, con "que" como case, sea cual sea la etiqueta que le ponga la escuela (nsubj, csubj, appos, flat, nmod, ADJ...).
        Si el adjetivo ha quedado colgando de otro nombre y la frase no tiene raiz, el adjetivo pasa a ser la raiz."""
        rows = [list(x) for x in rows]
        for r, x in enumerate(rows):
            if r < 1 or x[3] in ("punct", "root", "det", "case", "mark", "cc", "cop", "advmod") or x[2] == r + 1:      # parche-78: cualquier etiqueta
                continue
            if x[1] not in ("PROPN", "NOUN") and not (x[1] == "ADJ" and x[0][:1].isupper()):
                continue
            q = rows[r - 1]
            if _norm(q[0]) != "que" or q[2] != r + 1 or q[3] not in ("mark", "case"):
                continue
            hs = [y[2] for y in rows if _norm(y[0]) in ("mas", "menos") and y[3] == "advmod" and 0 < y[2] < r]
            if not hs:
                continue
            h = hs[0]
            if rows[h - 1][1] != "ADJ" and not any(y[2] == h and y[3] == "cop" for y in rows):
                continue
            if h - 1 == r:
                continue
            if rows[h - 1][2] != 0 and not any(y[2] == 0 for y in rows):      # sin raiz: el adjetivo (colgado de un nombre) pasa a ser la raiz
                rows[h - 1][2], rows[h - 1][3] = 0, "root"
            x[2], x[3] = h, "nmod"
            q[3] = "case"
            if x[1] == "ADJ":
                x[1] = "PROPN"
        return [tuple(x) for x in rows]

    @staticmethod
    def _fix_temporal_appos(rows):
        """parche-82: "Los lunes Nico va al gimnasio.": la escuela cuelga el nombre propio como aposicion del adverbial temporal ("lunes"). Un nombre propio
        que sigue a un sintagma temporal (dia/parte del dia/estacion, plural o con determinante) y precede a un verbo raiz sin sujeto es el sujeto."""
        TEMP = {"lunes", "martes", "miercoles", "jueves", "viernes", "sabados", "sabado", "domingos", "domingo", "tardes", "noches", "mananas", "veranos",
                "inviernos", "dias", "semanas", "meses", "anos", "fines"}
        rows = [list(x) for x in rows]
        for r, x in enumerate(rows):
            if x[1] != "PROPN" or x[3] not in ("appos", "flat", "nmod") or x[2] < 1:
                continue
            t = rows[x[2] - 1]
            if t[1] != "NOUN" or _norm(t[0]) not in TEMP or x[2] - 1 > r:
                continue
            v = next((k for k, y in enumerate(rows) if y[2] == 0 and y[1] == "VERB" and k > r), None)
            if v is None or any(y[2] == v + 1 and y[3] in ("nsubj", "csubj") for y in rows):
                continue
            x[2], x[3] = v + 1, "nsubj"
        return [tuple(x) for x in rows]

    @staticmethod
    def _fix_lo_contrario(rows):
        """parche-83: "Lo contrario de grande es pequeno.": la escuela deja "pequeno" como raiz y "contrario" como su sujeto. Se invierte para que sea
        igual que "Pequeno es lo contrario de grande": "contrario" raiz, "pequeno" su sujeto, la copula colgada de "contrario"."""
        rows = [list(x) for x in rows]
        for c, x in enumerate(rows):
            if _norm(x[0]) != "contrario" or x[3] != "nsubj" or x[2] < 1:
                continue
            r = x[2] - 1
            if rows[r][2] != 0 or not any(y[2] == c + 1 and y[3] == "det" and _norm(y[0]) == "lo" for y in rows):
                continue
            cop = [k for k, y in enumerate(rows) if y[2] == r + 1 and y[3] == "cop"]
            if not cop:
                continue
            x[2], x[3] = 0, "root"
            rows[r][2], rows[r][3] = c + 1, "nsubj"
            for k in cop:
                rows[k][2] = c + 1
            for k, y in enumerate(rows):
                if k not in (c, r) and y[2] == r + 1 and y[3] in ("punct",):
                    y[2] = c + 1
            if rows[r][1] == "ADJ":
                rows[r][1] = "PROPN" if rows[r][0][:1].isupper() else "NOUN"
        for c, x in enumerate(rows):                  # "Lo contrario de grande es Xqx." (pregunta reescrita): la copula cuelga del sujeto; se pasa a "contrario"
            if _norm(x[0]) == "contrario" and x[3] == "root":
                sj = [k for k, y in enumerate(rows) if y[2] == c + 1 and y[3] == "nsubj"]
                for k, y in enumerate(rows):
                    if y[3] == "cop" and (y[2] - 1) in sj:
                        y[2] = c + 1
        return [tuple(x) for x in rows]

    @staticmethod
    def _fix_inverted_subject(rows):
        """parche-76: "Vuela una gaviota." (de "¿Vuela una gaviota?"): verbo al principio sin sujeto y un unico sintagma nominal con determinante
        como "objeto": es el sujeto pospuesto. Solo se aplica sin tema previo (en un discurso, "Compra un coche." es sujeto omitido + objeto)."""
        if len(rows) < 3 or rows[0][1] != "VERB" or rows[0][2] != 0:
            return rows
        kids = [j for j, y in enumerate(rows) if y[2] == 1 and y[1] != "PUNCT"]
        if len(kids) != 1 or rows[kids[0]][3] != "obj" or rows[kids[0]][1] != "NOUN":
            return rows
        j = kids[0]
        if any(z[2] == j + 1 and z[3] != "det" for z in rows):       # "Tiene un triangulo lados.": el sintagma lleva mas dependientes: no es un sujeto solo
            return rows
        if not any(z[2] == j + 1 and z[3] == "det" and _norm(z[0]) in ("un", "una", "unos", "unas", "el", "la", "los", "las") for z in rows):
            return rows
        rows = [list(x) for x in rows]
        rows[j][3] = "nsubj"
        return [tuple(x) for x in rows]

    def _conjunto(self, m, topic=None, verbs=None):
        """parche-94: definicion por enumeracion. "El Sistema Solar es el conjunto de planetas, asteroides, cometas y lunas que orbitan alrededor del Sol."
        -> (sistema_solar conjunto_de X) por cada elemento, y la oracion de relativo se aplica a cada elemento plural: (X orbitar_alrededor_de sol)."""
        subj = m.group(1).strip()
        key = "_".join(re.sub(r"^(el|la|los|las)\s+", "", _norm(subj)).split())
        body, rel = m.group(2), ""
        parts = re.split(r"\s+(?:que|los que|las que)\s+", body, maxsplit=1)
        if len(parts) == 2:
            body, rel = parts
        items = []
        for it in re.split(r"\s*,\s*|\s+y\s+|\s+e\s+|\s*\.\.\.\s*|\s*…\s*|\s+etc\.?", body):
            it = re.sub(r"^(el|la|los|las|un|una|unos|unas)\s+", "", it.strip(" .;"), flags=re.I)
            if it and len(it.split()) <= 3:
                items.append(it)
        out = []
        for it in items:
            ik = "_".join(_norm(it).split())
            out.append({"s": key, "p": "conjunto_de", "o": ik, "neg": False, "head": 0, "si": None, "oi": None, "when": "", "when_disp": "", "when_idx": [], "q": "",
                        "template": "{s} es el conjunto de {o}", "s_disp": subj[:1].lower() + subj[1:], "o_disp": it.lower()})
        if rel and out:
            for it in items:
                if it.lower().endswith("s"):
                    try:
                        sub = self.parse(f"Los {it} {rel.strip(' .')}.", topic, verbs) or []
                    except Exception:                                  # noqa
                        sub = []
                    out += sub
        return out or None

    def parse(self, sentence: str, topic: Optional[str] = None, verbs=None) -> Optional[List[Dict]]:
        """None si no es una afirmacion analizable (pregunta, demasiado corta o larga); si no, lista de proposiciones."""
        if "?" in sentence or "¿" in sentence:
            return None
        mll = re.fullmatch(r"\s*((?:el|la|mi|su|un|una)\s+\S+(?:\s+(?:de|del)\s+\S+)?)\s+se\s+llama\s+(\S+?)\s*[.!]?\s*", sentence, re.I)
        if mll and mll.group(2)[:1].isupper():       # parche-86: "El perro de Irene se llama Toby.": el nombre propio de una cosa
            subj = mll.group(1)
            key = "_".join(re.sub(r"^(el|la|mi|su|un|una)\s+", "", _norm(subj)).split())
            return [{"s": key, "p": "llamarse", "o": _norm(mll.group(2)), "neg": False, "head": 0, "si": None, "oi": None, "when": "", "when_disp": "",
                     "when_idx": [], "q": "", "template": "{s} se llama {o}", "s_disp": subj[:1].upper() + subj[1:], "o_disp": mll.group(2)}]
        mcj = re.fullmatch(r"\s*((?:el|la|los|las)\s+[^,.:;]+?)\s+(?:es|son|era|eran)\s+(?:el|la)\s+(?:conjunto|grupo|totalidad|colecci[oó]n|serie)\s+de\s+(.+?)\s*[.!]?\s*", sentence, re.I)
        if mcj:
            return self._conjunto(mcj, topic, verbs)               # parche-94: "El Sistema Solar es el conjunto de planetas, ... que orbitan ..."
        from datetime import date
        from src.language.fechas import extract_abs
        sentence, abs_iv, abs_disp = extract_abs(sentence, getattr(self, "today", None) or date.today())
        forms = self._forms(sentence)
        if not 3 <= len(forms) <= 40:         # 3 = "Envia paquetes ." (sujeto omitido)
            return None
        tree = self._fix_verb_first(self.tree(sentence), verbs)
        if topic is None:
            tree = self._fix_inverted_subject(tree)
        found = triples_full(tree, entities_only=True, default_subject=topic)
        if not found and topic and sentence[:1].isupper():
            # "Bebe agua.": con mayuscula inicial la escuela puede leer el verbo como nombre; se reintenta en minuscula
            tree2 = self.tree(sentence[:1].lower() + sentence[1:])
            alt = triples_full(tree2, entities_only=True, default_subject=topic)
            if alt:
                tree, found = tree2, alt
        sino = [k for k, w_ in enumerate(tree) if _norm(w_[0]) == "sino"]
        if sino:                                     # parche-81: "Fernando no vive en Madrid sino en Toledo": lo que sigue a "sino" es afirmativo
            for t in found:
                if t.get("neg") and t.get("oi") is not None and t["oi"] > sino[0]:
                    t["neg"] = False
        for t in found:
            if t.get("when") and any(_norm(w_[0]) in ("los", "las") and (k + 1) in t.get("when_idx", []) and _norm(tree[k + 1][0]) not in ("tres", "dos", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce", "una") and not _norm(tree[k + 1][0]).isdigit() for k, w_ in enumerate(tree[:-1])):
                t["when"], t["when_disp"] = "", ""             # parche-82: "Los lunes ...": es habitual, no una fecha concreta
            t.update(surface(tree, t))
            if abs_iv and not t.get("when"):
                t["when"], t["when_disp"] = "abs:" + abs_iv, abs_disp
        return found
