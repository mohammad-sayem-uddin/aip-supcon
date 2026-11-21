import numpy as np
import pandas as pd

from src.data import build_regime_c, max_identity_to_train, pairwise_identity


def test_identical_is_one():
    assert pairwise_identity("ACDEFGHIKL", "ACDEFGHIKL") == 1.0


def test_one_substitution_in_ten():
    assert abs(pairwise_identity("ACDEFGHIKL", "ACDEFGHIKM") - 0.9) < 1e-9


def test_unrelated_is_low():
    assert pairwise_identity("AAAAAAAAAA", "WWWWWWWWWW") == 0.0


def test_normalised_by_shorter_sequence():
    # shorter sequence fully contained in the longer one -> identity 1.0
    assert pairwise_identity("DEFGH", "ACDEFGHIKL") == 1.0


def test_prefilter_matches_brute_force():
    train = ["ACDEFGHIKL", "MNPQRSTVWY", "ACDEFGHIKM", "GGGGGGGGGG"]
    test = ["ACDEFGHIKL", "ACDEFGHIKQ", "WWWWWWWWWW"]
    fast = max_identity_to_train(test, train, floor=0.8)
    for i, s in enumerate(test):
        brute = max(pairwise_identity(s, t) for t in train)
        if brute >= 0.8:
            assert abs(fast[i] - brute) < 1e-9
        else:
            assert fast[i] < 0.8


def test_build_regime_c_removes_near_duplicates():
    train = pd.DataFrame({"sequence": ["ACDEFGHIKL"], "label": [1]})
    test = pd.DataFrame({"sequence": ["ACDEFGHIKM", "WWWWWWWWWW"], "label": [1, 0]})
    c = build_regime_c(train, test, threshold=0.9)
    assert list(c["sequence"]) == ["WWWWWWWWWW"]
