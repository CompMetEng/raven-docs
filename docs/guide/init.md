# 14. Context-specific models with ftINIT

A genome-scale model describes what an organism *can* do. tINIT and ftINIT cut it
down to what a particular sample (a tissue, a cell line, a condition) appears to
be doing, from expression data plus a list of metabolic tasks the result must
still be able to perform.

This page walks through it on **Human-GEM**, with the RNA-seq data Human-GEM
ships, in both toolboxes.

:::{tip} Which one should I use?
**ftINIT.** It is the recommended method, and everything below uses it.

Use tINIT (`getINITModel`) only to reproduce a model that was built
with it. It remains supported and is not scheduled for removal, but it
issues a `RAVEN:legacyMethod` notice to say it is not what new work should
use. Silence it with `warning('off','RAVEN:legacyMethod')`.

**tINIT is MATLAB-only.** RAVEN keeps it for the models already built with
it; raven-toolbox, a new implementation with no such installed base, carries
ftINIT and nothing else. A tINIT model has to be reproduced in MATLAB.
:::

Despite the shared name, the two are **separate implementations that share no
algorithm code**. Reaction scoring and task gap-filling look like separate
implementations in the table below only because the two entry points call
their shared functions with different settings, not because two
implementations exist:

| | tINIT | ftINIT |
|---|---|---|
| Entry point | `getINITModel` | `prepINITModel`, then `ftINIT` |
| Reaction scoring | `scoreModel` (fixed isozyme/complex scoring, `dataPrecedence` `'reaction'`) | `scoreModel`, `groupRxnScores` |
| Core MILP | `runINIT` | `ftINITInternalAlg`, scheduled by `getINITSteps` |
| Task gap-filling | `fitTasks` | `fitTasks` (`gapFillMode` `'preMerged'`), `ftINITFillGaps` |
| Gene pruning | inline in `getINITModel` | `removeLowScoreGenes` |

What they do share is RAVEN's general machinery rather than anything specific to
the method: `checkTasks` and `getEssentialRxns` decide which tasks are feasible
and which reactions they need, and beneath that are `parseTaskList`,
`simplifyModel`, the solver layer and the model-manipulation and I/O functions.

`scoreModel` is one function for both: `getINITModel` calls it with a single
operator for both `and`/`or` in a grRule and `dataPrecedence` `'reaction'` (the
settings the original tINIT algorithm needs), converting an unmeasured gene's
score from `NaN` to `-Inf` afterward; `ftINIT` calls it with the general
defaults. Task gap-filling is likewise one `fitTasks` loop for both:
`getINITModel` uses the default `gapFillMode` (`'merge'`, backed by
`fillGaps`), `ftINIT` passes `'preMerged'` (backed by `ftINITFillGaps`, since
its reference model already contains the sample's own reactions and needs no
per-task merge). That MILP-formulation split (`fillGaps` merging per task vs.
`ftINITFillGaps` expecting a pre-merged model) is the one place gap-filling
genuinely differs, not `getINITModel` vs. `ftINIT` themselves.

:::{warning} The outputs on this page were produced by hand, not by the build
Every other page in this guide is re-executed on every commit. This one is
not: preparing Human-GEM took **113 minutes** in MATLAB and **126 minutes**
in Python, the MATLAB run producing a **159 MB** artefact, which no
documentation build should attempt. The numbers below come
from one real run (Human-GEM `main`, RAVEN 3, Gurobi 13.0.2) and
are quoted with their wall-clock so you can plan around them.

