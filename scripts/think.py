import json
import os
import pickle
import re
import time
import copy
import torch
from configs.config import LCMConfig
from src.memory import MemoryStore
from src.model.reasoner import LatentReasoner
from src.reasoning.engine import ReasoningEngine
from src.reasoning.rule_engine import Fact
from src.training.online import OnlineLearner
from src.language import Ear, EarParser
from src.language.online_ear import EarLearner
from src.language.lexicon import norm
from src.language.qa import QA, is_question, template_from
from src.memory.schema import is_entity
from src.reasoning.lessons import apply_lessons, inherit, compare
from src.language.dialogue import Dialogue
from src.language.discourse import split_sentences, next_topic

BASE_CKPT = "checkpoints/lcm_reasoner.pt"
ONLINE_CKPT = "checkpoints/lcm_online.pt"

HELP = """Comandos (todo en mayusculas):
  s p o | s p o | ...            razonar con esas premisas (hasta 4)
  NUEVO a b ...                  anadir entidades nuevas al catalogo (se recuerdan)
  NUEVO_PRED a b ...             anadir relaciones nuevas
  APRENDE p1 | p2 => conclusion  ENSENAR una regla con un ejemplo (el modelo se ajusta, con repaso)
  CORRIGE s p o                  ensenar la conclusion correcta para las ultimas premisas
  HECHO s p o                    guardar un hecho en la memoria (sin ajustar el modelo)
  OLVIDA s p o                   borrar un hecho
  PREGUNTA a p c                 buscar en la memoria una cadena de hechos de a a c y razonar
  DORMIR                         ciclo de sueno: consolida lo aprendido
  ENTENDI s p o [NEGADO]         corregir lo que entendi de tu ultima frase (el oido y la escuela aprenden)
  (frases normales)              p. ej. "Pedro es padre de Sara"  |  "Si Ana es madre de Luis, entonces Luis es hijo de Ana"
  ARBOL frase                    ver como analiza la escuela cada palabra de una frase
  (pregunta)                     escribe una pregunta con ¿...? y te contesto con lo que he aprendido (p. ej. ¿Quién escribió una novela?)
  MEMORIA                        resumen de lo aprendido
  GUARDAR | SALIR
"""


def load_checkpoint(path, device):
    try:
        return torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        return torch.load(path, map_location=device)


def save_online(model, config):
    os.makedirs("checkpoints", exist_ok=True)
    torch.save({"model_state_dict": model.state_dict(),
                "config": {"d_concept": config.d_concept, "n_layers": config.n_layers, "n_heads": config.n_heads,
                           "max_concept_seq": config.max_concept_seq, "dropout": config.dropout}}, ONLINE_CKPT)


def parse_triples(text):
    groups = [part.strip().split() for part in text.split("|") if part.strip()]
    if not groups or any(len(g) != 3 for g in groups):
        return None
    return [tuple(g) for g in groups]


