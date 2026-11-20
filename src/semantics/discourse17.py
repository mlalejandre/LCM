"""LCM 1.7: alcance discursivo, coordinación, relativas y episodios temporales.

Es una capa conservadora encima de DialogoConceptual 1.6. No aprende sinónimos
por listas de comandos ni modifica los embeddings. Todas las afirmaciones
se atribuyen a su fuente; una hipótesis o un suceso fechado no es un hecho
atemporal utilizable para reglas. Las frases no cubiertas se delegan.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from src.language.irregulares import IRREG

from src.semantics.dialogue16 import (
    DialogoConceptual, Prop, _clausula, clave, forma_verbal, nombre, normal,
    PAL, MODALES,
)

SCHEMA = 'lcm-discourse-1.7'
MAX_EVENTS = 3000
EPISTEMICOS = re.compile(
    r'\b(?:seg[uú]n|al parecer|parece que|me parece que|se rumorea que|'
    r'me han dicho que|me contaron que|puede que|es probable que|'
    r'imagina que|supongamos que)\b', re.I)
CONJ_PELIGROSAS = re.compile(r'\b(?:pero|aunque|porque|cuando|mientras|si|excepto|salvo)\b', re.I)
TEMPORAL = re.compile(r'^(ayer|hoy|anteayer)\s+(.+)$|^(.+?)\s+(ayer|hoy|anteayer)$',re.I)
NOMBRES = r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+'


def _fecha(etiqueta, fecha_base):
    base = fecha_base if isinstance(fecha_base, dt.date) else dt.date.today()
    dias={'hoy': 0, 'ayer':-1, 'anteayer':-2}
    return (base+dt.timedelta(days=dias[normal(etiqueta)])).isoformat()


def _imperfecto_a_infinitivo(forma):
    """Selecciona un lema documentado para -ía/-aba; si es ambiguo, abstiene."""
    f=normal(forma)
    lemmas=set(IRREG.values())
    if len(f)>4 and f.endswith('ia'):
        stem=f[:-2]
        candidatos=[v for v in (stem+'er',stem+'ir') if v in lemmas]
        return candidatos[0] if len(candidatos)==1 else None
    if len(f)>4 and f.endswith('aba'):
        candidato=f[:-3]+'ar'
        return candidato if candidato in lemmas else None
    return None


def _verbo_en_contexto(forma):
    """Lema en el subconjunto de pretérito regular -ar; no clasifica significado."""
    inf=_imperfecto_a_infinitivo(forma)
    if inf:return inf.upper()
    lem=forma_verbal(forma)
    if lem:return lem
    f=normal(forma)
    if len(f)>=5 and f.endswith("o"):
        return f[:-1].upper()+"AR"
    return None


def _pasado_a_presente(s):
    """Equivalencia MORFOLÓGICA de -ó (3.ª persona, pretérito -ar).

    No se confunde proximidad semántica con lematización. El resto del
    pretérito (particularmente -ió para -er/-ir) requiere Escuela/lemario.
    """
    def repl(m):
        t=m.group(0)
        if t.lower().endswith('ó') and len(t)>=5:
            return t[:-1]+'a'
        return t
    return re.sub(r'\b[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+\b',
                  lambda m: _imperfecto_a_infinitivo(m.group(0)) or repl(m),s)


class Discurso17:
    def __init__(self, nucleo: DialogoConceptual, ruta=None):
        self.nucleo=nucleo
        ruta_base=Path(getattr(nucleo.mem,'path','memory/lcm_memory.json'))
        self.ruta=Path(ruta) if ruta else ruta_base.with_name('lcm_discourse17.json')
        self.eventos=[]
        if self.ruta.is_file():
            d=json.loads(self.ruta.read_text(encoding='utf8'))
            if d.get('schema')!=SCHEMA or not isinstance(d.get('eventos'),list):
                raise ValueError('Memoria discursiva 1.7 desconocida; no se modifica.')
            for e in d['eventos'][-MAX_EVENTS:]:
                if (isinstance(e,dict) and all(isinstance(e.get(k),str) for k in ('s','p','o','tiempo','fuente'))
                        and isinstance(e.get('neg'),bool)):
                    self.eventos.append(e)

    def _guardar(self):
        self.ruta.parent.mkdir(parents=True,exist_ok=True)
        d={'schema':SCHEMA,'eventos':self.eventos[-MAX_EVENTS:]}
        with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=self.ruta.parent,
                                         prefix='.lcm17_',suffix='.tmp',delete=False) as f:
            json.dump(d,f,ensure_ascii=False,indent=2)
            p=Path(f.name)
        try:os.replace(p,self.ruta)
        finally:p.unlink(missing_ok=True)

    def _prop(self, frase, contexto=None):
        """Obtener roles desde Escuela o respaldo 1.6, sin memorizar todavía."""
        frase=frase.strip(' .!')
        frase=_pasado_a_presente(frase)
        # No alterar frases con modales, órdenes o subordinadas no previstas.
        if MODALES.search(frase) or EPISTEMICOS.search(frase) or CONJ_PELIGROSAS.search(frase):
            return None
        p=_clausula(frase,self.nucleo.parser,permitir_pron=True)
        if p and p.s in {'EL','ELLA','ELLOS','ELLAS'}:
            referente=self.nucleo._referente(p.s)
            if referente:p=Prop(referente,p.p,p.o,p.neg)
            else:return None
        return p

    def _insertar_eventos(self, eventos):
        nuevo=0
        for p,instante,fuente in eventos:
            e={'s':p.s,'p':p.p,'o':p.o,'neg':p.neg,
               'tiempo':instante,'fuente':fuente,'canal':'texto_declarado'}
            if e not in self.eventos:
                self.eventos.append(e)
                nuevo+=1
            self.nucleo._mencionar(p)
        if nuevo:self._guardar()
        return nuevo

    def _query_temporal(self,t):
        original=t.strip(' \t¿?!.')
        norm=normal(original)
        etiqueta=None
        for ad in ('ayer','hoy','anteayer'):
            if norm.endswith(' '+ad):
                etiqueta=ad
                original=original[:-(len(ad)+1)].strip()
                break
        if etiqueta is None:
            # Cambio de estado del discurso: «antes», «ahora».
            for ad in ('antes','ahora'):
                if norm.endswith(' '+ad):
                    etiqueta=ad
                    original=original[:-(len(ad)+1)].strip()
                    break
        if etiqueta is None:return None
        fecha=_fecha(etiqueta,getattr(self.nucleo.mem,'today',None)) if etiqueta in ('ayer','hoy','anteayer') else etiqueta
        q=normal(original)
        patron=None
        modo=None
        m=re.fullmatch(r'a quien\s+('+PAL+r')\s+('+PAL+r')',q)
        if m:
            v,s=m.groups();patron=(clave(s),_verbo_en_contexto(v),None);modo='objeto'
        m=m or re.fullmatch(r'quien\s+('+PAL+r')\s+a\s+('+PAL+r')',q)
        if m and modo is None:
            v,o=m.groups();patron=(None,_verbo_en_contexto(v),clave(o));modo='sujeto'
        m=m or re.fullmatch(r'donde\s+('+PAL+r')\s+('+PAL+r')',q)
        if m and modo is None:
            v,s=m.groups();patron=(clave(s),_verbo_en_contexto(v)+'_EN' if _verbo_en_contexto(v) else None,None);modo='objeto'
        m=m or re.fullmatch(r'('+PAL+r')\s+('+PAL+r')\s+a\s+('+PAL+r')',q)
        if m and modo is None:
            v,s,o=m.groups();patron=(clave(s),_verbo_en_contexto(v),clave(o));modo='polar'
        if patron is None or patron[1] is None:
            return None
        s,p,o=patron
        encontrados=[e for e in self.eventos if e['tiempo']==fecha and e['p']==p
                     and (s is None or s==e['s']) and (o is None or o==e['o'])]
        positivos=[e for e in encontrados if not e['neg']]
        negativos=[e for e in encontrados if e['neg']]
        if modo=='polar':
            if positivos and negativos:return 'Hay declaraciones incompatibles para esa fecha; necesito aclaración.'
            if positivos:return 'Sí, según «'+positivos[0]['fuente']+'».'
            if negativos:return 'No, según la negación explícita «'+negativos[0]['fuente']+'».'
            return 'No consta evidencia suficiente para esa fecha.'
        objetos={ (e['s'] if modo=='sujeto' else e['o']) for e in positivos }
        if objetos:
            fuente=positivos[0]['fuente']
            return ', '.join(nombre(v) for v in sorted(objetos)) + '. Según «'+fuente+'».'
        return 'No consta una respuesta afirmativa respaldada para esa fecha.'

    def _evento_nominal(self, texto):
        """Intransitivos con SN explícito: evento TESTIMONIADO, nunca hecho genérico.

        «Un pájaro ...» crea identificador de mención, no el concepto PAJARO.
        No presupone que dos menciones del mismo tipo sean el mismo individuo.
        """
        s=texto.strip(' .!')
        if EPISTEMICOS.search(s) or MODALES.search(s) or CONJ_PELIGROSAS.search(s):return None
        m=re.fullmatch(r'(un|una|el|la|ese|esa|este|esta)\s+('+NOMBRES+r')\s+(no\s+)?est[aá]\s+('+NOMBRES+r')(?:\s+en\s+(?:el\s+|la\s+)?('+NOMBRES+r'))?',s,re.I)
        neg=False;loc=None
        if m:
            det,sust,no,ger,loc=m.groups()
            ger=normal(ger)
            if not ger.endswith('ando') or len(ger)<6:return None
            verbo=ger[:-4].upper()+'AR'
            neg=bool(no)
        else:
            m=re.fullmatch(r'(un|una|el|la|ese|esa|este|esta)\s+('+NOMBRES+r')\s+(no\s+)?('+NOMBRES+r')',s,re.I)
            if not m:return None
            det,sust,no,fin=m.groups()
            # Solo pretérito -ó e imperfecto -aba, sin adivinar -ía/-ió.
            if fin.endswith('ó') and len(fin)>4:verbo=normal(fin[:-1]).upper()+'AR'
            elif normal(fin).endswith('aba') and len(fin)>=5:verbo=normal(fin[:-3]).upper()+'AR'
            else:return None
            neg=bool(no)
        ident='MENCION_'+hashlib.blake2s(s.encode('utf8'),digest_size=6).hexdigest().upper()
        return Prop(ident,verbo+('_EN' if loc else ''),clave(loc) if loc else '_',neg)

    def _progresivo_nominal(self,texto):
        p=self._evento_nominal(texto)
        if p is None:return None
        self._insertar_eventos([(p,'declarado_ahora',texto.strip())])
        return 'He registrado un acontecimiento declarado, sin confundirlo con el conocimiento general de esa especie.'

    def _eventos_temporales(self, texto):
        # Una orden «Hoy escucha ...» no debe convertirse en un hecho.
        m=TEMPORAL.fullmatch(texto.strip(' .!'))
        if not m:return None
        tiempo=(m.group(1) or m.group(4))
        cl=(m.group(2) or m.group(3))
        if not cl or '¿' in texto or '?' in texto:return None
        p=self._prop(cl) or self._evento_nominal(cl)
        if p is None:
            return 'No puedo identificar con seguridad el hecho temporal; no lo registraré.'
        instante=_fecha(tiempo,getattr(self.nucleo.mem,'today',None))
        n=self._insertar_eventos([(p,instante,texto.strip())])
        return ('He registrado un acontecimiento fechado, separado de los hechos permanentes.'
                if n else 'Ese acontecimiento fechado ya estaba registrado.')

    def _cambio_estado(self,texto):
        # Distinción entre estado anterior y actual; no convertirlo en contradicción.
        m=re.fullmatch(r'antes\s+(.+?),\s*ahora\s+(.+?)\s*[.!]?',texto.strip(),re.I)
        if not m:return None
        primera,segunda=m.groups()
        p1=self._prop(primera)
        if p1 is None:return 'No he almacenado el cambio porque no interpreto el estado anterior.'
        p2=self._prop(segunda)
        if p2 is None:
            # Elipsis con el sujeto previo explícito: «ahora vive en Sevilla».
            p2=self._prop(nombre(p1.s)+' '+segunda)
        if p2 is None or p1.s!=p2.s or p1.p!=p2.p:
            return 'No he registrado el cambio: no puedo vincular inequívocamente ambos estados.'
        self._insertar_eventos([(p1,'antes',texto.strip()),(p2,'ahora',texto.strip())])
        return 'He distinguido el estado anterior del actual; no los trataré como contradictorios.'

    def _cliticos(self,texto):
        """Pronombres átonos con un único antecedente reciente compatible.

        Esta heurística está deliberadamente limitada: no resuelve referencias
        discursivas largas, nombres de género incierto ni dobles candidatos.
        """
        m=re.fullmatch(r'\s*('+NOMBRES+r')\s+(lo|la)\s+('+NOMBRES+r')\s*[.!]?\s*',texto,re.I)
        if not m:return None
        sujeto,clitico,verbo=m.groups()
        if self.nucleo.ultimo is None:return 'No tengo un antecedente para ese pronombre. ¿A quién te refieres?'
        su=clave(sujeto)
        if normal(sujeto) in ('el','ella'):
            su=self.nucleo._referente(sujeto)
        if not su:return 'No puedo resolver el sujeto de forma inequívoca. ¿A quién te refieres?'
        candidatos={self.nucleo.ultimo.s,self.nucleo.ultimo.o}
        femenino=(normal(clitico)=='la')
        posibles={x for x in candidatos if x and x!='_' and (x.endswith('A')==femenino)}
        if len(posibles)!=1:
            return 'El complemento «lo/la» tiene más de un posible antecedente. ¿Cuál es?'
        objeto=posibles.pop()
        pred=forma_verbal(verbo)
        if pred is None:return 'No he entendido el verbo con seguridad; no guardaré ese hecho.'
        p=Prop(su,pred,objeto)
        self.nucleo._guardar_hecho(p,texto.strip())
        return 'He relacionado el pronombre con su antecedente y registrado la proposición.'

    def _coordinar(self,texto):
        s=texto.strip(' \t.!')
        if ' y ' not in normal(s) or CONJ_PELIGROSAS.search(s) or MODALES.search(s) or EPISTEMICOS.search(s):return None
        partes=re.split(r'\s+y\s+',s,flags=re.I)
        if len(partes)!=2 or len(s)>240:return None
        primero=self._prop(partes[0]);
        if primero is None:return None
        segundo=self._prop(partes[1])
        if segundo is None:
            # Elipsis controlada: el segundo predicado hereda sujeto, no objeto.
            segundo=self._prop(nombre(primero.s)+' '+partes[1])
        if segundo is None:
            return 'Hay dos cláusulas, pero no puedo asignar sus papeles con seguridad; no he guardado ninguna.'
        # Registra ambos atómicamente después de validar todas las cláusulas.
        for p in (primero,segundo):self.nucleo._guardar_hecho(p,texto.strip())
        return 'He registrado dos proposiciones conectadas por «y» y he conservado sus sujetos.'

    def _relativa(self,texto):
        # Solo relativa explicativa con antecedente explícito e invariable.
        m=re.fullmatch(r'\s*('+NOMBRES+r')\s*,\s*que\s+(.+?)\s*,\s*(.+?)\s*[.!]?\s*',texto,re.I)
        if not m:return None
        sujeto,rel,principal=m.groups()
        primero=self._prop(sujeto+' '+rel)
        segundo=self._prop(sujeto+' '+principal)
        if (not primero or not segundo or primero.s!=segundo.s or primero.s!=clave(sujeto)):
            return 'La oración contiene una relativa, pero no puedo asignar ambos hechos de forma segura; no he guardado ninguno.'
        for p in (primero,segundo):self.nucleo._guardar_hecho(p,texto.strip())
        return 'He registrado la propiedad de la relativa y la acción principal como proposiciones diferentes.'

    def _atribucion(self,texto):
        m=re.match(r'^\s*seg[uú]n\s+('+NOMBRES+r')\s*,\s*(.+?)\s*[.!]?\s*$',texto,re.I)
        if m:
            hablante,contenido=m.groups()
            self.nucleo.atribuciones.append({'hablante':clave(hablante),'actitud':'segun',
                                             'contenido':contenido.strip(' .'),'fuente':texto.strip()})
            self.nucleo._guardar()
            return 'He conservado esa afirmación atribuida sin convertirla en un hecho confirmado.'
        if EPISTEMICOS.search(texto):
            return 'Eso expresa una atribución, posibilidad o apariencia; no lo guardaré como un hecho demostrado.'
        return None

    def procesar(self,texto):
        s=(texto or '').strip()
        if not s or len(s)>500 or '\n' in s:return None
        if s.startswith(('¿','?')) or s.endswith('?'):
            return self._query_temporal(s)
        if re.match(r'^si\b',normal(s)):
            return None   # las condiciones pertenecen a 1.6
        attr=self._atribucion(s)
        if attr is not None:return attr
        cambi=self._cambio_estado(s)
        if cambi is not None:return cambi
        event=self._eventos_temporales(s)
        if event is not None:return event
        if re.search(r'\best[aá]\s+(?:[a-záéíóúñ]+ando)\b',normal(s)):
            prog=self._progresivo_nominal(s)
            if prog is not None:return prog
        rel=self._relativa(s)
        if rel is not None:return rel
        clit=self._cliticos(s)
        if clit is not None:return clit
        coord=self._coordinar(s)
        if coord is not None:return coord
        return None


def respuesta_http(texto,mem,parser=None,motor=None):
    """API idempotente compatible con src.web.motor.Motor."""
    nucleo=getattr(motor,'_dialogo16',None) if motor is not None else None
    if nucleo is None:
        nucleo=DialogoConceptual(mem,parser)
        if motor is not None:motor._dialogo16=nucleo
    puente=getattr(motor,'_discurso17',None) if motor is not None else None
    if puente is None:
        puente=Discurso17(nucleo)
        if motor is not None:motor._discurso17=puente
    respuesta=puente.procesar(texto)
    if respuesta is None:return None
    return {'respuesta':respuesta,'aprendido':[],'imagen':None,'fallo':False,'ms':0,
            'hechos':len(mem.facts),'delta':0,'discurso17':{'evidencia':'declaracion_usuario',
            'eventos':len(puente.eventos)}}
