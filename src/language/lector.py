"""parche-113: LECTOR DE TEXTOS. Aprende de textos largos (articulos, apuntes, paginas copiadas) sin limite de tamaño y sin LLM.

Tuberia:  limpiar (citas [5], parentesis, incisos, titulos)  ->  segmentar en frases y clausulas  ->  resolver el TEMA (él/ella/«Es…»/«Su X…»/«Este animal…»)
          ->  extraer con PATRONES PROPIOS (copulativas, verbales, pasivas, tener, listas, nombres cientificos, fechas)  ->  lo que no se entiende, a la escuela
          (frases cortas con el sujeto puesto)  ->  informe: hechos aprendidos con su frase de origen, frases no entendidas con el motivo.
Los patrones funcionan sin la escuela (se pueden medir en cualquier maquina); la escuela solo se usa para lo que ellos no cubren.
Los hechos se guardan como el resto de la memoria: SUJETO / PREDICADO (verbo_prep) / OBJETO en mayusculas, con su texto para contestar con las mismas palabras."""
from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Callable, Dict, List, Optional, Tuple

MAX_TEXTO = 400_000
_DIR = os.path.dirname(os.path.abspath(__file__))


def nrm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(c) != "Mn")


def clave(s: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^A-Z0-9Ñ]+", "_", nrm(s).upper().replace("ñ", "Ñ").replace("n̈", "Ñ"))).strip("_")


# ====================================================== léxico y morfología ===============================================================
class Lex:
    """Verbos, adjetivos y sustantivos conocidos (data/lexico_es.json) + conjugaciones generadas. Se carga una vez."""
    _i = None

    def __init__(self):
        self.V, self.A, self.N = set(), set(), set()
        try:
            d = json.load(open(os.path.join(_DIR, "..", "..", "data", "lexico_es.json"), encoding="utf-8"))
            for i, l in d.get("syn", {}).items():
                p = d["pos"].get(i)
                for w in l:
                    if " " in w:
                        continue
                    w = nrm(w)
                    (self.V if p == "v" else self.A if p in ("a", "s") else self.N if p == "n" else set()).add(w)
        except (OSError, ValueError, KeyError):
            pass
        self.forma: Dict[str, str] = {}
        self.part: Dict[str, str] = {}
        for inf in sorted(self.V | _EXTRA_INF):
            self._conj(inf)
        for inf, formas in _IRREG.items():
            for f in formas.split():
                self.forma.setdefault(f, inf)
            self.V.add(inf)
        for f, inf in _PART_IRREG.items():
            self.part[f] = inf

    @classmethod
    def get(cls):
        if cls._i is None:
            cls._i = Lex()
        return cls._i

    def _conj(self, inf: str):
        if len(inf) < 4 or inf[-2:] not in ("ar", "er", "ir") or " " in inf or inf.endswith("rse"):
            return
        st, t = inf[:-2], inf[-2:]
        vocal = st[-1] in "aeiou"
        if t == "ar":
            fs = ["a", "an", "o", "aron", "aba", "aban", "ara", "aran", "aria", "arian"]
            pa = ["ado", "ada", "ados", "adas"]
        else:
            e = "e" if t == "er" else "i"
            fs = ["e", "en", "io", "ieron", "ia", "ian", e + "ra", e + "ran", e + "ria", e + "rian"]
            pa = ["ido", "ida", "idos", "idas"]
            if vocal:
                fs += ["yo", "yeron"]
        for f in fs:
            self.forma.setdefault(st + f, inf)
        for f in pa:
            self.part.setdefault(st + f, inf)
        # alternancias vocalicas del presente (e>ie, o>ue, e>i) y del pret. de los -ir (e>i, o>u)
        for i in range(len(st) - 1, max(-1, len(st) - 6), -1):
            if st[i] == "e":
                self.forma.setdefault(st[:i] + "ie" + st[i + 1:] + "e", inf)
                self.forma.setdefault(st[:i] + "ie" + st[i + 1:] + "en", inf)
                self.forma.setdefault(st[:i] + "ie" + st[i + 1:] + "a", inf)
                self.forma.setdefault(st[:i] + "ie" + st[i + 1:] + "an", inf)
                if t == "ir":
                    for f in ("e", "en", "io", "ieron"):
                        self.forma.setdefault(st[:i] + "i" + st[i + 1:] + f, inf)
                break
            if st[i] == "o":
                for f in (("a", "an") if t == "ar" else ("e", "en")):
                    self.forma.setdefault(st[:i] + "ue" + st[i + 1:] + f, inf)
                if t == "ir":
                    for f in ("io", "ieron"):
                        self.forma.setdefault(st[:i] + "u" + st[i + 1:] + f, inf)
                break
        if st.endswith("c") and t == "er":
            self.forma.setdefault(st[:-1] + "zca", inf)
        if st.endswith("c") and t == "ar":
            self.forma.setdefault(st[:-1] + "quen", inf)

    def lema(self, w: str) -> Optional[str]:
        w = nrm(w)
        if w in self.forma:
            return self.forma[w]
        if w in _NO_VERBO:
            return None
        # forma regular de un verbo que el diccionario no tiene: solo terminaciones muy propias de verbo
        if len(w) >= 6 and w not in self.N and w not in self.A:
            for suf, rep in (("aron", "ar"), ("ieron", "er"), ("aban", "ar"), ("ian", "er")):
                if w.endswith(suf):
                    return w[:-len(suf)] + rep
        return None

    def participio(self, w: str) -> Optional[str]:
        w = nrm(w)
        if w in self.part:
            return self.part[w]
        if len(w) > 4 and re.search(r"(ado|ada|ados|adas)$", w):
            return re.sub(r"ad[oa]s?$", "ar", w)
        if len(w) > 4 and re.search(r"(ido|ida|idos|idas)$", w):
            return re.sub(r"id[oa]s?$", "er", w)
        return None

    def es_adj(self, w: str) -> bool:
        w = nrm(w)
        if w in self.A:
            return True
        if w in _NO_ADJ:
            return False
        return bool(len(w) > 4 and re.search(r"(oso|osa|osos|osas|ico|ica|icos|icas|ivo|iva|ivos|ivas|able|ibles?|ables|ante|antes|ente|entes|ario|aria|arios|arias|al|ales|ado|ada|ados|adas|ido|ida|idos|idas|ino|ina|inos|inas|udo|uda|ulo|nal|ar|ares|il|iles|eno|ena|enos|enas|ioso|ional)$", w))


_EXTRA_INF = set("""vivir habitar encontrar medir pesar alimentar reproducir nacer crecer cazar proteger descubrir describir nombrar llamar considerar crear formar existir
aparecer desconcertar liberar producir pervivir reunir representar poner dar aportar usar utilizar servir emplear fundar gobernar escribir publicar construir
dirigir morir ocurrir suceder mantener obtener conocer reconocer asignar derivar proceder ayudar generar contener incluir abarcar componer girar orbitar
poblar extender tener ser estar haber ir hacer poder deber soler""".split())
_IRREG = {
    "ser": "es son era eran fue fueron sera seran seria serian sido siendo", "estar": "esta estan estaba estaban estuvo estuvieron estara estaran",
    "haber": "ha han habia habian hubo habra hay", "ir": "va van iba iban fue fueron ira iran", "tener": "tiene tienen tuvo tuvieron tenia tenian tendra tendran tendria",
    "hacer": "hace hacen hizo hicieron hacia hacian hara haran", "poder": "puede pueden pudo pudieron podia podian podra podran podria",
    "poner": "pone ponen puso pusieron ponia ponian pondra", "decir": "dice dicen dijo dijeron decia decian dira", "ver": "ve ven vio vieron veia veian vera",
    "dar": "da dan dio dieron daba daban dara", "venir": "viene vienen vino vinieron venia venian vendra", "saber": "sabe saben supo supieron sabia sabian sabra",
    "traer": "trae traen trajo trajeron traia traian", "soler": "suele suelen solia solian", "deber": "debe deben debio debieron debia debian",
    "caer": "cae caen cayo cayeron caia", "salir": "sale salen salio salieron salia saldra", "conducir": "conduce conducen condujo condujeron", "producir": "produce producen produjo produjeron",
    "reducir": "reduce reducen redujo", "seguir": "sigue siguen siguio siguieron seguia", "elegir": "elige eligen eligio eligieron", "morir": "muere mueren murio murieron moria",
    "oir": "oye oyen oyo oyeron", "leer": "lee leen leyo leyeron leia", "creer": "cree creen creyo creyeron creia creian", "huir": "huye huyen huyo",
    "quedar": "queda quedan quedo quedaron quedaba", "llamar": "llama llaman llamo llamaron llamaba", "ocurrir": "ocurre ocurren ocurrio ocurrieron",
}
_PART_IRREG = {"hecho": "hacer", "hecha": "hacer", "hechos": "hacer", "dicho": "decir", "dicha": "decir", "puesto": "poner", "puesta": "poner", "puestos": "poner", "visto": "ver", "vista": "ver", "vistos": "ver",
               "escrito": "escribir", "escrita": "escribir", "escritos": "escribir", "descrito": "describir", "descrita": "describir", "descritos": "describir", "cubierto": "cubrir", "cubierta": "cubrir",
               "abierto": "abrir", "abierta": "abrir", "muerto": "morir", "muerta": "morir", "vuelto": "volver", "roto": "romper", "rota": "romper", "sido": "ser", "resuelto": "resolver", "devuelto": "devolver",
               "descubierto": "descubrir", "descubierta": "descubrir", "descubiertos": "descubrir", "propuesto": "proponer", "compuesto": "componer", "compuesta": "componer", "impreso": "imprimir"}
_NO_VERBO = set("""forma formas cuenta cuentas nombre nombres cola colas pico picos piel pieles caza centro cargo cambio canto celebra cuerpo duda estado estados fin fines final finales
hacia sobre entre desde hasta tras para pero sino como cual cuando donde mientras ahora aqui alli mas menos muy casi tambien ademas luego entonces pues mismo misma todo toda
sentido uso usos papel parte partes dato datos paso pasos caso casos medio medios modo modos lado lados fuera dentro cerca lejos junto""".split())
_NO_ADJ = set("""mas menos cual cualquier sin sobre entre desde hasta cuando donde nacional animal general especial total central principal""".split()) - {"nacional", "animal", "general", "especial", "total", "central", "principal"}

