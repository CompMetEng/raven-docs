# 16. Deletions and essentiality

Which genes can the organism lose and still grow? Knock each one out, re-solve,
and compare. The same machinery answers "which reactions are essential", "what
happens if I delete two things at once", and "what flux distribution does a
knockout have right after the gene is lost".

## Functions on this page

| MATLAB | Python | |
|---|---|---|
| `findGeneDeletions` | `single_gene_deletion` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | knock out every gene in turn |
| `findGeneDeletions` (`'sgd'`/`'dgd'`) | `double_gene_deletion` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | pairs of genes |
| `getEssentialRxns` | `find_task_essential_reactions` | reactions a task requires |
| `deleteUnusedGenes` | `remove_genes` | remove genes, rather than knock them out |
| no equivalent | `moma` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | a knockout's fluxes, staying near the wild type |

`removeGenes` and `remove_genes` rewrite each affected GPR without the removed gene. A reaction that loses its last catalyst stays with its rule dropped and its bounds set to `(0, 0)` (the default of `remove_genes`, and of `removeGenes` with `removeBlockedRxns` false), which is the bound state `knock_out_model_genes` leaves a blocked reaction in, so the flux consequence of the default equals that of a knockout. What differs is that the gene and its occurrences in the reaction rules are removed from the model; with `blocked_reactions="keep"` the blocked reactions stay at their bounds, and `removeBlockedRxns` true and `blocked_reactions="remove"` delete them. When at least one requested gene is in the model, genes that no remaining reaction used are removed as well, also when they were not requested; when none is in the model, no gene is removed (RAVEN still standardizes the rules when `standardizeRules` is true).

## Setup

`smallYeast.yml`, with glucose and oxygen open so the model grows. Uptake in
this model is a **positive** flux through a `=> metabolite` reaction, so it is
the upper bound that opens it.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
model = readYAMLmodel('smallYeast.yml');
model = setParam(model, 'ub', {'glcIN', 'o2IN'}, [1 1000]);
model = setParam(model, 'obj', 'biomassOUT', 1);
sol = solveLP(model);
fprintf('wild type: %.4f /h\n', sol.f);
```

```text
wild type: 0.1222 /h
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.io import read_yaml_model

model = read_yaml_model("smallYeast.yml")
model.reactions.get_by_id("glcIN").upper_bound = 1.0
model.reactions.get_by_id("o2IN").upper_bound = 1000.0
model.objective = "biomassOUT"
print(f"wild type: {model.slim_optimize():.4f} /h")
```

```text
wild type: 0.1222 /h
```
:::
::::

## 16.1 Knock out one gene

The question underneath every deletion study: with this gene gone, can the model
still reach its objective? A gene knockout is not a reaction knockout: the GPR
decides. Remove one of two isozymes and nothing happens; remove a subunit of a
complex and the reaction goes.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
modelKO = removeGenes(model, {'YBR196C'}, 'removeBlockedRxns', true);
solKO = solveLP(modelKO);
fprintf('PGI1 knockout: %.4f /h\n', solKO.f);
```

```text
PGI1 knockout: -0.0000 /h
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.manipulation import knock_out_model_genes

with model:
    knock_out_model_genes(model, ["YBR196C"])
    print(f"PGI1 knockout: {model.slim_optimize():.4f} /h")

print(f"wild type again: {model.slim_optimize():.4f} /h")
```

```text
PGI1 knockout: 0.0000 /h
wild type again: 0.1222 /h
```

`knock_out_model_genes` sets the bounds of every reaction whose GPR is no
longer satisfiable to zero, and leaves the rest alone. Inside `with model:`
it is undone on the way out, so the knockout does not persist past the
block.
:::
::::

## 16.2 Knock out every gene

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
[genes, fluxes] = findGeneDeletions(model, 'testType', 'sgd');
growth = full(fluxes(logical(model.c), :));   % fluxes come back sparse
fprintf('%d genes tested, %d essential\n', numel(genes), sum(growth < 1e-6));
```

```text
61 genes tested, 9 essential
```

`fluxes` comes back sparse and with one column per deletion, so the growth
row has to be pulled out by the objective's position, as above.
`findGeneDeletions` also returns a `details` vector saying what happened to
each gene: 1 when the deletion was solved, 2 when the problem had no optimal
solution (infeasible or failed, with fluxes reported as zero), and 4 when the
gene was skipped because it only appears on dead-end reactions and deleting it
could not change the answer. A gene whose deletion solves to zero growth gets 1,
not 2, so read lethality off the growth row, as above.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.flux_analysis import single_gene_deletion

results = single_gene_deletion(model)
essential = results[results.growth < 1e-6]
print(f"{len(results)} genes tested, {len(essential)} essential")
print(sorted(next(iter(ids)) for ids in essential.ids)[:5])
```

```text
61 genes tested, 9 essential
['YBR196C', 'YCR012W', 'YDL066W', 'YDR050C', 'YKL060C']
```

`single_gene_deletion` returns a DataFrame with one row per deletion: `ids`
(the set of deleted gene ids, a set so that the double-deletion case has the
same shape), `growth` and `status`. Look a gene up with
`results.knockout["YBR196C"]`. A knockout that makes the problem infeasible
gets `growth` NaN and `status` `'infeasible'`, and `growth < 1e-6` does **not**
select it. Use `results[(results.growth < 1e-6) | (results.status != "optimal")]`
to count those as lethal, which is what the MATLAB filter above does, since
`findGeneDeletions` reports zero fluxes for them. Here every solve is optimal,
so both filters find the same 9.
:::
::::

## 16.3 Essential reactions

