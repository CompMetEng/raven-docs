# Environment for the Python benchmark scripts (sourced by the sbatch files).
# Required before sourcing: RAVEN_TOOLBOX (checkout of raven-toolbox at 94f3940)
# and BENCH_PY (python of the venv with cobra 0.32.1 and gurobipy), GUROBI_HOME (Gurobi 13.0.1 installation).
module purge
module load SciPy-bundle/2026.05-gfbf-2026.1
export GUROBI_HOME=${GUROBI_HOME:?set GUROBI_HOME}
export GRB_LICENSE_FILE=$GUROBI_HOME/gurobi.lic
export LD_LIBRARY_PATH=$GUROBI_HOME/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=$RAVEN_TOOLBOX/src
