#!/usr/bin/env python3
"""Report the prose patterns that craft/skills/writing/references/docs-prose.md discourages.

Usage: check_style.py [PATH ...] [--summary] [--strict]

A PATH that is a site directory (it has a docs/ folder) is scanned page by page with all
pattern families; the Markdown pages under docs/ are scanned, not docs/api/ and not
generated pages. A PATH that is a Markdown file is scanned with the general families only,
which hold for every text (README, pull request drafts, comments). A Python or MATLAB file is scanned in its docstrings or its leading help block with the same families. Code blocks, inline code,
link targets and directive lines are ignored. Prints one line per
page and pattern family as ``S warning path:line N x family: first match``. A pattern is
a heuristic: one hit can be correct, a family that recurs on a page is a reason to rewrite
the page. ``--summary`` prints the rate per 1000 words of every family over the site and
the pages with the highest rates. The exit code is 0 unless ``--strict`` is given and there
is a finding.

The families are aids for writing quality. A hit is not evidence about who wrote a text.
Lines between ``<!-- check_style:ignore-start -->`` and ``<!-- check_style:ignore-end -->``
(each marker on its own line, nestable) are not scanned, so a page can quote a pattern on purpose.
The families that depend on sentence position (concession, importance opener, sentence-initial
transition) are reported at the first line of the paragraph and are not
checked in docstrings.
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)

# Only the words that occur far more often in formulaic text than in ordinary prose; "very", "just",
# "quite", "simply" and "only" are common in careful writing and are not reported.
INTENSIFIERS = "actually|genuine(?:ly)?|essentially|basically|truly|fundamentally"
EVALUATIVE = "crucial|powerful|powerfully|comprehensive|seamless(?:ly)?|elegant"
# Adverbs that grade a method or other people's work. "well" counts when it ends a clause or follows a
# verb of performance; "as well", "well-defined", "well plate" and the noun ("the same well") do not
# match. "successfully" counts next to a verb of performance, since "completes successfully" reports
# a status.
EVALUATIVE_ADVERB = (
    r"elegantly|neatly|nicely|effortlessly"
    r"|successfully\s+(?:recover|reproduc|captur|identif|predict|combin|solv)\w*"
    r"|(?:recover|reproduc|captur|identif|predict|combin|solv)\w*\s+successfully"
    r"|(?<=\w\s)well(?=\s*(?:[.,;:!?)]|$|\s(?:but|and|yet|enough|for)\b))(?<!as well)"
    r"(?<!the well)(?<!a well)(?<!each well)(?<!per well)(?<!every well)(?<!one well)"
    r"(?<!same well)(?<!either well)(?<!empty well)(?<!this well)(?<!that well)(?<!other well)(?<!not do well)"
    r"|(?:works?|performs?|scales?|handles?|fits?|generali[sz]es?|captures?|describes?|predicts?|explains?|"
    r"does|did|answers?|covers?|serves?|reproduces?|recovers?|supports?|addresses|matches|agrees?)"
    r"(?: (?!as\b|not\b)[\w-]+){0,4} well\b(?! as\b)(?!-)(?!\s+plates?\b)"
)
# Words that occur far more often in formulaic scientific and encyclopaedic text than in earlier text.
# Words that are common in ordinary scientific prose (potential, findings, across, within) are left out.
STOCK_VOCABULARY = (
    r"delv(?:e|es|ed|ing)|tapestr(?:y|ies)|testament|pivotal|intricate|intricacies|meticulous(?:ly)?|"
    r"multifaceted|holistic(?:ally)?|paramount|cornerstone|myriad|plethora|realm|embark(?:s|ed|ing)?|"
    r"noteworthy|transformative|ever-evolving|cutting-edge|game-chang\w+|groundbreaking|invaluable|interplay|"
    r"(?:evolving|changing|shifting|current|competitive|regulatory|funding|digital|research|scientific) landscape"
)
STOCK_PHRASE = (
    r"plays? an? (?:\w+ )?(?:key|crucial|pivotal|vital|significant|important|critical|central)(?: \w+)? role"
    r"|a testament to|stands? as|stood as|sets? the stage|setting the stage|at its core|at the heart of"
    r"|in today's|in the realm of|when it comes to|it is worth (?:noting|mentioning)"
    r"|it is important to (?:note|mention|remember)|it should be noted|it bears mentioning|needless to say"
    r"|the reality is|the truth is|it turns out|here's (?:what|the thing|why|the catch|the problem|the kicker)"
    r"|the real (?:question|story|point|problem|issue)|dive (?:in|into)|deep dive|take a step back"
    r"|moving forward|at the end of the day|in this day and age|in recent years"
    r"|over the past (?:few |several )?(?:years|decades?)"
)
CONCESSION_INLINE = (
    r"\b(?:is|are|was|were|remains?) (?:\w+ ){0,2}(?:useful|valuable|effective|powerful|impressive|"
    r"successful|promising|well[- ]established),? (?:but|yet|though|however)\b"
    r"|\b(?:admittedly|to be fair|it is true that)\b"
)
TRANSITIONS = (
    "moreover|furthermore|additionally|notably|importantly|interestingly|crucially|ultimately|overall|"
    "consequently|indeed|in conclusion|in summary|to summari[sz]e|in essence|in short|put simply"
)
CONCESSIVE_OPENERS = re.compile(r"(?:although|though|even though|while)\b", re.I)
# A concession is formulaic when the concessive clause states a merit (the reference: "states a merit of
# the work so that the next clause can state its limit"). Ordinary concessives with "yet", "still" or
# "but" in the second clause and a fact in the first are plain English and are not reported.
CONCESSION_MERIT = re.compile(
    r"\b(?:valuable|useful|well|important|powerful|effective|impressive|successful|promising)\b",
    re.I,
)
IMPORTANCE_OPENER = re.compile(
    r"\b(?:among|one of) the (?:largest|most|biggest|greatest|leading|major|top)\b"
    r"|\bis (?:a|an) (?:major|growing|critical|pressing|fundamental|central|key|important|significant|global)\b"
    r"|\b(?:increasingly|ever-increasing|ever-growing)\b"
    r"|\bremains? (?:a|one of)\b[^.]{0,40}\b(?:challenge|threat|problem)\b",
    re.I,
)


def standalone_importance(sent: str) -> bool:
    """True when an importance phrase is the claim of the sentence. A phrase set off by commas
    inside a sentence that goes on to make another claim ("X, among the largest threats to
    health, is not only ...") is subordinated and is not reported."""
    for m in IMPORTANCE_OPENER.finditer(sent):
        before = sent[:m.start()].rfind(",")
        after = sent.find(",", m.end())
        if before > 0 and after != -1 and sent[after + 1:].strip() and not sent[before + 1:m.start()].strip(" ").count("."):
            continue
        return True
    return False


FIGURATIVE = (
    r"travels?|lands?|buys?|hooks?|traps?|silently|quietly|loses|"
    r"sits? (?:in|on|at|inside|where)|lives? (?:in|on|at|inside)|"
    r"fold(?:s|ed|ing)? into|housekeeping|(?:on|from) the \w+ side|routes?"
)
INFLATED = r"utili[sz]\w*|leverag\w+|facilitat\w+|foster\w*|showcas\w+|underscor\w+"

# Family name -> (pattern, flags). Each match counts once.
FAMILIES: dict[str, re.Pattern[str]] = {
    "second person": re.compile(r"\b(?:you|your|yours|yourself)\b", re.I),
    "first person plural": re.compile(r"\b(?:we|our|ours|us)\b(?! recommend)", re.I),
    "contraction": re.compile(r"\b\w+(?:n't|'re|'ve|'ll|'d)\b|\b(?:it|that|there|what|here|let)'s\b", re.I),
    "intensifier": re.compile(rf"\b(?:{INTENSIFIERS})\b", re.I),
    "evaluative word": re.compile(rf"\b(?:{EVALUATIVE})\b", re.I),
    "figurative verb": re.compile(rf"\b(?:{FIGURATIVE})\b", re.I),
    "inflated verb": re.compile(rf"\b(?:{INFLATED})\b", re.I),
    "evaluative adverb": re.compile(rf"\b(?:{EVALUATIVE_ADVERB})\b", re.I),
    "concession": re.compile(CONCESSION_INLINE, re.I),
    "rhetorical number": re.compile(
        r"\b(?:one|a single) (?:(?:key|main|central|simple|big|real) )?(?:question|insight|lesson|takeaway)\b", re.I
    ),
    "stock vocabulary": re.compile(rf"\b(?:{STOCK_VOCABULARY})\b", re.I),
    "stock phrase": re.compile(rf"\b(?:{STOCK_PHRASE})\b", re.I),
    "vague attribution": re.compile(
        r"\b(?:experts?|(?:many|some|several) (?:researchers|scientists|experts)) (?:believe|argue|agree|say)\b"
        r"|\b(?:studies|research|work) (?:have |has )?(?:show|shown|suggest|indicate|demonstrate)s?\b"
        r"(?!(?: that)?\s*[\d\[(])|\bit (?:has been shown|is well known)\b"
        r"|\bit is (?:widely|generally|commonly) (?:believed|recogni[sz]ed|accepted|assumed)\b"
        r"|\bwidely (?:recogni[sz]ed|regarded|accepted|adopted)\b",
        re.I,
    ),
    "reply boilerplate": re.compile(
        r"\b(?:I hope this helps|Great question|Good question|Happy to help|as of my last|knowledge cutoff)\b"
        r"|\b(?:Certainly|Of course)!|\[INSERT",
        re.I,
    ),
    "contrast scaffolding": re.compile(
        r"\bnot (?:just|only|merely|simply)\b|\bnot an? [^.;:,]{1,60}\bbut\b|\bnot [^.;:,]{1,40}, but\b"
        r"|\bmore than (?:just|merely|simply)\b",
        re.I,
    ),
    "passive instruction": re.compile(
        r"\b(?:is|are) (?:set|checked|inspected|closed|opened|added|run|restricted|excluded|compared) "
        r"(?:first|before|afterwards)\b",
        re.I,
    ),
    "evaluative tail": re.compile(
        r", (?:which is why|making|thereby)\b"
        r"|, (?:highlighting|underscoring|reflecting|showcasing|emphasi[sz]ing|symboli[sz]ing|demonstrating|"
        r"illustrating|fostering|cultivating|contributing to|paving|cementing|solidifying|reinforcing|"
        r"signalling|signaling)\b"
        r"|\bThis is what\b|\bThat is why\b",
    ),
    "labelled opener": re.compile(
        r"\b(?:the )?(?:practical consequence|catch|upshot|takeaway|bottom line|short version|key point|trick)\s*:",
        re.I,
    ),
    "reference to the document": re.compile(
        r"\bthis (?:page|section|chapter)\b|\bin this (?:guide|tutorial)\b"
        r"|\b(?:as )?(?:shown|mentioned|noted|described|discussed|listed|given) (?:above|below|earlier)\b"
        r"|\b(?:table|example|code|list|figure) (?:above|below)\b",
        re.I,
    ),
    "directive to the reader": re.compile(
        r"\b(?:make sure|be careful|be aware|keep in mind|bear in mind|do not forget|remember (?:that|to))\b", re.I
    ),
    "copula avoidance": re.compile(r"\b(?:serves? as|acts? as|functions? as|boasts?)\b", re.I),
    "generic attribution": re.compile(
        r"\b(?:generally|commonly|typically|in practice|arguably|potentially|possibly|perhaps|presumably|it appears that)\b", re.I
    ),
    "american spelling": re.compile(
        r"\b(?:behavior\w*|colors?|normaliz\w+|artifacts?|analyz\w+|optimiz\w+|initializ\w+|"
        r"visualiz\w+|standardiz\w+|organiz\w+|modeling|modeled|centers?|catalyz\w+)\b",
        re.I,
    ),
    "italic emphasis": re.compile(r"(?<![\*\w])\*(?!\*)[^*\s][^*]*?(?<!\*)\*(?!\*)"),
    "latin abbreviation": re.compile(r"\b(?:e\.g\.|i\.e\.|etc\.)", re.I),
    "percent spacing": re.compile(r"\d%"),
    "history word": re.compile(
        r"\b(?:previously|no longer|used to|formerly|obsolete|legacy|historical(?:ly)?)\b|\(was:", re.I
    ),
    "section number": re.compile(r"§\s?\d"),
    "negative definition": re.compile(r"\bNeither (?:is|of|implementation)\b|\b(?:is|are) not (?:a|an|the) ", re.I),
    "vague quantifier": re.compile(
        r"\b(?:a handful|a large (?:share|number)|a number of|much of|largely|predominantly|a couple of)\b", re.I
    ),
    "slash alternative": re.compile(r"\b[A-Za-z]{3,}/[A-Za-z]{3,}\b"),
    "dash": re.compile(rf"{EM_DASH}|(?<!\d){EN_DASH}|{EN_DASH}(?!\d)"),
}

# Families that hold for documentation pages only; the others hold for every text.
DOCS_ONLY = {
    "second person", "first person plural", "contraction", "passive instruction", "heading form", "box title", "bold",
    "italic emphasis", "section number", "table header", "long table cell",
}

HEADING_WORDS = re.compile(r"^(?:\d+(?:\.\d+)*\s+)?(?:what|why|how|when|which|where|who|is|are|do|does|can)\b", re.I)
HEADING_CONTRAST = re.compile(r"\bnot\b|\bvs\.?\b|\bversus\b|\?$", re.I)
GENERIC_BOX = re.compile(r"^(?:what can go wrong|if you read nothing else|heads up|gotcha)$", re.I)
IGNORE_START = re.compile(r"^\s*<!--\s*check_style:ignore-start\s*-->\s*$")
IGNORE_END = re.compile(r"^\s*<!--\s*check_style:ignore-end\s*-->\s*$")
ABBREVIATION = re.compile(r"\b(?:e\.g|i\.e|et al|vs|cf|Figs?|Eq|approx|ca|Dr|Mr|Ms|No|Ref)\.")
SENTENCE_BREAK = re.compile(r"(?<=[.!?])[\"')\]]*\s+(?=[\"'(\[]?(?:`|[A-Z0-9]))")

SKIP_FILES = {"docs/matlab-vs-python.md"}
SKIP_PREFIXES = ("docs/api/", "docs/_build/", "docs/_")


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Lines of prose with code, inline code, link targets and directive syntax removed."""
    out = []
    in_code = False
    for i, raw in enumerate(text.splitlines(), 1):
        stripped = raw.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_code = not in_code
            continue
        if in_code or not stripped:
            continue
        if re.match(r":{3,}(?:\{|\s*$)", stripped) and not re.match(r":{3,}\{(?:note|warning|tip|important|admonition)\}", stripped):
            continue
        if re.match(r":\w[\w-]*:", stripped) or stripped.startswith(("<!--", "---", "|-", "| -", "|:-")):
            continue
        line = re.sub(r"`[^`]*`", "`x`", raw)
        line = re.sub(r"\]\([^)]*\)", "]", line)
        line = re.sub(r"\{[a-z-]+\}`[^`]*`", "", line)
        out.append((i, line))
    return out


def strip_ignored(text: str) -> tuple[str, int]:
    """Text with the lines between ignore markers (and the markers) blanked, and the line of the
    first ignore-start marker that has no end marker (0 when all are closed). Line numbers are kept."""
    depth = 0
    open_lines: list[int] = []
    out = []
    for i, raw in enumerate(text.splitlines(), 1):
        if IGNORE_START.match(raw):
            depth += 1
            open_lines.append(i)
            out.append("")
        elif IGNORE_END.match(raw):
            depth = max(depth - 1, 0)
            if open_lines:
                open_lines.pop()
            out.append("")
        else:
            out.append("" if depth else raw)
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), (open_lines[0] if open_lines else 0)


def split_sentences(paragraph: str) -> list[str]:
    protected = ABBREVIATION.sub(lambda m: m.group(0).replace(".", "\x00"), paragraph)
    return [s.replace("\x00", ".").strip() for s in SENTENCE_BREAK.split(protected) if s.strip()]


def paragraphs(text: str) -> list[tuple[int, bool, list[str]]]:
    """(first line, is list item, sentences) of every prose paragraph; headings, tables and boxes are skipped."""
    out: list[tuple[int, bool, list[str]]] = []
    current: list[str] = []
    start, item, prev = 0, False, None

    def flush() -> None:
        if current:
            out.append((start, item, split_sentences(" ".join(current))))
        current.clear()

    for i, line in prose_lines(text):
        s = line.strip()
        if re.match(r"#{1,6}\s", s) or s.startswith("|") or re.match(r":{3,}\{", s):
            flush()
            prev = None
            continue
        marker = re.match(r"(?:>\s*|(?:[-*+]|\d+[.)])\s+)", s)
        if prev is None or i != prev + 1 or (marker and not s.startswith(">")):
            flush()
            start, item = i, bool(marker and not s.startswith(">"))
        current.append(s[marker.end():] if marker else s)
        prev = i
    flush()
    return out


def sentence_hits(text: str) -> dict[str, list[tuple[int, str]]]:
    """Families that depend on the position in a sentence or paragraph. The reported line is the
    first line of the paragraph."""
    hits: dict[str, list[tuple[int, str]]] = defaultdict(list)
    transition = re.compile(rf"(?:{TRANSITIONS})\b", re.I)
    for start, item, sentences in paragraphs(text):
        found = [sent.split(",")[0][:40] for sent in sentences if transition.match(sent)]
        if len(found) >= 2:  # one transition is ordinary prose; a recurrence in a paragraph is the signal
            hits["sentence-initial transition"].append((start, ", ".join(found[:2])))
        for k, sent in enumerate(sentences):
            m = CONCESSIVE_OPENERS.match(sent)
            if m and CONCESSION_MERIT.search(sent[m.end():sent.find(",", m.end()) if "," in sent[m.end():] else None]):
                hits["concession"].append((start, sent[:60]))
            if k == 0 and standalone_importance(sent):
                hits["importance opener"].append((start, sent[:60]))
    return hits


def title_case_heading(title: str) -> bool:
    """A heading of 4 or more words in which every later word of 4 or more letters starts with a capital
    letter (all-caps and mixed-case names are skipped) and there are at least 3 such words."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", title.replace("`x`", ""))
    plain = [w for w in words[1:] if len(w) > 3 and not w.isupper() and w[1:] == w[1:].lower()]
    return len(words) >= 4 and len(plain) >= 3 and all(w[0].isupper() for w in plain)


