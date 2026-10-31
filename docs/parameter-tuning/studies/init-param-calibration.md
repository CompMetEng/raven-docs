# ftINIT parameter calibration & input-robustness

Empirical study of raven-toolbox's ftINIT parameters on a genome-scale model (Human-GEM,
Hart2015 / HCT116). Two questions:

1. **Calibration**: on clean data, which parameter values give the best speed/quality
   trade-off? (`scripts/analyze_init_params.py`)
2. **Robustness**: with the task layer always on (it is part of the pipeline, not a
   variable), how does degrading the *transcriptomics input* affect the model, and which
   parameters keep it functional and stable? (`scripts/analyze_init_robustness.py`)

Both scripts are resumable and reusable on any model/dataset; the numbers below are HCT116. The clean-data calibration uses the per-reaction big-M cap `big_m` (Human-GEM `38567ab8`). The robustness measurements used `big_m=100` and an earlier Human-GEM state whose commit is not recorded, so the two sets of numbers do not share a baseline.
"Jaccard" is reaction-set overlap with the reference (tightest setting / clean data); for
a model-extraction tool the reaction set is the product, and a MIP gap bounds only the
*objective*, so set-stability is tracked separately.

---

## 1. Clean-data calibration

Measurements in this section: Human-GEM commit `38567ab8` (v2.1.1 plus 15 commits), HCT116 column of Hart2015, raven-toolbox commit `94f3940`, Gurobi 13.0.1, 4 cores. The model after removing drug reactions, amino-acid triplet reactions and the duplicate complex I reaction has 11265 reactions; the scaled merged model that the MILP sees has 6657 reactions. `big_m` is the cap on the per-reaction big-M: each scored reaction gets `max(min(ub, big_m), min(-lb, big_m), force_on)`, an infinite bound counts as `big_m`, so `big_m` limits the flux that a reaction can carry while it counts as on. Each row is one run without seed repeats, so Jaccard differences of 1 to 2 % are not attributed to the parameter; this is the size of the spread between seeds in [ftinit-determinism.md](ftinit-determinism.md), which uses a different setup (Human-GEM v2.0.0-38, DLD1, `big_m=100`, escalation schedule). Times are the wall clock of the MILP call and of the whole `ftinit` call, without the model preparation (26 min for the scaled prep without tasks).

### ftINIT MILP: `mip_gap` (single step-0 solve, `big_m=1000`, `force_on=0.1`)

| `mip_gap` | time (s) | objective | rel.obj.gap | Jaccard vs tightest |
|--------:|---------:|----------:|------------:|--------------------:|
| 0.0002 | 24 | 45954 | ref | ref |
| 0.001 | 24 | 45949 | +0.0001 | 0.9976 |
| 0.003 | 24 | 45831 | +0.0027 | 0.9926 |
| 0.01 | 24 | 45789 | +0.0036 | 0.9908 |
| 0.03 | 25 | 44705 | +0.0272 | 0.9649 |
| 0.1 | 24 | 44647 | +0.0284 | 0.9663 |

The solve time is flat across the gap at 24 to 25 s. `mip_gap=0.001` is within 0.0001 of the tightest objective, and the reaction set drops below Jaccard 0.97 from 0.03. A named series such as `1+1` ignores `mip_gap` and `mip_gap_abs`, because every step runs its own schedule of MILP runs; the setting acts on a step without a schedule, such as this step-0 solve.

### ftINIT MILP: `big_m` (`mip_gap=0.001`, `force_on=0.1`)

| `big_m` | time (s) | rel.obj.gap | Jaccard vs `big_m=1000` | Jaccard vs `big_m=100` |
|------:|---------:|------------:|----------------------:|---------------------:|
| 1000 | 24 | ref | ref | 0.985 |
| 500 | 24 | +0.0002 | 0.983 | 0.990 |
| 250 | 26 | −0.0001 | 0.986 | 0.985 |
| 100 | 24 | −0.0001 | 0.985 | ref |
| 50 | 24 | −0.0003 | 0.988 | 0.987 |
| 25 | 25 | −0.0003 | 0.987 | 0.991 |
| 10 | 23 | −0.0002 | 0.988 | 0.990 |

