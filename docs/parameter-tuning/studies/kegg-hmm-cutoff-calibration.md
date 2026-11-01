# KEGG HMM cut-off calibration

KEGG-based reconstruction from sequence assigns each protein of a new organism to KEGG Orthology (KO) groups by searching the proteome against profile hidden Markov models (HMMs) of the KOs. The study ran this search on the proteomes of four organisms that KEGG annotates, assigned genes to KOs at a range of cut-offs and score ratios, and compared the result with KEGG's own gene→KO annotation of each organism. For each setting it records precision, recall and F1 of the gene→KO pairs, the fraction of the organism's annotated reactions that the prediction recovers and the number of predicted reactions outside the annotation. The results set the defaults `cutoff=1e-30` and `min_score_ratio_g=0.9` of `assign_kos` in place of the RAVEN 2.11.3 values `1e-50` and `0.8`.

## Set-up

### Parameters under test

`assign_kos` (`reconstruction/kegg/query.py`, called by `get_kegg_model_from_sequences`) turns a KO×gene E-value matrix into gene→KO assignments in three steps. RAVEN's `getKEGGModelForOrganism` applies the same steps with the arguments `cutOff`, `minScoreRatioKO` and `minScoreRatioG`.

1. `cutoff` keeps hits with `evalue <= cutoff`.
2. `min_score_ratio_ko` drops, within a KO, genes whose `log(evalue)/log(best_evalue_in_KO) < min_score_ratio_ko`.
3. `min_score_ratio_g` drops, within a gene, KOs whose `log(evalue)/log(best_evalue_for_gene) < min_score_ratio_g`.

### Inputs

The percentile, cut-off, score-ratio and defaults tables come from one run on 2026-11-01 (raven-toolbox commit `94f3940`, HMMER 3.4, 16 threads on an AMD EPYC 9354 node) of the sources below. The timing and the true-reaction counts come from separate jobs.

- Tables: the kegg118 artefacts (`organism_gene_ko`, `ko_reaction` and the reference model) published as the `kegg118` release of toolbox-assets.
- HMM libraries: the published kegg118 libraries `kegg118_eukaryotes.hmm` (2698 profiles, 696,233,564 bytes) and `kegg118_prokaryotes.hmm` (4205 profiles, 838,505,885 bytes), built by the maintainers with `build_ko_hmm`. The sequences of each KO were clustered with CD-HIT at 90 % identity and aligned with MAFFT FFT-NS-2, or with MAFFT PartTree for KOs whose alignment exceeds a memory budget.
- Queries: the CDS genes of each organism from the KEGG REST lists, downloaded on 2026-11-01 (KEGG genes updated 2026-10-31, which is not KEGG release 118): 6021, 5010, 4288 and 476 sequences, of 6449, 5094, 4639 and 525 list entries. The sequences were not compared with those of KEGG release 118. The search is `hmmsearch`; `run_hmmsearch` in raven-toolbox fixes `-Z` to the number of profiles. Whether these E-values equal those of `hmmscan` against the same library was not checked.
- Each organism's hits were computed once, and every setting was applied to the same hit table. The differences between settings therefore contain no search-to-search variation. For `sce` the parsed hit tables were identical in four runs at 16, 12, 4 and 1 threads; the other organisms were searched once.

### Reference and scores

The reference is the **KEGG annotation**: the organism's gene→KO pairs in the `organism_gene_ko` table of the kegg118 artefacts. The table lists the KOs linked to at least one reaction in `ko_reaction`, and the HMM libraries are built from the same table. The organism's **true reactions** are the reactions linked to its annotated KOs, limited to reactions that are in the kegg118 reference model (`--restrict-to-reference`). The limit is applied because reaction recall is measured against reactions that the draft can contain.

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
| `sce` | *Saccharomyces cerevisiae* (budding yeast) | euk | 6021 | 844 | 1217 |
| `cme` | *Cyanidioschyzon merolae* (red alga) | euk | 5010 | 709 | 1156 |
| `eco` | *Escherichia coli* K-12 MG1655 | prok | 4288 | 1072 | 1548 |
| `mge` | *Mycoplasmoides genitalium* G37 (minimal genome) | prok | 476 | 110 | 211 |

Without the limit to the reference model, the published `ko_reaction` table (7642 reactions, against 12,373 in the reference model) gives 1407, 1357, 1772 and 274 true reactions for the four organisms. The reaction columns of the tables below follow the limited definition.

`sce` and `eco` are model organisms; `cme` and `mge` are less studied. `mge` has the smallest proteome of the four and the weakest matched hits in the E-value table.

