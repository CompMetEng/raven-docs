# KEGG HMM cut-off calibration

KEGG-based reconstruction from sequence assigns each protein of a new organism to KEGG Orthology (KO) groups by searching the proteome against profile hidden Markov models (HMMs) of the KOs. The study ran this search on the proteomes of four organisms that KEGG annotates, assigned genes to KOs at a range of cut-offs and score ratios, and compared the result with KEGG's own gene→KO annotation of each organism. For each setting it records precision, recall and F1 of the gene→KO pairs, the fraction of the organism's annotated reactions that the prediction recovers and the number of predicted reactions outside the annotation. The results set the defaults `cutoff=1e-30` and `min_score_ratio_g=0.9` of `assign_kos` in place of the RAVEN 2.11.3 values `1e-50` and `0.8`.

## Set-up

### Parameters under test

`assign_kos` (`reconstruction/kegg/query.py`, called by `get_kegg_model_from_sequences`) turns a KO×gene E-value matrix into gene→KO assignments in three steps. RAVEN's `getKEGGModelForOrganism` applies the same steps with the arguments `cutOff`, `minScoreRatioKO` and `minScoreRatioG`.

1. `cutoff` keeps hits with `evalue <= cutoff`.
2. `min_score_ratio_ko` drops, within a KO, genes whose `log(evalue)/log(best_evalue_in_KO) < min_score_ratio_ko`.
3. `min_score_ratio_g` drops, within a gene, KOs whose `log(evalue)/log(best_evalue_for_gene) < min_score_ratio_g`.

### Inputs

- KEGG release 118.
- HMM libraries: `prokaryotes.hmm` (831 MB) and `eukaryotes.hmm` (692 MB), built by the maintainers with `build_ko_hmm`. The sequences of each KO were clustered with CD-HIT at 90 % identity and aligned with MAFFT FFT-NS-2, or with MAFFT PartTree for KOs whose alignment exceeds a memory budget.
- Queries: the full proteome of each organism, extracted from KEGG `genes.pep`, searched with `hmmscan`. `run_hmmsearch` in raven-toolbox fixes `hmmsearch -Z` to the number of profiles; with that setting its E-values match those of `hmmscan` against the same library.
- Each organism's hits were computed once, and every setting was applied to the same hit table. The differences between settings therefore contain no search-to-search variation, and the run-to-run spread of the search itself was not measured.
- Thread count and hardware of the sweep runs were not recorded.

### Reference and scores

The reference is the **KEGG annotation**: the organism's gene→KO pairs in the `organism_gene_ko` table of the KEGG artefacts. The table lists only KOs linked to at least one reaction in `ko_reaction`, and the HMM libraries are built from the same table. The organism's **true reactions** are the reactions linked to its annotated KOs.

A predicted pair is the output of `assign_kos`, with the `organism:` prefix stripped from the gene identifier so that it matches the reference. Each predicted pair is either **matched** (present in the annotation) or **novel** (absent from it).

| Score | Definition |
|---|---|
| gKO prec | gene→KO precision: matched predicted pairs divided by all predicted pairs |
| gKO rec | gene→KO recall: matched predicted pairs divided by all annotated pairs |
| gKO F1 | harmonic mean of gene→KO precision and recall |
| rxn rec | true reactions linked to a predicted KO, divided by all true reactions |
| rxn novel | number of reactions linked to a predicted KO that are not true reactions |

A novel pair counts as an error, although some novel pairs may be correct assignments that KEGG has not made.

### Organisms

| code | organism | library | proteome (seqs) | true gene→KO pairs | true reactions |
|---|---|---|---|---|---|
| `sce` | *Saccharomyces cerevisiae* (budding yeast) | euk | 6021 | 841 | 1217 |
| `cme` | *Cyanidioschyzon merolae* (red alga) | euk | 5010 | 709 | 1157 |
| `eco` | *Escherichia coli* K-12 MG1655 | prok | 4288 | 1071 | 1548 |
| `mge` | *Mycoplasmoides genitalium* G37 (minimal genome) | prok | 476 | 110 | 211 |

`sce` and `eco` are model organisms; `cme` and `mge` are less studied. `mge` has the smallest proteome of the four and the weakest matched hits in the E-value table.

## Results

### E-value distributions

