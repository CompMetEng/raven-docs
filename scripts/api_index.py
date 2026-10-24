"""Shared index of the two toolboxes' public APIs, collected from submodule source.

The API-reference generator (``gen_api_pages.py``), the linker
(``autolink.py``) and the name checker (``check_names.py``) need to know which
functions exist in the MATLAB toolbox and in the Python package. Collecting that
in one place means the prose is validated against exactly the index the
reference pages are built from, so a function name that no longer resolves
cannot slip through in one while the other is regenerated.

Collection is static in both languages: ``.m`` files are read as text and Python
modules are parsed with ``ast``. Neither MATLAB nor the installed Python package
is required. The names, paths and categories come from ``project.yml``.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import project as _project  # noqa: E402

PROJECT = _project.load()
ROOT = _project.ROOT

# The submodules are the source of truth for a real build. For local work the
# environment variables DOCS_MATLAB_SRC and DOCS_PYTHON_SRC point at a working
# checkout instead, which is useful when a submodule cannot be moved to the
# tracked commit.
MATLAB = PROJECT.matlab_src
PYPKG = PROJECT.python_src
# Top-level categories to document, in navigation order: (folder, page title).
MATLAB_CATEGORIES = PROJECT.categories
# Titles for the Python sub-packages.
PY_PACKAGE_TITLES = PROJECT.package_titles


def norm(name: str) -> str:
    """Normalise a function name for cross-language matching."""
    return re.sub(r"[_\s]", "", name).lower()


def slug(name: str) -> str:
    """Reproduce Python-Markdown's default heading slug for in-page anchors."""
    value = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


def cell(text: str) -> str:
    """Make a string safe for a single Markdown table cell."""
    return " ".join(text.split()).replace("|", "\\|")


# --------------------------------------------------------------------------- #
# Collect MATLAB functions                                                    #
# --------------------------------------------------------------------------- #
def is_matlab_function(path: Path) -> bool:
    """True if the .m file declares a function (i.e. not a plain script).

    Read as utf-8-sig: some .m files carry a UTF-8 byte-order mark,
    and a leading U+FEFF is not whitespace to ``str.strip()``, so the opening
    ``function`` line would not be recognised and the file would be indexed as
    a script -- dropping it from the API reference and from the name checker's
    index without any error.
    """
    try:
        with path.open(encoding="utf-8-sig", errors="ignore") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped or stripped.startswith("%"):
                    continue
                return stripped.startswith("function")
    except OSError:
        return False
    return False


def is_matlab_classdef(path: Path) -> bool:
    """True if the .m file declares a class rather than a function or script.

    A classdef file puts its help comment *before* the ``classdef`` line, the
    reverse of a function, whose help follows the ``function`` line.
    """
    try:
        with path.open(encoding="utf-8-sig", errors="ignore") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped or stripped.startswith("%"):
                    continue
                return stripped.startswith("classdef")
    except OSError:
        return False
    return False


def _strip_comment(line: str) -> str:
    text = line.strip()[1:]
    return text[1:] if text.startswith(" ") else text


def matlab_classdef_help_block(path: Path) -> list[str]:
    """Help lines of a classdef file: the comment block before ``classdef``."""
    try:
        with path.open(encoding="utf-8-sig", errors="ignore") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return []
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    help_lines: list[str] = []
    while i < len(lines) and lines[i].strip().startswith("%"):
        help_lines.append(_strip_comment(lines[i]))
        i += 1
    while help_lines and not help_lines[-1].strip():
        help_lines.pop()
    return help_lines


def is_documented_matlab_object(path: Path) -> bool:
    """A function, or a class that has a help block (an undocumented class is skipped)."""
    if is_matlab_function(path):
        return True
    return is_matlab_classdef(path) and any(line.strip() for line in matlab_classdef_help_block(path))


def matlab_help_block(path: Path) -> tuple[str, list[str]]:
    """(signature, help lines) of a MATLAB function file.

    The signature is the ``function`` line, with any ``...`` continuation
    lines joined onto it. The help lines are the comment block that follows,
    with the ``%`` and the one space after it removed, so the author's
    indentation and blank lines are kept. A classdef file has no signature, and
    its help block comes before the ``classdef`` line.
    """
    if is_matlab_classdef(path):
        return "", matlab_classdef_help_block(path)
    try:
        with path.open(encoding="utf-8-sig", errors="ignore") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return "", []

    i = 0
    while i < len(lines) and not lines[i].strip().startswith("function"):
        i += 1
    if i == len(lines):
        return "", []
    signature = [lines[i].strip()]
    while signature[-1].endswith("...") and i + 1 < len(lines):
        i += 1
        signature.append(lines[i].rstrip())
    i += 1

    while i < len(lines) and not lines[i].strip():
        i += 1
    help_lines: list[str] = []
    while i < len(lines) and lines[i].strip().startswith("%"):
        help_lines.append(_strip_comment(lines[i]))
        i += 1
    while help_lines and not help_lines[-1].strip():
        help_lines.pop()
    return "\n".join(signature), help_lines