## Results

### E-value distributions

The table gives percentiles of `log10(E-value)` of the best hit per (gene, KO) pair, for all hits that `hmmsearch` reported, split into matched and novel pairs. A more negative value is a stronger hit. The 99th percentile is the weakest 1 % of the pairs in a group. The table does not show the strongest novel pairs.

| organism | group | n | p50 | p90 | p95 | p99 |
|---|---|---|---|---|---|---|
| `sce` | matched | 842 | −153 | −73 | −57 | −25 |
| `sce` | novel | 9451 | −8 | −2 | 0 | 1 |
| `cme` | matched | 705 | −133 | −63 | −46 | −25 |
| `cme` | novel | 10189 | −8 | −2 | −2 | 0 |
| `eco` | matched | 1071 | −141 | −70 | −57 | −36 |
| `eco` | novel | 27352 | −7 | −2 | −1 | 0 |
| `mge` | matched | 110 | −102 | −43 | −35 | −15 |
| `mge` | novel | 1912 | −4 | −2 | −1 | 0 |

The median matched pair had an E-value between 1e-102 (`mge`) and 1e-153 (`sce`), and the weakest 1 % of matched pairs lay between 1e-15 and 1e-36. The median novel pair lay between 1e-4 and 1e-8. The weakest 1 % of matched pairs was 11 (`mge`) to 29 (`eco`) orders of magnitude stronger than the median novel pair.

The RAVEN 2.11.3 cut-off of `1e-50` falls inside the matched distribution: between p95 and p99 for `sce` and `eco`, between p90 and p95 for `cme`, and between p50 and p90 for `mge`. It therefore removes 1 to 5 % of the matched pairs of `sce` and `eco`, 5 to 10 % of `cme` and 10 to 50 % of `mge`. The default `1e-30` lies beyond p99 for `eco` (fewer than 1 % of the matched pairs removed) and between p95 and p99 for `sce`, `cme` and `mge`, and is 22 to 26 orders of magnitude stronger than the median novel pair.

### Cut-off sweep

`min_score_ratio_ko = 0.3` and `min_score_ratio_g = 0.8` (the RAVEN 2.11.3 values) were fixed while `cutoff` varied.

#### `sce`

| cutoff | gKO prec | gKO rec | gKO F1 | rxn rec | rxn novel |
|---|---|---|---|---|---|
| 1e-10 | 0.57 | 0.98 | 0.73 | 0.99 | 324 |
| 1e-20 | 0.66 | 0.98 | 0.79 | 0.99 | 274 |
| 1e-30 | 0.73 | 0.97 | 0.83 | 0.97 | 208 |
| 1e-50 | 0.78 | 0.95 | 0.86 | 0.96 | 151 |
| 1e-70 | 0.82 | 0.91 | 0.86 | 0.93 | 105 |
| 1e-100 | 0.85 | 0.76 | 0.80 | 0.79 | 61 |

#### `cme`

| cutoff | gKO prec | gKO rec | gKO F1 | rxn rec | rxn novel |
|---|---|---|---|---|---|
| 1e-10 | 0.51 | 0.98 | 0.67 | 1.00 | 539 |
| 1e-20 | 0.56 | 0.98 | 0.71 | 1.00 | 426 |
| 1e-30 | 0.61 | 0.97 | 0.75 | 0.99 | 370 |
| 1e-50 | 0.69 | 0.93 | 0.79 | 0.93 | 310 |
| 1e-70 | 0.75 | 0.85 | 0.80 | 0.87 | 223 |
| 1e-100 | 0.80 | 0.70 | 0.75 | 0.71 | 137 |

#### `eco`

| cutoff | gKO prec | gKO rec | gKO F1 | rxn rec | rxn novel |
|---|---|---|---|---|---|
| 1e-10 | 0.54 | 0.99 | 0.70 | 0.99 | 393 |
| 1e-20 | 0.58 | 0.99 | 0.73 | 0.99 | 308 |
| 1e-30 | 0.61 | 0.99 | 0.75 | 0.99 | 279 |
| 1e-50 | 0.68 | 0.96 | 0.79 | 0.98 | 208 |
| 1e-70 | 0.74 | 0.89 | 0.81 | 0.94 | 167 |
| 1e-100 | 0.82 | 0.75 | 0.78 | 0.81 | 111 |

#### `mge`

