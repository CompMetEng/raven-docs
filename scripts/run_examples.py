"""Execute the Python examples in the guide pages and check their output.

The guide pages promise that the reader can paste a snippet and get the printed
result shown underneath it. Nothing enforces that: ``check_names.py`` only
verifies that the *names* in a page exist, so a page can name real functions,
call them with arguments that no longer work, and show output that was correct
two releases ago.

This script closes that gap, for **both** language tabs. For every page it

* collects the ```python (or ```matlab) blocks in order -- including the ones
  nested inside ``=== "Python"`` / ``=== "MATLAB"`` content tabs,
* runs a page's blocks in one namespace (one Python namespace, or one MATLAB
  workspace), in a scratch directory seeded with a copy of ``docs/data/``, so the
  snippets can use the short relative paths the reader sees,
* captures what the block prints -- plus the repr of a trailing expression, the
  way a notebook or the REPL would -- and compares it with the plain ``text`` block
  that follows,
* reports every mismatch as a unified diff and exits non-zero.

MATLAB needs a MATLAB runtime on the PATH (or ``RAVEN_DOCS_MATLAB`` pointing at
one); RAVEN itself comes from the submodule, and the bundled GLPK is used so no
solver licence is involved. When MATLAB is missing, its half is skipped with a
notice rather than failing -- unless it was asked for explicitly.

Usage::

    python scripts/run_examples.py                     # both languages, docs/guide
    python scripts/run_examples.py --language python   # one language
    python scripts/run_examples.py docs/guide/fba.md
    python scripts/run_examples.py --update            # rewrite output blocks in place
    python scripts/run_examples.py --list              # show what would run

Page-level control, written as HTML comments in the markdown:

``<!-- run-examples: skip-file -->``
    anywhere in the page -- the page is not executed at all (use for pages whose
    examples need BLAST, a KEGG download, or a commercial solver).
``<!-- run-examples: skip -->``
    immediately before a ```python block -- that one block is neither executed
    nor checked, but the ones after it still run.
``<!-- run-examples: needs-gurobi -->``
    the block selects Gurobi (a MILP the page runs on Gurobi rather than on the
    bundled GLPK): it runs where Gurobi is available (``--gurobi`` or
    ``RAVEN_DOCS_GUROBI=1``, which CI sets when a licence is configured) and is
    skipped everywhere else.

``<!-- run-examples: tabs-differ -->``
    anywhere in the page -- the cross-tab check below is not applied to it,
    because the two tabs genuinely print different things.

An expected-output block consisting of a single ``...`` matches anything, and
``...`` inside a block matches any run of characters -- the same convention as
doctest's ELLIPSIS. Use it for timings, paths and long tables.

When both languages run, the tabs of each section are compared: a value printed
under the same label with the opposite sign in the other tab is reported. That is
the one thing the per-block check cannot see, since a block that runs cleanly and
prints a wrong number still matches the wrong number written beneath it.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import difflib
import io
import os
import json
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_TARGET = ROOT / "docs" / "guide"
DATA_DIR = ROOT / "docs" / "data"

# The solver the pasted numbers are produced with. GLPK ships with cobrapy as a
# wheel, so it is the one solver every reader and every CI runner is guaranteed
# to have; pinning it keeps the output blocks reproducible.
DEFAULT_SOLVER = "glpk"

# RAVEN, for the MATLAB half: the submodule checkout, and whatever MATLAB the
# machine has. RAVEN bundles GLPK and libSBML mex files for Windows, macOS and
# Linux, so nothing else has to be installed.
RAVEN_DIR = Path(os.environ.get("RAVEN_DOCS_RAVEN_SRC", ROOT / "RAVEN"))
MATLAB_SOLVER = "glpk"
LANGUAGES = ("python", "matlab")

# The info string of an expected-output fence: a bare ```text directly below the
# code block. A titled text fence (```text title="tasks.txt") is an input shown
# to the reader, not output.
OUTPUT_INFO = "text"

SKIP_FILE = "run-examples: skip-file"
SKIP_BLOCK = "run-examples: skip"
NEEDS_GUROBI = "run-examples: needs-gurobi"

# Examples that select Gurobi run only where Gurobi is available: on a machine
# with a licence, and in CI when the workflow has one configured. They are
# skipped everywhere else rather than failing, so a reader without Gurobi still
# gets a green run.
GUROBI_ENABLED = os.environ.get("RAVEN_DOCS_GUROBI", "") not in ("", "0")

_FENCE_OPEN = re.compile(r"^(?P<indent>[ \t]*)(?P<ticks>`{3,})(?P<info>.*)$")
_HTML_COMMENT = re.compile(r"<!--(?P<body>.*?)-->")


# --------------------------------------------------------------------------
# Markdown scanning
# --------------------------------------------------------------------------


@dataclass
class Fence:
    """One fenced code block, wherever it sits in the page."""

    indent: str
    info: str
    body: list[str]
    start: int  # index of the opening ``` line
    end: int  # index of the closing ``` line

    @property
    def language(self) -> str:
        return self.info.strip().split(maxsplit=1)[0] if self.info.strip() else ""

    @property
    def code(self) -> str:
        strip = len(self.indent)
        return "\n".join(line[strip:] if line[:strip].isspace() or not line[:strip] else line.lstrip() for line in self.body)


@dataclass
class Example:
    """A ```python block, with the output block that follows it, if any."""

    page: Path
    number: int
    code_fence: Fence
    section: str = ""
    section_index: int = 0
    output_fence: Fence | None = None
    skip: bool = False
    actual: str | None = None
    error: str | None = None
    status: str = "pending"  # pending | ok | mismatch | error | skipped


@dataclass
class PageResult:
    page: Path
    language: str = "python"
    examples: list[Example] = field(default_factory=list)
    skipped_page: bool = False
    # The page as it was when the examples were collected. --update rewrites
    # blocks by line number, so a page edited while a run is in flight would be
    # rewritten from stale positions and end up with duplicated fences.
    source: str = ""

    @property
    def failures(self) -> list[Example]:
        return [e for e in self.examples if e.status in {"mismatch", "error"}]


def scan_fences(lines: list[str]) -> list[Fence]:
    """Return every fenced block in ``lines``, including indented ones.

    Content tabs indent their code by four spaces, so a naive ``^```` scan finds
    nothing on a dual-language page. Closing fences are matched on the same
    indentation and at least as many backticks as the opening fence, which is
    what CommonMark requires and what pymdownx accepts.
    """
    fences: list[Fence] = []
    i = 0
    while i < len(lines):
        match = _FENCE_OPEN.match(lines[i])
        if not match or "`" in match.group("info"):
            i += 1
            continue
        indent, ticks, info = match.group("indent"), match.group("ticks"), match.group("info")
        close = re.compile(rf"^{re.escape(indent)}`{{{len(ticks)},}}[ \t]*$")
        j = i + 1
        while j < len(lines) and not close.match(lines[j]):
            j += 1
        if j >= len(lines):  # unterminated fence -- leave it to the markdown build
            break
        fences.append(Fence(indent=indent, info=info, body=lines[i + 1 : j], start=i, end=j))
        i = j + 1
    return fences


