#!/usr/bin/env python
"""Run raven-toolbox's scripts/homology_cutoff_kegg.py with its UniProt downloads cached.

The study driver (``fetch``, ``align``, ``score``) downloads UniProt proteomes and
UniProt-to-KEGG id tables through its ``_stream`` function, and ``score`` repeats
those downloads. This wrapper loads the driver unchanged and replaces ``_stream``
with a disk cache, so every UniProt table is downloaded once, recorded (URL, time,
UniProt release headers) and reused offline by later jobs.

Extra subcommand ``prefetch --out W`` wraps the driver: it calls the driver's
``_uniprot_keys`` for every proteome and its ``_oma_truth`` for every OMA target, so
that the UniProt tables and the OMA pairs (written to ``W/oma_pairs_<code>.json``)
that ``score --reference oma`` needs are in the cache. Every other subcommand is
passed to the driver as is.

Environment:
    HOMOLOGY_SCRIPT     path to the driver, scripts/homology_cutoff_kegg.py of the raven-toolbox checkout
    HOMOLOGY_URL_CACHE  directory of cached downloads (``index.jsonl`` lists them)
    HOMOLOGY_OFFLINE=1  fail on a cache miss instead of downloading

Command lines:
    python run_cached.py --out $W fetch
    python run_cached.py prefetch --out $W
    python run_cached.py --out $W align    [--aligner diamond]
    python run_cached.py --out $W score    --beta 0.5 --gene-ko K.tsv.gz [--aligner diamond] [--reference oma]
"""

from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
import os
import pathlib
import sys
import urllib.request


def _load_driver():
    spec = importlib.util.spec_from_file_location(
        "homology_cutoff_kegg", os.environ["HOMOLOGY_SCRIPT"]
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cached_stream(cache: pathlib.Path):
    cache.mkdir(parents=True, exist_ok=True)

    def _stream(url: str) -> str:
        path = cache / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".txt")
        if path.is_file():
            return path.read_text(encoding="utf-8")
        if os.environ.get("HOMOLOGY_OFFLINE") == "1":
            raise RuntimeError(f"not in cache: {url}")
        with urllib.request.urlopen(url, timeout=900) as fh:
            text = fh.read().decode("utf-8")
            headers = {
                k: v
                for k, v in fh.headers.items()
                if k.lower().startswith("x-uniprot") or k.lower() in ("date", "x-total-results")
            }
        path.write_text(text, encoding="utf-8")
        with open(cache / "index.jsonl", "a", encoding="utf-8") as idx:
            idx.write(
                json.dumps(
                    {
                        "url": url,
                        "file": path.name,
                        "fetched_utc": datetime.datetime.now(datetime.UTC).isoformat(),
                        "headers": headers,
                        "lines": text.count("\n"),
                    }
                )
                + "\n"
            )
        print(f"downloaded {url} ({text.count(chr(10))} lines) {headers}", flush=True)
        return text

    return _stream


def main(argv: list[str]) -> int:
    mod = _load_driver()
    mod._stream = _cached_stream(pathlib.Path(os.environ["HOMOLOGY_URL_CACHE"]))
    if argv and argv[0] == "prefetch":
        out = pathlib.Path(argv[argv.index("--out") + 1])
        out.mkdir(parents=True, exist_ok=True)
        for code in mod.PROTEOMES:
            keys = mod._uniprot_keys(code)
            print(f"{code}: {len(keys)} UniProt keys with a KEGG id", flush=True)
        for code in mod.OMA_TARGETS:
            _, n_pairs, _ = mod._oma_truth(code, {}, {}, out)
            print(f"{code}: {n_pairs} OMA pairs cached", flush=True)
        return 0
    return mod.main(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