DET = set("el la los las un una unos unas uno al del lo este esta estos estas ese esa esos esas aquel aquella aquellos aquellas su sus mi mis tu tus nuestro nuestra nuestros nuestras vuestro vuestra otro otra otros otras "
          "varios varias algun alguna algunos algunas ningun ninguna cada todo toda todos todas mucho mucha muchos muchas poco poca pocos pocas demas ambos ambas cierto cierta ciertos ciertas".split())
PRE_ADJ = set("unico unica unicos unicas primer primero primera primeros primeras segundo segunda tercer tercero ultimo ultima ultimos ultimas gran grandes principal principales mayor mayores menor menores "
              "mejor mejores peor mmas menos propio propia propios propias mismo misma mismos mismas nuevo nueva nuevos nuevas viejo antiguo antigua".split())
NUM = set("dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince veinte treinta cuarenta cincuenta cien ciento mil millon millones".split())
PREP = set("a ante bajo con contra de del desde durante en entre hacia hasta mediante para por segun sin sobre tras como junto".split())
ADV = set("actualmente ademas tambien asimismo solo solamente incluso casi muy mas menos bastante tan tanto ya aun todavia siempre nunca jamas hoy ahora luego despues antes entonces asi principalmente "
          "generalmente normalmente habitualmente comunmente aproximadamente aproximada exactamente tipicamente frecuentemente raramente apenas especialmente igualmente finalmente posteriormente originalmente "
          "recientemente inicialmente probablemente posiblemente realmente efectivamente".split())
CLASE_ENVOLTURA = {"especie": "ESPECIE", "tipo": "TIPO", "clase": "CLASE", "genero": "GENERO", "forma": "FORMA", "grupo": "GRUPO", "familia": "FAMILIA", "orden": "ORDEN", "subespecie": "SUBESPECIE",
                   "variedad": "VARIEDAD", "conjunto": "CONJUNTO", "tipos": "TIPO", "clases": "CLASE", "especies": "ESPECIE", "miembro": "MIEMBRO", "ejemplo": "EJEMPLO"}
TAXON = {"familia", "genero", "orden", "clase", "especie", "subespecie", "reino", "filo", "tribu", "superfamilia", "suborden", "infraorden", "division"}
ABREV = set("sr sra srta sres dr dra prof lic ing aprox ej etc vs cf pag pags págs pág num núm nº nª mª tel fig ed vol cap art av avda cia cía dpto ee uu a.c d.c s ss pp p.ej e.g i.e "
            "sta sto gral cnel pdte ud uds ntra ntro ltda inc jr mr mrs st vda admón máx mín dña excmo excma ilmo ilma fdo atte".split())
SUBORD = re.compile(r"^(?:ya que|puesto que|debido a que|porque|aunque|si bien|mientras que|mientras|pero|sin embargo|por lo que|de modo que|de forma que|cuando|donde|como|tras lo cual|llegando|siendo|aunque)\b", re.I)
RELATIVO = re.compile(r"^(?:que|quien|quienes|el cual|la cual|los cuales|las cuales|donde|cuyo|cuya|cuyos|cuyas)\b", re.I)


# ====================================================== limpieza y segmentación ===========================================================
CITAS = re.compile(r"\[[^\[\]]{0,30}\]|\^\d+")                          # [5], [n. 1], [nota 3], [cita requerida], [editar]
VINETA = re.compile(r"^\s*(?:[•·▪●○◦►‣*]|[-–—](?=\s)|\d{1,2}[.)](?=\s))\s*")
FICHA = re.compile(r"^([A-ZÁÉÍÓÚÑ][^:\t.;!?]{1,44}?)\s*(?::\s+|\t+|\s{3,})(\S.{0,119})$")
_VERBO_FINITO = re.compile(r"\b(?:es|son|fue|fueron|era|eran|está|están|tiene|tienen|hay|ha|han|puede|pueden|se)\b", re.I)


def _ficha(l: str):
    """«Radio medio: 6051,8 km», «Familia: Felidae»: dato de ficha (clave y valor cortos, sin verbo). -> (clave, valor) o None."""
    m = FICHA.match(l)
    if not m:
        return None
    k, v = m.group(1).strip(), m.group(2).strip()
    if len(k.split()) > 5 or len(v.split()) > 14 or _VERBO_FINITO.search(k) or _VERBO_FINITO.search(v):
        return None
    if v.endswith(".") and not re.search(r"\d", v):
        return None
    if not (re.search(r"\d", v) or v[:1].isupper() or len(v.split()) == 1):         # «Importante: no lo olvides» es una frase, no un dato
        return None
    return k, v


def limpiar(texto: str) -> List[Tuple[str, str]]:
    """-> [("titulo"|"parrafo", texto)]. Quita citas [5], espacios raros, lineas de menu y marcadores."""
    out = []
    texto = texto.replace("\r", "\n").replace(" ", " ").replace("​", "")
    for linea in texto.split("\n"):
        l = re.sub(r"(?<=[.!?»”\"])(?:\[[^\[\]]{0,30}\])+(?=[A-ZÁÉÍÓÚÑ¿¡«])", " ", linea)            # parche-127: «médica.[33]De la Fuente» -> dos frases
        l = CITAS.sub("", l)
        f_ = _ficha(re.sub(r"[ ]{2,}", "   ", VINETA.sub("", l.strip())).strip()) if ("\t" in l or ":" in l or "   " in l.strip()) else None
        l = re.sub(r"\s+", " ", l).strip()
        if not l or l.startswith("#") and len(l) < 3 or re.fullmatch(r"[\W_]+", l):
            continue
        l = VINETA.sub("", l.lstrip("#").strip()).strip()
        if f_ and l:
            out.append(("ficha", f_[0] + "\t" + f_[1]))
            continue
        if len(l.split()) <= 9 and not re.search(r"[.!?:;]$", l) and l[:1].isupper() and not re.search(r"\b(?:es|son|fue|fueron|era|tiene|tienen)\b", l):
            out.append(("titulo", l))
        else:
            out.append(("parrafo", l))
    return out


def _abrev_antes(txt: str, i: int) -> bool:
    j = i
    while j > 0 and (txt[j - 1].isalpha() or txt[j - 1] in ".ªº"):
        j -= 1
    w = txt[j:i].lower().rstrip(".")
    return w in ABREV or (len(w) == 1 and w.isalpha() and txt[j:i][:1].isupper()) or bool(re.fullmatch(r"(?:[a-z]\.)+[a-z]", txt[j:i].lower()))


_ARRANQUE = {"el", "la", "los", "las", "un", "una", "unos", "unas", "su", "sus", "en", "tras", "durante", "desde", "con", "por", "para", "al", "del", "este",
             "esta", "estos", "estas", "ese", "esa", "aquel", "aquella", "tambien", "despues", "entre", "alli", "sin", "segun", "hoy", "ya", "pero", "mas", "no",
             "se", "fue", "es", "era", "cuando", "como", "asi", "luego", "mientras", "ademas", "sobre", "hacia", "ante", "bajo", "hasta", "actualmente", "finalmente"}


def _numeral_fin_frase(txt: str, i: int, fin: int) -> bool:
    """«... cohete Saturno V. La tripulacion ...»: una sola letra de numeral romano (I, V, X, L, C, M, D) tras un nombre y delante de un arranque de frase
    (articulo, preposicion...) cierra la frase; una inicial de nombre («John F. Kennedy») va seguida de un apellido, no de un articulo."""
    j = i
    while j > 0 and txt[j - 1].isalpha():
        j -= 1
    w = txt[j:i]
    if len(w) != 1 or w not in "IVXLCMD" or j < 2 or not txt[j - 2].isalnum():
        return False
    m = re.match(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]+", txt[fin:])
    return bool(m) and nrm(m.group(0)) in _ARRANQUE


def frases(parrafo: str) -> List[str]:
    out, ini, n = [], 0, len(parrafo)
    for m in re.finditer(r"[.!?]+[\"»”)]*\s+", parrafo):
        fin = m.end()
        sig = parrafo[fin:fin + 1]
        if not sig or not (sig.isupper() or sig in "¿¡\"«“—(0123456789"):
            continue
        if parrafo[m.start()] == "." and (_abrev_antes(parrafo, m.start()) or re.search(r"\d$", parrafo[:m.start()]) and sig.isdigit()):
            if not _numeral_fin_frase(parrafo, m.start(), fin):
                continue
        out.append(parrafo[ini:m.start() + 1].strip())
        ini = fin
    if ini < n:
        out.append(parrafo[ini:].strip())
    return [f for f in out if len(f.split()) >= 2]


# ====================================================== tokens y sintagmas nominales ======================================================
TOK = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9'’\-\.]*|[,;:()\"«»—–]")


class W:
    __slots__ = ("t", "n", "cap", "i")

    def __init__(self, t, i):
        self.t, self.n, self.i = t.rstrip("."), nrm(t.rstrip(".")), i
        self.cap = t[:1].isupper() and not t.isupper() or (t.isupper() and len(t) > 1 and t.lower() not in ("xx", "xix", "xviii", "xvii", "xvi", "xv", "xiv", "xiii", "xii", "xi", "x"))

    def __repr__(self):
        return self.t


def toks(s: str) -> List[W]:
    out = []
    for m in TOK.finditer(s):
        w = m.group()
        if w.lower() in ("del", "al") and out:
            out += [W("de" if w.lower() == "del" else "a", len(out)), W("el", len(out) + 1)]
        else:
            out.append(W(w, len(out)))
    return out


def _conector(ws, j) -> bool:
    """«de» / «el» / «la»… dentro de un nombre propio: «Nueva Gales del Sur» (= de el Sur), «Reino de España»."""
    n = len(ws)
    if ws[j].n in ("de", "la", "las", "los", "el"):
        if j + 1 < n and ws[j + 1].cap:
            return True
        if ws[j].n == "de" and j + 2 < n and ws[j + 1].n in ("el", "la", "los", "las") and ws[j + 2].cap:
            return True
    return False


def _num_rom(w):
    return bool(re.fullmatch(r"[ivxlcm]+", w.n)) and w.n not in ("mi", "mil", "vi", "ci", "li", "di", "mix", "vid")


class NP:
    __slots__ = ("key", "disp", "adjs", "fin", "propio", "head", "nfin", "titulo")

    def __init__(self, key, disp, adjs, fin, propio, head=""):
        self.key, self.disp, self.adjs, self.fin, self.propio, self.head = key, disp, adjs, fin, propio, head


