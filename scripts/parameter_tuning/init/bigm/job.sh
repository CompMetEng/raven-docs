#!/bin/bash
#SBATCH -c 4
#SBATCH --mem=64G
#SBATCH -t 0-08:00:00
# Slurm wrapper for bm.py (example; account and log path go on the sbatch line).
#
# Usage:
#   export WORK=... TOOLBOX_ROOT=... HUMANGEM_ROOT=... PY=... BIGM_SCRIPTS=<folder of bm.py>
#   sbatch -A <account> -J step0 -o $WORK/logs/%x-%j.out $BIGM_SCRIPTS/job.sh step0 --cell HCT116
#
# Environment:
#   WORK            work folder; bm.py writes $WORK/out and reads/writes $WORK/shared
#   TOOLBOX_ROOT    raven-toolbox checkout (commit 94f3940); its src/ goes on PYTHONPATH
#   HUMANGEM_ROOT   Human-GEM git clone; HUMANGEM_COMMIT (default 38567ab8) is exported
#                   with git archive into $TMPDIR/hg, which bm.py receives as HUMANGEM_ROOT
#   PY              Python interpreter of the environment (cobra 0.32.1, optlang 1.9.1, gurobipy)
#   GUROBI_HOME     Gurobi 13.0.1 installation (required); GRB_LICENSE_FILE is
#                   always set to its gurobi.lic, whatever the calling shell exported
module purge
module load SciPy-bundle/2026.05-gfbf-2026.1
: "${WORK:?set WORK}" "${TOOLBOX_ROOT:?set TOOLBOX_ROOT}" "${HUMANGEM_ROOT:?set HUMANGEM_ROOT}"
HUMANGEM_COMMIT=${HUMANGEM_COMMIT:-38567ab8}
PY=${PY:-python3}
export GUROBI_HOME=${GUROBI_HOME:?set GUROBI_HOME}
export GRB_LICENSE_FILE=$GUROBI_HOME/gurobi.lic
export LD_LIBRARY_PATH=$GUROBI_HOME/lib PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
B=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
[ -f "$B/bm.py" ] || B=${BIGM_SCRIPTS:?set BIGM_SCRIPTS to the folder of bm.py}
HGREPO=$HUMANGEM_ROOT
export HUMANGEM_ROOT=$TMPDIR/hg OUT=${OUT:-$WORK/out} SHARED=${SHARED:-$WORK/shared}
mkdir -p "$OUT" "$SHARED" "$HUMANGEM_ROOT"
git -C "$HGREPO" archive "$HUMANGEM_COMMIT" model data/datasets data/metabolicTasks code/test | tar -x -C "$HUMANGEM_ROOT"
echo "host $(hostname) Human-GEM $HUMANGEM_COMMIT toolbox $(git -C "$TOOLBOX_ROOT" log --oneline -1)"
PYTHONPATH="$TOOLBOX_ROOT/src" "$PY" -c '
import sys, cobra, optlang, gurobipy
print("python", sys.version.split()[0], "cobra", cobra.__version__, "optlang", optlang.__version__,
      "gurobipy", gurobipy.__version__, "gurobi library", ".".join(map(str, gurobipy.gurobi.version())))
print("libgurobi", sorted({l.split()[-1] for l in open("/proc/self/maps") if "libgurobi" in l}))'
PYTHONPATH="$TOOLBOX_ROOT/src" "$PY" "$B/bm.py" "$@"
