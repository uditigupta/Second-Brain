#!/usr/bin/env python3
"""Generate index.md and graph.json for a second brain from its notes.

Scans `<brain-dir>/notes/*.md`, reads each note's YAML frontmatter and `[[wikilinks]]`, and writes:

  - <brain-dir>/graph.json : {"nodes": [...], "edges": [...]}  (machine-readable)
  - <brain-dir>/index.md   : a Map of Content grouped by note type  (human-readable)

Also prints any dangling links (a relation target or [[wikilink]] with no matching note) so they
can be fixed. Safe to re-run any time notes change — it overwrites both generated files.

Usage:
    python build_graph.py <brain-dir>

PyYAML is used when available for robust frontmatter parsing; a minimal built-in parser covers the
fields this skill writes (title, type, tags, created, source, relations) when it isn't installed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_yaml, body). Empty frontmatter if none present."""
    if text.startswith("---"):
        parts = text.split("\n", 1)
        if len(parts) == 2:
            rest = parts[1]
            end = rest.find("\n---")
            if end != -1:
                fm = rest[:end]
                body = rest[end + 4:].lstrip("\n")
                return fm, body
    return "", text


def parse_frontmatter(fm: str) -> dict:
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(fm) or {}
        if isinstance(data, dict):
            return data
    except ImportError:
        pass
    return _mini_yaml(fm)


def _mini_yaml(fm: str) -> dict:
    """Minimal parser for the flat + relations-list shape this skill writes."""
    data: dict = {}
    lines = fm.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if key == "relations" and val == "":
            rels, i = _read_relations(lines, i + 1)
            data["relations"] = rels
            continue
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            data[key] = [x.strip().strip("\"'") for x in inner.split(",") if x.strip()]
        else:
            data[key] = val.strip("\"'")
        i += 1
    return data


def _read_relations(lines: list[str], i: int) -> tuple[list[dict], int]:
    rels: list[dict] = []
    current: dict = {}
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped and not line.startswith((" ", "\t", "-")):
            break  # next top-level key
        item = re.match(r"^\s*-\s*(\w+):\s*(.*)$", line)
        cont = re.match(r"^\s+(\w+):\s*(.*)$", line)
        if item:
            if current:
                rels.append(current)
            current = {item.group(1): item.group(2).strip().strip("\"'")}
        elif cont:
            current[cont.group(1)] = cont.group(2).strip().strip("\"'")
        i += 1
    if current:
        rels.append(current)
    return rels, i


def main() -> int:
    ap = argparse.ArgumentParser(description="Build index.md and graph.json for a second brain.")
    ap.add_argument("brain_dir", type=Path, help="Root of the second brain (contains notes/)")
    args = ap.parse_args()

    notes_dir = args.brain_dir / "notes"
    if not notes_dir.is_dir():
        print(f"error: {notes_dir} not found (expected a notes/ subfolder)", file=sys.stderr)
        return 2

    nodes: list[dict] = []
    edges: list[dict] = []
    dangling: list[str] = []
    stems = {p.stem for p in notes_dir.glob("*.md")}

    for path in sorted(notes_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        fm, body = split_frontmatter(text)
        meta = parse_frontmatter(fm)
        stem = path.stem

        nodes.append(
            {
                "id": stem,
                "title": meta.get("title", stem),
                "type": meta.get("type", "reference"),
                "tags": meta.get("tags", []) or [],
                "path": f"notes/{path.name}",
            }
        )

        # edges from typed frontmatter relations
        for rel in meta.get("relations", []) or []:
            if not isinstance(rel, dict):
                continue
            target = rel.get("target")
            if not target:
                continue
            edges.append({"source": stem, "target": target, "type": rel.get("type", "related-to")})
            if target not in stems:
                dangling.append(f"{stem}: relation -> [[{target}]] (no such note)")

        # edges from body wikilinks (deduped against explicit relations)
        explicit = {(e["source"], e["target"]) for e in edges}
        for target in dict.fromkeys(WIKILINK_RE.findall(body)):
            target = target.strip()
            if (stem, target) not in explicit:
                edges.append({"source": stem, "target": target, "type": "links-to"})
            if target not in stems:
                dangling.append(f"{stem}: [[{target}]] (no such note)")

    graph = {"nodes": nodes, "edges": edges}
    (args.brain_dir / "graph.json").write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    _write_index(args.brain_dir, nodes, edges)

    print(f"wrote graph.json ({len(nodes)} nodes, {len(edges)} edges) and index.md")
    if dangling:
        print(f"\n{len(dangling)} dangling link(s) — create the notes or fix the names:", file=sys.stderr)
        for d in dict.fromkeys(dangling):
            print(f"  - {d}", file=sys.stderr)
    return 0


def _write_index(brain_dir: Path, nodes: list[dict], edges: list[dict]) -> None:
    by_type: dict[str, list[dict]] = {}
    for n in nodes:
        by_type.setdefault(n["type"], []).append(n)

    out_edges: dict[str, list[str]] = {}
    for e in edges:
        out_edges.setdefault(e["source"], []).append(f"{e['type']} → [[{e['target']}]]")

    lines = [
        "# Index",
        "",
        "_Generated by build_graph.py — do not edit by hand; edit the notes and regenerate._",
        "",
        f"{len(nodes)} notes, {len(edges)} links.",
        "",
    ]
    for note_type in sorted(by_type):
        lines.append(f"## {note_type.replace('-', ' ').title()}")
        lines.append("")
        for n in sorted(by_type[note_type], key=lambda x: x["title"].lower()):
            tag_str = f"  ·  _{', '.join(n['tags'])}_" if n["tags"] else ""
            lines.append(f"- [[{n['id']}|{n['title']}]]{tag_str}")
            for rel in out_edges.get(n["id"], []):
                lines.append(f"  - {rel}")
        lines.append("")

    (brain_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
