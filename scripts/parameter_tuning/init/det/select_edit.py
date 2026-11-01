"""Draw the template edit: 30 reactions of the reference model not kept by a build.

Candidates are prep.ref_model reactions absent from the first build in <build.json>
and not task-essential; random.Random(0).shuffle, first 30, sorted.
Command line: python select_edit.py <prep-base.pkl> <A-rtp1-1234-s1234.json> <edit-list.json>
"""

import json
import pickle
import random
import sys

import raven_toolbox.init  # noqa

prep = pickle.load(open(sys.argv[1], "rb"))
m0 = set(json.load(open(sys.argv[2]))[0]["reactions"])
cands = sorted(
    r.id
    for r in prep.ref_model.reactions
    if r.id not in m0 and r.id not in prep.essential_rxns and r.id.startswith("MAR0") is not None
)
cands = sorted(
    r.id for r in prep.ref_model.reactions if r.id not in m0 and r.id not in prep.essential_rxns
)
random.Random(0).shuffle(cands)
pick = sorted(cands[:30])
json.dump(pick, open(sys.argv[3], "w"))
print(len(cands), "candidates; picked", len(pick), pick)