The table gives percentiles of `log10(E-value)` of the best hit per (gene, KO) pair, for all hits that `hmmscan` reported, split into matched and novel pairs. A more negative value is a stronger hit. The 99th percentile is the weakest 1 % of the pairs in a group. The table does not show the strongest novel pairs.

| organism | group | n | p50 | p90 | p95 | p99 |
|---|---|---|---|---|---|---|
| `sce` | matched | 835 | −155 | −75 | −59 | −33 |
| `sce` | novel | 9467 | −8 | −2 | −0 | 1 |
| `cme` | matched | 704 | −133 | −63 | −47 | −25 |
| `cme` | novel | 10170 | −8 | −2 | −2 | 0 |
| `eco` | matched | 1070 | −142 | −69 | −57 | −36 |
| `eco` | novel | 27357 | −7 | −2 | −1 | −0 |
| `mge` | matched | 110 | −100 | −42 | −35 | −15 |
| `mge` | novel | 1904 | −4 | −2 | −1 | −0 |

The median matched pair had an E-value between 1e-100 (`mge`) and 1e-155 (`sce`), and the weakest 1 % of matched pairs lay between 1e-15 and 1e-36. The median novel pair lay between 1e-4 and 1e-8. The weakest 1 % of matched pairs was 11 (`mge`) to 29 (`eco`) orders of magnitude stronger than the median novel pair.

The RAVEN 2.11.3 cut-off of `1e-50` falls inside the matched distribution: between p95 and p99 for `sce` and `eco`, between p90 and p95 for `cme`, and between p50 and p90 for `mge`. It therefore removes 1 to 5 % of the matched pairs of `sce` and `eco`, 5 to 10 % of `cme` and 10 to 50 % of `mge`. The default `1e-30` lies beyond p99 for `sce` and `eco` and between p95 and p99 for `cme` and `mge`, and is 22 to 26 orders of magnitude stronger than the median novel pair.

### Cut-off sweep

`min_score_ratio_ko = 0.3` and `min_score_ratio_g = 0.8` (the RAVEN 2.11.3 values) were fixed while `cutoff` varied.

#### `sce`

| cutoff | gKO prec | gKO rec | gKO F1 | rxn rec | rxn novel |
|---|---|---|---|---|---|
| 1e-10 | 0.57 | 0.98 | 0.72 | 0.99 | 334 |
| 1e-20 | 0.65 | 0.98 | 0.78 | 0.97 | 283 |
| 1e-30 | 0.72 | 0.97 | 0.83 | 0.97 | 216 |
| 1e-50 | 0.78 | 0.95 | 0.86 | 0.96 | 157 |
| 1e-70 | 0.81 | 0.91 | 0.86 | 0.91 | 113 |
| 1e-100 | 0.84 | 0.76 | 0.80 | 0.79 | 68 |

#### `cme`

| cutoff | gKO prec | gKO rec | gKO F1 | rxn rec | rxn novel |
|---|---|---|---|---|---|
| 1e-10 | 0.50 | 0.98 | 0.67 | 1.00 | 541 |
| 1e-20 | 0.57 | 0.98 | 0.72 | 1.00 | 421 |
| 1e-30 | 0.61 | 0.97 | 0.75 | 0.97 | 367 |
| 1e-50 | 0.70 | 0.93 | 0.80 | 0.94 | 307 |
| 1e-70 | 0.75 | 0.85 | 0.80 | 0.87 | 223 |
| 1e-100 | 0.80 | 0.70 | 0.75 | 0.71 | 136 |

#### `eco`

| cutoff | gKO prec | gKO rec | gKO F1 | rxn rec | rxn novel |
|---|---|---|---|---|---|
| 1e-10 | 0.53 | 0.99 | 0.69 | 0.99 | 382 |
| 1e-20 | 0.57 | 0.99 | 0.73 | 0.99 | 300 |
| 1e-30 | 0.60 | 0.98 | 0.75 | 0.99 | 268 |
| 1e-50 | 0.67 | 0.95 | 0.78 | 0.98 | 198 |
| 1e-70 | 0.73 | 0.88 | 0.80 | 0.93 | 157 |
| 1e-100 | 0.82 | 0.74 | 0.77 | 0.80 | 96 |

#### `mge`

