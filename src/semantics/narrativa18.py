"""LCM 1.8: marcos de evento con roles, control de objetos y pruebas de procedencia.

Un hecho relatado por una persona NO equivale a una observacion por el modelo.
Las acciones se normalizan mediante un catalogo de sentidos externo a este codigo.
El parser deliberadamente restringido se abstiene ante estructuras no soportadas.
"""
from __future__ import annotations
import json
import os
import re
import tempfile
from pathlib import Path
from dataclasses import dataclass
from src.semantics.dialogue16 import normal, clave, nombre

SCHEMA='lcm-narrativa-1.8'
WORD=r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+'
# Alcance epistemico y ordenes. No permite hechos sin proposicion afirmativa.
NO_HECHO=re.compile(r'^(?:si\b|ojal[aá]\b|seg[uú]n\b|por favor\b|imagina\b|supongamos\b|no s[eé] si\b|me gustar[ií]a\b|puede que\b|quiz[aá]s\b|tal vez\b|se rumorea\b|es posible\b|creo que\b)|\b(?:dice que|dijo que|cree que|piensa que|podr[ií]a|habr[ií]a)\b',re.I)
QUERY_NO_PROPIEDAD=re.compile(r'^(?:quien es (?:el |la )?(?:dueno|duena|propietario|propietaria)|de quien es)\b')
TEMPORAL_PRE=re.compile(r'^(?:despu[eé]s|m[aá]s tarde|a continuaci[oó]n|entonces|luego)\s+',re.I)
ART=r'(?:el|la|los|las|un|una|unos|unas|su|sus|dos|tres)'
VERB=rf'{WORD}(?:\s+{WORD})?'

@dataclass(frozen=True)
class Evento:
    agente: str
    accion: str
    tema: str
    destinatario: str
    genero: str
    fuente: str

