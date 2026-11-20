"""Regresión de conceptos, intenciones vectoriales, abstención y persistencia."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json


def new(tmp):
    from src.semantics.bridge import PuenteSemantico
    return PuenteSemantico(aprendizaje=Path(tmp)/'semantica_aprendida.json')


def test_inventario():
    from src.semantics.lexicon import Semantica
    s=Semantica(aprendizaje=Path('/tmp/inexistente_aprendidos_lcm_000000999.json'))
    inv=s.informe()
    assert inv['conceptos'] >= 1800
    assert inv['formas']>=2500
    assert len(s.buscar('banco'))>=2
    assert 'accion.dibujar' in [c['id'] for c in s.buscar('dibujame','accion')]


def test_conceptos_de_accion_coherentes():
    with TemporaryDirectory() as d:
        p=new(d)
        casos={
            'Muéstrame un ejemplo de color azul':'mostrar',
            'Pinta el color rojo':'crear',
            'Dibuja el color verde':'crear',
            'Diseña un cuadro de color azul':'crear',
            'Quiero que generes una imagen verde':'crear',
            'Enseña el color negro':'mostrar',
            'Presenta el color blanco':'mostrar',
        }
        for frase,capacidad in casos.items():
            result=p.responder(frase)
            assert result is not None,frase
            assert result.get('imagen'),frase
            assert result['semantica']['capacidad']==capacidad,frase


def test_no_convertir_frases_declarativas_ni_negadas():
    with TemporaryDirectory() as d:
        p=new(d)
        assert p.responder('Ana dibuja el color rojo.') is None
        assert p.responder('No dibujes el color azul.') is None
        assert p.responder('El color verde es bonito.') is None


def test_definicion_semantica_real():
    with TemporaryDirectory() as d:
        p=new(d)
        r=p.responder('¿Qué es el color azul?')
        assert r and r['respuesta'].startswith('Azul:')
        assert 'sentidos' not in r['respuesta']


def test_aprendizaje_por_confirmacion_y_reinicio():
    with TemporaryDirectory() as d:
        p=new(d)
        q=p.responder('Trazulea una imagen azul')
        assert 'no conozco' in q['respuesta'].lower()
        assert p.lex.informe()['aprendidos']==0
        learned=p.responder('Es una forma de dibujar')
        assert learned and learned['aprendido']
        assert p.lex.informe()['aprendidos']==1
        p2=new(d)
        ok=p2.responder('Trazulea una imagen verde')
        assert ok and ok['semantica']['capacidad']=='crear'
        assert p2.lex.informe()['aprendidos']==1


def test_no_aprender_sin_confirmar():
    with TemporaryDirectory() as d:
        p=new(d)
        p.responder('Trazulea una imagen azul')
        p.responder('No, gracias')
        assert p.lex.informe()['aprendidos']==0


def test_simulador_tiene_modo_explicito():
    from scripts.evaluar_semantica import ejecutar
    rep=ejecutar(140,27)
    assert rep['n']==140
    assert rep['modo'].startswith('simulacion')
    assert rep['correctos']<=rep['n']


def test_motor_chat_integrado_sin_escuela_entrenada():
    # Parser mínimo únicamente para construir Conversation; la resolución
    # visual utiliza el mismo flujo Motor.chat que la web de producción.
    from src.web.motor import Motor

    class FakeParser:
        def parse(self, *a, **kw): return []

    with TemporaryDirectory() as d:
        m=Motor.crear(ruta_memoria=d+'/lcm.json',carpeta_cartuchos=d+'/cartuchos',
                      parser=FakeParser(),semilla=False,log=lambda *_:None)
        from src.semantics.bridge import PuenteSemantico
        m._puente_semantico = PuenteSemantico(aprendizaje=Path(d)/'semantica_aprendida.json')
        r=m.chat('Dibuja el color azul')
        assert r.get('imagen') and r.get('semantica',{}).get('capacidad')=='crear'
        assert m.chat('¿Qué es el color azul?')['respuesta'].startswith('Azul:')
        p=m.chat('Tramulea una imagen roja')
        assert 'no conozco' in p['respuesta'].lower()
        taught=m.chat('Es como pintar')
        assert taught.get('aprendido')
        again=m.chat('Tramulea una imagen roja')
        assert again['imagen']['color']=='ROJO'
