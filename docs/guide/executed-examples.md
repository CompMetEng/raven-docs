# Executed examples

<!-- docs-site: concept-page -->

The [Guide examples](https://github.com/CompMetEng/raven-docs/actions/workflows/examples.yml) workflow runs the code on the task pages, MATLAB and Python separately. It starts when a guide page, the example data or the runner changes, and once a week against the latest RAVEN and raven-toolbox. A run fails when a block raises an error or prints output that differs from the output shown beneath it. The blocks of a page run in order in one session, so a block uses what the preceding blocks made. Reading a page starts at its Setup section.

One page and part of another are not executed. [Reconstruction from KEGG](kegg.md) downloads tens of megabytes and takes minutes, and the Human-GEM steps of [Context-specific models with ftINIT](init.md) take hours. Both pages quote the run that their numbers come from. A few further blocks are marked as not run on their own page, with the reason. The protocol and the legacy tutorials are not executed.
