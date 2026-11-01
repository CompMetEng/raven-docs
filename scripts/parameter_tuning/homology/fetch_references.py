#!/usr/bin/env python
"""Download the gene-KO references and the S. cerevisiae ORF translations.

Writes into OUT:
  kegg118_organism_gene_ko_5org.tsv.gz  rows of KEGG release 118 ``organism_gene_ko``
      (from the raven-toolbox ``kegg118_core.tar.gz`` release asset, sha256 checked
      against the toolbox registry) for sce, kla, yli, ani, eco; header kept.
  kegg118_ko_check.json  how many of those KOs are linked to a reaction in
      ``ko_reaction`` of the same bundle.
  keggrest_organism_gene_ko_all.tsv.gz  current KEGG (REST ``link/ko/<org>``), all KOs.
  keggrest_organism_gene_ko_rxn.tsv.gz  the same, only KOs listed by ``link/reaction/ko``
      (the reaction-linked subset, as in the release-118 table).
  keggrest_info.txt  output of ``info/kegg`` (release and date).
  sgd_orf_trans_all.fasta.gz  SGD S288C translated ORFs (template proteome).
  oma_version.json  OMA browser API ``/api/version/``.
  manifest_references.json  URL, UTC time, size and sha256 of every download.

KEGG REST requests are sequential with a 1 s pause.

    python fetch_references.py --out $W/refs --kegg118-sha256 <sha>
"""

from __future__ import annotations

import argparse
import datetime
import gzip
import hashlib
import io
import json
import pathlib
import tarfile
import time
import urllib.request

ORGS = ("sce", "kla", "yli", "ani", "eco")
KEGG118_URL = (
    "https://github.com/CompMetEng/toolbox-assets/releases/download/kegg118/kegg118_core.tar.gz"
)
SGD_URL = (
    "http://sgd-archive.yeastgenome.org/sequence/S288C_reference/orf_protein/orf_trans_all.fasta.gz"
)
OMA_VERSION_URL = "https://omabrowser.org/api/version/"

manifest: list[dict] = []


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "raven-toolbox-studies/1.0"})
    with urllib.request.urlopen(req, timeout=900) as fh:
        data = fh.read()
    manifest.append(
        {
            "url": url,
            "fetched_utc": datetime.datetime.now(datetime.UTC).isoformat(),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    )
    print(f"got {url}: {len(data)} bytes", flush=True)
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--kegg118-sha256", required=True)
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    # KEGG 118 release table
    core = get(KEGG118_URL)
    sha = hashlib.sha256(core).hexdigest()
    if sha != args.kegg118_sha256:
        raise SystemExit(f"kegg118_core sha256 {sha} != registry {args.kegg118_sha256}")
    with tarfile.open(fileobj=io.BytesIO(core), mode="r:gz") as tar:
        names = tar.getnames()
        ogk_name = next(n for n in names if n.endswith("organism_gene_ko.tsv.gz"))
        kr_name = next(n for n in names if n.endswith("ko_reaction.tsv.gz"))
        ogk = gzip.decompress(tar.extractfile(ogk_name).read()).decode("utf-8").splitlines()
        kr = gzip.decompress(tar.extractfile(kr_name).read()).decode("utf-8").splitlines()
    header, kept = ogk[0], [line for line in ogk[1:] if line.split("\t", 1)[0] in ORGS]
    with gzip.open(out / "kegg118_organism_gene_ko_5org.tsv.gz", "wt", encoding="utf-8") as fh:
        fh.write(header + "\n" + "\n".join(kept) + "\n")
    rxn_kos = {line.split("\t")[0] for line in kr[1:]}
    all_kos_118 = {line.split("\t")[2] for line in ogk[1:]}
    check = {
        "members": names,
        "organism_gene_ko_header": header,
        "rows_all_orgs": len(ogk) - 1,
        "organisms_in_table": len({line.split("\t", 1)[0] for line in ogk[1:]}),
        "kos_in_table": len(all_kos_118),
        "kos_in_ko_reaction": len(rxn_kos),
        "kos_in_table_with_reaction": len(all_kos_118 & rxn_kos),
        "example_rows": kept[:3],
        "rows_per_org": {o: sum(1 for line in kept if line.startswith(o + "\t")) for o in ORGS},
        "genes_per_org": {
            o: len({line.split("\t")[1] for line in kept if line.startswith(o + "\t")})
            for o in ORGS
        },
    }
    (out / "kegg118_ko_check.json").write_text(json.dumps(check, indent=2))
    del ogk, kr, core

    # Current KEGG via REST
    (out / "keggrest_info.txt").write_bytes(get("https://rest.kegg.jp/info/kegg"))
    time.sleep(1)
    rxn_link = get("https://rest.kegg.jp/link/reaction/ko").decode().splitlines()
    rest_rxn_kos = {line.split("\t")[0].removeprefix("ko:") for line in rxn_link if line}
    rows = []
    for org in ORGS:
        time.sleep(1)
        for line in get(f"https://rest.kegg.jp/link/ko/{org}").decode().splitlines():
            if not line:
                continue
            gene, ko = line.split("\t")
            rows.append((org, gene.split(":", 1)[1], ko.removeprefix("ko:")))
    for name, keep in (("all", lambda r: True), ("rxn", lambda r: r[2] in rest_rxn_kos)):
        with gzip.open(
            out / f"keggrest_organism_gene_ko_{name}.tsv.gz", "wt", encoding="utf-8"
        ) as fh:
            fh.write(header + "\n")
            for r in rows:
                if keep(r):
                    fh.write("\t".join(r) + "\n")
    check_rest = {
        "kos_with_reaction": len(rest_rxn_kos),
        "rows_per_org_all": {o: sum(1 for r in rows if r[0] == o) for o in ORGS},
        "rows_per_org_rxn": {
            o: sum(1 for r in rows if r[0] == o and r[2] in rest_rxn_kos) for o in ORGS
        },
    }
    (out / "keggrest_check.json").write_text(json.dumps(check_rest, indent=2))

    (out / "sgd_orf_trans_all.fasta.gz").write_bytes(get(SGD_URL))
    (out / "oma_version.json").write_bytes(get(OMA_VERSION_URL))
    (out / "manifest_references.json").write_text(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
