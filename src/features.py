"""Classical peptide descriptors: AAC, DPC, CTD and normalised length.

Citations (for thesis Chapter 3):
  AAC / DPC: Bhasin M, Raghava GPS (2004) Classification of nuclear receptors based on amino acid composition
    and dipeptide composition. J Biol Chem 279:23262-23266.
  CTD: Dubchak I, Muchnik I, Holbrook SR, Kim SH (1995) Prediction of protein folding class using global
    description of amino acid sequence. PNAS 92:8700-8704; property groups as implemented in Cai et al. (2003)
    Nucleic Acids Res 31:3692-3697 (PROFEAT) and Dong et al. (2018) propy3.
"""
from __future__ import annotations

import numpy as np

AA = "ACDEFGHIKLMNPQRSTVWY"
_IDX = {a: i for i, a in enumerate(AA)}

# 7 physicochemical properties x 3 classes (Dubchak et al. 1995)
CTD_GROUPS = {
    "hydrophobicity": ("RKEDQN", "GASTPHY", "CLVIMFW"),
    "vdw_volume": ("GASTPDC", "NVEQIL", "MHKFRYW"),
    "polarity": ("LIFWCMVY", "PAGST", "HQRKNED"),
    "polarizability": ("GASDT", "CPNVEQIL", "KMHFRYW"),
    "charge": ("KR", "ANCQGHILMFPSTWYV", "DE"),
    "secondary_structure": ("EALMQKRH", "VIYCWFT", "GNPSD"),
    "solvent_accessibility": ("ALFCGIVW", "RKQEND", "MPSTHY"),
}
MAX_LEN = 30.0


def aac(seqs: list[str]) -> np.ndarray:
    """20-d amino acid composition (fraction of each residue)."""
    out = np.zeros((len(seqs), 20), dtype=np.float32)
    for r, s in enumerate(seqs):
        for ch in s:
            out[r, _IDX[ch]] += 1
        out[r] /= len(s)
    return out


def dpc(seqs: list[str]) -> np.ndarray:
    """400-d dipeptide composition (fraction of each ordered residue pair)."""
    out = np.zeros((len(seqs), 400), dtype=np.float32)
    for r, s in enumerate(seqs):
        for a, b in zip(s[:-1], s[1:]):
            out[r, _IDX[a] * 20 + _IDX[b]] += 1
        out[r] /= max(len(s) - 1, 1)
    return out


def _ctd_one(s: str) -> list[float]:
    n = len(s)
    feats: list[float] = []
    for groups in CTD_GROUPS.values():
        cls = np.array([next(i for i, g in enumerate(groups) if ch in g) for ch in s])
        # Composition: fraction of residues in each class
        feats += [float((cls == k).mean()) for k in range(3)]
        # Transition: fraction of adjacent pairs that switch between class pair (0,1), (0,2), (1,2)
        a, b = cls[:-1], cls[1:]
        for x, y in ((0, 1), (0, 2), (1, 2)):
            feats.append(float((((a == x) & (b == y)) | ((a == y) & (b == x))).sum()) / max(n - 1, 1))
        # Distribution: position (% of length) of the 1st, 25%, 50%, 75% and last residue of each class
        for k in range(3):
            pos = np.where(cls == k)[0] + 1
            if len(pos) == 0:
                feats += [0.0] * 5
                continue
            m = len(pos)
            ranks = [1, max(int(np.floor(0.25 * m)), 1), max(int(np.floor(0.5 * m)), 1),
                     max(int(np.floor(0.75 * m)), 1), m]
            feats += [100.0 * pos[r - 1] / n for r in ranks]
    return feats


def ctd(seqs: list[str]) -> np.ndarray:
    """147-d Composition-Transition-Distribution (7 properties x (3 C + 3 T + 15 D))."""
    return np.array([_ctd_one(s) for s in seqs], dtype=np.float32)


def length_feat(seqs: list[str]) -> np.ndarray:
    """Sequence length divided by 30 (the maximum peptide length in the data)."""
    return np.array([[len(s) / MAX_LEN] for s in seqs], dtype=np.float32)


_FUNCS = {"aac": aac, "dpc": dpc, "ctd": ctd, "len": length_feat}


def combine(seqs: list[str], which: tuple[str, ...] = ("aac", "dpc", "ctd")) -> np.ndarray:
    return np.hstack([_FUNCS[w](seqs) for w in which])
