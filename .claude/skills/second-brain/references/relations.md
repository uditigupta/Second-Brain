# Relations and note types

The value of a second brain is in the connections. This file gives a small, consistent vocabulary so
the graph stays coherent, plus prompts for the user interview in step 3.

## Note types (`type` frontmatter)

Use the smallest set that fits; consistency matters more than granularity.

| Type | For |
|------|-----|
| `reference` | A document you'll cite/return to (report, spec, article, PDF). Default for most converted files. |
| `source` | A raw external source (paper, book, transcript) you extract from. |
| `meeting-note` | Notes from a meeting/call. |
| `project` | An initiative that spans multiple notes. |
| `person` | A person (author, contact, stakeholder). |
| `idea` | An original thought, claim, or insight of the user's. |
| `hub` | A note that exists only to tie others together (a topic/map note, no single source document). |

## Relation types (`relations[].type`)

Relations are **directed**: they read "this note _[type]_ target".

| Relation | Meaning | Typical inverse |
|----------|---------|-----------------|
| `part-of` | This note belongs to a larger project/topic. | `contains` |
| `contains` | This note groups/owns the target (used on hubs). | `part-of` |
| `references` | This note cites or draws on the target. | `referenced-by` |
| `supersedes` | This note replaces an older one. | `superseded-by` |
| `related-to` | General association; use when nothing more specific fits. | `related-to` |
| `authored-by` | Links a document to a `person`. | `authored` |
| `depends-on` | This note/project depends on the target. | `blocks` |

You don't have to record both directions — `build_graph.py` stores edges directionally and can be
read either way. Prefer the direction that's most natural to state.

## Interview prompts (step 3)

Ask efficiently; batch questions. Good openers:

- "For each of these documents, tell me in a few words what it is and how you'd label it (a report?
  a meeting note? a source you cite?)."
- "Which of these are about the same project or topic? Should I create a hub note for that topic to
  tie them together?"
- "Does any document replace or update another (a newer version)?"
- "Are any of these authored by specific people you want tracked as their own notes?"
- "Is there context in your head that isn't in any file — a decision, an insight — that should
  become its own `idea` note?"

If the user is vague or busy, propose a structure inferred from the content (types, obvious topic
clusters, likely hubs) and ask them to correct it rather than starting from a blank slate. It's
faster to react than to author.
