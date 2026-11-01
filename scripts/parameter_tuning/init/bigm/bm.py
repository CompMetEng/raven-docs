#!/usr/bin/env python3
"""Driver of the ftINIT calibration, solver benchmark and validation runs (per-reaction big-M).

Runs raven-toolbox ftINIT on the cleaned Human-GEM and writes one JSON file per
run series, with the kept reaction sets, into $WORK/out (prepared models into
$WORK/shared).

Environment:
  HUMANGEM_ROOT  extracted Human-GEM tree (model/, data/, code/test/) at the
                 commit under study (38567ab8 for the October 2026 runs);
                 HG is accepted as the older name.
  WORK           work folder; OUT defaults to $WORK/out, SHARED to $WORK/shared.
  OUT, SHARED    override the two folders.
  PYTHONPATH     must contain $TOOLBOX_ROOT/src (raven-toolbox 94f3940).

Subcommands (one per job, see job.sh):
  prep                   cleaned Human-GEM -> prep_init_model(no tasks, scale=True)
                         -> SHARED/prep_notask.pkl, SHARED/ref_reactions.json
  preptask               same with metabolicTasks_Essential.txt -> SHARED/prep_task.pkl
  step0 [--cell C]       step-0 MILP grid (mip_gap, big_m, force_on) -> OUT/step0.json
  scale [--cell C]       unscaled prep, rescale_for_init(msd) x big_m 1000/100 -> OUT/scale.json
  full --gap G --big-m B [--scale off] [--noabs] --tag T
                         one ftinit() call, series 1+1, time_limit 600 -> OUT/full-T.json
  val --cell C           no-task, task and no-task big_m=100 ftinit() -> OUT/val-C.json
  solver --solvers a,b   ftinit() per optlang interface, time_limit 900
                         -> OUT/solver-a_b.json

Command line: python bm.py <subcommand> [options]
"""

import argparse
import json
import os
import pickle
import sys
import time
from pathlib import Path

HG = Path(os.environ.get("HUMANGEM_ROOT") or os.environ["HG"])
sys.path.insert(0, str(HG / "code" / "test"))
import cobra  # noqa: E402
import estimateEssentialGenes as E  # noqa: E402

from raven_toolbox.init import (  # noqa: E402
    ftinit,
    gene_scores_from_expression,  # noqa: E402
    prep_init_model,
    score_reactions_from_genes,
)
from raven_toolbox.init.ftinit import run_ftinit  # noqa: E402
from raven_toolbox.init.merge import group_rxn_scores  # noqa: E402
from raven_toolbox.init.prep import rescale_for_init  # noqa: E402
from raven_toolbox.init.steps import get_init_steps  # noqa: E402
from raven_toolbox.io import read_yaml_model  # noqa: E402
from raven_toolbox.tasks.tasklist import parse_task_list  # noqa: E402

OUT = Path(os.environ.get("OUT") or Path(os.environ["WORK"]) / "out")
SHARED = Path(
    os.environ.get("SHARED")
    or (Path(os.environ["WORK"]) / "shared" if os.environ.get("WORK") else OUT)
)


def use_gurobi(m):
    m.solver = "gurobi"


def clean_model():
    m = read_yaml_model(str(HG / "model" / "Human-GEM.yml"))
    rm = set(E._drug_reactions(m)) | set(E._aa_triplet_reactions(m))
    rm |= {E.DUPLICATE_COMPLEX_I_RXN} & {r.id for r in m.reactions}
    m.remove_reactions(sorted(rm), remove_orphans=True)
    ids = {r.id for r in m.reactions}
    spont = [r for r in E._load_spontaneous_reactions(E.REACTIONS_TSV) if r in ids]
    custom = [r for r in E.CUSTOM_RXNS_TO_IGNORE if r in ids]
    return m, spont, custom


def expr_for(cell):
    tissues, expression = E._read_rnaseq(E.RNASEQ_FILE)
    return expression[cell]


def scores_for(ref, cell):
    g = gene_scores_from_expression(expr_for(cell), 1.0)
    return g, score_reactions_from_genes(ref, g)


def jac(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 1.0


def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj))