| cutoff | gKO prec | gKO rec | gKO F1 | rxn rec | rxn novel |
|---|---|---|---|---|---|
| 1e-10 | 0.53 | 0.98 | 0.69 | 0.99 | 74 |
| 1e-20 | 0.62 | 0.96 | 0.76 | 0.98 | 51 |
| 1e-30 | 0.65 | 0.95 | 0.77 | 0.98 | 39 |
| 1e-50 | 0.77 | 0.85 | 0.81 | 0.88 | 30 |
| 1e-70 | 0.85 | 0.73 | 0.78 | 0.72 | 27 |
| 1e-100 | 0.88 | 0.53 | 0.66 | 0.55 | 21 |

Gene→KO recall was between 0.95 and 0.99 from 1e-10 to 1e-30 in all four organisms and fell at stricter cut-offs. The fall was largest for `mge`, whose reaction recall dropped from 0.98 at 1e-30 to 0.88 at 1e-50 and 0.55 at 1e-100. Precision rose with every stricter cut-off in all four organisms, from 0.73 to 0.78 for `sce` between 1e-30 and 1e-50. With the ratios fixed at 0.3 and 0.8, F1 was highest at 1e-50 or 1e-70 in every organism. Novel predictions remained at the strictest cut-off: at 1e-100 the three larger proteomes had 61 to 137 novel reactions and a gene→KO precision of 0.80 to 0.85 (0.88 for `mge`). The study does not show whether these are wrong assignments, paralogs or genes that KEGG has not annotated.

### Score-ratio sweep

`cutoff` was fixed at `1e-50`. The script scores every combination of `min_score_ratio_ko` (0.0, 0.3, 0.5) and `min_score_ratio_g` (0.5, 0.8, 0.95); the table holds the five combinations per organism that are reported.

| organism | ko ratio | g ratio | gKO prec | gKO rec | gKO F1 |
|---|---|---|---|---|---|
| `sce` | 0.0 | 0.50 | 0.61 | 0.96 | 0.74 |
| `sce` | 0.0 | 0.80 | 0.78 | 0.95 | 0.86 |
| `sce` | 0.0 | 0.95 | 0.84 | 0.93 | 0.88 |
| `sce` | 0.3 | 0.80 | 0.78 | 0.95 | 0.86 |
| `sce` | 0.5 | 0.80 | 0.80 | 0.95 | 0.87 |
| `cme` | 0.0 | 0.50 | 0.53 | 0.93 | 0.68 |
| `cme` | 0.0 | 0.80 | 0.69 | 0.93 | 0.79 |
| `cme` | 0.0 | 0.95 | 0.77 | 0.92 | 0.84 |
| `cme` | 0.3 | 0.80 | 0.69 | 0.93 | 0.79 |
| `cme` | 0.5 | 0.80 | 0.70 | 0.92 | 0.79 |
| `eco` | 0.0 | 0.50 | 0.40 | 0.96 | 0.56 |
| `eco` | 0.0 | 0.80 | 0.67 | 0.96 | 0.79 |
| `eco` | 0.0 | 0.95 | 0.77 | 0.94 | 0.85 |
| `eco` | 0.3 | 0.80 | 0.68 | 0.96 | 0.79 |
| `eco` | 0.5 | 0.80 | 0.70 | 0.95 | 0.81 |
| `mge` | 0.0 | 0.50 | 0.62 | 0.86 | 0.73 |
| `mge` | 0.0 | 0.80 | 0.77 | 0.85 | 0.81 |
| `mge` | 0.0 | 0.95 | 0.82 | 0.85 | 0.83 |
| `mge` | 0.3 | 0.80 | 0.77 | 0.85 | 0.81 |
| `mge` | 0.5 | 0.80 | 0.77 | 0.85 | 0.81 |

At `min_score_ratio_g = 0.80`, raising `min_score_ratio_ko` from 0.0 to 0.5 raised precision by 0.02 (`sce`), 0.01 (`cme`), 0.03 (`eco`) and 0.00 (`mge`), and lowered recall by 0.01 for `cme` and `eco` and not at all for `sce` and `mge`.

Raising `min_score_ratio_g` from 0.80 to 0.95 (at `min_score_ratio_ko = 0.0`) raised precision by 0.06 (`sce`), 0.08 (`cme`), 0.10 (`eco`) and 0.05 (`mge`), and lowered recall by 0.00 to 0.02. At 0.50, precision was the lowest of the three values in every organism. The value 0.9 lies between the tested values 0.8 and 0.95 and was not swept.

### Defaults compared with RAVEN 2.11.3

