# Deletions and essentiality

A gene deletion analysis finds the genes that can be deleted while the organism grows. Each gene is knocked out, the model is solved again, and the result is compared with the wild type. The same procedure identifies essential reactions, the effect of two simultaneous deletions, and the flux distribution of a knockout directly after the gene is lost.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `findGeneDeletions` | `single_gene_deletion` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | knock out each gene in turn |
| `findGeneDeletions` (`'sgd'`/`'dgd'`) | `double_gene_deletion` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | knock out pairs of genes |
| `getEssentialRxns` | `find_task_essential_reactions` | reactions that a task requires |
| `removeGenes` | `remove_genes` | remove genes from the model, which differs from a knockout |
| no equivalent | `moma` {bdg-link-secondary}`cobrapy <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html>` | fluxes of a knockout, kept close to the wild type |

`removeGenes` and `remove_genes` rewrite each affected gene rule without the removed gene. A reaction that has no catalyst left stays in the model with its rule dropped and its bounds set to `(0, 0)`. This is the default of `remove_genes`, the behaviour of `removeGenes` with `removeBlockedRxns` false, and the bound state in which `knock_out_model_genes` leaves a blocked reaction, so the flux consequence of the default equals that of a knockout. Removal also takes the gene and its occurrences in the reaction rules out of the model, which a knockout does not. With `blocked_reactions="keep"` the blocked reactions keep their bounds, and `removeBlockedRxns` true or `blocked_reactions="remove"` deletes them.

When at least one requested gene is in the model, the genes that no remaining reaction uses are removed as well, including genes that were not requested. When no requested gene is in the model, no gene is removed, and RAVEN standardises the rules in this case too when `standardizeRules` is true.

## Setup

The model is `smallYeast.yml` with glucose and oxygen open, and the model grows. Uptake in this model is a positive flux through a `=> metabolite` reaction, and the upper bound opens it.

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

## Single gene knockout

Every deletion study asks whether the model reaches its objective with a given gene deleted. A gene knockout differs from a reaction knockout, and the gene rule determines how the knockout affects the reactions. Removing one of two isozymes changes nothing, and removing a subunit of a complex blocks the reaction.

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

`knock_out_model_genes` sets the bounds of every reaction whose gene rule cannot be satisfied to zero and leaves the other reactions unchanged. Inside `with model:` the change is undone when the block ends.
:::
::::

## Knockout of every gene

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

`fluxes` is sparse and has one column per deletion, so the growth row is selected by the position of the objective (`fluxes(logical(model.c), :)`). `findGeneDeletions` also returns the vector `details`, which states what happened to each gene:

- `1`: the deletion was solved.
- `2`: the problem had no optimal solution (infeasible or failed), and the fluxes are reported as zero.
- `4`: the gene was skipped because it occurs only in dead-end reactions, so deleting it cannot change the result.

A deletion that is solved with zero growth gets `1` and not `2`, so lethality is read from the growth row.
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

`single_gene_deletion` returns a DataFrame with one row per deletion and the columns `ids`, `growth` and `status`. `ids` is the set of deleted gene identifiers, a set so that the double deletion has the same shape. A gene is looked up with `results.knockout["YBR196C"]`. A knockout that makes the problem infeasible gets `growth` NaN and `status` `'infeasible'`, and the filter `growth < 1e-6` does not select it. The selection `results[(results.growth < 1e-6) | (results.status != "optimal")]` counts these knockouts as lethal, as the MATLAB filter does, because `findGeneDeletions` reports zero fluxes for them. Every solve here is optimal, so both filters find the same 9 genes.
:::
::::

## Essential reactions

Reaction essentiality asks the same question for reactions. `getEssentialRxns` and `single_reaction_deletion` answer different questions, and their answers differ by 24 reactions.

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

