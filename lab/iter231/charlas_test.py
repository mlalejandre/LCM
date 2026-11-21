"""2.31 · MEDIDA LIMPIA de la segunda tanda de texto. Escrita DESPUÉS de congelar el texto nuevo y sin ejecutarla.
Las palabras no las elegí yo: son las de la base de fábrica que tienen dos sentidos que se excluyen (lista sacada por programa),
quitando las cuatro usadas en el desarrollo de la 2.30 (banco, ratón, carta, copa). Muchas NO aparecen en el texto inyectado.
Se mide UNA vez en 2.30 y en 2.31."""
C = [
 {"id": "alianza_1", "ctx": "sentido por el tema", "turnos": [
  ('En la boda mi marido me puso la alianza de oro en el dedo.', ""),
  ("¿la alianza es una joya?", "^si"),
  ("¿la alianza es un acuerdo?", "^no"),
 ]},
 {"id": "alianza_2", "ctx": "sentido por el tema", "turnos": [
  ('Los dos países han firmado una alianza para ayudarse y no pelear.', ""),
  ("¿la alianza es un acuerdo?", "^si"),
  ("¿la alianza es una joya?", "^no"),
 ]},
 {"id": "bote_1", "ctx": "sentido por el tema", "turnos": [
  ('Hemos salido a remar por el lago en un bote pequeño.', ""),
  ("¿el bote es un barco?", "^si"),
  ("¿el bote es un recipiente?", "^no"),
 ]},
 {"id": "bote_2", "ctx": "sentido por el tema", "turnos": [
  ('He guardado las galletas en un bote de cristal con tapa.', ""),
  ("¿el bote es un recipiente?", "^si"),
  ("¿el bote es un barco?", "^no"),
 ]},
 {"id": "caqui_1", "ctx": "sentido por el tema", "turnos": [
  ('De postre me he comido un caqui maduro y muy dulce.', ""),
  ("¿el caqui es una fruta?", "^si"),
  ("¿el caqui es un color?", "^no"),
 ]},
 {"id": "caqui_2", "ctx": "sentido por el tema", "turnos": [
  ('He pintado la pared de caqui y combina bien con el verde.', ""),
  ("¿el caqui es un color?", "^si"),
  ("¿el caqui es una fruta?", "^no"),
 ]},
 {"id": "cometa_1", "ctx": "sentido por el tema", "turnos": [
  ('Los niños vuelan una cometa de papel en la playa con el viento.', ""),
  ("¿la cometa es un juguete?", "^si"),
  ("¿la cometa es un astro?", "^no"),
 ]},
 {"id": "cometa_2", "ctx": "sentido por el tema", "turnos": [
  ('Anoche con el telescopio vimos un cometa cruzando el cielo entre las estrellas.', ""),
  ("¿la cometa es un astro?", "^si"),
  ("¿la cometa es un juguete?", "^no"),
 ]},
 {"id": "cubo_1", "ctx": "sentido por el tema", "turnos": [
  ('He llenado el cubo de agua para fregar el suelo.', ""),
  ("¿el cubo es un recipiente?", "^si"),
  ("¿el cubo es una forma?", "^no"),
 ]},
 {"id": "cubo_2", "ctx": "sentido por el tema", "turnos": [
  ('En clase de geometría hemos dibujado un cubo con sus seis caras cuadradas.', ""),
  ("¿el cubo es una forma?", "^si"),
  ("¿el cubo es un recipiente?", "^no"),
 ]},
 {"id": "estrella_1", "ctx": "sentido por el tema", "turnos": [
  ('De noche miramos una estrella que brillaba mucho en el cielo junto a la luna.', ""),
  ("¿la estrella es un astro?", "^si"),
  ("¿la estrella es una forma?", "^no"),
 ]},
 {"id": "estrella_2", "ctx": "sentido por el tema", "turnos": [
  ('He recortado una estrella de cinco puntas en cartulina, y también un círculo y un cuadrado.', ""),
  ("¿la estrella es una forma?", "^si"),
  ("¿la estrella es un astro?", "^no"),
 ]},
 {"id": "flamenco_1", "ctx": "sentido por el tema", "turnos": [
  ('En el lago vimos un flamenco rosa de patas largas metiendo el pico en el agua.', ""),
  ("¿el flamenco es un ave?", "^si"),
  ("¿el flamenco es un baile?", "^no"),
 ]},
 {"id": "flamenco_2", "ctx": "sentido por el tema", "turnos": [
  ('Mi prima baila flamenco con la guitarra y las palmas en la fiesta.', ""),
  ("¿el flamenco es un baile?", "^si"),
  ("¿el flamenco es un ave?", "^no"),
 ]},
 {"id": "granada_1", "ctx": "sentido por el tema", "turnos": [
  ('He pelado una granada y me he comido sus granos rojos de postre.', ""),
  ("¿la granada es una fruta?", "^si"),
  ("¿la granada es un arma?", "^no"),
 ]},
 {"id": "granada_2", "ctx": "sentido por el tema", "turnos": [
  ('El soldado lanzó una granada y explotó en la guerra.', ""),
  ("¿la granada es un arma?", "^si"),
  ("¿la granada es una fruta?", "^no"),
 ]},
 {"id": "lima_1", "ctx": "sentido por el tema", "turnos": [
  ('El carpintero alisa el borde del metal con una lima de acero.', ""),
  ("¿la lima es una herramienta?", "^si"),
  ("¿la lima es una fruta?", "^no"),
 ]},
 {"id": "lima_2", "ctx": "sentido por el tema", "turnos": [
  ('He exprimido una lima verde para echar su zumo ácido en la bebida.', ""),
  ("¿la lima es una fruta?", "^si"),
  ("¿la lima es una herramienta?", "^no"),
 ]},
 {"id": "naranja_1", "ctx": "sentido por el tema", "turnos": [
  ('He pelado una naranja y he exprimido su zumo para desayunar.', ""),
  ("¿la naranja es una fruta?", "^si"),
  ("¿la naranja es un color?", "^no"),
 ]},
 {"id": "naranja_2", "ctx": "sentido por el tema", "turnos": [
  ('He pintado la puerta de naranja, entre el rojo y el amarillo.', ""),
  ("¿la naranja es un color?", "^si"),
  ("¿la naranja es una fruta?", "^no"),
 ]},
 {"id": "palmera_1", "ctx": "sentido por el tema", "turnos": [
  ('En la playa hay una palmera muy alta con hojas largas que da sombra.', ""),
  ("¿la palmera es un árbol?", "^si"),
  ("¿la palmera es un dulce?", "^no"),
 ]},
 {"id": "palmera_2", "ctx": "sentido por el tema", "turnos": [
  ('En la pastelería he comprado una palmera de chocolate para merendar.', ""),
  ("¿la palmera es un dulce?", "^si"),
  ("¿la palmera es un árbol?", "^no"),
 ]},
 {"id": "regla_1", "ctx": "sentido por el tema", "turnos": [
  ('He medido el papel con la regla y he trazado una línea recta con el lápiz.', ""),
  ("¿la regla es una herramienta?", "^si"),
  ("¿la regla es una norma?", "^no"),
 ]},
 {"id": "regla_2", "ctx": "sentido por el tema", "turnos": [
  ('En este juego hay una regla que todos los jugadores deben cumplir.', ""),
  ("¿la regla es una norma?", "^si"),
  ("¿la regla es una herramienta?", "^no"),
 ]},
 {"id": "rosa_1", "ctx": "sentido por el tema", "turnos": [
  ('El jardinero ha cortado una rosa del rosal con cuidado de las espinas.', ""),
  ("¿la rosa es una flor?", "^si"),
  ("¿la rosa es un color?", "^no"),
 ]},
 {"id": "rosa_2", "ctx": "sentido por el tema", "turnos": [
  ('He pintado la habitación de rosa, un tono suave entre el rojo y el blanco.', ""),
  ("¿la rosa es un color?", "^si"),
  ("¿la rosa es una flor?", "^no"),
 ]},
 {"id": "salmon_1", "ctx": "sentido por el tema", "turnos": [
  ('El pescador ha pescado un salmón enorme en el río con su caña.', ""),
  ("¿el salmón es un pez?", "^si"),
  ("¿el salmón es un color?", "^no"),
 ]},
 {"id": "salmon_2", "ctx": "sentido por el tema", "turnos": [
  ('He elegido una camisa de color salmón, parecido al rosa y al naranja.', ""),
  ("¿el salmón es un color?", "^si"),
  ("¿el salmón es un pez?", "^no"),
 ]},
 {"id": "salsa_1", "ctx": "sentido por el tema", "turnos": [
  ('He echado salsa de tomate a la pasta antes de servirla en el plato.', ""),
  ("¿la salsa es un alimento?", "^si"),
  ("¿la salsa es un baile?", "^no"),
 ]},
 {"id": "salsa_2", "ctx": "sentido por el tema", "turnos": [
  ('Los sábados vamos a bailar salsa con música en la academia.', ""),
  ("¿la salsa es un baile?", "^si"),
  ("¿la salsa es un alimento?", "^no"),
 ]},
 {"id": "zapatero_1", "ctx": "sentido por el tema", "turnos": [
  ('He llevado las botas rotas al zapatero para que les arregle la suela.', ""),
  ("¿el zapatero es un profesional?", "^si"),
  ("¿el zapatero es un mueble?", "^no"),
 ]},
 {"id": "zapatero_2", "ctx": "sentido por el tema", "turnos": [
  ('Al entrar en casa dejo los zapatos en el zapatero de madera del recibidor, junto al armario.', ""),
  ("¿el zapatero es un mueble?", "^si"),
  ("¿el zapatero es un profesional?", "^no"),
 ]},
 {"id": "flecha_1", "ctx": "sentido por el tema", "turnos": [
  ('El arquero disparó una flecha con su arco y dio en el blanco.', ""),
  ("¿la flecha es un arma?", "^si"),
  ("¿la flecha es una forma?", "^no"),
 ]},
 {"id": "flecha_2", "ctx": "sentido por el tema", "turnos": [
  ('En el cartel hay dibujada una flecha que señala la salida, junto a un círculo y un triángulo.', ""),
  ("¿la flecha es una forma?", "^si"),
  ("¿la flecha es un arma?", "^no"),
 ]},
 {"id": "p_mecanico", "ctx": "la persona por el tema de la frase", "turnos": [
  ('Mi primo se llama Raúl y es mecánico.', ""),
  ('Mi vecino también se llama Raúl.', ""),
  ('Mi vecino es cocinero.', ""),
  ('Esta semana ha hecho mucho calor.', ""),
  ('Mi coche hace un ruido raro y no arranca.', ""),
  ('¿a qué se dedica Raúl?', 'mecanico'),
 ]},
 {"id": "p_medica", "ctx": "la persona por el tema de la frase", "turnos": [
  ('Mi hermana se llama Elena y es médica.', ""),
  ('Mi compañera de piso también se llama Elena.', ""),
  ('Mi compañera de piso es abogada.', ""),
  ('El domingo estuve en casa.', ""),
  ('Tengo fiebre y me duele mucho la garganta.', ""),
  ('¿a qué se dedica Elena?', 'medica'),
 ]},
 {"id": "p_peluquero", "ctx": "la persona por el tema de la frase", "turnos": [
  ('Mi tío se llama Julio y es carpintero.', ""),
  ('Mi amigo también se llama Julio.', ""),
  ('Mi amigo es peluquero.', ""),
  ('Ayer llovió toda la tarde.', ""),
  ('Tengo el pelo muy largo y quiero cortármelo.', ""),
  ('¿a qué se dedica Julio?', 'peluquero'),
 ]},
 {"id": "p_jardinera", "ctx": "la persona por el tema de la frase", "turnos": [
  ('Mi prima se llama Rosa y es jardinera.', ""),
  ('Mi jefa también se llama Rosa.', ""),
  ('Mi jefa es contable.', ""),
  ('No tengo planes para mañana.', ""),
  ('Se me han secado las plantas del balcón y no sé cómo regarlas.', ""),
  ('¿a qué se dedica Rosa?', 'jardinera'),
 ]},
 {"id": "p_maestro", "ctx": "la persona por el tema de la frase", "turnos": [
  ('Mi cuñado se llama Tomás y es camionero.', ""),
  ('Mi vecino también se llama Tomás.', ""),
  ('Mi vecino es maestro.', ""),
  ('Hoy me he levantado temprano.', ""),
  ('Mi hijo no entiende la lección y tiene un examen en el colegio.', ""),
  ('¿a qué se dedica Tomás?', 'maestro'),
 ]},
 {"id": "sin_motivo", "ctx": "no preguntar cuando no hace falta", "turnos": [
  ('He comprado una silla nueva.', ""),
  ('¿la silla es un mueble?', '^si'),
  ('Tengo un perro que ladra mucho.', ""),
  ('¿mi perro es un animal?', '^si'),
  ('He comido una manzana.', ""),
  ('¿la manzana es una fruta?', '^si'),
  ('Me he comprado un martillo.', ""),
  ('¿el martillo es una herramienta?', '^si'),
 ]},
]
