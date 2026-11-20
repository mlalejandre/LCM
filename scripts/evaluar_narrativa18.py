#!/usr/bin/env python3
"""LCM18 – evaluate locked cases with exact same procedure before and after patch.
Do not alter corpus in this file; SHA256 is pinned in the output.
"""
import json, re, hashlib, sys, tempfile, os, time, argparse
from pathlib import Path
from datetime import date

def normal(s):
 import unicodedata
 return ''.join(x for x in unicodedata.normalize('NFD',s.casefold()) if unicodedata.category(x)!='Mn')

def validar(resp,expected):
 s=normal(str(resp)); e=normal(expected)
 if e=='unknown':
  # abstencion explícita, sin referencia a un dato no autorizado
  patterns=['no consta','no se','no puedo','no tengo','insuficiente','desconozco','no hay','no sabemos','ambigu','no dispongo','no conozco']
  return any(x in s for x in patterns) and not re.search(r'\b(s[ií]|efectivamente|ciertamente)\b',s)
 # respuesta debe estar en una ASERCION, no en el eco de la pregunta en una cita
 front=s.split('segun ')[0].split('consta ')[0].split('porque ')[0]
 # para respuestas de fuente se permite citarla
 if len(e.split())>=2:
  return e in s
 # el nombre/objeto debe ser respuesta identificable en la primera cláusula
 return bool(re.search(r'(?<!\w)'+re.escape(e)+r'(?!\w)',front)) and not any(x in front for x in ('no consta','no se','insuficiente','no puedo','no tengo','desconozco','no hay','no conozco'))

def main():
 a=argparse.ArgumentParser();a.add_argument('--casos',required=True);a.add_argument('--salida',required=True);a.add_argument('--limit',type=int,default=0);args=a.parse_args()
 from src.web.motor import Motor
 from src.memory.store import MemoryStore
 class Stub:
  def parse(self,*a,**kw): return []
 archivo=Path(args.casos); data=json.loads(archivo.read_text(encoding='utf8')); arr=data['casos'];arr=arr[:args.limit] if args.limit else arr
 filas=[];t0=time.monotonic()
 for i,c in enumerate(arr):
  with tempfile.TemporaryDirectory() as d:
   mem=MemoryStore(d+'/mem.json');mem.today=date(2026,11,18)
   m=Motor(mem,Stub(),carpeta_cartuchos=d+'/cartuchos')
   responses=[]
   for t in c['turnos']:
    try:r=m.chat(t);res=r.get('respuesta') or '[error] '+str(r.get('error','sin respuesta'))
    except Exception as exc:res='[exception] '+str(exc)
    responses.append(res)
   passed=validar(responses[-1],c['expected'])
   filas.append({'id':c['id'],'grupo':c['grupo'],'correcto':passed,'expected':c['expected'],'response':responses[-1],'turnos':c['turnos']})
  if (i+1)%10==0:print('progreso',i+1,'/',len(arr),flush=True)
 result={'n':len(filas),'aciertos':sum(r['correcto'] for r in filas),'duracion_s':round(time.monotonic()-t0,3),
  'corpus_sha256':hashlib.sha256(archivo.read_bytes()).hexdigest(),'por_grupo':{},'filas':filas,
  'lotes':[{'lote':i//10+1,'correctas':sum(x['correcto'] for x in filas[i:i+10]),'total':len(filas[i:i+10]),
          'aprobada':sum(x['correcto'] for x in filas[i:i+10])>=9 if len(filas[i:i+10])==10 else None}
          for i in range(0,len(filas),10)]}
 for r in filas:
  g=result['por_grupo'].setdefault(r['grupo'],{'n':0,'aciertos':0});g['n']+=1;g['aciertos']+=r['correcto']
 Path(args.salida).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 print('RESULTADO',result['aciertos'],'/',result['n'],'segundos',result['duracion_s'],flush=True)
if __name__=='__main__':main()
