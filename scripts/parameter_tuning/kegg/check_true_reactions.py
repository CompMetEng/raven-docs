#!/usr/bin/env python3
"""Count each organism's "true reactions" of the KEGG artefacts under several definitions.

``analyze_hmm_cutoffs.py`` defines the true reactions as every reaction that
``ko_reaction`` links to one of the organism's annotated KOs. This script prints that
count next to the counts restricted to reactions present in the reference model, and
further to reactions not flagged ``general`` in ``rxn_flags``, plus the numbers of
distinct KOs and gene→KO pairs.

Example:
    python check_true_reactions.py --artefacts $XDG_CACHE_HOME/raven_toolbox/data/kegg-kegg118 \
        --orgs sce cme eco mge --json true_reactions.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from raven_toolbox.io.yaml import read_yaml_model
from raven_toolbox.reconstruction.kegg.parse import _resolve_artefact, read_kegg_table


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artefacts", type=Path, required=True)
    ap.add_argument("--orgs", nargs="+", default=["sce", "cme", "eco", "mge"])
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    a = args.artefacts
    kr = read_kegg_table(_resolve_artefact(a, "ko_reaction.tsv.gz"))
    ogk = read_kegg_table(_resolve_artefact(a, "organism_gene_ko.tsv.gz"))
    flags = read_kegg_table(_resolve_artefact(a, "rxn_flags.tsv.gz"))
    ref = read_yaml_model(_resolve_artefact(a, "reference_model.yml.gz"))
    ref_rx = {r.id for r in ref.reactions}
    print("rxn_flags columns:", list(flags.columns), "rows:", len(flags))
    general = set()
    for col in flags.columns:
        if "general" in col.lower():
            general = set(
                flags.loc[flags[col].str.lower().isin(["1", "true", "yes"]), flags.columns[0]]
            )
    if not general and "flag" in flags.columns:
        general = set(flags.loc[flags["flag"].str.lower() == "general", flags.columns[0]])
    ko2rxn: dict[str, set[str]] = {}
    for ko, rxn in zip(kr["ko"], kr["reaction"], strict=True):
        ko2rxn.setdefault(ko, set()).add(rxn)
    out = {
        "ko_reaction_rows": len(kr),
        "ko_reaction_kos": len(ko2rxn),
        "ko_reaction_reactions": int(kr["reaction"].nunique()),
        "reference_model_reactions": len(ref_rx),
        "general_reactions": len(general),
        "organisms": {},
    }
    for org in args.orgs:
        rows = ogk[ogk["organism"].str.lower() == org]
        pairs = set(zip(rows["gene"], rows["ko"], strict=True))
        kos = {k for _, k in pairs}
        rx = {r for k in kos for r in ko2rxn.get(k, ())}
        d = {
            "pairs": len(pairs),
            "genes": int(rows["gene"].nunique()),
            "kos": len(kos),
            "kos_without_reaction": len(kos - set(ko2rxn)),
            "true_reactions": len(rx),
            "in_reference_model": len(rx & ref_rx),
            "in_reference_not_general": len((rx & ref_rx) - general),
        }
        out["organisms"][org] = d
        print(org, d, flush=True)
    print({k: v for k, v in out.items() if k != "organisms"})
    if args.json:
        args.json.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
