#!/bin/bash
#SBATCH -t 05:00:00
#SBATCH -n 1
#SBATCH -c 16
#SBATCH --mem=48G
#SBATCH -J kegg-hmm
set -euo pipefail
module purge; module load SciPy-bundle/2026.05-gfbf-2026.1
: "${PY:?set PY}" "${DATA:?set DATA}"
D=${STUDY:?set STUDY}
TB=${TOOLBOX_ROOT:?set TOOLBOX_ROOT}
export XDG_CACHE_HOME=$TMPDIR/cache
export PYTHONPATH=$TB/src
THREADS=${SLURM_CPUS_PER_TASK}
mkdir -p $XDG_CACHE_HOME/raven_toolbox $D/results
# hmmsearch 3.4.0 already fetched by the toolbox; expose its binaries cache in the job cache
ln -sfn "${BINARIES_CACHE:?set BINARIES_CACHE}" $XDG_CACHE_HOME/raven_toolbox/binaries
hostname; date -u; lscpu | grep -E "Model name|^CPU\(s\)"; echo "threads=$THREADS"
git -C $TB rev-parse HEAD
$PY -c "import sys,cobra,optlang,pandas,numpy; print(sys.version); print('cobra',cobra.__version__,'optlang',optlang.__version__,'pandas',pandas.__version__,'numpy',numpy.__version__)"
which hmmsearch || echo "hmmsearch not on PATH"
$PY - <<'PY' > $TMPDIR/paths.sh
import os, subprocess
from raven_toolbox.binaries import resolve_binary
from raven_toolbox.data import ensure_kegg_data, ensure_kegg_hmm_library
from raven_toolbox.reconstruction.kegg.query import _count_profiles
exe = resolve_binary("hmmsearch")
d = ensure_kegg_data()
libs = {dom: ensure_kegg_hmm_library(dom) for dom in ("eukaryotes", "prokaryotes")}
import sys
print("hmmsearch:", exe, subprocess.run([exe, "-h"], capture_output=True, text=True).stdout.splitlines()[1], file=sys.stderr)
for dom, p in libs.items():
    print(dom, p, os.path.getsize(p), "bytes", _count_profiles(p), "profiles", file=sys.stderr)
for f in sorted(os.listdir(d)):
    print("artefact", f, os.path.getsize(os.path.join(d, f)), file=sys.stderr)
print(f"ART={d}\nEUK={libs['eukaryotes']}\nPROK={libs['prokaryotes']}")
PY
cat $TMPDIR/paths.sh; source $TMPDIR/paths.sh
mkdir -p $TMPDIR/prot $TMPDIR/tbl
tar xzf $DATA/kegg_proteomes_2026-11-01.tar.gz -C $TMPDIR/prot
for org in sce cme eco mge; do
  case $org in sce|cme) LIB=$EUK;; *) LIB=$PROK;; esac
  echo "### $org $(date -u)"
  $PY $D/analyze_hmm_cutoffs.py --artefacts $ART --org $org \
    --proteome $TMPDIR/prot/kegg_rest/$org.faa --library $LIB --threads $THREADS \
    --save-tblout $TMPDIR/tbl/$org.tbl --json $D/results/sweep_$org.json
done
tar czf $DATA/kegg_hmmsearch_tblout_2026-11-01.tar.gz -C $TMPDIR/tbl .
for org in mge sce; do
  case $org in sce) LIB=$EUK; DOM=eukaryotes;; *) LIB=$PROK; DOM=prokaryotes;; esac
  echo "### whole model $org $(date -u)"
  $PY $D/compare_kegg_paths.py --org $org --proteome $TMPDIR/prot/kegg_rest/$org.faa \
    --artefacts $ART --library $LIB --domain $DOM --threads $THREADS \
    --settings 1e-50,0.3,0.8 1e-30,0.3,0.9 --json $D/results/wholemodel_$org.json
done
date -u