def _marker_above(lines: list[str], fence: Fence) -> str | None:
    """The ``<!-- run-examples: ... -->`` marker just above the block, if any."""
    k = fence.start - 1
    while k >= 0 and not lines[k].strip():
        k -= 1
    if k < 0:
        return None
    for comment in _HTML_COMMENT.finditer(lines[k]):
        body = comment.group("body").strip()
        if body in (SKIP_BLOCK, NEEDS_GUROBI):
            return body
    return None


def _block_is_skipped(lines: list[str], fence: Fence) -> bool:
    marker = _marker_above(lines, fence)
    if marker == SKIP_BLOCK:
        return True
    if marker == NEEDS_GUROBI:
        return not GUROBI_ENABLED
    return False


def collect_examples(page: Path, language: str = "python") -> PageResult:
    source = page.read_text(encoding="utf-8")
    lines = source.splitlines()
    result = PageResult(page=page, language=language, source=source)
    if any(SKIP_FILE in line for line in lines):
        result.skipped_page = True
        return result

    headings = [
        (i, line.lstrip("#").strip())
        for i, line in enumerate(lines)
        if line.startswith("#")
    ]

    def section_of(line_no: int) -> str:
        title = ""
        for start, text in headings:
            if start < line_no:
                title = text
            else:
                break
        return title

    seen_per_section: dict[str, int] = {}
    fences = scan_fences(lines)
    for index, fence in enumerate(fences):
        if fence.language != language:
            continue
        section = section_of(fence.start)
        seen_per_section[section] = seen_per_section.get(section, 0) + 1
        output = None
        if index + 1 < len(fences):
            nxt = fences[index + 1]
            gap = lines[fence.end + 1 : nxt.start]
            if all(not line.strip() for line in gap) and nxt.info.strip() == OUTPUT_INFO:
                output = nxt
        result.examples.append(
            Example(
                page=page,
                number=len(result.examples) + 1,
                code_fence=fence,
                output_fence=output,
                skip=_block_is_skipped(lines, fence),
                section=section,
                section_index=seen_per_section[section],
            )
        )
    return result


