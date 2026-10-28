#!/usr/bin/env python3
"""Checks for the rules that hold in every CompMetEng repository.

No commit, branch or pull request carries the name of an AI tool or its
authorship: not as author or committer, not in a trailer or a message, not in a
branch name, not in a footer of a pull request body. See the `writing` skill of
the `craft` plugin.

Usage:
    repo_hygiene.py commits RANGE         commits in a git range, for CI
    repo_hygiene.py commit-msg FILE       the message in FILE and the identity that commits (commit-msg hook)
    repo_hygiene.py pre-push              reads the pre-push hook input on stdin
    repo_hygiene.py branch NAME           one branch name
    repo_hygiene.py pr EVENT_JSON         the branch and the body of a pull request event

Every finding is printed as one line, and the exit status is 1 when there is one.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

TOOLS = r"claude|anthropic|chatgpt|copilot|codex"
TOOL_WORD = re.compile(rf"\b({TOOLS})\b", re.I)
# Names of configuration files and folders are not attribution.
CONFIG_NAMES = re.compile(r"claude\.md|\.claude(?:-plugin)?\b", re.I)
TOOL_BRANCH = re.compile(rf"^(refs/heads/)?({TOOLS})[/_-]", re.I)
PR_FOOTER = re.compile(r"generated with \[?claude|claude\.ai/code|co-authored-by:\s*claude", re.I)
ZEROS = "0" * 40


def identity_findings(role: str, name: str, email: str) -> list[str]:
    found = []
    if TOOL_WORD.search(name):
        found.append(f"{role} name '{name}' is the name of a tool")
    if email.lower().endswith("@anthropic.com"):
        found.append(f"{role} email '{email}' belongs to a tool vendor")
    return found


def message_findings(message: str) -> list[str]:
    found = []
    for number, line in enumerate(message.splitlines(), 1):
        match = TOOL_WORD.search(CONFIG_NAMES.sub("", line))
        if match:
            found.append(f"message line {number} mentions '{match.group(1)}'")
    return found


def branch_findings(name: str) -> list[str]:
    if TOOL_BRANCH.search(name):
        return [f"branch '{name}' is named after a tool"]
    return []


def pr_body_findings(body: str) -> list[str]:
    if body and PR_FOOTER.search(body):
        return ["the pull request body carries an AI attribution footer"]
    return []


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def commit_findings(rev_args: list[str]) -> list[str]:
    out = git("log", "--format=%H%x1f%an%x1f%ae%x1f%cn%x1f%ce%x1f%B%x1e", *rev_args)
    found = []
    for record in out.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        sha, an, ae, cn, ce, message = record.split("\x1f", 5)
        for text in (
            identity_findings("author", an, ae)
            + identity_findings("committer", cn, ce)
            + message_findings(message)
        ):
            found.append(f"commit {sha[:8]}: {text}")
    return found


def commit_msg(path: str) -> list[str]:
    found = message_findings(Path(path).read_text(encoding="utf-8"))
    for role in ("AUTHOR", "COMMITTER"):
        ident = git("var", f"GIT_{role}_IDENT").strip()
        match = re.match(r"(.*) <(.*)> \d+ [+-]\d{4}$", ident)
        if match:
            found += identity_findings(role.lower(), match.group(1), match.group(2))
    return found


def pre_push(stdin_text: str) -> list[str]:
    found = []
    for line in stdin_text.splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        local_ref, local_sha, remote_ref, remote_sha = parts
        if local_sha == ZEROS:  # a deletion
            continue
        found += branch_findings(remote_ref)
        if remote_sha == ZEROS:
            found += commit_findings([local_sha, "--not", "--remotes"])
        else:
            found += commit_findings([f"{remote_sha}..{local_sha}"])
    return found


def pr_event(path: str) -> list[str]:
    event = json.loads(Path(path).read_text(encoding="utf-8"))
    pr = event.get("pull_request") or {}
    return branch_findings((pr.get("head") or {}).get("ref", "")) + pr_body_findings(pr.get("body") or "")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    mode, args = argv[1], argv[2:]
    if mode == "commits" and len(args) == 1:
        found = commit_findings([args[0]])
    elif mode == "commit-msg" and len(args) == 1:
        found = commit_msg(args[0])
    elif mode == "pre-push":
        found = pre_push(sys.stdin.read())
    elif mode == "branch" and len(args) == 1:
        found = branch_findings(args[0])
    elif mode == "pr" and len(args) == 1:
        found = pr_event(args[0])
    else:
        print(__doc__, file=sys.stderr)
        return 2
    for line in found:
        print(f"repo-hygiene: {line}")
    if found:
        print("repo-hygiene: see the writing skill of the craft plugin (CompMetEng/skills)", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
