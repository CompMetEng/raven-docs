# Environment of the ftINIT determinism jobs; sourced by prep.sbatch, job.sbatch and edit.sbatch.
# Required before sbatch (exported into the job):
#   WORK           work folder: $WORK/out (build JSON), $WORK/logs
#   PREP_DIR       folder for prep-base.pkl and prep-edit.pkl, on a file system all nodes see
#                  (default $WORK/prep)
#   TOOLBOX_ROOT   raven-toolbox checkout (commit 94f3940)
#   HUMANGEM_ROOT  Human-GEM git clone; HUMANGEM_COMMIT (default 1ea27d8b = v2.0.0-38) is
#                  exported into $TMPDIR/hg, whose code/test goes on PYTHONPATH
#   DET_SCRIPTS    folder of these scripts
#   PY             Python interpreter (default python3)
module purge
module load SciPy-bundle/2026.05-gfbf-2026.1
export GUROBI_HOME=${GUROBI_HOME:?set GUROBI_HOME}
export GRB_LICENSE_FILE=$GUROBI_HOME/gurobi.lic
export LD_LIBRARY_PATH=$GUROBI_HOME/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
: "${WORK:?set WORK}" "${TOOLBOX_ROOT:?set TOOLBOX_ROOT}" "${HUMANGEM_ROOT:?set HUMANGEM_ROOT}" "${DET_SCRIPTS:?set DET_SCRIPTS}"
HUMANGEM_COMMIT=${HUMANGEM_COMMIT:-1ea27d8b}
P=${PREP_DIR:-$WORK/prep}
PY=${PY:-python3}
HGT=$TMPDIR/hg
mkdir -p "$HGT" "$P" "$WORK/out" "$WORK/logs"
git -C "$HUMANGEM_ROOT" archive "$HUMANGEM_COMMIT" model/Human-GEM.yml model/reactions.tsv data/datasets/Hart2015_RNAseq.txt data/metabolicTasks code/test | tar -x -C "$HGT"
export PYTHONPATH=$TOOLBOX_ROOT/src:$HGT/code/test
