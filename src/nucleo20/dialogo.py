"""LCM 2.0 · conversación sobre el grafo: afirmaciones, preguntas, correcciones y explicaciones."""
from __future__ import annotations

import copy
import datetime as dt
import os
import re
from typing import Optional

from . import conceptos, vista, coloquial, social
from . import morfo as M
from .morfo import sa
from . import lengua as G
from .lengua import SN, Clausula
from .nucleo import (Nucleo, REL_DISP_BASE, REL_CANON, FAMILIA, SIMETRICAS, INVERSAS, PERSONA_CLS, FUNCIONAL, FUNC_SIEMPRE, V_EQ, DAR, OBTENER, PERDER, IR, COLORES, _ANT, ESTADO_TENER, ACK,
                     _cap, contrae, cambia_persona)

_CREENCIA = re.compile(r"\b(creo|crees|cree|pienso|piensa|supongo|supone|quiza|quizas|tal vez|a lo mejor|dice que|dijo que|dicen que|opina|parece que|ojala|imagino|sospecho|dudo|igual)\b")
_ORDEN = re.compile(r"^(olvida|olvidalo|borra|recuerda que|aprende|define|dormir|guardar|salir|memoria|ayuda|arbol|nuevo|hecho|corrige|entendi|pregunta|lee|resume|compara|dibuja|pinta|genera|crea|calcula|traduce|busca|pon|reserva)\b")
_CORR = re.compile(r"^\s*(?:no|perd[oó]n|perdona|disculpa|me he equivocado|me equivoqu[eé]|me he confundido|me confund[ií]|en realidad|mejor dicho|quer[ií]a decir|quiero decir|corrijo|rectifico|miento)"
                   r"(?:\s*[,:;.]?\s*(?:me he equivocado|me he confundido|me equivoqu[eé]|me confund[ií]))?\s*[,:;.]\s*(?:es que\s+|en realidad\s+|quer[ií]a decir(?: que)?\s+)?", re.I)
_QUE_LLAMA = re.compile(r"^(.*?\b(?:un|una|el|la|mi|su|tu|otro|otra)\s+[\wáéíóúñ]+(?:\s+[\wáéíóúñ]+)?)\s*,?\s+(?:que se llama|llamad[oa]|de nombre)\s+([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)?)\s*([.!]?)$")


_INCRUSTA = re.compile(r"^(?:y |oye,? |por favor,? )?(?:tu )?(?:sabes|sabrias decirme|sabrias|puedes decirme|me puedes decir|podrias decirme|me podrias decir|me dices|dime|recuerdas|te acuerdas de|"
                       r"tienes idea de|me sabrias decir|quiero saber|quisiera saber|necesito saber|me gustaria saber)\s+(si\s+)?(.+)$")


_DELEGA = re.compile(r"\b(?:que dia es hoy|a que dia estamos|que fecha es|en que (?:año|mes|dia) estamos|(?<!a )que hora (?:es|son|tienes)(?! (?:el|la|los|las|tu|mi|su)\b)|a que estamos|que dia es$|(?<!de )que año es(?! (?:el|la|los|las|tu|mi|su)\b)|que mes es)\b|"
                     r"^(?:estoy equivocad[oa]|me he equivocado|me equivoque|eso no es (?:verdad|cierto|asi)|era (?:una )?broma|es mentira|no es verdad|retiro lo dicho)$|"
                     r"\b(?:sirven? para|se usan? para|se utilizan? para|significa|quiere decir|es lo contrario de|es (?:un )?sinonimo de|es lo mismo que|es (?:una )?parte del?|son partes? del?|forma parte del?)\b|"
                     r"^que (?:hemos|habiamos) (?:hablado|dicho|comentado)|^de que (?:hemos|estabamos|estamos) hablando|^(?:que|cuantas cosas|cuanto) sabes$|^cuantos? (?:hechos|cosas|datos) (?:sabes|conoces|recuerdas)")


