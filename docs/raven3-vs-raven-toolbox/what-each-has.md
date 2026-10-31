# Features specific to each implementation

## Features specific to raven-toolbox

### Model type

A raven-toolbox model is a `cobra.Model`. Every cobrapy function, and the wider COBRA Python ecosystem, applies to it without conversion. RAVEN uses a MATLAB struct as the model, and `ravenCobraWrapper` converts between that struct and the COBRA Toolbox format.

FBA, FVA, knockouts and media handling, among other functions, are provided by cobrapy and not by raven-toolbox. The mapping table therefore gives a *cobrapy* row, not a raven-toolbox function, for the corresponding RAVEN functions.

### KEGG artefact generation

raven-toolbox builds the KEGG reference artefacts: it parses a KEGG release into reaction and compound tables, assembles the reference model, builds the per-KO FASTA sets and HMM libraries, and derives the phylogenetic distance matrix. RAVEN uses pre-built artefacts and does not produce them.

This makes the KEGG route reproducible for a stated KEGG release, independent of which artefact is currently distributed.

### Further functions

| Area | Description |
|---|---|
| Growth conditions | Apply a named, versioned growth condition to a model. |
| Batch curation | Apply a table of curation edits to a model in one pass. |
| ΔG and SBO annotation | Load and save thermodynamic data through CSV, and assign SBO terms. |
| Biomass helpers | Sum a biomass composition, rescale a pseudoreaction, and scale a fraction to a measured value. |
| Checksummed provisioning | Both toolboxes fetch BLAST+, DIAMOND, HMMER and the KEGG artefacts on demand from the same release and do not bundle them. Only raven-toolbox has the baked registry that pins a release to the exact assets it was tested against; RAVEN resolves from the published release each time. See [Download data and binaries](../installation/data-and-binaries.md). |

## Features specific to RAVEN

### tINIT

`getINITModel` and `runINIT` are the original tINIT implementation. RAVEN keeps them for models built with them. raven-toolbox is a new implementation without such an installed base and provides ftINIT only. A tINIT model has to be reproduced in MATLAB; see [14. Context-specific models](../guide/init.md).

### COBRA Toolbox conversion

`ravenCobraWrapper` converts between the RAVEN and COBRA Toolbox model structures. In Python the model is a `cobra.Model`, so no conversion is needed and no equivalent exists.

### Dynamic FBA

`runDynamicFBA` has no Python counterpart by design. Maintained Python packages cover dynamic FBA ([dfba](https://pypi.org/project/dfba/), [reframed](https://pypi.org/project/reframed/), [mewpy](https://pypi.org/project/mewpy/)), and raven-toolbox does not duplicate them.

### MATLAB-specific functions

A large share of the RAVEN functions are MATLAB housekeeping without a Python counterpart: path management (`addRavenToUserPath`, `findRAVENroot`), argument handling (`parseRAVENargs`, `convertCharArray`), progress and printing (`setRavenProgress`, `printOrange`), and the solver abstraction (`optimizeProb`, `setRavenSolver`), which in Python is the solver interface of cobrapy (optlang).
