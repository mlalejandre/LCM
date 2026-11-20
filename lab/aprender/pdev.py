"""APRENDER · banco de PARÁFRASIS (desarrollo, 2.20). Los textos son los de temas ya conocidos; las preguntas son nuevas y dicen lo mismo que el
texto con OTRAS palabras (P), más preguntas-trampa (N) con una palabra emparentada pero que el texto no contesta. No es una medida a ciegas."""
from lab.aprender import dev as _D, test as _T, test2 as _T2, test3 as _T3


def _t(mod, k, extra):
    t = mod.TEMAS[k]
    return {"nombre": t["nombre"], "intro": t["intro"], "frases": [(f, []) for f, _ in t["frases"]], "extra": extra}


TEMAS = [
 _t(_D, 0, [("P", "¿quién vigila las colmenas?", "apicultor*"), ("P", "¿qué emplea el apicultor para calmar a las abejas?", "humo"), ("P", "¿dónde se almacena la miel?", "panal"),
            ("P", "¿qué transportan las abejas de una flor a otra?", "polen"), ("P", "¿cuándo fallece la abeja obrera?", "picar"), ("P", "¿qué utiliza el apicultor para tranquilizar a las abejas?", "humo"),
            ("P", "¿las abejas residen en colmenas?", "^si|colmena"), ("N", "¿quién fabrica las colmenas?", "ABST"), ("N", "¿quién descubrió la miel?", "ABST"), ("N", "¿qué beben las abejas?", "ABST")]),
 _t(_D, 1, [("P", "¿quiénes investigan los volcanes?", "vulcanologo*"), ("P", "¿qué aparatos emplean los vulcanólogos?", "sismografo*"), ("P", "¿por dónde brota la lava?", "crater"),
            ("P", "¿en qué se transforma la lava al enfriarse?", "roca"), ("P", "¿qué miden los sismógrafos?", "temblores"), ("P", "¿cuánto mide el Teide?", "3715"),
            ("N", "¿quién descubrió el Teide?", "ABST"), ("N", "¿cuánto pesa la lava?", "ABST"), ("N", "¿quién fabrica los sismógrafos?", "ABST")]),
 _t(_D, 2, [("P", "¿con cuántas piezas comienza cada jugador?", "dieciseis|16"), ("P", "¿qué pieza se desplaza en diagonal?", "alfil"), ("P", "¿qué emplean los jugadores profesionales para medir el tiempo?", "reloj"),
            ("P", "¿cuándo finaliza la partida?", "jaque mate|escapar"), ("P", "¿en qué se transforma el peón?", "dama"), ("N", "¿quién inventó el ajedrez?", "ABST"), ("N", "¿cuánto cuesta un tablero?", "ABST")]),
 _t(_T, 0, [("P", "¿qué ingieren los murciélagos?", "insectos|fruta"), ("P", "¿cuándo descansan los murciélagos?", "dia"), ("P", "¿quiénes investigan los murciélagos?", "quiropterologo*"),
            ("P", "¿cuándo salen a capturar?", "noche"), ("N", "¿quién pinta a los murciélagos?", "ABST"), ("N", "¿qué beben los murciélagos?", "ABST")]),
 _t(_T, 1, [("P", "¿dónde se tuestan los granos?", "horno"), ("P", "¿qué país fabrica más café?", "brasil"), ("P", "¿qué sustancia tiene el café?", "cafeina"),
            ("P", "¿quiénes elaboran café en las cafeterías?", "barista*"), ("P", "¿cuándo lo bebe mucha gente?", "manana"), ("P", "¿los granos tostados se trituran?", "^si|polvo|muelen"),
            ("N", "¿quién descubrió el café?", "ABST"), ("N", "¿cuánto cuesta un café?", "ABST")]),
 _t(_T2, 0, [("P", "¿dónde se edifican los faros?", "costa"), ("P", "¿dónde residía el farero?", "faro"), ("P", "¿quiénes edificaron la Torre de Hércules?", "romanos"),
             ("P", "¿para qué se utilizan los faros?", "guiar|barcos"), ("P", "¿en qué se han transformado algunos faros viejos?", "hoteles|museos"),
             ("N", "¿quién inventó el faro?", "ABST"), ("N", "¿quién derribó la Torre de Hércules?", "ABST")]),
 _t(_T2, 1, [("P", "¿cuánto demora la Luna en dar una vuelta?", "veintisiete|27"), ("P", "¿qué causa las mareas?", "luna"), ("P", "¿quién fue la primera persona que caminó sobre la Luna?", "armstrong"),
             ("P", "¿cuándo arribó Armstrong a la Luna?", "1969"), ("N", "¿hay vida en Marte?", "ABST"), ("N", "¿quién descubrió la Luna?", "ABST")]),
 _t(_T3, 0, [("P", "¿qué ingieren los pingüinos?", "peces|calamares|crustaceos"), ("P", "¿qué los resguarda del frío?", "grasa"), ("P", "¿quiénes investigan las aves?", "ornitologo*"),
             ("P", "¿quién vigila el huevo?", "macho"), ("P", "¿dónde habitan casi todos los pingüinos?", "sur|antartida"), ("N", "¿quién caza a los ornitólogos?", "ABST"), ("N", "¿qué beben los pingüinos?", "ABST")]),
 _t(_T3, 1, [("P", "¿con qué se elabora el pan?", "harina"), ("P", "¿quiénes elaboran el pan?", "panadero*"), ("P", "¿cuándo comienza a trabajar un panadero?", "madrugada"),
             ("P", "¿dónde se cocina la masa?", "horno"), ("P", "¿qué genera la levadura?", "gas"), ("P", "¿para qué se utiliza el pan duro?", "torrijas|sopas"),
             ("N", "¿quién inventó el pan?", "ABST"), ("N", "¿cuánto cuesta una barra de pan?", "ABST")]),
]