For the same MATLAB workflow as the model's own documentation presents it,
including comparison of the extracted models, see the
[Human-GEM guide](https://sysbiochalmers.github.io/Human-GEM-guide/gem_extraction/),
which is maintained alongside the model.
:::

### Functions on this page

| MATLAB | Python | |
|---|---|---|
| `prepINITModel` | `prep_init_model` | the once-per-template preparation |
| `parseTaskList` | `parse_task_list` | the tasks the extracted model must satisfy |
| `getINITSteps` | `get_init_steps` | the step definitions (`1+0`, `1+1`, …) |
| `ftINIT` | `ftinit` | the staged extraction |
| `scoreModel` | `score_reactions_from_genes` | gene scores → reaction scores |
| no equivalent | `gene_scores_from_expression` | expression → gene scores |
| `runINIT`, `getINITModel` | no equivalent | the legacy tINIT, for reproducing older models |
| `removeLowScoreGenes` | `remove_low_score_genes` | prune negative-scoring genes from GPRs |
| `parseHPA`, `parseHPArna` | `parse_hpa`, `parse_hpa_rna` | read Human Protein Atlas dumps |
| no equivalent | `hpa_gene_scores`, `rna_gene_scores` | HPA levels or TPM to gene scores |
| `checkTasks` | `check_tasks` | confirm the result still does what it must |

## Setup

Human-GEM ships everything needed except the toolbox:

<!-- run-examples: skip -->

```bash
git clone --depth=1 https://github.com/SysBioChalmers/Human-GEM.git
```

| File | What it is |
|---|---|
| `model/Human-GEM.mat` (or `.xml`, `.yml`) | the template: 12 931 reactions, 2 848 genes |
| `model/reactions.tsv` | reaction annotations, including which reactions are spontaneous |
| `data/metabolicTasks/metabolicTasks_Essential.txt` | 57 tasks the extracted model must still pass |
| `data/datasets/Hart2015_RNAseq.txt` | TPM for five cell lines: DLD1, GBM, HCT116, HELA, RPE1 |

Both extractions are mixed-integer problems, so **GLPK will not do**: set Gurobi
up first ([6. Solvers and configuration](solvers.md)).

## 14.1 Prepare the template: once

The preparation finds the task-essential reactions, classifies every reaction
into omics-independent categories, merges linear stretches, and rescales the
stoichiometry so that a single big-M works across the model. It depends only on
the template and the task list, **not on your data**, so it is done once and
reused for every sample.

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
prepData.mat: 159 MB
```

Human-GEM also has a wrapper, `prepHumanModelForftINIT`, which reads those
two files for you; it needs Human-GEM 2.0.1 or later.
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
load 115s
prep_init_model 7552s
```

Reading Human-GEM from SBML alone takes about **two minutes**, and the
preparation itself **126 minutes**, the same order as MATLAB's 113, on the
same machine and solver. Two things affect the run:

- `prep_init_model` runs cobrapy's FVA, which spawns worker processes. Where
  that is not permitted (a locked-down Windows machine, some CI runners), it
  fails with `PermissionError: [WinError 5] Access is denied`. Setting
  `processes = 1` trades the parallelism for a run that finishes.
- `essential_cache_path` caches the slow task-essential discovery, so a
  second preparation of the same template skips it.
:::
::::

:::{note} Pass the spontaneous reactions
ftINIT keeps every reaction passed as
spontaneous in every extracted model, whatever the data say. Other reactions
without a gene rule are kept only where the optimisation needs them, so they can
differ from sample to sample. In Human-GEM, `spontaneous` marks reactions that need
no enzyme. That includes diffusion: transport between cytosol and nucleus through
the nuclear pores, and gases and water (O2, CO2, H2O, NH3, H2O2, NO, H2S) crossing
membranes. Leaving out the list lets ftINIT drop such transports in some
samples. The model then
falls back on other routes. For example, without the dCTP transport into the nucleus,
deoxycytidine kinase (DCK) becomes essential for DNA synthesis, which is an artefact
of the extraction rather than biology.
:::

## 14.2 Bring in the expression data

RAVEN wants one struct: the genes, the sample names, and a genes × samples matrix
of levels. `threshold` is the level above which a gene counts as expressed; leave
it out and the mean across samples is used per gene instead.

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

The two steps are separate in Python: `gene_scores_from_expression` applies
RAVEN's rule (**5·ln(level / reference)**, clamped to [−5, 10]) and
`score_reactions_from_genes` pushes the result through the GPRs. Splitting
them means any other source of gene scores (HPA via `hpa_gene_scores`,
proteomics, a curated list) feeds the same second step.

Seeing the clamp directly explains why two very different samples can
produce nearly the same model:

<!-- run-examples: skip -->

```python
print(gene_scores_from_expression({"a": 12.0, "b": 0.5, "c": 3.0}, reference=3.0))
```

```text
{'a': 6.93, 'b': -5.0, 'c': 0.0}
```

`b` computes to −8.96 and comes back at the floor; a gene exactly at its
reference scores zero, neither in nor out.
:::
::::

### Scores from the Human Protein Atlas

A transcript table is one source of gene scores. The Human Protein Atlas is
another, and both toolboxes read it directly.
[`hpa-sample.tsv`](../data/hpa-sample.tsv) is a ten-row excerpt in HPA's
proteomics format: the six columns the parsers expect, five human genes across
two tissues, with the levels chosen so each category appears. A real dump is
`normal_tissue.tsv` from
[proteinatlas.org](https://www.proteinatlas.org/about/download).

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

`parseHPA` returns a struct rather than a table. `genes` and `geneNames`
hold the Ensembl ids and the symbols, `tissues` and `celltypes` are parallel
arrays with one entry per tissue and cell-type combination rather than per
tissue, and `gene2Level` is a sparse genes-by-combination matrix whose values
index into `levels`. Reading a level therefore takes two steps, the same
indirection `model.metComps` uses in
[2. Model structure and identifiers](model-structure.md).

The `version` argument is accepted and ignored: the format is inferred from
the column headers. `hpaData` is what `ftINIT` takes as its fourth positional
argument, in place of the `transcrData` used above.
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

`parse_hpa` returns an `HPAData` wrapping a tidy pandas DataFrame on `.df`,
one row per gene, tissue and cell type, with the columns renamed to
`gene_id`, `gene_name`, `tissue`, `celltype`, `level` and `reliability`, so
ordinary grouping and filtering apply before any of it becomes a score.
`tissues()` and `celltypes()` save writing the obvious queries.

MATLAB's parallel arrays plus a sparse index matrix answer "what is the level
of gene i in combination j" directly; the DataFrame answers "show me every
row for this tissue". Neither holds anything the other does not.
:::
::::

### Levels to numbers

HPA reports a category, not a quantity, so a level has to become a number before
the scoring above can use it.

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
{'High': 20.0, 'Medium': 15.0, 'Low': 10.0, 'Not detected': -8.0, 'Strong': 20.0, 'Moderate': 15.0, 'Weak': 10.0, 'Negative': -8.0}
  ENSG00000067225  +20.0
  ENSG00000106633  +15.0
  ENSG00000111640  +20.0
  ENSG00000156515  +10.0
  ENSG00000159399  -8.0
```

The mapping is exposed as `HPA_LEVEL_SCORES` and is replaced by passing
`level_scores=`. Both vocabularies are covered: `High`/`Medium`/`Low`/`Not
detected` for expression, and `Strong`/`Moderate`/`Weak`/`Negative` for
antibody staining, scoring the same.

On the MATLAB side there is no separate step: `scoreModel` takes `hpaData`
and applies the mapping internally.
:::
::::

A negative score is a statement, not a missing value. `Not detected` scores
**-8**, which pushes a reaction towards exclusion; a gene absent from the tissue
is omitted from the result instead, and the reaction scorer falls back to its
`no_gene_score`. The two produce different models.

### One gene, several cell types

A tissue has several cell types, and a gene can be measured differently in each.
`PKM` in the excerpt is `High` in hepatocytes and `Low` in bile duct cells.

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

`"best"` takes the maximum and is the default, matching RAVEN. `"average"`
takes the mean. The maximum states what the tissue is capable of, the mean
what it does across the cells in it. Passing `celltype=` selects one and the
question does not arise.
:::
::::

`parseHPArna` and `parse_hpa_rna` read the RNA-seq dump instead, whose header is
`Gene`, `Gene name`, `Tissue` followed by the TPM columns. Those are quantities
already, so `rna_gene_scores` applies the same logarithmic rule as 14.2 rather
than a level mapping. Both routes end at a gene-to-score mapping, which is what
`score_reactions_from_genes` walks the GPRs with.

## 14.3 Extract a model for one sample

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
9595 rxns, 1761 genes
```

Two argument traps, both of which fail without mentioning the argument you
got wrong:

- `hpaData` is the **fourth positional** argument. Skip it and the expression
  struct lands on `metabolomicsData`, reporting `Metabolomics contains the
  same metabolite multiple times`.
- the step list is `'INITSteps'`, not `'steps'`. An unrecognised name is
  taken as a positional value, and you get that same misleading error.
:::
:::{tab-item} 🐍 Python
:sync: python

<!-- run-examples: skip -->

```python
from raven_toolbox.init import ftinit

context = ftinit(prep, rxn_scores, series="1+0", gene_scores=gene_scores)
print(len(context.reactions), "reactions,", len(context.genes), "genes")
```

`ftinit` takes the reaction scores directly rather than the expression
struct, which is why the scoring is a separate step above. `gene_scores` is
optional and prunes negative-scoring genes from the GPRs that survive;
`fill_gaps=False` skips the task repair.
:::
::::

**`1+0` or `1+1`?** `1+0` leaves out most reactions that have no gene rule and
takes 30–60 s per sample; `1+1` adds a second optimisation over those reactions,
takes two to three times longer, and gives a smaller model. The run above is
`1+0`: **12 931 → 9 595 reactions and 2 848 → 1 761 genes, in 70 seconds.**

## 14.4 Check what came out

An extracted model is a hypothesis. The tasks it was built to satisfy are the
first thing to re-check, and the least expensive.

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

Then compare the result against the template and against the other samples:
[9. Quality control](quality-control.md) covers the structural checks, and the
Human-GEM guide's
[GEM comparison](https://sysbiochalmers.github.io/Human-GEM-guide/gem_comparison/)
covers comparing many extracted models at once.

:::{warning} What can go wrong
- **Identifiers that do not match.** Human-GEM speaks ENSEMBL, and so does
  `Hart2015_RNAseq.txt`, which is why no mapping step appears above. With
  symbols or systematic names you need one; score a handful of genes and
  check they are not all at the floor before spending two hours on the
  preparation.
- **Re-preparing per sample.** The preparation depends only on the template
  and the tasks. Do it once, save it, and reuse it; separating preparation
  from extraction is what makes that possible.
- **No MILP solver.** Both extractions are mixed-integer; GLPK cannot.
- **A model that no longer does what you assumed.** Without a task list there
  is nothing to repair against, and the extraction is free to remove
  capabilities you never thought to check.
:::

## See also

- [Human-GEM guide: GEM extraction using ftINIT](https://sysbiochalmers.github.io/Human-GEM-guide/gem_extraction/),
  the same workflow in MATLAB, maintained with the model.
- [Human-GEM guide: extraction from single-cell data](https://sysbiochalmers.github.io/Human-GEM-guide/gem_extraction_sc/).
- [9. Quality control](quality-control.md), checking the model that comes out.
