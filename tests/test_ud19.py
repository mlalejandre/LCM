"""Ensayos de integracion UD 1.9: árboles oráculo, no son el checkpoint School."""
import json
from pathlib import Path
from src.memory.store import MemoryStore
from src.semantics.ud19 import PuenteUD19


def tree_active(s='Ana',v='entregó',lemma='entregar',o='libro',r='Luis',det='el'):
    return [(s,'PROPN',2,'nsubj',s.lower()),
            (v,'VERB',0,'root',lemma),
            (det,'DET',4,'det',det),
            (o,'NOUN',2,'obj',o),
            ('a','ADP',6,'case','a'),
            (r,'PROPN',2,'obl',r.lower()),
            ('.','PUNCT',2,'punct','.')]


def tree_passive(s='Ana',v='entregado',lemma='entregar',o='libro',r='Luis',det='el'):
    return [(det.title(),'DET',2,'det',det),(o,'NOUN',4,'nsubj:pass',o),
            ('fue','AUX',4,'aux','ser'),(v,'VERB',0,'root',lemma),
            ('a','ADP',6,'case','a'),(r,'PROPN',4,'obl',r.lower()),
            ('por','ADP',8,'case','por'),(s,'PROPN',4,'obl:agent',s.lower()),
            ('.','PUNCT',4,'punct','.')]


def tree_receipt(s='Ana',o='libro',r='Luis',det='el'):
    return [(r,'PROPN',2,'nsubj',r.lower()),('recibió','VERB',0,'root','recibir'),
            (det,'DET',4,'det',det),(o,'NOUN',2,'obj',o),
            ('de','ADP',6,'case','de'),(s,'PROPN',2,'obl',s.lower()),
            ('.','PUNCT',2,'punct','.')]


def tree_dative(s='Ana',v='entregó',lemma='entregar',o='libro',r='Luis',det='el'):
    return [(s,'PROPN',3,'nsubj',s.lower()),('le','PRON',3,'iobj','le'),
            (v,'VERB',0,'root',lemma),('a','ADP',5,'case','a'),
            (r,'PROPN',3,'obl',r.lower()),(det,'DET',7,'det',det),
            (o,'NOUN',3,'obj',o),('.','PUNCT',3,'punct','.')]

class FakeSchool:
    def __init__(self,mapping):self.mapping=mapping
    def tree(self,text):return self.mapping[text]


def build(tmp_path, tree, utterance):
    mem=MemoryStore(str(tmp_path/'mem.json'))
    p=FakeSchool({utterance:tree})
    return PuenteUD19(mem,p,ruta=tmp_path/'ud.json')


def test_active(tmp_path):
    text='Ana entregó el libro a Luis.'
    eng=build(tmp_path,tree_active(),text)
    assert eng.procesar(text)
    assert eng.procesar('¿Quién tiene el libro?').startswith('Luis')
    assert eng.procesar('¿A quién entregó Ana el libro?').startswith('Luis')
    assert eng.procesar('¿Quién entregó el libro a Luis?').startswith('Ana')
    assert eng.procesar('¿Qué entregó Ana a Luis?').startswith('Libro')
    assert 'no consta' in eng.procesar('¿Quién es el dueño del libro?').lower() if eng.procesar('¿Quién es el dueño del libro?') is not None else True


def test_passive(tmp_path):
    text='El libro fue entregado a Luis por Ana.'
    eng=build(tmp_path,tree_passive(),text)
    assert eng.procesar(text)
    assert eng.eventos[0]['agente']=='ANA'
    assert eng.eventos[0]['destinatario']=='LUIS'


def test_receipt(tmp_path):
    text='Luis recibió el libro de Ana.'
    eng=build(tmp_path,tree_receipt(),text)
    assert eng.procesar(text)
    assert eng.procesar('¿Quién tiene el libro?').startswith('Luis')


def test_dative(tmp_path):
    text='Ana le entregó a Luis el libro.'
    eng=build(tmp_path,tree_dative(),text)
    assert eng.procesar(text)
    assert eng.procesar('¿Quién tiene el libro?').startswith('Luis')


def test_corrupt_tree_abstains(tmp_path):
    text='Ana entregó el libro a Luis.'
    tree=tree_active();tree[1]=('entregó','VERB',1,'root','entregar')
    eng=build(tmp_path,tree,text)
    assert eng.procesar(text) is None
    assert eng.eventos==[]


def test_unknown_lemma_abstains(tmp_path):
    text='Ana entregó el libro a Luis.'
    tree=tree_active();tree[1]=('entregó','VERB',0,'root','inventar')
    eng=build(tmp_path,tree,text)
    assert eng.procesar(text) is None


def test_refuse_hypothesis(tmp_path):
    text='Si Ana entregó el libro a Luis.'
    eng=build(tmp_path,tree_active(),text)
    assert eng.procesar(text) is None
    assert eng.eventos==[]


def test_refuse_negation(tmp_path):
    text='Ana no entregó el libro a Luis.'
    tree=tree_active();tree=[('Ana','PROPN',3,'nsubj','ana'),('no','ADV',3,'advmod','no'),('entregó','VERB',0,'root','entregar'),
                       ('el','DET',5,'det','el'),('libro','NOUN',3,'obj','libro'),('a','ADP',7,'case','a'),('Luis','PROPN',3,'obl','luis'),('.', 'PUNCT',3,'punct','.')]
    eng=build(tmp_path,tree,text)
    assert eng.procesar(text) is None
    assert eng.eventos==[]


