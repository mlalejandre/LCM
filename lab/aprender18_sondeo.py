import sys; sys.path.insert(0,'.')
from lab.banco import correr, imprime
from lab.aprender18 import TEXTO
# solo hechos que la lectura guardó fielmente; misma pregunta con palabras del texto (=) y con otras (~)
P = [
 ("=", "¿los hongos tienen clorofila?", "^no"), ("~", "¿tienen clorofila las setas?", "^no"),
 ("~", "¿qué comen los hongos?", "restos|hojas|madera"),
 ("=", "¿dónde crece la trufa?", "tierra|encina*"), ("~", "¿la trufa crece en los árboles?", "^no|tierra|raices"),
 ("~", "¿cómo es la trufa?", "negra|bola"), ("~", "¿la trufa huele?", "^si|fuerte"), ("~", "¿qué forma tiene la trufa?", "bola"),
 ("=", "¿dónde están las láminas?", "sombrero"), ("~", "¿qué hay debajo del sombrero de una seta?", "laminas"),
 ("=", "¿qué lleva un setero?", "cesta"), ("~", "¿quién lleva una cesta de mimbre?", "setero"), ("~", "¿de qué es la cesta del setero?", "mimbre"),
 ("=", "¿cómo es el pie del boletus?", "grueso"), ("~", "¿el boletus tiene el pie fino?", "^no|grueso"),
 ("~", "¿qué hongo es negro?", "trufa"), ("~", "¿qué hongo huele muy fuerte?", "trufa"),
 ("~", "¿la trufa es una planta?", "^no"), ("~", "¿un boletus es un ser vivo?", "^si"), ("~", "¿qué es un boletus?", "seta"),
 ("~", "¿tiene sombrero el boletus?", "^si"), ("~", "¿cuántas partes tiene una seta?", "tres|3"),
 ("~", "¿qué hacen los hongos en el bosque?", "descompon*|nutrientes|devuelve*"),
]
D=[{"id":"sondeo","cat":t,"turnos":[(TEXTO,"")]+[(q,c) for t2,q,c in P if t2==t]} for t in ("=","~")]
f,r=correr(D,verboso=True); imprime(r,"SONDEO de recuperación (hechos guardados fielmente)")
