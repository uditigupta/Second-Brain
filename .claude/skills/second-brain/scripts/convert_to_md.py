#!/usr/bin/env python3
"""Convert a document (PDF, DOCX, HTML, TXT, MD) to a Markdown note.

Writes a `.md` file with a starter YAML frontmatter block into the output directory. Tries the best
available backend for each file type and falls back gracefully; if nothing is installed it prints a
clear install hint (see references/conversion.md) and exits non-zero.

Usage:
    python convert_to_md.py <input-file> --out <output-dir> [--title "Title"] [--type reference]

The produced note is a starting point: the skill still cleans extraction noise and fills in
relations afterward.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-") or "note"


# --- backends: each returns extracted Markdown/text or raises ImportError/Exception ---

def _via_markitdown(path: Path) -> str:
    from markitdown import MarkItDown  # type: ignore

    return MarkItDown().convert(str(path)).text_content


def _pdf_via_pdfplumber(path: Path) -> str:
    import pdfplumber  # type: ignore

    parts = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n\n".join(parts)


def _pdf_via_pypdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        from PyPDF2 import PdfReader  # type: ignore

    reader = PdfReader(str(path))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


def _docx_via_pandoc(path: Path) -> str:
    import shutil
    import subprocess

    if not shutil.which("pandoc"):
        raise ImportError("pandoc not installed")
    return subprocess.run(
        ["pandoc", str(path), "-t", "gfm"], check=True, capture_output=True, text=True
    ).stdout


def _docx_via_python_docx(path: Path) -> str:
    import docx  # type: ignore

    return "\n\n".join(p.text for p in docx.Document(str(path)).paragraphs if p.text.strip())


def _html_via_pandoc(path: Path) -> str:
    return _docx_via_pandoc(path)  # pandoc auto-detects html input by extension


def _passthrough(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# ext -> ordered list of (backend_name, callable)
BACKENDS = {
    ".pdf": [("markitdown", _via_markitdown), ("pdfplumber", _pdf_via_pdfplumber), ("pypdf", _pdf_via_pypdf)],
    ".docx": [("markitdown", _via_markitdown), ("pandoc", _docx_via_pandoc), ("python-docx", _docx_via_python_docx)],
    ".doc": [("markitdown", _via_markitdown), ("pandoc", _docx_via_pandoc)],
    ".html": [("markitdown", _via_markitdown), ("pandoc", _html_via_pandoc)],
    ".htm": [("markitdown", _via_markitdown), ("pandoc", _html_via_pandoc)],
    ".pptx": [("markitdown", _via_markitdown)],
    ".xlsx": [("markitdown", _via_markitdown)],
    ".txt": [("passthrough", _passthrough)],
    ".md": [("passthrough", _passthrough)],
    ".markdown": [("passthrough", _passthrough)],
}

INSTALL_HINTS = {
    "markitdown": 'pip install "markitdown[all]"',
    "pdfplumber": "pip install pdfplumber",
    "pypdf": "pip install pypdf",
    "pandoc": "install pandoc (brew install pandoc / apt-get install pandoc)",
    "python-docx": "pip install python-docx",
}


def convert(path: Path) -> tuple[str, str]:
    """Return (markdown_text, backend_used). Raises RuntimeError if no backend works."""
    ext = path.suffix.lower()
    if ext not in BACKENDS:
        raise RuntimeError(f"Unsupported file type: {ext}. Supported: {', '.join(sorted(BACKENDS))}")

    errors = []
    for name, fn in BACKENDS[ext]:
        try:
            text = fn(path)
            if text and text.strip():
                return text, name
            errors.append(f"{name}: produced no text")
        except ImportError:
            errors.append(f"{name}: not installed ({INSTALL_HINTS.get(name, 'see references/conversion.md')})")
        except Exception as exc:  # noqa: BLE001 - backend-specific failures are expected
            errors.append(f"{name}: {exc}")

    hints = [INSTALL_HINTS[n] for n, _ in BACKENDS[ext] if n in INSTALL_HINTS]
    raise RuntimeError(
        "No conversion backend succeeded for "
        f"{path.name}.\n  Tried:\n    " + "\n    ".join(errors)
        + ("\n  Install one of:\n    " + "\n    ".join(dict.fromkeys(hints)) if hints else "")
    )


def build_note(title: str, note_type: str, source: str, body: str) -> str:
    today = _dt.date.today().isoformat()
    fm = (
        "---\n"
        f"title: {title}\n"
        f"type: {note_type}\n"
        "tags: []\n"
        f"created: {today}\n"
        f'source: "{source}"\n'
        "relations: []\n"
        "---\n\n"
    )
    return fm + "## Summary\n\n_TODO: one or two sentences on what this note is._\n\n## Notes\n\n" + body.strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert a document to a Markdown note.")
    ap.add_argument("input", type=Path, help="Path to the source document")
    ap.add_argument("--out", type=Path, required=True, help="Output directory for the .md note")
    ap.add_argument("--title", help="Note title (defaults to the file stem)")
    ap.add_argument("--type", default="reference", help="Note type (default: reference)")
    ap.add_argument("--source", help="Source label for frontmatter (default: original filename)")
    args = ap.parse_args()

    if not args.input.exists():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return 2

    try:
        text, backend = convert(args.input)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    title = args.title or args.input.stem.replace("_", " ").replace("-", " ").strip().title()
    source = args.source or args.input.name

    args.out.mkdir(parents=True, exist_ok=True)
    out_path = args.out / f"{slugify(title)}.md"
    out_path.write_text(build_note(title, args.type, source, text), encoding="utf-8")

    words = len(text.split())
    print(f"wrote {out_path}  (backend: {backend}, ~{words} words)")
    if args.input.suffix.lower() == ".pdf" and words < 30:
        print(
            "  warning: very little text extracted — this PDF may be scanned/image-only. "
            "See references/conversion.md for OCR options.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
