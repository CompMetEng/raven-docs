#!/usr/bin/env python
"""Aligner-settings measurements: BLAST thread test and aligner E-value 1e-4 vs 1e-5.

Template proteome: SGD S288C ``orf_trans_all``. Target: hanpo-GEM ``data/genomes/hanpo.faa``.

1. Thread test: the first N (500) sequences of hanpo.faa as queries against a
   BLAST database of the template, ``blastp -evalue 1e-4``, once at 1 thread and
   once at 4; reports hits, wall time and whether the two hit tables are identical.
2. Full direction at 1 thread (optional, --single-thread-full): both directions
   of hanpo vs template with ``blastp -num_threads 1``, wall time per direction.
3. Aligner E-value: ``run_blast`` (bidirectional) at
   evalue 1e-4 and 1e-5 with --threads; hits, time, the number of extra hits, their
   share of the 1e-4 table and how many of them have an E-value above 1e-5.

    python aligner_settings.py --hanpo hanpo.faa --template orf_trans_all.fasta \\
        --bindir <binaries cache>/blast-2.17.0-linux-x86_64 \\
        --work $TMPDIR/as --out aligner_settings.json --threads 4 --single-thread-full
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import time

OUTFMT = "10 qseqid sseqid evalue pident length bitscore ppos"


def run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{cmd}: {proc.stderr}")
    return proc.stdout


def first_n(fasta: pathlib.Path, n: int, out: pathlib.Path) -> int:
    count, lines = 0, []
    for line in fasta.read_text().splitlines():
        if line.startswith(">"):
            count += 1
            if count > n:
                break
        lines.append(line)
    out.write_text("\n".join(lines) + "\n")
    return min(count, n)


def timed_blastp(blastp: str, query, db, evalue: str, threads: int) -> tuple[list[str], float]:
    t0 = time.perf_counter()
    out = run(
        [
            blastp,
            "-query",
            str(query),
            "-db",
            str(db),
            "-evalue",
            evalue,
            "-outfmt",
            OUTFMT,
            "-num_threads",
            str(threads),
        ]
    )
    return out.splitlines(), time.perf_counter() - t0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hanpo", type=pathlib.Path, required=True)
    ap.add_argument("--template", type=pathlib.Path, required=True)
    ap.add_argument("--bindir", type=pathlib.Path, required=True)
    ap.add_argument("--work", type=pathlib.Path, required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--subset", type=int, default=500)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--single-thread-full", action="store_true")
    args = ap.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    blastp, makeblastdb = str(args.bindir / "blastp"), str(args.bindir / "makeblastdb")
    res: dict = {
        "blastp_version": run([blastp, "-version"]).strip(),
        "n_hanpo": args.hanpo.read_text().count(">"),
        "n_template": args.template.read_text().count(">"),
    }

    db_t, db_h = args.work / "db_template", args.work / "db_hanpo"
    run([makeblastdb, "-in", str(args.template), "-dbtype", "prot", "-out", str(db_t)])
    run([makeblastdb, "-in", str(args.hanpo), "-dbtype", "prot", "-out", str(db_h)])

    sub = args.work / "subset.faa"
    res["subset_queries"] = first_n(args.hanpo, args.subset, sub)
    tt = {}
    for th in (1, args.threads):
        hits, secs = timed_blastp(blastp, sub, db_t, "1e-4", th)
        tt[th] = (sorted(hits), secs)
        print(f"subset, {th} thread(s): {len(hits)} hits, {secs:.1f} s", flush=True)
    res["thread_test"] = {
        "direction": "hanpo subset -> template db",
        "evalue": "1e-4",
        **{f"threads_{th}": {"hits": len(h), "seconds": round(s, 1)} for th, (h, s) in tt.items()},
        "identical_hit_tables": tt[1][0] == tt[args.threads][0],
    }

    if args.single_thread_full:
        full = {}
        for label, query, db in (
            ("hanpo->template", args.hanpo, db_t),
            ("template->hanpo", args.template, db_h),
        ):
            hits, secs = timed_blastp(blastp, query, db, "1e-4", 1)
            full[label] = {"hits": len(hits), "seconds": round(secs, 1)}
            print(f"full {label}, 1 thread: {len(hits)} hits, {secs:.1f} s", flush=True)
        res["single_thread_full"] = full

    from raven_toolbox.reconstruction.homology import run_blast

    ev = {}
    tables = {}
    for e in (1e-4, 1e-5):
        t0 = time.perf_counter()
        hits = run_blast(
            "hanpo",
            args.hanpo,
            ["sce"],
            [args.template],
            evalue=e,
            threads=args.threads,
            blastp=blastp,
            makeblastdb=makeblastdb,
        )
        secs = time.perf_counter() - t0
        tables[e] = hits
        ev[f"{e:g}"] = {"hits": len(hits), "seconds": round(secs, 1)}
        print(f"run_blast evalue {e:g}: {len(hits)} hits, {secs:.1f} s", flush=True)
    extra = len(tables[1e-4]) - len(tables[1e-5])
    above = int((tables[1e-4].evalue > 1e-5).sum())
    import collections

    def rows(df):
        return collections.Counter(
            zip(
                df.from_id,
                df.from_gene,
                df.to_gene,
                df.evalue,
                df.identity,
                df.align_len,
                df.bitscore,
                strict=False,
            )
        )

    r4, r5 = rows(tables[1e-4]), rows(tables[1e-5])
    only4, only5 = r4 - r5, r5 - r4
    ev4 = [k[3] for k, n in only4.items() for _ in range(n)]
    ev["row_diff"] = {
        "rows_only_in_1e-4": sum(only4.values()),
        "rows_only_in_1e-5": sum(only5.values()),
        "only_in_1e-4_with_evalue_above_1e-5": sum(1 for e in ev4 if e > 1e-5),
        "only_in_1e-4_with_evalue_at_most_1e-5": sum(1 for e in ev4 if e <= 1e-5),
        "only_in_1e-4_min_evalue": min(ev4) if ev4 else None,
        "only_in_1e-4_with_evalue_below_1e-30": sum(1 for e in ev4 if e < 1e-30),
        "only_in_1e-5_examples": [list(map(str, k)) for k in list(only5)[:5]],
        "only_in_1e-4_at_most_1e-5_examples": [list(map(str, k)) for k in only4 if k[3] <= 1e-5][
            :5
        ],
    }
    ev.update(
        {
            "extra_hits": extra,
            "extra_share_of_1e-4_table": round(extra / len(tables[1e-4]), 4),
            "hits_with_evalue_above_1e-5_in_1e-4_table": above,
            "hits_passing_max_evalue_1e-30_among_those": int(
                ((tables[1e-4].evalue > 1e-5) & (tables[1e-4].evalue < 1e-30)).sum()
            ),
            "threads": args.threads,
        }
    )
    res["aligner_evalue"] = ev
    args.out.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