TABLE_CELL_WORDS = 35


def table_hits(text: str) -> dict[str, list[tuple[int, str]]]:
    """Tables with an empty header cell, and table cells longer than TABLE_CELL_WORDS words."""
    hits: dict[str, list[tuple[int, str]]] = defaultdict(list)
    lines = text.splitlines()
    in_code = False
    for i, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped.startswith(("```", "~~~")):
            in_code = not in_code
            continue
        if in_code or not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if re.fullmatch(r"\|?[\s:|-]+\|?", nxt) and "-" in nxt and any(not c for c in cells):
            hits["table header"].append((i + 1, "empty header cell"))
        for c in cells:
            n = len(re.sub(r"`[^`]*`", "x", c).split())
            if n > TABLE_CELL_WORDS and not re.fullmatch(r"[\s:|-]*", c):
                hits["long table cell"].append((i + 1, f"{n} words"))
                break
    return hits


def scan_page(
    text: str, docs: bool = True, sentences: bool = True
) -> tuple[int, dict[str, list[tuple[int, str]]]]:
    """(word count, family -> [(line, matched text)]) for one page or file."""
    words = 0
    hits: dict[str, list[tuple[int, str]]] = defaultdict(list)
    bold = 0
    text, unclosed = strip_ignored(text)
    if unclosed:
        hits["ignore marker"].append((unclosed, "ignore-start without ignore-end"))
    for i, line in prose_lines(text):
        heading = re.match(r"(#{1,6})\s+(.*)", line)
        box = re.match(r":{3,}\{(?:note|warning|tip|important|admonition)\}\s*(.*)", line.strip())
        if heading:
            title = heading.group(2).strip()
            if (
                HEADING_WORDS.match(title)
                or HEADING_CONTRAST.search(title)
                or title_case_heading(title)
            ):
                hits["heading form"].append((i, title))
        elif box:
            if GENERIC_BOX.match(box.group(1).strip()) or box.group(1).strip().endswith(("?", ".")):
                hits["box title"].append((i, box.group(1).strip()))
            continue
        else:
            words += len(line.split())
            bold += len(re.findall(r"\*\*[^*]+\*\*", line))
        for name, pat in FAMILIES.items():
            for m in pat.finditer(line):
                hits[name].append((i, m.group(0)))
    if sentences:
        for name, found in sentence_hits(text).items():
            hits[name].extend(found)
    if docs:
        for name, found in table_hits(text).items():
            hits[name].extend(found)
    if words and bold * 1000 / words > 5:
        hits["bold"].append((0, f"{bold} bold spans in {words} words"))
    if not docs:
        hits = defaultdict(list, {k: v for k, v in hits.items() if k not in DOCS_ONLY})
    return words, hits


