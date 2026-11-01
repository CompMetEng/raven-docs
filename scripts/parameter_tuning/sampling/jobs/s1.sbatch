#!/bin/bash
# S1: one ACHR chain on the 4102-reaction yeast-GEM. Variable (via --export): THIN.
#SBATCH -N 1
#SBATCH -c 12
#SBATCH --mem=16G
set -euo pipefail
source "${STUDY:?set STUDY}/jobs/env.sh"
cd $STUDY
echo "cpus $SLURM_CPUS_PER_TASK, start $(date -Is)"
$PY $STUDY/env_report.py $Y4102
$PY $STUDY/single_chain_autocorr.py --model $Y4102 --thinning $THIN --n-samples 300 --warmup 1000 --seed 0 \
    --time-warmup --out results/ --save-samples $DATA/s1_t${THIN}.npz
echo "end $(date -Is)"
