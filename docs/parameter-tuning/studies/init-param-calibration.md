# ftINIT parameter calibration and input robustness

The study covers the ftINIT parameters of raven-toolbox on a genome-scale model (Human-GEM, Hart2015, HCT116) in two parts:

1. Calibration: the parameter values with the best trade-off between speed and quality on clean data (`scripts/analyze_init_params.py`).
2. Robustness: the effect of degrading the transcriptomics input on the model, with the task layer always on (it is part of the pipeline and is not varied), and the parameters that keep the model functional and stable (`scripts/analyze_init_robustness.py`).

Both scripts are resumable and reusable on any model and dataset; the numbers are for HCT116. The clean-data calibration uses the per-reaction big-M cap `big_m` (Human-GEM `38567ab8`). The robustness measurements used `big_m=100` and an earlier Human-GEM state whose commit is not recorded, so the two sets of numbers do not share a baseline. "Jaccard" is the reaction-set overlap with the reference (tightest setting or clean data). For a model-extraction tool the reaction set is the product, and a MIP gap bounds only the objective, so set stability is tracked separately.

---

## Clean-data calibration

The clean-data runs used Human-GEM commit `38567ab8` (v2.1.1 plus 15 commits), HCT116 column of Hart2015, raven-toolbox commit `94f3940`, Gurobi 13.0.1, 4 cores. The model after removing drug reactions, amino-acid triplet reactions and the duplicate complex I reaction has 11265 reactions; the scaled merged model that the MILP sees has 6657 reactions. `big_m` is the cap on the per-reaction big-M: each scored reaction gets `max(min(ub, big_m), min(-lb, big_m), force_on)`, an infinite bound counts as `big_m`, so `big_m` limits the flux that a reaction can carry while it counts as on. Each row is one run without seed repeats, so Jaccard differences of 1 to 2 % are not attributed to the parameter; this is the size of the spread between seeds in [ftinit-determinism.md](ftinit-determinism.md), which uses a different setup (Human-GEM v2.0.0-38, DLD1, `big_m=100`, escalation schedule). Times are the wall clock of the MILP call and of the whole `ftinit` call, without the model preparation (26 min for the scaled prep without tasks).

### ftINIT MILP `mip_gap` (single step-0 solve, `big_m=1000`, `force_on=0.1`)

| `mip_gap` | time (s) | objective | rel.obj.gap | Jaccard vs tightest |
|--------:|---------:|----------:|------------:|--------------------:|
| 0.0002 | 24 | 45954 | ref | ref |
| 0.001 | 24 | 45949 | +0.0001 | 0.9976 |
| 0.003 | 24 | 45831 | +0.0027 | 0.9926 |
| 0.01 | 24 | 45789 | +0.0036 | 0.9908 |
| 0.03 | 25 | 44705 | +0.0272 | 0.9649 |
| 0.1 | 24 | 44647 | +0.0284 | 0.9663 |

The solve time is flat across the gap at 24 to 25 s. `mip_gap=0.001` is within 0.0001 of the tightest objective, and the reaction set drops below Jaccard 0.97 from 0.03. A named series such as `1+1` ignores `mip_gap` and `mip_gap_abs`, because every step runs its own schedule of MILP runs; the setting acts on a step without a schedule, such as this step-0 solve.

### ftINIT MILP `big_m` (`mip_gap=0.001`, `force_on=0.1`)

| `big_m` | time (s) | rel.obj.gap | Jaccard vs `big_m=1000` | Jaccard vs `big_m=100` |
|------:|---------:|------------:|----------------------:|---------------------:|
| 1000 | 24 | ref | ref | 0.985 |
| 500 | 24 | +0.0002 | 0.983 | 0.990 |
| 250 | 26 | −0.0001 | 0.986 | 0.985 |
| 100 | 24 | −0.0001 | 0.985 | ref |
| 50 | 24 | −0.0003 | 0.988 | 0.987 |
| 25 | 25 | −0.0003 | 0.987 | 0.991 |
| 10 | 23 | −0.0002 | 0.988 | 0.990 |