| cutoff | gKO prec | gKO rec | gKO F1 | rxn rec | rxn novel |
|---|---|---|---|---|---|
| 1e-10 | 0.52 | 0.98 | 0.68 | 0.99 | 75 |
| 1e-20 | 0.62 | 0.96 | 0.75 | 0.98 | 51 |
| 1e-30 | 0.65 | 0.95 | 0.77 | 0.98 | 39 |
| 1e-50 | 0.77 | 0.84 | 0.80 | 0.87 | 29 |
| 1e-70 | 0.85 | 0.73 | 0.78 | 0.73 | 27 |
| 1e-100 | 0.87 | 0.50 | 0.64 | 0.47 | 21 |

Gene→KO recall stayed between 0.95 and 0.99 from 1e-10 to 1e-30 in all four organisms and fell at stricter cut-offs. The fall was largest for `mge`, whose reaction recall dropped from 0.98 at 1e-30 to 0.87 at 1e-50 and 0.47 at 1e-100. Precision rose with every stricter cut-off in all four organisms, from 0.72 to 0.78 for `sce` between 1e-30 and 1e-50. With the ratios fixed at 0.3 and 0.8, F1 was highest at 1e-50 or 1e-70 in every organism. Novel predictions remained at the strictest cut-off: at 1e-100 the three larger proteomes had 68 to 136 novel reactions and a gene→KO precision of 0.80 to 0.84 (0.87 for `mge`). The study does not show whether these are wrong assignments, paralogs or genes that KEGG has not annotated.

### Score-ratio sweep

`cutoff` was fixed at `1e-50`. The script scores every combination of `min_score_ratio_ko` (0.0, 0.3, 0.5) and `min_score_ratio_g` (0.5, 0.8, 0.95); the table holds the five combinations per organism that were reported.

| organism | ko ratio | g ratio | gKO prec | gKO rec | gKO F1 |
|---|---|---|---|---|---|
| `sce` | 0.0 | 0.50 | 0.61 | 0.96 | 0.74 |
| `sce` | 0.0 | 0.80 | 0.77 | 0.95 | 0.85 |
| `sce` | 0.0 | 0.95 | 0.84 | 0.93 | 0.88 |
| `sce` | 0.3 | 0.80 | 0.78 | 0.95 | 0.86 |
| `sce` | 0.5 | 0.80 | 0.80 | 0.95 | 0.86 |
| `cme` | 0.0 | 0.50 | 0.53 | 0.94 | 0.68 |
| `cme` | 0.0 | 0.80 | 0.69 | 0.93 | 0.79 |
| `cme` | 0.0 | 0.95 | 0.78 | 0.92 | 0.84 |
| `cme` | 0.3 | 0.80 | 0.70 | 0.93 | 0.80 |
| `cme` | 0.5 | 0.80 | 0.70 | 0.93 | 0.80 |
| `eco` | 0.0 | 0.50 | 0.39 | 0.96 | 0.56 |
| `eco` | 0.0 | 0.80 | 0.66 | 0.95 | 0.78 |
| `eco` | 0.0 | 0.95 | 0.76 | 0.94 | 0.84 |
| `eco` | 0.3 | 0.80 | 0.67 | 0.95 | 0.78 |
| `eco` | 0.5 | 0.80 | 0.69 | 0.95 | 0.80 |
| `mge` | 0.0 | 0.50 | 0.62 | 0.85 | 0.72 |
| `mge` | 0.0 | 0.80 | 0.77 | 0.84 | 0.80 |
| `mge` | 0.0 | 0.95 | 0.82 | 0.81 | 0.81 |
| `mge` | 0.3 | 0.80 | 0.77 | 0.84 | 0.80 |
| `mge` | 0.5 | 0.80 | 0.78 | 0.84 | 0.81 |

At `min_score_ratio_g = 0.80`, raising `min_score_ratio_ko` from 0.0 to 0.5 left recall unchanged and raised precision by 0.03 for `sce` and `eco` and by 0.01 for `cme` and `mge`.

Raising `min_score_ratio_g` from 0.80 to 0.95 (at `min_score_ratio_ko = 0.0`) raised precision by 0.07 (`sce`), 0.09 (`cme`), 0.10 (`eco`) and 0.05 (`mge`), and lowered recall by 0.01 to 0.03. At 0.50, precision was the lowest of the three values in every organism. The value 0.9 lies between the tested values 0.8 and 0.95 and was not swept.

