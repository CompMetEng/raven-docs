#!/bin/bash
#SBATCH -c 2
#SBATCH --mem=24G
#SBATCH -t 12:00:00
# Template-edit arm: select 30 unused reactions, prepare the edited template, build
# E-base, E-rt and E-rtp1 at seed 1234. Needs $WORK/out/A-rtp1-1234-s1234.json.
# Usage: sbatch -A <account> -J det-edit -o $WORK/logs/edit.log $DET_SCRIPTS/edit.sbatch
source "$DET_SCRIPTS/env.sh"
export FTINIT_DEBUG=1
$PY "$DET_SCRIPTS/select_edit.py" "$P/prep-base.pkl" "$WORK/out/A-rtp1-1234-s1234.json" "$WORK/out/edit-list.json"
$PY "$DET_SCRIPTS/prep.py" --model "$HGT/model/Human-GEM.yml" --remove "$WORK/out/edit-list.json" --out "$P/prep-edit.pkl" 2>&1 | grep -v "^Read LP\|Reading time\|^: "
for cfg in "E-base --rt 0" "E-rt --rt 1" "E-rtp1 --rt 1 --pag 1.0"; do
  set -- $cfg; n=$1; shift
  $PY "$DET_SCRIPTS/build.py" --prep "$P/prep-edit.pkl" --seed 1234 --out "$WORK/out/$n-s1234.json" --essential 1 "$@" 2>&1 | grep -v "^Set parameter\|^Read LP\|Reading time\|^: \|^Warning for adding"
done