In the single step-0 solve every `big_m` from 10 to 1000 is feasible, takes the same time and reaches the same objective within 0.0003. The reaction sets differ by 1 to 2 % between any two values, which is the size of the difference between equivalent solutions. The caps that matter appear in the staged pipeline (below).

### ftINIT MILP: `force_on` (`mip_gap=0.001`, `big_m=1000`)

| `force_on` | time (s) | rel.obj.gap | Jaccard vs 0.1 |
|---------:|---------:|------------:|---------------:|
| 0.1 | 24 | ref | ref |
| 0.02 | 25 | −0.0002 | 0.987 |
| 0.05 | 25 | −0.0002 | 0.989 |
| 0.2 | 25 | −0.0002 | 0.992 |
| 0.5 | 25 | −0.0000 | 0.987 |

`force_on` (minimum flux for a reaction to count as "on") changes the model through the on/off constraint, but the reaction set is insensitive (Jaccard ≥0.987) and the objective hardly moves. Default `force_on=0.1`.

### prep scaling: `rescaleModelForINIT` `max_stoich_diff` and on/off (`mip_gap=0.001`, step-0 solve)

| config | time (s), `big_m=1000` | rel.obj.gap | Jaccard vs scaled `msd=25`, `big_m=1000` | time (s), `big_m=100` | rel.obj.gap | Jaccard vs scaled `msd=25`, `big_m=1000` |
|--------|---------:|------------:|-------------------------:|---------:|------------:|-------------------------:|
| scale on, `msd=25` | 25 | ref | ref | 25 | +0.0001 | 0.986 |
| `msd=10` | 26 | +0.0021 | 0.991 | 24 | +0.0020 | 0.989 |
| `msd=50` | 25 | +0.0031 | 0.983 | 25 | +0.0031 | 0.983 |
| `msd=100` | 26 | +0.0048 | 0.980 | 25 | +0.0049 | 0.980 |
| scale off | 30 | −0.0050 | 0.984 | 25 | −0.0044 | 0.983 |

The reference row (scale on, msd=25, `big_m=1000`) comes from different runs than the same-named row of the `mip_gap` and `big_m` tables. The scale runs prepare the model unscaled and then call `rescale_for_init` with a 600 s limit; the step-0 runs use `prep(scale=True)` with a 900 s limit. The two runs reach objectives of 45539.6 and 45949.2 and share Jaccard 0.983. Within this table every Jaccard value is against the first row, including the `big_m=100` columns.

The single step-0 solve is feasible with and without scaling at both `big_m` values, and `max_stoich_diff` 10 to 100 stay within Jaccard 0.98 of `max_stoich_diff=25`. The full staged pipeline is where scaling and the cap interact:

| config (full pipeline, `time_limit=600`) | result |
|-----------------------------------|--------|
| scale on, `big_m=1000` | feasible, 83 s |
| scale off, `big_m=1000` | feasible, 157 s, 7264 reactions, Jaccard 0.969 vs scale on |
| scale off, `big_m=100` | infeasible (no usable solution after 30 s) |
| scale on, `big_m=25` | infeasible (no usable solution after 30 s) |

