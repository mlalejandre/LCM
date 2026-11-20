"""Núcleo relacional: pruebas de evidencia, no de comprensión general del idioma."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import pytest


def sem():
    from src.semantics.lexicon import Semantica
    return Semantica(aprendizaje=Path('/tmp/lcm_rel_test_no_existe_0000000000001.json'))


def test_semantica_anterior_conservada_y_new_vocabulario():
    s=sem()
    assert s.nucleo is not None
    assert s.buscar('pájaro')[0]['id']=='concepto.pajaro'
    assert s.buscar('piar')[0]['id']=='accion.piar'
    assert s.buscar('piando')[0]['id']=='accion.piar'
    assert len(s.buscar('banco'))>=2
    assert s.informe()['aprendidos']==0
    assert s.buscar('pájaro')[0]['evidencia']=='curacion_asistida'


def test_taxonomia_multisalto_y_pruebas_con_fuente():
    g=sem().nucleo
    r=g.probar('pájaro','ser vivo',predicado='ES_UN')
    assert r['estado']=='demostrado' and r['derivacion']=='transitividad'
    assert len(r['ruta'])>=3
    assert all(x['p']=='ES_UN' and x['evidencia']=='curacion_asistida' for x in r['ruta'])
    assert g.probar('cuadrado','figura plana')['estado']=='demostrado'


def test_no_todo_se_infiere_del_mismo_dominio():
    g=sem().nucleo
    assert g.probar('perro','ave','ES_UN')['estado']=='no_consta'
    assert g.probar('perro','piar','PUEDE_REALIZAR')['estado']=='no_consta'
    assert g.probar('pingüino','volar','PUEDE_REALIZAR')['estado']=='no_consta'
    assert g.probar('concepto.pajaro','concepto.pio','PRODUCE')['estado']=='no_consta'
    # 'pío' es ambiguo: sonido o flexión verbal, y no se desambigua a ciegas.
    assert g.probar('pájaro','pío','PRODUCE')['estado']=='no_resuelto'
    assert g.probar('pájaro','piar','PUEDE_REALIZAR')['estado']=='demostrado'


def test_sensores_modalidad_sin_alucinaciones():
    g=sem().nucleo
    assert g.probar('sonido','audición','SE_PERCIBE_POR')['estado']=='demostrado'
    assert g.probar('imagen','visión','SE_PERCIBE_POR')['estado']=='demostrado'
    assert g.probar('imagen','audición','SE_PERCIBE_POR')['estado']=='no_consta'


def test_no_inventar_identidad_por_coseno():
    g=sem().nucleo
    assert g.probar('palabra inventada','animal')['estado']=='no_resuelto'
    assert g.resolver('banco') is None


def test_interfaz_conversacional_pregunta_relacional_y_definicion():
    from src.semantics.bridge import PuenteSemantico
    with TemporaryDirectory() as d:
        b=PuenteSemantico(aprendizaje=Path(d)/'aprendizaje.json')
        x=b.responder('¿Qué relación hay entre un pájaro y un animal?')
        assert x and x['relacion']['estado']=='demostrado'
        assert 'ave' in x['respuesta']
        y=b.responder('¿Qué es un pájaro?')
        assert y and 'ave' in y['respuesta'].lower()
        z=b.responder('Dibuja el color verde')
        assert z and z['imagen']['color']=='VERDE'


def test_no_afirmar_relacion_por_vecindad():
    from src.semantics.relational_dialogue import respuesta_relacional
    s=sem()
    assert respuesta_relacional('¿Qué relación hay entre un gato y un círculo?',s) is None


def test_anotaciones_acusticas_requieren_confirmacion():
    from src.multimodal.grounding_relacional import evento_anotado
    g=sem().nucleo
    with pytest.raises(ValueError):
        evento_anotado(g,'audio','AUDIO_12',{'agente':'pájaro','accion':'piar'})
    o=evento_anotado(g,'audio','AUDIO_12',{'agente':'pájaro','accion':'piar'},confirmado=True)
    assert o.conceptos['agente']=='CONCEPTO.PAJARO'
    assert o.conceptos['accion']=='ACCION.PIAR'
    assert o.atributos['coherencia_semantica']=='compatible'
    assert o.evidencia=='usuario_confirmado'
    d=evento_anotado(g,'audio','AUDIO_13',{'agente':'gato','accion':'piar'},confirmado=True)
    assert d.atributos['coherencia_semantica']=='no_consta'


def test_grafo_es_solo_superposicion_en_vectores_originales():
    """Los vectores originales no cambian al agregar nuevas entradas."""
    import torch
    from src.ontology.concept_space import ConceptSpace
    base=json.loads(Path('data/semantica/conceptos_es.json').read_text(encoding='utf8'))
    antiguo=ConceptSpace(128)
    for c in base['conceptos']:
        antiguo.register_concept(c['id'],es_text=c['lema'],features=c['rasgos'],kind=c['tipo'])
    antiguo.build_space(seed=42)
    nuevo=sem()._space()
    for ident in ['VERDE','accion.dibujar','concepto.pajaro','concepto.silla']:
        assert torch.allclose(antiguo.get_vector(ident),nuevo.get_vector(ident),atol=1e-7)


def test_espacio_estructural_no_asevera_hechos():
    g=sem().nucleo
    v=g.similitudes_estructurales('pájaro',limite=4)
    assert len(v)==4 and v[0]['coseno_contextual']<=1.0001
    assert g.probar('perro','piar','PUEDE_REALIZAR')['estado']=='no_consta'


def test_conteo_y_auditoria_sin_etiqueta_99_por_ciento():
    from scripts.auditar_nucleo_relacional import ejecutar
    x=ejecutar()
    assert x['relaciones_explicitadas_adicionales']>=200
    assert x['nodos_aislados_en_grafo_nuevo']>1000
    assert 'evaluación lingüística' in x['tipo']
