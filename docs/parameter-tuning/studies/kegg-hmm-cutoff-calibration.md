# KEGG HMM-query cut-off calibration

The measurements behind the default KO-assignment parameters in `reconstruction/kegg/query.py` (`assign_kos` / `get_kegg_model_from_sequences`, pipeline step 3b.5) and IMPROVEMENTS K15 are the evidence for the default `cutoff=1e-30`, in place of RAVEN 2.11.3's `1e-50`.

## What the parameters do

`assign_kos` turns an `hmmsearch` KO×gene E-value matrix into gene→KO assignments in three steps:

1. `cutoff` keeps hits with `evalue <= cutoff`.
2. `min_score_ratio_ko` drops, within a KO, genes whose `log(evalue)/log(best_evalue_in_KO) < min_score_ratio_ko`.
3. `min_score_ratio_g` drops, within a gene, KOs whose `log(evalue)/log(best_evalue_for_gene) < min_score_ratio_g`.

## Method

- Data: KEGG release 118. Libraries: the maintainer-built `prokaryotes.hmm` (831 MB) and `eukaryotes.hmm` (692 MB), 90 %-clustered, FFT-NS-2 and PartTree (K12).
- Queries: each organism's full proteome, extracted from `genes.pep`.
- Ground truth: the organism's KEGG gene→KO links, from the `organism_gene_ko` table (restricted, as the table is, to reaction-linked KOs).
- Prediction: `assign_kos` output, with the `organism:` prefix stripped from query gene IDs so they match the bare gene IDs in the ground truth.
- Metrics at gene→KO level: precision = |pred ∩ truth| / |pred|, recall = |pred ∩ truth| / |truth|, F1. At reaction level, `rxn_rec` is the fraction of the organism's true reactions recovered (KO→reaction via `ko_reaction`) and `rxn_novel` is the number of predicted reactions that are not in the annotation set.
- Reproduce with [`scripts/analyze_hmm_cutoffs.py`](https://github.com/CompMetEng/raven-toolbox/blob/develop/scripts/analyze_hmm_cutoffs.py).

### Limits of the validation

All four organisms are present in the training set of the libraries, so their own sequences hit their KO profiles strongly and recall is an upper bound. The calibration is therefore relative: it shows how the parameters trade off and where the RAVEN 2.11.3 default sits relative to the signal, and it gives no absolute accuracy estimate. A genome absent from KEGG would be the next validation. The values of `rxn_novel` and "precision < 1" partly reflect legitimate homology that KEGG never annotated for that organism (paralogs, un-curated genes) and are not pure error, so the precision figures are a lower bound on the true precision.

## Organisms

| code | organism | library | proteome (seqs) | true gene→KO pairs | true reactions |
|---|---|---|---|---|---|
| `sce` | *Saccharomyces cerevisiae* (budding yeast) | euk | 6021 | 841 | 1217 |
| `cme` | *Cyanidioschyzon merolae* (red alga) | euk | 5010 | 709 | 1157 |
| `eco` | *Escherichia coli* K-12 MG1655 | prok | 4288 | 1071 | 1548 |
| `mge` | *Mycoplasmoides genitalium* G37 (minimal genome) | prok | 476 | 110 | 211 |

`sce` and `eco` are model organisms; `cme` and `mge` are lesser-studied, and `mge` is additionally a small, divergent genome.

## E-value separation

`log10(E-value)` percentiles of the best hit per (gene, KO) pair, split by whether the pair is in the organism's annotation (**matched**) or not (**novel**). A smaller (more negative) value is a stronger hit.

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

Matched pairs clustered at E ≈ 1e-100…1e-155, and even their weakest 1 % lay at 1e-15…1e-36. Novel pairs clustered at ≈1e-8. The two are separated by ~20 orders of magnitude. RAVEN 2.11.3's `1e-50` lies inside the matched tail (between the matched p95 and p99 for `sce` and `eco`, between p90 and p95 for `cme`, and between p50 and p90 for `mge`), so it discards annotated pairs that score weakly while gaining nothing against the (far weaker) noise.

## Cut-off sweep

`min_score_ratio_ko = 0.3` and `min_score_ratio_g = 0.8` were fixed. The tables give gene→KO precision, recall and F1 and reaction recovery against the annotation.

### `sce`

| cutoff | gKO prec | gKO rec | gKO F1 | rxn rec | rxn novel |
|---|---|---|---|---|---|
| 1e-10 | 0.57 | 0.98 | 0.72 | 0.99 | 334 |
| 1e-20 | 0.65 | 0.98 | 0.78 | 0.97 | 283 |
| 1e-30 | 0.72 | 0.97 | 0.83 | 0.97 | 216 |
| 1e-50 | 0.78 | 0.95 | 0.86 | 0.96 | 157 |
| 1e-70 | 0.81 | 0.91 | 0.86 | 0.91 | 113 |
| 1e-100 | 0.84 | 0.76 | 0.80 | 0.79 | 68 |

### `cme`

| cutoff | gKO prec | gKO rec | gKO F1 | rxn rec | rxn novel |
|---|---|---|---|---|---|
| 1e-10 | 0.50 | 0.98 | 0.67 | 1.00 | 541 |
| 1e-20 | 0.57 | 0.98 | 0.72 | 1.00 | 421 |
| 1e-30 | 0.61 | 0.97 | 0.75 | 0.97 | 367 |
| 1e-50 | 0.70 | 0.93 | 0.80 | 0.94 | 307 |
| 1e-70 | 0.75 | 0.85 | 0.80 | 0.87 | 223 |
| 1e-100 | 0.80 | 0.70 | 0.75 | 0.71 | 136 |

### `eco`

| cutoff | gKO prec | gKO rec | gKO F1 | rxn rec | rxn novel |
|---|---|---|---|---|---|
| 1e-10 | 0.53 | 0.99 | 0.69 | 0.99 | 382 |
| 1e-20 | 0.57 | 0.99 | 0.73 | 0.99 | 300 |
| 1e-30 | 0.60 | 0.98 | 0.75 | 0.99 | 268 |
| 1e-50 | 0.67 | 0.95 | 0.78 | 0.98 | 198 |
| 1e-70 | 0.73 | 0.88 | 0.80 | 0.93 | 157 |
| 1e-100 | 0.82 | 0.74 | 0.77 | 0.80 | 96 |

### `mge`

| cutoff | gKO prec | gKO rec | gKO F1 | rxn rec | rxn novel |
|---|---|---|---|---|---|
| 1e-10 | 0.52 | 0.98 | 0.68 | 0.99 | 75 |
| 1e-20 | 0.62 | 0.96 | 0.75 | 0.98 | 51 |
| 1e-30 | 0.65 | 0.95 | 0.77 | 0.98 | 39 |
| 1e-50 | 0.77 | 0.84 | 0.80 | 0.87 | 29 |
| 1e-70 | 0.85 | 0.73 | 0.78 | 0.73 | 27 |
| 1e-100 | 0.87 | 0.50 | 0.64 | 0.47 | 21 |

Recall was flat and high from 1e-10 to ~1e-30, then fell as the cut-off removed part of the matched tail, gently for model organisms and sharply for the divergent `mge` (rxn recall 0.98 → 0.87 from 1e-30 → 1e-50, → 0.47 at 1e-100). The recall lost to a stricter cut-off is not noise rejection (the noise lies at 1e-8); it is annotated pairs. `rxn_novel` shrank with stricter cut-offs because strong un-annotated homologs were also removed.

## Score-ratio sweep (`cutoff = 1e-50`)

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

- `min_score_ratio_ko` is inert here: across all four organisms, varying it 0.0 → 0.3 → 0.5 left recall unchanged in the rows shown and changed precision by 0.01 to 0.03 (0.03 for `sce` and `eco`, 0.01 for `cme` and `mge` at `min_score_ratio_g` = 0.80). The script output holds the full grid of 0.0, 0.3 and 0.5 against the g-values; the table shows representative rows.
- `min_score_ratio_g` is the precision lever: 0.80 → 0.95 raised precision by ~0.05–0.10 for a recall loss of ~0.01–0.03. The value 0.50 is too loose: it gave the lowest precision of the tested values.

## Chosen defaults and effect

| parameter | RAVEN 2.11.3 | default | rationale |
|---|---|---|---|
| `cutoff` | 1e-50 | 1e-30 | recovers the matched tail (especially divergent genomes); remains ~22 orders above the 1e-8 noise floor |
| `min_score_ratio_g` | 0.8 | 0.9 | the precision lever; offsets the looser cut-off |
| `min_score_ratio_ko` | 0.3 | 0.3 | inert in the measurements; retained for RAVEN parity |

The RAVEN 2.11.3 settings `(1e-50, 0.3, 0.8)` compared with the defaults `(1e-30, 0.3, 0.9)` (`min_score_ratio_ko` 0.3 ≡ 0.0 here):

| organism | gKO prec | gKO rec | rxn rec | rxn novel |
|---|---|---|---|---|
| `sce` | 0.78 → 0.76 | 0.95 → 0.96 | 0.96 → 0.96 | 157 → 137 |
| `cme` | 0.70 → 0.67 | 0.93 → 0.96 | 0.94 → 0.97 | 307 → 305 |
| `eco` | 0.67 → 0.67 | 0.95 → 0.97 | 0.98 → 0.99 | 198 → 173 |
| `mge` | 0.77 → 0.69 | 0.84 → 0.94 | 0.87 → 0.97 | 29 → 35 |

The divergent minimal genome gained ~10 points of gene→KO recall (the case the sequence path exists for). Recall rose by 0.01 to 0.03 for `sce`, `cme` and `eco`. Gene→KO precision fell by 0.02 for `sce`, 0.03 for `cme` and 0.08 for `mge`, and stayed at 0.67 for `eco`. `rxn_novel` fell for `sce` (157 → 137), `cme` (307 → 305) and `eco` (198 → 173) and rose for `mge` (29 → 35).

## Unmeasured settings of the query

Three settings next to the cut-offs were not swept; the reasons for their values do not need a sweep.

`threads` in `run_hmmsearch` and `build_ko_hmm` defaults to every CPU the process may run on. HMMER's Viterbi search is deterministic across thread counts; E-value estimation can differ in the last floating-point places, far below any cut-off used here. Single-threaded search against the full KO library (more than 26,000 HMMs) takes 30 to 60 minutes per proteome against roughly five multi-threaded.

`seq_identity` in `build_ko_hmm` is `0.9`, the identity at which CD-HIT collapses near-duplicate sequences within a KO before the HMM is built, so that a KO with many near-identical entries does not produce an overfitted profile. It is CD-HIT's own recommended value for proteins. `seq_identity=-1` skips the clustering. This step is Python-only: RAVEN 3 dropped its local clustering path when it moved to prebuilt HMM libraries, so there is no MATLAB value to compare with.

The model-assembly flags decide what a draft keeps, and match MATLAB:

| Flag | Default | What it admits |
|---|---|---|
| `keep_spontaneous` | `True` | Reactions marked spontaneous in KEGG, which carry no gene rule. Excluding them breaks real routes. |
| `keep_undefined_stoich` | `True` | Reactions with variable stoichiometry (`n` subunits). They cannot be mass-balanced as written, but dropping them loses real chemistry. |
| `keep_incomplete` | `True` | Reactions whose enzyme set is only partly known. |
| `keep_general` | `False` | Overview-map reactions that lump many specific steps into one. Admitting them double-counts. |

## Whole-model cross-validation

Full reconstruction of *S. cerevisiae* by two paths with the settings `(1e-50, 0.3, 0.8)`:

| | annotation path (3b.4) | HMM path (3b.5) |
|---|---|---|
| reactions | 1355 | 1461 |
| metabolites | 1501 | 1567 |
| genes | 835 | 896 |

Reaction recall 96.3 % (1305/1355 shared, Jaccard 0.86); gene recall 96.6 % (807/835 shared, Jaccard 0.87). The annotation path also uses the `organism_gene_ko.tsv.gz` artefact (K14). `hmmscan` throughput was ≈ 0.1 s/query against either library on 12 threads (yeast: 6021 queries in 633 s).
