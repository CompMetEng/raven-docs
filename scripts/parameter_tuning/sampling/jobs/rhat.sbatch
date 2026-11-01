#!/bin/bash
# R-hat run with scripts/analyze_sampling_convergence.py of the raven-toolbox checkout.
# Variables (via --export): TAG, MODELVAR (name of the model variable in env.sh), ARGS (options of the script).
#SBATCH -N 1
#SBATCH -c 12
#SBATCH --mem=32G
set -euo pipefail
source "${STUDY:?set STUDY}/jobs/env.sh"
MODEL=${!MODELVAR}
OUT=$DATA/$TAG
mkdir -p $OUT $DATA/logs
cd $STUDY
echo "cpus $SLURM_CPUS_PER_TASK, start $(date -Is)"
$PY $STUDY/env_report.py $MODEL
CMD="$PY $RAVEN_TOOLBOX_DIR/scripts/analyze_sampling_convergence.py --model $MODEL --out $OUT $ARGS"
echo "CMD: $CMD"
$CMD | tee $DATA/logs/$TAG.analysis.txt
WALL=$(grep -o '[0-9.]*s wall' $DATA/logs/$TAG.analysis.txt | head -1 | tr -d 's wall')
PKL=$(ls $OUT/chains_*.pkl)
$PY $STUDY/summarize_chains.py --pickle $PKL --analysis-script $RAVEN_TOOLBOX_DIR/scripts/analyze_sampling_convergence.py \
    --tag $TAG --out results/ --wall-s ${WALL:-nan} > /dev/null
echo "end $(date -Is)"