### Defaults compared with RAVEN 2.11.3

The table compares the RAVEN 2.11.3 settings `(1e-50, 0.3, 0.8)` with the defaults `(1e-30, 0.3, 0.9)`, given as `(cutoff, min_score_ratio_ko, min_score_ratio_g)`. For the RAVEN 2.11.3 settings the F1 column gives the measured value from the cut-off sweep; for the defaults, which were not part of either sweep, it is computed from the rounded precision and recall in the same row.

| organism | gKO prec | gKO rec | gKO F1 (measured → computed) | rxn rec | rxn novel |
|---|---|---|---|---|---|
| `sce` | 0.78 → 0.76 | 0.95 → 0.96 | 0.86 → 0.85 | 0.96 → 0.96 | 157 → 137 |
| `cme` | 0.70 → 0.67 | 0.93 → 0.96 | 0.80 → 0.79 | 0.94 → 0.97 | 307 → 305 |
| `eco` | 0.67 → 0.67 | 0.95 → 0.97 | 0.78 → 0.79 | 0.98 → 0.99 | 198 → 173 |
| `mge` | 0.77 → 0.69 | 0.84 → 0.94 | 0.80 → 0.80 | 0.87 → 0.97 | 29 → 35 |

With the defaults, gene→KO recall rose by 0.10 for `mge` and by 0.01 to 0.03 for the other three organisms. Gene→KO precision fell by 0.02 (`sce`), 0.03 (`cme`) and 0.08 (`mge`), and stayed at 0.67 for `eco`. F1 changed by at most 0.01. The number of novel reactions fell for `sce`, `cme` and `eco` and rose from 29 to 35 for `mge`.

### Whole-model comparison of the two KEGG paths

*S. cerevisiae* was reconstructed in full by two paths, both with the RAVEN 2.11.3 settings `(1e-50, 0.3, 0.8)`. The annotation path takes the organism's genes and KOs from the `organism_gene_ko` table; the HMM path assigns KOs to the proteome with the HMM search.

| Count | annotation path | HMM path |
|---|---|---|
| reactions | 1355 | 1461 |
| metabolites | 1501 | 1567 |
| genes | 835 | 896 |

The HMM path contained 96.3 % of the reactions of the annotation path (1305 of 1355, Jaccard index 0.86) and 96.6 % of its genes (807 of 835, Jaccard index 0.87). `hmmscan` took ≈ 0.1 s per query against either library on 12 threads (yeast: 6021 queries in 633 s, about 10.5 minutes).

## Meaning of the results

From 1e-10 to 1e-30 a stricter cut-off raised precision while gene→KO recall fell by at most 0.03 (from 0.98 or 0.99 to between 0.95 and 0.98). Beyond 1e-30 the cut-off traded recall for precision: it removed matched pairs together with novel pairs, and novel pairs remained at every cut-off tested. Across the whole sweep from 1e-10 to 1e-100 precision rose by 0.27 (`sce`, 0.57 to 0.84) to 0.35 (`mge`). The RAVEN 2.11.3 value `1e-50` removes 10 to 50 % of the matched pairs of `mge`, the organism with the weakest matched hits, and 1 to 10 % in the other three.

At `cutoff = 1e-50`, raising `min_score_ratio_g` from 0.80 to 0.95 raised precision by 0.05 to 0.10 for a recall loss of 0.01 to 0.03, and raising it from 0.50 to 0.80 raised precision by 0.15 to 0.27 (`eco`, 0.39 to 0.66). `min_score_ratio_ko` changed precision by 0.01 to 0.03 and recall not at all. The defaults move part of the filtering from the cut-off to `min_score_ratio_g`. On the four organisms the move gained recall, most for `mge`, at the cost of precision in three of them, and left F1 within 0.01 of the RAVEN 2.11.3 settings.

## Chosen defaults