In the single step-0 solve every `big_m` from 10 to 1000 was feasible, took the same time and reached the same objective within 0.0003. The reaction sets differ by 1 to 2 % between any two values, which is the size of the difference between equivalent solutions. The caps that matter appear in the staged pipeline.

### ftINIT MILP `force_on` (`mip_gap=0.001`, `big_m=1000`)

| `force_on` | time (s) | rel.obj.gap | Jaccard vs 0.1 |
|---------:|---------:|------------:|---------------:|
| 0.1 | 24 | ref | ref |
| 0.02 | 25 | −0.0002 | 0.987 |
| 0.05 | 25 | −0.0002 | 0.989 |
| 0.2 | 25 | −0.0002 | 0.992 |
| 0.5 | 25 | −0.0000 | 0.987 |

`force_on` (minimum flux for a reaction to count as "on") changes the model through the on/off constraint; the reaction set varied little (Jaccard ≥0.987) and the objective moved little. The default is `force_on=0.1`.

### Prep scaling by `rescaleModelForINIT` (`max_stoich_diff`, scaling on or off; `mip_gap=0.001`, step-0 solve)

| config | time (s), `big_m=1000` | rel.obj.gap | Jaccard vs scaled `msd=25`, `big_m=1000` | time (s), `big_m=100` | rel.obj.gap | Jaccard vs scaled `msd=25`, `big_m=1000` |
|--------|---------:|------------:|-------------------------:|---------:|------------:|-------------------------:|
| scale on, `msd=25` | 25 | ref | ref | 25 | +0.0001 | 0.986 |
| `msd=10` | 26 | +0.0021 | 0.991 | 24 | +0.0020 | 0.989 |
| `msd=50` | 25 | +0.0031 | 0.983 | 25 | +0.0031 | 0.983 |
| `msd=100` | 26 | +0.0048 | 0.980 | 25 | +0.0049 | 0.980 |
| scale off | 30 | −0.0050 | 0.984 | 25 | −0.0044 | 0.983 |

The reference row (scale on, msd=25, `big_m=1000`) comes from different runs than the same-named row of the `mip_gap` and `big_m` tables. The scale runs prepare the model unscaled and then call `rescale_for_init` with a 600 s limit; the step-0 runs use `prep(scale=True)` with a 900 s limit. The two runs reach objectives of 45539.6 and 45949.2 and share Jaccard 0.983. Within this table every Jaccard value is against the first row, including the `big_m=100` columns.

The single step-0 solve was feasible with and without scaling at both `big_m` values, and `max_stoich_diff` 10 to 100 stayed within Jaccard 0.98 of `max_stoich_diff=25`. In the full staged pipeline, scaling and the cap interact:

| config (full pipeline, `time_limit=600`) | result |
|-----------------------------------|--------|
| scale on, `big_m=1000` | feasible, 83 s |
| scale off, `big_m=1000` | feasible, 157 s, 7264 reactions, Jaccard 0.969 vs scale on |
| scale off, `big_m=100` | infeasible (no usable solution after 30 s) |
| scale on, `big_m=25` | infeasible (no usable solution after 30 s) |

