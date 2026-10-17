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

**Versions covered:** the latest released RAVEN 2 is **2.11.3**. RAVEN 3 is
unreleased; it is being developed on the `develop3` branch and is targeting
version **3.0.0**. This guide compares `develop3` against RAVEN 2's `develop`
branch (functionally identical to the 2.11.3 release; the commits between
them are only version-bump/tag merges). **This document will be frozen once
3.0.0 is tagged**; until then, `develop3` can still change.

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
| [§2–3. Backward-incompatible changes](raven3-migration/backward-incompatible.md) | The positional-or-named calling convention, and the full punch list: what will error, what will silently differ, what will warn, and what changed about installation. |
| [§6–8. File formats, reconstruction, and GPR parsing](raven3-migration/formats-and-reconstruction.md) | SBML, Excel and YAML I/O; the KEGG and homology reconstruction pipelines; the new grRule parser. |
| [§9–12. New functionality, dependencies, and error handling](raven3-migration/new-and-environment.md) | Gap-filling and ftINIT changes, everything purely additive, the toolbox dependency comparison, and error/warning handling. |

```{toctree}
:hidden:

raven3-migration/structure-and-renames
raven3-migration/backward-incompatible
raven3-migration/formats-and-reconstruction
raven3-migration/new-and-environment
```
