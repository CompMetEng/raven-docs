#!/usr/bin/env python3
"""random_sampling(method="random_objective") with replace_max_bound False and True.

1. Counts the big-M reactions of the model: reactions whose upper bound equals
   the largest upper bound, reactions whose lower bound equals the most
   negative lower bound, and reactions with either (the bounds that
   ``replace_max_bound=True`` replaces with infinity).
2. Runs ``random_sampling(model, n_samples, method="random_objective",
   seed=seed, replace_max_bound=False, n_proc=n_proc)`` and counts, with
   ``|v| >= bound * (1 - 1e-9)`` as "at the bound" (bound = the largest upper
   bound, 1000 in yeast-GEM):
   - entries of the sample matrix (samples x reactions) at the bound, as count
     and share of all entries and of the non-zero entries;
   - samples (rows) with at least one reaction at the bound;
   - reactions at the bound in at least one sample;
   - reactions at zero (``|v| < 1e-9``) in every sample, and the median of the
     per-reaction standard deviation.
3. Runs the same call with ``replace_max_bound=True``, ``n_proc=1`` and the
   ``good_reactions`` of step 2 (they are computed on the finite bounds in
   both cases, so passing them only skips the repeated loopless FVA), and
   records whether it completes or the exception it raises.
4. Diagnostic for step 3: on a copy of the model with the bounds replaced as
   ``replace_max_bound=True`` does, solves ``--n-probe`` random objectives drawn
   as ``_draw_one_sample`` draws them (two reactions from ``good_reactions``,
   weights U(0,1) with random sign) and counts the solver statuses.

Inputs: the SBML model file; ``--out`` directory for the JSON summary;
optionally ``--save-samples`` for the sample matrix of step 2.

Command line used:
    python random_objective_bounds.py --model docs/data/yeast-GEM.xml \
        --n-samples 200 --seed 0 --n-proc 12 --n-probe 50 --out results/ \
        --save-samples $DATA/s7_false.npz
"""

from __future__ import annotations

import argparse
import collections
import json
import time
import traceback
from pathlib import Path

import cobra
import numpy as np


def bigm_counts(model: cobra.Model) -> dict:
    ubs = np.array([r.upper_bound for r in model.reactions])
    lbs = np.array([r.lower_bound for r in model.reactions])
    max_ub, min_lb = ubs.max(), lbs.min()
    at_ub = ubs == max_ub
    at_lb = (lbs == min_lb) if min_lb < 0 else np.zeros_like(at_ub)
    return {
        "n_reactions": int(len(ubs)),
        "max_upper_bound": float(max_ub),
        "min_lower_bound": float(min_lb),
        "n_ub_at_max": int(at_ub.sum()),
        "n_lb_at_min": int(at_lb.sum()),
        "n_ub_or_lb_at_bigM": int((at_ub | at_lb).sum()),
        "n_ub_and_lb_at_bigM": int((at_ub & at_lb).sum()),
    }


def sample_counts(x: np.ndarray, bound: float) -> dict:
    at = np.abs(x) >= bound * (1 - 1e-9)
    nz = np.abs(x) >= 1e-9
    return {
        "n_samples": int(x.shape[0]),
        "n_entries": int(x.size),
        "entries_at_bound": int(at.sum()),
        "entries_at_bound_pct_of_all": 100.0 * at.sum() / x.size,
        "nonzero_entries": int(nz.sum()),
        "entries_at_bound_pct_of_nonzero": 100.0 * at.sum() / max(1, nz.sum()),
        "samples_with_any_reaction_at_bound": int(at.any(axis=1).sum()),
        "samples_with_any_reaction_at_bound_pct": 100.0 * at.any(axis=1).mean(),
        "reactions_at_bound_in_any_sample": int(at.any(axis=0).sum()),
        "reactions_at_bound_in_any_sample_pct_of_all_reactions": 100.0 * at.any(axis=0).mean(),
        "reactions_nonzero_in_any_sample": int(nz.any(axis=0).sum()),
        "reactions_always_zero": int((~nz).all(axis=0).sum()),
        "median_per_reaction_std": float(np.median(x.std(axis=0, ddof=1))),
        "max_abs_flux": float(np.abs(x).max()),
    }


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--n-samples", type=int, default=200)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--n-proc", type=int, default=1)
    p.add_argument("--n-probe", type=int, default=50)
    p.add_argument(
        "--save-samples",
        type=Path,
        default=None,
        help=".npz for the replace_max_bound=False samples",
    )
    args = p.parse_args()

    from raven_toolbox.analysis.sampling import random_sampling

    args.out.mkdir(parents=True, exist_ok=True)
    cobra.Configuration().processes = args.n_proc  # FVA of find_good_reactions
    model = cobra.io.read_sbml_model(str(args.model))
    summary: dict = {
        "model": str(args.model),
        "model_id": model.id,
        "solver_interface": model.solver.interface.__name__,
        "seed": args.seed,
        "bigM": bigm_counts(model),
    }
    bound = summary["bigM"]["max_upper_bound"]

    t0 = time.time()
    res = random_sampling(
        model,
        args.n_samples,
        method="random_objective",
        seed=args.seed,
        replace_max_bound=False,
        n_proc=args.n_proc,
    )
    x = res.samples.to_numpy()
    summary["false"] = {
        "completed": True,
        "wall_s": time.time() - t0,
        "n_proc": args.n_proc,
        "n_good_reactions": len(res.good_reactions),
        **sample_counts(x, bound),
    }
    print(json.dumps(summary, indent=2), flush=True)
    if args.save_samples:
        np.savez_compressed(
            args.save_samples,
            samples=x,
            reactions=np.array(res.samples.columns),
            good_reactions=np.array(res.good_reactions),
        )

    t0 = time.time()
    try:
        res_t = random_sampling(
            model,
            args.n_samples,
            method="random_objective",
            seed=args.seed,
            replace_max_bound=True,
            good_reactions=res.good_reactions,
            n_proc=1,
        )
        summary["true"] = {
            "completed": True,
            "wall_s": time.time() - t0,
            **sample_counts(res_t.samples.to_numpy(), bound),
        }
    except Exception as exc:  # noqa: BLE001
        summary["true"] = {
            "completed": False,
            "wall_s": time.time() - t0,
            "exception": type(exc).__name__,
            "message": str(exc),
            "traceback_tail": traceback.format_exc().splitlines()[-3:],
        }

    m = model.copy()
    max_ub = max(r.upper_bound for r in m.reactions)
    min_lb = min(r.lower_bound for r in m.reactions)
    for r in m.reactions:
        if r.upper_bound == max_ub:
            r.upper_bound = float("inf")
        if min_lb < 0 and r.lower_bound == min_lb:
            r.lower_bound = float("-inf")
    rng = np.random.default_rng(args.seed)
    objs = [m.reactions.get_by_id(r) for r in res.good_reactions]
    statuses = collections.Counter()
    for _ in range(args.n_probe):
        chosen = rng.choice(len(objs), size=2, replace=False)
        w = rng.random(2) * rng.choice((-1.0, 1.0), size=2)
        m.objective = m.problem.Objective(
            sum(wi * objs[j].flux_expression for j, wi in zip(chosen, w, strict=False)),
            direction="max",
        )
        statuses[m.solver.optimize()] += 1
    summary["true_probe_statuses"] = dict(statuses)
    summary["true_probe_n"] = args.n_probe

    with open(args.out / f"s7_random_objective_n{args.n_samples}_seed{args.seed}.json", "w") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
