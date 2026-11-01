"""fseof parameter sweep on iJO1366.

Runs ``raven_toolbox.analysis.fseof`` on iJO1366 (cobrapy ``iJO1366.xml.gz``, its own
biomass objective ``BIOMASS_Ec_iJO1366_core_53p95M``) with target ``EX_succ_e`` at the
defaults (n_steps 10, max_fraction 0.9, correlation_threshold 0.9, flux_eps 1e-6,
equality False) and with one parameter changed at a time:

* n_steps 5, 20
* max_fraction 0.5, 0.99
* correlation_threshold 0.7, 0.95

Each configuration runs ``--repeats`` times, each on a freshly read model, with Gurobi.

For each run it reports the counts per target type and compares the target set with the
first default run: targets added and dropped, by type. Two operational criteria mark
targets that may be spurious:

* ``added``: a target found at the swept value and not with the defaults.
* ``noise``: a target whose absolute flux has a standard deviation (ddof 0) across the
  scan below 1e-6.

For each added target it also gives the correlation and standard deviation of the
same reaction's absolute flux in the first default scan.

Outputs in ``--outdir``: sweep_summary.tsv (one row per run), sweep_targets.tsv
(targets of the first run of each configuration, with slope, r, std, in-default flag),
sweep.json (summary, versions, input checksum).

Command line (see sbatch_sweep.sh):
    $BENCH_PY fseof_sweep.py --outdir $OUT --repeats 3
with PYTHONPATH=<raven-toolbox checkout>/src (env_py.sh).
"""

import argparse
import gzip
import hashlib
import json
import os
import shutil
import sys
import time

import cobra
import numpy as np
import pandas as pd
from cobra.io import read_sbml_model
from scipy.stats import linregress

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from versions import versions  # noqa: E402

from raven_toolbox.analysis import fseof  # noqa: E402

NOISE_STD = 1e-6
TARGET = "EX_succ_e"
DEFAULT = {"n_steps": 10, "max_fraction": 0.9, "correlation_threshold": 0.9}
CONFIGS = [
    ("default", None, None),
    ("n_steps", "n_steps", 5),
    ("n_steps", "n_steps", 20),
    ("max_fraction", "max_fraction", 0.5),
    ("max_fraction", "max_fraction", 0.99),
    ("correlation_threshold", "correlation_threshold", 0.7),
    ("correlation_threshold", "correlation_threshold", 0.95),
]

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--outdir", required=True)
ap.add_argument("--repeats", type=int, default=3)
ap.add_argument("--tmp", default=os.environ.get("TMPDIR", "/tmp"))
args = ap.parse_args()
os.makedirs(args.outdir, exist_ok=True)

src = os.path.join(os.path.dirname(cobra.__file__), "data", "iJO1366.xml.gz")
with open(src, "rb") as f:
    sha = hashlib.sha256(f.read()).hexdigest()
sbml = os.path.join(args.tmp, "iJO1366.xml")
with gzip.open(src) as f, open(sbml, "wb") as o:
    shutil.copyfileobj(f, o)


def annotate(r):
    t = r.targets.copy()
    scan = r.scan.loc[t.reaction, r.enforced].abs()
    t["std_abs"] = scan.std(axis=1, ddof=0).to_numpy()
    t["kdko"] = t.target_type.isin(["knockdown", "knockout"])
    return t


