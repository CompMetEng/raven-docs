"""One ftINIT build (full pipeline or first N steps) with step records.

Scores the Hart2015 column --cell as Human-GEM 1ea27d8b estimateEssentialGenes.py
does, runs ftinit (series 1+1, first --nsteps steps, big_m=BIG_M 100,
mip_gap_abs=MIP_GAP_ABS 10, time_limit --tl) with --rt/--pag/--seed/--threads,
records objective, status, gap and time of every step (wrapping the private
_solve_step), the warnings, reaction and gene ids, growth and, with --essential 1,
the essential genes (find_essential_genes). Writes a JSON list (one entry per --repeat).
Command line: python build.py --prep P.pkl --out X.json [--cell DLD1] [--seed 1234]
              [--threads 1] [--rt 0|1] [--pag V] [--nsteps 2] [--fill-gaps 1] [--tl 1800]
              [--essential 0|1] [--repeat 1]
"""

import argparse
import json
import pickle
import sys
import time
import warnings

import cobra

sys.setrecursionlimit(10000)
cobra.Configuration().processes = 1
import raven_toolbox.init  # noqa
from raven_toolbox.init import (  # noqa: E402
    ftinit,
    get_init_steps,
)

FT = sys.modules["raven_toolbox.init.ftinit"]
import estimateEssentialGenes as eeg  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--prep", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--cell", default="DLD1")
ap.add_argument("--seed", type=int, default=1234)
ap.add_argument("--threads", type=int, default=1)
ap.add_argument("--rt", type=int, default=0)
ap.add_argument("--pag", type=float)
ap.add_argument("--nsteps", type=int, default=2)
ap.add_argument("--fill-gaps", type=int, default=1)
ap.add_argument("--tl", type=float, default=1800.0)
ap.add_argument("--essential", type=int, default=0)
ap.add_argument("--repeat", type=int, default=1)
a = ap.parse_args()

prep = pickle.load(open(a.prep, "rb"))
tissues, expr = eeg._read_rnaseq(eeg.RNASEQ_FILE)
gs = eeg.gene_scores_from_expression(expr[a.cell], eeg.EXPRESSION_THRESHOLD)
rs = eeg.score_reactions_from_genes(prep.ref_model, gs)

records = []
orig = FT._solve_step


def wrapped(*args, **kw):
    t = time.time()
    res = orig(*args, **kw)
    records.append(
        {
            "step": len(records) + 1,
            "objective": res.objective,
            "status": res.status,
            "achieved_gap": res.achieved_gap,
            "n_on": len(res.on_reactions),
            "n_kept_min": len(res.kept_reactions),
            "seconds": round(time.time() - t, 1),
        }
    )
    print("STEPREC", json.dumps(records[-1]), flush=True)
    return res


FT._solve_step = wrapped

results = []
for rep in range(a.repeat):
    records.clear()
    steps = get_init_steps("1+1")[: a.nsteps]
    t0 = time.time()
    with warnings.catch_warnings(record=True) as W:
        warnings.simplefilter("always")
        m = ftinit(
            prep,
            rxn_scores=rs,
            gene_scores=gs,
            steps=steps,
            fill_gaps=bool(a.fill_gaps),
            big_m=eeg.BIG_M,
            mip_gap_abs=eeg.MIP_GAP_ABS,
            time_limit=a.tl,
            resolve_ties=bool(a.rt),
            prove_abs_gap=a.pag,
            seed=a.seed,
            threads=a.threads,
            verbose=True,
        )
    wall = time.time() - t0
    out = {
        "args": vars(a),
        "rep": rep,
        "wall_s": round(wall, 1),
        "steps": list(records),
        "warnings": [str(w.message)[:160] for w in W],
        "reactions": sorted(r.id for r in m.reactions),
        "genes": sorted(g.id for g in m.genes),
    }
    try:
        out["growth"] = float(m.slim_optimize())
    except Exception as e:  # noqa
        out["growth"] = None
    print("TIMING build", round(wall), "s rxns", len(m.reactions), "warnings", len(W), flush=True)
    if a.essential:
        from cobra.flux_analysis import find_essential_genes

        t1 = time.time()
        ess = find_essential_genes(m, processes=1)
        out["essential"] = sorted(g.id for g in ess)
        out["essential_s"] = round(time.time() - t1)
        print("essential", len(ess), flush=True)
    results.append(out)
    json.dump(results, open(a.out, "w"))
