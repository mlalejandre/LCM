"""Generador de datos SINTETICOS para el enrutador de operaciones (parche-87). Combina prefijos, cuerpos, sufijos y ruido (sin tildes, sin signos,
mayusculas, faltas leves) y mucho OTRO (preguntas de hechos que contienen palabras como "hora" o "dia", afirmaciones, saludos, ordenes del dialogo)
para que el modelo no se dispare con una palabra suelta. El examen CIEGO esta aparte (data/intents_ciego.tsv) y no sale de estas plantillas."""
import random

PREFIX = ["", "", "", "sabes", "oye", "dime", "me puedes decir", "puedes decirme", "podrias decirme", "una pregunta", "perdona", "por favor",
          "disculpa", "hola", "me dirias", "quiero saber", "necesito saber", "sabrias decirme", "a ver", "oye dime", "y", "entonces", "vale y"]
SUFFIX = ["", "", "", "ahora", "ahora mismo", "por favor", "gracias", "hoy", "bro", "porfa"]

BODY = {
    "HORA": ["que hora es", "que hora tienes", "la hora", "me dices la hora", "que horas son", "tienes hora", "cual es la hora", "la hora actual",
             "a que hora estamos", "hora actual", "cuantas son", "que hora marca tu reloj", "que hora es en este momento", "dime la hora",
             "tienes la hora", "que hora tenemos", "hora", "que hora indica tu reloj", "me das la hora", "sabes decirme la hora", "que hora es exactamente", "me dices que horas son"],
    "FECHA": ["que dia es hoy", "que fecha es hoy", "en que fecha estamos", "a que dia estamos", "que dia es", "que dia de la semana es hoy",
              "cual es la fecha de hoy", "a cuantos estamos", "dime la fecha", "que dia estamos", "hoy que dia es", "en que dia estamos",
              "fecha de hoy", "que mes es", "en que mes estamos", "en que ano estamos", "que ano es", "que fecha tenemos", "que dia tenemos hoy",
              "hoy es lunes o martes", "la fecha de hoy"],
    "UBICACION": ["donde estamos", "donde estas", "donde estas ahora", "en que lugar estamos", "donde nos encontramos", "en que ciudad estamos",
                  "en que pais estamos", "donde estas tu", "en que lugar estas", "donde te encuentras", "desde donde me hablas", "donde estoy",
                  "en que ciudad estoy", "donde estamos ahora mismo", "sabes donde estamos", "en que sitio estas", "en que lugar nos hallamos", "donde estamos situados", "en que sitio estamos", "donde estas situado", "en que sitio nos encontramos"],
    "IDENTIDAD": ["quien eres", "que eres", "como te llamas", "cual es tu nombre", "presentate", "quien eres tu", "como te llaman", "tu nombre",
                  "eres una persona", "eres un robot", "eres humano", "eres una ia", "quien te creo", "quien te ha hecho", "como te llamabas",
                  "dime tu nombre", "eres real", "eres un programa", "que clase de cosa eres", "tienes nombre", "que tipo de ser eres", "cual es tu identidad", "como se llama este programa", "tu como te llamas", "me dices como te llamas", "puedes presentarte", "que eres exactamente", "quien eres realmente", "quien eres tu exactamente"],
    "CAPACIDAD": ["que sabes hacer", "que puedes hacer", "para que sirves", "en que me puedes ayudar", "que sabes hacer tu", "que haces",
                  "ayudame", "que puedes hacer por mi", "que cosas sabes hacer", "con que me puedes ayudar", "como puedes ayudarme", "que haces tu",
                  "en que eres bueno", "que sabes", "que se te da bien", "para que valdrias", "que tareas haces", "que tipo de cosas haces", "cuales son tus funciones", "que puedes resolver", "que tareas puedes hacer", "para que me sirves", "de que eres capaz", "que tareas sabes resolver", "que cosas resuelves", "para que sirves tu"],
}
DATES = ["3 de febrero", "dia 3 de febrero", "el 3 de febrero", "3 de febrero de 2026", "15 de marzo", "el dia 1 de enero", "28 de febrero",
         "31 de diciembre", "dia 10 de agosto de 2024", "el 29 de febrero de 2024", "7 de julio", "dia 20 de abril", "el 12 de octubre"]
