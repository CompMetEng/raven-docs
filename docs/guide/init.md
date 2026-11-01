# Context-specific models with ftINIT

A genome-scale model describes everything that an organism can do. ftINIT reduces it to what a given sample (a tissue, a cell line or a condition) appears to do. The input is expression data and a list of metabolic tasks that the result must be able to perform. The legacy method tINIT, which ftINIT replaces, extracts models in the same way for models that were built with it.

The workflow uses Human-GEM and the RNA-seq data that Human-GEM provides, in both toolboxes.

## Choice of method

ftINIT is the recommended method and replaces the legacy method tINIT. The workflow uses ftINIT.

tINIT (`getINITModel`) reproduces a model that was built with it. It is supported and not scheduled for removal. It issues the notice `RAVEN:legacyMethod` once per session, which states that the method is not intended for new work, and `warning('off','RAVEN:legacyMethod')` silences the notice.

tINIT exists in MATLAB only. RAVEN includes it for the models that were built with it. raven-toolbox has no such installed base and includes ftINIT only, so a tINIT model is reproduced in MATLAB.

## Relation between tINIT and ftINIT

The two methods are separate implementations that share no algorithm code. In the table, the entries for reaction scoring and task gap-filling differ only because the two entry points call shared functions with different settings. Two implementations do not exist for these steps.

| Aspect | tINIT | ftINIT |
|---|---|---|
| Entry point | `getINITModel` | `prepINITModel`, then `ftINIT` |
| Reaction scoring | `scoreModel` (fixed isozyme and complex scoring, `dataPrecedence` `'reaction'`) | `scoreModel`, `groupRxnScores` |
| Core mixed-integer linear program (MILP) | `runINIT` | `ftINITInternalAlg`, scheduled by `getINITSteps` |
| Task gap-filling | `fitTasks` | `fitTasks` (`gapFillMode` `'preMerged'`), `ftINITFillGaps` |
| Gene pruning | inline in `getINITModel` | `removeLowScoreGenes` |

The methods share general RAVEN functions that are not specific to either. `checkTasks` and `getEssentialRxns` decide which tasks are feasible and which reactions they need. Below these are `parseTaskList`, `simplifyModel`, the solver layer, and the functions for model manipulation and input and output.

`scoreModel` is one function for both methods. `getINITModel` calls it with a single operator for `and` and `or` in a gene rule and with `dataPrecedence` `'reaction'`, the settings that the original tINIT algorithm needs, and afterwards converts the score of an unmeasured gene from `NaN` to `-Inf`. `ftINIT` calls it with the general defaults. Task gap-filling is one `fitTasks` loop for both. `getINITModel` uses the default `gapFillMode` (`'merge'`, backed by `fillGaps`). `ftINIT` passes `'preMerged'`, backed by `ftINITFillGaps`, because its reference model already contains the reactions of the sample and needs no merge per task. The MILP formulation is therefore the one place where gap-filling differs: `fillGaps` merges per task, and `ftINITFillGaps` expects a model that is merged already. The difference does not lie between `getINITModel` and `ftINIT` as such.

## Reference run

