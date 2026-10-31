# Parameter tuning

RAVEN, both the MATLAB toolbox and raven-toolbox (Python), ships many functions with numerical defaults: solver tolerances, cut-offs, iteration limits, literature constants. [Tuned parameter defaults](../tuned-parameters.md) gives the short version of every one of them: current value, one-line reason, grouped by capability. The detail behind that page comprises the methodology for evaluating a default, the full write-up for every parameter that had a dedicated measurement campaign, and the quicker per-function working notes (**benchmarks**) produced along the way.

## Evaluation methodology

A default value is well-chosen when a user who does not read the docstring gets a correct and useful result for the most common case.

**MATLAB and Python parity.** The defaults of both implementations were not systematically validated from the start. MATLAB RAVEN's defaults were often chosen by trial and error, copied from earlier tools, or never reconsidered, and raven-toolbox inherited a mix of ported MATLAB values and upstream (cobrapy) conventions. An existing default in either toolbox is a prior: it reflects years of practical use or a well-tested upstream library, and it is not necessarily correct. Where the two implementations differ, the response is to run both and measure; the value that came first is not assumed to be correct.

The following criteria apply in rough priority order:

1. **Empirical correctness on real models.** Run the function with the candidate default on at least one large model (Yeast9, Human-GEM) and one small model (iJO1366 or similar). Compare the result against a known-good answer (a published reconstruction, a literature flux distribution, a validated gene-essentiality set). The default must produce a result that is meaningfully better than the alternatives tested, or at least no worse.
2. **Sensitivity envelope.** Vary the parameter by ±1 order of magnitude (or ±50 % for non-log-scale values) and measure the change in the result. If the output is insensitive across the range, the exact default value matters little; document that. If the output is highly sensitive, the default must lie in a plateau region (neither too loose nor too tight) and must be documented with the sensitivity profile.
3. **Literature anchor.** Algorithm-specific numerical parameters should match the value used in the original paper or the most-cited open-source implementation (cobrapy, COBRA Toolbox). Agreement with the literature is corroborating evidence and is not authority.
4. **Cross-implementation check.** Where a raven-toolbox function ports a MATLAB RAVEN function (or vice versa), note what the other side uses. A difference is to be investigated empirically and is not automatically a bug in either implementation.
5. **User expectation alignment.** Prefer values that match what a competent user would supply without thinking (for example `verbose=True` for a long-running MILP, `sort_ids=False` for round-trip-safe export).
6. **No undocumented `None` behaviour.** `None` or empty defaults are acceptable for optional features, but any resulting change to algorithmic behaviour must be documented in the fallback.

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

## Homology and KEGG reconstruction

| Study | Covers |
|---|---|
| [Homology cut-off calibration](studies/homology-cutoff-calibration.md) | `min_align_len`, `min_identity`, `max_evalue` in homology-based reconstruction, measured against independent KEGG and OMA ortholog references across a 4-organism relatedness series |
| [KEGG HMM cut-off calibration](studies/kegg-hmm-cutoff-calibration.md) | `cutoff`, `min_score_ratio_ko`, `min_score_ratio_g` in KEGG HMM-based reconstruction, measured against real KEGG gene→KO annotations across 4 organisms |

## Context-specific extraction (ftINIT)

| Study | Covers |
|---|---|
| [ftINIT parameter calibration](studies/init-param-calibration.md) | HCT116 on Human-GEM: `big_m`, `force_on`, stoichiometric scaling, and `mip_gap` in a single step (a named series ignores it) |
| [ftINIT reproducibility](studies/ftinit-determinism.md) | Reproducibility gained with `resolve_ties` and `prove_abs_gap` and the run time they cost on genome-scale Human-GEM |
| [Human-GEM validation vs MATLAB RAVEN](studies/humangem-validation.md) | raven-toolbox's ftINIT output validated against MATLAB RAVEN on Human-GEM across 5 cell lines (Jaccard 0.964–0.988) |

## Benchmarks

Per-function working notes are quicker parameter-by-parameter records produced alongside (and sometimes instead of) a full study, together with the master cross-toolbox to-do list.

| Benchmark | Function(s) |
|---|---|
| [Parameter benchmarks](benchmarks.md) | `fseof`, `remove_genes`, `connect_blocked_reactions`, `fill_gaps_*`, `check_tasks`, `find_task_essential_reactions` |

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
