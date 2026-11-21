"""Escalera de frases escritas por mí, de la más sencilla a la más compleja, con lo que DEBE salir: verbo principal y sujeto.
Sujeto: la palabra núcleo si está dicho; "IMPL" si va implícito (se sabe por el verbo); "NO" si la oración no tiene sujeto (llueve, hay).
Sirve de comprobación independiente del corpus: son frases de conversación y de enciclopedia, que es donde falló el LCM."""
E = [
 # 1 · sujeto + verbo
 (1, "El perro ladra.", "ladra", "perro"), (1, "María canta.", "canta", "María"), (1, "Los niños juegan.", "juegan", "niños"), (1, "Llueve.", "Llueve", "NO"),
 (1, "Duermo.", "Duermo", "IMPL"), (1, "Mi hermana estudia.", "estudia", "hermana"),
 # 2 · con objeto o atributo
 (2, "El gato come pescado.", "come", "gato"), (2, "Mi tío Manuel es carpintero.", "carpintero", "tío"), (2, "Tengo un coche rojo.", "Tengo", "IMPL"),
 (2, "Hay tres libros en la mesa.", "Hay", "NO"), (2, "La casa es muy grande.", "grande", "casa"), (2, "Compramos pan esta mañana.", "Compramos", "IMPL"),
 (2, "Vive en Navarra.", "Vive", "IMPL"), (2, "Los planetas giran alrededor del Sol.", "giran", "planetas"),
 # 3 · complementos con preposición, pronombres, sujeto detrás del verbo
 (3, "A Manuel le gusta cazar jabalíes.", "gusta", "cazar"), (3, "Le gustan mucho los gatos.", "gustan", "gatos"), (3, "Ayer vino mi primo desde Sevilla con sus hijos.", "vino", "primo"),
 (3, "En el cinturón se encuentra el planeta enano Ceres.", "encuentra", "planeta"), (3, "El médico me recetó un jarabe para la tos.", "recetó", "médico"),
 (3, "Por la tarde paseamos por el parque con el perro.", "paseamos", "IMPL"), (3, "Se venden pisos en el centro.", "venden", "pisos"), (3, "Nevó durante toda la noche.", "Nevó", "NO"),
 # 4 · dos verbos, coordinación, subordinadas
 (4, "Mi tío vive en Navarra y le gusta cazar jabalíes.", "vive", "tío"), (4, "Tengo un amigo que se llama Manuel Pérez.", "Tengo", "IMPL"),
 (4, "He aprendido que mi tío Manuel es carpintero.", "aprendido", "IMPL"), (4, "Cuando llueve, los caracoles salen de sus conchas.", "salen", "caracoles"),
 (4, "El Sol es el único cuerpo celeste del sistema solar que emite luz propia.", "cuerpo", "Sol"), (4, "Quiero que vengas a casa mañana.", "Quiero", "IMPL"),
 (4, "La niña que vive enfrente tiene dos perros.", "tiene", "niña"), (4, "Me han dicho que Lucía es enfermera.", "dicho", "IMPL"),
 (4, "Júpiter y Saturno están compuestos principalmente de helio e hidrógeno.", "compuestos", "Júpiter"),
 # 5 · frases largas de enciclopedia
 (5, "El sistema solar es el sistema planetario que liga gravitacionalmente a un conjunto de objetos astronómicos que giran en una órbita alrededor de una única estrella.", "sistema", "sistema"),
 (5, "La estrella concentra la mayor parte de la masa del sistema solar, y el resto se concentra en ocho planetas cuyas órbitas son prácticamente circulares.", "concentra", "estrella"),
 (5, "Los cuatro planetas más cercanos, considerablemente más pequeños, están compuestos principalmente por roca y metal.", "compuestos", "planetas"),
 (5, "El sistema solar se formó hace unos 4600 millones de años a partir del colapso de una nube molecular.", "formó", "sistema"),
 (5, "Urano y Neptuno, denominados gigantes helados, están formados mayoritariamente por agua congelada, amoniaco y metano.", "formados", "Urano"),
 (5, "Galileo, ayudado con un nuevo invento, el telescopio, descubre que alrededor de Júpiter rotan satélites naturales.", "descubre", "Galileo"),
 (5, "Tengo un amigo que se llama Manuel Pérez al que le gustan mucho los gatos.", "Tengo", "IMPL"),
 (5, "Plutón, que fue considerado el noveno planeta del sistema solar hasta 2006, es un planeta enano.", "planeta", "Plutón"),
 (5, "Aunque algunos objetos orbitan con un gran grado de inclinación, los demás planetas giran aproximadamente en el mismo plano.", "giran", "planetas"),
]


def mide():
    from src.sintaxis.analiza import palabras
    por = {}
    fallos = []
    for niv, f, verbo, suj in E:
        ps = palabras(f)
        rz = next((p for p in ps if p["cabeza"] == 0), None)
        sub = [p for p in ps if rz and p["cabeza"] == rz["i"] and p["funcion"] in ("nsubj", "csubj")]
        okv = bool(rz) and rz["forma"].lower() == verbo.lower()
        if suj in ("IMPL", "NO"):
            oks = okv and not sub
        else:
            oks = okv and any(p["forma"].lower() == suj.lower() for p in sub)
        d = por.setdefault(niv, [0, 0, 0]); d[0] += 1; d[1] += okv; d[2] += oks
        if not (okv and oks):
            fallos.append((niv, f, verbo, suj, rz["forma"] if rz else None, [p["forma"] for p in sub]))
    return por, fallos


if __name__ == "__main__":
    por, fallos = mide()
    print("nivel  frases  verbo principal  verbo y sujeto")
    for n in sorted(por):
        a = por[n]; print(f"  {n}     {a[0]:3d}        {a[1]:3d}             {a[2]:3d}")
    t = [sum(por[n][k] for n in por) for k in range(3)]
    print(f" todo    {t[0]:3d}        {t[1]:3d}             {t[2]:3d}")
    for x in fallos:
        print("  FALLA", x)
