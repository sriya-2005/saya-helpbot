"""
faq_loader.py
-------------
Responsible for ONE thing: reading faq.json from disk and turning it
into a clean, validated Python list. If the file is missing, empty,
or has malformed entries, we log a warning and skip/return gracefully
instead of crashing the whole server — a broken FAQ file should never
take down the API.

Expected shape of faq.json (see faq.example.json for a filled-in sample):
[
  {"question": "What is ReconX?", "answer": "ReconX is used for..."},
  {"question": "...", "answer": "..."}
]
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("saya_helpbot.faq_loader")

# faq.json is expected to live in the same folder as this file (backend/faq.json).
FAQ_PATH = Path(__file__).parent / "faq.json"


def load_faq(path: Path = FAQ_PATH) -> List[Dict[str, str]]:
    """
    Reads faq.json and returns a list of {"question": ..., "answer": ...} dicts.

    Design choice: we validate every entry individually. If one entry in a
    100-question file is malformed, we skip *that one entry* (with a logged
    warning) rather than throwing away the other 99 good ones.
    """
    if not path.exists():
        logger.warning("faq.json not found at %s — starting with an empty FAQ list.", path)
        return []

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error("Could not read faq.json: %s", exc)
        return []

    if not raw_text.strip():
        logger.warning("faq.json is empty — starting with an empty FAQ list.")
        return []

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error("faq.json contains invalid JSON: %s", exc)
        return []

    if not isinstance(data, list):
        logger.error("faq.json must contain a JSON array at the top level. Got %s.", type(data))
        return []

    valid_entries: List[Dict[str, str]] = []
    for i, entry in enumerate(data):
        cleaned = _validate_entry(entry, index=i)
        if cleaned is not None:
            valid_entries.append(cleaned)

    logger.info("Loaded %d valid FAQ entries from %s.", len(valid_entries), path.name)
    return valid_entries


def _validate_entry(entry: Any, index: int) -> Dict[str, str] | None:
    """Checks a single FAQ entry has non-empty 'question' and 'answer' strings."""
    if not isinstance(entry, dict):
        logger.warning("faq.json entry #%d is not an object — skipping.", index)
        return None

    question = entry.get("question")
    answer = entry.get("answer")

    if not isinstance(question, str) or not question.strip():
        logger.warning("faq.json entry #%d is missing a valid 'question' — skipping.", index)
        return None

    if not isinstance(answer, str) or not answer.strip():
        logger.warning("faq.json entry #%d is missing a valid 'answer' — skipping.", index)
        return None

    return {"question": question.strip(), "answer": answer.strip()}
