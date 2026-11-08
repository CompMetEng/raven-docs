# Differences in results between functions

A function of RAVEN and its counterpart in raven-toolbox can differ in the algorithm they choose, in the form of the result or in the value of the result. The sections below describe the differences found by reading the code of both implementations. Where a section says that a result was not checked, no run compared the two implementations.

The list is incomplete, and a function that is not listed can behave differently. Candidates that were not compared include `random_sampling`, which replaces both `sampleACHR` and `sampleCHRR`; `remove_duplicate_reactions`, which replaces `contractModel`; and `simplify_model`, which corresponds to `simplifyModel`.

## Metabolic task checking

The functions `checkTasks` and `check_tasks` implement the same task format and the same boundary semantics. The option `close_boundaries=True` of `check_tasks` corresponds to calling `checkTasks` on `closeModel(model)`. [Metabolic tasks](../guide/tasks.md) describes the options. Whether both functions return identical pass and fail results on a shared input was not checked.

`checkTasks` starts each task from the original model structure. `check_tasks` applies each task to one model inside a `with model:` block and reverts the changes afterwards. It also saves and restores direct edits of metabolite-constraint bounds. The runtime of the two functions was not compared.

The option `getEssential` of `checkTasks` has no counterpart option in `check_tasks`. In RAVEN, `checkTasks` calls `getEssentialRxns` on the model constrained by each task, and `find_task_essential_reactions` ports this step. It is the port of `checkTasks` with `getEssential`.

## Gap-filling functions

The function `fillGaps` of RAVEN selects one of five algorithms with the option `algorithm`: `reference` (default), `fastLP`, `swiftLP`, `gapfillMILP` and `topological`. raven-toolbox has four functions for them, so porting a `fillGaps` call means choosing one function from the table.

| Purpose | RAVEN algorithm | raven-toolbox function |
|---|---|---|
| Connecting blocked reactions against template models | `fillGaps` (default `'reference'`) | `connect_blocked_reactions` |
| Fast filling of a large candidate set by linear programming (LP) | `fillGaps` with `'fastLP'` and `'swiftLP'` | `fill_gaps_fast_lp` (`variant="fast"` and `variant="swift"`) |
| Filling by mixed-integer linear programming (MILP) with the fewest added reactions that restore growth | `fillGaps` with `'gapfillMILP'` | `fill_gaps_milp` |
| Finding the gaps without filling them | `fillGaps` with `'topological'` | `analyse_topology` |

The functions differ in three more points.

- `fillGaps` with `useModelConstraints=true` fills so that the constraints of the model hold. `connect_blocked_reactions` has no such mode, and its documentation points to `cobra.flux_analysis.gapfill` for that use. The closest function for a growth target is `fill_gaps_milp`.
- `fillGaps` takes a cell array of template models, but the RAVEN functions `gapFillFastLP`, `gapFillMILP` and `gapFillTopological` use the first template and ignore the rest. The four raven-toolbox functions accept several templates.
- `fillGaps` returns `newConnected`, `cannotConnect`, `addedRxns`, `newModel` and `exitFlag`. raven-toolbox returns a `GapFillResult` from `connect_blocked_reactions`, a `FastLPResult` from `fill_gaps_fast_lp`, a `MILPGapFillResult` from `fill_gaps_milp` and a `TopologicalAnalysisResult` from `analyse_topology`. The count `newConnected` is not stable across runs (see [Gap-filling](../guide/gap-filling.md)).

The RAVEN functions `canExchange`, `checkProduction` and `getAllSubGraphs` find gaps without filling them. raven-toolbox merges them into `gap_report`, the port of `gapReport`, and has no separate public function for each of them.

## Alternative optima of mixed-integer problems

The extraction with ftINIT, the reference and MILP gap-filling algorithms, and the assignment of compartments (`assignCompartments` and `assign_compartments`) solve mixed-integer problems, which can have several optima with the same objective value. The LP algorithms were not measured for this, and the documentation of `swiftLP` in both implementations calls it stochastic. A solve that stops at its gap or time limit can also end at a different objective value. Two runs can therefore return different reaction sets, and no single exact result is expected.

Four measurements quantify the differences.

