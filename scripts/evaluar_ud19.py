"""Auditoria de LCM1.8 vs puente UD19 con arboles oraculo y perturbaciones.

NO ejecuta School.pt; --real exige explicitamente checkpoint en el proyecto.
Todas las identidades, verbos y preguntas se generan independientemente del
modulo evaluado. Los informes contienen respuestas, aciertos, hashes y semilla.
"""
import argparse
import hashlib
import json
import random
import tempfile
from pathlib import Path
from src.memory.store import MemoryStore
from src.semantics.narrativa18 import Narrativa18
from src.semantics.ud19 import PuenteUD19

NAMES=['Ana','Luis','Elena','Jorge','Nora','Carlos','Irene','Diego','Marta','Raúl','Clara','Pablo',
       'Lucía','Bruno','Eva','Mario','Julia','Óscar','Carmen','Pedro','Sofía','Andrés','Silvia','Tomás']
OBJECTS=[('el','libro'),('la','carta'),('el','mapa'),('la','llave'),('el','cuaderno'),('la','taza'),
         ('el','reloj'),('la','postal'),('el','anillo'),('la','carpeta'),('el','bolso'),('la','radio')]
ACTS=[('entregó','entregar'),('prestó','prestar'),('dio','dar'),('devolvió','devolver')]

class EscuelaOraculo:
    def __init__(self, mapping, perturbar=None):
        self.mapping=mapping
        self.perturbar=perturbar
    def tree(self, s):
        rows=list(self.mapping[s]);modo=self.perturbar
        if modo=='omitir_sujeto':return [((f,u,h,'dep' if rel=='nsubj' else rel,lem)) for f,u,h,rel,lem in rows]
        if modo=='omitir_destinatario':return [((f,u,h,'dep' if rel=='obl' else rel,lem)) for f,u,h,rel,lem in rows]
        if modo=='lema_erroneo':return [((f,u,h,rel,'misterio' if rel=='root' else lem)) for f,u,h,rel,lem in rows]
        if modo=='ciclo':
            v=next(i for i,r in enumerate(rows) if r[3]=='root')
            f,u,h,rel,lem=rows[v];rows[v]=(f,u,1,'root',lem)
        if modo=='entidad_inventada':
            f,u,h,rel,lem=rows[0];rows[0]=('Marciano',u,h,rel,lem)
        return rows


def _tree_act(s,v,lema,det,o,r):
    return [(s,'PROPN',2,'nsubj',s.lower()),(v,'VERB',0,'root',lema),
            (det,'DET',4,'det',det),(o,'NOUN',2,'obj',o),
            ('a','ADP',6,'case','a'),(r,'PROPN',2,'obl',r.lower()),
            ('.','PUNCT',2,'punct','.')]


def _tree_dat(s,v,lema,det,o,r):
    return [(s,'PROPN',3,'nsubj',s.lower()),('le','PRON',3,'iobj','le'),(v,'VERB',0,'root',lema),
            ('a','ADP',5,'case','a'),(r,'PROPN',3,'obl',r.lower()),
            (det,'DET',7,'det',det),(o,'NOUN',3,'obj',o),('.', 'PUNCT',3,'punct','.')]


def _tree_pas(s,v,lema,det,o,r):
    # El tema fue participio a destinatario por agente
    p={'entregar':'entregado','prestar':'prestado','dar':'dado','devolver':'devuelto'}[lema]
    if det=='la' and p.endswith('o'):p=p[:-1]+'a'
    return [(det.title(),'DET',2,'det',det),(o,'NOUN',4,'nsubj',o),
            ('fue','AUX',4,'aux','ser'),(p,'VERB',0,'root',lema),('a','ADP',6,'case','a'),
            (r,'PROPN',4,'obl',r.lower()),('por','ADP',8,'case','por'),
            (s,'PROPN',4,'obl',s.lower()),('.', 'PUNCT',4,'punct','.')]


def _tree_rec(s,det,o,r):
    return [(r,'PROPN',2,'nsubj',r.lower()),('recibió','VERB',0,'root','recibir'),
            (det,'DET',4,'det',det),(o,'NOUN',2,'obj',o),('de','ADP',6,'case','de'),
            (s,'PROPN',2,'obl',s.lower()),('.', 'PUNCT',2,'punct','.')]


def _tree_des(s,v,lema,det,o,r):
    return [('A','ADP',2,'case','a'),(r,'PROPN',6,'obl',r.lower()),
            (',','PUNCT',6,'punct',','),(s,'PROPN',6,'nsubj',s.lower()),
            ('le','PRON',6,'iobj','le'),(v,'VERB',0,'root',lema),
            (det,'DET',8,'det',det),(o,'NOUN',6,'obj',o),('.', 'PUNCT',6,'punct','.')]


