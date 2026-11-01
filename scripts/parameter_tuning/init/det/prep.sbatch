#!/bin/bash
#SBATCH -c 2
#SBATCH --mem=24G
#SBATCH -t 04:00:00
# Base template preparation of the determinism study (about 2000 s).
# Usage: sbatch -A <account> -J det-prep -o $WORK/logs/prep.log $DET_SCRIPTS/prep.sbatch
source "$DET_SCRIPTS/env.sh"
echo host $(hostname)
$PY "$DET_SCRIPTS/prep.py" --model "$HGT/model/Human-GEM.yml" --out "$P/prep-base.pkl"
