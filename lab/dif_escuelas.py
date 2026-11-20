import sys, shutil
from lab import banco
from lab.examenes_usuario import corre
res={}
for tag,ck in (("old","checkpoints/school_v19.pt"),("new","checkpoints/school_v21.pt")):
    shutil.copyfile(ck,"checkpoints/school.pt"); banco._PARSER=None
    for path in sys.argv[1:]:
        res[(tag,path)]={x[0]:x for x in corre(path)[2]}
for path in sys.argv[1:]:
    for q,x in res[("new",path)].items():
        if q not in res[("old",path)]: print("  NUEVO FALLO [%s] %s | esp %s | %s" % (path.split('/')[-1],x[0],x[1],x[2]))
