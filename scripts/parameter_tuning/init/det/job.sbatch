#!/bin/bash
#SBATCH --mem=24G
#SBATCH -t 10:00:00
# One or more determinism builds (build.py), one per seed, in sequence.
# Usage: sbatch -A <account> -c N -J name -o log $DET_SCRIPTS/job.sbatch NAME "SEEDS" BUILD ARGS...
source "$DET_SCRIPTS/env.sh"
export FTINIT_DEBUG=1
echo host $(hostname) $(lscpu | grep 'Model name' | sed 's/.*: *//')
NAME=$1; SEEDS=$2; shift 2
for s in $SEEDS; do
  $PY "$DET_SCRIPTS/build.py" --prep "$P/prep-base.pkl" --seed $s --out "$WORK/out/$NAME-s$s.json" "$@" 2>&1 | grep -v "^Set parameter\|^Read LP\|Reading time\|^: \|^Warning for adding"
done
