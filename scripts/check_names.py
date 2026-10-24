"""Report prose that names a function that does not exist.

The hand-written pages describe two moving APIs, and names drift in by analogy:
`camelCase` rewritten as `snake_case` on the assumption that the Python function
must be called that. This script resolves every function-shaped identifier in
the hand-written pages against the same index the API reference is generated
from (:mod:`api_index`) and lists anything that does not resolve. Generated
pages are skipped: they come from the index by construction.

Two kinds of identifier are checked:

* **inline code spans** -- ``camelCase`` tokens must be MATLAB functions,
  ``snake_case`` tokens must be Python functions;
* **calls inside ```python blocks** -- every called name must be a
  Python function, a known cobrapy name, or allow-listed.

Anything that is legitimately not a function -- model struct fields
(``metDeltaG``), cobrapy names (``read_sbml_model``), reaction ids, file names --
belongs in ``known_names.txt`` next to this file, one per line. Keep that list
short: every entry is a name nothing can verify for you.

Run it with:

    python scripts/check_names.py
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from api_index import PROJECT, collect_matlab_all, collect_python  # noqa: E402

HERE = Path(__file__).resolve().parent
ALLOWLIST_FILE = HERE / "known_names.txt"

# Pages generated at build time from the API index; validating them against the
# same index would be circular.
GENERATED_PREFIXES = ("api/",)
GENERATED_FILES = {"matlab-vs-python.md"}

_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_FENCE = re.compile(r"^([ \t]*)```", re.M)
_PY_BLOCK = re.compile(r"```python\n(.*?)^[ \t]*```", re.S | re.M)

# camelCase: starts lower, contains an uppercase run, no separators.
_CAMEL = re.compile(r"^[a-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*$")
# snake_case: at least two alphanumeric characters before the first underscore,
# so reaction ids such as r_4041 and s_0584 are not mistaken for functions.
_SNAKE = re.compile(r"^[a-z][a-z0-9]+(?:_[a-z0-9]+)+$")

_BUILTINS = {
    "print", "len", "open", "sorted", "list", "dict", "set", "str", "int",
    "float", "range", "enumerate", "zip", "sum", "min", "max", "abs", "round",
}


def load_allowlist() -> set[str]:
    """Names that are legitimately not functions of either toolbox."""
    if not ALLOWLIST_FILE.is_file():
        return set()
    entries = set()
    for line in ALLOWLIST_FILE.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            entries.add(line)
    return entries


class Index:
    """The names that exist, collected once per build."""

    def __init__(self) -> None:
        self.matlab = set(collect_matlab_all())
        self.python = {obj["name"] for obj in collect_python(include_deprecated=True)}
        self.allowed = load_allowlist()

    def is_generated(self, src_path: str) -> bool:
        rel = src_path.replace("\\", "/")
        return rel in GENERATED_FILES or rel.startswith(GENERATED_PREFIXES)

    def problems(self, markdown: str, src_path: str) -> list[str]:
        if self.is_generated(src_path):
            return []
        found: list[str] = []
        found += self._check_inline(markdown)
        found += self._check_python_blocks(markdown)
        return found

    # -- inline code spans -------------------------------------------------- #
    def _check_inline(self, markdown: str) -> list[str]:
        problems = []
        for token in _INLINE_CODE.findall(_strip_fences(markdown)):
            token = token.strip()
            if token.endswith("()"):
                token = token[:-2]
            if not token or token in self.allowed:
                continue
            if _CAMEL.match(token):
                if token not in self.matlab:
                    problems.append(
                        f"`{token}` looks like a {PROJECT.matlab_name} function but no such .m "
                        f"file exists on the tracked branch"
                    )
            elif _SNAKE.match(token):
                if token not in self.python:
                    problems.append(
                        f"`{token}` looks like a {PROJECT.python_name} function but is "
                        f"not defined in the package"
                    )
        return problems

    # -- python code blocks ------------------------------------------------- #
    def _check_python_blocks(self, markdown: str) -> list[str]:
        problems = []
        for block in _PY_BLOCK.findall(markdown):
            code = _dedent_block(block)
            try:
                tree = ast.parse(code)
            except SyntaxError:
                continue  # illustrative fragment, not runnable code
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                # Only bare calls are checked. A method call belongs to whatever
                # object is on the left (a cobra.Model, a DataFrame, a Path), not
                # to the package namespace, so there is nothing here that
                # could verify it -- and allow-listing every .items(), .replace()
                # and .rglob() the examples use would dilute the check that does
                # work. The failure this exists to catch, an invented function
                # imported and called (``from <package>.io import
                # import_model``), is a bare call and is still caught.
                name = func.id if isinstance(func, ast.Name) else None
                if name is None or name in _BUILTINS or name in self.allowed:
                    continue
                if name not in self.python:
                    problems.append(
                        f"`{name}(...)` is called in a Python example but is "
                        f"neither a {PROJECT.python_name} function nor an allow-listed name"
                    )
        return problems


def _strip_fences(markdown: str) -> str:
    """Remove fenced code blocks so only prose code spans are inspected."""
    out, inside = [], False
    for line in markdown.splitlines():
        if _FENCE.match(line):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def _dedent_block(block: str) -> str:
    """Undo the indentation a fenced block carries inside a content tab."""
    lines = block.splitlines()
    bodies = [ln for ln in lines if ln.strip()]
    if not bodies:
        return block
    pad = min(len(ln) - len(ln.lstrip()) for ln in bodies)
    return "\n".join(ln[pad:] if len(ln) >= pad else ln for ln in lines)


# --------------------------------------------------------------------------- #
# Standalone                                                                  #
# --------------------------------------------------------------------------- #
def main() -> int:
    index = Index()
    docs = HERE.parent / "docs"
    total = 0
    for md in sorted(docs.rglob("*.md")):
        rel = md.relative_to(docs).as_posix()
        problems = index.problems(md.read_text(encoding="utf-8"), rel)
        for problem in problems:
            print(f"{rel}: {problem}")
        total += len(problems)
    print(
        f"\n{total} problem(s); index holds {len(index.matlab)} {PROJECT.matlab_name} and "
        f"{len(index.python)} {PROJECT.python_name} names, plus {len(index.allowed)} "
        f"allow-listed."
    )
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
