#!/bin/bash
# S7: random_objective with replace_max_bound False and True on the 4102-reaction yeast-GEM.
#SBATCH -N 1
#SBATCH -c 12
#SBATCH --mem=32G
set -euo pipefail
source "${STUDY:?set STUDY}/jobs/env.sh"
cd $STUDY
echo "cpus $SLURM_CPUS_PER_TASK, start $(date -Is)"
$PY $STUDY/env_report.py $Y4102
$PY $STUDY/random_objective_bounds.py --model $Y4102 --n-samples 200 --seed 0 --n-proc 12 --n-probe 50 --out results/ --save-samples $DATA/s7_false.npz
echo "end $(date -Is)"