Reaction essentiality asks the same question one level down. The two functions
below look equivalent but ask different questions, which is why their answers
differ by 24.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
essential = getEssentialRxns(model);
fprintf('%d essential reactions\n', numel(essential));
```

```text
0 essential reactions
```

`getEssentialRxns` zeroes the objective before it starts and calls a
reaction essential when constraining it to zero makes the problem
**infeasible**. It is asking what the model needs in order to have any
solution at all, not what it needs in order to grow. With the medium open,
nothing in `smallYeast.yml` is required for feasibility, so the answer is
zero. `ignoreRxns` excludes reactions from the search.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.flux_analysis import single_reaction_deletion

results = single_reaction_deletion(model)
essential = results[results.growth < 1e-6]
print(f"{len(essential)} essential reactions")
```

```text
24 essential reactions
```

`single_reaction_deletion` keeps the objective and counts the reactions
whose removal drops growth below the threshold applied afterwards, `1e-6`
here. That is essentiality with respect to growth, which is the question
most deletion studies mean, and it is why this returns 24 where the MATLAB
tab returns none.

For essentiality with respect to a *task* rather than the objective,
raven-toolbox has `find_task_essential_reactions`; see
[15. Metabolic tasks](tasks.md).
:::
::::

## 16.4 Two at a time

Double deletions find the redundancy single deletions miss: two genes that each
look dispensable but cannot both be deleted. The number of pairs to test is
quadratic in the number of genes, so run time grows sharply with model size.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
[genes, fluxes] = findGeneDeletions(model, 'testType', 'dgd');
fprintf('%d gene pairs tested\n', size(genes, 1));
```

```text
1830 gene pairs tested
```
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.flux_analysis import double_gene_deletion

subset = [gene for gene in model.genes][:8]
pairs = double_gene_deletion(model, gene_list1=subset)
print(f"{len(pairs)} combinations tested")
print(f"lowest growth: {pairs.growth.min():.4f} /h")
```

```text
36 combinations tested
lowest growth: 0.0000 /h
```
:::
::::

## 16.5 A knockout's fluxes, not just its growth rate

FBA assumes the knockout re-optimises perfectly, which a cell that just lost a
gene does not do. MOMA (minimisation of metabolic adjustment) instead looks for
the flux distribution closest to a wild-type reference that the mutant can
actually achieve. It models the state right after the knockout, before the cell
adapts, and gives a different answer from FBA.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

**RAVEN has no MOMA.** It had `qMOMA`, which solved the quadratic problem
with `quadprog` from MATLAB's **Optimization Toolbox**; RAVEN 3 removed it
as the last function that depended on a paid MATLAB toolbox. Nothing in
RAVEN replaces it, so a MOMA prediction has to come from the Python side,
or from the COBRA Toolbox, which keeps its own.

The FBA half of the comparison runs in RAVEN as usual:

```matlab
modelKO = removeGenes(model, {'YER178W'}, 'removeBlockedRxns', true);   % PDA1
solKO = solveLP(modelKO);
fprintf('FBA growth:  %.4f /h\n', solKO.f);
```

```text
FBA growth:  0.1053 /h
```

What RAVEN does offer for the same *question* (what changed in the mutant,
rather than by how much growth fell) is `compareFluxes` on two flux
vectors from the same model, in [21. Comparing models](comparing.md).
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from cobra.flux_analysis import moma, pfba

wild_type = pfba(model)                       # the reference: the unmodified model
with model:
    knock_out_model_genes(model, ["YER178W"])   # PDA1, pyruvate dehydrogenase
    fba_growth = model.slim_optimize()
    solution = moma(model, solution=wild_type, linear=False)
print(f"FBA growth:  {fba_growth:.4f} /h")
print(f"MOMA growth: {solution.fluxes['biomassOUT']:.4f} /h")
```

```text
FBA growth:  0.1053 /h
MOMA growth: 0.0869 /h
```

The reference has to be computed before the knockout. Without `solution=`,
cobrapy takes pFBA of the model it is given, which inside the `with` block is
already the mutant, and MOMA returns the FBA answer. `PDA1` is a good test
because it is not lethal: the PDH bypass (`PDC`, `ALD6`, `ACS`) keeps the
mutant growing, so FBA and MOMA can differ.

`linear=False` is the quadratic MOMA of Segrè et al. (2002): it minimises the
squared distance to the reference, a quadratic program (QP). GLPK cannot solve
QPs, so cobrapy switches to a QP-capable solver for the call (Gurobi or CPLEX)
and raises `SolverNotFound` when none is installed. `pip install gurobipy`
brings a size-limited Gurobi licence that is enough for a model this small.
`linear=True` minimises the summed absolute distance instead, an LP, and is a
different method with different answers. MOMA's prediction depends on the
reference flux vector, which pFBA picks from many alternative optima.
:::
::::

:::{warning} What can go wrong
- **Confusing gene and reaction knockouts.** Deleting a gene only silences a
  reaction when the GPR says so. Isozymes mask single knockouts, which is
  what the double deletions test.
- **Comparing essentiality numbers from the two toolboxes.**
  `getEssentialRxns` measures feasibility and `single_reaction_deletion`
  measures growth; they are not two implementations of one question.
- **A knockout that looks lethal because the medium is wrong.** Essentiality
  is relative to the medium and the objective. State both when you report it;
  see [5. Growth media and conditions](media.md).
- **Reading essentiality off a threshold.** `growth < 1e-6` is a numerical
  cut-off, not biology. A mutant at 1 % of wild-type growth is not dead.
- **Double deletions on a genome-scale model.** Quadratic in the gene count;
  restrict the lists, or accept the wait.
:::

## See also

- [4. Simulating growth with FBA](fba.md), the solve underneath all of this.
- [15. Metabolic tasks](tasks.md), essentiality with respect to a task.
- [9. Quality control](quality-control.md), before trusting any of it.
