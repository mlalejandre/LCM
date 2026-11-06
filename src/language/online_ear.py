"""Correccion del oido DESDE LA CONVERSACION (parche-16).

Cuando el oido entiende mal una frase, el usuario escribe  ENTENDI s p o [NEGADO].
La pareja (frase, significado) se guarda como ejemplo real y el oido se ajusta con:
  - esos ejemplos reales (repetidos, porque son pocos),
  - un repaso de frases generadas (para no olvidar lo ya sabido),
y se REVIERTE si el repaso baja mas de 2 puntos (misma idea que el canario del razonador).
"""
import copy
import json
import os
import random
import torch
from .corpus import HEADS_TRAIN, VERBS_TRAIN, PredicatePool, base_pool, es_pool, make, make_negatives
from .ear import key, predict
from .lexicon import tokenize
from .training import batch_loss


class EarLearner:
    def __init__(self, parser, device="cpu", examples_path="memory/oido_ejemplos.jsonl", ckpt="checkpoints/ear_online.pt"):
        self.parser = parser
        self.ear = parser.ear
        self.device = device
        self.examples_path = examples_path
        self.ckpt = ckpt
        pool = base_pool() + es_pool() + PredicatePool(HEADS_TRAIN, VERBS_TRAIN).items
        self.replay = make(1500, pool, seed=777) + make_negatives(400, seed=779)
        self.probe = make(300, pool, seed=778)
        self.texts = sorted({p[1] for p in pool})
        self.cands = [(p[0], p[1]) for p in {q[1]: q for q in pool}.values()]
        self.examples = self._load()

    def _load(self):
        if not os.path.exists(self.examples_path):
            return []
        with open(self.examples_path, encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def build_example(self, sentence, triple, negated, phrase):
        toks = tokenize(sentence)
        s, p, o = triple
        tags = [0] * len(toks)
        found = False
        for i, t in enumerate(toks):
            if t == s.lower():
                tags[i] = 1
            elif t == o.lower():
                tags[i] = 2
            found = found or t in (s.lower(), o.lower())
        if "son" in phrase.split() and phrase == "son":      # plurales: el nombre aparece con 's'
            for i, t in enumerate(toks):
                if t.startswith(s.lower()) and tags[i] == 0:
                    tags[i] = 1
                elif t.startswith(o.lower()) and tags[i] == 0:
                    tags[i] = 2
        if 1 not in tags or 2 not in tags:
            return None
        return {"tokens": toks, "tags": tags, "pred": p, "text": phrase, "neg": bool(negated), "triple": [s, p, o]}

    def accuracy(self):
        outs = predict(self.ear, [x["tokens"] for x in self.probe], self.cands, self.device)
        return sum((o["subject"], o["predicate"], o["object"], o["negated"]) == (*x["triple"], x["neg"])
                   for o, x in zip(outs, self.probe)) / len(self.probe)

    def learn(self, example, steps=60, lr=3e-4):
        self.examples.append(example)
        before = self.accuracy()
        snapshot = copy.deepcopy(self.ear.state_dict())
        rng = random.Random(len(self.examples))
        opt = torch.optim.AdamW(self.ear.parameters(), lr=lr, weight_decay=0.0)
        texts = sorted(set(self.texts) | {x["text"] for x in self.examples})
        self.ear.train()
        for _ in range(steps):
            real = [rng.choice(self.examples) for _ in range(16)] + [example] * 8
            batch = real + rng.sample(self.replay, 64)
            loss, _ = batch_loss(self.ear, batch, texts, rng, self.device)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(self.ear.parameters(), 1.0)
            opt.step()
        self.ear.eval()
        after = self.accuracy()
        out = predict(self.ear, [example["tokens"]], self.cands + [(example["pred"], example["text"])], self.device)[0]
        got = (out["subject"], out["predicate"], out["object"], out["negated"]) == (*example["triple"], example["neg"])
        accepted = (before - after) <= 0.02
        if not accepted:
            self.ear.load_state_dict(snapshot)
            self.examples.pop()
        else:
            os.makedirs(os.path.dirname(self.examples_path) or ".", exist_ok=True)
            with open(self.examples_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(example, ensure_ascii=False) + "\n")
            os.makedirs(os.path.dirname(self.ckpt) or ".", exist_ok=True)
            torch.save(self.ear.state_dict(), self.ckpt)
        return {"accepted": accepted, "learned": got, "repaso_antes": before, "repaso_despues": after}