REL = ["ayer", "anteayer", "manana", "pasado manana", "antes de ayer", "mañana"]
NUM = ["2", "3", "5", "10", "15", "30", "dos", "tres", "cinco", "diez", "una semana", "7", "20", "100", "45"]
CALC = ["si hoy es {d} que dia fue {r}", "si hoy es {d} que dia sera {r}", "si estamos a {d} que dia fue {r}", "hoy es {d} cual es la fecha de {r}",
        "que dia es {r} si hoy es {d}", "si hoy es {d} que fecha fue {r}", "supon que hoy es {d} que dia fue {r}", "si hoy fuera {d} que dia seria {r}",
        "hoy es {d} y que dia fue {r}", "si hoy es {d} que dia sera dentro de {n} dias", "si hoy es {d} que dia fue hace {n} dias",
        "que dia sera dentro de {n} dias si hoy es {d}", "{n} dias despues del {d} que dia es", "{n} dias antes del {d} que dia es",
        "si hoy es {d} que dia es dentro de {n} dias", "si hoy es {d} que fecha era hace {n} dias", "si hoy es {d} que dia de la semana fue {r}",
        "estamos a {d} que dia sera {r}", "si hoy es {d} cual era la fecha de {r}"]
NAMES = ["Pedro", "Ana", "Luis", "Marta", "Juan", "Rosa", "Carlos", "Elena", "Pablo", "Sara", "Clara", "Raul", "Irene", "Hugo", "Lucia", "Nora", "Teo", "Mario"]
THINGS = ["pan", "una casa", "un coche", "el libro", "flores", "una carta", "leche", "un regalo", "una moto", "el periodico"]
CITIES = ["Madrid", "Sevilla", "Lugo", "Bilbao", "Roma", "Paris", "Cuenca", "Valencia", "Cadiz"]
VERBS = [("compro", "compra"), ("escribio", "escribe"), ("leyo", "lee"), ("vendio", "vende"), ("abrio", "abre"), ("perdio", "pierde")]
OTRO_TPL = ["que hora llego {n}", "a que hora come {n}", "a que hora sale {n} de {c}", "que dia llego {n}", "que dia compro {n} {t}",
            "cuando {v1} {n} {t}", "cuando come {n}", "donde vive {n}", "donde esta {t}", "donde estudia {n}", "donde trabaja {n}", "donde vivia {n}",
            "quien {v1} {t}", "que {v1} {n}", "quien es {n}", "que es {t}", "como se llama {t} de {n}", "como se llama el perro de {n}", "quien es el padre de {n}",
            "es {n} mas alta que {m}", "es {n} la madre de {m}", "vive {n} en {c}", "tiene {n} {t}", "cuantos hijos tiene {n}", "que sabes de {n}",
            "por que {v1} {n} {t}", "como lo sabes", "estas seguro", "repite", "que te he dicho", "que sabes de {c}", "cual es lo contrario de grande",
            "que es lo contrario de {t}", "que color es {t}", "para que sirve {t}", "que hora es el examen de {n}", "que dia nacio {n}", "en que ano nacio {n}",
            "que mes {v1} {n} {t}", "que ano {v1} {n} {t}", "donde compro {n} {t}", "en que ciudad vive {n}", "en que pais esta {c}", "como se llama {n}", "que haces {n}", "que sabes hacer con {t}", "donde estamos {n} y yo en el mapa de {c}"]
OTRO_STMT = ["{n} {v2} {t}", "{n} {v1} {t} ayer", "{n} vive en {c}", "hoy es lunes", "hoy {n} {v2} {t}", "ayer fue martes", "{n} es la profesora de {m}", "{n} esta cansada",
             "hola", "gracias", "adios", "buenos dias", "buenas tardes", "vale", "si", "no", "ok", "me llamo {n}", "soy {n}", "{n} y {m} tienen {t}", "mi perro se llama {m}",
             "el perro de {n} se llama {m}", "olvida eso", "no, {n} vive en {c}", "todos los gatos son animales", "la hora es importante", "el dia es largo",
             "{n} no vive en {c} sino en {c}", "estoy en {c}", "vivo en {c}", "{n} esta en {c}", "estamos en {c}", "ya es la hora de {n}"]

