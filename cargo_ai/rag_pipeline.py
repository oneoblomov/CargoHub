"""Lightweight RAG toolkit built around TF-IDF embeddings for offline tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Sequence
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .documentation import DocumentChunk


@dataclass(slots=True)
class RetrievalResult:
    chunk: DocumentChunk
    score: float


class TfidfEmbedder:
    """Simple TF-IDF embedder with cosine similarity."""

    def __init__(self, max_features: int = 4096) -> None:
        self.vectorizer = TfidfVectorizer(max_features=max_features)
        self.document_matrix = None

    def fit(self, texts: Sequence[str]) -> None:
        self.document_matrix = self.vectorizer.fit_transform(texts)

    def encode(self, texts: Sequence[str]):
        if self.document_matrix is None:
            raise RuntimeError("Embedder must be fitted before encoding.")
        return self.vectorizer.transform(texts)

    def transform(self, text: str):
        if self.document_matrix is None:
            raise RuntimeError("Embedder must be fitted before encoding.")
        return self.vectorizer.transform([text])


class RAGPipeline:
    """Retrieval augmented answering pipeline."""

    def __init__(self, *, embedder: TfidfEmbedder | None = None) -> None:
        self.embedder = embedder or TfidfEmbedder()
        self.chunks: List[DocumentChunk] = []
        self.matrix = None

    def build(self, chunks: Iterable[DocumentChunk]) -> None:
        self.chunks = list(chunks)
        texts = [chunk.text for chunk in self.chunks]
        if not texts:
            raise ValueError("Chunk list boş olamaz")
        self.embedder.fit(texts)
        self.matrix = self.embedder.encode(texts)

    def save(self, output_dir: Path | str) -> None:
        import pickle

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        payload = {
            "chunks": self.chunks,
            "vectorizer": self.embedder.vectorizer,
            "matrix": self.matrix,
        }
        with (output_path / "tfidf_index.pkl").open("wb") as fp:
            pickle.dump(payload, fp)

    def load(self, index_path: Path | str) -> None:
        import pickle

        with Path(index_path).open("rb") as fp:
            payload = pickle.load(fp)
        self.chunks = payload["chunks"]
        self.embedder.vectorizer = payload["vectorizer"]
        self.matrix = payload["matrix"]

    def retrieve(self, query: str, *, top_k: int = 3) -> List[RetrievalResult]:
        if not query.strip():
            return []
        if self.matrix is None:
            raise RuntimeError("Index oluşturulmadan retrieval yapılamaz")
        query_vec = self.embedder.transform(query)
        similarities = cosine_similarity(query_vec, self.matrix)[0]
        cosine_scores = list(enumerate(map(float, similarities)))
        cosine_scores.sort(key=lambda item: item[1], reverse=True)
        results: List[RetrievalResult] = []
        for idx, score in cosine_scores[:top_k]:
            results.append(RetrievalResult(chunk=self.chunks[idx], score=score))
        return results


class HybridResponder:
    """RAG-first responder that can fall back to a fine-tuned model."""

    def __init__(
        self,
        rag_pipeline: RAGPipeline,
        *,
        min_score: float = 0.1,
        fine_tuned_model: Callable[[str, List[str], List[str]], str] | None = None,
    ) -> None:
        self.rag_pipeline = rag_pipeline
        self.min_score = min_score
        self.fine_tuned_model = fine_tuned_model

    def answer(self, question: str, *, top_k: int = 3) -> str | None:
        results = self.rag_pipeline.retrieve(question, top_k=top_k)
        if not results or results[0].score < self.min_score:
            return None

        contexts = [res.chunk.text for res in results]
        citations = [" → ".join(res.chunk.section_path[-2:]) for res in results]

        if self.fine_tuned_model is not None:
            return self.fine_tuned_model(question, contexts, citations)

        return self._template_answer(question, contexts, citations)

    def _template_answer(
        self,
        question: str,
        contexts: List[str],
        citations: List[str],
    ) -> str:
        joined_context = " ".join(contexts)
        snippet = joined_context[:400]
        citation_list = "; ".join(citations)
        return (
            f"Soru: {question}\n"
            f"Yanıt (RAG): {snippet.strip()}\n"
            f"Kaynak: {citation_list}"
        )


__all__ = ["RAGPipeline", "HybridResponder", "TfidfEmbedder", "RetrievalResult"]
