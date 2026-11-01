#!/usr/bin/env python3
"""Tables of the solver benchmark, the parameter calibration and the Human-GEM validation.

Reads the JSON outputs of bm.py (step0.json, scale.json, full-*.json, solver-*.json,
val-*.json), the RAVEN reaction lists matlab-<cell>.txt and, if given, the reference
list matlab_ref_reactions.txt and the job logs, and prints the tables of the solver benchmark, the
parameter calibration and the Human-GEM validation. Every derived count (shared, only, symmetric difference) comes from
the reaction sets, not from rounded Jaccard values. Also writes all values as JSON.

Command line:
  python compare.py --out $WORK/out [--shared $WORK/shared] [--logs $WORK/logs] [--json tables.json]
"""

import argparse
import glob
import json
import os
import re

CELLS = ("DLD1", "GBM", "HCT116", "HELA", "RPE1")


def jac(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 1.0


def load(d, n):
    p = os.path.join(d, n)
    return json.load(open(p)) if os.path.exists(p) else None


def relgap(ref, obj):
    return (ref - obj) / abs(ref)


def table(title, head, rows):
    print(f"\n### {title}\n")
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for r in rows:
        print("| " + " | ".join(str(x) for x in r) + " |")


def f4(x):
    return f"{x:+.4f}".replace("+-", "-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="bm.py output folder")
    ap.add_argument("--shared", help="folder with matlab_ref_reactions.txt")
    ap.add_argument("--logs", help="folder with the job logs (prep and RAVEN times)")
    ap.add_argument("--json", help="write all values to this JSON file")
    a = ap.parse_args()
    O = a.out  # noqa: E741
    R = {}

    # ---------------- solver benchmark ----------------
    solv = {}
    for f in sorted(glob.glob(os.path.join(O, "solver-*.json"))):
        solv.update(json.load(open(f)))
    if solv:
        rows = []
        for k, v in solv.items():
            name, bm = k.split("|")
            rows.append(
                [
                    name,
                    bm.split("=")[1],
                    round(v["seconds"]),
                    v["status"][:110],
                    v["n_kept"] or "none",
                ]
            )
        table(
            "Solver benchmark: results",
            ["interface", "big_m", "time (s)", "outcome", "reactions"],
            rows,
        )
        R["solver_results"] = {
            k: {x: y for x, y in v.items() if x != "reactions"} for k, v in solv.items()
        }
        g = set(solv.get("gurobi|big_m=1000", {}).get("reactions", []))
        g100 = set(solv.get("gurobi|big_m=100", {}).get("reactions", []))
        gl = set(solv.get("glpk|big_m=1000", {}).get("reactions", []))
        if g and gl:
            ov = dict(
                glpk=len(gl),
                gurobi=len(g),
                shared=len(g & gl),
                only_glpk=len(gl - g),
                only_gurobi=len(g - gl),
                symdiff=len(g ^ gl),
                jaccard=round(jac(g, gl), 4),
            )
            R["solver_glpk_vs_gurobi"] = ov
            print("\nGLPK vs Gurobi (big_m=1000):", ov)
        if g and g100:
            R["solver_gurobi_100_vs_1000"] = dict(
                jaccard=round(jac(g, g100), 4), symdiff=len(g ^ g100)
            )
            print("Gurobi big_m=100 vs 1000:", R["solver_gurobi_100_vs_1000"])

    # ---------------- step 0 ----------------
    s = load(O, "step0.json")
    if s:
        ref = s["gap=0.0002"]
        rows = []
        for k in ("gap=0.0002", "gap=0.001", "gap=0.003", "gap=0.01", "gap=0.03", "gap=0.1"):
            v = s[k]
            rows.append(
                [
                    k.split("=")[1],
                    round(v["seconds"]),
                    round(v["objective"]),
                    "ref" if k == "gap=0.0002" else f4(relgap(ref["objective"], v["objective"])),
                    "ref" if k == "gap=0.0002" else f"{jac(v['reactions'], ref['reactions']):.4f}",
                ]
            )
        table(
            "Step-0 mip_gap (big_m=1000, force_on=0.1)",
            ["mip_gap", "time (s)", "objective", "rel.obj.gap", "Jaccard vs tightest"],
            rows,
        )
        bm1000 = s[
            "gap=0.001"
        ]  # big_m=1000 at gap 0.001 is the same configuration and was run once
        bm100 = s["big_m=100"]
        rows = []
        for b in (1000, 500, 250, 100, 50, 25, 10):
            v = bm1000 if b == 1000 else s[f"big_m={b}"]
            rows.append(
                [
                    b,
                    round(v["seconds"]),
                    "ref" if b == 1000 else f4(relgap(bm1000["objective"], v["objective"])),
                    "ref" if b == 1000 else f"{jac(v['reactions'], bm1000['reactions']):.3f}",
                    "ref" if b == 100 else f"{jac(v['reactions'], bm100['reactions']):.3f}",
                ]
            )
        table(
            "Step-0 big_m (mip_gap=0.001, force_on=0.1)",
            ["big_m", "time (s)", "rel.obj.gap", "Jaccard vs big_m=1000", "Jaccard vs big_m=100"],
            rows,
        )
        rows = []
        for fo in ("0.1", "0.02", "0.05", "0.2", "0.5"):
            v = bm1000 if fo == "0.1" else s[f"force_on={fo}"]
            rows.append(
                [
                    fo,
                    round(v["seconds"]),
                    "ref" if fo == "0.1" else f4(relgap(bm1000["objective"], v["objective"])),
                    "ref" if fo == "0.1" else f"{jac(v['reactions'], bm1000['reactions']):.3f}",
                ]
            )
        table(
            "Step-0 force_on (mip_gap=0.001, big_m=1000)",
            ["force_on", "time (s)", "rel.obj.gap", "Jaccard vs 0.1"],
            rows,
        )
        R["step0"] = {
            k: dict(
                seconds=v["seconds"],
                objective=v["objective"],
                n_kept=v["n_kept"],
                solver_status=v.get("solver_status"),
                jac_vs_tightest=jac(v["reactions"], ref["reactions"]),
                jac_vs_bm1000=jac(v["reactions"], bm1000["reactions"]),
                jac_vs_bm100=jac(v["reactions"], bm100["reactions"]),
                symdiff_vs_bm1000=len(set(v["reactions"]) ^ set(bm1000["reactions"])),
            )
            for k, v in s.items()
        }
        js = [jac(s[k]["reactions"], ref["reactions"]) for k in s if k != "gap=0.0002"]
        print(
            f"\nStep-0 Jaccard range vs tightest over all settings: {min(js):.4f} to {max(js):.4f}"
        )
        print(
            "Step-0 statuses:",
            sorted({v.get("solver_status") for v in s.values()}),
            "times",
            round(min(v["seconds"] for v in s.values()), 1),
            "to",
            round(max(v["seconds"] for v in s.values()), 1),
        )

    # ---------------- scaling ----------------
    sc = load(O, "scale.json")
    if sc:
        r0 = sc["scale=on,msd=25|big_m=1000"]
        rows = []
        for lab, name in (
            ("scale=on,msd=25", "scale on, msd=25"),
            ("msd=10", "msd=10"),
            ("msd=50", "msd=50"),
            ("msd=100", "msd=100"),
            ("scale=off", "scale off"),
        ):
            row = [name]
            for b in (1000, 100):
                v = sc[f"{lab}|big_m={b}"]
                isref = lab == "scale=on,msd=25" and b == 1000
                row += [
                    round(v["seconds"]),
                    "ref" if isref else f4(relgap(r0["objective"], v["objective"])),
                    "ref" if isref else f"{jac(v['reactions'], r0['reactions']):.3f}",
                ]
            rows.append(row)
        table(
            "Step-0 scaling (mip_gap=0.001)",
            [
                "config",
                "time bm1000",
                "rel.obj.gap",
                "Jaccard",
                "time bm100",
                "rel.obj.gap",
                "Jaccard",
            ],
            rows,
        )
        R["scale"] = {
            k: dict(
                seconds=v["seconds"],
                objective=v["objective"],
                status=v["status"],
                n_kept=v["n_kept"],
                jac_vs_ref=jac(v["reactions"], r0["reactions"]),
            )
            for k, v in sc.items()
        }
        if s:
            rec = dict(
                scale_ref_objective=r0["objective"],
                step0_gap0001_objective=s["gap=0.001"]["objective"],
                jaccard=jac(r0["reactions"], s["gap=0.001"]["reactions"]),
            )
            R["scale_vs_step0"] = rec
            print("\nReconciliation scale ref vs step0 gap=0.001:", rec)

    # ---------------- full pipeline ----------------
    full = {
        os.path.basename(f)[5:-5]: json.load(open(f))
        for f in sorted(glob.glob(os.path.join(O, "full-*.json")))
    }
    if full:
        ref = set(full["g001-bm1000"]["reactions"]) if "g001-bm1000" in full else set()
        rows = []
        R["full"] = {}
        for t, v in sorted(full.items(), key=lambda x: (-x[1]["kw"]["big_m"], x[0])):
            st = set(v["reactions"])
            kw = v["kw"]
            d = dict(
                seconds=v["seconds"],
                status=v["status"],
                n_kept=v["n_kept"],
                kw=kw,
                scale=v.get("scale"),
                jac_vs_g001_bm1000=jac(st, ref) if st else None,
                symdiff_vs_g001_bm1000=len(st ^ ref) if st else None,
            )
            R["full"][t] = d
            rows.append(
                [
                    t,
                    kw["big_m"],
                    kw["mip_gap"],
                    kw.get("mip_gap_abs", "default (10)"),
                    v.get("scale"),
                    round(v["seconds"]),
                    v["status"][:70],
                    v["n_kept"],
                    f"{d['jac_vs_g001_bm1000']:.4f}" if st else "none",
                    d["symdiff_vs_g001_bm1000"],
                ]
            )
        table(
            "Full pipeline runs (time_limit=600)",
            [
                "tag",
                "big_m",
                "mip_gap",
                "mip_gap_abs",
                "scale",
                "time (s)",
                "status",
                "n_kept",
                "Jaccard vs g001-bm1000",
                "sym. diff vs g001-bm1000",
            ],
            rows,
        )
        # identical sets among runs with one cap
        groups = {}
        for _t, v in full.items():
            if v["n_kept"] and v.get("scale") == "on":
                groups.setdefault(v["kw"]["big_m"], []).append(frozenset(v["reactions"]))
        print(
            "\nDistinct reaction sets per cap (scaled):",
            {int(b): f"{len(set(x))} of {len(x)}" for b, x in groups.items()},
        )
        # symmetric differences of the kept reaction sets, counted from the sets
        print("\nCap differences vs big_m=1000")
        R["cap_differences"] = {}
        for b, tag in (
            (500, "g003-bm500"),
            (250, "g003-bm250"),
            (100, "g001-bm100"),
            (50, "g003-bm50"),
        ):
            if tag not in full:
                continue
            st = set(full[tag]["reactions"])
            exact = len(st ^ ref)
            R["cap_differences"][b] = dict(
                tag=tag,
                exact=exact,
                ratio_to_110=round(exact / 110, 3),
            )
            print(
                f"  big_m={b} ({tag}): {exact} differing reactions, ratio to 110 = {exact / 110:.2f}"
            )
        off = full.get("g003-bm1000-scaleoff")
        if off and off["n_kept"]:
            print(
                "scale off bm1000:",
                off["n_kept"],
                round(off["seconds"], 1),
                f"Jaccard {jac(off['reactions'], ref):.3f}",
            )

    # ---------------- validation ----------------
    val = {c: load(O, f"val-{c}.json") for c in CELLS}
    rav = {}
    for c in CELLS:
        p = os.path.join(O, f"matlab-{c}.txt")
        if os.path.exists(p):
            rav[c] = {x.strip() for x in open(p) if x.strip()}
    if any(val.values()) and rav:
        R["validation"] = {}
        rows = []
        for c in CELLS:
            if val[c] and c in rav:
                rows.append([c, len(rav[c]), val[c]["notask"]["n_kept"], val[c]["task"]["n_kept"]])
        table(
            "Reactions in the extracted models",
            ["Cell line", "RAVEN ftINIT", "no-task", "task-constrained"],
            rows,
        )
        for var, title in (("notask", "No-task vs RAVEN"), ("task", "Task-constrained vs RAVEN")):
            rows = []
            for c in CELLS:
                if not (val[c] and c in rav):
                    continue
                t = set(val[c][var]["reactions"])
                m = rav[c]
                rows.append([c, len(t & m), len(t - m), len(m - t), f"{jac(t, m):.3f}"])
                R["validation"].setdefault(c, {})[var] = dict(
                    n=len(t),
                    raven=len(m),
                    shared=len(t & m),
                    only_toolbox=len(t - m),
                    only_raven=len(m - t),
                    jaccard=jac(t, m),
                    seconds=val[c][var]["seconds"],
                )
            table(
                title, ["Cell line", "Shared", "Only raven-toolbox", "Only RAVEN", "Jaccard"], rows
            )
        rows = []
        for c in CELLS:
            if not (val[c] and c in rav):
                continue
            t1, t2, m = (
                set(val[c]["notask"]["reactions"]),
                set(val[c]["notask100"]["reactions"]),
                rav[c],
            )
            rows.append([c, f"{jac(t1, m):.3f}", f"{jac(t2, m):.3f}", f"{jac(t1, t2):.3f}"])
            R["validation"][c]["notask100"] = dict(
                n=len(t2),
                jaccard_raven=jac(t2, m),
                jaccard_vs_notask=jac(t1, t2),
                symdiff_vs_notask=len(t1 ^ t2),
                seconds=val[c]["notask100"]["seconds"],
            )
        table(
            "No-task at two big_m values",
            ["Cell line", "J vs RAVEN, 1000", "J vs RAVEN, 100", "J between the two"],
            rows,
        )
        for var in ("notask", "task", "notask100"):
            ts = [val[c][var]["seconds"] for c in CELLS if val[c]]
            print(
                f"ftinit {var} seconds: {[round(x) for x in ts]} -> {round(min(ts))} to {round(max(ts))}"
            )
        if a.shared and os.path.exists(os.path.join(a.shared, "matlab_ref_reactions.txt")):
            mref = {
                x.strip()
                for x in open(os.path.join(a.shared, "matlab_ref_reactions.txt"))
                if x.strip()
            }
            n_out = sum(
                len(set(val[c][v]["reactions"]) - mref)
                for c in CELLS
                if val[c]
                for v in ("notask", "task", "notask100")
            )
            print(
                f"RAVEN prepared model: {len(mref)} reactions; raven-toolbox reactions outside it (all runs): {n_out}"
            )
            R["validation_ref"] = dict(matlab_ref=len(mref), toolbox_reactions_outside=n_out)
    if a.logs:
        times = {}
        for f in glob.glob(os.path.join(a.logs, "*.out")):
            for line in open(f, errors="replace"):
                m = re.match(r"prep (notask|task) s ([\d.]+)", line)
                if m:
                    times[f"toolbox prep {m.group(1)}"] = float(m.group(2))
                m = re.match(r"prep (\d+)s$", line.strip())
                if m:
                    times["RAVEN prepHumanModelForftINIT"] = float(m.group(1))
                m = re.match(r"ftINIT (\w+) (\d+)s rxns (\d+)", line.strip())
                if m:
                    times[f"RAVEN ftINIT {m.group(1)}"] = (float(m.group(2)), int(m.group(3)))
        if times:
            print("\nTimes from logs:")
            for k in sorted(times):
                print(" ", k, times[k])
            R["log_times"] = times
    if a.json:
        json.dump(R, open(a.json, "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
