# Example data

The models that the pages of the [user guide](../guide/index.md) load are copied here and not read from the `RAVEN` submodule, so that every snippet can use a short, stable path (`smallYeast.yml`) that works the same way for a reader who downloads the file and for the example runner in CI.

| File | Size | Source | Used by |
|---|---|---|---|
| [`smallYeast.yml`](smallYeast.yml) | 45 kB | `RAVEN/tutorials/data/models/smallYeast.yml` | the default example model for most guide pages |
| [`empty.xml`](empty.xml) | 4 kB | `RAVEN/tutorials/data/empty.xml` | [Building a model from scratch](../guide/building.md): an empty SBML model with compartments defined, to build a model from scratch |
| [`smallYeastBad.yml`](smallYeastBad.yml) | 45 kB | `RAVEN/tutorials/data/models/smallYeastBad.yml` | [Quality control](../guide/quality-control.md) and [Comparing models](../guide/comparing.md), which need a model with known errors |
| [`yeast-GEM.yml`](yeast-GEM.yml) | 3.6 MB | yeast-GEM v9.1.0, `model/yeast-GEM.yml` | pages that need a genome-scale model: [Reading and writing models](../guide/io.md), [Simulating growth with FBA](../guide/fba.md), [Growth media and conditions](../guide/media.md), [Biomass composition and annotation](../guide/biomass.md) |
| [`yeast-GEM.xml`](yeast-GEM.xml) | 11.6 MB | yeast-GEM v9.1.0, `model/yeast-GEM.xml` | the same model as SBML, for [Reading and writing models](../guide/io.md) |
| [`anaerobic.yml`](anaerobic.yml) | 2 kB | transcribed from yeast-GEM's `anaerobicModel.m` | [Growth media and conditions](../guide/media.md): a condition file, yeast-GEM under anaerobic conditions |
| [`tasks.txt`](tasks.txt) | 0.5 kB | written for this guide | [Metabolic tasks](../guide/tasks.md) and [Gap-filling](../guide/gap-filling.md): a task list for `smallYeast.yml` |
| [`curation-mets.tsv`](curation-mets.tsv) | 0.3 kB | written for this guide | [Table-driven curation](../guide/curation.md): a metabolite curation table |
| [`hpa-sample.tsv`](hpa-sample.tsv) | 1 kB | a ten-row excerpt in Human Protein Atlas format | [Context-specific models with ftINIT](../guide/init.md) |

The two small yeast models are part of the RAVEN Toolbox (MIT licence). yeast-GEM is the consensus genome-scale model of *Saccharomyces cerevisiae* ([SysBioChalmers/yeast-GEM](https://github.com/SysBioChalmers/yeast-GEM), CC-BY-4.0). It is pinned here at release v9.1.0, so the numbers printed in the guide stay reproducible while the model keeps developing.

The `.yml` files are RAVEN YAML, read by `readYAMLmodel` in MATLAB and `read_yaml_model` in Python. `yeast-GEM.xml` is SBML, read by `importModel` and cobrapy's `read_sbml_model`.

## Refreshing the copies

The two RAVEN tutorial copies are deliberate duplicates and do not follow the `RAVEN` submodule automatically. After a submodule bump that changes either model, refresh the copies and re-run the examples:

```bash
cp "RAVEN/tutorials/data/models/smallYeast.yml" docs/data/smallYeast.yml
cp "RAVEN/tutorials/data/empty.xml" docs/data/empty.xml
cp "RAVEN/tutorials/data/models/smallYeastBad.yml" docs/data/smallYeastBad.yml
python scripts/run_examples.py
```

A change of the pinned tag is a deliberate act, and it changes every number that the guide prints from the model. Bump the tag, re-download both files and re-generate the affected output blocks in one commit:

```bash
YEAST_GEM=v9.1.0   # the release the guide currently documents
curl -sSL -o docs/data/yeast-GEM.yml "https://raw.githubusercontent.com/SysBioChalmers/yeast-GEM/${YEAST_GEM}/model/yeast-GEM.yml"
curl -sSL -o docs/data/yeast-GEM.xml "https://raw.githubusercontent.com/SysBioChalmers/yeast-GEM/${YEAST_GEM}/model/yeast-GEM.xml"
python scripts/run_examples.py --update
```

Do not edit the files in place. Any change here makes the guide's numbers unreproducible, without a warning, for a reader who takes the model from RAVEN.

## Proteomes for homology reconstruction

`hanpo.faa` and `sce-template.faa` back [Reconstruction from homology](../guide/homology.md).

| file | what it is |
|---|---|
| [`hanpo.faa`](hanpo.faa) | the *Hansenula polymorpha* proteome, 5177 sequences, copied unchanged from the `hanpo-GEM` submodule (`data/genomes/hanpo.faa`) |
| [`sce-template.faa`](sce-template.faa) | 61 *S. cerevisiae* sequences (exactly the genes of `smallYeast.yml`) extracted from the same submodule's `data/genomes/sce.faa` |

The template proteome is restricted to the genes of the model. BLAST against 61 subjects keeps the example of the homology page to about fifteen seconds per language, and a template protein that no reaction uses cannot contribute to the draft.

Regenerate `sce-template.faa` after a change to `smallYeast.yml`:

```bash
python - <<'EOF'
from pathlib import Path
from raven_toolbox.io import read_yaml_model
ids = {g.id for g in read_yaml_model("docs/data/smallYeast.yml").genes}
out, keep = [], False
for line in Path("hanpo-GEM/data/genomes/sce.faa").read_text().splitlines():
    if line.startswith(">"):
        keep = line[1:].strip().split()[0] in ids
    if keep:
        out.append(line)
Path("docs/data/sce-template.faa").write_text("\n".join(out) + "\n")
EOF
python scripts/run_examples.py docs/guide/homology.md --update
```
