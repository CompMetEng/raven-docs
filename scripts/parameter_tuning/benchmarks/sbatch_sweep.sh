#!/bin/bash
#SBATCH -c 2
#SBATCH --mem=8G
#SBATCH -t 01:00:00
#SBATCH -J bench_sweep
# Submit with STUDY set to this folder (sbatch --export=ALL -A <account>).
# Needs RAVEN_TOOLBOX and BENCH_PY in the environment.
S=${STUDY:?set STUDY}
source $S/env_py.sh
$BENCH_PY $S/fseof_sweep.py --outdir $STUDY/results --repeats 3
$BENCH_PY $S/gapfill_threshold.py --out $STUDY/results/gapfill_threshold.json