With the default `big_m=1000` the pipeline is feasible without scaling. With a cap of 100 and no scaling, or a cap of 25 with scaling, the run stops after 30 s with `ftINIT MILP produced no usable solution (status: infeasible)`. The recommended setting is scaling on (`max_stoich_diff=25`, RAVEN's setting): the pipeline took 83 s with scaling and 157 s without it in these single runs. It is not needed for feasibility at `big_m=1000`.

**Calibration summary:** `big_m=1000`, `force_on=0.1`, scaling on (`max_stoich_diff=25`); in a step-0 solve `mip_gap=0.001` is within 0.0001 of the tightest objective. A named series caps each scheduled run by its own limit (runs of 120 s, 5000 s and 5 s); `time_limit` lowers that cap, and the full-pipeline runs here used `time_limit=600`.

### ftINIT full pipeline (`ftinit`, series='1+1', no-task scaled prep, `time_limit=600s`)

| config | time (s) | `n_kept` | Jaccard vs `big_m=1000` |
|--------|---------:|-------:|---------------------:|
| **`big_m=1000`**, three runs | 83, 83, 84 | 7312 | ref (1.000 between the runs) |
| `big_m=500` | 83 | 7306 | 0.980 |
| `big_m=250` | 117 | 7323 | 0.978 |
| `big_m=100`, two runs | 117, 118 | 7324 | 0.981 |
| `big_m=50` | 82 | 7325 | 0.982 |
| `big_m=25` | 30 | infeasible | none |

The runs were started with different `mip_gap` values: 0.001, 0.003 and 0.01 at `big_m=1000`, 0.001 and 0.003 at `big_m=100`, and 0.003 at the other caps. Rows that differ in `mip_gap` or `mip_gap_abs` are repeats of one configuration, because a named series such as `1+1` ignores both: every step runs its own schedule of MILP runs. The three `big_m=1000` runs give the same 7312 reactions in 83, 83 and 84 s with the default `mip_gap_abs=10`, and in 85, 84 and 81 s with `mip_gap_abs=None`. The `mip_gap` conclusions of this study rest on the step-0 table.

`big_m` from 50 to 1000 gives feasible runs of 81 to 119 s without a trend and reaction sets that differ by 2 % from the default. Several caps have repeats: `big_m=1000` has six runs (81 to 85 s), `big_m=250` two (117 s, and 114 s without `mip_gap_abs`), `big_m=100` three (117, 118 and 119 s) and `big_m=50` two (82 s and 81 s); `big_m=500` and `big_m=25` are single runs. Below 50 the staged pipeline can become infeasible; 25 is infeasible here. → **Default `big_m=1000`**, the cap that RAVEN's `ftINITInternalAlg` uses (`bigMCap`); lower caps reduce the flux that a kept reaction can carry and show no measured gain.

---

## 2. Robustness to degraded transcriptomics (task layer always on)

Measured with `big_m=100` (scaled prep) on an earlier Human-GEM state than the clean-data runs, HCT116, with the task layer on, so its reaction counts and Jaccard values are not comparable with the no-task numbers of the clean-data calibration.

The metabolic-task + gap-fill layer is held fixed; only the expression input is degraded.
`frac` = fraction of the essential tasks the extracted model performs (`check_tasks`);
`Jaccard` = reaction-set overlap with the clean-data model.

| input | n_rxns | tasks pass | frac | Jaccard vs clean |
|-------|-------:|-----------:|-----:|-----------------:|
| **clean** | 7777 | 69/69 | 1.000 | ref |
| dropout 50% | 5968 | 67/69 | 0.971 | **0.713** |
| dropout 70% | 5113 | 68/69 | 0.986 | **0.594** |
| noise σ=1.0 | 7812 | 69/69 | 1.000 | 0.952 |
| noise σ=2.0 | 7768 | 69/69 | 1.000 | 0.919 |
| downsample 50% | 6765 | 68/69 | 0.986 | 0.815 |
| downsample 70% | 6123 | 68/69 | 0.986 | 0.728 |

(dropout = genes set to 0 → score −5; noise = ×`exp(N(0,σ))`; downsample = genes dropped →
`no_gene_score`.)

**Findings:**

* **The model is robust to noise but sensitive to sparsity.** Multiplicative expression noise barely changes
  the model (Jaccard 0.92–0.95, size stable, all tasks pass). Sparsity is far more damaging:
  50% dropout already drops the reaction set to **0.71 Jaccard** (and shrinks 7777→5968), 70%
  to **0.59**.
* **Sparsity shrinks the model toward the task-essential core.** Missing/zeroed genes remove
  the expression evidence for a reaction; the task layer only adds back what tasks require, so
  sparse input yields smaller, more "generic" models. Dropout (−5) is harsher than
  downsampling (−2).
* **Functionality is largely but not perfectly preserved.** With the task layer, `frac` stays
  ≥0.97, but dips to 67–68/69 under heavy sparsity, i.e. the bounded gap-fill plus the
  post-hoc low-score-gene pruning occasionally leave 1–2 essential tasks unsatisfied. (See the
  lever sweep below for whether `no_gene_score`/`force_on` recover them.)
* **Cost tracks damage.** Dropout runs are slowest (more broken tasks → more gap-fill);
  noise is cheap.

> **Tractability note (a parameter that prevents failure):** the gap-fill MILP must be bounded
> (`mip_gap`/`time_limit`). Unbounded, severe degradation (which breaks many tasks at once)
> makes it solve a hard min-cost MILP per broken task to proven optimality, observed to run
> >75 min for one 90%-dropout model. With the bound it returns a near-optimal fill quickly.

### Levers at dropout 70%: which parameter best stabilises the model?

| config | n_rxns | frac | Jaccard vs clean |
|--------|-------:|-----:|-----------------:|
| default (`no_gene_score=−2`, `force_on=0.1`) | 5113 | 0.986 | 0.594 |
| `no_gene_score=−1.0` | 5110 | 0.986 | 0.593 |
| `no_gene_score=−0.5` | 5128 | 0.986 | 0.593 |
| `force_on=0.2` | 5159 | 0.986 | 0.600 |

**No lever recovers the drift**: Jaccard stays ~0.59 across all settings. Two reasons,
both informative:

* The information dropout destroys is gone; no scoring or connectivity knob reconstructs
  the missing expression evidence. No parameter setting compensates for sparse input.
* `no_gene_score` is the wrong knob *for dropout specifically*: dropout leaves genes
  *present but zero* (scored −5), whereas `no_gene_score` only governs reactions whose genes
  are **absent** from the data, i.e. the *downsampling* failure mode. So `no_gene_score` is
  a meaningful lever for missing-data sparsity (a less-negative value keeps more
  unmeasured reactions, growing the model back toward clean), but it has nothing to act on
  under dropout.

**Practical takeaway.** The robustness levers that matter are *structural*, not numeric: the
task + gap-fill layer (keeps the model functional regardless of input quality) and a bounded
gap-fill MILP (keeps it tractable). For *missing*-gene sparsity specifically, `no_gene_score`
trades model size against confidence. For noise, defaults are already robust. No parameter
restores fidelity lost to dropout; that is a property of the data, not the pipeline.

---

## 3. The gene-scoring constants have no confirmed source

Expression values become gene scores through

```
score = clip(factor × ln(level / reference), min_score, max_score)
```

with `factor=5.0`, `max_score=10.0`, `min_score=-5.0` on both sides. The
logarithm is natural, not base 2, in `init/score.py` and in RAVEN's `scoreModel`
alike.

The constants themselves are unattributed. Neither implementation's source cites
a paper for them, and the one candidate reference that has been suggested (a
2012 paper describing mCADRE) uses categorical scoring rather than this
continuous log-ratio, so it is not the origin. They are RAVEN's own numbers with
no literature anchor behind them. Since both implementations agree there is
nothing to reconcile, but the values rest on convention rather than evidence.

## 4. Cross-solver portability

See [init-solver-benchmark.md](init-solver-benchmark.md) for the genome-scale
solver comparison (Gurobi/HiGHS/GLPK) and [tests/test_init_solvers.py](https://github.com/CompMetEng/raven-toolbox/blob/develop/tests/test_init_solvers.py)
for CI parameterised over installed MILP backends. Summary (Human-GEM HCT116, one run per solver): Gurobi completes the pipeline in 92 s. The 83 s of the full-pipeline table times the `ftinit` call alone, while the solver timing also includes loading the prep pickle and scoring the reactions, and its cap is 900 s instead of 600 s, which affects the 5000 s runs of the schedule, while the 120 s and 5 s runs stay below both caps. Neither run reaches its limit and both keep 7312 reactions; GLPK completes in 2182 s with time-limited incumbents (Jaccard 0.892 against Gurobi); HiGHS through optlang's `scipy` interface fails because it handles continuous variables only. Toy-scale correctness is portable (Gurobi + GLPK give identical verdicts on the unit-test networks), so local development works without a Gurobi licence.

---

## Reproducing

```bash
python scripts/analyze_init_params.py    --cell HCT116 --sweeps ftinit_milp,prep_scale,ftinit_full
python scripts/analyze_init_robustness.py --cell HCT116 --algo ftinit
```

Both reuse the cached Human-GEM preps from the validation run
([docs/humangem-validation.md](humangem-validation.md)) and are resumable.
