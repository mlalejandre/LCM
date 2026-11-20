from lab.imagenes import png, img, figura
D = [{"id": "k19", "cat": "libre", "turnos": [
 ("hola", "hola"), ("estoy organizando la fiesta de cumpleaños de mi hijo", "fiesta;hijo;!no lo he entendido"), ("cumple cinco años el viernes", "cinco;viernes;!no lo he entendido"),
 ("vendrán diez niños de su clase", "diez|10;!no lo he entendido"), (img("estos son los globos que he comprado", png("azul")), "azul*;globos;!no lo he entendido"),
 ("¿de qué color son los globos?", "azul*"), ("¿cuántos niños vendrán?", "diez|10"), ("¿cuándo cumple años mi hijo?", "viernes"),
 ("¿qué estoy organizando?", "fiesta"), ("¿cuántos años cumple mi hijo?", "cinco|5")]}]