The table compares the RAVEN 2.11.3 settings `(1e-50, 0.3, 0.8)` with the defaults `(1e-30, 0.3, 0.9)`, given as `(cutoff, min_score_ratio_ko, min_score_ratio_g)`. All values are scores of the saved hit tables; the RAVEN 2.11.3 values are the 1e-50 rows of the cut-off sweep.

| organism | gKO prec | gKO rec | gKO F1 | rxn rec | rxn novel |
|---|---|---|---|---|---|
| `sce` | 0.78 → 0.77 | 0.95 → 0.96 | 0.86 → 0.85 | 0.96 → 0.96 | 151 → 143 |
| `cme` | 0.69 → 0.67 | 0.93 → 0.96 | 0.79 → 0.79 | 0.93 → 0.99 | 310 → 306 |
| `eco` | 0.68 → 0.69 | 0.96 → 0.97 | 0.79 → 0.81 | 0.98 → 0.99 | 208 → 173 |
| `mge` | 0.77 → 0.70 | 0.85 → 0.94 | 0.81 → 0.80 | 0.88 → 0.97 | 30 → 33 |

With the defaults, gene→KO recall rose by 0.09 for `mge` and by 0.01 to 0.03 for the other three organisms. Gene→KO precision fell by 0.01 (`sce`), 0.02 (`cme`) and 0.07 (`mge`), and rose by 0.01 for `eco`. F1 changed by at most 0.01 for `sce`, `cme` and `mge` and rose by 0.02 for `eco`. All scores are rounded to two decimals, so a difference of 0.01 lies within the rounding. The number of novel reactions fell for `sce`, `cme` and `eco` and rose from 30 to 33 for `mge`.

### Whole-model comparison of the two KEGG paths

*S. cerevisiae* was reconstructed in full by two paths, both with the RAVEN 2.11.3 settings `(1e-50, 0.3, 0.8)`. The annotation path takes the organism's genes and KOs from the `organism_gene_ko` table; the HMM path assigns KOs to the proteome with the HMM search.

| Count | annotation path | HMM path |
|---|---|---|
| reactions | 1357 | 1454 |
| metabolites | 1502 | 1565 |
| genes | 838 | 899 |