# ---- parche-88: nuevas operaciones
WORDS_N = ["dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "doce", "quince", "veinte", "treinta y cinco", "cien", "cuarenta"]
ARIT_OPS = ["mas", "menos", "por", "entre", "dividido entre", "multiplicado por", "elevado a", "+", "-", "*", "x", "/"]
ARIT_TPL = ["cuanto es {a} {o} {b}", "cuanto son {a} {o} {b}", "{a} {o} {b}", "dime cuanto es {a} {o} {b}", "calcula {a} {o} {b}", "cuanto da {a} {o} {b}",
            "resultado de {a} {o} {b}", "cuanto es {a}{o}{b}", "me dices cuanto es {a} {o} {b}", "{a} {o} {b} igual a", "cuanto vale {a} {o} {b}",
            "raiz cuadrada de {a}", "cual es la raiz de {a}", "la raiz cuadrada de {a}", "el {p} por ciento de {a}", "{p}% de {a}", "cuanto es el {p}% de {a}",
            "suma {a} y {b}", "multiplica {a} por {b}", "divide {a} entre {b}", "cuanto es el {p} por ciento de {a}", "puedes calcular {a} {o} {b}"]
DS_TPL = ["que dia de la semana fue {d}", "que dia cayo {d}", "en que dia de la semana fue {d}", "que dia de la semana sera {d}", "que dia de la semana era {d}",
          "que dia de la semana cae {d}", "dime que dia de la semana fue {d}", "sabes que dia fue {d}", "{d} que dia de la semana fue", "que dia de la semana caera {d}"]
DS_DATES = ["el 1 de enero de 2000", "el 25 de diciembre", "el 12 de octubre de 1492", "el 20 de julio de 1969", "el 3 de marzo de 2030", "el 11 de septiembre de 2001",
            "el 14 de abril de 1931", "el dia 6 de junio de 1944", "el 29 de febrero de 2024", "el 15 de agosto"]
EVENTS = ["navidad", "nochevieja", "nochebuena", "ano nuevo", "reyes", "el 25 de diciembre", "el 1 de enero", "el 12 de octubre", "el 3 de febrero de 2027", "el 31 de diciembre",
          "el 1 de enero de 2020", "el 20 de julio de 1969", "el 14 de febrero", "halloween", "el 15 de agosto"]
DH_TPL = ["cuantos dias faltan para {e}", "cuantos dias quedan para {e}", "cuanto falta para {e}", "cuantos dias hay hasta {e}", "faltan muchos dias para {e}",
          "cuantos dias han pasado desde {e}", "cuantos dias hace desde {e}", "cuantos dias llevamos desde {e}", "dime cuantos dias faltan para {e}",
          "cuantos dias nos separan de {e}", "cuanto queda hasta {e}", "faltan pocos dias para {e}"]
FUERA_BODY = ["que tiempo hace hoy", "va a llover manana", "que temperatura hace", "dame las noticias", "cuanto cuesta el bitcoin", "quien gano el partido de ayer",
              "busca en internet recetas", "pon musica", "enviame un correo", "reserva un hotel", "cual es el precio de la gasolina", "que dice el periodico hoy",
              "llama a mi madre", "traduce esto al ingles", "escribeme un poema", "cuentame un chiste", "que tiempo hara el fin de semana", "abre youtube",
              "cuanto esta el dolar", "cual es la ultima noticia", "dime el resultado del barca", "hace frio fuera", "busca un restaurante cerca", "ponme una alarma",
              "hazme una foto", "que hay en la tele", "como llego al aeropuerto", "pide una pizza", "cuanto vale una entrada de cine", "va a nevar esta semana",
              "dime el pronostico del tiempo", "que cotizacion tiene la bolsa hoy", "mandame un mensaje", "descargame una cancion", "que hora es en tokio ahora mismo", "que hora es en nueva york", "que hora es en londres", "que hora es ahora en mexico", "que hora es en roma"]
OTRO_NUM = ["{n} tiene {k} {t}", "cuantos {t} tiene {n}", "{n} compro {k} {t}", "{n} nacio el 3 de marzo", "cuando nacio {n}", "el examen es el 12 de mayo", "{n} llego el 4 de abril",
            "{n} y {m} tienen {k} {t}", "cuantos hijos tiene {n}", "{n} tiene {k} anos", "cuantos anos tiene {n}", "el cumpleanos de {n} es en enero",
            "{n} compro pan por {k} euros", "cuanto cuesta {t} que compro {n}", "{n} gana mucho", "la raiz del problema es {n}", "{n} vive entre {c} y {c}",
            "mas de {k} personas viven en {c}", "{n} es mas alta que {m}", "el dia que llego {n}", "{n} dividio el pan entre {m}"]

FUERA_V = ["pon", "reproduce", "busca", "reserva", "compra", "envia", "abre", "llama a", "descarga", "enciende", "apaga", "programa", "dime", "muestrame", "recomiendame",
           "ponme", "mandame", "pide", "cancela", "agenda"]
FUERA_O = ["una cancion", "mesa para cuatro", "un taxi", "el partido de hoy", "la champions", "un vuelo a roma", "una entrada", "el telediario", "mi correo", "una pelicula",
           "un hotel", "la radio", "el pronostico", "las noticias deportivas", "una receta de paella", "mi madre", "el bitcoin", "la luz del salon", "una cita con el medico",
           "el resultado de la liga", "un mapa de la ciudad", "una playlist", "un video de gatos", "la clasificacion", "el precio del petroleo"]
FUERA_Q = ["quien gano {x}", "cuanto cuesta {x}", "cual es el precio de {x}", "que tiempo hace en {c}", "va a llover en {c}", "hace calor en {c}", "como esta el trafico en {c}",
           "a que hora abre {x}", "cual es el resultado de {x}", "que ponen hoy en {x}"]
FUERA_X = ["el partido", "la final", "la champions", "el oro", "la gasolina", "el cine", "el super", "la liga", "el tenis", "el concierto", "el banco"]


def _noise(s: str, rng: random.Random) -> str:
    r = rng.random()
    if r < 0.25:
        s = s.lower()
    elif r < 0.35:
        s = s.upper()
    elif r < 0.45:
        s = s[:1].upper() + s[1:]
    if rng.random() < 0.4:
        s = "¿" + s + "?"
    elif rng.random() < 0.3:
        s = s + "?"
    if rng.random() < 0.08 and len(s) > 6:
        i = rng.randrange(1, len(s) - 1)
        s = s[:i] + s[i + 1:]                                  # falta de letra
    return s


def _fill(tpl: str, rng: random.Random) -> str:
    n, m = rng.sample(NAMES, 2)
    v1, v2 = rng.choice(VERBS)
    return tpl.format(n=n, m=m, t=rng.choice(THINGS), c=rng.choice(CITIES), v1=v1, v2=v2)


def generate(n_per_class: int = 650, seed: int = 7):
    rng = random.Random(seed)
    out = []
    for op, bodies in BODY.items():
        for _ in range(n_per_class):
            s = " ".join(x for x in (rng.choice(PREFIX), rng.choice(bodies), rng.choice(SUFFIX)) if x)
            out.append((_noise(s, rng), op))
    for _ in range(n_per_class + 200):
        d, r, n = rng.choice(DATES), rng.choice(REL), rng.choice(NUM)
        s = rng.choice(CALC).format(d=d, r=r, n=n)
        s = " ".join(x for x in (rng.choice(PREFIX[:12]), s) if x)
        out.append((_noise(s, rng), "CALC_FECHA"))
    for _ in range(int(n_per_class * 2.0)):
        tpl = rng.choice(OTRO_TPL)
        out.append((_noise(_fill(tpl, rng), rng), "OTRO"))
    for _ in range(int(n_per_class * 1.2)):
        out.append((_noise(_fill(rng.choice(OTRO_STMT), rng), rng), "OTRO"))
    for _ in range(n_per_class):
        a, b = rng.choice([str(rng.randrange(0, 100)), rng.choice(WORDS_N), str(rng.randrange(100, 1000))]), rng.choice([str(rng.randrange(1, 60)), rng.choice(WORDS_N)])
        s = rng.choice(ARIT_TPL).format(a=a, b=b, o=rng.choice(ARIT_OPS), p=rng.choice(["5", "10", "20", "25", "50", "diez", "veinte"]))
        s = " ".join(x for x in (rng.choice(PREFIX[:12]), s) if x)
        out.append((_noise(s, rng), "ARITMETICA"))
    for _ in range(n_per_class):
        s = rng.choice(DS_TPL).format(d=rng.choice(DS_DATES))
        s = " ".join(x for x in (rng.choice(PREFIX[:15]), s) if x)
        out.append((_noise(s, rng), "DIA_SEMANA"))
    for _ in range(n_per_class):
        s = rng.choice(DH_TPL).format(e=rng.choice(EVENTS))
        s = " ".join(x for x in (rng.choice(PREFIX[:15]), s) if x)
        out.append((_noise(s, rng), "DIAS_HASTA"))
    for _ in range(n_per_class):
        s = " ".join(x for x in (rng.choice(PREFIX[:15]), rng.choice(FUERA_BODY), rng.choice(SUFFIX[:6])) if x)
        out.append((_noise(s, rng), "FUERA"))
    for _ in range(n_per_class):
        if rng.random() < .55:
            b = rng.choice(FUERA_V) + " " + rng.choice(FUERA_O)
        else:
            b = rng.choice(FUERA_Q).format(x=rng.choice(FUERA_X), c=rng.choice(CITIES))
        out.append((_noise(" ".join(x for x in (rng.choice(PREFIX[:15]), b, rng.choice(SUFFIX[:6])) if x), rng), "FUERA"))
    for _ in range(int(n_per_class * .8)):
        n, m = rng.sample(NAMES, 2)
        v = rng.choice(["compro", "reservo", "abrio", "busco", "puso", "pidio", "llamo a", "envio", "descargo"])
        out.append((_noise(rng.choice(["{n} {v} {o}", "ayer {n} {v} {o}", "{n} y {m} {v} {o}", "quien {v} {o}", "que {v} {n}"]).format(n=n, m=m, v=v, o=rng.choice(THINGS + FUERA_O[:6])), rng), "OTRO"))
    for _ in range(int(n_per_class * 1.4)):
        k = rng.choice(["dos", "tres", "cuatro", "5", "12", "20", "una", "cien"])
        n, m = rng.sample(NAMES, 2)
        out.append((_noise(rng.choice(OTRO_NUM).format(n=n, m=m, k=k, t=rng.choice(THINGS), c=rng.choice(CITIES)), rng), "OTRO"))
    rng.shuffle(out)
    return out
