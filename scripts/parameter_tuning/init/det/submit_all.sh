#!/bin/bash
# Submit the A (full pipeline), B (first-step probe) and C (prove_abs_gap sweep) builds
# of the determinism study after the base preparation job.
# Usage: export WORK TOOLBOX_ROOT HUMANGEM_ROOT DET_SCRIPTS PY [PREP_DIR]; export SBATCH_ACCOUNT=<account>
#        bash submit_all.sh <prep-jobid>
# Then: sbatch edit.sbatch after A-rtp1-1234 has finished; python analyse.py $WORK/out
: "${WORK:?set WORK}" "${DET_SCRIPTS:?set DET_SCRIPTS}" "${SBATCH_ACCOUNT:?set SBATCH_ACCOUNT}"
mkdir -p "$WORK/logs"
DEP="--dependency=afterok:$1"
S() { n=$1; c=$2; seeds=$3; shift 3; sbatch $DEP -c $c -J det-$n -o $WORK/logs/$n.log $DET_SCRIPTS/job.sbatch $n "$seeds" "$@"; }
# A: full pipeline + gap fill + essential genes
for sd in 1234 7; do
S A-base-$sd 2 "$sd" --rt 0 --essential 1 
S A-rt-$sd 2 "$sd" --rt 1 --essential 1
S A-rtp1-$sd 2 "$sd" --rt 1 --pag 1.0 --essential 1
S A-rtp005-$sd 2 "$sd" --rt 1 --pag 0.05 --essential 1
done
S A-base-rep 2 "1234" --rt 0 --essential 1 --repeat 2
S A-rt-rep 2 "1234" --rt 1 --essential 1 --repeat 2
# B: first-stage probe
S B-base-t1 2 "1234 7 1 2 3 4" --rt 0 --nsteps 1 --fill-gaps 0
S B-rt-t1 2 "1234 7 1 2 3 4" --rt 1 --nsteps 1 --fill-gaps 0
S B-base-t4 4 "1234 7 1 2 3 4" --rt 0 --nsteps 1 --fill-gaps 0 --threads 4
S B-rt-t4 4 "1234 7 1 2 3 4" --rt 1 --nsteps 1 --fill-gaps 0 --threads 4
# C: prove_abs_gap sweep (resolve_ties on), both stages, no gap fill
for sd in 1234 7 1 2; do
S C-none-$sd 2 "$sd" --rt 1 --fill-gaps 0
for g in 5.0 2.0 1.0 0.5 0.1 0.05; do S C-$g-$sd 2 "$sd" --rt 1 --pag $g --fill-gaps 0; done
done
