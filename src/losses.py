"""Supervised Contrastive Loss (Khosla et al., 2020), L_out form, single view."""
from __future__ import annotations

import torch
import torch.nn as nn


class SupConLoss(nn.Module):
    def __init__(self, temperature: float = 0.07) -> None:
        super().__init__()
        self.temperature = temperature

    def forward(self, projections: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """projections: (B, D) L2-normalised; labels: (B,). Mean over anchors with >=1 positive."""
        b = projections.shape[0]
        labels = labels.view(-1)
        sim = projections @ projections.T / self.temperature
        eye = torch.eye(b, dtype=torch.bool, device=projections.device)
        # row max over a != i, detached, for numerical stability
        row_max = sim.masked_fill(eye, float("-inf")).max(dim=1, keepdim=True).values.detach()
        row_max = torch.where(torch.isfinite(row_max), row_max, torch.zeros_like(row_max))
        logits = sim - row_max
        denom = (torch.exp(logits) * (~eye)).sum(dim=1, keepdim=True)
        log_prob = logits - torch.log(denom.clamp_min(1e-30))
        pos = (labels[:, None] == labels[None, :]) & ~eye
        n_pos = pos.sum(dim=1)
        valid = n_pos > 0
        if not valid.any():
            return projections.sum() * 0.0
        mean_log_prob_pos = (log_prob * pos).sum(dim=1) / n_pos.clamp_min(1)
        return -mean_log_prob_pos[valid].mean()
