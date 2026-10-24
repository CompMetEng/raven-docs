# Contributing to raven-docs

The standard for this site is the `docs-site` plugin of [CompMetEng/skills](https://github.com/CompMetEng/skills), and the intent of this site is in [DESIGN.md](DESIGN.md). Prose follows the `writing` skill of the `craft` plugin. The rules most often broken:

1. No em dashes anywhere: not in prose, headings, table cells or generated strings. Use the punctuation the sentence calls for: a comma where the clause continues, a semicolon where it is independent, a colon where what follows defines or lists what precedes it, parentheses around an aside.
2. Check every sentence while writing it:
   - Can the subject perform the verb? A file, function or table can return, raise, contain or default to. It cannot want, know or prefer, and it does nothing quietly or conveniently.
   - Does the sentence state a behaviour and its condition, or does it tell the reader what is worth doing? State the fact and leave the judgement to the reader.
   - Is the sentence about the software or about the document? Remove "this page is about" and "as mentioned above".
   - Does a word minimise something? Remove "just", "simply", "merely", "only", "of course" when the claim does not change.
   - Would a non-native English reader parse it on the first read? No idioms, figures of speech or headlines that drop the subject or verb.
3. Established technical shorthand (a domain term, a standard abbreviation) stays.
4. No mention of AI tools or AI authorship in the repository: not in commits, pull requests, code comments or pages. Branch names do not contain a tool name.

## Building and checking

```bash
git submodule update --init --recursive
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/check_site.py .
sphinx-build -W -b html docs docs/_build/html
```

Pages are written as described in the `docs-page` skill. A guide example is run before it is committed, and the output under it is the output of that run.
