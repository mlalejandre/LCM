"""parche-116: el lector no se cuelga con árboles de la escuela con ciclos."""
import time

from src.language.lector_ud import Arbol, ExtractorUD


def test_arbol_con_ciclos_no_se_cuelga():
    casos = [
        [("El", "DET", 1, "det", "el"), ("león", "NOUN", 3, "nsubj", "león"), ("caza", "VERB", 2, "root", "cazar"), ("presas", "NOUN", 3, "obj", "presa"), (".", "PUNCT", 9, "punct", ".")],
        [("A", "NOUN", 2, "conj", "a"), ("B", "NOUN", 3, "conj", "b"), ("C", "VERB", 1, "conj", "c"), ("D", "NOUN", 4, "obj", "d")],
        [("Goku", "PROPN", 1, "nsubj", "Goku"), ("vence", "VERB", 1, "root", "vencer"), ("a", "ADP", 4, "case", "a"), ("Freezer", "PROPN", 2, "obj", "Freezer")],
    ]
    t0 = time.time()
    for rows in casos:
        A = Arbol(rows)
        for i in range(A.n):
            assert i in A.sub(i)
        ExtractorUD().oracion(rows)
    assert time.time() - t0 < 2
