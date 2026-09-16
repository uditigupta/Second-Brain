---
name: second-brain
description: >-
  Build a portable, AI-tool-agnostic "second brain" (personal knowledge base) from documents
  stored in Google Drive. Use this skill whenever the user wants to turn a folder of PDFs, Word
  docs, or Google Docs into a linked set of Markdown notes — for example "build my second brain
  from this Drive folder", "turn my Google Drive research into a knowledge base", "convert these
  docs into a Zettelkasten / Obsidian vault", "make a knowledge graph from my documents", or
  "I want a notes system I can use with Claude, ChatGPT, and Gemini". It pulls source files from a
  Google Drive location, converts each PDF/DOCX/Google Doc to a clean Markdown note with YAML
  frontmatter, interviews the user about what the documents are and how they relate, wires the
  notes together with [[wikilinks]] and typed relations, and generates a human-readable index.md
  plus a machine-readable graph.json so the result works in any editor and with any AI assistant.
---

# Second Brain Builder

Turn a pile of documents in Google Drive into a **second brain**: a folder of plain-Markdown notes
that are linked to each other, indexed, and readable by a human, by Obsidian/Logseq-style tools,
and by any AI assistant (Claude, ChatGPT, Gemini, local models). Nothing about the output is
locked to one vendor — it is just Markdown, YAML, and JSON on disk.

## Why it's built this way

A knowledge base is only useful if you can still open it in ten years and if any tool can reason
over it. So the output deliberately uses the lowest-common-denominator formats:

- **Markdown notes** with **YAML frontmatter** — every note carries its own metadata (title, type,
  tags, source, relations), so a note is self-describing even in isolation.
- **`[[wikilinks]]`** in note bodies — the de-facto standard for note-to-note links (Obsidian,
  Logseq, Foam, etc.). Humans and tools both understand them.
- **`index.md`** — a "Map of Content" a person can read top-to-bottom to navigate the whole brain.
- **`graph.json`** — the same relationships in a structured form, so scripts and AI agents can load
  the graph without parsing Markdown.
- **`AGENTS.md`** — a short guide, dropped into the brain, that tells *any* AI assistant how the
  vault is organized and how to extend it. This is what makes it genuinely tool-agnostic.

Keeping both a human view (`index.md`, wikilinks) and a machine view (`graph.json`, frontmatter)
is intentional: neither alone serves both audiences well.

## The workflow

Follow these steps in order. Confirm the two locations with the user before touching any files.

### 1. Gather the inputs

Ask the user for (or confirm, if already given):

1. **Source location in Google Drive** — a folder name/link, or specific files. If they give a
   folder, list its contents so they can confirm the scope before you download anything.
2. **Output directory** — where the second brain should be written on disk (this skill does not
   assume a fixed path; always ask).

Find the files with the Google Drive tools (search first, then confirm):

- `mcp__Google_Drive__search_files` — find a folder or files by name.
- `mcp__Google_Drive__get_file_metadata` — resolve a folder's children / confirm MIME types.
- `mcp__Google_Drive__download_file_content` — download binary files (PDF, `.docx`).
- `mcp__Google_Drive__read_file_content` — read/export Google-native Docs (export a Google Doc to
  `.docx` or plain text so it can be converted like any other file).

Save downloaded originals into a `_sources/` subfolder of a scratch area (not the final brain), so
the brain stays clean Markdown. Handle Google-native Docs by exporting them; handle already-Markdown
or `.txt` files by copying them straight through.

If you cannot reach Google Drive (connector not authorized, folder not shared), say so plainly and
offer the alternative: the user drops the files somewhere local and points you at that path. The
rest of the workflow is identical from step 2 onward.

### 2. Convert each source to a Markdown note

Use the bundled converter — do not hand-transcribe documents:

```bash
python .claude/skills/second-brain/scripts/convert_to_md.py <input-file> --out <output-dir> [--title "..."]
```