class Narrativa18:
    def __init__(self,mem,ruta=None):
        self.mem=mem
        self.ruta=Path(ruta) if ruta else Path(getattr(mem,'path','memory/lcm_memory.json')).with_name('lcm_narrativa18.json')
        catalogo=Path(__file__).with_name('acciones18.json')
        data=json.loads(catalogo.read_text(encoding='utf8'))
        if data.get('schema')!='lcm18-acciones-1':raise ValueError('Catalogo de acciones no reconocido')
        self.lex={}
        self.acciones={}
        for a in data['acciones']:
            if a['marco']!='TRANSFERENCIA_CONTROL' or a['efecto']!='DESTINATARIO_CONTROLA':continue
            self.acciones[a['id']]=a
            for forma in a['formas']:
                key=normal(forma)
                if key in self.lex and self.lex[key]!=a['id']:raise ValueError('Forma ambigua sin desambiguar: '+forma)
                self.lex[key]=a['id']
        self.registros=[]
        self.dudas=set()
        self.ultimo_tema=None
        self.ultima_prueba=None
        if self.ruta.exists():
            state=json.loads(self.ruta.read_text(encoding='utf8'))
            if state.get('schema')!=SCHEMA or not isinstance(state.get('registros'),list):
                raise ValueError('Memoria de narrativa desconocida: no se modifica')
            for e in state['registros'][-3000:]:
                if isinstance(e,dict) and all(isinstance(e.get(k),str) for k in ('agente','accion','tema','destinatario','genero','fuente')):
                    self.registros.append(e)
            self.dudas=set(state.get('dudas',[]))
        if self.registros:self.ultimo_tema=self.registros[-1]['tema']

    def _guardar(self):
        self.ruta.parent.mkdir(parents=True,exist_ok=True)
        state={'schema':SCHEMA,'registros':self.registros[-3000:],'dudas':sorted(self.dudas)}
        fd,path=tempfile.mkstemp(prefix='.narrativa18_',suffix='.tmp',dir=self.ruta.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf8') as f:
                json.dump(state,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
            os.replace(path,self.ruta)
        finally:
            if os.path.exists(path):os.unlink(path)

    @staticmethod
    def _obj(art,pal):
        articulo=normal(art);tema=clave(pal)
        plural=articulo in ('los','las','unos','unas','sus','dos','tres') or normal(pal).endswith('s') and articulo in ('su','sus','dos','tres')
        fem=articulo in ('la','una','las','unas') or (articulo in ('su','sus','dos','tres') and normal(pal).endswith('a'))
        return tema,('f' if fem else 'm')+('p' if plural else '')

    @staticmethod
    def _pron_compatible(pron,genero):
        return {'lo':'m','la':'f','los':'mp','las':'fp'}.get(normal(pron))==genero

    def _interpretar_evento(self,t):
        """Analiza el marco TRANSFERENCIA_CONTROL, sin asignar verdad de propiedad.

        Los lemas y sus roles están en acciones18.json. Las estructuras
        gramaticales genéricas varían en posición y voz, no en nombres propios.
        """
        texto=t.strip(' .!')
        texto=TEMPORAL_PRE.sub('',texto)
        texto=re.sub(r'^(?:la semana pasada|esta manana|esta mañana|ayer|hoy)\s+', '', texto, flags=re.I)
        texto=re.sub(r'^despues de [^,]{1,60},\s*','',texto,flags=re.I)
        if NO_HECHO.search(texto) or re.search(r'[?¿;]|\b(?:porque|aunque|cuando|mientras|para que)\b',texto,re.I):return None
        # En «el paquete que había preparado», la relativa no modifica el
        # evento nuclear; no se extraen hechos de la relativa.
        texto=re.sub(r'\s+que\s+hab[ií]a\s+'+WORD+r'$', '', texto, flags=re.I)

        # Voz pasiva: articulo + tema + fue + participio + a destinatario + por agente.
        m=re.fullmatch(rf'({ART})\s+({WORD})\s+fue\s+({WORD})\s+a\s+({WORD})\s+por\s+({WORD})',texto,re.I)
        if m:
            art,tema,forma,receptor,agente=m.groups();accion=self.lex.get(normal(forma)) or (self.lex.get(normal(forma[:-1]+'o')) if normal(forma).endswith('a') else None)
            if accion and agente[:1].isupper() and receptor[:1].isupper():
                obj,gen=self._obj(art,tema)
                return Evento(clave(agente),accion,obj,clave(receptor),gen,t.strip()),False

        # Marco inverso de recepción: tema + lo/la recibió + receptor + de manos de agente.
        # Solo si se indican ambos participantes y el objeto; no presupone propiedad.
        m=re.fullmatch(rf'({ART})\s+({WORD})\s+(?:lo|la)\s+recibi[oó]\s+({WORD})\s+de\s+manos\s+de\s+({WORD})',texto,re.I)
        if m:
            art,tema,receptor,agente=m.groups()
            if receptor[:1].isupper() and agente[:1].isupper():
                obj,gen=self._obj(art,tema)
                return Evento(clave(agente),'accion.recibir',obj,clave(receptor),gen,t.strip()),False

        # Transferencia con objeto antes del destinatario, participio compuesto,
        # o accion conceptual compuesta («hacer llegar»).
        m=re.fullmatch(rf'({WORD})\s+(no\s+)?(?:le\s+)?(?:ha\s+)?({VERB})\s+({ART})\s+({WORD})(?:\s+({WORD}))?\s+a\s+({WORD})',texto,re.I)
        if m:
            agente,neg,forma,art,tema,adjetivo,receptor=m.groups()
            accion=self.lex.get(normal(forma))
            if accion and agente[:1].isupper() and receptor[:1].isupper():
                # Sin objeto indirecto el «adjetivo» no puede ser otra persona.
                obj,gen=self._obj(art,tema)
                return Evento(clave(agente),accion,obj,clave(receptor),gen,t.strip()),bool(neg)

        # Complementos desplazados: Ana le entregó a Luis el libro.
        m=re.fullmatch(rf'({WORD})\s+(no\s+)?(?:le\s+)?({VERB})\s+a\s+({WORD})\s+({ART})\s+({WORD})(?:\s+({WORD}))?',texto,re.I)
        if m:
            agente,neg,forma,receptor,art,tema,adjetivo=m.groups()
            accion=self.lex.get(normal(forma))
            if accion and agente[:1].isupper() and receptor[:1].isupper():
                obj,gen=self._obj(art,tema)
                return Evento(clave(agente),accion,obj,clave(receptor),gen,t.strip()),bool(neg)

        # «Pedro se la devolvió a Ana», último objeto inambiguo y género claro.
        m=re.fullmatch(rf'({WORD})\s+(no\s+)?(?:(?:se\s+)?(lo|la|los|las))\s+({WORD})\s+a\s+({WORD})',texto,re.I)
        if m:
            agente,neg,clit,forma,receptor=m.groups();accion=self.lex.get(normal(forma))
            if accion and self.acciones[accion]['lema']=='devolver' and agente[:1].isupper() and receptor[:1].isupper():
                tema=self.ultimo_tema
                if not tema:return ('ambiguo',None)
                hist=self._ultimos(tema)
                if not hist or not self._pron_compatible(clit,hist[-1]['genero']):return ('ambiguo',None)
                return Evento(clave(agente),accion,tema,clave(receptor),hist[-1]['genero'],t.strip()),bool(neg)
        return None

    def _ultimos(self,tema):return [e for e in self.registros if e['tema']==tema]
    def _estado(self,tema):
        if tema in self.dudas:return 'unknown',None
        hist=self._ultimos(tema)
        if not hist:return 'unknown',None
        return hist[-1]['destinatario'],hist[-1]

    def _responder(self,texto):
        t=normal(texto.strip(' ¿?!.'))
        # Propiedad y posesion intencionadamente separadas.
        if QUERY_NO_PROPIEDAD.search(t):
            return 'No consta quién es propietario: recibir o tener un objeto no demuestra ser su dueño.'
        obj=None;modo=None;referencia=False
        # ¿Quién tiene el libro? / ¿Quién lo tiene ahora?
        m=re.fullmatch(rf'quien\s+(?:tiene|tenia|tuvo)\s+(?:ahora\s+)?(?:({ART})\s+({WORD})|(lo|la|los|las))(?:\s+(antes|ahora))?',t)
        if m:
            art,tema,clit,cuando=m.groups()
            obj=clave(tema) if tema else self.ultimo_tema
            if not obj:return 'No tengo un antecedente inequívoco para identificar el objeto.'
            modo='anterior' if cuando=='antes' or t.startswith('quien tenia') else 'actual'
        if modo is None:
            m_quedar=re.fullmatch(rf'quien\s+se\s+quedo\s+con\s+({ART})\s+({WORD})',t)
            if m_quedar:
                art,tema=m_quedar.groups();obj=clave(tema);modo='actual'
        if modo is None:
            # Clítico antepuesto: «¿Quién lo tenía antes?».
            m_pron=re.fullmatch(r'quien\s+(lo|la|los|las)\s+(tiene|tenia|tuvo)(?:\s+(antes|ahora))?',t)
            if m_pron:
                pr,verbo,cuando=m_pron.groups()
                obj=self.ultimo_tema
                hist=self._ultimos(obj) if obj else []
                if not hist or not self._pron_compatible(pr,hist[-1]['genero']):
                    return 'No tengo un antecedente inequívoco para ese pronombre.'
                modo='anterior' if verbo in ('tenia','tuvo') or cuando=='antes' else 'actual'
        if modo is None:
            m=re.fullmatch(rf'quien\s+(?:recibio|lo\s+recibio|la\s+recibio)(?:\s+(?:({ART})\s+({WORD})|(lo|la|los|las)))?(?:\s+al final)?',t)
            if m:
                art,tema,clit=m.groups()
                obj=clave(tema) if tema else self.ultimo_tema;modo='ultimo'
        if modo is None:
            m=re.fullmatch(rf'a quien\s+({WORD})\s+({WORD})\s+({ART})\s+({WORD})',t)
            if m:
                verbo,suj,art,tema=m.groups();accion=self.lex.get(normal(verbo))
                if accion:
                    rows=[e for e in self.registros if e['accion']==accion and e['agente']==clave(suj) and e['tema']==clave(tema)]
                    if rows and clave(tema) not in self.dudas:return nombre(rows[-1]['destinatario'])+'. Según «'+rows[-1]['fuente']+'».'
                    return 'No consta una entrega de ese tipo con evidencia suficiente.'
        if modo is None:
            m=re.fullmatch(rf'que\s+({WORD})\s+({WORD})',t)
            if m:
                verbo,suj=m.groups();accion=self.lex.get(normal(verbo))
                if accion:
                    rows=[e for e in self.registros if e['accion']==accion and e['agente']==clave(suj)]
                    if rows:return nombre(rows[-1]['tema'])+'. Según «'+rows[-1]['fuente']+'».'
                    return 'No consta ese hecho.'
        if modo is None:
            m=re.fullmatch(rf'por que dices que\s+({WORD})\s+tiene\s+({ART})\s+({WORD})',t)
            if m:
                su,art,obj=m.groups();actual,e=self._estado(clave(obj))
                if actual==clave(su):return 'Porque consta la declaración «'+e['fuente']+'»; no lo he observado directamente.'
                return 'No tengo evidencia suficiente para sostener esa afirmación.'
        if modo is None:return None
        if not obj:return 'No tengo un antecedente inequívoco para identificar el objeto.'
        estado,e=self._estado(obj)
        if estado=='unknown':return 'No consta información suficiente sobre quién tiene ese objeto.'
        if modo=='anterior':
            hist=self._ultimos(obj)
            if len(hist)<2:return 'No consta información suficiente sobre la posesión anterior.'
            e=hist[-2];estado=e['destinatario']
        self.ultimo_tema=obj
        self.ultima_prueba='Según la declaración «'+e['fuente']+'», '+nombre(estado)+' recibió '+nombre(obj)+'.'
        return nombre(estado)+'. '+self.ultima_prueba

    def procesar(self,texto):
        if not isinstance(texto,str) or len(texto)>500:return None
        s=texto.strip()
        if not s:return None
        if '¿' in s or '?' in s:
            return self._responder(s)
        event=self._interpretar_evento(s)
        if event is None:
            # Una devolución narrada sin agente explícito puede alterar la
            # posesión; no presentar como actual el último estado conocido.
            if (self.ultimo_tema and re.fullmatch(
                rf'(?:lo|la|los|las|se\s+lo|se\s+la|se\s+los|se\s+las)\s+({WORD})\s+a\s+({WORD})[.!]?',s,re.I)):
                forma=re.match(rf'(?:lo|la|los|las|se\s+lo|se\s+la|se\s+los|se\s+las)\s+({WORD})',s,re.I).group(1)
                accion=self.lex.get(normal(forma))
                if accion and self.acciones[accion]['lema']=='devolver':
                    self.dudas.add(self.ultimo_tema);self._guardar()
                    return 'No sé quién realizó esa devolución; necesito identificar al agente antes de actualizar la posesión.'
            return None
        if event[0]=='ambiguo':return 'No puedo resolver el objeto del pronombre con seguridad. ¿A qué objeto te refieres?'
        frame,neg=event
        if neg:return 'He registrado la negación como información del diálogo; no asumiré que ocurrió una transferencia.'
        previo=self._estado(frame.tema)[0]
        # Un agente no puede entregar sin aclaracion un objeto cuya posesion
        # se atribuyo a alguien diferente. Mantener el conflicto explícito.
        if previo not in ('unknown',frame.agente):
            self.dudas.add(frame.tema);self._guardar()
            return 'Hay declaraciones incompatibles sobre quién controlaba ese objeto; necesito aclaración.'
        d=dict(agente=frame.agente,accion=frame.accion,tema=frame.tema,destinatario=frame.destinatario,genero=frame.genero,fuente=frame.fuente,canal='texto_declarado')
        if self.registros and self.registros[-1]==d:
            return 'Ese acontecimiento ya estaba registrado; no lo duplicaré.'
        self.registros.append(d)
        self.ultimo_tema=frame.tema
        self._guardar()
        return 'He registrado un acontecimiento con agente, objeto, destinatario y fuente. No implica propiedad legal.'


def respuesta_http(texto,mem,parser=None,motor=None):
    instancia=getattr(motor,'_narrativa18',None) if motor is not None else None
    if instancia is None:
        instancia=Narrativa18(mem)
        if motor is not None:motor._narrativa18=instancia
    respuesta=instancia.procesar(texto)
    if respuesta is None:return None
    return {'respuesta':respuesta,'aprendido':[],'imagen':None,'fallo':False,'ms':0,'hechos':len(mem.facts),'delta':0,
            'narrativa18':{'eventos':len(instancia.registros),'dudas':len(instancia.dudas)}}