def make_case(rng, index, kinds=None):
    kinds=kinds or ('activo','dativo','pasivo','recepcion','desplazado','hipotesis','negacion','error_arbol')
    kind=kinds[index % len(kinds)]
    s,r=rng.sample(NAMES,2);det,o=rng.choice(OBJECTS);v,lemma=rng.choice(ACTS)
    if kind=='activo': utter=f'{s} {v} {det} {o} a {r}.';tree=_tree_act(s,v,lemma,det,o,r)
    elif kind=='dativo':utter=f'{s} le {v} a {r} {det} {o}.';tree=_tree_dat(s,v,lemma,det,o,r)
    elif kind=='pasivo':
        p={'entregar':'entregado','prestar':'prestado','dar':'dado','devolver':'devuelto'}[lemma]
        if det=='la' and p.endswith('o'):p=p[:-1]+'a'
        utter=f'{det.title()} {o} fue {p} a {r} por {s}.';tree=_tree_pas(s,v,lemma,det,o,r)
    elif kind=='recepcion':utter=f'{r} recibió {det} {o} de {s}.';tree=_tree_rec(s,det,o,r)
    elif kind=='desplazado':utter=f'A {r}, {s} le {v} {det} {o}.';tree=_tree_des(s,v,lemma,det,o,r)
    elif kind=='hipotesis':utter=f'Si {s} {v} {det} {o} a {r}.';tree=_tree_act(s,v,lemma,det,o,r)
    elif kind=='negacion':
        utter=f'{s} no {v} {det} {o} a {r}.'
        base=_tree_act(s,v,lemma,det,o,r)
        tree=[]
        for f,u,h,rel,lem in base:
            if h and h>=2:h+=1
            if rel=='root':h=0
            tree.append((f,u,h,rel,lem))
        tree.insert(1,('no','ADV',3,'advmod','no'))
        tree[0]=(s,'PROPN',3,'nsubj',s.lower())
        tree[2]=(v,'VERB',0,'root',lemma)
    elif kind=='error_arbol':utter=f'{s} {v} {det} {o} a {r}.';tree=_tree_act(s,v,lemma,det,o,r)
    else:raise AssertionError(kind)
    return {'id':index,'tipo':kind,'enunciado':utter,'arbol':tree,
            'pregunta':f'¿Quién tiene {det} {o}?','esperado':r if kind in
            ('activo','dativo','pasivo','recepcion','desplazado') else None,
            'perturbacion':'omitir_destinatario' if kind=='error_arbol' else None}


def cases(seed,n):
    rng=random.Random(seed)
    return [make_case(rng,i) for i in range(n)]


def evaluacion(lista,save_rows=True,modo_real=False):
    resultados=[]
    with tempfile.TemporaryDirectory() as tmp:
        for idx,c in enumerate(lista):
            p=Path(tmp)
            su=c['enunciado'];q=c['pregunta']
            with tempfile.TemporaryDirectory(dir=tmp) as d:
                d=Path(d)
                mem=MemoryStore(str(d/'m.json'))
                base=Narrativa18(mem,ruta=d/'base.json')
                try:base.procesar(su);rb=base.procesar(q)
                except Exception as e:rb='ERROR:'+repr(e)
                school=EscuelaOraculo({su:c['arbol']},c.get('perturbacion'))
                new=PuenteUD19(mem,school,ruta=d/'new.json')
                try:
                    rn_ing=new.procesar(su)
                    rn=new.procesar(q)
                except Exception as e:rn='ERROR:'+repr(e);rn_ing='ERROR'
                exp=c['esperado']
                if exp:
                    okb=bool(rb and str(rb).casefold().startswith(exp.casefold()))
                    okn=bool(rn and str(rn).casefold().startswith(exp.casefold()))
                else:
                    # La seguridad exige que el nuevo modulo no memorice un hecho
                    # expresado hipoteticamente, negado o con parser defectuoso.
                    okb=not base.registros
                    okn=not new.eventos
                resultados.append({'id':c['id'],'tipo':c['tipo'],'esperado':exp,
                    'acierto_18':okb,'acierto_19':okn,'respuesta_18':rb,'respuesta_19':rn,
                    'ingesta_19':rn_ing})
    by={}
    for r in resultados:
        d=by.setdefault(r['tipo'],{'n':0,'ok18':0,'ok19':0});d['n']+=1;d['ok18']+=r['acierto_18'];d['ok19']+=r['acierto_19']
    comparables=[r for r in resultados if r['tipo']!='error_arbol']
    return {'n':len(resultados),
            'comparacion_valida':{'n':len(comparables),
                    'base_18':sum(r['acierto_18'] for r in comparables),
                    'ud19':sum(r['acierto_19'] for r in comparables)},
            'nota_comparacion':'No incluir error_arbol en la comparacion: 1.8 no consume ese arbol y puede inferir desde texto.',
            'base_18':sum(r['acierto_18'] for r in resultados),
            'ud19':sum(r['acierto_19'] for r in resultados),'por_familia':by,
            'tandas':[{'inicio':i+1,'n':len(resultados[i:i+10]),
                     'base18':sum(r['acierto_18'] for r in resultados[i:i+10]),
                     'ud19':sum(r['acierto_19'] for r in resultados[i:i+10])}
                      for i in range(0,len(resultados),10)],'casos':resultados}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,default=800)
    ap.add_argument('--semilla',type=int,default=1907)
    ap.add_argument('--guardar',default='reports/ud19_auditoria.json')
    a=ap.parse_args();data=cases(a.semilla,a.n)
    huella=hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    result=evaluacion(data)
    result.update({'schema':'auditoria-ud19-1','banco_sha256':huella,'semilla':a.semilla,
          'protocolo':'árboles UD oráculo simulados; no School.pt, sin evaluación de español libre'})
    path=Path(a.guardar);path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
    print('Escuela: ARBOLES UD ORACULO, NO MODELO NEURONAL')
    cv=result['comparacion_valida']
    print('Comparables: LCM18',cv['base_18'],'/',cv['n'],' | UD19',cv['ud19'],'/',cv['n'])
    print('Seguridad con arboles invalidos:',result['por_familia']['error_arbol']['ok19'],'/',result['por_familia']['error_arbol']['n'])
    for k,v in result['por_familia'].items():print(k,':',v)
    print('Tandas >=9/10:',sum(t['ud19']>=9 for t in result['tandas']),'/',len(result['tandas']))
    print('Informe:',path)

if __name__=='__main__':main()