`getEssentialRxns` sets the objective to zero before it starts, and it calls a reaction essential when constraining the reaction to zero makes the problem infeasible. The function determines what the model needs to have any solution, with no requirement to grow. With the medium open, nothing in `smallYeast.yml` is needed for feasibility, so the result is zero. `ignoreRxns` excludes reactions from the search.
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

`single_reaction_deletion` keeps the objective and counts the reactions whose removal lowers the growth below the threshold that is applied afterwards, `1e-6` here. This is essentiality with respect to growth, which is the question of most deletion studies, and the function returns 24 reactions where the MATLAB example returns none.

`find_task_essential_reactions` in raven-toolbox gives essentiality with respect to a task and not to the objective ([Metabolic tasks](tasks.md)).
:::
::::

## Double deletions

Double deletions find redundancy that single deletions miss, as two genes can each be dispensable and still not be deletable together. The number of pairs grows with the square of the number of genes, so the run time increases sharply with the size of the model.

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

## Fluxes of a knockout

FBA assumes that the knockout re-optimises perfectly, which a cell directly after the loss of a gene does not do. MOMA (minimisation of metabolic adjustment) finds the flux distribution that the mutant can achieve and that is closest to a wild-type reference. It models the state directly after the knockout, before the cell adapts, and gives a different answer from FBA.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

RAVEN has no MOMA. RAVEN 3 removed `qMOMA`, which solved the quadratic problem with `quadprog` from the Optimization Toolbox of MATLAB, as the last function that depended on a paid MATLAB toolbox. No function of RAVEN replaces it, and a MOMA prediction comes from Python or from the COBRA Toolbox, which has its own.

The FBA part of the comparison runs in RAVEN:

```matlab
modelKO = removeGenes(model, {'YER178W'}, 'removeBlockedRxns', true);   % PDA1
solKO = solveLP(modelKO);
fprintf('FBA growth:  %.4f /h\n', solKO.f);
```

```text
FBA growth:  0.1053 /h
```

`compareFluxes` compares two flux vectors of the same model and shows what changed in the mutant, beyond how much the growth fell ([Comparing models](comparing.md)).
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

The reference is computed before the knockout. Without `solution=`, cobrapy takes the pFBA solution of the model it receives, which inside the `with` block is the mutant, and MOMA returns the FBA answer. `PDA1` is the test gene because it is not lethal: the PDH bypass (`PDC`, `ALD6`, `ACS`) keeps the mutant growing, so FBA and MOMA can differ.

`linear=False` is the quadratic MOMA of Segrè et al. (2002), which minimises the squared distance to the reference as a quadratic program (QP). GLPK cannot solve QPs, so cobrapy switches to a solver that supports QPs (Gurobi or CPLEX) for the call and raises `SolverNotFound` when none is installed. `pip install gurobipy` installs a Gurobi licence with a size limit that suffices for a model of this size. `linear=True` minimises the summed absolute distance as a linear program, which is a different method with different answers. The MOMA prediction depends on the reference flux vector, which pFBA selects from many alternative optima.
:::
::::

:::{admonition} Troubleshooting
:class: warning

- Gene and reaction knockouts are confused. Deleting a gene silences a reaction only when the gene rule says so. Isozymes mask single knockouts, which the double deletions test.
- The essentiality numbers of the two toolboxes are compared. `getEssentialRxns` measures feasibility and `single_reaction_deletion` measures growth, which are different questions.
- A knockout looks lethal because the medium is wrong. Essentiality is relative to the medium and the objective, and both are stated with the result ([Growth media and conditions](media.md)).
- Essentiality is read from a threshold. `growth < 1e-6` is a numerical limit and not a biological one. A mutant at 1 % of the wild-type growth is not dead.
- A double deletion runs on a genome-scale model. The run time grows with the square of the number of genes, so the lists are restricted or the wait is accepted.
:::

## See also

- [Simulating growth with FBA](fba.md): the solve that underlies all of this.
- [Metabolic tasks](tasks.md): essentiality with respect to a task.
- [Quality control](quality-control.md): the checks before any of this.
