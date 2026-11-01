#!/bin/bash
#SBATCH -J hom-asettings
#SBATCH -n 1 -c 4
#SBATCH --mem=8G
#SBATCH -t 03:00:00
# Thread test (500 hanpo queries, 1 vs 4 threads), single-thread full directions,
# and aligner E-value 1e-4 vs 1e-5 (run_blast, 4 threads), H. polymorpha vs
# S. cerevisiae (SGD orf_trans_all from homology-inputs.tar.zst).
# Usage: sbatch job_aligner_settings.sh
set -euo pipefail
module purge; module load SciPy-bundle/2026.05-gfbf-2026.1
: "${PY:?set PY}" "${DATA:?set DATA}" "${TOOLBOX_ROOT:?set TOOLBOX_ROOT}"  "${BINARIES_CACHE:?set BINARIES_CACHE}" "${HANPO_FAA:?set HANPO_FAA}"
SD=${STUDY:?set STUDY}
RES=$STUDY/results
export PYTHONPATH=$TOOLBOX_ROOT/src
mkdir -p $RES
zstd -dc $DATA/homology-inputs.tar.zst | tar -C $TMPDIR -xf - homology-inputs/refs/sgd_orf_trans_all.fasta.gz
zcat $TMPDIR/homology-inputs/refs/sgd_orf_trans_all.fasta.gz > $TMPDIR/sce_sgd.fasta
date -u; hostname; nproc; lscpu | grep -E "Model name|^CPU\(s\)"
sha256sum $HANPO_FAA
$PY -I $SD/aligner_settings.py --hanpo $HANPO_FAA \
    --template $TMPDIR/sce_sgd.fasta --bindir $BINARIES_CACHE/blast-2.17.0-linux-x86_64 \
    --work $TMPDIR/as --out $RES/aligner_settings.json --threads 4 --single-thread-full
date -u
