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

Against the KEGG reference the highest score was at 40 % for `kla` and `eco` and at 35 % for `yli` and `ani`. Against the OMA reference with BLAST it was at 45 % for the three fungi and at 35 % for *E. coli*; with DIAMOND it was at 45 % for the fungi and at 30 % for *E. coli*. The OMA scores are not tabulated. With BLAST the optima of both references lie between 35 and 45 %; the only optimum below 35 % is *E. coli* against OMA with DIAMOND.

Scored with F1, which weights precision and recall equally, the optimum with BLAST moves to 30 % for `kla` and `eco` and 25 % for `yli` and `ani`; with DIAMOND it is 30 % for `kla`, `ani` and `eco` and 25 % for `yli` (values not tabulated). The best identity therefore depends on how the score weights the two kinds of error.

### Alignment length

| length | `kla` | `yli` | `ani` | `eco` |
|---|---|---|---|---|
| 50 | 0.933 | 0.871 | 0.815 | 0.618 |
| 100 | 0.933 | 0.871 | 0.815 | 0.618 |
| 150 | 0.932 | 0.869 | 0.813 | 0.615 |
| 200 (RAVEN 2.11.3) | 0.923 | 0.860 | 0.804 | 0.598 |
| 300 | 0.885 | 0.816 | 0.764 | 0.571 |

Lengths 50 and 100 gave identical scores and 150 was at most 0.003 lower. The score fell between 150 and 200, by 0.010 to 0.020 from 100 to 200. Compared with 200, a length of 100 raised recall by 3.0 (`kla`), 3.8 (`yli`), 2.2 (`ani`) and 3.1 (`eco`) percentage points, which is 3.9, 6.5, 4.3 and 10.2 % more correct matches, and changed precision by at most 0.6 percentage points (`yli`, 0.967 to 0.961; precision and recall values not tabulated). No OMA scores were reported for alignment length.

### E-value

The hits were collected at an aligner E-value of `1e-4`, so `max_evalue=1e-4` keeps every hit.

| `max_evalue` | `kla` | `yli` | `ani` | `eco` |
|---|---|---|---|---|
| 1e-4 | 0.923 | 0.860 | 0.804 | 0.598 |
| 1e-10 | 0.923 | 0.860 | 0.804 | 0.598 |
| 1e-30 | 0.923 | 0.860 | 0.804 | 0.598 |
| 1e-50 | 0.923 | 0.858 | 0.801 | 0.592 |
| 1e-100 | 0.903 | 0.809 | 0.743 | 0.535 |

The score was the same at 1e-4, 1e-10 and 1e-30 for all four organisms. At 1e-50 it was unchanged for `kla` and lower by 0.002 (`yli`), 0.003 (`ani`) and 0.006 (`eco`), and at 1e-100 it was lower by 0.020 to 0.063. The F1 values (BLAST) are 0.855 for `kla` from 1e-4 to 1e-50 and 0.811 at 1e-100, and 0.663, 0.658 and 0.563 for `ani` at 1e-30, 1e-50 and 1e-100. A hit with at least 40 % identity over at least 200 residues can therefore have an E-value above 1e-50 in `yli`, `ani` and `eco` (inference from the score change; the hit tables were not inspected for this). No OMA scores were reported for the E-value.

### BLAST and DIAMOND

| Organism | best with BLAST | best with DIAMOND | score at that point |
|---|---|---|---|
| `kla` | 40 | 40 | 0.923 vs 0.921 |
| `yli` | 35 | 35 | 0.868 vs 0.866 |
| `ani` | 35 | 35 | 0.814 vs 0.811 |
| `eco` | 40 | 40 | 0.598 vs 0.593 |

