# ftINIT parameter calibration and input robustness

The study runs the ftINIT of raven-toolbox on Human-GEM with the HCT116 expression data of the Hart2015 dataset and varies one or two settings per series of runs. The scaling runs and the full-pipeline runs vary the scaling and `big_m` together. The calibration part varies the settings `mip_gap`, `big_m` and `force_on` of the mixed-integer linear program (MILP) and the stoichiometric scaling of the prepared model, and records the run time, the MILP objective and the reactions that are kept. The robustness part degrades the expression input by dropout, noise and downsampling, extracts a model with the metabolic-task layer on, and records the size of the model, the essential tasks that it passes and its overlap with the model from clean data.

The overlap is the Jaccard index of two kept-reaction sets: the reactions in both divided by the reactions in either. Steps are counted from 1 on the pages of this study. The run logs count from 0, so the logged `step 1` is the second step.

The main findings are:

- In the first-step solve, every `big_m` from 10 to 1000 and every scaling setting was feasible, and the time stayed between 23 and 30 s.
- In the full pipeline, `big_m=1000` was feasible with and without scaling (83 s and 157 s), `big_m=100` was feasible with scaling only, and `big_m=25` was infeasible with scaling.
- Noise changed the model less than sparse input, and no tested parameter recovered the expression evidence that dropout removes.

## Set-up

### Software and inputs

The calibration runs used Human-GEM commit `38567ab8` (v2.1.1 plus 15 commits), the HCT116 column of the Hart2015 RNA sequencing file, raven-toolbox commit `94f3940` and Gurobi on 4 cores. The Gurobi library is 13.0.3 from the gurobipy wheel (most likely, because the logs print no version). The template is the reference model of the [Human-GEM cell-type model validation against RAVEN](humangem-validation.md): Human-GEM without the drug reactions, the amino-acid triplet reactions and the duplicate complex I reaction, with 11265 reactions. `prep_init_model` prepared it without a task list. Its scaled merged model, which is the model that the MILP receives, has 6657 reactions. The preparation took 26 min and is excluded from every time in the tables.

The robustness runs used Human-GEM at a commit that is not recorded, the same HCT116 data, a template prepared with the essential metabolic tasks, and `big_m=100`. The two parts therefore have no common baseline, and their reaction counts and Jaccard indices cannot be compared with each other.

