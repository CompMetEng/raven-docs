"""remove_genes on e_coli_core and fseof flux_eps on iJO1366.

1. e_coli_core (cobrapy ``textbook.xml.gz``): delete gene b1779 (the only gene of GAPD)
   with ``remove_genes`` for ``blocked_reactions`` in "constrain", "remove", "keep" and
   with no keyword (default); print reactions left, ``slim_optimize()`` and GAPD bounds;
   then the unmodified model.
2. iJO1366 (cobrapy ``iJO1366.xml.gz``, its own biomass objective): ``fseof`` with target
   ``EX_succ_e`` at ``flux_eps`` 1e-8, 1e-7, 1e-6, other arguments at their defaults;
   print the number of targets per ``target_type``. ``--repeats`` runs per value
   (each on a freshly read model).

Solver: Gurobi through optlang (``model.solver = "gurobi"``).

Inputs: the SBML files in the ``cobra/data`` folder of the running cobra, unzipped to
``$TMPDIR``. Output: log on stdout and the JSON file given by ``--out``.

Command line (see sbatch_small.sh):
    $BENCH_PY small.py --out $OUT/small.json --repeats 3
with PYTHONPATH=<raven-toolbox checkout>/src (env_py.sh).
"""

import argparse
import gzip
import hashlib
import json
import os
import shutil
import sys
import time

import cobra
from cobra.io import read_sbml_model

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from versions import versions  # noqa: E402

from raven_toolbox.analysis import fseof  # noqa: E402
from raven_toolbox.manipulation import remove_genes  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--out", required=True, help="JSON result file")
ap.add_argument("--repeats", type=int, default=1, help="fseof runs per flux_eps value")
ap.add_argument("--tmp", default=os.environ.get("TMPDIR", "/tmp"), help="scratch folder")
args = ap.parse_args()

data = os.path.join(os.path.dirname(cobra.__file__), "data")
tmp = args.tmp
res = {"inputs": {}, "remove_genes": [], "fseof": []}
for n in ("textbook", "iJO1366"):
    src = f"{data}/{n}.xml.gz"
    with open(src, "rb") as f:
        res["inputs"][n] = {"path": src, "sha256": hashlib.sha256(f.read()).hexdigest()}
    with gzip.open(src) as f, open(f"{tmp}/{n}.xml", "wb") as o:
        shutil.copyfileobj(f, o)
shutil.copy(f"{tmp}/textbook.xml", f"{tmp}/e_coli_core.xml")

print("=== remove_genes e_coli_core")
for mode in ("constrain", "remove", "keep", None):
    m = read_sbml_model(f"{tmp}/e_coli_core.xml")
    m.solver = "gurobi"
    if mode is None:
        remove_genes(m, "b1779")
        mode = "default"
    else:
        try:
            remove_genes(m, "b1779", blocked_reactions=mode)
        except Exception as e:  # noqa: BLE001
            print(mode, "ERR", e)
            continue
    g = m.slim_optimize()
    gap = m.reactions.GAPD if "GAPD" in m.reactions else None
    print(
        mode,
        "reactions",
        len(m.reactions),
        "growth %.4f" % g,  # noqa: UP031
        "GAPD bounds",
        gap.bounds if gap else "removed",
    )
    res["remove_genes"].append(
        {
            "call": mode,
            "reactions": len(m.reactions),
            "growth": g,
            "GAPD": list(gap.bounds) if gap else "removed",
            "GAPD_gpr": gap.gene_reaction_rule if gap else None,
        }
    )
m = read_sbml_model(f"{tmp}/e_coli_core.xml")
m.solver = "gurobi"
g = m.slim_optimize()
print("unmodified", len(m.reactions), "growth %.4f" % g)  # noqa: UP031
res["remove_genes"].append({"call": "unmodified", "reactions": len(m.reactions), "growth": g})

print("=== fseof iJO1366")
for rep in range(1, args.repeats + 1):
    m = read_sbml_model(f"{tmp}/iJO1366.xml")
    m.solver = "gurobi"
    growth = m.slim_optimize()
    print(
        "rep",
        rep,
        "reactions",
        len(m.reactions),
        "objective",
        m.objective.expression,
        "growth",
        growth,
    )
    for eps in (1e-8, 1e-7, 1e-6):
        t0 = time.time()
        r = fseof(m, target_rxn="EX_succ_e", flux_eps=eps)
        t = r.targets
        counts = t.target_type.value_counts().to_dict()
        print(
            "rep",
            rep,
            "EX_succ_e flux_eps",
            eps,
            "n_targets",
            len(t),
            counts,
            "enforced",
            r.enforced[0],
            r.enforced[-1],
            "%.0fs" % (time.time() - t0),
        )
        res["fseof"].append(
            {
                "rep": rep,
                "flux_eps": eps,
                "n_targets": len(t),
                "counts": {k: int(v) for k, v in counts.items()},
                "enforced_first": r.enforced[0],
                "enforced_last": r.enforced[-1],
                "n_levels": len(r.enforced),
                "targets": sorted(zip(t.reaction, t.target_type, strict=False)),
                "growth_unconstrained": growth,
            }
        )

res["versions"] = versions(m)
print("versions", json.dumps(res["versions"]))
same = len({json.dumps(x["targets"]) for x in res["fseof"]}) == 1
print("all fseof runs give the same target set and labels:", same)
with open(args.out, "w") as f:
    json.dump(res, f, indent=1)
