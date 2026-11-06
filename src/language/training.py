"""Pasos de entrenamiento del oido, compartidos por el entrenamiento inicial y el aprendizaje en conversacion."""
import torch
import torch.nn.functional as F
from .ear import encode_batch, encode_candidates


def batch_loss(ear, batch, pool_texts, rng, device, n_extra=24):
    """batch: dicts (tokens, tags, text, neg[, reject]). Las frases 'reject' solo entrenan el detector de ambito."""
    feat, ids, mask = encode_batch([x["tokens"] for x in batch], device)
    T = feat.shape[1]
    tags = torch.zeros(len(batch), T, dtype=torch.long)
    for i, x in enumerate(batch):
        tags[i, :min(T, len(x["tags"]))] = torch.tensor(x["tags"][:T])
    tags = tags.to(device)
    h, _ = ear(feat, mask)
    keep = torch.tensor([not x.get("reject") for x in batch], device=device)
    scope_loss = F.binary_cross_entropy_with_logits(ear.in_scope(h, mask), keep.float())
    idx = keep.nonzero().squeeze(1)
    if len(idx) == 0:
        return scope_loss, (0.0, 0.0, 0.0, scope_loss.item())
    pos = [batch[i] for i in idx.tolist()]
    hk, idk, mk, tk = h[idx], ids[idx], mask[idx], tags[idx]
    golds = sorted({x["text"] for x in pos})
    extra = [t for t in rng.sample(pool_texts, min(n_extra, len(pool_texts))) if t not in golds]
    cands = golds + extra
    cf, cm, ci = encode_candidates(cands, device)
    scores = ear.score(hk, mk, idk, cf, cm, ci)
    target = torch.tensor([cands.index(x["text"]) for x in pos], device=device)
    pred_loss = F.cross_entropy(scores * 6.0, target)
    _, logits = ear(feat[idx], mk, ear.mark(idk, ci[target]))
    tag_loss = F.cross_entropy(logits[mk], tk[mk])
    pol_target = torch.tensor([float(x["neg"]) for x in pos], device=device)
    pol_loss = F.binary_cross_entropy_with_logits(ear.polarity(hk, mk), pol_target)
    return tag_loss + pred_loss + pol_loss + scope_loss, (tag_loss.item(), pred_loss.item(), pol_loss.item(), scope_loss.item())
