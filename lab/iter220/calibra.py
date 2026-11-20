import sys,json,random,gzip,time; sys.path.insert(0,'.')
from src.nucleo20.morfo import sa
import torch, warnings; warnings.simplefilter("ignore")
L=json.load(open("data/lexico_es.json"))
syn={int(k):[sa(w.lower()) for w in v if " " not in w and sa(w.lower()).isalpha()] for k,v in L["syn"].items()}; pos=L["pos"]
hyp={int(k):[int(x) for x in v] for k,v in L["hyp"].items()}
hijos={}
for k,ps in hyp.items():
    for p in ps: hijos.setdefault(p,[]).append(k)
pal=sorted({w for ws in syn.values() for w in ws}); idx={w:i for i,w in enumerate(pal)}
def entrena(dim, a_hip, niter=6):
    W={}
    def suma(a,b,v):
        if a!=b:
            k=(idx[a],idx[b]) if idx[a]<idx[b] else (idx[b],idx[a]); W[k]=max(W.get(k,0),v)
    for s,ws in syn.items():
        for i in range(len(ws)):
            for j in range(i+1,len(ws)): suma(ws[i],ws[j],1.0)
        if a_hip:
            for p in hyp.get(s,[]):
                for a in ws:
                    for b in syn.get(p,[]): suma(a,b,a_hip)
    ii=[];vv=[]
    for (a,b),v in W.items(): ii+= [(a,b),(b,a)]; vv+=[v,v]
    n=len(pal)
    A=torch.sparse_coo_tensor(torch.tensor(ii).t(), torch.tensor(vv), (n,n)).coalesce()
    d=torch.sparse.sum(A,dim=1).to_dense()+1.0
    # normalización simétrica: D^-1/2 (A+I) D^-1/2
    i2=A.indices(); v2=A.values()/(d[i2[0]].sqrt()*d[i2[1]].sqrt())
    diag=torch.arange(n)
    An=torch.sparse_coo_tensor(torch.cat([i2,torch.stack([diag,diag])],1), torch.cat([v2,1.0/d]), (n,n)).coalesce()
    torch.manual_seed(7)
    U,S,Vt=torch.svd_lowrank(An,q=dim,niter=niter)
    signo=(U*Vt).sum(0).sign()
    X=U*(S.clamp_min(0)*(signo>0)).sqrt()
    return torch.nn.functional.normalize(X,dim=1)
def muestra(tipo,p_,X):
    random.seed(3); out=[]
    ks=[k for k in syn if pos[str(k)]==p_ and syn[k]]
    n_=0
    while len(out)<2500 and n_<400000:
        n_+=1
        k=random.choice(ks)
        if tipo=="sin":
            if len(syn[k])<2: continue
            a,b=random.sample(syn[k],2)
        elif tipo=="padre":
            ps=[p for p in hyp.get(k,[]) if syn.get(p)]
            if not ps: continue
            a=random.choice(syn[k]); b=random.choice(syn[ps[0]])
        else:
            ps=hyp.get(k) or []
            if not ps: continue
            hs=[h for h in hijos.get(ps[0],[]) if h!=k and syn.get(h)]
            if not hs: continue
            a=random.choice(syn[k]); h=random.choice(hs); b=random.choice(syn[h])
            if b in syn[k] or a in syn[h] or b in syn.get(ps[0],[]) or a in syn.get(ps[0],[]): continue
        if a==b: continue
        out.append(float((X[idx[a]]*X[idx[b]]).sum()))
    return out
PARES=[("vigilar","cuidar"),("almacenar","guardar"),("investigar","estudiar"),("transformar","convertir"),("ingerir","comer"),("descansar","dormir"),("elaborar","fabricar"),("manejar","conducir"),("perro","gato"),("inventar","construir"),("pescar","cazar"),("vida","fase"),("habitar","vivir"),("fabricar","producir"),("finalizar","terminar"),("brotar","salir"),("demorar","tardar"),("resguardar","proteger"),("generar","producir"),("cocinar","cocer"),("comer","beber"),("tren","coche")]
for dim,a in [(96,0.0),(128,0.6),(256,0.6),(256,0.8),(384,0.6)]:
    t0=time.time(); X=entrena(dim,a)
    r=[]
    for p_ in "vn":
        S=muestra("sin",p_,X); P=muestra("padre",p_,X); H=muestra("herm",p_,X)
        for t in (0.4,0.5,0.6):
            f=lambda Z: sum(x>=t for x in Z)/max(1,len(Z))
            r.append(f"{p_}@{t} sin {f(S):.2f} padre {f(P):.2f} herm {f(H):.2f}")
    print(dim,a,"%.0fs"%(time.time()-t0)," | ".join(r))
    print("   "," ".join(f"{x}/{y} {float((X[idx[x]]*X[idx[y]]).sum()):.2f}" for x,y in PARES if x in idx and y in idx))
