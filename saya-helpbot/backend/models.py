"""
models.py
---------
Pydantic models define the exact "shape" of data flowing in and out of
our API. FastAPI uses them to:
  1. Validate incoming JSON automatically (reject malformed requests
     with a clear 422 error, before our own code even runs).
  2. Serialize our Python objects back to JSON for the response.
  3. Auto-generate the interactive API docs at /docs.

Nothing in this file does any actual work — it's pure data definitions.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """What the frontend sends to POST /ask."""

    question: str = Field(
        ...,  # "..." means this field is required, not optional
        min_length=1,
        max_length=1000,
        description="The user's question, as free text.",
        examples=["How do I create a reconciliation?"],
    )


class AskResponse(BaseModel):
    """What POST /ask sends back to the frontend."""

    answer: str = Field(..., description="The best answer we found.")
    source: Literal["FAQ", "PDF", "NONE"] = Field(
        ...,
        description=(
            "Where the answer came from: an exact/near-exact FAQ match, "
            "a section of a PDF manual, or NONE if nothing confident was found."
        ),
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=100,
        description="Match confidence from 0-100. Higher is more certain.",
    )
    related_questions: List[str] = Field(
        default_factory=list,
        description="Other FAQ questions the user might have meant, or might want next.",
    )
    # Only populated when source == "PDF", so the user can go verify the source themselves.
    source_document: Optional[str] = Field(
        default=None, description="PDF filename the answer was pulled from, if source == PDF."
    )
    source_page: Optional[int] = Field(
        default=None, description="Page number within the PDF, if source == PDF."
    )


class SuggestedQuestionsResponse(BaseModel):
    """What GET /suggested-questions sends back."""

    questions: List[str] = Field(default_factory=list)


class ReloadResponse(BaseModel):
    """What POST /reload sends back, so you can confirm your new data loaded correctly."""

    status: Literal["ok", "error"]
    faq_count: int
    pdf_chunk_count: int
    pdf_files: List[str]
    message: Optional[str] = None
