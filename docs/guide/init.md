# Context-specific models with ftINIT

A genome-scale model describes what an organism can do. tINIT and ftINIT reduce it to what a particular sample (a tissue, a cell line, a condition) appears to be doing, from expression data plus a list of metabolic tasks that the result must be able to perform.

The workflow uses Human-GEM and the RNA-seq data that Human-GEM provides, in both toolboxes.

## Choice of method

ftINIT is the recommended method, and the workflow here uses it.

Use tINIT (`getINITModel`) only to reproduce a model that was built with it. tINIT is supported and is not scheduled for removal. It issues a `RAVEN:legacyMethod` notice, which states that it is not intended for new work. Silence the notice with `warning('off','RAVEN:legacyMethod')`.

tINIT is MATLAB-only. RAVEN includes it for the models already built with it; raven-toolbox, an implementation without such an installed base, includes ftINIT only. A tINIT model has to be reproduced in MATLAB.

## Relation between tINIT and ftINIT

The two methods are separate implementations that share no algorithm code. In the table, the reaction-scoring and task gap-filling entries differ between the two methods only because the two entry points call their shared functions with different settings, not because two implementations exist.

| Aspect | tINIT | ftINIT |
|---|---|---|
| Entry point | `getINITModel` | `prepINITModel`, then `ftINIT` |
| Reaction scoring | `scoreModel` (fixed isozyme and complex scoring, `dataPrecedence` `'reaction'`) | `scoreModel`, `groupRxnScores` |
| Core mixed-integer linear program (MILP) | `runINIT` | `ftINITInternalAlg`, scheduled by `getINITSteps` |
| Task gap-filling | `fitTasks` | `fitTasks` (`gapFillMode` `'preMerged'`), `ftINITFillGaps` |
| Gene pruning | inline in `getINITModel` | `removeLowScoreGenes` |

What they share is general RAVEN machinery, nothing specific to the method: `checkTasks` and `getEssentialRxns` decide which tasks are feasible and which reactions they need, and below these are `parseTaskList`, `simplifyModel`, the solver layer and the model-manipulation and I/O functions.

`scoreModel` is one function for both. `getINITModel` calls it with a single operator for both `and` and `or` in a grRule and `dataPrecedence` `'reaction'` (the settings the original tINIT algorithm needs), converting an unmeasured gene's score from `NaN` to `-Inf` afterward. `ftINIT` calls it with the general defaults. Task gap-filling is likewise one `fitTasks` loop for both. `getINITModel` uses the default `gapFillMode` (`'merge'`, backed by `fillGaps`). `ftINIT` passes `'preMerged'` (backed by `ftINITFillGaps`, since its reference model already contains the sample's own reactions and needs no per-task merge). The MILP formulation (`fillGaps` merging per task, `ftINITFillGaps` expecting a pre-merged model) is the one place where gap-filling differs, not `getINITModel` against `ftINIT` themselves.

## Reference run

