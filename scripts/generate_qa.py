"""Generate QA datasets from the CargoHub policy knowledge base."""

from __future__ import annotations

import argparse
from pathlib import Path

from cargo_ai.qa_generation import generate_datasets, generate_questions
from cargo_ai.documentation import DocumentChunk


def _write_chunk_cache(chunks: list[DocumentChunk], target_path: Path) -> None:
    import json

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as fp:
        for chunk in chunks:
            fp.write(
                json.dumps(
                    {
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "section_path": chunk.section_path,
                        "text": chunk.text,
                        "word_count": chunk.word_count,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "metadata": chunk.metadata,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="CargoHub QA veri seti oluşturucu")
    parser.add_argument(
        "--docs",
        type=Path,
        default=Path("docs/source_corpus"),
        help="Kaynak doküman klasörü",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/qa"),
        help="Çıktı klasörü",
    )
    args = parser.parse_args()

    qa_items, chunks = generate_questions(args.docs)
    generate_datasets(qa_items, args.output)

    chunk_path = Path("data/index/chunks.jsonl")
    if not chunk_path.exists():
        _write_chunk_cache(chunks, chunk_path)

    print(
        {
            "qa_pairs": len(qa_items),
            "chunks_cached": chunk_path.exists(),
        }
    )


if __name__ == "__main__":
    main()