def np_en(ws: List[W], i: int, lex: Lex, cadena_de=True, inicio_frase=False) -> Optional[NP]:
    """Sintagma nominal desde ws[i]: (determinante) (numero) nucleo (adjetivos) (de N)*. Los adjetivos se devuelven aparte."""
    n = len(ws)
    j = i
    det_poss = False
    cuant = ""
    for qf in CUANTIF:
        qw = qf.split()
        if [x.n for x in ws[j:j + len(qw)]] == qw and j + len(qw) < n and (re.fullmatch(r"\d+(?:[.,]\d+)?", ws[j + len(qw)].n) or ws[j + len(qw)].n in NUM or ws[j + len(qw)].n in ("unos", "unas")):
            cuant = " ".join(x.t.lower() for x in ws[j:j + len(qw)])
            j += len(qw)
            break
    while j < n and (ws[j].n in DET or ws[j].n in PRE_ADJ) and not (ws[j].n in NUM and j + 1 < n and ws[j + 1].n in PREP):
        det_poss = det_poss or ws[j].n in ("su", "sus")
        j += 1
        if j < n and ws[j].n == "de" and ws[j - 1].n in ("uno", "una", "unos", "unas", "pocos", "pocas", "muchos", "muchas", "algunos", "algunas", "varios", "varias", "demas", "todos", "todas"):
            j += 1                                                           # "uno de los pocos mamiferos" -> mamiferos
            while j < n and (ws[j].n in DET or ws[j].n in PRE_ADJ or ws[j].n in NUM):
                j += 1
    if j >= n or ws[j].t in ",;:()\"«»—–" or ws[j].n in PREP or ws[j].n in ("y", "e", "o", "u", "que", "no", "se", "pero"):
        return None
    pal = []
    propio = False
    if (ws[j].cap and not (j == 0 and not (j + 1 < n and ws[j + 1].cap))) or (ws[j].cap and j == i and i > 0) or _num_rom(ws[j]) and j > i:
        propio = True
    elif j == 0 and ws[j].cap and j + 1 < n and ws[j + 1].cap:
        propio = True
    if inicio_frase and j == 0 and ws[0].cap and not (j + 1 < n and ws[j + 1].cap):
        propio = False
    start = j
    if propio:
        while j < n and (ws[j].cap or _num_rom(ws[j]) or re.fullmatch(r"\d+", ws[j].n) or _conector(ws, j)):
            pal.append(ws[j])
            j += 1
        head = " ".join(w.t for w in pal)
    else:
        if ws[j].n in NUM and j + 1 < n and ws[j + 1].n not in PREP:
            pal.append(ws[j])
            j += 1
        pal.append(ws[j])
        j += 1
        head = pal[-1].n
    if not propio and len(pal) == 1 and pal[0].n in TITULOS:
        k = j
        if k < n and ws[k].n == "de" and k + 1 < n and ws[k + 1].cap:
            k += 1
        if k < n and ws[k].cap and ws[k].t not in ",;:" and k > 0:
            nom = []
            while k < n and (ws[k].cap or _num_rom(ws[k]) or _conector(ws, k)):
                nom.append(ws[k])
                k += 1
            if nom:
                np2 = NP(clave(re.sub(r"\bde el\b", "del", " ".join(w.t for w in nom), flags=re.I)), re.sub(r"\bde el\b", "del", " ".join(w.t for w in nom), flags=re.I), [], k, True, clave(nom[0].t))
                np2.nfin, np2.titulo = k, pal[0].n
                return np2
    nuc_fin = j
    adjs = []
    comparativo = False
    while j < n and not propio:
        w = ws[j]
        if w.t in ",;:()\"«»—–" or w.n in PREP or w.n in ("y", "e", "o", "u", "que", "se", "no", "pero") or lex.lema(w.t) and not lex.es_adj(w.t) and w.n not in lex.N:
            break
        if w.n in ("mas", "menos") and j + 1 < n and (lex.es_adj(ws[j + 1].t) or ws[j + 1].n in lex.A):
            j += 2                                                   # comparativo/superlativo: no se guarda como cualidad
            comparativo = True
            continue
        if w.n in ADV:
            j += 1
            continue
        if lex.es_adj(w.t) or (lex.participio(w.t) and w.n not in lex.N):
            adjs.append(w)
            j += 1
            continue
        if w.n in lex.A or w.n in lex.N and not pal[-1].n.endswith("s") is False:
            break
        break
    # cadena "de/del N" (cola de castor, pico de pato, estado de conservacion)
    while cadena_de and j + 1 < n and ws[j].n in ("de", "del") and not adjs and not comparativo:
        k = j + 1
        sub = np_en(ws, k, lex, cadena_de=True)
        if sub is None or (not sub.propio and sub.head in {c.upper() for c in CARDINAL}):
            break
        pal += [ws[j]] + [w for w in ws[k:sub.nfin] if sub.propio or w.n not in DET or w.n in NUM]
        j = sub.fin
        nuc_fin = sub.nfin
        adjs = list(sub.adjs)
        if sub.propio:
            break
    if not pal:
        return None
    conten = list(pal)
    key = clave(re.sub(r"\bde el\b", "del", " ".join(w.t for w in conten), flags=re.I))
    disp = re.sub(r"\bde el\b", "del", " ".join(w.t if (propio and w.cap) else w.t.lower() for w in conten), flags=re.I)
    if not key:
        return None
    if cuant:
        disp = cuant + " " + disp
    np_ = NP(key, disp, adjs, j, propio, clave(head))
    np_.nfin = nuc_fin if not propio else j
    np_.titulo = ""
    return np_


# ====================================================== extracción por patrones ===========================================================
class Hecho(dict):
    pass


def _h(s, p, o, s_disp, o_disp, tpl="", neg=False, when="", when_disp=""):
    return Hecho(s=s, p=p, o=o, s_disp=s_disp, o_disp=o_disp, template=tpl, neg=neg, when=when, when_disp=when_disp)


class Tema:
    """De lo que habla el texto: sustituye a «él», «Es…», «Este animal…», «Su X…»."""

    def __init__(self):
        self.key = self.disp = None
        self.propio = False
        self.clases = set()

    def poner(self, key, disp, propio=False):
        if key != self.key:
            self.clases = set()
        self.key, self.disp, self.propio = key, disp, propio


def _tpl(forma: str, prep: str = "") -> str:
    return "{s} " + forma.lower() + (" " + prep if prep else "") + " {o}"


TITULOS = set("""capitan rey reina doctor doctora profesor profesora general presidente presidenta senor senora san santa don dona principe princesa conde papa emperador sir lord naturalista cientifico
revista libro obra periodico familia genero orden clase especie reino tribu filo isla ciudad pais rio monte lago mar oceano estado provincia region condado departamento villa pueblo
puerto bahia golfo cabo peninsula desierto volcan sierra cordillera valle universidad instituto museo""".split())
GOBIERNA = set("""endemico nativo originario tipico propio caracteristico parecido cercano proximo lejano similar igual distinto diferente relacionado vinculado perteneciente dependiente famoso conocido capaz
responsable sinonimo ajeno comun habitual abundante escaso frecuente rico pobre apto util sensible resistente situado ubicado localizado presente distribuido extendido protegido""".split())
TEMPORAL = {"ACTUALIDAD", "MOMENTO", "EPOCA", "SIGLO", "ANO", "ANOS", "DIA", "DIAS", "VEZ", "TIEMPO", "PRINCIPIOS", "FINALES", "MEDIADOS", "ANTIGUEDAD", "HISTORIA", "ACTUALMENTE", "VISTA"}
NUMK = set(NUM) | {"mil", "millones", "millon", "cientos", "docenas", "decenas", "pares", "mitad", "parte", "resto", "total"}
CARDINAL = {"norte", "sur", "este", "oeste", "noreste", "noroeste", "sureste", "suroeste", "centro", "occidente", "oriente"}
CUANTIF = ("mas de", "menos de", "unos", "unas", "casi", "cerca de", "alrededor de", "aproximadamente", "mas o menos", "hasta", "al menos")
UBICAR = {"encontrar", "situar", "ubicar", "localizar", "hallar", "emplazar", "alojar"}
CLITICO = {"lo", "la", "le", "les", "los", "las", "me", "te", "nos", "os"}
STOP_OBJ = {"ELLO", "LO", "LA", "LOS", "LAS", "SI", "QUE", "ESTO", "ESO", "ALGO", "ALGUIEN", "NADA", "CUAL", "COMO", "DONDE", "CUANDO", "SE", "MISMO", "MISMA", "OTRO", "OTRA"}


_VERBO_SIN_SUJETO = {"hacer", "existir", "haber", "estudiar", "indicar", "parecer", "importar", "faltar", "bastar"}
_ADV_BASURA = set("""muy menudo casi tambien aun cualquier juntas rara raras raramente mas menos mucho muchos muchas poco pocos pocas demasiado particularmente practicamente ampliamente aproximadamente
numerosas numerosos varios varias diferentes diferente posibles posible siguiente anterior mismo misma mismos mismas otros otras otro otra ciertos ciertas cierto cierta algunos algunas algun alguna
mientras cuando donde quizas incluso excepto viceversa vez veces tanto tantos tantas todo todos toda todas ambos ambas cada cuantos cuantas cuanto cuanta tal tales asi ademas entonces luego despues antes
siempre nunca jamas ya todavia ahora hoy aqui alli alla ahi cerca lejos dentro fuera encima debajo delante detras junto frente casi apenas solamente sencillamente completamente totalmente
aguas nuevamente fieramente frecuentemente generalmente habitualmente normalmente principalmente especialmente actualmente ocasionalmente usualmente supuestamente probablemente posiblemente
ellos ellas ello esto eso aquello nosotros ustedes usted yo tu el ella mi""".split())


def _fin_gerundio(w):
    return bool(re.search(r"(ando|iendo|yendo)(?:se|lo|la|los|las|le|les|me|te|nos)?$", w))


def _concuerda(s_key, forma, lex=None):
    """Sujeto omitido: plural<->plural, singular<->singular (solo 3.ª persona)."""
    f = nrm(forma).split(" ")[0]
    plural_v = bool(re.search(r"(an|en|on)$", f)) and not re.search(r"(ion|cion)$", f)
    nuc = nrm(s_key.split("_")[0])
    plural_s = False
    if nuc.endswith("s") and len(nuc) > 3 and lex is not None and nuc not in lex.N:
        cands = [nuc[:-1]] + ([nuc[:-2]] if nuc.endswith("es") else [])
        plural_s = any(c in lex.N or c in lex.A for c in cands)
    elif nuc.endswith("s") and len(nuc) > 3 and lex is None:
        plural_s = not nuc.endswith(("sis", "is", "us"))
    return plural_s == plural_v