# --------------------------------------------------------------------------
# Execution
# --------------------------------------------------------------------------


def _exec_block(code: str, namespace: dict) -> str:
    """Run one block and return what a notebook cell would have shown.

    Everything printed is captured, and if the block ends in a bare expression
    its repr is appended -- so ``model.reactions.get_by_id("r_0001")`` on the
    last line produces output without the page having to wrap it in ``print``.
    """
    tree = ast.parse(code)
    buffer = io.StringIO()
    last_expr: ast.Expr | None = None
    body = tree.body
    if body and isinstance(body[-1], ast.Expr):
        last_expr = body[-1]  # type: ignore[assignment]
        body = body[:-1]

    with contextlib.redirect_stdout(buffer):
        if body:
            exec(compile(ast.Module(body=body, type_ignores=[]), "<example>", "exec"), namespace)
        if last_expr is not None:
            value = eval(  # noqa: S307 -- documentation snippets, run deliberately
                compile(ast.Expression(last_expr.value), "<example>", "eval"), namespace
            )
            if value is not None:
                print(repr(value), file=buffer)
    return buffer.getvalue()


def run_page(result: PageResult, solver: str | None) -> None:
    """Execute a page's blocks in one namespace inside a scratch directory."""
    namespace: dict = {"__name__": "__main__"}
    workdir = Path(tempfile.mkdtemp(prefix="raven-docs-examples-"))
    if DATA_DIR.is_dir():
        for item in DATA_DIR.iterdir():
            if item.is_file() and item.name != "README.md":
                shutil.copy2(item, workdir / item.name)
    previous_cwd = Path.cwd()
    try:
        os.chdir(workdir)
        if solver:
            _pin_solver(solver)
        for example in result.examples:
            if example.skip:
                example.status = "skipped"
                continue
            try:
                example.actual = tidy_python(
                    _exec_block(example.code_fence.code, namespace)
                )
                example.status = "ok"  # provisional; compared below
            except BaseException:  # noqa: BLE001 -- a failing snippet is a finding
                example.error = traceback.format_exc(limit=3)
                example.status = "error"
                break  # later blocks depend on this one, so stop the page here
    finally:
        os.chdir(previous_cwd)
        shutil.rmtree(workdir, ignore_errors=True)


def find_matlab() -> str | None:
    """The MATLAB executable, from RAVEN_DOCS_MATLAB or the PATH."""
    explicit = os.environ.get("RAVEN_DOCS_MATLAB")
    if explicit:
        return explicit if Path(explicit).exists() else None
    return shutil.which("matlab")


