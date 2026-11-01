#!/usr/bin/env python
"""Turn the score files of a run into the tables of the study.

Reads RES/<variant>.json (copies of the driver's ``hitlevel_results.json``, one per
score run: kegg118_blast_b0.5, kegg118_diamond_b0.5, kegg118_blast_b1,
kegg118_diamond_b1, oma_blast_b0.5, oma_diamond_b0.5, keggrest_rxn_blast_b0.5,
keggrest_rxn_diamond_b0.5, keggrest_all_blast_b0.5).
Writes RES/all_rows.tsv (every scored setting of every variant) and prints
Markdown tables.

    python make_tables.py --res results/ > results/tables.md
"""

from __future__ import annotations

import argparse
import json
import pathlib

import pandas as pd

ORGS = ("kla", "yli", "ani", "eco")
BASE = {"max_evalue": 1e-30, "min_align_len": 200, "min_identity": 40}


def load(res: pathlib.Path, name: str):
    path = res / f"{name}.json"
    return json.loads(path.read_text()) if path.is_file() else None


def row(data, code, **kw):
    want = {**BASE, **kw}
    return next(r for r in data[code]["rows"] if all(r[k] == v for k, v in want.items()))


def fmt(x):
    return "n/a" if x is None else f"{x:.3f}"


def sweep_best(data, code, key="fbeta"):
    rows = [r for r in data[code]["rows"] if r["min_align_len"] == 200 and r["max_evalue"] == 1e-30]
    best = max(rows, key=lambda r: r[key])
    return best["min_identity"], best[key]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--res", type=pathlib.Path, required=True)
    args = ap.parse_args()
    variants = [
        "kegg118_blast_b0.5",
        "kegg118_diamond_b0.5",
        "kegg118_blast_b1",
        "kegg118_diamond_b1",
        "oma_blast_b0.5",
        "oma_diamond_b0.5",
        "keggrest_rxn_blast_b0.5",
        "keggrest_rxn_diamond_b0.5",
        "keggrest_all_blast_b0.5",
    ]
    data = {v: load(args.res, v) for v in variants}
    flat = []
    for v, d in data.items():
        if d:
            for code, block in d.items():
                for r in block["rows"]:
                    flat.append(
                        {
                            "variant": v,
                            "organism": code,
                            "truth_pairs": block["truth_pairs"],
                            "n_hits": block["n_hits"],
                            **r,
                        }
                    )
    pd.DataFrame(flat).to_csv(args.res / "all_rows.tsv", sep="\t", index=False)

    k = data["kegg118_blast_b0.5"]
    print("## Identity sweep, F0.5, KEGG 118 reference, BLAST\n")
    print("| identity | " + " | ".join(f"`{o}`" for o in ORGS) + " |")
    print("|---|---|---|---|---|")
    for ide in (20, 25, 30, 35, 40, 45, 50, 60):
        cells = [fmt(row(k, o, min_identity=ide)["fbeta"]) for o in ORGS]
        print(f"| {ide} | " + " | ".join(cells) + " |")

    print("\n## Alignment-length sweep, F0.5, KEGG 118, BLAST\n")
    print("| length | " + " | ".join(f"`{o}`" for o in ORGS) + " |")
    print("|---|---|---|---|---|")
    for ln in (50, 100, 150, 200, 300):
        cells = [fmt(row(k, o, min_align_len=ln)["fbeta"]) for o in ORGS]
        print(f"| {ln} | " + " | ".join(cells) + " |")

    print("\n### Precision and recall at length 200, 100 and 50, KEGG 118, BLAST\n")
    print(
        "| org | P 200 | R 200 | P 100 | R 100 | P 50 | R 50 | recall gain 200->100 (pp) | "
        "TP gain 200->100 (%) |"
    )
    print("|---|---|---|---|---|---|---|---|---|")
    for o in ORGS:
        a, b, c = row(k, o), row(k, o, min_align_len=100), row(k, o, min_align_len=50)
        print(
            f"| {o} | {a['precision']:.3f} | {a['recall']:.3f} | {b['precision']:.3f} | "
            f"{b['recall']:.3f} | {c['precision']:.3f} | {c['recall']:.3f} | "
            f"{100 * (b['recall'] - a['recall']):.1f} | {100 * (b['tp'] / a['tp'] - 1):.1f} |"
        )

    print("\n## E-value sweep, F0.5, KEGG 118, BLAST\n")
    print("| max_evalue | " + " | ".join(f"`{o}`" for o in ORGS) + " |")
    print("|---|---|---|---|---|")
    for ev in (1e-4, 1e-10, 1e-30, 1e-50, 1e-100):
        vals = [row(k, o, max_evalue=ev)["fbeta"] for o in ORGS]
        print(f"| {ev:g} | " + " | ".join(fmt(v) for v in vals) + " |")

    dm = data["kegg118_diamond_b0.5"]
    if dm:
        print("\n## BLAST and DIAMOND, best identity (length 200, 1e-30), F0.5, KEGG 118\n")
        print("| org | best BLAST | best DIAMOND | score BLAST vs DIAMOND at the BLAST optimum |")
        print("|---|---|---|---|")
        for o in ORGS:
            ib, sb = sweep_best(k, o)
            idd, sd = sweep_best(dm, o)
            sd_at_b = row(dm, o, min_identity=ib)["fbeta"]
            print(
                f"| {o} | {ib} | {idd} | {sb:.3f} vs {sd_at_b:.3f}"
                f"{'' if idd == ib else f' (DIAMOND best {sd:.3f})'} |"
            )
        print("\nDIAMOND length and E-value rows:\n")
        print("| setting | " + " | ".join(ORGS) + " |")
        print("|---|---|---|---|---|")
        for label, kw in [
            ("len 100", {"min_align_len": 100}),
            ("len 50", {"min_align_len": 50}),
            ("len 300", {"min_align_len": 300}),
            ("1e-100", {"max_evalue": 1e-100}),
            ("1e-4", {"max_evalue": 1e-4}),
        ]:
            print(f"| {label} | " + " | ".join(fmt(row(dm, o, **kw)["fbeta"]) for o in ORGS) + " |")

    for name, label in (
        ("kegg118_blast_b1", "F1, KEGG 118, BLAST"),
        ("kegg118_diamond_b1", "F1, KEGG 118, DIAMOND"),
        ("oma_blast_b0.5", "F0.5, OMA, BLAST"),
        ("oma_diamond_b0.5", "F0.5, OMA, DIAMOND"),
        ("keggrest_rxn_blast_b0.5", "F0.5, current KEGG (REST, reaction-linked KOs), BLAST"),
        ("keggrest_rxn_diamond_b0.5", "F0.5, current KEGG (REST, reaction-linked KOs), DIAMOND"),
        ("keggrest_all_blast_b0.5", "F0.5, current KEGG (REST, all KOs), BLAST"),
    ):
        d = data[name]
        if not d:
            print(f"\n## {label}: missing\n")
            continue
        print(f"\n## Identity sweep, {label}\n")
        print("| identity | " + " | ".join(ORGS) + " |")
        print("|---|---|---|---|---|")
        for ide in (20, 25, 30, 35, 40, 45, 50, 60):
            print(
                f"| {ide} | "
                + " | ".join(fmt(row(d, o, min_identity=ide)["fbeta"]) for o in ORGS)
                + " |"
            )
        print(
            "| best identity (len 200) | "
            + " | ".join(str(sweep_best(d, o)[0]) for o in ORGS)
            + " |"
        )
        print("| truth pairs | " + " | ".join(str(d[o]["truth_pairs"]) for o in ORGS) + " |")
        if name.startswith("keggrest") or name.startswith("oma"):
            print(
                "| len 100 | "
                + " | ".join(fmt(row(d, o, min_align_len=100)["fbeta"]) for o in ORGS)
                + " |"
            )
            print(
                "| 1e-100 | "
                + " | ".join(fmt(row(d, o, max_evalue=1e-100)["fbeta"]) for o in ORGS)
                + " |"
            )

    print("\n## Counts at the base setting (40, 200, 1e-30), KEGG 118, BLAST\n")
    print("| org | hits | truth pairs | judged | unjudgeable | tp | fp | P | R |")
    print("|---|---|---|---|---|---|---|---|---|")
    for o in ORGS:
        r = row(k, o)
        print(
            f"| {o} | {k[o]['n_hits']} | {k[o]['truth_pairs']} | {r['judged']} | {r['unjudgeable']} | "
            f"{r['tp']} | {r['fp']} | {r['precision']:.3f} | {r['recall']:.3f} |"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
