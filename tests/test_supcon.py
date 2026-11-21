import math

import numpy as np
import torch
import torch.nn.functional as F

from src.losses import SupConLoss
from src.model import AIPNet


def _clustered(n_per_class: int, d: int = 8):
    z = torch.zeros(2 * n_per_class, d)
    z[:n_per_class, 0] = 1.0
    z[n_per_class:, 0] = -1.0
    y = torch.cat([torch.zeros(n_per_class), torch.ones(n_per_class)]).long()
    return z, y


def test_perfect_clusters_with_one_positive_is_near_zero():
    # |P(i)| = 1 for every anchor -> analytic floor of the loss is 0
    z, y = _clustered(2)
    assert SupConLoss(0.07)(z, y).item() < 1e-5


def test_perfect_clusters_reach_analytic_floor_log_P():
    # with |P| positives all at similarity 1 the loss floor is log|P| (not 0)
    z, y = _clustered(8)
    loss = SupConLoss(0.07)(z, y).item()
    assert abs(loss - math.log(7)) < 1e-3


def test_permuted_labels_substantially_higher():
    torch.manual_seed(0)
    z, y = _clustered(16)
    z = F.normalize(z + 0.05 * torch.randn_like(z), dim=1)
    good = SupConLoss(0.07)(z, y).item()
    bad = SupConLoss(0.07)(z, y[torch.randperm(len(y))]).item()
    assert bad > good + 1.0


def test_no_nan_single_class_batch():
    z = F.normalize(torch.randn(16, 8), dim=1)
    loss = SupConLoss(0.07)(z, torch.ones(16).long())
    assert torch.isfinite(loss)


def test_no_positive_anchors_returns_zero_not_nan():
    z = F.normalize(torch.randn(2, 8), dim=1)
    z.requires_grad_(True)
    loss = SupConLoss(0.07)(z, torch.tensor([0, 1]))
    assert torch.isfinite(loss) and loss.item() == 0.0
    loss.backward()  # graph stays connected


def test_gradient_flows_to_input():
    z = F.normalize(torch.randn(32, 8), dim=1).requires_grad_(True)
    y = torch.randint(0, 2, (32,))
    SupConLoss(0.1)(z, y).backward()
    assert z.grad is not None and torch.isfinite(z.grad).all() and z.grad.abs().sum() > 0


def test_matches_naive_reference():
    torch.manual_seed(1)
    z = F.normalize(torch.randn(20, 6), dim=1)
    y = torch.randint(0, 2, (20,))
    T = 0.2
    total, cnt = 0.0, 0
    for i in range(20):
        P = [p for p in range(20) if p != i and y[p] == y[i]]
        if not P:
            continue
        den = sum(math.exp(float(z[i] @ z[a]) / T) for a in range(20) if a != i)
        li = -sum(math.log(math.exp(float(z[i] @ z[p]) / T) / den) for p in P) / len(P)
        total += li
        cnt += 1
    assert abs(SupConLoss(T)(z, y).item() - total / cnt) < 1e-5


def test_aipnet_shapes_and_unit_norm():
    net = AIPNet(320).eval()
    out = net(torch.randn(5, 320))
    assert out["embedding"].shape == (5, 256)
    assert out["projection"].shape == (5, 128)
    assert out["logit"].shape == (5,)
    assert np.allclose(out["projection"].norm(dim=1).detach().numpy(), 1.0, atol=1e-5)
