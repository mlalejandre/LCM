"""LCM 2.13 · APLICACIONES DETERMINISTAS.

El LCM no calcula ni dibuja de memoria: reconoce QUÉ operación se pide y con QUÉ datos, llama a una aplicación de este paquete,
recoge el resultado y lo comunica. Cada aplicación se declara en el registro (`registro.registra`) con:
  · nombre, familia y versión
  · la función que hace el trabajo (determinista)
  · su léxico: las palabras con que se pide en castellano (el LCM construye su reconocimiento a partir de ellas)
  · el concepto bajo el que entra en la base de fábrica del LCM
  · ejemplos (frase -> resultado) que la prueba de sincronía pasa por el LCM completo
Añadir una aplicación = añadir un archivo con @registra: el LCM la entiende sin tocar su código, y la prueba de sincronía la vigila.
"""
from . import registro                                   # noqa: F401
from . import mates, calendario, dibujo                  # noqa: F401  (se registran al importarse)