Gene scores are `5·ln(level/1)` of each expression level, clipped to [−5, 10] (see [Gene-scoring constants](#gene-scoring-constants)). Reaction scores follow from the gene rules (`score_reactions_from_genes`, default `no_gene_score=-2`).

### Run types

| Run type | What runs | Script and sweep |
|---|---|---|
| First-step solve | One `run_ftinit` call (one MILP, no run schedule) for the first step of series `1+1` on the scaled merged model, with a 900 s limit | `bigm/bm.py step0` |
| Scaling run | The same first-step solve on a model prepared without scaling, which `rescale_for_init` then rescales with the given `max_stoich_diff` or leaves unscaled, with a 600 s limit and `mip_gap=0.001` | `bigm/bm.py scale` |
| Full pipeline | One call of `ftinit` with series `1+1` and `time_limit=600` on the prepared model without tasks: both MILP steps, each with its own schedule of runs | `bigm/bm.py full` |
| Robustness run | One call of `ftinit` with series `1+1` on the template prepared with tasks, including the gap-fill that adds reactions until every task is feasible, followed by `check_tasks` on the extracted model | `scripts/analyze_init_robustness.py` (`MIP_GAP` 0.02, `TIME_LIMIT` 120), phases `gradient` and `levers` (not recoverable) |

A named series such as `1+1` ignores `mip_gap` and `mip_gap_abs`. Every step runs its own schedule of MILP runs, with limits of 120 s, 5000 s and 5 s. The setting `time_limit` lowers the limit of each scheduled run, so at `time_limit=600` it shortens the 5000 s runs only. The setting `mip_gap` therefore acts on the first-step solve and not on the full pipeline.

The setting `big_m` is the cap on the per-reaction big-M of the on and off constraints. Each scored reaction gets `max(min(ub, big_m), min(-lb, big_m), force_on)`, and an infinite bound counts as `big_m`, so `big_m` limits the flux that a reaction can carry while it counts as on. The setting `force_on` is the smallest flux at which a reaction counts as on. The setting `max_stoich_diff` is the largest ratio between the stoichiometric coefficients of one reaction after `rescale_for_init` (`rescaleModelForINIT` of RAVEN).

The robustness runs degrade the expression vector of HCT116 in three ways, each with one random draw (seed 0):

- **Dropout:** a fraction of the genes in the data gets the level 0, which scores −5.
- **Noise:** every level is multiplied by `exp(N(0,σ))`, a log-normal factor with standard deviation σ on the natural-log scale.
- **Downsampling:** a fraction of the genes is removed from the data. Within a gene rule a missing gene is skipped, and a reaction whose genes are all missing gets `no_gene_score`.

The lever runs repeat the 70 % dropout input with `no_gene_score` or `force_on` changed.

### Measurements

| Column | Meaning |
|---|---|
| time (s) | Wall-clock time of the `run_ftinit` call (first-step and scaling runs) or the `ftinit` call (full pipeline), including the construction of the MILP and excluding the preparation |
| objective | MILP objective of the first-step solve |
| rel.obj.gap | (reference objective − objective) / reference objective. A positive value is a lower objective than the reference row |
| `n_kept` | Reactions in the model that the full pipeline returns |
| n_rxns | Reactions in the model that a robustness run returns, after the gap-fill |
| Jaccard | Jaccard index of two kept-reaction sets. First-step sets are merged-model reaction identifiers, and full-pipeline and robustness sets are Human-GEM reaction identifiers |
| tasks pass, frac | Essential tasks that `check_tasks` reports as passed on the extracted model, as a count and as a fraction |

A MIP gap bounds the objective only. Two solutions within the gap can keep different reactions, so the reaction set is compared separately from the objective.

Each table row is one run unless the row states repeats. This set-up has no runs that differ only in the seed. The only measure of the seed-to-seed spread comes from another set-up, in [ftINIT reproducibility with `resolve_ties` and `prove_abs_gap`](ftinit-determinism.md). There, two baseline builds that differed only in the seed (Human-GEM v2.0.0-38, DLD1, `big_m=100`, escalation schedule, with tasks and gap-fill) differed by 110 reactions, which is the symmetric difference of the kept-reaction sets. The two builds kept 7779 and 7781 reactions, so the 110 reactions are 1.4 % of the model and correspond to a Jaccard index of 0.986. That pair compares two full pipelines with gap-fill, whereas a first-step set is the result of one MILP step on merged-model identifiers without tasks, which is another kind of object. Between the settings of the calibration the Jaccard index ranged from 0.9976 to 0.9649, a difference of 0.2 to 3.5 % from identical sets.

### Source of the numbers

The calibration tables come from `bigm/bm.py` with the subcommands `step0`, `scale` and `full`, summarised by `bigm/summ.py` and `bigm/compare.py` (prepared model `prep_notask.pkl`). The scripts are in the raven-docs repository under `scripts/parameter_tuning/init/`. The subcommand `step0` runs a grid of 16 solves: `mip_gap` 0.0002 to 0.1, `big_m` 10 to 1000 and `force_on` 0.02 to 0.5, at `big_m=1000` for the `mip_gap` and `force_on` sweeps. The subcommand `scale` runs the unscaled preparation rescaled with `max_stoich_diff` 10, 25, 50 and 100 or left unscaled, at `big_m` 1000 and 100. The subcommand `full` runs one `ftinit` call per setting, with the options `--gap`, `--big-m`, `--scale` and `--noabs` (`mip_gap_abs=None`).

`compare.py` computes the tables of the first-step solve, the scaling runs and the full pipeline from the outputs. The robustness tables (degraded expression input, lever runs and the 90 % dropout run) come from `scripts/analyze_init_robustness.py`. The script exists at the pinned commit, and the state of the script and the inputs that produced the tables are not recoverable.

## Results

### First-step solve with different `mip_gap` values

The settings are `big_m=1000` and `force_on=0.1`, and the reference is the tightest gap.

| `mip_gap` | time (s) | objective | rel.obj.gap | Jaccard vs tightest |
|--------:|---------:|----------:|------------:|--------------------:|
| 0.0002 | 24 | 45954 | ref | ref |
| 0.001 | 24 | 45949 | +0.0001 | 0.9976 |
| 0.003 | 24 | 45831 | +0.0027 | 0.9926 |
| 0.01 | 24 | 45789 | +0.0036 | 0.9908 |
| 0.03 | 25 | 44705 | +0.0272 | 0.9649 |
| 0.1 | 24 | 44647 | +0.0284 | 0.9663 |

### First-step solve with different `big_m` values

The settings are `mip_gap=0.001` and `force_on=0.1`. The last two columns compare each set with the run at `big_m=1000` and with the run at `big_m=100`.

| `big_m` | time (s) | rel.obj.gap | Jaccard vs `big_m=1000` | Jaccard vs `big_m=100` |
|------:|---------:|------------:|----------------------:|---------------------:|
| 1000 | 24 | ref | ref | 0.985 |
| 500 | 24 | +0.0002 | 0.983 | 0.990 |
| 250 | 26 | −0.0001 | 0.986 | 0.985 |
| 100 | 24 | −0.0001 | 0.985 | ref |
| 50 | 24 | −0.0003 | 0.988 | 0.987 |
| 25 | 25 | −0.0003 | 0.987 | 0.991 |
| 10 | 23 | −0.0002 | 0.988 | 0.990 |

### First-step solve with different `force_on` values

The settings are `mip_gap=0.001` and `big_m=1000`, and the reference is the default 0.1.

| `force_on` | time (s) | rel.obj.gap | Jaccard vs 0.1 |
|---------:|---------:|------------:|---------------:|
| 0.1 | 24 | ref | ref |
| 0.02 | 25 | −0.0002 | 0.987 |
| 0.05 | 25 | −0.0002 | 0.989 |
| 0.2 | 25 | −0.0002 | 0.992 |
| 0.5 | 25 | −0.0000 | 0.987 |

### First-step solve with different stoichiometric scaling

The scaling runs used `mip_gap=0.001` and two `big_m` values. Every rel.obj.gap and Jaccard index in the table, including the `big_m=100` columns, is against the first row at `big_m=1000` (scale on, `max_stoich_diff=25`, abbreviated `msd`).

| config | time (s), `big_m=1000` | rel.obj.gap | Jaccard vs scaled `msd=25`, `big_m=1000` | time (s), `big_m=100` | rel.obj.gap | Jaccard vs scaled `msd=25`, `big_m=1000` |
|--------|---------:|------------:|-------------------------:|---------:|------------:|-------------------------:|
| scale on, `msd=25` | 25 | ref | ref | 25 | +0.0001 | 0.986 |
| `msd=10` | 26 | +0.0021 | 0.991 | 24 | +0.0020 | 0.989 |
| `msd=50` | 25 | +0.0031 | 0.983 | 25 | +0.0031 | 0.983 |
| `msd=100` | 26 | +0.0048 | 0.980 | 25 | +0.0049 | 0.980 |
| scale off | 30 | −0.0050 | 0.984 | 25 | −0.0044 | 0.983 |

The reference row of this table and the `mip_gap=0.001` row of the first-step `mip_gap` table have the same settings and come from different runs. The scaling run rescales an unscaled preparation with `rescale_for_init` and has a 600 s limit, whereas the first-step run uses `prep(scale=True)` and a 900 s limit. Their objectives are 45539.6 and 45949.2, and their reaction sets share a Jaccard index of 0.983.

### Full pipeline with and without scaling

The runs used `time_limit=600`.

| config | result |
|-----------------------------------|--------|
| scale on, `big_m=1000` | feasible, 83 s |
| scale off, `big_m=1000` | feasible, 157 s, 7264 reactions, Jaccard 0.969 vs scale on |
| scale off, `big_m=100` | infeasible (no usable solution after 30 s) |
| scale on, `big_m=25` | infeasible (no usable solution after 30 s) |

An infeasible run stopped with `ftINIT MILP produced no usable solution (status: infeasible)`.

### Full pipeline with different `big_m` values

The runs used a scaled preparation without tasks, series `1+1` and `time_limit=600s`.

| config | time (s) | `n_kept` | Jaccard vs `big_m=1000` |
|--------|---------:|-------:|---------------------:|
| `big_m=1000`, three runs | 83, 83, 84 | 7312 | ref (1.000 between the runs) |
| `big_m=500` | 83 | 7306 | 0.980 |
| `big_m=250` | 117 | 7323 | 0.978 |
| `big_m=100`, two runs | 117, 118 | 7324 | 0.981 |
| `big_m=50` | 82 | 7325 | 0.982 |
| `big_m=25` | 30 | infeasible | none |

The runs were started with different `mip_gap` values, which the series ignores, so runs at one `big_m` are repeats of one configuration: 0.001, 0.003 and 0.01 at `big_m=1000`, 0.001 and 0.003 at `big_m=100`, and 0.003 at the other caps. Further repeats ran with `mip_gap_abs=None` in place of the default `mip_gap_abs=10`:

- at `big_m=1000`, three runs of 85, 84 and 81 s, which kept the same 7312 reactions;
- at `big_m=250`, one run of 114 s;
- at `big_m=100`, a third run of 119 s (`mip_gap=0.001`, `mip_gap_abs=None`);
- at `big_m=50`, a second run of 81 s (`mip_gap=0.003`, `mip_gap_abs=None`).

In total `big_m=1000` has six runs (81 to 85 s), `big_m=250` two, `big_m=100` three (117, 118 and 119 s) and `big_m=50` two (82 and 81 s). The caps `big_m=500` and `big_m=25` ran once.

### Degraded expression input

The robustness runs had the task layer on, and the clean row is the reference of the Jaccard column.

| input | n_rxns | tasks pass | frac | Jaccard vs clean |
|-------|-------:|-----------:|-----:|-----------------:|
| clean | 7777 | 69/69 | 1.000 | ref |
| dropout 50 % | 5968 | 67/69 | 0.971 | 0.713 |
| dropout 70 % | 5113 | 68/69 | 0.986 | 0.594 |
| noise σ=1.0 | 7812 | 69/69 | 1.000 | 0.952 |
| noise σ=2.0 | 7768 | 69/69 | 1.000 | 0.919 |
| downsample 50 % | 6765 | 68/69 | 0.986 | 0.815 |
| downsample 70 % | 6123 | 68/69 | 0.986 | 0.728 |

One model from 90 % dropout input, outside these tables, ran for more than 75 min in the gap-fill MILP.

### Parameters at 70 % dropout

The lever runs used the 70 % dropout input. The default row is the dropout 70 % row of the previous table.

| config | n_rxns | frac | Jaccard vs clean |
|--------|-------:|-----:|-----------------:|
| default (`no_gene_score=−2`, `force_on=0.1`) | 5113 | 0.986 | 0.594 |
| `no_gene_score=−1.0` | 5110 | 0.986 | 0.593 |
| `no_gene_score=−0.5` | 5128 | 0.986 | 0.593 |
| `force_on=0.2` | 5159 | 0.986 | 0.600 |

## Interpretation

### Effect of `mip_gap` on a single solve

In the first-step solve the time was 24 to 25 s at every gap from 0.0002 to 0.1. At `mip_gap=0.001` the objective was within 0.0001 of the tightest gap and the Jaccard index was 0.9976. The index stayed at 0.99 or above up to `mip_gap=0.01` and fell to 0.9649 and 0.9663 at 0.03 and 0.1. In the full pipeline the gap has no effect: the three `big_m=1000` runs at 0.001, 0.003 and 0.01 kept the same 7312 reactions.

### Effect of `big_m` and scaling

In the first-step solve every `big_m` from 10 to 1000 was feasible, took 23 to 26 s and reached the objective of `big_m=1000` within 0.0003. Against the run at `big_m=1000` and against the run at `big_m=100`, the reaction sets of the other caps had Jaccard indices of 0.983 to 0.991. The first-step solve has no repeats of the seed, and the seed pair in [Set-up](#set-up) compares full pipelines with gap-fill, so it is no reference for these sets. In the first-step scaling runs, every `max_stoich_diff` from 10 to 100 and the unscaled model were feasible at both caps, with Jaccard indices of 0.980 to 0.991 against the scaled reference.

The full pipeline separates the settings that the first-step solve does not.

- At `big_m=1000` it was feasible with and without scaling. It took 83 s with scaling and 157 s without, and the two models shared a Jaccard index of 0.969 (7312 and 7264 reactions).
- At `big_m=100` it was feasible with scaling (117 to 119 s) and infeasible without.
- At `big_m=25` it was infeasible with scaling.
- With scaling, the caps from 50 to 1000 gave runs of 81 to 119 s with no trend in `big_m`, and reaction sets that shared a Jaccard index of 0.978 to 0.982 with the default. The fastest run at a cap below 1000 (80.8 s at `big_m=50`, with `mip_gap_abs=None`) was as fast as the fastest `big_m=1000` run (81.1 s).

Counted from the reaction sets, the sets at the caps 500, 250, 100 and 50 differed from the `big_m=1000` set by 150, 165, 140 and 133 reactions. The rounded Jaccard values in the table give 148 and 163 for the first two. The one seed pair available, from the other set-up, differed by 110 reactions, so every cap difference is 21 to 50 % larger than that single value, and the seed-to-seed spread of this set-up is unknown. The three `big_m=1000` runs kept identical sets (Jaccard 1.000) and only the cap changed between rows, so the differences follow the cap. Whether they are systematic or a different choice among near-equal optima was not tested. A lower cap also reduces the flux that a kept reaction can carry.

### Effect of `force_on`

The setting `force_on` changes the MILP itself, through the on and off constraints. From 0.02 to 0.5 the first-step solve took 24 to 25 s, the objective moved by at most 0.0002 and the reaction set shared a Jaccard index of 0.987 or more with the default 0.1. The full pipeline was not run with other `force_on` values.

### Effect of degraded input

Noise changed the model less than sparse input. At σ=1.0 and σ=2.0 the model kept 7812 and 7768 reactions against 7777 for clean data, passed all 69 tasks and shared a Jaccard index of 0.952 and 0.919 with the clean model. Dropout of 50 % and 70 % reduced the model to 5968 and 5113 reactions (Jaccard 0.713 and 0.594), and downsampling of 50 % and 70 % to 6765 and 6123 reactions (Jaccard 0.815 and 0.728). At equal fractions dropout removed more reactions than downsampling. The difference matches the scores involved, −5 for a zero level against −2 for a reaction without measured genes, but this explanation was not tested. Under dropout and downsampling the model passed 67 or 68 of 69 tasks, and the failing tasks and the cause of the failures were not examined.

At 70 % dropout no tested lever moved the model back towards the clean model. The Jaccard index stayed at 0.593 to 0.600, the size at 5110 to 5159 reactions and the task fraction at 0.986. Under dropout the dropped genes stay in the data with a zero level and score −5, so `no_gene_score` acts only on reactions without gene rules and on reactions whose genes are all absent from the data. The conclusion that no parameter recovers the expression evidence that dropout removes is an inference from the four lever settings, which do not include other parameters. The lever runs did not include downsampled input, so the effect of `no_gene_score` on missing genes was not measured.

In raven-toolbox commit `94f3940`, `ftinit` calls `fill_tasks` without a time limit, so the gap-fill uses the default of `fill_tasks`, 300 s per task (`_FILL_TIME_LIMIT`), and not the `time_limit` of the extraction. The time limit that the 90 % dropout run of more than 75 min used is not recorded.

### Choice of settings

The defaults `big_m=1000`, `force_on=0.1` and scaling on with `max_stoich_diff=25` are the values of RAVEN. Every `big_m` from 50 to 1000 was feasible with scaling on, and `big_m=25` was infeasible. The cap `big_m=1000` is the one that `ftINITInternalAlg` of RAVEN uses (`bigMCap`). Scaling is not needed for feasibility at `big_m=1000`, and in these single runs the pipeline took 83 s with scaling and 157 s without. In the first-step solve, `mip_gap=0.001` reached an objective within 0.0001 of the tightest gap, and a named series ignores the setting. The full-pipeline runs used `time_limit=600` and the robustness script uses `time_limit=120`. No full-pipeline run took longer than 157 s in total. For noisy input the tested settings needed no change, and no tested setting compensated for dropout.

## Gene-scoring constants

Expression values become gene scores through

```
score = clip(factor × ln(level / reference), min_score, max_score)
```

with `factor=5.0`, `max_score=10.0` and `min_score=-5.0`, the same in both implementations. The logarithm is natural (base e) in `init/score.py` and in `scoreModel` of RAVEN. The source of each implementation cites no paper for the three constants. A 2012 paper (Wang et al. 2012, [mCADRE](https://doi.org/10.1186/1752-0509-6-153)) uses categorical scoring and is not the origin. The constants are values of RAVEN itself without a literature source.

## Comparison with the solver benchmark

[ftINIT on different solvers](init-solver-benchmark.md) runs the same full pipeline with each solver interface. With Gurobi it took 92 s and kept 7312 reactions, against 83 s and 7312 reactions here. The benchmark time also includes loading the prepared model and scoring the reactions, and its limit is 900 s against 600 s here. A limit shortens only the 5000 s runs of the schedule, and no Gurobi run in either study ran for its overall limit.

The warning `ftINIT step 1 hit the 600s time limit` appears 14 times in 13 full-pipeline and validation logs, and the Gurobi run of the solver benchmark has the same warning with 900 s. The logged `step 1` is the second step. The warning prints the `time_limit` argument and not the limit of the run that stopped. The stopped run is a shorter scheduled run, inferred from the total times of 83 s and 92 s, and the logs do not say which. One scheduled solve per run stopped at a limit.

The Gurobi run of the solver benchmark at `big_m=100` kept 7324 reactions, the count of the two `big_m=100` runs here, whose reaction set shares a Jaccard index of 0.981 with the `big_m=1000` set. The solver comparison itself is on that page: GLPK at 2182 s with a Jaccard index of 0.892 against Gurobi, and the failure of HiGHS through the `scipy` interface.

## Limits

- One model (Human-GEM), one cell line (HCT116) and one solver (Gurobi library 13.0.3 from the gurobipy wheel, most likely, because the logs print no version).
- Most settings ran once, and the repeats are listed with the full-pipeline table. This set-up has no repeats of the seed. The full-pipeline differences between caps are larger than the one seed pair available, which comes from another set-up, so the seed-to-seed spread of this set-up is unknown.
- The robustness runs used a Human-GEM commit that is not recorded and `big_m=100`. The script at the pinned commit passes no `big_m`, so a run with it uses the default 1000. Each degradation is one random draw at one seed.
- The first-step solve shows no difference between caps or scaling settings that the full pipeline shows, so first-step results alone do not predict the feasibility of the pipeline.
- The robustness tables have no run times, and the effect of `no_gene_score` on downsampled input was not measured.

## Reproduction

The commands run through the Slurm wrapper `job.sh` of `scripts/parameter_tuning/init/bigm/` as in the README of that folder, with `WORK`, `TOOLBOX_ROOT`, `HUMANGEM_ROOT` and `PY` set. The prepared models come first:

```bash
job.sh prep
job.sh step0 --cell HCT116
job.sh scale --cell HCT116
job.sh full --gap 0.003 --big-m 1000 --tag g003-bm1000
job.sh full --gap 0.003 --big-m 100  --scale off --tag g003-bm100-scaleoff
job.sh full --gap 0.001 --big-m 100  --noabs --tag noabs-g0.001-bm100
python summ.py $WORK/out
python compare.py --out $WORK/out --shared $WORK/shared --logs $WORK/logs
```

The tags of the other full-pipeline runs are listed in the README: `--big-m` 25, 50, 250 and 500 at `--gap 0.003`, the `mip_gap` runs 0.001, 0.003 and 0.01 at `big_m=1000`, and the `--noabs` repeats. The unscaled preparation of `scale` takes about 26 min. The robustness tables have no reproduction command, because the state of `analyze_init_robustness.py` and the inputs that produced them are not recoverable.