The HMM path contained 96.2 % of the reactions of the annotation path (1306 of 1357, Jaccard index 0.87) and 96.5 % of its genes (809 of 838, Jaccard index 0.87). The counts were measured with the published kegg118 tables and libraries. The search of `sce` against the eukaryote library is timed under [Settings without a sweep](#settings-without-a-sweep); the prokaryote library was not timed.

## Meaning of the results

From 1e-10 to 1e-30 a stricter cut-off raised precision while gene→KO recall fell by at most 0.03 (from 0.98 or 0.99 to between 0.95 and 0.99). Beyond 1e-30 the cut-off traded recall for precision: it removed matched pairs together with novel pairs, and novel pairs remained at every cut-off tested. Across the whole sweep from 1e-10 to 1e-100 precision rose by 0.28 (`sce`, 0.57 to 0.85) to 0.35 (`mge`). The RAVEN 2.11.3 value `1e-50` removes 10 to 50 % of the matched pairs of `mge`, the organism with the weakest matched hits, and 1 to 10 % in the other three.

At `cutoff = 1e-50`, raising `min_score_ratio_g` from 0.80 to 0.95 raised precision by 0.05 to 0.10 for a recall loss of 0.00 to 0.02, and raising it from 0.50 to 0.80 raised precision by 0.15 to 0.27 (`eco`, 0.40 to 0.67). At `min_score_ratio_g = 0.80` and `cutoff = 1e-50`, raising `min_score_ratio_ko` from 0.0 to 0.5 raised precision by 0.00 to 0.03 and lowered recall by 0.00 to 0.01; its effect at other settings was not reported. The defaults move part of the filtering from the cut-off to `min_score_ratio_g`. On the four organisms the move gained recall, most for `mge`, at the cost of precision in three of them, and left F1 within 0.01 of the RAVEN 2.11.3 settings for three organisms and raised it by 0.02 for `eco`.

## Chosen defaults

| parameter | RAVEN 2.11.3 | default (raven-toolbox and RAVEN 3) | basis |
|---|---|---|---|
| `cutoff` (`cutOff`) | 1e-50 | 1e-30 | beyond matched p99 for `eco`, between p95 and p99 for `sce`, `cme` and `mge`; with `min_score_ratio_g` 0.9, `mge` recall 0.85 → 0.94 |
| `min_score_ratio_g` (`minScoreRatioG`) | 0.8 | 0.9 | from 0.80 to 0.95 it raised precision by 0.05 to 0.10 for a recall loss of 0.00 to 0.02; offsets part of the precision lost to the looser cut-off (inference, 0.9 not swept) |
| `min_score_ratio_ko` (`minScoreRatioKO`) | 0.3 | 0.3 | at `min_score_ratio_g` 0.80 and `cutoff` 1e-50, 0.0 to 0.5 raised precision by 0.00 to 0.03 and lowered recall by 0.00 to 0.01; kept at the RAVEN value |

The defaults favour recall: the changed settings raised recall in every organism and lowered precision in three of the four.

## Settings without a sweep

Two settings next to the cut-offs, `seq_identity` and the model-assembly flags, were not measured in the study. The reasons given for their values are not tested. `threads` was measured in one configuration.

`threads` in `run_hmmsearch` and `build_ko_hmm` defaults to every CPU the process may run on. `hmmsearch` 3.4 of `sce` (6021 sequences) against `kegg118_eukaryotes.hmm` (2698 profiles) returned 10,293 hit rows for 2198 genes and 1998 KOs at 16, 12, 4 and 1 threads, and the parsed hit tables (KO, gene, E-value) were identical. One run per thread count took 89.7 s (16 threads), 88.6 s (12), 96.4 s (4) and 242.5 s (1), on an AMD EPYC 9354 node used exclusively (2026-11-01). Between 16 and 4 threads the time changes by less than 9 %. `build_ko_hmm` was not timed.

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
- Four organisms, the KEGG tables of release 118 and one hit table per organism. For `sce` the parsed hit tables were identical in four runs at 16, 12, 4 and 1 threads; the other organisms were searched once. The scoring of a hit table by `assign_kos` involves no random step.
- The score-ratio sweep used `cutoff = 1e-50` only, and `min_score_ratio_g = 0.9` was not part of either sweep.

## Reproduction

The scripts are in [`scripts/parameter_tuning/kegg/`](https://github.com/CompMetEng/raven-toolbox/tree/develop/scripts/parameter_tuning/kegg) of raven-toolbox. They search with `hmmsearch` from the toolbox binary bundle (`resolve_binary("hmmsearch")`) and take the published kegg118 tables and HMM libraries through `ensure_kegg_data()` and `ensure_kegg_hmm_library("eukaryotes")` or `("prokaryotes")`.

| Script | Produces |
|---|---|
| `fetch_proteomes.py` | the proteomes from the KEGG REST lists and from UniProt |
| `analyze_hmm_cutoffs.py` | the organism header, E-value percentiles, cut-off sweep at (0.3, 0.8), the score-ratio grid and the defaults row (1e-30, 0.3, 0.9) |
| `check_true_reactions.py` | the true-reaction counts under both definitions |
| `compare_kegg_paths.py` | the whole-model comparison of the annotation and HMM paths |
| `time_hmmsearch.py` | the timing and hit-table identity at several thread counts |

`analyze_hmm_cutoffs.py` is called once per organism with `--artefacts`, `--org`, `--proteome`, `--library` and `--threads`. `--save-tblout` writes the `hmmsearch --tblout` table, `--tblout` scores a saved table without searching, `--json` writes the results, and `--restrict-to-reference` limits `ko_reaction` to reactions of the reference model, which is the definition behind the reaction columns above. The gene→KO columns and the percentiles do not depend on that option. `compare_kegg_paths.py` is called with `--org`, `--proteome`, `--artefacts`, `--library`, `--domain`, `--threads` and `--settings`, for example `--settings 1e-50,0.3,0.8 1e-30,0.3,0.9`.

The proteomes (`kegg_rest/<org>.faa`, `uniprot/<org>.faa`, `counts.json`) are in the archived input bundle `kegg_proteomes_2026-11-01.tar.gz`, and the four `hmmsearch --tblout` tables in `kegg_hmmsearch_tblout_2026-11-01.tar.gz`.

The scores of the tables come from the run of 2026-11-01 with raven-toolbox commit `94f3940`, HMMER 3.4 and the published kegg118 tables and libraries, searched with 16 threads on an AMD EPYC 9354 node. Rescoring each saved hit table with `--tblout` gives the saved scores exactly. Not checked: whether the KEGG REST sequences of 2026-10-31 equal the sequences of KEGG release 118 (the sequence counts were compared, not the sequences), and whether `hmmsearch -Z` E-values equal `hmmscan` E-values on these inputs, because the binary bundle has no `hmmscan`. The UniProt proteomes in the bundle were downloaded and counted but not searched.
