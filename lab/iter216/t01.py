N = "!no lo he entendido"
D = [{"id": "l01", "cat": "lectura", "turnos": [
 ("Te cuento una historia. El sábado Marcos fue al zoo con su prima Elsa. Vieron leones, jirafas y un oso panda. Luego comieron bocadillos en un banco. Elsa compró un peluche en la tienda porque era su cumpleaños.", N),
 ("¿con quién fue Marcos al zoo?", "elsa|prima"), ("¿qué vieron?", "leones"), ("¿qué comieron?", "bocadillos"), ("¿qué compró Elsa?", "peluche"), ("¿por qué compró un peluche?", "cumpleaños"),
 ("¿cuándo fue Marcos al zoo?", "sabado"), ("¿vieron animales?", "^si"), ("¿fueron a la playa?", "^no|ABST")]},
 {"id": "l02", "cat": "lectura", "turnos": [
 ("Lee esto: El zorro es un cánido que vive en el bosque. Tiene el hocico alargado y la cola peluda. Come ratones y fruta por la noche. Es un animal astuto y muy rápido.", N),
 ("¿dónde vive el zorro?", "bosque"), ("¿cómo tiene el hocico el zorro?", "alargado"), ("¿qué come el zorro?", "ratones"), ("¿cómo es el zorro?", "astuto|rapido"),
 ("¿el zorro tiene la cola corta?", "ABST|^no"), ("¿los cánidos viven en el bosque?", "ABST"), ("¿el zorro vuela?", "^no")]},
 {"id": "l03", "cat": "lectura", "turnos": [
 ("Escucha: Mi primo Iván trabaja de cocinero en Gijón. Tiene una hija que se llama Noa y un gato que se llama Milo. Los lunes lleva a Noa a clase de piano y los viernes cena con sus padres. El año que viene se muda a Oviedo porque quiere abrir un restaurante.", N),
 ("¿a qué se dedica Iván?", "cocinero"), ("¿cómo se llama la hija de Iván?", "noa"), ("¿quién es Milo?", "gato"), ("¿qué hace Iván los lunes?", "piano"), ("¿con quién cena Iván los viernes?", "padres"),
 ("¿adónde se muda Iván?", "oviedo"), ("¿por qué se muda?", "restaurante"), ("¿Iván tiene un animal?", "^si"), ("¿cuándo se muda?", "año")]},
 {"id": "l04", "cat": "adjetivos", "turnos": [
 ("mi perro tiene el pelo largo y las orejas caídas", N), ("¿mi perro tiene el pelo corto?", "^no"), ("¿mi perro tiene el pelo largo?", "^si"), ("¿mi perro tiene el pelo negro?", "ABST"),
 ("un tupi es un pájaro que vive en la selva", N), ("¿dónde vive un tupi?", "selva"), ("¿los pájaros viven en la selva?", "ABST|^no")]}]
