"""Question-answer dataset generation helpers for CargoHub policy documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from .documentation import (
    DocumentChunk,
    DocumentSection,
    load_markdown_documents,
    make_chunks,
)


@dataclass(slots=True)
class QAItem:
    """Structured representation of a question-answer pair."""

    qa_id: str
    question: str
    answer: str
    qa_type: str
    source_sections: List[str]
    source_chunks: List[str]
    metadata: Dict[str, str] | None = None


def _normalize_heading(value: str) -> str:
    lowered = value.lower()
    return lowered.replace("i̇", "i")


def _clean_text(text: str) -> str:
    return " ".join(text.split()).strip()


def _section_lookup(sections: Iterable[DocumentSection]) -> Dict[str, DocumentSection]:
    lookup: Dict[str, DocumentSection] = {}
    for section in sections:
        lookup[_normalize_heading(section.title)] = section
    return lookup


def _chunk_lookup(chunks: Iterable[DocumentChunk]) -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = {}
    for chunk in chunks:
        heading = _normalize_heading(chunk.metadata.get("heading", ""))
        if not heading:
            continue
        mapping.setdefault(heading, []).append(chunk.chunk_id)
    return mapping


_blueprints = {
    "simple": [
        {
            "id": "simple_delivery_time",
            "heading": _normalize_heading("standart teslimat süresi"),
            "questions": [
                "Standart teslimat süresi ne kadar?",
                "Standart gönderilerin tahmini teslim süresi nedir?",
            ],
            "eval_split": "test",
        },
        {
            "id": "simple_defective_return_window",
            "heading": _normalize_heading("kusurlu ürün iadeleri"),
            "questions": [
                "Üretim hatası olan ürünler için iade süresi kaç gün?",
                "Kusurlu ürünlerde kaç gün içinde iade talep edebilirim?",
            ],
            "eval_split": "dev",
            "answer_override": "Üretim hatası taşıyan ürünler için iade süresi 30 gündür ve kargo masrafı CargoHub tarafından karşılanır.",
        },
        {
            "id": "simple_warranty",
            "heading": _normalize_heading("elektronik ürün garantisi"),
            "questions": [
                "Elektronik ürünlerin garantisi kaç yıl?",
                "Elektronik kategorisinde garanti süresi nedir?",
            ],
            "eval_split": "train",
        },
    ],
    "complex": [
        {
            "id": "complex_return_difference",
            "headings": [
                _normalize_heading("normal iade koşulları"),
                _normalize_heading("kusurlu ürün iadeleri"),
            ],
            "questions": [
                "Normal iade ile kusurlu ürün iadesi arasındaki farklar nelerdir?",
                "Standart iade politikasıyla kusurlu ürün iadesi nasıl ayrışıyor?",
            ],
            "eval_split": "test",
        },
        {
            "id": "complex_cancellation_after_shipping",
            "headings": [
                _normalize_heading("kargoya verilmiş siparişlerin iptali"),
                _normalize_heading("normal iade koşulları"),
            ],
            "questions": [
                "Siparişim kargoya verildiyse iptal edebilir miyim?",
                "Kargo taşıyıcıya teslim edildikten sonra iptal süreci nasıl işler?",
            ],
            "eval_split": "dev",
        },
        {
            "id": "complex_peak_period",
            "headings": [
                _normalize_heading("yoğun dönem teslimatları"),
                _normalize_heading("standart teslimat süresi"),
            ],
            "questions": [
                "Yoğun dönemlerde kargo ne kadar sürebilir?",
                "Kampanya dönemlerinde teslimat süreleri nasıl etkilenir?",
            ],
            "eval_split": "train",
        },
    ],
    "negative": [
        {
            "id": "negative_new_product",
            "questions": [
                "Yeni bir ürünün ne zaman piyasaya sürüleceği bilgisi var mı?",
                "Yeni ürün lansman tarihleri dokümanda bulunuyor mu?",
            ],
            "eval_split": "test",
        },
        {
            "id": "negative_price",
            "questions": [
                "Ürünlerin fiyatı ne kadar?",
                "Fiyat listesi paylaşılmış mı?",
            ],
            "eval_split": "dev",
        },
        {
            "id": "negative_credit_card",
            "questions": [
                "Hangi kredi kartları geçerli?",
                "Desteklenen ödeme kartları hangileri?",
            ],
            "eval_split": "train",
        },
    ],
}


def _summarize_section(section: DocumentSection) -> str:
    return _clean_text(section.content)


def _compose_complex_answer(
    headings: List[str], lookup: Dict[str, DocumentSection]
) -> str:
    parts: List[str] = []
    for heading in headings:
        section = lookup.get(heading)
        if not section:
            continue
        parts.append(_summarize_section(section))
    return " ".join(parts)


def _negative_answer() -> str:
    return (
        "Bu bilgi referans dokümanında yer almıyor. CargoHub kayıtlarında paylaşılmadı."
    )


def generate_questions(
    doc_folder: Path | str,
) -> tuple[List[QAItem], List[DocumentChunk]]:
    """Generate QA items and document chunks from markdown corpus."""

    sections = load_markdown_documents(doc_folder)
    chunks = make_chunks(sections)

    lookup = _section_lookup(sections)
    chunk_map = _chunk_lookup(chunks)

    qa_items: List[QAItem] = []

    for group, entries in _blueprints.items():
        for entry in entries:
            questions = entry["questions"]
            eval_split = entry["eval_split"]

            if group == "negative":
                answer = _negative_answer()
                source_sections: List[str] = []
                source_chunks: List[str] = []
            else:
                if group == "simple":
                    heading = entry["heading"]
                    section = lookup.get(heading)
                    if not section:
                        raise KeyError(f"Heading '{heading}' bulunamadı")
                    if entry.get("answer_override"):
                        answer = entry["answer_override"]
                    else:
                        answer = _summarize_section(section)
                    source_sections = list(section.path)
                    source_chunks = list(chunk_map.get(heading, []))
                else:  # complex
                    headings = entry["headings"]
                    answer = _compose_complex_answer(headings, lookup)
                    if not answer:
                        raise KeyError(f"Başlıklardan biri bulunamadı: {headings}")
                    sec_paths = [lookup[h].path for h in headings if lookup.get(h)]
                    source_sections = [
                        item for sublist in sec_paths for item in list(sublist)
                    ]
                    source_chunks = [
                        chunk_id
                        for h in headings
                        for chunk_id in list(chunk_map.get(h, []))
                    ]

            for variant_idx, question in enumerate(questions):
                if variant_idx == 0:
                    split = eval_split
                else:
                    split = "train"
                qa_item = QAItem(
                    qa_id=f"{entry['id']}#{variant_idx}",
                    question=question,
                    answer=answer,
                    qa_type=group,
                    source_sections=source_sections,
                    source_chunks=source_chunks,
                    metadata={"split": split},
                )
                qa_items.append(qa_item)

    return qa_items, chunks


def generate_datasets(
    qa_items: Iterable[QAItem],
    output_dir: Path | str,
) -> None:
    """Write QA datasets to split directories as JSONL."""

    import json

    splits: Dict[str, List[dict]] = {"train": [], "dev": [], "test": []}

    for item in qa_items:
        metadata = getattr(item, "metadata", {})
        split = metadata.get("split", "train")
        payload = {
            "id": item.qa_id,
            "question": item.question,
            "answer": item.answer,
            "type": item.qa_type,
            "source_sections": item.source_sections,
            "source_chunks": item.source_chunks,
        }
        splits.setdefault(split, []).append(payload)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for split, records in splits.items():
        if not records:
            continue
        split_dir = output_path / split
        split_dir.mkdir(parents=True, exist_ok=True)
        target_path = split_dir / f"{split}.jsonl"
        with target_path.open("w", encoding="utf-8") as fp:
            for record in records:
                fp.write(json.dumps(record, ensure_ascii=False) + "\n")


__all__ = [
    "QAItem",
    "generate_questions",
    "generate_datasets",
]