| parameter | RAVEN 2.11.3 | default (raven-toolbox and RAVEN 3) | basis |
|---|---|---|---|
| `cutoff` (`cutOff`) | 1e-50 | 1e-30 | beyond matched p99 for `sce` and `eco`, between p95 and p99 for `cme` and `mge`; with the new `min_score_ratio_g`, `mge` recall 0.84 → 0.94 |
| `min_score_ratio_g` (`minScoreRatioG`) | 0.8 | 0.9 | from 0.80 to 0.95 it raised precision by 0.05 to 0.10 for a recall loss of 0.01 to 0.03; partly offsets the precision lost to the looser cut-off |
| `min_score_ratio_ko` (`minScoreRatioKO`) | 0.3 | 0.3 | changed precision by 0.01 to 0.03 and recall not at all; kept at the RAVEN value |

The defaults favour recall: the changed settings raised recall in every organism and lowered precision in three of the four.

## Settings without a sweep

Three settings next to the cut-offs were not measured in the study. The reasons given for their values are not tested.

`threads` in `run_hmmsearch` and `build_ko_hmm` defaults to every CPU the process may run on. The value rests on the assumption, not tested here, that HMMER's search gives the same hits at any thread count and that E-values differ at most in the last floating-point places. Single-threaded search against the full KO library (more than 26,000 HMMs) is given as 30 to 60 minutes per proteome, against roughly five minutes multi-threaded; no run with a recorded thread count and hardware supports either figure. The one timed run, `sce` against `eukaryotes.hmm` on 12 threads, took 633 s (about 10.5 minutes).

`seq_identity` in `build_ko_hmm` is `0.9`: the identity at which CD-HIT collapses near-duplicate sequences within a KO before the HMM is built; the clustering keeps a KO with many near-identical entries from giving an overfitted profile. It is CD-HIT's recommended value for proteins and the default of `seqIdentity` in RAVEN 2.11.3. `seq_identity=-1` skips the clustering. RAVEN 3's `getKEGGModelForOrganism` uses prebuilt HMM libraries and has no clustering step.

The model-assembly flags decide which reactions a draft keeps, and have the same defaults as in RAVEN:

| Flag | Default | What it admits | Reason given for the default |
|---|---|---|---|
| `keep_spontaneous` | `True` | Reactions marked spontaneous in KEGG, which carry no gene rule. | Excluding them breaks pathways that need them. |
| `keep_undefined_stoich` | `True` | Reactions with variable stoichiometry (`n` subunits), which cannot be mass-balanced as written. | Dropping them removes real chemistry from the draft. |
| `keep_incomplete` | `True` | Reactions whose enzyme set is only partly known. | |
| `keep_general` | `False` | Overview-map reactions that lump many specific steps into one. | Admitting them counts the same conversion twice. |

## Limits

- All four organisms are in the set of sequences from which the libraries were built, so their own sequences contribute to their KO profiles. Recall on these organisms is therefore an upper bound for an organism outside KEGG (inference; a genome absent from KEGG was not tested). The comparison between settings is relative and gives no absolute accuracy.
- A novel pair that is a correct assignment KEGG has not made counts as an error, so the precision figures are a lower bound. The study does not measure how many novel pairs are correct.
- Four organisms, one KEGG release (118) and one hit table per organism. Each search ran once, so its run-to-run spread, and its dependence on the thread count, were not measured; the scoring of a hit table by `assign_kos` involves no random step.
- The score-ratio sweep used `cutoff = 1e-50` only, and `min_score_ratio_g = 0.9` was not part of either sweep.

## Reproduction

The sweeps are produced by [`scripts/analyze_hmm_cutoffs.py`](https://github.com/CompMetEng/raven-toolbox/blob/develop/scripts/analyze_hmm_cutoffs.py), one organism per call, with the KEGG artefacts, the organism's proteome and the HMM library (or a saved `hmmscan --tblout` file) as input. It prints the E-value percentiles, the cut-off sweep and the full score-ratio grid. The comparison of the defaults with RAVEN 2.11.3 and the whole-model comparison are not produced by this script.

With raven-toolbox at commit `94f3940` the script does not run: it imports `run_hmmscan` and `parse_hmmscan_tblout` from `reconstruction/kegg/query.py`, which provides `run_hmmsearch` and `parse_hmmsearch_tblout` instead. Its cut-off sweep calls `assign_kos` with the default ratios, which are 0.3 and 0.9 at that commit, so it no longer reproduces the sweep at 0.3 and 0.8.
