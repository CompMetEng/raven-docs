# Differences in results between functions

The page lists functions that differ between RAVEN and raven-toolbox in the algorithm choice, in the form of the result or in the value of the result. The differences were found by reading the code of both implementations; where a section says a result was not checked, no run compared the two. The list is incomplete: a function that is not listed can behave differently. Candidates that were not compared include `random_sampling`, which replaces both `sampleACHR` and `sampleCHRR`, `remove_duplicate_reactions`, which replaces `contractModel`, and `simplify_model`, which corresponds to `simplifyModel`.

## Metabolic task checking

`checkTasks` and `check_tasks` implement the same task format and the same boundary semantics. `close_boundaries=True` of `check_tasks` corresponds to calling `checkTasks` on `closeModel(model)`; [Metabolic tasks](../guide/tasks.md) describes the options. Identical pass and fail results on a shared input were not checked here.

`checkTasks` starts each task from the original model structure. `check_tasks` applies each task to one model inside a `with model:` block and reverts the changes afterwards. It also saves and restores direct edits of metabolite-constraint bounds. The runtime of the two functions was not compared.

The `getEssential` option of `checkTasks` has no option in `check_tasks`. In RAVEN, `checkTasks` calls `getEssentialRxns` on the model constrained by each task. The function `find_task_essential_reactions` ports this step, so it corresponds to `checkTasks` with `getEssential`, not to `getEssentialRxns` called on a model without a task.

## Gap-filling functions

`fillGaps` in RAVEN selects one of five algorithms with the `algorithm` option: `reference` (default), `fastLP`, `swiftLP`, `gapfillMILP` and `topological`. raven-toolbox has four functions for them, so porting a `fillGaps` call requires choosing a function from this table:

| Purpose | RAVEN algorithm | raven-toolbox function |
|---|---|---|
| Connecting blocked reactions against template models | `fillGaps` (default `'reference'`) | `connect_blocked_reactions` |
| Fast filling of a large candidate set by linear programming (LP) | `fillGaps` with `'fastLP'` and `'swiftLP'` | `fill_gaps_fast_lp` (`variant="fast"` and `variant="swift"`) |
| Filling by mixed-integer linear programming (MILP) with the fewest added reactions that restore growth | `fillGaps` with `'gapfillMILP'` | `fill_gaps_milp` |
| Finding the gaps without filling them | `fillGaps` with `'topological'` | `analyse_topology` |

Further differences:

- `fillGaps` with `useModelConstraints=true` fills so that the constraints of the model hold. `connect_blocked_reactions` has no such mode; its documentation points to `cobra.flux_analysis.gapfill` for that use. `fill_gaps_milp` is the closest function for a growth target.
- `fillGaps` takes a cell array of template models, and the RAVEN functions `gapFillFastLP`, `gapFillMILP` and `gapFillTopological` use only the first template. The four raven-toolbox functions accept several templates.
- `fillGaps` returns `newConnected`, `cannotConnect`, `addedRxns`, `newModel` and `exitFlag`. raven-toolbox returns a `GapFillResult` from `connect_blocked_reactions`, a `FastLPResult` from `fill_gaps_fast_lp`, a `MILPGapFillResult` from `fill_gaps_milp` and a `TopologicalAnalysisResult` from `analyse_topology`. The count `newConnected` is not stable across runs; see [Gap-filling](../guide/gap-filling.md).

The RAVEN functions `canExchange`, `checkProduction` and `getAllSubGraphs` find gaps without filling them. raven-toolbox merges them into `gap_report`, the port of `gapReport`, and has no separate public function for each of them.

## Alternative optima of mixed-integer problems

ftINIT extraction, the reference and MILP gap-filling algorithms and compartment assignment (`assignCompartments` and `assign_compartments`) solve mixed-integer problems that can have several optima of equal objective value. The linear-programming algorithms were not measured for this, and the documentation of `swiftLP` in both implementations calls it stochastic. A solve that stops at its gap or time limit can also end at a different objective value. Two runs can return different reaction sets, and no single exact result is expected.

Measurements of the differences:

