"""Pruebas invariantes de LCM1.8: roles, fuente, no alucinar, persistencia."""
import json
import pytest
from src.memory.store import MemoryStore
from src.semantics.narrativa18 import Narrativa18

@pytest.fixture
def d(tmp_path):
    m=MemoryStore(str(tmp_path/'mem.json'))
    return Narrativa18(m,ruta=tmp_path/'nar.json')

def test_control_tras_transferencia(d):
    assert 'agente' in d.procesar('Ana entregó el libro a Luis.')
    assert d.registros[-1]['agente']=='ANA'
    assert d.registros[-1]['tema']=='LIBRO'
    assert d.registros[-1]['destinatario']=='LUIS'
    assert d.registros[-1]['canal']=='texto_declarado'
    assert d.procesar('¿Quién tiene el libro?').startswith('Luis')

def test_devolucion_y_orden(d):
    d.procesar('Eva dio un cuaderno a Mario.')
    d.procesar('Mario se lo devolvió a Eva.')
    assert d.procesar('¿Quién tiene el cuaderno ahora?').startswith('Eva')
    assert d.procesar('¿Quién tenía el cuaderno antes?').startswith('Mario')

@pytest.mark.parametrize('frase',[
    'Si Ana entregara el libro a Luis, sería útil.',
    'Según Ana, Luis entregó el libro a Marta.',
    'Por favor, entrega el libro a Luis.',
    'Ojalá Ana prestara el libro a Luis.',
    'Creo que Ana dio el libro a Luis.',
    'No sé si Ana prestó el libro a Luis.',
    'Ana cree que Luis devolvió el libro a Ana.',
])
def test_no_convertir_modales_en_hechos(d,frase):
    d.procesar(frase)
    assert d.registros==[]
    assert d.procesar('¿Quién tiene el libro?').startswith('No consta')

def test_negacion_no_transfiere(d):
    d.procesar('Ana no entregó el libro a Luis.')
    assert d.registros==[]

def test_no_inferir_propiedad(d):
    d.procesar('Sara prestó la llave a Nora.')
    assert 'no consta' in d.procesar('¿Quién es dueño de la llave?').lower()

def test_pronombre_femenino(d):
    d.procesar('Leo entregó la postal a Eva.')
    d.procesar('Eva se la devolvió a Leo.')
    assert d.procesar('¿Quién la tiene ahora?').startswith('Leo')

def test_pronombre_genero_incompatible_no_cambia_estado(d):
    d.procesar('Leo entregó la postal a Eva.')
    assert 'no puedo resolver' in d.procesar('Eva se lo devolvió a Leo.').lower()
    assert len(d.registros)==1

def test_pasiva_simple(d):
    d.procesar('El anillo fue entregado a Ana por Jorge.')
    assert d.registros[-1]['agente']=='JORGE'
    assert d.procesar('¿Quién recibió el anillo?').startswith('Ana')

def test_orden_alternativo(d):
    d.procesar('Clara le prestó a Oscar el cuaderno.')
    assert d.procesar('¿Quién tiene el cuaderno?').startswith('Oscar')

def test_declaracion_conflictiva_abstiene(d):
    d.procesar('Clara dio el libro a Ana.')
    r=d.procesar('Eva entregó el libro a Marta.')
    assert 'incompatibles' in r
    assert 'no consta' in d.procesar('¿Quién tiene el libro?').lower()

def test_agente_implicito_no_se_adivina(d):
    d.procesar('Clara dio la postal a Ana.')
    r=d.procesar('La devolvieron a Clara.')
    assert 'no se' in r.lower() or 'necesito' in r.lower()
    assert 'no consta' in d.procesar('¿Quién tiene la postal?').lower()

def test_inferir_solo_ultimo_tenedor_no_propiedad(d):
    d.procesar('Ana entregó la taza a Luis.')
    assert d.registros[0]['accion']=='accion.entregar'
    assert d.procesar('¿Quién es propietaria de la taza?').startswith('No consta')

def test_independencia_objetos(d):
    d.procesar('Ana entregó el libro a Luis.')
    d.procesar('Ana entregó la taza a Sara.')
    assert d.procesar('¿Quién tiene el libro?').startswith('Luis')
    assert d.procesar('¿Quién tiene la taza?').startswith('Sara')

def test_idempotencia_misma_declaracion(d):
    d.procesar('Ana entregó el libro a Luis.')
    d.procesar('Ana entregó el libro a Luis.')
    assert len(d.registros)==1

def test_memoria_resiste_reinicio(tmp_path):
    p=tmp_path/'nar.json';mem=MemoryStore(str(tmp_path/'mem.json'))
    x=Narrativa18(mem,ruta=p)
    x.procesar('Ana entregó el libro a Luis.')
    y=Narrativa18(mem,ruta=p)
    assert y.procesar('¿Quién tiene el libro?').startswith('Luis')

def test_schema_desconocido_no_pisar(tmp_path):
    p=tmp_path/'nar.json';p.write_text('{"schema":"desconocido","registros":[]}',encoding='utf8')
    with pytest.raises(ValueError):Narrativa18(MemoryStore(str(tmp_path/'mem.json')),ruta=p)
    assert 'desconocido' in p.read_text()

def test_integracion_motor_real(tmp_path):
    from src.web.motor import Motor
    class Stub:
        def parse(self,*args,**kw):return []
    mem=MemoryStore(str(tmp_path/'m.json'))
    m=Motor(mem,Stub(),carpeta_cartuchos=str(tmp_path/'cartuchos'))
    assert 'agente' in m.chat('Ana entregó el libro a Luis.')['respuesta']
    assert 'Luis' in m.chat('¿Quién tiene el libro?')['respuesta']
    assert mem.facts==[]  # la narración es una observación testimonial, no un hecho sin contexto
