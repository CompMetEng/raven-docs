#!/usr/bin/env python3
"""Check a documentation site against the docs-site standard.

Usage: check_site.py [SITE_DIR] [--against PLUGIN_SCRIPTS_DIR]

With --against, the scripts in SITE_DIR/scripts that also exist in the plugin are
compared with the plugin copies, and a difference is an error.

Prints one finding per line as ``CODE severity path[:line] message`` and exits
with 1 when there is an error. Warnings do not change the exit code.

Codes: L layout, N name, C configuration, D design file, S style, P page.
"""

from __future__ import annotations

import configparser
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REQUIRED_FILES = [
    ".gitmodules",
    ".readthedocs.yaml",
    "CONTRIBUTING.md",
    "DESIGN.md",
    "README.md",
    "requirements.txt",
    "docs/conf.py",
    "docs/index.md",
    "docs/_static/custom.css",
    "docs/_static/language-sync.js",
    "scripts/gen_api_pages.py",
    "scripts/project.yml",
]

# Scripts that every site copies unchanged from the plugin.
SHARED_SCRIPTS = [
    "project.py", "api_index.py", "gen_api_pages.py", "autolink.py",
    "check_names.py", "run_examples.py", "check_site.py", "report_broken_links.py",
]

WRONG_NAMES = {
    "requirements-sphinx.txt": "requirements.txt",
    "scripts/gen_api_pages_sphinx.py": "scripts/gen_api_pages.py",
}

GENERATED = ["docs/api/matlab", "docs/api/python", "docs/matlab-vs-python.md"]

DESIGN_HEADINGS = ["Purpose", "Decisions log"]

TEXT_SUFFIXES = {".md", ".py", ".yml", ".yaml", ".css", ".cff", ".txt", ".toml"}
SKIP_DIRS = {".git", ".venv", "_build", "__pycache__", "node_modules"}

EM_DASH = chr(0x2014)
AI_WORDS = re.compile(r"\b(claude|anthropic|chatgpt|copilot|co-authored-by)\b", re.I)
AI_BRANCH = re.compile(r"\b(claude|anthropic|codex|copilot|chatgpt)/", re.I)
# Files that state the rules or implement the check name what they forbid.
RULE_FILES = {"scripts/check_site.py", "CONTRIBUTING.md"}

GUIDE_EXPECTED = ["Functions on this page", "What can go wrong", "See also"]
# A page that explains a concept instead of a task opts out of the anatomy.
CONCEPT_MARKER = "<!-- docs-site: concept-page -->"


@dataclass
class Finding:
    code: str
    severity: str
    path: str
    message: str
    line: int | None = None

    def __str__(self) -> str:
        where = f"{self.path}:{self.line}" if self.line else self.path
        return f"{self.code} {self.severity} {where} {self.message}"


def tracked_files(site: Path) -> list[Path]:
    """Files of the site, excluding submodules and build output."""
    try:
        out = subprocess.run(
            ["git", "-C", str(site), "ls-files", "-z"],
            check=True, capture_output=True, text=True,
        ).stdout
        files = [site / p for p in out.split("\0") if p]
    except (subprocess.CalledProcessError, FileNotFoundError):
        files = [p for p in site.rglob("*") if p.is_file()]
    submodules = set(submodule_paths(site))
    keep = []
    for p in files:
        rel = p.relative_to(site)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if rel.parts and rel.parts[0] in submodules:
            continue
        if p.is_file():
            keep.append(p)
    return keep


def submodule_paths(site: Path) -> list[str]:
    cfg = read_gitmodules(site)
    return [cfg[s].get("path", "") for s in cfg.sections() if cfg.has_option(s, "path")]


def read_gitmodules(site: Path) -> configparser.RawConfigParser:
    cfg = configparser.RawConfigParser()
    path = site / ".gitmodules"
    if path.is_file():
        cfg.read(path, encoding="utf-8")
    return cfg


def check_layout(site: Path) -> list[Finding]:
    out = []
    for rel in REQUIRED_FILES:
        if not (site / rel).exists():
            out.append(Finding("L", "error", rel, "required file is missing"))
    for old, new in WRONG_NAMES.items():
        if (site / old).exists():
            out.append(Finding("N", "error", old, f"rename to {new}"))
    return out


def check_generated(site: Path, files: list[Path]) -> list[Finding]:
    out = []
    rels = {str(p.relative_to(site)).replace("\\", "/") for p in files}
    for gen in GENERATED:
        hit = sorted(r for r in rels if r == gen or r.startswith(gen + "/"))
        if hit:
            out.append(Finding("L", "error", gen, f"generated at build time but committed ({len(hit)} file(s))"))
    gitignore = site / ".gitignore"
    text = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    for gen in GENERATED:
        if gen not in text and gen + "/" not in text:
            out.append(Finding("L", "warning", ".gitignore", f"does not list the generated path {gen}"))
    return out


