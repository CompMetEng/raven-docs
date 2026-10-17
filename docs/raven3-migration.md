# RAVEN 2 to RAVEN 3

:::{admonition} If you read nothing else
:class: important

Run `checkRaven` (replaces `checkInstallation`) right after upgrading: it
offers to fetch any missing on-demand binaries/data, and its checks catch
several of the changes below before your scripts do. Beyond that, the two
changes most likely to break silently rather than error are homology/KEGG
reconstruction returning a different draft model from the same call
([§7](raven3-migration/formats-and-reconstruction.md#kegg-reconstruction)), and WoLF PSORT-based localization scores having
no in-toolbox migration path ([§3](raven3-migration/backward-incompatible.md#backward-incompatible-changes)).
:::

This guide describes what changed between RAVEN 2 and RAVEN 3. It is written
for existing RAVEN 2 users who need to know what will break in their scripts,
what moved, what was removed outright, and what new capabilities are
available.

**Versions covered:** RAVEN 2 as of its last release, **2.11.3**, and RAVEN 3.

RAVEN 3 is a deliberate breaking release: the codebase was reorganized, a large
number of low-value or duplicate functions were removed, several external
dependencies were dropped, and the calling convention for optional function
arguments changed almost everywhere. None of this was accidental; see the
project's [v3 development review](https://github.com/CompMetEng/RAVEN/blob/develop/docs/v3_review.md)
for the rationale, but it means that **most non-trivial RAVEN 2 scripts need to
be checked**, even though the core reconstruction and analysis behavior is
mostly the same.

:::{note} This is the MATLAB-to-MATLAB axis
This page is about RAVEN 2 → RAVEN 3, both MATLAB. How the Python package
differs from the MATLAB one is a separate question, answered in
[RAVEN vs. raven-toolbox](raven3-vs-raven-toolbox.md).
:::

---

(calling-convention)=
## Calling convention: positional or named arguments

RAVEN 2 functions took optional arguments strictly positionally
(`f(model, a, b, c)`), which made it easy to lose track of argument order and
impossible to skip an early optional argument to set a later one without also
specifying all of the ones in between.

RAVEN 3 introduces `utils/parseRAVENargs.m`, used by 112 functions across the
toolbox. Required leading arguments stay as explicit, positional parameters;
everything optional is collected into `varargin` and can be supplied three ways,
interchangeably:

```matlab
removeReactions(model, rxnList, true, true, true)                       % positional (RAVEN 2 style, still works)
removeReactions(model, rxnList, "removeUnusedGenes", true)              % named
removeReactions(model, rxnList, true, "removeUnusedComps", true)        % hybrid
```

The rule: parsing scans for the first argument that is a string matching a known
parameter name. Everything before that point is assigned positionally, in the
order the function's `parseRAVENargs` specification declares; everything from
that point on must be valid name-value pairs.

**This means old positional calls keep working, if the function's new
parameter order still matches the old positional order.** In every function
spot-checked for this guide (`importModel`, `exportModel`,
`exportToExcelFormat`, `removeReactions`, `ftINIT`, `fillGaps`, `fitTasks`,
`getModelFromHomology`, `addIdentifierPrefix`/`removeIdentifierPrefix`, and
`exportForGit`), new optional parameters were appended at the end of the list,
so old positional calls keep working unchanged.

One caveat from the parser's own documentation: if a positional argument you're
passing is itself a string that happens to match one of the function's parameter
names, use the explicit name-value form for that argument to avoid ambiguity.

---

Start with the [upgrade checklist](#upgrade-checklist) below, then read
[Backward-incompatible changes](raven3-migration/backward-incompatible.md#backward-incompatible-changes); it lists
everything that can break. The detail pages after it go into the detail
behind each item.

---

(upgrade-checklist)=
## Upgrade checklist

1. Update to RAVEN 3.0.0 (or later) and run `checkRaven` (replaces
   `checkInstallation`); it will offer to fetch any missing on-demand
   binaries/data (§11).
2. Search your scripts for the functions listed in [§4](raven3-migration/structure-and-renames.md#removed-functionality)
   (removed) and [§5](raven3-migration/structure-and-renames.md#renamed-merged-and-consolidated-functions)
   (renamed/merged) and update or remove those calls.
3. If you use `getModelFromKEGG`/`getKEGGModelForOrganism` or
   `getModelFromHomology`: expect a different draft reconstruction even from an
   unmodified call: default cutoffs, the KEGG data source, and the homology
   best-hit criterion all changed ([§7](raven3-migration/formats-and-reconstruction.md#kegg-reconstruction)). Rebuild and
   re-validate any KEGG- or homology-derived draft models.
4. If you use `.xlsx` curation templates or `importExcelModel`: convert your
   curation data to the `.tsv` format `curateModelFromTables` expects; there
   is no drop-in Excel importer ([§6](raven3-migration/formats-and-reconstruction.md#excel-io)).
5. If you use WoLF PSORT-based localization scores: switch to one of the
   modern predictors (DeepLoc2, MULocDeep, COMPARTMENTS, UniProt); there is no
   in-toolbox migration path ([§10](raven3-migration/new-and-environment.md#new-functionality)).
6. If your workflows include metabolic-task gap-filling (`fitTasks`,
   `checkTasks`, `ftINIT`): re-run and check task pass/fail results; a fixed
   bug means a previously "passing" task can now correctly fail
   ([§9](raven3-migration/new-and-environment.md#ftinit)).
7. If your model files are under version control (YAML/SBML): expect diffs on
   the next export even with no content changes (quoting style, EC-code
   annotation, ΔG fields; [§6](raven3-migration/formats-and-reconstruction.md#file-formats-and-model-io)).
8. Re-run your own test suite / validation pipeline and diff key outputs
   (model size, growth rate, task results) against your RAVEN 2 baseline
   before trusting RAVEN 3 results in production.

---

## Detail pages

| | |
|---|---|
| [§1–5. What moved, what's gone, and what's renamed](raven3-migration/structure-and-renames.md) | The folder reorganization, every removed function and subsystem, and every renamed or merged function. |
| [§3. Backward-incompatible changes](raven3-migration/backward-incompatible.md) | The full punch list: what will error, what will silently differ, what will warn, and what changed about installation. |
| [§6–8. File formats, reconstruction, and GPR parsing](raven3-migration/formats-and-reconstruction.md) | SBML, Excel and YAML I/O; the KEGG and homology reconstruction pipelines; the new grRule parser. |
| [§9–12. New functionality, dependencies, and error handling](raven3-migration/new-and-environment.md) | Gap-filling and ftINIT changes, everything purely additive, the toolbox dependency comparison, and error/warning handling. |

```{toctree}
:hidden:

raven3-migration/structure-and-renames
raven3-migration/backward-incompatible
raven3-migration/formats-and-reconstruction
raven3-migration/new-and-environment
```
