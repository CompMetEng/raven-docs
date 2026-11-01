#!/usr/bin/env python3
"""Lag-1 autocorrelation and ESS of one ACHR chain of raven-toolbox's random_sampling.

Runs one chain ``random_sampling(model, n_samples, method="achr", seed=seed,
thinning=thinning, warmup=warmup)`` (``warmup`` is ignored by ACHR, it is passed
for compatibility with the other samplers), and computes per reaction the lag-1 autocorrelation of the
stored samples. The operational definitions are:

* non-constant reaction: ``max - min`` of the reaction's flux over the chain is
  larger than ``--const-tol`` (default 1e-6). Other reactions get no rho.
* ``rho_pearson``: Pearson correlation of ``x[0:n-1]`` with ``x[1:n]``
  (``pandas.Series.autocorr(lag=1)``).
* ``rho_acf``: the standard autocorrelation-function estimator
  ``sum_t (x_t - m)(x_{t+1} - m) / sum_t (x_t - m)^2`` with the mean ``m`` of the
  whole chain (as in ``statsmodels.tsa.stattools.acf``).
* the combined rho of the chain is the mean over non-constant reactions of
  ``rho_pearson`` (the primary number); the median of ``rho_pearson``, the mean
  and median of ``rho_acf`` are reported next to it.
* ESS uses the formula ``n (1 - rho) / (1 + rho)`` on the combined rho;
  the median over reactions of the per-reaction ESS is also reported.

Wall times: ``t_read`` (``read_sbml_model``), ``t_sample`` (the
``random_sampling`` call: ACHR warmup points plus the sampling) and their sum.
With ``--time-warmup`` the script afterwards builds
``cobra.sampling.ACHRSampler(model, thinning=thinning, seed=seed)`` once more
on a fresh copy of the model and times it, which is the warmup-point part of
``t_sample``.

Inputs: the SBML model file; ``--out`` directory for the JSON summary and the
per-reaction TSV (and, with ``--save-samples``, the sample matrix as .npz).

Command line used (one Slurm job per thinning):
    python single_chain_autocorr.py --model docs/data/yeast-GEM.xml \
        --thinning 20 --n-samples 300 --warmup 1000 --seed 0 --time-warmup \
        --out results/
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cobra
import numpy as np
import pandas as pd


def lag1_table(samples: pd.DataFrame, const_tol: float = 1e-6) -> pd.DataFrame:
    """Per-reaction range, lag-1 autocorrelations and ESS of one chain (samples x reactions)."""
    x = samples.to_numpy(dtype=float)
    n = x.shape[0]
    rng = x.max(axis=0) - x.min(axis=0)
    nonconst = rng > const_tol
    d = x - x.mean(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        acf = (d[:-1] * d[1:]).sum(axis=0) / (d * d).sum(axis=0)
        a, b = x[:-1], x[1:]
        da, db = a - a.mean(axis=0), b - b.mean(axis=0)
        pear = (da * db).sum(axis=0) / np.sqrt((da * da).sum(axis=0) * (db * db).sum(axis=0))
    acf[~nonconst] = np.nan
    pear[~nonconst] = np.nan
    ess = n * (1 - pear) / (1 + pear)
    return pd.DataFrame(
        {
            "range": rng,
            "nonconstant": nonconst,
            "rho_pearson": pear,
            "rho_acf": acf,
            "ess_pearson": ess,
        },
        index=samples.columns,
    )


def summarize(tab: pd.DataFrame, n: int) -> dict:
    p = tab["rho_pearson"].dropna()
    a = tab["rho_acf"].dropna()
    rho = float(p.mean())
    return {
        "n_samples": n,
        "n_reactions": int(len(tab)),
        "n_nonconstant": int(tab["nonconstant"].sum()),
        "rho_mean_pearson": rho,
        "rho_median_pearson": float(p.median()),
        "rho_mean_acf": float(a.mean()),
        "rho_median_acf": float(a.median()),
        "rho_p10_pearson": float(p.quantile(0.1)),
        "rho_p90_pearson": float(p.quantile(0.9)),
        "ess_from_mean_rho": n * (1 - rho) / (1 + rho),
        "ess_from_median_rho": n * (1 - float(p.median())) / (1 + float(p.median())),
        "ess_median_per_reaction": float(tab["ess_pearson"].dropna().median()),
    }


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--thinning", type=int, required=True)
    p.add_argument("--n-samples", type=int, default=300)
    p.add_argument("--warmup", type=int, default=1000)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--const-tol", type=float, default=1e-6)
    p.add_argument("--time-warmup", action="store_true")
    p.add_argument("--save-samples", type=Path, default=None)
    args = p.parse_args()

    from raven_toolbox.analysis.sampling import random_sampling

    args.out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    model = cobra.io.read_sbml_model(str(args.model))
    t1 = time.time()
    res = random_sampling(
        model,
        args.n_samples,
        method="achr",
        seed=args.seed,
        thinning=args.thinning,
        warmup=args.warmup,
    )
    t2 = time.time()
    samples = res.samples
    tab = lag1_table(samples, args.const_tol)
    summary = {
        "model": str(args.model),
        "model_id": model.id,
        "solver_interface": model.solver.interface.__name__,
        "thinning": args.thinning,
        "warmup_arg": args.warmup,
        "seed": args.seed,
        "n_warmup_points": getattr(res, "n_warmup", None),
        "const_tol": args.const_tol,
        "t_read_s": t1 - t0,
        "t_sample_s": t2 - t1,
        "t_total_s": t2 - t0,
        **summarize(tab, samples.shape[0]),
    }
    if args.time_warmup:
        from cobra.sampling import ACHRSampler

        m2 = cobra.io.read_sbml_model(str(args.model))
        t3 = time.time()
        ACHRSampler(m2, thinning=args.thinning, seed=args.seed)
        summary["t_achr_warmup_points_s"] = time.time() - t3
    stem = f"s1_achr_t{args.thinning}_n{args.n_samples}_seed{args.seed}"
    tab.to_csv(args.out / f"{stem}_per_reaction.tsv", sep="\t", float_format="%.6g")
    with open(args.out / f"{stem}.json", "w") as fh:
        json.dump(summary, fh, indent=2)
    if args.save_samples:
        np.savez_compressed(
            args.save_samples, samples=samples.to_numpy(), reactions=np.array(samples.columns)
        )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