def main():
    if not os.path.exists(BASE_CKPT):
        print("[!] No hay checkpoint. Ejecuta primero: python -m scripts.train_reasoner")
        return
    if not os.path.exists("data/concept_space.pkl"):
        print("[!] No hay ontologia. Ejecuta primero: python -m scripts.prepare_concepts")
        return

    with open("data/concept_space.pkl", "rb") as handle:
        base_space = pickle.load(handle)
    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = load_checkpoint(BASE_CKPT, device)
    saved = checkpoint.get("config", {})
    config = LCMConfig(
        d_concept=base_space.d_concept,
        n_layers=int(saved.get("n_layers", 4)),
        n_heads=int(saved.get("n_heads", 4)),
        max_concept_seq=int(saved.get("max_concept_seq", 4)),
        dropout=float(saved.get("dropout", 0.05)),
        device=device,
    )
    model = LatentReasoner(config)
    model.set_space(base_space)
    model.load_state_dict(checkpoint["model_state_dict"])

    # Memoria: re-registra los conceptos aprendidos y, si existe, carga los pesos ajustados.
    memory = MemoryStore()
    space = copy.deepcopy(base_space)
    restored = memory.apply_concepts(space)
    model.set_space(space)
    if os.path.exists(ONLINE_CKPT):
        try:
            state = {k: v for k, v in load_checkpoint(ONLINE_CKPT, device)["model_state_dict"].items()
                     if k not in ("concepts", "roles")}       # el catalogo puede haber crecido: sus vectores son deterministas
            model.load_state_dict(state, strict=False)
            print("[+] Recuerdos cargados: pesos ajustados en sesiones anteriores.")
        except RuntimeError:
            print("[!] El checkpoint online no encaja con el catalogo actual; se usa el base.")
    model.to(device)

    engine = ReasoningEngine(model, space, device=device)
    learner = None
    if os.path.exists("data/concept_train_dataset.pkl") and os.path.exists("data/concept_val_dataset.pkl"):
        with open("data/concept_train_dataset.pkl", "rb") as h:
            train = pickle.load(h).tensors
        with open("data/concept_val_dataset.pkl", "rb") as h:
            val = pickle.load(h).tensors
        gen = torch.Generator().manual_seed(1)
        core_idx = torch.randperm(len(train[0]), generator=gen)[:4000]
        canary_idx = torch.randperm(len(val[0]), generator=gen)[:300]
        core = tuple(t[core_idx] for t in train)       # mismo indice para X, M, Y
        canary = tuple(t[canary_idx] for t in val)
        learner = OnlineLearner(model, space, core, canary, device=device)
        for l in memory.lessons:
            learner.lessons.append(([tuple(p) for p in l["premises"]], tuple(l["conclusion"])))
    else:
        print("[!] Sin datos de repaso: APRENDE queda desactivado (ejecuta prepare_concepts).")

    print("=" * 65)
    print(f" LARGE CONCEPTUAL MODEL (LCM) - RAZONAMIENTO Y APRENDIZAJE [{device.upper()}]")
    print("=" * 65)
    print(f" Memoria: {memory.summary()}" + (f" ({restored} conceptos restaurados)" if restored else ""))
    print(HELP)
    dirty = False
    last_premises = None
    ear = None
    ear_learner = None
    last_sentence = None
    ear = ear_learner = None
    for ckpt in ("checkpoints/ear_online.pt", "checkpoints/ear.pt"):
        if not os.path.exists(ckpt):
            continue
        try:
            _e = Ear()
            _e.load_state_dict(torch.load(ckpt, map_location="cpu"))
            ear = EarParser(_e, device)
            ear_learner = EarLearner(ear, device)
            print(f" [oido] Entiendo frases en espanol ({os.path.basename(ckpt)}). Si me malinterpreto: ENTENDI s p o [NEGADO].")
            break
        except Exception:
            print(f" [oido] {ckpt} no es compatible con esta version (se ignora).")
    school = None
    if os.path.exists("checkpoints/school.pt"):
        try:
            from src.language.school_parser import SchoolParser
            from src.language.ud import load_school
            from src.language.school_learn import load_overrides
            _s, _scripts = load_school(device=device)
            school = SchoolParser(_s, device, _scripts, load_overrides())
            print(" [escuela] Analizo frases libres en espanol (school.pt) cuando el oido de plantillas no las entiende.")
            from src.language.semilla import load_seed
            added = load_seed(memory, school)
            try:                                                  # parche-91: cartuchos de conocimiento activos (cartuchos/activos.json)
                from src.memory.cartuchos import montar
                for _n, _k in montar(memory):
                    print(f" [cartucho] {_n}: " + (f"{_k} hechos" if _k is not None else f"NO ENCONTRADO (quitalo: python -m scripts.cartucho retirar {_n})"))
            except Exception as _e:                               # noqa
                print(f" [cartucho] no se pudieron montar: {_e!r}")
            try:                                                  # parche-99: diccionario de conceptos (universales, multilingue)
                from src.language import conceptos as _cc
                if _cc.disponible():
                    print(f" [conceptos] {_cc.total()} conceptos universales (sentidos con nombres en es/en/fr/it/pt/ca/gl/eu), con jerarquia, partes y vector de rasgos.")
            except Exception:                                     # noqa
                pass
            if added:
                memory.save()
                print(f" [semilla] Conocimiento de fabrica cargado: {added} hechos (colores, formas, naturaleza, cuerpo, objetos, opuestos...).")
        except Exception as exc:
            print(f" [escuela] school.pt no se pudo cargar ({type(exc).__name__}); se ignora.")
    if ear is None:
        print(" [oido] Sin oido valido: ejecuta  python -m scripts.train_ear")
    COMMANDS = {"NUEVO", "NUEVO_PRED", "APRENDE", "CORRIGE", "HECHO", "OLVIDA", "PREGUNTA", "MEMORIA",
                "GUARDAR", "SALIR", "EXIT", "QUIT", "DORMIR", "AYUDA", "ENTENDI", "ARBOL"}

    def vaccinate(preds):
        """Relacion nueva: aprende al momento que, sin regla, no concluye nada (evita conclusiones inventadas)."""
        nonlocal dirty
        if learner is None or not learner.lessons:
            return
        info = learner.inoculate(preds)
        if info.get("done"):
            dirty = True
            save_online(model, config)
            print(f"[vacuna] {', '.join(preds)}: sin regla, no concluyo nada (canario {info['canary']:.0%}).")
        else:
            print(f"[vacuna] no aplicada ({info.get('reason')}).")

    def register(names, kind):
        created = []
        for n in names:
            if n not in space.concept_to_id:
                feats = ({"predicate": 1, "relation": 1, f"identity:{n}": 0.5} if kind == "predicate"
                         else {"individual": 1, f"identity:{n}": 0.5})
                space.add_concept(n, features=feats, kind=kind)
                memory.add_concept(n, feats, kind)
                created.append(n)
        if created:
            model.set_space(space)
            model.to(device)
            if kind == "predicate":
                vaccinate(created)
        return created

    def log_dialogue(sentence, parsed):
        os.makedirs("memory", exist_ok=True)
        with open(os.path.join("memory", "dialogo.jsonl"), "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"t": time.time(), "frase": sentence, "significado": parsed}, ensure_ascii=False) + "\n")

    last_raw = {}
    topic = [None]          # sujeto de la frase anterior (parche-44): para "Ella..." y para el sujeto omitido

    def understand(clause):
        out = ear.parse(clause, ear.candidates(space)) if ear is not None else None
        last_raw["out"] = out
        if out is not None and out["confidence"] >= ear.min_conf:
            return out
        if school is not None:
            found = school.parse(clause)
            last_raw["school"] = found
            if found and len(found) == 1:
                t = found[0]
                return {"subject": t["s"].upper(), "predicate": t["p"].upper(), "object": t["o"].upper(),
                        "negated": t["neg"], "confidence": 1.0, "via": "escuela", "template": t.get("template"),
                        "s_disp": t.get("s_disp"), "o_disp": t.get("o_disp"), "when": t.get("when", ""), "when_disp": t.get("when_disp", "")}
        return None

    def understand_many(clause):
        """Una o varias proposiciones (coordinaciones, verbos con sujeto compartido, sujeto omitido)."""
        one = understand(clause)
        if one is not None and one.get("via") != "escuela":
            return [one]
        if school is None:
            return [one] if one else []
        found = school.parse(clause, topic=topic[0])
        last_raw["school"] = found
        if not found or len(found) > 6:
            return []
        return [{"subject": t["s"].upper(), "predicate": t["p"].upper(), "object": t["o"].upper(), "negated": t["neg"],
                 "confidence": 1.0, "via": "escuela", "template": t.get("template"), "s_disp": t.get("s_disp"),
                 "o_disp": t.get("o_disp"), "when": t.get("when", ""), "when_disp": t.get("when_disp", "")} for t in found]

    replay_cache = []
    backed_up = [False]

    def school_correct(sentence, trip):
        """ENTENDI tambien ensena a la escuela: ajuste pequeno con repaso, canario (conversacion) y reversion (parche-49)."""
        from src.language.school_learn import (append_log, learn_correction, read_log, replay_sentences, save_overrides,
                                               synthetic_replay)
        from src.language.ud import save_school
        canary = None
        if os.path.exists("data/frases_prueba.tsv"):
            from scripts.eval_frases import evaluate
            canary = lambda: evaluate(school, path="data/frases_prueba.tsv")[1]
        if not replay_cache:
            replay_cache.extend(replay_sentences(n=150) + synthetic_replay(200))
        info = learn_correction(school.model, device, school.scripts, sentence, trip, extra=read_log(), replay=replay_cache,
                                canary=canary, overrides=school.overrides)
        if info["done"]:
            if not backed_up[0] and os.path.exists("checkpoints/school.pt"):
                import shutil
                shutil.copy("checkpoints/school.pt", "checkpoints/school.pt.bak")
                backed_up[0] = True
            save_school(school.model, school.scripts)
            save_overrides(school.overrides)
            append_log(sentence, trip)
            c = info.get("canary") or (None, None)
            print("[escuela] Aprendido: ahora leo asi tu frase (repitela para que la guarde)." + (f" ({info['nota']})" if info.get("nota") else "") +
                  (f" Conversacion {c[0]:.0%} -> {c[1]:.0%}." if c[0] is not None else ""))
        else:
            print(f"[escuela] No he cambiado nada: {info.get('reason')}.")

    def explain_rejection():
        sc = last_raw.get("school")
        if sc:
            print("        (escuela: veo " + str(len(sc)) + " proposiciones: " + "; ".join(f"{t['s']} {t['p']} {t['o']}" for t in sc[:4]) +
                  " - solo acepto frases con UNA proposicion; simplifica la frase)")
        o = last_raw.get("out")
        if o and o.get("predicate"):
            print(f"        (mejor lectura: {o['subject']} {o['predicate']} {o['object']} | confianza {o['confidence']:.0%}, "
                  f"es-afirmacion {o['in_scope']:.0%}, umbral {ear.min_conf:.0%})")

    dialogue = Dialogue(memory)

    def deduce(facts):
        """Motor simbolico (relaciones fijas) + lecciones aprendidas con "Si... entonces..." (con explicacion)."""
        given = {Fact(*f) for f in facts}
        out = {(f.subject, f.predicate, f.obj): [] for f in engine.deduce(given)["facts"] - given}
        out.update(apply_lessons(facts, memory.active_lessons(), is_var=lambda n: is_entity(space, n)))
        for k, v in list(inherit(facts).items()) + list(compare(facts).items()):
            out.setdefault(k, v)
        return out

    conv_box = []

    def get_conv():
        """parche-103: las PREGUNTAS pasan por la misma capa que los examenes (Conversation.say: normalizador de familias, erratas, sinonimos, lexico, conceptos, seguimiento).
        Comparte memoria y Dialogue con esta sesion."""
        if not conv_box:
            from src.language.dialogue import Conversation
            c = Conversation(memory, school, lambda m, p: QA(m, school.parse, deduce))
            c.d = dialogue
            conv_box.append(c)
        return conv_box[0]

    def answer_question(raw):
        if school is None:
            print("[pregunta] Necesito la escuela de espanol (python -m scripts.train_school).\n")
            return
        print("[respuesta] " + get_conv().say(raw) + "\n")

    def handle_natural(raw):
        nonlocal dirty, last_sentence
        if school is not None and not dialogue.pending:
            from src.language import consultas as _cs
            try:
                _q = is_question(raw) or is_question(_cs.canonical(raw))
            except Exception:                                  # noqa
                _q = False
            if not _q and _cs.es_orden(raw):                   # parche-103: una orden no es un hecho: no se aprende
                try:                                           # parche-105: pero "dime cinco frutas" es una pregunta de diccionario
                    from src.language import conceptos as _cn
                    _r = _cn.antes_orden(raw, memory)
                except Exception:                              # noqa
                    _r = None
                if _r:
                    print("[respuesta] " + _r + "\n")
                    return
                print("[respuesta] Eso parece una orden y no un hecho, así que no lo guardo. Todavía no sé hacerlo; si quieres saber algo, pregúntamelo con ¿…?\n")
                return
            if _q:                                             # parche-103: pregunta (con o sin signos, "dime un sinonimo de perro"): capa completa de preguntas
                return answer_question(raw)
        reply, cont = dialogue.act(raw, QA(memory, school.parse, None) if school is not None else None)
        if reply:
            dialogue.last = reply
            print("[respuesta] " + reply + "\n")
            memory.save()
        if cont is None:
            return
        raw = cont
        if is_question(raw):
            return answer_question(raw)
        parts = split_sentences(raw)
        if len(parts) > 1 and "entonces" not in norm(raw):     # varias frases: una a una, recordando el sujeto
            for part in parts:
                handle_natural(part)
            return
        last_sentence = raw
        low = norm(raw)
        mh = re.match(r"\s*hoy(?:\s+es)?\s*(.*?)\s*[.!]?\s*$", low)
        if mh and not is_question(raw) and (mh.group(1) == "" or re.search(r"\d", mh.group(1))):
            from datetime import date as _d
            from src.language.fechas import extract_abs, fmt, parse_iv
            if mh.group(1):
                iso = re.fullmatch(r"\d{4}-\d{2}-\d{2}", mh.group(1))
                iv = (mh.group(1) + "/" + mh.group(1)) if iso else extract_abs(mh.group(1), _d.today())[1]
                if not iv:
                    print("[!] No entendi la fecha. Ejemplo: Hoy es 6 de noviembre de 2026  |  HOY 2026-11-06\n")
                    return
                memory.today = parse_iv(iv)[0]
                if school is not None:
                    school.today = memory.today
            print(f"[fecha] Hoy es {fmt(_d.isoformat(getattr(memory, 'today', None) or _d.today()) + '/' + _d.isoformat(getattr(memory, 'today', None) or _d.today()))}. "
                  "Lo relativo (ayer, el lunes...) se guarda como fecha absoluta.\n")
            return
        if "entonces" in low and not low.startswith("entonces"):
            a, b = re.split(r"\bentonces\b", low[3:] if low.startswith("si ") else low, maxsplit=1)
            pa, pb = understand(a), understand(b)
            if not pa or not pb:
                print("[oido] No he entendido bien alguna de las dos partes. Reformula la frase.\n")
                return
            if pa["negated"] or pb["negated"]:
                print("[oido] Aun no aprendo reglas con negaciones. Dime la regla en positivo.\n")
                return
            prem, concl = (pa["subject"], pa["predicate"], pa["object"]), (pb["subject"], pb["predicate"], pb["object"])
            print(f"[oido] Regla entendida: {' '.join(prem)}  =>  {' '.join(concl)}")
            if learner is None:
                print("[!] Aprendizaje desactivado.\n")
                return
            register([prem[0], prem[2], concl[0], concl[2]], "entity")
            register([x for x in (prem[1], concl[1]) if x not in space.concept_to_id], "predicate")
            info = learner.learn([([prem], concl)])
            log_dialogue(raw, {"regla": [prem, concl], "aceptada": info["accepted"]})
            if info["accepted"]:
                memory.add_lesson([prem], concl)
                ra, rb = re.split(r"\bentonces\b", re.sub(r"^\s*si\s+", "", raw, flags=re.I), maxsplit=1, flags=re.I)
                for part, trip in ((ra, prem), (rb, concl)):
                    tpl = template_from(part.strip(" ,."), trip[0], trip[2])
                    if tpl:
                        memory.note_surface(trip, *tpl)
                memory.save()
                dirty = True
                save_online(model, config)
                print(f"[+] Aprendido. Acierto en la leccion: {info['before']:.0%} -> {info['after']:.0%} | "
                      f"conocimiento previo (canario): {info['canary']:.0%}\n")
            else:
                print(f"[!] Cambio REVERTIDO (canario {info['canary']:.0%}).\n")
            return
        outs = understand_many(raw)
        if not outs:
            explain_rejection()
            print("[oido] " + dialogue.clarify_statement(raw) + " (Si usa una relacion nueva, creala antes con NUEVO_PRED.)\n")
            return
        if not any(o["negated"] for o in outs):
            dialogue.apply_effects([(o["subject"], o["predicate"], o["object"], o.get("o_disp") or "") for o in outs])      # parche-59: dar/vender/abrir/ir...
        for out in outs:
            triple = (out["subject"], out["predicate"], out["object"])
            register([triple[0], triple[2]], "entity")
            if triple[1] not in space.concept_to_id:
                register([triple[1]], "predicate")
                print(f"[escuela] Relacion nueva para mi: {triple[1]} (la he anadido al catalogo)")
            neg = out["negated"]
            how = "por la escuela de espanol" if out.get("via") else f"confianza {out['confidence']:.0%}"
            print(f"[oido] Entendido: {'NO ' if neg else ''}{' '.join(triple)}   ({how}) "
                  "- si no era eso, corrigeme con ENTENDI s p o [NEGADO]")
            memory.add_fact(triple, source=raw, neg=neg, when=out.get("when", ""), when_disp=out.get("when_disp", ""), quant=out.get("q", ""))
            if out.get("template"):
                memory.note_surface(triple, out["template"], out.get("s_disp"), out.get("o_disp"))
            elif len(outs) == 1 and not neg:                 # frase entendida por el oido de plantillas: plantilla sacada de tus palabras
                tpl = template_from(raw.strip(" ,."), triple[0], triple[2])
                if tpl:
                    memory.note_surface(triple, *tpl)
            note = dialogue.note_new(triple, neg, raw, out.get("when", ""), QA(memory, school.parse, None).say if school is not None else None)
            if note:
                print("[coherencia] " + note)
            memory.save()
            log_dialogue(raw, {"hecho": triple, "negado": neg, "confianza": out["confidence"]})
            if neg:
                print("    (guardado como hecho negado; todavia no se usa para razonar)\n")
                continue
            show_inference([triple])
        dialogue.last_facts = [(o["subject"], o["predicate"], o["object"]) for o in outs if not o["negated"]]
        topic[0] = next_topic([{"s": o["subject"].lower()} for o in outs], topic[0])

    def known(tokens):
        return sorted({t for t in tokens if t not in space.concept_to_id})

    def show_inference(groups):
        nonlocal last_premises
        premise_vectors = [space.encode_proposition(*g) for g in groups]
        result_vector = engine.think_vectors(premise_vectors, steps=1)[0]
        with torch.no_grad():
            s_i, p_i, o_i = model.read_slots(result_vector.view(1, 1, -1).to(device))[0, 0].tolist()
        decoded = "::".join(space.id_to_concept[i] for i in (s_i, p_i, o_i))
        similarity = float(torch.nn.functional.cosine_similarity(
            result_vector.view(1, -1).cpu(), space.encode_proposition(*decoded.split("::")).view(1, -1))[0])
        last_premises = groups
        print("\n[OK] Representacion conceptual generada.")
        print(f"     ├── Candidato: {decoded}")
        print(f"     └── Similitud coseno: {similarity * 100:.2f}% (no es probabilidad calibrada)")
        given = {Fact(*g) for g in groups}
        derived = engine.deduce(given)["facts"] - given
        n_s, n_p, n_o = decoded.split("::")
        if derived:
            print("     Motor simbolico deduce: " + ", ".join(f"{f.subject} {f.predicate} {f.obj}" for f in sorted(derived)))
            agree = Fact(n_s, n_p, n_o) in derived
        else:
            print("     Motor simbolico: sin conclusion con estas premisas")
            agree = n_p == "SIN_CONCLUSION"
        print(f"     Acuerdo red/simbolico: {'SI' if agree else 'NO (puede ser algo que solo sabe la red, o un fallo)'}")
        print(f"     Verbalizado: \"{n_s} {n_p} {n_o}\"\n")

    while True:
        try:
            raw = input("Premisas > ").strip()
            line = raw.upper()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if line in {"SALIR", "EXIT", "QUIT"}:
            break
        if not line:
            continue
        if line == "AYUDA":
            print(HELP)
            continue
        if line == "GUARDAR":
            memory.save()
            if dirty:
                save_online(model, config)
            print("[+] Guardado.\n")
            continue
        if line == "DORMIR":
            if learner is None:
                print("[!] Aun no hay modelo online cargado.\n")
                continue
            from src.memory.sleep import SleepCycle
            rep = SleepCycle(learner, memory).run()
            g = lambda t: (sum(r["probe"] for r in t["groups"]) / len(t["groups"])) if t["groups"] else float("nan")
            print(f"[zzz] esquemas: {len(rep['after']['groups'])} | generaliza {g(rep['before']):.0%} -> {g(rep['after']):.0%} | "
                  f"canario {rep['after']['canary']:.0%} | archivadas {rep['compressed']} | hechos olvidados {rep['decayed_facts']} | "
                  f"revertido {rep['consolidate']['rolled_back']} | pasos {rep['consolidate'].get('steps', 0)} "
                  f"(consolidacion {rep['consolidate'].get('consolidation', 1):.0%})")
            memory.save()
            save_online(model, config)
            dirty = False
            print()
            continue
        if line.startswith("ARBOL ") and school is not None:
            for i, (form, upos, head, rel, lemma) in enumerate(school.tree(raw[6:]), 1):
                print(f"   {i:2d} {form:15s} {upos:6s} -> {head:2d} {rel:7s} lema: {lemma}")
            print("   (cada palabra: categoria, numero de la palabra de la que depende (0 = raiz), funcion y forma base)\n")
            continue
        if line == "MEMORIA":
            print(f"[*] {memory.summary()}")
            for l in memory.lessons[-5:]:
                print("    leccion:", " | ".join(" ".join(p) for p in l["premises"]), "=>", " ".join(l["conclusion"]))
            for f in memory.facts[-5:]:
                print("    hecho:", f["s"], f["p"], f["o"])
            print()
            continue
        words = line.split()
        if words[0] == "ENTENDI":
            if school is not None and last_sentence is not None and len(words) in (4, 5):
                _p = words[1:-1] if words[-1] == "NEGADO" else words[1:]
                if len(_p) == 3:
                    school_correct(last_sentence, tuple(_p))
                    if _p[1] not in space.concept_to_id:      # la relacion aun no existe: el oido de plantillas no tiene nada que corregir
                        print()
                        continue
            if ear_learner is None or last_sentence is None:
                print("[!] No hay una frase reciente que corregir.\n")
                continue
            negated = words[-1] == "NEGADO"
            parts = words[1:-1] if negated else words[1:]
            if len(parts) != 3 or any(t not in space.concept_to_id for t in (parts[1],)):
                print("[!] Formato: ENTENDI sujeto RELACION objeto [NEGADO]  (la relacion debe existir)\n")
                continue
            toks = set(norm(last_sentence).split())
            aliases = [t for n, t in ear.candidates(space) if n == parts[1]]
            phrase = next((t for t in aliases if all(w in toks or w[:4] in {x[:4] for x in toks} for w in t.split())), aliases[0])
            example = ear_learner.build_example(last_sentence, tuple(parts), negated, phrase)
            if example is None:
                print("[!] No encuentro el sujeto y el objeto escritos tal cual en tu frase.\n")
                continue
            info = ear_learner.learn(example)
            if info["accepted"]:
                print(f"[+] Oido ajustado. Ahora entiende esa frase: {'si' if info['learned'] else 'todavia no (repite la correccion)'}"
                      f" | repaso {info['repaso_antes']:.0%} -> {info['repaso_despues']:.0%}\n")
            else:
                print(f"[!] Cambio del oido REVERTIDO: empeoraba lo que ya sabia ({info['repaso_antes']:.0%} -> {info['repaso_despues']:.0%}).\n")
            continue
        if (ear is not None and (words[0] not in COMMANDS or not raw.isupper()) and any(c.islower() for c in raw) and "_" not in raw
                and (len(words) >= 2 or dialogue.talks(raw))):
            handle_natural(raw)
            continue
        if words[0] in ("NUEVO", "NUEVO_PRED") and len(words) > 1:
            created = []
            for name in words[1:]:
                if name not in space.concept_to_id:
                    feats = ({"predicate": 1, "relation": 1, f"identity:{name}": 0.5} if words[0] == "NUEVO_PRED"
                             else {"individual": 1, f"identity:{name}": 0.5})
                    kind = "predicate" if words[0] == "NUEVO_PRED" else "entity"
                    space.add_concept(name, features=feats, kind=kind)
                    memory.add_concept(name, feats, kind)
                    created.append(name)
            model.set_space(space)
            model.to(device)
            if words[0] == "NUEVO_PRED" and created:
                vaccinate(created)
            memory.save()
            print(f"[+] Conceptos anadidos: {created or 'ninguno (ya existian)'}\n")
            continue
        if words[0] == "HECHO" and len(words) == 4:
            if known(words[1:]):
                print(f"[!] Conceptos desconocidos: {known(words[1:])}. Usa NUEVO.\n")
                continue
            new = memory.add_fact(tuple(words[1:]))
            memory.save()
            print(f"[+] Hecho {'guardado' if new else 'ya conocido (refuerzo)'}.\n")
            continue
        if words[0] == "OLVIDA" and len(words) == 4 and raw.isupper():
            print(f"[+] {'Olvidado' if memory.forget_fact(tuple(words[1:])) else 'No estaba en la memoria'}.\n")
            memory.save()
            continue
        if words[0] == "PREGUNTA" and len(words) == 4:
            route = memory.find_path(words[1], words[3], max_len=config.max_concept_seq)
            if not route:
                print("[!] No hay en la memoria una cadena de hechos entre esos dos conceptos.\n")
                continue
            print("[*] Premisas recuperadas de la memoria: " + " | ".join(" ".join(r) for r in route))
            show_inference(route)
            continue
        if words[0] == "APRENDE" or words[0] == "CORRIGE":
            if learner is None:
                print("[!] Aprendizaje desactivado.\n")
                continue
            if words[0] == "CORRIGE":
                if last_premises is None or len(words) != 4:
                    print("[!] Formato: CORRIGE s p o (despues de una inferencia)\n")
                    continue
                premises, concl = last_premises, [tuple(words[1:])]
            else:
                body = line[len("APRENDE"):].split("=>")
                premises = parse_triples(body[0]) if len(body) == 2 else None
                concl = parse_triples(body[1]) if len(body) == 2 else None
                if not premises or not concl or len(concl) != 1:
                    print("[!] Formato: APRENDE s p o | s p o => s p o\n")
                    continue
            tokens = [t for g in premises + concl for t in g]
            if known(tokens):
                print(f"[!] Conceptos desconocidos: {known(tokens)}. Usa NUEVO / NUEVO_PRED.\n")
                continue
            info = learner.learn([(premises, concl[0])])
            if info["accepted"]:
                memory.add_lesson(premises, concl[0])
                memory.save()
                dirty = True
                save_online(model, config)
                print(f"[+] Aprendido. Acierto en la leccion: {info['before']:.0%} -> {info['after']:.0%} | "
                      f"conocimiento previo (canario): {info['canary']:.0%}\n")
            else:
                print(f"[!] Cambio REVERTIDO: rompia el conocimiento previo (canario {info['canary']:.0%}). "
                      "Ensena mas ejemplos o revisa la regla.\n")
            continue

        groups = parse_triples(line)
        if not groups:
            print("[!] Formato: SUJETO PREDICADO OBJETO | ...   (escribe AYUDA)\n")
            continue
        if len(groups) > config.max_concept_seq:
            print(f"[!] Maximo {config.max_concept_seq} proposiciones por inferencia.\n")
            continue
        unknown = known([t for g in groups for t in g])
        if unknown:
            print(f"[!] Nodos no registrados en la ontologia: {unknown}. Usa NUEVO / NUEVO_PRED.\n")
            continue
        try:
            show_inference(groups)
        except (KeyError, ValueError, RuntimeError) as exc:
            print(f"[!] No se pudo construir la inferencia: {exc}")

    memory.save()
    if dirty:
        save_online(model, config)
        print("[+] Memoria y pesos guardados.")


if __name__ == "__main__":
    main()
