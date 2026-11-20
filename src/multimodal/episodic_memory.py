"""LCM 1.3: memoria de evidencias multimodales y afirmaciones con alcance.

No es un reconocedor, un LLM ni un parser universal del español. La identidad
conceptual es la misma que en LCM; la modalidad describe el origen de la evidencia.
Una capacidad POSIBLE no autoriza afirmar un SUCESO ACTUAL.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from threading import RLock
from typing import Optional
import json
import os
import re
import tempfile

SCHEMA = 'lcm-episodios-1.3'
MODALIDADES = frozenset({'texto', 'imagen', 'audio'})
ESTATUS = frozenset({'actual', 'posible', 'hipotetico', 'creencia'})
FUENTES = frozenset({'usuario_afirma','usuario_confirmado','clasificador_color',
                     'analisis_composicional','acustica_sin_clasificar'})
RELACIONES = frozenset({'TENER_COLOR','REALIZAR','PUEDE_REALIZAR',
                        'ETIQUETA_ACCION','ETIQUETA_AGENTE','ES_UN'})
COLORES = frozenset({'VERDE','ROJO','AZUL','AMARILLO','BLANCO','NEGRO'})
ID = re.compile(r'^[A-Za-z0-9_.:\-]{2,120}$')
MAX_REGISTROS = 100_000


def _id(s, campo):
    if not isinstance(s, str) or not ID.fullmatch(s):
        raise ValueError(f'{campo}: identidad no válida')
    return s


def _instante(x):
    if x is None:
        return None
    if not isinstance(x,str): raise ValueError('instante debe ser ISO-8601 o None')
    try:
        d = datetime.fromisoformat(x)
    except ValueError as e:
        raise ValueError('instante ISO-8601 inválido') from e
    if d.tzinfo is None or d.utcoffset() is None:
        raise ValueError('el instante requiere zona horaria explícita')
    return d.isoformat()


@dataclass(frozen=True)
class Afirmacion:
    sujeto: str
    relacion: str
    objeto: str
    contexto: str
    estatus: str = 'actual'
    polaridad: bool = True
    modalidad: str = 'texto'
    evidencia: str = 'usuario_afirma'
    hablante: str = 'USUARIO'
    instante: Optional[str] = None
    alcance: str = 'instancia'  # instancia / tipo
    observacion_id: Optional[str] = None

    def __post_init__(self):
        for nombre in ('sujeto','objeto','contexto','hablante'):
            _id(getattr(self,nombre), nombre)
        if self.observacion_id is not None:
            _id(self.observacion_id, 'observacion_id')
        if self.relacion not in RELACIONES:
            raise ValueError('relación no admitida')
        if self.estatus not in ESTATUS or self.modalidad not in MODALIDADES:
            raise ValueError('modalidad o estatus no admitido')
        if self.evidencia not in FUENTES:
            raise ValueError('procedencia no admitida')
        if self.alcance not in ('tipo','instancia') or type(self.polaridad) is not bool:
            raise ValueError('alcance o polaridad inválido')
        _instante(self.instante)
        if self.relacion == 'PUEDE_REALIZAR':
            if self.alcance != 'tipo' or self.estatus != 'posible':
                raise ValueError('capacidad de un tipo NO equivale a acontecimiento actual')
        if self.relacion == 'REALIZAR':
            if self.alcance != 'instancia' or self.sujeto.startswith(('concepto.','accion.')):
                raise ValueError('un acontecimiento requiere instancia, no categoría')
        if self.evidencia=='clasificador_color':
            if not (self.modalidad=='imagen' and self.relacion=='TENER_COLOR'
                    and self.objeto in COLORES and self.estatus=='actual'
                    and self.alcance=='instancia' and self.polaridad):
                raise ValueError('un clasificador de color solo prueba su propia clasificación cromática')
        if self.evidencia=='acustica_sin_clasificar':
            raise ValueError('audio sin clasificar no autoriza afirmaciones de contenido')
        if self.evidencia=='analisis_composicional':
            raise ValueError('interpretar una petición no prueba que ocurra el acontecimiento')
        if self.evidencia=='usuario_confirmado' and not self.observacion_id:
            raise ValueError('la anotación confirmada exige observación de origen')

    def serializar(self):
        return asdict(self)


def _hash(obj):
    payload=json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',',':'))
    return sha256(payload.encode('utf-8')).hexdigest()[:24].upper()


def _validar_obs(o):
    if hasattr(o, 'serializar'):
        o=o.serializar()
    if not isinstance(o,dict):
        raise ValueError('observación inválida')
    if o.get('modalidad') not in MODALIDADES:
        raise ValueError('modalidad de observación inválida')
    _id(o.get('entidad'),'entidad')
    if o.get('concepto') is not None:
        _id(o.get('concepto'),'concepto')
    if o.get('evidencia') not in FUENTES:
        raise ValueError('evidencia de observación inválida')
    if o.get('modalidad')=='audio' and o.get('concepto') and o.get('evidencia')!='usuario_confirmado':
        # Los reconocedores de audio futuros necesitarán un tipo de evidencia propio,
        # explícitamente validado y distinto de medidas de señal.
        raise ValueError('audio etiquetado debe ser confirmado por usuario')
    # Serialización validada: comprobar límites y tipos de campos no estructurados.
    if not isinstance(o.get('atributos',{}),dict) or not isinstance(o.get('conceptos',{}),dict):
        raise ValueError('atributos/conceptos no válidos')
    safe={k:o.get(k) for k in ('modalidad','entidad','concepto','origen','evidencia','atributos','conceptos')}
    if not isinstance(safe['origen'],str) or len(safe['origen'])>300:
        raise ValueError('origen inválido')
    if len(json.dumps(safe,ensure_ascii=False))>10_000:
        raise ValueError('observación demasiado grande')
    return safe


class MemoriaEpisodica:
    """Registro JSON separado de MemoryStore. No modifica ni checkpoints ni hechos.

    La consulta no convierte un testimonio o una hipótesis en hecho demostrado.
    La comparación de contradicciones usa un mismo contexto e instante: dos
    momentos diferentes no implican contradicción.
    """
    def __init__(self, ruta='memory/lcm_episodios.json'):
        self.ruta=Path(ruta)
        self.lock=RLock()
        self.observaciones=[]
        self.afirmaciones=[]
        if self.ruta.is_file():
            raw=json.loads(self.ruta.read_text(encoding='utf-8'))
            if raw.get('schema')!=SCHEMA:
                raise ValueError('Memoria episódica: esquema incompatible')
            self.observaciones=[]
            for r in raw.get('observaciones',[]):
                o=_validar_obs(r['dato'])
                if r['_id']!='OBS_'+_hash(o):
                    raise ValueError('integridad de observación inválida')
                self.observaciones.append(o | {'_id':r['_id']})
            self.afirmaciones=[]
            for r in raw.get('afirmaciones',[]):
                a=Afirmacion(**r['dato'])
                if r['_id'] != _hash(a.serializar()):
                    raise ValueError('integridad de afirmación inválida')
                self.afirmaciones.append({'_id':r['_id'],'dato':a.serializar()})
        self._ids_obs={x['_id'] for x in self.observaciones}
        self._ids_af={x['_id'] for x in self.afirmaciones}

    def _persistir(self):
        if len(self.observaciones)+len(self.afirmaciones)>MAX_REGISTROS:
            raise ValueError('límite de almacenamiento episódico alcanzado')
        # Almacenar sólo metadata/roles, no bytes originales de imagen o audio.
        obj={'schema':SCHEMA,
             'observaciones':[{'_id':r['_id'], 'dato':{k:v for k,v in r.items() if k!='_id'}}
                              for r in self.observaciones],
             'afirmaciones':self.afirmaciones}
        self.ruta.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix='.lcm_ep_',dir=str(self.ruta.parent))
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as out:
                json.dump(obj,out,ensure_ascii=False,indent=2)
                out.write('\n');out.flush();os.fsync(out.fileno())
            os.replace(tmp,self.ruta)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)

    def afirmar(self, a):
        if isinstance(a,dict): a=Afirmacion(**a)
        if not isinstance(a,Afirmacion): raise TypeError('se requiere Afirmacion')
        r={'_id':_hash(a.serializar()),'dato':a.serializar()}
        with self.lock:
            if r['_id'] in self._ids_af:return {'nuevo':False,'id':r['_id']}
            self.afirmaciones.append(r)
            self._ids_af.add(r['_id'])
            try:self._persistir()
            except Exception:
                self.afirmaciones.pop();self._ids_af.discard(r['_id']);raise
        return {'nuevo':True,'id':r['_id']}

    def observar(self, observacion, contexto='ESCENA_LOCAL'):
        """Registra evidencia multimodal; solo produce hechos del alcance probado.

        Una observación acústica sin identificar se guarda SIN etiquetar sonido.
        Si el usuario confirma una anotación de audio, se guardan etiquetas
        de la grabación, NO la afirmación de que se observó un evento real.
        """
        o=_validar_obs(observacion)
        _id(contexto,'contexto')
        ident='OBS_'+_hash(o)
        with self.lock:
            nuevo=ident not in self._ids_obs
            if nuevo:
                self.observaciones.append(o | {'_id':ident})
                self._ids_obs.add(ident)
                try:self._persistir()
                except Exception:
                    self.observaciones.pop();self._ids_obs.discard(ident);raise
        afirmaciones=[]
        if o['modalidad']=='imagen' and o['evidencia']=='clasificador_color' and o['concepto'] in COLORES:
            afirmaciones.append(Afirmacion(o['entidad'],'TENER_COLOR',o['concepto'],
                contexto,modalidad='imagen',evidencia='clasificador_color',
                hablante='CLASIFICADOR_COLOR',observacion_id=ident))
        if o['modalidad']=='audio' and o['evidencia']=='usuario_confirmado':
            for rol,rel in (('accion','ETIQUETA_ACCION'),('agente','ETIQUETA_AGENTE')):
                etiqueta=o['conceptos'].get(rol)
                if etiqueta:
                    _id(etiqueta,'etiqueta')
                    afirmaciones.append(Afirmacion(o['entidad'],rel,etiqueta,contexto,
                        modalidad='audio',evidencia='usuario_confirmado',
                        hablante='USUARIO',observacion_id=ident))
        af=[self.afirmar(a) for a in afirmaciones]
        return {'id':ident,'observacion_nueva':nuevo,'afirmaciones_creadas':sum(x['nuevo'] for x in af),
                'contenido_semantico_verificado':bool(af)}

    def consultar(self, sujeto, relacion, objeto, contexto=None, instante=None,
                  estatus='actual', hablante=None):
        """Devuelve pruebas filtradas; si varían los instantes, no inventa conflicto.

        Creencia, posibilidad y actual se consultan por separado.
        Para creencias, la perspectiva del hablante es parte del mundo evaluado.
        """
        _id(sujeto,'sujeto');_id(objeto,'objeto')
        if relacion not in RELACIONES or estatus not in ESTATUS:
            raise ValueError('consulta inválida')
        if contexto is not None:_id(contexto,'contexto')
        if hablante is not None:_id(hablante,'hablante')
        inst=_instante(instante)
        rows=[r for r in self.afirmaciones if r['dato']['sujeto']==sujeto
            and r['dato']['relacion']==relacion and r['dato']['objeto']==objeto
            and r['dato']['estatus']==estatus
            and (contexto is None or r['dato']['contexto']==contexto)
            and (inst is None or _instante(r['dato']['instante'])==inst)
            and (hablante is None or r['dato']['hablante']==hablante)]
        # Una creencia pertenece al hablante y no contradice un hecho externo.
        # Dos afirmaciones en momentos diferentes tampoco se contradicen.
        grupos={}
        for r in rows:
            d=r['dato']
            key=(d['contexto'],_instante(d['instante']), d['hablante'] if estatus=='creencia' else None)
            grupos.setdefault(key,[]).append(r)
        conflic=[k for k,rr in grupos.items() if len({r['dato']['polaridad'] for r in rr})>1]
        if conflic: estado='conflicto'
        elif not rows: estado='no_consta'
        elif len(grupos)>1: estado='evidencias_distintos_contextos'
        elif not rows[0]['dato']['polaridad']: estado='negado'
        elif estatus=='actual': estado=('observado_por_clasificador' if
            all(r['dato']['evidencia']=='clasificador_color' for r in rows) else 'declarado')
        elif estatus=='posible': estado='posible'
        elif estatus=='creencia': estado='creencia_atribuida'
        else: estado='hipotetico'
        return {'estado':estado,'estatus':estatus,'pruebas':rows,
                'n_pruebas':len(rows),'contextos':len(grupos),
                'nota':'pruebas de procedencia; no equivalen a probabilidad ni a verdad absoluta'}

    def inventario(self):
        return {'observaciones':len(self.observaciones),'afirmaciones':len(self.afirmaciones),
                'por_modalidad':{m:sum(o['modalidad']==m for o in self.observaciones) for m in sorted(MODALIDADES)},
                'por_estatus':{e:sum(a['dato']['estatus']==e for a in self.afirmaciones) for e in sorted(ESTATUS)}}
