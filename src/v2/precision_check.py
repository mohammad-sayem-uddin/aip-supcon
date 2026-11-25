"""Check that mean-pooling the cached residue vectors reproduces the v1 pooled embeddings (all sequences); writes results/v2/half_precision_check.csv."""
import numpy as np
import pandas as pd

from src.embed import get_embeddings
from src.v2.common import V2
from src.v2.embed_res import load_residue_cache


def main() -> None:
    rows = []
    for ck in ("esm2_t6_8M", "esm2_t33_650M"):
        idx, res, _ = load_residue_cache(ck)
        seqs, off, ln = idx["sequences"], idx["offsets"], idx["lengths"]
        pooled = np.stack([np.asarray(res[o : o + L], dtype=np.float32).mean(0) for o, L in zip(off, ln)])
        ref = get_embeddings(ck, seqs)
        d = np.abs(pooled - ref)
        rows.append({"checkpoint": ck, "residue_cache_dtype": idx["dtype"], "n_sequences": len(seqs), "max_abs_diff": float(d.max()),
                     "mean_abs_diff": float(d.mean()), "max_abs_value_reference": float(np.abs(ref).max()),
                     "max_abs_diff_relative_to_max_value": float(d.max() / np.abs(ref).max())})
    pd.DataFrame(rows).to_csv(V2 / "half_precision_check.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
