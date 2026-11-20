"""LCM 1.9: puente conservador entre la Escuela UD y acontecimientos conceptuales.

Este modulo NO simula los pesos neuronales: acepta la API SchoolParser.tree.
Solo registra eventos cuando los roles estan respaldados por dependencias
sintacticas explicitamente compatibles y una accion tiene un marco semantico.
No asume propiedad legal, simetria, verdad de testimonios, ni identidad
entre menciones sin evidencia.
"""
from __future__ import annotations
import json
import os
import re
import tempfile
from datetime import date, timedelta
from dataclasses import dataclass
from pathlib import Path
from src.semantics.dialogue16 import clave, nombre, normal

SCHEMA = 'lcm-ud-discurso-1.9'
WORDS = r'[a-záéíóúüñ0-9_]+'
# Guardas de alcance: estas expresiones NO autorizan a afirmar el hecho
# subordinado. No sustituyen la semantica vectorial ni definen comandos.
GUARD = re.compile(r'\b(?:si|ojala|quizas|quiza|quizá|segun|según|supongamos|imagina|imagine|'
                   r'creo|cree|creen|pensaba|piensa|dicen|dijo|dice|afirma|afirmo|afirmó|'
                   r'puede que|tal vez|talvez|es posible que|habria|habría|podria|podría|'
                   r'deberia|debería|no se si|no sé si|para que|aunque|mientras)\b', re.I)

@dataclass(frozen=True)
class EventoUD:
    agente: str
    tema: str
    destinatario: str
    accion: str
    fuente: str
    genero: str = ''
    tiempo: str = 'actual'
    esquema: str = 'TRANSFERENCIA_CONTROL'


def _kids(rows, i):
    return [j for j,r in enumerate(rows) if r[2] == i + 1]


def _norm(s):
    return normal(s)


def _safe_rows(rows, text):
    if not isinstance(rows,(list,tuple)) or not 2 <= len(rows) <= 60:return False
    allowed={'nsubj','obj','iobj','obl','case','det','amod','nmod','flat','nsubj:pass',
             'obl:agent','root','punct','aux','aux:pass','cc','conj','advmod','neg','expl',
             'mark','advcl','acl','ccomp','xcomp','cop','compound','dep'}
    for j,r in enumerate(rows):
        if not isinstance(r,(tuple,list)) or len(r)<5:return False
        f,u,h,rel,lemma=r[:5]
        if not isinstance(h,int) or h<0 or h>len(rows) or h==j+1:return False
        if not all(isinstance(z,str) for z in (f,u,rel,lemma)) or not f or rel not in allowed:return False
        if not any(ch.isalnum() for ch in f):continue
        if _norm(f) not in _norm(text).split() and not re.search(r'\b'+re.escape(_norm(f))+r'\b',_norm(text)):
            return False
    # No ciclos; un unico root real
    if sum(r[2]==0 and r[3]=='root' for r in rows)!=1:return False
    for j in range(len(rows)):
        seen=set();i=j
        while rows[i][2]:
            if i in seen:return False
            seen.add(i);i=rows[i][2]-1
    return True


