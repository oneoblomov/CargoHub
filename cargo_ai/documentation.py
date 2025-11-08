"""Utilities for parsing project knowledge base documents and creating RAG chunks."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, List


@dataclass(slots=True)
class DocumentSection:
    """Represents a markdown section extracted from a document."""

    document_id: str
    title: str
    level: int
    path: List[str]
    content: str
    start_line: int
    end_line: int

    def full_title(self) -> str:
        return " / ".join(self.path)


@dataclass(slots=True)
class DocumentChunk:
    """Represents a chunk suitable for retrieval augmented generation."""

    chunk_id: str
    document_id: str
    section_path: List[str]
    text: str
    word_count: int
    start_line: int
    end_line: int

    metadata: dict = field(default_factory=dict)


def _normalize_document_id(path: Path) -> str:
    return path.stem.replace(" ", "_").lower()


def load_markdown_documents(folder: Path | str) -> List[DocumentSection]:
    """Parse markdown documents under *folder* and return extracted sections."""

    folder_path = Path(folder)
    if not folder_path.exists():
        raise FileNotFoundError(f"Document folder not found: {folder_path}")

    sections: List[DocumentSection] = []

    for md_path in sorted(folder_path.glob("*.md")):
        document_id = _normalize_document_id(md_path)
        sections.extend(_parse_markdown_sections(md_path, document_id))

    return sections


def _parse_markdown_sections(md_path: Path, document_id: str) -> List[DocumentSection]:
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    sections: List[DocumentSection] = []
    current_lines: List[str] = []
    current_path: List[tuple[int, str]] = []
    current_level = 0
    start_line = 0

    def flush(end_index: int) -> None:
        nonlocal current_lines
        if not current_path or not current_lines:
            current_lines = []
            return
        titles = [title for _lvl, title in current_path]
        section = DocumentSection(
            document_id=document_id,
            title=current_path[-1][1],
            level=current_level,
            path=titles[:],
            content="\n".join(current_lines).strip(),
            start_line=start_line,
            end_line=end_index,
        )
        if section.content:
            sections.append(section)
        current_lines = []

    for idx, raw_line in enumerate(lines):
        line = raw_line.rstrip()

        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()
            if level < 1:
                continue

            flush(idx)

            while current_path and current_path[-1][0] >= level:
                current_path.pop()

            current_path.append((level, title))
            current_level = level
            start_line = idx + 1
            continue

        current_lines.append(line)

    flush(len(lines))
    return sections


def _chunk_text(text: str, max_words: int, overlap: int) -> Iterator[str]:
    words = text.split()
    if not words:
        return

    step = max(max_words - overlap, 1)
    for start in range(0, len(words), step):
        end = start + max_words
        yield " ".join(words[start:end])
        if end >= len(words):
            break


def make_chunks(
    sections: Iterable[DocumentSection],
    *,
    max_words: int = 200,
    overlap: int = 40,
) -> List[DocumentChunk]:
    """Create retrieval-friendly chunks from *sections*."""

    chunks: List[DocumentChunk] = []
    for section in sections:
        if not section.content:
            continue

        for index, text in enumerate(_chunk_text(section.content, max_words, overlap)):
            chunk_id = f"{section.document_id}#{section.title.replace(' ', '_').lower()}#{index}"
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=section.document_id,
                section_path=section.path,
                text=text,
                word_count=len(text.split()),
                start_line=section.start_line,
                end_line=section.end_line,
                metadata={"heading": section.title, "path": section.path},
            )
            chunks.append(chunk)

    return chunks
