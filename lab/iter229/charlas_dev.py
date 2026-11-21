"""2.29 · DESARROLLO: probabilidad por contexto con una caché corta. Tocayos y sentidos de palabras."""
C = [
 {"id": "pedros", "ctx": "de quién se venía hablando", "turnos": [
  ("Mi hermano se llama Pedro y vive en Cádiz.", ""),
  ("Mi vecino también se llama Pedro.", ""),
  ("El vecino Pedro es fontanero.", ""),
  ("Ayer hablé con mi vecino.", ""),
  ("¿a qué se dedica Pedro?", "fontanero"),
  ("Mi hermano viene mañana a comer.", ""),
  ("¿dónde vive Pedro?", "cadiz"),
  ("Tengo una fuga en el grifo.", ""),
  ("He llamado al fontanero.", ""),
  ("¿quién es fontanero?", "vecino"),
 ]},
 {"id": "pedros_duda", "ctx": "sin contexto se pregunta", "turnos": [
  ("Mi primo se llama Carlos.", ""),
  ("Mi jefe también se llama Carlos.", ""),
  ("¿dónde vive Carlos?", "que carlos|cual"),
  ("mi primo", ""),
  ("Carlos vive en Jaén.", ""),
  ("¿dónde vive mi primo?", "jaen"),
  ("¿dónde vive mi jefe?", "ABST"),
 ]},
 {"id": "raton", "ctx": "el sentido por lo que se dice alrededor", "turnos": [
  ("He comprado un ratón para el ordenador.", ""),
  ("¿el ratón es un animal?", "^no"),
  ("¿el ratón es un aparato?", "^si"),
 ]},
 {"id": "copa", "ctx": "preguntar, aprender y no volver a preguntar", "turnos": [
  ("He ganado una copa en el torneo de tenis.", ""),
  ("¿mi copa es un premio?", "^si|varios sentidos|cual"),   # 2.30: con los vectores de tema ya no hace falta preguntar («torneo» va con «premio»)
  ("premio", ""),
  ("¿mi copa es un recipiente?", "^no"),
  ("Mi hermano ha ganado otra copa en el torneo.", ""),
  ("¿la copa es un premio?", "^si"),
 ]},
 {"id": "defecto", "ctx": "sin nada en contra, el sentido de siempre y sin preguntar", "turnos": [
  ("Tengo una planta en el salón.", ""),
  ("¿mi planta es un ser vivo?", "^si"),
  ("Tengo un gato.", ""),
  ("¿mi gato es un animal?", "^si"),
  ("Tengo un banco en el jardín.", ""),
  ("¿mi banco es un mueble?", "^si"),
 ]},
]
