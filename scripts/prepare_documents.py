"""Prepare markdown documents into chunked JSONL payload for RAG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cargo_ai import load_markdown_documents, make_chunks


def prepare_documents(source_dir: Path, output_path: Path) -> None:
    sections = load_markdown_documents(source_dir)
    chunks = make_chunks(sections)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
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

    print(f"Kaydedilen chunk sayısı: {len(chunks)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CargoHub dokümanlarını chunk'lara böler")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("docs/source_corpus"),
        help="Markdown dokümanlarının bulunduğu dizin",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/index/chunks.jsonl"),
        help="Chunk verisinin yazılacağı dosya",
    )
    args = parser.parse_args()
    prepare_documents(args.source, args.output)


if __name__ == "__main__":
    main()
