"""Lectura de libros para el oido (parche-17): RTF -> texto -> frases limpias."""
import re
import unicodedata

_SKIP_DEST = {"fonttbl", "colortbl", "stylesheet", "info", "pict", "header", "footer", "expandedcolortbl", "listtable",
              "listoverridetable", "generator", "themedata", "colorschememapping", "latentstyles", "datastore"}


def rtf_to_text(data: str, codepage: str = "cp1252") -> str:
    """Convierte RTF a texto plano sin dependencias (escapes \\'hh, \\uN, grupos de destino, \\par)."""
    # En RTF, "\\" + salto de linea es un \par; aqui los libros vienen con las lineas cortadas a mano:
    # una sola es un salto duro (espacio) y una linea en blanco separa parrafos.
    data = re.sub(r"(?:\\\r?\n[ \t]*){2,}", lambda m: "\\par ", data)
    data = re.sub(r"\\\r?\n", lambda m: " ", data)
    m = re.search(r"\\ansicpg(\d+)", data[:2000])
    if m:
        codepage = "cp" + m.group(1)
    out, i, n = [], 0, len(data)
    stack = []           # (saltando, uc)
    skipping, uc = False, 1
    pending_skip = 0
    while i < n:
        c = data[i]
        if c == "{":
            stack.append((skipping, uc))
            i += 1
            # destino: {\* ...} o {\fonttbl ...}
            m = re.match(r"\\\*|\\([a-zA-Z]+)", data[i:i + 40])
            if m and (m.group(0) == "\\*" or m.group(1) in _SKIP_DEST):
                skipping = True
            continue
        if c == "}":
            if stack:
                skipping, uc = stack.pop()
            i += 1
            continue
        if c == "\\":
            i += 1
            if i >= n:
                break
            d = data[i]
            if d in "\\{}":
                if not skipping and not pending_skip:
                    out.append(d)
                pending_skip = max(0, pending_skip - 1) if pending_skip else 0
                i += 1
            elif d == "'":
                hexa = data[i + 1:i + 3]
                i += 3
                if pending_skip:
                    pending_skip -= 1
                elif not skipping:
                    try:
                        out.append(bytes([int(hexa, 16)]).decode(codepage, errors="replace"))
                    except ValueError:
                        pass
            elif d == "~":
                out.append(" "); i += 1
            elif d in "-_":
                i += 1
            elif d.isalpha():
                m = re.match(r"([a-zA-Z]+)(-?\d+)? ?", data[i:])
                word, num = m.group(1), m.group(2)
                i += m.end()
                if skipping:
                    continue
                if word in ("par", "line", "sect", "page"):
                    out.append("\n")
                elif word == "tab":
                    out.append(" ")
                elif word == "uc" and num is not None:
                    uc = int(num)
                elif word == "u" and num is not None:
                    v = int(num)
                    out.append(chr(v + 65536 if v < 0 else v))
                    pending_skip = uc
                elif word in ("emdash",):
                    out.append("—")
                elif word in ("endash",):
                    out.append("–")
                elif word in ("lquote", "rquote"):
                    out.append("'")
                elif word in ("ldblquote", "rdblquote"):
                    out.append('"')
            else:
                i += 1
            continue
        if c in "\r\n":              # salto de linea "duro" del archivo: separa palabras (no es parrafo)
            if not skipping and out and out[-1] not in (" ", "\n"):
                out.append(" ")
            i += 1
            continue
        if not skipping:
            if pending_skip:
                pending_skip -= 1
            else:
                out.append(c)
        i += 1
    return "".join(out)


def clean(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u00a0", " ").replace("«", '"').replace("»", '"').replace("“", '"').replace("”", '"')
    text = re.sub(r"[ \t]+", " ", text)
    return text


def sentences(text: str, max_words: int = 30):
    """Frases sueltas. Las muy largas (Claudin escribe periodos enormes) se parten en clausulas por , ; :"""
    out = []
    for para in re.split(r"\n+", clean(text)):
        para = para.strip()
        if not para:
            continue
        para = re.sub(r"\s*[—–]\s*", " , ", para)           # guion de dialogo -> coma (aprox.)
        for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡\"—])", para):
            s = s.strip(" ,\"")
            n = len(s.split())
            if 4 <= n <= max_words:
                out.append(s)
            elif n > max_words:
                for clause in re.split(r"\s*[,;:]\s*", s):
                    clause = clause.strip(" \"")
                    if 4 <= len(clause.split()) <= max_words:
                        out.append(clause)
    return out
