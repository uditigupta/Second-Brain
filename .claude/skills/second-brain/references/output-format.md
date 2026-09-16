# Output format spec

The second brain is plain files on disk. This document is the contract every note follows so that
humans, note apps, and AI assistants can all read it.

## Directory layout

```
<brain-dir>/
├── AGENTS.md        # guide for AI tools (copied from assets/)
├── index.md         # generated Map of Content
├── graph.json       # generated node/edge graph
└── notes/
    └── *.md         # one file per note
```

- One note per file. File names are `kebab-case.md`, human-meaningful, stable (other notes link to
  them by name). Prefer a date prefix for time-bound notes: `2024-06-q2-review.md`.
- `index.md` and `graph.json` are **generated** by `build_graph.py`. Do not edit them by hand — edit
  the notes and regenerate.

## Note structure

Each note is YAML frontmatter followed by a Markdown body:

```markdown
---
title: Q2 Pricing Strategy
type: reference
tags: [pricing, strategy, 2024]
created: 2024-06-14
source: "Google Drive: Q2 Pricing Strategy.pdf"
relations:
  - type: part-of
    target: pricing-project
  - type: supersedes
    target: 2023-pricing-strategy
  - type: references
    target: competitor-analysis
---

## Summary
One or two sentences on what this note is and why it matters.

## Notes
The converted / cleaned document content, in Markdown.

## Related
- Part of [[pricing-project]]
- Supersedes [[2023-pricing-strategy]]
- Draws on [[competitor-analysis]]
```

### Frontmatter fields

| Field | Required | Meaning |
|-------|----------|---------|
| `title` | yes | Human-readable title. |
| `type` | yes | One of the note types (see `relations.md`), e.g. `reference`, `project`, `person`, `meeting-note`, `idea`, `source`, `hub`. |
| `tags` | recommended | Flat list of topic tags for grouping/search. |
| `created` | recommended | ISO date (`YYYY-MM-DD`). |
| `source` | when applicable | Where the note came from (original filename / Drive location). Omit for hub notes. |
| `relations` | when applicable | List of `{type, target}`. `target` is the **file stem** of another note (the filename without `.md`), matching how you'd write `[[target]]`. |

Keep frontmatter valid YAML: quote values containing colons, use `[a, b]` or block lists for arrays.

## Links

- Body links use `[[note-stem]]` (optionally `[[note-stem|display text]]`).
- Every relation in frontmatter should also appear as a wikilink in the body (usually under
  `## Related`), so the connection is visible while reading, not just in metadata.
- `target` values in `relations` and the stems inside `[[...]]` must match a real file in `notes/`.
  `build_graph.py` reports any that don't as dangling links.

## Why both frontmatter relations and body wikilinks?

They serve different readers. Frontmatter `relations` are typed and structured — ideal for
`graph.json` and for programmatic/AI traversal. Body `[[wikilinks]]` are what a person (and note
apps) actually click while reading. Keeping them in sync costs little and makes the brain legible to
both audiences.