class PuenteUD19:
    def __init__(self, memoria, parser, ruta=None):
        self.mem=memoria
        self.parser=parser
        base=Path(getattr(memoria,'path','memory/lcm_memory.json'))
        self.ruta=Path(ruta) if ruta else base.with_name('lcm_ud19.json')
        catalogo=json.loads(Path(__file__).with_name('acciones18.json').read_text(encoding='utf8'))
        self.acciones={a['lema']:a for a in catalogo['acciones']
                       if a.get('marco')=='TRANSFERENCIA_CONTROL' and a.get('efecto')=='DESTINATARIO_CONTROLA'}
        self.eventos=[]
        self.dudas=set()
        self.ultimo_tema=None
        if self.ruta.exists():
            d=json.loads(self.ruta.read_text(encoding='utf8'))
            if d.get('schema')!=SCHEMA or not isinstance(d.get('eventos'),list):
                raise ValueError('Memoria UD19 con esquema desconocido. No se modifica.')
            self.dudas=set(d.get('dudas',[]))
            for e in d['eventos'][-3000:]:
                if isinstance(e,dict) and all(isinstance(e.get(k),str) for k in
                       ('agente','tema','destinatario','accion','fuente','canal')):
                    self.eventos.append(e)
            if self.eventos:self.ultimo_tema=self.eventos[-1]['tema']

    def _guardar(self):
        self.ruta.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix='.ud19_',suffix='.tmp',dir=self.ruta.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf8') as f:
                json.dump({'schema':SCHEMA,'eventos':self.eventos[-3000:],'dudas':sorted(self.dudas)},f,ensure_ascii=False,indent=2)
                f.flush();os.fsync(f.fileno())
            os.replace(tmp,self.ruta)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)

    def _nodo(self, rows, k, tipo='persona'):
        if k is None:return None
        f,u,_,_,lemma=rows[k][:5]
        if tipo=='persona':
            if u!='PROPN' or not f[:1].isupper():return None
            # personas con nombre compuesto mediante flat
            nombres=[(k,f)]+[(j,rows[j][0]) for j in _kids(rows,k) if rows[j][3]=='flat']
            return clave('_'.join(w for _,w in sorted(nombres)))
        if u not in ('NOUN','PROPN'):return None
        # Los modificadores sirven para distinguir: libro rojo != libro azul.
        ajustes=[_norm(rows[j][4] or rows[j][0]) for j in _kids(rows,k)
                 if rows[j][3] in ('amod','nummod')]
        return clave('_'.join([_norm(lemma or f)]+sorted(ajustes)))

    def _genero(self,rows,k):
        if k is None:return ''
        det={_norm(rows[j][0]) for j in _kids(rows,k) if rows[j][3]=='det'}
        if det & {'la','una'}:return 'f'
        if det & {'el','un'}:return 'm'
        return ''

    def _case(self,rows,k):
        return {_norm(rows[j][0]) for j in _kids(rows,k) if rows[j][3]=='case'}

    def _extraer(self, texto):
        if self.parser is None or not hasattr(self.parser,'tree'):return None
        if len(texto)>400 or any(c in texto for c in '?¿;\n') or GUARD.search(_norm(texto)):
            return None
        try:rows=self.parser.tree(texto)
        except Exception:return None
        if not _safe_rows(rows,texto):return None
        # Una sola clausula informativa: jamás afirmar una subordinada o una coordinacion no procesada.
        if any(r[3] in ('ccomp','xcomp','advcl','conj') and r[1]=='VERB' for r in rows):return None
        vi=[j for j,r in enumerate(rows) if r[3]=='root' and r[1] in ('VERB','AUX')]
        if len(vi)!=1:return None
        i=vi[0]
        lemma=_norm(rows[i][4])
        # Es un marco conceptual ya existente, no una lista de frases/comandos.
        accion=self.acciones.get(lemma)
        if accion is None or lemma=='hacer llegar':return None
        hijos=_kids(rows,i)
        # Negación explícita no altera posesión. Imperativos no tienen sujeto garantizado.
        if any(_norm(rows[j][0]) in ('no','nunca','jamas','jamás','tampoco') for j in hijos):return None
        # El infinitivo, presente futuro o forma condicional no se equiparan automáticamente a un hecho.
        if _norm(rows[i][0])==lemma:return None
        # Los checkpoints de la Escuela 1.x eliminan subtipos UD: nsubj:pass
        # se convierte en nsubj y obl:agent en obl. Recuperamos la voz pasiva
        # por el auxiliar SER y el complemento de agente introducido por 'por'.
        voz_pasiva=any(rows[j][3]=='aux' and _norm(rows[j][4])=='ser' for j in hijos)
        subj=[j for j in hijos if rows[j][3]=='nsubj' and not voz_pasiva]
        subj_pass=[j for j in hijos if rows[j][3]=='nsubj:pass' or
                   (voz_pasiva and rows[j][3]=='nsubj')]
        allowed={_norm(f) for f in accion.get('formas',[])}
        forma=_norm(rows[i][0])
        if voz_pasiva:
            # Participio es MORFOLOGÍA, no una equivalencia de intención.
            irregular={'dar':'dado','devolver':'devuelto'}
            participio=irregular.get(lemma) or (lemma[:-2]+('ado' if lemma.endswith('ar') else 'ido'))
            allowed.add(participio)
            allowed |= {x[:-1]+'a' for x in list(allowed) if x.endswith('o')}
        elif lemma.endswith(('ar','er','ir')):
            allowed.add(lemma[:-2]+('a' if lemma.endswith('ar') else 'e'))
        if forma not in allowed:return None
        objs=[j for j in hijos if rows[j][3]=='obj']
        dativos=[j for j in hijos if rows[j][3] in ('iobj','obl') and 'a' in self._case(rows,j)]
        agentes=[j for j in hijos if rows[j][3] in ('obl','obl:agent') and 'por' in self._case(rows,j)]
        origen=[j for j in hijos if rows[j][3]=='obl' and 'de' in self._case(rows,j)]
        if lemma=='recibir':
            if len(subj)!=1 or len(objs)!=1 or len(origen)!=1:return None
            agente=self._nodo(rows,origen[0]);destino=self._nodo(rows,subj[0]);tema=self._nodo(rows,objs[0],'objeto')
        elif subj_pass:
            if len(subj_pass)!=1 or len(agentes)!=1 or len(dativos)!=1 or subj:return None
            agente=self._nodo(rows,agentes[0]);destino=self._nodo(rows,dativos[0]);tema=self._nodo(rows,subj_pass[0],'objeto')
        else:
            if len(subj)!=1 or len(objs)!=1 or len(dativos)!=1:return None
            agente=self._nodo(rows,subj[0]);destino=self._nodo(rows,dativos[0]);tema=self._nodo(rows,objs[0],'objeto')
        # Clíticos referenciales: una sola mención de objeto compatible;
        # varias posibilidades fuerzan abstención, nunca elección al azar.
        tema_i=objs[0] if not subj_pass else subj_pass[0]
        if tema is None and rows[tema_i][1]=='PRON':
            clit=_norm(rows[tema_i][0])
            if clit in {'lo','la'} and self.ultimo_tema and len({e['tema'] for e in self.eventos})==1:
                candidatos=[e for e in self.eventos if e['tema']==self.ultimo_tema]
                gen=candidatos[-1].get('genero') if candidatos else None
                if gen==('f' if clit=='la' else 'm'):
                    tema=self.ultimo_tema
        if not all((agente,destino,tema)) or agente==destino:return None
        palabras=set(_norm(texto).split())
        if palabras & {'manana','mañana','proximamente'}:
            return None  # evento futuro no realizado
        base=getattr(self.mem,'today',None)
        if not isinstance(base,date):base=date.today()
        tiempo=(base-timedelta(days=1)).isoformat() if 'ayer' in palabras else \
                (base-timedelta(days=1)).isoformat() if 'anoche' in palabras else 'actual'
        return EventoUD(agente,tema,destino,accion['id'],texto.strip(),
                        self._genero(rows,objs[0] if not subj_pass else subj_pass[0]),tiempo)

    def _consultar(self, texto):
        q=_norm(texto.strip(' ¿?!.'))
        if not q:return None
        # Consultas focalizadas en roles, no un enrutador universal de intenciones.
        modo=None;obj=None;su=None;dest=None;accion=None;pron=None;cuando=None
        m=re.fullmatch(rf'quien (?:tiene|tenia|tuvo) (?:ahora )?(?:el |la |un |una )?({WORDS})(?: (antes|ahora))?',q)
        if m:
            obj=clave(m.group(1));modo='antes' if m.group(2)=='antes' or 'tenia' in q else 'actual'
        if modo is None:
            m=re.fullmatch(rf'quien (?:lo|la) (?:tiene|tenia|tuvo)(?: (antes|ahora))?',q)
            if m:
                if not self.ultimo_tema:return 'No tengo un antecedente inequívoco para ese objeto.'
                obj=self.ultimo_tema;pron='f' if 'quien la ' in q else 'm';modo='antes' if 'tenia' in q or 'antes' in q else 'actual'
        if modo is None:
            m=re.fullmatch(rf'quien (?:recibio|recibió) (?:el |la |un |una )?({WORDS})',q)
            if m:obj=clave(m.group(1));modo='ultimo'
        if modo is None:
            m=re.fullmatch(rf'a quien (?:le )?({WORDS}) ({WORDS}) (?:el |la |un |una )?({WORDS})',q)
            if m:
                verb,who,item=m.groups();su=clave(who);obj=clave(item);modo='destinatario'
                accion=self._accion_consulta(verb)
                if accion is None:return None
        if modo is None:
            m=re.fullmatch(rf'quien ({WORDS}) (?:el |la |un |una )?({WORDS}) a ({WORDS})',q)
            if m:
                verb,item,to=m.groups();dest=clave(to);obj=clave(item);modo='agente'
                accion=self._accion_consulta(verb)
                if accion is None:return None
        if modo is None:
            m=re.fullmatch(rf'que ({WORDS}) ({WORDS}) a ({WORDS})',q)
            if m:
                verb,who,to=m.groups();su=clave(who);dest=clave(to);modo='tema'
                accion=self._accion_consulta(verb)
                if accion is None:return None
        if modo is None:
            m=re.fullmatch(rf'quien (?:recibio|recibió) (?:el |la |un |una )?({WORDS}) (ayer|anoche)',q)
            if m:
                obj=clave(m.group(1));modo='ultimo'
                base=getattr(self.mem,'today',None)
                if not isinstance(base,date):base=date.today()
                cuando=(base-timedelta(days=1)).isoformat()
        if modo is None:return None
        if obj in self.dudas:return 'No consta quién tiene ese objeto: existen declaraciones incompatibles.'
        if not self.eventos:return None  # Respeta los episodios previos de LCM 1.8
        rows=[e for e in self.eventos if (obj is None or e['tema']==obj)
              and (su is None or e['agente']==su) and (dest is None or e['destinatario']==dest)
              and (accion is None or e['accion']==accion)
              and (cuando is None or e.get('tiempo')==cuando)]
        if pron and rows and rows[-1].get('genero')!=pron:
            return 'No tengo un antecedente inequívoco compatible con ese pronombre.'
        if not rows:
            if accion is not None and any(e['tema']==obj for e in self.eventos):
                return 'No consta esa acción concreta con evidencia suficiente.'
            return None  # Delegar al conocimiento historico de LCM 1.8
        if modo=='antes':
            if len(rows)<2:return 'No consta quién tenía ese objeto antes de la transferencia.'
            elegido=rows[-2]
        else: elegido=rows[-1]
        if modo=='actual' and elegido.get('tiempo','actual')!='actual':
            return 'Solo tengo evidencia de una transferencia pasada; no consta la posesión actual.'
        key={'actual':'destinatario','ultimo':'destinatario','antes':'destinatario','destinatario':'destinatario',
             'agente':'agente','tema':'tema'}[modo]
        return self._visible(elegido,elegido[key])+'. Según la declaración «'+elegido['fuente']+'».'

    @staticmethod
    def _visible(registro, clave_entidad):
        # El identificador vectorial omite tildes, la verbalizacion no.
        fuente=registro.get('fuente','')
        for palabra in re.findall(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+',fuente):
            if clave(palabra)==clave_entidad:return palabra[0].upper()+palabra[1:]
        return nombre(clave_entidad)

    def _accion_consulta(self, forma):
        f=_norm(forma)
        encontrados={a['id'] for a in self.acciones.values() for x in a.get('formas',[])
                     if f==_norm(x)}
        return next(iter(encontrados)) if len(encontrados)==1 else None

    def procesar(self,texto):
        if not isinstance(texto,str) or not texto.strip():return None
        if '¿' in texto or '?' in texto:
            return self._consultar(texto)
        ev=self._extraer(texto)
        if ev is None:return None
        hist=[x for x in self.eventos if x['tema']==ev.tema]
        if hist and hist[-1]['destinatario']!=ev.agente:
            # No mantener un estado confiado tras una declaración incompatible.
            self.dudas.add(ev.tema);self._guardar()
            return 'No puedo confirmar la continuidad del objeto entre esas transferencias; necesito aclaración.'
        row={'agente':ev.agente,'tema':ev.tema,'destinatario':ev.destinatario,
             'accion':ev.accion,'fuente':ev.fuente,'canal':'texto_declarado','genero':ev.genero,'tiempo':ev.tiempo}
        if self.eventos and self.eventos[-1]==row:
            return 'Esa declaración ya estaba registrada.'
        self.eventos.append(row);self.ultimo_tema=ev.tema;self._guardar()
        return ('He registrado una transferencia pasada; no presupongo la posesión actual.' if ev.tiempo!='actual'
                else 'He registrado una transferencia con agente, objeto y destinatario, atribuida a tu declaración.')


def respuesta_http(texto,mem,parser=None,motor=None):
    if parser is None or not hasattr(parser,'tree'):
        return None
    instancia=getattr(motor,'_ud19',None) if motor is not None else None
    if instancia is None:
        instancia=PuenteUD19(mem,parser)
        if motor is not None:motor._ud19=instancia
    respuesta=instancia.procesar(texto)
    if respuesta is None:return None
    return {'respuesta':respuesta,'aprendido':[],'imagen':None,'fallo':False,'ms':0,
            'hechos':len(mem.facts),'delta':0,
            'ud19':{'eventos':len(instancia.eventos),'fuente':'declaracion_usuario'}}
