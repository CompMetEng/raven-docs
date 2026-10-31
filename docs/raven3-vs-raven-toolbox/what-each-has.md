# Features specific to each implementation

The page describes the features that exist in raven-toolbox only and the features that exist in RAVEN only.

## Features specific to raven-toolbox

### Model type

A raven-toolbox model is a `cobra.Model`. Every cobrapy function and cobrapy-based package applies to it without conversion. RAVEN uses a MATLAB struct as the model, and `ravenCobraWrapper` converts between that struct and the COBRA Toolbox format.

cobrapy provides flux balance analysis (FBA), flux variability analysis (FVA), knockouts and media handling, in addition to the other functions that the mapping table marks as covered by cobrapy. The mapping table therefore gives a cobrapy entry in place of a raven-toolbox function for the corresponding RAVEN functions.

### KEGG artefact generation

raven-toolbox builds the KEGG reference artefacts: it parses a KEGG release into reaction and compound tables, assembles the reference model, builds the per-KEGG Orthology (KO) FASTA sets and HMM libraries, and derives the phylogenetic distance matrix. RAVEN uses pre-built artefacts and does not produce them.

The artefacts can therefore be rebuilt from a specified KEGG release.

### Checksum registry for binaries and data

Both implementations fetch BLAST+, DIAMOND, HMMER and the KEGG artefacts on demand, do not bundle them, pin a release and check downloads against checksums (see [Download data and binaries](../installation/data-and-binaries.md)).

raven-toolbox has the checksums and the release of each dataset in a registry in its source, which ties each release to the assets it was tested with. RAVEN checks a download against the checksum of the published manifest. When the manifest cannot be read or has no entry for the asset, RAVEN issues a warning and keeps the file unchecked, and an already cached file is reused without a check.

## Features specific to RAVEN

### tINIT

`getINITModel` and `runINIT` are the original tINIT implementation. RAVEN keeps them for models built with them. raven-toolbox has no earlier tINIT models to reproduce, so it implements ftINIT only. A tINIT model has to be reproduced in MATLAB; see [14. Context-specific models with ftINIT](../guide/init.md).

### COBRA Toolbox conversion

`ravenCobraWrapper` converts between the RAVEN and COBRA Toolbox model structures. In raven-toolbox the model is a `cobra.Model`, so no conversion is needed and no equivalent exists.

### Dynamic FBA

`runDynamicFBA` has no raven-toolbox counterpart by design. Python packages cover dynamic FBA ([dfba](https://pypi.org/project/dfba/), [reframed](https://pypi.org/project/reframed/), [mewpy](https://pypi.org/project/mewpy/)), and raven-toolbox does not reimplement it.

### MATLAB-specific functions

RAVEN has MATLAB-specific infrastructure: path management (`addRavenToUserPath`, `findRAVENroot`), argument handling (`parseRAVENargs`, `convertCharArray`), progress and printing (`setRavenProgress`, `printOrange`) and the solver abstraction (`optimizeProb`, `setRavenSolver`). cobrapy's solver interface (optlang) takes the place of the solver abstraction.
