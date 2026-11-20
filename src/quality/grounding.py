"""LCM 1.4: barreras de fundamentación y ejecución de operaciones ya comprendidas.

No sustituye la semántica por un enrutador de verbos: las mejoras se basan en
entidades/relaciones específicas de operaciones (reloj y calendario) y evidencia.
Toda regla conservadora puede desactivarse y contrastarse mediante el banco.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import unicodedata
from pathlib import Path

FLAGS = ('reloj', 'edad_hipotetica', 'citas_ajenas', 'comparacion_sin_prueba')
CONFIG = Path('reports/lcm_dialogo14_flags.json')


def normalizar(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', str(s).lower()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', s)).strip()


def config(ruta=CONFIG):
    """Ausencia de configuración: instalamos mejoras verificadas activas."""
    if not Path(ruta).exists():
        return {k: True for k in FLAGS}
    try:
        val = json.loads(Path(ruta).read_text(encoding='utf-8'))
        return {k: bool(val.get(k, True)) for k in FLAGS}
    except (ValueError, OSError, TypeError):
        return {k: True for k in FLAGS}


def _reloj_local(t):
    palabras = normalizar(t).split()
    if 'hora' not in palabras or not palabras:
        return False
    s = ' '.join(palabras)
    # ¿Cuántas horas?, ¿a qué hora sale el tren? -> no es hora actual
    if any(x in s for x in ('a que hora', 'cuantas horas', 'cuantos minutos', 'hora de ', 'zona horaria', 'que hora era', 'que hora sera')):
        return False
    if len(palabras) > 15 or not any(x in palabras for x in ('es', 'son', 'tienes', 'tenemos', 'decir', 'dices', 'dime', 'sabes', 'ahora', 'actual', 'actualmente')):
        return False
    # No responder una afirmación (ej. «no sé qué hora es») ni un reloj externo.
    if palabras[0] in ('no', 'ayer', 'manana') or any(x in s for x in ('tokio', 'londres', 'nueva york', 'llegara', 'llega', 'sale', 'salir', 'empieza', 'termina')):
        return False
    return s.startswith(('que ', 'sabes ', 'me ', 'puedes ', 'podrias ', 'dime ', 'cual ', 'tienes ', 'ahora ', 'hora '))


_HIP = re.compile(r'^(?:y\s+)?si\s+(?:la\s+|el\s+)?(?P<nombre>[a-zñáéíóúü][a-zñáéíóúü-]{1,35})\s+naci[oó]\s+en\s+(?P<anio>(?:18|19|20)\d\d)\b(?P<cola>.*)$', re.I | re.S)


def _edad_hipotetica(t, ahora):
    m = _HIP.match(t.strip(' ¿?¡!.'))
    if not m:
        return None
    q = normalizar(m.group('cola'))
    if not ('anos' in q or 'edad' in q) or not any(x in q.split() for x in ('cuantos', 'cuantas', 'edad', 'tendria', 'tiene', 'tendra')):
        return None
    anyo = int(m.group('anio'))
    if anyo > ahora.year:
        return 'La fecha de nacimiento propuesta está en el futuro; necesito una aclaración.'
    # Hipótesis de año sin día ni mes -> intervalo, no año exacto.
    bajo = ahora.year - anyo - 1
    alto = ahora.year - anyo
    nombre = m.group('nombre').capitalize()
    return f'Si {nombre} nació en {anyo}, ahora tiene entre {bajo} y {alto} años porque no sé el día y el mes de su nacimiento.'


def pre_respuesta(texto, mem=None, flags=None, ahora=None):
    flags = config() if flags is None else flags
    ahora = ahora or getattr(mem, 'today', None) or dt.date.today()
    if isinstance(ahora, dt.datetime):
        ahora = ahora.date()
    if flags.get('reloj') and _reloj_local(texto):
        return 'Son las ' + dt.datetime.now().astimezone().strftime('%H:%M') + ' (hora local del equipo).'
    if flags.get('edad_hipotetica'):
        x = _edad_hipotetica(texto, ahora)
        if x:
            return x
    return None


_STOP = {'hola','que','quien','cual','cuantos','cuantas','como','cuando','donde','es','son','el','la','los','las','un','una','de','en','del','a','al','por','para','me','puedes','dime','sabes','se','ha','hace','ahora','si','y','o','del','mas','fue','ser','ese','esa','tiene'}


def _nombres_consulta(raw):
    """Extraer nombres escritos con mayúscula fuera del inicio de frase.

    Solo se aplica a respuestas que CItAN texto externo; no equivale a NER general.
    """
    palabras = re.findall(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+', str(raw))
    return {normalizar(w) for i, w in enumerate(palabras) if w[0].isupper() and normalizar(w) not in _STOP and (i != 0 or w.upper() == w)}


def post_respuesta(texto, respuesta, flags=None, mem=None):
    flags = config() if flags is None else flags
    if not isinstance(respuesta, str):
        return respuesta
    r = normalizar(respuesta)
    if flags.get('citas_ajenas') and ('en el texto:' in respuesta.lower() or 'en el texto «' in respuesta.lower()):
        nombres = _nombres_consulta(texto)
        # Nunca permitir que un extracto sobre otro individuo responda a María.
        from src.quality.evidencia15 import tokens_documento
        visibles = set(r.split()) | tokens_documento(mem, respuesta)
        # Una refutación («No. Según el texto, está en Perú») no repite el nombre refutado.
        refuta = r.startswith('no ') and any(n in visibles for n in nombres)
        if nombres and not refuta and not all(n in visibles for n in nombres):
            return 'No dispongo de información pertinente sobre ' + ', '.join(sorted(nombres)).capitalize() + ' para responder con seguridad.'
    if flags.get('comparacion_sin_prueba'):
        t = normalizar(texto)
        # Preguntas comparativas: una ficha de atributos no prueba cual gana.
        if ('mas fuerte' in t or 'mas rapido' in t or 'mas pesado' in t) and (t.startswith(('que ', 'quien ', 'cual ', 'dime '))):
            if 'no se' not in r and 'no puedo' not in r and 'depende' not in r:
                # Si el texto no establece comparación o resultado, no aparentar responder.
                indicador = ('mas fuerte' in r or 'mas rapido' in r or 'mas pesado' in r)
                comparado = ' que ' in r or ('entre ' in r and ' y ' in r)
                if not (indicador and comparado):
                    return 'No puedo establecer esa comparación con los hechos que tengo. Necesito evidencia sobre ambos elementos y un criterio de comparación.'
    return respuesta
