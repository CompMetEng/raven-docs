# Differences in results between functions

The page lists functions that return a different result, return it in a different order, change the model differently or run for a different time in RAVEN and raven-toolbox, and two cases in which raven-toolbox differs from cobrapy. The list contains a function only after the difference is confirmed in the code of both functions compared.

The list is incomplete: a function that is not listed can still behave differently.

## Runtime of metabolic task checking

`checkTasks` in RAVEN and `check_tasks` in raven-toolbox return the same pass and fail results and differ in runtime.

`checkTasks` rebuilds the working model from the original for each task. `check_tasks` applies each task's constraints to one model inside a `with model:` block and reverts them afterwards. `check_tasks` saves and restores direct changes of mass-balance bounds, the one kind of edit that the context manager of cobrapy does not track.

At genome scale, copying the model for each task adds to the runtime of `checkTasks`, and `check_tasks` reuses a single model to avoid it.

## Gap-filling functions

`fillGaps` in RAVEN selects one of several algorithms with the `algorithm` option. raven-toolbox splits them into four functions, so porting a `fillGaps` call requires choosing among the functions in this table:

| Purpose | RAVEN algorithm | raven-toolbox function |
|---|---|---|
| Connecting blocked reactions against template models | `fillGaps` (default `'reference'`) | `connect_blocked_reactions` |
| Fast filling of a large candidate set by linear programming (LP) | `fillGaps` with `'fastLP'` and `'swiftLP'` | `fill_gaps_fast_lp` (`variant="fast"` and `variant="swift"`) |
| Filling by mixed-integer linear programming (MILP) with the fewest added reactions that restore growth | `fillGaps` with `'gapfillMILP'` | `fill_gaps_milp` |
| Finding the gaps without filling them | `fillGaps` with `'topological'` (`gapFillTopological`) | `analyse_topology` |

The choice among these functions changes the reactions added and the runtime.

The RAVEN functions `canExchange`, `checkProduction` and `getAllSubGraphs` find gaps without filling them. raven-toolbox merges them into `gap_report`, the port of `gapReport`, and has no separate function for each of them.

## Alternative optima of mixed-integer problems

ftINIT extraction, gap-filling and compartment assignment solve mixed-integer problems that routinely have several optima of equal objective value. Two runs can return different reaction sets that are both correct. Results can differ between implementations, between solvers and between repeat runs of one solver.

The ftINIT reproducibility study measured raven-toolbox only (RAVEN's `ftINIT` was not run): runs of one solver also differ with the seed and the number of threads, and two repeated builds at one seed differed by 2 reactions when a step stopped at its wall-clock limit (see [ftINIT reproducibility with `resolve_ties` and `prove_abs_gap`](../parameter-tuning/studies/ftinit-determinism.md)). No single exact result is expected.

Compare these outputs by the overlap of their reaction sets; do not test them for identity.

`resolveTies` in RAVEN's `ftINIT` and `resolve_ties` in raven-toolbox's `ftinit` reduce the difference between runs for the ftINIT MILP. Each step then keeps the score optimum and picks among the tied solutions in phases: the fewest kept removable reactions, then the lowest summed ID rank of those, then the fluxes with the least total absolute flux, then the fluxes with the least ID-rank-weighted backward flux. The last step of `ftINIT` skips the two flux phases.

For a given score optimum, the selected solution does not depend on the seed when every tie-break phase finishes within its time limit. It can differ between solvers, and a step that stops at its time limit keeps the solver's own answer. The primary solve can still reach a different score optimum for a different seed, so the final reaction sets can differ between seeds. Without `resolveTies` or `resolve_ties`, the ftINIT MILP can return any of the tied optima, and results differ between implementations, between solvers and between repeated runs of one solver.

## Elemental balance results

`getElementalBalance` in RAVEN and `get_elemental_balance` in raven-toolbox check whether each element (carbon, hydrogen, oxygen and so on) has the same count on both sides of a reaction. A reaction is unbalanced when the counts were computed and did not match, and the result is unknown when the counts cannot be computed. The two functions use different codes for these results.

`getElementalBalance` returns the numeric field `balanceStructure.balanceStatus` per reaction: 1 for balanced, 0 for unbalanced, -1 for missing information (no formula, or a reaction without metabolites) and -2 for a formula that cannot be parsed. `get_elemental_balance` returns the strings `balanced`, `unbalanced` and `unknown`. It reports `unknown` for a missing formula, for a formula that cobrapy cannot parse and for a reaction without metabolites, so the codes -1 and -2 of RAVEN are one result in raven-toolbox. For a reaction whose metabolites all have parseable formulas, the two functions return the same result.

cobrapy's `check_mass_balance` has no separate `unknown` result and raises an error for a formula that it cannot parse. For a reaction with a missing formula it treats the formula as empty and returns either an element imbalance or an empty result, so it gives the same kind of result as for a reaction with known formulas. raven-toolbox keeps its own function to retain the distinction.

## Parsing of gene-reaction rules

raven-toolbox and the JSON reader of cobrapy parse gene-reaction rules (the `grRules` field in RAVEN) differently. raven-toolbox reads them with `utils.parse_gr_rule` in `read_yaml_model`, `read_matlab_model`, `batch_curate` and the functions that copy or build rules, so `G1&G2` is one gene ID there. The JSON reader of cobrapy splits `G1&G2` into `G1` and `G2`.