_MATLAB_DRIVER = """function ravendocs_run(ravendocs_harness)
% Run every block of every page and write the captured output as JSON.
% One workspace per page, so a page's blocks build on each other exactly as the
% reader's session would.
% Warnings are part of what a reader sees, but their HTML links and stack
% traces name temporary paths that change every run -- turn both off so the
% captured text is stable.
feature('hotlinks', 'off');
warning('off', 'backtrace');
if ~isempty(getenv('GUROBI_HOME'))
    addpath(fullfile(getenv('GUROBI_HOME'), 'matlab'));
end
% RAVEN keeps the solver and the progress backend as MATLAB preferences, which
% outlive this process -- so remember whatever the machine had and put it back
% at the end. Without this, running the harness locally silently rewrites the
% reader's own RAVEN settings.
ravendocs_keys = {'solver', 'progressBar'};
ravendocs_prefs = struct('name', {}, 'value', {}, 'had', {});
for ravendocs_k = 1:numel(ravendocs_keys)
    ravendocs_key = ravendocs_keys{ravendocs_k};
    ravendocs_had = ispref('RAVEN', ravendocs_key);
    ravendocs_val = [];
    if ravendocs_had
        ravendocs_val = getpref('RAVEN', ravendocs_key);
    end
    ravendocs_prefs(end + 1) = struct( ...
        'name', ravendocs_key, 'value', {ravendocs_val}, 'had', ravendocs_had); %#ok<AGROW>
end
ravendocs_pages = dir(fullfile(ravendocs_harness, 'page_*'));
ravendocs_out = struct('page', {}, 'block', {}, 'output', {}, 'error', {});
addpath(genpath('@RAVEN@'));
% Progress bars redraw with carriage returns and pick their milestones from the
% terminal width, so the captured text would differ from machine to machine.
% This has to come after the addpath above: on a machine where RAVEN is not
% already on the saved path -- a CI runner, say -- setRavenProgress does not
% exist yet, and the progress lines end up in the documented output.
try
    setRavenProgress('none');
catch ravendocs_err
    fprintf(2, 'could not silence progress reporting: %s\\n', ravendocs_err.message);
end
for ravendocs_p = 1:numel(ravendocs_pages)
    ravendocs_dir = fullfile(ravendocs_harness, ravendocs_pages(ravendocs_p).name);
    ravendocs_blocks = dir(fullfile(ravendocs_dir, 'block_*.m'));
    cd(ravendocs_dir);
    clearvars -except ravendocs_*
    % setRavenSolver writes a MATLAB preference, which outlives the page
    % that set it -- so reset it per page, or one page choosing Gurobi
    % silently changes every page after it.
    try
        setRavenSolver('@SOLVER@');
    catch ravendocs_err
        fprintf(2, 'could not select solver: %s\\n', ravendocs_err.message);
    end
    for ravendocs_b = 1:numel(ravendocs_blocks)
        [~, ravendocs_name] = fileparts(ravendocs_blocks(ravendocs_b).name);
        ravendocs_entry = struct( ...
            'page', ravendocs_pages(ravendocs_p).name, ...
            'block', ravendocs_name, 'output', '', 'error', '');
        try
            ravendocs_entry.output = evalc(ravendocs_name);
        catch ravendocs_err
            ravendocs_entry.error = ravendocs_err.message;
        end
        ravendocs_out(end + 1) = ravendocs_entry; %#ok<AGROW>
        if ~isempty(ravendocs_entry.error)
            break   % later blocks depend on this one
        end
    end
end
for ravendocs_k = 1:numel(ravendocs_prefs)
    if ravendocs_prefs(ravendocs_k).had
        setpref('RAVEN', ravendocs_prefs(ravendocs_k).name, ...
            ravendocs_prefs(ravendocs_k).value);
    elseif ispref('RAVEN', ravendocs_prefs(ravendocs_k).name)
        rmpref('RAVEN', ravendocs_prefs(ravendocs_k).name);
    end
end
ravendocs_fid = fopen(fullfile(ravendocs_harness, 'results.json'), 'w');
fwrite(ravendocs_fid, jsonencode(ravendocs_out));
fclose(ravendocs_fid);
end
"""


def prepare_matlab(results: list[PageResult], harness: Path) -> dict[str, PageResult]:
    """Write the MATLAB harness: one directory per page, plus the driver.

    Split out from running it, because on GitHub-hosted runners MATLAB is only
    licensed when it is started by ``matlab-actions/run-command`` -- so CI
    prepares the harness, lets that action run the driver, and collects the
    results afterwards. Locally, :func:`run_matlab` does all three in one go.
    """
    harness.mkdir(parents=True, exist_ok=True)
    page_dirs: dict[str, PageResult] = {}
    runnable = [r for r in results if not r.skipped_page and r.examples]
    for index, result in enumerate(runnable, start=1):
        page_dir = harness / f"page_{index:02d}"
        page_dir.mkdir(exist_ok=True)
        page_dirs[page_dir.name] = result
        if DATA_DIR.is_dir():
            for item in DATA_DIR.iterdir():
                if item.is_file() and item.name != "README.md":
                    shutil.copy2(item, page_dir / item.name)
        for example in result.examples:
            if example.skip:
                example.status = "skipped"
                continue
            (page_dir / f"block_{example.number:02d}.m").write_text(
                example.code_fence.code + chr(10), encoding="utf-8"
            )

    driver = _MATLAB_DRIVER.replace("@RAVEN@", RAVEN_DIR.as_posix()).replace(
        "@SOLVER@", MATLAB_SOLVER
    )
    (harness / "ravendocs_run.m").write_text(driver, encoding="utf-8")
    return page_dirs


