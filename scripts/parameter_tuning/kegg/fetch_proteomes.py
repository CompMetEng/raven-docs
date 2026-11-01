#!/usr/bin/env python3
"""Fetch the proteomes of the KEGG HMM cut-off study from KEGG REST and UniProt.

For each KEGG organism code (default sce, cme, eco, mge) this writes two protein
FASTA files with headers ``>org:gene``:

- ``kegg_rest/<org>.faa``: every gene of type CDS in ``https://rest.kegg.jp/list/<org>``,
  sequences from ``https://rest.kegg.jp/get/<id1>+...+<id10>/aaseq`` (10 ids per
  request, one request at a time, at most about 3 requests per second);
- ``uniprot/<org>.faa``: the UniProt reference proteome, relabelled to the KEGG
  gene id from the UniProt KEGG cross-reference with the exact organism prefix
  (entries without one are dropped), as ``homology_cutoff_kegg.py fetch`` does.

It writes ``counts.json`` (sequence counts per source, request dates and URLs) and
packs everything into one ``.tar.gz`` given by ``--archive``.

Command line used:
    python -I fetch_proteomes.py --work $TMPDIR/prot \
        --archive $DATA/kegg_proteomes_2026-11-01.tar.gz
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import tarfile
import time
import urllib.error
import urllib.request

UNIPROT = {
    "sce": "UP000002311",
    "cme": "UP000007014",
    "eco": "UP000000625",
    "mge": "UP000000807",
}
KEGG = "https://rest.kegg.jp"
_last = [0.0]


def get(url: str, *, pause: float = 0.35, tries: int = 5) -> str:
    for attempt in range(tries):
        wait = _last[0] + pause - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            with urllib.request.urlopen(url, timeout=300) as fh:
                return fh.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == tries - 1:
                raise
            print(f"retry {attempt + 1} for {url}: {exc}", flush=True)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def parse_fasta(text: str) -> dict[str, str]:
    out, name, seq = {}, None, []
    for line in text.splitlines():
        if line.startswith(">"):
            if name:
                out[name] = "".join(seq)
            name, seq = line[1:].split()[0], []
        elif name:
            seq.append(line.strip())
    if name:
        out[name] = "".join(seq)
    return out


def write_fasta(path: pathlib.Path, seqs: dict[str, str]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for name, seq in seqs.items():
            fh.write(f">{name}\n")
            for i in range(0, len(seq), 60):
                fh.write(seq[i : i + 60] + "\n")


def kegg_rest(org: str, out: pathlib.Path) -> dict:
    listing = get(f"{KEGG}/list/{org}")
    types: dict[str, int] = {}
    cds = []
    for line in listing.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        types[parts[1]] = types.get(parts[1], 0) + 1
        if parts[1] == "CDS":
            cds.append(parts[0] if ":" in parts[0] else f"{org}:{parts[0]}")
    seqs: dict[str, str] = {}
    for i in range(0, len(cds), 10):
        chunk = cds[i : i + 10]
        try:
            text = get(f"{KEGG}/get/{'+'.join(chunk)}/aaseq")
        except urllib.error.HTTPError as exc:  # 404 if none of the ids has a sequence
            print(f"{org}: HTTP {exc.code} for chunk {i}", flush=True)
            continue
        seqs.update(parse_fasta(text))
        if i % 500 == 0:
            print(f"{org}: {len(seqs)}/{len(cds)}", flush=True)
    write_fasta(out / f"{org}.faa", seqs)
    return {
        "list_entries": sum(types.values()),
        "types": types,
        "cds": len(cds),
        "sequences": len(seqs),
        "cds_without_sequence": len(set(cds) - set(seqs)),
    }


def uniprot(org: str, out: pathlib.Path) -> dict:
    upid = UNIPROT[org]
    rows = get(
        f"https://rest.uniprot.org/uniprotkb/stream?query=proteome:{upid}"
        f"&format=tsv&fields=accession,xref_kegg",
        pause=1,
    ).splitlines()[1:]
    mapping = {}
    for line in rows:
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        for entry in filter(None, (p.strip() for p in parts[1].split(";"))):
            prefix, _, gene = entry.partition(":")
            if prefix == org:
                mapping[parts[0]] = f"{org}:{gene}"
                break
    fasta = get(
        f"https://rest.uniprot.org/uniprotkb/stream?query=proteome:{upid}&format=fasta", pause=1
    )
    raw = parse_fasta(fasta)
    seqs, dup = {}, 0
    for name, seq in raw.items():
        parts = name.split("|")
        acc = parts[1] if len(parts) > 2 else parts[0]
        gene = mapping.get(acc)
        if gene is None:
            continue
        if gene in seqs:
            dup += 1
            continue
        seqs[gene] = seq
    write_fasta(out / f"{org}.faa", seqs)
    return {
        "proteome": upid,
        "entries": len(raw),
        "mapped_unique_genes": len(seqs),
        "duplicate_gene_ids": dup,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", type=pathlib.Path, required=True)
    ap.add_argument("--archive", type=pathlib.Path, required=True)
    ap.add_argument("--orgs", nargs="+", default=["sce", "cme", "eco", "mge"])
    args = ap.parse_args()
    (args.work / "kegg_rest").mkdir(parents=True, exist_ok=True)
    (args.work / "uniprot").mkdir(parents=True, exist_ok=True)
    info = {
        "date_utc": dt.datetime.now(dt.UTC).isoformat(),
        "kegg_info": get(f"{KEGG}/info/kegg").strip().splitlines(),
        "urls": {
            "kegg_list": f"{KEGG}/list/<org>",
            "kegg_aaseq": f"{KEGG}/get/<id>+...(10 ids)/aaseq",
            "uniprot_fasta": "https://rest.uniprot.org/uniprotkb/stream?query=proteome:<UP>&format=fasta",
            "uniprot_xref": "https://rest.uniprot.org/uniprotkb/stream?query=proteome:<UP>&format=tsv&fields=accession,xref_kegg",
        },
        "organisms": {},
    }
    for org in args.orgs:
        u = uniprot(org, args.work / "uniprot")
        print(org, "uniprot", u, flush=True)
        k = kegg_rest(org, args.work / "kegg_rest")
        print(org, "kegg_rest", k, flush=True)
        info["organisms"][org] = {"kegg_rest": k, "uniprot": u}
    (args.work / "counts.json").write_text(json.dumps(info, indent=1))
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.archive, "w:gz") as tar:
        for sub in ("counts.json", "kegg_rest", "uniprot"):
            tar.add(args.work / sub, arcname=sub)
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
