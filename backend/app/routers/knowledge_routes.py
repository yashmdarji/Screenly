from fastapi import APIRouter, Form, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from backend.app.services.rag_engine import rag_engine

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base & RAG"])


class KnowledgeSearchQuery(BaseModel):
    query: str
    target_role: Optional[str] = None
    top_k: int = 3


class IngestDocPayload(BaseModel):
    text: str
    role: str
    book_title: str
    chapter_title: Optional[str] = "Custom Chapter"
    section_title: Optional[str] = "General"


@router.get("/status")
def get_knowledge_status():
    """Returns indexed knowledge base statistics, loaded textbooks, and chunk count."""
    return rag_engine.get_knowledge_summary()


@router.post("/search")
def search_knowledge_base(payload: KnowledgeSearchQuery):
    """
    Direct RAG search query against the vector store.
    Returns top-k grounded chunks with citations and cosine similarity scores.
    """
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    results = rag_engine.retrieve_grounded_context(
        query=payload.query,
        target_role=payload.target_role or "AI/ML Engineer",
        top_k=payload.top_k
    )
    return {
        "query": payload.query,
        "target_role": payload.target_role,
        "results_count": len(results),
        "chunks": results
    }


@router.post("/ingest")
def ingest_custom_knowledge(payload: IngestDocPayload):
    """Dynamically adds new knowledge content into the RAG vector store."""
    if len(payload.text.strip()) < 30:
        raise HTTPException(status_code=400, detail="Document text too short to ingest.")

    rag_engine.vector_store.add_document(
        text=payload.text,
        role=payload.role,
        book_title=payload.book_title,
        chapter_title=payload.chapter_title,
        section_title=payload.section_title
    )
    rag_engine.vector_store.build_index()

    return {
        "status": "success",
        "message": f"Successfully ingested document into '{payload.book_title}'",
        "total_chunks_now": len(rag_engine.vector_store.chunks)
    }