# MATLAB wraps warning text to the width of the command window, which differs
# between a developer's machine and a CI runner, and pads it with backspace
# characters once hotlinks are off. Flatten each warning to one line so the same
# warning compares equal everywhere.
# A warning ends at a "]" that closes the line -- not at the first "]" in the
# text, which may well be part of a quoted task or reaction id.
_MATLAB_WARNING = re.compile(
    r"\[Warning:.*?\](?=[ \t]*(?:\r?\n|$))", re.S
)


# Parallel Computing Toolbox chatter. Functions such as getAllowedBounds run in
# parallel, so the first one to be called opens a pool and says so -- naming a
# worker count that is a property of the machine, and only when no pool happens
# to be open already. Neither belongs in a documentation page.
_MATLAB_PARPOOL = re.compile(
    r"^(Starting parallel pool \(parpool\).*|Connected to parallel pool.*|"
    r"Parallel pool using the .* is shutting down\.)$"
)


# Both toolboxes fetch third-party binaries (BLAST+, DIAMOND, hmmer) from
# raven-data the first time a function needs one, and say so. Whether the line
# appears -- and its exact wording, which has drifted between toolbox versions
# ("Downloading blast+ from raven-data ...", "Downloading blast-2.17.0-...zip...
# COMPLETE") -- depends on what the machine has cached and which binary-fetch
# code is current, not on the example. Match on the leading word alone.
_BINARY_DOWNLOAD = re.compile(r"^Downloading .*$")


def tidy_matlab(text: str) -> str:
    text = text.replace(chr(8), "")  # backspaces left behind by hotlink removal
    text = _MATLAB_WARNING.sub(lambda m: " ".join(m.group(0).split()), text)
    keep = [
        line
        for line in text.split(chr(10))
        if not _MATLAB_PARPOOL.match(line.strip())
        and not _BINARY_DOWNLOAD.match(line.strip())
    ]
    return chr(10).join(keep)


# Solver chatter that is not the example's output: Gurobi's start-up banner --
# which names the machine's licence -- and the LP files optlang writes to a
# temporary path that changes every run. Neither belongs in a documentation page,
# and the licence line must never be written into one.
_SOLVER_NOISE = re.compile(
    r"^(Set parameter .*|Academic license.*|Restricted license.*|"
    r"Read LP format model from file .*|Reading time = .*|"
    r": \d+ rows, \d+ columns, \d+ nonzeros)$"
)


def tidy_python(text: str) -> str:
    keep = [
        line
        for line in text.split(chr(10))
        if not _SOLVER_NOISE.match(line.strip())
        and not _BINARY_DOWNLOAD.match(line.strip())
    ]
    return chr(10).join(keep)


def collect_matlab(
    page_dirs: dict[str, PageResult], harness: Path, diagnostics: str = ""
) -> None:
    """Read what MATLAB captured and attach it to the examples."""
    results_file = harness / "results.json"
    if not results_file.exists():
        for result in page_dirs.values():
            for example in result.examples:
                if example.status != "skipped":
                    example.status = "error"
                    example.error = (
                        "MATLAB produced no results. " + diagnostics.strip()
                    )
        return

    raw = json.loads(results_file.read_text(encoding="utf-8") or "[]")
    if isinstance(raw, dict):  # jsonencode collapses a one-element struct array
        raw = [raw]
    captured = {(entry["page"], entry["block"]): entry for entry in raw}
    for page_name, result in page_dirs.items():
        for example in result.examples:
            if example.status == "skipped":
                continue
            entry = captured.get((page_name, f"block_{example.number:02d}"))
            if entry is None:
                example.status = "error"
                example.error = "not reached (an earlier block on this page failed)"
            elif entry.get("error"):
                example.status = "error"
                example.error = entry["error"]
            else:
                example.actual = tidy_matlab(entry.get("output", ""))
                example.status = "ok"


def run_matlab(results: list[PageResult], matlab: str) -> None:
    """Prepare, run and collect in one go, with a locally licensed MATLAB.

    MATLAB takes tens of seconds to start, so all the pages share one process;
    each still gets its own directory and a cleared workspace.
    """
    if not [r for r in results if not r.skipped_page and r.examples]:
        return
    harness = Path(tempfile.mkdtemp(prefix="raven-docs-matlab-"))
    try:
        page_dirs = prepare_matlab(results, harness)
        command = [
            matlab, "-batch",
            f"addpath('{harness.as_posix()}'); ravendocs_run('{harness.as_posix()}')",
        ]
        completed = subprocess.run(  # noqa: S603 -- our own generated script
            command, cwd=str(ROOT), capture_output=True, text=True
        )
        collect_matlab(
            page_dirs, harness, completed.stderr or completed.stdout or ""
        )
    finally:
        shutil.rmtree(harness, ignore_errors=True)


