#!/usr/bin/env python3
"""Two checks on stored results of the sampling study.

1. ``--achr-pickle`` / ``--chrr-pickle`` (chain pickles of the e_coli_core ACHR
   and CHRR runs): for each reaction that is constant in every ACHR chain (no
   R-hat), the flux range within each CHRR chain and the mean, to see whether
   CHRR's variation of these reactions is at rounding-error size.
2. ``--s7-npz`` (samples of ``random_objective_bounds.py --save-samples``) and
   ``--bound``: the share of samples at the bound under further denominators
   (entries of the good reactions, reactions at big-M, reactions that are
   non-zero in some sample).

Command line used:
    python posthoc_checks.py --achr-pickle $DATA/S2_.../chains_*.pkl \
        --chrr-pickle $DATA/S5_.../chains_*.pkl --s7-npz $DATA/s7_false.npz \
        --model docs/data/yeast-GEM.xml --out results/posthoc.json
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import numpy as np


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--achr-pickle", type=Path, required=True)
    p.add_argument("--chrr-pickle", type=Path, required=True)
    p.add_argument("--s7-npz", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    out: dict = {}

    achr = pickle.load(open(args.achr_pickle, "rb"))
    chrr = pickle.load(open(args.chrr_pickle, "rb"))
    a = np.stack([c.to_numpy() for c in achr])
    const = [rid for j, rid in enumerate(achr[0].columns) if (a[:, :, j].std(axis=1) == 0).all()]
    rows = {}
    for rid in const:
        v = np.stack([c[rid].to_numpy() for c in chrr])
        rows[rid] = {
            "achr_value": float(achr[0][rid].iloc[0]),
            "chrr_mean": float(v.mean()),
            "chrr_max_range_within_chain": float((v.max(axis=1) - v.min(axis=1)).max()),
        }
    out["ecore_achr_constant_reactions_in_chrr"] = rows

    import cobra

    model = cobra.io.read_sbml_model(str(args.model))
    d = np.load(args.s7_npz, allow_pickle=True)
    x, rxns, good = d["samples"], list(d["reactions"]), set(d["good_reactions"])
    ub = np.array([model.reactions.get_by_id(r).upper_bound for r in rxns])
    bound = ub.max()
    at = np.abs(x) >= bound * (1 - 1e-9)
    gmask = np.array([r in good for r in rxns])
    nz = np.abs(x) >= 1e-9
    out["s7"] = {
        "entries_at_bound": int(at.sum()),
        "pct_of_good_reaction_entries": 100.0 * at[:, gmask].sum() / at[:, gmask].size,
        "reactions_at_bound_any_sample": int(at.any(axis=0).sum()),
        "pct_reactions_at_bound_of_bigM_ub": 100.0
        * at.any(axis=0).sum()
        / int((ub == bound).sum()),
        "pct_reactions_at_bound_of_good": 100.0 * at.any(axis=0).sum() / len(good),
        "pct_reactions_at_bound_of_nonzero_any": 100.0
        * at.any(axis=0).sum()
        / int(nz.any(axis=0).sum()),
        "per_sample_pct_entries_at_bound_mean": float(100.0 * at.mean(axis=1).mean()),
        "pct_of_nonzero_entries_in_good_reactions": 100.0
        * at[:, gmask].sum()
        / max(1, nz[:, gmask].sum()),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
