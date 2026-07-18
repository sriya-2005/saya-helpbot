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

import fitz  # PyMuPDF

logger = logging.getLogger("saya_helpbot.pdf_loader")

# docs/ is expected to live in the same folder as this file (backend/docs/).
DOCS_DIR = Path(__file__).parent / "docs"

# Chunking parameters (words)
# Aim for chunks around 400-600 words; pick a target and overlap to stay inside that
CHUNK_TARGET = 500
CHUNK_OVERLAP = 100


def load_pdfs(docs_dir: Path = DOCS_DIR) -> List[Dict]:
    """Scans docs_dir for *.pdf files and returns a flat list of text chunks.

    Each chunk is a dict with keys: text, source (filename), page (1-based).
    """
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
        except Exception as exc:  # keep robust: don't let one bad PDF stop startup
            logger.exception("Skipping %s — error while parsing: %s", pdf_path.name, exc)

    logger.info("Total PDF chunks loaded across %d file(s): %d", len(pdf_files), len(all_chunks))
    return all_chunks


def _extract_chunks_from_pdf(pdf_path: Path) -> List[Dict]:
    """Opens one PDF with PyMuPDF, extracts page text, and returns overlapping word-chunks.

    Each chunk is tagged with the source filename and the page number it came from.
    """
    doc = fitz.open(str(pdf_path))
    chunks: List[Dict] = []

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        page_text = page.get_text("text") or ""
        normalized = _normalize_whitespace(page_text)
        if not normalized:
            continue

        page_chunks = _split_page_into_overlapping_chunks(normalized)
        for chunk_text in page_chunks:
            chunks.append({
                "text": chunk_text,
                "source": pdf_path.name,
                "page": page_number + 1,
            })

    doc.close()
    return chunks


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _split_page_into_overlapping_chunks(page_text: str) -> List[str]:
    """Split a full page string into overlapping chunks of words.

    We split on whitespace to get words, then build sliding windows of
    size CHUNK_TARGET with CHUNK_OVERLAP words of overlap between windows.
    If the page is shorter than CHUNK_TARGET, the whole page is one chunk.
    """
    words = page_text.split()
    n = len(words)
    if n == 0:
        return []
    if n <= CHUNK_TARGET:
        return [" ".join(words)]

    chunks: List[str] = []
    start = 0
    step = CHUNK_TARGET - CHUNK_OVERLAP
    while start < n:
        end = min(start + CHUNK_TARGET, n)
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end == n:
            break
        start += step

    return chunks
