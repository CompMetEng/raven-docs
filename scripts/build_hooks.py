"""MkDocs build hooks that keep the site resilient to submodule restructuring.

raven-docs documents the RAVEN (MATLAB) and raven-toolbox sources tracked as git
submodules on their fast-moving ``develop`` branches. When
those branches add or remove folders or files, a statically-configured build
breaks. These hooks make the build adapt automatically instead of aborting:

* ``on_config``        -- prune the mkdocstrings ``matlab`` handler ``paths`` to
                          only directories that actually exist, so a removed
                          category folder (e.g. ``visualization``) no longer
                          aborts the build with a "paths do not exist" error.
* ``on_page_markdown`` -- replace ``--8<--`` snippet includes whose source file
                          is missing with a visible note, so a removed source
                          file (e.g. a dropped tutorial script) renders a
                          warning instead of raising ``SnippetMissingError``.

Both log a warning for every pruned path / missing snippet, so the gaps stay
visible in the build log rather than failing silently.

Registered via the ``hooks:`` key in mkdocs.yml.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from mkdocs.plugins import event_priority

log = logging.getLogger("mkdocs.hooks.build_hooks")

# Matches a single-line pymdownx.snippets include: --8<-- "path/to/file"
_SNIPPET_RE = re.compile(r'^(?P<indent>[ \t]*)--8<--[ \t]+"(?P<path>[^"]+)"[ \t]*$', re.M)


def _repo_root(config) -> Path:
    """Directory containing mkdocs.yml (the snippets base_path and submodule root)."""
    return Path(config["config_file_path"]).resolve().parent


@event_priority(100)  # Run before mkdocstrings' on_config instantiates handlers.
def on_config(config):
    """Drop non-existent directories from the mkdocstrings matlab handler paths."""
    root = _repo_root(config)
    plugin = config["plugins"].get("mkdocstrings")
    if plugin is None:
        return config

    handlers = plugin.config.handlers or {}
    matlab = handlers.get("matlab")
    if not matlab or "paths" not in matlab:
        return config

    kept, dropped = [], []
    for rel in matlab["paths"]:
        (kept if (root / rel).is_dir() else dropped).append(rel)

    if dropped:
        log.warning(
            "build_hooks: pruning %d missing matlab path(s) from the API "
            "reference (not present on the tracked branch): %s",
            len(dropped),
            ", ".join(dropped),
        )
        matlab["paths"] = kept

    return config


def on_page_content(html, *, page, config, **kwargs):
    """Strip the repeated MATLAB function name from docstring descriptions.

    MATLAB convention puts the function name on the first help line:
        % checkProduction Check which metabolites can be produced from a model.
    mkdocstrings-matlab renders this verbatim, duplicating the h3 heading that
    our page generator already emits.  This hook removes the leading word when
    it matches a camelCase identifier followed by a capital letter (i.e. the
    start of the real description).
    """
    if not page.file.src_path.replace("\\", "/").startswith("api/matlab/"):
        return html
    # Require at least one uppercase letter inside the identifier so plain
    # English words like "see", "use", "for" are not accidentally stripped.
    # \s+ handles the MATLAB two-space convention after the function name.
    html = re.sub(
        r"(<p>)([a-z][a-z0-9]*(?:[A-Z][A-Za-z0-9]*)+)\s+([A-Z])",
        r"\1\3",
        html,
    )
    return html


def on_page_markdown(markdown, *, page, config, files):
    """Neutralize snippet includes whose source file is missing."""
    root = _repo_root(config)

    def replace(match: re.Match) -> str:
        indent, rel = match.group("indent"), match.group("path")
        if (root / rel).is_file():
            return match.group(0)
        log.warning(
            "build_hooks: snippet '%s' referenced by '%s' is missing on the "
            "tracked branch; rendering a placeholder note instead.",
            rel,
            page.file.src_path,
        )
        return (
            f'{indent}!!! warning "Source not available"\n'
            f'{indent}    `{rel}` is not present on the currently tracked '
            f"branch, so its contents cannot be shown here."
        )

    return _SNIPPET_RE.sub(replace, markdown)
