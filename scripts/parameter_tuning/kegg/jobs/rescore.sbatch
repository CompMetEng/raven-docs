#!/bin/bash
#SBATCH -t 00:40:00
#SBATCH -n 1
#SBATCH -c 2
#SBATCH --mem=16G
#SBATCH -J kegg-rescore
set -euo pipefail
module purge; module load SciPy-bundle/2026.05-gfbf-2026.1
: "${PY:?set PY}" "${DATA:?set DATA}"
D=${STUDY:?set STUDY}
export XDG_CACHE_HOME=$TMPDIR/cache PYTHONPATH=${TOOLBOX_ROOT:?set TOOLBOX_ROOT}/src
mkdir -p $TMPDIR/prot $TMPDIR/tbl
ART=$($PY -c "from raven_toolbox.data import ensure_kegg_data; print(ensure_kegg_data())")
tar xzf $DATA/kegg_proteomes_2026-11-01.tar.gz -C $TMPDIR/prot
tar xzf $DATA/kegg_hmmsearch_tblout_2026-11-01.tar.gz -C $TMPDIR/tbl
for org in sce cme eco mge; do
  # same hit tables and all ko_reaction links: must equal the first run
  $PY $D/analyze_hmm_cutoffs.py --artefacts $ART --org $org --proteome $TMPDIR/prot/kegg_rest/$org.faa \
    --tblout $TMPDIR/tbl/$org.tbl --json $TMPDIR/check_$org.json > /dev/null
  $PY - $TMPDIR/check_$org.json $D/results/sweep_$org.json <<'PY'
import json, sys
a, b = (json.load(open(p)) for p in sys.argv[1:])
for d in (a, b):
    d.pop("search", None); d.pop("restrict_to_reference", None)
print(sys.argv[2], "rescored from saved tblout identical:", a == b)
PY
  $PY $D/analyze_hmm_cutoffs.py --artefacts $ART --org $org --proteome $TMPDIR/prot/kegg_rest/$org.faa \
    --tblout $TMPDIR/tbl/$org.tbl --restrict-to-reference --json $D/results/sweep_${org}_refrxn.json
done
