# GEM reconstruction protocol: *Hansenula polymorpha*

This protocol is a complete homology-based reconstruction of `hanpo-GEM`, followed from start to finish: it takes template models as input and produces a growing methylotrophic draft. It is the published pipeline, in order, and states the choices made.

It is the counterpart to the [user guide](../guide/index.md). Each numbered guide page covers one operation; this protocol covers a whole reconstruction in order.

The protocol predates the dual-language guide and its steps are MATLAB. The documentation build does not run its commands, unlike the numbered guide pages; several steps take hours and need data that is not shipped with this site.

## Protocol steps

| Page | Content |
|---|---|
| [Introduction](reconstruction.md) | what is being built, and from what |
| [Materials and installation](materials.md) | software, databases and input files |
| [Importing template models](template-models.md) | the *S. cerevisiae* and *R. toruloides* models the draft is built from |
| [Draft from homology](homology.md) | BLAST and `getModelFromHomology`; see also [12. Reconstruction from homology](../guide/homology.md) |
| [Biomass composition](biomass.md) | measuring and assembling the biomass equation |
| [Curation of lipid reactions](lipid-curation.md) | SLIME formalism for the lipid reactions |
| [Gap-filling](gap-filling.md) | making the draft able to produce biomass; see also [17. Gap-filling](../guide/gap-filling.md) |
| [Saving to GitHub and simulating](simulation.md) | writing the model out and checking it grows |
| [Manual curation](manual-curation.md) | fixing gene associations and adding methanol metabolism |

## Related

- [Legacy tutorials](../tutorials/index.md), five shorter exercises from the original RAVEN paper.
- [12. Reconstruction from homology](../guide/homology.md), the same technique at small scale, in both languages, with every example executed.

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
