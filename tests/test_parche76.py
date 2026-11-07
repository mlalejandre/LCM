"""parche-76: arreglos simbolicos posteriores a la escuela (verbo sin complemento, relativos, nombre/verbo invertidos, sujeto pospuesto,
lemas regulares, "La madre de X es Y")."""
from src.language.extract import triples_full
from src.language.school_parser import SchoolParser

S = SchoolParser


def _tr(rows):
    return [(t["s"], t["p"], t["o"], t["neg"]) for t in triples_full(rows, entities_only=True)]


def test_verbo_con_complemento_mal_etiquetado():
    A = [("Andrés", "PROPN", 2, "nsubj", "andres"), ("cocina", "VERB", 0, "root", "cocinar"), ("pasta", "ADJ", 2, "compound", "pasta"), (".", "PUNCT", 2, "punct", ".")]
    assert _tr(S._fix_verb_complement(A)) == [("andres", "cocinar", "pasta", False)]
    P = [("Pedro", "PROPN", 2, "nsubj", "pedro"), ("cocina", "VERB", 0, "root", "cocinar"), ("pasta", "NOUN", 2, "amod", "pasta"), (".", "PUNCT", 2, "punct", ".")]
    assert _tr(S._fix_verb_complement(P)) == [("pedro", "cocinar", "pasta", False)]
    T = [("Pedro", "PROPN", 2, "nsubj", "pedro"), ("llegó", "VERB", 0, "root", "llegar"), ("tarde", "NOUN", 2, "amod", "tarde"), (".", "PUNCT", 2, "punct", ".")]
    assert S._fix_verb_complement(T)[2][3] == "amod"                  # una palabra de tiempo no es objeto


def test_relativo_con_que_mark():
    R = [("El", "DET", 2, "det", "el"), ("niño", "NOUN", 7, "nsubj", "nino"), ("que", "SCONJ", 4, "mark", "que"), ("rompió", "VERB", 2, "acl", "romper"),
         ("la", "DET", 6, "det", "el"), ("ventana", "NOUN", 4, "obj", "ventana"), ("vive", "VERB", 0, "root", "vivir"), ("en", "ADP", 9, "case", "en"),
         ("Toledo", "PROPN", 7, "obl", "toledo"), (".", "PUNCT", 7, "punct", ".")]
    assert _tr(S._fix_relative(R)) == [("nino", "romper", "ventana", False), ("nino", "vivir_en", "toledo", False)]


def test_nombre_y_verbo_invertidos():
    L = [("Lucía", "VERB", 2, "amod", "lucia"), ("cocina", "NOUN", 1, "obj", "cocina"), ("pasta", "NOUN", 2, "amod", "pasta"), ("y", "CCONJ", 7, "cc", "y"),
         ("su", "DET", 6, "det", "su"), ("hermana", "NOUN", 7, "nsubj", "hermana"), ("prepara", "VERB", 0, "root", "preparar"),
         ("ensalada", "NOUN", 7, "obj", "ensalada"), (".", "PUNCT", 7, "punct", ".")]
    got = _tr(S._fix_verb_complement(S._fix_name_noun_inverted(L)))
    assert ("lucia", "cocinar", "pasta", False) in got and ("hermana", "preparar", "ensalada", False) in got


def test_verbo_al_principio_ya_visto():
    B = [("Bebe", "NOUN", 2, "nsubj", "bebe"), ("agua", "VERB", 0, "root", "agua"), (".", "PUNCT", 2, "punct", ".")]
    assert S._fix_verb_first(B, {}) == B and S._fix_verb_first(B, {"otra": "x"}) == B       # sin evidencia no se toca
    assert _tr(S._fix_verb_first(B, {"bebe": "beber"})) == []                                    # sin sujeto: lo pone el tema del discurso
    got = triples_full(S._fix_verb_first(B, {"bebe": "beber"}), entities_only=True, default_subject="tomas")
    assert [(t["s"], t["p"], t["o"]) for t in got] == [("tomas", "beber", "agua")]


def test_sujeto_pospuesto_y_verbo_como_appos():
    G = [("una", "DET", 2, "det", "uno"), ("gaviota", "NOUN", 0, "root", "gaviota"), ("vuela", "NOUN", 2, "appos", "vuela"), (".", "PUNCT", 2, "punct", ".")]
    assert _tr(S._fix_subject_verb_appos(G)) == [("gaviota", "volar", "_", False)]
    Q = [("Vuela", "VERB", 0, "root", "volar"), ("una", "DET", 3, "det", "uno"), ("gaviota", "NOUN", 1, "obj", "gaviota"), (".", "PUNCT", 1, "punct", ".")]
    assert _tr(S._fix_inverted_subject(Q)) == [("gaviota", "volar", "_", False)]
    T = [("Tiene", "VERB", 0, "root", "tener"), ("un", "DET", 3, "det", "uno"), ("triángulo", "NOUN", 1, "obj", "triangulo"),
         ("lados", "NOUN", 3, "amod", "lado"), (".", "PUNCT", 1, "punct", ".")]
    assert S._fix_inverted_subject(T) == T                                   # el sintagma lleva mas dependientes: no es un sujeto solo


def test_vino_sara_y_flat_a_traves_del_verbo():
    V = [("Vino", "PROPN", 0, "root", "vino"), ("Sara", "PROPN", 1, "flat", "sara"), (".", "PUNCT", 1, "punct", ".")]
    assert _tr(S._fix_verb_name_inverted(V)) == [("sara", "venir", "_", False)]
    F = [("Rosa", "PROPN", 2, "nsubj", "rosa"), ("lee", "VERB", 0, "root", "leer"), ("Xqx", "PROPN", 1, "flat", "xqx"), (".", "PUNCT", 2, "punct", ".")]
    assert _tr(S._fix_flat_across_verb(F)) == [("rosa", "leer", "xqx", False)]


def test_lemas_regulares():
    assert S._lema_regular("cocina", "cocina") == "cocinar" and S._lema_regular("respira", "respir") == "respirar"
    assert S._lema_regular("cantan", "cantan") == "cantar"
    assert S._lema_regular("come", "comer") == "comer" and S._lema_regular("vive", "vivir") == "vivir" and S._lema_regular("va", "ir") == "ir"


def test_la_madre_de_x_es_y():
    M = [("La", "DET", 2, "det", "el"), ("madre", "NOUN", 6, "nsubj", "madre"), ("de", "ADP", 4, "case", "de"), ("Marcos", "PROPN", 2, "nmod", "marcos"),
         ("es", "AUX", 6, "cop", "ser"), ("Ana", "PROPN", 0, "root", "ana"), (".", "PUNCT", 6, "punct", ".")]
    assert _tr(M) == [("ana", "madre_de", "marcos", False)]
    H = [("El", "DET", 2, "det", "el"), ("hermano", "NOUN", 6, "nsubj", "hermano"), ("de", "ADP", 4, "case", "de"), ("Marcos", "PROPN", 2, "nmod", "marcos"),
         ("es", "AUX", 2, "cop", "ser"), ("Pedro", "PROPN", 0, "root", "pedro"), (".", "PUNCT", 6, "punct", ".")]
    assert _tr(H) == [("pedro", "hermano_de", "marcos", False)]
