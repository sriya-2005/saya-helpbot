"""
search.py
---------
This is the "brain" of the chatbot. It never generates text — it only
ever picks the best-matching existing answer (from faq.json) or the
best-matching existing PDF section. This is what "never hallucinate"
means in practice: every possible response is a piece of text that was
already sitting in your data files. If nothing matches confidently
enough, we say so plainly instead of guessing.

Workflow (matches the spec exactly):
  1. Fuzzy-match the question against every FAQ question.
  2. If the best FAQ match scores >= FAQ_CONFIDENCE_THRESHOLD, return it.
  3. Otherwise, fuzzy-match the question against every PDF text chunk.
  4. Return the best-scoring chunk as the answer, citing its source file + page.
  5. If NEITHER source produces a match above the minimum floor, return
     source="NONE" with an honest "couldn't find that" message.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, TypedDict

from rapidfuzz import fuzz, process
import re

logger = logging.getLogger("saya_helpbot.search")

# --- Tuning knobs -----------------------------------------------------------
# A FAQ match at or above this score is considered confident enough to answer
# directly. 0-100 scale, where 100 means the question matched a FAQ exactly.
FAQ_CONFIDENCE_THRESHOLD = 88.0

# A PDF chunk match below this score is considered too weak to be useful —
# below this, we'd rather say "I don't know" than show a barely-related paragraph.
PDF_CONFIDENCE_FLOOR = 35.0

# How many alternate FAQ questions to suggest alongside an answer.
RELATED_QUESTIONS_COUNT = 3


class SearchResult(TypedDict):
    answer: str
    source: str  # "FAQ" | "PDF" | "NONE"
    confidence: float
    related_questions: List[str]
    source_document: Optional[str]
    source_page: Optional[int]


def search(
    question: str,
    faq_list: List[Dict[str, str]],
    pdf_chunks: List[Dict],
) -> SearchResult:
    """The single entry point main.py calls for every /ask request."""
    question = question.strip()

    faq_match = _search_faq(question, faq_list)
    pdf_match = _search_pdf(question, pdf_chunks)

    # Debug logging for both scores on every request
    faq_score = faq_match["confidence"] if faq_match else 0.0
    pdf_score = pdf_match["confidence"] if pdf_match else 0.0
    logger.debug("Scores for question=%r: FAQ=%.1f PDF=%.1f", question, faq_score, pdf_score)

    if faq_match and faq_score >= FAQ_CONFIDENCE_THRESHOLD:
        logger.info(
            "FAQ match found (confidence=%.1f): %r", faq_score, question
        )
        return {
            "answer": faq_match["answer"],
            "source": "FAQ",
            "confidence": round(faq_score, 1),
            "related_questions": _related_faq_questions(
                faq_list, exclude_question=faq_match["matched_question"]
            ),
            "source_document": None,
            "source_page": None,
        }

    if pdf_match and pdf_score >= PDF_CONFIDENCE_FLOOR:
        logger.info(
            "PDF match found (confidence=%.1f) in %s p.%s: %r",
            pdf_score,
            pdf_match["source"],
            pdf_match["page"],
            question,
        )
        return {
            "answer": pdf_match["text"],
            "source": "PDF",
            "confidence": round(pdf_score, 1),
            "related_questions": _related_faq_questions(faq_list, exclude_question=None),
            "source_document": pdf_match["source"],
            "source_page": pdf_match["page"],
        }

    # Neither source cleared the bar — be honest instead of guessing.
    logger.info("No confident match found for question: %r", question)
    best_faq_score = faq_match["confidence"] if faq_match else 0.0
    best_pdf_score = pdf_match["confidence"] if pdf_match else 0.0
    return {
        "answer": (
            "I couldn't find a confident answer to that in the FAQ or the manuals. "
            "Try rephrasing, or take a look at one of the related questions below."
        ),
        "source": "NONE",
        "confidence": round(max(best_faq_score, best_pdf_score), 1),
        "related_questions": _related_faq_questions(faq_list, exclude_question=None),
        "source_document": None,
        "source_page": None,
    }


# --- FAQ matching ------------------------------------------------------------

def _search_faq(question: str, faq_list: List[Dict[str, str]]) -> Optional[Dict]:
    """Finds the single best-matching FAQ question using rapidfuzz."""
    if not faq_list or not question:
        return None

    choices = [item["question"] for item in faq_list]

    # process.extractOne compares `question` against every string in `choices`
    # and returns the best one: (matched_string, score, index_in_choices).
    # Use token_sort_ratio which is stricter about ordering/word differences.
    result = process.extractOne(question, choices, scorer=fuzz.token_sort_ratio)
    if result is None:
        return None

    matched_question, score, idx = result
    return {
        "matched_question": matched_question,
        "answer": faq_list[idx]["answer"],
        "confidence": float(score),
    }


def _related_faq_questions(
    faq_list: List[Dict[str, str]], exclude_question: Optional[str], limit: int = RELATED_QUESTIONS_COUNT
) -> List[str]:
    """Returns a few FAQ questions to show as follow-up suggestions."""
    questions = [q["question"] for q in faq_list if q["question"] != exclude_question]
    return questions[:limit]


# --- PDF matching ------------------------------------------------------------

def _search_pdf(question: str, pdf_chunks: List[Dict]) -> Optional[Dict]:
    """Finds the single best-matching PDF chunk using rapidfuzz."""
    # Deterministic keyword-based matching (no AI, embeddings, or ML).
    if not pdf_chunks or not question:
        return None

    # Normalize and extract words from the question.
    query_words = re.findall(r"\w+", question.lower())
    if not query_words:
        return None

    best_chunk: Optional[Dict] = None
    best_score = -1.0

    for chunk in pdf_chunks:
        text = chunk.get("text", "").lower()
        # Exact phrase match is highest-confidence
        if question.lower().strip() in text:
            score = 100.0
        else:
            # Count how many unique query words appear in the chunk
            matched = 0
            text_words = set(re.findall(r"\w+", text))
            for w in set(query_words):
                if w in text_words:
                    matched += 1
            # Score is percentage of query words found (0-100)
            score = (matched / len(set(query_words))) * 100.0 if query_words else 0.0

        if score > best_score:
            best_score = score
            best_chunk = chunk

    if best_chunk is None:
        return None

    return {
        "text": best_chunk["text"],
        "source": best_chunk["source"],
        "page": best_chunk["page"],
        "confidence": best_score,
    }
