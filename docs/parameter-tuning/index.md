# Parameter tuning

RAVEN, both the MATLAB toolbox and raven-toolbox (Python), has many functions with numerical defaults: solver tolerances, cut-offs, iteration limits and literature constants. [Tuned parameter defaults](../tuned-parameters.md) lists each of them with its current value and a one-line reason, grouped by capability. The detail behind that list comprises the method for evaluating a default, a study for each parameter with a dedicated measurement campaign, and shorter per-function records (**benchmarks**) for parameters that needed no study of their own.

## Evaluation methodology

A default is well chosen when a user who does not read the docstring gets a correct result for the most common case.

The defaults of the two implementations were not validated systematically when they were set. raven-toolbox took over a mix of ported MATLAB values and upstream (cobrapy) conventions. An existing default in either implementation is a starting point for the evaluation and is not assumed to be correct. Where the two implementations differ, both values are measured; the value that came first has no precedence.

The criteria apply in this order of priority:

1. Empirical correctness on real models. The function runs with each candidate default on at least one large model (yeast-GEM or Human-GEM) and one small model (iJO1366 or similar). The result is compared with a known answer: a published reconstruction, a flux distribution from the literature or a validated gene-essentiality set. The chosen default gives a result that is better than the other candidates or no worse.
2. Sensitivity envelope. The parameter is varied by ±1 order of magnitude, or by ±50 % for a value on a linear scale, and the change in the result is measured. When the result does not change across the range, the exact value matters little, and the documentation says so. When the result changes steeply, the default lies on a plateau between too loose and too tight, and the documentation gives the sensitivity profile.
3. Literature anchor. A numerical parameter of an algorithm matches the value in the original paper or in the most-cited open-source implementation (cobrapy, COBRA Toolbox). Agreement with the literature corroborates a value and does not determine it.
4. Cross-implementation check. Where a raven-toolbox function ports a MATLAB RAVEN function, or the reverse, the documentation states the value of the other implementation. A difference is measured and is not assumed to be a bug in either implementation.
5. Alignment with user expectation. A default matches the value a user would supply without thinking about it, for example `verbose=True` for a long-running mixed-integer linear program (MILP) and `sort_ids=False` for an export that reads back unchanged.
6. Documented `None` behaviour. A default of `None` or empty is acceptable for an optional feature, and any change of algorithmic behaviour that follows from it is documented with the fallback.

### Evaluation workflow per parameter

```
1. Read the current docstring: does it explain *why* this value?
2. Identify candidate values: current default, the other implementation's
   default (if any), paper value (if any), and at least two plausible
   alternatives (e.g. 1 order of magnitude up/down).
3. Run all candidates on iJO1366 (fast) and Yeast9 or Human-GEM (realistic).
   Record: result quality metric, wall time, any solver/numerical warnings.
4. Compute the sensitivity envelope: how much does the result metric change
   across the candidate range? If the function is a reconstruction method,
   use a curated gene-essentiality set or a held-out growth condition as the
   benchmark.
5. Record the finding, with the measurement it rests on.
6. If a change is warranted: state the proposed new value, quote the test
   that supports it, and update the default and its docstring.
```

Yeast9 in the checklist is version 9 of yeast-GEM.

## Homology and KEGG reconstruction

| Study | Parameters and measurement |
|---|---|
| [Homology cut-off calibration](studies/homology-cutoff-calibration.md) | `min_align_len`, `min_identity` and `max_evalue` of homology-based reconstruction, measured for 4 organisms of increasing distance against KEGG KO annotations (partly derived from sequence similarity); `min_identity` also against the OMA reference, independent of BLAST |
| [KEGG HMM cut-off calibration](studies/kegg-hmm-cutoff-calibration.md) | `cutoff`, `min_score_ratio_ko` and `min_score_ratio_g` of KEGG reconstruction with hidden Markov models (HMMs), measured against the KEGG Orthology (KO) annotations of the genes of 4 organisms |

## Context-specific extraction (ftINIT)

| Study | Parameters and measurement |
|---|---|
| [ftINIT parameter calibration and input robustness](studies/init-param-calibration.md) | `big_m`, `force_on`, stoichiometric scaling and `mip_gap` on Human-GEM with HCT116 expression; `mip_gap` acts on a single step, and a named series such as `1+1` ignores it |
| [ftINIT reproducibility with `resolve_ties` and `prove_abs_gap`](studies/ftinit-determinism.md) | Reproducibility of the extracted model with `resolve_ties` and `prove_abs_gap`, and the run time they add on Human-GEM |
| [Human-GEM cell-type model validation against RAVEN](studies/humangem-validation.md) | ftINIT models of raven-toolbox compared with those of MATLAB RAVEN on Human-GEM for 5 cell lines (Jaccard index 0.964–0.988) |
| [ftINIT on different solvers](studies/init-solver-benchmark.md) | Benchmark of the completion, run time and extracted reactions of ftINIT on Human-GEM with each solver interface |

## Flux sampling

| Study | Parameters and measurement |
|---|---|
| [Flux sampling convergence and settings](studies/sampling-convergence-calibration.md) | `thinning`, `n_samples` and convergence of artificially centered hit-and-run (ACHR) and coordinate hit-and-run with rounding (CHRR) sampling on e_coli_core and yeast-GEM, by autocorrelation and R-hat; two random-objective settings compared with RAVEN MATLAB |

## Benchmarks

| Benchmark | Functions |
|---|---|
| [Benchmarks of `fseof`, `remove_genes` and other defaults](benchmarks.md) | `fseof`, `remove_genes`, `connect_blocked_reactions`, `fill_gaps_*`, `check_tasks` |

```{toctree}
:hidden:

../tuned-parameters
benchmarks
```

```{toctree}
:hidden:
:caption: Homology and KEGG reconstruction

studies/homology-cutoff-calibration
studies/kegg-hmm-cutoff-calibration
```

```{toctree}
:hidden:
:caption: Context-specific extraction (ftINIT)

studies/init-param-calibration
studies/ftinit-determinism
studies/humangem-validation
studies/init-solver-benchmark
```

```{toctree}
:hidden:
:caption: Flux sampling

studies/sampling-convergence-calibration
```
