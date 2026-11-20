"""LCM 1.3: tests de seguridad inferencial, multimodalidad y persistencia.

Son pruebas dirigidas y no equivalen a evaluar comprensión del español.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import pytest

from src.multimodal.episodic_memory import Afirmacion, MemoriaEpisodica
from src.multimodal.events import ObservacionConceptual


def memoria(tmp_path):
    return MemoriaEpisodica(tmp_path/'episodios.json')


def actual(sujeto='AVE_1', verbo='accion.piar', contexto='PATIO', **kw):
    return Afirmacion(sujeto,'REALIZAR',verbo,contexto,**kw)


def test_actual_desde_declaracion_no_es_prueba_sensor(tmp_path):
    m=memoria(tmp_path)
    assert m.afirmar(actual())['nuevo']
    r=m.consultar('AVE_1','REALIZAR','accion.piar','PATIO')
    assert r['estado']=='declarado' and r['pruebas'][0]['dato']['evidencia']=='usuario_afirma'


def test_posibilidad_de_tipo_no_es_suceso(tmp_path):
    m=memoria(tmp_path)
    m.afirmar(Afirmacion('concepto.pajaro','PUEDE_REALIZAR','accion.piar','GENERAL',
                        estatus='posible',alcance='tipo'))
    assert m.consultar('concepto.pajaro','PUEDE_REALIZAR','accion.piar',estatus='posible')['estado']=='posible'
    assert m.consultar('AVE_1','REALIZAR','accion.piar')['estado']=='no_consta'


def test_capacidad_no_se_registra_como_actual():
    with pytest.raises(ValueError):
        Afirmacion('concepto.pajaro','PUEDE_REALIZAR','accion.piar','GENERAL')
    with pytest.raises(ValueError):
        actual(sujeto='concepto.pajaro')


def test_creencia_separa_contenido_de_mundo_externo(tmp_path):
    m=memoria(tmp_path)
    m.afirmar(actual(estatus='creencia',hablante='ANA'))
    assert m.consultar('AVE_1','REALIZAR','accion.piar','PATIO')['estado']=='no_consta'
    assert m.consultar('AVE_1','REALIZAR','accion.piar','PATIO',estatus='creencia',hablante='ANA')['estado']=='creencia_atribuida'


def test_creencias_distintos_hablantes_no_conflicto(tmp_path):
    m=memoria(tmp_path)
    m.afirmar(actual(estatus='creencia',hablante='ANA'))
    m.afirmar(actual(estatus='creencia',hablante='PEDRO',polaridad=False))
    r=m.consultar('AVE_1','REALIZAR','accion.piar','PATIO',estatus='creencia')
    assert r['estado']=='evidencias_distintos_contextos'


def test_hablante_con_creencias_opuestas_conflicto_local(tmp_path):
    m=memoria(tmp_path)
    m.afirmar(actual(estatus='creencia',hablante='ANA'))
    m.afirmar(actual(estatus='creencia',hablante='ANA',polaridad=False))
    assert m.consultar('AVE_1','REALIZAR','accion.piar','PATIO',estatus='creencia',hablante='ANA')['estado']=='conflicto'


def test_hipotesis_no_realidad(tmp_path):
    m=memoria(tmp_path)
    m.afirmar(actual(estatus='hipotetico'))
    assert m.consultar('AVE_1','REALIZAR','accion.piar','PATIO',estatus='hipotetico')['estado']=='hipotetico'
    assert m.consultar('AVE_1','REALIZAR','accion.piar','PATIO')['estado']=='no_consta'


def test_negacion_actual(tmp_path):
    m=memoria(tmp_path)
    m.afirmar(actual(polaridad=False))
    assert m.consultar('AVE_1','REALIZAR','accion.piar','PATIO')['estado']=='negado'


def test_dos_testimonios_opuestos_mismo_momento_conflicto(tmp_path):
    m=memoria(tmp_path)
    m.afirmar(actual())
    m.afirmar(actual(hablante='PEDRO',polaridad=False))
    r=m.consultar('AVE_1','REALIZAR','accion.piar','PATIO')
    assert r['estado']=='conflicto' and r['n_pruebas']==2


def test_tiempos_diferentes_no_conflicto(tmp_path):
    m=memoria(tmp_path)
    m.afirmar(actual(instante='2026-11-17T12:00:00+01:00'))
    m.afirmar(actual(polaridad=False,instante='2026-11-17T18:00:00+01:00'))
    assert m.consultar('AVE_1','REALIZAR','accion.piar','PATIO')['estado']=='evidencias_distintos_contextos'
    assert m.consultar('AVE_1','REALIZAR','accion.piar','PATIO',instante='2026-11-17T18:00:00+01:00')['estado']=='negado'


def test_escenas_distintas_no_conflicto(tmp_path):
    m=memoria(tmp_path)
    m.afirmar(actual(contexto='PATIO'))
    m.afirmar(actual(contexto='CALLE',polaridad=False))
    assert m.consultar('AVE_1','REALIZAR','accion.piar')['estado']=='evidencias_distintos_contextos'


def test_instante_sin_zona_rechazado():
    with pytest.raises(ValueError):actual(instante='2026-11-17T14:00:00')


def test_imagen_verde_misma_identidad_y_procedencia(tmp_path):
    m=memoria(tmp_path)
    o=ObservacionConceptual('imagen','IMAGEN_ABC','VERDE','foto.png','clasificador_color',
                          {'color':'VERDE'}, {'color':'VERDE'})
    r=m.observar(o,contexto='PATIO')
    assert r['afirmaciones_creadas']==1
    res=m.consultar('IMAGEN_ABC','TENER_COLOR','VERDE','PATIO')
    assert res['estado']=='observado_por_clasificador'
    assert res['pruebas'][0]['dato']['observacion_id']==r['id']


def test_imagen_no_resuelta_no_crea_concepto(tmp_path):
    m=memoria(tmp_path)
    o=ObservacionConceptual('imagen','IMAGEN_DUDOSA',None,'foto.png','clasificador_color',
                           {},{})
    assert m.observar(o)['afirmaciones_creadas']==0
    assert m.consultar('IMAGEN_DUDOSA','TENER_COLOR','VERDE')['estado']=='no_consta'


def test_audio_sin_clasificar_no_deduce_pajaro(tmp_path):
    m=memoria(tmp_path)
    o=ObservacionConceptual('audio','SONIDO_ABC',None,'audio.wav',
                             'acustica_sin_clasificar',{'rms_relativo':0.03},{})
    r=m.observar(o)
    assert r['afirmaciones_creadas']==0
    assert m.consultar('SONIDO_ABC','ETIQUETA_ACCION','ACCION.PIAR')['estado']=='no_consta'


def test_audio_anotado_usuario_no_sensor_automatico(tmp_path):
    m=memoria(tmp_path)
    o=ObservacionConceptual('audio','SONIDO_DEF',None,'audio.wav',
                            'usuario_confirmado',{},
                            {'agente':'CONCEPTO.PAJARO','accion':'ACCION.PIAR'})
    r=m.observar(o)
    assert r['afirmaciones_creadas']==2
    assert m.consultar('SONIDO_DEF','ETIQUETA_ACCION','ACCION.PIAR')['estado']=='declarado'
    assert m.consultar('SONIDO_DEF','REALIZAR','accion.piar')['estado']=='no_consta'


def test_anotacion_sonora_no_confirmada_no_contiene_concepto():
    from src.multimodal.audio_features import observacion_audio
    import wave, io
    b=io.BytesIO()
    with wave.open(b,'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
        w.writeframes(b'\x00\x00'*1600)  # 0,2 s de silencio válido
    raw=b.getvalue()
    assert observacion_audio(raw).concepto is None
    with pytest.raises(ValueError,match='confirmación'):
        observacion_audio(raw,etiqueta='pajaro_piando',usuario_confirmo=False)


def test_no_registrar_peticion_textual_como_realidad(tmp_path):
    m=memoria(tmp_path)
    o=ObservacionConceptual('texto','TEXTO_123','ACCION.DIBUJAR','lenguaje',
                             'analisis_composicional',{'clase':'peticion'},
                             {'accion':'ACCION.DIBUJAR'})
    assert m.observar(o)['afirmaciones_creadas']==0
    with pytest.raises(ValueError):
        m.afirmar(actual(evidencia='analisis_composicional'))


def test_idempotencia_observacion_y_afirmacion(tmp_path):
    m=memoria(tmp_path)
    o=ObservacionConceptual('imagen','IMAGEN_ABC','AZUL','foto.png',
                            'clasificador_color',{}, {'color':'AZUL'})
    assert m.observar(o)['afirmaciones_creadas']==1
    assert m.observar(o)['afirmaciones_creadas']==0
    assert m.inventario()['observaciones']==1
    assert m.inventario()['afirmaciones']==1
    assert m.afirmar(actual())['nuevo']
    assert not m.afirmar(actual())['nuevo']


def test_persistencia_y_reinicio(tmp_path):
    m=memoria(tmp_path)
    m.afirmar(actual(estatus='creencia',hablante='ANA'))
    obs=ObservacionConceptual('imagen','IMAGEN_AA','ROJO','png',
                              'clasificador_color',{}, {'color':'ROJO'})
    m.observar(obs)
    otro=memoria(tmp_path)
    assert otro.inventario()==m.inventario()
    assert otro.consultar('AVE_1','REALIZAR','accion.piar','PATIO',estatus='creencia')['estado']=='creencia_atribuida'


def test_memoria_episodica_no_toca_memoria_semantica(tmp_path):
    memoria_original=tmp_path/'lcm_memory.json'
    memoria_original.write_text('{"marcador": 345}',encoding='utf-8')
    m=MemoriaEpisodica(tmp_path/'lcm_episodios.json')
    m.afirmar(actual())
    assert memoria_original.read_text(encoding='utf-8')=='{"marcador": 345}'


def test_anotacion_no_admite_inventar_sonido_de_clasificador():
    with pytest.raises(ValueError):
        Afirmacion('SONIDO_ABC','TENER_COLOR','ROJO','ESCENA',
                  modalidad='audio',evidencia='clasificador_color')
    with pytest.raises(ValueError):
        Afirmacion('SONIDO_ABC','REALIZAR','accion.piar','ESCENA',
                  modalidad='audio',evidencia='acustica_sin_clasificar')


def test_integridad_de_registro_tamper(tmp_path):
    m=memoria(tmp_path)
    m.afirmar(actual())
    data=json.loads(m.ruta.read_text())
    data['afirmaciones'][0]['dato']['objeto']='accion.ladrar'
    m.ruta.write_text(json.dumps(data),encoding='utf-8')
    with pytest.raises(ValueError,match='integridad'):
        memoria(tmp_path)


def test_resolver_roles_y_capacidad_sin_inferir_suceso(tmp_path):
    from src.semantics.lexicon import Semantica
    from src.semantics.event_bridge import resolver_rol,capacidad_no_es_suceso,suceso_declarado
    with TemporaryDirectory() as folder:
        s=Semantica(aprendizaje=Path(folder)/'aprendizaje.json')
        assert resolver_rol(s,'pájaro')['estado']=='resuelto'
        assert resolver_rol(s,'banco')['estado']=='ambiguo'
        assert resolver_rol(s,'xipifo')['estado']=='desconocido'
        a=capacidad_no_es_suceso(s,'pájaro','piar')
        assert a['estado']=='capacidad_de_tipo' and a['autoriza_suceso'] is False
        m=memoria(tmp_path)
        assert m.consultar('AVE_1','REALIZAR','accion.piar')['estado']=='no_consta'
        suceso_declarado(m,'AVE_1','accion.piar','PATIO',cree='ANA')
        assert m.consultar('AVE_1','REALIZAR','accion.piar','PATIO')['estado']=='no_consta'


def test_inventario_no_calibra_coseno(tmp_path):
    m=memoria(tmp_path)
    assert m.inventario()['afirmaciones']==0
    assert m.consultar('AVE_1','REALIZAR','accion.piar')['nota'].find('probabilidad')>=0


def test_motor_web_vision_registra_evidencia_episodica(tmp_path):
    """Prueba el trayecto web existente, no solamente el almacén aislado."""
    from src.web.motor import Motor
    from src.memory.store import MemoryStore
    from PIL import Image
    from threading import RLock
    import io
    motor=Motor.__new__(Motor)
    motor.mem=MemoryStore(str(tmp_path/'lcm_memory.json'))
    motor.lock=RLock()
    motor._vision_reciente=None
    archivo=io.BytesIO()
    Image.new('RGB',(48,48),(22,170,65)).save(archivo,format='PNG')
    r=motor.vision_analizar(archivo.getvalue(),'color.png')
    assert r['concepto']=='VERDE' and r['episodio']['afirmaciones_creadas']==1
    m=MemoriaEpisodica(tmp_path/'lcm_episodios.json')
    assert m.consultar(r['entidad'],'TENER_COLOR','VERDE','IMAGEN_CHAT')['estado']=='observado_por_clasificador'
    r2=motor.vision_analizar(archivo.getvalue(),'color.png')
    assert r2['episodio']['afirmaciones_creadas']==0


def test_motor_web_vision_ambigua_no_crea_hechos(tmp_path):
    from src.web.motor import Motor
    from src.memory.store import MemoryStore
    from PIL import Image
    from threading import RLock
    import io
    motor=Motor.__new__(Motor)
    motor.mem=MemoryStore(str(tmp_path/'lcm_memory.json'))
    motor.lock=RLock()
    motor._vision_reciente=None
    imagen=Image.new('RGB',(40,40),(220,10,10))
    for x in range(20,40):
        for y in range(40): imagen.putpixel((x,y),(10,20,230))
    archivo=io.BytesIO()
    imagen.save(archivo,format='PNG')
    r=motor.vision_analizar(archivo.getvalue(),'mixto.png')
    assert r['concepto'] is None
    assert r['episodio']['afirmaciones_creadas']==0
    m=MemoriaEpisodica(tmp_path/'lcm_episodios.json')
    assert m.inventario()['observaciones']==1
    assert m.inventario()['afirmaciones']==0


def test_oraculo_curado_contiene_variedad_y_no_responde_por_similitud():
    """Casos humanos reservados para evaluar un extractor lingüístico futuro."""
    ruta=Path('data/semantica/oraculo_eventos_es_13.jsonl')
    casos=[json.loads(x) for x in ruta.read_text(encoding='utf-8').splitlines()]
    assert len(casos)>=40
    assert len({x['id'] for x in casos})==len(casos)
    assert len({x['clase'] for x in casos})>=15
    assert all(x['estatus'] in ('actual','posible','hipotetico','creencia','ninguno') for x in casos)
    assert any(x['canal_mencionado']=='audio' for x in casos)
    assert any(x['canal_mencionado']=='imagen' for x in casos)
    assert any(not x['autoriza_afirmar_suceso_actual'] for x in casos)


def test_chat_con_adjunto_registra_episodio_en_respuesta(tmp_path):
    from src.web.motor import Motor
    from src.memory.store import MemoryStore
    from PIL import Image
    from threading import RLock
    import io
    motor=Motor.__new__(Motor)
    motor.mem=MemoryStore(str(tmp_path/'lcm_memory.json'))
    motor.lock=RLock()
    motor._vision_reciente=None
    archivo=io.BytesIO()
    Image.new('RGB',(48,48),(22,170,65)).save(archivo,format='PNG')
    res=motor.chat('¿De qué color es?',imagen=archivo.getvalue(),nombre='adjunto.png')
    assert 'verde' in res['respuesta'].lower()
    assert res['episodio']['afirmaciones_creadas']==1
    assert res.get('aviso_episodio') is None