def _FUERTE_VERBO(n):
    return n.endswith(("aron", "ieron", "aba", "aban", "ia", "ian")) and len(n) > 5


TEMPORAL_MIN = {"ano", "anos", "dia", "dias", "mes", "meses", "hora", "horas", "minuto", "minutos", "siglo", "siglos", "milenio", "decada", "semana", "semanas", "periodo", "epoca", "kg", "cm", "km", "mm", "metros", "newtons", "g"}
_PLURALIA = {"ELLOS", "NUMEROSAS", "ANOS", "DIAS", "PADRES", "HERBAZALES", "ALREDEDORES", "PRESAS_"}
_SINONIMO_PRED = {"HABITAR": "VIVIR_EN", "HABITAR_EN": "VIVIR_EN", "ALIMENTAR_DE": "COMER", "ALIMENTAR_CON": "COMER", "NUTRIR_DE": "COMER", "ALIMENTAR": "COMER", "RESIDIR_EN": "VIVIR_EN", "MORAR_EN": "VIVIR_EN"}

class Extractor:
    def __init__(self, lex: Optional[Lex] = None):
        self.lex = lex or Lex.get()
        self.tema = Tema()
        self.apellido: Dict[str, Tuple[str, str]] = {}
        self.ultimo = None
        self.principal = None            # sujeto de la oración principal de la frase anterior (para el sujeto omitido)

    def _recordar(self, np: "NP"):
        """«George Shaw» ... «Shaw»: la segunda vez es la misma persona."""
        if np.propio and " " in np.disp and not np.titulo:
            self.apellido.setdefault(clave(np.disp.split(" ")[-1]), (np.key, np.disp))

    def _resolver(self, np: "NP") -> "NP":
        if np.propio and " " not in np.disp and np.key in self.apellido:
            k, d = self.apellido[np.key]
            np.key, np.disp = k, d
        else:
            self._recordar(np)
        return np

    # ---------- utilidades ----------
    def _inf(self, w: W) -> bool:
        n_ = re.sub(r"(?:se|lo|la|le|me|te|nos|los|las)$", "", w.n) if w.n.endswith(("arse", "erse", "irse", "arlo", "arla", "erlo", "irlo")) else w.n
        return len(n_) > 3 and n_[-2:] in ("ar", "er", "ir") and (n_ in self.lex.V or n_ in _EXTRA_INF or w.n != n_)

    def _verbo(self, ws, i):
        """-> (fin, lema, forma, negado, es_pasiva, (participio_lema, texto), se) del grupo verbal que empieza en i, o None."""
        n = len(ws)
        j, neg, se = i, False, False
        while j < n and ws[j].n in ("no", "nunca", "jamas", "tampoco", "se", "ya", "tambien", "solo", "incluso", "aun", "todavia", "casi", "actualmente", "aun"):
            neg = neg or ws[j].n in ("no", "nunca", "jamas", "tampoco")
            se = se or ws[j].n == "se"
            j += 1
        if j >= n:
            return None
        lem = self.lex.lema(ws[j].t)
        if not lem:
            return None
        forma = ws[j].t
        j += 1
        if lem == "haber" and j < n and (self.lex.participio(ws[j].t) or ws[j].n in _PART_IRREG):
            lem2 = self.lex.participio(ws[j].t) or _PART_IRREG.get(ws[j].n)
            return j + 1, lem2, ws[j].t, neg, False, None, se
        if lem in ("ser", "estar") and j < n:
            pj = j
            while pj < n and ws[pj].n in ADV:
                pj += 1
            if pj < n:
                p = self.lex.participio(ws[pj].t) or _PART_IRREG.get(ws[pj].n)
                if p and ws[pj].n not in DET and ws[pj].n not in lex_noun_adj(self.lex):
                    return pj + 1, lem, forma, neg, True, (p, ws[pj].t), se
        if lem in ("poder", "soler", "deber", "tender") and j < n and self._inf(ws[j]):
            return j + 1, (("poder_" + ws[j].n) if lem == "poder" else ws[j].n), forma + " " + ws[j].t, neg, False, None, se
        return j, lem, forma, neg, False, None, se

    def _prep_np(self, ws, i):
        """Complementos desde i: [(prep, NP)] hasta fin de clausula. Reparte «de A y de B» y listas «A, B y C»."""
        out, n = [], len(ws)
        j = i
        prep = ""
        while j < n:
            w = ws[j]
            if w.t in ";()":
                break
            if w.t == "," or w.n in ("y", "e", "o", "u"):
                j += 1
                if j < n and ws[j].n in ("el", "la", "los", "las", "un", "una", "unos", "unas") and not ws[j].cap:
                    prep = ""
                if j < n and ((self.lex.lema(ws[j].t) and not self.lex.es_adj(ws[j].t) and ws[j].n not in self.lex.N) or ws[j].n in ("que", "pero", "cuando", "donde", "como", "porque", "aunque", "si", "ya", "sin")):
                    break
                continue
            if w.n in PREP:
                if w.n == "como" and j == i:
                    pass
                prep = w.n
                j += 1
                if j < n and (self._inf(ws[j]) or ws[j].n in ("si", "que")):
                    break                                              # "para comprobar…", "de dar a luz…": subordinada de infinitivo, no se trocea
                continue
            if not prep and j == i and self._inf(ws[j]):
                break
            np = np_en(ws, j, self.lex)
            if np is None:
                if ws[j].n in ("que", "se", "no", "pero", "como", "si") or self.lex.lema(ws[j].t):
                    break
                j += 1
                continue
            if np.propio is False and np.key.split("_")[0].lower() in CARDINAL and prep in ("a", "de", "hacia", "desde"):
                j = np.fin
                continue
            if out and out[-1][1].propio is False and "_DE_" in out[-1][1].key and np.propio and ws[j - 1].t in (",", "y", "e"):
                j = np.fin                                           # «obras de Velázquez, Goya y El Greco»: no se sabe a qué se une la lista
                continue
            if prep in ("en", "hasta", "desde", "durante") and re.fullmatch(r"(?:1\d{3}|20\d{2})", np.key):
                out.append(("@cuando", np))
            else:
                out.append((prep, np))
            j = np.fin
        return out, j

    def _clases(self, np: NP) -> List["Hecho"]:
        """«la familia Ornithorhynchidae» -> (ORNITHORHYNCHIDAE ES FAMILIA)."""
        t = getattr(np, "titulo", "")
        return [_h(np.key, "ES", clave(t), np.disp, t)] if t and np.propio else []

    # ---------- una clausula ----------
    def clausula(self, texto: str, inicio=False, sujeto=None) -> List["Hecho"]:
        ws = toks(texto)
        lex = self.lex
        while ws and ws[0].n in ("y", "e", "pero", "pues", "ni") or (ws and ws[0].t in ",;"):
            ws = ws[1:]
        if len(ws) < 2:
            return []
        when = when_disp = ""
        # adverbial inicial / fecha: "En 1798, ...", "Hasta principios del siglo xx, ...", "Actualmente ..."
        k = 0
        if ws[0].n in ("en", "hasta", "desde", "durante", "tras", "hacia", "alrededor", "antes", "despues", "a") or ws[0].n in ADV:
            for q in range(1, min(len(ws), 12)):
                if ws[q].t == ",":
                    k = q + 1
                    break
                if lex.lema(ws[q].t) and ws[q].n not in lex.N and not lex.es_adj(ws[q].t) and ws[q].n not in ("siglo",):
                    break
            if k == 0 and ws[0].n in ADV:
                k = 1
            if k == 0 and ws[0].n == "en" and len(ws) > 3 and re.fullmatch(r"1\d{3}|20\d{2}", ws[1].n):
                k = 2
            if k:
                inic = " ".join(w.t for w in ws[:k])
                my = re.search(r"\b(1\d{3}|20\d{2})\b", inic)
                if my and ws[0].n not in ADV:
                    when, when_disp = my.group(1), inic.strip(" ,").lower()
                elif ws[0].n not in ADV and ws[0].n in ("hasta", "desde", "durante", "tras", "hacia", "alrededor", "antes", "despues"):
                    when_disp = ""
        ws = ws[k:]
        if len(ws) < 2:
            return []
        for q, w in enumerate(ws):
            w.i = q
        tema = self.tema
        # primer verbo conjugado
        iv = None
        for q in range(len(ws)):
            if lex.lema(ws[q].t) and (q == 0 or (ws[q - 1].n not in DET and ws[q - 1].n not in PREP)) and ws[q].n not in _NO_VERBO:
                if q > 0 and lex.es_adj(ws[q - 1].t) and ws[q].n in lex.N:
                    continue
                if q > 0 and ws[q].cap:
                    continue                                       # «… Asia Occidental»: nombre propio, no «asir»
                if q > 0 and ws[q].n in lex.A and ws[q - 1].n in lex.N and ws[q - 1].n not in lex.V and ws[q].t != "," and not ws[q].n.endswith(("an", "en", "on")):
                    continue                                       # «temperatura interna»: adjetivo tras nombre
                if q > 0 and (ws[q].n in lex.N or ws[q].n in lex.A) and not _FUERTE_VERBO(ws[q].n) and (ws[q - 1].n in ADV or ws[q - 1].n in ("mas", "menos", "tan", "muy") or lex.es_adj(ws[q - 1].t) or ws[q - 1].n in lex.N and q == 1 and False):
                    continue                                       # «el león más largo»: «largo» no es «largar»
                iv = q
                break
        if iv is None:
            return []
        sub_ws = ws[:iv]
        while sub_ws and sub_ws[-1].n in ("no", "se", "ya", "tambien", "nunca", "solo", "casi", "incluso", "aun", "actualmente"):
            iv -= 1
            sub_ws = sub_ws[:-1]
        if iv + 1 < len(ws) and ws[iv - 1 if iv else 0].n in CLITICO and iv > 0:
            return []                                              # "… lo convierten en …": sin sujeto fiable
        if any(w.n in CLITICO for w in sub_ws[-1:]):
            return []
        v = self._verbo(ws, iv)
        if v is None:
            return []
        fin_v, lem, forma, neg, pas, part, se = v
        out: List[Hecho] = []
        s_key = s_disp = None
        s_prop = poss = False
        if sujeto == "PREV":
            if not self.ultimo:
                return []
            s_key, s_disp, s_prop = self.ultimo
        elif sujeto:
            s_key, s_disp, s_prop = sujeto
        elif not sub_ws:
            s_key, s_disp, s_prop = self.principal if self.principal and not inicio and lem not in ("ser", "estar") else (tema.key, tema.disp, tema.propio)
        else:
            np = np_en(sub_ws, 0, lex, cadena_de=True, inicio_frase=inicio)
            if np is not None:
                np = self._resolver(np)
            if np is None:
                if sub_ws[0].n in ("el", "este", "esta") or all(w.n in ADV or w.n in ("el", "ello") for w in sub_ws):
                    s_key, s_disp, s_prop = tema.key, tema.disp, tema.propio
                else:
                    return []
            else:
                resto = sub_ws[np.fin:]
                if resto and resto[0].t == ",":                               # aposicion: "el capitan John Hunter, segundo gobernador de Nueva Gales del Sur, envio …"
                    cierre = next((q for q in range(1, len(resto)) if resto[q].t == ","), None)
                    if cierre is not None and cierre >= 2:
                        ap = np_en(resto, 1, lex)
                        if ap is not None:
                            if np.propio:
                                out += self._clases(np)
                                h0 = ap.key
                                out.append(_h(np.key, "ES", h0.split("_DE_")[0], np.disp, ap.disp.split(" de ")[0]))
                                if "_DE_" in h0:
                                    out.append(_h(np.key, h0.split("_DE_")[0] + "_DE", h0.split("_DE_", 1)[1], np.disp, ap.disp.split(" de ", 1)[1], tpl="{s} es " + ap.disp.split(" de ")[0] + " de {o}"))
                            resto = resto[cierre + 1:]
                if resto and not all(w.n in ADV or w.t == "," for w in resto):
                    return []
                if sub_ws[0].n in ("su", "sus") and tema.key:
                    s_key, s_disp, poss = tema.key, tema.disp, np
                elif sub_ws[0].n in ("este", "esta", "estos", "estas", "ese", "esa", "dicho", "dicha") and tema.key and (np.key in tema.clases or _sing(np.key) in tema.clases or np.key in ("ANIMAL", "ESPECIE", "EJEMPLAR", "FELINO", "FELIDO", "MAMIFERO", "PLANTA", "CIUDAD", "PAIS", "PERSONA")):
                    s_key, s_disp, s_prop = tema.key, tema.disp, tema.propio
                elif sub_ws[0].n in ("el", "la") and not np.propio and tema.key and np.key in tema.clases:
                    s_key, s_disp, s_prop = tema.key, tema.disp, tema.propio      # «La ciudad tiene…» = Madrid
                else:
                    s_key, s_disp, s_prop = np.key, np.disp, np.propio
                    out += self._clases(np) if not out else []
        if not s_key or s_key in STOP_OBJ:
            return []
        if not sub_ws and not sujeto and lem in _VERBO_SIN_SUJETO:
            return []                                              # «hace diez mil años», «existía una interacción»: no es del tema
        if not sub_ws and not sujeto and not _concuerda(s_key, forma, lex):
            if tema.key and lem not in ("ser", "estar") and (_concuerda(tema.key, forma, lex) or not tema.propio):
                s_key, s_disp, s_prop = tema.key, tema.disp, tema.propio
            else:
                return []                                          # sujeto omitido: el verbo debe concordar en número con el tema
        self.ultimo = (s_key, s_disp, s_prop)
        if sujeto == "PREV":
            pass
        # ----- copulativas -----
        if lem in ("ser", "estar", "parecer", "resultar", "quedar") and not pas:
            return self._copula(out, ws, fin_v, lem, forma, neg, s_key, s_disp, s_prop, poss, when, when_disp, inicio)
        if poss:
            return []                                              # «su X <verbo>…»: sin sujeto claro
        # ----- pasivas -----
        if pas and part:
            inf, ptxt = part
            comp, _ = self._prep_np(ws, fin_v)
            cuando = [np for pr, np in comp if pr == "@cuando"]
            if cuando and not when:
                when, when_disp = cuando[0].key, "en " + cuando[0].key
            agente = [np for pr, np in comp if pr == "por"]
            if agente:
                for ag in agente[:2]:
                    out.append(_h(ag.key, clave(inf), s_key, ag.disp, s_disp, tpl=_tpl(_activa(inf)), neg=neg, when=when, when_disp=when_disp))
                    out += self._clases(ag)
            elif inf in UBICAR | {"situar"} and any(pr == "en" for pr, _ in comp):
                pass
            else:
                out.append(_h(s_key, "SER", clave(ptxt), s_disp, ptxt.lower(), neg=neg, when=when, when_disp=when_disp))
            for pr, np in comp[:4]:
                if re.search(r"(?:^|_)\d", np.key) or np.key.split("_")[0] in TEMPORAL:
                    continue
                if pr == "en" and inf in UBICAR | {"situar"} and np.key not in STOP_OBJ:
                    out.append(_h(s_key, "ESTAR_EN", np.key, s_disp, np.disp, tpl="{s} está en {o}", neg=neg))
                    out += self._clases(np)
                    continue
                if pr in ("en", "como", "de", "con", "para", "entre", "sobre") and np.key not in STOP_OBJ:
                    out.append(_h(s_key, clave(ptxt) + "_" + pr.upper(), np.key, s_disp, np.disp, tpl=_tpl("es " + ptxt.lower(), pr), neg=neg, when=when, when_disp=when_disp))
                    out += self._clases(np)
            return self._fin(out, s_key, s_disp, s_prop, inicio, False)
        # ----- verbales -----
        comp, fin = self._prep_np(ws, fin_v)
        cuando = [np for pr, np in comp if pr == "@cuando"]
        if cuando and not when:
            when, when_disp = cuando[0].key, "en " + cuando[0].key
        comp = [(pr, np) for pr, np in comp if pr != "@cuando" and np.key not in STOP_OBJ and np.key.split("_")[0] not in TEMPORAL and not re.search(r"(?:^|_)\d", np.key)]
        if se and lem in UBICAR and nrm(forma) in ("encuentra", "encuentran", "situa", "ubica", "halla", "localiza", "emplaza", "situan", "ubican", "hallan"):
            pred0_ = "ESTAR"
            for pr, np in comp[:2]:
                if pr == "en":
                    out.append(_h(s_key, "ESTAR_EN", np.key, s_disp, np.disp, tpl="{s} está en {o}", neg=neg, when=when, when_disp=when_disp))
                    out += self._clases(np)
            comp = []
            if out:
                return self._fin(out, s_key, s_disp, s_prop, inicio, False)
        if se and not sub_ws and not sujeto:
            return []                                                  # "se proyecta una disminucion": impersonal/pasiva refleja sin agente: no se atribuye al tema
        if lem == "haber" and nrm(forma) == "hay":
            return []
        if not comp:
            return []
        pred0 = "TENER" if lem == "tener" else clave(lem)
        if lem == "tener":
            comp = [(pr, np) for pr, np in comp if not pr]
        for pr, np in comp[:3]:
            if pr not in ("", "a", "en", "de", "con", "por", "para", "sobre", "entre", "sin", "contra", "hacia", "desde", "hasta", "como", "ante", "bajo", "durante"):
                continue
            if pr in ("hasta", "durante", "desde") and re.search(r"\b(?:siglo|ano|\d{3,4})\b", nrm(np.disp)):
                continue
            pred = pred0 + ("_" + pr.upper() if pr and not (lem == "tener" and pr == "") else "")
            o_key, o_disp = np.key, np.disp
            if not np.propio and any(w.n in ("su", "sus") for w in ws[fin_v:np.fin]) and s_key:
                o_key, o_disp = np.key + "_DE_" + s_key, np.disp + " de " + s_disp
            tpl = "{s} tiene {o}" if lem == "tener" and not pr else _tpl(forma, pr)
            out.append(_h(s_key, pred, o_key, s_disp, o_disp, tpl=tpl, neg=neg, when=when, when_disp=when_disp))
            out += self._clases(np)
            if lem == "tener" and not pr and "_DE_" in np.key and not np.propio and np.key.split("_")[0].lower() not in NUMK:
                base = np.key.split("_DE_")[0]
                out.append(_h(s_key, "TENER", base, s_disp, np.disp.split(" de ")[0], tpl="{s} tiene {o}", neg=neg))
                out.append(_h(np.key, "ES", base, np.disp, np.disp.split(" de ")[0]))
            for a in np.adjs:
                if lex.es_adj(a.t):
                    out.append(_h(o_key, "SER", clave(a.t), o_disp, a.t.lower()))
        return self._fin(out, s_key, s_disp, s_prop, inicio, False)

    def _copula(self, out, ws, rest_i, lem, forma, neg, s_key, s_disp, s_prop, poss, when, when_disp, inicio):
        lex = self.lex
        j = rest_i
        while j < len(ws) and (ws[j].n in ADV):
            j += 1
        if j < len(ws) and ws[j].n in ("cuando", "donde", "como", "porque", "decir", "que", "lo", "cierto", "mas"):
            return []                                                    # «es cuando el león caza», «es decir…»: no es una definición
        if j + 1 < len(ws) and ws[j].n in ("el", "la", "lo", "los", "las") and ws[j + 1].n == "de":
            j += 2                                                       # "su estado de conservacion es el de una especie casi amenazada"
        # atributo posesivo: (TEMA, ATRIBUTO, valor)
        def atributo(valor_key, valor_disp):
            nk = poss.key
            return [_h(s_key, nk, valor_key, s_disp, valor_disp, tpl="{s} tiene como " + poss.disp + " {o}", neg=neg, when=when, when_disp=when_disp)]
        # adjetivos directos: "es venenoso", "esta casi amenazada", "es pequeño y ligero"
        adjs = []
        q = j
        while q < len(ws):
            if ws[q].n in ADV:
                q += 1
                continue
            if ws[q].n in DET or ws[q].n in PREP or not (lex.es_adj(ws[q].t) or lex.participio(ws[q].t)) or (ws[q].n in lex.N and ws[q].n not in lex.A and not lex.participio(ws[q].t)):
                break
            adjs.append(ws[q])
            q += 1
            if q < len(ws) and (ws[q].n in ("y", "e") or ws[q].t == ","):
                q += 1
        if adjs and (q >= len(ws) or ws[q].n in PREP or ws[q].t in ",;"):
            if poss:
                return self._fin(atributo(clave(" ".join(a.t for a in adjs)), " ".join(a.t.lower() for a in adjs)), s_key, s_disp, s_prop, inicio, False)
            for a in adjs:
                out.append(_h(s_key, "ESTAR" if lem == "estar" else "SER", clave(a.t), s_disp, a.t.lower(), neg=neg, when=when, when_disp=when_disp))
            a_last = adjs[-1]
            for pr, np in self._prep_np(ws, q)[0][:3]:
                if re.search(r"(?:^|_)\d", np.key) or np.key in STOP_OBJ:
                    continue
                if pr == "en" and (self.lex.participio(a_last.t) or "") in UBICAR | {"situar"}:
                    out = [h for h in out if h["o"] != clave(a_last.t)]
                    out.append(_h(s_key, "ESTAR_EN", np.key, s_disp, np.disp, tpl="{s} está en {o}", neg=neg))
                    out += self._clases(np)
                elif pr in ("de", "en", "a", "con", "por", "para", "como", "entre"):
                    out.append(_h(s_key, clave(a_last.t) + "_" + pr.upper(), np.key, s_disp, np.disp, tpl="{s} es " + a_last.t.lower() + " " + pr + " {o}", neg=neg))
                    out += self._clases(np)
            return self._fin(out, s_key, s_disp, s_prop, inicio, False)
        np0 = np_en(ws, j, lex, cadena_de=False)
        if np0 is None:
            return self._fin(out, s_key, s_disp, s_prop, inicio, False)
        if poss:
            vd = (np0.disp + " " + " ".join(a.t.lower() for a in np0.adjs)).strip()
            return self._fin(atributo(clave(vd), vd), s_key, s_disp, s_prop, inicio, False)
        partitivo = j + 1 < len(ws) and ws[j].n in ("uno", "una") and ws[j + 1].n == "de"
        if j < len(ws) and ws[j].n in ("el", "la", "un", "uno", "una") and False:
            pass
        # "una especie de mamifero …": la clase es lo que va tras el "de"
        head_w = None
        for w in ws[j:np0.nfin]:
            if w.n not in DET and w.n not in PRE_ADJ and w.n not in NUM:
                head_w = w
                break
        cabeza = head_w.n if head_w else ""
        tail_i = np0.fin
        if np0.propio is False and cabeza in CLASE_ENVOLTURA and tail_i + 1 < len(ws) and ws[tail_i].n == "de":
            sub = np_en(ws, tail_i + 1, lex, cadena_de=True)
            if sub is not None:
                out.append(_h(s_key, "ES", sub.key, s_disp, sub.disp, neg=neg, when=when, when_disp=when_disp))
                out += self._clases(sub)
                for a in sub.adjs:
                    out.append(_h(s_key, "SER", clave(a.t), s_disp, a.t.lower(), neg=neg))
                tail_i = sub.fin
                gov_adj = sub.adjs[-1] if sub.adjs else None
                return self._cola(out, ws, tail_i, s_key, s_disp, s_prop, gov_adj, cabeza, "", neg, inicio)
        # (si no era «especie de X» sigue)
        if np0.propio:                                                  # "Platypus es un termino", "Madrid es la capital de España" (np0 propio: "X es Y")
            out.append(_h(s_key, "ES", np0.key, s_disp, np0.disp, neg=neg, when=when, when_disp=when_disp))
            return self._fin(out, s_key, s_disp, s_prop, inicio, True)
        if cabeza in CLASE_ENVOLTURA:
            return self._fin(out, s_key, s_disp, s_prop, inicio, False)        # «es una de las cinco especies»: no dice nada
        k0, d0 = (_sing(np0.key), _sing(np0.disp)) if partitivo else (np0.key, np0.disp)
        out.append(_h(s_key, "ES", k0, s_disp, d0, neg=neg, when=when, when_disp=when_disp))
        for a in np0.adjs:
            out.append(_h(s_key, "SER", _sing(clave(a.t)) if partitivo else clave(a.t), s_disp, _sing(a.t.lower()) if partitivo else a.t.lower(), neg=neg))
        gov = np0.adjs[-1] if np0.adjs else None
        return self._cola(out, ws, tail_i, s_key, s_disp, s_prop, gov, None if partitivo else np0.key, np0.disp, neg, inicio)

    def _cola(self, out, ws, i, s_key, s_disp, s_prop, gov_adj, cabeza_key, cabeza_disp, neg, inicio):
        """Preposiciones tras la clase: «endémico DE Australia» (lo gobierna el adjetivo) o «representante DE la familia X» (lo gobierna el nombre)."""
        gob = gov_adj is not None and (nrm(gov_adj.t) in GOBIERNA or self.lex.participio(gov_adj.t))
        comp, _ = self._prep_np(ws, i)
        for pr, np in comp[:4]:
            if pr == "@cuando" or np.key in STOP_OBJ or re.search(r"(?:^|_)\d", np.key):
                continue
            if pr == "":
                if not np.propio and len(np.key) > 2 and np.key.split("_")[0] not in TEMPORAL:
                    out.append(_h(s_key, "ES", np.key, s_disp, np.disp))              # «la capital de España Y LA CIUDAD más poblada…»
                    for a in np.adjs:
                        out.append(_h(s_key, "SER", clave(a.t), s_disp, a.t.lower()))
                break                                                              # lo que sigue cuelga de ese segundo sintagma
            core, cdisp = np.key, np.disp
            m = re.match(r"(ESTE|OESTE|NORTE|SUR|CENTRO|NORESTE|SURESTE|NOROESTE|SUROESTE)_DE_(.+)", core)
            if m:
                core, cdisp = m.group(2), cdisp.split(" de ", 1)[-1]
            if gob:
                out.append(_h(s_key, clave(gov_adj.t) + "_" + pr.upper(), core, s_disp, cdisp, tpl="{s} es " + gov_adj.t.lower() + " " + pr + " {o}", neg=neg))
            elif pr == "de" and cabeza_key and not cabeza_key.startswith("ESPECIE"):
                h = cabeza_key.split("_DE_")[0]
                out.append(_h(s_key, h + "_DE", core, s_disp, cdisp, tpl="{s} es " + (cabeza_disp.split(" de ")[0] or h.lower()) + " de {o}", neg=neg))
            out += self._clases(np)
        return self._fin(out, s_key, s_disp, s_prop, inicio, True)

    def _fin(self, out, s_key, s_disp, s_prop, inicio, definicion):
        if definicion and out and (self.tema.key is None or inicio) and not s_key.endswith("_DE_" + (self.tema.key or "#")):
            self.tema.poner(s_key, s_disp, s_prop)
        if s_key == self.tema.key:
            for h in out:
                if h["s"] == s_key and h["p"] == "ES":
                    self.tema.clases.add(h["o"])
        return [h for h in out if h["s"] != h["o"] and h["s"] and h["o"] and h["o"] not in STOP_OBJ and len(h["o"]) > 1]