- **Between implementations.** The ftINIT models of five cell lines, extracted from the same Human-GEM inputs with RAVEN and raven-toolbox, share Jaccard indices of 0.964 to 0.988 over their reaction sets (see [Human-GEM cell-type model validation against RAVEN](../parameter-tuning/studies/humangem-validation.md)). The template preparation differed between the two runs.
- **Between solvers.** In the raven-toolbox ftINIT benchmark on Human-GEM with one run per solver, Gurobi extracted 7312 reactions and GLPK 6758 (Jaccard index 0.892). Both main steps of GLPK stopped at the 900 s limit with an unproven incumbent, so the two models differ in objective value as well as in tied optima (see [ftINIT on different solvers](../parameter-tuning/studies/init-solver-benchmark.md)). RAVEN was not run on several solvers in that study.
- **Between repeated runs.** Two repeated raven-toolbox builds at one seed with the default settings differed by 2 reactions. In each build one run of the final step stopped at its 5 s wall-clock limit, which is the presumed and untested cause (see [ftINIT reproducibility with `resolve_ties` and `prove_abs_gap`](../parameter-tuning/studies/ftinit-determinism.md)). The effects of seed, thread count and time limit were not measured for the `ftINIT` of RAVEN.
- **Between thread counts.** In the first ftINIT step of raven-toolbox without `resolve_ties`, with six seeds, the solutions at `Threads` 1 and 4 for the same seed were 5 to 20 reactions apart. In 5 of the 6 seeds the two runs reached different objective values (see [ftINIT reproducibility with `resolve_ties` and `prove_abs_gap`](../parameter-tuning/studies/ftinit-determinism.md)).

Compare such outputs by the overlap of the reaction sets, for example the Jaccard index.

The option `resolveTies` of the `ftINIT` of RAVEN and `resolve_ties` of the `ftinit` of raven-toolbox are off by default in both. When on, each step keeps the score optimum and selects among the tied solutions in four phases, in this order: the fewest kept removable reactions, the lowest summed ID rank of those, the least total absolute flux and the least backward flux weighted by ID rank. The last step of `ftINIT` skips the two flux phases. A step that stops at its time limit keeps the answer of the solver.

In raven-toolbox, runs with `resolve_ties` at the same score optimum returned identical solutions across seeds. The primary solve can end at a different objective value for a different seed, within the gap and time limits, so the final reaction sets can differ. This was not measured for RAVEN. Without `resolveTies` or `resolve_ties`, the ftINIT MILP can return any of the tied optima.

## Elemental balance results

The functions `getElementalBalance` in RAVEN and `get_elemental_balance` in raven-toolbox check whether each element has the same count on both sides of a reaction. A reaction is unbalanced when the counts were computed and do not match. The result is unknown when the counts cannot be computed. The two functions code these results differently.

The function `getElementalBalance` returns the numeric field `balanceStructure.balanceStatus` per reaction: 1 for balanced, 0 for unbalanced, -1 for missing information (no formula, or a reaction without metabolites) and -2 for a formula that cannot be parsed. The function `get_elemental_balance` returns the strings `balanced`, `unbalanced` and `unknown`. It reports `unknown` for a missing formula, for a formula that cannot be parsed and for a reaction without metabolites, so the codes -1 and -2 of RAVEN are one result in raven-toolbox.

The two parsers parse some formulas differently, so the results differ for some reactions.

- A polymer formula such as `(C5H8)n` is counted with n equal to 1 in RAVEN. raven-toolbox reports `unknown`.
- RAVEN uses the field `inchis` when `metFormulas` is absent. raven-toolbox does not.
- RAVEN reports a charge balance (`chargeStatus` and `chargeResidual`). `get_elemental_balance` reports elements.

The comparison used the code, and the functions were not run on a shared model.

## Parsing of gene-reaction rules

The parsing of rules matters when a RAVEN user takes a model through cobrapy readers in Python. raven-toolbox parses gene-reaction rules (the field `grRules` in RAVEN) with `utils.parse_gr_rule`, which follows the grammar of `parseGrRule` of RAVEN. The function is used in `read_yaml_model`, `read_matlab_model`, `batch_curate` and the functions that copy or build rules, so `G1&G2` is one gene ID there. According to the changelog of raven-toolbox, the JSON reader of cobrapy splits `G1&G2` into `G1` and `G2`, and the SBML reader keeps it as one ID. This was not checked against cobrapy itself.
