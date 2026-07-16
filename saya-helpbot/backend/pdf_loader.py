"""
pdf_loader.py
-------------
Responsible for ONE thing: scanning the docs/ folder, opening every PDF
it finds, and turning them into a flat list of small text "chunks" that
search.py can later score against a user's question.

Why chunk at all? A whole PDF page (or worse, a whole PDF) is too big and
too unfocused to compare directly against a short question — the fuzzy
match score would be diluted by hundreds of irrelevant words. Splitting
into paragraph-sized chunks means each one is a focused, comparable unit,
similar to a single FAQ answer.

Each chunk looks like:
{
    "text": "To configure matching rules, open Settings > Matching...",
    "source": "reconx_manual.pdf",
    "page": 12,
}

If docs/ is empty or a PDF fails to open (corrupted, password-protected,
scanned image with no text layer, etc.), we log a warning and skip that
file — one bad PDF should never take down the whole server.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

from pypdf import PdfReader
from pypdf.errors import PdfReadError

logger = logging.getLogger("saya_helpbot.pdf_loader")

# docs/ is expected to live in the same folder as this file (backend/docs/).
DOCS_DIR = Path(__file__).parent / "docs"

# Tuning knobs for chunking. Kept as module-level constants so they're easy
# to find and adjust without hunting through function bodies.
MIN_CHUNK_CHARS = 120   # paragraphs shorter than this get merged with the next one
MAX_CHUNK_CHARS = 900   # paragraphs longer than this get split further


def load_pdfs(docs_dir: Path = DOCS_DIR) -> List[Dict]:
    """Scans docs_dir for *.pdf files and returns a flat list of text chunks."""
    docs_dir.mkdir(parents=True, exist_ok=True)  # create docs/ if it doesn't exist yet

    pdf_files = sorted(docs_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in %s. PDF fallback search will return nothing.", docs_dir)
        return []

    all_chunks: List[Dict] = []
    for pdf_path in pdf_files:
        try:
            chunks = _extract_chunks_from_pdf(pdf_path)
            all_chunks.extend(chunks)
            logger.info("Loaded %d chunks from %s.", len(chunks), pdf_path.name)
        except PdfReadError as exc:
            logger.error("Skipping %s — could not be read (corrupted or encrypted): %s", pdf_path.name, exc)
        except Exception as exc:  # noqa: BLE001 - deliberately broad: one bad PDF must not crash startup
            logger.error("Skipping %s — unexpected error while parsing: %s", pdf_path.name, exc)

    logger.info("Total PDF chunks loaded across %d file(s): %d", len(pdf_files), len(all_chunks))
    return all_chunks


def _extract_chunks_from_pdf(pdf_path: Path) -> List[Dict]:
    """Opens one PDF and returns its text chunks, tagged with filename + page number."""
    reader = PdfReader(str(pdf_path))
    chunks: List[Dict] = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if not page_text.strip():
            continue  # scanned image pages with no text layer produce empty strings

        for paragraph in _split_into_paragraphs(page_text):
            chunks.append(
                {
                    "text": paragraph,
                    "source": pdf_path.name,
                    "page": page_number,
                }
            )

    return chunks


def _split_into_paragraphs(page_text: str) -> List[str]:
    """
    Splits one page's raw text into clean, reasonably-sized paragraphs.

    Real-world PDF text extraction is messy — paragraph breaks don't always
    line up with blank lines. This does a best-effort job:
      1. Split on blank lines first (natural paragraph breaks).
      2. Merge any pieces that are too short to be useful alone.
      3. Split any piece that's too long into smaller windows.
    """
    raw_pieces = [p.strip() for p in page_text.split("\n\n") if p.strip()]
    if not raw_pieces:
        # Some PDFs use single newlines instead of blank lines between paragraphs
        raw_pieces = [p.strip() for p in page_text.split("\n") if p.strip()]

    merged: List[str] = []
    buffer = ""
    for piece in raw_pieces:
        buffer = f"{buffer} {piece}".strip() if buffer else piece
        if len(buffer) >= MIN_CHUNK_CHARS:
            merged.append(buffer)
            buffer = ""
    if buffer:  # leftover text shorter than MIN_CHUNK_CHARS still needs to be kept
        if merged:
            merged[-1] = f"{merged[-1]} {buffer}".strip()
        else:
            merged.append(buffer)

    final_chunks: List[str] = []
    for piece in merged:
        final_chunks.extend(_hard_split(piece, MAX_CHUNK_CHARS))

    return final_chunks


def _hard_split(text: str, max_len: int) -> List[str]:
    """Splits an overly long paragraph into word-boundary-respecting windows."""
    if len(text) <= max_len:
        return [text]

    words = text.split()
    windows: List[str] = []
    current: List[str] = []
    current_len = 0

    for word in words:
        if current_len + len(word) + 1 > max_len and current:
            windows.append(" ".join(current))
            current = []
            current_len = 0
        current.append(word)
        current_len += len(word) + 1

    if current:
        windows.append(" ".join(current))

    return windows
