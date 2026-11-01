#!/bin/bash
#SBATCH -c 4
#SBATCH --mem=64G
#SBATCH -t 1-00:00:00
# Slurm wrapper for the MATLAB side of the Human-GEM validation (example).
#
# Usage:
#   export WORK=... RAVEN_ROOT=... HUMANGEM_ROOT=... BIGM_SCRIPTS=<folder of the .m files>
#   sbatch -A <account> -J mlprep  -o $WORK/logs/%x-%j.out $BIGM_SCRIPTS/mljob.sh ml_prep
#   sbatch -A <account> -J ml-DLD1 -o $WORK/logs/%x-%j.out $BIGM_SCRIPTS/mljob.sh ml_cell DLD1
#
# Environment:
#   WORK            work folder ($WORK/out, $WORK/shared)
#   RAVEN_ROOT      RAVEN checkout (commit 2d0630e3)
#   HUMANGEM_ROOT   Human-GEM git clone; HUMANGEM_COMMIT (default 38567ab8) is exported into
#                   $TMPDIR/hg, which the .m files receive as HUMANGEM_ROOT
#   MATLAB          MATLAB executable (R2024b)
#   MATLAB_PREFS    optional matlabprefs.mat copied into the temporary preference folder
#   GUROBI_HOME     Gurobi 13.0.1 installation (required); GRB_LICENSE_FILE is
#                   always set to its gurobi.lic, whatever the calling shell exported
module purge
: "${WORK:?set WORK}" "${RAVEN_ROOT:?set RAVEN_ROOT}" "${HUMANGEM_ROOT:?set HUMANGEM_ROOT}"
HUMANGEM_COMMIT=${HUMANGEM_COMMIT:-38567ab8}
B=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
[ -f "$B/ml_common.m" ] || B=${BIGM_SCRIPTS:?set BIGM_SCRIPTS to the folder of the .m files}
HGREPO=$HUMANGEM_ROOT
export HUMANGEM_ROOT=$TMPDIR/hg OUT=${OUT:-$WORK/out} SHARED=${SHARED:-$WORK/shared} CELL=$2 RAVEN_ROOT
export GUROBI_HOME=${GUROBI_HOME:?set GUROBI_HOME}
export GRB_LICENSE_FILE=$GUROBI_HOME/gurobi.lic
export LD_LIBRARY_PATH=$GUROBI_HOME/lib
mkdir -p "$OUT" "$SHARED" "$HUMANGEM_ROOT"
git -C "$HGREPO" archive "$HUMANGEM_COMMIT" model data/datasets data/metabolicTasks code | tar -x -C "$HUMANGEM_ROOT"
export MATLAB_PREFDIR=$TMPDIR/prefs; mkdir -p $MATLAB_PREFDIR
[ -n "$MATLAB_PREFS" ] && cp "$MATLAB_PREFS" $MATLAB_PREFDIR/
cd $TMPDIR
echo "RAVEN $(git -C "$RAVEN_ROOT" log --oneline -1)"
MATLAB=${MATLAB:?set MATLAB to the MATLAB executable}
$MATLAB -batch "run('$B/$1.m')"
