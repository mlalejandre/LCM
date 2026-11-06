"""Lexico del oido: normalizacion del texto, frases de los predicados y trozos de vocabulario."""
import re
import unicodedata

PREPS = {"de", "a", "que", "con", "en", "por", "para", "sobre", "entre", "hacia"}
NO_EAR = {"ES", "SIN_CONCLUSION", "NINGUNA", "REGLA_HEREDA"}
ES_ALIASES = ["es un", "es una", "son", "era un", "era una", "eran"]   # "ES" se reconoce por estos giros

# (frase, tipo)  A = "es <frase>" (nombre/adjetivo + preposicion) | V = verbo
BASE_PHRASES = {
    "MAYOR_QUE": ("mayor que", "A"), "MENOR_QUE": ("menor que", "A"), "SUPERIOR_A": ("superior a", "A"),
    "ANTERIOR_A": ("anterior a", "A"), "POSTERIOR_A": ("posterior a", "A"),
    "CAUSA": ("causa", "V"), "PRODUCE": ("produce", "V"), "PROVOCA": ("provoca", "V"), "ORIGINA": ("origina", "V"),
    "POSEE": ("posee", "V"), "EXHIBE": ("exhibe", "V"), "MUESTRA": ("muestra", "V"), "ADQUIERE": ("adquiere", "V"),
    "HEREDA": ("hereda", "V"), "IMPLICA": ("implica", "V"), "TIENE_RASGO": ("tiene como rasgo", "V"),
    "DERIVA_EN": ("deriva en", "V"), "CAE_HACIA": ("cae hacia", "V"), "EXPUESTO_A": ("expuesto a", "A"),
    "SOMETIDO_A": ("sometido a", "A"), "LIBERADO_EN": ("liberado en", "A"), "CAMBIA_A": ("cambia a", "V"),
    "CONTRADICE": ("contradice", "V"), "TIENE_BIYECCION_CON": ("tiene biyeccion con", "V"),
}


def norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def tokenize(text: str):
    t = re.sub(r"\bdel\b", "de el", norm(text))
    t = re.sub(r"\bal\b", "a el", t)
    return re.findall(r"[a-z0-9_]+|[,.;:!?]", t)


def phrase_for(name: str):
    """Frase y tipo de un predicado. Si no esta en la tabla se deriva del nombre (PADRE_DE -> 'padre de')."""
    if name in BASE_PHRASES:
        return BASE_PHRASES[name]
    words = name.lower().split("_")
    kind = "A" if len(words) >= 2 and words[-1] in PREPS else "V"
    return " ".join(words), kind
