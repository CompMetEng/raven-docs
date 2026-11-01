# Materials and installation

## Software

The protocol runs in MATLAB, together with software to reconstruct and analyse GEMs. The published protocol states MATLAB R2013b or later, and [RAVEN (MATLAB)](../installation/raven.md) describes the requirements of RAVEN 3. No extra MathWorks toolboxes are required. Most of the software is open source or available under an academic licence.

| Software | Dependency | Source |
|---|---|---|
| MATLAB | Licence | <https://mathworks.com/products/matlab.html> |
| RAVEN | libSBML, solver | <https://github.com/CompMetEng/RAVEN> |
| COBRA | MATLAB | <https://github.com/opencobra/cobratoolbox> |
| Gurobi | Licence | <https://www.gurobi.com/products/gurobi-optimizer/> |
| libSBML | MATLAB | <http://sbml.org/Software/libSBML> |

- RAVEN drives the reconstruction.
- libSBML imports and exports the community-standard SBML (`.xml`) format.
- Simulation needs a linear-programming solver. The protocol uses Gurobi (free academic licence). RAVEN also runs on the open-source GLPK solver that it bundles.

[Installation](../installation/raven.md) describes the complete setup.

## Files

Homology-based reconstruction needs files for the target organism and for the template organisms.

| File type | Usage | Organism | Source |
|---|---|---|---|
| GEM (SBML) | Template network | *S. cerevisiae* | [yeast-GEM v8.3.0](https://github.com/SysBioChalmers/yeast-GEM/releases/tag/v8.3.0) |
| GEM (SBML) | Template network | *R. toruloides* | [rhto-GEM v1.1.2](https://github.com/SysBioChalmers/rhto-GEM) |
| Protein FASTA | BLAST | *S. cerevisiae* | hanpo-GEM `data/genomes/sce.faa` |
| Protein FASTA | BLAST | *R. toruloides* | hanpo-GEM `data/genomes/rhto.faa` |
| Protein FASTA | BLAST | *H. polymorpha* | [JGI Hanpo2](https://genome.jgi.doe.gov/portal/Hanpo2/Hanpo2.home.html) |
| DNA FASTA | Biomass curation | *H. polymorpha* | NCBI `GCF_001664045.1_Hanpo2` |
| GenBank | Biomass curation | *H. polymorpha* | NCBI `GCF_001664045.1_Hanpo2` |

The target organism needs a protein FASTA file of all proteins in its genome, a DNA FASTA file for the nucleotide ratios and a GenBank file for the ribonucleotide ratios. Each template needs a protein FASTA file and a model file in SBML format.

:::{admonition} Matching identifiers
:class: important

For automatic gene matching, the protein FASTA file and the model file of each template must use the same gene identifiers.
:::

The [hanpo-GEM](https://github.com/SysBioChalmers/hanpo-GEM) repository provides all required files for *H. polymorpha*, and a clone of it gives a local copy.

## Literature data

Known metabolic behaviour of the target organism improves the quality of the model: the macromolecule fractions of the biomass, essential and non-essential genes, usable nutrient sources and the growth rate. A short literature search gives the total protein, lipid and carbohydrate content for *H. polymorpha*, which sets the stoichiometric coefficients of the biomass ([Biomass composition](biomass.md)). Values from related organisms can replace missing organism-specific data.

## Installing RAVEN

After the software and files are obtained, RAVEN is installed ([Installing RAVEN](../installation/raven.md)). `pathtool` adds the RAVEN folder to the MATLAB path, and RAVEN bundles libSBML. Gurobi is added to the path by its own MATLAB integration ([RAVEN (MATLAB)](../installation/raven.md#choosing-and-configuring-a-solver)), and the installation is verified with:

```matlab
checkRaven
```

[Installing RAVEN](../installation/raven.md#verification) shows the output of a successful run.

:::{admonition} Troubleshooting
:class: warning

- Problem: `checkRaven` reports Fail for Export Excel format.
- Possible reason: The Text Analytics Toolbox of MATLAB can conflict with Excel files.
- Solution: Uninstall the Text Analytics Toolbox. Support is available through the [RAVEN issues](https://github.com/CompMetEng/RAVEN/issues) page.
:::
