"""LCM 1.6: composición comprobable de proposiciones, reglas y contexto.

No es un parser universal ni un LLM. El analizador UD del LCM tiene prioridad
cuando existe; el respaldo gramatical reconoce una clase limitada y explícita
de cláusulas SVO. Los fallos no se compensan inventando información externa.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import unicodedata
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from src.language.irregulares import IRREG

SCHEMA = 'lcm-composicion-dialogo-1.6'
PAL = r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9_]+'
VAR = frozenset({'X', 'Y', 'Z'})
PRON = frozenset({'el', 'ella', 'ellos', 'ellas'})
FUNCIONALES = frozenset({'que','quien','quienes','cual','cuanto','cuantos','donde',
 'cuando','por','para','como','puedes','podrias','favor','este','esta','ese','esa'})
# Modificadores epistemológicos: una cita, deseo o posibilidad NO implica verdad.
MODALES = re.compile(r'\b(?:cree|creen|creo|dicen|dice|dijo|afirma|afirmó|imagina|imagino|supone|supongo|quizá|quizas|tal vez|puede que|es posible que)\b', re.I)


def normal(s):
    s=''.join(c for c in unicodedata.normalize('NFD',str(s)).casefold() if unicodedata.category(c)!='Mn')
    return re.sub(r'\s+',' ',s).strip()


def clave(s):
    return re.sub(r'[^A-Z0-9_]+','_',normal(s).upper()).strip('_')


def nombre(s):
    return re.sub(r'_',' ',s).capitalize()


def forma_verbal(v):
    """Lematización superficial, con inventario de irregulares del LCM.

    No crea equivalencias semánticas entre verbos ni permite que un verbo
    nuevo ejecute una capacidad; solo asigna una clave provisional estable.
    """
    w=normal(v)
    if w in IRREG:return IRREG[w].upper()
    irregular={'es':'SER','son':'SER','esta':'ESTAR','estan':'ESTAR',
               'nacio':'NACER','nacieron':'NACER','fue':'SER',
               'acompanan':'ACOMPAÑAR'}
    if w in irregular:return irregular[w]
    if w.endswith(('ar','er','ir')):return w.upper()
    if len(w)>3 and w.endswith(('an','as','a')):return (w[:-2] if w.endswith(('an','as')) else w[:-1]).upper()+'AR'
    if len(w)>3 and w.endswith(('en','es','e')):return (w[:-2] if w.endswith(('en','es')) else w[:-1]).upper()+'ER'
    return None


@dataclass(frozen=True)
class Prop:
    s: str
    p: str
    o: str
    neg: bool = False

    def dato(self):return [self.s,self.p,self.o,self.neg]


def _clausula(texto, parser=None, *, permitir_pron=True, regla=False):
    """Devuelve una proposición SOLO para cláusulas simples seguras.

    La salida de la Escuela (roles s,p,o) es preferente. El respaldo procesa
    únicamente 3ª persona y sujeto explícito. Nada con subordinadas/citas.
    """
    s=texto.strip(' \t\n.,;:!¡¿?')
    if not s or len(s)>240 or '\n' in s or MODALES.search(s):return None
    if regla and re.search(r'\b(?:o|pero|aunque|salvo|excepto)\b',normal(s)):return None
    if parser is not None and not re.search(r'\b[XYZ]\b',s):
        try:
            ts=parser.parse(s+'.') or []
        except (ValueError,TypeError,AttributeError):ts=[]
        if len(ts)==1:
            t=ts[0]
            su,pr,ob=clave(t.get('s','')),clave(t.get('p','')),clave(t.get('o',''))
            # El parser no puede aportar por sí solo una entidad distinta de
            # las mencionadas: verifica alineamiento superficial antes de aprender.
            mencionados=set(re.findall(PAL,normal(s)))
            s_present=all(w in mencionados for w in normal(su.replace('_',' ')).split())
            o_present=(ob=='_' or all(w in mencionados for w in normal(ob.replace('_',' ')).split()))
            if su and pr and ob and s_present and o_present and su not in {'_','EL','ELLA'}:
                return Prop(su,pr,ob,bool(t.get('neg',False)))
    # Evitar asimilar subordinadas, enunciados discursivos y órdenes a hechos.
    if re.search(r'\b(?:que|porque|si|cuando|aunque|mientras|podría|debería|quizás)\b',normal(s)):return None
    m=re.fullmatch(r'('+PAL+r')\s+(no\s+)?('+PAL+r')\s+(?:(a|en|de)\s+)?(?:el\s+|la\s+|un\s+|una\s+)?('+PAL+r')',s,re.I)
    if not m:return None
    su,no,verbo,prep,ob=m.groups()
    # No confundir determinantes demostrativos con verbos conjugados:
    # «Escucha esta grabación» es una orden, no un hecho ESCUCHA-ESTAR-GRABACIÓN.
    if normal(verbo) in {'este','esta','estos','estas','ese','esa','esos','esas','aquel','aquella'} and not verbo.endswith(('á','é')):
        return None
    if not regla and not permitir_pron and normal(su) in PRON:return None
    if not (su[:1].isupper() or normal(su) in PRON or (regla and su in VAR)):
        return None
    if normal(su) in FUNCIONALES:return None
    pred=forma_verbal(verbo)
    if pred is None:return None
    if pred=='SER' and prep: return None
    if prep=='en' and pred=='NACER':return None # fecha de nacimiento se analiza aparte
    if prep=='en':pred+='_EN'
    if prep=='de':pred+='_DE'
    obj=clave(ob)
    if not obj or not clave(su):return None
    return Prop(clave(su),pred,obj,bool(no))


class DialogoConceptual:
    """Estado de UNA conversación, no global. Las reglas se guardan aparte.

    Ni los hechos hipotéticos ni las atribuciones se introducen en MemoryStore.
    """
    def __init__(self, mem, parser=None, ruta=None):
        self.mem,self.parser=mem,parser
        self.ruta=Path(ruta) if ruta is not None else Path(getattr(mem,'path','memory/lcm_memory.json')).with_name('lcm_condicionales16.json')
        self.reglas=[];self.atribuciones=[];self.ultimo=None;self.ultima_prueba=None
        if self.ruta.is_file():
            data=json.loads(self.ruta.read_text(encoding='utf8'))
            if data.get('schema')!=SCHEMA:raise ValueError('Reglas 1.6: formato desconocido; no se modifica')
            for r in data.get('reglas',[]):
                prem=[Prop(*p) for p in r['premisas']]; concl=Prop(*r['conclusion'])
                if self._segura(prem,concl):self.reglas.append({'premisas':prem,'conclusion':concl,'fuente':r['fuente']})
            self.atribuciones=data.get('atribuciones',[])[:5000]

    def _guardar(self):
        self.ruta.parent.mkdir(parents=True,exist_ok=True)
        data={'schema':SCHEMA,
              'reglas':[{'premisas':[p.dato() for p in r['premisas']], 'conclusion':r['conclusion'].dato(), 'fuente':r['fuente']} for r in self.reglas],
              'atribuciones':self.atribuciones[-5000:]}
        with tempfile.NamedTemporaryFile(mode='w',dir=self.ruta.parent,prefix='.lcm16_',suffix='.tmp',delete=False,encoding='utf8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2);tmp=Path(f.name)
        try:os.replace(tmp,self.ruta)
        finally:tmp.unlink(missing_ok=True)

    @staticmethod
    def _segura(prem,concl):
        if not (1<=len(prem)<=2) or any(p.s=='_' or p.o=='_' or p.p=='_' for p in prem+[concl]):return False
        origen={x for p in prem for x in (p.s,p.o) if x in VAR}
        return all(x in origen for x in (concl.s,concl.o) if x in VAR)

    @staticmethod
    def _coincide(patron, hecho, env):
        if patron.p!=hecho.p or patron.neg!=hecho.neg:return None
        nuevo=env.copy()
        for a,b in ((patron.s,hecho.s),(patron.o,hecho.o)):
            if a in VAR:
                if a in nuevo and nuevo[a]!=b:return None
                nuevo[a]=b
            elif a!=b:return None
        return nuevo

    @staticmethod
    def _instanciar(p,ent):
        return Prop(ent.get(p.s,p.s),p.p,ent.get(p.o,p.o),p.neg)

    def _hechos(self):
        out={}
        for f in self.mem.facts:
            if f.get('archived'):continue
            p=Prop(f['s'],f['p'],f['o'],bool(f.get('neg')))
            out.setdefault(p,{'fuente':f.get('source','memoria'), 'antecedentes':[]})
        return out

    def _cierre(self, extra=(), max_pasos=3):
        hechos=self._hechos()
        for p in extra:hechos.setdefault(p,{'fuente':'supuesto temporal; no se memoriza','antecedentes':[]})
        for paso in range(max_pasos):
            nuevos={}
            universo=list(hechos.items())
            for r in self.reglas:
                ambientes=[({},[])]
                for plantilla in r['premisas']:
                    siguientes=[]
                    for env,ante in ambientes:
                        for h,e in universo:
                            # Una premisa disputada no autoriza una conclusión.
                            contrario=Prop(h.s,h.p,h.o,not h.neg)
                            if contrario in hechos:continue
                            enl=self._coincide(plantilla,h,env)
                            if enl is not None: siguientes.append((enl,ante+[h]))
                            if len(siguientes)>=500:break
                        if len(siguientes)>=500:break
                    ambientes=siguientes
                    if not ambientes:break
                for env,ante in ambientes:
                    c=self._instanciar(r['conclusion'],env)
                    if c.s in VAR or c.o in VAR:continue
                    if c not in hechos and c not in nuevos:
                        nuevos[c]={'fuente':r['fuente'],'antecedentes':ante}
                    if len(nuevos)>=1000:break
                if len(nuevos)>=1000:break
            if not nuevos:break
            hechos.update(nuevos)
            if len(hechos)>10000:break
        return hechos

    def _referente(self, s):
        if normal(s) not in PRON:return clave(s)
        if not self.ultimo:return None
        candidatos=[self.ultimo.s,self.ultimo.o]
        # Compatibilidad gramatical muy conservadora, no NER ni identidad inferida.
        femenino=normal(s) in {'ella','ellas'}
        compatibles=[x for x in candidatos if (x.endswith('A')==femenino) and x not in {'_','NADIE'}]
        return compatibles[0] if len(set(compatibles))==1 else None

    def _mencionar(self,p):
        if p.s not in VAR and p.o not in VAR:self.ultimo=p

    def _enunciado(self,t):
        birth=re.fullmatch(r'\s*('+PAL+r')\s+naci[oó]\s+en\s+((?:18|19|20)\d{2})\s*[.!]?\s*',t,re.I)
        if birth:
            sujeto,year=birth.groups()
            return 'nacimiento', Prop(clave(sujeto),'NACER','_'),year
        p=_clausula(t,self.parser,permitir_pron=True)
        if p:
            if p.s in {'EL','ELLA','ELLOS','ELLAS'}:
                ref=self._referente(p.s)
                if not ref:return 'ambiguo',None,None
                p=Prop(ref,p.p,p.o,p.neg)
            return 'hecho',p,None
        return None,None,None

    def _guardar_hecho(self,p,texto,year=None):
        if year:
            agregado=self.mem.add_fact((p.s,p.p,p.o),source=texto,when=year)
        else:agregado=self.mem.add_fact((p.s,p.p,p.o),source=texto,neg=p.neg)
        self.mem.note_surface((p.s,p.p,p.o),s_disp=nombre(p.s),o_disp=nombre(p.o))
        if agregado:self.mem.save()
        self._mencionar(p)
        return agregado

    def _regla(self,texto):
        m=re.match(r'^\s*si\s+(.+?)\s*,?\s+entonces\s+(.+?)\s*[.!]?\s*$',texto,re.I)
        if not m:return None
        cuerpo,con=m.groups(); con=con.rstrip('.!? ')
        piezas=re.split(r'\s+y\s+',cuerpo)
        if len(piezas)>2:return 'No puedo registrar más de dos premisas en esta versión.'
        prem=[_clausula(p,self.parser,regla=True) for p in piezas]
        fin=_clausula(con,self.parser,regla=True)
        if not fin or any(p is None for p in prem) or not self._segura(prem,fin):
            return 'No puedo interpretar esa regla con seguridad. Usa «Si X ayuda a Y, entonces Y saluda a X» o dos premisas sencillas.'
        r={'premisas':prem,'conclusion':fin,'fuente':texto.strip()}
        if not any(old['premisas']==prem and old['conclusion']==fin for old in self.reglas):
            self.reglas.append(r);self._guardar()
        return 'He aprendido la relación condicional. No afirmaré su conclusión sin comprobar todas las premisas.'

    def _atribuir(self,texto):
        m=re.match(r'^\s*('+PAL+r')\s+(cree|dice|afirma|piensa)\s+que\s+(.+?)\s*[.!]?\s*$',texto,re.I)
        if not m:return None
        hablante,verbo,contenido=m.groups()
        self.atribuciones.append({'hablante':clave(hablante),'actitud':normal(verbo),'contenido':contenido.strip(' .'), 'fuente':texto})
        self._guardar()
        return f'He registrado que {hablante} {verbo} eso; no lo tomaré automáticamente como un hecho confirmado.'

    @staticmethod
    def _gerundio(forma):
        f=normal(forma)
        if len(f)>5 and f.endswith('ando'):return f[:-4].upper()+'AR'
        if len(f)>6 and f.endswith('iendo'):
            # El radical podría pertenecer a -er o -ir: sin Escuela,
            # la forma sola es ambigua. No inventar identidad léxica.
            return None
        return None

    def _resolver_consulta(self,texto,extra=()):
        """Resuelve preguntas explícitas contra el grafo y devuelve prueba.

        Si la consulta no corresponde a la gramática reconocida, delega en
        el LCM existente sin contaminar su memoria.
        """
        raw=texto.strip(' \t¿?!.')
        t=normal(raw)
        if t in ('por que','como lo sabes'):
            return self.ultima_prueba or 'No tengo una prueba de la respuesta anterior que pueda mostrarte.'
        if t.startswith(('que es','que significa','cuantos','que hora','sabes que hora')):return None
        # ¿Carla a quién está acompañando? / ¿A quién está acompañando Carla?
        # 'estar + gerundio' aporta aspecto, no invierte agente y paciente.
        q=re.fullmatch(r'('+PAL+r')\s+a\s+quien\s+esta\s+('+PAL+r')',t)
        if q:
            su,ger=q.groups()
            pred=self._gerundio(ger)
            if pred:
                ref=self._referente(su)
                if ref:return self._responder_patron(ref,pred,None,extra)
                return 'El antecedente es ambiguo. ¿De quién hablas?'
        q=re.fullmatch(r'a\s+quien\s+esta\s+('+PAL+r')\s+('+PAL+r')',t)
        if q:
            ger,su=q.groups()
            pred=self._gerundio(ger)
            if pred:
                ref=self._referente(su)
                if ref:return self._responder_patron(ref,pred,None,extra)
                return 'El antecedente es ambiguo. ¿De quién hablas?'
        # ¿Quién acompaña a Carla? — variable sujeto.
        q=re.fullmatch(r'quien\s+('+PAL+r')\s+a\s+('+PAL+r')+' ,t)
        if q:
            verbo,ob=q.groups();pred=forma_verbal(verbo)
            if not pred:return None
            return self._responder_patron(None,pred,clave(ob),extra)
        # ¿A quién acompaña Ana? — variable objeto.
        q=re.fullmatch(r'a\s+quien\s+('+PAL+r')\s+('+PAL+r')',t)
        if q:
            verbo,suj=q.groups();pred=forma_verbal(verbo)
            if not pred:return None
            sujeto=self._referente(suj)
            if not sujeto:return 'No sé a quién te refieres. ¿Puedes indicar el sujeto?'
            return self._responder_patron(sujeto,pred,None,extra)
        # ¿Qué compra ella?  (se omite 'a').
        q=re.fullmatch(r'que\s+('+PAL+r')\s+('+PAL+r')',t)
        if q:
            verbo,suj=q.groups();pred=forma_verbal(verbo)
            if not pred:return None
            sujeto=self._referente(suj)
            if not sujeto:return 'El antecedente es ambiguo. ¿De quién hablas?'
            return self._responder_patron(sujeto,pred,None,extra)
        # ¿Dónde vive Ana? / ¿Dónde trabaja Ana? — predicado con rol locativo.
        q=re.fullmatch(r'donde\s+('+PAL+r')\s+('+PAL+r')',t)
        if q:
            verbo,suj=q.groups();pred=forma_verbal(verbo)
            if pred:
                sujeto=self._referente(suj)
                if not sujeto:return 'El antecedente es ambiguo. ¿De quién hablas?'
                return self._responder_patron(sujeto,pred+'_EN',None,extra)
        # ¿Ayuda Ana a Luis? Es interrogativa polar; no inferir inversión.
        q=re.fullmatch(r'('+PAL+r')\s+('+PAL+r')\s+(?:a\s+)?('+PAL+r')',t)
        if q:
            verbo,suj,ob=q.groups();pred=forma_verbal(verbo)
            if pred and normal(suj) not in FUNCIONALES:
                sujeto=self._referente(suj)
                if not sujeto:return 'El referente es ambiguo. ¿Puedes aclararlo?'
                return self._responder_patron(sujeto,pred,clave(ob),extra)
        return None

    def _responder_patron(self,s,p,o,extra=()):
        hechos=self._cierre(extra)
        buenos=[(h,e) for h,e in hechos.items() if h.p==p and (s is None or h.s==s) and (o is None or h.o==o)]
        positivos=[(h,e) for h,e in buenos if not h.neg]
        negativos=[(h,e) for h,e in buenos if h.neg]
        if s is not None and o is not None:
            if positivos and negativos:return 'Hay testimonios incompatibles; no puedo afirmar sí o no sin aclaración.'
            if positivos:
                h,e=positivos[0]
                prueba=self._prueba(h,hechos)
                self.ultima_prueba=prueba
                return 'Sí. '+prueba
            if negativos:return f'No: consta explícitamente una negación de esa relación ({nombre(s)}, {p.lower()}, {nombre(o)}).'
            return 'No consta información suficiente para afirmarlo ni negarlo.'
        if positivos:
            pares=sorted({(h.s,h.o) for h,_ in positivos})
            if len(pares)>6:pares=pares[:6]
            nombres=[nombre(x if o is not None else y) for x,y in pares]
            h,e=positivos[0]
            self.ultima_prueba=self._prueba(h,hechos)
            return ', '.join(nombres)+'. '+self.ultima_prueba
        if negativos:return 'Solo constan negaciones, no una respuesta afirmativa.'
        return 'No consta una relación de ese tipo; no invertiré las relaciones existentes.'

    def _prueba(self,h,hechos,visitados=None):
        if visitados is None: visitados=set()
        if h in visitados:return 'Se detectó una referencia circular en la explicación.'
        visitados.add(h)
        info=hechos[h]; prev=info['antecedentes']
        if not prev:
            return f'Consta {nombre(h.s)} {h.p.lower().replace("_"," ")} {nombre(h.o)}, por «{info["fuente"]}».'
        pasos=[]
        for p in prev:
            pasos.append(self._prueba(p,hechos,visitados))
        return 'Se deduce por la regla «'+info['fuente']+'» a partir de: '+' '.join(pasos)

    def procesar(self,texto):
        """Devuelve respuesta o None para delegar. No tiene efectos en entradas interrogativas salvo contexto."""
        t=(texto or '').strip()
        if not t:return None
        # Un «si» condicional no es nunca un hecho de memoria.
        if re.match(r'^si\s+',normal(t)):
            # Suponer premisas en una consulta NO las guarda.
            trozos=re.match(r'^\s*si\s+(.+?)\s*,\s*(¿?.+\?)\s*$',t,re.I)
            if trozos:
                prem,q=trozos.groups();extra=_clausula(prem,self.parser,regla=True)
                if extra:
                    ans=self._resolver_consulta(q,[extra])
                    return ans if ans is not None else 'No puedo evaluar esa pregunta hipotética sin más estructura.'
            reg=self._regla(t)
            if reg:return reg
            return 'Es una condición, no un hecho observado. Necesito que indiques «si ... entonces ...» para aprender la regla.'
        if re.search(r'\b(?:no se si|no sabemos si|me pregunto si|y si)\b',normal(t)):
            return 'Eso expresa duda o una condición; no registraré el contenido como hecho confirmado.'
        if '?' in t or '¿' in t:
            return self._resolver_consulta(t)
        if MODALES.search(t):
            atr=self._atribuir(t)
            if atr:return atr
            return 'Detecto una creencia o posibilidad, no un hecho confirmado. No la guardaré como verdadera.'
        if re.search(r'\b(?:seria|podria|quizas|tal vez|suele|suelen|puede|pueden|deberia)\b',normal(t)):
            return 'Es una posibilidad, no un hecho confirmado; no la guardaré como verdadera.'
        tipo,p,year=self._enunciado(t)
        if tipo=='ambiguo':return 'No tengo un antecedente inequívoco para ese pronombre. ¿A quién te refieres?'
        if p:
            nuevo=self._guardar_hecho(p,t,year)
            return 'He registrado ese hecho con su procedencia.' if nuevo else 'Ese hecho ya constaba en mi memoria.'
        return None

    def observar_turno(self,texto):
        """Invocable después del conversador anterior, para seguir el sujeto sin reescribir hechos."""
        if '?' in texto or '¿' in texto or re.match(r'^si\b',normal(texto)) or MODALES.search(texto):return
        _,p,_=self._enunciado(texto)
        if p:self._mencionar(p)


def respuesta_http(texto,mem,parser=None, motor=None):
    """Adaptador web: devuelve dict de Motor o None, conservando API antigua."""
    engine=getattr(motor,'_dialogo16',None) if motor is not None else None
    if engine is None:
        engine=DialogoConceptual(mem,parser)
        if motor is not None:motor._dialogo16=engine
    ans=engine.procesar(texto)
    if ans is None:return None
    return {'respuesta':ans,'aprendido':[],'imagen':None,'fallo':False,'ms':0,
            'hechos':len(mem.facts),'delta':0,'composicion16':{'modulo':'alcance_y_reglas','prueba':engine.ultima_prueba}}
