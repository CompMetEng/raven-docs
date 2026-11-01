# Environment of every job of the sampling study (sourced by the sbatch scripts).
# Required in the environment of sbatch:
#   STUDY              this study folder (scripts/parameter_tuning/sampling)
#   RAVEN_TOOLBOX_DIR  raven-toolbox checkout (commit 94f3940); its src/ goes on PYTHONPATH
#   PY                 Python interpreter (cobra 0.32.1, optlang 1.9.1, gurobipy 13.0.3)
#   DATA               work folder for chain pickles and sample matrices
#   Y4105, Y4102, ECORE  yeast-GEM 9.1.1 (4105 reactions), yeast-GEM 9.1.0 (4102 reactions) and
#                      the cobra e_coli_core file (cobra/data/textbook.xml.gz)
#   GUROBI_HOME        Gurobi 13.0.1 installation; only its gurobi.lic is used
: "${STUDY:?}" "${RAVEN_TOOLBOX_DIR:?}" "${PY:?}" "${DATA:?}" "${Y4105:?}" "${Y4102:?}" "${ECORE:?}"
module purge
module load SciPy-bundle/2026.05-gfbf-2026.1
export PYTHONPATH=$RAVEN_TOOLBOX_DIR/src
export GUROBI_HOME=${GUROBI_HOME:?set GUROBI_HOME}
export GRB_LICENSE_FILE=$GUROBI_HOME/gurobi.lic
export LD_LIBRARY_PATH=$GUROBI_HOME/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
