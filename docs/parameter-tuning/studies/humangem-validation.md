# Human-GEM cell-type model validation against RAVEN

raven-toolbox's ftINIT was run on Human-GEM with the RNA sequencing (RNA-seq) data of five cell lines from the Hart2015 dataset (DLD1, GBM, HCT116, HELA, RPE1), and each extracted cell-type model was compared with the model that MATLAB RAVEN's `ftINIT` extracted from the same input. The comparison records the reactions each model contains, the reactions the two models share and the reactions only one of them contains, and the time each step took. The question is whether raven-toolbox selects the same reactions as RAVEN.

## Set-up

Software: Human-GEM commit `38567ab8` (v2.1.1 plus 15 commits), RAVEN commit `2d0630e3` on MATLAB 2024b, raven-toolbox commit `94f3940`, and Gurobi for both tools, with 4 cores per run. The Python runs load the Gurobi library 13.0.3 from the gurobipy wheel (most likely; the logs print no version), and the MATLAB side links to the Gurobi module library 13.0.1 (from the linkage of the MATLAB interface; MATLAB prints no version).

Template preparation is the step that runs once per template model, before any cell line. For RAVEN, the Human-GEM function `prepHumanModelForftINIT` removed the drug reactions, the amino-acid triplet reactions and the duplicate complex I reaction from Human-GEM, set the spontaneous and custom reaction lists, and prepared the model with the essential tasks of `metabolicTasks_Essential.txt`. RAVEN's prepared model, the model from which RAVEN extracts, has 9730 reactions. For raven-toolbox, `prep_init_model` ran on the same cleaned Human-GEM (11265 reactions). Every reaction in every raven-toolbox result is in RAVEN's prepared model, so the reaction identifiers of the two results are compared directly.

Scoring: gene scores are `5·ln(level/1)` of the transcripts per million (TPM) values in the Hart2015 file, clipped to [−5, 10], and reactions take their scores from the gene rules; a reaction without genes scores −2. raven-toolbox computes this with `gene_scores_from_expression` and `score_reactions_from_genes`, RAVEN with `transcrData` and `threshold=1`.

Extraction: both tools ran the series `1+1`, two staged mixed-integer linear program (MILP) steps. RAVEN ran `ftINIT` with its default settings. raven-toolbox ran `raven_toolbox.init.ftinit` with series `1+1`, `time_limit=600` and the default `big_m=1000`. A named series runs its own schedule of MILP runs in each step, so `mip_gap` and `mip_gap_abs` have no effect on these runs.

raven-toolbox ran in two variants:

- **No-task**: the template is prepared without a task list, and the extraction uses the expression scores alone.
- **Task-constrained**: the template is prepared with the essential metabolic tasks, the reactions that a task needs are kept whatever their score, and `ftinit` adds reactions back until every task is feasible (its default `fill_gaps=True`).

The RAVEN result is task-constrained in this sense. A third set of no-task runs used `big_m=100`.

Measurements: the result of a run is its set of reaction identifiers. For each cell line the comparison gives the number of reactions in both sets (shared), in one set only, and the Jaccard index, the shared count divided by the size of the union. The comparison covers reactions only; genes, essential genes and task performance of the extracted models were not compared. Each cell line, variant and `big_m` value ran once. Times are wall-clock times of single runs on shared nodes.

## Results

### Run times

