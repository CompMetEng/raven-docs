#!/usr/bin/env python3
"""Turn the output of ``sphinx-build -b linkcheck`` into the body of an issue.

Usage:
    report_broken_links.py OUTPUT_JSON [--count] [--run-url URL]

OUTPUT_JSON is ``output.json`` in the linkcheck output folder: one JSON object
per line with ``filename``, ``lineno``, ``status``, ``code``, ``uri`` and ``info``.
Without options the script prints the Markdown body. With ``--count`` it prints
the number of distinct broken links instead.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

MAX_ROWS = 100
MAX_REASON = 120


def read(path: Path) -> list[dict]:
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def broken(entries: list[dict]) -> dict[str, dict]:
    """Broken links by address: the reason and the pages that contain the link."""
    found: dict[str, dict] = {}
    for entry in entries:
        if entry.get("status") != "broken":
            continue
        item = found.setdefault(entry["uri"], {"info": entry.get("info", ""), "where": []})
        place = f"{entry['filename']}:{entry['lineno']}"
        if place not in item["where"]:
            item["where"].append(place)
    return found


def cell(text: str, limit: int = 0) -> str:
    text = " ".join(str(text).split())
    if limit and len(text) > limit:
        text = text[: limit - 3].rstrip() + "..."
    return text.replace("|", "\\|")


def render(found: dict[str, dict], run_url: str = "") -> str:
    lines = [
        f"The weekly link check found {len(found)} broken external link(s).",
        "",
        "| Link | Reason | Found in |",
        "|---|---|---|",
    ]
    for uri in sorted(found)[:MAX_ROWS]:
        item = found[uri]
        places = ", ".join(f"`{p}`" for p in item["where"][:3])
        if len(item["where"]) > 3:
            places += f" and {len(item['where']) - 3} more"
        lines.append(f"| {cell(uri)} | {cell(item['info'], MAX_REASON)} | {places} |")
    if len(found) > MAX_ROWS:
        lines += ["", f"{len(found) - MAX_ROWS} more links are not listed."]
    lines += [
        "",
        "A link that rejects crawlers but works in a browser is added to `linkcheck_ignore` in `docs/conf.py`, with the reason as a comment.",
    ]
    if run_url:
        lines += ["", f"Workflow run: {run_url}"]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    args = argv[1:]
    run_url = ""
    if "--run-url" in args:
        i = args.index("--run-url")
        run_url = args[i + 1]
        del args[i:i + 2]
    count_only = "--count" in args
    args = [a for a in args if a != "--count"]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(args[0])
    if not path.is_file():
        print(f"{path} does not exist: the link check did not run", file=sys.stderr)
        return 2
    found = broken(read(path))
    print(len(found) if count_only else render(found, run_url), end="\n" if count_only else "")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