With the default `big_m=1000` the pipeline is feasible without scaling. With a cap of 100 and no scaling, or a cap of 25 with scaling, the run stops after 30 s with `ftINIT MILP produced no usable solution (status: infeasible)`. The recommended setting is scaling on (`max_stoich_diff=25`, RAVEN's setting): the pipeline took 83 s with scaling and 157 s without it in these single runs. It is not needed for feasibility at `big_m=1000`.

The calibration gives `big_m=1000`, `force_on=0.1` and scaling on (`max_stoich_diff=25`); in a step-0 solve `mip_gap=0.001` is within 0.0001 of the tightest objective. A named series caps each scheduled run by its own limit (runs of 120 s, 5000 s and 5 s); `time_limit` lowers that cap, and the full-pipeline runs here used `time_limit=600`.

### ftINIT full pipeline (`ftinit`, series='1+1', no-task scaled prep, `time_limit=600s`)

| config | time (s) | `n_kept` | Jaccard vs `big_m=1000` |
|--------|---------:|-------:|---------------------:|
| `big_m=1000`, three runs | 83, 83, 84 | 7312 | ref (1.000 between the runs) |
| `big_m=500` | 83 | 7306 | 0.980 |
| `big_m=250` | 117 | 7323 | 0.978 |
| `big_m=100`, two runs | 117, 118 | 7324 | 0.981 |
| `big_m=50` | 82 | 7325 | 0.982 |
| `big_m=25` | 30 | infeasible | none |

The runs were started with different `mip_gap` values: 0.001, 0.003 and 0.01 at `big_m=1000`, 0.001 and 0.003 at `big_m=100`, and 0.003 at the other caps. Rows that differ in `mip_gap` or `mip_gap_abs` are repeats of one configuration, because a named series such as `1+1` ignores both: every step runs its own schedule of MILP runs. The three `big_m=1000` runs give the same 7312 reactions in 83, 83 and 84 s with the default `mip_gap_abs=10`, and in 85, 84 and 81 s with `mip_gap_abs=None`. The `mip_gap` conclusions of this study rest on the step-0 table.

`big_m` from 50 to 1000 gave feasible runs of 81 to 119 s without a trend and reaction sets that differ by 2 % from the default. Several caps have repeats: `big_m=1000` has six runs (81 to 85 s), `big_m=250` two (117 s, and 114 s without `mip_gap_abs`), `big_m=100` three (117, 118 and 119 s) and `big_m=50` two (82 s and 81 s); `big_m=500` and `big_m=25` are single runs. Below 50 the staged pipeline can become infeasible; 25 was infeasible here. The default is `big_m=1000`, the cap that RAVEN's `ftINITInternalAlg` uses (`bigMCap`). Lower caps reduce the flux that a kept reaction can carry and showed no measured gain.

---

## Robustness to degraded transcriptomics (task layer always on)

Measured with `big_m=100` (scaled prep) on an earlier Human-GEM state than the clean-data runs, HCT116, with the task layer on, so its reaction counts and Jaccard values are not comparable with the no-task numbers of the clean-data calibration.

The metabolic-task and gap-fill layer is held fixed; only the expression input is degraded. `frac` is the fraction of the essential tasks that the extracted model performs (`check_tasks`); `Jaccard` is the reaction-set overlap with the clean-data model.

| input | n_rxns | tasks pass | frac | Jaccard vs clean |
|-------|-------:|-----------:|-----:|-----------------:|
| clean | 7777 | 69/69 | 1.000 | ref |
| dropout 50 % | 5968 | 67/69 | 0.971 | 0.713 |
| dropout 70 % | 5113 | 68/69 | 0.986 | 0.594 |
| noise σ=1.0 | 7812 | 69/69 | 1.000 | 0.952 |
| noise σ=2.0 | 7768 | 69/69 | 1.000 | 0.919 |
| downsample 50 % | 6765 | 68/69 | 0.986 | 0.815 |
| downsample 70 % | 6123 | 68/69 | 0.986 | 0.728 |

Dropout sets genes to 0 (score −5), noise multiplies levels by `exp(N(0,σ))`, and downsampling drops genes (they receive `no_gene_score`).

Findings:

* Multiplicative expression noise changed the model little (Jaccard 0.92–0.95, size stable, all tasks pass). Sparsity changed it far more: 50 % dropout reduced the reaction set to 0.71 Jaccard (7777→5968 reactions) and 70 % to 0.59.
* Sparsity shrinks the model toward the task-essential core. Missing or zeroed genes remove the expression evidence for a reaction, and the task layer adds back only what tasks require, so sparse input yields smaller, more generic models. Dropout (−5) shrank the model more than downsampling (−2).
* With the task layer, `frac` stayed ≥0.97 and dipped to 67–68/69 under heavy sparsity: the bounded gap-fill plus the post-hoc low-score-gene pruning occasionally leave 1–2 essential tasks unsatisfied. The lever sweep at 70 % dropout below tests whether `no_gene_score` or `force_on` recovers these tasks.
* Run time tracks damage. Dropout runs are slowest (more broken tasks, more gap-fill); noise runs take little run time.

The gap-fill MILP must be bounded (`mip_gap`/`time_limit`). Unbounded, severe degradation (which breaks many tasks at once) makes it solve a hard min-cost MILP per broken task to proven optimality, observed to run >75 min for one 90 %-dropout model. With the bound it returns a near-optimal fill quickly.

### Levers at 70 % dropout

| config | n_rxns | frac | Jaccard vs clean |
|--------|-------:|-----:|-----------------:|
| default (`no_gene_score=−2`, `force_on=0.1`) | 5113 | 0.986 | 0.594 |
| `no_gene_score=−1.0` | 5110 | 0.986 | 0.593 |
| `no_gene_score=−0.5` | 5128 | 0.986 | 0.593 |
| `force_on=0.2` | 5159 | 0.986 | 0.600 |

No lever recovered the drift: Jaccard stayed ~0.59 across all settings, for two reasons.

* The information that dropout destroys is gone. No scoring or connectivity setting reconstructs the missing expression evidence, and no parameter setting compensates for sparse input.
* `no_gene_score` governs only reactions whose genes are absent from the data, which is the downsampling failure mode. Dropout leaves genes present with a zero level (scored −5), so `no_gene_score` has nothing to act on under dropout. For missing-data sparsity, `no_gene_score` is a lever: a less-negative value keeps more unmeasured reactions and grows the model back toward clean.

The robustness levers that matter are structural and not numeric: the task and gap-fill layer (functional regardless of input quality) and a bounded gap-fill MILP (tractable). For missing-gene sparsity, `no_gene_score` trades model size against confidence. For noise, no parameter change is needed. No parameter restores fidelity lost to dropout; the loss is a property of the data and not of the pipeline.

---

## Gene-scoring constants

Expression values become gene scores through

```
score = clip(factor × ln(level / reference), min_score, max_score)
```

with `factor=5.0`, `max_score=10.0`, `min_score=-5.0` on both sides. The logarithm is natural (base e) in `init/score.py` and in RAVEN's `scoreModel`.

The constants are unattributed. The source of each implementation cites no paper for them, and the one candidate reference that has been suggested (a 2012 paper describing mCADRE) uses categorical scoring, which differs from this continuous log-ratio, so it is not the origin. They are RAVEN's own numbers with no literature source. Both implementations agree, so there is nothing to reconcile; the values rest on convention, with no evidence behind them.

## Cross-solver portability

The genome-scale solver comparison (Gurobi, HiGHS, GLPK) is in [init-solver-benchmark.md](init-solver-benchmark.md), and CI parameterised over installed MILP backends is in [tests/test_init_solvers.py](https://github.com/CompMetEng/raven-toolbox/blob/develop/tests/test_init_solvers.py). For Human-GEM HCT116 with one run per solver, Gurobi completes the pipeline in 92 s. The 83 s of the full-pipeline table times the `ftinit` call alone, while the solver timing also includes loading the prep pickle and scoring the reactions, and its cap is 900 s against 600 s, which affects the 5000 s runs of the schedule, while the 120 s and 5 s runs stay below both caps. Neither run reaches its limit and both keep 7312 reactions; GLPK completes in 2182 s with time-limited incumbents (Jaccard 0.892 against Gurobi); HiGHS through optlang's `scipy` interface fails because it handles continuous variables only. Toy-scale correctness is portable (Gurobi and GLPK give identical verdicts on the unit-test networks), so local development works without a Gurobi licence.

---

## Reproducing

```bash
python scripts/analyze_init_params.py    --cell HCT116 --sweeps ftinit_milp,prep_scale,ftinit_full
python scripts/analyze_init_robustness.py --cell HCT116 --algo ftinit
```

Both reuse the cached Human-GEM preps from the validation run ([docs/humangem-validation.md](humangem-validation.md)) and are resumable.