Against the KEGG reference with F0.5, the best identity was the same with both aligners for every organism, and the scores at that identity differed by 0.002 to 0.005. DIAMOND ran with `--more-sensitive`, and the speed ratios below apply to that mode. DIAMOND returned 32,192 hits on `kla` against 54,513 for BLAST. After filtering, the two aligners agreed on between 87.9 and 92.3 % of the surviving matches, measured as the Jaccard index of the (template gene, target gene) pairs that survive the filters at the base setting (identity 40, length 200, E-value 1e-30): 92.3 % (`kla`), 88.9 % (`yli`), 87.9 % (`ani`) and 91.8 % (`eco`). That the hits missing from DIAMOND are weak matches the filters would discard is an inference from these two results. BLAST took 140, 152, 200 and 44 s for `kla`, `yli`, `ani` and `eco`, and DIAMOND 12, 11, 14 and 7 s; DIAMOND was 11.7 times faster on `kla` and 14.3 times on `ani` (4 threads, AMD EPYC 9354, DIAMOND with `--more-sensitive`).

### Aligner settings

Two more settings control the search that produces the hits. Neither was part of the sweeps.

`evalue` is the aligner's own cut-off: `1e-4` for `run_blast` and `1e-3` for `run_diamond`. Each matches the MATLAB side: `getBlast` passes `-evalue 10e-5`, which equals `1e-4`, and `getDiamond` passes none, so DIAMOND's own default applies. On *H. polymorpha* against *S. cerevisiae*, loosening the BLAST cut-off from `1e-5` to `1e-4` added 5,200 raw hits (58,702 against 53,502), 8.9 % of the table. The tables differ row by row: 5,314 rows are only in the `1e-4` table and 114 only in the `1e-5` table. Of the 5,314 rows, 4,372 have an E-value above `1e-5` and so fail `max_evalue=1e-30`, and 942 have an E-value at or below `1e-5` (the smallest is 3.1e-60; 4 are below `1e-30`). In the five examples of the 942 rows that were inspected, the rows are other alignments (HSPs) of gene pairs that the cut-off change reports differently; the other rows were not inspected. Whether the 4 rows below `1e-30` and the 114 rows found only at `1e-5` also pass the identity and length filters, and so could change a model, was not checked. The remaining rows fail `max_evalue=1e-30`, so for them the aligner cut-off changes the size of the hit table and not the model.

`threads` defaults to every CPU the process may run on. The first 500 sequences of the *H. polymorpha* proteome returned the same 2,746 hits at one thread and at four, with identical hit tables, in 20.4 s and 5.9 s (3.5 times faster). On a full proteome pair, single-threaded BLASTP took 205 s (*H. polymorpha* against *S. cerevisiae*) and 218 s (the reverse direction). The aligner cut-offs `1e-4` and `1e-5` took 111 s and 108.5 s. The measurements used the SGD translated ORFs (6,735 sequences) as template and Linux BLAST+ 2.17.0 on an AMD EPYC 9354 node.

## Chosen defaults

| Setting | RAVEN 2.11.3 | Default (raven-toolbox and RAVEN 3) | Basis |
|---|---|---|---|
| `min_identity` (`minIde`) | 40 | 40 | Over the sweep from 25 to 50 % the score changed by 0.062 (`kla`) to 0.275 (`eco`), against 0.047 to 0.055 over alignment lengths 50 to 300 and 0.020 to 0.063 over E-values 1e-4 to 1e-100; with BLAST the optima of both references lie between 35 and 45 %. |
| `min_align_len` (`minLen`) | 200 | 100 | 100 scored 0.010 to 0.020 higher than 200 against KEGG; 50 and 100 scored the same, and 100 is the stricter of the two. |
| `max_evalue` (`maxE`) | 1e-30 | 1e-30 | No change in score from 1e-4 to 1e-30 in any organism; 1e-50 lowered it by up to 0.006; kept at the RAVEN value. |

The study supports one `min_identity` for BLAST and DIAMOND against the KEGG reference with F0.5, since both reached the same best identity for every organism. Against OMA the optimum for *E. coli* is 35 % with BLAST and 30 % with DIAMOND, and with F1 the optimum for `ani` is 25 % with BLAST and 30 % with DIAMOND. DIAMOND scores for alignment length and E-value are not tabulated here. No DIAMOND scores are tabulated for the length and E-value sweeps, whose base scores equal those of BLAST.

## Limits

