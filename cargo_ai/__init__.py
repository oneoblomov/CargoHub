"""CargoHub AI toolkit for RAG, QA generation, and hybrid chat."""

from .documentation import (
    DocumentChunk,
    DocumentSection,
    load_markdown_documents,
    make_chunks,
)
from .qa_generation import generate_datasets, generate_questions
from .rag_pipeline import HybridResponder, RAGPipeline

__all__ = [
    "DocumentChunk",
    "DocumentSection",
    "load_markdown_documents",
    "make_chunks",
    "generate_questions",
    "generate_datasets",
    "RAGPipeline",
    "HybridResponder",
]