_DECENAS = {"veinti": 20, "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90}
_UNIDADES = {"uno": 1, "un": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9}


def _gerundio_a_presente(m):
    """«sigue viviendo» -> «vive todavía»."""
    aux, ger = m.group(1).lower(), m.group(0).split()[-1].lower()
    pers = {"sigue": "3s", "siguen": "3p", "sigues": "2s", "sigo": "1s"}[aux]
    c = [x for x in M.analizar(ger) if x[1] == "ger"]
    if not c:
        return m.group(0)
    return M.conjugar(c[0][0], "pres", pers) + " todavía"


def _numeros_compuestos(t):
    """«treinta y dos» -> «32» (los números simples ya los entiende el núcleo)."""
    def r(m):
        u = _UNIDADES.get(sa(m.group(2)))
        return str(_DECENAS[sa(m.group(1))] + u) if u else m.group(0)
    return re.sub(r"\b(treinta|cuarenta|cincuenta|sesenta|setenta|ochenta|noventa) y (uno|un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve)\b", r, t, flags=re.I)


_CUERPO = {"cadera", "pierna", "brazo", "mano", "pie", "tobillo", "muñeca", "muneca", "rodilla", "hombro", "codo", "dedo", "nariz", "diente", "muela", "espalda", "cabeza",
           "cuello", "costilla", "hueso", "uña", "una", "ojo", "oreja", "labio", "pelo"}
_INACUS = {"morir", "nacer", "llegar", "venir", "caer", "ocurrir", "pasar", "romper", "estropear", "perder", "acabar", "terminar", "empezar", "comenzar", "aparecer", "desaparecer",
           "crecer", "salir", "entrar", "volver", "regresar", "marchar", "ir", "quedar", "faltar", "sobrar", "enfermar", "jubilar", "casar", "divorciar", "mudar"}
_RASGOS = {"jardin", "piscina", "terraza", "garaje", "balcon", "ascensor", "trastero", "chimenea", "patio", "vista", "habitacion", "baño", "salon", "cocina", "huerto",
           "porche", "buhardilla", "sotano", "calefaccion", "aire", "techo", "suelo", "motor", "maletero", "rueda", "asiento", "puerta", "ventana"}
_CON_RASGOS = {"casa", "piso", "chalet", "apartamento", "coche", "hotel", "finca", "cortijo", "habitacion", "local", "oficina", "tienda", "restaurante", "bar", "furgoneta", "caravana", "barco", "moto"}
_ANIMADOS = {"invitar", "decir", "llamar", "pedir", "contar", "prometer", "preguntar", "contestar", "responder", "regalar", "felicitar", "saludar", "visitar", "opinar",
             "pensar", "creer", "querer", "enfadar", "reir", "llorar", "casar", "divorciar", "trabajar", "estudiar", "comer", "cenar", "dormir"}
_V_COSA = {"llevar", "traer", "arreglar", "lavar", "vender", "aparcar", "reparar", "pintar", "comprar", "dejar", "guardar", "coger", "romper", "limpiar", "devolver",
           "recoger", "terminar", "acabar", "empezar", "hacer", "preparar", "cocinar", "leer", "escribir", "ver", "probar", "usar", "abrir", "cerrar", "decorar", "montar",
           "regalar", "tirar", "buscar", "encontrar", "perder", "olvidar", "poner", "cambiar", "pagar", "alquilar", "reservar", "plantar", "regar", "construir", "vaciar", "llenar"}
_OBJ_PERSONA = {"invitar", "llamar", "ayudar", "visitar", "ver", "recoger", "esperar", "saludar", "avisar", "felicitar", "buscar", "conocer", "querer", "llevar",
                "acompañar", "operar", "atender", "contratar", "despedir", "echar", "examinar", "entrevistar", "molestar", "despertar", "abrazar", "besar", "engañar",
                "escuchar", "entender", "convencer", "animar", "apoyar", "cuidar", "odiar", "admirar", "preocupar", "sorprender", "regañar", "castigar", "multar", "invitado"}
_V_LUGAR = {"vivir", "estar", "ir", "trabajar", "nacer", "viajar", "mudar", "llegar", "volver", "regresar", "venir", "salir", "residir", "quedar", "veranear", "estudiar", "crecer", "morir"}


def _es_finito(w):
    return any(x[1] in ("pres", "pret", "imp", "fut", "cond") for x in M.analizar(sa(w)))


_EVENTOS_SIN_NOMBRE = {"santo", "cumpleanos", "boda", "fiesta", "cena", "comida", "reunion", "examen", "mudanza", "final", "partido", "viaje", "entierro", "bautizo", "comunion", "aniversario", "graduacion", "cita", "operacion"}


def _Cp_tabla(nuc):
    try:
        from . import compuestos as _C
        return {k for k in _C.tabla(nuc)}
    except Exception:                                    # noqa
        return set()


class Conversador(Nucleo):
    # ================================================================== entrada
    def procesar(self, texto: str) -> Optional[dict]:
        """2.19: los términos de varias palabras («la Torre de Hércules», «el zorro volador») entran como una pieza y salen con su forma."""
        from . import compuestos as _C
        try:
            if texto and not getattr(self, "_leyendo", False):
                if "?" not in texto and len(texto) < 400:
                    _C.aprende_propios(self, texto)
                if len(texto) < 400:
                    texto = _C.codifica(self, texto)
        except Exception:                                # noqa
            pass
        r = r_decl = None
        try:                                             # 2.21: sinónimos que enseña el usuario, y la duda que el modelo le planteó
            from . import sinonimia as _S
            if texto and not getattr(self, "_leyendo", False):
                d_ = getattr(self, "_duda_sentido", None)
                self._duda_sentido = None
                if d_ and self.turno - d_["turno"] <= 1 and len(texto.split()) <= 6:
                    n_ = _S.sa(texto.lower()).strip(" .!¡,")
                    if re.match(r"^(?:si|claro|exacto|eso es|correcto|asi es|efectivamente|vale|eso|lo mismo|si,? (?:es )?lo mismo|si,? claro)\b", n_):
                        for a_, b_ in d_["pares"]:
                            _S.aprende(self, a_, b_)
                        self.turno += 1
                        r = {"respuesta": "Aprendido: " + " y ".join(f"«{a_}» es como «{b_}»" for a_, b_ in d_["pares"]) + ". Entonces: " + d_["respuesta"], "estado": "ok", "consultar": False, "tipo": "resp"}
                    elif re.match(r"^no\b", n_):
                        self.usuario.setdefault("no_sinonimos", []).extend([list(x) for x in d_["pares"]])
                        self.turno += 1
                        r = {"respuesta": "Vale, no es lo mismo. Entonces no lo sé.", "estado": "abst", "consultar": False, "tipo": "abst"}
                if r is None:
                    r_decl = _S.declara(self, texto)
        except Exception:                                # noqa
            r = None
        if r is None and texto and not any(getattr(self, x, False) for x in ("_leyendo", "_partiendo", "_componiendo", "_siguiendo")):
            try:                                         # 2.26: el orden de los pasos, las tareas que faltan y lo que «ya» no es verdad
                from . import hilo as _H
                if "?" in texto:
                    r = _H.responde(self, texto)
                    if r is not None:
                        self.turno += 1
                        self.pend = None
                        self._ult_resp = r["respuesta"]
                elif not os.environ.get("LCM_SIN_HILO"):
                    _H.apunta_paso(self, texto)
            except Exception:                            # noqa
                r = None
        if r is None:
            r = self._sigue_hilo(texto)                  # 2.25: «¿desde cuándo?» tras otra pregunta; «…a las once, no a las diez»
        if r is None:
            r = self._compuesta(texto)                   # 2.25: una frase compuesta de la charla («…y las corto», «…y a Hugo el fútbol») se entiende por sus simples
        if r is None:
            r = self._por_partes(texto)                  # 2.23: frase a frase, igual que al leer: cada frase completa antes de entenderla
        if r is None:
            r = self._procesar_218(texto)
            if r_decl is not None and not (isinstance(r, dict) and r.get("estado") == "ok" and "no lo he entendido" not in sa((r.get("respuesta") or "").lower())):
                r = r_decl                               # el núcleo no tenía nada que hacer con la frase: al menos queda aprendido el sinónimo
        try:
            if isinstance(r, dict) and r.get("respuesta") and _C.tabla(self):
                r = dict(r, respuesta=_C.decodifica(self, r["respuesta"]))
                self._ult_resp = r["respuesta"]
        except Exception:                                # noqa
            pass
        return r

    _WH225 = r"(?:(?:desde|hasta|con|para|por|de|a|en)\s+)?(?:qu[eé]|qui[eé]n(?:es)?|cu[aá]ndo|d[oó]nde|c[oó]mo|cu[aá]nt[oa]s?|cu[aá]l(?:es)?)"

    def _sigue_hilo(self, texto):
        """2.25 · Dos formas de seguir el hilo sin repetir la frase entera:
        - una pregunta de una o dos palabras («¿desde cuándo?», «¿y con quién?») continúa la pregunta anterior: se rehace con ella;
        - «…a las once, no a las diez» corrige lo último que se dijo con «a las diez»."""
        if getattr(self, "_leyendo", False) or getattr(self, "_partiendo", False) or getattr(self, "_componiendo", False) or getattr(self, "_siguiendo", False) or not texto:
            return None
        ant, self._hist225 = getattr(self, "_hist225", None), texto
        if os.environ.get("LCM_SIN_SEGUIMIENTO"):
            return None
        try:
            t = texto.strip()
            m = re.match(r"^¿?\s*(?:y\s+)?(" + self._WH225 + r")\s*\?$", t, re.I)
            if m and ant and "?" in ant:
                ma = re.match(r"^¿?\s*(?:y\s+)?" + self._WH225 + r"\s+(.+?)\s*\?\s*$", ant.strip(), re.I)
                if ma and len(ma.group(1).split()) >= 2:
                    nueva = "¿" + m.group(1).lower() + " " + ma.group(1) + "?"
                    self._siguiendo = True
                    try:
                        r = self.procesar(nueva)
                    finally:
                        self._siguiendo = False
                    self._hist225 = nueva
                    if isinstance(r, dict) and r.get("estado") == "ok":
                        return r
                return None
            mc = re.match(r"^(?:al final\s+|bueno,?\s+|perd[oó]n,?\s+|no,\s+)?(.+?),\s+(?:y\s+)?no\s+((?:a|en|de|con|el|la|los|las|un|una|para|por)\s+.{2,40}?)\.?$", t, re.I)
            if mc and "?" not in t:
                a_, b_ = mc.group(1).strip(), mc.group(2).strip()
                p0 = b_.split()[0].lower()
                k = a_.lower().rfind(" " + p0 + " ")
                if k < 0:
                    return None
                nuevo = a_[k + 1:].strip()
                if len(nuevo.split()) > 5 or sa(nuevo.lower()) == sa(b_.lower()):
                    return None
                for f in reversed(self.F):
                    src = f.get("src") or ""
                    if f.get("vig", True) and re.search(r"\b" + re.escape(b_) + r"(?=\W|$)", src, re.I):
                        corregida = re.sub(r"\b" + re.escape(b_) + r"(?=\W|$)", nuevo, src, count=1, flags=re.I).rstrip(".")
                        self._siguiendo = True
                        try:
                            r = self.procesar("Perdona, me he equivocado: " + corregida[:1].lower() + corregida[1:] + ".")
                        finally:
                            self._siguiendo = False
                        if isinstance(r, dict) and r.get("estado") == "ok":
                            return r
                        return None
                self._siguiendo = True                   # nada que corregir: vale la parte afirmada («Vivo en Madrid, no en Sevilla» -> «Vivo en Madrid»)
                try:
                    r = self.procesar(a_.rstrip(".") + ".")
                finally:
                    self._siguiendo = False
                return r if isinstance(r, dict) and r.get("estado") == "ok" and not sa((r.get("respuesta") or "").lower()).startswith("no lo he entendido") else None
        except Exception:                                # noqa
            return None
        return None

    def _compuesta(self, texto):
        """2.25: «Pelo las patatas y las corto en rodajas» = «Pelo las patatas.» + «Corto las patatas en rodajas.». El núcleo entiende
        cada simple; aquí se parten (coordina.py) y se juntan las respuestas. None si no hay nada que partir."""
        if not texto or getattr(self, "_leyendo", False) or getattr(self, "_partiendo", False) or getattr(self, "_componiendo", False):
            return None
        try:
            from . import coordina as _K
            piezas = _K.partes(texto)
            if not piezas or len(piezas) < 2:
                return None
            self._componiendo = True
            resp, n_ok, raro = [], 0, None
            for pz in piezas:
                r_p = self.procesar(pz)
                tx = (r_p or {}).get("respuesta") or ""
                if isinstance(r_p, dict) and r_p.get("estado") == "ok" and tx and not sa(tx.lower()).startswith("no lo he entendido"):
                    n_ok += 1
                    resp.append(re.sub(r"^(?:¡[^!]+!\s*|Lo siento\.\s*)?Entendido(?:, me lo apunto)?[:.]?\s*", "", tx).rstrip("."))
                elif tx and raro is None:
                    raro = tx
            cuerpo = "; ".join(x for x in resp if x)
            if n_ok == len(piezas) and cuerpo:
                return {"respuesta": "Entendido: " + cuerpo + ".", "estado": "ok", "consultar": False, "tipo": "ack"}
            if n_ok and cuerpo:
                return {"respuesta": "Entendido: " + cuerpo + ". " + (raro or ""), "estado": "ok", "consultar": False, "tipo": "ack"}
            return {"respuesta": raro, "estado": "ok", "consultar": False, "tipo": "ack"} if raro else None
        except Exception:                                # noqa
            return None
        finally:
            self._componiendo = False

    def _por_partes(self, texto):
        """2.23: una frase de la charla que explica algo y no se sostiene sola («Se toca de pie», «…y maman durante un año») se completa
        con aquello de lo que se viene hablando y se lee por partes. Devuelve la respuesta, o None si la frase va por el camino normal."""
        if not texto or "?" in texto or getattr(self, "_leyendo", False) or getattr(self, "_partiendo", False) or len(texto) > 240 or "\n" in texto:
            return None
        try:
            from . import discurso as _D, exposicion as _X, lectura as _L
            t = texto.strip()
            if not _X._impersonal(t) or _X._personal(t):
                self._disc = None                        # se ha pasado a hablar de uno mismo: lo que venga ya no sigue aquel tema («Tenía fiebre» soy yo)
            if len(_L.frases(t)) != 1 or len(t.split()) < 2 or not _X._impersonal(t) or _X._personal(t) \
                    or re.match(r"^\W*(?:dime|dame|cuenta|explica|describe|pon|haz|escribe|apunta|recuerda|olvida|hola|gracias|vale|no,|si,|sí,|perd[oó]n|adi[oó]s)", t, re.I) \
                    or _X._nombra_persona(self, t[:1].upper() + t[1:]):
                return None
            est = getattr(self, "_disc", None)
            if est is None or self.turno - getattr(self, "_disc_turno", -9) > 3:
                est = self._disc = _D.Estado()
            self._disc_turno = self.turno
            T = t[:1].upper() + t[1:]
            T = T if T.endswith(".") else T.rstrip("!") + "."
            w_ini = T.split()[0]
            if w_ini[:1].isupper() and sa(w_ini.lower()) not in _D._DET and not _D._fin3(w_ini) and sa(w_ini.lower()) not in (
                    "se", "no", "con", "en", "debajo", "dentro", "despues", "antes", "tambien", "ademas", "luego", "hoy", "antiguamente", "cuando", "alli", "su", "sus", "para", "al", "a",
                    "de", "por", "si", "durante", "desde", "encima", "detras", "delante", "cerca", "solo", "primero", "entonces"):
                _D.prepara(T, est)                       # empieza por un nombre propio: solo se sigue el hilo; la frase la lee el núcleo como siempre
                return None
            piezas = _D.prepara(T, est)
            if len(piezas) == 1 and piezas[0][0] == T:
                return None
            self._partiendo = True
            resp, n_ok, n_f0 = [], 0, len(self.F)
            tema = next((x[1] for x in piezas if x[1]), None)
            for lista, _tema, _orig in piezas:
                try:
                    from . import compuestos as _Cp
                    sn_p = _D._sujeto(lista.rstrip("."))[0]
                    if sn_p and len(sn_p.split()) == 3:
                        _Cp.aprende_clase(self, sn_p)    # «el pan integral»: en una explicación es una clase de pan, no «el pan» con un adjetivo
                    lista = _Cp.codifica(self, lista)    # «el queso fresco» es una pieza si ya se presentó como tal
                except Exception:                        # noqa
                    pass
                r_p = self._procesar_218(lista)
                if isinstance(r_p, dict) and r_p.get("respuesta"):
                    tx = r_p["respuesta"].strip()
                    if not sa(tx.lower()).startswith("no lo he entendido"):
                        n_ok += 1
                        resp.append(re.sub(r"^Entendido(?:, me lo apunto)?[:.]?\s*", "", tx).rstrip("."))
                    elif "Pero ojo" in tx or "no coincide" in tx:
                        resp.append(tx.rstrip("."))
            self._partiendo = False
            for f_ in self.F[n_f0:]:
                f_.setdefault("expo", True)              # son cosas explicadas: cuentan al describir y al contrastar
            _X._apunta(self, T, tema=tema)               # y queda guardada entera, con su tema, para poder citarla
            self.pend = None
            cuerpo = "; ".join(x for x in resp if x)
            if n_ok and cuerpo:
                return {"respuesta": "Entendido: " + cuerpo + ".", "estado": "ok", "consultar": False, "tipo": "ack"}
            if n_ok:
                return {"respuesta": "Entendido, me lo apunto.", "estado": "ok", "consultar": False, "tipo": "ack"}
            return {"respuesta": f"No lo he entendido del todo, pero me lo apunto tal como lo dices: «{T.rstrip('.')}».", "estado": "ok", "consultar": False, "tipo": "ack"}
        except Exception:                                # noqa
            return None
        finally:
            self._partiendo = False

    def _encadenar(self, texto):
        """2.21: ¿sale juntando dos cosas aprendidas? («el recorrido más largo» es el Transiberiano, y de él sí sé cuánto tarda).
        2.23: se intenta ANTES que nada: si la pregunta nombra algo por su descripción, lo primero es saber de qué habla."""
        if getattr(self, "_encadena", False) or getattr(self, "_leyendo", False) or not texto or "?" not in texto:
            return None
        try:
            from . import cadena as _CD
            cands = _CD.reformula(self, texto)
            if not cands:
                return None
            self._encadena = True
            for cand, nombre, desc in cands:
                self.ult_just = None
                r_c = self._procesar_218(cand)
                if isinstance(r_c, dict) and r_c.get("estado") == "ok" and self._solo_fabrica():
                    c_c = lectura.cita(self, cand, excluye=_CD.fuentes(self, nombre, desc))   # se encadena lo APRENDIDO: lo que «suele» pasar según la fábrica no vale como segundo paso
                    r_c = {"respuesta": c_c, "estado": "ok", "consultar": False, "tipo": "resp"} if c_c else None
                if isinstance(r_c, dict) and r_c.get("estado") == "ok" and r_c.get("tipo") != "ack" and r_c.get("respuesta") \
                        and not any(sa(x.lower()) in sa(r_c["respuesta"].lower()) for x in _CD.fuentes(self, nombre, desc)):
                    r_c = dict(r_c)
                    r_c["respuesta"] = _CD.aviso(r_c["respuesta"], nombre, desc)
                    r_c["encadenado"] = (nombre, desc)
                    self.pend = None
                    return r_c
        except Exception:                                # noqa
            pass
        finally:
            self._encadena = False
        return None

    def _sentido(self, texto):
        """2.24 · La pregunta usa una palabra que no está en lo aprendido (o que allí se dice de otra manera). Se prueba con cada palabra
        aprendida que podría decir lo mismo y DECIDE EL TEXTO: vale la que deja una pregunta que lo aprendido contesta. Un indicio seguro
        basta con que haya respuesta; uno débil necesita que la frase traiga todo lo demás que se pregunta. Si dos lecturas distintas
        quedan igual de bien apoyadas, se dan las dos."""
        from . import sinonimia as _S
        from . import lectura
        cache = getattr(self, "_sent224", None)
        if cache and cache[0] == (self.turno, texto):
            return cache[1]
        res = None
        ant_reform, ant_just, ant_pend = getattr(self, "_reform", False), getattr(self, "ult_just", None), getattr(self, "pend", None)
        try:
            hechos = []
            for cand, cambios, clase, valor, orden in _S.propuestas(self, texto):
                vistos = [cand] + ([] if os.environ.get("LCM_SENTIDO_SIN_TABLA") else _S.alternativas(cand)[:2])
                for q2 in vistos:
                    resp, fuente = None, ""
                    self._reform = True
                    self.ult_just = None
                    try:
                        r_c = self._procesar_charla(q2)
                    except Exception:                    # noqa
                        r_c = None
                    finally:
                        self._reform = ant_reform
                    if isinstance(r_c, dict) and r_c.get("estado") == "ok" and r_c.get("respuesta") and r_c.get("tipo") not in ("ack", "crea") and not self._solo_fabrica():
                        resp = r_c["respuesta"]
                        fuente = resp + " " + " ".join(x for x in ((self.ult_just or {}).get("dicho") or []) if isinstance(x, str))
                    tabla = q2 is not cand               # rehecha además con la tabla de equivalencias («comen» -> «se alimentan de»): el verbo ya no es el de la candidata
                    def _tiempo(x):                      # …pero el tiempo sí tiene que casar: lo que PASÓ no lo contesta una costumbre
                        return _S.ancla(texto, q2, x) if tabla else _S.casa_tiempo(cambios, x)
                    if resp is None or not (_tiempo(resp) and _S.casa_tipo(texto, resp)):
                        resp = lectura.cita(self, q2)
                        fuente = resp or ""
                        if resp and not (_tiempo(resp) and _S.casa_tipo(texto, resp)):
                            resp = None
                    if not resp or not _S.cita_firme(self, q2, cambios, fuente):
                        continue
                    hechos.append({"resp": resp, "cambios": cambios, "clase": clase, "valor": valor, "apoyo": _S.apoyo(self, q2, cambios, fuente), "just": self.ult_just, "orden": orden})
                    break
                if hechos and hechos[-1]["clase"] == "S" and hechos[-1]["cambios"] is cambios:
                    break                                # indicio seguro y con respuesta: no hace falta mirar más
            el = None
            if hechos and hechos[-1]["clase"] == "S":
                el = hechos[-1]
            else:
                # con apoyo en la frase vale cualquier indicio; sin nada que comprobar, solo la primera candidata y de las que pasan el umbral
                bolsa = [h for h in hechos if h["apoyo"] == "firme"] or [h for h in hechos if h["clase"] == "F" and h["orden"] == 0 and h["apoyo"] == "neutro"]
                if os.environ.get("LCM_SENTIDO_SIN_APOYO"):
                    bolsa = [h for h in hechos if h["clase"] in ("S", "F")]
                bolsa.sort(key=lambda h: (h["cambios"][0][1] == "hacer", {"S": 0, "F": 1, "D": 2}[h["clase"]], -h["valor"]))   # «hacer» vale por casi todo: detrás de cualquier palabra más precisa
                distintas = []
                for h in bolsa:
                    if not any(sa(h["resp"].lower()) == sa(o["resp"].lower()) for o in distintas):
                        distintas.append(h)
                if len(distintas) > 1 and distintas[0]["cambios"][0][0] == distintas[1]["cambios"][0][0] \
                        and _S.evidencia(sa(distintas[0]["cambios"][0][1]), sa(distintas[1]["cambios"][0][1]))[1] in ("S", "F"):
                    distintas = distintas[:1]            # las dos candidatas dicen lo mismo entre sí («terminar» y «acabar»): no hay dos lecturas
                if len(distintas) == 1 or (len(distintas) > 1 and (distintas[0]["valor"] >= distintas[1]["valor"] + 0.1 or distintas[0]["clase"] != distintas[1]["clase"]
                                                                   or os.environ.get("LCM_SENTIDO_SIN_DOS"))):
                    el = distintas[0]
                elif len(distintas) > 1:
                    a_, b_ = distintas[0], distintas[1]
                    if a_["cambios"][0][0] == b_["cambios"][0][0]:
                        res = {"respuesta": _S.dos_lecturas(a_["cambios"][0][0], (a_["cambios"][0][1], a_["resp"]), (b_["cambios"][0][1], b_["resp"])),
                               "estado": "ok", "consultar": False, "tipo": "resp", "por_sentido": a_["cambios"] + b_["cambios"], "dos_lecturas": True}
                        self.ult_just = {"dicho": [a_["resp"], b_["resp"]]}
                    else:
                        el = a_
            if el is not None:
                res = {"respuesta": _S.aviso(el["cambios"], el["resp"]), "estado": "ok", "consultar": False, "tipo": "resp", "por_sentido": el["cambios"],
                       "clase_sentido": el["clase"] if not any(sa(c_[0]) in _S.vocabulario(self)[0] or sa(c_[0]) in _S.vocabulario(self)[1] for c_ in el["cambios"]) else "dentro"}
                self.ult_just = el["just"] or {"dicho": [el["resp"]]}
            if res is not None:
                self.pend = None
            self._duda224 = None
            vb_, nm_ = _S.vocabulario(self)               # solo se pregunta por palabras que NO están en lo aprendido
            dudas = [h for h in hechos if len(h["cambios"]) == 1 and h["valor"] >= _S.UMBRAL_DUDA and h["apoyo"] != "falla"
                     and sa(h["cambios"][0][0]) not in vb_ and sa(h["cambios"][0][0]) not in nm_]
            if res is None and dudas:
                h = sorted(dudas, key=lambda h: -h["valor"])[0]   # hay candidata con respuesta, pero el indicio no basta: se preguntará
                self._duda224 = (self.turno, texto, h["cambios"], h["resp"])
        except Exception:                                # noqa
            res = None
        finally:
            self._reform = ant_reform
            if res is None:
                self.ult_just, self.pend = ant_just, ant_pend
        self._sent224 = ((self.turno, texto), res)
        return res

    def _solo_fabrica(self):
        """¿La última respuesta salió solo del conocimiento de fábrica (lo que «suele» pasar), sin nada dicho o leído en la conversación?"""
        j = self.ult_just or {}
        d = j.get("dicho") or []
        return bool(j.get("fabrica")) or (bool(d) and all(x == "fábrica" for x in d))

    def _procesar_218(self, texto: str) -> Optional[dict]:
        """2.16: la charla, más leer un texto inserto, seguir el hilo de quién va con quién y, si hace falta, citar lo leído."""
        from . import lectura, crear, relaciones as _rel
        _rel.ENSENADO.clear(); _rel.ENSENADO.update(self.usuario.get("rel") or {})
        if texto and "?" in texto and len(texto) < 220 and (self.usuario.get("leido") or []) and not os.environ.get("LCM_CADENA_TARDE"):
            r_cd = self._encadenar(texto)                # 2.23: lo primero, saber de qué habla una descripción («la sala más silenciosa»)
            if r_cd is not None:
                return r_cd
        if texto and not getattr(self, "_leyendo", False) and len(texto) < 220:
            # 2.19: «volviendo a las setas, ¿…?», «cambiando de tema, …»: el giro de la charla no es parte de lo que se dice
            m_g = re.match(r"^\s*(?:(?:y\s+)?volviendo a[^,:?]{2,40}|cambiando de tema|por cierto|otra cosa|a prop[oó]sito|una (?:pregunta|duda|cosa)(?: m[aá]s)?|oye|y otra cosa|hablando de[^,:?]{2,40})\s*[,:]\s*(\S.+)$", texto, re.I)
            if m_g:
                texto = m_g.group(1)[:1].upper() + m_g.group(1)[1:] if not m_g.group(1).startswith(("¿", "¡")) else m_g.group(1)
            from . import iniciativa as _ini
            try:
                texto = _ini.correferencia(self, texto)  # 2.17: «las niñas» son mis hijas
            except Exception:                            # noqa
                pass
            if "?" in texto:
                try:
                    from . import exposicion as _X
                    texto = _X.sustituye(self, texto)    # 2.18: «el volcán más alto de España» -> el Teide
                    rex = _X.responder(self, texto)      # definiciones, tipos, superlativos, reglas… aprendidos de lo leído
                except Exception:                        # noqa
                    rex = None
                if rex is not None:
                    self._ult_resp = rex.get("respuesta")
                    return rex
            try:
                rin = _ini.antes(self, texto)            # 2.17: ¿contesta a lo que pregunté?, ¿pide algo sobre la propia charla?
            except Exception:                            # noqa
                rin = None
            if rin is not None:
                if isinstance(rin, dict) and rin.get("respuesta"):
                    self._ult_resp = rin["respuesta"]
                return rin
        if texto and not getattr(self, "_leyendo", False) and len(texto) < 220:
            try:
                from . import exposicion as _X
                rpx = _X.corrige_contra(self, texto) or _X.pide(self, texto)   # 2.18: «dime un N», «descríbeme X» con lo aprendido
            except Exception:                            # noqa
                rpx = None
            if rpx is not None:
                self._ult_resp = rpx.get("respuesta")
                return rpx
            try:
                rcr = crear.responder(self, texto)       # crear a petición (poema, cuento, rima, adivinanza…): no es un hecho que guardar
            except Exception:                            # noqa
                rcr = None
            if rcr:
                self.turno += 1
                if not self.ult_just or not self.ult_just.get("fabrica"):
                    self.ult_just = {"pasos": ["lo he compuesto ahora con lo que sé de los conceptos y de lo que me has contado; no lo tenía guardado"], "fabrica": True}
                return self._ok(rcr, tipo="crea")
        if texto and not getattr(self, "_leyendo", False) and lectura.es_texto(texto):
            return lectura.leer(self, texto)

        if texto and not getattr(self, "_leyendo", False) and "?" not in texto:
            try:
                from . import exposicion as _X
                rps = _X.peticion_sin_atender(texto, self)     # 2.18: una petición nunca se apunta como un hecho
                if rps is None and len(lectura.frases(texto)) == 1:
                    foto_c, n_c = _X.foto_leido(self), len(self.F)
                    rps = _X.charla(self, texto)         # una frase que explica algo general se lee como al leer un texto
                    if rps is not None:                  # 2.19: también aquí se contrasta con lo leído
                        rps = _X.contraste(self, texto, rps, foto_c, n_c)
                        rps = _X.contraste_texto(self, texto, rps)
            except Exception:                            # noqa
                rps = None
            if rps is not None:
                self._ult_resp = rps.get("respuesta")
                return rps
        largo = bool(texto) and "?" not in texto and not getattr(self, "_leyendo", False) and len(lectura.frases(texto)) >= 3
        n_antes = len(self.F)
        if texto and "?" in texto and re.search(r"\best[aá]n?\s+(?:en|dentro)\b", texto):
            rc0 = self._contenido_en(texto)              # antes de decir que no: ¿está dentro de algo que está ahí?
            if rc0 is not None:
                return rc0
        if texto and not getattr(self, "_leyendo", False) and getattr(self, "_ult_resp", None) and re.match(
                r"^\W*(?:no (?:te |lo )?(?:he entendido|entiendo|he pillado)(?: (?:lo [uú]ltimo|eso|bien|nada))?|(?:me lo )?(?:puedes|podr[ií]as) repetir(?:lo|melo)?|rep[ií]te(?:lo|melo)?(?: por favor)?|c[oó]mo dices|qu[eé] has dicho|c[oó]mo)\W*$", texto.strip(), re.I):
            self.turno += 1
            return self._ok("Te decía esto: " + self._ult_resp)
        if texto and "?" not in texto and getattr(self, "_ult_suelto", None) and self.turno - self._ult_suelto[1] <= 2 and not getattr(self, "_leyendo", False):
            from . import iniciativa as _ini
            try:
                rcs = _ini.causa_suelta(self, texto, self._ult_suelto[0])     # 2.17: la explicación de algo que no dejó un hecho
            except Exception:                            # noqa
                rcs = None
            if rcs is not None:
                self._ult_suelto = None
                return rcs
        if texto and "?" not in texto and getattr(self, "_ult_afirm", None) and self.turno - self._ult_afirm[1] <= 2:
            m_eq = re.match(r"^\s*(?:es que|es porque|porque|pues porque|y es que)\s+(.+)$", texto.strip(), re.I)
            if m_eq and self._ult_afirm[3] > self._ult_afirm[2]:   # «Estoy triste.» «Es que he discutido con mi hermana.»: la segunda explica la primera
                from .nucleo import cambia_persona, causa_tu as _causa_tu
                a_, b_ = self._ult_afirm[2], self._ult_afirm[3]
                causa = m_eq.group(1).strip().rstrip(".!")
                try:
                    self._procesar_charla(causa[:1].upper() + causa[1:] + ".")
                except Exception:                        # noqa
                    pass
                for f in self.F[a_:b_]:
                    if not f.get("causa"):
                        f["causa"] = causa
                self.ult_just = {"dicho": [self._ult_afirm[0], texto.strip()]}
                base = self.frase(self.F[a_])
                return self._ok(f"Entendido: {base[:1].lower() + base[1:] if not base.split()[0][:1].isupper() or base.split()[0].lower() in ('estás', 'tienes', 'te', 'tu') else base} porque {_causa_tu(causa)}.", tipo="ack")
        n_af = len(self.F)
        try:
            from . import exposicion as _X
            foto_l = _X.foto_leido(self) if (texto and "?" not in texto and not getattr(self, "_leyendo", False)) else []
        except Exception:                                # noqa
            foto_l = []
        r = self._procesar_charla(texto)
        if foto_l:
            try:
                r = _X.contraste(self, texto, r, foto_l, n_af)   # 2.18: lo que me dicen frente a lo que leí
            except Exception:                            # noqa
                pass
        if texto and "?" not in texto and not getattr(self, "_leyendo", False):
            try:
                r = _X.contraste_texto(self, texto, r)   # 2.19: …y frente a las frases leídas que no dejaron un hecho
                _X.apunta_no_entendida(self, texto, r)
            except Exception:                            # noqa
                pass
        if texto and "?" in texto and not getattr(self, "_leyendo", False) and (r is None or (isinstance(r, dict) and r.get("estado") == "abst")) and not getattr(self, "_reform", False):
            self._reform = True
            try:
                rpc = _X.por_clase(self, texto)          # 2.18: lo que vale para la clase vale para quien es de esa clase
            except Exception:                            # noqa
                rpc = None
            finally:
                self._reform = False
            if rpc is not None:
                r = rpc
        if texto and "?" not in texto and not getattr(self, "_leyendo", False) and isinstance(r, dict) and r.get("estado") == "ok" and len(self.F) == n_af and 2 <= len(texto.split()) <= 12:
            self._ult_suelto = (texto.strip(), self.turno)
        elif texto and "?" not in texto:
            self._ult_suelto = None
        if texto and "?" in texto and not getattr(self, "_leyendo", False) and (r is None or (isinstance(r, dict) and r.get("estado") in ("abst", "aclara"))) and not getattr(self, "_reform", False):
            from . import iniciativa as _ini
            rps = _ini.porque_suelto(self, texto)
            if rps is not None:
                return rps
            alt = _ini.accion_evento(self, texto)        # 2.17: «¿con quién ceno?» cuando se dijo «tengo una cena con…»
            if not alt:
                try:
                    from . import exposicion as _X
                    alt = _X.inversa(texto)              # 2.18: «¿qué pieza se mueve en diagonal?» -> ¿quién…?
                except Exception:                        # noqa
                    alt = None
            if not alt:
                try:                                     # 2.19: la misma pregunta con otras palabras («¿de qué se alimentan?» = «¿qué comen?»)
                    from . import sinonimia as _S
                    self._reform = True
                    for cand in _S.alternativas(texto):
                        r_c = self._procesar_charla(cand)
                        if isinstance(r_c, dict) and r_c.get("estado") == "ok":
                            r = r_c
                            break
                    else:                                # 2.20: y si no, por el sentido: la palabra aprendida más cercana (vectores del léxico)
                        r_s = self._sentido(texto)       # 2.24: varias candidatas, y decide el texto
                        c_t = None
                        if not (r_s is not None and r_s.get("clase_sentido") == "S") and (self.usuario.get("leido") or []) and not getattr(self, "_leyendo", False):
                            c_t = lectura.cita(self, texto)   # salvo sinónimo seguro, antes lo que el texto dice tal cual o con una equivalencia de la lengua
                            if not c_t and not os.environ.get("LCM_SIN_TABLA_CITA"):
                                for cand in _S.alternativas(texto):
                                    c_t = lectura.cita(self, cand)
                                    if c_t and _S.ancla(texto, cand, c_t) and _S.apoyo(self, cand, [], c_t) != "falla":
                                        break
                                    c_t = None
                        if not c_t and r_s is not None:
                            r = r_s
                except Exception:                        # noqa
                    pass
                finally:
                    self._reform = False
            if alt:
                self._reform = True
                try:
                    r_alt = self._procesar_charla(alt)
                finally:
                    self._reform = False
                if isinstance(r_alt, dict) and r_alt.get("estado") == "ok":
                    r = r_alt
        if texto and "?" in texto and not getattr(self, "_leyendo", False):
            try:
                from . import iniciativa as _ini
                r = _ini.nombra_grupo(self, texto, r)    # 2.17: «con dos amigas» + sus nombres, si se dijeron
            except Exception:                            # noqa
                pass
        if texto and not getattr(self, "_leyendo", False):
            try:
                from . import iniciativa as _ini
                r = _ini.despues(self, texto, r, n_af)   # 2.17: recibe la noticia con su tono y, si falta algo, hace UNA pregunta
            except Exception:                            # noqa
                pass
        if texto and "?" not in texto and isinstance(r, dict) and r.get("estado") == "ok" and len(texto.split()) <= 12 and not getattr(self, "_leyendo", False) and len(self.F) > n_af:
            self._ult_afirm = (texto.strip(), self.turno, n_af, len(self.F))
        if isinstance(r, dict) and r.get("respuesta") and not getattr(self, "_leyendo", False):
            self._ult_resp = r["respuesta"]
        if texto and "?" in texto and (r is None or (isinstance(r, dict) and r.get("estado") == "abst")) and re.match(r"^\W*(?:y\s+)?qui[eé]n(?:es)?\s", texto, re.I):
            rq_ = self._quien_de_fabrica(texto)          # nadie lo ha contado, pero por su oficio hay quien lo hace («¿quién apaga los fuegos?»)
            if rq_ is not None:
                return rq_
        if texto and "?" in texto and isinstance(r, dict) and r.get("estado") == "abst" and re.search(r"\best[aá]n?\s+(?:en|dentro)\b", texto):
            rc_ = self._contenido_en(texto)              # lo que está dentro de algo está también donde esté ese algo
            if rc_ is not None:
                return rc_
        if largo:
            if (r is None or (isinstance(r, dict) and r.get("estado") != "ok")) and len(self.F) == n_antes:
                return lectura.leer(self, texto)         # un texto largo sin presentar que la charla normal no ha sabido leer entero
            leidos = self.usuario.setdefault("leido", [])
            leidos.append({"turno": self.turno, "frases": lectura.frases(texto)})
            del leidos[:-3]
        if texto and "?" in texto and not getattr(self, "_leyendo", False) and not getattr(self, "_encadena", False) \
                and (r is None or (isinstance(r, dict) and r.get("estado") in ("abst", "aclara"))):
            r_cd = self._encadenar(texto)
            if r_cd is not None:
                return r_cd
        # 2.23: si la respuesta sale SOLO de la fábrica y lo leído o explicado dice algo sobre eso, manda lo leído
        de_fabrica = isinstance(r, dict) and r.get("estado") == "ok" and r.get("tipo") not in ("ack", "crea") and "?" in (texto or "") \
            and (re.search(r"\bsuelen? \w+.*Lo sé porque\b", r.get("respuesta") or "") is not None or (self._solo_fabrica() and not os.environ.get("LCM_FABRICA_MANDA")
                                                                                                           and re.match(r"^\W*(?:y\s+)?(?:(?:a|de|con|en|por|para|sobre)\s+)?(?:qu[eé]|qui[eé]n|c[oó]mo|cu[aá]ndo|d[oó]nde|cu[aá]l|cu[aá]nt)", texto.strip(), re.I) is not None
                                                                                                           and re.match(r"^\W*(?:y\s+)?qu[eé] (?:es|son|significa)\b", texto.strip(), re.I) is None))
        if texto and "?" in texto and not getattr(self, "_leyendo", False) and (r is None or de_fabrica or (isinstance(r, dict) and r.get("estado") in ("abst", "aclara"))) \
                and (self.usuario.get("leido") or []):
            c = lectura.cita(self, texto)                # el núcleo no lo sabe (o solo sabe lo que «suele» pasar): ¿lo dice lo leído o explicado?
            if not c and not os.environ.get("LCM_SIN_TABLA_CITA"):
                try:                                     # 2.24: ¿lo dice con una equivalencia de la lengua? («¿de qué se alimentan?» con «…comen pienso»; «¿qué da vueltas?» con «…gira»)
                    from . import sinonimia as _S
                    for cand in _S.alternativas(texto):
                        c = lectura.cita(self, cand)
                        if c and _S.ancla(texto, cand, c) and _S.apoyo(self, cand, [], c) != "falla":
                            break
                        c = None
                except Exception:                        # noqa
                    c = None
            if not c:
                try:                                     # 2.20: ¿lo dice con otras palabras?
                    from . import sinonimia as _S
                    r_s = self._sentido(texto)
                    c = r_s["respuesta"] if r_s is not None else None
                except Exception:                        # noqa
                    c = None
            if c:
                self.ult_just = {"dicho": [c]}
                self.pend = None
                return {"respuesta": c, "estado": "ok", "consultar": False, "tipo": "resp"}
        if texto and "?" in texto and not getattr(self, "_leyendo", False) and not getattr(self, "_encadena", False) and not getattr(self, "_reform", False) \
                and (r is None or (isinstance(r, dict) and r.get("estado") in ("abst", "aclara"))):
            try:                                         # 2.21: hay una palabra leída que se parece, pero no lo bastante: se pregunta en vez de adivinar
                from . import sinonimia as _S
                self._reform = True
                d224 = getattr(self, "_duda224", None)
                if d224 and d224[0] == self.turno and d224[1] == texto and [d224[2][0][0], d224[2][0][1]] not in (self.usuario.get("no_sinonimos") or []):
                    self._duda_sentido = {"turno": self.turno, "pares": [(d224[2][0][0], d224[2][0][1])], "respuesta": d224[3]}
                    self.pend = None
                    return {"respuesta": f"No lo sé seguro. ¿«{d224[2][0][0]}» quiere decir aquí lo mismo que «{d224[2][0][1]}»? Si es así, dímelo y te contesto.",
                            "estado": "abst", "consultar": False, "tipo": "abst"}
                for cand, cambios in _S.por_sentido(self, texto, duda=True):
                    if len(cambios) != 1:
                        continue
                    if [cambios[0][0], cambios[0][1]] in (self.usuario.get("no_sinonimos") or []):
                        continue                         # ya dijo que no
                    r_c = self._procesar_charla(cand)    # solo si el núcleo la contesta: ahí tienen que casar también quién y qué
                    if not (isinstance(r_c, dict) and r_c.get("estado") == "ok" and r_c.get("tipo") != "ack"):
                        r_c = None
                    if r_c and r_c.get("respuesta") and _S.casa_tiempo(cambios, r_c["respuesta"]):
                        self._duda_sentido = {"turno": self.turno, "pares": [(cambios[0][0], cambios[0][1])], "respuesta": r_c["respuesta"]}
                        self.pend = None
                        return {"respuesta": f"No lo sé seguro. ¿«{cambios[0][0]}» quiere decir aquí lo mismo que «{cambios[0][1]}»? Si es así, dímelo y te contesto.",
                                "estado": "abst", "consultar": False, "tipo": "abst"}
            except Exception:                            # noqa
                pass
            finally:
                self._reform = False
            try:                                         # y si no hay candidata, al menos decir QUÉ palabra no aparece en lo aprendido
                from . import sinonimia as _S
                w_ = _S.desconocida(self, texto)
                if w_ and isinstance(r, dict) and r.get("respuesta") and "«" + w_ + "»" not in r["respuesta"]:
                    if not self.usuario.get("pista_sinonimo"):
                        self.usuario["pista_sinonimo"] = True
                        nota_ = f" En lo que he aprendido no aparece «{w_}»; si es otra forma de decir algo, dímelo («{w_} es lo mismo que…»)."
                    else:
                        nota_ = f" («{w_}» no aparece en lo que he aprendido.)"
                    return dict(r, respuesta=r["respuesta"].rstrip() + nota_)
            except Exception:                            # noqa
                pass
        if r is None and texto and "?" in texto and not getattr(self, "_leyendo", False):
            try:
                from . import exposicion as _X
                rs = _X.sin_respuesta(self, texto)       # 2.18: sobre lo leído, mejor «no lo sé» que una respuesta del diccionario
            except Exception:                            # noqa
                rs = None
            if rs is not None:
                return rs
        if r is None and texto and "?" not in texto and not getattr(self, "_leyendo", False):
            try:
                from . import exposicion as _X
                rn = _X.nota(self, texto)                # 2.18: una explicación que no se entiende se guarda tal cual y se dice
            except Exception:                            # noqa
                rn = None
            if rn is not None:
                return rn
        return r

    _IGUAL_AB = re.compile(r"^\s*([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)\s+y\s+([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)\s+(tienen la misma edad|tienen los mismos años|pesan lo mismo|miden lo mismo|cuestan lo mismo|"
                           r"valen lo mismo|ganan lo mismo|cobran lo mismo|son igual de (?:altos|altas|viejos|viejas|mayores)|tienen el mismo (?:n[úu]mero de )?[a-záéíóúñ]+|tienen la misma [a-záéíóúñ]+)\s*[.!]?\s*$", re.I)
    _IGUAL_QUE = re.compile(r"^\s*([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)\s+(tiene la misma edad|tiene los mismos años|pesa lo mismo|mide lo mismo|cuesta lo mismo|vale lo mismo|gana lo mismo|cobra lo mismo|"
                            r"es igual de (?:alto|alta|viejo|vieja|mayor)|tiene el mismo (?:n[úu]mero de )?[a-záéíóúñ]+|tiene la misma [a-záéíóúñ]+)\s+que\s+([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)\s*[.!]?\s*$", re.I)

    @staticmethod
    def _clave_igual(pred):
        p = sa(pred.lower())
        for k, v in (("edad", r"\banos?\b|\bedad\b"), ("anos", r"\banos?\b|\bedad\b"), ("viej", r"\banos?\b"), ("mayor", r"\banos?\b"), ("pes", r"\bpes[ao]\w*"), ("mid", r"\bmid\w+"), ("alt", r"\bmid\w+"),
                     ("cuest", r"\bcuest\w+|\bval\w+"), ("val", r"\bcuest\w+|\bval\w+"), ("gan", r"\bgan\w+|\bcobr\w+"), ("cobr", r"\bgan\w+|\bcobr\w+")):
            if k in p:
                return v
        m = re.search(r"(?:mismo|misma) (?:numero de )?([a-zñ]+)$", p)
        return (r"\b" + re.escape(m.group(1)[:5]) + r"\w*") if m else None

    def _igualdad(self, texto):
        """2.16: «Eva y Sara tienen la misma edad»: lo que se sepa de una en esa medida vale para la otra (y al revés)."""
        m = self._IGUAL_AB.match(texto or "")
        a, b, pred = (m.group(1), m.group(2), m.group(3)) if m else (None, None, None)
        if not m:
            m = self._IGUAL_QUE.match(texto or "")
            if not m:
                return None
            a, pred, b = m.group(1), m.group(2), m.group(3)
        clave = self._clave_igual(pred)
        if not clave:
            return None
        self.usuario.setdefault("iguales", []).append([a, b, clave, pred])
        self.turno += 1
        for x, y in ((a, b), (b, a)):                    # si ya se sabía de una, se deduce para la otra
            for f in list(self.F):
                src = f.get("src") or ""
                if re.search(rf"\b{re.escape(x)}\b", src) and re.search(clave, sa(src.lower()).replace('ñ', 'n')) and not f.get("deducido") and "?" not in src:
                    self._copia_igual(src, x, y)
        self.ult_just = {"dicho": [texto.strip()]}
        return self._ok(f"Entendido: {a} y {b} {pred.replace('tiene ', 'tienen ').replace('pesa ', 'pesan ').replace('mide ', 'miden ').replace('cuesta ', 'cuestan ') if not m.re is self._IGUAL_AB else pred}.", tipo="ack")

    def _copia_igual(self, src, x, y):
        n0 = len(self.F)
        foto_t = self.turno
        try:
            self._procesar_216(re.sub(rf"\b{re.escape(x)}\b", y, src))
        except Exception:                                # noqa
            pass
        self.turno = foto_t
        for f in self.F[n0:]:
            f["deducido"] = True
            f["src"] = f"{src.strip().rstrip('.')} (y {x} y {y} van iguales en eso)"

    # ---- 2.16: cuentas contadas («tenía 20 euros, gasté 5 y luego me dieron 3») -> un saldo que calculan las aplicaciones
    _MONEDAS = ("euro", "euros", "dolar", "dolares", "peso", "pesos", "centimo", "centimos", "libra", "libras")

    def _saldo_contado(self, texto):
        from . import calculo as CA
        from src.apps.registro import ErrorApp
        def _a_pret(m_):                                 # 2.17: «me he gastado 45» = «me gasté 45»
            an_ = [a_ for a_ in (M.analizar(m_.group(3)) or []) if a_[1] == "part"]
            per_ = {"he": "1s", "hemos": "1p", "ha": "3s", "han": "3p", "has": "2s"}[m_.group(2).lower()]
            return (m_.group(1) or "") + (M.conjugar(an_[0][0], "pret", per_) or m_.group(0)) if an_ else m_.group(0)
        texto = re.sub(r"\b((?:me|nos|se|te)\s+)?(he|hemos|ha|han|has)\s+([a-záéíóúñ]+(?:ado|ido|to|cho|so))\b", _a_pret, texto)
        t = sa(texto.lower())
        if "?" in texto or len(re.findall(r"\d+|\b(?:dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|veinte|cien)\b", t)) < 2:
            return None
        if not re.match(r"^\s*(?:yo\s+)?(?:tenia|tengo|habia|hay|tenemos|teniamos|compre|compramos|cogi|recogi|gane|recibi|traje|me dieron|me regalaron)\b", t):
            return None
        L = CA.lexico()
        if not any(f" {x} " in f" {re.sub('[,.;]', ' ', t)} " for x in L["mas"] + L["menos"] if len(x) >= 4 and x not in ("menos",)):
            return None                                  # sin algo que entre o salga no hay cuenta: «tengo 2 perros y 3 gatos» son dos datos
        try:
            rp = CA.problema(texto.strip().rstrip(".") + ", ¿cuántos hay en total ahora?")
            if not rp:
                return None
            nodo, unidad = rp
            if nodo[0] != "app" or nodo[1] not in ("suma", "resta"):
                return None
            traza = []
            v = CA.ejecuta(nodo, traza)
        except (ErrorApp, Exception):                    # noqa
            return None
        m_u = re.search(r"\d+\s+([a-zñ]+)", t)
        unidad = (m_u.group(1) if m_u else unidad) or ""
        self.usuario.setdefault("saldos", {})[sa(M.singular(unidad))] = {"valor": str(v), "cuenta": CA.escribe(nodo), "unidad": unidad, "dicho": texto.strip()}
        self.turno += 1
        self.ult_just = {"app": True, "texto": CA.justificacion(traza)}
        return self._ok(f"Entendido. Echo la cuenta: {CA.escribe(nodo)} = {CA.F(v)} {unidad}.", tipo="ack")

    def _saldo_pregunta(self, texto):
        sal = self.usuario.get("saldos") or {}
        if not sal or "?" not in texto:
            return None
        n = sa(texto.lower()).strip(" ¿?.!")
        m = re.match(r"^(?:y )?(?:entonces )?cuant[oa]s? ((?!me |nos )[a-zñ]+ )?(?:tengo|me quedan?|quedan?|hay|tenemos|nos quedan?)(?: ahora| al final| en total| todavia| aun)?$", n)
        if not m:
            return None
        u = sa(M.singular((m.group(1) or "").strip()))
        k = u if u in sal else next((x for x in sal if (u in ("dinero", "") and (x in self._MONEDAS or len(sal) == 1))), None)
        if k is None:
            return None
        d = sal[k]
        from fractions import Fraction
        from . import calculo as CA
        self.turno += 1
        self.ult_just = {"dicho": [d["dicho"]]}
        return self._ok(f"{CA.F(Fraction(d['valor']))} {d['unidad']}: {d['cuenta']} = {CA.F(Fraction(d['valor']))}.")

    def _quien_de_fabrica(self, texto):
        n = sa(texto.lower()).strip(" ¿?.!")
        m = re.match(r"^(?:y )?quien(?:es)? ([a-zñ]+)(?: (.+))?$", n)
        if not m:
            return None
        lem = next((a[0] for a in M.analizar(m.group(1)) if a[1] == "pres"), None)
        if not lem or lem in ("ser", "estar", "tener", "saber", "poder", "querer"):
            return None
        resto = {w[:5] for w in re.findall(r"[a-zñ]+", m.group(2) or "") if w not in ("el", "la", "los", "las", "a", "de", "un", "una", "al", "del")}
        c_obj = next((conceptos._kb_clase(w) for w in reversed(re.findall(r"[a-zñ]+", m.group(2) or "")) if conceptos._kb_clase(w)), None)
        if c_obj and lem in ("conducir", "pilotar", "manejar", "usar", "utilizar", "tocar", "llevar"):
            from . import relaciones as _R               # quién lo usa típicamente («¿quién conduce un taxi?»)
            _, us = _R.valores(c_obj, "usuario")
            if us:
                self.turno += 1
                self.ult_just = {"pasos": [f"{conceptos.los(c_obj)} los usan {_R._los(sa(us[0]))}"], "fabrica": True}
                return self._ok(conceptos._cap(self._lista([_R._los(sa(u)) for u in us[:2]])) + ".")
        hall = []
        for (x, neg, v, r) in conceptos.kb()["props"]:
            if neg or sa(v) != sa(lem) or "persona" not in conceptos.ancestros(x):
                continue
            rr = {w[:5] for w in re.findall(r"[a-zñ]+", sa(r)) if w not in ("el", "la", "los", "las", "a", "de", "un", "una", "al", "del")}
            if not resto or (resto & rr):
                hall.append((len(resto & rr), x, v, r))
        if not hall:
            return None
        hall.sort(key=lambda h: -h[0])
        mejores = list({h[1]: h for h in reversed([h for h in hall if h[0] == hall[0][0]])}.values())[:3]
        self.turno += 1
        self.ult_just = {"pasos": [conceptos._frase_prop(x, False, v, r) for _, x, v, r in mejores], "fabrica": True}
        return self._ok(conceptos._cap(self._lista([conceptos._frase_prop(x, False, v, r) for _, x, v, r in mejores[:2]])) + ".")

    def _cadena_lugar(self, e, visto=None):
        """2.16: dónde está algo, y dónde está lo que lo contiene («las gafas en el estuche, el estuche en la mochila»)."""
        visto = visto or set()
        if e in visto:
            return []
        visto.add(e)
        for f in reversed(self.F):
            if f["v"] == "estar" and f.get("s") and self.can(f["s"]) == e and not f.get("neg") and f.get("vig", True):
                for c in f.get("comps") or []:
                    if c[0] in ("en", "dentro_de", "dentro de", "dentro") and c[1]:
                        return [(f, self.can(c[1]))] + self._cadena_lugar(self.can(c[1]), visto)
        return []

    def _contenido_en(self, texto):
        m = re.match(r"^\W*(?:y\s+)?(?:(?:el|la|los|las|mi|mis|tu|tus)\s+)?(.+?)\s+est[aá]n?\s+(?:en|dentro de|dentro del)\s+(?:(?:el|la|los|las|mi|tu|su|l)\s+)?(.+?)\W*$", texto.strip(), re.I)
        if not m:
            return None
        rx, ry = sa(M.singular(m.group(1).split()[-1].lower())), sa(M.singular(m.group(2).split()[-1].lower()))
        for e in list(self.E):
            if e in ("U", "L") or rx not in sa(M.singular(self.disp(e).split()[-1].lower())):
                continue
            cad = self._cadena_lugar(e)
            for k, (f, cont) in enumerate(cad):
                if ry in sa(self.disp(cont).lower()) and k >= 1:
                    self.ult_just = {"pasos": [self.frase(x) for x, _ in cad[:k + 1]]}
                    self.turno += 1
                    return self._ok("Sí: " + " y ".join(self.frase(x) for x, _ in cad[:k + 1]) + ".")
        return None

    def _procesar_charla(self, texto: str) -> Optional[dict]:
        n00 = len(self.F)
        if texto and re.search(r"\d|\b(?:dos|tres|cuatro|cinco|diez|veinte)\b", texto) and not getattr(self, "_leyendo", False):
            rs0 = self._saldo_contado(texto) if "?" not in texto else self._saldo_pregunta(texto)
            if rs0 is not None:
                return rs0
        elif texto and "?" in texto and self.usuario.get("saldos"):
            rs0 = self._saldo_pregunta(texto)
            if rs0 is not None:
                return rs0
        if texto and "?" not in texto and re.search(r"\bmism[oa]s?\b|\bigual de\b", texto):
            rig = self._igualdad(texto)
            if rig is not None:
                return rig
        from . import secuencias
        if texto and "?" not in texto and not getattr(self, "_leyendo", False) and secuencias.es_secuencia(texto):
            rs = secuencias.registrar(self, texto)       # 2.16: «primero…, después… y luego…»: hechos con su orden
            if rs is not None:
                return rs
        if texto and "?" in texto and (self.usuario.get("secuencias") or []):
            rq = secuencias.responder(self, texto, sa(texto.lower()))
            if rq is not None:
                self.turno += 1
                return self._ok(rq)
        r = self._procesar_216(texto)
        if texto and "?" not in texto and self.usuario.get("iguales") and len(self.F) > n00 and not getattr(self, "_copiando", False):
            self._copiando = True
            try:
                foto_j = self.ult_just
                for a_, b_, clave, _p in self.usuario["iguales"]:
                    for x, y in ((a_, b_), (b_, a_)):
                        if re.search(rf"\b{re.escape(x)}\b", texto) and re.search(clave, sa(texto.lower()).replace('ñ', 'n')) and not re.search(rf"\b{re.escape(y)}\b", texto):
                            self._copia_igual(texto, x, y)
                self.ult_just = foto_j
            finally:
                self._copiando = False
        for f in self.F[n00:]:                           # 2.16: quien hace algo CON alguien forma un grupo con él («compraron», «volvieron»)
            cs = [c for c in (f.get("comps") or []) if c and c[0] == "con" and c[1] and (str(c[1]).startswith("N:") or self.es_persona(c[1]) or self._persona_por_rol(c[1]))]
            if cs and f.get("s") and f["s"] != "L":
                self.ult_grupo = list(dict.fromkeys([self.can(f["s"])] + [self.can(c[1]) for c in cs]))
        return r

    def _procesar_216(self, texto: str) -> Optional[dict]:
        """2.11: antes de todo, las disyunciones («o», «o… o») y, después de cada afirmación, si resuelve alguna."""
        m_tu = re.match(r"^¿?\s*(?:(?:t[úu] y yo|yo y t[úu])\s+)?somos\s+(amig[oa]s|compañer[oa]s|colegas)(?:\s+(?:t[úu] y yo|yo y t[úu]))?\s*([?.!]?)\s*$", (texto or "").strip(), re.I)
        if m_tu and (re.search(r"t[úu] y yo|yo y t[úu]", texto, re.I) or "?" in texto):
            self.turno += 1                              # 2.12: «tú y yo somos amigos»: la relación es con el propio LCM
            rel = m_tu.group(1).lower()
            if "?" in texto:
                previa = self.usuario.get("con_lcm")
                return self._ok(f"Sí: me dijiste que tú y yo somos {previa}." if previa else "Me gusta pensar que sí, aunque no me lo habías dicho.")
            self.usuario["con_lcm"] = rel
            return self._ok(f"Entendido: tú y yo somos {rel}. Me alegra.", tipo="ack")
        self._traza_app = []
        ra = self._aplicaciones(texto) if texto else None   # 2.13: cálculo, calendario, comparación supuesta y dibujo -> aplicaciones
        if ra is not None:
            return ra
        rc = self._condicional(texto) if texto else None    # 2.11: «si P, Q» (regla) y «si P, ¿Q?» (suposición)
        if rc is not None:
            return rc
        if texto and "?" in texto and re.search(r"\s[ou]\s", texto):
            rp = self._pregunta_alternativa(texto)       # «¿Bea vive en Jaca o en Sabiñánigo?»
            if rp is not None:
                return rp
        if texto and "?" not in texto and re.search(r"(?:^|\s)(?:[OoUu]|[Bb]ien)\s", texto):
            from . import conectores
            if conectores.expande_o(texto.strip(), coloquial._verbo_finito):
                return self._disyuncion(texto)           # si no se entiende como «o», nunca se trata como «y»
        n0 = len(self.F)
        r = self._procesar_base(texto)
        if isinstance(r, dict) and texto and "?" not in texto and getattr(self, "disy", None):
            extra = self._revisa_disy(n0)
            if extra:
                r = dict(r, respuesta=(r.get("respuesta") or "").rstrip() + " " + extra)
        if texto and "?" not in texto and getattr(self, "reglas", None):
            extra = self._aplica_reglas(texto)        # 2.11: modus ponens
            if extra:
                base_txt = (r.get("respuesta") or "").rstrip() if isinstance(r, dict) and r.get("estado") == "ok" else "Entendido."
                r = {"respuesta": base_txt + " " + extra, "estado": "ok", "consultar": False, "tipo": "ack"}
        return r

    def _sirve_para(self, p, n):
        """«¿Los cuchillos sirven para comer?», «¿Para qué sirve una mochila?»: propiedad «servir para…» de la clase o de sus capas de arriba."""
        t = n.strip(" ?¿")
        m1 = re.match(r"^(?:y\s+)?(?:(?:los|las|un|una|el|la|unos|unas)\s+)?([a-zñ ]+?)\s+sirven?\s+para\s+(.+)$", t)
        m2 = re.match(r"^(?:y\s+)?para que sirven?\s+(?:(?:los|las|un|una|el|la|unos|unas)\s+)?([a-zñ ]+)$", t)
        m = m1 or m2
        if not m:
            return None
        c = conceptos._clase_de_texto(m.group(1))
        if not c:
            return None
        k = conceptos.kb()
        usos = []
        for cl in [c] + conceptos.ancestros(c):
            us = [(neg, r) for (x, neg, v, r) in k["props"] if x == cl and v == "servir" and r.startswith("para ")]
            if us:
                usos.append((cl, us))
        if not usos:
            return None
        cl0, us0 = usos[0]
        self.turno += 1
        self.ult_just = {"pasos": [f"{conceptos.los(cl0)} sirven {r}" for neg, r in us0 if not neg][:2], "fabrica": True}
        if m2:
            return self._ok(f"{conceptos._cap(conceptos.un(c))} sirve " + self._lista([r for neg, r in us0 if not neg]).replace(" y para ", " y ") + ".")
        pedido = sa(m1.group(2))
        for cl, us in usos:
            for neg, r in us:
                if sa(r[5:]) == pedido or pedido.startswith(sa(r[5:])) or sa(r[5:]).startswith(pedido):
                    return self._ok(("No" if neg else "Sí") + f", {conceptos.los(c)} {'no ' if neg else ''}sirven {r}." + ("" if cl == c else f" Lo sé porque {conceptos.los(c)} son {conceptos.forma(cl, plural=True)}."))
        self.turno -= 1
        return None

    # ------------------------------------------------------------------ 2.13: aplicaciones deterministas
    _EXPLICA_CALC = re.compile(r"^(?:y\s+)?(?:c[óo]mo|de qu[ée] (?:forma|manera)|qu[ée] (?:cuenta|operaci[óo]n) has hecho|con qu[ée])\s*"
                               r"(?:lo\s+)?(?:has\s+(?:calculado|hecho|sacado|resuelto|dibujado)|calculas|lo calculas|haces la cuenta|has hecho la cuenta|lo has hecho|"
                               r"has llegado a (?:eso|ese resultado)|lo has dibujado|has dibujado eso)?\s*$", re.I)

    def _app_ok(self, txt, traza, imagen=None, valor=None, tipo="resp"):
        from . import calculo as CA
        self.turno += 1
        j = CA.justificacion(traza) if traza and traza[0].get("familia") != "dibujo" else (
            "No lo he dibujado de memoria: la imagen la genera la aplicación de dibujo a partir de la figura, el color y la cantidad que pides." if traza else None)
        self.ult_just = {"app": True, "texto": j} if j else None
        if valor is not None:
            self._calc_ult = valor
        r = {"respuesta": txt, "estado": "ok", "consultar": False, "tipo": tipo}
        if imagen is not None:
            r["imagen"] = imagen
        return r

    def _aplicaciones(self, texto):
        from src.apps.registro import ErrorApp, ejecuta as RA_ejecuta
        from . import calculo as CA, comparativos as CO, dibujar as DJ
        from .morfo import sa as _sa
        t = (texto or "").strip()
        n = _sa(t.lower()).strip(" ¿?¡!.")
        if self._EXPLICA_CALC.match(t.strip(" ¿?¡!.")) and re.search(r"calcul|cuenta|operaci|dibuj|sacado|resuelto|hecho", n):
            j = self.ult_just or {}
            if j.get("app") and j.get("texto"):
                self.turno += 1
                return self._ok(j["texto"])
            if j.get("app_traza"):
                self.turno += 1
                return self._ok(CA.justificacion(j["app_traza"]))
            return None
        if re.match(r"^(?:y\s+)?que (?:has|me has) (?:dibujado|pintado)(?: (?:antes|hasta ahora|hoy))?$", n):
            ds = self.usuario.get("dibujos") or []
            self.turno += 1
            if not ds:
                return self._ok("Todavía no he dibujado nada en esta conversación.")
            return self._ok("He dibujado " + (ds[0] if len(ds) == 1 else ", ".join(ds[:-1]) + " y " + ds[-1]) + ".")
        if re.match(r"^(?:que|cuales)\s+(?:operaciones|cuentas|calculos|aplicaciones)\s+(?:sabes hacer|sabes|puedes hacer|tienes|conoces|haces)$", n):
            from src.apps import registro as RA
            ar = [a.nombre_humano or a.nombre for a in RA.REGISTRO.values() if a.familia == "aritmetica"]
            self.turno += 1
            return self._ok("Las cuentas no las hago de memoria: las hacen mis aplicaciones. Tengo " + ", ".join(ar[:-1]) + " y " + ar[-1]
                            + "; además, el calendario semanal, el reloj y la aplicación de dibujo.")
        # cuentas con las edades que se han dicho en la charla: «¿cuánto suman nuestras edades?»
        if re.match(r"^(?:y\s+)?(?:cuanto suman (?:nuestras|las dos|ambas) edades|cuantos anos (?:tenemos|sumamos) entre (?:los dos|las dos|ambos|ambas)|cuantos anos sumamos)$", n.replace("ñ", "n")):
            otro = self.ref3(persona=True)
            if otro:
                a_, b_ = self._edad("U"), self._edad(otro)
                if a_ is None or b_ is None:
                    self.turno += 1
                    return self._abst("No lo sé: me falta la edad de alguno de los dos.")
                v, tr = RA_ejecuta("suma", a_[0], b_[0])
                return self._app_ok(f"{CA.F(v)} años: {a_[0]} + {b_[0]} = {CA.F(v)}.", [tr], valor=v)
        # dibujar / pintar / mostrar
        o = DJ.orden(t)
        if o is not None:
            if "desconocido" in o:
                self.turno += 1
                self.ult_just = None
                return self._ok(DJ.no_se(o))
            try:
                txt, img, traza = DJ.ejecuta(o)
            except ErrorApp as e:
                self.turno += 1
                return self._ok(str(e))
            self.usuario.setdefault("dibujos", []).append(DJ.describe(o["piezas"], o["colores"]))
            self.usuario["dibujos"] = self.usuario["dibujos"][-20:]
            try:
                self.guardar()
            except Exception:                         # noqa
                pass
            return self._app_ok(txt, traza, imagen=img, tipo="accion")
        if "?" not in t and not re.search(r"\d|^(?:calcula|suma|resta|multiplica|divide|cuanto|cual|dime|haz|y )|\b(?:mas|menos|por|entre)\b", CA._limpia(t)):
            return None
        try:
            r = CA.calendario(t)
            if r:
                return self._app_ok(r[0], r[1])
            r = CO.responde(t)
            if r:
                self.turno += 1
                self.ult_just = {"pasos": ["en una comparación, lo contrario de «más A» es «más B» (grande/pequeño, rápido/lento…)", "lo que supones sigue valiendo en orden: si A > B y B > C, A > C"], "fabrica": True}
                return self._ok(r)
            nodo = CA.calculo_seguido(t, getattr(self, "_calc_ult", None)) if re.match(r"^(?:¿\s*)?(?:y|ahora|y ahora)\b|^(?:¿\s*)?(?:sumale|restale|quitale|multiplicalo|dividelo|anadele)\b", n) else None
            if nodo is None:
                nodo = CA.calculo_directo(t, getattr(self, "_calc_ult", None))
            unidad = None
            if nodo is None:
                rp = CA.problema(t)
                if rp:
                    nodo, unidad = rp
            if nodo is None:
                return None
            traza = []
            v = CA.ejecuta(nodo, traza)
        except ErrorApp as e:
            self.turno += 1
            self.ult_just = None
            return self._ok(str(e))
        if unidad:
            txt = f"{CA.F(v)} {unidad}: {CA.escribe(nodo)} {'=' if CA.M.es_exacto(v) else '≈'} {CA.F(v)}."
        else:
            txt = CA.frase_resultado(nodo, v)
        return self._app_ok(txt, traza, valor=v)

    def _pregunta_alternativa(self, texto):
        from . import conectores as K
        cuerpo = texto.strip().strip("¿?").strip()
        if re.match(r"^(?:qu[ée]|qui[ée]n|cu[áa]l|c[óo]mo|d[óo]nde|cu[áa]ndo|cu[áa]nt)", cuerpo, re.I) or cuerpo.count(",") > 1:
            return None                                  # «¿qué prefiero, X o Y?» lo tratan otras reglas
        alts = K.expande_o(cuerpo, coloquial._verbo_finito)
        if not alts or len(alts) < 2:
            return None
        t0 = self.turno
        rs = []
        for a in alts:
            self.turno = t0
            try:
                r = self._procesar_base("¿" + a[:1].upper() + a[1:] + "?")
            except Exception:                            # noqa
                r = None
            rs.append(r if isinstance(r, dict) else None)
        self.turno = t0 + 1
        txts = [(r or {}).get("respuesta") or "" for r in rs]
        for r, t in zip(rs, txts):
            if r and r.get("estado") == "ok" and re.match(r"^(?:Sí|Si)\b", t):
                return dict(r, respuesta=re.sub(r"^(?:Sí|Si)[,:]?\s*", "", t)[:1].upper() + re.sub(r"^(?:Sí|Si)[,:]?\s*", "", t)[1:])
        for r, t in zip(rs, txts):
            if r and t.startswith("Puede ser"):
                return dict(r)
        if all(r and r.get("estado") == "ok" and t.startswith("No") for r, t in zip(rs, txts)):
            return self._ok("Ninguna de las dos cosas: " + txts[0][txts[0].find(" ") + 1:] if txts[0].startswith("No,") else txts[0])
        return None

    # ------------------------------------------------------------------ 2.11 · condicionales
    _TIEMPO_RE = re.compile(r"\b(hoy|mañana|ayer|esta (?:mañana|tarde|noche)|este (?:fin de semana|verano|invierno)|el (?:lunes|martes|miércoles|jueves|viernes|sábado|domingo)|pasado mañana)\b", re.I)

    def _condicional(self, texto):
        from . import conectores as K
        t = texto.strip()
        m = re.match(r"^¿?\s*(?:[Yy]\s+)?[Ss]i\s+(.+?)\s*,\s*¿?\s*(.+?)\s*([?.!]?)$", t)
        q_al_final = False
        if not m:
            m2 = re.match(r"^¿\s*(.+?)\s+si\s+(.+?)\s*\?$", t)
            if not m2:
                return None
            P, Q, es_preg = m2.group(2), m2.group(1), True
            q_al_final = True
        else:
            P, Q = m.group(1), m.group(2)
            es_preg = "?" in t
        if len(P.split()) < 1 or len(Q.split()) < 1:
            return None
        if es_preg:
            return self._hipotesis(P, Q)
        if not any(coloquial._verbo_finito(w.lower()) for w in Q.split()) and not re.search(r"\b(?:iré|iremos|irá|voy|vamos|va)\b", Q):
            return None
        if not hasattr(self, "reglas") or self.reglas is None:
            self.reglas = []
        self.reglas.append({"cond": P, "cons": Q, "src": texto, "lem": coloquial.lemas(P), "neg": bool(re.search(r"\bno\b", P, re.I))})
        self.turno += 1
        return self._ok(f"Entendido: si {K.a_segunda(P)}, {K.a_segunda(Q)}. Lo tendré en cuenta.", tipo="ack")

    def _busca_regla(self, P):
        lp = coloquial.lemas(P)
        neg = bool(re.search(r"\bno\b", P, re.I))
        for rg in reversed(getattr(self, "reglas", []) or []):
            if rg["neg"] == neg and rg["lem"] and (rg["lem"] <= lp or lp <= rg["lem"]):
                return rg
        return None

    def _hipotesis(self, P, Q):
        """«Si P, ¿Q?»: se supone P en una copia de la memoria, se responde Q y se deja todo como estaba."""
        from . import conectores as K
        Pn, Qn = P.strip(" ¿?,."), Q.strip(" ¿?.")
        if K.es_generica(Qn):
            rg = self._busca_regla(Pn)
            if rg:
                self.turno += 1
                return self._ok(self._fin(f"Me dijiste que si {K.a_segunda(rg['cond'])}, {K.a_segunda(rg['cons'])}"), {"dicho": [rg["src"]]})
        P2 = K.indicativo(Pn)
        hipo = P2 != Pn or bool(re.search(r"r[íi]a(?:s|mos|n)?\b", Qn))
        Q2 = K.presente_de_condicional(Qn)
        ma = re.match(r"^(?:yo\s+)?tengo\s+(\d+|un|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|quince|veinte|treinta)\s+años?\s+(menos|más|mas)$", sa(P2.lower()).replace("mas", "más") if False else P2.lower())
        if ma and re.search(r"\b(?:edad|años)\b", sa(Qn.lower())):
            ed = self._edad("U")                         # «si tuviera 10 años menos, ¿qué edad tendría?»
            self.turno += 1
            if not ed:
                return self._abst("No lo sé: no sé cuántos años tienes ahora.")
            d = M.numero(ma.group(1)) if not ma.group(1).isdigit() else int(ma.group(1))
            d = -d if ma.group(2).startswith("men") else d
            n_, just = ed
            if just.get("aprox"):
                return self._ok(f"Tendrías {n_ - 1 + d} o {n_ + d} años (ahora tienes {n_ - 1} o {n_}, según si ya has cumplido este año).")
            return self._ok(f"Tendrías {n_ + d} años (ahora tienes {n_}).")
        foto = self._foto()
        t0 = self.turno
        rq = None
        try:
            rp = self._procesar_base(P2[:1].upper() + P2[1:] + ".")
            if isinstance(rp, dict) and rp.get("estado") == "ok":
                rq = self._procesar_base("¿" + Q2[:1].upper() + Q2[1:] + "?")
        finally:
            self._restaura(foto)
            self.turno = t0 + 1
        if not isinstance(rq, dict):
            return self._abst(f"No sé responder a eso con esa suposición: «si {Pn}».")
        ans = rq.get("respuesta") or ""
        if rq.get("estado") != "ok":
            return dict(rq)
        if hipo:
            ans = K.condicional_de_presente(ans)
        return dict(rq, respuesta="En ese caso, " + (ans[:1].lower() + ans[1:] if not ans[:2].isupper() else ans))

    def _aplica_reglas(self, texto):
        from . import conectores as K
        lt = coloquial.lemas(texto)
        neg = bool(re.search(r"\bno\b", texto, re.I))
        out = []
        for rg in getattr(self, "reglas", []) or []:
            if rg.get("aplicada") == texto or not rg["lem"] or not rg["lem"] <= lt or rg["neg"] != neg:
                continue
            cons = rg["cons"].rstrip(" .")
            tm = self._TIEMPO_RE.search(texto)
            if tm and not self._TIEMPO_RE.search(cons):
                cons = f"{tm.group(1)} {cons[:1].lower() + cons[1:]}"
            n0 = len(self.F)
            try:
                rd = self._procesar_base(cons[:1].upper() + cons[1:] + ".")
            except Exception:                           # noqa
                rd = None
            nuevos = self.F[n0:]
            rg["aplicada"] = texto
            if not isinstance(rd, dict) or rd.get("estado") != "ok" or not nuevos:
                continue
            for f in nuevos:
                f["deducido"] = f"si {K.a_segunda(rg['cond'])}, {K.a_segunda(rg['cons'])}"
            out.append(f"Entonces {self.frase(nuevos[0])}: lo deduzco porque me dijiste que si {K.a_segunda(rg['cond'])}, {K.a_segunda(rg['cons'])}.")
        return " ".join(out)

    def _disyuncion(self, texto):
        from . import conectores
        alts = conectores.expande_o(texto.strip(), coloquial._verbo_finito)
        if not alts or len(alts) < 2:
            return None
        foto = self._foto()
        t0 = self.turno
        gid = f"o{t0}_{len(self.F)}"
        grupo, rels = [], []
        for k, a in enumerate(alts):
            for x in grupo:
                x["vig"] = False                         # que la alternativa anterior no cuente como «lo que había»
            n0, r0 = len(self.F), len(self.R)
            self.turno = t0
            try:
                r = self._procesar_base(a[:1].upper() + a[1:] + ".")
            except Exception:                            # noqa
                r = None
            fs = self.F[n0:]
            if not isinstance(r, dict) or r.get("estado") != "ok" or r.get("tipo") != "ack" or not fs:
                self._restaura(foto)
                return None
            for f in fs:
                f["posible"], f["alt"], f["src"] = gid, k, texto
            grupo += fs
            if re.search(r"\b(?:es|son|era|eran|fue)\s+(?:mi|tu|su|mis|tus|sus)\s", a, re.I):
                rels.append(self.R[r0:])                 # «Pablo es mi primo o mi hermano»: la relación es lo dudoso
                del self.R[r0:]
            else:
                rels.append([])                          # «mi padre o mi madre»: que existen no está en duda
        for x in grupo:
            x["vig"] = True
            try:
                self._espejo(x, quitar=True)             # una posibilidad no va a la memoria de hechos
            except Exception:                            # noqa
                pass
        self.turno = t0 + 1
        if not hasattr(self, "disy") or self.disy is None:
            self.disy = {}
        self.disy[gid] = {"rels": rels, "src": texto, "txt": self.frase(grupo[0])}
        self.ult_marco = grupo[0]
        return self._ok(f"Entendido: {self.frase(grupo[0])}; lo apunto como una de esas posibilidades.", tipo="ack")

    def _revisa_disy(self, n0):
        """Lo que se acaba de decir ¿niega o confirma una alternativa? Si queda una sola, se deduce."""
        out = []
        nuevos = [f for f in self.F[n0:] if not f.get("posible")]
        for gid, info in list(getattr(self, "disy", {}).items()):
            miembros = [x for x in self.F if x.get("posible") == gid]
            if not miembros:
                continue
            def _txt(x, neg=False):
                self._en_disy = True
                try:
                    return sa(self.frase(dict(x, neg=neg, posible=None)))
                finally:
                    self._en_disy = False
            tocadas = {}
            for f in nuevos:
                ftxt = _txt(f, neg=False)
                for x in miembros:
                    if x["v"] == f["v"] and self.can(x.get("s") or "") == self.can(f.get("s") or "") and _txt(x) == ftxt:
                        tocadas[x.get("alt")] = "no" if f.get("neg") else "si"
            if not tocadas:
                continue
            alts = sorted({x.get("alt") for x in miembros})
            si = [k for k, v in tocadas.items() if v == "si"]
            vivas = [k for k in alts if tocadas.get(k) != "no"] if not si else si[:1]
            orig = info.get("txt") or self.frase(miembros[0])
            for x in miembros:
                if x.get("alt") not in vivas:
                    self.F = [y for y in self.F if y is not x]
            if len(vivas) == 1:
                k = vivas[0]
                for x in [y for y in self.F if y.get("posible") == gid]:
                    x.pop("posible", None)
                    x["deducido"] = orig
                    try:
                        self._espejo(x)
                    except Exception:                    # noqa
                        pass
                self.R.extend(info["rels"][k] if k < len(info["rels"]) else [])
                quedan = [y for y in self.F if y.get("deducido") == orig]
                if quedan and not si:
                    out.append(f"Entonces {self.frase(quedan[0])}: lo deduzco porque me dijiste que {orig}.")
                self.disy.pop(gid, None)
        return " ".join(out)

    def _procesar_base(self, texto: str) -> Optional[dict]:
        """Respuesta del núcleo o None (delegar). dict: respuesta, estado ('ok'|'abst'|'aclara'), consultar (bool)."""
        if not texto or self.parser is None or not hasattr(self.parser, "tree"):
            return None
        raw = texto.strip()
        if len(raw) > 400 or "\n" in raw:
            return None
        raw = coloquial.normaliza(raw)
        n_glob = sa(raw).strip(" .!¡¿?")
        if "," in raw and re.match(r"^(?:muchas |mil )?gracias\b", n_glob):
            sg = social.responder(self, raw, n_glob, False)
            if sg is not None:
                self.turno += 1
                return sg if isinstance(sg, dict) else {"respuesta": sg, "estado": "ok", "consultar": False, "tipo": "social"}
        self._ult_era_preg = "?" in raw
        self._solo = False
        if "?" not in raw and re.search(r"\b(?:solo|sólo|solamente|únicamente|unicamente)\s+(?=[a-záéíóúñ]+(?:o|a|e|as|es|an|en|amos|emos)\b)", raw, re.I):
            raw = re.sub(r"\b(?:solo|sólo|solamente|únicamente|unicamente)\s+", "", raw, count=1, flags=re.I)
            self._solo = True
        raw = re.sub(r"\b(el|la) (mes|año|semana|verano|invierno|lunes|martes|miércoles|jueves|viernes|sábado|domingo|fin de semana) que viene\b",
                     lambda m_: f"{m_.group(1)} próxim{'a' if m_.group(1) == 'la' else 'o'} {m_.group(2)}", raw, flags=re.I)
        raw = re.sub(r"\b(con|para|sin) ([^,.;?]+?) y \1 ", r"\1 \2 y ", raw)
        raw = re.sub(r"^(?:Hablemos|Vamos a hablar|Hablamos|Cambiemos) de otra cosa\.?$", "Cambiando de tema.", raw, flags=re.I)
        raw = re.sub(r",\s*(?:ya te lo (?:dije|he dicho|había dicho)|como te dije|como te he dicho)\s*([.!]?)$", r"\1", raw, flags=re.I)
        # «Mi jefe es majo, se llama Alfonso»: dos frases unidas por una coma
        if "?" not in raw:                               # «Es en un banco, a las nueve» = «Es en un banco. Es a las nueve.»
            raw = re.sub(r"^((?:Es|Será|Fue|Era) .+?),\s+(a las? (?:\d+|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce)(?: y (?:media|cuarto))?(?: de la (?:mañana|tarde|noche))?)\s*([.!]?)$",
                         lambda m_: m_.group(1) + ". " + m_.group(1).split()[0] + " " + m_.group(2) + (m_.group(3) or "."), raw)
        if "?" not in raw and not _CORR.match(raw):
            raw = re.sub(r",\s+((?:se |me |le |lo |la )?(?:llama|llamo|llaman|es|está|esta|tiene|vive|trabaja|son|están|tienen|viven|trabajan|tengo|vivo|trabajo|estoy|soy|va|voy)\b)",
                         lambda m_: (". " + m_.group(1)[:1].upper() + m_.group(1)[1:]) if len(raw[:m_.start()].split()) >= 3 else m_.group(0), raw)
            raw = re.sub(r"^(?:De pequeñ[oa]|De niñ[oa]|De joven|De chic[oa]|De crí[oa]|Cuando era (?:pequeñ[oa]|niñ[oa]|joven|chic[oa]))\s*,?\s+", "Antes ", raw)
        else:
            raw = re.sub(r"\s+(?:de pequeñ[oa]|de niñ[oa]|de joven|de chic[oa]|cuando era (?:pequeñ[oa]|niñ[oa]|joven))(?=\s*\?)", " antes", raw)
        mcu = re.match(r"^(?:(Mi|Tu|Su)\s+cumpleaños|[Ee]l\s+cumpleaños\s+de\s+(.+?))\s+(?:es|será|cae)\s+(.+?)([.!]?)$", raw)
        if mcu and "?" not in raw:                      # «Su cumpleaños es el día doce» -> «(Mi novia) cumple años el día doce»
            if mcu.group(1) == "Mi":
                raw = f"Cumplo años {mcu.group(3)}{mcu.group(4) or '.'}"
            elif mcu.group(2):
                raw = f"{mcu.group(2)[:1].upper() + mcu.group(2)[1:]} cumple años {mcu.group(3)}{mcu.group(4) or '.'}"
            elif mcu.group(1) == "Su":
                e_cu = next((x for x in [self.ult_suj] + list(reversed(self.menc)) if x and self.can(x) not in ("U", "L") and self.es_persona(x)), None)
                if e_cu:
                    q_ = cambia_persona(self.disp(self.can(e_cu)))
                    raw = f"{q_[:1].upper() + q_[1:]} cumple años {mcu.group(3)}{mcu.group(4) or '.'}"
        raw = re.sub(r"^(Cumple|Cumplo|Cumplen|Cumplió|Cumplí)\s+(\d+|veinte|treinta|cuarenta|cincuenta|sesenta|setenta|ochenta|noventa|cien)\s*([.!]?)$", r"\1 \2 años\3", raw)
        if any(f["v"] == "cumplir" for f in self.F):
          raw = re.sub(r"^¿Cuándo es (?:el|mi|tu|su) cumpleaños(?: de (.+?))?\?$", lambda m_: "¿Cuándo cumple años " + m_.group(1) + "?" if m_.group(1) else "¿Cuándo cumplo años?", raw, flags=re.I)
        raw = re.sub(r"^¿(?:Cuántos años|Cuántos) (cumple|cumplo|cumplen) (.+?)\?$", r"¿Cuántos años \1 \2?", raw, flags=re.I)
        if "?" in raw:
            def _cap_(m_):
                c_ = [x for x in M.analizar(m_.group(2)) if x[1] == "inf"]
                # 2.15: la capacidad de fábrica («los pájaros vuelan») no vale para «¿quién sabe…?» ni cuando la persona ha contado quién sabe hacerlo
                if c_ and (re.match(r"^\W*(?:y\s+)?qui[ée]n", raw, re.I) or any(sa(f_.get("xinf") or "") == c_[0][0] for f_ in self.F)):
                    return m_.group(0)
                if c_ and any(not rs_ and sa(v_[:-2] if v_.endswith("se") and len(v_) > 4 else v_) == c_[0][0] for _, _, v_, rs_ in conceptos.kb()["props"]):
                    return M.conjugar(c_[0][0], "pres", "3p" if m_.group(1).lower().endswith("n") else "3s")
                return m_.group(0)
            raw = re.sub(r"\b(puede|pueden|sabe|saben)\s+([a-záéíóúñ]+r)\b", _cap_, raw)
        mt = re.match(r"^((?:[Ee]l|[Ll]a) próxim[oa] (?:mes|año|semana|verano|invierno|lunes|martes|miércoles|jueves|viernes|sábado|domingo|fin de semana))\s*,?\s+(.+?)([.!]?)$", raw)
        if mt and "?" not in raw:
            raw = mt.group(2)[:1].upper() + mt.group(2)[1:] + " " + mt.group(1).lower() + (mt.group(3) or ".")
        # «¿Cuál es tu color favorito?» … «El mío es el azul» = «Mi color favorito es el azul»
        pt_ = getattr(self, "_preg_tuyo", None)
        mm_ = re.match(r"^(?:Pues |Bueno,? )?(?:[Ee]l|[Ll]a) m[ií][oa] (?:es|son) (.+?)([.!]?)$", raw)
        if pt_ and mm_ and "?" not in raw:
            raw = f"Mi {pt_[0]} {pt_[1]} es {mm_.group(1)}{mm_.group(2) or '.'}"
        if "?" not in raw:
            self._preg_tuyo = None
        # «¿Tú sabes cocinar?» … «Yo sí, me encanta» = «Yo sé cocinar. Me encanta cocinar.»
        pl_ = getattr(self, "_preg_a_lcm", None)
        my = re.match(r"^(?:Pues |Bueno,? )?[Yy]o (s[ií]|tambi[eé]n|no|tampoco)\b\s*[,.]?\s*(.*?)([.!]?)$", raw)
        if pl_ and my and "?" not in raw:
            neg_ = my.group(1).lower() in ("no", "tampoco")
            verbo = {"sabes": "sé", "puedes": "puedo", "te gusta": "me gusta", "te gustaria": "me gustaría", "sueles": "suelo", "has probado a": "he probado a"}[pl_[0]]
            raw = ("No " if neg_ else "") + verbo + " " + pl_[1] + "."
            resto_ = my.group(2).strip()
            if resto_ and re.match(r"^(?:me|no me) (?:encanta|gusta|apasiona|chifla|aburre)\b", resto_, re.I) and len(resto_.split()) <= 4:
                raw += " " + resto_[:1].upper() + resto_[1:] + " " + pl_[1] + "."
            elif resto_:
                raw += " " + resto_[:1].upper() + resto_[1:] + "."
            raw = raw[:1].upper() + raw[1:]
        self._preg_a_lcm = None if "?" not in texto else getattr(self, "_preg_a_lcm", None)
        # «A mis hijos no les gustan nada»: el objeto es lo último de lo que se habló
        # elipsis del verbo: «Mi suegra se llama Pilar y mi suegro Antonio» -> dos frases
        mgp = re.match(r"^((?:[Mm]i|[Tt]u|[Ss]u|[Ee]l|[Ll]a)\s+\w+(?:\s+(?:mayor|pequeño|pequeña|menor))?)\s+(se llama|se llaman|vive en|trabaja en|es de|es|tiene|estudia)\s+([^,]+?)\s*,?\s+y\s+((?:mi|tu|su|el|la)\s+\w+(?:\s+(?:mayor|pequeño|pequeña|menor))?)\s+([^,]+?)([.!]?)$", raw)
        if mgp and "?" not in raw and not any(G._es_verbo_finito(t, G.tokens(self.parser, mgp.group(5)), k) for k, t in enumerate(G.tokens(self.parser, mgp.group(5)))) \
                and (mgp.group(2) not in ("se llama", "se llaman") or mgp.group(5)[:1].isupper()):
            raw = f"{mgp.group(1)} {mgp.group(2)} {mgp.group(3)}. {mgp.group(4)[:1].upper() + mgp.group(4)[1:]} {mgp.group(2)} {mgp.group(5)}{mgp.group(6) or '.'}"
        # «Tengo dos perros, uno grande y otro pequeño»: dos de la misma clase que se distinguen por un adjetivo
        muo = re.match(r"^((?:[Tt]engo|[Tt]enemos)\s+dos\s+([a-záéíóúñ]+s))\s*[,:]\s*(?:uno|una)\s+([a-záéíóúñ]+)\s+y\s+(?:el |la )?(?:otro|otra)\s+([a-záéíóúñ]+)\s*([.!]?)$", raw)
        if muo and "?" not in raw:
            self._descr = {"pl": muo.group(2), "adjs": [sa(M.masc(muo.group(3))), sa(M.masc(muo.group(4)))], "turno": self.turno}
            raw = muo.group(1) + "."
        # «El grande se llama Thor. El pequeño se llama Kira.» con esos dos adjetivos pendientes
        de_ = getattr(self, "_descr", None)
        if de_ and "?" not in raw and self.turno - de_["turno"] <= 3:
            pares = re.findall(r"(?:^|\.\s+)(?:[Ee]l|[Ll]a|[Yy] el|[Yy] la)\s+([a-záéíóúñ]+)\s+se llama\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)", raw)
            if pares and all(sa(M.masc(a_)) in de_["adjs"] for a_, _ in pares):
                frases = []
                for a_, nom in pares:
                    frases.append(f"{nom} es {M.concuerda(sa(M.masc(a_)), M.genero_nombre(nom))}.")
                noms = [nom for _, nom in pares]
                raw = (f"Mis {de_['pl']} se llaman {' y '.join(noms)}. " if len(noms) == 2 else f"Uno de mis {de_['pl']} se llama {noms[0]}. ") + " ".join(frases)
                if len(noms) == 2:
                    self._descr = None
        # «(Mario quiere un móvil.) Todos sus amigos ya tienen uno»: «uno» es otro de lo último que se nombró con «un»
        mun = re.match(r"^(.*\b(?:tiene|tienen|tengo|tenemos|quiero|quiere|quieren|compré|compró|compraron|he comprado|ha comprado|han comprado|busco|busca|necesito|necesita|necesitan|llevo|lleva|llevan))\s+(uno|una)\b((?:\s+(?:también|tambien|ya|igual|así|asi|parecido|parecida|igualito|igualita))*\s*[.!]?)$", raw)
        if mun and "?" not in raw:
            for f_u in reversed(self.F[-10:]):
                od_u = f_u.get("obj_disp") or ""
                if re.match(r"^(?:un|una)\s+\S", od_u) and od_u.split()[0] == ("un" if mun.group(2) == "uno" else "una") and f_u.get("turno", -9) >= self.turno - 8:
                    raw = mun.group(1) + " " + cambia_persona(od_u) + mun.group(3)
                    break
        # «(Mi hermana quiere que vaya a su casa.) Lo haré la semana que viene»: «lo» es lo que me han pedido
        mlo = re.match(r"^[Ll]o (haré|hare|haremos|hago|hacemos|voy a hacer|vamos a hacer)\s+(.+?)([.!]?)$", raw)
        um_lo = self.ult_marco or {}
        if mlo and "?" not in raw and um_lo.get("dicho") and (um_lo.get("obj_disp") or "").startswith("que "):
            ws = um_lo["obj_disp"][4:].split()
            k_ = 0
            while k_ < len(ws) - 1 and sa(ws[k_]) in ("no", "te", "se", "lo", "la", "le", "ya"):
                k_ += 1
            inf_ = coloquial.subjuntivo(ws[k_][:-1]) if ws and ws[k_].endswith("s") else None
            if inf_:
                fut = M.conjugar(inf_, "fut", "1p" if mlo.group(1) in ("haremos", "hacemos", "vamos a hacer") else "1s")
                resto_ = " ".join(ws[k_ + 1:])
                resto_ = cambia_persona(resto_)
                raw = f"{fut[:1].upper() + fut[1:]} {resto_} {mlo.group(2)}{mlo.group(3) or '.'}"
        # «(Estamos pensando en comprar un sofá nuevo.) Lo compraremos en…»: «lo» es lo que se iba a comprar
        mcl = re.match(r"^([Ll]o|[Ll]a|[Ll]os|[Ll]as)\s+([a-záéíóúñ]+)\b(.*)$", raw)
        if mcl and "?" not in raw:
            for f_c in reversed(self.F[-10:]):
                if f_c.get("turno", -9) < self.turno - 6:
                    break
                txts = [d2 or "" for _, _, d2 in f_c.get("comps", [])] + [f_c.get("xinf") or ""]
                hecho = None
                for t_ in txts:
                    mi_ = re.search(r"\b([a-záéíóúñ]+)(ar|er|ir)\s+(?:un|una|unos|unas|el|la|los|las)\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)$", t_)
                    if mi_ and len(mi_.group(1)) >= 3 and sa(mcl.group(2).lower()).startswith(sa(mi_.group(1))):
                        nuc_ = mi_.group(3).split()[0]
                        g_ = M.genero_sust(sa(M.singular(nuc_)))
                        pl_ = nuc_.endswith("s") and sa(M.singular(nuc_)) != sa(nuc_)
                        cl_ = mcl.group(1).lower()
                        if (cl_ in ("la", "las")) == (g_ == "f") and cl_.endswith("s") == pl_:
                            art = {"lo": "el", "la": "la", "los": "los", "las": "las"}[cl_]
                            hecho = f"{mcl.group(2)[:1].upper() + mcl.group(2)[1:]} {art} {mi_.group(3)}{mcl.group(3)}"
                            break
                if hecho:
                    raw = hecho
                    break
        # «(Me hice daño en el tobillo.) Me duele bastante»: lo que duele es la parte del cuerpo de la que se habla
        mdu = re.match(r"^(?:[Yy] |[Aa]hora )?(?:me|Me) (duele|duelen|molesta|molestan|pica|pican)((?:\s+(?:bastante|mucho|muchísimo|un poco|todavía|aún|ya|un montón|fatal))*)\s*([.!]?)$", raw)
        if mdu and "?" not in raw:
            for f_d in reversed(self.F[-10:]):
                txts = [d2 or "" for _, _, d2 in f_d.get("comps", [])] + [f_d.get("obj_disp") or ""]
                hit = None
                for t_ in txts:
                    for w_ in sa(t_).split():
                        if w_ in _CUERPO or sa(M.singular(w_)) in _CUERPO:
                            hit = w_
                if hit and f_d.get("turno", -9) >= self.turno - 4:
                    pl_d = hit.endswith("s") and sa(M.singular(hit)) in _CUERPO and sa(M.singular(hit)) != hit
                    art = ("las " if M.genero_sust(sa(M.singular(hit))) == "f" else "los ") if pl_d else ("la " if M.genero_sust(hit) == "f" else "el ")
                    vb = mdu.group(1) if not pl_d else {"duele": "duelen", "molesta": "molestan", "pica": "pican"}.get(mdu.group(1), mdu.group(1))
                    raw = f"Me {vb} {art}{hit}{mdu.group(2)}{mdu.group(3) or '.'}"
                    break
        # «(Mi gata ha tenido gatitos.) Ha tenido cuatro, dos negros y dos blancos»: el número sin nombre es de lo último nombrado
        mnum = re.match(r"^((?:(?:ha|han|he|hemos|había|habían)\s+[a-záéíóúñ]+(?:ado|ido))|tiene|tienen|tengo|tenemos|tuvo|tuvieron|compré|compró|compramos|vinieron|vienen|vendrán|hay|había|habrá)\s+(dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|\d+)(?:\s*,\s*.+)?\s*([.!]?)$", raw, re.I)
        um_n = self.ult_marco or {}
        if mnum and "?" not in raw and um_n.get("obj_cls") and um_n.get("pl_obj") is not None and self.turno - um_n.get("turno", -9) <= 2:
            nom_n = M.plural(um_n["obj_cls"].split()[0]) if " " not in um_n["obj_cls"] else um_n["obj_cls"]
            if not mnum.group(1).split()[-1].startswith(("tien", "teng", "ten")) or um_n.get("v") == "tener":
                raw = f"{mnum.group(1)} {mnum.group(2)} {nom_n}{mnum.group(3) or '.'}"
        # «(He cocinado una paella para mis suegros.) Les ha encantado»: a quién y qué, de lo último que se dijo
        mle = re.match(r"^(Le|Les)\s+(?:(?:ha|han|había|habían)\s+)?(gustado|encantado|gustó|encantó|gustaron|encantaron)(?:\s+(?:mucho|muchísimo|un montón))?\s*([.!]?)$", raw)
        um_l = self.ult_marco or {}
        if mle and um_l.get("obj_disp") and um_l.get("obj") and not self.es_persona(um_l["obj"]):
            pl_l = mle.group(1) == "Les"
            exp_l = None
            for p2, e2, d2 in um_l.get("comps", []):
                if e2 and self.es_persona(e2) and e2 not in ("U", "L") and bool(self.E.get(self.can(e2), {}).get("pl")) == pl_l:
                    exp_l = cambia_persona(self.disp(e2)); break
            if exp_l:
                od_l = re.sub(r"^(?:un|una|unos|unas)\s+", lambda x: {"un": "el ", "una": "la ", "unos": "los ", "unas": "las "}[x.group(0).strip()], cambia_persona(um_l["obj_disp"]))
                vb_l = ("encant" if "encant" in mle.group(2) else "gust") + ("aron" if um_l.get("pl_obj") else "ó")
                raw = f"A {exp_l} {mle.group(1).lower()} {vb_l} {od_l}{mle.group(3) or '.'}"
        mg_ = re.match(r"^(.*\b(?:me|te|le|les|nos)\s+(?:gusta|gustan|gustó|gustaron|encanta|encantan|encantó|apasiona|apasionan|chifla|chiflan|(?:ha|han)\s+(?:gustado|encantado)))(?:\s+(?:nada|mucho|muchísimo|nada de nada|un montón|bastante))?\s*([.!]?)$", raw)
        um_ = self.ult_marco or {}
        if mg_ and "?" not in raw and um_.get("obj_disp") and um_.get("obj_cls"):
            od = re.sub(r"^(?:un|una|unos|unas)\s+", lambda x: {"un": "el ", "una": "la ", "unos": "los ", "unas": "las "}[x.group(0).strip()], cambia_persona(um_["obj_disp"]))
            if not re.match(r"^(?:el|la|los|las|un|una|mi|tu|su)\b", od):
                cl_ = um_["obj_cls"]
                od = ("las " if M.genero_sust(cl_) == "f" else "los ") + od if od.split()[0].endswith("s") else ("la " if M.genero_sust(cl_) == "f" else "el ") + od
            raw = mg_.group(1) + " " + od + (mg_.group(2) or ".")
        # «Las tenía en el bolso»: el pronombre de objeto es lo último de lo que se habló (si concuerda)
        raw = re.sub(r"^((?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s*,?\s+)?)([Ll]o|[Ll]a|[Ll]os|[Ll]as)\s+(he|has|ha|hemos|habéis|han|había|habías|habíamos|habían)\s+([a-záéíóúñ]+(?:ado|ido|to|cho|so))\b",
                     lambda m_: m_.group(1) + m_.group(2) + " " + m_.group(3) + "_" + m_.group(4), raw)   # «La he visto» -> verbo compuesto en un bloque
        raw = re.sub(r"^([Ss]e)\s+(lo|la|los|las)\s+(?=\w+.*\ba\s+(?:mi|mis|tu|tus|su|sus|el|la|los|las|[A-ZÁÉÍÓÚÑ]))", lambda m_: m_.group(2).capitalize() + " ", raw)   # «Se lo voy a enseñar a mis padres»: el «se» repite «a mis padres»
        raw = re.sub(r"^((?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s*,?\s+)?)([Ll]o|[Ll]a|[Ll]os|[Ll]as)\s+(voy a|vas a|va a|vamos a|van a|tengo que|tienes que|tiene que|tenemos que|quiero|quiere|queremos|puedo|puede|podemos|debo|debemos|necesito|pienso|suelo|solemos|intento)\s+([a-záéíóúñ]+[aei]r)\b",
                     lambda m_: m_.group(1) + m_.group(2) + " " + m_.group(3).replace(" ", "_") + "_" + m_.group(4), raw)   # «Las voy a llevar» -> perífrasis en un bloque
        mc_ = re.match(r"^((?:(?:Mañana|Hoy|Luego|Después|Esta tarde|Esta noche|El (?:lunes|martes|miércoles|jueves|viernes|sábado|domingo))\s*,?\s+)?)([Ll]o|[Ll]a|[Ll]os|[Ll]as)\s+([a-záéíóúñ_]+)\s+(.+?)([.!]?)$", raw)
        um_c = self.ult_marco or {}
        if mc_ and "_" not in mc_.group(3) and (conceptos._kb_clase(sa(mc_.group(3))) or _es_finito(mc_.group(4).split()[0])
                                                or (sa(mc_.group(4).split()[0].lower()) in ("de", "del", "es", "son", "era", "fue", "y", "que")
                                                    and all(x[1] == "pres" and x[2] == "3s" for x in M.analizar(sa(mc_.group(3))) if x[1] in ("pres", "pret", "imp", "fut", "cond")))):
            mc_ = None                                  # «La casa es grande»: «la» es artículo, no pronombre
        if mc_ and (mc_.group(1) or mc_.group(2)[0] == "L") and "?" not in raw and any(x[1] in ("pres", "pret", "imp", "fut", "cond") for x in M.analizar(mc_.group(3).split("_")[0])) \
                and (um_c.get("obj_disp") or self._ref_clitico(mc_.group(2).lower())):
            od = um_c.get("obj_disp") or ""
            if od.startswith("que "):                   # «Me ha pedido que haga un informe. Lo tengo que entregar…»: lo = el informe
                f_q = mc_.group(2).lower() in ("la", "las"); pl_q = mc_.group(2).lower() in ("los", "las")
                cands = re.findall(r"\b(un|una|unos|unas|el|la|los|las|mi|mis|tu|tus)\s+([a-záéíóúñ]+)", od)
                od = ""
                for art_q, nom_q in reversed(cands):
                    g_q = "f" if art_q in ("una", "unas", "la", "las") else ("m" if art_q in ("un", "unos", "el", "los") else M.genero_sust(sa(nom_q)))
                    if (g_q == "f") == f_q and (art_q.endswith("s") or nom_q.endswith("s") and art_q in ("mis", "tus")) == pl_q:
                        od = {"un": "el", "una": "la", "unos": "los", "unas": "las"}.get(art_q, art_q) + " " + nom_q
                        od = cambia_persona(od)
                        break
            if not od:                                  # «Mis sobrinas vienen el sábado. Las voy a llevar al zoo»
                e_0 = self._ref_clitico(mc_.group(2).lower())
                od = cambia_persona(self.disp(e_0)) if e_0 else ""
            pref_c = mc_.group(1).strip(" ,")
            pl_c, f_c = mc_.group(2).lower() in ("los", "las"), mc_.group(2).lower() in ("la", "las")
            ult_ = mc_.group(3).split("_")[-1]
            v_c = ([x[0] for x in M.analizar(ult_) if x[1] in ("part", "inf")] or [""])[0] if "_" in mc_.group(3) else M.analizar(mc_.group(3))[0][0]
            if (um_c.get("obj_cls") or "") in ("año", "mes", "dia", "hora", "minuto", "euro", "kilo", "metro", "vez", "semana") or (um_c.get("obj") or "").startswith("K:"):
                e_c = self._ent_reciente(gen="f" if f_c else "m", pl=pl_c, cosa=v_c in _V_COSA) or self._ent_reciente(gen="f" if f_c else "m", pl=pl_c)
                medida_ = (um_c.get("obj_cls") or "") in ("año", "mes", "dia", "hora", "minuto", "euro", "kilo", "metro", "vez", "semana")
                od = cambia_persona(self.disp(e_c)) if e_c else ("" if medida_ else od)   # «Thor tiene cinco años… Los saco a pasear»: no son los años
                if not e_c and pl_c:                    # «Tengo dos perros»: «los» son mis perros
                    for f_t in reversed(self.F[-14:]):
                        if f_t["v"] == "tener" and self.can(f_t.get("s") or "") == "U" and f_t.get("pl_obj") and f_t.get("obj_cls") and \
                                f_t["obj_cls"] not in ("año", "mes", "dia", "hora", "euro") and (M.genero_sust(f_t["obj_cls"]) == "f") == f_c:
                            od = "mis " + M.plural(f_t["obj_cls"]); break
            if v_c in ("llevar", "traer", "arreglar", "lavar", "vender", "aparcar", "reparar", "pintar", "comprar", "dejar", "guardar", "coger", "romper", "limpiar", "devolver", "recoger"):
                e_f = self._cosa_fisica(gen="f" if f_c else "m", pl=pl_c)   # «Tengo un problema con mi coche. Lo llevo al taller»: lo físico
                if e_f:
                    od = cambia_persona(self.disp(e_f))
            art = sa(re.sub(r"^a\s+", "", od).split()[0]) if od else ""
            ok_c = bool(od) and (art in ("los", "las", "mis", "tus", "sus", "unos", "unas") or od.split()[0].endswith("s")) == pl_c and \
                   ((art in ("la", "las", "una", "unas")) == f_c if art in ("el", "la", "los", "las", "un", "una", "unos", "unas") else True)
            if not ok_c and v_c in _V_COSA:              # «(Vamos a pintar la cocina… me gusta el azul.) La pintaremos de blanco»: la cocina
                e_c2 = self._ent_reciente(gen="f" if f_c else "m", pl=pl_c, turnos=6, cosa=True)
                if e_c2:
                    od = cambia_persona(self.disp(e_c2)); ok_c = True
            if ok_c:
                vb_ = mc_.group(3).replace("_", " ")
                raw = vb_[:1].upper() + vb_[1:] + " " + od + " " + mc_.group(4) + ((" " + pref_c.lower()) if pref_c else "") + (mc_.group(5) or ".")
        raw = re.sub(r"\b(he|has|ha|hemos|habéis|han|había|habías|habíamos|habían)_", r"\1 ", raw)
        raw = re.sub(r"\b([a-záéíóúñ]+)_((?:a|que)_)?([a-záéíóúñ]+[aei]r)\b", lambda m_: m_.group(1) + " " + (m_.group(2) or "").replace("_", " ") + m_.group(3), raw)
        # «Mis hijos la prefieren con queso»: clítico de objeto entre el sujeto y el verbo
        msc = re.match(r"^((?:(?:[Mm]is?|[Tt]us?|[Ss]us?|[Ee]l|[Ll]a|[Ll]os|[Ll]as)\s+[a-záéíóúñ]+)|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s+(?:también\s+|siempre\s+|no\s+)?(lo|la|los|las)\s+([a-záéíóúñ]+)\b(.*?)([.!]?)$", raw)
        if msc and "?" not in raw and _es_finito(msc.group(3)) and not _es_finito(msc.group(1).split()[-1]) and not M.analizar(sa(msc.group(1).split()[-1])):
            sn_t = msc.group(1)
            cab_t = sa(M.singular(sn_t.split()[-1].lower()))
            persona_t = sn_t[:1].isupper() and len(sn_t.split()) == 1 or cab_t in FAMILIA or cab_t in PERSONA_CLS or M.masc(cab_t) in FAMILIA
            if persona_t:
                pl_s, f_s = msc.group(2) in ("los", "las"), msc.group(2) in ("la", "las")
                v_s = M.analizar(sa(msc.group(3)))[0][0] if M.analizar(sa(msc.group(3))) else ""
                e_s = self._ent_reciente(gen="f" if f_s else "m", pl=pl_s, turnos=6, cosa=True)
                od_s = None
                um_s = self.ult_marco or {}
                if um_s.get("obj_disp") and um_s.get("obj") and not self.es_persona(um_s["obj"]):
                    art_s = sa(um_s["obj_disp"].split()[0])
                    g_o = self.E.get(self.can(um_s["obj"]), {}).get("gen") or M.genero_sust(sa(um_s.get("obj_cls") or ""))
                    if (g_o == "f") == f_s and bool(um_s.get("pl_obj")) == pl_s:
                        od_s = re.sub(r"^(?:un|una|unos|unas)\s+", lambda x: {"un": "el ", "una": "la ", "unos": "los ", "unas": "las "}[x.group(0).strip()], cambia_persona(um_s["obj_disp"]))
                        if not re.match(r"^(?:el|la|los|las|mi|mis|tu|tus|su|sus)\s", od_s):
                            od_s = ("la " if f_s else "el ") + od_s if not pl_s else ("las " if f_s else "los ") + od_s
                if od_s is None and e_s:
                    od_s = cambia_persona(self.disp(e_s))
                if od_s:
                    neg_s = " no" if re.search(r"\sno\s+(?:lo|la|los|las)\s", raw) else ""
                    raw = f"{sn_t}{neg_s} {msc.group(3)} {od_s}{msc.group(4)}{msc.group(5) or '.'}"
        # «(La serie) va de unos detectives»: de qué trata lo último que se nombró
        mv_ = re.match(r"^(?:Va|Trata|Habla|Iba|Trataba)\s+(?:de|sobre)\s+(.+?)([.!]?)$", raw)
        um_v = self.ult_marco or {}
        if mv_ and "?" not in raw and um_v.get("obj") and not self.es_persona(um_v["obj"]) and um_v.get("obj_disp"):
            od_v = re.sub(r"^(?:un|una)\s+", lambda x: "el " if x.group(0).strip() == "un" else "la ", um_v["obj_disp"])
            raw = od_v[:1].upper() + od_v[1:] + " trata de " + mv_.group(1) + (mv_.group(2) or ".")
        raw = re.sub(r"^(.+?\s+(?:es|era|son))\s+de\s+((?:19|20)\d\d)\s*([.!]?)$", r"\1 del año \2\3", raw) if "?" not in raw else raw
        mk_ = re.match(r"^(.+?)\s+es\s+un[a]?\s+([A-Z][A-Za-záéíóúñ]+(?:\s+[A-Z0-9][A-Za-z0-9]*)?)(?:\s+de\s+(\d{4}))?([.!]?)$", raw)
        if mk_ and "?" not in raw and ("N:" + sa(mk_.group(2).split()[0])) not in self.E and not self.es_persona(self._sn_ent(mk_.group(1)) or "U"):
            raw = f"{mk_.group(1)} es de la marca {mk_.group(2)}." if not mk_.group(3) else f"{mk_.group(1)} es de la marca {mk_.group(2)}. {mk_.group(1)[:1].upper() + mk_.group(1)[1:]} es del año {mk_.group(3)}."
            raw = raw[:1].upper() + raw[1:]
        uc = getattr(self, "_ult_clase", None)
        if uc and re.search(r"\b(?:quiere|quiero|tiene|tengo|compr[oóé]|compra|necesito|necesita|busca|busco)\s+(?:uno|una)\s*[.!]?$", raw, re.I):
            raw = re.sub(r"\s+(?:uno|una)(\s*[.!]?)$", " " + conceptos.un(uc) + r"\1", raw)
        raw = re.sub(r"^\s*(?:te cuento|a ver|pues nada|pues mira|resulta que|que sepas que|por cierto|te digo una cosa|sabes que|una cosa|te comento|cambiando de tema|hablando de otra cosa|por otro lado|otra cosa|a todo esto|volviendo a lo de antes|volviendo a lo (?:anterior|de (?:antes|mi \w+|\w+))|retomando lo de antes|como te dec[ií]a)\s*[:,.]\s*(?=\S)", "", raw, flags=re.I)
        raw = re.sub(r"\b(?:todav[ií]a|a[uú]n)\s+(?=(?:no\s+)?[a-záéíóúñ]+(?:[aeo]|an|en|o)\b)", "", raw, flags=re.I)
        raw = raw[:1].upper() + raw[1:]
        raw = _numeros_compuestos(raw)
        mf = re.search(r"\b(?:[Ss]oy|[Ee]stoy) (?:una |muy )?([a-záéíóúñ]+a)\b", raw)
        if mf and not self.E["U"].get("gen") and M.masc(sa(mf.group(1))) != sa(mf.group(1)) and not raw.startswith(("¿", "Soy de ")):
            self.E["U"]["gen"] = "f"                          # «Soy enfermera», «Estoy cansada»: la persona habla en femenino
        raw = re.sub(r"\b(sigue|siguen|sigues|sigo)\s+([a-záéíóúñ]+)(?:ando|iendo|yendo)\b", lambda m: _gerundio_a_presente(m), raw, flags=re.I)
        raw = re.sub(r"\bse (encuentra|encuentran)\b(?!\s+(?:con|un|una|el|la)\b)", lambda m: "está" if m.group(1).endswith("a") else "están", raw, flags=re.I)
        raw = re.sub(r"\bme encuentro\b(?!\s+(?:con|un|una|el|la)\b)", "estoy", raw, flags=re.I)
        # «Tenemos una hija, Vera, de ocho años» = «Tenemos una hija. Se llama Vera. Vera tiene ocho años.»
        ma = re.match(r"^(.*?\b(?:un|una|mi|tu|su|otro|otra)\s+[a-záéíóúñ]+),\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+),\s*(?:de\s+(\S+)\s+(años?|meses))?\s*\.?$", raw)
        if ma:
            raw = f"{ma.group(1)}. Se llama {ma.group(2)}." + (f" {ma.group(2)} tiene {ma.group(3)} {ma.group(4)}." if ma.group(3) else "")
        # «una se llama Carla y la otra Marta» (tras «dos chicas») = «Se llaman Carla y Marta.»
        mu = re.match(r"^(?:Una|Uno)\s+se\s+llama\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s*,?\s+y\s+(?:la|el)\s+otr[oa]\s+(?:se\s+llama\s+)?([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s*\.?$", raw)
        if mu:
            raw = f"Se llaman {mu.group(1)} y {mu.group(2)}."
        # «Tengo dos amigos: Mario y Bea.» = «Tengo dos amigos. Se llaman Mario y Bea.»
        mg = re.match(r"^(.*\b(?:dos|tres|cuatro|cinco|seis)\s+[a-záéíóúñ]+)\s*[:,]\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:,\s*[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\s+[ye]\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s*\.?$", raw)
        if mg:
            raw = f"{mg.group(1)}. Se llaman {mg.group(2)}."
        # «Los dos viven en Burgos», «Ellos viven…»: el sujeto es el último grupo nombrado
        if getattr(self, "ult_grupo", None):
            raw = re.sub(r"^(?:los dos|las dos|ambos|ambas|ellos|ellas)\s+(?=[a-záéíóúñ]+n\b)", "", raw, flags=re.I)
            raw = raw[:1].upper() + raw[1:]
            mj = re.match(r"^(?:Los dos |Las dos |Ellos |Ellas )?(viven|trabajan|estudian) juntos\.?$", raw, re.I)
            if mj and len(self.ult_grupo) == 2:
                a_, b_ = [self.disp(x) for x in self.ult_grupo]
                v_ = M.conjugar(M.analizar(mj.group(1).lower())[0][0], "pres", "3s")
                raw = f"{a_} {v_} con {b_}. {b_} {v_} con {a_}."
        # «Allí trabaja…»: el último lugar nombrado
        if re.search(r"\b(?:all[ií]|all[aá])\b", raw, re.I) and getattr(self, "_ult_lugar", None) and not re.search(r"\b(?:de|desde|hasta|por|hacia|para) all", raw, re.I):
            raw = re.sub(r"\b(?:all[ií]|all[aá])\b", "en " + self.disp(self._ult_lugar), raw, count=1, flags=re.I)
            raw = raw[:1].upper() + raw[1:]
        m = _QUE_LLAMA.match(raw)
        if m:
            raw = f"{m.group(1)}. Se llama {m.group(2)}."
        partes = [p.strip() for p in re.split(r"(?<=[.!?…])\s+(?=[¿¡A-ZÁÉÍÓÚÑ])", raw) if p.strip()]
        partes2 = []
        for p in partes:
            if "?" not in p and "¿" not in p:
                trozos = re.split(r"\s*[,;]\s+(?:pero\s+|y\s+)?(?=(?:ahora|ya no|antes|actualmente)\b)|\s+(?:pero|y)\s+(?=ahora\b)", p)
                if len(trozos) > 1 and all(len(x.split()) >= 2 for x in trozos):
                    partes2.extend(x[:1].upper() + x[1:] for x in trozos); continue
            partes2.append(p)
        partes = []
        self._saludo_previo = ""
        for k_, p in enumerate(partes2):
            if k_ == 0:
                ms = re.match(r"^\s*(hola+|buenas|buenos d[ií]as|buenas tardes|buenas noches|hey|oye|mira|pues|bueno)\s*[,.!]+\s*(?=\S)", p, re.I)
                if ms and len(p) > ms.end() + 3 and "?" not in p[:ms.end()] and not re.match(r"^(hola|buenos dias|buenas tardes|buenas noches|buenas|que tal|como estas|como va|como andas|que hay)\b", sa(p[ms.end():]).strip(" ¿¡")):
                    if sa(ms.group(1)) in ("hola", "holaa", "buenas", "buenos dias", "buenas tardes", "buenas noches", "hey"):
                        self._saludo_previo = {"buenos dias": "¡Buenos días!", "buenas tardes": "¡Buenas tardes!", "buenas noches": "¡Buenas noches!"}.get(sa(ms.group(1)), "¡Hola!")
                    p = p[ms.end():]
                    p = p[:1].upper() + p[1:]
            if "?" not in p and "¿" not in p and re.search(r"\s(?:y|e|pero)\s|,\s", p):
                partes.extend(self._parte_clausulas(p))
            else:
                partes.append(p)
        if len(partes) > 5:
            return None
        foto = self._foto()
        v_ = getattr(self, "vista", None)
        if v_ is not None and not getattr(self, "_vista_usada", False) and v_["turno"] < self.turno and (
                not getattr(self, "_ult_era_preg", True) or str(self.ult_suj or "").startswith(("N:", "I:", "G:"))):
            self.foco_vista = False                      # la imagen dejó de ser el tema: se ha hablado de otra cosa
        self._vista_usada = False
        self.turno += 1
        self._suj_cl = None
        G.NOMBRES.clear()
        G.NOMBRES.update(k[2:].split()[0] for k in self.E if k.startswith("N:"))
        res = []
        self._multi_parte = len(partes) > 1             # 2.12: «me voy a trabajar» dentro de una lista de acciones no es una despedida
        for p in partes:
            try:
                r = self._una(p)
            except Exception:                                                 # noqa  (nunca romper el turno: se delega)
                if os.environ.get("LCM_DEPURA"):
                    import traceback; traceback.print_exc()
                r = None
            if r is None:
                self._restaura(foto)
                return None
            if getattr(self, "_solo", False) and r.get("tipo") == "ack":
                for f in self.F:
                    if f.get("turno") == self.turno and not f.get("efecto"):
                        f["solo"] = True                  # «Solo hablo español»: lo que no esté dicho, no
            res.append(r)
        if len(res) == 1:
            out = res[0]
            if self._saludo_previo and out.get("tipo") == "ack" and not out["respuesta"].startswith(("Encantado", "¡")):
                out = dict(out); out["respuesta"] = self._saludo_previo + " " + out["respuesta"]
        else:
            # varias frases: se unen; las confirmaciones se resumen en una sola
            acks = [r for r in res if r.get("tipo") == "ack"]
            otros = [r for r in res if r.get("tipo") != "ack"]
            trozos = []
            if acks:
                cuerpo = [re.sub(r"^(?:Entendido|De acuerdo|Anotado|Vale)[:,]\s*", "", a["respuesta"]).rstrip(".") for a in acks]
                cuerpo = [c for c in cuerpo if c]
                sabidos = [c for c in cuerpo if re.match(r"^Sí, (?:eso )?ya (?:me lo habías dicho|lo sabía)", c)]
                if sabidos and len(sabidos) == len(cuerpo):
                    cuerpo = []
                    trozos.append("Sí, eso ya me lo habías dicho.")
                else:
                    cuerpo = [c for c in cuerpo if c not in sabidos]
                if cuerpo:
                  trozos.append(("Entendido: " + "; ".join(c[:1].lower() + c[1:] if not c[:1].isupper() or c.split()[0].lower() in ("tu", "tus", "te", "a", "el", "la", "los", "las", "antes", "eres", "vives", "tienes", "estás") else c for c in cuerpo) + ".") if cuerpo else "Entendido.")
            trozos.extend(r["respuesta"] for r in otros)
            est = "ok" if all(r.get("estado") == "ok" for r in res) else next(r["estado"] for r in res if r.get("estado") != "ok")
            if self._saludo_previo:
                trozos.insert(0, self._saludo_previo)
            nombres = [a["respuesta"] for a in acks if a["respuesta"].startswith("Encantado")]
            if nombres:
                trozos = [nombres[0]] + [t for t in trozos if not t.startswith("¡Hola")]
                trozos = [t.replace("Entendido: encantado, " + self.usuario.get("nombre", "") + "; ", "Entendido: ").replace("Entendido: encantado, " + self.usuario.get("nombre", "") + ".", "").replace("Encantado, " + self.usuario.get("nombre", "") + "; ", "") for t in trozos]
                trozos = [t for t in trozos if t.strip()]
                trozos = list(dict.fromkeys(trozos))
            out = {"respuesta": " ".join(trozos), "estado": est, "consultar": False}
        self.guardar()
        return out

    def _parte_clausulas(self, p):
        """«Soy Marcos y vivo en Madrid» -> dos cláusulas, si cada lado tiene su propio verbo conjugado."""
        T = G.tokens(self.parser, p)
        if not T:
            return [p]
        cortes = []
        for k, t in enumerate(T):
            if t.n in ("y", "e", "pero") and 0 < k < len(T) - 1:
                izq, der = T[:k], T[k + 1:]
                d0 = 0
                while d0 < len(der) and (der[d0].n in G.NEG or der[d0].n in G.CLIT or der[d0].n in ("tambien", "ademas", "ya", "ahora", "luego", "despues", "yo", "hoy", "mañana", "ayer", "siempre", "nunca")):
                    d0 += 1
                vi = next((x for i_, x in enumerate(izq) if G._es_verbo_finito(x, izq, i_)), None)
                def _pers(x):
                    return {c[2] for c in M.analizar(x.f, x.lem) if c[1] in ("pres", "pret", "imp", "fut")}
                if d0 < len(der) and vi is not None and len(der) - d0 >= 2 and G._es_verbo_finito(der[d0], der[d0:], 0) and (der[d0].pos in ("VERB", "AUX") or (_pers(vi) & _pers(der[d0]) & {"1s", "1p"})):
                    cortes.append(k)
                elif any(G._es_verbo_finito(x, izq, i_) for i_, x in enumerate(izq)):
                    rs = G.sn(der, d0) if d0 < len(der) else None
                    if rs and rs[1] < len(der) and (G._es_verbo_finito(der[rs[1]], der, rs[1]) or der[rs[1]].n in G.NEG or der[rs[1]].n in G.CLIT) and der[rs[1]].pos in ("VERB", "AUX", "ADV", "PRON"):
                        cortes.append(k)
        if not cortes:
            return [p]
        # se reconstruye sobre el texto original cortando en la conjunción correspondiente
        trozos, resto = [], p
        for _ in cortes:
            m = re.search(r"\s*,?\s+(?:y|e|pero)\s+", resto)
            cand = None
            for m in re.finditer(r"\s*,?\s+(?:y|e|pero)\s+", resto):
                izq = resto[:m.start()]; der = resto[m.end():]
                Ti, Td = G.tokens(self.parser, izq), G.tokens(self.parser, der)
                if Ti and Td and len(Td) >= 2 and any(G._es_verbo_finito(x, Ti, i_) for i_, x in enumerate(Ti)) and any(G._es_verbo_finito(x, Td, i_) and i_ < 5 for i_, x in enumerate(Td)):
                    cand = m
                    break
            if cand is None:
                break
            trozos.append(resto[:cand.start()].strip())
            resto = resto[cand.end():].strip()
            resto = resto[:1].upper() + resto[1:]
        trozos.append(resto)
        return [t for t in trozos if t]

    def _pendiente(self, p, n):
        """Respuesta a una aclaración pedida por el núcleo («¿la anterior o la nueva?»)."""
        pd = getattr(self, "pend", None)
        if not pd:
            return None
        self.pend = None
        if pd["turno"] < self.turno - 1:
            return None
        nuevo, viejo = pd["nuevo"], pd["viejo"]
        if re.match(r"^(?:la |lo |el )?(?:anterior|primera|primero|de antes|vieja|que te dije antes|que dije antes|antigua)\b", n) or re.match(r"^(?:no ha cambiado|sigue igual|no|ninguna|olvida(?:lo)?|la de antes)$", n):
            self.ult_just = {"dicho": [viejo["src"]]}
            return self._ok(f"De acuerdo, me quedo con la anterior: {self.frase(viejo)}.", tipo="ack")
        if re.match(r"^(?:la |lo |el )?(?:nueva|nuevo|ultima|ultimo|segunda|segundo|de ahora|que acabo de decir)\b", n) or re.match(r"^(?:ha cambiado|ahora|si|cambio|ya no|la de ahora|actualizalo|actualiza)\b", n):
            viejo["vig"] = False
            self._espejo(viejo, quitar=True)
            self.F.append(nuevo); self._espejo(nuevo)
            self.ult_marco = nuevo
            self.ult_just = {"dicho": [nuevo["src"]]}
            return self._ok(f"De acuerdo, lo actualizo: {self.frase(nuevo)}.", tipo="ack")
        # otra cosa: por defecto vale lo último dicho, y el turno sigue su curso
        viejo["vig"] = False
        self._espejo(viejo, quitar=True)
        self.F.append(nuevo); self._espejo(nuevo)
        return None

    def _foto(self):
        return copy.deepcopy((self.E, self.R, self.F, self.eq, self.turno, self.menc, self.ult_suj, self.ult_nuevo, self.ult_preg, self.ult_just, self.usuario, self.ult_marco, getattr(self, "pend", None)))

    def _restaura(self, f):
        (self.E, self.R, self.F, self.eq, self.turno, self.menc, self.ult_suj, self.ult_nuevo, self.ult_preg, self.ult_just, self.usuario, self.ult_marco, self.pend) = f

    def _una(self, p: str) -> Optional[dict]:
        from . import social, conceptos
        # «un loro llamado Paco» = «un loro que se llama Paco»; «no bebo ni vino ni cerveza» = «no bebo vino y cerveza»
        p = re.sub(r"^(\s*¿?\s*(?:\w+\s+){0,3}?(?:[Nn]o|[Nn]unca|[Jj]amás)\s+(?:\w+\s+){1,3}?)ni\s+(.+?)\s+ni\s+", r"\1\2 y ", p)
        n = re.sub(r"\s+", " ", re.sub(r"\s*[¿¡]\s*", " ", sa(p))).strip(" .!¡¿?")
        if not n:
            return None
        mo = re.match(r"^(?:olvida|olvidate de|borra|quita)(?: todo)? lo (?:de|que te he dicho de|que te dije de|sobre) (.+)$", n)
        if mo and not ("?" in p or "¿" in p):
            clave = coloquial.lemas(mo.group(1))
            borrar = [f for f in self.F if clave and clave <= coloquial.lemas(f.get("src", "") + " " + self.frase(f))]
            for f in borrar:
                self._espejo(f, quitar=True)
            self.F = [f for f in self.F if not any(f is b for b in borrar)]
            antes_n = len(getattr(self, "notas", []))
            self.notas = [x for x in getattr(self, "notas", []) if not (clave <= set(x["l"]))]
            k = len(borrar) + antes_n - len(self.notas)
            self.guardar()
            if not k:
                return {"respuesta": f"No tenía nada guardado sobre {mo.group(1)}.", "estado": "ok", "consultar": False, "tipo": "ack"}
            return self._ok(f"Hecho: he olvidado lo que me contaste de {mo.group(1)}.", tipo="ack")
        if _ORDEN.match(n) or p.isupper():
            return None
        try:
            from src.vision.concept_alignment import color_solicitado
            if color_solicitado(p) and not re.search(r"\b(?:es|son|era|eran|esta|estan|sera|seran|fue|fueron)\b", n):
                return None                              # «Muéstrame el verde»: la muestra la genera la capa de visión
        except Exception:                                # noqa
            pass
        rv = vista.colores_que_veo(n)
        if rv is not None:
            return rv
        if getattr(self, "vista", None) is None and ("?" in p or "¿" in p) and re.search(r"\b(?:la|esta|esa) (?:foto|imagen|figura|fotografia)\b|^(?:y )?que ves\b|^que hay en la (?:foto|imagen)", n):
            return {"respuesta": "Todavía no me has enseñado ninguna imagen, así que no puedo decirte qué hay en ella.", "estado": "abst", "consultar": False, "tipo": "abst"}
        if getattr(self, "vista", None) is None and re.search(r"\b(?:de|del) (?:este|ese) (?:mismo )?(?:color|tono)\b|\b(?:tienen?|son|es) (?:este|ese) color\b", n):
            return {"respuesta": "No sé de qué color me hablas: no he visto ninguna imagen. Si me la enseñas, te digo el color.", "estado": "abst", "consultar": False, "tipo": "abst"}
        if getattr(self, "vista", None) is not None:
            p2 = vista.reescribe(self, p)
            if p2 != p:
                p = p2; n = sa(p).strip(" .!¡¿?")
            rv = vista.responder(self, p, n, "?" in p or "¿" in p)
            if rv is not None:
                return rv
        self._gq_txt = ""
        if re.search(r"\b(?:hijos?|hermanos?|nietos?|sobrinos?|primos?|tios?) var(?:on|ones)\b", n):
            self._gq_txt = "m"                       # «¿Tengo algún hijo varón?»
            p = re.sub(r"\s+var[oó]n(?:es)?\b", "", p, flags=re.I); n = sa(p).strip(" .!¡¿?")
        mq = re.match(r"^(?:y )?que te (?:he|habia) (?:dicho|contado) (?:de|sobre|acerca de) (.+)$", n)
        if mq and ("?" in p or "¿" in p):
            resto_o = " ".join(p.strip(" ¿?").split()[-len(mq.group(1).split()):])
            r2 = self._una("¿Qué sabes de " + resto_o + "?")
            if r2 is not None and r2.get("estado") == "ok":
                return r2
            clave = coloquial.lemas(resto_o)
            citas = [f["src"] for f in self.F if f.get("src") and clave & coloquial.lemas(f["src"]) and f.get("vig", True) and not f.get("erroneo")]
            citas += [x["t"] for x in getattr(self, "notas", []) if clave & set(x["l"])]
            citas = list(dict.fromkeys(c.strip().rstrip(".") for c in citas))
            if clave and citas:
                return self._ok("Me dijiste: " + self._lista([f"«{c}»" for c in citas[-3:]]) + ".")
            if r2 is not None:
                return r2
        ms_ = re.match(r"^(?:en (?:mi|la|el|nuestro|nuestra) ([a-zñ ]+?) )?somos (?:solo |solamente |unos |unas |como |casi )?(\d+|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|quince|veinte)(?: (personas|hermanos|amigos|compañeros|primos|vecinos|socios|[a-zñ]+s))?(?: en (?:mi|la|el|nuestro|nuestra) ([a-zñ ]+?))?(?:[:,] .+)?$", n)
        if ms_ and not ("?" in p or "¿" in p):
            num = M.numero(ms_.group(2))
            donde = (ms_.group(1) or ms_.group(4) or getattr(self, "_ult_ambito", "") or "").strip()
            if not donde and self.ult_marco:
                for p_, e_, d_ in self.ult_marco.get("comps", []):
                    if p_ == "en" and d_:
                        donde = re.sub(r"^(?:un|una|el|la|mi|nuestra|nuestro)\s+", "", sa(d_)).split(" ")[0]
            self.somos = [x for x in getattr(self, "somos", []) if x["donde"] != donde] + [{"n": int(num), "que": ms_.group(3) or "personas", "donde": donde, "src": p}]
            self.ult_just = {"dicho": [p]}
            return self._ok(f"Entendido: sois {M.num_pal(int(num)) if int(num) < 30 else int(num)}{' ' + ms_.group(3) if ms_.group(3) else ''}{' en ' + ('la ' if M.genero_sust(donde) == 'f' else 'el ') + donde if donde else ''}, contándote a ti.", tipo="ack")
        ms_ = re.match(r"^(?:y )?cuant[oa]s (?:(personas|[a-zñ]+s) )?(?:somos|sois|hay)(?: en (?:mi|la|el|nuestro|nuestra|tu) ([a-zñ ]+))?$", n)
        if ms_ and getattr(self, "somos", None):
            d_ = (ms_.group(2) or "").strip()
            cs = [x for x in self.somos if not d_ or x["donde"] == d_ or d_.startswith(x["donde"]) and x["donde"]]
            if cs:
                x = cs[-1]
                self.ult_just = {"dicho": [x["src"]]}
                return self._ok(f"Sois {M.num_pal(x['n']) if x['n'] < 30 else x['n']}{' ' + x['que'] if x['que'] != 'personas' or True else ''}{' en ' + ('la ' if M.genero_sust(x['donde']) == 'f' else 'el ') + x['donde'] if x['donde'] else ''}.")
        if coloquial.lemas(p) & {"llover", "nevar", "granizar", "tronar", "diluviar"} or re.search(
                r"^(?:y )?que tiempo (?:hace|hizo|hara|hacia|hacía|ha hecho|va a hacer)\b|\b(?:hace|hizo|hacia|hara|ha hecho|hacía|hará)\s+(?:muchisimo |mucho |muy |un |una |bastante |demasiado )?(?:mas |menos )?(?:frio|calor|sol|viento|bueno|buen tiempo|mal tiempo|fresco|niebla|humedad|bochorno|un dia precioso|un dia horrible)\b", n):
            # el tiempo no tiene sujeto: se guarda tal cual lo dice la persona y se cita si pregunta
            if "?" in p or "¿" in p:
                cita = coloquial.recuerda(self, p)
                if not cita and re.search(r"\btiempo\b", n):   # «¿Qué tiempo hizo?»: la última nota sobre el tiempo
                    tn = [x for x in getattr(self, "notas", []) if coloquial.lemas(x["t"]) & {"llover", "nevar", "granizar", "tronar", "diluviar"}
                          or re.search(r"\b(?:frio|calor|sol|viento|niebla|bochorno|buen tiempo|mal tiempo|fresco|humedad)\b", sa(x["t"]).lower())]
                    cita = tn[-1]["t"] if tn else None
                if cita:
                    return self._ok(f"Me dijiste: «{cita.rstrip('.')}».")
                return {"respuesta": "No lo sé: no tengo datos del tiempo, solo lo que tú me cuentes.", "estado": "abst", "consultar": False, "tipo": "abst"}
            if coloquial.anota(self, p):
                return self._ok(f"Vale, lo apunto: «{p.strip().rstrip('.')}».", tipo="ack")
        r = self._yo_dije(p, n)
        if r is not None:
            return r
        r = self._deseo(p, n)
        if r is not None:
            return r
        r = self._dicho(p, n)
        if r is not None:
            return r
        if not ("?" in p or "¿" in p):
            for mm_ in re.finditer(r"\b(?:mi|mis)\s+([a-záéíóúñ]+)\b", p, re.I):
                w_ = sa(mm_.group(1))
                if (w_ in REL_CANON or w_ in FAMILIA or sa(M.singular(w_)) in FAMILIA) and len(p.split()) > 4:
                    self._menc_frase = getattr(self, "_menc_frase", []) + [mm_.group(0)]
        r = self._nadie(p, n)
        if r is not None:
            return r
        mq = re.match(r"^(algun[oa]s|ciert[oa]s|much[oa]s|poc[oa]s|casi tod[oa]s l[oa]s|la mayoria de l[oa]s|la mayor parte de l[oa]s|no tod[oa]s l[oa]s|vari[oa]s) ([a-zñ]+) (.+)$", n)
        if mq and not ("?" in p or "¿" in p) and not getattr(self, "_en_parcial", False):
            fem = mq.group(1).split()[-1].endswith("as") or mq.group(1) in ("algunas", "ciertas", "muchas", "pocas", "varias")
            resto_o = " ".join(p.strip(" .!").split()[len(mq.group(1).split()):])
            self._en_parcial = True
            try:
                r = self._una(("Las " if fem else "Los ") + resto_o + ".")
            finally:
                self._en_parcial = False
            fs = [f for f in self.F if f.get("turno") == self.turno and str(f.get("s", "")).startswith("K:")]
            if r is not None and r.get("estado") == "ok" and fs:
                cu = p.strip(" .!").split()[:len(mq.group(1).split())]
                for f in fs:
                    f["parcial"] = " ".join(cu).lower(); f["src"] = p
                    self._espejo(f, quitar=True)
                self.ult_just = {"dicho": [p]}
                self.guardar()
                return self._ok("Entendido: " + p.strip(" .!")[:1].lower() + p.strip(" .!")[1:] + ". No lo tomaré como regla para todos.", tipo="ack")
            if r is not None and fs:
                return r
        mn = re.match(r"^(?:no|perdona|perdon|me he equivocado|me equivoque|mejor dicho|quiero decir)(?:[,:; ]+(?:perdona|perdon|me he equivocado|me equivoque))?[,:; ]+(?:en realidad )?(tiene|tienes|mide|pesa|cuesta|son|eran) (\d+)$", n)
        if mn and self.ult_marco is not None and self.ult_marco.get("cuant") is not None and self.ult_marco.get("v") == M.analizar(mn.group(1))[0][0]:
            f0 = self.ult_marco
            viejo = f0["cuant"]
            txt = self.frase(dict(f0, obj_disp=re.sub(r"^\S+", mn.group(2), f0.get("obj_disp") or "") if f0.get("obj_disp") else ""))
            if str(int(viejo) if viejo == int(viejo) else viejo) in txt.split() or mn.group(2) in txt.split():
                r = self._una("No, " + txt + ".")
                if r is not None:
                    return r
        r = self._corrige_quien(p, n)
        if r is not None:
            return r
        mr = re.match(r"^(?:(?:no|perdona|perdon|me he equivocado|me equivoque|mejor dicho|quiero decir)(?:[, ]+(?:perdona|perdon))?[, ]+)?(?:no se llama ([a-zñ]+)[, ]+)?(?:sino )?(?:que )?se llama ([a-zñ]+)$", n)
        if mr and (mr.group(1) or re.match(r"^(?:no|perdona|perdon|me he equivocado|me equivoque|mejor dicho|quiero decir)\b", n)):
            r = self._renombra(mr.group(1), p.strip(" .!¡¿?").split()[-1], p)
            if r is not None:
                return r
        if n in ("ey", "hey", "ei", "epa", "holi", "holaa", "holaaa", "wenas"):   # «hola»/«buenas» los lleva el diálogo de base (sabe si se habla de usted)
            nom = self.usuario.get("nombre")
            return self._ok(f"¡Hola{', ' + nom if nom else ''}! ¿Qué tal?", tipo="social")
        if len(n.split()) == 1 and not ("?" in p or "¿" in p) and not re.match(r"^(?:ja|je|ji){2,}\w*$|^jaja\w*$", n):
            return None                      # una sola palabra («Vale», «Gracias», «Sí»): la lleva el diálogo de base, que conoce su contexto
        m_en2 = re.match(r"^(?:lo |el )?(?:contrario|opuesto) (?:de|del|de la|de lo) ([a-zñ]+) es (?:el |la |lo )?([a-zñ]+)$", n.strip(" .!"))
        if m_en2 and "?" not in p:                       # 2.16: «lo contrario de fleco es brumo» (el mismo hecho dicho en el otro orden)
            orig_ = {sa(w.lower()): w.lower() for w in re.findall(r"[\wáéíóúñü]+", p)}
            a_, b_ = orig_.get(m_en2.group(2), m_en2.group(2)), orig_.get(m_en2.group(1), m_en2.group(1))
            ant_u = self.usuario.setdefault("ant", {})
            ant_u.setdefault(a_, []).insert(0, b_); ant_u.setdefault(b_, []).insert(0, a_)
            self.turno += 1
            return self._ok(f"Entendido: lo contrario de {b_} es {a_}.", tipo="ack")
        m_sg = re.match(r"^(?:la palabra |el verbo |decir )?([a-zñ]+) (?:significa|quiere decir|es lo mismo que|es sinonimo de|es otra forma de decir) (.+)$", n.strip(" .!"))
        if m_sg and "?" not in p and m_sg.group(1) not in ("eso", "esto", "que", "no"):
            self.usuario.setdefault("significa", {})[m_sg.group(1)] = m_sg.group(2).strip()
            self.turno += 1
            self.ult_just = {"dicho": [p.strip()]}
            return self._ok(f"Entendido: «{m_sg.group(1)}» significa {m_sg.group(2).strip()}.", tipo="ack")
        m_sq = re.match(r"^(?:y )?que (?:significa|quiere decir|es eso de) (?:la palabra |el verbo )?([a-zñ]+)$", n.strip(" ?¿.!"))
        if m_sq and m_sq.group(1) in (self.usuario.get("significa") or {}):
            self.turno += 1
            self.ult_just = {"dicho": [f"{m_sq.group(1)} significa {self.usuario['significa'][m_sq.group(1)]}"]}
            return self._ok(f"«{m_sq.group(1)}» significa {self.usuario['significa'][m_sq.group(1)]}: me lo enseñaste tú.")
        m_pt = re.match(r"^((?:un|una|el|la|los|las) [a-zñ]+) tienen? (?:[a-zñ0-9]+ )?partes?\s*:?\s+(.+)$", n.strip(" .!"))
        if m_pt and "?" not in p and len(re.split(r",| y ", m_pt.group(2))) >= 2:
            cosa = sa(M.singular(m_pt.group(1).split()[1]))
            ps_ = [re.sub(r"^(?:el|la|los|las|un|una)\s+", "", x.strip()) for x in re.split(r"\s*,\s*|\s+y\s+", m_pt.group(2)) if x.strip()]
            self.usuario.setdefault("partes", {})[cosa] = ps_
            try:
                self._una(f"{m_pt.group(1)[:1].upper() + m_pt.group(1)[1:]} tiene {self._lista(ps_)}.")   # además, como hechos normales («¿un trebo tiene rueda?»)
            except Exception:                            # noqa
                pass
            self.ult_just = {"dicho": [p.strip()]}
            return self._ok(f"Entendido: {m_pt.group(1)} tiene {len(ps_)} partes: {self._lista(ps_)}.", tipo="ack")
        m_pp = re.match(r"^(?:y )?(?:un|una|el|la|los|las) ([a-zñ]+) tienen? (?:un |una |el |la |los |las )?([a-zñ]+)$", n.strip(" ?¿.!"))
        if m_pp and ("?" in p or "¿" in p) and sa(M.singular(m_pp.group(1))) in (self.usuario.get("partes") or {}):
            cosa = sa(M.singular(m_pp.group(1)))
            ps_ = self.usuario["partes"][cosa]
            self.turno += 1
            self.ult_just = {"dicho": [f"{cosa}: {', '.join(ps_)}"]}
            if sa(M.singular(m_pp.group(2))) in {sa(M.singular(x.split()[-1])) for x in ps_}:
                return self._ok(f"Sí: me dijiste que tiene {self._lista(ps_)}.")
            return self._abst(f"No me consta: de sus partes solo me dijiste {self._lista(ps_)}.")
        m_pq = re.match(r"^(?:y )?(?:que|cuales son las) partes (?:tienen?|de) (?:un|una|el|la|los|las) ([a-zñ]+)$", n.strip(" ?¿.!"))
        if m_pq and sa(M.singular(m_pq.group(1))) in (self.usuario.get("partes") or {}):
            cosa = sa(M.singular(m_pq.group(1)))
            self.turno += 1
            self.ult_just = {"dicho": [f"{cosa}: {', '.join(self.usuario['partes'][cosa])}"]}
            return self._ok(f"{self._lista(self.usuario['partes'][cosa]).capitalize()}: me lo enseñaste tú.")
        m_en = re.match(r"^(?:el |la |lo |los |las )?([a-zñ]+) es (?:lo |el )?(?:contrario|opuesto) (?:de|del|de la|de lo) ([a-zñ]+)$", n.strip(" .!"))
        if m_en and "?" not in p:                        # 2.14: «el frío es lo contrario del calor»: lo enseña la persona
            orig_ = {sa(w.lower()): w.lower() for w in re.findall(r"[\wáéíóúñü]+", p)}
            a_, b_ = orig_.get(m_en.group(1), m_en.group(1)), orig_.get(m_en.group(2), m_en.group(2))
            ant_u = self.usuario.setdefault("ant", {})
            ant_u.setdefault(a_, []).append(b_); ant_u.setdefault(b_, []).append(a_)
            self.turno += 1
            return self._ok(f"Entendido: lo contrario de {b_} es {a_}.", tipo="ack")
        if "?" not in p and "¿" not in p and re.search(r"\b(?:sirven?|usan?|utilizan?|valen?) para\b|\bhech[oa]s? de\b|\bsuelen? (?:estar|encontrarse)\b|\bse (?:suelen? )?guardan? en\b", n):
            from . import relaciones                     # 2.16: la persona enseña una relación («una pinfa sirve para doblar alambre»)
            r_ap = relaciones.aprender(self, p, n)
            if r_ap is not None:
                self.turno += 1
                return self._ok(r_ap, tipo="ack")
        if "?" in p or "¿" in p:                         # 2.15: relaciones entre conceptos (función, material, lugar, usuario), en los dos sentidos
            from . import relaciones
            r_rel = relaciones.responder(self, p, n)
            if r_rel is None and not any(w in n.split() for w in ("mi", "mis", "tu", "tus", "su", "sus")):
                r_rel = relaciones.tamano_y_habitat(self, n)
            if r_rel is not None:
                self.turno += 1
                return r_rel if isinstance(r_rel, dict) else self._ok(r_rel)
        m_ct = conceptos._CONTR.match(n.strip(" ?¿"))
        if m_ct and ("?" in p or "¿" in p or n.startswith(("dime", "sabes"))):
            # 2.14: «¿qué es lo contrario de X?» es una pregunta, no una enseñanza: la contesta la base de conceptos
            x = m_ct.group(1)
            ant_u = {sa(k_): v_ for k_, v_ in (self.usuario.get("ant") or {}).items()}
            if x in ant_u:
                self.ult_just = {"dicho": [f"{ant_u[x][0]} es lo contrario de {x}"]}
                return self._ok(f"Lo contrario de {conceptos.forma(x) if x in conceptos.kb()['forma'] else x} es {ant_u[x][0]}: me lo enseñaste tú.")
            if False:
                self.ult_just = {"dicho": [f"{self.usuario['ant'][x][0]} es lo contrario de {x}"]}
                return self._ok(f"Lo contrario de {x} es {self.usuario['ant'][x][0]}: me lo enseñaste tú.")
            if x in conceptos.kb()["ant"]:
                return self._ok(conceptos.responder(self, p, n.strip(" ?¿"), True))
            x_d = next((w for w in re.findall(r"[\wáéíóúñü]+", p.lower()) if sa(w) == x), x)
            ants = [] if conceptos._kb_clase(x) else conceptos.antonimos_lexico(x)   # «médico» es un oficio: el antónimo del adjetivo no vale
            if ants:
                self.ult_just = {"pasos": [f"en mi léxico, «{ants[0]}» es antónimo de «{x}»"], "fabrica": True}
                return self._ok(f"Según mi léxico, lo contrario de {x_d} es {' o '.join(ants[:2])}.")
            return self._abst(f"No lo sé: no tengo anotado el contrario de «{x_d}».")
        if _DELEGA.search(n):
            return None
        pend = self._pendiente(p, n)
        if pend is not None:
            return pend
        # perífrasis de relativo: «¿Quién es el que compra leche?» = «¿Quién compra leche?»; «¿Qué es lo que compra Ana?» = «¿Qué compra Ana?»
        mc = re.match(r"^(\s*¿?\s*(?:y\s+)?(?:(?:a|de|con|en|para|por)\s+)?(?:qui[eé]n(?:es)?|qu[eé]|d[oó]nde|c[oó]mo|cu[aá]ndo))\s+(?:es|son|fue|era)\s+(?:el|la|lo|los|las)\s+que\s+(.+)$", p, re.I) \
            or re.match(r"^(\s*¿?\s*(?:y\s+)?(?:d[oó]nde|c[oó]mo|cu[aá]ndo))\s+(?:es|fue|era)\s+(?:donde|como|cuando|que)\s+(.+)$", p, re.I)
        if mc:
            return self._una(mc.group(1) + " " + mc.group(2))
        if re.match(r"^(?:sabes|adivina|a que no sabes) (?:que|lo que) (?:me ha pasado|me paso|ha pasado|paso|me han dicho|ha ocurrido)(?: hoy| ayer| esta mañana| esta tarde)?$", n):
            return self._ok("No, cuéntame. ¿Qué ha pasado?", tipo="social")
        m = _INCRUSTA.match(n)
        if m and ("?" in p or "¿" in p or re.match(r"^(?:dime|cuentame|explicame)\b", n)):
            resto = m.group(2).strip()
            # se recupera el texto original (con acentos y mayúsculas) de esa parte
            k = len(p.rstrip(" ?.!")) - len(p.rstrip(" ?.!").split(None, len(n.split()) - len(resto.split()))[-1]) if resto else 0
            orig = p.strip(" ¿?.!").split(None, len(n.split()) - len(resto.split()))[-1] if resto else ""
            if orig:
                if re.match(r"^(?:a |de |con |en |para |por )?(?:que|quien|quienes|cual|cuales|donde|adonde|cuando|cuant[oa]s?|como)\b", resto) or m.group(1):
                    return self._una("¿" + orig[:1].upper() + orig[1:] + "?")
                T0 = G.tokens(self.parser, orig)
                r0 = G.sn_coord(T0, 0) if T0 else None
                if r0 and r0[1] == len(T0) and (r0[0].pos or r0[0].de is not None):
                    return self._una("¿Cuál es " + orig + "?")
        es_preg = "?" in p or "¿" in p or n.split()[0] in G.WH or re.match(r"^(?:y\s+)?(?:a|de|con|en|para|por|desde|hasta|sobre)\s+(?:que|quien|quienes|cual|donde|cuando|cuant[oa]s?)\b", n) is not None
        s = conceptos.responder(self, p, n, es_preg)
        if s is None:
            s = social.responder(self, p, n, es_preg)
        if s is not None:
            return s if isinstance(s, dict) else {"respuesta": s, "estado": "ok", "consultar": False, "tipo": "social"}
        if es_preg:
            return self.preguntar(p, n)
        return self.afirmar(p, n)

    def _corrige_quien(self, p, n):
        """«No, perdona, no era mi jefe, era mi jefa»: se cambia esa persona (o cosa) en lo que se acaba de contar."""
        m = re.match(r"^(?:(?:no|perdona|perdon|me he equivocado|me equivoque)[, ]+)*no (?:era|es|fue|eran|son|fueron) (.+?)[, ]+(?:sino |era |es |fue |eran |son |fueron )(?:que )?(.+)$", n)
        if not m or "?" in p:
            return None
        txt = p.strip(" .!¡")
        k_old = len(m.group(1).split()); k_new = len(m.group(2).split())
        palabras = re.sub(r"[,;]", " ", txt).split()
        new_t = " ".join(palabras[-k_new:])
        i_old = next((i for i in range(len(palabras)) if sa(" ".join(palabras[i:i + k_old]).lower()) == m.group(1)), None)
        if i_old is None:
            return None
        old_t = " ".join(palabras[i_old:i_old + k_old])
        e_old = self._sn_ent(old_t)
        if not e_old or e_old in ("U", "L"):
            return None
        recientes = [f for f in self.F if f.get("turno", -9) >= self.turno - 4 and f.get("vig", True) and (
            self.can(f.get("s") or "") == e_old or self.can(f.get("obj") or "") == e_old or any(self.can(c_[1] or "") == e_old for c_ in f.get("comps", [])))]
        if not recientes:
            return None
        sn_new = self._sn_de(new_t)
        if sn_new is None:
            return None
        cl_old = self.E.get(e_old, {}).get("clase")
        cl_new = self._clase_sn(sn_new)[0] if sn_new.cab else None
        if cl_new and cl_old and M.masc(cl_new) == M.masc(cl_old):
            self.E[e_old]["gen"] = M.genero_sust(sa(sn_new.cab)) or self.E[e_old].get("gen")   # «jefe» -> «jefa»: la misma persona, otro género
            e_new = e_old
        else:
            e_new = self.ent_de(sn_new)
            if not isinstance(e_new, str):
                return None
            for f in recientes:
                if self.can(f.get("s") or "") == e_old:
                    f["s"] = e_new
                if self.can(f.get("obj") or "") == e_old:
                    f["obj"] = e_new; f["obj_disp"] = new_t
                for c_ in f.get("comps", []):
                    if self.can(c_[1] or "") == e_old:
                        c_[1] = e_new; c_[2] = new_t
        self.mencionar(e_new)
        self.ult_just = {"dicho": [p]}
        return self._ok("Corregido: " + "; ".join(self.frase(f) for f in recientes[-2:]) + ".", tipo="ack")

    def _ok(self, txt, just=None, tipo="resp"):
        if just is not None:
            self.ult_just = just
        return {"respuesta": txt, "estado": "ok", "consultar": False, "tipo": tipo}

    def _abst(self, txt, consultar=False):
        self.ult_just = None
        if not consultar:
            try:
                d16 = getattr(self, "motor_d16", None)
                if self.mem.active_lessons() or (d16 is not None and getattr(d16(), "reglas", None)):
                    consultar = True
            except Exception:                                                 # noqa
                pass
        return {"respuesta": txt, "estado": "abst", "consultar": consultar, "tipo": "abst"}

    # ================================================================== afirmaciones
    def afirmar(self, p: str, n: str) -> Optional[dict]:
        self._p_txt = p
        self._suj_txt = ""
        corr = False
        m = _CORR.match(p)
        self._corr_error = bool(m and re.search(r"perd[oó]n|perdona|equivoc|confund|mejor dicho|quer[ií]a decir|quiero decir|me he liado|disculpa", m.group(0), re.I))
        if m and len(p) > m.end() + 3:
            p = p[m.end():]
            p = p[:1].upper() + p[1:]
            n = sa(p).strip(" .!")
            corr = True
        if _CREENCIA.search(n) or n.startswith(("si ", "ojala", "cuando ", "aunque ", "mientras ")):
            return None
        self._cuando_sub = ""
        mw_ = re.search(r"\s+(cuando|siempre que|cada vez que)\s+", p, re.I)
        if mw_ and not ("?" in p or "¿" in p) and mw_.start() > 0:
            self._cuando_sub = mw_.group(1).lower() + " " + coloquial.a_segunda(p[mw_.end():].strip(" .!"))
            p = p[:mw_.start()]
        self._finalidad = ""
        mf_ = re.search(r"\s+para que\s+", p, re.I)
        if mf_ and not ("?" in p or "¿" in p):
            self._finalidad = coloquial.a_segunda(p[mf_.end():].strip(" .!"))
            p = p[:mf_.start()]
        causa = ""
        mc = re.search(r"\s+porque\s+", p, re.I)
        if mc:
            causa = p[mc.end():].strip(" .!")
            p = p[:mc.start()]
        T = G.tokens(self.parser, p)
        if not T or len(T) > 24:
            return None
        ns = [t.n for t in T]
        for k, w in enumerate(ns):
            if w in ("que", "si", "cuando", "aunque", "mientras", "pero", "sino", "donde", "quien", "cual"):
                if w == "que" and k > 0 and (ns[k - 1] in ("tener", "tengo", "tienes", "tiene", "tenemos", "tienen", "tenia", "tuvo", "tuve", "hay") or any(x in ("mas", "menos", "mayor", "menor", "mejor", "peor") for x in ns[max(0, k - 3):k])):
                    continue
                return None
        C = G.clausula(T)
        resto_c = None
        if C is None:
            # «Ayer Carla cocinó paella para las tres»: si un complemento final impide el análisis, se guarda como texto
            for k_ in range(len(T) - 1, 1, -1):
                if T[k_].n in ("para", "con", "por", "sin", "desde", "hasta", "en", "a", "de") and k_ < len(T) - 1:
                    C = G.clausula(T[:k_])
                    if C is not None and C.v:
                        resto_c = (T[k_].n, " ".join(t.f for t in T[k_ + 1:]).strip(" .!"))
                        break
                    C = None
            if C is None:
                return None
            C.comps.append((resto_c[0], SN(cab="", texto=resto_c[1])))
        # «Se ha muerto el perro de mi vecina», «Llegó mi hermano»: con estos verbos el sintagma pospuesto es el sujeto
        if C.suj is None and C.obj is not None and C.pers in ("3s", "3p") and C.v in _INACUS and not C.obj.pron and not (C.refl and _CUERPO & {sa(C.obj.cab)}) and not C.clit[1:] and not ("me" in C.clit or "te" in C.clit):
            C.suj, C.obj = C.obj, None
            self._suj_txt = C.suj.texto if (C.suj.num not in (None, 1) or C.suj.cuant) else ""
        self.anota_palabras(T)
        if corr:
            C.marc.append("corr")
        r = self._interpreta(C, p.strip(), causa)
        return r

    def _ref_clitico(self, cl):
        """Referente de un «lo/la/los/las» sin objeto previo: lo último nombrado que concuerda (o la última persona mencionada)."""
        f_, pl_ = cl in ("la", "las"), cl in ("los", "las")
        e = self._ent_reciente(gen="f" if f_ else "m", pl=pl_, turnos=4)
        if e is None and not pl_:
            e = self.ref3(genero="f" if f_ else "m", persona=True)
        return e

    def _od_clitico(self, cl):
        """Texto (desde quien habla) de lo que señala un «lo/la/los/las» de objeto: lo último nombrado que concuerda."""
        pl_s, f_s = cl in ("los", "las"), cl in ("la", "las")
        um_s = self.ult_marco or {}
        for f_ in [um_s] + list(reversed(self.F[-8:])):
            if not f_ or not f_.get("obj_disp") or not f_.get("obj") or self.es_persona(f_["obj"]) or f_.get("dicho") or f_.get("turno", -9) < self.turno - 6:
                continue
            g_o = self.E.get(self.can(f_["obj"]), {}).get("gen") or M.genero_sust(sa((f_.get("obj_cls") or "").split()[0] if f_.get("obj_cls") else ""))
            if (g_o == "f") == f_s and bool(f_.get("pl_obj")) == pl_s and (f_.get("obj_cls") or "") not in ("año", "mes", "dia", "hora", "vez", "euro"):
                od = re.sub(r"^(?:un|una|unos|unas)\s+", lambda x: {"un": "el ", "una": "la ", "unos": "los ", "unas": "las "}[x.group(0).strip()], cambia_persona(f_["obj_disp"]))
                if not re.match(r"^(?:el|la|los|las|mi|mis|tu|tus|su|sus)\s", od):
                    od = (("las " if f_s else "los ") if pl_s else ("la " if f_s else "el ")) + od
                return od
        e_s = self._ent_reciente(gen="f" if f_s else "m", pl=pl_s, turnos=6, cosa=True)
        return cambia_persona(self.disp(e_s)) if e_s else None

    def _ent_reciente(self, gen=None, pl=None, turnos=4, cosa=False):
        """Lo último nombrado (persona, animal o cosa concreta) que concuerda en género y número con un pronombre."""
        for f in reversed(self.F[-14:]):
            if f.get("turno", -99) < self.turno - turnos:
                break
            for e in [f.get("obj")] + [c_[1] for c_ in f.get("comps", [])] + [f.get("s")]:
                if not e or e in ("U", "L") or e not in self.E:
                    continue
                if self.can(e).startswith("K:") and not (cosa and e == f.get("obj") and re.match(r"^(?:el|la|los|las)\s", f.get("obj_disp") or "")):
                    continue                            # «pintar la cocina»: una cosa concreta aunque no tenga dueño
                d = self.E[self.can(e)]
                if (d.get("clase") or "") in ("año", "mes", "dia", "hora", "euro", "vez") or (cosa and self.es_persona(self.can(e))):
                    continue
                g_ = d.get("gen") or self.gen(self.can(e))
                if gen and g_ and g_ != gen or pl is not None and bool(d.get("pl")) != pl:
                    continue
                return self.can(e)
        return None

    def _cosa_fisica(self, gen=None, pl=None, turnos=3):
        """Objeto físico nombrado hace poco (objeto o complemento de los últimos marcos), del más reciente al más antiguo."""
        for f in reversed(self.F[-12:]):
            if f.get("turno", -99) < self.turno - turnos:
                break
            for e in [f.get("obj")] + [c_[1] for c_ in f.get("comps", [])]:
                if not e or e in ("U", "L") or e not in self.E or self.es_persona(e):
                    continue
                d = self.E[e]; c = d.get("clase") or ""
                if not (c == "objeto" or "objeto" in conceptos.ancestros(c)):
                    continue
                if gen and d.get("gen") and d["gen"] != gen or pl is not None and bool(d.get("pl")) != pl:
                    continue
                return self.can(e)
        return None

    def _suj_implicito(self, C):
        if C.pers == "3s" and C.v == "tener" and C.obj is not None and (C.obj.cab or (C.obj.coord and C.obj.coord[0].cab)):
            cabs_ = [sa(M.singular(x.cab)) for x in (C.obj.coord or [C.obj]) if x.cab]
            cosa_r = self._ent_reciente(turnos=3, cosa=True)
            cl_r = self.E.get(cosa_r, {}).get("clase") if cosa_r else None
            partes_r = {sa(M.singular(x)) for x in conceptos.kb()["partes"].get(cl_r, [])} if cl_r else set()
            if cosa_r and cabs_ and all(c_ in _RASGOS or c_ in partes_r for c_ in cabs_) and (cl_r in _CON_RASGOS or partes_r):
                return cosa_r                           # «Pedro se ha comprado una casa. Tiene un jardín enorme»: la casa
        r = self._suj_implicito0(C)
        if C.v in _ANIMADOS and not C.refl and C.pers in ("3s", "3p") and isinstance(r, str) and r not in ("U", "L") and not self.es_persona(r):
            e_p = self.ref3(persona=True)               # «nos ha invitado a comer»: quien invita es una persona, no la casa
            if e_p:
                r = e_p
        if C.v == "llamar" and C.refl and C.pers == "3s" and isinstance(r, str) and r.startswith("I:") \
                and sa(self.E.get(self.can(r), {}).get("clase") or "") in _EVENTOS_SIN_NOMBRE:
            dn = self.can(self.E.get(self.can(r), {}).get("dueno") or "")
            if dn and dn not in ("U", "L") and self.es_persona(dn):
                r = dn                                  # «Mañana es el santo de mi abuela. Se llama Dolores»: la abuela, no el santo
        if C.pers == "3p" and isinstance(r, str) and r not in ("U", "L") and not self.E.get(self.can(r), {}).get("pl") \
                and not getattr(self, "_suj_txt", "") and not r.startswith(("G:", "K:")):
            return None                                 # «(Bilbao…) Pagan mejor»: un plural impersonal no es un lugar en singular
        return r

    def _suj_implicito0(self, C: Clausula):
        if C.pers in ("1s", "1p"):
            return "U"
        um0 = self.ult_marco or {}
        if C.v == "ser" and not C.attr and C.obj is None and (any(p_ == "en" for p_, _ in C.comps) or C.cuando) and not any(p_ == "de" for p_, _ in C.comps) \
                and C.pers in ("3s", "3p") and um0.get("turno", -9) >= self.turno - 2 and um0.get("turno") != self.turno:
            cands = [um0.get("obj")] + [c_[1] for c_ in um0.get("comps", [])]
            for x_ in cands:                             # «Estudio para las oposiciones. Son en marzo»: lo de lo que se habló
                if x_ and x_ not in ("U", "L") and not self.es_persona(x_):
                    pl_x = bool(self.E.get(self.can(x_), {}).get("pl")) or any(c_[1] == x_ and sa(c_[2] or "").split()[0] in ("los", "las", "mis", "tus", "unos", "unas") for c_ in um0.get("comps", []))
                    if pl_x == (C.pers == "3p"):
                        txt_x = [c_[2] for c_ in um0.get("comps", []) if c_[1] == x_ and c_[2]]
                        if pl_x and txt_x:
                            self._suj_txt = txt_x[0]          # «las oposiciones son…», no «la oposición es…»
                        return self.can(x_)
        um = self.ult_marco or {}
        if C.v in ("estar", "ser") and C.attr and C.pers == "3s" and um.get("obj") and um.get("turno", -9) >= self.turno - 2 and not self.es_persona(um["obj"]):
            ult_w = sa(re.sub(r"[^\wáéíóúñ ]", "", getattr(self, "_p_txt", "")).split()[-1]) if getattr(self, "_p_txt", "").strip() else sa(C.attr[0])
            g_adj = "f" if ult_w.endswith("a") else ("m" if ult_w.endswith("o") else "")
            _animo = {"cansado", "nervioso", "contento", "triste", "enfadado", "feliz", "agobiado", "preocupado", "enfermo", "harto", "aburrido", "tranquilo", "emocionado", "orgulloso", "dormido", "despierto"}
            de_cosa = M.masc(sa(C.attr[0])) not in _animo
            if g_adj and g_adj == self.gen(um["obj"]) and (de_cosa or not um.get("s") or g_adj != self.gen(um["s"])):
                return self.can(um["obj"])              # «Carla cocinó paella. Estaba buenísima»: lo que estaba bueno es la paella
        if C.v == "llamar" and C.refl and C.amb1 and C.tiempo == "imp" and self.ult_nuevo:
            return self.can(self.ult_nuevo)            # «Se llamaba Toby» habla de lo recién nombrado, no de la persona
        if C.v == "llamar" and C.refl and C.amb1 and C.tiempo == "imp":
            for e_ in reversed(self.menc):
                e_ = self.can(e_)
                if e_ not in ("U", "L") and not e_.startswith("K:"):
                    return e_
        if C.amb1:
            if "me" in C.clit or (C.obj is not None and C.obj.pos == "U") or any(s_.pos == "U" for _, s_ in C.comps) or not (self.ult_suj and self.ult_suj != "U") \
                    or getattr(self, "_afirma_de", None) == "U":
                return "U"                              # lo último que CONTÓ la persona era sobre sí misma (las preguntas no cambian eso)
        if C.pers == "2s":
            return "L"
        if C.pers == "3p" and getattr(self, "ult_grupo", None) and C.v not in ("llamar",) and not (("me" in C.clit or "nos" in C.clit) and "U" in [self.can(x_) for x_ in self.ult_grupo]):
            return list(self.ult_grupo)                  # 2.17: «me han puesto…»: quien habla no puede ser a la vez el sujeto
        if C.v == "llamar" and C.refl:
            if self.ult_nuevo and self.can(self.ult_nuevo).startswith("I:"):
                return self.can(self.ult_nuevo)          # «Mi vecino tiene un loro. Se llama Paco»: el nombre es de lo recién presentado
            for e in reversed(self.menc):
                e = self.can(e)
                if e.startswith("I:"):
                    return e
            cand = self.ult_nuevo or self.ult_suj
            if cand and self.can(cand) in ("U", "L") and C.pers == "3s":
                return self.ref3(persona=True)           # «se llama Ernesto» (3.ª persona) nunca es la persona que habla
            return cand
        _animo2 = {"cansado", "nervioso", "contento", "triste", "enfadado", "feliz", "agobiado", "preocupado", "enfermo", "harto", "aburrido", "tranquilo", "emocionado", "orgulloso", "dormido", "despierto", "casado", "soltero"}
        if C.v in G.COPULAS and self.ult_nuevo and self.E.get(self.can(self.ult_nuevo), {}).get("t_nuevo") == self.turno - 1 and not self.es_persona(self.ult_nuevo) and "corr" not in C.marc \
                and not (C.attr and M.masc(sa(C.attr[0])) in _animo2):
            return self.can(self.ult_nuevo)
        if C.pers in ("3s", "3p") and (not self.ult_suj or self.can(self.ult_suj) in ("U", "L")):
            # 3.ª persona: no puede ser la persona que habla; es la última persona (o cosa) nombrada
            e3 = self.ref3(persona=True) if not (C.attr and not self.es_persona(self.ref3() or "U")) else self.ref3()
            if C.v in ("hacer", "funcionar", "sonar", "costar", "pesar", "medir", "tardar", "durar", "fallar", "gastar", "consumir", "arrancar", "pitar", "oler", "frenar", "calentar"):
                cosa = self._cosa_fisica(turnos=1)
                if cosa:
                    return cosa                        # «Tengo un problema con mi coche. Hace un ruido raro»: el coche
            return e3 or self.ref3()
        return self.can(self.ult_suj) if self.ult_suj else self.ref3()

    def olvida(self, texto):
        """«Olvida que Ana vive en Madrid» / «Olvida todo»: el grafo olvida lo mismo que la memoria clásica."""
        n = sa(texto).strip(" .!")
        if re.match(r"^(?:olvida(?:lo)? todo|olvidalo todo|borra todo|borra(?:lo)? todo lo que sabes|olvida todo lo que (?:te he dicho|sabes)|reinicia(?: la memoria)?|empieza de cero)$", n):
            self.olvidar_todo()
            return True
        m = re.match(r"^(?:olvida|borra|elimina|quita)\s+(?:que\s+|lo de que\s+)?(.+)$", texto.strip(" .!"), re.I)
        if not m:
            return False
        T = G.tokens(self.parser, m.group(1)[:1].upper() + m.group(1)[1:])
        C = G.clausula(T) if T else None
        if C is None:
            return False
        s = self.ent_de(C.suj, crear=False) if C.suj is not None else ("U" if C.pers == "1s" else None)
        if s is None or isinstance(s, list) or str(s).startswith("?"):
            return False
        s = self.can(s)
        if C.v == "ser" and C.obj is not None and (C.obj.de is not None or C.obj.pos):
            cl = self._clase_sn(C.obj)[0]
            antes = len(self.R)
            self.R = [q for q in self.R if not (q["r"] == cl and self.can(q["x"]) == s)]
            self.guardar()
            return len(self.R) < antes
        borrar = [f for f in self.F if f["v"] == C.v and self.can(f["s"]) == s and (not C.attr or set(C.attr) & set(f.get("attr", []))) and self._coincide_obj(f, C.obj) and self._coincide_comps(f, C.comps)]
        for f in borrar:
            self._espejo(f, quitar=True)
        self.F = [f for f in self.F if not any(f is b for b in borrar)]
        self.guardar()
        return bool(borrar)

    def turno_delegado(self, texto, es_pregunta):
        """Las capas anteriores llevaron el turno: el núcleo actualiza su foco con los nombres que conoce o lo deja en blanco."""
        self.ult_dicho = texto if not es_pregunta else getattr(self, "ult_dicho", "")
        vistos = []
        for w in re.findall(r"[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+", texto):
            k = "N:" + sa(w)
            if k in self.E or k in self.eq:
                vistos.append(self.can(k))
        if vistos:
            for e in vistos:
                self.mencionar(e)
            self.ult_suj = vistos[0]
        elif not es_pregunta:
            self.ult_suj = None
            self.foco_ajeno = True
        self.ult_nuevo = None

    def _aclara(self):
        return {"respuesta": "No tengo claro de quién hablas. ¿A quién te refieres?", "estado": "aclara", "consultar": False, "tipo": "aclara"}

    def _interpreta(self, C: Clausula, src: str, causa: str) -> Optional[dict]:
        v = C.v
        nuevos, notas = [], []
        if not G.resuelve_elipsis(C):
            return None
        if C.pers == "1p" and C.tiempo == "pres" and not C.cuando and not C.freq:
            # «visitamos la Alhambra» (presente y pretérito son iguales): si se está contando algo pasado, es pasado
            ambiguo = any(any(x == (v, "pret", "1p") for x in M.analizar(sa(w))) for w in src.split()[:4])
            prev = [f for f in self.F if f.get("turno", -9) >= self.turno - 3 and self.can(f.get("s") or "") == "U" and not f.get("dicho")]
            if ambiguo and prev and any(f_.get("t") in ("pret", "imp") for f_ in prev[-2:]):
                C.tiempo = "pret"
        # «Vinieron mis abuelos», «Llegó Ana»: sujeto pospuesto con verbos de movimiento o suceso
        if C.suj is None and C.pers in ("3s", "3p") and C.obj is not None and C.obj2 is None and v in ("venir", "llegar", "salir", "entrar", "nacer", "morir", "faltar", "aparecer", "volver", "ir", "pasar", "ocurrir") and not C.clit:
            C.suj, C.obj = C.obj, None
            self._suj_txt = C.suj.texto if (C.suj.num not in (None, 1) or C.suj.cuant) else ""
        # existencia: «En mi calle hay tres bares», «Hay un sofá en el salón»
        if v == "haber" and C.suj is None and C.obj is not None and C.comps:
            return self._hay(C, src)
        # ---------- verbos de afecto: «a Ana le gusta X», «me encanta X»
        dat_ev = G.dativo_ev(C)
        if (v in G.GUSTAR and (C.clit or C.dat)) or dat_ev:
            exp = None
            if dat_ev and C.dat is None and ("me" in C.clit or "nos" in C.clit):
                exp = "U"                               # «se me cayó al suelo»: «al suelo» es un lugar, no a quién le pasa
            elif C.dat is not None:
                exp = self.ent_de(C.dat)
            elif any(p_ == "a" for p_, _ in C.comps):
                sn_a = [s_ for p_, s_ in C.comps if p_ == "a"][0]
                exp = self.ent_de(sn_a)
                C.comps = [(p_, s_) for p_, s_ in C.comps if p_ != "a"]
            elif "me" in C.clit or "nos" in C.clit:
                exp = "U"
            elif "te" in C.clit:
                return None
            elif "le" in C.clit or "les" in C.clit:
                exp = self.ult_suj if (self.ult_suj and self.can(self.ult_suj) not in ("U", "L")) else None
                if exp is None:                         # «le encantan los libros»: «le» nunca es quien habla
                    for f_l in reversed(self.F[-6:]):
                        for x_ in [c_[1] for c_ in f_l.get("comps", [])] + [f_l.get("obj"), f_l.get("s")]:
                            if x_ and self.can(x_) not in ("U", "L") and self.es_persona(x_) and bool(self.E.get(self.can(x_), {}).get("pl")) == ("les" in C.clit):
                                exp = self.can(x_); break
                        if exp:
                            break
                exp = exp or self.ref3(persona=True)
                if exp is None:
                    return self._aclara()
            if exp is None or (C.comps and not dat_ev):
                return None
            est = C.obj or C.suj
            exps = exp if isinstance(exp, list) else [exp]
            ests = (est.coord if est is not None and est.coord else [est]) if est is not None else [None]
            if est is None and not C.xinf:
                um = self.ult_marco
                if um is not None and um.get("obj") and um["turno"] >= self.turno - 2:
                    for e in exps:
                        nuevos.append(self._nuevo(v=v, s=self.can(e), exp=True, neg=C.neg, t=C.tiempo, src=src, obj=um["obj"], obj_disp=um.get("obj_disp", ""), obj_cls=um.get("obj_cls", ""), causa=causa))
                        if dat_ev:                      # «se me cayó al suelo» (el móvil de antes)
                            nuevos[-1]["dat_ev"] = True
                            nuevos[-1]["se_dat"] = "se" in C.clit
                            nuevos[-1]["comps"] = [[p_, None, s_.texto] for p_, s_ in C.comps if s_.texto]
                    return self._graba(nuevos, C, notas)
                return None
            for e in exps:
                for st in ests:
                    f = self._nuevo(v=v, s=self.can(e), exp=True, neg=C.neg, t=C.tiempo, src=src, modo=list(C.modo), freq=C.freq, causa=causa)
                    if st is not None:
                        f["obj"] = self._obj_ent(st, v, e)
                        f["obj_disp"] = st.texto; f["obj_cls"] = self._clase_sn(st)[0]; f["pl_obj"] = bool(st.pl)
                    else:
                        f["xinf"] = C.xinf
                    if dat_ev:
                        f["dat_ev"] = True
                        f["comps"] = [[p_, None, s_.texto] for p_, s_ in C.comps if s_.texto]
                        f["cuando"] = f.get("cuando") or (C.cuando or "")
                        if "se" in C.clit:
                            f["se_dat"] = True
                        if getattr(C, "prog", False):
                            f["prog"] = True
                    nuevos.append(f)
            return self._graba(nuevos, C, notas)
        # ---------- sujeto
        if C.suj is not None and not C.suj.coord and C.suj.cuant:
            if C.suj.cuant in ("ningun", "ninguna", "ningunos", "ningunas"):
                C.neg = True; C.suj.pl = True
            elif C.suj.cuant not in ("todo", "todos", "todas", "cada"):
                return None                  # «algunos / muchos X ...»: no es una verdad de toda la clase; no se generaliza
        if C.suj is not None and C.suj.cab in ("nadie", "alguien", "algo", "todo") and not C.suj.det:
            return None
        if C.suj is not None:
            s = self.ent_de(C.suj)
            if s is None:
                return self._aclara() if (C.suj.pron or C.suj.pos == "3") else None
        else:
            if getattr(self, "foco_ajeno", False) and C.pers in ("3s", "3p") and not C.amb1:
                return None                  # el tema lo llevaban las capas anteriores: que sigan ellas
            if C.v == "llamar" and C.refl and C.pers == "3p" and C.obj is not None and C.obj.coord and all(x.propio for x in C.obj.coord) and not C.comps:
                r_g = self._nombra_grupo(C, [], src)  # «Se llaman Marcos y Elena» tras «voy con mis cuñados»: el grupo antes que el sujeto implícito
                if r_g is not None:
                    return r_g
            s = self._suj_implicito(C)
            if s is None:
                return self._aclara()
        if s == "L" or (isinstance(s, list) and "L" in s):
            return None
        if C.suj is not None:
            self.foco_ajeno = False
        sujetos = s if isinstance(s, list) else [s]
        if len(sujetos) > 1 and all(self.es_persona(x) for x in sujetos):
            self.ult_grupo = [self.can(x) for x in sujetos]
        # «Rafael y Susana están casados»
        if len(sujetos) == 2 and v in ("estar", "ser") and set(C.attr) & {"casado"} and not C.neg and not C.comps:
            self._rel("esposo", sujetos[0], sujetos[1], src); self._rel("esposo", sujetos[1], sujetos[0], src)
            for x in sujetos:
                self.mencionar(x)
            self.ult_just = {"dicho": [src]}
            return self._ok(f"Entendido: {self._lista([self.disp(x) for x in sujetos])} están casados.", tipo="ack")
        pl_suj = len(sujetos) == 1 and bool(C.suj is not None and C.suj.pl and not C.suj.coord) and sujetos[0].startswith("K:")
        if len(sujetos) == 1 and C.suj is not None and C.suj.pl and not C.suj.coord and sujetos[0].startswith("I:") and sujetos[0] in self.E \
                and not self.es_persona(sujetos[0]):
            self.E[sujetos[0]]["pl"] = True             # «Mis globos son azules»: son varios
        if pl_suj:
            self.E[sujetos[0]]["pl"] = True
        if C.suj is not None and not C.suj.coord and sujetos[0].startswith("K:") and not C.suj.det and not C.suj.pl:
            self.E[sujetos[0]]["sinart"] = True
        # ---------- llamarse
        if v == "llamar" and C.refl:
            if C.obj is not None and C.obj.coord and all(x.propio for x in C.obj.coord) and not C.comps:
                return self._nombra_grupo(C, sujetos, src)
            if C.obj is None or not C.obj.propio or C.comps or len(sujetos) != 1:
                return None
            return self._nombra(sujetos[0], C.obj, src)
        # ---------- ser
        if v == "ser":
            r = self._ser(C, sujetos, src, causa, nuevos, notas)
            if r is not None:
                return r if isinstance(r, dict) else self._graba(nuevos, C, notas)
            return None
        # ---------- el resto de verbos
        if v in ("sentir", "encontrar", "notar") and C.refl and (C.attr or C.modo) and C.obj is None and not C.comps:
            v = C.v = "estar"; C.refl = False
        if v in ("estar", "parecer") and C.obj is not None and not C.obj.coord and C.obj.cab and not C.obj.det and not C.obj.propio and C.obj.de is None and not C.obj.pos and C.obj.num is None and not C.attr:
            C.attr = [M.masc(C.obj.cab)]; C.obj = None          # «está contenta» con la palabra mal etiquetada como sustantivo
        if C.obj2 is not None:
            return None
        objs = [None]
        if C.obj is not None:
            objs = C.obj.coord or [C.obj]
        self._pers_clausula = C.pers
        for s1 in sujetos:
            self._suj_cl = self.can(s1) if isinstance(s1, str) and self.can(s1) not in ("U", "L") and self.es_persona(s1) else None
            for o in objs:
                f = self._nuevo(v=v, s=self.can(s1), neg=C.neg, refl=C.refl, t=C.tiempo, attr=list(C.attr), grado=C.grado, cuando=C.cuando, freq=C.freq, modo=list(C.modo), xinf=C.xinf,
                                src=src, lugar_adv=C.lugar_adv, causa=causa, pl_suj=pl_suj)
                if C.pers == "1p":
                    f["nos"] = True
                if getattr(self, "_suj_txt", ""):
                    f["suj_txt"] = self._suj_txt; f["pl_suj"] = True
                if getattr(self, "_finalidad", ""):
                    f["comps"].append(["para", None, "que " + self._finalidad])
                if getattr(self, "_cuando_sub", "") and not f.get("cuando"):
                    f["cuando"] = self._cuando_sub
                if C.modal:
                    f["modal"] = C.modal
                if C.comp:
                    e2 = self.ent_de(C.comp[2]) if C.comp[2] is not None else None
                    if e2 is None or isinstance(e2, list):
                        return None
                    f["comp"] = [C.comp[0], C.comp[1], e2]
                for p_, s_ in C.comps:
                    if not s_.cab and not s_.pron and not s_.coord:
                        mi_ = re.match(r"^([a-záéíóúñ]+(?:ar|er|ir))\s+(con|en|para|por)\s+(.+)$", s_.texto or "")
                        if p_ == "a" and mi_:              # «salgo a cenar con dos compañeros»: el «con» es del verbo principal
                            f["comps"].append([p_, None, mi_.group(1)])
                            f["comps"].append([mi_.group(2), None, mi_.group(3)]); continue
                        f["comps"].append([p_, None, s_.texto]); continue
                    e = self.ent_de(s_, papel="comp")
                    if e is None:
                        return self._aclara() if (s_.pron or s_.pos == "3") else None
                    if isinstance(e, list):
                        for k_, e1 in enumerate(e):
                            f["comps"].append([p_, e1, s_.coord[k_].texto if s_.coord else s_.texto])
                    else:
                        f["comps"].append([p_, e, s_.texto if not s_.pron or e in ("U", "L") else cambia_persona(self.disp(e))])
                        if p_ in ("en", "a", "desde", "hacia") and v in _V_LUGAR and str(e).startswith("N:") and not self.E.get(e, {}).get("clase"):
                            self.E[e]["lugar"] = True; self.E[e]["cosa"] = True
                            # «Me voy a Japón… mi hermana vive en Madrid… estaremos allí»: «allí» es el destino del que habla quien habla
                            if self.can(s1) == "U" or v not in ("vivir", "residir", "nacer", "trabajar") or not getattr(self, "_ult_lugar_u", None):
                                self._ult_lugar = e
                            if self.can(s1) == "U":
                                self._ult_lugar_u = e
                if o is not None:
                    if v == "tener":
                        r = self._tener(f, o, s1)
                        if r is None:
                            return None
                    else:
                        if not o.cab and not o.pron:
                            return None
                        f["obj"] = self._obj_ent(o, v, s1)
                        if f["obj"] is None:
                            return self._aclara()
                        f["obj_disp"] = o.texto if not o.pron else self.disp(f["obj"])
                        f["obj_cls"] = self._clase_sn(o)[0] if o.cab else ""
                        f["cuant"] = o.num; f["pl_obj"] = bool(o.pl)
                elif "lo" in C.clit or "la" in C.clit:
                    e = self.ult_nuevo or None
                    if e is None:
                        return None
                    f["obj"] = self.can(e); f["obj_disp"] = self.disp(e); f["obj_cls"] = self.E.get(self.can(e), {}).get("clase", "")
                if not f["obj"] and v in _OBJ_PERSONA and (("me" in C.clit and C.pers != "1s") or ("nos" in C.clit and C.pers != "1p") or ("te" in C.clit and C.pers != "2s")) and not C.refl:
                    yo = "me" in C.clit or "nos" in C.clit   # «Lola me ha invitado a su boda»: me = la persona que habla
                    f["obj"] = "U" if yo else "L"; f["clit_obj"] = True
                if v not in G.COPULAS and v != "tener" and not (f["obj"] or f["comps"] or f["attr"] or f["xinf"] or f["modo"] or f["lugar_adv"] or f["cuando"] or f["freq"] or f["comp"]):
                    # verbo solo («Ana duerme», «los pájaros vuelan»): válido si el verbo es conocido
                    if v not in M._VERBOS_BASE and not self.marcos(v=v, vig=None):
                        pass
                if v == "estar" and not (f["attr"] or f["comps"] or f["lugar_adv"] or f["modo"]):
                    return None
                if v == "estar" and f["modo"] and not f["attr"]:
                    f["attr"] = [sa(x) for x in f["modo"]]; f["modo"] = []
                if v in DAR and ("me" in C.clit) and C.pers != "1s" and not any(p_ == "a" for p_, _, _ in f["comps"]):
                    f["comps"].append(["a", "U", "mí"])
                if v in DAR and ("le" in C.clit or "les" in C.clit) and not any(p_ == "a" for p_, _, _ in f["comps"]):
                    excl = tuple(self.can(x) for x in sujetos)
                    quien = None
                    for e_ in reversed(self.menc):          # «le» es singular y «les» plural
                        e_ = self.can(e_)
                        if e_ in excl or e_ in ("U", "L") or e_.startswith("K:") or not self.es_persona(e_):
                            continue
                        if bool(self.E.get(e_, {}).get("pl")) == ("les" in C.clit):
                            quien = e_
                            break
                    if quien:
                        f["comps"].append(["a", quien, self.disp(quien) if quien != "U" else "mí"])
                        f["comps"][-1][2] = cambia_persona(f["comps"][-1][2]) if self.disp(quien).startswith(("tu ", "tus ")) else f["comps"][-1][2]
                nuevos.append(f)
        return self._graba(nuevos, C, notas)

    def _obj_ent(self, o: SN, v, s):
        if o.pos == "3" and s and self.can(s) not in ("U", "L") and not str(s).startswith("K:"):
            prev = self.ult_suj
            self.ult_suj = self.can(s)                     # «Mi hermano rompió su bici»: «su» es del sujeto
            try:
                e = self.ent_de(o)
            finally:
                self.ult_suj = prev
            return e[0] if isinstance(e, list) else e
        if o.propio or o.pron or o.pos or o.de is not None or o.apos:
            e = self.ent_de(o)
            return e[0] if isinstance(e, list) else e
        cl = self._clase_sn(o)[0]
        if v in OBTENER and o.det == "i" and not o.pl and o.num is None:
            eid = self._ent("I:" + cl + "@" + self.can(s), clase=cl, dueno=self.can(s), gen=o.gen or M.genero_sust(cl))
            self._rel(cl, eid, s, "")
            self.E[eid]["t_nuevo"] = self.turno
            self._nuevo_ref = eid
            return eid
        if o.det == "d" and not o.pl:
            return self.ent_de(o)
        return self._ent("K:" + cl, clase=cl, gen=o.gen or M.genero_sust(cl))

    def _hay(self, C, src):
        nuevos = []
        for o in (C.obj.coord or [C.obj]):
            if not o.cab or o.propio:
                return None
            cl = self._clase_sn(o)[0]
            f = self._nuevo(v="haber", s=None, neg=C.neg, t=C.tiempo, src=src, obj=self._ent("K:" + cl, clase=cl, gen=o.gen or M.genero_sust(cl)), obj_cls=cl, obj_disp=o.texto,
                            cuant=o.num if o.num is not None else (1 if o.det == "i" and not o.pl else None), pl_obj=bool(o.pl))
            for p_, s_ in C.comps:
                e = self.ent_de(s_, papel="comp")
                if e is None or isinstance(e, list):
                    return None
                f["comps"].append([p_, e, s_.texto])
            nuevos.append(f)
        def _desc(f_):                                  # «tres bares» y «cuatro bares» describen lo mismo; «niños de Rumanía» y «niños de Ecuador», no
            return re.sub(r"^(?:\d+|un|una|unos|unas|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|muchos|muchas|pocos|pocas|varios|varias|algunos|algunas)\s+", "", sa(f_.get("obj_disp") or ""))
        for f in nuevos:
            self.F = [g for g in self.F if not (g["v"] == "haber" and g.get("obj_cls") == f["obj_cls"] and str(g.get("comps")) == str(f["comps"]) and _desc(g) == _desc(f) and not any(g is n_ for n_ in nuevos))]
            self.F.append(f)
        self.ult_marco = nuevos[-1]
        self.ult_just = {"dicho": [src]}
        lug = contrae(" ".join(p_.replace("_", " ") + " " + cambia_persona(d) for p_, e, d in nuevos[0]["comps"]))
        return self._ok(f"Entendido: {lug} hay {self._lista([cambia_persona(f['obj_disp']) for f in nuevos])}.", tipo="ack")

    def _nombra_grupo(self, C, sujetos, src):
        """«Tengo dos hermanos. Se llaman Pedro y Juan.» -> cada nombre queda relacionado con su dueño."""
        nombres = C.obj.coord
        cl, dueno = None, None
        if C.suj is not None and not C.suj.coord and C.suj.cab and (C.suj.pos or C.suj.de is not None):
            cl = self._clase_sn(C.suj)[0]
            dueno = "U" if C.suj.pos == "U" else (self.ent_de(C.suj.de) if C.suj.de is not None else (self.ult_suj or self.ref3(persona=True)))
        else:
            for f in reversed(self.F):
                if f["v"] == "tener" and f.get("vig", True) and f.get("pl_obj") and f.get("obj_cls") and (f.get("cuant") in (None, len(nombres))) and f["turno"] >= self.turno - 3:
                    cl, dueno = f["obj_cls"], self.can(f["s"])
                    break
        if not cl:
            # «Mis sobrinas vienen… Se llaman Paula y Marta»: el grupo del que se viene hablando
            for f in reversed(self.F[-8:]):
                g_ = self.can(f.get("s") or "")
                if g_.startswith("G:") and self.E.get(g_, {}).get("pl") and f.get("turno", -9) >= self.turno - 3:
                    cl, dueno = self.E[g_].get("clase"), self.can(self.E[g_].get("dueno") or "")
                    self._grupo_origen = g_
                    break
        if not cl:
            # «Vivo con mis abuelos. Se llaman Paco y Juana», «Salgo a cenar con dos compañeros. Se llaman…»: un grupo de personas
            for f in reversed(self.F[-6:]):
                if f.get("turno", -9) < self.turno - 2:
                    continue
                txts = [d_ or "" for _, _, d_ in f.get("comps", [])] + [f.get("xinf") or "", f.get("obj_disp") or ""]
                hit = None
                for t_ in txts:
                    mm = re.search(r"\b(?:con|a|para)?\s*(mis|tus|dos|tres|cuatro|cinco)\s+([a-záéíóúñ]+s)\b", sa(t_))
                    if mm:
                        c0 = sa(M.singular(mm.group(2)))
                        c0m = M.masc(c0)
                        if (c0m in FAMILIA or c0m in PERSONA_CLS or c0 in FAMILIA) and (not mm.group(1).isalpha() or M.numero(mm.group(1)) in (None, len(nombres))):
                            hit = c0m if c0m in FAMILIA or c0m in PERSONA_CLS else c0
                            break
                if hit:
                    cl, dueno = hit, ("U" if self.can(f.get("s") or "") == "U" else self.can(f.get("s") or ""))
                    break
        if not cl:
            # «Vivo con dos chicas. Una se llama Carla y la otra Marta.»: el grupo va en un complemento
            for f in reversed(self.F[-8:]):
                for k_, (p_, e_, d_) in enumerate(f.get("comps", [])):
                    mm = re.match(r"^(?:mis |unas? |unos )?(dos|tres|cuatro|cinco|seis) ([a-záéíóúñ]+)$", sa(d_ or ""))
                    if mm and M.numero(mm.group(1)) == len(nombres):
                        cl0 = sa(M.singular(mm.group(2)))
                        g0 = "f" if cl0.endswith("a") else "m"
                        ids = []
                        for n_ in nombres:
                            nid = self._ent("N:" + n_.cab, nombre=n_.nombre, clase=M.masc(cl0) if g0 == "f" else cl0, gen=g0)
                            self.E[nid]["src_nombre"] = src
                            h = dict(f); h["comps"] = [list(c) for c in f["comps"]]; h["comps"][k_] = [p_, nid, n_.nombre]; h["src"] = src; h["turno"] = self.turno
                            h["miembro"] = True; f["grupo_de"] = True
                            self.F.append(h); self._espejo(h)
                            self.mencionar(nid); ids.append(nid)
                        self.ult_grupo = ids
                        self.ult_just = {"dicho": [f["src"], src]}
                        return self._ok(f"Entendido: {self._lista([self.frase(x) for x in self.F[-len(ids):]])}.", tipo="ack")
        if not cl or dueno is None or isinstance(dueno, list):
            return None
        ph = "I:" + cl + "@" + self.can(dueno)
        self.R = [q for q in self.R if self.can(q["x"]) != ph]
        self.E.pop(ph, None)
        ids = []
        for n_ in nombres:
            nid = self._ent("N:" + n_.cab, nombre=n_.nombre, clase=cl, dueno=self.can(dueno))
            self.E[nid]["src_nombre"] = src
            self._rel(cl, nid, dueno, src)
            if cl == "hijo" and self.can(dueno) == "U" and any(f["v"] == "tener" and f.get("nos") and f.get("obj_cls") == "hijo" for f in self.F[-6:]):
                pareja = [r_["x"] for r_ in self.rels("esposo", y="U")]
                if len(pareja) == 1:
                    self._rel(cl, nid, pareja[0], src)
            self.mencionar(nid); ids.append(nid)
        self.ult_just = {"dicho": [src]}
        self.ult_grupo = list(ids)
        g_or = getattr(self, "_grupo_origen", None) or ("G:" + cl + "@" + self.can(dueno))
        self._grupo_origen = None
        for f_g in [f for f in self.F if self.can(f.get("s") or "") == g_or and f.get("vig", True)]:
            if f_g["v"] == "ser" and set(f_g.get("attr", [])) & {"gemelo", "mellizo", "hermano"}:
                for a_ in ids:                          # «Son gemelas. Se llaman Paula y Marta»: son hermanas entre sí
                    for b_ in ids:
                        if a_ != b_:
                            self._rel("hermano", a_, b_, src)
            elif f_g["v"] in ("ser", "tener", "estar", "vivir") and not f_g.get("neg"):
                for a_ in ids:                          # lo dicho del grupo vale para cada una
                    h = dict(f_g); h["s"] = a_; h["comps"] = [list(c) for c in f_g.get("comps", [])]; h["src"] = f_g["src"]; h["miembro"] = True; h["pl_suj"] = False
                    self.F.append(h)
        if self.E.get(g_or, {}).get("gen") == "f" and all(not self.E.get(x, {}).get("gen") for x in ids):
            for x in ids:
                self.E[x]["gen"] = "f"                  # «mis sobrinas»: todas son chicas
        g = "f" if all(self.gen(x) == "f" for x in ids) else "m"
        if C.suj is not None and not C.suj.coord and getattr(C.suj, "gen", "") == "m" and cl not in FAMILIA and cl not in PERSONA_CLS:
            g = "m"                                     # «Los gatos se llaman Luna y Sol»: se dijo «gatos»
        nom = M.plural(self._acento(self._rel_nombre(cl, g)))
        quien = ("tus " + nom) if self.can(dueno) == "U" else contrae(f"{'las' if g == 'f' else 'los'} {nom} de {self.disp(dueno)}")
        return self._ok(f"{self._ack()}: {quien} se llaman {self._lista([self.disp(x) for x in ids])}.", tipo="ack")

    _AMB = r"(?:familia|casa|clase|trabajo|grupo|equipo|oficina|barrio|pueblo|cuadrilla|empresa)"

    def _nadie(self, p, n):
        """«Nadie de mi familia fuma» y «¿Fuma alguien de mi familia?»: un cuantificador negativo con su ámbito."""
        es_preg = "?" in p or "¿" in p
        A = self._AMB
        if not es_preg:
            m = re.match(rf"^(?:(?:en|de) (mi|tu|su) ({A}),? )?nadie(?: (?:de|en) (mi|tu|su) ({A}))? (?!no )(.+)$", n)
            if not m or getattr(self, "_en_nadie", False):
                return None
            pos, amb, pred = m.group(1) or m.group(3) or "", m.group(2) or m.group(4) or "", m.group(5)
            pred_o = " ".join(p.strip(" .!").split()[-len(pred.split()):])
            nombre = "Nemo" + amb
            self._en_nadie = True
            try:
                r = self._una(f"{nombre} no {pred_o}.")
            finally:
                self._en_nadie = False
            eid = "N:" + sa(nombre)
            if r is None or r.get("estado") != "ok" or eid not in self.E:
                if eid in self.E and not any(self.can(f["s"]) == eid for f in self.F if f.get("s")):
                    self.E.pop(eid, None)
                return None
            de = {"mi": "tu", "tu": "mi", "su": "su"}.get(pos, "")
            self.E[eid].update(nombre="nadie" + (f" de {de} {amb}" if amb else ""), nadie=True, gen="m", cosa=True)
            self.menc = [x for x in self.menc if x != eid]
            self.ult_suj = None; self.ult_nuevo = None
            fs = [f for f in self.F if f.get("s") and self.can(f["s"]) == eid and f.get("turno") == self.turno]
            for f in fs:
                f["src"] = p
            self.ult_just = {"dicho": [p]}
            self.guardar()
            return self._ok("Entendido: " + (self.frase(fs[-1]) if fs else "nadie " + pred_o) + ".", tipo="ack")
        m = re.search(rf"\balguien(?: (?:de|en) (mi|tu|su) ({A}))?\b", n)
        if not m:
            return None
        nemos = [e for e, d in self.E.items() if d.get("nadie") and e not in self.eq]
        eid = "N:nemo" + (m.group(2) or "")
        if eid not in nemos:
            if m.group(2) or len(nemos) != 1:
                return None
            eid = nemos[0]
        ps = p.split()
        ns = [sa(w).strip("¿?¡!.,") for w in ps]
        i = ns.index("alguien")
        k = 4 if m.group(2) else 1
        fin = "?" if ps[i + k - 1].endswith("?") else ""
        ini = "¿" if ps[i].startswith("¿") else ""
        q = " ".join(ps[:i] + [ini + eid[2:].title() + fin] + ps[i + k:])
        r = self._una(q)
        if r is not None and r.get("estado") == "ok":
            r["respuesta"] = re.sub(r"^No, ", "No, ", r["respuesta"])
            self.ult_suj = None
            return r
        return self._abst("No lo sé: no me has dicho eso.") if r is not None else None

    _V_DECIR = r"(?:siempre |tambien |ya |me |te |le |nos )*(?:dice|dicen|decia|dijo|dijeron|opina|opinan|piensa|piensan|cree|creen|comenta|comento|asegura|insiste en|ha dicho|han dicho|ha comentado|recomienda|recomendo|ha recomendado|aconseja|aconsejo)"

    _V_DESEO = {"quiere": "querer", "quieren": "querer", "queria": "querer", "querian": "querer", "pide": "pedir", "piden": "pedir", "pidio": "pedir",
                "ha pedido": "pedir", "han pedido": "pedir", "necesita": "necesitar", "prefiere": "preferir", "prefieren": "preferir", "espera": "esperar",
                "esperan": "esperar", "prohibe": "prohibir", "manda": "mandar", "deja": "dejar", "aconseja": "aconsejar", "recomienda": "recomendar"}

    def _yo_dije(self, p, n):
        """«Le he dicho que lo deje», «A mi hermano le he dicho que…»: lo que la persona le dijo o pidió a otra."""
        if "?" in p or "¿" in p:
            return None
        m = re.match(r"^(?:yo\s+)?(?:a\s+(.+?)\s+)?(le|les)\s+(he dicho|dije|digo|decia|he pedido|pedi|pido|he aconsejado|aconseje|he recomendado|recomende)\s+que\s+(.+)$", n)
        if not m:
            return None
        ps = p.strip(" .!").split()
        i_que = next((i for i, w in enumerate(ps) if sa(w.lower()) == "que"), None)
        cont = " ".join(ps[i_que + 1:]) if i_que is not None else m.group(4)
        if m.group(1):
            k0 = 1 if sa(ps[0].lower()) == "a" else (2 if sa(ps[1].lower()) == "a" else 1)
            e = self._sn_ent(" ".join(ps[k0:k0 + len(m.group(1).split())]))
        else:
            e = next((x for x in [self.ult_suj] + list(reversed(self.menc)) if x and self.can(x) not in ("U", "L") and self.es_persona(x)), None)
        if not e:
            return None
        e = self.can(e)
        v = {"he dicho": "decir", "dije": "decir", "digo": "decir", "decia": "decir"}.get(m.group(3)) or ("pedir" if "ped" in m.group(3) else ("aconsejar" if "aconsej" in m.group(3) else "recomendar"))
        t_ = "pres" if m.group(3) in ("digo", "pido") else ("imp" if m.group(3) == "decia" else "pret")
        f = self._nuevo(v=v, s="U", obj_disp="que " + cont, comps=[["a", e, self.disp(e)]], src=p, t=t_, dicho=True)
        f["comps"][0][2] = cambia_persona(f["comps"][0][2]) if self.disp(e).startswith(("tu ", "tus ")) else f["comps"][0][2]
        self.F.append(f); self.ult_marco = f; self.mencionar(e)
        self.ult_just = {"dicho": [p]}
        self.guardar()
        return self._ok(f"Entendido: {self.frase(f)}.", tipo="ack")

    def _deseo(self, p, n):
        """«Mi hermana quiere que vaya a su casa»: lo que alguien quiere o pide que haga otra persona (no es un hecho)."""
        if "?" in p or "¿" in p:
            return None
        m = re.match(r"^(.+?)\s+(?:me\s+|te\s+|le\s+|nos\s+)?(" + "|".join(sorted(self._V_DESEO, key=len, reverse=True)) + r")\s+que\s+(.+)$", n)
        if not m or m.group(1) in ("yo", "no", "tu"):
            return None
        ps = p.strip(" .!").split()
        k_s = len(m.group(1).split())
        i_que = next((i for i in range(k_s, len(ps)) if sa(ps[i].lower()) == "que"), None)
        if i_que is None:
            return None
        cont = " ".join(ps[i_que + 1:])
        cont_s, es_subj = coloquial.subj_a_segunda(cont)
        if not es_subj:
            return None                                 # «quiere que» va con subjuntivo; si no, no es esto
        sn_ = self._sn_de(" ".join(ps[:k_s]))
        e = self.ent_de(sn_) if sn_ is not None else None
        if not isinstance(e, str) or e in ("U", "L"):
            return None
        e = self.can(e)
        self._suj_cl = e if self.es_persona(e) else None
        txt = coloquial.a_segunda_sin_verbo(cont_s)
        v = self._V_DESEO[m.group(2)]
        f = self._nuevo(v=v, s=e, obj_disp="que " + txt, src=p, dicho=True, t="pres")
        self.F.append(f); self.mencionar(e); self.ult_marco = f
        self.ult_just = {"dicho": [p]}
        self.guardar()
        return self._ok(f"Entendido: {self.frase(f)}. Lo apunto como algo que {'quiere' if v == 'querer' else 'pide' if v == 'pedir' else M.conjugar(v, 'pres', '3s')} {'ella' if self.gen(e) == 'f' else 'él'}, no como un hecho.", tipo="ack")

    def _dicho(self, p, n):
        """Estilo indirecto: «Mi mujer dice que debería hacer deporte» se guarda como algo que ELLA dice, no como un hecho."""
        es_preg = "?" in p or "¿" in p
        mo_ = re.match(r"^(?:pues |bueno,? )?(?:yo )?(creo|pienso|opino|me parece|considero) que (.+)$", n) if not es_preg else None
        if mo_ and not re.match(r"^(?:no|si)$", mo_.group(2)):
            # «Yo creo que es muy pequeño»: una opinión de quien habla, no un hecho
            ps = p.strip(" .!").split()
            k0 = next((i for i, w in enumerate(ps) if sa(w.lower()) == "que"), None)
            cont = " ".join(ps[k0 + 1:]) if k0 is not None else mo_.group(2)
            T_o = G.tokens(self.parser, cont[:1].upper() + cont[1:])
            C_o = G.clausula(T_o) if T_o else None
            if C_o is not None and C_o.suj is None and C_o.pers in ("3s", "3p"):
                e_o = self._suj_implicito(C_o)       # «es muy pequeño»: de quién se habla
                if isinstance(e_o, str) and e_o not in ("U", "L") and not e_o.startswith("?"):
                    cont = cambia_persona(self.disp(e_o)) + " " + cont
            txt = coloquial.a_segunda(cont)
            f = self._nuevo(v="creer", s="U", obj_disp="que " + txt, src=p, dicho=True, t="pres")
            self.F.append(f); self.ult_marco = f
            self.ult_just = {"dicho": [p]}
            self.guardar()
            return self._ok(f"Entendido: crees que {txt}. Lo apunto como tu opinión, no como un hecho.", tipo="ack")
        if not es_preg:
            m = re.match(rf"^(?:((?!(?:me|te|le|nos|siempre|ya|tambien|hoy|ayer)\b).+?) )?({self._V_DECIR}) que (.+)$", n)
            if not m or n.startswith(("no ", "si ", "creo ", "pienso ", "opino ", "digo ")):
                return None
            ps = p.strip(" .!").split()
            k_s = len(m.group(1).split()) if m.group(1) else 0
            k_v = len(m.group(2).split())
            cont = " ".join(ps[k_s + k_v + 1:])
            if m.group(1):
                sn_ = self._sn_de(" ".join(ps[:k_s]))
                e = self.ent_de(sn_) if sn_ is not None else None
                if e == "U" and sn_ is not None:
                    e = self._otro_no_u(sn_, p, crear=True) or e   # «El padre de Mario dice que sí», dicho por su madre o su padre
            else:
                e = None
                um = self.ult_marco or {}
                for x in [c_[1] for c_ in um.get("comps", [])] + [um.get("obj")]:
                    if x and x not in ("U", "L") and (self.es_persona(x) or "persona" in [c for c, _ in self.clases(x)] or "persona" in conceptos.ancestros(str(x)[2:])):
                        e = self.can(x)
                if e is None:
                    for d_ in [c_[2] for c_ in um.get("comps", []) if c_[2]] + [um.get("obj_disp") or ""]:
                        c_k = conceptos._kb_clase(d_.split()[-1]) if d_ else None
                        if c_k and "persona" in conceptos.ancestros(c_k):
                            e = self._ent("K:" + c_k, clase=c_k, gen=conceptos.genero(c_k))
                e = e or self.ref3(persona=True)
            if e is None or isinstance(e, list) or e in ("U", "L"):
                return None
            e = self.can(e)
            a_mi = bool(re.search(r"\bme\b", m.group(2)))
            cont_s, es_subj = coloquial.subj_a_segunda(cont)
            txt = coloquial.a_segunda(cont_s) if not es_subj else coloquial.a_segunda_sin_verbo(cont_s)
            pl_d = bool(m.group(2).endswith("n") or (m.group(1) and re.match(r"^(?:los|las|mis|tus|sus|unos|unas)\b", m.group(1))))
            f = self._nuevo(v="decir", s=e, obj_disp="que " + txt, src=p, dicho=True, t="pres", a_u=a_mi, pl_suj=pl_d)
            self.F.append(f)
            self._hablante_dicho = e
            self.mencionar(e); self.ult_marco = f
            self.ult_suj = None                         # quien habla sigue siendo la persona: «de pequeño jugaba…» es ella
            self._afirma_de = "U"
            self.ult_just = {"dicho": [p]}
            self.guardar()
            quien_d = (re.sub(r"^(el|la) ", lambda x: "los " if x.group(1) == "el" else "las ", self.disp(e)) + ("s" if not self.disp(e).endswith("s") else "")) if pl_d and e.startswith("K:") else self.disp(e)
            quien_pr = ("ellas" if self.gen(e) == "f" else "ellos") if pl_d else ("ella" if self.gen(e) == "f" else "él")
            return self._ok(f"Entendido: {quien_d} {'te ' if a_mi else ''}{'dicen' if pl_d else 'dice'} que {txt}. Lo apunto como algo que {'dicen' if pl_d else 'dice'} {quien_pr}, no como un hecho.", tipo="ack")
        mr_ = re.match(r"^(?:tiene razon|esta en lo cierto|lleva razon|es (?:verdad|cierto) lo que dice|acierta|se equivoca) (.+)$", n)
        if mr_:
            resto_o = " ".join(p.strip(" ¿?").split()[-len(mr_.group(1).split()):])
            sn_ = self._sn_de(resto_o)
            e = self._q_ent(sn_) if sn_ is not None else None
            fs = [f for f in self.F if f.get("dicho") and e and not isinstance(e, list) and self.can(f["s"]) == self.can(e)]
            if fs:                                       # se contrasta lo que dice con lo que sé
                cont = re.sub(r"^que\s+", "", fs[-1]["obj_disp"])
                r_ = self._una("¿" + cont[:1].upper() + cont[1:] + "?")
                if r_ is not None and r_.get("estado") == "ok":
                    txt = r_["respuesta"]
                    quien = self.disp(self.can(e))
                    if txt.startswith("No"):
                        return self._ok(f"No: {quien} dice que {cont}, pero " + txt[3:].lstrip(", ").rstrip(".") + ".")
                    if txt.startswith("Sí"):
                        return self._ok(f"Sí: {quien} dice que {cont}, y " + txt[3:].lstrip(", ").rstrip(".") + ".")
                return self._abst(f"No lo sé: no tengo datos para saber si {cont}.")
        m = re.match(r"^que (?:(me|te|le|nos) )?(?:dice|dicen|decia|dijo|opina|piensa|cree|comenta|ha dicho|recomienda|aconseja|ha recomendado) (.+?)(?: de (?:eso|esto|ello)| sobre (?:eso|esto))?$", n)
        if not m:
            return None
        resto_o = " ".join(p.strip(" ¿?").split()[-len(m.group(2).split()):])
        sn_ = self._sn_de(resto_o)
        e = self._q_ent(sn_) if sn_ is not None else None
        if e is None or isinstance(e, list) or str(e).startswith("?"):
            return None
        e = self.can(e)
        if e == "U" and sn_ is not None and (sn_.de is not None or sn_.pos == "3"):
            e = self._otro_no_u(sn_, p, crear=False) or e
        fs = [f for f in self.F if f.get("dicho") and self.can(f["s"]) == e and (e != "U" or f.get("v") != "creer")]
        if not fs and sn_ is not None and sn_.cab:      # «el médico» = el médico del que se habló
            fs = [f for f in self.F if f.get("dicho") and str(f["s"]).startswith("K:") and str(f["s"])[2:] == sa(sn_.cab)]
            e = self.can(fs[-1]["s"]) if fs else e
        if not fs:
            return self._abst(f"No lo sé: no me has contado qué dice {self.disp(e)}.")
        self.mencionar(e); self.ult_suj = e
        self.ult_just = {"dicho": [f["src"] for f in fs[-2:]]}
        pl_d = bool(fs[-1].get("pl_suj"))
        quien_d = (re.sub(r"^(el|la) ", lambda x: "los " if x.group(1) == "el" else "las ", self.disp(e)) + ("s" if not self.disp(e).endswith("s") else "")) if pl_d and e.startswith("K:") else self.disp(e)
        return self._ok(self._fin(_cap(quien_d) + (" dicen " if pl_d else " dice ") + self._lista([f["obj_disp"] for f in fs[-2:]])))

    def _otro_no_u(self, sn_, src, crear=False):
        """«el padre de Mario» / «su padre» cuando el análisis da la persona que habla: el otro (o uno nuevo)."""
        if not sn_.cab:
            return None
        if sn_.de is not None:
            du_ = self.ent_de(sn_.de, crear=False)
        elif sn_.pos == "3":
            du_ = next((x for x in [self.ult_suj] + list(reversed(self.menc)) if x and self.can(x) not in ("U", "L") and self.es_persona(x)), None)
        else:
            return None
        if not isinstance(du_, str) or self.can(du_) in ("U", "L"):
            return None
        du_ = self.can(du_)
        cl_ = self._clase_sn(sn_)[0]
        otros_ = [r_["x"] for r_ in self.rels(cl_, y=du_) if self.can(r_["x"]) != "U"]
        if otros_:
            return self.can(otros_[0])
        if not crear:
            return None
        e = self._ent(f"I:{cl_}@{du_}", clase=cl_, dueno=du_, gen=M.genero_sust(cl_))
        self._rel(cl_, e, du_, src)
        return e

    def _sn_ent(self, texto):
        try:
            sn_ = self._sn_de(texto)
            e_ = self.ent_de(sn_, crear=False) if sn_ is not None else None
            return self.can(e_) if isinstance(e_, str) and not e_.startswith("?") else None
        except Exception:                               # noqa
            return None

    def _sn_de(self, texto):
        """SN de un texto corto («mi coche», «Luna», «la casa de Ana»)."""
        T = G.tokens(self.parser, texto)
        r = G.sn_coord(T, 0) if T else None
        return r[0] if r else None

    def _renombra(self, viejo, nombre, src):
        """Corrección de un nombre: «No, se llama Luisa» / «No se llama Lucía, se llama Luisa»."""
        e = None
        if viejo and ("N:" + viejo in self.E or "N:" + viejo in self.eq):
            e = self.can("N:" + viejo)
        elif not viejo or True:
            e = self.can(self.ult_suj) if self.ult_suj else None
            if e is None or e in ("U", "L"):
                e = self.ult_nuevo
        if not e or not str(e).startswith(("N:", "I:")) or not nombre[:1].isupper():
            return None
        e = self.can(e)
        nid = "N:" + sa(nombre)
        if nid == e:
            return None
        antes = self.E.get(e, {}).get("nombre") if e.startswith("N:") else ""
        desc = None
        d = self.E.get(e, {})
        if d.get("clase") and d.get("dueno"):
            desc = self.disp("I:" + d["clase"] + "@" + d["dueno"]) if ("I:" + d["clase"] + "@" + d["dueno"]) not in self.E else None
            g = d.get("gen") or M.genero_sust(d["clase"])
            du = self.can(d["dueno"])
            nom = self._acento(self._rel_nombre(d["clase"], g))
            desc = ("tu " + nom) if du == "U" else contrae(f"{'la' if g == 'f' else 'el'} {nom} de {self.disp(du)}")
        self._ent(nid, nombre=nombre)
        for k in ("clase", "dueno", "gen"):
            if d.get(k):
                self.E[nid][k] = d[k]
        self.E[nid]["src_nombre"] = src
        self.unir(e, nid)
        self.mencionar(nid); self.ult_suj = nid; self.ult_nuevo = nid
        self.ult_just = {"dicho": [src]}
        self.guardar()
        return self._ok(f"Entendido, lo corrijo: {desc or 'ahora'} se llama {nombre}" + (f", no {antes}." if antes else "."), tipo="ack")

    def _nombra(self, e, sn_nom: SN, src):
        e = self.can(e)
        nombre = sn_nom.nombre
        if e == "U":
            previo = self.usuario.get("nombre")
            self.usuario["nombre"] = nombre; self.E["U"]["nombre"] = nombre
            self.E["U"]["gen"] = M.genero_nombre(nombre)
            self.E["U"]["src_nombre"] = src
            self.mencionar("U")
            self.ult_just = {"dicho": [src]}
            if previo and sa(previo) != sa(nombre):
                return self._ok(f"Encantado, {nombre}. A partir de ahora te llamo así (antes me dijiste {previo}).", tipo="ack")
            return self._ok(f"Encantado, {nombre}." if not previo else f"Encantado de nuevo, {nombre}.", tipo="ack")
        nid = "N:" + sa(nombre)
        self._ent(nid, nombre=nombre)
        if e.startswith("I:"):
            d = self.E.get(e, {})
            self.E[nid]["clase"] = self.E[nid].get("clase") or d.get("clase", "")
            self.E[nid]["dueno"] = self.E[nid].get("dueno") or d.get("dueno")
            if d.get("gen"):
                self.E[nid]["gen"] = d["gen"]
            self.E[nid]["src_nombre"] = src
            desc = self.disp(e)
            gemelas = [k for k, d2 in list(self.E.items()) if k.startswith("I:") and k != e and k not in self.eq and d2.get("clase") == d.get("clase") and d2.get("t_nuevo") and d2.get("t_nuevo") == d.get("t_nuevo")]
            for k in gemelas:
                self.unir(k, nid)
            self.unir(e, nid)
            self.mencionar(nid); self.ult_nuevo = nid; self.ult_suj = nid
            self.E[nid]["t_nuevo"] = self.turno
            self.ult_just = {"dicho": [src]}
            return self._ok(f"Entendido: {desc} se llama {nombre}.", tipo="ack")
        if e.startswith("N:") and e != nid:
            self.E[e].setdefault("apodos", []).append(nombre)
            return self._ok(f"Entendido: {self.disp(e)} también se llama {nombre}.", tipo="ack")
        if e.startswith("K:"):
            # «el perro se llama Toby» sin dueño conocido
            d = self.E.get(e, {})
            self.E[nid]["clase"] = d.get("clase", ""); self.E[nid]["src_nombre"] = src
            self.mencionar(nid); self.ult_suj = nid
            return self._ok(f"Entendido: {self.disp(e)} se llama {nombre}.", tipo="ack")
        return self._ok("Sí, ya lo sabía.", tipo="ack")

    def _ser(self, C: Clausula, sujetos, src, causa, nuevos, notas):
        o = C.obj
        if len(sujetos) == 1 and isinstance(sujetos[0], str) and self.can(sujetos[0]) not in ("U", "L") and self.es_persona(sujetos[0]):
            self._suj_cl = self.can(sujetos[0])          # «Jorge fue el mejor alumno de su clase»: la clase de Jorge
        if o is not None and not o.det and not o.pos and not o.propio and not o.coord and o.cab and sa(M.masc(o.cab)) in COLORES and not C.attr:
            C.attr = [sa(M.masc(o.cab))]; C.obj = o = None   # «El cuadro es naranja»: color, no la fruta
        if o is None and not C.attr and len(C.comps) == 1 and C.comps[0][0] == "de" and C.comps[0][1].cab and sa(C.comps[0][1].cab).startswith("color") and C.comps[0][1].adjs:
            C.attr = [sa(M.masc(C.comps[0][1].adjs[0]))]; C.comps = []      # «es de color naranja»
        if C.obj2 is not None or C.xinf:
            return None
        if o is None and not C.attr and not C.comps and not C.comp and (C.freq or C.cuando) and len(sujetos) == 1 and not self.es_persona(sujetos[0]):
            # «Las clases son los martes y los jueves», «La reunión es mañana»: cuándo ocurre algo
            f = self._nuevo(v="ser", s=sujetos[0], src=src, freq=C.freq, cuando=C.cuando, t=C.tiempo, neg=C.neg, pl_suj=bool(C.suj is not None and C.suj.pl))
            nuevos.append(f)
            return True
        pl_suj = len(sujetos) == 1 and sujetos[0].startswith("K:") and bool(self.E[sujetos[0]].get("pl"))
        # nombre de la persona: «soy Marcos», «mi nombre es Marcos»
        if o is not None and o.propio and len(sujetos) == 1 and not C.comps:
            s = sujetos[0]
            if s == "U":
                return self._nombra("U", o, src)
            d = self.E.get(s, {})
            if s.startswith("I:") and d.get("clase") == "nombre":
                self._quita_rel_placeholder(s)
                quien = self.can(d.get("dueno"))
                if quien.startswith("N:") and C.suj is not None and C.suj.pos == "3":
                    sin = [e for e in reversed(self.menc) if self.can(e).startswith("I:")]
                    if sin:
                        quien = self.can(sin[0])
                self.E.pop(s, None)
                return self._nombra(quien, o, src)
            if s.startswith("I:"):
                return self._nombra(s, o, src)
            if s.startswith("N:"):
                return None
        _kc = conceptos._kb_clase(o.cab) if (o is not None and o.cab and o.de is not None and not o.pos) else None
        _no_rel = bool(_kc and "persona" not in conceptos.ancestros(_kc) and _kc not in REL_DISP_BASE and _kc not in FAMILIA) or bool(
            o is not None and o.de is not None and not o.pos and o.det == "i" and o.adjs)
        if _no_rel and all(not self.es_persona(x) for x in sujetos):
            # «La paella es un plato típico de Valencia»: una cosa no tiene parentescos; se guarda tal cual
            f = self._nuevo(v="ser", s=sujetos[0], attr=[self._clase_sn(o)[0]], isa=[self._clase_sn(o)[0]], src=src)
            f["isa_txt"] = o.texto
            nuevos.append(f)
            return True
        if o is not None and not o.coord and o.cab and (o.de is not None or o.pos) and not o.propio and not C.attr and not C.comps:
            # relación: «Ana es la hermana de Luis», «Ana es mi jefa»
            cl, g = self._clase_sn(o)
            dueno = "U" if o.pos == "U" else ("L" if o.pos == "L" else None)
            if o.pos == "3":
                dueno = self.ref3(persona=True, excluye=tuple(sujetos))
            if o.de is not None:
                dueno = self.ent_de(o.de)
            duenos = dueno if isinstance(dueno, list) else [dueno]
            if dueno is None or any(d_ is None or d_ == "L" for d_ in duenos):
                return None
            hecho = False
            for dueno in duenos:
                for s in sujetos:
                    self._quita_rel_placeholder_de(cl, dueno)
                    hecho = self._rel(cl, s, dueno, src, g) or hecho
                    self.mencionar(s)
                self.mencionar(dueno)
            self.ult_suj = sujetos[0]
            fr = self._lista([self._frase_rel(cl, self.can(s), self.can(d_)) for s in sujetos for d_ in duenos])
            self.ult_just = {"dicho": [src]}
            if C.neg:
                return None
            return self._ok((f"{self._ack()}: {fr}." if hecho else f"Sí, ya sabía que {fr}."), tipo="ack")
        if o is None and len(sujetos) > 1 and len(C.attr) == 1 and not C.comps and (self._canon_rel(C.attr[0])[0] if C.attr[0] in REL_CANON else C.attr[0]) in (SIMETRICAS | {"hermano", "primo", "novio", "esposo", "gemelo"}):
            o = SN(cab=C.attr[0], pl=True); C.attr = []
        if o is not None and not o.coord and len(sujetos) > 1 and o.pl and not o.det and self._clase_sn(o)[0] in (SIMETRICAS | {"hermano", "primo", "novio", "esposo", "gemelo"}) and not C.neg:
            cl = self._clase_sn(o)[0]
            if cl == "gemelo":
                cl = "hermano"
            for i_, a in enumerate(sujetos):
                for b in sujetos[i_ + 1:]:
                    self._rel(cl, a, b, src)
            for a in sujetos:
                self.mencionar(a)
            self.ult_just = {"dicho": [src]}
            return self._ok(f"{self._ack()}: {self._lista([self.disp(a) for a in sujetos])} son {M.plural(cl)}.", tipo="ack")
        if o is not None and not o.coord and len(sujetos) == 1 and sujetos[0].startswith("I:") and (o.det == "d" or o.propio) and not C.attr and not C.neg:
            # valor de un papel: «mi color favorito es el azul»
            s = sujetos[0]
            d = self.E.get(s, {})
            val = self._ent("K:" + o.cab, clase=o.cab, gen=o.gen or M.genero_sust(o.cab))
            self._quita_rel_placeholder(s)
            self._rel(d.get("clase"), val, d.get("dueno"), src)
            self.ult_just = {"dicho": [src]}
            return self._ok(f"{self._ack()}: {self.disp(s)} es {self.disp(val)}.", tipo="ack")
        for s in sujetos:
            f = self._nuevo(v="ser", s=self.can(s), neg=C.neg, t=C.tiempo, attr=list(C.attr), grado=C.grado, cuando=C.cuando, freq=C.freq, src=src, causa=causa, pl_suj=pl_suj or len(sujetos) > 1 and False)
            if C.comp:
                e2 = self.ent_de(C.comp[2]) if C.comp[2] is not None else None
                if e2 is None or isinstance(e2, list):
                    return None
                f["comp"] = [C.comp[0], C.comp[1], e2]
            if o is not None:
                for o1 in (o.coord or [o]):
                    if o1.propio or o1.pron or not o1.cab:
                        return None
                    if o1.det == "d" and not (s.startswith("K:")) and not o1.adjs:
                        return None
                    cl = self._canon_rel(o1.cab)[0] if o1.cab in REL_CANON else o1.cab
                    if s == "U" and not self.E["U"].get("gen") and cl.endswith("a") and ((cl[:-1] + "o") in self._profesiones() or "profesional" in conceptos.ancestros(cl[:-1] + "o")):
                        self.E["U"]["gen"] = "f"            # «Soy enfermera»: la persona habla en femenino
                    cl = M.masc(cl) if (cl.endswith("a") and self.gen(s) == "f" and (cl[:-1] + "o") in self._profesiones()) else cl
                    f["attr"].append(cl); f["isa"].append(cl)
                    if not o1.det and not o1.pl and self.es_persona(s) and cl not in FAMILIA and cl not in SIMETRICAS and cl not in INVERSAS and cl not in ("persona", "hombre", "niño", "chico", "señor"):
                        f["prof"] = True
                    if o1.det == "i":
                        f.setdefault("isa_art", {})[cl] = "un"
                        if s.startswith("N:") and not self.E[self.can(s)].get("clase") and not C.neg:
                            self.E[self.can(s)]["clase"] = cl
                    f["attr"].extend(a for a in o1.adjs if a not in f["attr"])
                    if o1.adjs:
                        f.setdefault("isa_adj", {})[cl] = list(o1.adjs)
                    if not self.E.get(self.can(s), {}).get("gen") and o1.gen and not s.startswith("K:"):
                        self.E[self.can(s)]["gen"] = o1.gen
            for p_, s_ in C.comps:
                e = self.ent_de(s_, papel="comp")
                if e is None or isinstance(e, list):
                    return None
                if p_ == "de" and (self.es_persona(e)) and not self.es_persona(s):
                    # posesión: «el coche es de Ana»
                    cl = self.E.get(self.can(s), {}).get("clase", "")
                    if not cl:
                        return None
                    if s.startswith("N:"):
                        inst = self.can(s)
                        self.E[inst]["dueno"] = self.can(e)
                        self._quita_rel_placeholder_de(cl, e)
                    else:
                        inst = self._ent("I:" + cl + "@" + self.can(e), clase=cl, dueno=self.can(e), gen=self.gen(s))
                    self._rel(cl, inst, e, src)
                    ft = self._nuevo(v="tener", s=self.can(e), obj=inst, obj_cls=cl, obj_disp=self._un(cl, self.gen(inst)), cuant=1, src=src)
                    nuevos.append(ft)
                    continue
                f["comps"].append([p_, e, s_.texto])
            if f["attr"] or f["comps"] or f["comp"] or (f["cuando"] and not s.startswith("N:") and s != "U"):
                nuevos.append(f)
        return True if nuevos else None

    def _profesiones(self):
        try:                                             # 2.12: más toda la jerarquía «profesional» de fábrica
            from .conceptos import kb as _kb, ancestros as _anc
            extra = {c for c in _kb()["isa"] if "profesional" in _anc(c)}
        except Exception:                                # noqa
            extra = set()
        return extra | {"medico", "profesor", "abogado", "ingeniero", "enfermero", "cocinero", "camarero", "arquitecto", "maestro", "veterinario", "fontanero", "carpintero", "bombero", "panadero",
                "peluquero", "mecanico", "psicologo", "biologo", "fisico", "quimico", "informatico", "secretario", "funcionario", "cartero", "jardinero", "granjero", "pescador", "pintor",
                "escritor", "actor", "director", "doctor", "conductor", "vendedor", "programador", "diseñador", "traductor", "investigador", "agricultor", "alumno", "niño", "chico", "amigo",
                "vecino", "abuelo", "tio", "primo", "hermano", "hijo", "novio", "esposo", "empleado", "gato", "perro", "cientifico", "matematico", "musico", "politico", "empresario", "obrero"}

    def _quita_rel_placeholder(self, inst):
        inst = self.can(inst)
        self.R = [q for q in self.R if self.can(q["x"]) != inst]

    def _quita_rel_placeholder_de(self, cl, dueno):
        dueno = self.can(dueno)
        ph = "I:" + cl + "@" + dueno
        self.R = [q for q in self.R if not (q["r"] == cl and self.can(q["x"]) == ph and self.can(q["y"]) == dueno)]

    def _tener(self, f, o: SN, s):
        s = self.can(s)
        if not o.cab and o.num is not None and not o.det and 0 < o.num < 125 and self.es_persona(s):
            f["obj_cls"] = "año"; f["cuant"] = o.num; f["obj_disp"] = f"{int(o.num) if o.num == int(o.num) else o.num} años"; f["pl_obj"] = True
            return True
        if not o.cab:
            return None
        cl, g = self._clase_sn(o)
        if o.cab in ("año", "ano") and o.num is not None:
            f["obj_cls"] = "año"; f["cuant"] = o.num; f["obj_disp"] = o.texto
            return True
        if o.cab in ESTADO_TENER and not o.det and o.num is None:
            f["obj_cls"] = o.cab; f["obj_disp"] = o.texto + (" de " + o.de.texto if o.de is not None else "")
            return True
        if o.propio or o.pron:
            return None
        if o.pl or o.num not in (None, 1) or (o.cuant and o.cuant != "otro") or (not o.det and not o.pos and o.num is None):
            f["obj"] = self._ent("K:" + cl, clase=cl, gen=o.gen or g or M.genero_sust(cl))
            f["obj_cls"] = cl; f["cuant"] = o.num; f["obj_disp"] = o.texto; f["pl_obj"] = True
            f["obj_gen"] = g or ("f" if o.gen == "f" else "")
            return True
        if o.de is not None or o.pos:
            e = self.ent_de(o)
            if e is None or isinstance(e, list):
                return None
            f["obj"] = e; f["obj_cls"] = cl; f["obj_disp"] = o.texto
            return True
        # instancia propia: «Ana tiene un perro»
        ya = [r["x"] for r in self.rels(cl, y=s)]
        if ya and o.det == "d":
            inst = ya[0]
        else:
            inst = "I:" + cl + ("#2" if o.cuant == "otro" else "") + "@" + s
            if o.apos:
                inst = "N:" + sa(o.apos)
                self._ent(inst, nombre=o.apos, clase=cl, dueno=s, gen=g or o.gen or None)
            else:
                self._ent(inst, clase=cl, dueno=s, gen=g or o.gen or M.genero_sust(cl))
            if not f.get("neg"):
                self._rel(cl, inst, s, f["src"], g)
                # «(Mi mujer y yo) tenemos una hija»: la hija también es de la pareja
                if cl == "hijo" and s == "U" and getattr(self, "_pers_clausula", "") == "1p":
                    pareja = [r["x"] for r in self.rels("esposo", y="U")]
                    if len(pareja) == 1:
                        self._rel(cl, inst, pareja[0], f["src"], g)
        self.E[self.can(inst)]["t_nuevo"] = self.turno
        f["obj"] = self.can(inst); f["obj_cls"] = cl; f["cuant"] = 1 if not f.get("neg") else None; f["obj_disp"] = o.texto
        f["obj_gen"] = g or ("f" if o.gen == "f" else "")
        if o.adjs and not f.get("neg"):
            extra = [a for a in o.adjs if a not in ("favorito", "preferido", "mejor", "mayor", "menor", "pequeño", "primero", "ultimo", "nuevo", "viejo")] or [a for a in o.adjs if a in ("nuevo", "viejo", "pequeño")]
            if extra:
                self._extra = getattr(self, "_extra", [])
                self._extra.append(self._nuevo(v="ser", s=self.can(inst), attr=extra, src=f["src"]))
        self._nuevo_ref = self.can(inst)
        return True

    def _ack(self):
        return ACK[self.turno % len(ACK)]

    # ------------------------------------------------------------------ grabación con vigencia, duplicados y efectos
    def _firma(self, f):
        return (f["v"], self.can(f["s"]) if f["s"] else None, bool(f.get("neg")), tuple(sorted(f.get("attr", []))), self.can(f["obj"]) if f.get("obj") else None, f.get("obj_cls", ""),
                f.get("cuant"), tuple((p, self.can(e) if e else d) for p, e, d in f.get("comps", [])), sa(f.get("xinf", "")), f.get("t", "pres") in ("pret", "imp"), sa(f.get("cuando", "")),
                tuple(f["comp"]) if f.get("comp") else None, sa(f.get("freq", "")), f.get("lugar_adv", ""), f.get("obj_gen", ""))

    def _mismo_asunto(self, a, b):
        """a y b hablan de lo mismo (salvo polaridad)."""
        if a["v"] != b["v"] or self.can(a["s"]) != self.can(b["s"]):
            return False
        if a.get("attr") or b.get("attr"):
            return bool(set(a.get("attr", [])) & set(b.get("attr", [])))
        if a.get("obj_cls") or b.get("obj_cls") or a.get("obj") or b.get("obj"):
            if a.get("obj") and b.get("obj") and self.can(a["obj"]) == self.can(b["obj"]):
                return True
            return bool(a.get("obj_cls")) and a.get("obj_cls") == b.get("obj_cls")
        if a.get("comps") or b.get("comps"):
            return any(p == p2 and ((e and e2 and self.can(e) == self.can(e2)) or sa(d) == sa(d2)) for p, e, d in a.get("comps", []) for p2, e2, d2 in b.get("comps", []))
        if a.get("xinf") or b.get("xinf"):
            return sa(a.get("xinf", "")) == sa(b.get("xinf", ""))
        return True

    def _graba(self, nuevos, C: Clausula, notas) -> Optional[dict]:
        self._suj_cl = None
        nuevos = list(nuevos) + getattr(self, "_extra", [])
        self._extra = []
        if not nuevos:
            return None
        ahora = "ahora" in C.marc or "corr" in C.marc
        repetidos, cambios, hechos = 0, [], []
        for f in nuevos:
            firma = self._firma(f)
            if any(self._firma(g) == firma and g.get("vig", True) for g in self.F):
                repetidos += 1
                continue
            pasado = f.get("t") in ("pret", "imp")
            conflicto = None
            # --- vigencia: valores únicos, correcciones, negaciones
            for g in self.F:
                if not g.get("vig", True) or self.can(g["s"]) != self.can(f["s"]) or g["v"] != f["v"]:
                    continue
                if not f.get("neg") and not g.get("neg") and f.get("obj") and g.get("obj") and self.can(f["obj"]) == self.can(g["obj"]) and g.get("turno", -9) >= self.turno - 6 \
                        and f.get("t") == g.get("t") and not g.get("attr") and not g.get("cuando") or (not f.get("neg") and not g.get("neg") and f.get("obj") and g.get("obj")
                        and self.can(f["obj"]) == self.can(g["obj"]) and g.get("turno", -9) >= self.turno - 6 and f.get("t") == g.get("t") and g.get("cuando") and g.get("cuando") == f.get("cuando")):
                    gc = {(p_, sa(d_ or "")) for p_, _, d_ in g.get("comps", [])}
                    fc = {(p_, sa(d_ or "")) for p_, _, d_ in f.get("comps", [])}
                    if gc < fc or (gc == fc and f.get("cuando") and not g.get("cuando")):
                        g["vig"] = False; g["refinado"] = True   # «Vamos a pintar la cocina… la pintaremos de blanco»: el segundo precisa el primero
                        continue
                if bool(g.get("neg")) != bool(f.get("neg")) and self._mismo_asunto(f, g) and not pasado:
                    g["vig"] = False; cambios.append(g); continue
                if f.get("neg") or g.get("neg") or pasado or g.get("t") in ("pret", "imp", "fut"):
                    continue
                # atributos excluyentes: colores y contrarios
                if f.get("attr") and g.get("attr") and f["v"] in ("ser", "estar"):
                    fa, ga = set(f["attr"]), set(g["attr"])
                    choque = (fa & COLORES and ga & COLORES and not (fa & ga)) or any(a in _ANT.get(b, ()) for a in fa for b in ga)
                    if choque and not ahora and "ya" not in C.marc and "corr" not in C.marc and not f.get("cuando") and len(nuevos) == 1:
                        conflicto = g
                        continue
                    if choque or ("corr" in C.marc and g is self.ult_marco):
                        g["vig"] = False; cambios.append(g)
                    continue
                # complementos de valor único (vivir en, estar en...) o marcados con «ahora»
                for p, e, d in f.get("comps", []):
                    if ((f["v"], p) in FUNC_SIEMPRE or (ahora and (f["v"], p) in FUNCIONAL) or ("corr" in C.marc and g is self.ult_marco)) and any(p2 == p for p2, _, _ in g.get("comps", [])) \
                            and not any(p2 == p and e2 and e and self.can(e2) == self.can(e) for p2, e2, _ in g.get("comps", [])) and not f.get("obj") and not g.get("obj"):
                        g["vig"] = False; cambios.append(g)
                        break
                if f["v"] == "estar" and f.get("lugar_adv") and g.get("comps") or f["v"] == "estar" and f.get("comps") and g.get("lugar_adv"):
                    g["vig"] = False
                # edad y cantidades del mismo tipo
                if f["v"] == "tener" and f.get("obj_cls") and f.get("obj_cls") == g.get("obj_cls") and f.get("obj_gen", "") == g.get("obj_gen", "") and g.get("turno") != f.get("turno") and f.get("cuant") is not None and g.get("cuant") is not None and f["cuant"] != g["cuant"] \
                        and (f["obj_cls"] == "año" or ahora or "ya" in C.marc or True) and g.get("vig", True) and self._es_conteo(f) and self._es_conteo(g):
                    g["vig"] = False; cambios.append(g)
                if "corr" in C.marc and g is self.ult_marco and g.get("vig", True) and (f.get("obj_cls") or f.get("obj")) and (g.get("obj_cls") or g.get("obj")) and not self._mismo_asunto(f, g):
                    g["vig"] = False; cambios.append(g)
            if "corr" in C.marc and getattr(self, "_corr_error", False):
                for g in cambios:
                    if g.get("turno", 0) >= self.turno - 6:
                        g["erroneo"] = True             # «Perdona, vive en Cuenca»: lo de antes fue un error, no un cambio
            if conflicto is not None:
                self.pend = {"tipo": "conflicto", "nuevo": f, "viejo": conflicto, "turno": self.turno}
                self.mencionar(f["s"]); self.ult_suj = self.can(f["s"])
                return {"respuesta": f"Antes me dijiste que {self.frase(conflicto)}. ¿Cuál vale: la anterior o la nueva?", "estado": "aclara", "consultar": False, "tipo": "aclara"}
            if getattr(self, "_suj_txt", "") and not f.get("suj_txt") and f is nuevos[0]:
                f["suj_txt"] = self._suj_txt; f["pl_suj"] = True
            self.F.append(f)
            hechos.append(f)
            self._espejo(f)
            self._efectos(f, C)
        for g in cambios:
            self._espejo(g, quitar=True)
        # --- foco del discurso
        for f in nuevos:
            if f["s"]:
                self.mencionar(f["s"])
            if f.get("obj") and not str(f["obj"]).startswith("K:"):
                self.mencionar(f["obj"])
            for p, e, d in f.get("comps", []):
                if e and not str(e).startswith("K:") and self.es_persona(e):
                    self.mencionar(e)
        for f in nuevos:                              # «la boda de mi hermano»: el hermano también queda mencionado
            for e_ in [f.get("obj")] + [e for _, e, _ in f.get("comps", [])]:
                du_ = self.E.get(self.can(e_), {}).get("dueno") if e_ else None
                if du_ and self.es_persona(du_) and self.can(du_) not in ("U", "L"):
                    self.mencionar(du_)
        if nuevos[0]["s"]:
            self.mencionar(nuevos[0]["s"])
        self.ult_suj = self.can(nuevos[0]["s"]) if nuevos[0]["s"] else self.ult_suj
        self._afirma_de = self.ult_suj
        self.foco_ajeno = False                         # el núcleo ha entendido esta frase: el tema vuelve a ser suyo
        for txt_ in getattr(self, "_menc_frase", []):   # «fui a ver a mi abuelo»: el abuelo pasa a estar en foco
            try:
                sn_ = self._sn_de(txt_)
                e_ = self.ent_de(sn_, crear=False) if sn_ is not None else None
                if isinstance(e_, str) and e_.startswith("?I:"):
                    cl_, du_ = e_[3:].split("@", 1)
                    usado = any(d.get("clase") == cl_ and self.can(d.get("dueno") or "") == du_ for k, d in self.E.items() if k not in self.eq)
                    e_ = None if usado else self.ent_de(sn_)
                ya_ = set()
                for f_ in nuevos:
                    for x_ in [f_.get("s"), f_.get("obj")] + [c_[1] for c_ in f_.get("comps", [])]:
                        if x_:
                            ya_.add(self.can(x_)); ya_.add(self.can(self.E.get(self.can(x_), {}).get("dueno") or ""))
                if isinstance(e_, str) and e_ not in ("U", "L") and not e_.startswith("?") and self.can(e_) not in ya_:
                    self.mencionar(e_)
            except Exception:                            # noqa
                pass
        self._menc_frase = []
        nr = getattr(self, "_nuevo_ref", None)
        self.ult_nuevo = nr if nr else None
        if nr:
            self.E[self.can(nr)]["t_nuevo"] = self.turno
        self._nuevo_ref = None
        self.ult_marco = hechos[-1] if hechos else self.ult_marco
        self.ult_just = {"dicho": [nuevos[0]["src"]]}
        if not hechos:
            return self._ok(["Sí, eso ya me lo habías dicho.", "Sí, ya lo sabía."][self.turno % 2], tipo="ack")
        txt = self._parafrasis(hechos)
        previos = [g for g in cambios if not g.get("neg") and not any(h.get("neg") for h in hechos)]
        if previos and not any(h.get("neg") for h in hechos):
            ant = self._lista([self.frase(g, tiempo="imp", sin_sujeto=True, antes=False) for g in previos[:2]])
            pref = "Corregido" if "corr" in C.marc else self._ack()
            return self._ok(f"{pref}: {txt} (antes me dijiste que {ant}).", tipo="ack")
        if cambios and any(h.get("neg") for h in hechos):
            return self._ok(f"{self._ack()}, lo actualizo: {txt}.", tipo="ack")
        if cambios:
            return self._ok(f"{self._ack()}, lo actualizo: {txt}.", tipo="ack")
        return self._ok(f"{'Corregido' if 'corr' in C.marc else self._ack()}: {txt}.", tipo="ack")

    @staticmethod
    def _es_conteo(f):
        return f.get("cuant") is not None and (f.get("pl_obj") or f.get("obj_cls") == "año")

    def _parafrasis(self, hechos):
        # agrupa sujetos u objetos coordinados para no repetir
        if len(hechos) > 1 and len({(h["v"], self.can(h["s"]), bool(h.get("neg"))) for h in hechos}) == 1 and all(h.get("obj_disp") for h in hechos) \
                and len({(str([(p, d) for p, e, d in h.get("comps", [])]), h.get("cuando") or "", h.get("freq") or "") for h in hechos}) == 1:
            h = dict(hechos[0]); h["obj_disp"] = self._lista([x["obj_disp"] for x in hechos]); h["pl_obj"] = True
            return self.frase(h)
        if len(hechos) > 1 and len({(h["v"], tuple(h.get("attr", [])), h.get("obj_disp"), str(h.get("comps"))) for h in hechos}) == 1 and not hechos[0].get("exp"):
            h = dict(hechos[0]); h["pl_suj"] = True
            fr = self.frase(h, sin_sujeto=True)
            return self._lista([self.disp(x["s"]) for x in hechos]) + " " + fr
        return "; ".join(self.frase(h) for h in hechos[:3])

    def _efectos(self, f, C: Clausula):
        v, s = f["v"], self.can(f["s"])
        if f.get("neg") or f.get("t") == "fut" or f.get("modal") or f.get("xinf"):
            return
        obj = self.can(f["obj"]) if f.get("obj") else None
        dest = [e for p, e, d in f.get("comps", []) if p == "a" and e] if (v in DAR and obj) else []
        if v in DAR and obj and dest:
            if dest:
                d0 = self.can(dest[0])
                self._retira_tener(s, obj, f)
                self.F.append(self._nuevo(v="tener", s=d0, obj=obj, obj_cls=f.get("obj_cls", ""), obj_disp=f.get("obj_disp", ""), cuant=f.get("cuant") or 1, src=f["src"], efecto=True))
                if obj.startswith("I:") or obj.startswith("N:"):
                    self.E[obj]["dueno_act"] = d0
        elif v in OBTENER and obj:
            if not any(self.can(g.get("obj") or "") == obj and g["v"] == "tener" and self.can(g["s"]) == s and g.get("vig", True) and not g.get("neg") for g in self.F):
                self.F.append(self._nuevo(v="tener", s=s, obj=obj, obj_cls=f.get("obj_cls", ""), obj_disp=f.get("obj_disp", ""), cuant=f.get("cuant") or (None if f.get("pl_obj") else 1), src=f["src"], efecto=True, pl_obj=f.get("pl_obj", False)))
        elif v in PERDER and obj and v not in ("regalar", "vender"):
            self._retira_tener(s, obj, f)
            if v in ("perder",) and not obj.startswith("K:") and not any(g["v"] == "tener" and g.get("neg") and self.can(g.get("obj") or "") == obj and g.get("turno") == self.turno for g in self.F):
                self.F.append(self._nuevo(v="tener", s=s, neg=True, obj=obj, obj_cls=f.get("obj_cls", ""), obj_disp=f.get("obj_disp", ""), src=f["src"], efecto=True,
                                          por=self.frase(f)))
        elif v in ("regalar", "vender") and obj:
            self._retira_tener(s, obj, f)
        if v in IR and f.get("t") in ("pres", "pret"):
            for p, e, d in f.get("comps", []):
                if p == "a" and e and f.get("t") == "pret" or p == "a" and e and "ahora" in C.marc:
                    for g in self.F:
                        if g["v"] == "estar" and self.can(g["s"]) == s and g.get("vig", True) and any(p2 == "en" for p2, _, _ in g.get("comps", [])):
                            g["vig"] = False
                    self.F.append(self._nuevo(v="estar", s=s, comps=[["en", e, d]], src=f["src"], efecto=True))
        # el destino de un viaje ya hecho o en curso hacia un lugar con nombre: «Ana va a Madrid», «Ana llega a Sevilla»
        if v in ("ir", "llegar", "volver", "regresar", "entrar") and f.get("t") == "pres" and not f.get("freq") and not f.get("cuando") and "ahora" not in C.marc and not f.get("refl"):
            for p, e, d in f.get("comps", []):
                if p in ("a", "en") and e and (str(e).startswith("N:") or v != "ir"):
                    for g in self.F:
                        if g["v"] == "estar" and self.can(g["s"]) == s and g.get("vig", True) and any(p2 == "en" for p2, _, _ in g.get("comps", [])):
                            g["vig"] = False
                    self.F.append(self._nuevo(v="estar", s=s, comps=[["en", e, d]], src=f["src"], efecto=True))
        # estado en que queda el objeto: «Ana rompe el vaso» -> el vaso está roto
        est = conceptos.kb()["efectos"].get(v)
        if est and obj and f.get("t") in ("pres", "pret") and not f.get("freq") and re.match(r"^(?:el|la|los|las|mi|tu|su|mis|tus|sus|este|esta|ese|esa) ", f.get("obj_disp", "") + " ") or est and obj and str(obj).startswith(("N:", "I:")) and f.get("t") in ("pres", "pret") and not f.get("freq"):
            for g in self.F:
                if g["v"] in ("estar", "ser") and self.can(g["s"]) == obj and g.get("vig", True) and g.get("attr") and (set(g["attr"]) & (_ANT.get(est, set()) | {est}) or g.get("efecto")):
                    g["vig"] = False
            self.F.append(self._nuevo(v="estar", s=obj, attr=[est], src=f["src"], efecto=True))
        if v == "estar" and set(f.get("attr", [])) & {"casado"} or v == "casar" and f.get("refl"):
            for p, e, d in f.get("comps", []):
                if p == "con" and e:
                    self._rel("esposo", e, s, f["src"])
                    self._rel("esposo", s, e, f["src"])
        if v in ("poner", "dejar", "colocar", "guardar", "meter") and obj and f.get("t") in ("pres", "pret"):
            lug = [[p, e, d] for p, e, d in f.get("comps", []) if p in ("en", "sobre", "dentro_de", "encima_de", "debajo_de", "detras_de", "delante_de", "al_lado_de", "junto_a", "cerca_de", "entre", "bajo")]
            if lug:
                for g in self.F:
                    if g["v"] == "estar" and self.can(g["s"]) == obj and g.get("vig", True) and g.get("comps"):
                        g["vig"] = False
                self.F.append(self._nuevo(v="estar", s=obj, comps=lug, src=f["src"], efecto=True))
        if v == "mudar" and f.get("refl"):
            for p, e, d in f.get("comps", []):
                if p == "a" and e:
                    for g in self.F:
                        if g["v"] == "vivir" and self.can(g["s"]) == s and g.get("vig", True):
                            g["vig"] = False
                    self.F.append(self._nuevo(v="vivir", s=s, comps=[["en", e, d]], src=f["src"], efecto=True))

    def _retira_tener(self, s, obj, f):
        tenia = False
        for g in self.F:
            if g["v"] == "tener" and self.can(g["s"]) == s and g.get("vig", True) and not g.get("neg") and (self.can(g.get("obj") or "") == obj or (g.get("obj_cls") and g.get("obj_cls") == f.get("obj_cls") and g.get("cuant") in (None, 1))):
                g["vig"] = False; tenia = True
        self.F.append(self._nuevo(v="tener", s=s, obj=obj, obj_cls=f.get("obj_cls", ""), obj_disp=f.get("obj_disp", ""), neg=True, src=f["src"], efecto=True, por=self.frase(f)))
