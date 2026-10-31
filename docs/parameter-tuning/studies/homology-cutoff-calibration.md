# Homology cut-off calibration

Homology-based reconstruction transfers a template reaction to a new organism when a gene of the new organism matches a template gene in a BLAST or DIAMOND search and the match passes three filters: `min_identity`, `min_align_len` and `max_evalue` (`minIde`, `minLen` and `maxE` in RAVEN's `getModelFromHomology`). The study aligned the proteomes of four organisms against *S. cerevisiae* once, applied each filter setting to the saved hits, and scored the surviving matches against two references that state which genes are counterparts. It records one score per organism and setting, the agreement between BLAST and DIAMOND, and their run times.

## Set-up

### Organisms and alignment

*S. cerevisiae* S288C is the template. The four targets span a range of relatedness to it, because a setting that suits a close relative need not suit a distant one:

| Code | Organism | Relation to yeast |
|---|---|---|
| `kla` | *K. lactis* | close |
| `yli` | *Y. lipolytica* | moderate |
| `ani` | *A. nidulans* | distant |
| `eco` | *E. coli* | most distant |

Proteomes come from UniProt reference proteomes. Each protein is relabelled with its KEGG gene name through UniProt's KEGG cross-reference for the exact organism code; proteins without one are dropped. Both references can then be applied to the same matches.

Each target was aligned against the template in both directions, once with `run_blast` (aligner E-value `1e-4`) and once with `run_diamond` (aligner E-value `1e-3`). Every filter setting was applied to the same saved hit table, so each score comes from one deterministic calculation. A hit is kept when `evalue <= max_evalue`, `align_len >= min_align_len` and `identity >= min_identity`; `get_model_from_homology` requires `evalue < max_evalue`. The kept hits are collected into a set of (template gene, target gene) pairs, so a pair found in both directions, or by more than one hit, counts as one match. A hit whose two genes are not both judged by the reference is counted as unjudgeable and left out of the score. The scoring does not reduce hits to best hits or build a model.

The sweeps vary one setting at a time from the RAVEN 2.11.3 values `max_evalue=1e-30`, `min_align_len=200` and `min_identity=40`. The identity sweep therefore ran at an alignment length of 200, the length sweep at 40 % identity, and the E-value sweep at 40 % identity and length 200.

### References

The **KEGG reference** counts a match between a template gene and a target gene as correct when the two genes share at least one KO in KEGG's `organism_gene_ko` table (release 118). The table lists only KOs that are linked to a reaction. A match is judged only when both genes have such a KO; other matches are left out of the score.

The **OMA reference** counts a match as correct when the [OMA browser](https://omabrowser.org/) lists the two genes as a pair of orthologs. OMA identifies proteins by UniProt identifiers, which are mapped to KEGG gene names on both sides; OMA pairs that cannot be mapped are dropped. A match is judged when both genes have a KEGG gene name, so the OMA reference covers the whole mapped proteome.

### Score

For each setting, **precision** is the number of correct matches divided by all judged matches, and **recall** is the number of correct matches divided by all pairs in the reference. The score is F0.5, the weighted harmonic mean `1.25·P·R / (0.25·P + R)` of precision P and recall R. With β = 0.5 it weights precision twice as heavily as recall. The weighting is the authors' choice: a missing reaction can be added by gap-filling, while a wrongly transferred reaction is hard to notice and harder to remove. The reproduction command passes `--beta 0.5`, which is also the default of the script, so the scores in the tables are F0.5. All score tables are against the KEGG reference; their base rows agree with each other.

## Results

### Sequence identity

| identity | `kla` | `yli` | `ani` | `eco` |
|---|---|---|---|---|
| 25 | 0.861 | 0.833 | 0.771 | 0.460 |
| 30 | 0.896 | 0.851 | 0.796 | 0.518 |
| 35 | 0.917 | 0.868 | 0.814 | 0.558 |
| 40 | 0.923 | 0.860 | 0.804 | 0.598 |
| 45 | 0.907 | 0.813 | 0.735 | 0.520 |
| 50 | 0.882 | 0.736 | 0.640 | 0.323 |

Against the KEGG reference the highest score was at 40 % for `kla` and `eco` and at 35 % for `yli` and `ani`. Against the OMA reference it was at 45 % for the three fungi and at 35 % for *E. coli*; the OMA scores are not tabulated. The optima of both references lie between 35 and 45 %, and in neither reference is an optimum below 35 %.

Scored with F1, which weights precision and recall equally, the optimum moves to 25 % (values not tabulated). The best identity therefore depends on how the score weights the two kinds of error.

### Alignment length

| length | `kla` | `yli` | `ani` | `eco` |
|---|---|---|---|---|
| 50 | 0.933 | 0.871 | 0.815 | 0.618 |
| 100 | 0.933 | 0.871 | 0.815 | 0.618 |
| 150 | 0.932 | 0.869 | 0.813 | 0.615 |
| 200 (RAVEN 2.11.3) | 0.923 | 0.860 | 0.804 | 0.598 |
| 300 | 0.885 | 0.816 | 0.764 | 0.571 |

Lengths 50 and 100 gave identical scores and 150 was at most 0.003 lower. The score fell between 150 and 200, by 0.010 to 0.020 from 100 to 200. Compared with 200, a length of 100 gave 3 to 4 more recall on every organism and lowered precision by at most 0.6 percentage points (precision and recall values not tabulated). The unit of the 3 to 4 is not recorded: percentage points of recall, or per cent more correct matches. No OMA scores were reported for alignment length.

### E-value

The E-value sweep was reported for `kla` and `ani` only. The hits were collected at an aligner E-value of `1e-4`, so `max_evalue=1e-4` keeps every hit.

| `max_evalue` | `kla` | `ani` |
|---|---|---|
| 1e-4 … 1e-50 | 0.923 | 0.804 (identical throughout) |
| 1e-100 | 0.877 | 0.703 |

The score was the same at 1e-4, 1e-10, 1e-30 and 1e-50, which spans 46 orders of magnitude, and fell at 1e-100. A likely reason (inference, not checked against the hit tables) is that every hit with at least 40 % identity over at least 200 residues already has an E-value below 1e-50. No OMA scores were reported for the E-value.

### BLAST and DIAMOND

| Organism | best with BLAST | best with DIAMOND | score at that point |
|---|---|---|---|
| `kla` | 40 | 40 | 0.923 vs 0.921 |
| `yli` | 35 | 35 | 0.868 vs 0.865 |
| `ani` | 35 | 35 | 0.814 vs 0.811 |
| `eco` | 40 | 40 | 0.598 vs 0.593 |

The best identity was the same with both aligners for every organism, and the scores at that identity differed by 0.002 to 0.005. DIAMOND returned 29,785 hits on `kla` against 54,478 for BLAST. After filtering, the two aligners agreed on 87 to 92 % of the surviving matches. That the hits missing from DIAMOND are weak matches the filters would discard is an inference from these two results. DIAMOND took 34 s against 358 s for BLAST on `kla` and 40 s against 788 s on `ani`, 10.5 and 19.7 times faster (thread count not recorded).

### Aligner settings

Two more settings control the search that produces the hits. Neither was part of the sweeps.

`evalue` is the aligner's own cut-off: `1e-4` for `run_blast` and `1e-3` for `run_diamond`. Each matches the MATLAB side: `getBlast` passes `-evalue 10e-5`, which equals `1e-4`, and `getDiamond` passes none, so DIAMOND's own default applies. On *H. polymorpha* against *S. cerevisiae*, loosening the BLAST cut-off from `1e-5` to `1e-4` added 5,204 raw hits, 8.9 % of the table. Every added hit has an E-value above `1e-5` and so fails `max_evalue=1e-30`. As long as the aligner cut-off is looser than `max_evalue`, it changes the size of the hit table and not the model.

`threads` defaults to every CPU the process may run on. A 500-query subset returned the same 2,469 hits at one thread and at four, in 45.2 s and 23.7 s. On a full proteome pair, single-threaded BLASTP took about 20 minutes per direction.

## Chosen defaults

| Setting | RAVEN 2.11.3 | Default (raven-toolbox and RAVEN 3) | Basis |
|---|---|---|---|
| `min_identity` (`minIde`) | 40 | 40 | The setting with the largest effect; the optima of both references lie between 35 and 45 %. |
| `min_align_len` (`minLen`) | 200 | 100 | 100 scored 0.010 to 0.020 higher than 200 against KEGG; 50 and 100 scored the same, and 100 is the stricter of the two. |
| `max_evalue` (`maxE`) | 1e-30 | 1e-30 | No change in score from 1e-4 to 1e-50; kept at the RAVEN value. |

The study supports one `min_identity` for BLAST and DIAMOND, since both reached the same best identity for every organism. No DIAMOND scores were reported for the length and E-value sweeps, whose base scores equal those of BLAST.

## Limits

- KEGG's KO annotations are partly derived from sequence similarity, so the KEGG reference alone would partly measure agreement with the method under test. OMA infers orthology independently of BLAST, and its optima lie in the same range of 35 to 45 % identity. OMA scores were reported for identity only.
- The two references are not comparable in absolute terms. The KEGG reference judges only genes with a reaction-linked KO, while the OMA reference judges the whole mapped proteome and counts every match that OMA does not list as an ortholog pair as wrong. Paralogs probably lower the OMA score for this reason (inference). Only the shape of each column is comparable between the references.
- The OMA reference for *Y. lipolytica* is incomplete: 38 % of its OMA pairs could not be mapped to KEGG gene names.
- One template: everything was measured outward from *S. cerevisiae*.
- One setting was varied at a time from length 200 and identity 40 %. The identity optimum and the absence of an E-value effect were measured at length 200, and were not measured at the default length of 100.
- The scores count gene matches, not reactions in a finished model. A reaction transfers when any one of its genes matches, so the effect on a finished model is probably smaller (inference, not measured).
- Each score comes from one alignment per organism; scoring is deterministic, so there is no run-to-run spread.

## Retired curated-GEM reference

A further part of the study scored candidate settings against two curated genome-scale metabolic models (GEMs) of non-model fungi, [hanpo-GEM](https://github.com/SysBioChalmers/hanpo-GEM) and [rhto-GEM](https://github.com/SysBioChalmers/rhto-GEM), which were built with RAVEN's homology-based reconstruction. This reference was dropped.

The test loosened the settings one step at a time and recorded which fraction of the newly admitted reactions was already in the curated model. The fraction stayed between 0.62 and 0.85 up to hanpo-GEM's own build settings (`max_evalue=1e-30, min_align_len=150, min_identity=35`) and fell to 0.06 one step beyond them. The inference is that the curated model agrees with predictions made at its own build settings and with nothing looser, whether or not those settings are good. A score against such a model returns its build settings and measures self-consistency, not correctness. The same applies to any curated model drafted with RAVEN's homology method (inference).

## Reproducing

```bash
python scripts/homology_cutoff_kegg.py fetch --out work/
python scripts/homology_cutoff_kegg.py align --out work/
python scripts/homology_cutoff_kegg.py score --out work/ --beta 0.5 \
    --gene-ko kegg118_organism_gene_ko.tsv.gz
```

`scripts/homology_cutoff_kegg.py` is in raven-toolbox. `align --aligner diamond` and `score --aligner diamond` repeat the steps with DIAMOND, and `score --reference oma` scores against the OMA reference. The script also scores identities of 20 and 60 %, which are not reported. The alignment times recorded for `kla` and `ani` are in [BLAST and DIAMOND](#blast-and-diamond). The alignment output is saved, so re-scoring under a different weighting or against a different reference takes about two minutes. The *H. polymorpha* and thread measurements of the aligner settings are not produced by this script.
