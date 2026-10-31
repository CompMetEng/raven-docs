# Same function, different answer

Where the two agree on the job but differ in what they hand back, how they order
it, or what they do to the model on the way. Deliberately short: an entry is
added only once the difference has been confirmed in both sources.

:::{admonition} Not a complete list
:class: info
Absence from this section is not a guarantee of identical behaviour. It only
means the difference has not been confirmed and written up yet.
:::

## Duplicate reactions: gene associations are not merged

`contractModel` merges duplicate reactions **and their gene associations**: when
it collapses a set of duplicates it joins the distinct `grRules` with `or`, so
every gene that pointed at any of the duplicates still points at the survivor.

`remove_duplicate_reactions` keeps one reaction of each duplicate set and removes
the rest, without merging gene associations. A gene that was associated *only*
with a removed duplicate is no longer associated with anything.

The stoichiometric network is the same either way; the gene–reaction mapping is
not. If you are contracting a draft assembled from several templates, where the
same reaction commonly arrives with different gene associations, check the GPRs
of the survivors afterwards.

## Metabolic tasks: the same result, a different runtime

`checkTasks` rebuilds the working model from the original for each task.
`check_tasks` instead applies each task's constraints to one model inside a
`with model:` block and reverts them afterwards, restoring by hand the one kind
of edit cobra's context manager does not track (direct mass-balance bound
changes).

The pass and fail results are the same. The runtime is not: at genome scale,
copying the model for each task dominates the MATLAB runtime, which is why the
Python version reuses a single model. This changes runtime comparisons, not
results.

## Gap-filling: `fillGaps` splits into three functions in raven-toolbox

`fillGaps` does several different jobs through one function call.
raven-toolbox splits them, so porting a `fillGaps` call means choosing:

| What you were doing | Use |
|---|---|
| Connecting blocked reactions against template models | `connect_blocked_reactions` |
| Fast LP-based filling of a large candidate set | `fill_gaps_fast_lp` |
| MILP filling with the fewest added reactions that restore growth | `fill_gaps_milp` |
| Only *finding* the gaps (`canExchange`, `checkProduction`, `getAllSubGraphs`, `haveFlux`, `gapFillTopological`) | `analyse_topology` |

The choice changes both the reaction set added and the runtime, because each
of the three functions uses a different algorithm; they are not the same
algorithm under three different names.

## Anything solved by MILP

ftINIT extraction, gap-filling, and compartment assignment all solve
mixed-integer problems that routinely have **several optima of equal objective
value**. Two runs can return different reaction sets and both be correct; across
languages, across solvers, and in some configurations across runs of the same
solver.

Do not compare these outputs for identity. Compare them for overlap, and
expect a range of acceptable values, not one exact number.

`resolveTies` in RAVEN's `ftINIT` and `resolve_ties` in raven-toolbox's `ftinit` reduce this spread for the ftINIT MILP. Each step then keeps the score optimum and picks among the tied solutions in phases: the fewest kept removable reactions, then the lowest summed id rank of those, then the fluxes with the least total absolute flux, then the fluxes with the least id-rank-weighted backward flux. The last step skips the two flux phases. The choice does not rely on the solver seed. It can still differ between solvers, and a step that stops at its time limit keeps the solver's own answer. Without `resolveTies` or `resolve_ties`, the caveat above applies in full.

## Elemental balance: an unknown result is not the same as balanced

Elemental balance checks whether a reaction has the same count of each
chemical element (carbon, hydrogen, oxygen, and so on) on both sides, the way
a correct chemical equation must. `getElementalBalance` and
`get_elemental_balance` each report one of three results per reaction, not
two: `balanced`, `unbalanced`, or `unknown`. A reaction is `unknown` when one
of its metabolites has no chemical formula recorded, so the element counts
cannot be computed at all; that is different from `unbalanced`, which means
the counts were computed and did not match. The two functions agree on this
three-way result.

That third case is lost if you switch to plain cobrapy: its
`check_mass_balance` has no separate `unknown` result, so a reaction with a
missing formula and a reaction that is genuinely unbalanced can look the
same. raven-toolbox keeps its own function instead of using cobrapy's
directly, specifically to keep that distinction.