def lex_noun_adj(lex):
    return set()


def _sing(w: str) -> str:
    if not w or " " in w and False:
        return w
    return " ".join(_sing1(x) for x in w.split(" ")) if " " in w else _sing1(w)


def _sing1(w: str) -> str:
    if w.endswith("ces"):
        return w[:-3] + ("Z" if w.isupper() else "z")
    if re.search(r"[rlndzjsRLNDZJS][eE][sS]$", w) and not re.search(r"[aeiouAEIOU]ES$|[aeiou]es$", w[-4:-2] + w[-2:]):
        return w[:-2]
    return w[:-1] if w.lower().endswith("s") and len(w) > 3 else w


def _activa(lema: str) -> str:
    l = nrm(lema)
    if l.endswith("ar"):
        return l[:-2] + "ó"
    if l.endswith(("er", "ir")):
        return l[:-2] + "ió"
    return l


# ====================================================== frase completa ====================================================================
INCISO = re.compile(r"\s*[—–]([^—–]{3,200})[—–]\s*")
PAREN = re.compile(r"\s*\(([^()]{0,120})\)")
BINOM = re.compile(r"^[A-Z][a-z]+(?: [a-z]+){1,2}$")


class Lector:
    """Lee un texto entero y lo guarda en la memoria. `escuela(clausula, tema_disp) -> [dict|Hecho] | None` es opcional (la escuela de español, para lo que los patrones no cubren)."""

    def __init__(self, mem, escuela: Optional[Callable] = None, lex: Optional[Lex] = None):
        self.mem, self.escuela = mem, escuela
        self.ex = Extractor(lex)
        self.vistos: set = set()          # palabras (sin acento) vistas en el texto
        self.acentos: Dict[str, str] = {}  # sin acento -> con acento, tal como aparece en el texto
        self.disp_map: Dict[str, str] = {}
        self.minus: set = set()

    # ---------- control de calidad: mas vale callar que aprender basura ----------
    def _tok(self, k):
        return [t for t in nrm(k).split("_") if t]

    def _formas(self, t):
        fs = [t]
        if t.endswith("es") and len(t) > 4:
            fs.append(t[:-2])
        if t.endswith("s") and len(t) > 3:
            fs.append(t[:-1])
            if t.endswith("as"):
                fs.append(t[:-2] + "o")
        if t.endswith("a") and len(t) > 3:
            fs.append(t[:-1] + "o")
        return fs

    def _solo_adj(self, t):
        """Adjetivo del diccionario (en cualquier género/número) que no es también nombre."""
        lex = self.ex.lex
        fs = self._formas(t)
        return any(f in lex.A for f in fs) and not any(f in lex.N for f in fs)

    def _malo(self, k, rol, p):
        """¿Es esta clave un sujeto/objeto inservible? (adverbios, gerundios, infinitivos, numerales, adjetivos sueltos, restos de frase)"""
        lex = self.ex.lex
        ts = self._tok(k)
        if not ts:
            return True
        a, z = ts[0], ts[-1]
        if a in _ADV_BASURA or a in ("ser", "estar", "hace", "hacia", "hay") or z in ("y", "o", "e", "u", "de", "a", "en", "con", "por", "para", "que", "como", "mas", "menos"):
            return True
        if re.fullmatch(r"\d+", a) or a in NUM or a in NUMK or a in TEMPORAL_MIN:
            return True
        if _fin_gerundio(a) or a.endswith("mente"):
            return True
        if len(ts) == 1:
            if a in lex.V or (a.endswith(("ar", "er", "ir", "arse", "erse", "irse", "arla", "arlas", "arlo", "arlos", "erla", "erlo")) and self._inf_clitico(a)):
                if a not in lex.N:
                    return True                                    # infinitivo suelto
            if self._solo_adj(a) and not (rol == "o" and (p in ("SER", "ESTAR") or p == "ES" and not a.endswith("s"))):
                return True                                        # adjetivo suelto como si fuera cosa
            if lex.lema(a) and a not in lex.N and not lex.es_adj(a) and not k.endswith("_DE"):
                return True                                        # forma verbal suelta
        elif len(ts) >= 3 and ts[-2] == "de" and ts[-1] in lex.A and ts[-1] not in lex.N:
            return True                                            # «cocodrilos_de_considerable»
        return False

    def _inf_clitico(self, a):
        lex = self.ex.lex
        b = re.sub(r"(se|la|las|lo|los|le|les|me|te|nos)$", "", a) if a.endswith(("arse", "erse", "irse", "arla", "arlas", "arlo", "arlos", "erla", "erlo", "irla", "irlo")) else a
        return b in lex.V

    def _ok(self, h: Hecho) -> bool:
        lex = self.ex.lex
        s, p, o = h["s"], h["p"], h["o"]
        if self._malo(s, "s", p) or self._malo(o, "o", p):
            return False
        pp = p.split("_")
        if pp[0] == "HACER" and len(pp) > 1 or pp[0] in ("PROMEDIAR", "INTERNAR", "SITER", "SITIAR", "SOLER", "SUPONER", "PARECER", "RESULTAR"):
            return False
        if pp[0] == "PODER" and (len(pp) > 2 or len(pp) == 1):
            return False
        if pp[-1] == "COMO" and len(pp) > 1 and pp[0] not in ("ACTUAR", "FUNCIONAR", "SERVIR", "CONSIDERAR", "USAR", "UTILIZAR", "CONOCER", "LLAMAR", "DESCRIBIR", "CLASIFICAR", "TRABAJAR", "DESEMPENAR", "ACTUA"):
            return False
        if pp[0] == "SER" and len(pp) > 1:
            pass
        to = self._tok(o)
        if p == "ES":
            if len(to) == 1 and to[0] not in lex.N and to[0] not in lex.A and (any(f in lex.part for f in self._formas(to[0])) or lex.lema(to[0])):
                return False                                       # «es descritas», «es cazando»: forma verbal, no clase
            if to[0] in ("caso", "hecho", "hizo", "cierto", "capaz", "receptor", "inverso", "igual", "mutuos", "forma", "formas"):
                return False
        if p == "SER":
            if len(to) != 1 or not lex.es_adj(to[0]) and not lex.participio(to[0]):
                return False
            if to[0] in lex.N and to[0] not in lex.A and not lex.participio(to[0]):
                return False
        if p in ("ESTAR", "ESTAR_EN") and h["o"] == h["s"]:
            return False
        return True

    def _singular(self, w, disp):
        """«leones» -> «león»; solo si la forma singular existe en el léxico (o ya se vio en el texto)."""
        lex = self.ex.lex
        n = nrm(w)
        cands = []
        if n.endswith("ces"):
            cands.append(n[:-3] + "z")
        if n.endswith("es"):
            cands.append(n[:-2])
        if n.endswith("s"):
            cands.append(n[:-1])
        for c in cands:
            if len(c) > 2 and (c in lex.N or c in lex.A or c in self.vistos):
                return c
        return None

    @staticmethod
    def _sing_disp(orig, cand):
        o = (orig or "").lower()
        for k in (3, 2, 1):
            if len(o) > k + 1 and nrm(o[:-k]) == cand:
                return o[:-k]
            if k == 3 and o.endswith("ces") and nrm(o[:-3] + "z") == cand:
                return o[:-3] + "z"
        return None

    def _canon(self, h: Hecho):
        """Sujeto genérico en plural («los leones viven…») -> el singular de la especie, para que «el león» y «los leones» sean una sola cosa."""
        s = h["s"]
        if "_" in s or not s.endswith("S") or len(s) < 5 or nrm(s) not in self.minus:
            return
        sg = self._singular(s.lower(), h.get("s_disp") or "")
        if not sg or sg in ("ser", "estar") or nrm(sg).upper() in _PLURALIA:
            return
        sk = clave(sg)
        h["s"] = sk
        sd = self.disp_map.get(sk) or self._sing_disp(h.get("s_disp") or "", sg) or (self.acentos.get(sg) or sg)
        h["s_disp"] = sd[:1].upper() + sd[1:] if (h.get("s_disp") or "")[:1].isupper() else sd
        if h["p"] in ("ES", "SER") and h["o"] and "_" not in h["o"]:
            so = self._singular(nrm(h["o"]).lower(), "")
            if so:
                h["o"] = clave(so)
                od = self._sing_disp(h.get("o_disp") or "", so) or self.acentos.get(so) or so
                h["o_disp"] = od
        tpl = h.get("template") or ""
        if tpl:
            def un(m):
                v = m.group(2)
                if v == "son":
                    nv = "es"
                elif v.endswith(("an", "en")) and not v.endswith(("ron", "cion", "sion")) and len(v) > 3:
                    nv = v[:-1]
                else:
                    nv = v
                return m.group(1) + nv
            h["template"] = re.sub(r"(\{s\} (?:no )?)(\w+)", un, tpl, count=1)

    def _guardar(self, h: Hecho, frase: str, via: str, rep: dict):
        if h.get("p") in _SINONIMO_PRED:
            h["p"] = _SINONIMO_PRED[h["p"]]
        if not self._ok(h):
            rep["descartados"] = rep.get("descartados", 0) + 1
            rep.setdefault("lista_descartados", []).append((h["s"], h["p"], h["o"]))
            return
        self._canon(h)
        if not self._ok(h):
            rep["descartados"] = rep.get("descartados", 0) + 1
            return
        if h.get("s_disp"):
            self.disp_map.setdefault(h["s"], h["s_disp"])
        tr = (h["s"], h["p"], h["o"])
        if tr[0] == tr[2] or not all(tr):
            return
        nuevo = self.mem.add_fact(tr, source=frase[:300], neg=bool(h.get("neg")), when=h.get("when", ""), when_disp=h.get("when_disp", ""))
        self.mem.note_surface(tr, h.get("template") or None, h.get("s_disp"), h.get("o_disp"))
        rep["hechos"].append({"s": tr[0], "p": tr[1], "o": tr[2], "neg": bool(h.get("neg")), "frase": frase, "via": via, "nuevo": bool(nuevo),
                              "sd": h.get("s_disp") or tr[0].title(), "od": h.get("o_disp") or tr[2].title()})

    def _lista_inciso(self, cabeza: Optional[str], texto: str) -> List[Hecho]:
        """«mamifero —ponedor de huevos, venenoso, con hocico en forma de pico de pato y cola de castor—»: rasgos del tema."""
        t = self.ex.tema
        if not t.key:
            return []
        out = []
        items = [x.strip() for x in re.split(r",\s*|\s+y\s+(?=con |de |sin )|\s+y\s+(?=[a-záéíóúñ]+(?: de| en)? )", texto) if x.strip()]
        lex = self.ex.lex
        con = False
        for it in items:
            ws = toks(it)
            if not ws:
                continue
            if ws[0].n == "con":
                np = np_en(ws, 1, lex)
                con = True
                if np:
                    out.append(_h(t.key, "TENER", np.key, t.disp, np.disp, tpl="{s} tiene {o}"))
                    if "_DE_" in np.key:
                        b = np.key.split("_DE_")[0]
                        out.append(_h(t.key, "TENER", b, t.disp, np.disp.split(" de ")[0], tpl="{s} tiene {o}"))
                        out.append(_h(np.key, "ES", b, np.disp, np.disp.split(" de ")[0]))
            elif len(ws) == 1 and lex.es_adj(ws[0].t):
                out.append(_h(t.key, "SER", clave(ws[0].t), t.disp, ws[0].t.lower()))
            elif ws[0].n.endswith("dor") or ws[0].n.endswith("dora"):
                out.append(_h(t.key, "SER", clave(it), t.disp, it.lower()))
            elif con and np_en(ws, 0, lex):
                np = np_en(ws, 0, lex)
                out.append(_h(t.key, "TENER", np.key, t.disp, np.disp, tpl="{s} tiene {o}"))
                if "_DE_" in np.key:
                    b = np.key.split("_DE_")[0]
                    out.append(_h(t.key, "TENER", b, t.disp, np.disp.split(" de ")[0], tpl="{s} tiene {o}"))
                    out.append(_h(np.key, "ES", b, np.disp, np.disp.split(" de ")[0]))
            elif lex.es_adj(ws[0].t):
                out.append(_h(t.key, "SER", clave(it), t.disp, it.lower()))
        return out

    def frase(self, f: str, rep: dict, inicio_parrafo=False):
        ex = self.ex
        orig = f
        if not any(ex.lex.lema(w.t) and (not w.cap or k_ == 0) for k_, w in enumerate(toks(PAREN.sub("", f)))) and len(f.split()) < 16:
            rep["omitidas"] = rep.get("omitidas", 0) + 1                # pie de foto o titular sin verbo: no es una afirmación
            return
        sin_cita = f
        # nombres cientificos entre parentesis justo despues del sujeto
        for m in list(PAREN.finditer(f)):
            c = m.group(1).strip()
            if BINOM.match(c) and ex.tema.key is None or BINOM.match(c) and inicio_parrafo:
                pre = f[:m.start()].strip()
                np = np_en(toks(pre), 0, ex.lex, inicio_frase=True)
                if np and not np.fin < len(toks(pre)) - 0 or np:
                    ex.tema.poner(np.key, np.disp, np.propio)
                    h = _h(np.key, "NOMBRE_CIENTIFICO", clave(c), np.disp, c, tpl="{s} tiene como nombre científico {o}")
                    self._guardar(h, orig, "patron", rep)
                    try:
                        self.mem.alias[clave(c)] = np.key
                    except Exception:                                   # noqa
                        pass
        f = PAREN.sub("", f)
        incisos = []
        for m in INCISO.finditer(f):
            incisos.append(m.group(1).strip())
        f = INCISO.sub(" ", f)
        f = re.sub(r"\s+([,.;:])", r"\1", re.sub(r"\s+", " ", f)).strip()
        f = re.sub(r"^(?:adem[aá]s|asimismo|por otro lado|sin embargo|por eso|por ello|as[ií]|por lo tanto|en resumen|en consecuencia|de hecho|entonces|igualmente|tambi[eé]n|actualmente|hoy en d[ií]a),?\s+", "", f, flags=re.I)
        # nombres: "Su nombre común en inglés, Platypus, es un término…" / "Los aborígenes nombran al X de formas: A, B, C"
        mn = re.match(r"^(?:[Ss]u|[Ee]l) nombre (?:com[uú]n|cient[ií]fico|popular|oficial)?\s*(?:en [a-záéíóúñ]+)?,?\s*([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+(?: [a-z]+)?),?\s+(?:es|era|proviene|deriva)", f)
        if mn and ex.tema.key:
            nom = mn.group(1)
            self._guardar(_h(ex.tema.key, "NOMBRE_EN_OTRA_LENGUA", clave(nom), ex.tema.disp, nom, tpl="{s} también se llama {o}"), orig, "patron", rep)
            try:
                self.mem.alias[clave(nom)] = ex.tema.key
            except Exception:                                           # noqa
                pass
        n0 = len(rep["hechos"])
        if re.match(r"^(?:su|el|los|sus) nombres?\b", f, re.I):
            if mn or len(rep["hechos"]) > n0:
                return                                                  # frase de nombres: ya resuelta
            return                                                      # etimologia/nombres: informativa, no es un fallo
        primera = True
        ex.principal_siguiente = None
        for cl, suj in self._clausulas(f):
            if suj == "SKIP":
                continue
            antes_ = ex.ultimo
            try:
                hs = ex.clausula(cl, inicio=inicio_parrafo and primera, sujeto=suj if suj else None)
            except Exception:                                           # noqa
                hs = []
            if primera and ex.ultimo is not antes_:
                ex.principal_siguiente = ex.ultimo
            primera = False
            for h in hs:
                self._guardar(h, orig, "patron", rep)
            if not hs and self.escuela and 3 <= len(cl.split()) <= 18 and not suj:
                self._via_escuela(cl, orig, rep)
        if getattr(ex, "principal_siguiente", None):
            ex.principal = ex.principal_siguiente
        for inc in incisos:
            for h in self._lista_inciso(None, inc):
                self._guardar(h, orig, "patron", rep)
        if len(rep["hechos"]) == n0:
            rep["sin_entender"].append({"frase": orig, "motivo": self._motivo(f)})

    def _motivo(self, f):
        ws = toks(f)
        if len(ws) > 40:
            return "frase muy larga y sin una estructura sujeto-verbo-complemento reconocible"
        if not any(self.ex.lex.lema(w.t) for w in ws):
            return "no encuentro un verbo conjugado que conozca"
        return "no reconozco el sujeto o el complemento"

    def _antecedente(self, ws, k):
        """NP que termina justo antes de la coma ws[k] (para las relativas «George Shaw, que …»). -> (key, disp, propio) | None."""
        lex = self.ex.lex
        for st in range(max(0, k - 6), k):
            np = np_en(ws[st:k], 0, lex, inicio_frase=(st == 0))
            if np is not None and np.fin == k - st:
                if not np.propio and ("_DE_" in np.key or np.key.split("_")[0] in {"UNA", "UNO", "CUATRO", "CINCO", "DOS", "TRES", "SEIS", "SIETE", "OCHO", "NUEVE", "DIEZ"}):
                    return None
                return np.key, np.disp, np.propio
        return None

    def _clausulas(self, f: str):
        """-> [(texto, sujeto_forzado|None)]. Parte por «; », subordinadas iniciales, relativas («, que …» con su antecedente) y coordinadas con verbo propio."""
        f = f.rstrip(".!? ")
        lex = self.ex.lex
        res = []
        for p in re.split(r";\s+", f):
            ws = toks(p)
            cortes = [(0, None)]
            if ws and ws[0].n in ("cuando", "si", "aunque", "mientras", "tras", "despues", "antes", "como") and (ws[0].n != "como" or True):
                for k in range(2, min(len(ws), 24)):
                    if ws[k].t == ",":
                        cortes.append((k + 1, None))
                        break
            for k, w in enumerate(ws):
                if w.t == "," and k + 1 < len(ws):
                    sig = " ".join(x.t for x in ws[k + 1:k + 4])
                    if RELATIVO.match(sig):
                        ant = self._antecedente(ws, k)
                        cortes.append((k + 1, ant if ant else "SKIP"))
                    elif SUBORD.match(sig):
                        cortes.append((k + 1, None))
                    elif lex.lema(ws[k + 1].t) and not ws[k + 1].cap and not lex.es_adj(ws[k + 1].t) and ws[k + 1].n not in lex.N:
                        ini_seg = max([c[0] for c in cortes] + [0])
                        if any(lex.lema(x.t) and x.n not in lex.N and x.n not in _NO_VERBO for x in ws[ini_seg:k]):
                            cortes.append((k + 1, None))
                elif w.n in ("pero", "aunque", "porque") and k > 0 and ws[k - 1].t != ",":
                    cortes.append((k, None))
                elif w.n == "y" and k + 1 < len(ws) and k > 1 and lex.lema(ws[k + 1].t) and not ws[k + 1].cap and ws[k + 1].n not in _NO_VERBO and not lex.es_adj(ws[k + 1].t) and ws[k + 1].n not in DET \
                        and any(lex.lema(x.t) and x.n not in lex.N for x in ws[max([c[0] for c in cortes] + [0]):k]):
                    cortes.append((k + 1, "PREV"))
            cortes = sorted(set(cortes), key=lambda c: c[0])
            fin = [(len(ws), None)]
            for (a, suj), (b, _) in zip(cortes, cortes[1:] + fin):
                trozo = ws[a:b]
                if suj not in (None, "PREV", "SKIP") and trozo and trozo[0].n in ("que", "quien", "quienes", "donde", "cuyo", "cuya", "cuyos", "cuyas", "el", "la", "los", "las") and trozo[0].n != "que":
                    suj = "SKIP"
                while trozo and (trozo[0].t == "," or trozo[0].n in ("pero", "aunque", "porque", "y", "e", "ya", "que", "puesto", "debido", "mientras", "cuando", "si", "bien", "tras", "como", "quien", "quienes")):
                    if trozo[0].n in ("ya", "puesto", "debido") and len(trozo) > 1 and trozo[1].n == "que":
                        trozo = trozo[2:]
                        continue
                    if trozo[0].n == "si" and len(trozo) > 1 and trozo[1].n == "bien":
                        trozo = trozo[2:]
                        continue
                    trozo = trozo[1:]
                txt = " ".join(x.t for x in trozo).replace(" ,", ",")
                if len(trozo) >= 2:
                    res.append((txt, suj))
        return res or [(f, None)]

    def _via_escuela(self, cl: str, orig: str, rep: dict):
        t = self.ex.tema
        txt = cl
        ws = toks(cl)
        if t.key and (not ws or ws[0].n in ("es", "son", "fue", "era", "tiene", "tienen", "se")):
            txt = ("El " if not t.propio else "") + (t.disp or "") + " " + cl[:1].lower() + cl[1:]
        try:
            found = self.escuela(txt, t.disp) or []
        except Exception:                                               # noqa
            found = []
        for x in found:
            if not x.get("s") or not x.get("o"):
                continue
            h = _h(x["s"].upper(), x["p"].upper(), x["o"].upper(), x.get("s_disp") or "", x.get("o_disp") or "", tpl=x.get("template") or "", neg=bool(x.get("neg")), when=x.get("when", ""), when_disp=x.get("when_disp", ""))
            self._guardar(h, orig, "escuela", rep)

    def ficha(self, clave_: str, valor: str, rep: dict) -> bool:
        """Dato de ficha «Clave: valor». El lector de patrones no lo aprovecha (lo trata como titulo); el lector con escuela lo guarda."""
        return False

    def leer(self, texto: str, progreso: Optional[Callable] = None) -> dict:
        texto = (texto or "")[:MAX_TEXTO]
        for t_ in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{3,}", texto):
            n_ = nrm(t_)
            self.vistos.add(n_)
            if t_[0].islower():
                self.minus.add(n_)
                if n_ != t_.lower() and n_ not in self.acentos:
                    self.acentos[n_] = t_
        rep = {"hechos": [], "sin_entender": [], "titulos": [], "frases": 0, "caracteres": len(texto), "descartados": 0}
        primera_del_bloque = True
        for tipo, par in limpiar(texto):
            if tipo == "titulo":
                rep["titulos"].append(par)
                continue
            if tipo == "ficha":
                k_, _, v_ = par.partition("\t")
                if not self.ficha(k_, v_, rep):
                    rep["titulos"].append(k_ + ": " + v_)
                continue
            for k, f in enumerate(frases(par)):
                rep["frases"] += 1
                self.frase(f, rep, inicio_parrafo=(k == 0))
                if progreso and rep["frases"] % 20 == 0:
                    progreso(rep["frases"])
        rep["nuevos"] = sum(1 for h in rep["hechos"] if h["nuevo"])
        return rep


