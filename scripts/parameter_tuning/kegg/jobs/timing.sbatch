#!/bin/bash
#SBATCH -t 02:00:00
#SBATCH -n 1
#SBATCH -c 16
#SBATCH --mem=32G
#SBATCH --exclusive
#SBATCH -J kegg-time
set -euo pipefail
module purge; module load SciPy-bundle/2026.05-gfbf-2026.1
: "${PY:?set PY}" "${DATA:?set DATA}"
D=${STUDY:?set STUDY}
export XDG_CACHE_HOME=$TMPDIR/cache PYTHONPATH=${TOOLBOX_ROOT:?set TOOLBOX_ROOT}/src
mkdir -p $XDG_CACHE_HOME/raven_toolbox $TMPDIR/prot
ln -sfn "${BINARIES_CACHE:?set BINARIES_CACHE}" $XDG_CACHE_HOME/raven_toolbox/binaries
hostname; date -u; lscpu | grep -E "Model name|^CPU\(s\)"; nproc
eval "$($PY -c "
from raven_toolbox.data import ensure_kegg_data, ensure_kegg_hmm_library
print(f'ART={ensure_kegg_data()}; EUK={ensure_kegg_hmm_library(\"eukaryotes\")}')")"
tar xzf $DATA/kegg_proteomes_2026-11-01.tar.gz -C $TMPDIR/prot
$PY $D/check_true_reactions.py --artefacts $ART --json $D/results/true_reactions.json
$PY $D/time_hmmsearch.py --proteome $TMPDIR/prot/kegg_rest/sce.faa --library $EUK \
  --threads 16 12 4 1 --json $D/results/timing_sce_eukaryotes.json
date -u