- KEGG's KO annotations are partly derived from sequence similarity, so the KEGG reference alone would partly measure agreement with the method under test. OMA infers orthology independently of BLAST, and its optima lie in the same range of 35 to 45 % identity. OMA scores were reported for identity only.
- The two references are not comparable in absolute terms. The KEGG reference judges only genes with a reaction-linked KO, while the OMA reference judges the whole mapped proteome and counts every match that OMA does not list as an ortholog pair as wrong. Paralogs probably lower the OMA score for this reason (inference). Only the shape of each column is comparable between the references.
- The OMA reference for *Y. lipolytica* is incomplete: 38 % of its OMA pairs could not be mapped to KEGG gene names.
- One template: everything was measured outward from *S. cerevisiae*.
- One setting was varied at a time from length 200 and identity 40 %. The identity optimum and the absence of an E-value effect up to 1e-30 were measured at length 200, and were not measured at the default length of 100.
- The scores count gene matches, not reactions in a finished model. A reaction transfers when any one of its genes matches, so the effect on a finished model is probably smaller (inference, not measured).
- Each score comes from one alignment per organism. Scoring a saved hit table is deterministic. DIAMOND returned 32,192 hits for `kla`. The alignment was run once, so the run-to-run spread of the hit table was not measured.

## Curated-GEM reference

Scoring against curated genome-scale metabolic models (GEMs) of non-model fungi such as [hanpo-GEM](https://github.com/SysBioChalmers/hanpo-GEM) and [rhto-GEM](https://github.com/SysBioChalmers/rhto-GEM) is not part of the 2026-11-01 measurement, and the study reports no numbers for it. Both models were built with RAVEN's homology-based reconstruction, so a score against them would measure agreement with their own build settings and not correctness (inference).

## Reproducing

The scripts are in [`scripts/parameter_tuning/homology/`](https://github.com/CompMetEng/raven-docs/tree/main/scripts/parameter_tuning/homology) of the raven-docs repository. The driver `homology_cutoff_kegg.py` takes `--out` before the subcommand:

```bash
python homology_cutoff_kegg.py --out work fetch
python run_cached.py prefetch --out work
python fetch_references.py --out work/refs --kegg118-sha256 <sha256 of kegg118_core.tar.gz>
python homology_cutoff_kegg.py --out work align
python homology_cutoff_kegg.py --out work score --beta 0.5 \
    --gene-ko work/refs/kegg118_organism_gene_ko_5org.tsv.gz
python agreement.py --work work --gene-ko work/refs/kegg118_organism_gene_ko_5org.tsv.gz --out agreement.tsv
```

`fetch_references.py` downloads the release-118 gene→KO rows (from the `kegg118_core.tar.gz` release asset of raven-toolbox), the current KEGG REST tables and the SGD translated ORFs. `align --aligner diamond` and `score --aligner diamond` repeat the steps with DIAMOND, `score --reference oma` scores against the OMA reference and `score --beta 1` gives F1. The driver also scores identities of 20 and 60 %, which are not tabulated above. `agreement.py` computes the BLAST and DIAMOND agreement, `make_tables.py` collects the results, and `aligner_settings.py` runs the *H. polymorpha* measurements (thread test, aligner E-value `1e-4` against `1e-5`, single-thread full directions). `run_cached.py` wraps the driver, whose path is given in the environment variable `HOMOLOGY_SCRIPT`, and replaces its UniProt download with a disk cache, which allows scoring against OMA offline; it adds the `prefetch` subcommand and passes every other subcommand to the driver. The alignment output is saved, so re-scoring under a different weighting or against a different reference takes about two minutes.

The UniProt downloads, the OMA pairs, the KEGG tables and the SGD ORFs are in the archived input bundle `homology-inputs.tar.zst` (18.9 MB), and the BLAST and DIAMOND hit tables in `homology-hits.tar.zst` (4.0 MB).

The scores come from the run of 2026-11-01 with raven-toolbox `94f3940`, BLAST+ 2.17.0, DIAMOND 2.1.17, the KEGG release-118 table and UniProt release 2026_03, with BLAST and DIAMOND at 4 threads on an AMD EPYC 9354 node. The *H. polymorpha* template is the SGD ORF file, and the thread test uses the first 500 sequences of `hanpo.faa`. The curated-GEM reference is not part of this run.
