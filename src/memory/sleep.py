"""Ciclo de sueno del LCM (parche-14).

Inspirado en el "ciclo de sueno" del proyecto memoria-unificada (tareas rotativas:
repair, decay, dedupe, selftest, ...), adaptado a un modelo que aprende con
pesos: ademas de ordenar la memoria, CONSOLIDA el aprendizaje.

Tareas:
  repair    : archiva lecciones que mencionan conceptos desaparecidos
  selftest  : se examina: recuerda cada leccion? generaliza su esquema a entidades nuevas?
  compress  : de cada esquema conserva pocas lecciones representativas (el resto se
              archiva, de forma reversible: su informacion queda en el esquema)
  consolidate: repasa lecciones + ejemplos de fabrica + SUENOS (ejemplos generados
              desde los esquemas con otras entidades), dando mas peso a lo debil;
              revierte si el canario cae
  decay     : olvido de hechos poco importantes/usados (reversible)
"""
from __future__ import annotations

import copy
import datetime
import os
import random
from typing import Dict, List

import torch

from .schema import Schema, induce, instantiate, is_entity


class SleepCycle:
    def __init__(self, learner, memory, seed: int = 0):
        self.L = learner
        self.mem = memory
        self.rng = random.Random(seed)

    # ---- utilidades ---------------------------------------------------
    @property
    def space(self):
        return self.L.space

    def sync(self) -> None:
        self.L.lessons = [([tuple(p) for p in l["premises"]], tuple(l["conclusion"])) for l in self.mem.active_lessons()]

    def entities(self) -> List[str]:
        return [n for n in self.space.concept_to_id if is_entity(self.space, n)]

    def groups(self, include_archived: bool = True) -> Dict[str, dict]:
        out: Dict[str, dict] = {}
        for i, l in enumerate(self.mem.lessons):
            if l.get("archived") and not include_archived:
                continue
            premises = [tuple(p) for p in l["premises"]]
            schema = induce(self.space, premises, tuple(l["conclusion"]))
            g = out.setdefault(schema.signature, {"schema": schema, "idx": []})
            g["idx"].append(i)
        return out

    # ---- tareas -------------------------------------------------------
    def task_repair(self) -> int:
        fixed = 0
        for l in self.mem.lessons:
            names = [x for p in l["premises"] for x in p] + list(l["conclusion"])
            if not l.get("archived") and any(n not in self.space.concept_to_id for n in names):
                l["archived"] = True
                fixed += 1
        return fixed

    def selftest(self, probes: int = 40) -> dict:
        self.sync()
        entities = self.entities()
        rows = []
        for sig, g in self.groups(include_archived=False).items():
            lessons = [(  [tuple(p) for p in self.mem.lessons[i]["premises"]], tuple(self.mem.lessons[i]["conclusion"]))
                       for i in g["idx"]]
            recall = self.L.exact(*self.L.encode(lessons))
            fresh = [instantiate(self.space, g["schema"], self.rng, entities) for _ in range(probes)]
            probe = self.L.exact(*self.L.encode(fresh))
            rows.append({"sig": sig, "n": len(lessons), "recall": recall, "probe": probe})
        return {"groups": rows, "canary": self.L.canary_score()}

    def task_compress(self, max_keep: int = 3) -> int:
        archived = 0
        test = self.selftest(probes=10)
        recall_by_sig = {r["sig"]: r["recall"] for r in test["groups"]}
        for sig, g in self.groups(include_archived=False).items():
            idx = g["idx"]
            if len(idx) > max_keep:
                # se conservan las ultimas aprendidas (las mas frescas); el resto se archiva
                for i in idx[:-max_keep]:
                    self.mem.lessons[i]["archived"] = True
                    archived += 1
        self.sync()
        return archived

    def task_consolidate(self, steps: int = 400, lr: float = 5e-4, use_lessons: bool = True, use_dreams: bool = True,
                         bank_size: int = 300, dreams_per_step: int = 32, replay_core: bool = True,
                         use_negatives: bool = True, neg_per_step: int = 32) -> dict:
        self.sync()
        L = self.L
        entities = self.entities()
        test = self.selftest(probes=20)
        banks = []
        if use_dreams:
            all_groups = self.groups(include_archived=True)
            weak = {r["sig"]: r["probe"] for r in test["groups"]}
            for sig, g in all_groups.items():
                examples = [instantiate(self.space, g["schema"], self.rng, entities) for _ in range(bank_size)]
                weight = 1.0 + 2.0 * (1.0 - weak.get(sig, 0.5))       # mas sueños donde peor generaliza
                banks.append((L.encode(examples), max(4, int(dreams_per_step * weight / 2))))
        own = L.encode(L.lessons) if (use_lessons and L.lessons) else None
        neg = None
        if use_negatives and L.lessons:
            from .negatives import make_negatives
            negs = make_negatives(self.space, L.lessons, 400, self.rng, entities, L.safe(), ghost_exclude=L.neg_exclude)
            neg = L.encode(negs) if negs else None
        snapshot = copy.deepcopy(L.model.state_dict())
        L.model.train()
        optimizer = torch.optim.AdamW(L.model.parameters(), lr=lr, weight_decay=0.0)
        def one_step():
            parts = []
            if replay_core:
                j = torch.randint(0, len(L.core[0]), (L.replay_batch,))
                parts.append(tuple(t[j] for t in L.core))
            if own is not None:
                j = torch.randint(0, len(own[0]), (min(L.replay_batch, len(own[0])),))
                parts.append(tuple(t[j] for t in own))
            if neg is not None:
                j = torch.randint(0, len(neg[0]), (neg_per_step,))
                parts.append(tuple(t[j] for t in neg))
            for (X, M, Y), k in banks:
                j = torch.randint(0, len(X), (k,))
                parts.append((X[j], M[j], Y[j]))
            if not parts:
                return False
            X, M, Y = (torch.cat([p[i] for p in parts]).to(L.device) for i in range(3))
            _, loss = L.model(X, target=Y, attention_mask=M)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(L.model.parameters(), 1.0)
            optimizer.step()
            return True

        def consolidated():
            """Se duerme hasta estar consolidado: recuerda lecciones, generaliza sus esquemas y no inventa donde no aplica."""
            L.model.eval()
            scores = []
            if own is not None:
                scores.append(L.exact(*own))
            for sig, g in self.groups(include_archived=False).items():
                fresh = [instantiate(self.space, g["schema"], self.rng, entities) for _ in range(40)]
                scores.append(L.exact(*L.encode(fresh)))
            if use_negatives and L.lessons:
                from .negatives import make_negatives as mk
                negs = mk(self.space, L.lessons, 200, self.rng, entities, L.safe(), ghost_exclude=L.neg_exclude)
                if negs:
                    scores.append(L.exact(*L.encode(negs)))
            L.model.train()
            return (min(scores) if scores else 1.0), scores

        total, extra, score = 0, 200, 1.0
        limit = steps * 3
        while total < limit:
            n = steps if total == 0 else extra
            if not all(one_step() for _ in range(n)):
                break
            total += n
            score, _ = consolidated()
            if score >= 0.97:
                break
        L.model.eval()
        canary = L.canary_score()
        rolled_back = canary < L.canary_min
        if rolled_back:
            L.model.load_state_dict(snapshot)
        return {"canary": canary, "rolled_back": rolled_back, "groups": len(banks), "steps": total, "consolidation": score}

    # ---- ciclo completo -----------------------------------------------
    def run(self, steps: int = 400, use_lessons: bool = True, use_dreams: bool = True, use_negatives: bool = True, neg_per_step: int = 32, max_keep: int = 3,
            ledger: str | None = "reports/ledger.md") -> dict:
        self.mem.tick += 1
        report = {"repair": self.task_repair()}
        before = self.selftest()
        report["before"] = before
        report["compressed"] = self.task_compress(max_keep)
        report["consolidate"] = self.task_consolidate(steps=steps, use_lessons=use_lessons, use_dreams=use_dreams, use_negatives=use_negatives,
                                                   neg_per_step=neg_per_step)
        report["decayed_facts"] = self.mem.decay()
        after = self.selftest()
        report["after"] = after
        if ledger:
            os.makedirs(os.path.dirname(ledger) or ".", exist_ok=True)
            mean = lambda t: (sum(r["probe"] for r in t["groups"]) / len(t["groups"])) if t["groups"] else float("nan")
            with open(ledger, "a", encoding="utf-8") as handle:
                handle.write(f"| {datetime.datetime.now():%Y-%m-%d %H:%M} | tick {self.mem.tick} | esquemas {len(after['groups'])} | "
                             f"generaliza {mean(before):.0%} -> {mean(after):.0%} | canario {after['canary']:.0%} | "
                             f"archivadas {report['compressed']} | revertido {report['consolidate']['rolled_back']} |\n")
        return report
