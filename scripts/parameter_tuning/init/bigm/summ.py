"""Print the step-0, scaling, full-pipeline and solver summaries of bm.py outputs.

Reads OUT/step0.json, OUT/scale.json, OUT/full-*.json and OUT/solver-gurobi_hybrid.json.
Command line: python summ.py [OUT]   (default: $WORK/out, else ./out)
"""

import glob
import json
import os
import sys

O = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get("WORK", "."), "out")  # noqa: E741


def J(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 1


s = json.load(open(os.path.join(O, "step0.json")))
ref = s["gap=0.0002"]
print("STEP0 ref gap0.0002 obj", ref["objective"])
for k, v in s.items():
    print(
        k,
        round(v["seconds"]),
        v["status"],
        v["solver_status"] if "solver_status" in v else "",
        v["objective"],
        v["n_kept"],
        "jac_vs_gap.0002",
        round(J(v["reactions"], ref["reactions"]), 4),
        "jac_bm100",
        round(J(v["reactions"], s["big_m=100"]["reactions"]), 4),
        "jac_bm1000",
        round(J(v["reactions"], s["gap=0.001"]["reactions"]), 4),
        "relgap",
        round((ref["objective"] - v["objective"]) / abs(ref["objective"]), 4)
        if v["objective"]
        else None,
    )
sc = json.load(open(os.path.join(O, "scale.json")))
print("SCALE")
for k, v in sc.items():
    print(
        k,
        round(v["seconds"]),
        v["status"][:60],
        v["objective"],
        v["n_kept"],
        round(J(v["reactions"], sc["scale=on,msd=25|big_m=1000"]["reactions"]), 4),
    )
print("FULL")
ref = json.load(open(os.path.join(O, "full-g001-bm1000.json")))["reactions"]
for f in sorted(glob.glob(os.path.join(O, "full-*.json"))):
    v = json.load(open(f))
    print(
        os.path.basename(f)[5:-5],
        round(v["seconds"]),
        v["status"][:50],
        v["n_kept"],
        round(J(v["reactions"], ref), 4),
    )
print("SOLVER")
for k, v in json.load(open(os.path.join(O, "solver-gurobi_hybrid.json"))).items():
    print(k, round(v["seconds"]), v["status"][:120], v["n_kept"])
