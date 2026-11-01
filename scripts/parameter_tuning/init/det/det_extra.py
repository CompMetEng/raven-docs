#!/usr/bin/env python3
"""Figures of the determinism study that analyse.py does not print.

From the build JSON files (<out>): the template-edit table (E builds against the
unedited A builds), the edit-list reactions kept by the unedited builds, the pooled
first-step probe (objective values, distinct sets and pairwise ranges per objective,
Threads 1 against 4 at one seed), the distances of the sweep's final sets, the
build-time ratios. From the FTINIT_DEBUG logs (<logs>): the phase statuses of the
tie-broken solves per prove_abs_gap value and, per full build, whether it adopted a
phase at time_limit, had a primary solve at time_limit or dropped a tie-break (phase
2a or 2b without incumbent).

Command line: python det_extra.py <out> <logs> [--json det_extra.json]
"""

import argparse
import itertools
import json
import os
import re
import statistics as st

PROVEN = 45899.11297453767


def load(o, n):
    p = os.path.join(o, n + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def sd(a, b):
    return len(set(a) ^ set(b))


def builds_in_log(path):
    """Split an FTINIT_DEBUG log into builds, each a list of solve blocks."""
    builds, cur, solve = [], None, None
    for line in open(path, errors="replace"):
        line = line.strip()
        m = re.match(r"\[ftinit\] step (\d+)/(\d+)", line)
        if m and m.group(1) == "1":
            cur = []
            builds.append(cur)
        if line.startswith("[ftinit] final solve:"):
            solve = {
                "step_line": line,
                "primary": re.search(r"status=(\w+)", line).group(1),
                "phases": {},
                "skipped": False,
            }
            if cur is not None:
                cur.append(solve)
        elif line.startswith("[ftinit] tie-break skipped") and solve is not None:
            solve["skipped"] = True
        else:
            m = re.match(r"\[ftinit\] tie-break (phase\w+)-\w+: status=(\w+) obj=(\S+)", line)
            if m and solve is not None:
                solve["phases"][m.group(1)] = (m.group(2), m.group(3))
    return builds


def classify(build):
    adopted = primary_tl = dropped = False
    for s in build:
        if s["primary"] == "time_limit":
            primary_tl = True
        ph = s["phases"]
        drop = any(ph.get(p, ("", ""))[1] == "inf" for p in ("phase2a", "phase2b"))
        if drop:
            dropped = True
        for p, (stt, obj) in ph.items():
            if stt == "time_limit" and obj != "inf" and not (drop and p in ("phase2a", "phase2b")):
                adopted = True
    return dict(
        adopted_phase_at_time_limit=adopted,
        primary_at_time_limit=primary_tl,
        tie_break_dropped=dropped,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("logs")
    ap.add_argument("--json")
    a = ap.parse_args()
    O, L, R = a.out, a.logs, {}  # noqa: E741

    # template edit
    print("== Template edit (seed 1234)")
    edit = (
        json.load(open(os.path.join(O, "edit-list.json")))
        if os.path.exists(os.path.join(O, "edit-list.json"))
        else []
    )
    R["edit"] = {}
    for cfg, ref in (
        ("base", "A-base-1234-s1234"),
        ("rt", "A-rt-1234-s1234"),
        ("rtp1", "A-rtp1-1234-s1234"),
    ):
        e, u = load(O, f"E-{cfg}-s1234"), load(O, ref)
        if not (e and u):
            continue
        e, u = e[0], u[0]
        gains = len(set(e["essential"]) - set(u["essential"]))
        d = dict(
            rxn_diff=sd(e["reactions"], u["reactions"]),
            gene_diff=sd(e["essential"], u["essential"]),
            gene_gains=gains,
            ess_unedited=len(u["essential"]),
            ess_edited=len(e["essential"]),
            wall_edited=e["wall_s"],
            n_edited=len(e["reactions"]),
            n_unedited=len(u["reactions"]),
            edit_reactions_kept_by_unedited=len(set(edit) & set(u["reactions"])),
        )
        R["edit"][cfg] = d
        print(cfg, d)
    rtp1 = load(O, "A-rtp1-1234-s1234")
    if rtp1:
        print(
            "A-rtp1-1234: reactions",
            len(rtp1[0]["reactions"]),
            "essential",
            len(rtp1[0]["essential"]),
        )
    print("edit list size", len(edit))

    # full-pipeline extras
    print("== Full pipeline extras")
    A = {
        n: load(O, n)
        for n in (
            "A-base-1234-s1234",
            "A-base-7-s7",
            "A-rt-1234-s1234",
            "A-rt-7-s7",
            "A-rtp1-1234-s1234",
            "A-rtp1-7-s7",
            "A-rtp005-1234-s1234",
            "A-rtp005-7-s7",
        )
    }
    for n, v in A.items():
        if v:
            x = v[0]
            print(
                n,
                "nrxn",
                len(x["reactions"]),
                "growth",
                round(x["growth"], 1) if x["growth"] is not None else None,
                "step objs",
                [round(s["objective"], 3) for s in x["steps"]],
                "wall",
                x["wall_s"],
            )
    b = [A["A-base-1234-s1234"][0]["wall_s"], A["A-base-7-s7"][0]["wall_s"]]
    r = [A["A-rt-1234-s1234"][0]["wall_s"], A["A-rt-7-s7"][0]["wall_s"]]
    p = [A["A-rtp1-1234-s1234"][0]["wall_s"], A["A-rtp1-7-s7"][0]["wall_s"]]
    R["time_ratio"] = dict(rt=st.mean(r) / st.mean(b), rtp1=st.mean(p) / st.mean(b))
    print(
        "build-time ratio vs baseline (means of seeds 1234 and 7): rt %.2f, rtp1 %.2f"  # noqa: UP031
        % (R["time_ratio"]["rt"], R["time_ratio"]["rtp1"])
    )

    # first-step probe pooled
    print("== First-step probe, pooled")
    runs = {}
    for cfg in ("base-t1", "base-t4", "rt-t1", "rt-t4"):
        for s in (1234, 7, 1, 2, 3, 4):
            v = load(O, f"B-{cfg}-s{s}")
            if v:
                runs[(cfg, s)] = v[0]
    R["probe"] = {}
    for setting in ("base", "rt"):
        rr = {k: v for k, v in runs.items() if k[0].startswith(setting + "-")}
        objs = {k: round(v["steps"][0]["objective"], 3) for k, v in rr.items()}
        sets = {k: frozenset(v["reactions"]) for k, v in rr.items()}
        byobj = {}
        for k, o in objs.items():
            byobj.setdefault(o, []).append(k)
        info = {}
        for o, ks in sorted(byobj.items()):
            pw = [len(sets[x] ^ sets[y]) for x, y in itertools.combinations(ks, 2)]
            info[o] = dict(
                n=len(ks),
                distinct=len({sets[k] for k in ks}),
                pair_min=min(pw) if pw else None,
                pair_max=max(pw) if pw else None,
            )
        same_seed = {
            s: dict(
                diff=len(sets[(f"{setting}-t1", s)] ^ sets[(f"{setting}-t4", s)]),
                same_obj=objs[(f"{setting}-t1", s)] == objs[(f"{setting}-t4", s)],
            )
            for s in (1234, 7, 1, 2, 3, 4)
            if (f"{setting}-t1", s) in sets and (f"{setting}-t4", s) in sets
        }
        walls = {
            t: [
                rr[(f"{setting}-{t}", s)]["wall_s"]
                for s in (1234, 7, 1, 2, 3, 4)
                if (f"{setting}-{t}", s) in rr
            ]
            for t in ("t1", "t4")
        }
        R["probe"][setting] = dict(
            n=len(rr),
            distinct=len(set(sets.values())),
            objectives=sorted(set(objs.values())),
            by_objective=info,
            t1_vs_t4_same_seed=same_seed,
            wall_range={t: (min(w), max(w)) for t, w in walls.items() if w},
        )
        print(setting, json.dumps(R["probe"][setting], default=str))

    # sweep final sets
    print("== Sweep final sets and times")
    R["sweep"] = {}
    for g in ("none", "5.0", "2.0", "1.0", "0.5", "0.1", "0.05"):
        rr = [load(O, f"C-{g}-{s}-s{s}") for s in (1234, 7, 1, 2)]
        rr = [x[0] for x in rr if x]
        if not rr:
            continue
        sets = [frozenset(x["reactions"]) for x in rr]
        pw = [len(x ^ y) for x, y in itertools.combinations(sets, 2)]
        d = dict(
            distinct=len(set(sets)),
            pair_min=min(pw),
            pair_max=max(pw),
            step1_below_proven=sorted(round(PROVEN - x["steps"][0]["objective"], 1) for x in rr),
            step1_s=(
                min(x["steps"][0]["seconds"] for x in rr),
                max(x["steps"][0]["seconds"] for x in rr),
            ),
            step2_s=(
                min(x["steps"][1]["seconds"] for x in rr),
                max(x["steps"][1]["seconds"] for x in rr),
            ),
            wall=(min(x["wall_s"] for x in rr), max(x["wall_s"] for x in rr)),
            wall_mean=round(st.mean(x["wall_s"] for x in rr), 1),
            statuses=sorted({s["status"] for x in rr for s in x["steps"]}),
            with_warning=sum(1 for x in rr if x["warnings"]),
        )
        R["sweep"][g] = d
        print(g, json.dumps(d))
    s10 = [x for x in (load(O, f"C-1.0-{s}-s{s}") for s in (1234, 7, 1, 2)) if x]
    if s10:
        sh = [x[0]["steps"][0]["seconds"] / x[0]["wall_s"] for x in s10]
        print("pag=1.0 step-1 share of build per run: %.3f to %.3f" % (min(sh), max(sh)))  # noqa: UP031
        R["sweep_step1_share_1.0"] = (min(sh), max(sh))

    # phase statuses of the sweep logs
    print("== Phase statuses of the tie-broken solves in the sweep logs")
    R["phases"] = {}
    for g in ("5.0", "2.0", "1.0", "0.5", "0.1", "0.05", "none"):
        cnt = {}
        for s in (1234, 7, 1, 2):
            f = os.path.join(L, f"C-{g}-{s}.log")
            if not os.path.exists(f):
                continue
            for bld in builds_in_log(f):
                for _k, solve in enumerate(bld):
                    for ph, (stt, obj) in solve["phases"].items():
                        key = f"{ph} {stt}" + (" no-incumbent" if obj == "inf" else "")
                        cnt[key] = cnt.get(key, 0) + 1
        R["phases"][g] = dict(sorted(cnt.items()))
        print(g, dict(sorted(cnt.items())))

    # build counts of the full builds
    print("== Full builds: adopted phase / primary at time_limit / dropped tie-break")
    R["build_counts"] = {}
    logs = [
        ("baseline", "A-base-1234.log"),
        ("baseline", "A-base-7.log"),
        ("baseline", "A-base-rep.log"),
        ("rt", "A-rt-1234.log"),
        ("rt", "A-rt-7.log"),
        ("rt", "A-rt-rep.log"),
        ("pag", "A-rtp1-1234.log"),
        ("pag", "A-rtp1-7.log"),
        ("pag", "A-rtp005-1234.log"),
        ("pag", "A-rtp005-7.log"),
    ]
    per = []
    for setting, f in logs:
        p = os.path.join(L, f)
        if os.path.exists(p):
            for i, bld in enumerate(builds_in_log(p)):
                per.append((setting, f"{f}#{i + 1}", classify(bld)))
    ep = os.path.join(L, "edit.log")
    if os.path.exists(ep):
        for setting, bld in zip(("baseline", "rt", "pag"), builds_in_log(ep), strict=False):
            per.append((setting, f"edit.log ({setting})", classify(bld)))
    for setting, name, c in per:
        print(f"  {setting:8s} {name:24s} {c}")
    for setting in ("baseline", "rt", "pag"):
        cs = [c for s_, _, c in per if s_ == setting]
        R["build_counts"][setting] = (
            dict(builds=len(cs), **{k: sum(c[k] for c in cs) for k in cs[0]}) if cs else {}
        )
        print(setting, R["build_counts"][setting])
    R["build_counts_per_build"] = [dict(setting=s_, build=n, **c) for s_, n, c in per]
    if a.json:
        json.dump(R, open(a.json, "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
