#!/usr/bin/env python3
"""Tables from the chain pickle written by analyze_sampling_convergence.py.

Loads ``chains_*.pkl`` (a list of sample DataFrames, one per chain, seeds
0..m-1), computes R-hat per reaction with ``_gelman_rubin`` imported from the
analysis script given by ``--analysis-script`` (the raven-toolbox
``scripts/analyze_sampling_convergence.py``), and writes:

* ``<tag>_rhat.tsv``: R-hat per reaction (NaN = constant in every chain, not scored);
* ``<tag>.json``: the R-hat summary (reactions, scored, median,
  p90, max, counts and shares above 1.01 and 1.1, worst 10) and, per chain,
  the lag-1 autocorrelation summary of ``single_chain_autocorr.lag1_table``
  (same definitions as the single-chain runs).

Inputs: the pickle, the analysis script, ``--tag`` and ``--out``.

Command line used:
    python summarize_chains.py --pickle <out>/chains_yeast-GEM_achr_m4_n300_t100_w1000.pkl \
        --analysis-script $RAVEN_TOOLBOX_DIR/scripts/analyze_sampling_convergence.py \
        --tag s3_yeast_achr_m4_n300_t100 --out results/
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from single_chain_autocorr import lag1_table, summarize  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--pickle", type=Path, required=True)
    p.add_argument("--analysis-script", type=Path, required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument(
        "--wall-s", type=float, default=None, help="wall time printed by the analysis script"
    )
    args = p.parse_args()

    spec = importlib.util.spec_from_file_location("asc", args.analysis_script)
    asc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(asc)

    with open(args.pickle, "rb") as fh:
        chains = pickle.load(fh)
    r = asc._gelman_rubin(chains)
    scored = r.dropna()
    finite = scored[scored != float("inf")]
    worst = scored.sort_values(ascending=False).head(10)
    out = {
        "tag": args.tag,
        "pickle": str(args.pickle),
        "wall_s": args.wall_s,
        "n_chains": len(chains),
        "n_samples": int(chains[0].shape[0]),
        "n_reactions": int(len(r)),
        "n_constant": int(r.isna().sum()),
        "n_scored": int(len(scored)),
        "n_infinite": int((scored == float("inf")).sum()),
        "median": float(scored.median()),
        "p90": float(scored.quantile(0.9)),
        "max": float(scored.max()),
        "max_finite": float(finite.max()) if len(finite) else None,
        "n_gt_1.01": int((scored > 1.01).sum()),
        "pct_gt_1.01": 100.0 * float((scored > 1.01).mean()),
        "n_gt_1.1": int((scored > 1.1).sum()),
        "pct_gt_1.1": 100.0 * float((scored > 1.1).mean()),
        "worst10": [[k, float(v)] for k, v in worst.items()],
        "per_chain_lag1": [summarize(lag1_table(c), c.shape[0]) for c in chains],
    }
    args.out.mkdir(parents=True, exist_ok=True)
    r.to_csv(args.out / f"{args.tag}_rhat.tsv", sep="\t", float_format="%.6g", header=True)
    with open(args.out / f"{args.tag}.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
