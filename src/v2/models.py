"""Phase B architectures over frozen residue-level ESM-2 embeddings.

Every model maps (x: (B,L,d), mask: (B,L) True=real residue) to
{"embedding": h (256), "projection": z (128, L2-normalised), "logit": (B,)}, so the same BCE + lambda*SupCon
code path applies to all of them. B1 (mean-pool MLP) is the v1 AIPNet and is not re-implemented here.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

ARCHS = ["B2_cnn", "B3_bilstm", "B4_cnn_bilstm", "B5_transformer", "B6_attnpool"]
MAXLEN = 30


def _masked_max(h: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    return h.masked_fill(~mask.unsqueeze(-1), float("-inf")).max(dim=1).values


def _masked_mean(h: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    m = mask.unsqueeze(-1).float()
    return (h * m).sum(1) / m.sum(1).clamp_min(1.0)


class Heads(nn.Module):
    """feature vector -> encoder block -> (embedding, projection, logit); mirrors AIPNet's heads."""

    def __init__(self, in_dim: int, hidden=(256,), proj_dim: int = 128, dropout: float = 0.3):
        super().__init__()
        blocks, d = [], in_dim
        for h in hidden:
            blocks += [nn.Linear(d, h), nn.BatchNorm1d(h), nn.ReLU(), nn.Dropout(dropout)]
            d = h
        self.encoder = nn.Sequential(*blocks)
        self.projection = nn.Linear(d, proj_dim)
        self.classifier = nn.Linear(d, 1)

    def forward(self, f: torch.Tensor) -> dict:
        h = self.encoder(f)
        return {"embedding": h, "projection": F.normalize(self.projection(h), dim=1), "logit": self.classifier(h).squeeze(-1)}


ADAPT = 64  # per-residue linear bottleneck d -> ADAPT (learned), keeps CPU cost feasible and limits overfitting


class Adapter(nn.Module):
    def __init__(self, d: int, out: int = ADAPT, dropout: float = 0.2):
        super().__init__()
        self.lin, self.drop = nn.Linear(d, out), nn.Dropout(dropout)

    def forward(self, x):
        return self.drop(F.relu(self.lin(x)))


class CNN1D(nn.Module):
    def __init__(self, d: int, dropout: float = 0.3, ch: int = 64):
        super().__init__()
        self.ad = Adapter(d)
        self.convs = nn.ModuleList([nn.Conv1d(ADAPT, ch, k, padding=k // 2) for k in (3, 5, 7)])
        self.heads = Heads(3 * ch, dropout=dropout)

    def forward(self, x, mask):
        xt = self.ad(x).transpose(1, 2)
        feats = [_masked_max(F.relu(c(xt)).transpose(1, 2), mask) for c in self.convs]
        return self.heads(torch.cat(feats, dim=1))


def _run_lstm(lstm: nn.LSTM, x: torch.Tensor, lengths: torch.Tensor):
    packed = nn.utils.rnn.pack_padded_sequence(x, lengths.cpu(), batch_first=True, enforce_sorted=False)
    out, (hn, _) = lstm(packed)
    out, _ = nn.utils.rnn.pad_packed_sequence(out, batch_first=True, total_length=x.shape[1])
    return out, hn


class BiLSTM(nn.Module):
    def __init__(self, d: int, dropout: float = 0.3, hid: int = 64):
        super().__init__()
        self.ad = Adapter(d)
        self.lstm = nn.LSTM(ADAPT, hid, num_layers=2, bidirectional=True, batch_first=True, dropout=dropout)
        self.heads = Heads(2 * hid, dropout=dropout)

    def forward(self, x, mask):
        _, hn = _run_lstm(self.lstm, self.ad(x), mask.sum(1))
        return self.heads(torch.cat([hn[-2], hn[-1]], dim=1))  # last layer, forward and backward final states


class CNNBiLSTM(nn.Module):
    def __init__(self, d: int, dropout: float = 0.3, ch: int = 64, hid: int = 64):
        super().__init__()
        self.ad = Adapter(d)
        self.conv = nn.Conv1d(ADAPT, ch, 5, padding=2)
        self.drop = nn.Dropout(dropout)
        self.lstm = nn.LSTM(ch, hid, num_layers=1, bidirectional=True, batch_first=True)
        self.heads = Heads(2 * hid, dropout=dropout)

    def forward(self, x, mask):
        c = self.drop(F.relu(self.conv(self.ad(x).transpose(1, 2))).transpose(1, 2))
        out, _ = _run_lstm(self.lstm, c, mask.sum(1))
        return self.heads(_masked_max(out, mask))


class TransformerEnc(nn.Module):
    def __init__(self, d: int, dropout: float = 0.3):
        super().__init__()
        self.inp = nn.Sequential(Adapter(d), nn.Linear(ADAPT, 128))
        self.pos = nn.Parameter(torch.zeros(1, MAXLEN, 128))
        nn.init.normal_(self.pos, std=0.02)
        layer = nn.TransformerEncoderLayer(128, 4, 256, dropout=0.1, batch_first=True)
        self.enc = nn.TransformerEncoder(layer, 2, enable_nested_tensor=False)
        self.heads = Heads(128, dropout=dropout)

    def forward(self, x, mask):
        h = self.inp(x) + self.pos[:, : x.shape[1]]
        h = self.enc(h, src_key_padding_mask=~mask)
        return self.heads(_masked_mean(h, mask))


class AttnPool(nn.Module):
    """Attention pooling over residues followed by the same 512-256 encoder as the v1 MLP (isolates pooling)."""

    def __init__(self, d: int, dropout: float = 0.3):
        super().__init__()
        self.att = nn.Sequential(nn.Linear(d, 128), nn.Tanh(), nn.Linear(128, 1))
        self.heads = Heads(d, hidden=(512, 256), dropout=dropout)

    def forward(self, x, mask):
        s = self.att(x).squeeze(-1).masked_fill(~mask, float("-inf"))
        w = torch.softmax(s, dim=1).unsqueeze(-1)
        return self.heads((w * x).sum(1))


def build(arch: str, d: int) -> nn.Module:
    return {"B2_cnn": CNN1D, "B3_bilstm": BiLSTM, "B4_cnn_bilstm": CNNBiLSTM, "B5_transformer": TransformerEnc,
            "B6_attnpool": AttnPool}[arch](d)
