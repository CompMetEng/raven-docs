#!/bin/bash
#SBATCH -J hom-align
#SBATCH -n 1 -c 4
#SBATCH --mem=16G
#SBATCH -t 04:00:00
# Align the four targets against S. cerevisiae with BLAST and DIAMOND (4 threads,
# the driver's default), score every variant, compute the BLAST/DIAMOND agreement
# and the tables. Inputs: homology-inputs.tar.zst (job_fetch.sh).
# Usage: sbatch job_align_score.sh
set -euo pipefail
module purge; module load SciPy-bundle/2026.05-gfbf-2026.1
: "${PY:?set PY}" "${DATA:?set DATA}" "${TOOLBOX_ROOT:?set TOOLBOX_ROOT}"  "${BINARIES_CACHE:?set BINARIES_CACHE}"
SD=${STUDY:?set STUDY}
RES=$STUDY/results
TB=$TOOLBOX_ROOT
export HOMOLOGY_SCRIPT=$TB/scripts/homology_cutoff_kegg.py
export PYTHONPATH=$TB/src
mkdir -p $RES
zstd -dc $DATA/homology-inputs.tar.zst | tar -C $TMPDIR -xf -
W=$TMPDIR/homology-inputs
export HOMOLOGY_URL_CACHE=$W/uniprot_cache HOMOLOGY_OFFLINE=1
REFS=$W/refs
date -u; hostname; nproc; lscpu | grep -E "Model name|^CPU\(s\)|Thread|Socket"
echo "raven-toolbox $(git -C $TB rev-parse HEAD)"
$PY -c "import raven_toolbox, pandas, sys; print('raven_toolbox', getattr(raven_toolbox, '__version__', '?'), 'pandas', pandas.__version__, 'python', sys.version.split()[0])"
BIN=$BINARIES_CACHE
$BIN/blast-2.17.0-linux-x86_64/blastp -version; $BIN/diamond-2.1.17-linux-x86_64/diamond version
$PY -c "from raven_toolbox.binaries import resolve_binary as r; print(r('blastp'), r('diamond'))"

$PY -I $SD/run_cached.py --out $W align                     2>&1 | tee $RES/align_blast.txt
$PY -I $SD/run_cached.py --out $W align --aligner diamond   2>&1 | tee $RES/align_diamond.txt

score() {  # name, args...
  local name=$1; shift
  echo "== score $name: $*"
  $PY -I $SD/run_cached.py --out $W score "$@" 2>&1 | tee $RES/score_$name.txt
  cp $W/hitlevel_results.json $RES/$name.json
}
K118=$REFS/kegg118_organism_gene_ko_5org.tsv.gz
score kegg118_blast_b0.5   --beta 0.5 --gene-ko $K118
score kegg118_diamond_b0.5 --beta 0.5 --gene-ko $K118 --aligner diamond
score kegg118_blast_b1     --beta 1   --gene-ko $K118
score kegg118_diamond_b1   --beta 1   --gene-ko $K118 --aligner diamond
score oma_blast_b0.5       --beta 0.5 --gene-ko $K118 --reference oma
score oma_diamond_b0.5     --beta 0.5 --gene-ko $K118 --reference oma --aligner diamond
score keggrest_rxn_blast_b0.5   --beta 0.5 --gene-ko $REFS/keggrest_organism_gene_ko_rxn.tsv.gz
score keggrest_rxn_diamond_b0.5 --beta 0.5 --gene-ko $REFS/keggrest_organism_gene_ko_rxn.tsv.gz --aligner diamond
score keggrest_all_blast_b0.5   --beta 0.5 --gene-ko $REFS/keggrest_organism_gene_ko_all.tsv.gz

$PY -I $SD/agreement.py --work $W --gene-ko $K118 --out $RES/agreement.tsv
$PY -I $SD/make_tables.py --res $RES > $RES/tables.md
tar -C $W -cf - $(cd $W && ls hits_*.csv) | zstd -19 -T4 -q -f -o $DATA/homology-hits.tar.zst
ls -la $DATA/homology-hits.tar.zst
date -u
