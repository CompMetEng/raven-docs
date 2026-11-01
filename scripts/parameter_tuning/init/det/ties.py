"""Tied-score blocks of the step-1 merged scores per Hart2015 cell line.

Loads the base PrepData, scores every Hart2015 cell line as estimateEssentialGenes.py
does, applies ftinit's private _nudge_scores and group_rxn_scores with the step-1
ignore mask, and prints the negative-score count, the share in tied blocks and the
three largest blocks. Needs the Human-GEM 1ea27d8b code/test on PYTHONPATH (env.sh).
Command line: python ties.py <prep-base.pkl>
"""

import collections
import pickle
import sys

import raven_toolbox.init  # noqa
from raven_toolbox.init import get_init_steps
from raven_toolbox.init.merge import group_rxn_scores

FT = sys.modules["raven_toolbox.init.ftinit"]
import estimateEssentialGenes as eeg  # noqa: E402

prep = pickle.load(open(sys.argv[1], "rb"))
tissues, expr = eeg._read_rnaseq(eeg.RNASEQ_FILE)
step = get_init_steps("1+1")[0]
blocks = {}
for t in tissues:
    gs = eeg.gene_scores_from_expression(expr[t], eeg.EXPRESSION_THRESHOLD)
    rs = FT._nudge_scores(eeg.score_reactions_from_genes(prep.ref_model, gs))
    sc = group_rxn_scores(
        prep.min_model, rs, prep.orig_rxn_ids, prep.group_ids, prep.masks.ignored(step.ignore_mask)
    )
    neg = {r: s for r, s in sc.items() if s < 0}
    c = collections.Counter(round(s, 6) for s in neg.values())
    top = c.most_common(3)
    inblock = sum(v for k, v in c.items() if v > 1)
    nogpr = sum(1 for r in prep.ref_model.reactions if not r.gene_reaction_rule)
    print(
        t,
        "negative",
        len(neg),
        "in tied blocks",
        inblock,
        round(100 * inblock / len(neg), 1),
        "top",
        top,
        flush=True,
    )
    blocks[t] = top[0]
print(
    "GPRless ref reactions",
    nogpr,
    "ref",
    len(prep.ref_model.reactions),
    "merged",
    len(prep.min_model.reactions),
)
