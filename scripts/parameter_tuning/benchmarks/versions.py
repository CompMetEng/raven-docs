"""Software versions of a benchmark run.

Imported by small.py, fseof_sweep.py and gapfill_threshold.py. ``versions(model)``
returns a dict with the Python, cobra, optlang, gurobipy and Gurobi library versions,
the optlang interface of ``model``, the raven-toolbox path and its git commit, and
the libgurobi shared objects mapped into the process (read from /proc/self/maps after
a solve, so it names the library that actually solved).
"""

import os
import platform
import subprocess


def versions(model=None):
    import cobra
    import optlang

    import raven_toolbox

    out = {
        "python": platform.python_version(),
        "cobra": cobra.__version__,
        "optlang": optlang.__version__,
        "raven_toolbox_file": raven_toolbox.__file__,
    }
    src = os.path.dirname(os.path.dirname(os.path.dirname(raven_toolbox.__file__)))
    try:
        out["raven_toolbox_commit"] = subprocess.run(
            ["git", "-C", src, "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip()
        out["raven_toolbox_dirty"] = bool(
            subprocess.run(
                ["git", "-C", src, "status", "--porcelain", "--untracked-files=no"],
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except OSError:
        pass
    try:
        import gurobipy

        out["gurobipy"] = gurobipy.__version__
        out["gurobi_library"] = ".".join(map(str, gurobipy.gurobi.version()))
    except Exception as e:  # noqa: BLE001
        out["gurobipy"] = f"unavailable: {e}"
    if model is not None:
        out["solver_interface"] = model.solver.interface.__name__
    try:
        with open("/proc/self/maps") as f:
            libs = sorted({line.split()[-1] for line in f if "libgurobi" in line})
        out["libgurobi_mapped"] = libs
    except OSError:
        pass
    return out
