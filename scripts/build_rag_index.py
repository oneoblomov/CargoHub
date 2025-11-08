"""Construct the TF-IDF based RAG index from prepared chunks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cargo_ai.documentation import DocumentChunk
from cargo_ai.rag_pipeline import RAGPipeline


def _load_chunks(chunk_path: Path) -> list[DocumentChunk]:
    with chunk_path.open("r", encoding="utf-8") as fp:
        raw_lines = [line.strip() for line in fp if line.strip()]

    chunks: list[DocumentChunk] = []
    for line in raw_lines:
        payload = json.loads(line)
        chunk = DocumentChunk(
            chunk_id=payload["chunk_id"],
            document_id=payload["document_id"],
            section_path=payload["section_path"],
            text=payload["text"],
            word_count=payload["word_count"],
            start_line=payload["start_line"],
            end_line=payload["end_line"],
            metadata=payload.get("metadata", {}),
        )
        chunks.append(chunk)
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="TF-IDF tabanlı RAG indeksi oluşturur")
    parser.add_argument(
        "--chunk-file",
        type=Path,
        default=Path("data/index/chunks.jsonl"),
        help="Chunk dosyasının yolu",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/index"),
        help="İndeks dosyasının yazılacağı dizin",
    )
    args = parser.parse_args()

    chunks = _load_chunks(args.chunk_file)
    pipeline = RAGPipeline()
    pipeline.build(chunks)
    pipeline.save(args.output_dir)

    print(f"RAG indeksi kaydedildi: {args.output_dir / 'tfidf_index.pkl'}")


if __name__ == "__main__":
    main()
