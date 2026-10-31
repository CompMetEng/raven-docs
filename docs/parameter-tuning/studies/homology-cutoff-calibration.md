# Homology cut-off calibration

Three settings decide which template reactions transfer to a new organism: `min_identity`, `min_align_len` and `max_evalue`. None of them had been measured in either toolbox before this study.

| Setting | Previous value | Current value | Reason |
|---|---|---|---|
| `min_identity` | 40 | 40 | Changes the result most; 40 is at the centre of the optimum range given by both references. |
| `min_align_len` | 200 (RAVEN 2.11.3) | 100 | 200 discarded real matches; at 100 the wrong-match rate moves by at most 0.6 percentage points. |
| `max_evalue` | 1e-30 | 1e-30 | No effect anywhere between 1e-4 and 1e-50. |

`min_align_len` is 100 in raven-toolbox and in RAVEN 3 (`getModelFromHomology`'s `minLen`); RAVEN 2.11.3 used 200.

## Test design

Four organisms were reconstructed from an *S. cerevisiae* template at a range of settings. Each match that survived was assessed for whether the two genes are counterparts.

Two independent sources provide the reference: KEGG's gene annotations and OMA's ortholog assignments. Wrong matches count double, because a wrong reaction is worse than a missing one: gap-filling can add what is absent, while a wrong reaction is hard to notice and harder to remove.

The organisms span a range of relatedness, because a setting that suits a close relative need not suit a distant one:

| Code | Organism | Relation to yeast |
|---|---|---|
| `kla` | *K. lactis* | close |
| `yli` | *Y. lipolytica* | moderate |
| `ani` | *A. nidulans* | distant |
| `eco` | *E. coli* | very distant |

Proteomes come from UniProt, relabelled with KEGG gene names so both references can be applied to the same matches.

## Sequence identity

The scores are against KEGG annotations (higher is better); the name of the score is not stated.

| identity | `kla` | `yli` | `ani` | `eco` |
|---|---|---|---|---|
| 25 | 0.861 | 0.833 | 0.771 | 0.460 |
| 30 | 0.896 | 0.851 | 0.796 | 0.518 |
| 35 | 0.917 | 0.868 | 0.814 | 0.558 |
| 40 | 0.923 | 0.860 | 0.804 | 0.598 |
| 45 | 0.907 | 0.813 | 0.735 | 0.520 |
| 50 | 0.882 | 0.736 | 0.640 | 0.323 |

Against OMA the best value is 45 for the three fungi and 35 for *E. coli*. The two sources therefore put the optimum between 35 and 45, and 40 is at the centre of that range. Neither supports a looser setting. The default stays at 40.

Counting a missing match as equally bad as a wrong one moves the recommendation to 25, a different answer from the same measurements. A recommendation about these settings that does not state how it weighs the two kinds of mistake cannot be interpreted.

## Alignment length

The reference of this table is not labelled. Its 200 row (0.923, 0.860, 0.804, 0.598) equals the 40 row of the KEGG identity table, so it is scored against KEGG annotations. No OMA scores are reported for alignment length.

| length | `kla` | `yli` | `ani` | `eco` |
|---|---|---|---|---|
| 50 | 0.933 | 0.871 | 0.815 | 0.618 |
| 100 | 0.933 | 0.871 | 0.815 | 0.618 |
| 150 | 0.932 | 0.869 | 0.813 | 0.615 |
| 200 (RAVEN 2.11.3) | 0.923 | 0.860 | 0.804 | 0.598 |
| 300 | 0.885 | 0.816 | 0.764 | 0.571 |

Every value at or below 150 performs the same; the loss appears between 150 and 200. Dropping to 100 recovers 3–4 % more real matches on every organism while the wrong-match rate moves by at most 0.6 of a percentage point. 50 and 100 are identical, so 100 was chosen as the less permissive of the two.

## E-value

This table covers `kla` and `ani` only, and its reference is not labelled. Its 1e-4 … 1e-50 values (0.923, 0.804) equal the 40 row of the KEGG identity table, so it is scored against KEGG annotations. No OMA scores are reported for the e-value.

| `max_evalue` | `kla` | `ani` |
|---|---|---|
| 1e-4 … 1e-50 | 0.923 | 0.804 (identical throughout) |
| 1e-100 | 0.877 | 0.703 |

The score does not change across the 46 orders of magnitude from 1e-4 to 1e-50. Identity and length have already removed whatever a looser e-value would have removed, so the e-value has no remaining effect. The score changes only at 1e-100, where good matches are discarded. The value stays at 1e-30 to match RAVEN.

## Comparison of DIAMOND and BLAST

Both toolboxes offer DIAMOND as the fast alternative and apply the same three settings to its output, which is safe only if the two aligners behave alike; the table shows that they do:

| Organism | best with BLAST | best with DIAMOND | score at that point |
|---|---|---|---|
| `kla` | 40 | 40 | 0.923 vs 0.921 |
| `yli` | 35 | 35 | 0.868 vs 0.865 |
| `ani` | 35 | 35 | 0.814 vs 0.811 |
| `eco` | 40 | 40 | 0.598 vs 0.593 |

DIAMOND finds about half as many matches (29,785 against 54,478 on `kla`), but almost all the missing ones are weak matches that these settings discard. After filtering, the two agree on 87–92 % of what survives, and DIAMOND runs 10–20× faster (34 s against 358 s on `kla`; 40 s against 788 s on `ani`).

The data therefore support one shared set of defaults for both aligners, and DIAMOND is the faster option for large jobs.

## Search settings

The three settings filter BLAST's output. Two more control the search that produces it, and neither affected the finished model.

`evalue` is the aligner's own cut-off, `1e-4` for `run_blast` and `1e-3` for `run_diamond`, each matching what the MATLAB side passes, explicitly in `getBlast`'s case and by inheriting DIAMOND's own default in `getDiamond`'s. On *H. polymorpha* against *S. cerevisiae*, loosening from `1e-5` to `1e-4` admits 5,204 more raw hits, 8.9 % of the table. None of them reach the model: at `min_identity=40` and `max_evalue=1e-30` the post-BLAST filters discard essentially all of them. The setting decides the size of the intermediate hit table and nothing downstream of it, so there is no correctness argument for either value.

`threads` defaults to every CPU the process may run on. Both aligners score each query sequence independently, so the result does not depend on it: a 500-query subset returned an identical 2,469 hits at one thread and at four, in 45.2 s and 23.7 s. On a full proteome pair, single-threaded BLASTP takes about 20 minutes per direction.

## Limits of the measurements

- KEGG's annotations rely on BLAST comparisons, so on their own they would partly measure agreement with the method being tested. OMA infers counterparts independently, so both references were used; they agree.
- The two sources are not directly comparable in absolute terms. KEGG only covers genes it has annotated (a few hundred well-studied ones per organism) while OMA covers whole proteomes and lists strict counterparts, so ordinary gene duplicates lower the measured score. Only the shape of each column is comparable between the two sources.
- The *Y. lipolytica* OMA row has the weakest reference: 38 % of its OMA pairs could not be matched to KEGG gene names, so that reference is incomplete.
- One template: everything was measured outward from *S. cerevisiae*.
- The measurements are on gene matches, not finished models: a reaction transfers if any one of its genes matches, so the effect on a finished model is smaller than these numbers suggest.

## Retired curated-GEM reference

One arm of this study scored candidate thresholds against curated non-model-organism GEMs (hanpo-GEM, rhto-GEM) built by RAVEN's own homology-based reconstruction. The arm was dropped, and the reason is recorded here because it generalises beyond this study.

The diagnostic loosened the thresholds one step at a time and recorded what fraction of newly admitted reactions were already in the curated model. The rate held between 0.62 and 0.85 up to hanpo-GEM's actual build settings (`max_evalue=1e-30, min_align_len=150, min_identity=35`) and fell to 0.06 one step past them. The drop reflects the reference matching its own build settings: the curated model agrees with predictions made at its own build settings and disagrees with everything else, regardless of whether those other settings are better or worse. Optimising against it returns the build settings whether or not they are good, and it can measure self-consistency but not correctness. Most curated non-model fungal GEMs are RAVEN drafts built the same way, so this applies to that class as well as to these two models.

## Reproducing

```bash
python scripts/homology_cutoff_kegg.py fetch --out work/
python scripts/homology_cutoff_kegg.py align --out work/
python scripts/homology_cutoff_kegg.py score --out work/ --beta 0.5 \
    --gene-ko kegg118_organism_gene_ko.tsv.gz
```

Aligning is the only slow part and its output is saved, so re-scoring (under a different weighting, or against a different reference) takes about two minutes.
