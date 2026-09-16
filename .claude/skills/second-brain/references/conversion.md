# Conversion backends

`scripts/convert_to_md.py` turns a source document into a Markdown note. It auto-detects the file
type and tries backends in order of quality, falling back gracefully. This file explains what it
uses and how to fix a "no backend available" error.

## What handles what

| Input | Preferred backend | Fallbacks |
|-------|-------------------|-----------|
| `.pdf` | `markitdown` | `pdfplumber` → `pypdf` |
| `.docx` / `.doc` | `markitdown` | `pandoc` → `python-docx` |
| `.html` / `.htm` | `markitdown` | `pandoc` |
| `.pptx`, `.xlsx` | `markitdown` | — |
| `.txt`, `.md`, `.markdown` | passthrough (copied/wrapped) | — |

`markitdown` (Microsoft's converter) is preferred because it handles the widest range with good
Markdown structure. The others exist so the script still works when it isn't installed.

## Installing backends

Install whichever the script reports as missing:

```bash
pip install "markitdown[all]"     # broad coverage: pdf, docx, pptx, xlsx, html, ...
pip install pdfplumber pypdf      # PDF fallbacks
pip install python-docx           # DOCX fallback
# pandoc is a system package:
#   macOS:  brew install pandoc
#   Debian: apt-get install -y pandoc
```

Installing `markitdown` alone covers the large majority of cases.

## Scanned / image-only PDFs

If a PDF is scanned (images of pages, no text layer), text extractors return little or nothing. The
script warns when extracted text is suspiciously short. Options:

1. OCR the PDF first, then convert the searchable output:
   ```bash
   pip install ocrmypdf        # also needs the tesseract system package
   ocrmypdf input.pdf ocr.pdf
   python convert_to_md.py ocr.pdf --out notes/
   ```
2. If OCR isn't available, note in the file's frontmatter that it needs OCR and move on — don't
   fabricate content that isn't extractable.

## After conversion

Automated extraction is never perfect. Always skim the output and clean up:

- repeated running headers/footers and page numbers,
- hyphenated line-break splits (`inter-\nnational` → `international`),
- broken tables (re-lay them as Markdown tables where it matters),
- figure/image placeholders.

The goal is a note that reads cleanly, not a byte-perfect transcript.
