#!/bin/bash
# Post-hoc checks on stored chains and S7 samples.
#SBATCH -N 1
#SBATCH -c 1
#SBATCH --mem=8G
set -euo pipefail
source "${STUDY:?set STUDY}/jobs/env.sh"
cd $STUDY
$PY $STUDY/posthoc_checks.py --achr-pickle $(ls $DATA/S2_ecore_achr_m4_n300_t100/chains_*.pkl) \
    --chrr-pickle $(ls $DATA/S5_ecore_chrr_m4_n300_t100/chains_*.pkl) --s7-npz $DATA/s7_false.npz \
    --model $Y4102 --out results/posthoc.json