- Between implementations: ftINIT models of five cell lines, extracted from the same Human-GEM inputs with RAVEN and raven-toolbox, share Jaccard indices of 0.964 to 0.988 over their reaction sets (see [Human-GEM cell-type model validation against RAVEN](../parameter-tuning/studies/humangem-validation.md)). The template preparation differed between the two runs.
- Between solvers: in the raven-toolbox ftINIT benchmark on Human-GEM with one run per solver, Gurobi extracted 7312 reactions and GLPK 6758 (Jaccard index 0.892). Both main steps of GLPK stopped at the 900 s limit with an unproven incumbent, so the two models differ in objective value as well as in tied optima (see [ftINIT on different solvers](../parameter-tuning/studies/init-solver-benchmark.md)). RAVEN was not run on several solvers in that study.
- Between repeated runs: two repeated raven-toolbox builds at one seed with the default settings differed by 2 reactions. Each build had one run of the final step that stopped at its 5 s wall-clock limit, the presumed and untested cause (see [ftINIT reproducibility with `resolve_ties` and `prove_abs_gap`](../parameter-tuning/studies/ftinit-determinism.md)). RAVEN's `ftINIT` was not run for the effects of seed, thread count and time limit.
- Between thread counts: in raven-toolbox's first ftINIT step without `resolve_ties`, with six seeds, the solutions at `Threads` 1 and 4 for the same seed were 5 to 20 reactions apart, and in 5 of the 6 seeds the two runs reached different objective values (see [ftINIT reproducibility with `resolve_ties` and `prove_abs_gap`](../parameter-tuning/studies/ftinit-determinism.md)).

Compare outputs by the overlap of their reaction sets, for example with the Jaccard index.

`resolveTies` in RAVEN's `ftINIT` and `resolve_ties` in raven-toolbox's `ftinit` are off by default in both. When on, each step keeps the score optimum and picks among the tied solutions in phases: the fewest kept removable reactions, then the lowest summed ID rank of those, then the least total absolute flux, then the least ID-rank-weighted backward flux. The last step of `ftINIT` skips the two flux phases. A step that stops at its time limit keeps the solver's own answer.

In raven-toolbox, runs with `resolve_ties` at the same score optimum returned identical solutions across seeds. The primary solve can still end at a different objective value for a different seed, within the gap and time limits, so the final reaction sets can differ. This was not measured for RAVEN. Without `resolveTies` or `resolve_ties`, the ftINIT MILP can return any of the tied optima.

## Elemental balance results

`getElementalBalance` in RAVEN and `get_elemental_balance` in raven-toolbox check whether each element has the same count on both sides of a reaction. A reaction is unbalanced when the counts were computed and did not match, and the result is unknown when the counts cannot be computed. The two functions use different codes for these results.

`getElementalBalance` returns the numeric field `balanceStructure.balanceStatus` per reaction: 1 for balanced, 0 for unbalanced, -1 for missing information (no formula, or a reaction without metabolites) and -2 for a formula that cannot be parsed. `get_elemental_balance` returns the strings `balanced`, `unbalanced` and `unknown`. It reports `unknown` for a missing formula, for an unparseable formula and for a reaction without metabolites, so the codes -1 and -2 of RAVEN are one result in raven-toolbox.

The two parsers differ for some formulas, so the results differ for some reactions with formulas:

- A polymer formula such as `(C5H8)n` is counted with n equal to 1 in RAVEN. raven-toolbox reports `unknown`.
- RAVEN uses the `inchis` field when `metFormulas` is absent. raven-toolbox does not.
- RAVEN reports a charge balance (`chargeStatus` and `chargeResidual`). `get_elemental_balance` reports elements only.

The comparison used the code only; the functions were not run on a shared model.

## Parsing of gene-reaction rules

The section applies when a RAVEN user takes a model through cobrapy readers in Python. raven-toolbox parses gene-reaction rules (the `grRules` field in RAVEN) with `utils.parse_gr_rule`, which follows the grammar of RAVEN's `parseGrRule`. The function is used in `read_yaml_model`, `read_matlab_model`, `batch_curate` and the functions that copy or build rules, so `G1&G2` is one gene ID there. According to the raven-toolbox changelog, the JSON reader of cobrapy splits `G1&G2` into `G1` and `G2`, and the SBML reader keeps it. This was not checked against cobrapy itself.
