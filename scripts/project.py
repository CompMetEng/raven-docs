"""Project settings of a documentation site, read from ``scripts/project.yml``.

The scripts of the docs-site plugin (``api_index.py``, ``gen_api_pages.py``,
``autolink.py``, ``check_names.py``) contain no project name, path or category
list. Everything that differs between sites is in ``project.yml``; see
``templates/scripts/project.yml`` for the keys.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

COBRAPY_URL = "https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html"

# Folders of a MATLAB toolbox that hold no API.
DEFAULT_EXCLUDED = ("legacy", "external", "software", "testing", "doc", "deprecated")


@dataclass(frozen=True)
class Project:
    matlab_name: str
    matlab_src: Path
    categories: list[tuple[str, str]]
    excluded_folders: frozenset[str]
    python_name: str
    python_package: str
    python_src: Path
    package_titles: dict[str, str]
    cobrapy: bool
    examples: dict

    @property
    def matlab_rel(self) -> str:
        """The MATLAB source folder as written in page text, e.g. ``RAVEN/src``."""
        try:
            return self.matlab_src.relative_to(ROOT).as_posix()
        except ValueError:
            return self.matlab_src.name


def load(config: Path | None = None) -> Project:
    path = config or HERE / "project.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    matlab, python = data["matlab"], data["python"]

    matlab_src = Path(os.environ.get("DOCS_MATLAB_SRC", ROOT / matlab["path"]))
    subdir = matlab.get("src_subdir")
    if subdir and (matlab_src / subdir).is_dir():
        matlab_src = matlab_src / subdir
    python_src = Path(os.environ.get("DOCS_PYTHON_SRC", ROOT / python["path"]))

    categories = [(c["folder"], c["title"]) for c in matlab["categories"]]
    return Project(
        matlab_name=matlab["name"],
        matlab_src=matlab_src,
        categories=categories,
        excluded_folders=frozenset(matlab.get("excluded_folders", DEFAULT_EXCLUDED)),
        python_name=python["name"],
        python_package=python["package"],
        python_src=python_src,
        package_titles=dict(python.get("package_titles", {})),
        cobrapy=bool(data.get("cobrapy", True)),
        examples=dict(data.get("examples") or {}),
    )
