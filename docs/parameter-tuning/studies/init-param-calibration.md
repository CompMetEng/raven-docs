# ftINIT parameter calibration and input robustness

This study runs raven-toolbox's ftINIT on Human-GEM with the HCT116 expression data of the Hart2015 dataset and varies one or two settings per run series; the scaling runs and the full-pipeline runs vary scaling and `big_m` together. The calibration part varies the mixed-integer linear program (MILP) settings `mip_gap`, `big_m` and `force_on` and the stoichiometric scaling of the prepared model, and records the run time, the MILP objective and which reactions are kept. The robustness part degrades the expression input by dropout, noise and downsampling, extracts a model with the metabolic-task layer on, and records the model size, the essential tasks the model passes and its overlap with the model from clean data. Overlap is measured as the Jaccard index of two kept-reaction sets: the reactions in both divided by the reactions in either.

## Set-up

### Software and inputs

The calibration runs used Human-GEM commit `38567ab8` (v2.1.1 plus 15 commits), the HCT116 column of the Hart2015 RNA sequencing file, raven-toolbox commit `94f3940` and Gurobi 13.0.1 on 4 cores. The template is the reference model of the [Human-GEM cell-type model validation against RAVEN](humangem-validation.md): Human-GEM without the drug reactions, the amino-acid triplet reactions and the duplicate complex I reaction, 11265 reactions. `prep_init_model` prepared it without a task list. Its scaled merged model, the model that the MILP receives, has 6657 reactions; the preparation took 26 min and is excluded from every time in the tables.

The robustness runs used an earlier Human-GEM state whose commit is not recorded, the same HCT116 data, a template prepared with the essential metabolic tasks, and `big_m=100`. The two parts therefore have no common baseline, and their reaction counts and Jaccard indices cannot be compared with each other.

