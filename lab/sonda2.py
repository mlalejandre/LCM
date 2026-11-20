import sys, traceback
from lab import banco
from src.nucleo20 import lengua as G
def run(frases):
    mo = banco.motor(); n = mo._nucleo20()
    orig = n._una
    def una(p):
        try: return orig(p)
        except Exception: traceback.print_exc(); raise
    n._una = una
    for q in frases:
        r = mo.chat(q)
        T = G.tokens(mo.parser, q)
        print("> %s\n   [%s] %s" % (q, r.get('nucleo20', 'CAPAS'), r.get('respuesta')))
        if 'nucleo20' not in r or '-t' in sys.argv: print("   ", [(t.f, t.pos, t.lem) for t in T])
if __name__ == "__main__":
    run([l.strip() for l in sys.stdin if l.strip()])
