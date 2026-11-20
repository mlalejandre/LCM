"""Regresión: composición semántica y contrato multimodal, sin datos privados."""
from __future__ import annotations
import io
import math
import struct
import wave
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest


def puente(d):
    from src.semantics.bridge import PuenteSemantico
    return PuenteSemantico(aprendizaje=Path(d)/'aprendizaje.json')


def wav_ejemplo(freq=1200, t=0.18, rate=16000):
    b=io.BytesIO()
    with wave.open(b,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
        w.writeframes(b''.join(struct.pack('<h',round(8000*math.sin(2*math.pi*freq*i/rate))) for i in range(int(rate*t))))
    return b.getvalue()


def test_banco_composicion_reproducible():
    from scripts.evaluar_composicion import ejecutar
    informe=ejecutar()
    assert informe['n']>=30
    assert informe['aciertos']==informe['n'], informe['fallos']


def test_distingue_negacion_global_y_contraste():
    with TemporaryDirectory() as d:
        p=puente(d)
        assert p.responder('No quiero que crees nada azul.') is None
        r=p.responder('No pintes: solo muestra el color verde.')
        assert r and r['semantica']['capacidad']=='mostrar'
        assert r['imagen']['color']=='VERDE'


def test_subjuntivo_y_futuro_declarativo():
    with TemporaryDirectory() as d:
        p=puente(d)
        assert p.responder('Me gustaría que dibujaras una muestra roja.')['imagen']['color']=='ROJO'
        assert p.responder('Te mostraré el color verde mañana.') is None


def test_paralelismo_modalidades_misma_identidad():
    from src.multimodal.events import desde_vision
    with TemporaryDirectory() as d:
        r=puente(d).responder('Dibuja una muestra verde.')
        lenguaje=r['observacion']
        visual=desde_vision({'entidad':'IMAGEN_123ABC','concepto':'VERDE'}).serializar()
        assert lenguaje['modalidad']=='texto' and visual['modalidad']=='imagen'
        assert lenguaje['conceptos']['color']==visual['conceptos']['color']=='VERDE'
        assert lenguaje['conceptos']['accion']=='ACCION.DIBUJAR'


def test_multimodal_no_inventa_significados_acusticos():
    from src.multimodal.audio_features import observacion_audio
    sample=wav_ejemplo()
    o=observacion_audio(sample)
    assert o.modalidad=='audio' and o.concepto is None
    assert o.evidencia=='acustica_sin_clasificar'
    assert o.atributos['identificacion']=='no_disponible'
    assert o.atributos['rms_relativo']>0


def test_etiqueta_audio_solo_tras_confirmacion():
    from src.multimodal.audio_features import observacion_audio
    sample=wav_ejemplo()
    with pytest.raises(ValueError):
        observacion_audio(sample,etiqueta='pájaro piando',usuario_confirmo=False)
    o=observacion_audio(sample,etiqueta='pájaro piando',usuario_confirmo=True)
    assert o.concepto=='PAJARO_PIANDO'
    assert o.evidencia=='usuario_confirmado'
    assert o.conceptos['evento']=='PAJARO_PIANDO'


def test_audio_silencio_no_se_convierte_en_concepto():
    from src.multimodal.audio_features import observacion_audio
    wave_data=io.BytesIO()
    with wave.open(wave_data,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
        w.writeframes(b'\x00\x00'*4000)
    res=observacion_audio(wave_data.getvalue())
    assert res.atributos['silencio_probable'] is True
    assert res.concepto is None


def test_audio_archivo_invalido_y_formato_incompatible():
    from src.multimodal.audio_features import analizar_wav
    with pytest.raises(ValueError):analizar_wav(b'NO ES WAV')
    with pytest.raises(ValueError):analizar_wav(b'0'*12_000_001)
    p=io.BytesIO()
    with wave.open(p,'wb') as w:
        w.setnchannels(1);w.setsampwidth(1);w.setframerate(8000);w.writeframes(b'\x00'*1600)
    with pytest.raises(ValueError):analizar_wav(p.getvalue())


def test_vision_produce_observacion_unica_sin_reetiquetar():
    from src.vision.perception import procesar_imagen
    from PIL import Image
    from src.memory.store import MemoryStore
    import io
    b=io.BytesIO();Image.new('RGB',(80,80),(22,163,74)).save(b,'PNG')
    with TemporaryDirectory() as d:
        m=MemoryStore(str(Path(d)/'memoria.json'))
        r=procesar_imagen(m,b.getvalue(),'verde.png')
        assert r['concepto']=='VERDE'
        assert r['observacion']['modalidad']=='imagen'
        assert r['observacion']['conceptos']['color']=='VERDE'
        assert all(f['o']!='PAJARO_PIANDO' for f in m.facts)


def test_no_modifica_memoria_por_texto_hasta_ensenanza():
    with TemporaryDirectory() as d:
        p=puente(d)
        p.responder('Dibuja un color azul.')
        assert not (Path(d)/'aprendizaje.json').exists()
        p.responder('Tramulea un color rojo.')
        assert not (Path(d)/'aprendizaje.json').exists()
        p.responder('Es como pintar.')
        assert (Path(d)/'aprendizaje.json').exists()
