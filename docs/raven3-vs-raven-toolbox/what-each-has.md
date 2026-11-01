# Features specific to each implementation

Some features belong to raven-toolbox alone, and some belong to RAVEN alone. The sections below describe both groups.

## Features specific to raven-toolbox

### Model type

A raven-toolbox model is a `cobra.Model`. Every function of cobrapy and of cobrapy-based packages applies to it without conversion. RAVEN uses a MATLAB struct as the model.

cobrapy provides flux balance analysis (FBA), flux variability analysis (FVA), knockouts and media handling. For the functions of RAVEN that cobrapy covers, the page [MATLAB vs Python](../matlab-vs-python.md) gives a cobrapy entry (see [Name differences](../raven3-vs-raven-toolbox.md#name-differences)). The function `setExchangeBounds` has two rows in the mapping: `set_exchange_bounds` in raven-toolbox and `cobra.Model.medium` in cobrapy.

### KEGG artefact generation

raven-toolbox builds the KEGG reference artefacts. It parses a KEGG release into tables of reactions and compounds, assembles the reference model with `build_reference_model`, builds the FASTA sets and HMM libraries per KEGG Orthology (KO) entry, and derives the phylogenetic distance matrix. The download of a KEGG release requires a KEGG FTP subscription, and the artefacts can be rebuilt from a specified KEGG release.

RAVEN loads published artefacts and does not produce them. The function `buildGlobalKEGGModel` joins a downloaded bundle onto the reference model, and the phylogenetic distance matrix is a file shipped with RAVEN (`keggPhylDist.mat`). In the mapping, `getModelFromKEGG` corresponds to `build_reference_model`, which loads in RAVEN and builds in raven-toolbox.

### Checksum registry for binaries and data

Both implementations fetch BLAST+, DIAMOND, HMMER and the KEGG tables on demand and do not bundle them. RAVEN bundles other components: the GLPK and libSBML MEX files and `keggPhylDist.mat`. [Download data and binaries](../installation/data-and-binaries.md) describes the download behaviour.

The checksum handling differs.

- raven-toolbox keeps the checksum and the release of each dataset and binary in a registry in its source (a version-pinned registry). A fresh download is checked against its checksum. A cached data file is reused without a check, unless `ensure_data_file` is called with `verify=True`, which checks it and downloads it anew on a mismatch. A cached binary is reused without a check. A JSON manifest can be merged into the registries with `raven_toolbox.manifest.load_into_registries`, which reads the path or URL in the environment variable `RAVEN_PYTHON_MANIFEST` when no source is passed. The resolvers load that variable by themselves while the registry is empty, so the call is needed with the filled default registries.
- RAVEN checks a download against the checksum in the published manifest. A mismatch deletes the file and raises an error. When the manifest cannot be read or has no entry for the asset, RAVEN issues a warning and keeps the file unchecked. A cached file is reused without a check.

### Further functions

Further features of raven-toolbox have no RAVEN counterpart in the generated mapping. Examples are `localization.relocate_reactions`, which places reactions in compartments chosen by a curator and repairs the model around that decision; `localization.triage_localization`; and the per-reaction confidence record of the `confidence` module, which scores the facets localization, equation and gene association and stores the scores in the reaction notes.

## Features specific to RAVEN

### Legacy tINIT method

The functions `getINITModel` and `runINIT` are the legacy tINIT method, which ftINIT replaces. RAVEN keeps them for models built with them. raven-toolbox implements ftINIT as its sole INIT variant, as a design decision. A model built with tINIT has to be reproduced in MATLAB (see [Context-specific models with ftINIT](../guide/init.md)).

### COBRA Toolbox conversion

The function `ravenCobraWrapper` converts a model in memory between the RAVEN structure and the COBRA Toolbox structure, and a round trip drops some fields. The model of raven-toolbox is a `cobra.Model`, so no in-memory conversion is needed and no equivalent exists. [Choosing an implementation](../raven3-vs-raven-toolbox.md#choosing-an-implementation) describes the exchange by file, and cobrapy writes the COBRA layout.

### Dynamic FBA

`runDynamicFBA` has no raven-toolbox counterpart by design. Python packages cover dynamic FBA: [dfba](https://pypi.org/project/dfba/), [reframed](https://pypi.org/project/reframed/) and [mewpy](https://pypi.org/project/mewpy/). The packages were not checked here.

### MATLAB-specific functions

RAVEN has MATLAB-specific infrastructure that raven-toolbox does not port:

- path management (`addRavenToUserPath`, `findRAVENroot`);
- argument handling (`parseRAVENargs`, `convertCharArray`);
- progress and printing (`setRavenProgress`, `printOrange`);
- the solver abstraction (`optimizeProb`, `setRavenSolver`), which the solver interface of cobrapy (optlang) replaces.

The generated mapping table lists the functions of its tracked categories. `addRavenToUserPath` and `findRAVENroot` belong to the installation folder, which is not tracked, so the table does not list them. The table "Deliberately not ported" lists further infrastructure functions, for example `checkSolution`, `permuteModel`, `parseYAML` and `deprecationWarning`.

### Functions without a Python counterpart

Some functions that raven-toolbox does not port are not infrastructure. Three have no replacement and can block a port: `getTransportRxns`, `runRobustnessAnalysis` and `runSimpleOptKnock`. The function `readFasta` has no public reader, and `findPotentialErrors` has no step that detects an invalid rule string, because the GPR class of cobrapy represents a parsed rule directly. For other functions the table gives a replacement: the `.annotation` dictionary of cobrapy for `editMiriam` and `extractMiriam`, the `cobra.Reaction` API for `reverseRxns`, and `model.summary()` for `printFluxes`. The table "Deliberately not ported" on the [MATLAB vs Python](../matlab-vs-python.md) page is the reference.