def cmd_prep(a):
    m, spont, custom = clean_model()
    print("cleaned", len(m.reactions), "spont", len(spont), "custom", len(custom), flush=True)
    (SHARED / "ref_reactions.json").write_text(json.dumps(sorted(r.id for r in m.reactions)))
    t = time.time()
    prep = prep_init_model(m, None, ext_comp="e", spontaneous=spont, custom=custom, scale=True)
    print("prep notask s", time.time() - t, "min_model", len(prep.min_model.reactions), flush=True)
    pickle.dump(prep, open(SHARED / "prep_notask.pkl", "wb"))


def cmd_preptask(a):
    m, spont, custom = clean_model()
    tasks = parse_task_list(E.ESSENTIAL_TASKS)
    cobra.Configuration().processes = 1
    t = time.time()
    prep = prep_init_model(
        m, tasks, ext_comp="e", spontaneous=spont, custom=custom, scale=True, verbose=True
    )
    print("prep task s", time.time() - t, "essential", len(prep.essential_rxns), flush=True)
    pickle.dump(prep, open(SHARED / "prep_task.pkl", "wb"))


def load_prep(name):
    p = pickle.load(open(SHARED / name, "rb"))
    return p


def step0_inputs(prep, rxn_scores):
    step = get_init_steps("1+1")[0]
    to_zero = prep.masks.ignored(step.ignore_mask)
    scores = group_rxn_scores(
        prep.min_model, rxn_scores, prep.orig_rxn_ids, prep.group_ids, to_zero
    )
    return step, scores


def run_step0(mm, scores, prep, step, **kw):
    t = time.time()
    try:
        res = run_ftinit(
            mm,
            scores,
            essential_rxns=set(prep.essential_rxns),
            allow_excretion=step.allow_met_secr,
            rem_pos_rev=step.pos_rev_off,
            ignore_mets=step.mets_to_ignore,
            **kw,
        )
        return dict(
            seconds=time.time() - t,
            status="ok",
            objective=res.objective,
            n_kept=len(res.on_reactions),
            reactions=sorted(res.on_reactions),
            solver_status=res.status,
        )
    except Exception as ex:  # noqa: BLE001
        return dict(
            seconds=time.time() - t,
            status=f"FAIL:{type(ex).__name__}:{str(ex)[:100]}",
            objective=None,
            n_kept=0,
            reactions=[],
        )


