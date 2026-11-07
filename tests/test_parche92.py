"""parche-92: el examen de comprension del texto esta bien formado."""
from src.language.ingesta import preparar


def test_examen_solar_bien_formado():
    frases, _ = preparar(open("data/textos/sistema_solar.txt", encoding="utf-8").read())
    lines = [l.rstrip("\n") for l in open("data/textos/sistema_solar_examen.tsv", encoding="utf-8") if l.startswith("U:")]
    assert [l[3:].split("\t")[0] for l in lines[:len(frases)]] == frases
    preguntas = lines[len(frases):]
    assert len(preguntas) >= 20 and all(l.count("\t") == 1 and l.split("\t")[1] for l in preguntas)