summary, target_rows, runs = [], [], {}
default_t = default_scan = None
for rep in range(1, args.repeats + 1):
    for _label, key, value in CONFIGS:
        m = read_sbml_model(sbml)
        m.solver = "gurobi"
        kw = dict(DEFAULT)
        if key:
            kw[key] = value
        t0 = time.time()
        r = fseof(m, TARGET, **kw)
        secs = time.time() - t0
        t = annotate(r)
        name = "default" if key is None else f"{key}={value}"
        if key is None and rep == 1:
            default_t, default_scan, default_enf = t, r.scan, np.asarray(r.enforced)
        dset = dict(zip(default_t.reaction, default_t.target_type, strict=False))
        cur = dict(zip(t.reaction, t.target_type, strict=False))
        added = {k: v for k, v in cur.items() if k not in dset}
        dropped = {k: v for k, v in dset.items() if k not in cur}
        relabelled = {k: (dset[k], v) for k, v in cur.items() if k in dset and dset[k] != v}
        noise = set(t.reaction[t.std_abs < NOISE_STD])
        c = t.target_type.value_counts()
        row = {
            "config": name,
            "parameter": key or "default",
            "value": value if key else "",
            "rep": rep,
            "n_levels": len(r.enforced),
            "enforced_last": r.enforced[-1],
            "amplify": int(c.get("amplify", 0)),
            "knockdown": int(c.get("knockdown", 0)),
            "knockout": int(c.get("knockout", 0)),
            "added_amplify": sum(v == "amplify" for v in added.values()),
            "added_kdko": sum(v != "amplify" for v in added.values()),
            "dropped_amplify": sum(v == "amplify" for v in dropped.values()),
            "dropped_kdko": sum(v != "amplify" for v in dropped.values()),
            "relabelled": len(relabelled),
            "noise_targets": len(noise),
            "noise_amplify": int(((t.std_abs < NOISE_STD) & (t.target_type == "amplify")).sum()),
            "added_noise": len(noise & set(added)),
            "seconds": round(secs, 1),
        }
        row["kdko"] = row["knockdown"] + row["knockout"]
        summary.append(row)
        print(json.dumps(row))
        if rep == 1:
            runs[name] = {"added": added, "dropped": dropped, "relabelled": relabelled}
            for _, x in t.iterrows():
                target_rows.append(
                    {
                        "config": name,
                        "reaction": x.reaction,
                        "target_type": x.target_type,
                        "slope": x.slope,
                        "correlation": x.correlation,
                        "std_abs": x.std_abs,
                        "in_default": x.reaction in dset,
                    }
                )
            for rid, ttype in added.items():
                a = default_scan.loc[rid, list(default_enf)].abs().to_numpy(dtype=float)
                ok = a.std() > 0
                runs[name].setdefault("added_detail", []).append(
                    {
                        "reaction": rid,
                        "type": ttype,
                        "r_here": float(t.loc[t.reaction == rid, "correlation"].iloc[0]),
                        "std_here": float(t.loc[t.reaction == rid, "std_abs"].iloc[0]),
                        "r_default_scan": float(linregress(default_enf, a).rvalue) if ok else None,
                        "std_default_scan": float(a.std()),
                    }
                )
            for k in ("added_detail",):
                for d in runs[name].get(k, []):
                    print("  added", json.dumps(d))
            for rid, ttype in dropped.items():
                print("  dropped", rid, ttype)

pd.DataFrame(summary).to_csv(os.path.join(args.outdir, "sweep_summary.tsv"), sep="\t", index=False)
pd.DataFrame(target_rows).to_csv(
    os.path.join(args.outdir, "sweep_targets.tsv"), sep="\t", index=False, float_format="%.6g"
)
stable = {}
for row in summary:
    stable.setdefault(row["config"], set()).add(
        (
            row["amplify"],
            row["knockdown"],
            row["knockout"],
            row["added_amplify"],
            row["added_kdko"],
            row["dropped_amplify"],
            row["dropped_kdko"],
        )
    )
print("identical counts across repeats:", {k: len(v) == 1 for k, v in stable.items()})
out = {
    "input": {"path": src, "sha256": sha},
    "target": TARGET,
    "defaults": DEFAULT,
    "noise_std": NOISE_STD,
    "summary": summary,
    "rep1": runs,
    "versions": versions(m),
}
with open(os.path.join(args.outdir, "sweep.json"), "w") as f:
    json.dump(out, f, indent=1, default=str)
print("versions", json.dumps(out["versions"]))