It handles PDF, DOCX/DOC, HTML, TXT, and Markdown, tries the best available backend, and writes a
`.md` file with a starter YAML frontmatter block. Run it once per source file. If it reports a
missing dependency, install what it suggests and re-run — see `references/conversion.md` for the
backends, install commands, and how to handle scanned/image-only PDFs.

After conversion, skim each note and clean up obvious extraction noise (page numbers, repeated
headers/footers, broken tables) so the note reads well. Give each note a clear, human file name in
`kebab-case.md` (e.g. `2023-pricing-strategy.md`), not the raw upload name.

### 3. Interview the user about the documents and relations

This is the step that turns a pile of files into a *brain*. The converter cannot know what these
documents mean to the user or how they connect — only the user can. Ask focused questions, ideally
grouped so the user can answer efficiently:

- **What is each document?** Its type (e.g. `reference`, `meeting-note`, `project`, `person`,
  `idea`, `source`) and a one-line summary.
- **How do they relate?** Which notes are about the same project/topic, which one supersedes
  another, which is a source for a claim in another, which person authored which. Capture the
  *kind* of relation, not just "these two are linked".
- **What's missing?** Sometimes the right move is to create a new **hub note** (e.g. a project or
  topic note) that doesn't correspond to any single document but ties several together. Propose these.

Don't over-ask. If the user is vague, propose a reasonable structure from the content and let them
correct it. Read `references/relations.md` for the vocabulary of relation types and how to record
them.

### 4. Wire the notes together

For every note, fill in its frontmatter and add links, following `references/output-format.md`:

- Complete the frontmatter: `title`, `type`, `tags`, `created`, `source`, and a `relations` list of
  `{type, target}` entries capturing what you learned in step 3.
- Add a short `## Summary` at the top of the body if one isn't already clear.
- Add `[[wikilinks]]` in the body (and/or a `## Related` section) so the connections are visible
  while reading, not just in metadata.
- Create any hub notes the user agreed to.

### 5. Generate the index and the graph

Run the bundled builder to produce the navigation and machine views from the notes' frontmatter and
wikilinks — regenerate these any time notes change rather than editing them by hand:

```bash
python .claude/skills/second-brain/scripts/build_graph.py <brain-dir>
```

This writes `index.md` (grouped Map of Content) and `graph.json` (nodes + typed edges) into the
brain directory, and reports any dangling links (a `[[link]]` with no matching note) so you can fix
typos or create the missing note.

### 6. Make it tool-agnostic and hand it over

Copy the agent guide into the brain so any assistant can pick it up later:

```bash
cp .claude/skills/second-brain/assets/AGENTS.md <brain-dir>/AGENTS.md
```

Then give the user a short summary: how many notes, the top-level structure, where `index.md` is,
and how to use the brain with any AI tool (point it at the folder and at `AGENTS.md`). If the output
is inside a git repo, offer to commit it.

## Output layout

```
<brain-dir>/
├── AGENTS.md            # how any AI tool should read/extend this brain
├── index.md             # human-readable Map of Content (generated)
├── graph.json           # machine-readable node/edge graph (generated)
└── notes/
    ├── some-note.md     # a note: YAML frontmatter + Markdown body + [[wikilinks]]
    └── ...
```

Keep source originals out of the brain itself (in a separate `_sources/` scratch folder); the brain
should be clean, portable Markdown.

## Reference files

- `references/output-format.md` — the exact note/frontmatter/wikilink spec and file layout.
- `references/relations.md` — the relation-type vocabulary and interview prompts.
- `references/conversion.md` — conversion backends, install hints, and OCR for scanned PDFs.
- `scripts/convert_to_md.py` — document → Markdown converter.
- `scripts/build_graph.py` — generates `index.md` and `graph.json`; reports dangling links.
- `assets/note-template.md` — the frontmatter/body template for a note.
- `assets/AGENTS.md` — the guide copied into every generated brain.