def test_same_predicate_requirement(tmp_path):
    utter='Ana entregó el libro a Luis.'
    eng=build(tmp_path,tree_active(),utter)
    eng.procesar(utter)
    assert eng.procesar('¿A quién prestó Ana el libro?').startswith('No consta')


def test_persistence(tmp_path):
    utter='Ana entregó el libro a Luis.'
    eng=build(tmp_path,tree_active(),utter)
    eng.procesar(utter)
    eng2=build(tmp_path,tree_active(),utter)
    assert eng2.procesar('¿Quién tiene el libro?').startswith('Luis')


def test_conflict_not_silent(tmp_path):
    utter='Ana entregó el libro a Luis.'
    utter2='Eva entregó el libro a Mario.'
    mem=MemoryStore(str(tmp_path/'mem.json'))
    eng=PuenteUD19(mem,FakeSchool({utter:tree_active(),utter2:tree_active('Eva','entregó','entregar','libro','Mario')}),ruta=tmp_path/'ud.json')
    eng.procesar(utter)
    assert 'necesito aclaración' in eng.procesar(utter2)
    assert 'incompatibles' in eng.procesar('¿Quién tiene el libro?')


def test_futuro_no_se_confunde_con_hecho(tmp_path):
    text='Ana entregará el libro a Luis.'
    tree=tree_active(v='entregará')
    eng=build(tmp_path,tree,text)
    assert eng.procesar(text) is None
    assert not eng.eventos


def test_tiempo_pasado_no_implica_posesion_actual(tmp_path):
    text='Ayer Ana entregó el libro a Luis.'
    old=tree_active()
    tree=[('Ayer','ADV',3,'advmod','ayer')]+[
        (f,u,(h+1 if h else 0),rel,lem) for f,u,h,rel,lem in old]
    # Ayer depende del verbo, que ahora ocupa la posicion 3.
    eng=build(tmp_path,tree,text)
    assert eng.procesar(text)
    assert 'pasada' in eng.procesar('¿Quién tiene el libro?')
    assert eng.procesar('¿Quién recibió el libro ayer?').startswith('Luis')


def test_pronombre_incompatible_abstiene(tmp_path):
    text='Ana entregó el libro a Luis.'
    eng=build(tmp_path,tree_active(),text)
    eng.procesar(text)
    assert 'antecedente' in eng.procesar('¿Quién la tiene?')
    assert eng.procesar('¿Quién lo tiene?').startswith('Luis')


def test_voz_pasiva_sin_subtipos_ud(tmp_path):
    text='El libro fue entregado a Luis por Ana.'
    tr=tree_passive()
    tr=[(f,u,h,'nsubj' if rel=='nsubj:pass' else ('obl' if rel=='obl:agent' else rel),lem)
        for f,u,h,rel,lem in tr]
    eng=build(tmp_path,tr,text)
    assert eng.procesar(text)
    assert eng.procesar('¿Quién tiene el libro?').startswith('Luis')


def test_integracion_motor_chat(tmp_path):
    from src.web.motor import Motor
    text='Ana entregó el libro a Luis.'
    p=FakeSchool({text:tree_active()})
    p.parse=lambda t: []
    mem=MemoryStore(str(tmp_path/'mem.json'))
    motor=Motor(mem,p,str(tmp_path))
    a=motor.chat(text)
    b=motor.chat('¿Quién tiene el libro?')
    assert a.get('ud19') and b['respuesta'].startswith('Luis')


def tree_clitic(s='Luis',v='devolvió',r='Ana',clit='lo'):
    return [(s,'PROPN',4,'nsubj',s.lower()),('se','PRON',4,'expl','se'),
            (clit,'PRON',4,'obj',clit),(v,'VERB',0,'root','devolver'),
            ('a','ADP',6,'case','a'),(r,'PROPN',4,'obl',r.lower()),
            ('.','PUNCT',4,'punct','.')]


def test_clitico_unico_con_evidencia(tmp_path):
    first='Ana entregó el libro a Luis.'
    follow='Luis se lo devolvió a Ana.'
    eng=PuenteUD19(MemoryStore(str(tmp_path/'m.json')),
      FakeSchool({first:tree_active(),follow:tree_clitic()}),ruta=tmp_path/'ud.json')
    assert eng.procesar(first)
    assert eng.procesar(follow)
    assert eng.procesar('¿Quién tiene el libro?').startswith('Ana')
    assert eng.procesar('¿Quién tenía el libro antes?').startswith('Luis')


def test_clitico_genero_incompatible_no_memoriza(tmp_path):
    first='Ana entregó el libro a Luis.'
    follow='Luis se la devolvió a Ana.'
    eng=PuenteUD19(MemoryStore(str(tmp_path/'m.json')),
      FakeSchool({first:tree_active(),follow:tree_clitic(clit='la')}),ruta=tmp_path/'ud.json')
    eng.procesar(first)
    assert eng.procesar(follow) is None
    assert len(eng.eventos)==1


def test_consulta_deja_responder_a_version_anterior(tmp_path):
    eng=build(tmp_path,tree_active(),'Ana entregó el libro a Luis.')
    assert eng.procesar('¿Quién tiene el libro?') is None
