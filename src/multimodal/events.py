"""Identidad conceptual y evidencia independiente de la modalidad.

No se atribuye a sonidos un concepto que no haya sido inferido por un
reconocedor validado o enseñado expresamente por el usuario. Los valores
numéricos de modelos no se consideran probabilidades calibradas.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping, Optional
import re

TIPOS = frozenset({'texto','imagen','audio'})

@dataclass(frozen=True)
class ObservacionConceptual:
    modalidad: str
    entidad: str
    concepto: Optional[str]
    origen: str
    evidencia: str  # 'usuario_confirmado', 'clasificador_color', 'acustica_sin_clasificar', etc.
    atributos: Mapping = field(default_factory=dict)
    conceptos: Mapping = field(default_factory=dict)  # roles -> IDENTIDAD compartida
    # Este contrato registra evidencia; no ejecuta funciones en el motor.

    def __post_init__(self):
        if self.modalidad not in TIPOS:
            raise ValueError('Modalidad desconocida')
        if not re.fullmatch(r'[A-Z0-9_:.\-]{3,100}',self.entidad):
            raise ValueError('Identidad de observación inválida')
        if self.concepto is not None and not re.fullmatch(r'[A-Z0-9_:.\-]{2,100}',self.concepto):
            raise ValueError('Identidad conceptual inválida')
        if not self.evidencia:
            raise ValueError('Evidencia obligatoria')
        for rol,identidad in self.conceptos.items():
            if not re.fullmatch(r'[a-z_]{2,30}',str(rol)) or not re.fullmatch(r'[A-Z0-9_:.\-]{2,100}',str(identidad)):
                raise ValueError('Identidad conceptual por rol inválida')

    def serializar(self):
        return {'modalidad':self.modalidad,'entidad':self.entidad,
                'concepto':self.concepto,'origen':self.origen,
                'evidencia':self.evidencia,'atributos':dict(self.atributos),
                'conceptos':dict(self.conceptos)}


def desde_vision(resultado):
    """Reutiliza el concepto visual validado; no crea otro 'VERDE'."""
    e=resultado.get('entidad')
    if not e:
        raise ValueError('No hay entidad visual')
    color=resultado.get('concepto')
    return ObservacionConceptual('imagen',str(e),str(color) if color else None,
              str(resultado.get('origen','visión 0.1')), 'clasificador_color',
              {'color':color,'detalle':'clasificación de color predominante'},
              {'color':str(color)} if color else {})


def desde_marco_textual(marco):
    """Un marco es una interpretación de una petición, NO percepción visual."""
    import hashlib
    entidad='TEXTO_'+hashlib.sha256(marco.original.encode('utf8')).hexdigest()[:12].upper()
    return ObservacionConceptual('texto',entidad,marco.accion.upper() if marco.accion else None,
              'lenguaje', 'analisis_composicional',
              {'clase':marco.clase,'capacidad':marco.capacidad,'colores':list(marco.conceptos_color)},
              dict([('accion',marco.accion.upper())] if marco.accion else []) |
              dict([('color',marco.conceptos_color[0].upper())] if len(marco.conceptos_color)==1 else []))
