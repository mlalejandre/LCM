"""Morfología mínima del español para el núcleo 2.0: normalización, números, género y conjugación
(análisis forma -> lema/tiempo/persona y generación lema -> forma). Sin dependencias externas."""
from __future__ import annotations

import re
import unicodedata

PERS = ("1s", "2s", "3s", "1p", "3p")


def sa(s: str) -> str:
    """minúsculas sin acentos (conserva ñ)."""
    s = str(s).lower().replace("ñ", "\0")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.replace("\0", "ñ")


# ---------------------------------------------------------------- números
_UNI = "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis diecisiete dieciocho diecinueve veinte".split()
_DEC = {"treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90, "cien": 100, "ciento": 100, "mil": 1000}
NUM = {w: i for i, w in enumerate(_UNI)}
NUM.update({"un": 1, "una": 1, "veintiun": 21, "veintiuno": 21, "veintiuna": 21, "veintidos": 22, "veintitres": 23, "veinticuatro": 24, "veinticinco": 25,
            "veintiseis": 26, "veintisiete": 27, "veintiocho": 28, "veintinueve": 29, "medio": 0.5, "media": 0.5, "ningun": 0, "ninguna": 0, "ningunos": 0})
NUM.update(_DEC)
_PAL = {0: "cero", 1: "uno", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis", 7: "siete", 8: "ocho", 9: "nueve", 10: "diez", 11: "once", 12: "doce",
        13: "trece", 14: "catorce", 15: "quince", 16: "dieciséis", 17: "diecisiete", 18: "dieciocho", 19: "diecinueve", 20: "veinte"}


def numero(w):
    w = sa(w)
    if re.fullmatch(r"\d+(?:[.,]\d+)?", w):
        x = float(w.replace(",", "."))
        return int(x) if x == int(x) else x
    return NUM.get(w)


def num_pal(n, genero="m"):
    if isinstance(n, float) and n == int(n):
        n = int(n)
    if n == 1:
        return "un" if genero == "m" else "una"
    return _PAL.get(n, str(n))


# ---------------------------------------------------------------- género y número de nombres
_FEM_NO_A = set("carmen isabel pilar raquel beatriz ines mercedes dolores rocio irene lourdes nieves ester esther belen montserrat mar sol luz paz noemi rut ruth judit judith salome "
                "carol miriam maribel leonor soledad concepcion consuelo rosario amparo maite marisol araceli nuri noor raquel abigail elisabet elizabeth liz iris lis cris "
                "matilde clotilde beatrix guadalupe socorro milagros remedios angeles asuncion encarnacion trini charo mamen maricarmen merche nerea".split())
_MASC_A = set("luca borja josema garcia joshua elias isaias matias tobias jeremias zacarias andrea_m nikita bautista santi rafa chema txema gorka kepa aitzol jona".split())
_SUST_M_A = set("dia mapa problema idioma sofa planeta tema clima programa sistema poema drama pijama papa futbolista cura tranvia".split())
_SUST_F = set("mano foto moto radio flor leche noche tarde gente calle clase llave nube nieve sangre carne sal piel miel pared ciudad red luz voz paz vez tos ley "
              "madre mujer hermana fuente torre parte muerte suerte mente frase base fase clave nave sede tele imagen cancion razon".split())


def genero_nombre(nombre: str) -> str:
    n = sa(nombre.split()[0])
    if n in _FEM_NO_A:
        return "f"
    if n in _MASC_A:
        return "m"
    return "f" if n.endswith("a") else "m"


GEN_EXTRA = {}            # género de sustantivos que no se deduce de la terminación (lo rellena la base de conceptos)


def genero_sust(lema: str) -> str:
    g = GEN_EXTRA.get(sa(lema))
    if g:
        return g
    n = sa(lema.split()[0])
    if n in _SUST_M_A:
        return "m"
    if n in _SUST_F or n.endswith(("a", "cion", "sion", "dad", "tad", "tud", "umbre", "ez")):
        return "f"
    return "m"


def singular(w: str) -> str:
    n = w
    s = sa(w)
    if len(s) <= 3 or not s.endswith("s") or s in ("lunes", "martes", "miercoles", "jueves", "viernes", "crisis", "tesis", "dosis", "gafas", "tijeras", "paraguas", "cumpleaños", "virus", "atlas", "pais", "mes", "tos", "dios", "autobus", "ingles", "frances", "interes", "compas", "adios", "anis", "bus", "gas", "ras", "tras", "dos", "tres", "seis", "menos", "mas", "lejos", "gratis", "carlos", "marcos", "luis", "tomas", "andres", "ines", "jesus", "nicolas", "matias", "lucas", "paris", "mercedes", "dolores", "nieves", "lourdes", "angeles"):
        return n
    if s in ("paises", "meses", "autobuses", "intereses", "ingleses", "franceses", "dioses", "gases", "toses", "buses"):
        return n[:-2]
    if s.endswith("ces"):
        return n[:-3] + "z"
    if s.endswith(("ones", "anes", "enes", "ines")) and len(s) > 5:
        base = n[:-2]
        return base[:-2] + {"on": "ón", "an": "án", "en": "én", "in": "ín"}[sa(base)[-2:]] if sa(base)[-2:] in ("on", "an", "en", "in") else base
    if s.endswith(("es", "as", "is", "os", "us")) and n[-2:-1] in "éáíóú" and len(s) > 3:
        return n                                       # «portugués», «inglés», «compás»: agudas terminadas en -s ya son singulares
    if s.endswith(("eses", "anes", "ines", "ones")) and False:
        pass
    if s.endswith("ses"):
        return n[:-1]                                  # clases, frases, bases (los agudos en -s van en la lista de arriba)
    if s.endswith(("res", "les", "des", "nes")) and s[-4] not in "aeiou":
        return n[:-1]                                  # padres, muebles, calles, verdes, carnes
    if s.endswith(("res", "les", "des", "nes", "yes", "jes")):
        return n[:-2]
    if s.endswith(("is", "us")) and not s.endswith(("ais", "eis")):
        return n
    return n[:-1]


def plural(w: str) -> str:
    s = sa(w)
    if s.endswith(("s", "x")):
        return w
    if s.endswith("z"):
        return w[:-1] + "ces"
    if s[-1] in "aeiou" or w[-1] in "áéó":
        return w + "s"
    if w.endswith(("ón", "án", "én", "ín")):
        return sa(w[-2:]).join([w[:-2], ""]) + "es"
    return w + "es"


_FEM_CONS = {"española": "español", "francesa": "frances", "inglesa": "ingles", "alemana": "aleman", "portuguesa": "portugues", "japonesa": "japones", "holandesa": "holandes",
             "irlandesa": "irlandes", "escocesa": "escoces", "catalana": "catalan", "andaluza": "andaluz", "trabajadora": "trabajador", "habladora": "hablador",
             "encantadora": "encantador", "holgazana": "holgazan", "dormilona": "dormilon", "cabezona": "cabezon", "china": "chino"}
_INV_A = {"rosa", "lila", "violeta", "naranja", "belga", "hipocrita", "idiota", "optimista", "pesimista", "egoista", "agricola", "fucsia", "turquesa", "malva", "croata", "israelita"}


def masc(adj: str) -> str:
    """forma masculina singular aproximada de un adjetivo/participio (sin acentos)."""
    a = sa(adj)
    if a.endswith("ces") and len(a) > 4:
        a = a[:-3] + "z"
    elif a.endswith("es") and len(a) > 4 and a[-3] in "lrnsdj" and a[-4] in "aeiou":
        a = a[:-2]
    elif a.endswith("s") and len(a) > 3 and a[-2] in "aeiou" and a not in ("gris", "cortes", "ingles", "frances", "japones", "portugues", "gratis", "lejos"):
        a = a[:-1]
    if a in _FEM_CONS:
        return _FEM_CONS[a]
    if a.endswith("a") and len(a) > 3 and a not in _INV_A and not a.endswith("ista"):
        a = a[:-1] + "o"
    return a


def concuerda(adj_m: str, genero: str, plural_: bool = False) -> str:
    a = adj_m
    if genero == "f" and a.endswith("o"):
        a = a[:-1] + "a"
    elif genero == "f" and a.endswith(("dor", "tor", "sor", "on", "an", "in", "es")) and a not in ("mayor", "menor", "mejor", "peor", "joven", "marron", "cortes", "gris"):
        a = (a[:-2] + "es" if a.endswith("es") else a) + "a" if not a.endswith("es") else a[:-2] + "esa"
    if plural_:
        a = a + ("s" if a[-1] in "aeiou" else "es")
    return a


# ---------------------------------------------------------------- conjugación
_REG = {
    "ar": {"pres": "o as a amos an", "pret": "é aste ó amos aron", "imp": "aba abas aba ábamos aban"},
    "er": {"pres": "o es e emos en", "pret": "í iste ió imos ieron", "imp": "ía ías ía íamos ían"},
    "ir": {"pres": "o es e imos en", "pret": "í iste ió imos ieron", "imp": "ía ías ía íamos ían"},
}
_FUT = "é ás á emos án".split()
_COND = "ía ías ía íamos ían".split()
_IRR = {  # lema: pres | pret | imp | raíz de futuro | participio | gerundio   ('' = regular)
    "ser": "soy eres es somos son|fui fuiste fue fuimos fueron|era eras era éramos eran||sido|siendo",
    "estar": "estoy estás está estamos están|estuve estuviste estuvo estuvimos estuvieron||||",
    "tener": "tengo tienes tiene tenemos tienen|tuve tuviste tuvo tuvimos tuvieron||tendr||",
    "ir": "voy vas va vamos van|fui fuiste fue fuimos fueron|iba ibas iba íbamos iban||ido|yendo",
    "haber": "he has ha hemos han|hube hubiste hubo hubimos hubieron||habr||",
    "hacer": "hago haces hace hacemos hacen|hice hiciste hizo hicimos hicieron||har|hecho|",
    "decir": "digo dices dice decimos dicen|dije dijiste dijo dijimos dijeron||dir|dicho|diciendo",
    "poder": "puedo puedes puede podemos pueden|pude pudiste pudo pudimos pudieron||podr||pudiendo",
    "querer": "quiero quieres quiere queremos quieren|quise quisiste quiso quisimos quisieron||querr||",
    "saber": "sé sabes sabe sabemos saben|supe supiste supo supimos supieron||sabr||",
    "venir": "vengo vienes viene venimos vienen|vine viniste vino vinimos vinieron||vendr||viniendo",
    "dar": "doy das da damos dan|di diste dio dimos dieron||||",
    "ver": "veo ves ve vemos ven|vi viste vio vimos vieron|veía veías veía veíamos veían||visto|",
    "poner": "pongo pones pone ponemos ponen|puse pusiste puso pusimos pusieron||pondr|puesto|",
    "salir": "salgo sales sale salimos salen|||saldr||",
    "traer": "traigo traes trae traemos traen|traje trajiste trajo trajimos trajeron||||trayendo",
    "caer": "caigo caes cae caemos caen|caí caíste cayó caímos cayeron||||cayendo",
    "oir": "oigo oyes oye oímos oyen|oí oíste oyó oímos oyeron||||oyendo",
    "leer": "|leí leíste leyó leímos leyeron||||leyendo",
    "creer": "|creí creíste creyó creímos creyeron||||creyendo",
    "conducir": "conduzco conduces conduce conducimos conducen|conduje condujiste condujo condujimos condujeron||||",
    "traducir": "traduzco traduces traduce traducimos traducen|traduje tradujiste tradujo tradujimos tradujeron||||",
    "producir": "produzco produces produce producimos producen|produje produjiste produjo produjimos produjeron||||",
    "andar": "|anduve anduviste anduvo anduvimos anduvieron||||",
    "caber": "quepo cabes cabe cabemos caben|cupe cupiste cupo cupimos cupieron||cabr||",
    "valer": "valgo vales vale valemos valen|||valdr||",
    "reir": "río ríes ríe reímos ríen|reí reíste rio reímos rieron||||riendo",
    "sonreir": "sonrío sonríes sonríe sonreímos sonríen|sonreí sonreíste sonrió sonreímos sonrieron||||sonriendo",
    "oler": "huelo hueles huele olemos huelen|||||",
    "jugar": "juego juegas juega jugamos juegan|jugué jugaste jugó jugamos jugaron||||",
    "abrir": "||||abierto|", "escribir": "||||escrito|", "romper": "||||roto|", "volver": "vuelvo vuelves vuelve volvemos vuelven||||vuelto|",
    "morir": "muero mueres muere morimos mueren|morí moriste murió morimos murieron|||muerto|muriendo",
    "dormir": "duermo duermes duerme dormimos duermen|dormí dormiste durmió dormimos durmieron||||durmiendo",
    "cubrir": "||||cubierto|", "descubrir": "||||descubierto|", "resolver": "resuelvo resuelves resuelve resolvemos resuelven||||resuelto|",
    "devolver": "devuelvo devuelves devuelve devolvemos devuelven||||devuelto|",
    "construir": "construyo construyes construye construimos construyen|construí construiste construyó construimos construyeron||||construyendo",
}
_CAMBIO = {  # diptongación / cierre vocálico en presente (1s 2s 3s 3p)
    "ie": "pensar empezar cerrar entender perder preferir sentir comenzar despertar sentar mentir divertir recomendar calentar encender defender atender nevar merendar regar negar confesar atravesar gobernar apretar tropezar fregar sugerir convertir advertir herir hervir invertir referir",
    "ue": "encontrar contar recordar costar llover mostrar soñar almorzar volar probar sonar acordar acostar aprobar colgar demostrar mover morder doler soler rogar tostar forzar renovar soltar torcer cocer oler_ apostar comprobar consolar",
    "i": "pedir seguir servir repetir vestir conseguir elegir medir despedir competir corregir impedir perseguir reñir teñir freir derretir",
}
_CAMB = {v: k for k, vs in _CAMBIO.items() for v in vs.split()}
_ZCO = ("conocer", "parecer", "nacer", "crecer", "ofrecer", "agradecer", "merecer", "obedecer", "pertenecer", "aparecer", "desaparecer", "reconocer", "establecer", "padecer", "permanecer", "amanecer", "anochecer", "envejecer", "favorecer", "enriquecer", "lucir")
_PRET_I = {"sentir", "preferir", "mentir", "divertir", "sugerir", "convertir", "advertir", "herir", "hervir", "invertir", "referir", "pedir", "seguir", "servir", "repetir", "vestir", "conseguir", "elegir", "medir",
           "despedir", "competir", "corregir", "impedir", "perseguir", "derretir"}


def _lem(lema):
    return sa(lema).replace("ñ", "ñ")


def _cambia(raiz, tipo):
    i = max(raiz.rfind("e"), raiz.rfind("o")) if tipo != "i" else raiz.rfind("e")
    if tipo == "ie":
        i = raiz.rfind("e")
    if tipo == "ue":
        i = raiz.rfind("o")
    if i < 0:
        return raiz
    return raiz[:i] + {"ie": "ie", "ue": "ue", "i": "i"}[tipo] + raiz[i + 1:]


_HIATO = {"maulla": "maúlla", "maullan": "maúllan", "maullas": "maúllas", "maullo": "maúllo", "aulla": "aúlla", "aullan": "aúllan", "aullas": "aúllas", "aullo": "aúllo"}


def conjugar(lema: str, tiempo: str = "pres", persona: str = "3s") -> str:
    f = _conjugar(lema, tiempo, persona)
    return _HIATO.get(f, f) if tiempo == "pres" else f


def _conjugar(lema: str, tiempo: str = "pres", persona: str = "3s") -> str:
    """tiempo: pres | pret | imp | fut | cond | part | ger | inf."""
    lema = sa(lema)
    refl = lema.endswith("se") and len(lema) > 4 and lema[-4:-2] in ("ar", "er", "ir")
    if refl:
        lema = lema[:-2]
    if tiempo == "inf":
        return lema
    irr = _IRR.get(lema)
    partes = (irr.split("|") if irr else [""] * 6) + [""] * 6
    term = lema[-2:] if lema[-2:] in _REG else ("ir" if lema.endswith(("ír",)) else "ar")
    if lema in ("oir", "reir", "sonreir", "freir"):
        term = "ir"
    raiz = lema[:-2]
    k = PERS.index(persona) if persona in PERS else 2
    if tiempo == "part":
        return partes[4] or raiz + ("ado" if term == "ar" else "ido")
    if tiempo == "ger":
        return partes[5] or raiz + ("ando" if term == "ar" else "iendo")
    if tiempo in ("fut", "cond"):
        base = partes[3] or lema
        return base + (_FUT if tiempo == "fut" else _COND)[k]
    idx = {"pres": 0, "pret": 1, "imp": 2}[tiempo]
    if partes[idx]:
        return partes[idx].split()[k]
    fin = _REG[term][tiempo].split()[k]
    if tiempo == "pres":
        if lema in _CAMB and persona in ("1s", "2s", "3s", "3p"):
            raiz = _cambia(raiz, _CAMB[lema])
        if persona == "1s":
            if lema in _ZCO:
                return raiz[:-1] + "zco"
            if lema.endswith(("ger", "gir")):
                return raiz[:-1] + "jo"
            if lema.endswith("guir"):
                return raiz[:-1] + "o"
    if tiempo == "pret":
        if lema in _PRET_I and persona in ("3s", "3p"):
            raiz = _cambia(raiz, "i")
        if persona == "1s" and term == "ar":
            if raiz.endswith("c"):
                raiz = raiz[:-1] + "qu"
            elif raiz.endswith("g"):
                raiz = raiz + "u"
            elif raiz.endswith("z"):
                raiz = raiz[:-1] + "c"
    return raiz + fin


_FORMAS = None
_VERBOS_BASE = """ser estar tener ir haber hacer decir poder querer saber venir dar ver poner salir traer caer oir leer creer conducir traducir andar valer reir jugar abrir escribir romper volver morir dormir
vivir trabajar comer beber comprar vender hablar estudiar llamar gustar encantar interesar molestar apetecer doler importar necesitar usar utilizar llevar tomar pasar quedar dejar llegar entrar mirar escuchar
cantar bailar nadar correr caminar pasear viajar cocinar preparar limpiar lavar cuidar ayudar amar odiar adorar preferir pensar empezar cerrar entender perder sentir encontrar contar recordar costar mostrar
soñar almorzar volar pedir seguir servir repetir vestir conseguir elegir conocer parecer nacer crecer ofrecer regalar prestar entregar enviar mandar recibir aprender enseñar tocar pintar dibujar construir
visitar esperar buscar pagar ganar cambiar abrazar besar saludar invitar acompañar odiar temer deber soler aparcar conducir montar practicar desayunar cenar merendar descansar levantar acostar despertar
duchar bañar peinar casar mudar llorar sonreir gritar saltar subir bajar coger tirar guardar perder olvidar terminar acabar comenzar continuar intentar lograr decidir creer suponer explicar preguntar responder
contestar llover nevar robar matar criar adoptar pasear plantar regar cortar arreglar reparar romper celebrar cumplir medir pesar durar tardar faltar sobrar tener pertenecer colecciona_ coleccionar tejer coser
leer escribir ver mirar oler probar tostar hornear freir asar hervir fumar toser respirar reir divertir aburrir preocupar asustar alegrar enfadar cansar emocionar fascinar disfrutar sufrir
aullar balar cazar circular croar flotar funcionar gruñir ladrar maullar mover mugir navegar ocurrir picar relinchar reptar rugir sonar brillar caber durar girar rodar morder arder soplar""".split()


def _lemas_verbales():
    lemas = {v for v in _VERBOS_BASE if not v.endswith("_")}
    lemas.update(_IRR)
    lemas.update(_CAMB)
    try:
        from src.language import lexico
        d = lexico._load()
        for i, ps in d.get("pos", {}).items():
            if ps == "v":
                for l in d["syn"].get(i, ()):
                    l = sa(l)
                    if " " not in l and l.endswith(("ar", "er", "ir")) and len(l) > 3:
                        lemas.add(l)
                    elif " " not in l and l.endswith(("arse", "erse", "irse")) and len(l) > 5:
                        lemas.add(l[:-2])
    except Exception:                                                         # noqa
        pass
    lemas.discard("oler_")
    return lemas


def formas():
    """dict forma (con acentos) -> [(lema, tiempo, persona)] y otro sin acentos."""
    global _FORMAS
    if _FORMAS is None:
        ex, lax = {}, {}
        for l in _lemas_verbales():
            for t in ("pres", "pret", "imp", "fut", "cond"):
                for p in PERS:
                    try:
                        f = conjugar(l, t, p)
                    except Exception:                                          # noqa
                        continue
                    ex.setdefault(f, []).append((l, t, p))
            for t in ("part", "ger", "inf"):
                ex.setdefault(conjugar(l, t), []).append((l, t, ""))
        ex.setdefault("hay", []).append(("haber", "pres", "3s"))
        orden = {"pres": 0, "pret": 1, "imp": 2, "fut": 3, "cond": 4, "inf": 5, "part": 6, "ger": 7}
        comunes = set(_VERBOS_BASE) | set(_IRR)
        for f, v in ex.items():
            v.sort(key=lambda x: (x[0] not in comunes, orden[x[1]], PERS.index(x[2]) if x[2] in PERS else 9))
            lax.setdefault(sa(f), []).extend(v)
        for f, v in lax.items():
            v.sort(key=lambda x: (x[0] not in comunes, orden[x[1]], PERS.index(x[2]) if x[2] in PERS else 9))
        _FORMAS = (ex, lax)
    return _FORMAS


def analizar(forma: str, lema_hint: str = None):
    """[(lema, tiempo, persona)] candidatos de una forma verbal (exacta primero; luego sin acentos)."""
    ex, lax = formas()
    f = forma.lower()
    c = list(ex.get(f, ())) or list(lax.get(sa(f), ()))
    if lema_hint:
        h = sa(lema_hint)
        pri = [x for x in c if x[0] == h]
        if pri:
            return pri + [x for x in c if x[0] != h]
    return c
