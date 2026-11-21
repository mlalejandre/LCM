"""2.31 · SEGUNDA MEDIDA LIMPIA, escrita con el código ya congelado y sin ejecutarla. La primera se usó para desarrollar (dejó de ser ciega).
Palabras de la misma lista sacada por programa, que no estaban ni en la primera medida ni en el desarrollo. Se mide UNA vez en 2.30 y en 2.31."""
C = [
 {"id": "violeta_1", "ctx": "sentido por el tema", "turnos": [
  ('He cogido una violeta del jardín y huele muy bien entre las otras flores.', ""),
  ("¿la violeta es una flor?", "^si"),
  ("¿la violeta es un color?", "^no"),
 ]},
 {"id": "violeta_2", "ctx": "sentido por el tema", "turnos": [
  ('He pintado el techo de violeta, un tono entre el azul y el rojo.', ""),
  ("¿la violeta es un color?", "^si"),
  ("¿la violeta es una flor?", "^no"),
 ]},
 {"id": "lila_1", "ctx": "sentido por el tema", "turnos": [
  ('En primavera la lila del jardín se llena de flores y de abejas.', ""),
  ("¿la lila es una flor?", "^si"),
  ("¿la lila es un color?", "^no"),
 ]},
 {"id": "lila_2", "ctx": "sentido por el tema", "turnos": [
  ('Mi hermana lleva una bufanda de color lila, parecido al morado.', ""),
  ("¿la lila es un color?", "^si"),
  ("¿la lila es una flor?", "^no"),
 ]},
 {"id": "mostaza_1", "ctx": "sentido por el tema", "turnos": [
  ('He puesto mostaza y sal en la carne para darle sabor.', ""),
  ("¿la mostaza es un condimento?", "^si"),
  ("¿la mostaza es un color?", "^no"),
 ]},
 {"id": "mostaza_2", "ctx": "sentido por el tema", "turnos": [
  ('He comprado un jersey de color mostaza, un amarillo oscuro.', ""),
  ("¿la mostaza es un color?", "^si"),
  ("¿la mostaza es un condimento?", "^no"),
 ]},
 {"id": "pollo_1", "ctx": "sentido por el tema", "turnos": [
  ('He asado el pollo en el horno con patatas para cenar.', ""),
  ("¿el pollo es una carne?", "^si"),
  ("¿el pollo es un ave?", "^no"),
 ]},
 {"id": "pollo_2", "ctx": "sentido por el tema", "turnos": [
  ('En el corral un pollo picotea el suelo junto a la gallina y mueve las alas.', ""),
  ("¿el pollo es un ave?", "^si"),
  ("¿el pollo es una carne?", "^no"),
 ]},
 {"id": "conejo_1", "ctx": "sentido por el tema", "turnos": [
  ('En el monte vimos un conejo que salía de su madriguera y comía hierba.', ""),
  ("¿el conejo es un mamífero?", "^si"),
  ("¿el conejo es una carne?", "^no"),
 ]},
 {"id": "conejo_2", "ctx": "sentido por el tema", "turnos": [
  ('He guisado el conejo con ajo y cebolla en la cazuela y lo he servido en platos.', ""),
  ("¿el conejo es una carne?", "^si"),
  ("¿el conejo es un mamífero?", "^no"),
 ]},
 {"id": "cine_1", "ctx": "sentido por el tema", "turnos": [
  ('Han construido un cine nuevo de tres pisos en la plaza, al lado del hotel.', ""),
  ("¿el cine es un edificio?", "^si"),
  ("¿el cine es un arte?", "^no"),
 ]},
 {"id": "cine_2", "ctx": "sentido por el tema", "turnos": [
  ('Me gusta el cine tanto como la pintura, la escultura y la música.', ""),
  ("¿el cine es un arte?", "^si"),
  ("¿el cine es un edificio?", "^no"),
 ]},
 {"id": "teatro_1", "ctx": "sentido por el tema", "turnos": [
  ('El albañil está arreglando la fachada y el tejado del teatro viejo.', ""),
  ("¿el teatro es un edificio?", "^si"),
  ("¿el teatro es un arte?", "^no"),
 ]},
 {"id": "teatro_2", "ctx": "sentido por el tema", "turnos": [
  ('Estudio teatro y literatura porque me gustan la poesía y la pintura.', ""),
  ("¿el teatro es un arte?", "^si"),
  ("¿el teatro es un edificio?", "^no"),
 ]},
 {"id": "policia_1", "ctx": "sentido por el tema", "turnos": [
  ('La policía es una organización grande con muchas comisarías y jefes en todo el país.', ""),
  ("¿la policía es una organización?", "^si"),
  ("¿la policía es un profesional?", "^no"),
 ]},
 {"id": "policia_2", "ctx": "sentido por el tema", "turnos": [
  ('Mi tía es policía y trabaja de noche igual que un médico o un bombero.', ""),
  ("¿la policía es un profesional?", "^si"),
  ("¿la policía es una organización?", "^no"),
 ]},
 {"id": "chocolate_1", "ctx": "sentido por el tema", "turnos": [
  ('He mordido una tableta de chocolate con almendras de postre.', ""),
  ("¿el chocolate es un dulce?", "^si"),
  ("¿el chocolate es una bebida?", "^no"),
 ]},
 {"id": "chocolate_2", "ctx": "sentido por el tema", "turnos": [
  ('Me he bebido una taza de chocolate caliente para desayunar.', ""),
  ("¿el chocolate es una bebida?", "^si"),
  ("¿el chocolate es un dulce?", "^no"),
 ]},
 {"id": "radio_1", "ctx": "sentido por el tema", "turnos": [
  ('He enchufado la radio y le he cambiado las pilas porque no se encendía.', ""),
  ("¿la radio es un aparato?", "^si"),
  ("¿la radio es un medio de comunicación?", "^no"),
 ]},
 {"id": "radio_2", "ctx": "sentido por el tema", "turnos": [
  ('Las noticias llegan por la radio, por la prensa y por la televisión.', ""),
  ("¿la radio es un medio de comunicación?", "^si"),
  ("¿la radio es un aparato?", "^no"),
 ]},
 {"id": "p_electricista", "ctx": "la persona por el tema de la frase", "turnos": [
  ('Mi tío se llama Ramón y es electricista.', ""),
  ('Mi amigo también se llama Ramón.', ""),
  ('Mi amigo es panadero.', ""),
  ('El lunes fue un día normal.', ""),
  ('Se ha ido la luz y un enchufe echa chispas.', ""),
  ('¿a qué se dedica Ramón?', 'electricista'),
 ]},
 {"id": "p_panadero", "ctx": "la persona por el tema de la frase", "turnos": [
  ('Mi tío se llama Ramón y es electricista.', ""),
  ('Mi amigo también se llama Ramón.', ""),
  ('Mi amigo es panadero.', ""),
  ('El lunes fue un día normal.', ""),
  ('Quiero comprar pan recién hecho y unos bollos.', ""),
  ('¿a qué se dedica Ramón?', 'panadero'),
 ]},
 {"id": "p_dentista", "ctx": "la persona por el tema de la frase", "turnos": [
  ('Mi vecina se llama Clara y es dentista.', ""),
  ('Mi prima también se llama Clara.', ""),
  ('Mi prima es taxista.', ""),
  ('No he salido de casa.', ""),
  ('Me duele una muela desde ayer.', ""),
  ('¿a qué se dedica Clara?', 'dentista'),
 ]},
 {"id": "p_carpintero", "ctx": "la persona por el tema de la frase", "turnos": [
  ('Mi suegro se llama Felipe y es carpintero.', ""),
  ('Mi compañero también se llama Felipe.', ""),
  ('Mi compañero es pintor.', ""),
  ('Hoy hace buen día.', ""),
  ('Necesito una mesa de madera a medida.', ""),
  ('¿a qué se dedica Felipe?', 'carpintero'),
 ]},
 {"id": "sin_motivo", "ctx": "no preguntar cuando no hace falta", "turnos": [
  ('He comprado un sofá.', ""),
  ('¿el sofá es un mueble?', '^si'),
  ('Tengo un canario.', ""),
  ('¿mi canario es un animal?', '^si'),
 ]},
]
