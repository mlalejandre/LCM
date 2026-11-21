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
        self._vision_reciente = None  # último adjunto de esta sesión

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

    def _capas20(self):
        from src.semantics.ud19 import respuesta_http as c19
        from src.semantics.narrativa18 import respuesta_http as c18
        from src.semantics.discourse17 import respuesta_http as c17
        from src.semantics.dialogue16 import respuesta_http as c16
        return (c19, c18, c17, c16)

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
    # LCM_NUCLEO_20: el núcleo conversacional unificado responde primero; lo que no entiende por
    # completo se delega en las capas 1.4-1.9 y, si estas tampoco saben, se emite su abstención.
    def _nucleo20(self):
        n = getattr(self, '_n20', None)
        if n is None:
            from src.nucleo20 import Nucleo20, activo
            if not activo(getattr(self, 'parser', None)):
                self._n20 = False
                return None
            from pathlib import Path
            n = Nucleo20(self.mem, self.parser, str(Path(self.mem.path).with_name('lcm_nucleo20.json')))
            self._n20 = n
        return n or None

    def chat(self, texto, imagen=None, nombre='imagen'):
        """La conversación de siempre y, después, la capa de SINTAXIS: si se ha leído un texto, el analizador entrenado saca sus relaciones;
        si se pregunta, contesta primero esa memoria de relaciones (ver src/sintaxis/integra.py). Se apaga con LCM_SIN_SINTAXIS=1."""
        out = self._chat_base(texto, imagen, nombre)
        try:
            if texto and not imagen and isinstance(out, dict):
                from src.sintaxis import integra as _SI
                if _SI.activo():
                    n20 = self._nucleo20()
                    if n20 is not None and not _SI.lee(n20, texto):
                        rs = _SI.responde(n20, texto, out)
                        if rs is not None:
                            out = dict(out, respuesta=rs["respuesta"], origen_sintaxis=True, fuente_texto=rs.get("fuente_texto"), seguridad=rs.get("seguridad"))
                            try:
                                n20.ult_resp = out["respuesta"]
                            except Exception:            # noqa
                                pass
        except Exception:                                # noqa
            pass
        return out

    def _chat_base(self, texto, imagen=None, nombre='imagen'):
        if imagen is not None:
            return self._chat_imagen(texto, imagen, nombre)
        n20 = self._nucleo20()
        if n20 is None:
            return self._chat_capas(texto, imagen, nombre)
        from src.quality.arbitraje20 import es_abstencion, respuesta_vacia, limpia_eco
        t0 = time.time()
        # una pregunta pendiente del diálogo de base («¿Lo olvido?», «¿Cómo te llamas?») la contesta él
        if getattr(getattr(self.conv, 'd', None), 'pending', None) and getattr(self, '_fuente20', '') != 'capas':
            try:
                self.conv.d.pending = None          # la pregunta pendiente no llegó a mostrarse: no cuenta
            except Exception:                       # noqa
                pass
        if getattr(getattr(self.conv, 'd', None), 'pending', None):
            # respuesta corta («Sí», «Marcos»): es para la pregunta pendiente. Una frase completa que el núcleo entiende no lo es.
            r_p = None
            if len((texto or '').split()) > 2 and not getattr(n20, 'pend_olvido', False):
                with self.lock:
                    antes = self._claves(); n0 = len(self.mem.facts)
                    n20._ult_texto = (texto or '').strip()
                    r_p = n20.procesar((texto or '').strip())
                    if r_p is not None and not (r_p.get('estado') == 'abst' and r_p.get('consultar', True)):
                        try:
                            self.conv.d.pending = None
                        except Exception:              # noqa
                            pass
                        self._fuente20 = 'nucleo'
                        return self._salida20(n20, r_p, antes, n0, t0)
            self._fuente20 = 'capas'
            out = self._chat_capas(texto, imagen, nombre)
            n20.turno_delegado(texto or '', '?' in (texto or ''))
            self._olvido20(n20, texto, out)
            return out
        try:                                   # multimodal: «mi coche es de ese color» -> el color de la última imagen vista
            import re as _re
            vr = self._vision_reciente or {}
            col = str(vr.get('concepto') or '').lower()
            if col and texto and '?' not in texto and getattr(n20, 'vista', None) is None and _re.search(r"\b(?:de|del)\s+(?:ese|este|el)\s+(?:mismo\s+)?(?:color|tono)\b", texto, _re.I):
                texto = _re.sub(r"\b(?:de|del)\s+(?:ese|este|el)\s+(?:mismo\s+)?(?:color|tono)\b", col, texto, flags=_re.I)
        except Exception:                      # noqa
            pass
        with self.lock:
            antes = self._claves()
            n0 = len(self.mem.facts)
            n20._ult_texto = (texto or '').strip()
            r20 = n20.procesar((texto or '').strip())
            if r20 is not None and r20.get('estado') == 'abst' and ('?' in (texto or '') or getattr(n20, '_ult_era_preg', False)):
                try:                               # antes de decir «no lo sé»: ¿lo dijo la persona con otras palabras?
                    from src.nucleo20 import coloquial as _Q
                    cita = _Q.recuerda(n20, _Q.normaliza((texto or '').strip()))
                    if cita:
                        r20 = {'respuesta': f"No lo tengo del todo claro, pero me dijiste: «{cita.rstrip('.')}».", 'estado': 'ok', 'consultar': False, 'tipo': 'resp'}
                except Exception:                  # noqa
                    pass
            if r20 is not None and not (r20.get('estado') == 'abst' and r20.get('consultar')):
                self._fuente20 = 'nucleo'
                return self._salida20(n20, r20, antes, n0, t0)
        out = self._chat_capas(texto, imagen, nombre)
        resp = out.get('respuesta') if isinstance(out, dict) else None
        if r20 is not None and isinstance(resp, str) and resp.startswith("Eso queda fuera de lo que sé hacer") and r20.get('estado') == 'abst' and '?' in (texto or ''):
            try:                                   # 2.24: una pregunta sobre lo que se acaba de leer no es «algo del exterior»: vale el «no lo sé» del núcleo
                from src.nucleo20 import sinonimia as _S20, lectura as _L20
                _vb, _nm = _S20.vocabulario(n20)
                if (n20.usuario.get('leido') or []) and any(_S20._entera(w) in _nm for w in _L20._contenido(texto)):
                    with self.lock:
                        self._fuente20 = 'nucleo'
                        return self._salida20(n20, r20, antes, n0, t0)
            except Exception:                      # noqa
                pass
        if r20 is not None and (out.get('error') or out.get('fallo') or respuesta_vacia(resp) or es_abstencion(resp)):
            from src.quality.arbitraje20 import abstencion_util
            if not (r20['respuesta'] == 'No lo sé.' and abstencion_util(resp)):
                with self.lock:
                    self._fuente20 = 'nucleo'
                    return self._salida20(n20, r20, antes, n0, t0)
        # LCM 2.5: si ninguna capa lo ha entendido de verdad, se guarda literal (para poder citarlo) o se cita lo guardado
        try:
            alt = self._memoria_literal(n20, texto, out, r20)
            if alt is not None:
                self._fuente20 = 'nucleo'
                return self._salida20(n20, alt, antes, n0, t0)
        except Exception:                      # noqa
            pass
        self._fuente20 = 'capas' 
        if isinstance(resp, str):
            out['respuesta'] = limpia_eco(resp, out.get('aprendido'))
            n20.ult_resp = out['respuesta']
            n20.ult_just = None
        if r20 is None:
            n20.turno_delegado(texto or '', '?' in (texto or '') or '¿' in (texto or ''))
            self._olvido20(n20, texto, out)
        return out

    _MAL_ENTENDIDO = ("he registrado ese hecho con su procedencia", "no he entendido", "asi sabre a quien te refieres", "pero no he entendido que quieres decirme",
                      "detecto una creencia o posibilidad", "es una condicion, no un hecho", "no consta una relacion de ese tipo", "no consta informacion suficiente")

    def _memoria_literal(self, n20, texto, out, r20):
        from src.nucleo20 import coloquial as Q
        from src.nucleo20.morfo import sa as _sa
        from src.quality.arbitraje20 import es_abstencion
        t = Q.normaliza((texto or '').strip())
        if not t or len(t.split()) < 2:
            return None
        resp = _sa(str((out or {}).get('respuesta') or ''))
        flojo = any(x in resp for x in self._MAL_ENTENDIDO) or es_abstencion((out or {}).get('respuesta')) or (r20 is not None and r20.get('estado') == 'abst')
        if not flojo:
            return None
        if '?' in t or '¿' in t:
            cita = Q.recuerda(n20, t)
            if cita:
                return {'respuesta': f"No lo tengo del todo claro, pero me dijiste: «{cita.rstrip('.')}».", 'estado': 'ok', 'consultar': False, 'tipo': 'resp'}
            if r20 is not None:
                return None
            if 'asi sabre a quien te refieres' in resp or 'no he entendido' in resp or 'no consta' in resp:
                return {'respuesta': "No he entendido bien la pregunta. ¿Me la dices de otra forma?", 'estado': 'abst', 'consultar': False, 'tipo': 'abst'}
            return None
        if (out or {}).get('aprendido') or (out or {}).get('delta'):
            if r20 is None:
                Q.anota(n20, t)                    # las capas anteriores sí aprendieron algo: se respeta, y queda además la cita literal
            return None
        if r20 is None and Q.anota(n20, t):
            return {'respuesta': f"No lo he entendido del todo, pero me lo apunto tal como lo dices: «{t.rstrip('.')}».", 'estado': 'ok', 'consultar': False, 'tipo': 'nota'}
        return None

    def _olvido20(self, n20, texto, out):
        """El grafo del núcleo olvida lo mismo que la memoria clásica (y solo cuando esta lo ha olvidado de verdad)."""
        try:
            import re as _re
            from src.nucleo20.morfo import sa as _sa
            r = _sa(str((out or {}).get('respuesta') or ''))
            t = _sa(texto or '').strip(' .!')
            with self.lock:
                if getattr(n20, 'pend_olvido', False):
                    n20.pend_olvido = False
                    if _re.search(r"\b(olvidado|borrado|he olvidado|ya no recuerdo|memoria (?:vacia|borrada)|hecho)\b", r) and not _re.match(r"^(no|cancela|mejor no|dejalo)\b", t):
                        n20.olvidar_todo()
                    return
                if _re.match(r"^(olvida|olvidate de|borra) (todo|todo lo que sabes|todo lo anterior)$|^olvidalo todo$|^borra la memoria$", t):
                    if 'seguro' in r:
                        n20.pend_olvido = True
                    elif _re.search(r"\b(olvidado|borrado)\b", r):
                        n20.olvidar_todo()
                elif _re.match(r"^(olvida|borra|elimina|quita)\b", t):
                    if n20.olvida(texto) and isinstance(out, dict) and not _re.search(r"\b(olvid|borr|elimin)", r):
                        # la memoria clásica no lo encontró, pero el núcleo sí lo tenía y lo ha olvidado
                        m_ = _re.match(r"^(?:olvida|borra|elimina|quita)\s+(?:que\s+|lo de que\s+)?(.+)$", (texto or '').strip(' .!'), _re.I)
                        out['respuesta'] = "De acuerdo, he olvidado que " + (m_.group(1) if m_ else "eso") + "."
        except Exception:                      # noqa
            pass

    def _chat_imagen(self, texto, imagen, nombre='imagen'):
        """LCM 2.3: la imagen pasa a ser un referente del núcleo (color y forma) y el texto que la acompaña se interpreta con ella."""
        n20 = self._nucleo20()
        if n20 is None:
            return self._chat_capas(texto, imagen, nombre)
        from src.vision.perception import procesar_imagen
        from src.nucleo20 import vista as V
        t0 = time.time()
        with self.lock:
            visto = procesar_imagen(self.mem, imagen, nombre)
            if visto.get("error"):
                return {"error": visto["error"]}
            self._vision_reciente = visto
            self._registrar_vision_episodica(visto)
            try:
                from src.vision.formas import analizar_forma
                forma = analizar_forma(imagen)
            except Exception:                                                  # noqa
                forma = {}
            escena = {}
            if not forma.get("forma"):                                         # 2.10: varias figuras y cómo están colocadas
                try:
                    from src.vision.formas import analizar_escena
                    escena = analizar_escena(imagen)
                except Exception:                                              # noqa
                    escena = {}
            desc = V.ver(n20, visto, forma, escena)
        extra = {"episodio": visto.get("episodio"), "aviso_episodio": visto.get("aviso_episodio")}
        import re as _re                      # «Te paso una foto.» solo anuncia la imagen: no es un hecho que guardar
        texto = _re.sub(r"^\s*(?:(?:te|os) )?(?:paso|mando|env[ií]o|enseño|adjunto|pongo|subo|dejo)(?: aqu[ií])? (?:una|esta|la|otra) (?:foto(?:graf[ií]a)?|imagen|captura)(?: (?:que he hecho|m[ií]a))?\s*[.,:;!]*\s*", "", texto or "", flags=_re.I)
        if not (texto or '').strip():
            return dict({"respuesta": desc, "aprendido": visto.get("aprendido", []), "imagen": None, "fallo": not (visto.get("concepto") or forma.get("forma")),
                         "ms": int((time.time() - t0) * 1000), "hechos": len(self.mem.facts), "delta": len(visto.get("aprendido", [])), "nucleo20": "vista"}, **extra)
        out = self.chat(texto)
        if isinstance(out, dict):
            out = dict(out, **extra)
        return out

    def _salida20(self, n20, r20, antes, n0, t0):
        nuevos = [self._fila(f) for f in self.mem.facts if (f["s"], f["p"], f["o"], bool(f.get("neg"))) not in antes][:40]
        try:
            self.mem.save()
        except OSError:
            pass
        n20.ult_resp = r20['respuesta']
        if r20.get('tipo') == 'ack':
            n20.ult_dicho = getattr(n20, '_ult_texto', '') or getattr(n20, 'ult_dicho', '')
        try:                                   # el diálogo de base comparte el nombre de la persona
            nom = n20.usuario.get('nombre')
            if nom and getattr(self.conv.d, 'user', None) != nom:
                self.conv.d.user = nom
        except Exception:                      # noqa
            pass
        return {'respuesta': r20['respuesta'], 'aprendido': nuevos, 'imagen': r20.get('imagen'), 'fallo': r20.get('estado') == 'abst', 'ms': int((time.time() - t0) * 1000),
                'hechos': len(self.mem.facts), 'delta': len(self.mem.facts) - n0, 'nucleo20': r20.get('estado')}

    def _chat_capas(self, texto, imagen=None, nombre='imagen'):
        texto = (texto or "").strip()
        if not texto and imagen is None:
            return {"error": "Escribe algo o adjunta una imagen."}
        from src.language.lector import MAX_TEXTO
        if len(texto) > MAX_TEXTO:
            return {"error": f"Texto demasiado largo (máx. {MAX_TEXTO:,} caracteres): pártelo en dos.".replace(",", ".")}
        # LCM_CALIDAD14_PRE
        from src.quality.grounding import pre_respuesta
        _respuesta_fundamentada = pre_respuesta(texto, self.mem, getattr(self, '_calidad_flags', None))
        if _respuesta_fundamentada is not None:
            return {'respuesta': _respuesta_fundamentada, 'aprendido': [], 'imagen': None,
                    'fallo': False, 'ms': 0, 'hechos': len(self.mem.facts), 'delta': 0}
        # LCM_EVIDENCIA15_PRE: hechos de nacimiento, no coincidencias textuales.
        from src.quality.evidencia15 import pre_respuesta as pre_evidencia15
        _evidencia15 = pre_evidencia15(texto, self.mem)
        if _evidencia15 is not None:
            return {'respuesta': _evidencia15, 'aprendido': [], 'imagen': None,
                    'fallo': False, 'ms': 0, 'hechos': len(self.mem.facts), 'delta': 0}
        # LCM_VISION_01_CHAT_INTEGRADO: texto e imagen llegan al mismo método.
        from src.vision.concept_alignment import (responder_pregunta_visual,
            es_pregunta_color_visual, color_solicitado)
        from src.vision.sample import datos_muestra
        with self.lock:
            if imagen is not None:
                from src.vision.perception import procesar_imagen
                visto = procesar_imagen(self.mem, imagen, nombre)
                if visto.get("error"):
                    return {"error": visto["error"]}
                self._vision_reciente = visto
                self._registrar_vision_episodica(visto)
                if not texto or es_pregunta_color_visual(texto):
                    if visto.get("concepto") and texto:
                        respuesta = responder_pregunta_visual(self.mem, texto, visto)
                    else:
                        respuesta = visto.get("respuesta") or visto.get("mensaje")
                    return {"respuesta": respuesta, "aprendido": visto.get("aprendido", []),
                            "imagen": None, "fallo": not bool(visto.get("concepto")),
                            "ms": 0, "hechos": len(self.mem.facts), "delta": len(visto.get("aprendido", [])), "episodio": visto.get("episodio"), "aviso_episodio": visto.get("aviso_episodio")}
                # Una imagen ambigua no debe hacer que respondamos sobre otra previa.
                if not visto.get("concepto"):
                    return {"respuesta": visto.get("respuesta"), "aprendido": [],
                            "fallo": True, "ms": 0, "hechos": len(self.mem.facts), "delta": 0, "episodio": visto.get("episodio"), "aviso_episodio": visto.get("aviso_episodio")}

            # LCM_ARBITRAJE_20: las capas 1.6-1.9 responden por orden, pero una ABSTENCIÓN
            # («No consta...») no cierra el turno: se retiene y se consulta al resto de capas.
            # Solo si ninguna aporta una respuesta fundada se devuelve la abstención retenida.
            from src.quality.arbitraje20 import es_abstencion
            _retenida = None
            for _capa in self._capas20():
                _r = _capa(texto, self.mem, self.parser, self)
                if _r is None:
                    continue
                if es_abstencion(_r.get('respuesta')) and ('?' in texto or '¿' in texto):
                    _retenida = _retenida or _r
                    continue
                return _r
            # LCM_SEMANTICA_V1_INICIO
            # La forma lingüística se resuelve por conceptos, no por regex de órdenes.
            from src.semantics.bridge import PuenteSemantico
            if getattr(self, '_puente_semantico', None) is None:
                self._puente_semantico = PuenteSemantico()
            respuesta_semantica = self._puente_semantico.responder(texto, self.mem)
            if respuesta_semantica is not None:
                respuesta_semantica.setdefault('ms', 0)
                respuesta_semantica.setdefault('hechos', len(self.mem.facts))
                respuesta_semantica.setdefault('delta', len(respuesta_semantica.get('aprendido', [])))
                return respuesta_semantica
            # LCM_SEMANTICA_V1_FIN
            # LCM_EVIDENCIA15_NEGACION: composición vectorial, no verbos rígidos.
            from src.quality.evidencia15 import confirmacion_negacion_visual
            _confirmacion = confirmacion_negacion_visual(texto, self._puente_semantico.lex)
            if _confirmacion is not None:
                return {'respuesta': _confirmacion, 'imagen': None, 'aprendido': [],
                        'fallo': False, 'ms': 0, 'hechos': len(self.mem.facts), 'delta': 0}
            respuesta_visual = responder_pregunta_visual(self.mem, texto, self._vision_reciente)
            if respuesta_visual is not None:
                return {"respuesta": respuesta_visual, "aprendido": [],
                        "fallo": self._vision_reciente is not None and not bool(self._vision_reciente.get("concepto")),
                        "ms": 0, "hechos": len(self.mem.facts), "delta": 0}
        # Fuera del caso visual, el texto sigue el flujo conversacional original.
        with self.lock:
            antes = self._claves()
            n0 = len(self.mem.facts)
            t0 = time.time()
            try:
                resp = self.conv.say(texto)
                # Mantener referentes entre turnos procesados por el diálogo legado.
                if getattr(self, '_dialogo16', None) is not None:
                    self._dialogo16.observar_turno(texto)
                # LCM_CALIDAD14_POST
                from src.quality.grounding import post_respuesta
                resp = post_respuesta(texto, resp, getattr(self, '_calidad_flags', None), mem=self.mem)
                from src.quality.evidencia15 import post_respuesta as post_evidencia15
                resp = post_evidencia15(texto, resp, mem=self.mem)
            except Exception as e:                                             # noqa
                return {"error": f"No he podido procesar eso ({type(e).__name__})."}
            nuevos = [self._fila(f) for f in self.mem.facts if (f["s"], f["p"], f["o"], bool(f.get("neg"))) not in antes][:40]
            try:
                self.mem.save()
            except OSError:
                pass
            from src.language.consultas import es_fallo
            from src.quality.arbitraje20 import respuesta_vacia
            if _retenida is not None and not nuevos and (es_fallo(resp) or respuesta_vacia(resp)):
                return _retenida
            return {"respuesta": resp, "aprendido": nuevos, "fallo": bool(es_fallo(resp)), "ms": int((time.time() - t0) * 1000), "hechos": len(self.mem.facts), "delta": len(self.mem.facts) - n0}

    # LCM_VISION_01_METHOD: API legacy también actualiza el contexto del chat.
    # LCM_EPISODIOS_13_PUENTE
    def _registrar_vision_episodica(self, visto):
        """Conserva procedencia visual sin cambiar la respuesta de conversación."""
        observacion = visto.get('observacion')
        if not observacion:
            return
        try:
            from pathlib import Path
            from src.multimodal.episodic_memory import MemoriaEpisodica
            registro = getattr(self, '_episodios', None)
            if registro is None:
                ruta = Path(self.mem.path).with_name('lcm_episodios.json')
                registro = MemoriaEpisodica(ruta)
                self._episodios = registro
            visto['episodio'] = registro.observar(observacion, contexto='IMAGEN_CHAT')
        except (OSError, ValueError, TypeError) as exc:
            # El registro episódico es adicional: no romper una respuesta válida
            # ni ocultar el diagnóstico para el usuario o la interfaz.
            visto['aviso_episodio'] = type(exc).__name__ + ': ' + str(exc)[:180]

    def vision_analizar(self, contenido, nombre="imagen"):
        from src.vision.perception import procesar_imagen
        with self.lock:
            res = procesar_imagen(self.mem, contenido, nombre)
            if not res.get("error"):
                self._vision_reciente = res
                self._registrar_vision_episodica(res)
            return res

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
            from src.language.lector_ud import guardar_traza
            guardar_traza(rep)
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
            self._vision_reciente = None
            if getattr(self, '_narrativa18', None) is not None:
                self._narrativa18.ultimo_tema = None
            if getattr(self, '_dialogo16', None) is not None:
                self._dialogo16.ultimo = None
                self._dialogo16.ultima_prueba = None
            if getattr(self, '_puente_semantico', None) is not None:
                self._puente_semantico.pendiente = None
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
