"""Exámenes escritos por el AUTOR del proyecto (data/*.tsv), pasados por Motor.chat. Medida independiente de mi banco."""
import sys, os, glob, datetime, json, re
from lab import banco
def corre(path):
    mo = banco.motor(); ok = n = 0; fallos = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"): continue
        if line.startswith("HOY:"):
            try: mo.mem.today = datetime.date.fromisoformat(line.split(":", 1)[1].strip())
            except ValueError: pass
            continue
        if line.startswith("---") or line.startswith("NUEVO") or line.startswith("RESET"):
            mo = banco.motor(); continue
        m = re.match(r"^(H|P|U|Q|A|R)\s*:\s*(.*)$", line)
        if not m: continue
        cuerpo = m.group(2)
        txt, _, esp = cuerpo.partition("\t")
        try: r = mo.chat(txt.strip()).get("respuesta") or ""
        except Exception as e: r = "ERR %r" % e
        if esp.strip():
            n += 1
            alts = [a.strip() for a in esp.strip().split("|") if a.strip()]
            neg = [a[1:] for a in alts if a.startswith("!")]; pos = [a for a in alts if not a.startswith("!")]
            R = banco.nr(r)
            if esp.strip() in ("SI", "NO", "NOSE"):
                bien = {"SI": bool(re.match(r"\W*si\b", R)), "NO": bool(re.match(r"\W*(no|ya no|ningun\w*)\b", R)) and not banco.abstiene(r), "NOSE": banco.abstiene(r) or "eso no me consta" in R}[esp.strip()]
            else:
                bien = (not pos or any(banco.nr(a) in R for a in pos)) and not any(banco.nr(a) in R for a in neg)
            ok += bien
            if not bien: fallos.append((txt.strip(), esp.strip(), r[:110]))
    return ok, n, fallos
if __name__ == "__main__":
    tot = [0, 0]; det = {}
    for path in sorted(glob.glob("data/*.tsv")):
        ok, n, fallos = corre(path)
        if n == 0: continue
        det[os.path.basename(path)] = (ok, n); tot[0] += ok; tot[1] += n
        print("%-28s %3d/%-3d %5.1f%%" % (os.path.basename(path), ok, n, 100 * ok / n))
        if "-v" in sys.argv:
            for f in fallos[:6]: print("      x %s | esp: %s | %s" % f)
    print("TOTAL exámenes del autor: %d/%d = %.2f%%  (nucleo20=%s)" % (tot[0], tot[1], 100 * tot[0] / tot[1], os.environ.get("LCM_NUCLEO20", "1")))
    json.dump(det, open("lab/examenes_usuario_%s.json" % os.environ.get("LCM_NUCLEO20", "1"), "w"))
