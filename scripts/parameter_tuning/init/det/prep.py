"""Build PrepData for the Human-GEM v2.0.0-38 export (optionally minus an edit list).

Reads Human-GEM.yml, removes the reaction ids of --remove (JSON list), and runs
estimateEssentialGenes._prep_human_model_for_ftinit with the essential tasks.
Command line: python prep.py --model <Human-GEM.yml> --out <prep.pkl> [--remove <ids.json>]
"""

import argparse
import json
import pickle
import sys
import time

import cobra

sys.setrecursionlimit(10000)
cobra.Configuration().processes = 1
import estimateEssentialGenes as eeg  # noqa: E402

from raven_toolbox.io import read_yaml_model  # noqa: E402
from raven_toolbox.tasks.tasklist import parse_task_list  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--remove")  # json list of reaction ids to remove from the template
a = ap.parse_args()
t0 = time.time()
model = read_yaml_model(a.model)
print("model", len(model.reactions), len(model.genes), flush=True)
if a.remove:
    ids = json.load(open(a.remove))
    model.remove_reactions(ids, remove_orphans=True)
    print("removed", len(ids), flush=True)
tasks = parse_task_list(eeg.ESSENTIAL_TASKS)
prep = eeg._prep_human_model_for_ftinit(model, tasks)
print(
    "ref",
    len(prep.ref_model.reactions),
    "merged",
    len(prep.min_model.reactions),
    "essential",
    len(prep.essential_rxns),
    "tasks",
    len(prep.tasks),
    flush=True,
)
pickle.dump(prep, open(a.out, "wb"))
print("TIMING prep", round(time.time() - t0), "s")