The outputs in this workflow come from one run made by hand. The [Executed examples](index.md#executed-examples) workflow runs the other guide pages again whenever a guide page, the example data, the runner, the workflow or a submodule changes, and once a week. It does not run the outputs here, because preparing Human-GEM took 47 minutes in MATLAB and 37 minutes in Python, and the MATLAB run produced an artefact of 174 MB, which a documentation build should not attempt. The numbers come from one run (Human-GEM `main` at commit `6812be2a`, RAVEN commit `2d0630e3`, raven-toolbox commit `94f39407`, Gurobi (MATLAB links the 13.0.1 module library; Python most likely loads the library of gurobipy 13.0.3), four cores, 2026-10-30) and are quoted with their wall-clock times for planning.

The [Human-GEM guide](https://sysbiochalmers.github.io/Human-GEM-guide/gem_extraction/) presents the same MATLAB workflow, including the comparison of the extracted models. It is maintained together with the model.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `prepINITModel` | `prep_init_model` | preparation of the template, once |
| `parseTaskList` | `parse_task_list` | the tasks that the extracted model must satisfy |
| `getINITSteps` | `get_init_steps` | the step definitions (`1+0`, `1+1`, …) |
| `ftINIT` | `ftinit` | the staged extraction |
| `scoreModel` | `score_reactions_from_genes` | gene scores to reaction scores |
| no equivalent | `gene_scores_from_expression` | expression to gene scores |
| `runINIT`, `getINITModel` | no equivalent | the legacy tINIT method, for reproducing models built with it |
| `removeLowScoreGenes` | `remove_low_score_genes` | remove negative-scoring genes from gene-protein-reaction rules (GPRs) |
| `parseHPA`, `parseHPArna` | `parse_hpa`, `parse_hpa_rna` | read Human Protein Atlas (HPA) files |
| no equivalent | `hpa_gene_scores`, `rna_gene_scores` | HPA levels or transcripts per million (TPM) to gene scores |
| `checkTasks` | `check_tasks` | confirm that the result performs the tasks |

## Setup

Human-GEM provides everything except the toolbox:

<!-- run-examples: skip -->

```bash
git clone --depth=1 https://github.com/SysBioChalmers/Human-GEM.git
```

| File | Content |
|---|---|
| `model/Human-GEM.mat` (or `.xml`, `.yml`) | the template: 12 748 reactions, 2 870 genes |
| `model/reactions.tsv` | reaction annotations, including which reactions are spontaneous |
| `data/metabolicTasks/metabolicTasks_Essential.txt` | 57 tasks that the extracted model must pass |
| `data/datasets/Hart2015_RNAseq.txt` | TPM for five cell lines: DLD1, GBM, HCT116, HELA, RPE1 |

Both extractions are mixed-integer problems. On Human-GEM, GLPK completed a benchmark extraction in 2182 s with a time-limited result (Jaccard 0.892 against Gurobi), so Gurobi is set up first ([Solvers and configuration](solvers.md)). That benchmark ([ftINIT on different solvers](../parameter-tuning/studies/init-solver-benchmark.md)) used Human-GEM `38567ab8` (cleaned), prepared without a task list and with scaled stoichiometry, series `1+1` and `time_limit=900`. The input differs from the `6812be2a` template with task preparation used here.

In raven-toolbox without `time_limit`, the scheduled runs of a series keep their own limits, for GLPK as for Gurobi. The limits are 120 s and 5000 s, plus a first run of 5 s in the last step of `1+1` and `2+1`, and 10000 s for `full`, which runs once. With `setRavenSolver('glpk')`, RAVEN does not pass the `TimeLimit` of the schedule to GLPK, and `optimizeProb` sets a limit of 1000 s on every GLPK MILP.

## Template preparation

The preparation finds the task-essential reactions, classifies every reaction into categories that do not depend on omics data, merges linear stretches, and rescales the stoichiometry to a narrower range of coefficients. The rescaling is not needed for feasibility at the default `big_m`. In the single runs of [ftINIT parameter calibration and input robustness](../parameter-tuning/studies/init-param-calibration.md), it shortened the run (83 s against 157 s). The preparation depends on the template and the task list and not on the expression data, so it is done once and reused for every sample.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

<!-- run-examples: skip -->

```matlab
load('Human-GEM/model/Human-GEM.mat');          % the struct is called humanGEM
tasks = parseTaskList('Human-GEM/data/metabolicTasks/metabolicTasks_Essential.txt');

% spontaneous reactions are flagged in the model's own annotation table
tsv   = readtable('Human-GEM/model/reactions.tsv', 'FileType', 'text', 'Delimiter', '\t');
spont = tsv.rxns(tsv.spontaneous == 1);

prepData = prepINITModel(humanGEM, tasks, 'spontRxnNames', spont, 'extComp', 'e');
save('prepData.mat', 'prepData', '-v7.3');
```

```text
prepData.mat: 174 MB
```

Human-GEM has a wrapper, `prepHumanModelForftINIT`, which reads those two files. It needs Human-GEM 2.0.1 or later.
:::
:::{tab-item} 🐍 Python
:sync: python

<!-- run-examples: skip -->

```python
import cobra
import pandas as pd
from cobra.io import read_sbml_model

from raven_toolbox.init import prep_init_model
from raven_toolbox.tasks import parse_task_list

cobra.Configuration().processes = 1     # see the note below

model = read_sbml_model("Human-GEM/model/Human-GEM.xml")
model.solver = "gurobi"
tasks = parse_task_list("Human-GEM/data/metabolicTasks/metabolicTasks_Essential.txt")

# spontaneous reactions are flagged in the model's own annotation table
tsv = pd.read_csv("Human-GEM/model/reactions.tsv", sep="\t")
spont = tsv.loc[tsv["spontaneous"] == 1, "rxns"].tolist()

prep = prep_init_model(model, tasks, ext_comp="e", spontaneous=spont)
```

```text
load 11s
prep_init_model 2216s
```

Reading Human-GEM from the Systems Biology Markup Language (SBML) file alone takes about 11 seconds, and the preparation takes 37 minutes in Python and 47 minutes in MATLAB. The two preparations were separate Slurm jobs on the same node type with four cores each. The MATLAB run used the default of `prepINITModel` for `runParallel`, which is serial, and the Python run used `processes = 1`, so the two times compare the complete runs and not the code alone. Two settings affect the run:

- `prep_init_model` takes the argument `processes`, which defaults to 1, and its `simplify_model` passes follow `cobra.Configuration().processes`, which starts worker processes by default. The Python run above used `processes = 1`. Where worker processes are not permitted (a locked-down Windows machine, some continuous integration (CI) runners), the default fails with `PermissionError: [WinError 5] Access is denied`, and `processes = 1` removes the parallelism and lets the run finish.
- `essential_cache_path` caches the slow search for task-essential reactions, so a second preparation of the same template skips it.
:::
::::

:::{admonition} Spontaneous reactions
:class: note

The list of spontaneous reactions is passed to the preparation. ftINIT keeps every reaction in the list in every extracted model, whatever the data say. Other reactions without a gene rule are kept only where the optimisation needs them, so they can differ between samples. In Human-GEM, `spontaneous` marks reactions that need no enzyme. These include diffusion: transport between cytosol and nucleus through the nuclear pores, and gases and water (O2, CO2, H2O, NH3, H2O2, NO, H2S) crossing membranes. Without the list, ftINIT can remove such transports in some samples, and the model then uses other pathways. Without the transport of dCTP into the nucleus, for example, deoxycytidine kinase (DCK) becomes essential for DNA synthesis, which is an artefact of the extraction and not biology.
:::

## Expression data

RAVEN takes one struct with the genes, the sample names, and a matrix of levels with genes in the rows and samples in the columns. `threshold` is the level above which a gene counts as expressed. Without it, the mean across the samples is used for each gene.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

<!-- run-examples: skip -->

```matlab
tbl = readtable('Human-GEM/data/datasets/Hart2015_RNAseq.txt', ...
    'FileType', 'text', 'Delimiter', '\t');

arrayData.genes     = tbl.gene;
arrayData.tissues   = tbl.Properties.VariableNames(2:end)';
arrayData.levels    = table2array(tbl(:, 2:end));
arrayData.threshold = 1;
```

```text
18687 genes x 5 samples
```
:::
:::{tab-item} 🐍 Python
:sync: python

<!-- run-examples: skip -->

```python
import pandas as pd

from raven_toolbox.init import gene_scores_from_expression, score_reactions_from_genes

tpm = pd.read_csv("Human-GEM/data/datasets/Hart2015_RNAseq.txt", sep="\t", index_col="gene")
print(f"{tpm.shape[0]} genes x {tpm.shape[1]} samples")

gene_scores = gene_scores_from_expression(tpm["HCT116"].to_dict(), reference=1.0)
rxn_scores = score_reactions_from_genes(model, gene_scores)
```

The two steps are separate in Python. `gene_scores_from_expression` applies the rule of RAVEN (5·ln(level / reference), clamped to [−5, 10]), and `score_reactions_from_genes` maps the result through the gene rules. Any other source of gene scores (HPA through `hpa_gene_scores`, proteomics or a curated list) can therefore feed the second step.

The clamp explains why two samples that differ widely can give nearly the same model:

<!-- run-examples: skip -->

```python
print(gene_scores_from_expression({"a": 12.0, "b": 0.5, "c": 3.0}, reference=3.0))
```

```text
{'a': 6.93, 'b': -5.0, 'c': 0.0}
```

`b` computes to −8.96 and is returned at the floor. A gene at its reference scores zero, which is neither in nor out.
:::
::::

### Scores from the Human Protein Atlas

A transcript table is one source of gene scores, and the Human Protein Atlas is another. Both toolboxes read it directly. [`hpa-sample.tsv`](../data/hpa-sample.tsv) is an excerpt of ten rows in the proteomics format of HPA, with the six columns that the parsers expect and five human genes in two tissues. The levels are chosen so that every category occurs. A complete file is `normal_tissue.tsv` from [proteinatlas.org](https://www.proteinatlas.org/about/download).

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

```matlab
hpaData = parseHPA('hpa-sample.tsv');
fprintf('%d genes, %d tissue/cell-type columns\n', ...
    numel(hpaData.genes), numel(hpaData.tissues));
fprintf('levels: %s\n', strjoin(hpaData.levels, ', '));
```

```text
5 genes, 3 tissue/cell-type columns
levels: High, Low, Medium, Not detected
```

`parseHPA` returns a struct and not a table. `genes` and `geneNames` hold the Ensembl identifiers and the symbols. `tissues` and `celltypes` are parallel arrays with one entry per combination of tissue and cell type, not per tissue. `gene2Level` is a sparse matrix of genes by combination, and its values are indices into `levels`. A level is therefore read in two steps, the same indirection that `model.metComps` uses in [Model structure and identifiers](model-structure.md).

The argument `version` is accepted and ignored, because the format is inferred from the column headers. `hpaData` is what `ftINIT` takes as its fourth positional argument, in place of `transcrData`.
:::
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.init import parse_hpa

hpa = parse_hpa("hpa-sample.tsv")
print(hpa.df.shape[0], "rows")
print("tissues:", hpa.tissues())
print("cell types in liver:", hpa.celltypes("liver"))
print("levels:", sorted(hpa.df["level"].unique()))
```

```text
10 rows
tissues: ['kidney', 'liver']
cell types in liver: ['bile duct cells', 'hepatocytes']
levels: ['High', 'Low', 'Medium', 'Not detected']
```

`parse_hpa` returns an `HPAData` that wraps a pandas DataFrame in `.df`, with one row per gene, tissue and cell type and the columns `gene_id`, `gene_name`, `tissue`, `celltype`, `level` and `reliability`. Ordinary grouping and filtering apply before anything becomes a score. `tissues()` and `celltypes()` return the corresponding lists.

The parallel arrays and the sparse index matrix of MATLAB answer the question for the level of gene i in combination j directly, and the DataFrame answers which rows belong to a tissue. Neither holds information that the other lacks.
:::
::::

### Levels to numbers

HPA reports a category and not a quantity, so a level becomes a number before it is used in scoring.

::::{tab-set}
:::{tab-item} 🐍 Python
:sync: python

```python
from raven_toolbox.init import HPA_LEVEL_SCORES, hpa_gene_scores

print(HPA_LEVEL_SCORES)

scores = hpa_gene_scores(hpa, tissue="liver")
for gene, score in sorted(scores.items()):
    print(f"  {gene}  {score:+.1f}")
```

```text
{'High': 20.0, 'Medium': 15.0, 'Low': 10.0, 'None': -8.0, 'Not detected': -8.0, 'Strong': 20.0, 'Moderate': 15.0, 'Weak': 10.0, 'Negative': -8.0}
  ENSG00000067225  +20.0
  ENSG00000106633  +15.0
  ENSG00000111640  +20.0
  ENSG00000156515  +10.0
  ENSG00000159399  -8.0
```

The mapping is available as `HPA_LEVEL_SCORES`, and `level_scores=` replaces it. Both vocabularies are covered, `High`, `Medium`, `Low` and `Not detected` for expression and `Strong`, `Moderate`, `Weak` and `Negative` for antibody staining, and the corresponding terms score the same.

MATLAB has no separate step: `scoreModel` takes `hpaData` and applies the mapping internally.
:::
::::

A negative score is a statement and not a missing value. `Not detected` scores -8, which pushes a reaction towards exclusion. A gene that is absent from the tissue is omitted from the result, and the reaction scorer then uses its `no_gene_score`. The two cases give different models.

### One gene in several cell types

A tissue has several cell types, and a gene can be measured differently in each. `PKM` in the excerpt is `High` in hepatocytes and `Low` in bile duct cells.

::::{tab-set}
:::{tab-item} 🐍 Python
:sync: python

```python
best = hpa_gene_scores(hpa, tissue="liver", multiple_celltype="best")
average = hpa_gene_scores(hpa, tissue="liver", multiple_celltype="average")
print(f"PKM  best {best['ENSG00000067225']:+.1f}, "
      f"average {average['ENSG00000067225']:+.1f}")
```

```text
PKM  best +20.0, average +15.0
```

`"best"` takes the maximum and is the default, as in RAVEN. `"average"` takes the mean. The maximum describes the capacity of the tissue, and the mean describes its activity across cells. `celltype=` selects one cell type, and the choice then does not arise.
:::
::::

`parseHPArna` and `parse_hpa_rna` read the RNA-seq file, whose header is `Gene`, `Gene name`, `Tissue` followed by the TPM columns. These values are quantities, so `rna_gene_scores` applies the logarithmic rule of `gene_scores_from_expression` and not a level mapping. Both sources end as a mapping from genes to scores, which `score_reactions_from_genes` applies to the gene rules.

## Extraction for one sample

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

<!-- run-examples: skip -->

```matlab
contextModel = ftINIT(prepData, 'HCT116', [], [], ...
    'transcrData', arrayData, ...
    'INITSteps', getINITSteps([], '1+0'));
```

```text
9544 rxns, 1785 genes
```

Two argument errors fail without naming the argument:

- `hpaData` is the fourth positional argument. When it is skipped, the string `'transcrData'` is taken as `hpaData`, and the expression struct is assigned to `transcrData` by position.
- The step list is `'INITSteps'` and not `'steps'`. An unrecognised name is taken as a positional value, and the misleading error message `Metabolomics contains the same metabolite multiple times` appears.
:::
:::{tab-item} 🐍 Python
:sync: python

<!-- run-examples: skip -->

```python
from raven_toolbox.init import ftinit

context = ftinit(prep, rxn_scores=rxn_scores, series="1+0", gene_scores=gene_scores)
print(len(context.reactions), "reactions,", len(context.genes), "genes")
```

`ftinit` takes the reaction scores and not the expression struct, so the scoring is a separate step. `gene_scores` is optional and removes negative-scoring genes from the gene rules that remain. `fill_gaps=False` skips the task repair.
:::
::::

### Series `1+0` and `1+1`

`1+0` leaves out most reactions without a gene rule, and in this sample it ran in 124 s in Python and in 797 s in MATLAB. `1+1` adds a second optimisation over those reactions. The run shown uses `1+0`. It gives 12 748 → 9 543 reactions and 2 870 → 1 783 genes in Python (124 seconds), and 12 748 → 9 544 reactions and 2 870 → 1 785 genes in MATLAB (797 seconds).

## Checking the extracted model

An extracted model is a hypothesis. The first check is the set of tasks that the model was built to satisfy, which is also the cheapest check.

::::{tab-set}
:::{tab-item} Ⓜ️ MATLAB
:sync: matlab

<!-- run-examples: skip -->

```matlab
taskReport = checkTasks(contextModel, [], 'taskStructure', tasks);
```
:::
:::{tab-item} 🐍 Python
:sync: python

<!-- run-examples: skip -->

```python
from raven_toolbox.tasks import check_tasks

report = check_tasks(context, tasks)
print(sum(1 for result in report if result.passed), "of", len(report), "tasks pass")
```
:::
::::

The result is compared with the template and with the other samples. [Quality control](quality-control.md) covers the structural checks, and the [GEM comparison](https://sysbiochalmers.github.io/Human-GEM-guide/gem_comparison/) of the Human-GEM guide covers the comparison of many extracted models.

:::{admonition} Troubleshooting
:class: warning

- The identifiers do not match. Human-GEM and `Hart2015_RNAseq.txt` both use ENSEMBL identifiers, so the workflow has no mapping step. Expression data with symbols or systematic names needs a mapping. A few genes are scored and checked against the floor before the preparation of 37 to 47 minutes starts.
- The template is prepared again for every sample. The preparation depends on the template and the tasks only. It is done once, saved and reused, which is possible because preparation and extraction are separate.
- Gurobi is not available. Both extractions are mixed-integer problems. On Human-GEM, GLPK completed a benchmark extraction in 2182 s with a time-limited result (Jaccard 0.892 against Gurobi; Human-GEM `38567ab8` prepared without a task list and with scaled stoichiometry, series `1+1`, `time_limit=900`, a different input from the one in this workflow).
- The task list is missing. Without a task list there is nothing to repair against, and the extraction can remove capabilities that were never checked.
:::

## See also

- [Human-GEM guide: GEM extraction using ftINIT](https://sysbiochalmers.github.io/Human-GEM-guide/gem_extraction/): the same workflow in MATLAB, maintained with the model.
- [Human-GEM guide: extraction from single-cell data](https://sysbiochalmers.github.io/Human-GEM-guide/gem_extraction_sc/).
- [Quality control](quality-control.md): checking the model that results.