def docstrings(path: Path) -> list[str]:
    """Docstrings of a Python file or the leading help block of a MATLAB file."""
    import ast

    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix == ".py":
        out = []
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    out.append(doc)
        return out
    block: list[str] = []
    started = False
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("%"):
            started = True
            block.append(stripped.lstrip("%")[1:] if stripped.lstrip("%").startswith(" ") else stripped.lstrip("%"))
        elif started:
            break
    return ["\n".join(block)] if block else []


def site_pages(site: Path) -> list[Path]:
    pages = []
    for p in sorted((site / "docs").rglob("*.md")):
        rel = str(p.relative_to(site)).replace("\\", "/")
        if rel in SKIP_FILES or rel.startswith(SKIP_PREFIXES):
            continue
        pages.append(p)
    return pages


def run(site: Path, summary: bool = False, files: list[Path] | None = None) -> tuple[list[str], int]:
    lines: list[str] = []
    total_words = 0
    totals: Counter[str] = Counter()
    per_page: list[tuple[float, str, int, int]] = []
    findings = 0
    for p in files if files is not None else site_pages(site):
        rel = str(p.relative_to(site)).replace("\\", "/") if files is None else str(p)
        words, hits = scan_page(p.read_text(encoding="utf-8"), docs=files is None)
        total_words += words
        n = 0
        for name, found in hits.items():
            totals[name] += len(found)
            n += len(found)
            line_no, text = found[0]
            where = f"{rel}:{line_no}" if line_no else rel
            lines.append(f"S warning {where} {len(found)} x {name}: {text[:80]}")
            findings += 1
        if words:
            per_page.append((n * 1000 / words, rel, n, words))
    if summary:
        lines.append(f"\n{total_words} words of prose in {len(per_page)} pages")
        for name, count in totals.most_common():
            lines.append(f"  {count:5d}  {count * 1000 / max(total_words, 1):5.2f} per 1000 words  {name}")
        lines.append("\nPages by hits per 1000 words")
        for rate, rel, n, words in sorted(per_page, reverse=True)[:15]:
            lines.append(f"  {rate:5.1f}  {n:4d} hits  {words:6d} words  {rel}")
    return lines, findings


def run_docstrings(path: Path) -> tuple[list[str], int]:
    """Scan the docstrings of a Python file or the help block of a MATLAB file, general families only."""
    totals: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for doc in docstrings(path):
        _, hits = scan_page(doc, docs=False, sentences=False)
        for name, found in hits.items():
            totals[name].extend(found)
    lines = [f"S warning {path} {len(found)} x {name}: {found[0][1]}" for name, found in totals.items()]
    return lines, len(lines)


def main(argv: list[str]) -> int:
    args = argv[1:]
    summary = "--summary" in args
    strict = "--strict" in args
    args = [a for a in args if not a.startswith("--")] or ["."]
    findings = 0
    for arg in args:
        path = Path(arg).resolve()
        if path.is_file() and path.suffix in (".py", ".m"):
            lines, n = run_docstrings(path)
        elif path.is_file():
            lines, n = run(path.parent, summary, files=[path])
        elif (path / "docs").is_dir():
            lines, n = run(path, summary)
        else:
            print(f"{path} is neither a Markdown file nor a site with a docs/ folder", file=sys.stderr)
            return 2
        for line in lines:
            print(line)
        findings += n
    print(f"{findings} finding(s)")
    return 1 if strict and findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