def matlab_summary_and_body(path: Path, fname: str) -> tuple[str, list[str]]:
    """(summary, remaining help lines) of a MATLAB function.

    The first help line is often just the function name, or the name followed
    by the summary; the name is stripped, and a line holding nothing else
    gives way to the next one.
    """
    _signature, help_lines = matlab_help_block(path)
    nonblank = [n for n, line in enumerate(help_lines) if line.strip()]
    if not nonblank:
        return "", []
    first_idx = nonblank[0]
    first = help_lines[first_idx].strip()
    if first.lower().startswith(fname.lower()):
        rest = first[len(fname):].strip(" -:\t")
        if rest:
            return rest, help_lines[first_idx + 1:]
        if len(nonblank) > 1:
            return help_lines[nonblank[1]].strip(), help_lines[nonblank[1] + 1:]
        return "", []
    return first, help_lines[first_idx + 1:]


def matlab_summary(path: Path, fname: str) -> str:
    """First descriptive line of a function's MATLAB help block."""
    return matlab_summary_and_body(path, fname)[0]


def collect_matlab() -> dict[str, list[dict]]:
    """category -> sorted list of {name, summary} for documented functions."""
    cats: dict[str, list[dict]] = {}
    for folder, _title in MATLAB_CATEGORIES:
        funcs: dict[str, str] = {}
        base = MATLAB / folder
        for m in base.rglob("*.m"):
            if m.stem == "Contents":
                continue
            if not is_documented_matlab_object(m):
                continue
            funcs.setdefault(m.stem, matlab_summary(m, m.stem))
        cats[folder] = [
            {"name": n, "summary": funcs[n]}
            for n in sorted(funcs, key=str.lower)
        ]
    return cats


def collect_matlab_all() -> dict[str, str]:
    """Every function or class name of the MATLAB toolbox -> its category folder.

    Unlike :func:`collect_matlab` this also walks the folders that are not part
    of the documented category list, so the name checker recognises a function
    that exists in the toolbox but has no reference page.
    """
    found: dict[str, str] = {}
    for m in MATLAB.rglob("*.m"):
        rel = m.relative_to(MATLAB)
        if rel.parts[0] in PROJECT.excluded_folders:
            continue
        if m.stem == "Contents" or not (is_matlab_function(m) or is_matlab_classdef(m)):
            continue
        found.setdefault(m.stem, rel.parts[0])
    return found


# --------------------------------------------------------------------------- #
# Collect Python functions and classes                                        #
# --------------------------------------------------------------------------- #
def module_dotted(path: Path) -> str:
    """<package>/src/<name>/io/excel.py -> <name>.io.excel"""
    rel = path.relative_to(PYPKG.parent)  # relative to src/
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def is_deprecated_alias(summary: str) -> bool:
    """True for a backward-compatibility alias, whose docstring starts "Deprecated".

    The alias sits next to its replacement. It is left out of the reference, which
    also keeps name matching from pairing a MATLAB function with the shim.
    """
    return summary.startswith("Deprecated")


def py_summary(node: ast.AST) -> str:
    """First non-empty line of a node's docstring."""
    doc = ast.get_docstring(node) or ""
    for line in doc.strip().splitlines():
        if line.strip():
            return line.strip()
    return ""


def collect_python(include_deprecated: bool = False) -> list[dict]:
    """List of {name, ident, package, summary} for public top-level objects.

    Deprecated aliases are left out unless ``include_deprecated`` is set. The
    reference pages leave them out; the name checker keeps them, because a page
    may name an alias on purpose.
    """
    objects: list[dict] = []
    for py in PYPKG.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue
        dotted = module_dotted(py)
        rel = py.relative_to(PYPKG)
        package = rel.parts[0] if len(rel.parts) > 1 else "_toplevel"
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith("_"):
                    continue
                summary = py_summary(node)
                if is_deprecated_alias(summary) and not include_deprecated:
                    continue
                ident = f"{dotted}.{node.name}" if dotted else node.name
                objects.append(
                    {
                        "name": node.name,
                        "ident": ident,
                        "package": package,
                        "summary": summary,
                    }
                )
    return objects
