#!/usr/bin/env python
"""BLAST/DIAMOND agreement on the matches that survive the homology filters.

For each target organism, reads the saved BLAST and DIAMOND hit tables of
homology_cutoff_kegg.py (``hits_<code>.csv``, ``hits_diamond_<code>.csv``),
applies one filter setting (kept when evalue <= max_evalue, align_len >=
min_align_len, identity >= min_identity, as in the driver's ``score``), and
collapses the kept hits of both directions into a set of (template gene, target
gene) pairs. It then compares the BLAST set B and the DIAMOND set D:

  jaccard        |B & D| / |B | D|
  blast_in_dmnd  |B & D| / |B|   (share of BLAST matches DIAMOND also finds)
  dmnd_in_blast  |B & D| / |D|

once over all surviving pairs and once over the pairs the KEGG reference judges
(both genes carry a KO in the gene-KO table), which are the pairs the scores use.

Settings: the base (40 %, 200, 1e-30), the toolbox default (40 %, 100, 1e-30)
and each organism's best identity at length 200 (kla 40, yli 35,
ani 35, eco 40).

    python agreement.py --work $W --gene-ko kegg118_organism_gene_ko_5org.tsv.gz --out agreement.tsv
"""

from __future__ import annotations

import argparse
import collections
import gzip
import pathlib

import pandas as pd

TEMPLATE = "sce"
TARGETS = ("kla", "yli", "ani", "eco")
BEST_IDE = {"kla": 40, "yli": 35, "ani": 35, "eco": 40}


def pairs(hits: pd.DataFrame, ide: float, length: int, evalue: float) -> set[tuple[str, str]]:
    kept = hits[(hits.evalue <= evalue) & (hits.align_len >= length) & (hits.identity >= ide)]
    out = set()
    for a, b, src in zip(kept.from_gene, kept.to_gene, kept.from_id, strict=True):
        out.add((a, b) if src == TEMPLATE else (b, a))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", type=pathlib.Path, required=True)
    ap.add_argument("--gene-ko", type=pathlib.Path, required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    args = ap.parse_args()

    genes = collections.defaultdict(set)
    with gzip.open(args.gene_ko, "rt", encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            org, gene, _ = line.rstrip("\n").split("\t")
            genes[org].add(gene)

    rows = []
    for code in TARGETS:
        blast = pd.read_csv(
            args.work / f"hits_{code}.csv", dtype={"from_gene": str, "to_gene": str}
        )
        dmnd = pd.read_csv(
            args.work / f"hits_diamond_{code}.csv", dtype={"from_gene": str, "to_gene": str}
        )
        settings = {
            "base_40_200": (40, 200, 1e-30),
            "default_40_100": (40, 100, 1e-30),
            f"best_{BEST_IDE[code]}_200": (BEST_IDE[code], 200, 1e-30),
        }
        for label, (ide, length, ev) in settings.items():
            b, d = pairs(blast, ide, length, ev), pairs(dmnd, ide, length, ev)
            for subset in ("all", "kegg_judged"):
                if subset == "kegg_judged":
                    keep = lambda p: p[0] in genes[TEMPLATE] and p[1] in genes[code]  # noqa: E731, B023
                    bb, dd = {p for p in b if keep(p)}, {p for p in d if keep(p)}
                else:
                    bb, dd = b, d
                inter, union = len(bb & dd), len(bb | dd)
                rows.append(
                    {
                        "organism": code,
                        "setting": label,
                        "pairs": subset,
                        "n_blast": len(bb),
                        "n_diamond": len(dd),
                        "both": inter,
                        "jaccard": round(inter / union, 4) if union else None,
                        "blast_in_dmnd": round(inter / len(bb), 4) if bb else None,
                        "dmnd_in_blast": round(inter / len(dd), 4) if dd else None,
                        "raw_hits_blast": len(blast),
                        "raw_hits_diamond": len(dmnd),
                    }
                )
    df = pd.DataFrame(rows)
    df.to_csv(args.out, sep="\t", index=False)
    print(df.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
