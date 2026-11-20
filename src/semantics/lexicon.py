"""Resolución de sentidos y proximidad semántica mediante ConceptSpace del LCM.
Los vectores usan rasgos declarados (NO embeddings de texto preentrenados).
No se asignan similitudes fingidas a palabras fuera del vocabulario.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path
from threading import RLock


def normalizar(txt):
    x = unicodedata.normalize('NFD', str(txt).lower().replace('_',' '))
    x = ''.join(ch for ch in x if not unicodedata.combining(ch))
    return re.sub(r'\s+', ' ', x).strip()


def tokens(texto):
    return re.findall(r'[a-zñü0-9]+',normalizar(texto))


def formas_regulares(lema):
    """Formas frecuentes para recuperar lemas; no infiere su significado."""
    if not lema.endswith(('ar','er','ir')): return []
    raiz, term = lema[:-2], lema[-2:]
    imp = {'ar':'a','er':'e','ir':'e'}[term]
    conj = {'ar':('o','as','a','amos','ais','an','e','es','en','ado','ando'),
            'er':('o','es','e','emos','eis','en','a','an','ido','iendo'),
            'ir':('o','es','e','imos','is','en','a','an','ido','iendo')}[term]
    res = {lema, raiz+imp,raiz+imp+'me',raiz+imp+'lo',raiz+imp+'la'}
    res.update(raiz+suf for suf in conj)
    return sorted(res)


class Semantica:
    def __init__(self, base=None, aprendizaje=None):
        self.lock=RLock()
        raiz=Path.cwd()
        self.base=Path(base or raiz/'data/semantica/conceptos_es.json')
        self.aprendizaje=Path(aprendizaje or raiz/'memory/semantica_aprendida.json')
        data=json.loads(self.base.read_text(encoding='utf-8'))
        if data.get('schema')!='lcm-semantica-1.0': raise ValueError('Esquema semantico incompatible')
        self.items={c['id']:dict(c) for c in data['conceptos']}
        self.relaciones=list(data['relaciones'])
        self.nuevos=[]
        if self.aprendizaje.exists():
            raw=json.loads(self.aprendizaje.read_text(encoding='utf-8'))
            if raw.get('schema')!='lcm-aprendizaje-1.0': raise ValueError('Memoria semantica incompatible')
            for c in raw['conceptos']:
                if c['id'] in self.items: raise ValueError('Concepto aprendido con ID duplicado')
                self.items[c['id']]=c
                self.nuevos.append(c)
        # LCM_NUCLEO_RELACIONAL_V12_INICIO
        # Capa adicional: conserva rasgos y vectores existentes.
        self._nucleo_data=None
        ruta_nucleo=self.base.parent/'nucleo_relacional_12.json'
        if ruta_nucleo.is_file():
            extra=json.loads(ruta_nucleo.read_text(encoding='utf-8'))
            if extra.get('schema')!='lcm-nucleo-relacional-1.2':
                raise ValueError('Versión de núcleo relacional incompatible')
            self._nucleo_data=extra
            for c in extra['nuevos']:
                if c['id'] in self.items:
                    raise ValueError('Identidad de núcleo ya existente: '+c['id'])
                self.items[c['id']]=dict(c)
            for ident,definicion in extra['definiciones'].items():
                if ident not in self.items:
                    raise ValueError('Definición sin concepto original: '+ident)
                if self.items[ident].get('evidencia')=='agrupacion_inicial':
                    self.items[ident]['definicion']=definicion
                    self.items[ident]['evidencia']='curacion_asistida'
            self.relaciones.extend(extra['relaciones'])
        self.indice={}
        self.space=None
        self._reindex()
        from .nucleo_relacional import NucleoRelacional
        self.nucleo=NucleoRelacional(self,self._nucleo_data) if self._nucleo_data else None
        # LCM_NUCLEO_RELACIONAL_V12_FIN

    def _reindex(self):
        self.indice.clear()
        for c in self.items.values():
            formas = [c['lema']] + c.get('alias',[]) + c.get('formas',[])
            if c['tipo']=='accion': formas += formas_regulares(c['lema'])
            for forma in set(map(normalizar,formas)):
                if forma:
                    self.indice.setdefault(forma,[]).append(c['id'])

    def buscar(self, palabra, tipo=None):
        ids=self.indice.get(normalizar(palabra),[])
        cs=[self.items[i] for i in ids]
        if tipo:
            return [c for c in cs if c['tipo']==tipo]
        # Cuando hay un sentido específico revisado, la entrada genérica de
        # agrupación no añade información y no debe provocar falsa polisemia.
        revisados=[c for c in cs if c.get('evidencia') in ('curado','desambiguado','usuario_confirmado')]
        if revisados:
            cs=[c for c in cs if c.get('evidencia')!='agrupacion_inicial']
        return cs

    def _space(self):
        if self.space is None:
            # Un mismo algoritmo de representacion que la ontologia existente.
            from src.ontology.concept_space import ConceptSpace
            espacio=ConceptSpace(128)
            for c in self.items.values():
                espacio.register_concept(c['id'],es_text=c['lema'],features=c['rasgos'],kind=c['tipo'])
            espacio.build_space(seed=42)
            self.space=espacio
        return self.space

    def similares(self, concepto, tipo=None, limite=6, omitir=None):
        """Similitud coseno. NO es una probabilidad calibrada."""
        import torch
        with self.lock:
            s=self._space()
            if concepto.upper() not in s.concept_to_id: return []
            v=s.get_vector(concepto)
            sims=s.embeddings@v
            resultados=[]
            omitir=set(omitir or ())
            for j in torch.argsort(sims, descending=True).tolist():
                id_=s.id_to_concept[j].lower()
                if id_==concepto or id_ in omitir: continue
                c=self.items[id_]
                if tipo and c['tipo']!=tipo: continue
                resultados.append({'id':id_,'lema':c['lema'],'similitud':round(float(sims[j]),4)})
                if len(resultados)>=limite: break
            return resultados

    def relacionar_accion(self, accion):
        """Resolver capacidad comparando el vector de la acción con prototipos conceptuales.
        No hay una tabla de verbos -> función. Las decisiones poco separadas se abstienen.
        """
        with self.lock:
            s=self._space()
            import torch
            if accion not in self.items or accion.upper() not in s.concept_to_id: return None
            v=s.get_vector(accion)
            raices={'crear':'accion.crear','mostrar':'accion.mostrar'}
            scores={nombre:float(torch.dot(v,s.get_vector(raiz))) for nombre,raiz in raices.items()}
            elegido=sorted(scores,key=scores.get,reverse=True)
            if scores[elegido[0]] < .38 or scores[elegido[0]]-scores[elegido[1]] < .06:
                return {'accion':accion,'operacion':None,'similitudes':scores}
            return {'accion':accion,'operacion':elegido[0],'similitudes':scores}

    def contexto_acciones(self, limite=4):
        """Candidatos de acciones VISUALES por contexto, no supuesta similitud de palabra desconocida."""
        # Son prototipos de acción que ya existen como conceptos.
        posibilidades=['accion.dibujar','accion.crear','accion.mostrar','accion.pintar','accion.disenar']
        return [self.items[i]['lema'] for i in posibilidades if i in self.items][:limite]

    def aprender_verbo(self, forma_usuario, lema, padre, mem=None):
        """Añade un sentido nuevo relacionado con uno conocido, preservando su identidad.
        Se requiere una enseñanza/confirmación explícita; no se crean relaciones por azar.
        """
        forma=normalizar(forma_usuario)
        lemma=normalizar(lema)
        with self.lock:
            if not re.fullmatch(r'[a-zñü]{3,40}',lemma): raise ValueError('Lema no valido')
            if padre not in self.items or self.items[padre]['tipo']!='accion': raise ValueError('Acción padre no válida')
            id_='accion.aprendido_'+re.sub(r'[^a-z0-9]+','_',lemma)
            if id_ in self.items:
                return self.items[id_]
            if self.buscar(lemma,'accion'):
                raise ValueError('El concepto ya tiene significado registrado; requiere desambiguación')
            ref=self.items[padre]
            features=dict(ref['rasgos'])
            features[f'identidad:{id_}']=0.55
            features[f'vinculo_aprendido:{padre}']=0.32
            c={'id':id_,'lema':lemma,'tipo':'accion','familia':ref['familia'],
               'subfamilia':ref['subfamilia'],'definicion':f'Acción relacionada con {ref["lema"]}, según explicación del usuario.',
               'alias':[],'formas':[forma] if forma!=lemma else [],'padres':[padre],
               'rasgos':features,'operacion':None,'evidencia':'usuario_confirmado'}
            nuevo=self.nuevos+[c]
            self.aprendizaje.parent.mkdir(parents=True,exist_ok=True)
            data={'schema':'lcm-aprendizaje-1.0','conceptos':nuevo}
            tmp=self.aprendizaje.with_name(self.aprendizaje.name+'.tmp')
            tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            os.replace(tmp,self.aprendizaje)
            self.items[id_]=c
            self.nuevos=nuevo
            self._reindex()
            if self.space is not None: self.space.add_concept(id_,es_text=lemma,features=features,kind='accion')
            if mem is not None:
                # La memoria conversacional tambien conoce el concepto, sin degradar sinonimos previos.
                mem.add_concept(id_.upper(),features=features,kind='accion')
                mem.add_fact((id_,'RELACIONADO_CON',padre),source='usuario:semantica')
                mem.save()
            return c

    def informe(self):
        tipos={}
        familias={}
        for c in self.items.values():
            tipos[c['tipo']]=tipos.get(c['tipo'],0)+1
            familias[c['familia']]=familias.get(c['familia'],0)+1
        ambiguos={w:ids for w,ids in self.indice.items() if len(ids)>1 and ' ' not in w}
        return {'conceptos':len(self.items),'aprendidos':len(self.nuevos),'formas':len(self.indice),
                'formas_ambiguas':len(ambiguos),'tipos':tipos,'familias':familias,
                'definiciones_explicitadas':sum(bool(c['definicion']) and c.get('evidencia') not in ('agrupacion_inicial','rol_gramatical') for c in self.items.values())}
