# Materials and installation

## Software

This protocol runs in **MATLAB** (R2013b or later; no extra MathWorks toolboxes
required), complemented with software for reconstructing and analysing GEMs.
Most of it is open source or available under an academic license.

| Software | Dependency | Source |
|---|---|---|
| MATLAB | License | <https://mathworks.com/products/matlab.html> |
| RAVEN | libSBML, solver | <https://github.com/CompMetEng/RAVEN> |
| COBRA | MATLAB | <https://github.com/opencobra/cobratoolbox> |
| Gurobi | License | <https://www.gurobi.com/products/gurobi-optimizer/> |
| libSBML | MATLAB | <http://sbml.org/Software/libSBML> |

- **RAVEN** is the toolbox that drives the reconstruction.
- **libSBML** enables import/export of the community-standard SBML (`.xml`)
  format.
- A **linear-programming solver** is needed for simulation. This protocol uses
  **Gurobi** (free academic license); RAVEN can alternatively use the
  open-source **GLPK** solver bundled with COBRA.

See [Installation](../installation/raven.md) for the full setup.

## Files

Homology-based reconstruction requires files for both the **target** organism
and the **template** organisms.

| File type | Usage | Organism | Source |
|---|---|---|---|
| GEM (SBML) | Template network | *S. cerevisiae* | [yeast-GEM v8.3.0](https://github.com/SysBioChalmers/yeast-GEM/releases/tag/v8.3.0) |
| GEM (SBML) | Template network | *R. toruloides* | [rhto-GEM v1.1.2](https://github.com/SysBioChalmers/rhto-GEM) |
| Protein FASTA | BLAST | *S. cerevisiae* | hanpo-GEM `data/genomes/sce.faa` |
| Protein FASTA | BLAST | *R. toruloides* | hanpo-GEM `data/genomes/rhto.faa` |
| Protein FASTA | BLAST | *H. polymorpha* | [JGI Hanpo2](https://genome.jgi.doe.gov/portal/Hanpo2/Hanpo2.home.html) |
| DNA FASTA | Biomass curation | *H. polymorpha* | NCBI `GCF_001664045.1_Hanpo2` |
| GenBank | Biomass curation | *H. polymorpha* | NCBI `GCF_001664045.1_Hanpo2` |

For the target organism you need (1) a protein FASTA of all proteins in its
genome, (2) a DNA FASTA for nucleotide ratios, and (3) a GenBank file for
ribonucleotide ratios. For each template you need a protein FASTA and a model
file in SBML format.

:::{important} Matching identifiers
For automatic gene matching, the protein FASTA and the model file of each
template **must use the same gene identifiers**.
:::

All required files for *H. polymorpha* are provided in the
[hanpo-GEM](https://github.com/SysBioChalmers/hanpo-GEM) repository; clone it to
get a local copy.

## Literature data

Model quality improves by leveraging any known metabolic behaviour of the target
organism: macromolecule fractions of biomass, essential/non-essential genes,
usable nutrient sources, and growth rate. A short literature search yields total
protein, lipid and carbohydrate content for *H. polymorpha*, used to set the
biomass stoichiometric coefficients ([Biomass composition](biomass.md)). Where
organism-specific data is missing, values from related organisms can be used.

## Install RAVEN

After obtaining the software and files, install RAVEN (see
[Installing RAVEN](../installation/raven.md)). Use `pathtool` to add the
RAVEN, libSBML and Gurobi subfolders to the MATLAB path, then verify with:

```matlab
checkRaven
```

See [Installing RAVEN](#verify) for what a
successful run looks like.

:::{warning}
If `checkRaven` reports that importing SBML format **failed**, uninstall
MATLAB's **Text Analytics Toolbox**, which conflicts with RAVEN's Excel
parser. For support, see the
[RAVEN issues](https://github.com/CompMetEng/RAVEN/issues) page.
:::
