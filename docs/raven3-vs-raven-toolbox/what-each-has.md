# Features specific to each implementation

The page describes the features that exist in raven-toolbox only and the features that exist in RAVEN only.

## Features specific to raven-toolbox

### Model type

A raven-toolbox model is a `cobra.Model`. Every cobrapy function and cobrapy-based package applies to it without conversion. RAVEN uses a MATLAB struct as the model.

cobrapy provides flux balance analysis (FBA), flux variability analysis (FVA), knockouts and media handling. The [MATLAB vs Python](../matlab-vs-python.md) page gives a cobrapy entry for the corresponding RAVEN functions where cobrapy covers them; [Name differences](../raven3-vs-raven-toolbox.md#name-differences) describes the page. `setExchangeBounds` has two rows in the mapping: `set_exchange_bounds` in raven-toolbox and `cobra.Model.medium` in cobrapy.

### KEGG artefact generation

raven-toolbox builds the KEGG reference artefacts: it parses a KEGG release into reaction and compound tables, assembles the reference model with `build_reference_model`, builds the per-KEGG Orthology (KO) FASTA sets and HMM libraries, and derives the phylogenetic distance matrix. The download of a KEGG release requires a KEGG FTP subscription. The artefacts can be rebuilt from a specified KEGG release.

RAVEN loads published artefacts and does not produce them. `buildGlobalKEGGModel` joins a downloaded bundle onto the reference model, and the phylogenetic distance matrix is a file shipped with RAVEN (`keggPhylDist.mat`). In the mapping, `getModelFromKEGG` corresponds to `build_reference_model`, which loads in RAVEN and builds in raven-toolbox.

### Checksum registry for binaries and data

BLAST+, DIAMOND, HMMER and the KEGG tables are fetched on demand in both implementations and are not bundled. RAVEN bundles other components: the GLPK and libSBML MEX files and `keggPhylDist.mat`. [Download data and binaries](../installation/data-and-binaries.md) describes the download behaviour.

The checksum handling differs:

- raven-toolbox keeps the checksum and release of each dataset and binary in a registry in its source (a version-pinned registry). A fresh download is checked against its checksum. A cached data file is reused without a check unless `ensure_data_file` is called with `verify=True`, which re-checks it and downloads it again on a mismatch; a cached binary is reused without a check. A JSON manifest can be merged into the registries with `raven_toolbox.manifest.load_into_registries`, which reads the path or URL in the environment variable `RAVEN_PYTHON_MANIFEST` when no source is passed. The resolvers load that variable by themselves only while the registry is empty, so with the filled default registries the call is needed.
- RAVEN checks a download against the checksum in the published manifest. A mismatch deletes the file and raises an error. When the manifest cannot be read or has no entry for the asset, RAVEN issues a warning and keeps the file unchecked. A cached file is reused without a check.

### Further functions

Further raven-toolbox features have no RAVEN counterpart in the generated mapping. Examples are `localization.relocate_reactions`, which places reactions in compartments chosen by a curator and repairs the model around the decision, `localization.triage_localization`, and the per-reaction confidence record of the `confidence` module, which scores the facets localization, equation and gene association and stores them in the reaction notes.

## Features specific to RAVEN

### tINIT

`getINITModel` and `runINIT` are the original tINIT implementation. RAVEN keeps them for models built with them. raven-toolbox implements ftINIT only, as a design decision. A tINIT model has to be reproduced in MATLAB; see [Context-specific models with ftINIT](../guide/init.md).

### COBRA Toolbox conversion

`ravenCobraWrapper` converts a model in memory between the RAVEN and COBRA Toolbox structures. A round trip drops some fields. In raven-toolbox the model is a `cobra.Model`, so no in-memory conversion is needed and no equivalent exists. File exchange is described in [Choosing an implementation](../raven3-vs-raven-toolbox.md#choosing-an-implementation); cobrapy writes the COBRA layout.

### Dynamic FBA

`runDynamicFBA` has no raven-toolbox counterpart by design. Python packages cover dynamic FBA ([dfba](https://pypi.org/project/dfba/), [reframed](https://pypi.org/project/reframed/), [mewpy](https://pypi.org/project/mewpy/)); the packages were not checked here.

### MATLAB-specific functions

RAVEN has MATLAB-specific infrastructure that raven-toolbox does not port: path management (`addRavenToUserPath`, `findRAVENroot`), argument handling (`parseRAVENargs`, `convertCharArray`), progress and printing (`setRavenProgress`, `printOrange`) and the solver abstraction (`optimizeProb`, `setRavenSolver`). cobrapy's solver interface (optlang) takes the place of the solver abstraction.

The generated mapping table lists the functions in its tracked categories. `addRavenToUserPath` and `findRAVENroot` belong to the installation folder, which is not tracked, so the table does not list them. The "Deliberately not ported" table lists further infrastructure functions, for example `checkSolution`, `permuteModel`, `parseYAML` and `deprecationWarning`.

### Functions without a Python counterpart

Some RAVEN functions that raven-toolbox does not port are not infrastructure. `getTransportRxns`, `runRobustnessAnalysis` and `runSimpleOptKnock` have no replacement and can block a port. `readFasta` has no public reader, and `findPotentialErrors` has no step that detects an invalid rule string, because the cobrapy GPR class represents a parsed rule directly. The table gives other replacements: the `.annotation` dictionary of cobrapy for `editMiriam` and `extractMiriam`, the `cobra.Reaction` API for `reverseRxns` and `model.summary()` for `printFluxes`. The "Deliberately not ported" table of the [MATLAB vs Python](../matlab-vs-python.md) page is the reference.
