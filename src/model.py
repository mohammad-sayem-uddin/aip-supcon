"""AIPNet: shared encoder, L2-normalised projection head, single-logit classifier head."""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class AIPNet(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: tuple[int, ...] = (512, 256),
                 proj_dim: int = 128, dropout: float = 0.3) -> None:
        super().__init__()
        blocks: list[nn.Module] = []
        d = input_dim
        for h in hidden_dims:
            blocks += [nn.Linear(d, h), nn.BatchNorm1d(h), nn.ReLU(), nn.Dropout(dropout)]
            d = h
        self.encoder = nn.Sequential(*blocks)
        self.projection = nn.Linear(d, proj_dim)
        self.classifier = nn.Linear(d, 1)

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        h = self.encoder(x)
        z = F.normalize(self.projection(h), p=2, dim=1)
        logit = self.classifier(h).squeeze(-1)
        return {"embedding": h, "projection": z, "logit": logit}
