"""
main.py
-------
This is the file you actually run. It:
  1. Configures logging so we can see what's happening in the terminal.
  2. Creates the FastAPI app and enables CORS so your React frontend
     (running on a different port) is allowed to call this API.
  3. Loads faq.json and all docs/*.pdf into memory once, at startup.
  4. Defines the three endpoints your frontend needs: /ask,
     /suggested-questions, and /reload.

Run it with:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import faq_loader
import pdf_loader
import search
from models import (
    AskRequest,
    AskResponse,
    ReloadResponse,
    SuggestedQuestionsResponse,
)

# --- Logging setup -----------------------------------------------------------
# LOG_LEVEL can be overridden with an environment variable, e.g.
#   LOG_LEVEL=DEBUG uvicorn main:app --reload
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("saya_helpbot.main")

# --- In-memory data store ----------------------------------------------------
# A plain dict is enough here — this app has one knowledge base shared by
# everyone, not per-user data. `/reload` mutates this dict in place, so every
# request after a reload immediately sees the fresh data.
data_store: Dict[str, List] = {
    "faq": [],
    "pdf_chunks": [],
}


def load_all_data() -> None:
    """Loads faq.json and every PDF in docs/ into the in-memory data_store."""
    logger.info("Loading knowledge base...")
    data_store["faq"] = faq_loader.load_faq()
    data_store["pdf_chunks"] = pdf_loader.load_pdfs()
    logger.info(
        "Knowledge base ready: %d FAQ entries, %d PDF chunks.",
        len(data_store["faq"]),
        len(data_store["pdf_chunks"]),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts up.
    load_all_data()
    yield
    # (nothing needed on shutdown for this app)


app = FastAPI(
    title="SAYA HelpBot API",
    description="Answers questions from an FAQ file and PDF manuals using fuzzy matching. Never generates text.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS ---------------------------------------------------------------------
# Without this, a browser will block your React app (on e.g. localhost:5173)
# from calling this API (on localhost:8000) — browsers block cross-origin
# requests by default unless the server explicitly allows them.
#
# ALLOWED_ORIGINS can be set as an env var, comma-separated, e.g.:
#   ALLOWED_ORIGINS=http://localhost:5173,https://your-production-domain.com
# Defaults to allowing the two most common local Vite/CRA dev ports.
_default_origins = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
logger.info("CORS enabled for origins: %s", allowed_origins)


# --- Endpoints -----------------------------------------------------------------

@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest) -> AskResponse:
    """
    Main chatbot endpoint. Receives a question, searches faq.json first,
    falls back to the PDF manuals, and returns the best answer found —
    never a generated/invented one.
    """
    try:
        result = search.search(
            question=request.question,
            faq_list=data_store["faq"],
            pdf_chunks=data_store["pdf_chunks"],
        )
        return AskResponse(**result)
    except Exception as exc:  # noqa: BLE001 - guarantee the API never 500s silently
        logger.exception("Unexpected error while answering question: %r", request.question)
        raise HTTPException(status_code=500, detail="Something went wrong answering that question.") from exc


@app.get("/suggested-questions", response_model=SuggestedQuestionsResponse)
def get_suggested_questions() -> SuggestedQuestionsResponse:
    """Returns every FAQ question, for the frontend to show as chips/suggestions."""
    try:
        questions = [item["question"] for item in data_store["faq"]]
        return SuggestedQuestionsResponse(questions=questions)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error while listing suggested questions.")
        raise HTTPException(status_code=500, detail="Could not load suggested questions.") from exc


@app.post("/reload", response_model=ReloadResponse)
def reload_knowledge_base() -> ReloadResponse:
    """
    Re-reads faq.json and every PDF in docs/ from disk, without restarting
    the server. Call this after you replace faq.json or add/remove PDFs.
    """
    try:
        load_all_data()
        pdf_files = sorted({chunk["source"] for chunk in data_store["pdf_chunks"]})
        return ReloadResponse(
            status="ok",
            faq_count=len(data_store["faq"]),
            pdf_chunk_count=len(data_store["pdf_chunks"]),
            pdf_files=pdf_files,
            message="Knowledge base reloaded successfully.",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error while reloading the knowledge base.")
        return ReloadResponse(
            status="error",
            faq_count=len(data_store["faq"]),
            pdf_chunk_count=len(data_store["pdf_chunks"]),
            pdf_files=[],
            message=f"Reload failed: {exc}",
        )


@app.get("/health")
def health_check() -> dict:
    """Simple liveness check — useful for uptime monitors or deploy pipelines."""
    return {
        "status": "ok",
        "faq_count": len(data_store["faq"]),
        "pdf_chunk_count": len(data_store["pdf_chunks"]),
    }
