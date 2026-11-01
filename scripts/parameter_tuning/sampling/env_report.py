#!/usr/bin/env python3
"""Print the software versions, the solver and the input file ids of a sampling run.

Prints Python, cobra, optlang, gurobipy (and the Gurobi library version it
loads), numpy, pandas, scipy, the raven-toolbox commit and the solver that
cobra selects for each model, with the sha256, the SBML model id and the
reaction count of each model file given on the command line.

Inputs: model files as arguments; RAVEN_TOOLBOX_DIR (the raven-toolbox
checkout whose src/ is on PYTHONPATH) for the commit.

Command line used:
    python env_report.py <model.xml> [<model.xml.gz> ...]
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys


def versions() -> dict:
    import cobra
    import numpy
    import optlang
    import pandas
    import scipy

    out = {
        "python": sys.version.split()[0],
        "cobra": cobra.__version__,
        "optlang": optlang.__version__,
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "scipy": scipy.__version__,
    }
    try:
        import gurobipy

        out["gurobipy"] = gurobipy.__version__ if hasattr(gurobipy, "__version__") else None
        out["gurobi_library"] = ".".join(str(x) for x in gurobipy.gurobi.version())
    except Exception as exc:  # noqa: BLE001
        out["gurobipy"] = f"unavailable: {exc}"
    rt = os.environ.get("RAVEN_TOOLBOX_DIR")
    if rt:
        try:
            out["raven_toolbox_commit"] = subprocess.run(
                ["git", "-C", rt, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            ).stdout.strip()
        except Exception as exc:  # noqa: BLE001
            out["raven_toolbox_commit"] = f"unknown: {exc}"
    try:
        with open("/proc/cpuinfo") as fh:
            out["cpu_model"] = next(
                line.split(":", 1)[1].strip() for line in fh if line.startswith("model name")
            )
    except Exception:  # noqa: BLE001
        pass
    out["cpus_allowed"] = len(os.sched_getaffinity(0))
    return out


def model_info(path: str) -> dict:
    import cobra

    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    model = cobra.io.read_sbml_model(path)
    return {
        "file": path,
        "sha256": h.hexdigest(),
        "model_id": model.id,
        "n_reactions": len(model.reactions),
        "n_metabolites": len(model.metabolites),
        "solver_interface": model.solver.interface.__name__,
    }


if __name__ == "__main__":
    report = {"versions": versions(), "models": [model_info(p) for p in sys.argv[1:]]}
    print(json.dumps(report, indent=2))
