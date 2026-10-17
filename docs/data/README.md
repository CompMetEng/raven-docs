# Example data

The models the [user guide](../guide/index.md) pages load. They are copied here,
rather than read from the `RAVEN` submodule, so that every snippet can use a
short, stable path (`smallYeast.yml`) that works the same way for a reader who
downloads the file and for the example runner in CI.

| File | Size | Source | Used by |
|---|---|---|---|
| [`smallYeast.yml`](smallYeast.yml) | 45 kB | `RAVEN/tutorials/data/models/smallYeast.yml` | the default example model for most guide pages |
| [`empty.xml`](empty.xml) | 4 kB | `RAVEN/tutorials/data/empty.xml` | [7. Building](../guide/building.md): an empty SBML model with compartments defined, to build a model from scratch |
| [`smallYeastBad.yml`](smallYeastBad.yml) | 45 kB | `RAVEN/tutorials/data/models/smallYeastBad.yml` | [9. Quality control](../guide/quality-control.md) and [21. Comparing](../guide/comparing.md), which need a model with known errors |
| [`yeast-GEM.yml`](yeast-GEM.yml) | 3.6 MB | yeast-GEM **v9.1.0**, `model/yeast-GEM.yml` | pages that need a genome-scale model: [3. I/O](../guide/io.md), [4. FBA](../guide/fba.md), [5. Media](../guide/media.md), [11. Biomass](../guide/biomass.md) |
| [`yeast-GEM.xml`](yeast-GEM.xml) | 11.6 MB | yeast-GEM **v9.1.0**, `model/yeast-GEM.xml` | the same model as SBML, for [3. I/O](../guide/io.md) |
| [`anaerobic.yml`](anaerobic.yml) | 2 kB | transcribed from yeast-GEM's `anaerobicModel.m` | [5. Media](../guide/media.md): a condition file, yeast-GEM under anaerobic conditions |
| [`tasks.txt`](tasks.txt) | 0.5 kB | written for this guide | [15. Metabolic tasks](../guide/tasks.md) and [17. Gap-filling](../guide/gap-filling.md): a task list for `smallYeast.yml` |
| [`curation-mets.tsv`](curation-mets.tsv) | 0.3 kB | written for this guide | [10. Table-driven curation](../guide/curation.md): a metabolite curation table |
| [`hpa-sample.tsv`](hpa-sample.tsv) | 1 kB | a ten-row excerpt in Human Protein Atlas format | [14. Context-specific models](../guide/init.md) |

The two small yeast models are part of the RAVEN Toolbox (MIT licence).
yeast-GEM is the consensus genome-scale model of *Saccharomyces cerevisiae*
([SysBioChalmers/yeast-GEM](https://github.com/SysBioChalmers/yeast-GEM),
CC-BY-4.0), pinned here at release **v9.1.0** so the numbers printed in the guide
stay reproducible while the model keeps developing.

The `.yml` files are RAVEN YAML, read by `readYAMLmodel` in MATLAB and
`read_yaml_model` in Python; `yeast-GEM.xml` is SBML, read by `importModel` and
cobrapy's `read_sbml_model`.

## Refreshing them

The two RAVEN tutorial copies are deliberate duplicates, so they do not follow the
`RAVEN` submodule automatically. After a submodule bump that changes either
model, refresh them and re-run the examples:

```bash
cp "RAVEN/tutorials/data/models/smallYeast.yml" docs/data/smallYeast.yml
cp "RAVEN/tutorials/data/empty.xml" docs/data/empty.xml
cp "RAVEN/tutorials/data/models/smallYeastBad.yml" docs/data/smallYeastBad.yml
python scripts/run_examples.py
```

Moving to a newer yeast-GEM is a deliberate act, not a routine one: every number
the guide prints from it changes, so bump the tag, re-download both files, and
re-generate the affected output blocks in one commit.

```bash
YEAST_GEM=v9.1.0   # the release the guide currently documents
curl -sSL -o docs/data/yeast-GEM.yml "https://raw.githubusercontent.com/SysBioChalmers/yeast-GEM/${YEAST_GEM}/model/yeast-GEM.yml"
curl -sSL -o docs/data/yeast-GEM.xml "https://raw.githubusercontent.com/SysBioChalmers/yeast-GEM/${YEAST_GEM}/model/yeast-GEM.xml"
python scripts/run_examples.py --update
```

Do not edit the files in place: any change here silently makes the guide's
numbers unreproducible for a reader who takes the model from RAVEN instead.

## Proteomes, for the homology page

`hanpo.faa` and `sce-template.faa` back [12. Reconstruction from
homology](../guide/homology.md).

| file | what it is |
|---|---|
| [`hanpo.faa`](hanpo.faa) | the *Hansenula polymorpha* proteome, 5177 sequences, copied unchanged from the `hanpo-GEM` submodule (`data/genomes/hanpo.faa`) |
| [`sce-template.faa`](sce-template.faa) | 61 *S. cerevisiae* sequences (exactly the genes of `smallYeast.yml`) extracted from the same submodule's `data/genomes/sce.faa` |

The template proteome is cut down to the model's own genes on purpose: BLAST
against 61 subjects instead of a whole proteome is what keeps the page's example
to about fifteen seconds per language, and a template protein that no reaction
uses could not have contributed to the draft anyway.

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
