import json,gzip,sys
from src.nucleo20 import vectores as V
from src.nucleo20.morfo import sa
w2s,hyp=V._grafo()
D=json.load(gzip.open("data/definiciones.json.gz","rt"))
C=json.load(gzip.open("data/conceptos.json.gz","rt"))
gl={int(k):set(x for x in v if x is not None) for k,v in D["gl"].items()}
L=json.load(open("data/lexico_es.json")); pos={int(k):v for k,v in L["pos"].items()}; syn={int(k):v for k,v in L["syn"].items()}
def anc(s,n):
    out={s}; f={s}
    for _ in range(n):
        f={p for x in f for p in hyp.get(x,())}; out|=f
    return out
def ev(a,b):
    A,B=w2s.get(sa(a),set()),w2s.get(sa(b),set())
    r={}
    r["par"]=V.parentesco(a,b); r["vec"]=round(V.sim(a,b),2); r["pte"]=V.puente(a,b); r["2p"]=V.dos_pasos(a,b)
    r["hyp2"]=bool({p for s in A for p in anc(s,2)}&B or {p for s in B for p in anc(s,2)}&A)
    pa={p for s in A for p in hyp.get(s,())}; pb={p for s in B for p in hyp.get(s,())}
    r["herm"]=len(pa&pb)
    r["glosa"]=(sum(1 for s in A if gl.get(s,set())&B), sum(1 for s in B if gl.get(s,set())&A))
    return r
if __name__=="__main__":
    for p in sys.argv[1:]:
        a,b=p.split("/"); print(p, len(w2s.get(sa(a),())), len(w2s.get(sa(b),())), ev(a,b))
