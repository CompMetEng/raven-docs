#!/bin/bash
#SBATCH -t 02:00:00
#SBATCH -n 1
#SBATCH -c 2
#SBATCH -J kegg-fetch
set -euo pipefail
module purge; module load SciPy-bundle/2026.05-gfbf-2026.1
: "${PY:?set PY}" "${DATA:?set DATA}"
D=${STUDY:?set STUDY}
export XDG_CACHE_HOME=$TMPDIR/cache
export PYTHONPATH=${TOOLBOX_ROOT:?set TOOLBOX_ROOT}/src
hostname; date -u
# peek at the core tables
$PY -c "
from raven_toolbox.data import ensure_kegg_data
from raven_toolbox.reconstruction.kegg.parse import read_kegg_table, _resolve_artefact
d=ensure_kegg_data(); import os; print(d, sorted(os.listdir(d)))
o=read_kegg_table(_resolve_artefact(d,'organism_gene_ko.tsv.gz'))
for org in ['sce','cme','eco','mge']:
    r=o[o.organism.str.lower()==org]; print(org, len(r), r.gene.nunique(), r.head(3).values.tolist())
"
$PY $D/fetch_proteomes.py --work $TMPDIR/prot \
  --archive $DATA/kegg_proteomes_2026-11-01.tar.gz
cp $TMPDIR/prot/counts.json $D/results/proteome_counts.json
date -u
