"""Logica de la interfaz web, SIN HTTP (se prueba sola). Un Motor sostiene la memoria, la conversacion y los cartuchos; todo acceso va bajo un cerrojo."""
import copy
import json
import os
import re
import tempfile
import threading
import time
import unicodedata
from datetime import date

from src.memory import cartuchos
from src.memory.store import MemoryStore

SECCIONES_OK = ("hechos", "alias", "verb_isa", "defs", "surface", "display", "opposites", "fuente", "creado", "nombre", "version", "frases", "no_entendidas", "descripcion")
MAX_CARTUCHO = 8_000_000
SUGERENCIAS = ["¿Qué es un perro?", "¿Para qué sirve un martillo?", "¿Cuál no encaja: perro, gato, mesa?", "¿Qué relación hay entre un perro y un lobo?", "Dime cinco frutas",
               "¿Cuántos planetas hay?", "¿Qué día fue hace 4 días?", "¿Qué significa feliz?", "El perro de Ana se llama Rex.", "¿Cómo se dice casa en inglés?"]


def _nrm(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


def nombre_seguro(n):
    n = re.sub(r"[^a-z0-9_\-]+", "_", _nrm(n).strip()).strip("_")[:48]
    return n if n and n != "activos" else ""


class Motor:
    def __init__(self, mem, parser, carpeta_cartuchos="cartuchos", fabrica=None):
        self.mem, self.parser, self.base = mem, parser, carpeta_cartuchos
        self.lock = threading.RLock()
        self.conv = self._nueva_conv()
        self.inicio = time.time()
        self.fabrica = fabrica or {}

    # ---- construccion ------------------------------------------------------------------------------------------------
    @staticmethod
    def crear(ruta_memoria="memory/lcm_memory.json", carpeta_cartuchos="cartuchos", parser=None, semilla=True, log=print):
        mem = MemoryStore(ruta_memoria)
        mem.today = date.today()
        if parser is not None:
            parser.today = mem.today
        n_sem = 0
        if semilla and parser is not None:
            try:
                from src.language.semilla import load_seed
                n_sem = load_seed(mem, parser)
            except Exception as e:                                             # noqa
                log(f"[semilla] no se pudo cargar: {e!r}")
        m = Motor(mem, parser, carpeta_cartuchos)
        try:
            for n, k in cartuchos.montar(mem, carpeta_cartuchos):
                log(f"[cartucho] {n}: " + (f"{k} hechos" if k is not None else "NO ENCONTRADO"))
        except Exception as e:                                                 # noqa
            log(f"[cartucho] no se pudieron montar: {e!r}")
        if n_sem:
            mem.save()
        return m

    def _nueva_conv(self):
        from src.language.dialogue import Conversation
        from src.language.qa import QA
        from src.reasoning.lessons import deduce_all
        return Conversation(self.mem, self.parser, lambda m, p: QA(m, p.parse, lambda facts: deduce_all(facts, m.active_lessons())))

    # ---- utilidades ---------------------------------------------------------------------------------------------------
    def _disp(self, k):
        v = self.mem.display.get(k)
        return v if v else str(k).replace("_", " ").lower()

    @staticmethod
    def _tit(s):
        return s[:1].upper() + s[1:] if s else s

    def _origen(self, f):
        if f.get("cart"):
            return f["cart"]
        return "fábrica" if f.get("source") == "semilla" else "personal"

    def _texto(self, f):
        try:
            from src.language.qa import QA
            return QA(self.mem, None, None).say((f["s"], f["p"], f["o"]), bool(f.get("neg")))
        except Exception:                                                      # noqa
            return f"{self._disp(f['s'])} {str(f['p']).lower().replace('_', ' ')} {self._disp(f['o'])}"

    def _fila(self, f):
        return {"s": f["s"], "p": f["p"], "o": f["o"], "neg": bool(f.get("neg")), "origen": self._origen(f), "texto": self._texto(f), "archivado": bool(f.get("archived")),
                "sd": self._tit(self._disp(f["s"])), "pd": str(f["p"]).lower().replace("_", " "), "od": self._disp(f["o"]), "cuando": f.get("when_disp") or f.get("when") or "", "veces": f.get("n", 1), "por": f.get("por", ""), "peso": f.get("peso", 0)}

    def _claves(self):
        return {(f["s"], f["p"], f["o"], bool(f.get("neg"))) for f in self.mem.facts}

    def _es_clase(self, k):
        try:
            from src.language import conceptos
            return bool(conceptos._es_clase(self.mem, k))
        except Exception:                                                      # noqa
            return False

    # ---- conversacion -------------------------------------------------------------------------------------------------
    def chat(self, texto):
        texto = (texto or "").strip()
        if not texto:
            return {"error": "Escribe algo."}
        from src.language.lector import MAX_TEXTO
        if len(texto) > MAX_TEXTO:
            return {"error": f"Texto demasiado largo (máx. {MAX_TEXTO:,} caracteres): pártelo en dos.".replace(",", ".")}
        with self.lock:
            antes = self._claves()
            n0 = len(self.mem.facts)
            t0 = time.time()
            try:
                resp = self.conv.say(texto)
            except Exception as e:                                             # noqa
                return {"error": f"No he podido procesar eso ({type(e).__name__})."}
            nuevos = [self._fila(f) for f in self.mem.facts if (f["s"], f["p"], f["o"], bool(f.get("neg"))) not in antes][:40]
            try:
                self.mem.save()
            except OSError:
                pass
            from src.language.consultas import es_fallo
            return {"respuesta": resp, "aprendido": nuevos, "fallo": bool(es_fallo(resp)), "ms": int((time.time() - t0) * 1000), "hechos": len(self.mem.facts), "delta": len(self.mem.facts) - n0}

    def aprender(self, texto):
        """parche-113: aprende de un texto largo (pegado o subido). Devuelve el informe completo: hechos con su frase de origen y frases no entendidas."""
        texto = (texto or "").strip()
        from src.language.lector import MAX_TEXTO, resumen
        from src.language.lector_ud import lector_para
        if len(texto) < 20:
            return {"error": "Pega un texto (al menos una frase)."}
        if len(texto) > MAX_TEXTO:
            return {"error": f"Texto demasiado largo (máx. {MAX_TEXTO:,} caracteres): pártelo en dos.".replace(",", ".")}
        with self.lock:
            t0 = time.time()
            n0 = len(self.mem.facts)

            def escuela(cl, tema):
                try:
                    return self.parser.parse(cl, self.conv.topic) or []
                except Exception:                                                  # noqa
                    return []
            rep = lector_para(self.mem, self.parser).leer(texto)
            try:
                self.mem.save()
            except OSError:
                pass
            hs = [{"sd": self._tit(h["sd"]), "pd": h["p"].lower().replace("_", " "), "od": h["od"], "s": h["s"], "p": h["p"], "o": h["o"], "neg": h["neg"], "frase": h["frase"], "via": h["via"], "nuevo": h["nuevo"]}
                  for h in rep["hechos"]]
            return {"ok": True, "frases": rep["frases"], "caracteres": rep["caracteres"], "nuevos": rep["nuevos"], "hechos": hs, "titulos": rep["titulos"][:50],
                    "sin_entender": rep["sin_entender"][:200], "resumen": resumen(rep), "ms": int((time.time() - t0) * 1000), "total": len(self.mem.facts), "delta": len(self.mem.facts) - n0}

    def nueva_conversacion(self):
        with self.lock:
            self.conv = self._nueva_conv()
        return {"ok": True}

    # ---- estado / memoria ---------------------------------------------------------------------------------------------
    def estado(self):
        with self.lock:
            fs = self.mem.facts
            por = {"fábrica": 0, "personal": 0, "cartuchos": 0}
            for f in fs:
                o = self._origen(f)
                por["cartuchos" if f.get("cart") else o] += 1
            ents = set()
            for f in fs:
                ents.add(f["s"])
                ents.add(f["o"])
            try:
                from src.language import conceptos
                dic = conceptos.total() if conceptos.disponible() else 0
            except Exception:                                                  # noqa
                dic = 0
            act = cartuchos.activos(self.base)
            return {"hechos": len(fs), "por_origen": por, "entidades": len(ents), "predicados": len({f["p"] for f in fs}), "lecciones": len(self.mem.lessons), "cartuchos_activos": len(act),
                    "cartuchos_total": len(cartuchos.listar(self.base)), "diccionario": dic, "hoy": str(getattr(self.mem, "today", None) or date.today()), "activo_desde": int(time.time() - self.inicio),
                    "escuela": self.parser is not None, "nexos": len(getattr(self.mem, "nexos", []))}

    def hechos(self, q="", origen="", n=60, pag=0):
        with self.lock:
            qq = _nrm(q)
            out = []
            for f in self.mem.facts:
                if origen and self._origen(f) != origen:
                    continue
                if qq and qq not in _nrm(f"{f['s']} {f['p']} {f['o']} {self._disp(f['s'])} {self._disp(f['o'])}"):
                    continue
                out.append(f)
            tot = len(out)
            n = max(1, min(int(n), 200))
            page = out[int(pag) * n:(int(pag) + 1) * n]
            return {"total": tot, "filas": [self._fila(f) for f in page]}

    def olvidar(self, s, p, o):
        with self.lock:
            tr = (str(s).upper(), str(p).upper(), str(o).upper())
            tocados = [f for f in self.mem.facts if (f["s"], f["p"], f["o"]) == tr]
            if not tocados:
                return {"error": "No encuentro ese hecho."}
            if any(f.get("cart") or f.get("source") == "semilla" for f in tocados):
                return {"error": "Ese hecho viene de fábrica o de un cartucho: retira el cartucho en vez de borrarlo."}
            self.mem.forget_fact(tr)
            self.mem.save()
            return {"ok": True, "hechos": len(self.mem.facts)}

    # ---- conceptos ----------------------------------------------------------------------------------------------------
    def _indice(self):
        ent = {}
        for f in self.mem.facts:
            for k, lado in ((f["s"], "out"), (f["o"], "in")):
                e = ent.setdefault(k, {"out": 0, "in": 0, "orig": set(), "cl": set()})
                e[lado] += 1
                e["orig"].add(self._origen(f))
            if str(f["p"]).upper() == "ES" and not f.get("neg"):
                ent[f["s"]]["cl"].add(f["o"])
        return ent

    def conceptos(self, q="", tipo="", origen="", n=80, pag=0):
        with self.lock:
            ent = self._indice()
            qq = _nrm(q)
            res = []
            for k, e in ent.items():
                if qq and qq not in _nrm(self._disp(k) + " " + k):
                    continue
                cl = self._es_clase(k)
                if tipo == "clase" and not cl or tipo == "entidad" and cl:
                    continue
                if origen and origen not in e["orig"]:
                    continue
                res.append({"k": k, "nombre": self._tit(self._disp(k)), "tipo": "clase" if cl else "entidad", "sale": e["out"], "entra": e["in"], "origen": sorted(e["orig"]),
                            "es": [self._tit(self._disp(c)) for c in sorted(e["cl"])][:3]})
            res.sort(key=lambda r: (-(r["sale"] + r["entra"]), r["nombre"]))
            n = max(1, min(int(n), 300))
            return {"total": len(res), "filas": res[int(pag) * n:(int(pag) + 1) * n]}

    def _cadena(self, k, limite=8):
        out, vistos, cur = [], {k}, [k]
        for _ in range(limite):
            nxt = []
            for x in cur:
                for f in self.mem.facts:
                    if f["s"] == x and str(f["p"]).upper() == "ES" and not f.get("neg") and f["o"] not in vistos:
                        vistos.add(f["o"])
                        nxt.append(f["o"])
                        out.append(f["o"])
            if not nxt:
                break
            cur = nxt
        return out

    def concepto(self, k):
        with self.lock:
            k = str(k).upper()
            sal, ent = {}, {}
            for f in self.mem.facts:
                if f["s"] == k:
                    sal.setdefault(str(f["p"]).lower().replace("_", " "), []).append(self._fila(f))
                if f["o"] == k:
                    ent.setdefault(str(f["p"]).lower().replace("_", " "), []).append(self._fila(f))
            nex = [dict(self._fila(h), sale=h["s"] == k) for h in getattr(self.mem, "nexos", []) if k in (h["s"], h["o"])]
            if not sal and not ent and not nex:
                return {"error": "No tengo ese concepto en la memoria."}
            nombre = self._disp(k)
            cl = self._es_clase(k)
            ficha = ""
            extra = {}
            try:
                from src.language import conceptos, definiciones
                pal = re.sub(r"^(?:el|la|los|las|un|una)\s+", "", nombre)
                if conceptos.disponible():
                    ficha = conceptos.describir(pal, self.mem) or ""
                    cs = conceptos.conceptos(pal)
                    if cs and definiciones.disponible():
                        f_ = definiciones.funcion(cs[0], pal)
                        if f_:
                            extra["sirve_para"] = f_
                        co = definiciones.contrarios(cs[0])
                        if co:
                            extra["contrarios"] = co[:4]
                        rel = definiciones.relacionados(cs[0], 6)
                        if rel:
                            extra["relacionados"] = rel
            except Exception:                                                  # noqa
                pass
            hij = sorted({f["s"] for f in self.mem.facts if f["o"] == k and str(f["p"]).upper() == "ES" and not f.get("neg")})
            return {"k": k, "nombre": self._tit(nombre), "tipo": "clase" if cl else "entidad", "sale": sal, "entra": ent, "cadena": [{"k": c, "nombre": self._tit(self._disp(c))} for c in self._cadena(k)],
                    "subtipos": [{"k": c, "nombre": self._tit(self._disp(c))} for c in hij[:40]], "nexos": nex, "ficha": ficha, "diccionario": extra, "origen": sorted({r["origen"] for v in list(sal.values()) + list(ent.values()) for r in v})}

    def grafo(self, k=None, prof=1, maximo=45):
        with self.lock:
            fs = [f for f in self.mem.facts if not f.get("archived")]
            if k:
                k = str(k).upper()
                nodos, front = {k}, {k}
                aristas = []
                for _ in range(max(1, min(int(prof), 2))):
                    nuevo = set()
                    for f in fs:
                        if f["s"] in front or f["o"] in front:
                            aristas.append(f)
                            for x in (f["s"], f["o"]):
                                if x not in nodos and len(nodos) < maximo:
                                    nodos.add(x)
                                    nuevo.add(x)
                    front = nuevo
                aristas = [f for f in aristas if f["s"] in nodos and f["o"] in nodos]
            else:
                grado = {}
                for f in fs:
                    for x in (f["s"], f["o"]):
                        grado[x] = grado.get(x, 0) + 1
                nodos = {x for x, _ in sorted(grado.items(), key=lambda t: -t[1])[:maximo]}
                aristas = [f for f in fs if f["s"] in nodos and f["o"] in nodos]
            if k:                                                              # parche-111: los nexos de la reflexion tambien se dibujan (a trazos finos)
                for h in getattr(self.mem, "nexos", []):
                    if (h["s"] == k or h["o"] == k) and len(nodos) < maximo + 12:
                        nodos.add(h["s"])
                        nodos.add(h["o"])
                        aristas.append(h)
            seen, ar = set(), []
            for f in aristas:
                kk = (f["s"], f["p"], f["o"])
                if kk not in seen and len(ar) < 160:
                    seen.add(kk)
                    ar.append({"a": f["s"], "b": f["o"], "p": str(f["p"]).lower().replace("_", " "), "neg": bool(f.get("neg")), "nexo": f.get("cart") == "reflexion"})
            return {"centro": k, "nodos": [{"k": x, "nombre": self._tit(self._disp(x)), "tipo": "clase" if self._es_clase(x) else "entidad"} for x in sorted(nodos)], "aristas": ar}

    def diccionario(self, q):
        q = (q or "").strip()
        if not q:
            return {"error": "Escribe una palabra."}
        with self.lock:
            try:
                from src.language import conceptos, definiciones
                if not conceptos.disponible():
                    return {"error": "El diccionario de conceptos no está instalado."}
                pal = re.sub(r"^(?:el|la|los|las|un|una)\s+", "", q.lower())
                ficha = conceptos.describir(pal, self.mem)
                cs = conceptos.conceptos(pal)
                extra = {}
                if cs:
                    f_ = definiciones.funcion(cs[0], pal)
                    if f_:
                        extra["sirve_para"] = f_
                    co = definiciones.contrarios(cs[0])
                    if co:
                        extra["contrarios"] = co[:5]
                    tp = conceptos.tipos(cs[0], 8)
                    if tp:
                        extra["tipos"] = tp
                    pt = conceptos.partes(cs[0], "parte", 8)
                    if pt:
                        extra["partes"] = pt
                try:
                    from src.language import lexico
                    sin = lexico.sinonimos(pal) if lexico.disponible() else []
                except Exception:                                              # noqa
                    sin = []
                if sin:
                    extra["sinonimos"] = sin[:8]
                return {"palabra": q, "ficha": ficha or "", "extra": extra, "sentidos": len(cs)} if (ficha or extra) else {"error": f"No encuentro «{q}» en el diccionario."}
            except Exception as e:                                             # noqa
                return {"error": f"No he podido consultar el diccionario ({type(e).__name__})."}

    # ---- cartuchos ----------------------------------------------------------------------------------------------------
    def cartuchos(self):
        with self.lock:
            act = set(cartuchos.activos(self.base))
            out = []
            for n, a, nh, fuente in cartuchos.listar(self.base):
                c = cartuchos.cargar(n, self.base) or {}
                try:
                    kb = os.path.getsize(os.path.join(self.base, n + ".json")) // 1024
                except OSError:
                    kb = 0
                out.append({"nombre": n, "activo": n in act, "hechos": nh, "fuente": fuente, "creado": c.get("creado", ""), "frases": c.get("frases"), "kb": kb,
                            "descripcion": c.get("descripcion", ""), "no_entendidas": len(c.get("no_entendidas", []) or [])})
            perso = [f for f in self.mem.facts if not f.get("cart") and f.get("source") != "semilla"]
            return {"cartuchos": out, "personal": len(perso), "fabrica": sum(1 for f in self.mem.facts if f.get("source") == "semilla" and not f.get("cart"))}

    def _remontar(self):
        cartuchos.montar(self.mem, self.base)
        self.conv = self._nueva_conv()

    def reflexionar(self):
        """El LCM repasa todos sus conceptos y descubre nexos (src/language/reflexion.py); guarda y monta el cartucho `reflexion`."""
        from src.language import reflexion
        with self.lock:
            res = reflexion.reflexionar(self.mem)
            if res["informe"].get("error"):
                return {"error": res["informe"]["error"]}
            reflexion.guardar(res, self.mem, self.base)
            self._remontar()
            return {"ok": True, "informe": res["informe"], "hechos": len(self.mem.facts)}

    def reflexion_informe(self):
        with self.lock:
            c = cartuchos.cargar("reflexion", self.base)
            return {"informe": (c or {}).get("informe"), "activo": "reflexion" in cartuchos.activos(self.base)}

    def cartucho_activar(self, nombre, activo):
        with self.lock:
            nombre = nombre_seguro(nombre)
            ok = cartuchos.insertar(nombre, self.base) if activo else cartuchos.retirar(nombre, self.base)
            if not ok:
                return {"error": "Nada que hacer (no existe o ya estaba así)."}
            self._remontar()
            return {"ok": True, "hechos": len(self.mem.facts)}

    def cartucho_descargar(self, nombre):
        nombre = nombre_seguro(nombre)
        p = os.path.join(self.base, nombre + ".json")
        if not nombre or not os.path.isfile(p):
            return None
        with open(p, "rb") as fh:
            return nombre + ".json", fh.read()

    def cartucho_ver(self, nombre, n=40):
        c = cartuchos.cargar(nombre_seguro(nombre), self.base)
        if c is None:
            return {"error": "No existe ese cartucho."}
        with self.lock:
            hs = [{"texto": self._texto(f), "neg": bool(f.get("neg"))} for f in c.get("hechos", [])[:n]]
        return {"nombre": c.get("nombre"), "hechos": len(c.get("hechos", [])), "muestra": hs, "fuente": c.get("fuente", ""), "creado": c.get("creado", "")}

    def cartucho_subir(self, nombre, contenido, sobrescribir=False):
        with self.lock:
            if isinstance(contenido, str):
                try:
                    contenido = json.loads(contenido)
                except ValueError:
                    return {"error": "El fichero no es un JSON válido."}
            if not isinstance(contenido, dict) or not isinstance(contenido.get("hechos"), list):
                return {"error": "No parece un cartucho del LCM (falta la lista «hechos»)."}
            if len(contenido["hechos"]) > 60000:
                return {"error": "Cartucho demasiado grande."}
            for f in contenido["hechos"]:
                if not isinstance(f, dict) or not all(isinstance(f.get(x), str) and f.get(x) for x in ("s", "p", "o")):
                    return {"error": "Hay hechos mal formados (cada uno necesita s, p, o)."}
            nom = nombre_seguro(nombre or contenido.get("nombre", ""))
            if not nom:
                return {"error": "Nombre no válido (usa letras, números, _ o -)."}
            if os.path.exists(os.path.join(self.base, nom + ".json")) and not sobrescribir:
                return {"error": f"Ya existe «{nom}». Marca «sobrescribir» o cambia el nombre.", "existe": True}
            limpio = {k: v for k, v in contenido.items() if k in SECCIONES_OK}
            limpio["hechos"] = [{k: v for k, v in f.items() if k != "cart"} for f in contenido["hechos"]]
            for sec in ("alias", "verb_isa", "defs", "surface", "display"):
                if not isinstance(limpio.get(sec, {}), dict):
                    limpio.pop(sec, None)
            meta = {k: limpio.pop(k) for k in ("fuente", "descripcion", "frases", "no_entendidas") if k in limpio}
            for k in ("nombre", "creado", "version"):
                limpio.pop(k, None)
            meta.setdefault("fuente", "subido desde la interfaz web")
            cartuchos.guardar_cartucho(nom, limpio, meta, self.base)
            return {"ok": True, "nombre": nom, "hechos": len(limpio["hechos"])}

    def cartucho_borrar(self, nombre):
        with self.lock:
            nombre = nombre_seguro(nombre)
            if not nombre or not cartuchos.borrar(nombre, self.base):
                return {"error": "No existe ese cartucho."}
            self._remontar()
            return {"ok": True}

    def cartucho_desde_memoria(self, nombre, descripcion=""):
        with self.lock:
            nom = nombre_seguro(nombre)
            if not nom:
                return {"error": "Nombre no válido."}
            hs = [{k: v for k, v in f.items() if k != "cart"} for f in self.mem.facts if not f.get("cart") and f.get("source") != "semilla" and not f.get("archived")]
            if not hs:
                return {"error": "Tu memoria personal está vacía: no hay nada que guardar."}
            claves = {x for f in hs for x in (f["s"], f["o"])}
            preds = {f["p"] for f in hs}
            cont = {"hechos": copy.deepcopy(hs), "display": {k: v for k, v in self.mem.display.items() if k in claves}, "surface": {k: v for k, v in self.mem.surface.items() if k in preds}}
            cartuchos.guardar_cartucho(nom, cont, {"fuente": "memoria personal (interfaz web)", "descripcion": descripcion[:300]}, self.base)
            return {"ok": True, "nombre": nom, "hechos": len(hs)}

    def cartucho_desde_texto(self, nombre, texto, descripcion=""):
        nom = nombre_seguro(nombre)
        if not nom:
            return {"error": "Nombre no válido."}
        if self.parser is None:
            return {"error": "Necesito la escuela de español para leer textos (python -m scripts.train_school)."}
        texto = (texto or "")[:200_000]
        if len(texto.strip()) < 10:
            return {"error": "El texto es demasiado corto."}
        from src.language.ingesta import comprobar, informe, leer, preparar
        from src.language.dialogue import Conversation
        from src.language.qa import QA
        from src.reasoning.lessons import deduce_all
        with self.lock:
            with tempfile.TemporaryDirectory() as d:
                mem = MemoryStore(os.path.join(d, "lectura.json"))
                mem.today = getattr(self.mem, "today", None) or date.today()
                try:
                    from src.language.semilla import load_seed
                    load_seed(mem, self.parser)
                except Exception:                                              # noqa
                    pass
                cartuchos.montar(mem, self.base, excluir=nom)
                snap = cartuchos.instantanea(mem)
                conv = Conversation(mem, self.parser, lambda m, p: QA(m, p.parse, lambda facts: deduce_all(facts, m.active_lessons())))
                frases, titulos = preparar(texto)
                rep = leer(conv, mem, frases)
                chk = comprobar(conv, mem, rep["hechos_nuevos"])
                cont = cartuchos.delta(mem, snap)
            cartuchos.guardar_cartucho(nom, cont, {"fuente": "texto pegado en la interfaz web", "frases": len(frases), "descripcion": descripcion[:300],
                                                  "no_entendidas": [f for f, _ in rep["no_entendidas"]]})
            cartuchos.insertar(nom, self.base)
            self._remontar()
            return {"ok": True, "nombre": nom, "hechos": len(cont["hechos"]), "informe": informe(rep, titulos, chk)}

    def exportar_memoria(self):
        with self.lock:
            return json.dumps(self.mem._personal(), ensure_ascii=False, indent=1).encode("utf-8")
