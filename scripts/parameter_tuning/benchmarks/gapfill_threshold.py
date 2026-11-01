"""connect_blocked_reactions threshold on a synthetic supply-limited gap.

The synthetic model is:

* draft: metabolites A[c] and B[c]; EX_A (A <=>, lower bound -0.5: uptake of at most
  0.5); R_AB (A -> B, irreversible, bounds 0..1000). B is a dead end, so R_AB is blocked.
* template: B[c] and EX_B (B ->, bounds 0..1000).

``connect_blocked_reactions(draft, template, threshold=t)`` is run for t in 0.01, 0.1, 0.5, 1.0 (1.0 is the default) and the other
arguments at their defaults (min_flux 0.1, penalty 1.0, allow_net_production False).
The result lists the reactions added to fill the gap at each threshold.

Solver: Gurobi. Output: log and the JSON file given by ``--out``.

Command line (see sbatch_sweep.sh):
    $BENCH_PY gapfill_threshold.py --out $OUT/gapfill_threshold.json
"""

import argparse
import json
import os
import sys

import cobra

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from versions import versions  # noqa: E402

from raven_toolbox.gapfilling import connect_blocked_reactions  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--out", required=True)
args = ap.parse_args()


def met(mid, name):
    return cobra.Metabolite(mid, name=name, compartment="c")


def draft():
    m = cobra.Model("draft")
    m.solver = "gurobi"
    a, b = met("A_c", "A"), met("B_c", "B")
    ex = cobra.Reaction("EX_A", lower_bound=-0.5, upper_bound=1000)
    ex.add_metabolites({a: -1})
    rab = cobra.Reaction("R_AB", lower_bound=0, upper_bound=1000)
    rab.add_metabolites({a: -1, b: 1})
    m.add_reactions([ex, rab])
    return m


def template():
    t = cobra.Model("template")
    t.solver = "gurobi"
    exb = cobra.Reaction("EX_B", lower_bound=0, upper_bound=1000)
    exb.add_metabolites({met("B_c", "B"): -1})
    t.add_reactions([exb])
    return t


rows = []
for thr in (0.01, 0.1, 0.5, 1.0):
    d = draft()
    r = connect_blocked_reactions(d, template(), threshold=thr)
    with r.model as fm:
        fm.objective = "R_AB"
        max_ab = fm.slim_optimize()
    row = {
        "threshold": thr,
        "added": r.added_reactions,
        "newly_connected": r.newly_connected,
        "cannot_connect": r.cannot_connect,
        "R_AB_max_after": max_ab,
    }
    print(json.dumps(row))
    rows.append(row)
out = {"rows": rows, "versions": versions(d)}
print("versions", json.dumps(out["versions"]))
with open(args.out, "w") as f:
    json.dump(out, f, indent=1)
