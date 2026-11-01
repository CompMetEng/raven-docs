#!/usr/bin/env python3
"""Whole-model comparison of the two KEGG reconstruction paths for one organism.

Builds the organism's draft model twice with raven-toolbox:

- annotation path: ``get_kegg_model_for_organism_from_artefacts(org, artefacts)``,
  genes and KOs from the ``organism_gene_ko`` table;
- HMM path: ``get_kegg_model_from_sequences_with_artefacts(proteome, artefacts, library,
  cutoff, min_score_ratio_ko, min_score_ratio_g)``, KOs assigned by ``hmmsearch`` of the
  KO library against the proteome.

Both use the default keep flags (``keep_spontaneous``, ``keep_undefined_stoich``,
``keep_incomplete`` true, ``keep_general`` false). It reports the numbers of reactions,
metabolites and genes of each model, the shared reactions, metabolites and genes
(the ``org:`` prefix of the HMM-path gene ids is stripped) and their Jaccard indices,
and writes them as JSON.

Inputs: ``--artefacts`` the directory of the KEGG core artefacts (version-prefixed
names allowed), ``--library`` the domain HMM library flatfile, ``--proteome`` a FASTA
with ``>org:gene`` headers. ``--settings`` takes one or more
``cutoff,ratio_ko,ratio_g`` triples; each runs one HMM-path build.

Example:
    python compare_kegg_paths.py --org sce --proteome sce.faa \
        --artefacts $XDG_CACHE_HOME/raven_toolbox/data/kegg-kegg118 \
        --library kegg118_eukaryotes.hmm --domain eukaryotes --threads 16 \
        --settings 1e-50,0.3,0.8 --json wholemodel_sce.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from raven_toolbox.reconstruction.kegg.organism import get_kegg_model_for_organism_from_artefacts
from raven_toolbox.reconstruction.kegg.query import get_kegg_model_from_sequences_with_artefacts


def ids(model, strip=False):
    rx = {r.id for r in model.reactions}
    mets = {m.id for m in model.metabolites}
    genes = {g.id.split(":", 1)[1] if strip and ":" in g.id else g.id for g in model.genes}
    return rx, mets, genes


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--org", required=True)
    ap.add_argument("--proteome", type=Path, required=True)
    ap.add_argument("--artefacts", type=Path, required=True)
    ap.add_argument("--library", type=Path, required=True)
    ap.add_argument("--domain", default="eukaryotes")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--settings", nargs="+", default=["1e-50,0.3,0.8"])
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    ann = get_kegg_model_for_organism_from_artefacts(args.org, args.artefacts)
    a_rx, a_met, a_gene = ids(ann)
    out = {
        "org": args.org,
        "annotation": {"reactions": len(a_rx), "metabolites": len(a_met), "genes": len(a_gene)},
        "hmm": [],
    }
    print(
        f"{args.org} annotation path: {len(a_rx)} reactions, {len(a_met)} metabolites, "
        f"{len(a_gene)} genes"
    )
    for setting in args.settings:
        cutoff, rko, rg = (float(x) for x in setting.split(","))
        t0 = time.perf_counter()
        hmm = get_kegg_model_from_sequences_with_artefacts(
            args.proteome,
            args.artefacts,
            args.library,
            domain=args.domain,
            model_id=args.org,
            cutoff=cutoff,
            min_score_ratio_ko=rko,
            min_score_ratio_g=rg,
            threads=args.threads,
        )
        secs = time.perf_counter() - t0
        h_rx, h_met, h_gene = ids(hmm, strip=True)
        row = {
            "cutoff": cutoff,
            "ko_ratio": rko,
            "g_ratio": rg,
            "seconds": secs,
            "threads": args.threads,
            "reactions": len(h_rx),
            "metabolites": len(h_met),
            "genes": len(h_gene),
            "shared_reactions": len(a_rx & h_rx),
            "shared_metabolites": len(a_met & h_met),
            "shared_genes": len(a_gene & h_gene),
            "jaccard_reactions": jaccard(a_rx, h_rx),
            "jaccard_metabolites": jaccard(a_met, h_met),
            "jaccard_genes": jaccard(a_gene, h_gene),
        }
        out["hmm"].append(row)
        print(
            f"{args.org} HMM path {setting}: {len(h_rx)} reactions, {len(h_met)} metabolites, "
            f"{len(h_gene)} genes; shared reactions {row['shared_reactions']}/{len(a_rx)} "
            f"(Jaccard {row['jaccard_reactions']:.2f}), shared genes "
            f"{row['shared_genes']}/{len(a_gene)} (Jaccard {row['jaccard_genes']:.2f}); "
            f"{secs:.0f} s",
            flush=True,
        )
    if args.json:
        args.json.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
