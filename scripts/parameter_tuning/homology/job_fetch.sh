#!/bin/bash
#SBATCH -J hom-fetch
#SBATCH -n 1 -c 1
#SBATCH -t 02:00:00
# Download all inputs of the homology cut-off study and pack them into one
# zstd tar under $DATA. Usage: sbatch job_fetch.sh
set -euo pipefail
module purge; module load SciPy-bundle/2026.05-gfbf-2026.1
: "${PY:?set PY}" "${DATA:?set DATA}" "${TOOLBOX_ROOT:?set TOOLBOX_ROOT}"
SD=${STUDY:?set STUDY}
export HOMOLOGY_SCRIPT=$TOOLBOX_ROOT/scripts/homology_cutoff_kegg.py
export PYTHONPATH=$TOOLBOX_ROOT/src
W=$TMPDIR/homology-inputs
mkdir -p $W $DATA
export HOMOLOGY_URL_CACHE=$W/uniprot_cache
date -u; hostname
$PY -I $SD/run_cached.py --out $W fetch
$PY -I $SD/run_cached.py prefetch --out $W
$PY -I $SD/fetch_references.py --out $W/refs \
    --kegg118-sha256 520ba8bb09d6ca479ca1ab84ea70bf7c1d7f82d8f6406b717cee293b7c8609ca
for f in $W/proteomes/*.faa; do echo "$f $(grep -c '>' $f)"; done
ls -la $W $W/refs $W/uniprot_cache
tar -C $TMPDIR -cf - homology-inputs | zstd -19 -T1 -q -o $DATA/homology-inputs.tar.zst -f
ls -la $DATA/homology-inputs.tar.zst; sha256sum $DATA/homology-inputs.tar.zst
date -u