The outputs in this workflow come from one run made by hand. Other guide pages are re-executed by the [Executed examples](index.md#executed-examples) workflow whenever a guide page, the example data, the runner, the workflow or a submodule changes, and once a week; the outputs here are not, because preparing Human-GEM took 47 minutes in MATLAB and 37 minutes in Python, and the MATLAB run produced a 174 MB artefact, which no documentation build should attempt. The numbers come from one real run (Human-GEM `main` at commit `6812be2a`, RAVEN commit `2d0630e3`, raven-toolbox commit `94f39407`, Gurobi 13.0.1, four cores, 2026-10-30) and are quoted with their wall-clock times for planning.

The same MATLAB workflow, as the model's own documentation presents it and including the comparison of the extracted models, is in the [Human-GEM guide](https://sysbiochalmers.github.io/Human-GEM-guide/gem_extraction/), which is maintained alongside the model.

## Functions

| MATLAB | Python | Purpose |
|---|---|---|
| `prepINITModel` | `prep_init_model` | the once-per-template preparation |
| `parseTaskList` | `parse_task_list` | the tasks the extracted model must satisfy |
| `getINITSteps` | `get_init_steps` | the step definitions (`1+0`, `1+1`, …) |
| `ftINIT` | `ftinit` | the staged extraction |
| `scoreModel` | `score_reactions_from_genes` | gene scores → reaction scores |
| no equivalent | `gene_scores_from_expression` | expression → gene scores |
| `runINIT`, `getINITModel` | no equivalent | tINIT, for reproducing models built with it |
| `removeLowScoreGenes` | `remove_low_score_genes` | prune negative-scoring genes from gene-protein-reaction rules (GPRs) |
| `parseHPA`, `parseHPArna` | `parse_hpa`, `parse_hpa_rna` | read Human Protein Atlas (HPA) dumps |
| no equivalent | `hpa_gene_scores`, `rna_gene_scores` | HPA levels or transcripts per million (TPM) to gene scores |
| `checkTasks` | `check_tasks` | confirm that the result performs the tasks |

## Setup

Human-GEM ships everything needed except the toolbox:

<!-- run-examples: skip -->

```bash
git clone --depth=1 https://github.com/SysBioChalmers/Human-GEM.git
```

| File | What it is |
|---|---|
| `model/Human-GEM.mat` (or `.xml`, `.yml`) | the template: 12 748 reactions, 2 870 genes |
| `model/reactions.tsv` | reaction annotations, including which reactions are spontaneous |
| `data/metabolicTasks/metabolicTasks_Essential.txt` | 57 tasks the extracted model must pass |
| `data/datasets/Hart2015_RNAseq.txt` | TPM for five cell lines: DLD1, GBM, HCT116, HELA, RPE1 |

Both extractions are mixed-integer problems. On Human-GEM, GLPK completed a benchmark extraction in 2182 s with a time-limited result (Jaccard 0.892 against Gurobi), so set Gurobi up first ([Solvers and configuration](solvers.md)). That benchmark used Human-GEM `38567ab8` (cleaned), the no-task scaled prep, series `1+1` and `time_limit=900`, a different input from the `6812be2a` template with task preparation used here. In raven-toolbox, without `time_limit`, the scheduled runs of a series keep their own limits (120 s and 5000 s, plus a 5 s first run in the last step of `1+1` and `2+1`; 10000 s for `full`, which runs once), for GLPK as for Gurobi. With `setRavenSolver('glpk')`, RAVEN does not pass the `TimeLimit` of the schedule to GLPK: `optimizeProb` sets a 1000 s limit on every GLPK MILP.

## Template preparation

The preparation finds the task-essential reactions, classifies every reaction into omics-independent categories, merges linear stretches, and rescales the stoichiometry to a narrower coefficient range, which is not needed for feasibility at the default `big_m` and shortens the run (83 s against 157 s in the [calibration](../parameter-tuning/studies/init-param-calibration.md)). It depends only on the template and the task list, and not on the expression data, so it is done once and reused for every sample.

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

Human-GEM also has a wrapper, `prepHumanModelForftINIT`, which reads those two files; it needs Human-GEM 2.0.1 or later.
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

Reading Human-GEM from the Systems Biology Markup Language (SBML) file alone takes about 11 seconds, and the preparation itself 37 minutes in Python and 47 minutes in MATLAB. The two preparations were separate Slurm jobs on the same node type with four cores each. MATLAB used a pool of 4 workers and Python ran with `processes = 1`, so the two times compare the whole runs, not the code alone. Two things affect the run:

- `prep_init_model` runs cobrapy's flux variability analysis (FVA), which spawns worker processes by default; the Python run above used `processes = 1`. Where worker processes are not permitted (a locked-down Windows machine, some continuous integration (CI) runners), the default fails with `PermissionError: [WinError 5] Access is denied`, and `processes = 1` removes the parallelism and lets the run finish.
- `essential_cache_path` caches the slow task-essential discovery, so a second preparation of the same template skips it.
:::
::::

:::{admonition} Spontaneous reactions
:class: note

Pass the list of spontaneous reactions. ftINIT keeps every reaction passed as spontaneous in every extracted model, whatever the data say. Other reactions without a gene rule are kept only where the optimisation needs them, so they can differ from sample to sample. In Human-GEM, `spontaneous` marks reactions that need no enzyme. That includes diffusion: transport between cytosol and nucleus through the nuclear pores, and gases and water (O2, CO2, H2O, NH3, H2O2, NO, H2S) crossing membranes. Leaving out the list lets ftINIT drop such transports in some samples. The model then uses other routes. For example, without the dCTP transport into the nucleus, deoxycytidine kinase (DCK) becomes essential for DNA synthesis, which is an artefact of the extraction and not biology.
:::

## Expression data

RAVEN takes one struct: the genes, the sample names, and a genes × samples matrix of levels. `threshold` is the level above which a gene counts as expressed; when it is left out, the mean across samples is used per gene.

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

The two steps are separate in Python: `gene_scores_from_expression` applies RAVEN's rule (5·ln(level / reference), clamped to [−5, 10]) and `score_reactions_from_genes` maps the result through the GPRs. Because the steps are separate, any other source of gene scores (HPA via `hpa_gene_scores`, proteomics, a curated list) feeds the same second step.

The clamp explains why two samples that differ widely can produce nearly the same model:

<!-- run-examples: skip -->

```python
print(gene_scores_from_expression({"a": 12.0, "b": 0.5, "c": 3.0}, reference=3.0))
```

```text
{'a': 6.93, 'b': -5.0, 'c': 0.0}
```

`b` computes to −8.96 and is returned at the floor; a gene exactly at its reference scores zero, which is neither in nor out.
:::
::::

### Scores from the Human Protein Atlas

A transcript table is one source of gene scores. The Human Protein Atlas is another, and both toolboxes read it directly. [`hpa-sample.tsv`](../data/hpa-sample.tsv) is a ten-row excerpt in HPA's proteomics format: the six columns the parsers expect, five human genes across two tissues, with the levels chosen so each category appears. A real dump is `normal_tissue.tsv` from [proteinatlas.org](https://www.proteinatlas.org/about/download).

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

`parseHPA` returns a struct, not a table. `genes` and `geneNames` hold the Ensembl ids and the symbols, `tissues` and `celltypes` are parallel arrays with one entry per tissue and cell-type combination, not per tissue, and `gene2Level` is a sparse genes-by-combination matrix whose values index into `levels`. Reading a level therefore takes two steps, the same indirection `model.metComps` uses in [Model structure and identifiers](model-structure.md).

The `version` argument is accepted and ignored: the format is inferred from the column headers. `hpaData` is what `ftINIT` takes as its fourth positional argument, in place of `transcrData`.
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

`parse_hpa` returns an `HPAData` wrapping a tidy pandas DataFrame on `.df`, one row per gene, tissue and cell type, with the columns renamed to `gene_id`, `gene_name`, `tissue`, `celltype`, `level` and `reliability`, so ordinary grouping and filtering apply before any of it becomes a score. `tissues()` and `celltypes()` save writing the corresponding queries.

MATLAB's parallel arrays plus a sparse index matrix answer "what is the level of gene i in combination j" directly; the DataFrame answers "which rows belong to this tissue". Neither holds anything the other does not.
:::
::::

### Levels to numbers

HPA reports a category and not a quantity, so a level has to become a number before it can be used in scoring.

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

The mapping is exposed as `HPA_LEVEL_SCORES` and is replaced by passing `level_scores=`. Both vocabularies are covered: `High`, `Medium`, `Low` and `Not detected` for expression, and `Strong`, `Moderate`, `Weak` and `Negative` for antibody staining, scoring the same.

In MATLAB there is no separate step: `scoreModel` takes `hpaData` and applies the mapping internally.
:::
::::

A negative score is a statement and not a missing value. `Not detected` scores -8, which pushes a reaction towards exclusion. A gene absent from the tissue is omitted from the result, and the reaction scorer then uses its `no_gene_score`. The two cases produce different models.

### One gene, several cell types

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

`"best"` takes the maximum and is the default, matching RAVEN. `"average"` takes the mean. The maximum states what the tissue is capable of, the mean what it does across the cells in it. Passing `celltype=` selects one cell type, so the choice does not arise.
:::
::::

`parseHPArna` and `parse_hpa_rna` read the RNA-seq dump, whose header is `Gene`, `Gene name`, `Tissue` followed by the TPM columns. Those are quantities already, so `rna_gene_scores` applies the same logarithmic rule as `gene_scores_from_expression` and not a level mapping. Both sources end at a gene-to-score mapping, which `score_reactions_from_genes` applies to the GPRs.

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

Two argument errors fail without naming the argument at fault:

- `hpaData` is the fourth positional argument. When it is skipped, the string `'transcrData'` is taken as `hpaData` and the expression struct is assigned to `transcrData` by position.
- the step list is `'INITSteps'` and not `'steps'`. An unrecognised name is taken as a positional value, and the misleading error message `Metabolomics contains the same metabolite multiple times` appears.
:::
:::{tab-item} 🐍 Python
:sync: python

<!-- run-examples: skip -->

```python
from raven_toolbox.init import ftinit

context = ftinit(prep, rxn_scores=rxn_scores, series="1+0", gene_scores=gene_scores)
print(len(context.reactions), "reactions,", len(context.genes), "genes")
```

`ftinit` takes the reaction scores directly and not the expression struct, so the scoring is a separate step. `gene_scores` is optional and prunes negative-scoring genes from the GPRs that survive; `fill_gaps=False` skips the task repair.
:::
::::

### Series `1+0` and `1+1`

`1+0` leaves out most reactions that have no gene rule; in this sample it ran in 124 s in Python and 797 s in MATLAB. `1+1` adds a second optimisation over those reactions. The run shown uses `1+0`: 12 748 → 9 543 reactions and 2 870 → 1 783 genes in Python (124 seconds), 12 748 → 9 544 reactions and 2 870 → 1 785 genes in MATLAB (797 seconds).

## Checking the extracted model

An extracted model is a hypothesis. The first check is the tasks the model was built to satisfy, which is also the least expensive check.

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

Compare the result against the template and against the other samples: [Quality control](quality-control.md) covers the structural checks, and the Human-GEM guide's [GEM comparison](https://sysbiochalmers.github.io/Human-GEM-guide/gem_comparison/) covers comparing many extracted models at once.

:::{admonition} Troubleshooting
:class: warning

- Identifiers that do not match. Human-GEM uses ENSEMBL identifiers, and so does `Hart2015_RNAseq.txt`, so no mapping step appears in the workflow. Expression data with symbols or systematic names needs a mapping; score a few genes and check that they are not all at the floor before spending 37 to 47 minutes on the preparation.
- Re-preparing per sample. The preparation depends only on the template and the tasks. Do it once, save it, and reuse it; preparation and extraction are separate, which makes that possible.
- No Gurobi. Both extractions are mixed-integer problems; on Human-GEM, GLPK completed a benchmark extraction in 2182 s with a time-limited result (Jaccard 0.892 against Gurobi; Human-GEM `38567ab8`, no-task scaled prep, series `1+1`, `time_limit=900`, a different input from the one in this workflow).
- A model without capabilities assumed of it. Without a task list there is nothing to repair against, and the extraction is free to remove capabilities that were never checked.
:::

## See also

- [Human-GEM guide: GEM extraction using ftINIT](https://sysbiochalmers.github.io/Human-GEM-guide/gem_extraction/), the same workflow in MATLAB, maintained with the model.
- [Human-GEM guide: extraction from single-cell data](https://sysbiochalmers.github.io/Human-GEM-guide/gem_extraction_sc/).
- [Quality control](quality-control.md), checking the model that comes out.