def resumen(rep: dict, maximo=8) -> str:
    """Respuesta corta para el chat."""
    if not rep["frases"]:
        return "No he encontrado frases que leer."
    por = {}
    for h in rep["hechos"]:
        if h["nuevo"]:
            por.setdefault(h["sd"], []).append(h)
    mem_ = rep.get("memorizadas", 0)
    L = [f"He leído {rep['frases']} frases y he aprendido {rep['nuevos']} hechos nuevos"
         + (f" (sobre {len(por)} temas)" if por else "")
         + (f"; he memorizado {mem_} frases completas para poder responder preguntas sobre lo que dicen" if mem_ else "")
         + (f"; en {len(rep['sin_entender'])} no he podido sacar hechos sueltos" + (", pero quedan memorizadas" if mem_ else "") if rep["sin_entender"] else "")
         + (f" y he descartado {rep['descartados']} datos poco fiables" if rep.get("descartados") else "") + "."]
    n = 0
    for sd, hs in por.items():
        L.append(f"· {sd}: " + "; ".join(f"{h['p'].lower().replace('_', ' ')} {h['od']}" for h in hs[:6]) + ("…" if len(hs) > 6 else ""))
        n += 1
        if n >= maximo:
            break
    if rep.get("anclaje"):
        c_ = rep["anclaje"]["cuenta"]
        L.append(f"Conceptos: {c_['conocido']} que ya conocía, {c_['entidad']} nombres propios, {c_['nuevo']} nuevos y {c_.get('dudoso', 0)} que no encajan con mi diccionario.")
    if rep["sin_entender"]:
        L.append("No he entendido, por ejemplo: «" + rep["sin_entender"][0]["frase"][:120] + "» (" + rep["sin_entender"][0]["motivo"] + ").")
    return "\n".join(L)
