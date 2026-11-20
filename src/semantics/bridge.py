"""Puente hacia Motor.chat: decide por significado vectorial y pregunta ante desconocidos.
La gramática composicional se implementa en composition.py.
Límites de alcance: operaciones VISUALES con muestras cromáticas; el resto sigue
por el sistema conversacional existente. No es un enrutador de intención global.
"""
from __future__ import annotations

import re
from .lexicon import Semantica, normalizar, tokens

COLORES=('rojo','verde','azul','amarillo','blanco','negro')
# Flexión de adjetivos de color: es normalización morfológica, NO interpretación de intenciones.
FORMAS_COLOR={}
for nombre in COLORES:
    FORMAS_COLOR[nombre]=nombre
    FORMAS_COLOR[nombre+'s' if nombre.endswith('e') else nombre+'es' if nombre=='azul' else nombre+'s']=nombre
    if nombre.endswith('o'):
        raiz=nombre[:-1]
        for terminacion in ('a','as','os'):
            FORMAS_COLOR[raiz+terminacion]=nombre
PREFIJOS={'por','favor','me','puedes','podrias','podrías','quiero','quisiera','deseo','necesito','que','un','una','hazme'}
NEGACIONES={'no','nunca','tampoco','sin'}


def color_en(texto):
    ts=tokens(texto)
    colores=sorted({FORMAS_COLOR[w] for w in ts if w in FORMAS_COLOR})
    return colores


def _consulta_definicion(t):
    t=normalizar(t).strip('¿? ')
    for ini in ('que es ','que significa ','define ','explicame que es ','dime que es '):
        if t.startswith(ini):
            resto=t[len(ini):].strip(' .?')
            resto=re.sub(r'^(el|la|los|las|un|una)\s+','',resto)
            if resto.startswith('color '): resto=resto[6:]
            return resto.strip()
    return None


def _forma_sugerida_a_lema(palabra):
    p=normalizar(palabra)
    if p.endswith('ame') and len(p)>6: p=p[:-2]
    if p.endswith('a') and len(p)>4: return p[:-1]+'ar'
    if p.endswith('e') and len(p)>4: return p[:-1]+'er'
    return p