def _pin_solver(solver: str) -> None:
    try:
        import cobra  # noqa: PLC0415 -- optional, and only needed at run time
    except ImportError:
        return
    try:
        cobra.Configuration().solver = solver
    except Exception as exc:  # noqa: BLE001 -- report, do not abort the run
        print(f"warning: could not select solver {solver!r}: {exc}", file=sys.stderr)


# --------------------------------------------------------------------------
# Comparison
# --------------------------------------------------------------------------


def normalise(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def matches(expected: str, actual: str) -> bool:
    """Compare with doctest-style ``...`` wildcards."""
    expected, actual = normalise(expected), normalise(actual)
    if expected.strip() == "...":
        return True
    if "..." not in expected:
        return expected == actual
    pattern = ".*?".join(re.escape(part) for part in expected.split("..."))
    return re.fullmatch(pattern, actual, flags=re.S) is not None


def compare(result: PageResult) -> None:
    for example in result.examples:
        if example.status != "ok" or example.output_fence is None:
            continue
        expected = "\n".join(
            line[len(example.output_fence.indent) :] if line.startswith(example.output_fence.indent) else line
            for line in example.output_fence.body
        )
        if not matches(expected, example.actual or ""):
            example.status = "mismatch"


# --------------------------------------------------------------------------
# Cross-tab check
# --------------------------------------------------------------------------

# A labelled value: "growth:    0.0809 /h" -> ("growth", 0.0809). Comparing
# labels rather than loose numbers is what makes this precise: the two tabs of a
# step print the same labels by convention, while the rest of their output --
# counts, dicts, warnings -- is free to differ.
_LABELLED = re.compile(
    r"^(?P<label>[A-Za-z][A-Za-z0-9 _()/-]*?)[:=]\s*"
    r"(?P<value>[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\b"
)
TABS_DIFFER = "run-examples: tabs-differ"


def labelled_values(text: str) -> dict[str, float]:
    """``{label: value}`` for every ``label: number`` line in the output."""
    found: dict[str, float] = {}
    for line in (text or "").split("\n"):
        match = _LABELLED.match(line.strip())
        if match:
            found[match.group("label").strip().lower()] = float(match.group("value"))
    return found


def cross_check(results: list[PageResult], tolerance: float = 1e-6) -> list[str]:
    """Report a labelled value whose sign differs between the two tabs.

    The runner checks that a block still prints what the page says it prints --
    not that the page says something true. A bug shipped that way: a MATLAB tab
    printing ``growth: -0.0809 /h`` beside a Python tab printing ``0.0809``,
    because the prose claimed ``solveLP`` returns a negated objective. Comparing
    the two tabs is what a reader does by eye; this does it automatically.

    Only **sign flips on the same label** are reported. Tabs legitimately print
    different counts, orderings and warnings -- section 9.2 of the quality-control
    page prints per-element imbalances on one side and totals on the other -- so a
    looser comparison is noise, and noise gets switched off.

    It cannot catch a page where *both* tabs are wrong in the same way: the
    solvers page once opened an uptake in the wrong direction, and both tabs
    agreed on a growth rate of zero. Only reading the page catches that.
    """
    by_page: dict[Path, dict[str, dict[tuple[str, int], Example]]] = {}
    for result in results:
        if result.skipped_page:
            continue
        for example in result.examples:
            if example.status != "ok" or example.actual is None:
                continue
            key = (example.section, example.section_index)
            by_page.setdefault(result.page, {}).setdefault(result.language, {})[key] = example

    findings: list[str] = []
    for page, languages in by_page.items():
        if TABS_DIFFER in page.read_text(encoding="utf-8"):
            continue
        python, matlab = languages.get("python", {}), languages.get("matlab", {})
        for key, py_example in python.items():
            ml_example = matlab.get(key)
            if ml_example is None:
                continue
            py_values = labelled_values(py_example.actual)
            ml_values = labelled_values(ml_example.actual)
            for label, value in py_values.items():
                other = ml_values.get(label)
                if other is None or abs(value) <= tolerance:
                    continue
                scale = tolerance * max(1.0, abs(value))
                if abs(value - other) > scale and abs(value + other) <= scale:
                    findings.append(
                        f"{rel(page)}: section {key[0]!r} prints {label!r} as "
                        f"{value:g} in the Python tab and {other:g} in the MATLAB tab"
                    )
    return findings


# --------------------------------------------------------------------------
# --update
# --------------------------------------------------------------------------


def update_page(result: PageResult) -> bool:
    """Rewrite each output block to what the snippet actually printed.

    Blocks that produced no output lose their output block; blocks that gained
    output get one inserted, indented to match the code block above it.
    Returns True when the file changed.
    """
    current = result.page.read_text(encoding="utf-8")
    if current != result.source:
        print(
            f"  skipped  {rel(result.page)}  (changed on disk since it was read; "
            f"re-run --update)"
        )
        return False
    lines = current.splitlines()
    edits: list[tuple[int, int, list[str]]] = []  # (start, end_exclusive, replacement)

    for example in result.examples:
        if example.status in {"skipped", "error"} or example.actual is None:
            continue
        if example.status == "ok" and example.output_fence is not None:
            # Already matches, so leave the author's wording alone -- including
            # deliberate inline ``...`` wildcards. The one exception is a block
            # that is *only* ``...``: that is the placeholder an author writes
            # while drafting, and filling it in is the point of --update.
            body = normalise("\n".join(example.output_fence.body))
            if body.strip() != "...":
                continue
        actual = normalise(example.actual)
        indent = example.code_fence.indent
        if actual:
            block = [f"{indent}```{OUTPUT_INFO}"]
            block += [f"{indent}{line}".rstrip() for line in actual.split("\n")]
            block += [f"{indent}```"]
        else:
            block = []
        if example.output_fence is not None:
            start, end = example.output_fence.start, example.output_fence.end + 1
            if not block:  # also drop the blank line that separated the blocks
                while start > example.code_fence.end + 1 and not lines[start - 1].strip():
                    start -= 1
            edits.append((start, end, block))
        elif block:
            insert_at = example.code_fence.end + 1
            edits.append((insert_at, insert_at, ["", *block]))

    if not edits:
        return False
    changed = False
    for start, end, block in sorted(edits, reverse=True):
        if lines[start:end] != block:
            lines[start:end] = block
            changed = True
    if changed:
        result.page.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def rel(path: Path) -> str:
    """Repo-relative path where possible -- pages may be passed from anywhere."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def report(results: list[PageResult]) -> int:
    failures = 0
    for result in results:
        page = f"{rel(result.page)} [{result.language}]"
        if result.skipped_page:
            print(f"  skip  {page}  (skip-file)")
            continue
        counts = {"ok": 0, "skipped": 0, "mismatch": 0, "error": 0}
        for example in result.examples:
            counts[example.status] = counts.get(example.status, 0) + 1
        state = "FAIL" if result.failures else "ok  "
        print(
            f"  {state}  {page}  "
            f"{counts['ok']} passed, {counts['skipped']} skipped, "
            f"{counts['mismatch']} mismatched, {counts['error']} errored"
        )
        for example in result.failures:
            failures += 1
            line = example.code_fence.start + 1
            print(f"\n    {page}:{line}  example {example.number}")
            if example.status == "error":
                for text in example.error.splitlines():
                    print(f"      {text}")
            else:
                expected = "\n".join(
                    li[len(example.output_fence.indent) :] if li.startswith(example.output_fence.indent) else li
                    for li in example.output_fence.body
                )
                diff = difflib.unified_diff(
                    normalise(expected).split("\n"),
                    normalise(example.actual or "").split("\n"),
                    fromfile="documented output",
                    tofile="actual output",
                    lineterm="",
                )
                for text in diff:
                    print(f"      {text}")
            print()
    return failures


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def gather_pages(targets: list[str]) -> list[Path]:
    if not targets:
        return sorted(DEFAULT_TARGET.rglob("*.md")) if DEFAULT_TARGET.is_dir() else []
    pages: list[Path] = []
    for target in targets:
        path = Path(target)
        if not path.is_absolute():
            path = ROOT / path
        pages.extend(sorted(path.rglob("*.md")) if path.is_dir() else [path])
    return pages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("targets", nargs="*", help="markdown files or directories (default: docs/guide)")
    parser.add_argument("--update", action="store_true", help="rewrite output blocks to the actual output")
    parser.add_argument("--list", action="store_true", help="list the examples without running them")
    parser.add_argument(
        "--language", choices=[*LANGUAGES, "both"], default="both",
        help="which tabs to run (default: both; MATLAB is skipped when no MATLAB is installed)",
    )
    parser.add_argument("--solver", default=DEFAULT_SOLVER, help=f"cobrapy solver to pin (default: {DEFAULT_SOLVER}; '' to leave alone)")
    parser.add_argument(
        "--gurobi", action="store_true",
        help="run the examples marked needs-gurobi as well (also RAVEN_DOCS_GUROBI=1)",
    )
    parser.add_argument(
        "--matlab-prepare", metavar="DIR",
        help="write the MATLAB harness to DIR and stop, for a runner that has to "
             "start MATLAB itself (see .github/workflows/examples.yml)",
    )
    parser.add_argument(
        "--matlab-collect", metavar="DIR",
        help="check the output MATLAB left in DIR after --matlab-prepare",
    )
    args = parser.parse_args(argv)

    if args.gurobi:
        globals()["GUROBI_ENABLED"] = True

    pages = gather_pages(args.targets)
    if not pages:
        print("run_examples: no pages found -- nothing to check.")
        return 0

    os.environ.setdefault("MPLBACKEND", "Agg")

    if args.matlab_prepare or args.matlab_collect:
        harness = Path(args.matlab_prepare or args.matlab_collect)
        collected = [collect_examples(page, "matlab") for page in pages]
        page_dirs = prepare_matlab(collected, harness)
        if args.matlab_prepare:
            print(f"run_examples: MATLAB harness written to {harness}")
            print(f"    run: addpath('{harness.as_posix()}'); ravendocs_run('{harness.as_posix()}')")
            return 0
        collect_matlab(page_dirs, harness)
        for result in collected:
            compare(result)
        print(f"run_examples: {sum(len(r.examples) for r in collected)} MATLAB example(s)")
        failures = report(collected)
        if failures:
            print(f"run_examples: {failures} failing example(s).")
            return 1
        print("run_examples: all examples match their documented output.")
        return 0

    languages = list(LANGUAGES) if args.language == "both" else [args.language]
    matlab = find_matlab() if "matlab" in languages else None
    if "matlab" in languages and matlab is None:
        if args.language == "matlab":
            print(
                "run_examples: no MATLAB found. Install one, or point "
                "RAVEN_DOCS_MATLAB at the executable."
            )
            return 1
        print("run_examples: no MATLAB found -- skipping the MATLAB tabs.")
        languages.remove("matlab")

    if args.list:
        for language in languages:
            for result in [collect_examples(page, language) for page in pages]:
                page = f"{rel(result.page)} [{language}]"
                if result.skipped_page:
                    print(f"{page}: skipped (skip-file)")
                    continue
                for example in result.examples:
                    mark = " (skip)" if example.skip else ""
                    has_output = " +output" if example.output_fence else ""
                    print(f"{page}:{example.code_fence.start + 1}  example {example.number}{mark}{has_output}")
        return 0

    def run_all(language: str) -> list[PageResult]:
        collected = [collect_examples(page, language) for page in pages]
        if language == "python":
            for result in collected:
                if not result.skipped_page and result.examples:
                    run_page(result, args.solver or None)
        else:
            run_matlab(collected, matlab)
        for result in collected:
            compare(result)
        return collected

    results: list[PageResult] = []
    for language in languages:
        collected = run_all(language)
        if args.update:
            for result in collected:
                if update_page(result):
                    print(f"  updated  {rel(result.page)} [{language}]")
            # Re-check, so the exit status reflects the updated files.
            collected = run_all(language)
        results.extend(collected)

    total = sum(len(r.examples) for r in results)
    print(f"run_examples: {total} example(s) in {len(pages)} page(s), {'+'.join(languages)}")
    failures = report(results)

    if len(languages) > 1:
        disagreements = cross_check(results)
        for finding in disagreements:
            print(f"  TABS  {finding}")
        if disagreements:
            print()
            print(f"run_examples: {len(disagreements)} sign flip(s) between the "
                  f"MATLAB and Python tabs. Fix the page, or mark it "
                  f"<!-- {TABS_DIFFER} --> if the two really do differ.")
            failures += len(disagreements)
    if failures:
        print(f"\nrun_examples: {failures} failing example(s).")
        print("Fix the snippet, or re-generate the output blocks with:")
        print("    python scripts/run_examples.py --update")
        return 1
    print("run_examples: all examples match their documented output.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
