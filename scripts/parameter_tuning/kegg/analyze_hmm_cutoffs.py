#!/usr/bin/env python3
"""Cut-off sensitivity for the KEGG HMM query path.

Cross-validates ``assign_kos`` against an organism's *real* KEGG gene→KO
annotation (from the ``organism_gene_ko`` table) and sweeps the E-value cut-off
and the two score-ratio filters. Produces the tables of
``docs/parameter-tuning/studies/kegg-hmm-cutoff-calibration.md``.

Usage
-----
    python analyze_hmm_cutoffs.py \
        --artefacts <folder with the KEGG tables> \
        --proteome <org>.faa \
        --org sce --library kegg118_eukaryotes.hmm --threads 16

``--proteome`` is the organism's protein FASTA (headers ``>org:gene ...``).
``--tblout`` may be given instead of ``--library`` to reuse a cached
``hmmsearch --tblout`` file (written by ``--save-tblout``). ``hmmsearch`` is
resolved by the toolbox (``RAVEN_PYTHON_HMMSEARCH``, PATH or the bundled binary)
when ``--library`` is used. ``--artefacts`` may hold the tables with or without a
version prefix (``kegg118_ko_reaction.tsv.gz``). ``--json`` writes all printed
numbers. ``--restrict-to-reference`` keeps only the ``ko_reaction`` links to
reactions of the reference model when the true and predicted reactions are counted.

The cut-off sweep is printed twice: at (min_score_ratio_ko, min_score_ratio_g) =
(0.3, 0.8), the RAVEN 2.11.3 ratios, and at (0.3, 0.9), the defaults.

Caveat: organisms present in the library's training set give an upper bound on
recall; the comparison is relative.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from raven_toolbox.reconstruction.kegg.parse import _resolve_artefact, read_kegg_table
from raven_toolbox.reconstruction.kegg.query import (
    assign_kos,
    parse_hmmsearch_tblout,
    run_hmmsearch,
)

CUTOFFS = (1e-10, 1e-20, 1e-30, 1e-50, 1e-70, 1e-100)
KO_RATIOS = (0.0, 0.3, 0.5)
G_RATIOS = (0.5, 0.8, 0.95)
SWEEP_RATIOS = ((0.3, 0.8), (0.3, 0.9))


def load_ko2rxn(artefacts: Path, restrict_to_reference: bool = False) -> dict[str, set[str]]:
    tbl = read_kegg_table(_resolve_artefact(artefacts, "ko_reaction.tsv.gz"))
    if restrict_to_reference:
        from raven_toolbox.io.yaml import read_yaml_model

        ref = read_yaml_model(_resolve_artefact(artefacts, "reference_model.yml.gz"))
        tbl = tbl[tbl["reaction"].isin({r.id for r in ref.reactions})]
    ko2rxn: dict[str, set[str]] = {}
    for ko, rxn in zip(tbl["ko"], tbl["reaction"], strict=True):
        ko2rxn.setdefault(ko, set()).add(rxn)
    return ko2rxn


def ground_truth(artefacts: Path, org: str, ko2rxn) -> tuple[set, set]:
    ogk = read_kegg_table(_resolve_artefact(artefacts, "organism_gene_ko.tsv.gz"))
    rows = ogk[ogk["organism"].str.lower() == org]
    pairs = set(zip(rows["gene"], rows["ko"], strict=True))
    rxns = {r for _, ko in pairs for r in ko2rxn.get(ko, ())}
    return pairs, rxns


def predicted_pairs(hits: pd.DataFrame, **kw) -> set:
    out = set()
    for ko, genes in assign_kos(hits, **kw).items():
        for g in genes:
            out.add((g.split(":", 1)[1] if ":" in g else g, ko))
    return out


def prf(pred: set, truth: set) -> tuple[float, float, float]:
    tp = len(pred & truth)
    rec = tp / len(truth) if truth else 0.0
    prec = tp / len(pred) if pred else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return prec, rec, f1


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artefacts", type=Path, required=True)
    ap.add_argument("--org", required=True, help="KEGG organism code, e.g. sce")
    ap.add_argument("--proteome", type=Path, help="protein FASTA (headers >org:gene)")
    ap.add_argument("--library", type=Path, help="HMM library flatfile for hmmsearch")
    ap.add_argument("--tblout", type=Path, help="cached hmmsearch --tblout (skip hmmsearch)")
    ap.add_argument("--save-tblout", type=Path, help="write the hmmsearch --tblout text here")
    ap.add_argument("--json", type=Path, help="write the results as JSON here")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument(
        "--restrict-to-reference",
        action="store_true",
        help="keep only ko_reaction links to reactions of the reference model",
    )
    args = ap.parse_args(argv)
    result: dict = {"org": args.org.lower()}

    if args.tblout:
        text = args.tblout.read_text()
    elif args.library and args.proteome:
        t0 = time.perf_counter()
        text = run_hmmsearch(args.proteome, args.library, threads=args.threads)
        secs = time.perf_counter() - t0
        result["search"] = {
            "threads": args.threads,
            "seconds": secs,
            "library": str(args.library),
            "proteome": str(args.proteome),
        }
        print(f"hmmsearch: {secs:.1f} s on {args.threads} threads")
    else:
        ap.error("give --tblout, or --library and --proteome")
    if args.save_tblout:
        args.save_tblout.write_text(text)

    org = args.org.lower()
    hits = parse_hmmsearch_tblout(text)
    hits = hits[hits["gene"].str.startswith(f"{org}:")].reset_index(drop=True)
    ko2rxn = load_ko2rxn(args.artefacts, args.restrict_to_reference)
    result["restrict_to_reference"] = args.restrict_to_reference
    gt_pairs, gt_rxns = ground_truth(args.artefacts, org, ko2rxn)
    if args.proteome:
        result["proteome_seqs"] = sum(
            1 for line in args.proteome.read_text().splitlines() if line.startswith(">")
        )
    result.update(
        {
            "hit_rows": len(hits),
            "genes_with_hits": int(hits["gene"].nunique()),
            "true_pairs": len(gt_pairs),
            "true_reactions": len(gt_rxns),
        }
    )

    print(
        f"\n{'=' * 70}\n{org}: {hits['gene'].nunique()} query genes with hits, "
        f"{len(gt_pairs)} true gene->KO pairs, {len(gt_rxns)} true reactions\n{'=' * 70}"
    )

    best: dict[tuple, float] = {}
    for ko, gene, e in zip(hits["ko"], hits["gene"], hits["evalue"], strict=True):
        key = (gene.split(":", 1)[1], ko)
        if key not in best or e < best[key]:
            best[key] = e
    matched = np.array([e for k, e in best.items() if k in gt_pairs])
    novel = np.array([e for k, e in best.items() if k not in gt_pairs])

    def logq(arr, q):
        if not len(arr):
            return float("nan")
        v = np.quantile(arr, q)
        return np.log10(v) if v > 0 else -300.0

    print("\nlog10(E-value) percentiles  [matched=in annotation, novel=not]:")
    print(f"  {'group':<8}{'n':>7}{'p50':>8}{'p90':>8}{'p95':>8}{'p99':>8}")
    result["percentiles"] = {}
    for name, arr in (("matched", matched), ("novel", novel)):
        print(
            f"  {name:<8}{len(arr):>7}{logq(arr, 0.5):>8.0f}{logq(arr, 0.9):>8.0f}"
            f"{logq(arr, 0.95):>8.0f}{logq(arr, 0.99):>8.0f}"
        )
        result["percentiles"][name] = {
            "n": len(arr),
            **{f"p{int(q * 100)}": float(logq(arr, q)) for q in (0.5, 0.9, 0.95, 0.99)},
        }

    result["cutoff_sweep"] = []
    for rko, rg in SWEEP_RATIOS:
        print(f"\ncutoff sweep (min_score_ratio_ko={rko}, min_score_ratio_g={rg}):")
        print(
            f"  {'cutoff':>8}{'gKO_prec':>9}{'gKO_rec':>8}{'gKO_F1':>8}{'rxn_rec':>9}{'rxn_novel':>10}"
        )
        for cutoff in CUTOFFS:
            pred = predicted_pairs(
                hits, cutoff=cutoff, min_score_ratio_ko=rko, min_score_ratio_g=rg
            )
            prec, rec, f1 = prf(pred, gt_pairs)
            pred_rxns = {r for _, ko in pred for r in ko2rxn.get(ko, ())}
            rrec = len(pred_rxns & gt_rxns) / len(gt_rxns) if gt_rxns else 0.0
            print(
                f"  {cutoff:>8.0e}{prec:>9.2f}{rec:>8.2f}{f1:>8.2f}{rrec:>9.2f}"
                f"{len(pred_rxns - gt_rxns):>10}"
            )
            result["cutoff_sweep"].append(
                {
                    "ko_ratio": rko,
                    "g_ratio": rg,
                    "cutoff": cutoff,
                    "pairs": len(pred),
                    "prec": prec,
                    "rec": rec,
                    "f1": f1,
                    "rxn_rec": rrec,
                    "rxn_novel": len(pred_rxns - gt_rxns),
                }
            )

    print("\nratio sweep (cutoff=1e-50):")
    print(f"  {'ko_ratio':>9}{'g_ratio':>8}{'gKO_prec':>9}{'gKO_rec':>8}{'gKO_F1':>8}")
    result["ratio_sweep"] = []
    for rko in KO_RATIOS:
        for rg in G_RATIOS:
            pred = predicted_pairs(hits, cutoff=1e-50, min_score_ratio_ko=rko, min_score_ratio_g=rg)
            prec, rec, f1 = prf(pred, gt_pairs)
            print(f"  {rko:>9.1f}{rg:>8.2f}{prec:>9.2f}{rec:>8.2f}{f1:>8.2f}")
            result["ratio_sweep"].append(
                {"ko_ratio": rko, "g_ratio": rg, "prec": prec, "rec": rec, "f1": f1}
            )
    if args.json:
        args.json.write_text(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
