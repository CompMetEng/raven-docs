# GEM reconstruction protocol: *Hansenula polymorpha*

A complete homology-based reconstruction of `hanpo-GEM`, followed from start to
finish: it takes template models as input and produces a growing methylotrophic
draft. This is the published pipeline, in order, with the judgement calls left
visible.

It is the counterpart to the [user guide](../guide/index.md). The numbered guide
pages answer "how do I do this one thing"; this protocol answers "what does a
whole reconstruction look like, and in what order".

:::{note} MATLAB only, and not executed here
The protocol predates the dual-language guide and its steps are MATLAB. Its
commands are also not run by the documentation build, unlike the numbered
guide pages; several steps take hours and need data that is not shipped
with this site.
:::

## The steps

| | |
|---|---|
| [Introduction](reconstruction.md) | what is being built, and from what |
| [Materials and installation](materials.md) | software, databases and input files |
| [Import template models](template-models.md) | the *S. cerevisiae* and *R. toruloides* models the draft is built from |
| [Draft from homology](homology.md) | BLAST and `getModelFromHomology`; see also [12. Reconstruction from homology](../guide/homology.md) |
| [Biomass composition](biomass.md) | measuring and assembling the biomass equation |
| [Curation of lipid reactions](lipid-curation.md) | the part that never generalises |
| [Gap-filling](gap-filling.md) | closing the holes; see also [17. Gap-filling](../guide/gap-filling.md) |
| [Save and simulate](simulation.md) | writing the model out and checking it grows |
| [Manual curation](manual-curation.md) | what no function does for you |

## Related

- [Legacy tutorials](../tutorials/index.md), five shorter exercises from the
  original RAVEN paper.
- [12. Reconstruction from homology](../guide/homology.md), the same technique
  at small scale, in both languages, with every example executed.

```{toctree}
:hidden:

reconstruction
materials
template-models
homology
biomass
lipid-curation
gap-filling
simulation
manual-curation
```
