"""API reference generator for the Sphinx/pydata-sphinx-theme exploration.

Runs from ``docs/conf.py`` (Sphinx's ``setup()`` hook), before Sphinx reads
the source tree, mirroring what ``scripts/gen_api_pages.py`` does for the
mkdocs-gen-files build.

**Not the same rendering as the MkDocs build.** mkdocs-material's version
defers per-function help text to two live plugins at render time:
mkdocstrings' Python handler (griffe) and a separate mkdocstrings-matlab
handler (tree-sitter). Neither has a drop-in Sphinx equivalent verified to
work the same way -- the MATLAB one in particular is a bespoke handler with
no direct autodoc-family counterpart. Rather than depend on an unverified
third-party extension, this generator extracts the *full* help text itself
(the collection layer already reads the source; ``api_index.py`` just
discards everything past the first line) and writes fully static pages. No
live directive, no package install, no MATLAB runtime -- same constraint the
MkDocs build already keeps, met a different way.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

from api_index import (  # noqa: E402
    MATLAB_CATEGORIES,
    PY_PACKAGE_TITLES,
    PYPKG,
    RAVEN as MATLAB,
    cell,
    is_matlab_function,
    module_dotted,
    norm,
    slug,
)

import ast


# --------------------------------------------------------------------------- #
# Full-text collection (api_index.py's matlab_summary / py_summary keep only
# the first line; these keep everything).                                    #
# --------------------------------------------------------------------------- #
def matlab_help(path: Path, fname: str) -> tuple[str, str]:
    """(summary, full help text) for one MATLAB function."""
    try:
        lines = path.read_text(encoding="utf-8-sig", errors="ignore").splitlines()
    except OSError:
        return "", ""

    help_lines: list[str] = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not started:
            if stripped.startswith("function"):
                started = True
            continue
        if stripped.startswith("%"):
            help_lines.append(stripped.lstrip("%").strip())
        elif stripped == "" and not help_lines:
            continue
        else:
            break

    cleaned = [h for h in help_lines if h]
    if not cleaned:
        return "", ""
    first = cleaned[0]
    if first.lower().startswith(fname.lower()):
        rest = first[len(fname):].strip(" -:\t")
        if rest:
            summary, body = rest, cleaned[1:]
        elif len(cleaned) > 1:
            summary, body = cleaned[1], cleaned[2:]
        else:
            summary, body = "", []
    else:
        summary = first
        body = cleaned[1:]
    return summary, "\n".join(body)


def py_help(node: ast.AST) -> tuple[str, str]:
    """(summary, rest of the docstring) for one Python function/class node."""
    doc = ast.get_docstring(node) or ""
    lines = doc.strip().splitlines()
    if not lines:
        return "", ""
    summary = ""
    rest_start = 0
    for idx, line in enumerate(lines):
        if line.strip():
            summary = line.strip()
            rest_start = idx + 1
            break
    rest = "\n".join(lines[rest_start:]).strip()
    return summary, rest


def collect_matlab_full() -> dict[str, list[dict]]:
    cats: dict[str, list[dict]] = {}
    for folder, _title in MATLAB_CATEGORIES:
        funcs: dict[str, dict] = {}
        base = MATLAB / folder
        if not base.is_dir():
            continue
        for m in base.rglob("*.m"):
            if m.stem == "Contents" or not is_matlab_function(m):
                continue
            summary, body = matlab_help(m, m.stem)
            funcs.setdefault(m.stem, {"name": m.stem, "summary": summary, "body": body, "path": m})
        cats[folder] = [funcs[n] for n in sorted(funcs, key=str.lower)]
    return cats


def collect_python_full() -> list[dict]:
    objects: list[dict] = []
    if not PYPKG.is_dir():
        return objects
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
                ident = f"{dotted}.{node.name}" if dotted else node.name
                summary, rest = py_help(node)
                sig = ""
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sig = f"({ast.unparse(node.args)})" if hasattr(ast, "unparse") else ""
                objects.append(
                    {
                        "name": node.name,
                        "ident": ident,
                        "package": package,
                        "summary": summary,
                        "body": rest,
                        "signature": sig,
                        "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                    }
                )
    return objects


# --------------------------------------------------------------------------- #
# Page rendering                                                              #
# --------------------------------------------------------------------------- #
def render_matlab_page(title: str, folder: str, funcs: list[dict]) -> str:
    out = [f"# {title}", "", f"MATLAB functions in `RAVEN/src/{folder}` of the RAVEN toolbox.", "",
           "## Functions", "", "| Function | Summary |", "|---|---|"]
    for f in funcs:
        out.append(f"| [`{f['name']}`](#{slug(f['name'])}) | {cell(f['summary'])} |")
    out += ["", "## Reference", ""]
    for f in funcs:
        # A cross-document markdown link with a #fragment resolves against
        # the target page's auto-generated heading anchor, so this heading
        # must auto-slug to exactly `slug(name)` -- true here since it is a
        # bare MATLAB identifier, nothing an explicit target would improve.
        out += [f"### {f['name']}", ""]
        if f["summary"]:
            out += [f["summary"], ""]
        if f["body"]:
            out += ["```text", f["body"], "```", ""]
    return "\n".join(out) + "\n"


def render_python_page(title: str, dotted: str, objs: list[dict]) -> str:
    out = [f"# {title} (Python)", "", f"`raven-toolbox` objects in `{dotted}`.", "",
           "## Functions", "", "| Function | Summary |", "|---|---|"]
    for o in objs:
        out.append(f"| [`{o['name']}`](#{slug(o['name'])}) | {cell(o['summary'])} |")
    out += ["", "## Reference", ""]
    for o in objs:
        # The heading is the bare name, not name+signature: a cross-document
        # markdown link with a #fragment resolves against the target page's
        # auto-generated heading anchor, not an explicit MyST target, so a
        # heading has to auto-slug to exactly `slug(name)` to be linkable at
        # all. The signature goes on its own line underneath instead.
        out += [f"### {o['name']}", ""]
        if o["signature"]:
            out += [f"`{o['name']}{o['signature']}`", ""]
        if o["summary"]:
            out += [o["summary"], ""]
        if o["body"]:
            out += ["```text", o["body"], "```", ""]
    return "\n".join(out) + "\n"


def render_group_index(title: str, intro: str, links: list[tuple[str, str]]) -> str:
    stems = [href.rsplit(".", 1)[0] for _title, href in links]
    out = ["---", "icon: material/folder-open", "---", "", f"# {title}", "", intro, "",
           "```{toctree}", ":hidden:"]
    out += stems
    out += ["```", ""]
    for link_title, href in links:
        out.append(f"- [{link_title}]({href})")
    return "\n".join(out) + "\n"


def generate(docs_root: Path) -> None:
    api_dir = docs_root / "api"
    (api_dir / "matlab").mkdir(parents=True, exist_ok=True)
    (api_dir / "python").mkdir(parents=True, exist_ok=True)

    matlab = collect_matlab_full()
    python_objs = collect_python_full()
    py_by_norm: dict[str, dict] = {}
    for obj in python_objs:
        py_by_norm.setdefault(norm(obj["name"]), obj)

    matlab_links: list[tuple[str, str]] = []
    for folder, title in MATLAB_CATEGORIES:
        funcs = matlab.get(folder, [])
        if not funcs:
            continue
        (api_dir / "matlab" / f"{folder}.md").write_text(
            render_matlab_page(title, folder, funcs), encoding="utf-8"
        )
        matlab_links.append((title, f"{folder}.md"))
    (api_dir / "matlab" / "index.md").write_text(
        render_group_index("MATLAB API (RAVEN)", "RAVEN's MATLAB functions, by category.", matlab_links),
        encoding="utf-8",
    )

    by_package: dict[str, list[dict]] = {}
    for obj in python_objs:
        by_package.setdefault(obj["package"], []).append(obj)
    python_links: list[tuple[str, str]] = []
    for package in sorted(by_package, key=lambda p: (p == "_toplevel", PY_PACKAGE_TITLES.get(p, p).lower())):
        objs = sorted(by_package[package], key=lambda o: o["name"].lower())
        title = PY_PACKAGE_TITLES.get(package, package)
        dotted = "raven_toolbox" if package == "_toplevel" else f"raven_toolbox.{package}"
        (api_dir / "python" / f"{package}.md").write_text(
            render_python_page(title, dotted, objs), encoding="utf-8"
        )
        python_links.append((title, f"{package}.md"))
    (api_dir / "python" / "index.md").write_text(
        render_group_index(
            "Python API (raven-toolbox)", "raven-toolbox's packages, by category.", python_links
        ),
        encoding="utf-8",
    )

    # --- matlab-vs-python.md: identical logic to gen_api_pages.py, static write
    matlab_all = {f["name"]: folder for folder, _t in MATLAB_CATEGORIES for f in matlab.get(folder, [])}
    py_by_name = {obj["name"]: obj for obj in python_objs}
    curated = yaml.safe_load((Path(__file__).resolve().parent / "curated_pairs.yml").read_text(encoding="utf-8"))

    unresolved: list[str] = []
    for m_name, p_name in curated["aliases"].items():
        if m_name not in matlab_all:
            unresolved.append(f"aliases: RAVEN function '{m_name}' is not on the tracked branch")
        if p_name not in py_by_name:
            unresolved.append(f"aliases: raven-toolbox function '{p_name}' (for {m_name}) does not exist")
    for section in ("cobrapy", "not_ported"):
        for m_name in curated[section]:
            if m_name not in matlab_all:
                unresolved.append(f"{section}: RAVEN function '{m_name}' is not on the tracked branch")
    if unresolved:
        listed = "\n  - ".join(unresolved)
        raise SystemExit(f"gen_api_pages_sphinx: scripts/curated_pairs.yml is out of date:\n  - {listed}")

    cobrapy_docs_url = "https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html"

    # Each row: (matlab name, matlab folder, python-column markdown, summary text).
    rows: list[tuple[str, str, str, str]] = []
    seen_matlab: set[str] = set()
    n_auto = 0
    for folder, _title in MATLAB_CATEGORIES:
        for f in matlab.get(folder, []):
            match = py_by_norm.get(norm(f["name"]))
            if match:
                p_cell = f"[`{match['name']}`](api/python/{match['package']}.md#{slug(match['name'])})"
                rows.append((f["name"], folder, p_cell, f["summary"] or match["summary"]))
                seen_matlab.add(f["name"])
                n_auto += 1
    n_curated = 0
    for m_name, p_name in curated["aliases"].items():
        if m_name in seen_matlab:
            continue
        folder = matlab_all[m_name]
        obj = py_by_name[p_name]
        m_summary = next((f["summary"] for f in matlab.get(folder, []) if f["name"] == m_name), "")
        p_cell = f"[`{p_name}`](api/python/{obj['package']}.md#{slug(p_name)})"
        rows.append((m_name, folder, p_cell, m_summary or obj["summary"]))
        seen_matlab.add(m_name)
        n_curated += 1
    n_cobrapy = 0
    for m_name, target in curated["cobrapy"].items():
        folder = matlab_all[m_name]
        m_summary = next((f["summary"] for f in matlab.get(folder, []) if f["name"] == m_name), "")
        p_cell = f"`{target}` {{bdg-link-secondary}}`cobrapy <{cobrapy_docs_url}>`"
        rows.append((m_name, folder, p_cell, m_summary))
        seen_matlab.add(m_name)
        n_cobrapy += 1

    lines = [
        "# MATLAB vs Python", "",
        "RAVEN ships as a MATLAB toolbox and as the Python package **raven-toolbox**. "
        "This page is generated from the source of both toolboxes at build time. "
        "Pairs are found automatically where the names match, completed from a "
        "curated list where they do not, and marked with a "
        f"{{bdg-link-secondary}}`cobrapy <{cobrapy_docs_url}>` badge where cobrapy "
        "covers the function instead of raven-toolbox. Every name is verified to exist.",
        "", "## Paired functions", "",
        f"**{len(rows)}** RAVEN functions listed: {n_auto} matched automatically, "
        f"{n_curated} from a curated list, {n_cobrapy} covered by cobrapy instead of "
        "raven-toolbox.",
        "", "| RAVEN (MATLAB) | raven-toolbox (Python) | Summary |", "|---|---|---|",
    ]
    for m_name, m_folder, p_cell, text in sorted(rows, key=lambda r: r[0].lower()):
        m_link = f"[`{m_name}`](api/matlab/{m_folder}.md#{slug(m_name)})"
        lines.append(f"| {m_link} | {p_cell} | {cell(text)} |")

    lines += ["", "## Deliberately not ported", "", "| RAVEN (MATLAB) | Why not |", "|---|---|"]
    for m_name, reason in sorted(curated["not_ported"].items(), key=lambda kv: kv[0].lower()):
        folder = matlab_all[m_name]
        m_link = f"[`{m_name}`](api/matlab/{folder}.md#{slug(m_name)})"
        lines.append(f"| {m_link} | {cell(reason)} |")

    accounted = {r[0] for r in rows} | set(curated["not_ported"])
    unmapped = sorted((n for n in matlab_all if n not in accounted), key=str.lower)
    if unmapped:
        lines += ["", "## Not yet mapped", "",
                  f"**{len(unmapped)}** RAVEN functions are not yet recorded here.", ""]
        for chunk_start in range(0, len(unmapped), 6):
            row = unmapped[chunk_start:chunk_start + 6]
            lines.append(", ".join(f"`{n}`" for n in row) + ("," if chunk_start + 6 < len(unmapped) else ""))

    (docs_root / "matlab-vs-python.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
