"""2.30 · MEDIDA LIMPIA de los vectores de tema. Escrita ANTES de escribir el texto de entrenamiento y sin ejecutarla.
Se mide UNA vez en 2.29 y en 2.30. Lo que se mira: que elija el sentido o la persona por el tema de lo que se habla, sin preguntar;
que siga sin preguntar cuando no hay motivo; y que aprenda del texto que le da el usuario."""
C = [
 {"id": "banco_dinero", "ctx": "sentido por el tema", "turnos": [
  ("He ido al banco a sacar dinero de mi cuenta.", ""),
  ("¿el banco es un mueble?", "^no"),
  ("¿el banco es un edificio?", "^si"),
 ]},
 {"id": "banco_parque", "ctx": "sentido por el tema", "turnos": [
  ("Me he sentado a descansar en un banco de madera del parque.", ""),
  ("¿el banco es un mueble?", "^si"),
  ("¿el banco es un edificio?", "^no"),
 ]},
 {"id": "raton_queso", "ctx": "sentido por el tema", "turnos": [
  ("Hay un ratón en la cocina y se ha comido el queso.", ""),
  ("¿el ratón es un animal?", "^si"),
  ("¿el ratón es un aparato?", "^no"),
 ]},
 {"id": "raton_pantalla", "ctx": "sentido por el tema", "turnos": [
  ("Muevo el ratón y hago clic en la pantalla.", ""),
  ("¿el ratón es un aparato?", "^si"),
  ("¿el ratón es un animal?", "^no"),
 ]},
 {"id": "carta_baraja", "ctx": "sentido por el tema", "turnos": [
  ("Hemos jugado una partida y me ha tocado una carta muy mala de la baraja.", ""),
  ("¿la carta es un juego?", "^si"),
  ("¿la carta es un documento?", "^no"),
 ]},
 {"id": "carta_correo", "ctx": "sentido por el tema", "turnos": [
  ("He escrito una carta a mi abuela y la he enviado por correo.", ""),
  ("¿la carta es un documento?", "^si"),
  ("¿la carta es un juego?", "^no"),
 ]},
 {"id": "fontanero", "ctx": "la persona por el tema de la frase", "turnos": [
  ("Mi cuñado se llama Andrés y es fontanero.", ""),
  ("Mi profesor también se llama Andrés.", ""),
  ("Mi profesor da clases de inglés.", ""),
  ("Hace días que no hablamos de ninguno de los dos.", ""),
  ("Me he apuntado a un curso de idiomas.", ""),
  ("Se ha roto una tubería del baño.", ""),
  ("¿a qué se dedica Andrés?", "fontanero"),
 ]},
 {"id": "profesor", "ctx": "la persona por el tema de la frase", "turnos": [
  ("Mi tía se llama Marta y es veterinaria.", ""),
  ("Mi jefa también se llama Marta.", ""),
  ("Mi jefa dirige una empresa de transportes.", ""),
  ("Ayer no pasó nada especial.", ""),
  ("Mi perro está enfermo y no quiere comer.", ""),
  ("¿a qué se dedica Marta?", "veterinaria"),
 ]},
 {"id": "sin_motivo", "ctx": "no preguntar cuando no hace falta", "turnos": [
  ("Tengo un gato muy tranquilo.", ""),
  ("¿mi gato es un animal?", "^si"),
  ("He comprado una copa de cristal.", ""),
  ("¿la copa es un recipiente?", "^si"),
  ("He plantado una planta en el jardín.", ""),
  ("¿la planta es un ser vivo?", "^si"),
 ]},
 {"id": "aprende_texto", "ctx": "aprender el tema de un texto del usuario", "turnos": [
  ("Te voy a leer un texto sobre los zurbos.\nLos zurbos son unos pasteles de almendra.\nLos zurbos se hornean en bandejas.\nEn la pastelería venden zurbos recién hechos.\nLos zurbos se comen de postre con el café.", ""),
  ("Mi amigo se llama Nico y es pastelero.", ""),
  ("Mi vecino también se llama Nico.", ""),
  ("Mi vecino es taxista.", ""),
  ("Hoy no he visto a nadie.", ""),
  ("Quiero encargar unos zurbos para el domingo.", ""),
  ("¿a qué se dedica Nico?", "pastelero"),
 ]},
]
