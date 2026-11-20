from datetime import date
from src.quality.evidencia15 import edad_hecho, pertinencia, post_respuesta
from src.memory.store import MemoryStore


def mem(tmp_path):
    m=MemoryStore(str(tmp_path/'m.json')); m.today=date(2026,11,18);return m


def test_edad_ano_con_hecho(tmp_path):
    m=mem(tmp_path)
    m.add_fact(('MARIA','NACER','_'),source='María nació en 1982.',when='1982')
    resp=edad_hecho('¿Cuántos años tiene María?',m)
    assert '43' in resp and '44' in resp


def test_edad_sin_hecho_no_inventa(tmp_path):
    m=mem(tmp_path)
    m.add_fact(('LAMINE','NACER','_'),source='Lamine nació en 2007',when='2007')
    assert edad_hecho('¿Cuántos años tiene María?',m) is None


def test_edad_dia_exactamente(tmp_path):
    m=mem(tmp_path)
    m.add_fact(('MARIA','NACER','_'),when='abs:1982-01-01/1982-01-01')
    assert '44 años' in edad_hecho('¿Qué edad tiene María?',m)


def test_edad_conflictos(tmp_path):
    m=mem(tmp_path)
    m.add_fact(('MARIA','NACER','_'),when='1982')
    m.add_fact(('MARIA','NACER','_'),when='1983')
    assert 'incompatibles' in edad_hecho('¿Qué edad tiene María?',m)


def test_solo_nacimiento_positivo(tmp_path):
    m=mem(tmp_path)
    m.add_fact(('MARIA','NACER','_'),when='1982',neg=True)
    assert edad_hecho('¿Qué edad tiene María?',m) is None


def test_cita_ajena():
    q='¿Cuántos años tiene María?'
    r='No. Según el texto, fue en 2007. En el texto: «Lamine nació en 2007».'
    assert not pertinencia(q,r)[0]
    assert 'no tengo' in post_respuesta(q,r).lower()


def test_cita_pertinente():
    q='¿Dónde nació María?'
    r='Según el texto María nació en Toledo. En el texto: «María nació en Toledo».'
    assert pertinencia(q,r)[0]


def test_cita_de_otro_tema():
    q='¿Qué relación hay entre hipopótamo y mamífero?'
    r='Según el texto, De la Fuente dijo que Lamine jugó 90 minutos.'
    assert not pertinencia(q,r)[0]


def test_no_tocar_citas_sin_comprobacion():
    assert post_respuesta('¿Qué es un pájaro?','Pájaro es un ave.')=='Pájaro es un ave.'


def test_no_mezclar_hipotetica_con_hechos(tmp_path):
    m=mem(tmp_path)
    m.add_fact(('MARIA','NACER','_'),when='2005')
    assert edad_hecho('Si María nació en 1982 ¿cuántos años tendría hoy?',m) is None


def test_raiz_cuadrada_operacion():
    from src.quality.evidencia15 import operacion_matematica
    assert operacion_matematica('¿Sabes calcular la raíz cuadrada de 144?').endswith('12.')
    assert operacion_matematica('¿Cuál es la raíz cuadrada de 81?').endswith('9.')
    assert operacion_matematica('Ana dijo que la raíz cuadrada de 81 es 9.') is None
    assert operacion_matematica('No calcules la raíz cuadrada de 81') is None


def test_negacion_por_composicion_no_por_verbo():
    from src.semantics.bridge import PuenteSemantico
    p=PuenteSemantico()
    from src.quality.evidencia15 import confirmacion_negacion_visual
    for x in ('No dibujes nada de color azul', 'No me muestres el color verde',
              'No quiero que dibujes el color amarillo'):
        assert p.responder(x) is None  # contrato heredado
        assert 'No generaré' in confirmacion_negacion_visual(x,p.lex)
    assert p.responder('No sé si dibujas de color rojo') is None
    assert confirmacion_negacion_visual('No sé si dibujas de color rojo',p.lex) is None