def cmd_step0(a):
    prep = load_prep("prep_notask.pkl")
    g, rs = scores_for(prep.ref_model, a.cell)
    step, scores = step0_inputs(prep, rs)
    mm = prep.min_model
    res = {}
    cfgs = [
        ("gap=%s" % x, dict(mip_gap=x, big_m=1000.0, force_on=0.1))  # noqa: UP031
        for x in (0.0002, 0.001, 0.003, 0.01, 0.03, 0.1)
    ]
    cfgs += [
        ("big_m=%d" % b, dict(mip_gap=0.001, big_m=float(b), force_on=0.1))  # noqa: UP031
        for b in (10, 25, 50, 100, 250, 500, 1000)
    ]
    cfgs += [
        ("force_on=%s" % f, dict(mip_gap=0.001, big_m=1000.0, force_on=f))  # noqa: UP031
        for f in (0.02, 0.05, 0.1, 0.2, 0.5)
    ]
    seen = set()
    for label, kw in cfgs:
        key = json.dumps(kw, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        print("run", label, flush=True)
        res[label] = run_step0(mm, scores, prep, step, time_limit=900, **kw)
        res[label]["kw"] = kw
        print(label, res[label]["seconds"], res[label]["status"], res[label]["n_kept"], flush=True)
        dump("step0.json", res)


def cmd_scale(a):
    m, spont, custom = clean_model()
    base = prep_init_model(m, None, ext_comp="e", spontaneous=spont, custom=custom, scale=False)
    g, rs = scores_for(base.ref_model, a.cell)
    step, scores = step0_inputs(base, rs)
    res = {}
    for bm_ in (1000.0, 100.0):
        for label, msd in (
            ("scale=on,msd=25", 25.0),
            ("msd=10", 10.0),
            ("msd=50", 50.0),
            ("msd=100", 100.0),
            ("scale=off", None),
        ):
            mm = base.min_model.copy()
            if msd is not None:
                rescale_for_init(mm, msd)
            k = f"{label}|big_m={int(bm_)}"
            res[k] = run_step0(
                mm, scores, base, step, mip_gap=0.001, big_m=bm_, force_on=0.1, time_limit=600
            )
            print(k, res[k]["seconds"], res[k]["status"], res[k]["n_kept"], flush=True)
            dump("scale.json", res)


def run_full(prep, g, rs, **kw):
    t = time.time()
    try:
        out = ftinit(prep, rxn_scores=rs, gene_scores=g, series="1+1", **kw)
        return dict(
            seconds=time.time() - t,
            status="ok",
            n_kept=len(out.reactions),
            reactions=sorted(x.id for x in out.reactions),
            kw=kw,
        )
    except Exception as ex:  # noqa: BLE001
        return dict(
            seconds=time.time() - t,
            status=f"FAIL:{type(ex).__name__}:{str(ex)[:150]}",
            n_kept=0,
            reactions=[],
            kw=kw,
        )


def cmd_full(a):
    kw = dict(mip_gap=a.gap, big_m=a.big_m, time_limit=600)
    if a.noabs:
        kw["mip_gap_abs"] = None
    if a.scale == "off":
        m, spont, custom = clean_model()
        prep = prep_init_model(m, None, ext_comp="e", spontaneous=spont, custom=custom, scale=False)
    else:
        prep = load_prep("prep_notask.pkl")
    g, rs = scores_for(prep.ref_model, a.cell)
    r = run_full(prep, g, rs, **kw)
    r["scale"] = a.scale
    print(a.tag, r["seconds"], r["status"], r["n_kept"], flush=True)
    dump(f"full-{a.tag}.json", r)


def cmd_val(a):
    res = {}
    for variant, pname, bm_ in (
        ("notask", "prep_notask.pkl", 1000.0),
        ("task", "prep_task.pkl", 1000.0),
        ("notask100", "prep_notask.pkl", 100.0),
    ):
        prep = load_prep(pname)
        g, rs = scores_for(prep.ref_model, a.cell)
        res[variant] = run_full(prep, g, rs, mip_gap=0.001, big_m=bm_, time_limit=600)
        print(
            a.cell,
            variant,
            res[variant]["seconds"],
            res[variant]["status"],
            res[variant]["n_kept"],
            flush=True,
        )
        dump(f"val-{a.cell}.json", res)


def cmd_solver(a):
    res = {}
    for solver in a.solvers.split(","):
        for bm_ in (1000.0, 100.0):
            if solver != "gurobi" and bm_ != 1000.0:
                continue
            k = f"{solver}|big_m={int(bm_)}"
            t = time.time()
            try:
                prep = load_prep("prep_notask.pkl")
                prep.ref_model.solver = solver
                prep.min_model.solver = solver
                g, rs = scores_for(prep.ref_model, a.cell)
                out = ftinit(
                    prep,
                    rxn_scores=rs,
                    gene_scores=g,
                    series="1+1",
                    mip_gap=0.001,
                    time_limit=900,
                    big_m=bm_,
                )
                res[k] = dict(
                    seconds=time.time() - t,
                    status="ok",
                    n_kept=len(out.reactions),
                    reactions=sorted(x.id for x in out.reactions),
                )
            except Exception as ex:  # noqa: BLE001
                res[k] = dict(
                    seconds=time.time() - t,
                    status=f"FAIL:{type(ex).__name__}:{str(ex)[:150]}",
                    n_kept=0,
                    reactions=[],
                )
            print(k, res[k]["seconds"], res[k]["status"], res[k]["n_kept"], flush=True)
            dump(f"solver-{a.solvers.replace(',', '_')}.json", res)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for n in ("prep", "preptask", "step0", "scale", "full", "val", "solver"):
        p = sp.add_parser(n)
        p.add_argument("--cell", default="HCT116")
        p.add_argument("--gap", type=float, default=0.001)
        p.add_argument("--big-m", dest="big_m", type=float, default=1000.0)
        p.add_argument("--scale", default="on")
        p.add_argument("--tag", default="x")
        p.add_argument("--noabs", action="store_true")
        p.add_argument("--solvers", default="gurobi")
        p.set_defaults(fn=globals()[f"cmd_{n}"])
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