class PuenteSemantico:
    def __init__(self, base=None, aprendizaje=None):
        self.lex=Semantica(base,aprendizaje)
        self.pendiente=None

    def _accion(self, texto):
        """Extrae una acción candidata desde la estructura de la solicitud.
        No asigna el verbo a un comando; el valor semántico viene del espacio.
        """
        tt=tokens(texto)
        if not tt or 'no' in tt[:3] or 'nunca' in tt[:3]: return None,None
        # «Me pregunto ...», «me imagino ...»: enunciado en primera persona,
        # no petición de ejecutar el verbo.
        if len(tt)>1 and tt[0]=='me' and tt[1].endswith('o') and self.lex.buscar(tt[1],'accion'):
            return None,None
        posibles=[]
        # Orden explícita (inicio de frase), o predicado tras modal/solicitud.
        for i,x in enumerate(tt[:9]):
            if i>0 and tt[i-1] not in {'que','me','te','nos','lo','la','por','favor','puedes','podrias','quiero','quisiera','deseo','necesito','quieres'}:
                continue
            if x in PREFIJOS and i<3: continue
            acciones=self.lex.buscar(x,tipo='accion')
            if acciones:
                for a in acciones:
                    # Los sentidos de mostrar y enseñar prevalecen en contexto visual,
                    # mientras que los de enseñar-instruir se reservan fuera de él.
                    bonus=.25 if (a.get('operacion') and color_en(texto)) else 0.
                    posibles.append((i, bonus, a))
        if posibles:
            pos, _, elegido=sorted(posibles,key=lambda r:(r[0],-r[1],r[2]['id']))[0]
            return elegido, None
        # Si se pide una imagen y el primer verbo no se conoce, pedir aclaración.
        # Un desconocido NO recibe embedding ficticio: los candidatos salen del contexto.
        if not color_en(texto) or not any(w in tt for w in ('imagen','color','cuadro','muestra','dibujo')):
            return None,None
        if tt[0] in ('que','cual','como','cuando','donde','por','el','la','un','una','azul','rojo','verde','amarillo','blanco','negro'):
            return None,None
        ix=0
        while ix<len(tt) and tt[ix] in ('por','favor','me','puedes','podrias','quiero','quisiera','que','una','un'):
            ix+=1
        if ix>=len(tt): return None,None
        candidata=tt[ix]
        # No convertir declaraciones con sujeto en preguntas sobre verbos desconocidos.
        if any(self.lex.buscar(w,'accion') for w in tt[ix+1:ix+3]):
            return None,None
        if candidata not in ('color','imagen','cuadro') and not self.lex.buscar(candidata):
            return None,candidata
        return None,None

    def _definir(self, texto):
        q=_consulta_definicion(texto)
        if q is None: return None
        cs=self.lex.buscar(q)
        if not cs: return None
        if len(cs)>1:
            opciones=[]
            for c in cs[:4]:
                if c['definicion'] and c.get('evidencia')!='agrupacion_inicial':
                    opciones.append(c['definicion'])
                else:
                    opciones.append(f'contexto {c["familia"]}/{c["subfamilia"]}')
            return {'respuesta':f'«{q}» tiene varios sentidos posibles: '+ '; '.join(opciones) +'. ¿A cuál te refieres?',
                    'aprendido':[],'fallo':False,'imagen':None}
        c=cs[0]
        if not c['definicion'] or c['evidencia']=='agrupacion_inicial':
            # No afirmar un pseudo-significado generado desde una etiqueta vaga.
            return None
        return {'respuesta':f'{c["lema"].capitalize()}: {c["definicion"]}',
                'aprendido':[],'fallo':False,'imagen':None}

    def _respuesta_ensenanza(self, texto, mem=None):
        if not self.pendiente: return None
        tt=tokens(texto)
        if not tt: return None
        if tt[0] in ('no','cancela','cancelar','olvida') and len(tt)<=5:
            self.pendiente=None
            return {'respuesta':'Entendido, no he incorporado ninguna asociación nueva.', 'aprendido':[], 'imagen':None,'fallo':False}
        candidatos=[]
        auxiliares={'ser','estar','significar','querer','poder','decir','relacionar','explicar','entender'}
        for w in tt:
            for c in self.lex.buscar(w,'accion'):
                if c['lema'] in auxiliares: continue
                if c['id'] not in (v['id'] for v in candidatos): candidatos.append(c)
        # La enseñanza debe contener un concepto/acción de referencia inequívoco.
        if not candidatos: return None
        if len(candidatos)>1:
            if len(set(c['id'] for c in candidatos))>1:
                return {'respuesta':'¿Con qué acción lo relacionas principalmente: '+', '.join(c['lema'] for c in candidatos[:4])+'?',
                        'aprendido':[],'imagen':None,'fallo':False}
        target=candidatos[0]
        forma=self.pendiente['forma']
        nuevo=self.lex.aprender_verbo(forma,_forma_sugerida_a_lema(forma),target['id'],mem=mem)
        self.pendiente=None
        return {'respuesta':f'He incorporado «{nuevo["lema"]}» como acción relacionada con «{target["lema"]}», conservando ambos conceptos separados. Puedes corregirme si la relación es demasiado amplia.',
                'aprendido':[{'concepto':nuevo['id'],'relacionado_con':target['id']}], 'imagen':None,'fallo':False}

    def responder(self, texto, mem=None):
        """Componer la frase antes de decidir si hay alguna capacidad ejecutable."""
        if not texto.strip(): return None
        if self.pendiente:
            x=self._respuesta_ensenanza(texto,mem)
            if x: return x
            self.pendiente=None
        # LCM_NUCLEO_RELACIONAL_V12_CONVERSAR
        # Solo se responde si existe prueba conceptual explícita.
        from .relational_dialogue import respuesta_relacional
        evidencia_relacional=respuesta_relacional(texto,self.lex)
        if evidencia_relacional is not None:
            return evidencia_relacional
        from .composition import analizar
        colores=color_en(texto)
        marco=analizar(texto, self.lex, colores)
        if marco.clase=='definicion':
            salida=self._definir(texto)
            if salida is None:
                # "Me enseñas qué es el color azul" no comienza por "qué es".
                t=normalizar(texto)
                import re
                m=re.search(r'\bque (?:es|significa) (?:el |la |un |una )?(?:color )?(rojo|verde|azul|amarillo|blanco|negro)\b',t)
                if m: salida=self._definir('¿Qué es el color '+m.group(1)+'?')
            if salida is not None:
                salida['composicion']=marco.dict()
                return salida
            # Una pregunta que no sabemos definir debe quedar a cargo del
            # conversador general, NUNCA convertirse en generación de imagen.
            return None
        # El motor conversacional conserva la responsabilidad de todas las
        # declaraciones, narraciones y solicitudes no soportadas.
        if marco.clase in ('declaracion','negacion','no_soportada') or (marco.clase=='ambigua' and marco.razon=='no se ha resuelto un predicado de acción'):
            # Preguntar por un verbo desconocido solo si hay un contexto visual
            # inequívoco y no hubo ningún predicado reconocido o negado.
            if colores and marco.razon=='no se ha resuelto un predicado de acción':
                _, desconocida=self._accion(texto)
                if desconocida:
                    sugerencias=', '.join(self.lex.contexto_acciones())
                    self.pendiente={'forma':desconocida,'frase':texto}
                    return {'respuesta':f'No conozco aún el significado de «{desconocida}» en esta petición. Por el contexto visual, quizá lo relaciones con {sugerencias}. ¿Con qué acción lo vincularías? No asumiré que significan lo mismo.',
                            'aprendido':[], 'imagen':None,'fallo':False,
                            'composicion':marco.dict()}
            return None
        if marco.clase=='ambigua':
            return {'respuesta':'La solicitud visual es ambigua; necesito que precises una sola acción y un solo color.',
                    'aprendido':[], 'imagen':None, 'fallo':False,
                    'composicion':marco.dict()}
        if marco.clase!='peticion' or not marco.capacidad or not colores:
            return None
        from src.vision.sample import datos_muestra
        color=colores[0].upper()
        img=datos_muestra(color)
        crear=marco.capacidad=='crear'
        explicacion=(f'He creado una muestra del color {color.lower()}.' if crear else
                     f'Aquí tienes una muestra visual del color {color.lower()}.')
        if 'cuadro' in tokens(texto) and crear:
            explicacion+=' Es una muestra uniforme, no una pintura artística.'
        pred=next((x for x in marco.predicados if x.concepto==marco.accion and not x.negado),None)
        from src.multimodal.events import desde_marco_textual
        obs=desde_marco_textual(marco).serializar()
        return {'respuesta':explicacion,'imagen':img,'aprendido':[],'fallo':False,
                'observacion':obs,
                'semantica':{'concepto_accion':marco.accion,'capacidad':marco.capacidad,
                  'similitudes':{k:round(v,3) for k,v in (pred.similitudes if pred else {}).items()},
                  'nota':'coseno no calibrado; no es probabilidad'},
                'composicion':marco.dict()}
