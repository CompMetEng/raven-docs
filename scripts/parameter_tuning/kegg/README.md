# KEGG HMM cut-off calibration

Scripts for the KEGG HMM cut-off page of the parameter-tuning documentation. The gene-to-KO assignment of the `kegg118` HMM libraries is scored against the gene-to-KO and KO-to-reaction tables of the `kegg118` release for *S. cerevisiae* (`sce`), *C. merolae* (`cme`), *E. coli* (`eco`) and *M. genitalium* (`mge`), over E-value, `min_score_ratio_ko` and `min_score_ratio_g`. The annotation path and the HMM path are compared for whole models.

## Inputs and environment

The reference tables and HMM libraries are the `kegg118` release of [CompMetEng/toolbox-assets](https://github.com/CompMetEng/toolbox-assets/releases/tag/kegg118). `ensure_kegg_data()` and `ensure_kegg_hmm_library("eukaryotes" | "prokaryotes")` fetch them and check the SHA-256. The libraries hold 2698 (eukaryotes, used for `sce` and `cme`) and 4205 (prokaryotes, used for `eco` and `mge`) profiles.

The fetch step downloads the proteomes from the KEGG REST API (`list/<org>` and `get/<ids>/aaseq`) and UniProt, and packs them into `kegg_proteomes_<date>.tar.gz`. It yields 6021 (`sce`), 5010 (`cme`), 4288 (`eco`) and 476 (`mge`) KEGG sequences. The UniProt proteomes are downloaded and not searched. The search step packs the `hmmsearch --tblout` files into `kegg_hmmsearch_tblout_<date>.tar.gz`, which the rescore step reads.

| Variable | Meaning |
| --- | --- |
| `STUDY` | this folder |
| `TOOLBOX_ROOT` | raven-toolbox checkout (`94f3940`); its `src` goes on `PYTHONPATH` |
| `PY` | Python interpreter with cobra, optlang, pandas and numpy |
| `DATA` | folder of the two archives |
| `BINARIES_CACHE` | `raven_toolbox/binaries` cache with the `hmmsearch` 3.4 bundle |

The fetch step needs 2 cores. The search step needs 16 cores and 48 GB, the rescore step 2 cores and 16 GB. The timing step needs a node of 16 cores that runs nothing else, 32 GB.

## Commands

```bash
export STUDY=... TOOLBOX_ROOT=... DATA=... BINARIES_CACHE=...
export PYTHONPATH=$TOOLBOX_ROOT/src XDG_CACHE_HOME=$TMPDIR/cache
mkdir -p $XDG_CACHE_HOME/raven_toolbox $TMPDIR/prot $TMPDIR/tbl $STUDY/results
ln -sfn $BINARIES_CACHE $XDG_CACHE_HOME/raven_toolbox/binaries
DATE=2026-11-01
```

Fetch the proteomes:

```bash
python $STUDY/fetch_proteomes.py --work $TMPDIR/prot --archive $DATA/kegg_proteomes_$DATE.tar.gz
cp $TMPDIR/prot/counts.json $STUDY/results/proteome_counts.json
```

Resolve the reference tables and libraries, unpack the proteomes and run the sweeps. For each organism the loop calls `analyze_hmm_cutoffs.py`, and `compare_kegg_paths.py` follows for `sce` and `mge`.

```bash
THREADS=16
ART=$(python -c "from raven_toolbox.data import ensure_kegg_data; print(ensure_kegg_data())")
EUK=$(python -c "from raven_toolbox.data import ensure_kegg_hmm_library as f; print(f('eukaryotes'))")
PROK=$(python -c "from raven_toolbox.data import ensure_kegg_hmm_library as f; print(f('prokaryotes'))")
tar xzf $DATA/kegg_proteomes_$DATE.tar.gz -C $TMPDIR/prot
for org in sce cme eco mge; do
  case $org in sce|cme) LIB=$EUK;; *) LIB=$PROK;; esac
  python $STUDY/analyze_hmm_cutoffs.py --artefacts $ART --org $org \
      --proteome $TMPDIR/prot/kegg_rest/$org.faa --library $LIB --threads $THREADS \
      --save-tblout $TMPDIR/tbl/$org.tbl --json $STUDY/results/sweep_$org.json
done
tar czf $DATA/kegg_hmmsearch_tblout_$DATE.tar.gz -C $TMPDIR/tbl .
for org in mge sce; do
  case $org in sce) LIB=$EUK; DOM=eukaryotes;; *) LIB=$PROK; DOM=prokaryotes;; esac
  python $STUDY/compare_kegg_paths.py --org $org --proteome $TMPDIR/prot/kegg_rest/$org.faa \
      --artefacts $ART --library $LIB --domain $DOM --threads $THREADS \
      --settings 1e-50,0.3,0.8 1e-30,0.3,0.9 --json $STUDY/results/wholemodel_$org.json
done
```

The rescore step scores the saved hit tables again with `--tblout`, which gives identical sweeps, and with `--restrict-to-reference`:

```bash
tar xzf $DATA/kegg_hmmsearch_tblout_$DATE.tar.gz -C $TMPDIR/tbl
for org in sce cme eco mge; do
  python $STUDY/analyze_hmm_cutoffs.py --artefacts $ART --org $org --proteome $TMPDIR/prot/kegg_rest/$org.faa \
      --tblout $TMPDIR/tbl/$org.tbl --json $TMPDIR/check_$org.json > /dev/null
  python $STUDY/analyze_hmm_cutoffs.py --artefacts $ART --org $org --proteome $TMPDIR/prot/kegg_rest/$org.faa \
      --tblout $TMPDIR/tbl/$org.tbl --restrict-to-reference --json $STUDY/results/sweep_${org}_refrxn.json
done
```

`$TMPDIR/check_<org>.json` and `results/sweep_<org>.json` hold the same sweep apart from the `search` and `restrict_to_reference` keys.

The timing step runs `check_true_reactions.py` and `time_hmmsearch.py --threads 16 12 4 1`:

```bash
python $STUDY/check_true_reactions.py --artefacts $ART --json $STUDY/results/true_reactions.json
python $STUDY/time_hmmsearch.py --proteome $TMPDIR/prot/kegg_rest/sce.faa --library $EUK \
    --threads 16 12 4 1 --json $STUDY/results/timing_sce_eukaryotes.json
```

## Outputs

| File | Content |
| --- | --- |
| `analyze_hmm_cutoffs.py` | E-value percentiles of matched and novel hits, cut-off sweep at (0.3, 0.8) and (0.3, 0.9), score-ratio sweep and defaults row, as printed tables and JSON. By default every `ko_reaction` link counts as a true reaction; `--restrict-to-reference` counts links to reactions of the reference model. |
| `results/sweep_<org>.json`, `results/sweep_<org>_refrxn.json` | Sweep output per organism, without and with `--restrict-to-reference`. |
| `compare_kegg_paths.py` to `results/wholemodel_<org>.json` | Reactions, metabolites and genes of the two paths at each setting, and their overlap. |
| `check_true_reactions.py` to `results/true_reactions.json` | True reactions per organism under several definitions. |
| `time_hmmsearch.py` to `results/timing_sce_eukaryotes.json` | `hmmsearch` wall time at the given thread counts and a comparison of the parsed hit tables. |
