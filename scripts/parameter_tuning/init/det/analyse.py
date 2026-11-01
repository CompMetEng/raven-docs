"""Print the tables of the determinism builds (A full pipeline, B first-step probe, C sweep).

Reads <out>/{A,B,C}-*.json written by build.py.
Command line: python analyse.py [<out>]   (default: $WORK/out)
"""

import itertools
import json
import os
import statistics as st
import sys

O = os.path.join(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ["WORK"], "out"), "")  # noqa: E741


def load(n):
    p = O + n + ".json"
    return json.load(open(p)) if os.path.exists(p) else None


def sd(a, b):
    return len(set(a) ^ set(b))


print("== A: full pipeline")
for cfg in ["base", "rt", "rtp1", "rtp005"]:
    r = [load(f"A-{cfg}-{s}-s{s}") for s in (1234, 7)]
    if None in r:
        print(cfg, "missing")
        continue
    a, b = r[0][0], r[1][0]
    print(
        cfg,
        "rxnswing",
        sd(a["reactions"], b["reactions"]),
        "geneswing",
        sd(a["essential"], b["essential"]),
        "ess",
        len(a["essential"]),
        len(b["essential"]),
        "nrxn",
        len(a["reactions"]),
        len(b["reactions"]),
        "wall",
        a["wall_s"],
        b["wall_s"],
        "ess_s",
        a["essential_s"],
        "growth",
        a["growth"],
        b["growth"],
        "warn",
        len(a["warnings"]),
        len(b["warnings"]),
    )
for cfg in ["base", "rt"]:
    r = load(f"A-{cfg}-rep-s1234")
    if r:
        print(
            "repeat",
            cfg,
            "rxn",
            sd(r[0]["reactions"], r[1]["reactions"]),
            "gene",
            sd(r[0]["essential"], r[1]["essential"]),
            "wall",
            r[0]["wall_s"],
            r[1]["wall_s"],
            "nrxn",
            len(r[0]["reactions"]),
            len(r[1]["reactions"]),
        )
print(
    "base vs rt seed 1234: rxn",
    sd(load("A-base-1234-s1234")[0]["reactions"], load("A-rt-1234-s1234")[0]["reactions"]),
    "gene",
    sd(load("A-base-1234-s1234")[0]["essential"], load("A-rt-1234-s1234")[0]["essential"]),
)
print("== B: stage-1 probe")
for cfg in ["base-t1", "rt-t1", "base-t4", "rt-t4"]:
    runs = []
    for s in (1234, 7, 1, 2, 3, 4):
        r = load(f"B-{cfg}-s{s}")
        if r:
            runs.append(r[0])
    sets = [frozenset(x["reactions"]) for x in runs]
    objs = [round(x["steps"][0]["objective"], 3) for x in runs]
    pairs = [len(a ^ b) for a, b in itertools.combinations(sets, 2)]
    print(
        cfg,
        "n",
        len(runs),
        "distinct",
        len(set(sets)),
        "objs",
        sorted(set(objs)),
        "meanpair",
        round(st.mean(pairs), 1) if pairs else None,
        "wall",
        [x["wall_s"] for x in runs],
        "status",
        [x["steps"][0]["status"] for x in runs],
    )
    # fixed objective
    for o in sorted(set(objs)):
        ss = {frozenset(x["reactions"]) for x, ob in zip(runs, objs, strict=False) if ob == o}
        print("   obj", o, "n", objs.count(o), "distinct", len(ss))
print("== C: sweep")
for g in ["none", "5.0", "2.0", "1.0", "0.5", "0.1", "0.05"]:
    runs = []
    for s in (1234, 7, 1, 2):
        r = load(f"C-{g}-{s}-s{s}")
        if r:
            runs.append(r[0])
    if not runs:
        continue
    for k in (0, 1):
        objs = [round(x["steps"][k]["objective"], 3) for x in runs]
        ss = {frozenset(x["reactions"]) for x in runs} if k == 1 else None
        st1 = {frozenset(x["reactions"]) for x in runs}
        print(
            g,
            "stage",
            k + 1,
            "n",
            len(runs),
            "objs",
            sorted(set(objs)),
            "status",
            [x["steps"][k]["status"] for x in runs],
            "secs",
            [x["steps"][k]["seconds"] for x in runs],
            "n_on",
            [x["steps"][k]["n_on"] for x in runs],
        )
    print(
        g,
        "final distinct sets",
        len({frozenset(x["reactions"]) for x in runs}),
        "wall",
        [x["wall_s"] for x in runs],
        "nrxn",
        [len(x["reactions"]) for x in runs],
        "warnings",
        [len(x["warnings"]) for x in runs],
    )
