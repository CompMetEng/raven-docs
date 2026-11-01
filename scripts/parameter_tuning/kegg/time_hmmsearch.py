#!/usr/bin/env python3
"""Time ``run_hmmsearch`` of one proteome against one KO HMM library at several thread counts.

For each thread count it runs ``raven_toolbox.reconstruction.kegg.query.run_hmmsearch``
once, reports the wall time, the number of hit rows, genes and KOs in the parsed
``--tblout``, and whether the parsed hit table (KO, gene, E-value) equals the one of
the first run. Writes the results as JSON.

Example:
    python time_hmmsearch.py --proteome sce.faa --library kegg118_eukaryotes.hmm \
        --threads 16 12 1 --json timing_sce_eukaryotes.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from raven_toolbox.reconstruction.kegg.query import parse_hmmsearch_tblout, run_hmmsearch


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--proteome", type=Path, required=True)
    ap.add_argument("--library", type=Path, required=True)
    ap.add_argument("--threads", type=int, nargs="+", required=True)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    nseq = sum(1 for line in args.proteome.read_text().splitlines() if line.startswith(">"))
    rows, first = [], None
    for t in args.threads:
        t0 = time.perf_counter()
        hits = parse_hmmsearch_tblout(run_hmmsearch(args.proteome, args.library, threads=t))
        secs = time.perf_counter() - t0
        key = sorted(zip(hits["ko"], hits["gene"], hits["evalue"], strict=False))
        same = None if first is None else key == first
        first = key if first is None else first
        row = {
            "threads": t,
            "seconds": secs,
            "queries": nseq,
            "hit_rows": len(hits),
            "genes_with_hits": int(hits["gene"].nunique()),
            "kos_with_hits": int(hits["ko"].nunique()),
            "identical_to_first_run": same,
        }
        rows.append(row)
        print(row, flush=True)
    if args.json:
        args.json.write_text(
            json.dumps(
                {"proteome": str(args.proteome), "library": str(args.library), "runs": rows},
                indent=1,
            )
        )


if __name__ == "__main__":
    main()