def check_gitmodules(site: Path) -> list[Finding]:
    out = []
    cfg = read_gitmodules(site)
    for section in cfg.sections():
        name = section
        if not cfg.has_option(section, "branch"):
            out.append(Finding("C", "error", ".gitmodules", f"{name}: no branch is set"))
        if cfg.get(section, "shallow", fallback="").lower() != "true":
            out.append(Finding("C", "error", ".gitmodules", f"{name}: shallow = true is not set"))
    return out


def find_line(text: str, pattern: str) -> int | None:
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(pattern, line):
            return i
    return None


def check_readthedocs(site: Path) -> list[Finding]:
    path = site / ".readthedocs.yaml"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    out = []
    if not re.search(r"^submodules:\s*\n\s+include:\s*all", text, re.M):
        out.append(Finding("C", "error", ".readthedocs.yaml", "submodules.include must be all"))
    if not re.search(r"^\s+recursive:\s*true", text, re.M):
        out.append(Finding("C", "error", ".readthedocs.yaml", "submodules.recursive must be true"))
    if not re.search(r"^\s+fail_on_warning:\s*true", text, re.M):
        out.append(Finding("C", "error", ".readthedocs.yaml", "sphinx.fail_on_warning must be true"))
    if not re.search(r"requirements:\s*requirements\.txt", text):
        out.append(Finding("C", "error", ".readthedocs.yaml", "python.install must use requirements.txt"))
    return out


def check_conf(site: Path) -> list[Finding]:
    path = site / "docs" / "conf.py"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    out = []
    expected = {
        r"^smartquotes\s*=\s*False": "smartquotes = False",
        r"^html_show_sourcelink\s*=\s*False": "html_show_sourcelink = False",
        r'^html_theme\s*=\s*"pydata_sphinx_theme"': 'html_theme = "pydata_sphinx_theme"',
        r'"collapse_navigation":\s*True': '"collapse_navigation": True',
        r'"default_mode":\s*"auto"': '"default_mode": "auto"',
    }
    for pattern, label in expected.items():
        if not re.search(pattern, text, re.M):
            out.append(Finding("C", "error", "docs/conf.py", f"{label} is not set"))
    for ext in ("myst_parser", "sphinx_design", "sphinx_copybutton"):
        if f'"{ext}"' not in text:
            out.append(Finding("C", "error", "docs/conf.py", f"extension {ext} is not enabled"))
    if re.search(r"html_(logo|favicon)\s*=\s*\"assets/", text) or re.search(r'"image_(light|dark)":\s*"assets/', text):
        out.append(Finding("C", "error", "docs/conf.py", "logo and favicon paths are relative to _static/, not assets/"))
    if not re.search(r"html_js_files\s*=\s*\[[^\]]*[\"']language-sync\.js[\"']", text):
        out.append(Finding("C", "error", "docs/conf.py", "html_js_files does not list language-sync.js"))
    logo = re.search(r'"image_light":\s*"([^"]+)"\s*,\s*"image_dark":\s*"([^"]+)"', text, re.S)
    if logo and logo.group(1) == logo.group(2):
        out.append(Finding("C", "error", "docs/conf.py", "the dark-mode logo is the same file as the light-mode logo"))
    return out


def check_css(site: Path) -> list[Finding]:
    path = site / "docs" / "_static" / "custom.css"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    out = []
    for cls in ("site-hero", "site-logo-row", "site-tag", "site-tagline", "site-logo-light", "site-logo-dark"):
        if f".{cls}" not in text:
            out.append(Finding("C", "error", "docs/_static/custom.css", f"class .{cls} is not defined"))
    for var in ("--site-accent", "--pst-color-primary", "--pst-color-link"):
        if var not in text:
            out.append(Finding("C", "error", "docs/_static/custom.css", f"{var} is not set"))
    for m in re.finditer(r"--pst-color-(?:primary|link)\s*:\s*([^;]+);", text):
        value = m.group(1).strip()
        if re.fullmatch(r"\d+\s*,\s*\d+\s*,\s*\d+", value):
            out.append(Finding("C", "error", "docs/_static/custom.css", f"colour value '{value}' is a list of numbers, not a colour"))
    return out


def check_design(site: Path) -> list[Finding]:
    path = site / "DESIGN.md"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    headings = [re.sub(r"^[#\s\d.]+", "", h).strip().lower() for h in re.findall(r"^#{1,3} .*$", text, re.M)]
    out = []
    for want in DESIGN_HEADINGS:
        if not any(h.startswith(want.lower()) for h in headings):
            out.append(Finding("D", "error", "DESIGN.md", f"no section '{want}'"))
    return out