Gene scores are `5·ln(level/1)` of each expression level, clipped to [−5, 10] (see [Gene-scoring constants](#gene-scoring-constants)), and reaction scores follow from the gene rules (`score_reactions_from_genes`, default `no_gene_score=-2`).

### Run types

| Run type | What runs | Script and sweep |
|---|---|---|
| Step-0 solve | One `run_ftinit` call (one MILP, no run schedule) for the first step of series `1+1` on the scaled merged model, with a 900 s limit | `analyze_init_params.py`, sweep `ftinit_milp` |
| Scaling run | The same step-0 solve on a model prepared without scaling, which `rescale_for_init` then rescales with the given `max_stoich_diff` (or leaves unscaled), with a 600 s limit and `mip_gap=0.001`. | `analyze_init_params.py`, sweep `prep_scale` |
| Full pipeline | One call of `ftinit` with series `1+1` and `time_limit=600` on the prepared model without tasks: both MILP steps, each with its own schedule of runs. | `analyze_init_params.py`, sweep `ftinit_full` |
| Robustness run | One call of `ftinit` with series `1+1` on the template prepared with tasks, including the gap-fill that adds reactions until every task is feasible, followed by `check_tasks` on the extracted model. | `analyze_init_robustness.py`, phases `gradient` and `levers` |

A named series such as `1+1` ignores `mip_gap` and `mip_gap_abs`: every step runs its own schedule of MILP runs, with limits of 120 s, 5000 s and 5 s. `time_limit` lowers the limit of each scheduled run, so at `time_limit=600` it shortens the 5000 s runs only. `mip_gap` therefore acts on the step-0 solve and not on the full pipeline.

`big_m` is the cap on the per-reaction big-M of the on and off constraints. Each scored reaction gets `max(min(ub, big_m), min(-lb, big_m), force_on)`, and an infinite bound counts as `big_m`, so `big_m` limits the flux that a reaction can carry while it counts as on. `force_on` is the smallest flux at which a reaction counts as on. `max_stoich_diff` is the largest ratio between the stoichiometric coefficients of one reaction after `rescale_for_init` (RAVEN's `rescaleModelForINIT`).

The robustness runs degrade the expression vector of HCT116 in three ways, each with one random draw (seed 0):

- **Dropout**: a fraction of the genes in the data gets the level 0, which scores −5.
- **Noise**: every level is multiplied by `exp(N(0,σ))`, a log-normal factor with standard deviation σ on the natural-log scale.
- **Downsampling**: a fraction of the genes is removed from the data. Within a gene rule a missing gene is skipped, and a reaction whose genes are all missing gets `no_gene_score`.

The lever runs repeat the 70 % dropout input with `no_gene_score` or `force_on` changed.

### Measurements

| Column | Meaning |
|---|---|
| time (s) | Wall-clock time of the `run_ftinit` call (step-0 and scaling runs) or the `ftinit` call (full pipeline), including the construction of the MILP and excluding the preparation |
| objective | MILP objective of the step-0 solve |
| rel.obj.gap | (reference objective − objective) / reference objective; a positive value is a lower objective than the reference row |
| `n_kept` | Reactions in the model that the full pipeline returns |
| n_rxns | Reactions in the model that a robustness run returns, after the gap-fill |
| Jaccard | Jaccard index of two kept-reaction sets: the reactions in both divided by the reactions in either. Step-0 sets are merged-model reaction identifiers; full-pipeline and robustness sets are Human-GEM reaction identifiers |
| tasks pass, frac | Essential tasks that `check_tasks` reports as passed on the extracted model, as a count and as a fraction |

A MIP gap bounds the objective only. Two solutions within the gap can keep different reactions, so the reaction set is compared separately from the objective.

Each table row is one run unless the row states repeats; this set-up has no runs that differ only in the seed. The only available measure of the seed-to-seed spread comes from a different set-up, in [ftINIT reproducibility with `resolve_ties` and `prove_abs_gap`](ftinit-determinism.md): two baseline builds (Human-GEM v2.0.0-38, DLD1, `big_m=100`, escalation schedule, with tasks and gap-fill) that differed only in the seed differed by 110 reactions (symmetric difference of the kept-reaction sets). That page does not give the sizes of these two builds; the 7754 reactions it reports belong to a build with `resolve_ties=True` and `prove_abs_gap=1.0`. Assuming builds of about 7300 to 7800 reactions, 110 reactions are about 1.5 % of the model and correspond to a Jaccard index of about 0.985. That pair compares two full pipelines with gap-fill; a step-0 set is the result of one MILP step on merged-model identifiers without tasks, a different kind of object. Between the settings of the calibration the Jaccard index ranged from 0.9976 to 0.9649, a difference of 0.2 to 3.5 % from identical sets.

### Source of the numbers

The calibration tables come from `analyze_init_params.py` with the sweeps `ftinit_milp`, `prep_scale` and `ftinit_full`, and the robustness tables from `analyze_init_robustness.py` with the phases `gradient` and `levers`. The calibration runs differ from the sweep grids of the pinned script. The script runs the step-0 `mip_gap` and `force_on` sweeps and the scaling runs at `big_m=100.0`; the tables report `big_m=1000` for the `mip_gap` and `force_on` sweeps and both caps for the scaling runs. The script's step-0 `big_m` grid is 1000, 250, 100, 50 and 25, and its full-pipeline grid is the default `big_m` (1000) at `mip_gap` 0.001, 0.003 and 0.01 and `big_m` 50 and 250 at `mip_gap=0.003`, all on the scaled preparation. Outside these grids the calibration ran `big_m` 10 and 500 in the step-0 solve; `big_m` 500, 100 and 25 and the unscaled preparation in the full pipeline; `big_m=1000` in the scaling runs; and the repeats with `mip_gap_abs=None`. The result files of the runs are not in the repository.

## Results

### Step-0 solve with different `mip_gap` values

`big_m=1000`, `force_on=0.1`. The reference is the tightest gap.

| `mip_gap` | time (s) | objective | rel.obj.gap | Jaccard vs tightest |
|--------:|---------:|----------:|------------:|--------------------:|
| 0.0002 | 24 | 45954 | ref | ref |
| 0.001 | 24 | 45949 | +0.0001 | 0.9976 |
| 0.003 | 24 | 45831 | +0.0027 | 0.9926 |
| 0.01 | 24 | 45789 | +0.0036 | 0.9908 |
| 0.03 | 25 | 44705 | +0.0272 | 0.9649 |
| 0.1 | 24 | 44647 | +0.0284 | 0.9663 |

### Step-0 solve with different `big_m` values

`mip_gap=0.001`, `force_on=0.1`. The last two columns compare each set with the run at `big_m=1000` and with the run at `big_m=100`.

| `big_m` | time (s) | rel.obj.gap | Jaccard vs `big_m=1000` | Jaccard vs `big_m=100` |
|------:|---------:|------------:|----------------------:|---------------------:|
| 1000 | 24 | ref | ref | 0.985 |
| 500 | 24 | +0.0002 | 0.983 | 0.990 |
| 250 | 26 | −0.0001 | 0.986 | 0.985 |
| 100 | 24 | −0.0001 | 0.985 | ref |
| 50 | 24 | −0.0003 | 0.988 | 0.987 |
| 25 | 25 | −0.0003 | 0.987 | 0.991 |
| 10 | 23 | −0.0002 | 0.988 | 0.990 |

### Step-0 solve with different `force_on` values

`mip_gap=0.001`, `big_m=1000`. The reference is the default 0.1.

| `force_on` | time (s) | rel.obj.gap | Jaccard vs 0.1 |
|---------:|---------:|------------:|---------------:|
| 0.1 | 24 | ref | ref |
| 0.02 | 25 | −0.0002 | 0.987 |
| 0.05 | 25 | −0.0002 | 0.989 |
| 0.2 | 25 | −0.0002 | 0.992 |
| 0.5 | 25 | −0.0000 | 0.987 |

### Step-0 solve with different stoichiometric scaling

Scaling runs at `mip_gap=0.001` and two `big_m` values. Every rel.obj.gap and Jaccard index in the table, including the `big_m=100` columns, is against the first row at `big_m=1000` (scale on, `max_stoich_diff=25`, abbreviated `msd`).

| config | time (s), `big_m=1000` | rel.obj.gap | Jaccard vs scaled `msd=25`, `big_m=1000` | time (s), `big_m=100` | rel.obj.gap | Jaccard vs scaled `msd=25`, `big_m=1000` |
|--------|---------:|------------:|-------------------------:|---------:|------------:|-------------------------:|
| scale on, `msd=25` | 25 | ref | ref | 25 | +0.0001 | 0.986 |
| `msd=10` | 26 | +0.0021 | 0.991 | 24 | +0.0020 | 0.989 |
| `msd=50` | 25 | +0.0031 | 0.983 | 25 | +0.0031 | 0.983 |
| `msd=100` | 26 | +0.0048 | 0.980 | 25 | +0.0049 | 0.980 |
| scale off | 30 | −0.0050 | 0.984 | 25 | −0.0044 | 0.983 |

The reference row of this table and the `mip_gap=0.001` row of the step-0 `mip_gap` table have the same settings and come from different runs: the scaling run rescales an unscaled preparation with `rescale_for_init` and has a 600 s limit, the step-0 run uses `prep(scale=True)` and a 900 s limit. Their objectives are 45539.6 and 45949.2, and their reaction sets share a Jaccard index of 0.983.

### Full pipeline with and without scaling

`time_limit=600`.

| config (full pipeline, `time_limit=600`) | result |
|-----------------------------------|--------|
| scale on, `big_m=1000` | feasible, 83 s |
| scale off, `big_m=1000` | feasible, 157 s, 7264 reactions, Jaccard 0.969 vs scale on |
| scale off, `big_m=100` | infeasible (no usable solution after 30 s) |
| scale on, `big_m=25` | infeasible (no usable solution after 30 s) |

An infeasible run stopped with `ftINIT MILP produced no usable solution (status: infeasible)`.

### Full pipeline with different `big_m` values

Scaled preparation without tasks, series `1+1`, `time_limit=600s`.

| config | time (s) | `n_kept` | Jaccard vs `big_m=1000` |
|--------|---------:|-------:|---------------------:|
| `big_m=1000`, three runs | 83, 83, 84 | 7312 | ref (1.000 between the runs) |
| `big_m=500` | 83 | 7306 | 0.980 |
| `big_m=250` | 117 | 7323 | 0.978 |
| `big_m=100`, two runs | 117, 118 | 7324 | 0.981 |
| `big_m=50` | 82 | 7325 | 0.982 |
| `big_m=25` | 30 | infeasible | none |

The runs were started with different `mip_gap` values, which the series ignores, so runs at one `big_m` are repeats of one configuration: 0.001, 0.003 and 0.01 at `big_m=1000`, 0.001 and 0.003 at `big_m=100`, and 0.003 at the other caps. Further repeats ran with `mip_gap_abs=None` in place of the default `mip_gap_abs=10`: at `big_m=1000` three runs of 85, 84 and 81 s, which kept the same 7312 reactions, and at `big_m=250` one run of 114 s. A third run at `big_m=100` took 119 s and a second run at `big_m=50` took 81 s; the record of the runs does not state their settings beyond the cap. In total `big_m=1000` has six runs (81 to 85 s), `big_m=250` two, `big_m=100` three (117, 118 and 119 s) and `big_m=50` two (82 and 81 s); `big_m=500` and `big_m=25` ran once.

### Degraded expression input

Robustness runs with the task layer on. The clean row is the reference of the Jaccard column.

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

Lever runs on the 70 % dropout input. The default row is the dropout 70 % row of the previous table.

| config | n_rxns | frac | Jaccard vs clean |
|--------|-------:|-----:|-----------------:|
| default (`no_gene_score=−2`, `force_on=0.1`) | 5113 | 0.986 | 0.594 |
| `no_gene_score=−1.0` | 5110 | 0.986 | 0.593 |
| `no_gene_score=−0.5` | 5128 | 0.986 | 0.593 |
| `force_on=0.2` | 5159 | 0.986 | 0.600 |

## Effect of `mip_gap` on a single solve

In the step-0 solve the time was 24 to 25 s at every gap from 0.0002 to 0.1. At `mip_gap=0.001` the objective was within 0.0001 of the tightest gap and the Jaccard index was 0.9976. The Jaccard index stayed at 0.99 or above up to `mip_gap=0.01` and fell to 0.9649 and 0.9663 at 0.03 and 0.1. In the full pipeline the gap has no effect: the three `big_m=1000` runs at 0.001, 0.003 and 0.01 kept the same 7312 reactions.

## Effect of `big_m` and scaling

In the step-0 solve every `big_m` from 10 to 1000 was feasible, took 23 to 26 s and reached the objective of `big_m=1000` within 0.0003. Against the run at `big_m=1000` and against the run at `big_m=100`, the reaction sets of the other caps had Jaccard indices of 0.983 to 0.991. The step-0 solve has no seed repeats, and the seed pair in [Set-up](#set-up) compares full pipelines with gap-fill, so it is no reference for these sets. In the step-0 scaling runs, every `max_stoich_diff` from 10 to 100 and the unscaled model were feasible at both caps, with Jaccard indices of 0.980 to 0.991 against the scaled reference.

The full pipeline separates the settings that the step-0 solve does not. At `big_m=1000` it was feasible with and without scaling: 83 s with scaling, 157 s without, and the two models shared a Jaccard index of 0.969 (7312 and 7264 reactions). At `big_m=100` it was feasible with scaling (117 to 119 s) and infeasible without, and at `big_m=25` it was infeasible with scaling. With scaling, the caps from 50 to 1000 gave runs of 81 to 119 s with no trend in `big_m` and reaction sets that shared a Jaccard index of 0.978 to 0.982 with the default. No cap below 1000 ran faster than the 81 to 85 s of the `big_m=1000` runs. Derived from the sizes and Jaccard indices in the table (the sizes of two sets add up to the size of their union times 1 + J), the sets at caps 500, 250, 100 and 50 differed from the `big_m=1000` set by about 148, 163, 140 and 133 reactions. The one seed pair available, from the different set-up in [Set-up](#set-up), differed by 110 reactions, so every cap difference is about 20 to 50 % larger than that single value; the seed-to-seed spread of this set-up is unknown. The three `big_m=1000` runs kept identical sets (Jaccard 1.000) and only the cap changed between rows, so the differences follow the cap; whether they are systematic or a different choice among near-equal optima was not tested. A lower cap also reduces the flux that a kept reaction can carry.

## Effect of `force_on`

`force_on` changes the MILP itself, through the on and off constraints. From 0.02 to 0.5 the step-0 solve took 24 to 25 s, the objective moved by at most 0.0002 and the reaction set shared a Jaccard index of 0.987 or more with the default 0.1. The full pipeline was not run with other `force_on` values.

## Effect of degraded input

Noise changed the model less than sparse input. At σ=1.0 and σ=2.0 the model kept 7812 and 7768 reactions against 7777 for clean data, passed all 69 tasks and shared a Jaccard index of 0.952 and 0.919 with the clean model. Dropout of 50 % and 70 % reduced the model to 5968 and 5113 reactions (Jaccard 0.713 and 0.594), and downsampling of 50 % and 70 % to 6765 and 6123 reactions (Jaccard 0.815 and 0.728). At equal fractions dropout removed more reactions than downsampling. The difference matches the scores involved, −5 for a zero level against −2 for a reaction without measured genes, but this explanation was not tested. Under dropout and downsampling the model passed 67 or 68 of 69 tasks; the failing tasks and the cause of the failures were not examined.

At 70 % dropout no tested lever moved the model back towards the clean model: the Jaccard index stayed at 0.593 to 0.600, the size at 5110 to 5159 reactions and the task fraction at 0.986. Under dropout the dropped genes stay in the data with a zero level and score −5, so `no_gene_score` acts only on reactions without gene rules and on reactions whose genes are all absent from the data. The study concludes that no parameter recovers the expression evidence that dropout removes; this is an inference from the four lever settings, which do not include other parameters. The lever runs did not include downsampled input, so the effect of `no_gene_score` on missing genes was not measured.

In raven-toolbox commit `94f3940`, `ftinit` calls `fill_tasks` without a time limit, so the gap-fill uses the default of `fill_tasks`, 300 s per task (`_FILL_TIME_LIMIT`), and not the `time_limit` of the extraction. The time limit that the 90 % dropout run of more than 75 min used is not recorded.

## Choice of settings

The calibration supports the defaults `big_m=1000`, `force_on=0.1` and scaling on with `max_stoich_diff=25` (RAVEN's setting). `big_m=1000` is the cap that RAVEN's `ftINITInternalAlg` uses (`bigMCap`). Scaling is not needed for feasibility at `big_m=1000`; in these single runs the pipeline took 83 s with scaling and 157 s without. In the step-0 solve, `mip_gap=0.001` reached an objective within 0.0001 of the tightest gap; a named series ignores the setting. The full-pipeline runs used `time_limit=600` and the robustness script uses `time_limit=120`; no full-pipeline run took longer than 157 s in total. For noisy input the tested settings needed no change, and no tested setting compensated for dropout.

## Gene-scoring constants

Expression values become gene scores through

```
score = clip(factor × ln(level / reference), min_score, max_score)
```

with `factor=5.0`, `max_score=10.0` and `min_score=-5.0`, the same in both implementations. The logarithm is natural (base e) in `init/score.py` and in RAVEN's `scoreModel`. The source of each implementation cites no paper for the three constants. The one candidate reference that has been suggested, a 2012 paper that describes mCADRE, uses categorical scoring, which differs from this continuous log-ratio, so it is not their origin. The constants are RAVEN's own values without a literature source.

## Comparison with the solver benchmark

[ftINIT on different solvers](init-solver-benchmark.md) runs the same full pipeline with each solver interface. With Gurobi it took 92 s and kept 7312 reactions, against 83 s and 7312 reactions here. The benchmark time also includes loading the prepared model and scoring the reactions, and its limit is 900 s against 600 s here. A limit shortens only the 5000 s runs of the schedule, and no Gurobi run in either study reached its limit. Its Gurobi run at `big_m=100` kept 7324 reactions, the count of the two `big_m=100` runs here, whose reaction set shares a Jaccard index of 0.981 with the `big_m=1000` set. The solver comparison itself, with GLPK at 2182 s and a Jaccard index of 0.892 against Gurobi and the failure of HiGHS through the `scipy` interface, is on that page.

## Limits

- One model (Human-GEM), one cell line (HCT116) and one solver (Gurobi 13.0.1).
- Most settings ran once; the repeats are listed with the full-pipeline table. This set-up has no seed repeats. The full-pipeline differences between caps are larger than the one seed pair available, which comes from a different set-up, so the seed-to-seed spread of this set-up is unknown.
- The robustness runs used a Human-GEM state whose commit is not recorded and `big_m=100`; the pinned script passes no `big_m`, so a rerun uses the default 1000. Each degradation is one random draw at one seed.
- The step-0 solve shows no difference between caps or scaling settings that the full pipeline shows, so step-0 results alone do not predict feasibility of the pipeline.
- The robustness tables have no run times, and the effect of `no_gene_score` on downsampled input was not measured.

## Reproduction

```bash
python scripts/analyze_init_params.py    --cell HCT116 --sweeps ftinit_milp,prep_scale,ftinit_full
python scripts/analyze_init_robustness.py --cell HCT116 --algo ftinit
```

Both scripts read the reference model `raven_refModel.xml` from the working folder of [Human-GEM cell-type model validation against RAVEN](humangem-validation.md) (`--work`, default `~/hgem_compare`) and keep their results in a pickle file, so a rerun skips finished settings. `analyze_init_params.py` prepares the template itself; `analyze_init_robustness.py` loads the prepared template with tasks, `rg_prep_tasks.pkl`, from the same folder. The grids of the pinned `analyze_init_params.py` are smaller than the set of runs in the tables (see [Source of the numbers](#source-of-the-numbers)).
