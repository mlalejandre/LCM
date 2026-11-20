"""Regresión del control de fundamentación. No evalúa comprensión libre de español."""
import datetime as dt
from src.quality.grounding import pre_respuesta, post_respuesta
from scripts.iterar_lcm import generar, evaluar_respuesta


def test_hora_diferentes_formas_y_fuentes():
    for t in ('¿Qué hora es ahora?', '¿Sabes qué hora es?', '¿Me puedes decir qué hora es?', '¿Me dices la hora?'):
        r=pre_respuesta(t)
        assert r is not None and 'hora local' in r
    for t in ('¿A qué hora sale el tren?', 'No sé qué hora es', '¿Qué hora es en Tokio?'):
        assert pre_respuesta(t) is None


def test_hipotesis_sin_escritura_y_sin_edad_falsa():
    year=dt.date.today().year
    r=pre_respuesta('Si María nació en 1982, ¿cuántos años tiene ahora María?')
    assert str(year-1982-1) in r and str(year-1982) in r
    assert pre_respuesta('Si María nació en 1982, mañana saldrá el sol.') is None


def test_cita_de_otra_entidad_se_rechaza():
    q='¿Cuándo nació María?'
    r='En el texto: «Lamine Yamal nació en 2007». Fue en 2007.'
    out=post_respuesta(q,r)
    assert '2007' not in out and 'Mar' in out
    assert post_respuesta('¿Cuándo nació Lamine?',r)==r


def test_comparacion_sin_prueba_se_abstiene():
    q='¿Qué es más fuerte, un león o un unicornio?'
    r='El león es un mamífero.'
    assert 'No puedo establecer' in post_respuesta(q,r)


def test_banco_tandas_y_rubricas():
    casos=generar(40)
    assert len(casos)==40 and len({x['id'] for x in casos})==40
    assert casos[2]['tipo']=='reloj'
    assert evaluar_respuesta(casos[7],{'imagen':{'color':'VERDE'},'respuesta':'verde'})[0]
    assert not evaluar_respuesta(casos[7],{'imagen':None,'respuesta':'verde'})[0]


def test_motor_gate_opcional_con_parser_minimo(tmp_path):
    from src.memory.store import MemoryStore
    from src.web.motor import Motor
    class Parser:
        def parse(self,*a,**kw): return []
    motor=Motor(MemoryStore(str(tmp_path/'mem.json')),Parser(),str(tmp_path/'cart'))
    assert 'hora local' in motor.chat('¿Qué hora es ahora?')['respuesta']
    assert '1982' in motor.chat('Si María nació en 1982, ¿cuántos años tiene ahora María?')['respuesta']
    motor._calidad_flags={'reloj':False,'edad_hipotetica':False,'citas_ajenas':False,'comparacion_sin_prueba':False}
    from src.quality.grounding import pre_respuesta
    assert pre_respuesta('¿Qué hora es ahora?',flags=motor._calidad_flags) is None
