# How to use this second brain (for any AI assistant)

This folder is a **portable personal knowledge base**. It is plain Markdown + JSON, with no
dependency on any single app or AI vendor. These instructions let any assistant — Claude, ChatGPT,
Gemini, a local model — read, reason over, and extend it consistently. Point your tool at this
folder and read this file first.

## Layout

```
index.md      # human-readable Map of Content, grouped by note type (generated)
graph.json    # machine-readable {nodes, edges} (generated)
notes/*.md    # the notes: YAML frontmatter + Markdown body + [[wikilinks]]
```

## How a note works

Each note in `notes/` starts with YAML frontmatter and then a Markdown body:

```markdown
---
title: ...
type: reference        # reference | source | meeting-note | project | person | idea | hub
tags: [...]
created: YYYY-MM-DD
source: "..."
relations:
  - type: references   # part-of | contains | references | supersedes | related-to | authored-by | depends-on
    target: other-note-stem
---
## Summary
...
## Notes
...
## Related
- ... [[other-note-stem]]
```

- A note's **id** is its filename without `.md` (its "stem"). Links use `[[stem]]`.
- **Relations** in frontmatter are the typed, structured connections. `[[wikilinks]]` in the body
  are the same connections made visible for reading.

## Reading / answering questions

- For a quick map of everything, read `index.md`.
- To traverse relationships programmatically, load `graph.json` (`nodes` have `id/title/type/tags/
  path`; `edges` have `source/target/type`).
- To answer a question, find relevant notes (by tag/type/title or full-text search of `notes/`),
  then follow their relations to gather context before answering.

## Extending it (adding or editing notes)

1. Add a new file in `notes/` named `kebab-case.md`, following the frontmatter shape above.
2. Fill in `type`, `tags`, and `relations` (each `target` is another note's stem).
3. Mirror those relations as `[[wikilinks]]` in the body so they're visible while reading.
4. Regenerate the navigation and graph so they stay in sync:
   ```bash
   python build_graph.py .    # if you have the second-brain skill's script
   ```
   If you don't have that script, you may edit `index.md`/`graph.json` to match, but treat the notes
   as the source of truth — they're what makes this brain portable.

## Principles

- **Notes are the source of truth.** `index.md` and `graph.json` are derived views.
- **Keep it plain.** No app-specific syntax; anything beyond standard Markdown/YAML/JSON breaks
  portability.
- **Link generously but meaningfully** — a good relation type is worth more than a bare link.
