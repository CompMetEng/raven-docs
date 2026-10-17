"""Link function names on the guide pages to their API reference.

A Sphinx extension. On ``source-read`` it rewrites the inline code spans of
``guide/*`` pages, outside fenced code, headings and existing links:

* a RAVEN function becomes a link to its entry in the generated MATLAB API
  pages (``api/matlab/<folder>.md``);
* a raven-toolbox function or class becomes a link to its entry in the Python
  API pages (``api/python/<package>.md``);
* a cobrapy object becomes a link to its entry in cobrapy's documentation,
  looked up in cobrapy's intersphinx inventory. Single names such as ``pfba``
  or ``Model`` are only looked up in a table row that carries the cobrapy
  badge; elsewhere a cobrapy name has to be dotted (``Model.optimize``) or
  snake_case (``read_sbml_model``), so ordinary words are never linked.

Every span in a table row is linked, so the "Functions on this page" table
links each entry; in prose only the first mention of a name per section is.
The cobrapy badge in a table row points at the first cobrapy object linked in
that row instead of cobrapy's index page.

The page sources on disk are not changed, so ``scripts/run_examples.py``, which
reads them directly, sees the same code blocks.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from api_index import collect_matlab, collect_python, slug  # noqa: E402
from sphinx.util import logging  # noqa: E402

COBRA_INDEX = "https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/index.html"

_FENCE = re.compile(r"^\s*(```|~~~)")
_HEADING = re.compile(r"^#{1,6}\s")
# An inline code span that is not the text of a markdown link ([`x`](...)) and
# not the content of a role ({bdg-link-secondary}`...`).
_SPAN = re.compile(r"(?<![\[}`])`([^`\n]+)`(?![`\]])")
_BADGE = re.compile(r"\{bdg-link-secondary\}`cobrapy <" + re.escape(COBRA_INDEX) + r">`")
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
_SNAKE = re.compile(r"^[a-z][a-z0-9]+(?:_[a-z0-9]+)+$")
_COBRA_TYPES = ("py:function", "py:method", "py:class", "py:attribute", "py:property")
# raven-toolbox names that mean something else on the guide pages: `main` is a
# command-line entry point in the package and a branch name in the prose.
_NOT_LINKED = {"main"}


class Linker:
    def __init__(self, cobra_inventory: dict | None) -> None:
        self.matlab = {f["name"]: folder for folder, funcs in collect_matlab().items() for f in funcs}
        packages: dict[str, set[str]] = {}
        for obj in collect_python():
            packages.setdefault(obj["name"], set()).add(obj["package"])
        # A name defined in two packages has no single target: leave it unlinked.
        self.python = {name: next(iter(pk)) for name, pk in packages.items() if len(pk) == 1}
        self.cobra = self._cobra_index(cobra_inventory or {})
        self.counts = {"matlab": 0, "python": 0, "cobrapy": 0, "badges": 0}

    @staticmethod
    def _cobra_index(inventory: dict) -> dict[str, str]:
        """Every dotted suffix of a cobrapy object's full name -> its URL.

        ``cobra.core.model.Model.optimize`` is reachable as ``optimize``,
        ``Model.optimize``, ``model.Model.optimize`` and so on. Where two
        objects share a suffix, the one with the shorter full name wins.
        """
        best: dict[str, tuple[int, str, str]] = {}
        for role in _COBRA_TYPES:
            for full, entry in inventory.get(role, {}).items():
                url = getattr(entry, "uri", None) or entry[2]
                parts = full.split(".")
                for i in range(len(parts)):
                    key = ".".join(parts[i:])
                    rank = (len(parts), full, url)
                    if key not in best or rank < best[key]:
                        best[key] = rank
        return {key: url for key, (_n, _f, url) in best.items()}

    def target(self, token: str, in_badged_row: bool) -> tuple[str, str] | None:
        """(kind, href) for a code span, or None to leave it as it is."""
        if token in _NOT_LINKED:
            return None
        if token in self.matlab:
            return "matlab", f"../api/matlab/{self.matlab[token]}.md#{slug(token)}"
        if token in self.python:
            return "python", f"../api/python/{self.python[token]}.md#{slug(token)}"
        if not _IDENT.match(token):
            return None
        bare = token.removeprefix("cobra.")
        if "." in bare or _SNAKE.match(bare) or in_badged_row:
            url = self.cobra.get(bare) or self.cobra.get(token)
            if url:
                return "cobrapy", url
        return None

    def link_page(self, text: str) -> str:
        out: list[str] = []
        in_fence = False
        seen: set[str] = set()
        for line in text.split("\n"):
            if _FENCE.match(line):
                in_fence = not in_fence
                out.append(line)
                continue
            if in_fence:
                out.append(line)
                continue
            if _HEADING.match(line):
                seen = set()
                out.append(line)
                continue
            out.append(self._link_line(line, seen))
        return "\n".join(out)

    def _link_line(self, line: str, seen: set[str]) -> str:
        if "`" not in line:
            return line
        in_table = line.lstrip().startswith("|")
        badged = in_table and bool(_BADGE.search(line))
        first_cobra: list[str] = []

        def replace(m: re.Match) -> str:
            raw = m.group(1)
            token = raw.strip()
            token = token[:-2] if token.endswith("()") else token
            found = self.target(token, badged)
            if found is None:
                return m.group(0)
            kind, href = found
            if not in_table:
                if token in seen:
                    return m.group(0)
                seen.add(token)
            if kind == "cobrapy" and not first_cobra:
                first_cobra.append(href)
            self.counts[kind] += 1
            return f"[`{raw}`]({href})"

        line = _SPAN.sub(replace, line)
        if badged and first_cobra:
            line = _BADGE.sub(
                lambda _m: f"{{bdg-link-secondary}}`cobrapy <{first_cobra[0]}>`", line, count=1
            )
            self.counts["badges"] += 1
        return line


def _cobra_inventory(app) -> dict | None:
    named = getattr(app.env, "intersphinx_named_inventory", None) or {}
    return named.get("cobra")


def setup(app):
    state: dict[str, Linker] = {}

    def on_source_read(app, docname, source):
        if not docname.startswith("guide/"):
            return
        if "linker" not in state:
            state["linker"] = Linker(_cobra_inventory(app))
        source[0] = state["linker"].link_page(source[0])

    def on_build_finished(app, exception):
        if "linker" in state:
            c = state["linker"].counts
            logging.getLogger(__name__).info(
                "autolink: %d RAVEN, %d raven-toolbox and %d cobrapy links; %d cobrapy badges",
                c["matlab"], c["python"], c["cobrapy"], c["badges"],
            )

    app.connect("source-read", on_source_read)
    app.connect("build-finished", on_build_finished)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
