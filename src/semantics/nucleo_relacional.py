"""Núcleo conceptual tipado y trazable de LCM 1.2.

No infiere hechos desde coseno. Solo ES_UN es transitiva; OPUESTO_DE y
RELACIONADO_CON son simétricas solo a un salto. Las capacidades, partes y
relaciones sensoriales NO se heredan automáticamente.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import re
import unicodedata
from pathlib import Path
import json

PREDICADOS = frozenset({
    'ES_UN','PARTE_TIPICA_DE','PRODUCE','PUEDE_REALIZAR','SE_PERCIBE_POR',
    'SE_REALIZA_CON','PUEDE_PRODUCIR','PUEDE_PRESENTAR','CONTIENE_TIPO_DE_SENAL',
    'ALGUNOS_PUEDEN_REALIZAR','RELACIONADO_CON','OPUESTO_DE',
})
SIMETRICAS = frozenset({'OPUESTO_DE','RELACIONADO_CON'})


def _nrm(x):
    x = unicodedata.normalize('NFKD', str(x).lower())
    x = ''.join(c for c in x if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9ñ]+',x))


class NucleoRelacional:
    def __init__(self, lex, datos):
        self.lex = lex
        if datos.get('schema') != 'lcm-nucleo-relacional-1.2':
            raise ValueError('Versión de grafo incompatible')
        self.datos = datos
        self.por_sujeto = defaultdict(list)
        self.por_objeto = defaultdict(list)
        self.por_par = defaultdict(list)
        self.ancestros_directos = defaultdict(list)
        claves = set()
        for r in datos['relaciones']:
            s,p,o = r['s'],r['p'],r['o']
            if s not in lex.items or o not in lex.items:
                raise ValueError('Relación con identidad desconocida: '+str((s,p,o)))
            if p not in PREDICADOS: raise ValueError('Predicado no autorizado: '+p)
            if s==o or (s,p,o) in claves: raise ValueError('Autorreferencia o duplicado')
            claves.add((s,p,o))
            if r.get('evidencia') != 'curacion_asistida':
                raise ValueError('Falta procedencia de curación')
            self.por_sujeto[s].append(r)
            self.por_objeto[o].append(r)
            self.por_par[(s,o)].append(r)
            if p=='ES_UN': self.ancestros_directos[s].append(o)
        # Es una taxonomía: prohibir ciclos desde el arranque.
        estado = {}
        def recorrer(n):
            if estado.get(n)==1:raise ValueError('Ciclo ES_UN: '+n)
            if estado.get(n)==2:return
            estado[n]=1
            for o in self.ancestros_directos.get(n,()): recorrer(o)
            estado[n]=2
        for n in self.ancestros_directos: recorrer(n)

    def resolver(self, expresion, tipo=None):
        """Identidad exacta o lema inequívoco. Devuelve None ante polisemia."""
        ident_directo=str(expresion).lower()
        if ident_directo in self.lex.items:
            c=self.lex.items[ident_directo]
            return ident_directo if tipo is None or c['tipo']==tipo else None
        # No asignar un vector a una forma desconocida.
        cs = self.lex.buscar(_nrm(expresion),tipo=tipo)
        ids = {x['id'] for x in cs}
        return next(iter(ids)) if len(ids)==1 else None

    def ambiguedad(self, palabra):
        return [x['id'] for x in self.lex.buscar(palabra)]

    def glosa(self, palabra):
        ident=self.resolver(palabra)
        if not ident:return None
        x=self.lex.items[ident]
        return {'id':ident,'lema':x['lema'],'definicion':x.get('definicion',''),
                'evidencia':x.get('evidencia'), 'padres':[r['o'] for r in self.por_sujeto[ident] if r['p']=='ES_UN']}

    def ancestros(self, ident, profundidad=8):
        ident=self.resolver(ident)
        if not ident:return []
        cola=deque([(ident,0)]); visitados={ident}; salida=[]
        while cola:
            n,d=cola.popleft()
            if d>=profundidad:continue
            for p in self.ancestros_directos.get(n,()):
                if p in visitados:continue
                visitados.add(p);salida.append((p,d+1));cola.append((p,d+1))
        return salida

    def probar(self, origen, destino, predicado=None, profundidad=12):
        """Devolver prueba tipada; nunca un no categórico a partir de falta de datos.

        Sin predicado, prioriza relaciones directas y después cadena ES_UN.
        """
        s=self.resolver(origen);o=self.resolver(destino)
        if s is None or o is None:
            return {'estado':'no_resuelto','motivo':'concepto desconocido o ambiguo',
                    'origen':origen,'destino':destino,'ruta':[]}
        if predicado is not None and predicado not in PREDICADOS:
            raise ValueError('Predicado no admitido')
        directas=self.por_par.get((s,o),())
        for r in directas:
            if predicado is None or r['p']==predicado:
                return {'estado':'demostrado','origen':s,'destino':o,
                        'predicado':r['p'],'ruta':[dict(r)],'derivacion':'directa'}
        for r in self.por_par.get((o,s),()):
            if r['p'] in SIMETRICAS and (predicado is None or r['p']==predicado):
                return {'estado':'demostrado','origen':s,'destino':o,
                        'predicado':r['p'],'ruta':[dict(r)],'derivacion':'simetria'}
        if predicado in (None,'ES_UN') and s != o:
            cola=deque([(s,[])]); vistos={s}
            while cola:
                n,camino=cola.popleft()
                if len(camino)>=profundidad:continue
                for r in self.por_sujeto.get(n,()):
                    if r['p']!='ES_UN':continue
                    nuevo=camino+[dict(r)]
                    if r['o']==o:
                        return {'estado':'demostrado','origen':s,'destino':o,
                                'predicado':'ES_UN','ruta':nuevo,
                                'derivacion':'transitividad' if len(nuevo)>1 else 'directa'}
                    if r['o'] not in vistos:
                        vistos.add(r['o']); cola.append((r['o'],nuevo))
        return {'estado':'no_consta','origen':s,'destino':o,
                'predicado':predicado,'ruta':[],'motivo':'no hay prueba autorizada en este núcleo'}

    def vinculaciones(self, concepto, maximo=100):
        ident=self.resolver(concepto)
        if ident is None:return []
        return ([dict(x) for x in self.por_sujeto.get(ident,())]
                +[dict(x) for x in self.por_objeto.get(ident,())])[:maximo]

    def similitudes_estructurales(self, concepto, limite=8):
        """Vecinos en el espacio 128D *proyectado* con señales taxonómicas.

        No modifica el espacio original ni su catálogo. Los cosenos no son
        probabilidades y no autorizan nuevas relaciones como hechos.
        """
        import torch
        import torch.nn.functional as F
        ident=self.resolver(concepto)
        if ident is None:return []
        sp=self.lex._space()
        # Características semánticas explicitas por antepasado; vector hash de
        # rasgo de ConceptSpace estable con semilla y dimensión originales.
        def v_node(n):
            v=sp.get_vector(n)
            anc=self.ancestros(n)
            if not anc:return v
            vgrafo=torch.zeros_like(v)
            for padre,prof in anc:
                vgrafo += sp._feature_vector('jerarquia:'+padre) / prof
            vgrafo=F.normalize(vgrafo,p=2,dim=-1)
            return F.normalize(.75*v + .25*vgrafo,p=2,dim=-1)
        q=v_node(ident)
        candidatos=[]
        for c in self.lex.items.values():
            n=c['id']
            if n==ident or c['tipo'] != self.lex.items[ident]['tipo']: continue
            sim=float(torch.dot(q,v_node(n)))
            candidatos.append((sim,n,c['lema']))
        candidatos.sort(key=lambda x:(-x[0],x[1]))
        return [{'id':n,'lema':lemma,'coseno_contextual':round(sim,4)}
                for sim,n,lemma in candidatos[:max(0,limite)]]

    def inventario(self):
        return {'conceptos_nuevos':len(self.datos['nuevos']),
                'definiciones_revisadas':len(self.datos['definiciones']),
                'relaciones':len(self.datos['relaciones']),
                'tipos':{p:sum(r['p']==p for r in self.datos['relaciones']) for p in sorted(PREDICADOS)},
                'representacion':'grafo tipado + vectores base sin alterar'}
