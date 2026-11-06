"""Aprendizaje al vuelo con repaso y guardia contra el olvido (parche-13).

Medido (ver scripts/evaluate_online.py): ajustar el modelo SOLO con ejemplos
nuevos aprende la regla en pocos ejemplos pero destruye lo anterior (olvido
catastrofico). Mezclar ejemplos antiguos en cada paso (repaso) conserva todo.
La guardia comprueba un conjunto "canario" tras cada actualizacion y revierte
si algo importante se ha roto.
"""
from __future__ import annotations

import copy
from typing import List, Sequence, Tuple

import random

import torch

Triple = Tuple[str, str, str]
Lesson = Tuple[Sequence[Triple], Triple]


class OnlineLearner:
    def __init__(self, model, space, core_pool, canary, device="cpu",
                 lr: float = 1e-3, steps: int = 120, replay_batch: int = 64,
                 canary_min: float = 0.98, use_negatives: bool = True):
        self.model, self.space, self.device = model, space, device
        self.core = tuple(t.cpu() for t in core_pool)       # (X, M, Y) del entrenamiento original
        self.canary = tuple(t.to(device) for t in canary)
        self.lr, self.steps, self.replay_batch, self.canary_min = lr, steps, replay_batch, canary_min
        self.lessons: List[Lesson] = []
        self.use_negatives = use_negatives
        self.neg_exclude = set()          # relaciones que NO se usan como negativos (para medir generalizacion)
        self._safe = (-1, [])
        self.rng = random.Random(0)

    # ---- utilidades ---------------------------------------------------
    def encode(self, lessons: Sequence[Lesson]):
        length = self.model.config.max_concept_seq
        X = torch.zeros(len(lessons), length, self.space.d_concept)
        M = torch.zeros(len(lessons), length, dtype=torch.bool)
        Y = []
        for i, (premises, conclusion) in enumerate(lessons):
            for j, premise in enumerate(premises):
                X[i, j] = self.space.encode_proposition(*premise)
                M[i, j] = True
            Y.append(self.space.encode_proposition(*conclusion))
        from ..memory.negatives import purge_ghosts
        purge_ghosts(self.space)            # las relaciones fantasma solo viven durante la codificacion
        return X, M, torch.stack(Y)

    @torch.no_grad()
    def exact(self, X, M, Y) -> float:
        was_training = self.model.training
        self.model.eval()
        X, M, Y = X.to(self.device), M.to(self.device), Y.to(self.device)
        pred, _ = self.model(X, attention_mask=M)
        got = self.model.read_slots(pred.unsqueeze(1))[:, 0]
        want = self.model.read_slots(Y.unsqueeze(1))[:, 0]
        self.model.train(was_training)
        return float((got == want).all(dim=-1).float().mean().item())

    def entities(self):
        from ..memory.schema import is_entity
        return [n for n in self.space.concept_to_id if is_entity(self.space, n)]

    def safe(self):
        from ..memory.negatives import safe_predicates
        if self._safe[0] != len(self.space.concept_to_id):
            self._safe = (len(self.space.concept_to_id), safe_predicates(self.space))
        return [q for q in self._safe[1] if q not in self.neg_exclude]

    def negatives(self, lessons, n: int = 200):
        """Casos hermanos donde la regla NO aplica (parche-20). Devuelve tensores (X, M, Y) o None."""
        if not self.use_negatives or not lessons:
            return None
        from ..memory.negatives import make_negatives
        negs = make_negatives(self.space, lessons, n, self.rng, self.entities(), self.safe(), ghost_exclude=self.neg_exclude)
        return self.encode(negs) if negs else None

    def canary_score(self) -> float:
        return self.exact(*self.canary)

    # ---- aprendizaje --------------------------------------------------
    def learn(self, lessons: Sequence[Lesson], replay_core: bool = True,
              replay_lessons: bool = True, guard: bool = True) -> dict:
        new = self.encode(lessons)
        past = self.encode(self.lessons) if (replay_lessons and self.lessons) else None
        neg = self.negatives(list(self.lessons) + list(lessons))
        reps = max(1, -(-16 // len(new[0])))                  # las lecciones nuevas pesan lo mismo que sus negativos
        new_train = tuple(t.repeat(reps, *([1] * (t.dim() - 1))) for t in new)
        snapshot = copy.deepcopy(self.model.state_dict())
        before = self.exact(*new)
        self.model.train()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=0.0)
        for _round in range(6 if neg is not None else 3):  # mas rondas si aun no acierta la propia leccion
            for _ in range(self.steps):
                parts = [new_train]
                if replay_core:
                    j = torch.randint(0, len(self.core[0]), (self.replay_batch,))
                    parts.append(tuple(t[j] for t in self.core))
                if past is not None:
                    j = torch.randint(0, len(past[0]), (min(self.replay_batch, len(past[0])),))
                    parts.append(tuple(t[j] for t in past))
                if neg is not None:
                    j = torch.randint(0, len(neg[0]), (min(32, len(neg[0])),))
                    parts.append(tuple(t[j] for t in neg))
                X, M, Y = (torch.cat([p[k] for p in parts]).to(self.device) for k in range(3))
                _, loss = self.model(X, target=Y, attention_mask=M)
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
            self.model.eval()
            if self.exact(*new) >= 1.0:
                break
            self.model.train()
        self.model.eval()
        after = self.exact(*new)
        canary = self.canary_score()
        accepted = True
        if guard and canary < self.canary_min:
            self.model.load_state_dict(snapshot)   # revertir: no se rompe lo ya sabido
            accepted = False
        elif accepted:
            self.lessons.extend(lessons)
        return {"accepted": accepted, "before": before, "after": after, "canary": canary}

    def inoculate(self, preds, n: int = 240, steps: int = 60, lr: float = 5e-4) -> dict:
        """Relaciones NUEVAS (parche-33): ensena en el momento que, mientras no haya una regla, X <relacion> Y no concluye nada.
        Casos negativos con solo esas relaciones + repaso de fabrica y de lecciones; si el canario baja, se revierte."""
        preds = [q for q in preds if q in self.space.concept_to_id]
        if not preds or not self.lessons:
            return {"done": False, "reason": "sin lecciones o sin relaciones nuevas"}
        from ..memory.negatives import make_negatives
        negs = make_negatives(self.space, self.lessons, n, self.rng, self.entities(), preds, ghosts=0.0)
        if not negs:
            return {"done": False, "reason": "sin negativos"}
        neg = self.encode(negs)
        own = self.encode(self.lessons)
        from ..memory.schema import induce, instantiate
        schemas = {}
        for prem, concl in self.lessons:
            sc = induce(self.space, [tuple(x) for x in prem], tuple(concl))
            schemas[sc.signature] = sc
        ents = self.entities()
        banks = [self.encode([instantiate(self.space, sc, self.rng, ents) for _ in range(200)]) for sc in schemas.values()]
        snapshot = copy.deepcopy(self.model.state_dict())
        self.model.train()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=0.0)
        for _ in range(steps):
            parts = []
            j = torch.randint(0, len(self.core[0]), (self.replay_batch,))
            parts.append(tuple(t[j] for t in self.core))
            j = torch.randint(0, len(own[0]), (min(self.replay_batch, len(own[0])),))
            parts.append(tuple(t[j] for t in own))
            j = torch.randint(0, len(neg[0]), (min(48, len(neg[0])),))
            parts.append(tuple(t[j] for t in neg))
            for X_, M_, Y_ in banks:                    # "suenos": la regla debe seguir generalizando a gente nueva
                j = torch.randint(0, len(X_), (24,))
                parts.append((X_[j], M_[j], Y_[j]))
            X, M, Y = (torch.cat([p[k] for p in parts]).to(self.device) for k in range(3))
            _, loss = self.model(X, target=Y, attention_mask=M)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            optimizer.step()
        self.model.eval()
        canary = self.canary_score()
        if canary < self.canary_min:
            self.model.load_state_dict(snapshot)
            return {"done": False, "reason": f"revertido (canario {canary:.0%})", "canary": canary}
        return {"done": True, "canary": canary, "lessons": self.exact(*own)}
