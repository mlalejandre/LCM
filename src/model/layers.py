import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        var = x.pow(2).mean(-1, keepdim=True)
        return x * torch.rsqrt(var + self.eps) * self.weight


class ContinuousAttention(nn.Module):
    """Atencion causal sobre vectores continuos con mascara de padding."""
    def __init__(self, d_concept: int, n_heads: int, max_len: int, dropout: float = 0.0):
        super().__init__()
        if d_concept % n_heads != 0:
            raise ValueError("d_concept debe ser divisible por n_heads.")
        self.n_heads = n_heads
        self.head_dim = d_concept // n_heads
        self.q = nn.Linear(d_concept, d_concept, bias=False)
        self.k = nn.Linear(d_concept, d_concept, bias=False)
        self.v = nn.Linear(d_concept, d_concept, bias=False)
        self.out = nn.Linear(d_concept, d_concept, bias=False)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, attention_mask: torch.Tensor = None) -> torch.Tensor:
        batch, length, channels = x.shape
        q = self.q(x).view(batch, length, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k(x).view(batch, length, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.v(x).view(batch, length, self.n_heads, self.head_dim).transpose(1, 2)

        scores = (q @ k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        causal = torch.tril(torch.ones(length, length, device=x.device, dtype=torch.bool))
        scores = scores.masked_fill(~causal.view(1, 1, length, length), float("-inf"))
        if attention_mask is not None:
            valid_keys = attention_mask.to(device=x.device, dtype=torch.bool).view(batch, 1, 1, length)
            scores = scores.masked_fill(~valid_keys, float("-inf"))
        probs = self.drop(F.softmax(scores, dim=-1))
        out = (probs @ v).transpose(1, 2).contiguous().view(batch, length, channels)
        return self.out(out)


class ConceptBlock(nn.Module):
    def __init__(self, d_concept: int, n_heads: int, max_len: int, dropout: float):
        super().__init__()
        self.norm1 = RMSNorm(d_concept)
        self.attn = ContinuousAttention(d_concept, n_heads, max_len, dropout)
        self.norm2 = RMSNorm(d_concept)
        self.mlp = nn.Sequential(
            nn.Linear(d_concept, d_concept * 4, bias=False),
            nn.SiLU(),
            nn.Linear(d_concept * 4, d_concept, bias=False),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor, attention_mask: torch.Tensor = None) -> torch.Tensor:
        x = x + self.attn(self.norm1(x), attention_mask=attention_mask)
        x = x + self.mlp(self.norm2(x))
        return x
