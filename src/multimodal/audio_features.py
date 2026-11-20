"""Características reproducibles de WAV PCM; no reconoce aves ni habla.

Uso futuro: reconocimiento acústico -> concepto compartido -> memoria.
Solo el USUARIO o un clasificador posterior validado pueden asignar la etiqueta
'PÁJARO_PÍA'. Esta pieza mide audio, no inventa su contenido semántico.
"""
from __future__ import annotations
import array
import hashlib
import io
import math
import sys
import wave
from .events import ObservacionConceptual

MAX_BYTES=12_000_000
MAX_DURACION=60


def _decode_samples(raw, sampwidth):
    if sampwidth!=2:
        raise ValueError('Visión/Audio 0.1 acepta WAV PCM de 16 bits')
    a=array.array('h');a.frombytes(raw)
    if sys.byteorder!='little':a.byteswap()
    return a


def analizar_wav(datos:bytes):
    if not isinstance(datos,(bytes,bytearray)) or len(datos)>MAX_BYTES:
        raise ValueError('Archivo de audio inválido o demasiado grande')
    try:
        with wave.open(io.BytesIO(datos),'rb') as wav:
            nchan=wav.getnchannels();rate=wav.getframerate();width=wav.getsampwidth()
            n=wav.getnframes();comp=wav.getcomptype()
            if nchan not in (1,2) or rate<8000 or rate>192000 or width!=2 or comp!='NONE':
                raise ValueError('Se requiere WAV PCM 16 bits, 1–2 canales, 8–192 kHz')
            dur=n/rate
            if not 0.08<=dur<=MAX_DURACION:
                raise ValueError('Duración no admitida: 0,08 a 60 segundos')
            if n*nchan*width>MAX_BYTES:
                raise ValueError('Audio descomprimido demasiado grande')
            # Hasta ~1 s distribuido en la grabación: cálculo acotado en CPU.
            frames=wav.readframes(n)
    except (wave.Error,EOFError) as exc:
        raise ValueError('WAV no válido') from exc
    x=_decode_samples(frames,width)
    if not x:
        raise ValueError('Audio vacío')
    # Reproducible para ambas plataformas y sin modelos externos.
    salto=max(1,n//(rate*2))
    count=0;acc=0;peak=0;cambios=0;prev=None
    for j in range(0,n,salto):
        v=int(x[j*nchan]) if nchan==1 else (int(x[j*2])+int(x[j*2+1]))//2
        count+=1;acc+=v*v;peak=max(peak,abs(v))
        signo=1 if v>0 else (-1 if v<0 else 0)
        if prev is not None and signo and prev and signo!=prev:cambios+=1
        if signo:prev=signo
    rms=math.sqrt(acc/max(1,count))/32768
    return {'entidad':'SONIDO_'+hashlib.sha256(datos).hexdigest()[:12].upper(),
            'duracion_s':round(dur,3),'canales':nchan,'frecuencia_muestreo_hz':rate,
            'rms_relativo':round(rms,5),'pico_relativo':round(peak/32768,5),
            'cruces_cero_relativos':round(cambios/max(1,count-1),5),
            'silencio_probable':rms<0.003,
            'identificacion':'no_disponible'}


def observacion_audio(datos:bytes, etiqueta=None, usuario_confirmo=False):
    medidas=analizar_wav(datos)
    if etiqueta and not usuario_confirmo:
        raise ValueError('La etiqueta semántica de audio requiere confirmación del usuario')
    concepto=None
    if etiqueta:
        import unicodedata,re
        norm=unicodedata.normalize('NFD',str(etiqueta).upper())
        norm=''.join(c for c in norm if not unicodedata.combining(c))
        concepto=re.sub(r'[^A-Z0-9_]+','_',norm).strip('_')
        if not 2<=len(concepto)<=80:
            raise ValueError('Etiqueta inválida')
    evidencia='usuario_confirmado' if concepto else 'acustica_sin_clasificar'
    return ObservacionConceptual('audio',medidas['entidad'],concepto,
           'archivo_wav',evidencia,medidas, {'evento':concepto} if concepto else {})