def check_text(site: Path, files: list[Path]) -> list[Finding]:
    out = []
    for p in files:
        rel = str(p.relative_to(site)).replace("\\", "/")
        if p.suffix not in TEXT_SUFFIXES:
            continue
        if rel.startswith("docs/api/") or rel.endswith("known_names.txt"):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if EM_DASH in line:
                out.append(Finding("S", "error", rel, "em dash", i))
            if rel in RULE_FILES:
                continue
            m = AI_WORDS.search(line)
            if m and p.suffix != ".txt":
                out.append(Finding("S", "error", rel, f"mentions '{m.group(0)}'", i))
            if AI_BRANCH.search(line):
                out.append(Finding("S", "error", rel, "branch name with a tool name", i))
    return out


def hard_wrapped_paragraphs(text: str) -> int:
    """Count prose paragraphs of three or more consecutive lines."""
    count = 0
    run = 0
    in_code = False
    for raw in text.splitlines() + [""]:
        line = raw.rstrip()
        if line.lstrip().startswith(("```", ":::")):
            in_code = not in_code if line.lstrip().startswith("```") else in_code
            run = 0
            continue
        prose = (
            bool(line.strip())
            and not in_code
            and not line.lstrip().startswith(("|", "#", "-", "*", "+", ">", "<", ":", "{", "!"))
            and not re.match(r"\s*\d+[.)] ", line)
            and not re.match(r"\s*\[.*\]:", line)
        )
        if prose:
            run += 1
        else:
            if run >= 3:
                count += 1
            run = 0
    return count


def heading_skips(text: str) -> tuple[int, int, int] | None:
    """(line, previous level, level) of the first heading that skips a level."""
    prev = 0
    in_code = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        m = re.match(r"(#{1,6}) \S", line)
        if in_code or not m:
            continue
        level = len(m.group(1))
        if prev and level > prev + 1:
            return i, prev, level
        prev = level
    return None


def check_pages(site: Path, files: list[Path]) -> list[Finding]:
    out = []
    for p in files:
        rel = str(p.relative_to(site)).replace("\\", "/")
        if p.suffix != ".md" or not rel.startswith("docs/") or rel.startswith("docs/api/"):
            continue
        text = p.read_text(encoding="utf-8")
        n = hard_wrapped_paragraphs(text)
        if n:
            out.append(Finding("S", "warning", rel, f"{n} hard-wrapped paragraph(s); one line per paragraph"))
        skip = heading_skips(text)
        if skip:
            out.append(Finding("P", "error", rel, f"heading level jumps from H{skip[1]} to H{skip[2]} (strict build warns)", skip[0]))
        if rel.startswith("docs/guide/") and p.name != "index.md" and CONCEPT_MARKER not in text:
            for h in GUIDE_EXPECTED:
                if not re.search(rf"^#+ {re.escape(h)}", text, re.M):
                    out.append(Finding("P", "warning", rel, f"no '{h}' section"))
    return out


def aggregate(findings: list[Finding], examples: int = 3) -> list[str]:
    """One line per kind of warning, so a site-wide habit is one line, not one per page."""
    lines = []
    groups: dict[tuple[str, str], list[Finding]] = {}
    for f in findings:
        if f.severity == "error":
            lines.append(str(f))
        else:
            key = (f.code, re.sub(r"\d+ hard-wrapped paragraph\(s\)", "hard-wrapped paragraphs", f.message))
            groups.setdefault(key, []).append(f)
    for (code, message), group in groups.items():
        if len(group) == 1:
            lines.append(str(group[0]))
            continue
        shown = ", ".join(f.path for f in group[:examples])
        more = f" and {len(group) - examples} more" if len(group) > examples else ""
        lines.append(f"{code} warning {len(group)} files: {message} ({shown}{more})")
    return lines


def check_shared_scripts(site: Path, plugin_scripts: Path) -> list[Finding]:
    out = []
    for name in SHARED_SCRIPTS:
        mine, theirs = site / "scripts" / name, plugin_scripts / name
        if not mine.is_file() or not theirs.is_file():
            continue
        if mine.read_bytes() != theirs.read_bytes():
            out.append(Finding("N", "error", f"scripts/{name}", "differs from the plugin copy"))
    return out


def run(site: Path, plugin_scripts: Path | None = None) -> list[Finding]:
    files = tracked_files(site)
    findings: list[Finding] = []
    findings += check_layout(site)
    findings += check_generated(site, files)
    findings += check_gitmodules(site)
    findings += check_readthedocs(site)
    findings += check_conf(site)
    findings += check_css(site)
    findings += check_design(site)
    findings += check_text(site, files)
    findings += check_pages(site, files)
    if plugin_scripts is not None:
        findings += check_shared_scripts(site, plugin_scripts)
    return findings


def main(argv: list[str]) -> int:
    args = argv[1:]
    plugin_scripts = None
    if "--against" in args:
        i = args.index("--against")
        plugin_scripts = Path(args[i + 1]).resolve()
        del args[i:i + 2]
    site = Path(args[0] if args else ".").resolve()
    if not site.is_dir():
        print(f"{site} is not a directory", file=sys.stderr)
        return 2
    findings = run(site, plugin_scripts)
    for line in aggregate(findings):
        print(line)
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = len(findings) - errors
    print(f"{errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