| Step | Time |
|------|-----:|
| RAVEN `prepHumanModelForftINIT` (4-worker parallel pool, once per template) | 4320 s |
| raven-toolbox `prep_init_model`, no-task (cobrapy's default process count for flux variability analysis, once per template) | 1556 s |
| raven-toolbox `prep_init_model`, task-constrained (`cobra.Configuration().processes = 1`, once per template) | 1695 s |
| RAVEN `ftINIT`, per cell line | 40 to 91 s |
| raven-toolbox `ftinit`, no-task, per cell line | 81 to 91 s |
| raven-toolbox `ftinit`, task-constrained, per cell line | 146 to 381 s |

### Reactions in the extracted models

| Cell line | RAVEN `ftINIT` | raven-toolbox, no-task | raven-toolbox, task-constrained |
|-----------|-------------:|--------------------------:|-----------------------:|
| DLD1      | 7339 | 7310 | 7348 |
| GBM       | 7278 | 7255 | 7281 |
| HCT116    | 7348 | 7312 | 7343 |
| HELA      | 7417 | 7384 | 7432 |
| RPE1      | 7166 | 7052 | 7165 |

### Agreement of the no-task variant with RAVEN

| Cell line | Shared | Only raven-toolbox | Only RAVEN | Jaccard |
|-----------|-------:|--------------:|-----------:|--------:|
| DLD1   | 7255 |  55 |  84 | 0.981 |
| GBM    | 7202 |  53 |  76 | 0.982 |
| HCT116 | 7236 |  76 | 112 | 0.975 |
| HELA   | 7321 |  63 |  96 | 0.979 |
| RPE1   | 6980 |  72 | 186 | 0.964 |

### Agreement of the task-constrained variant with RAVEN

| Cell line | Shared | Only raven-toolbox | Only RAVEN | Jaccard |
|-----------|-------:|--------------:|-----------:|--------:|
| DLD1   | 7286 | 62 | 53 | 0.984 |
| GBM    | 7235 | 46 | 43 | 0.988 |
| HCT116 | 7277 | 66 | 71 | 0.982 |
| HELA   | 7366 | 66 | 51 | 0.984 |
| RPE1   | 7095 | 70 | 71 | 0.981 |

### Agreement of the no-task variant at two `big_m` values

| Cell line | Jaccard against RAVEN, `big_m=1000` (default) | Jaccard against RAVEN, `big_m=100` | Jaccard between the two raven-toolbox results |
|-----------|---------------------:|----------:|----------------------------------------------:|
| DLD1   | 0.981 | 0.979 | 0.984 |
| GBM    | 0.982 | 0.982 | 0.985 |
| HCT116 | 0.975 | 0.974 | 0.981 |
| HELA   | 0.979 | 0.979 | 0.981 |
| RPE1   | 0.964 | 0.967 | 0.984 |

The no-task `ftinit` runs took 83 to 122 s at `big_m=100` and 81 to 91 s at `big_m=1000`.

## Agreement with the task layer

The task-constrained variant shares Jaccard 0.981 to 0.988 with RAVEN across the five cell lines. Its reaction counts are within 0.2 % of RAVEN's, and the differences run in both directions in similar numbers: 46 to 70 reactions only in the raven-toolbox model and 43 to 71 only in the RAVEN model, out of ~7300.

Neither tool was run twice on the same input, so the comparison does not separate alternate optima of the MILP from a difference between the two implementations. For scale, two raven-toolbox runs that differed only in the seed differed by 110 reactions in [ftINIT reproducibility with `resolve_ties` and `prove_abs_gap`](ftinit-determinism.md). That measurement used a different set-up (Human-GEM v2.0.0-38, DLD1, `big_m=100`, an escalation schedule), so it indicates the order of magnitude and does not bound the spread here.

## Agreement without the task layer

The no-task variant shares Jaccard 0.964 to 0.982 with RAVEN. It keeps fewer reactions than RAVEN in every cell line: 0.3 to 0.5 % fewer for four cell lines and 1.6 % fewer for RPE1. The reactions only in the RAVEN model (76 to 186) outnumber those only in the raven-toolbox model (53 to 76).

The no-task variant omits the task layer that the RAVEN result includes. With the task layer, the reactions only in the RAVEN model fall to 43 to 71 per cell line. That the task layer accounts for most of the surplus is an inference from these counts; the reactions in the surplus were not checked against the task-essential reactions.

## Effect of `big_m`

Lowering the cap on the per-reaction big-M from 1000 to 100 changed the Jaccard index against RAVEN by at most 0.003 in each cell line, one run per cell line and value. In every cell line the two raven-toolbox results shared a higher Jaccard index with each other (0.981 to 0.985) than either shared with RAVEN (0.964 to 0.982); for RPE1 the values were 0.984 between the two results against 0.964 and 0.967 with RAVEN. The cap therefore changed the reaction set (1 minus the Jaccard index between the two results, 0.015 to 0.019) by more than it changed the agreement with RAVEN (at most 0.003). At this resolution the two values agree with RAVEN equally well.

## Run time

After the template preparation, a task-constrained cell-type model took 146 to 381 s in raven-toolbox and 40 to 91 s in RAVEN; a no-task model took 81 to 91 s. The template preparation took 1556 s (26 min) and 1695 s (28 min) in raven-toolbox and 4320 s (72 min) in RAVEN. The preparations ran with different parallelism (see the run-time table), so the times compare whole runs and not the code alone. The [Reference run](../../guide/init.md#reference-run) of the guide Context-specific models with ftINIT reports a preparation of 47 min in MATLAB and 37 min in Python and an extraction of 797 s in MATLAB and 124 s in Python. That run used RAVEN's `prepINITModel` directly on Human-GEM `6812be2a` (12748 reactions) without the cleaning step, and series `1+0`; these four differences from this validation (preparation function, Human-GEM commit, cleaning step, series) were not separated, so the times are not comparable.

## Numerical settings shared with RAVEN

raven-toolbox builds the extraction MILP with two numerical settings of RAVEN:

- Per-reaction big-M. The on-off constraints of a scored reaction use `max(min(ub, big_m), min(-lb, big_m), force_on)` as big-M, an infinite bound counting as `big_m`. The default cap `big_m=1000` is RAVEN's `bigMCap` in `ftINITInternalAlg`. The cap limits the flux a reaction can carry while it counts as on.
- Stoichiometric rescaling. `prep_init_model` applies RAVEN's `rescaleModelForINIT` to the merged model: each coefficient of a reaction is capped at 25 times the smallest coefficient of that reaction, and the reaction is then scaled to a mean absolute coefficient of 1.

Which combinations of `big_m` and rescaling are feasible for the staged pipeline was measured on HCT116 in [ftINIT parameter calibration and input robustness](init-param-calibration.md): with rescaling, `big_m=25` was infeasible and `big_m=100` feasible; without rescaling, `big_m=1000` was feasible (157 s against 83 s with rescaling, Jaccard 0.969 between the two results) and `big_m=100` infeasible.

## Constraint construction

Each steady-state balance of the extraction MILP is built from a flat list of terms and summed with `optlang.symbolics.add`; the same construction is used in the gap-fill. Python's `sum()` re-simplifies the growing expression at each term, and the balances of hub metabolites such as ATP, H⁺ and H₂O are long sums.

## Use of the result

The agreement was measured with the code defaults `big_m=1000` (`_BIG_M` in `raven_toolbox/init/ftinit.py`, listed in [Tuned parameter defaults](../../tuned-parameters.md)) and rescaling on (`scale=True` in `prep_init_model`, with `max_stoich_diff=25` in `rescale_for_init`, both in `raven_toolbox/init/prep.py`). A raven-toolbox model agreed most closely with a RAVEN `ftINIT` model when `prep_init_model` received the same task list as RAVEN's preparation.

## Limits

Each cell line, variant and `big_m` value ran once, without seed repeats, so the run-to-run spread of either tool was not measured and Jaccard differences of a few tenths of a percent are not resolved. The comparison covers reaction sets on one template and one dataset; gene content, essential genes and task performance were not compared. The timings come from shared nodes and are approximate.

## Reproduction

The numbers come from `bigm/bm.py prep`, `preptask` and `val` (raven-toolbox side), `bigm/ml_prep.m` and `bigm/ml_cell.m` (RAVEN side) and `bigm/compare.py`, which prints every table of the study. The scripts are in the raven-docs repository under `scripts/parameter_tuning/init/`. The commands run through the Slurm wrappers `job.sh` and `mljob.sh` as in the README of that folder, with `WORK`, `TOOLBOX_ROOT`, `RAVEN_ROOT`, `HUMANGEM_ROOT` and `PY` set:

```bash
job.sh prep
job.sh preptask
mljob.sh ml_prep
for c in DLD1 GBM HCT116 HELA RPE1; do
  job.sh val --cell $c
  mljob.sh ml_cell $c
done
python compare.py --out $WORK/out --shared $WORK/shared --logs $WORK/logs
```

The preparations `prep`, `preptask` and `ml_prep` write the prepared models `prep_notask.pkl`, `prep_task.pkl` and `matlab_prepData.mat` to `shared/`. The tables are computed from the outputs by `compare.py`.
