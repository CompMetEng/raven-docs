# GEM reconstruction protocol: *Hansenula polymorpha*

The protocol is a complete homology-based reconstruction of `hanpo-GEM`, from the template models as input to a draft that grows on methanol. It follows the published pipeline in order and states the choices that were made.

The protocol complements the [user guide](../guide/index.md). Each page of the guide covers one operation, and the protocol covers a whole reconstruction in order.

The protocol predates the guide, which covers MATLAB and Python, and its steps are MATLAB. The documentation build does not run its commands, unlike the guide pages. Several steps take hours and need data that this site does not ship.

## Protocol steps

| Page | Content |
|---|---|
| [Introduction](reconstruction.md) | what is built, and from what |
| [Materials and installation](materials.md) | software, databases and input files |
| [Importing template models](template-models.md) | the *S. cerevisiae* and *R. toruloides* models that the draft is built from |
| [Draft from homology](homology.md) | BLAST and `getModelFromHomology` ([Reconstruction from homology](../guide/homology.md)) |
| [Biomass composition](biomass.md) | measuring and assembling the biomass equation |
| [Curation of lipid reactions](lipid-curation.md) | the SLIME formalism for the lipid reactions |
| [Gap-filling](gap-filling.md) | making the draft able to produce biomass ([Gap-filling](../guide/gap-filling.md)) |
| [Saving to GitHub and simulating](simulation.md) | writing the model and checking that it grows |
| [Manual curation](manual-curation.md) | correcting gene associations and adding methanol metabolism |

## Related

- [Legacy tutorials](../tutorials/index.md): five shorter exercises from the original RAVEN paper.
- [Reconstruction from homology](../guide/homology.md): the same technique at small scale, in both languages, with every example executed.

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
