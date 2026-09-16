# Second Brain

A portable, **AI-tool-agnostic** personal knowledge base builder.

This repository holds the `second-brain` [Claude Code skill](.claude/skills/second-brain/). It turns
a folder of documents living in Google Drive into a set of linked Markdown notes — a "second brain"
you can open in any editor and reason over with any AI assistant (Claude, ChatGPT, Gemini, or a
local model). Nothing in the output is tied to one vendor: it's just Markdown, YAML, and JSON on
disk.

## Why this exists

Most note and knowledge-base tools lock your thinking into their format. If the app dies, or you
switch AI assistants, your knowledge goes with it. This skill takes the opposite bet — the most
durable knowledge base is plain text you fully own:

- **Markdown notes** with **YAML frontmatter** — each note is self-describing (title, type, tags,
  source, relations), readable a decade from now, in any editor.
- **`[[wikilinks]]`** — the de-facto standard for note-to-note links (Obsidian, Logseq, Foam…).
- **`index.md`** — a human-readable "Map of Content" to navigate the whole brain top to bottom.
- **`graph.json`** — the same relationships in structured form, so scripts and AI agents can load
  the knowledge graph without parsing Markdown.
- **`AGENTS.md`** — a short guide, dropped into every generated brain, telling *any* AI assistant
  how the vault is organized and how to extend it consistently. This is what makes it genuinely
  tool-agnostic.

Keeping both a human view (`index.md`, wikilinks) and a machine view (`graph.json`, frontmatter) is
deliberate — neither alone serves both a person and an AI well.

## What the skill does

1. **Pulls sources from Google Drive** — you point it at a Drive folder or set of files; it lists
   them for confirmation, then downloads PDFs and Word docs and exports Google-native Docs.
2. **Converts each document to a clean Markdown note** — with a starter YAML frontmatter block,
   using the best available converter for each file type.
3. **Interviews you about the documents** — what each one *is* (a report? a meeting note? a source?)
   and how they relate, since only you know the meaning behind the files.
4. **Wires the notes together** — typed relations in frontmatter plus `[[wikilinks]]` in the body,
   and any "hub" notes needed to tie a topic or project together.
5. **Generates the index and graph** — a human-readable `index.md` and a machine-readable
   `graph.json`, and flags any dangling links.
6. **Makes it portable** — drops an `AGENTS.md` guide into the brain so any AI tool can pick it up
   later, and (optionally) commits the result.

## Output layout

A generated second brain looks like this — clean, portable, all plain text:

```
<brain-dir>/
├── AGENTS.md        # how any AI tool should read/extend this brain
├── index.md         # human-readable Map of Content (generated)
├── graph.json       # machine-readable node/edge graph (generated)
└── notes/
    ├── some-note.md # YAML frontmatter + Markdown body + [[wikilinks]]
    └── ...
```

A note carries its own metadata and links:

```markdown
---
title: Q2 Pricing Strategy
type: reference
tags: [pricing, strategy, 2024]
created: 2024-06-14
source: "Google Drive: Q2 Pricing Strategy.pdf"
relations:
  - type: supersedes
    target: 2023-pricing-strategy
  - type: references
    target: competitor-analysis
---
## Summary
Why we're raising prices in Q2.

## Related
- Supersedes [[2023-pricing-strategy]]
- Draws on [[competitor-analysis]]
```

## Usage

From a Claude Code session with this repository (and the Google Drive connector enabled), just ask
in plain language — the skill triggers on requests like:

- "Build my second brain from this Google Drive folder."
- "Turn my Drive research into a knowledge base I can use with Claude and ChatGPT."
- "Convert these docs into an Obsidian-style vault with a knowledge graph."

The skill will ask you for the **source location** in Drive and the **output directory** before it
touches any files, then walk through the steps above. If Google Drive isn't reachable, you can point
it at a local folder of documents instead — the rest of the flow is identical.

### Using the output with any AI tool

Point your assistant at the generated folder and have it read `AGENTS.md` first. That file explains
the layout and conventions, so Claude, ChatGPT, Gemini, or a local model can all answer questions
over your notes and add new ones in the same format.

## Repository layout

```
.claude/skills/second-brain/
├── SKILL.md                 # skill definition + 6-step workflow
├── references/
│   ├── output-format.md     # note / frontmatter / wikilink spec
│   ├── relations.md         # relation-type vocabulary + interview prompts
│   └── conversion.md        # converter backends, install hints, OCR
├── scripts/
│   ├── convert_to_md.py     # document → Markdown converter (multi-backend)
│   └── build_graph.py       # generates index.md + graph.json, flags dangling links
└── assets/
    ├── note-template.md     # the note template
    └── AGENTS.md            # guide copied into every generated brain
```

## Requirements

- **Claude Code** with the **Google Drive** connector (optional — a local folder works too).
- **Python 3** for the two helper scripts.
- Conversion backends are installed on demand; the converter prints the exact `pip install` hint
  when one is missing. `pip install "markitdown[all]"` covers the large majority of file types.
  Scanned/image-only PDFs need OCR (`ocrmypdf`) — see
  [`conversion.md`](.claude/skills/second-brain/references/conversion.md).

## Design principles

- **Notes are the source of truth.** `index.md` and `graph.json` are generated views — regenerate
  them with `build_graph.py` rather than editing by hand.
- **Keep it plain.** No app-specific syntax; anything beyond standard Markdown/YAML/JSON breaks
  portability.
- **Link meaningfully.** A good typed relation is worth more than a bare link.
