"""Evaluation harness for RAG and fine-tuned models across QA types."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List

from cargo_ai.rag_pipeline import HybridResponder, RAGPipeline


def _load_dataset(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as fp:
        return [json.loads(line) for line in fp if line.strip()]


def _token_overlap_score(prediction: str, reference: str) -> float:
    pred_tokens = set(prediction.lower().split())
    ref_tokens = set(reference.lower().split())
    if not ref_tokens:
        return 0.0
    intersection = pred_tokens & ref_tokens
    return len(intersection) / len(ref_tokens)


def _negative_success(prediction: str) -> float:
    lowered = prediction.lower()
    keywords = ["bilgi", "bulunmuyor", "paylaşılmadı", "mevcut değil", "elimde yok"]
    return 1.0 if any(word in lowered for word in keywords) else 0.0


def _evaluate_split(
    responder: HybridResponder,
    records: Iterable[dict],
) -> Dict[str, float]:
    stats: Dict[str, List[float]] = {}
    for record in records:
        prediction = responder.answer(record["question"]) or ""
        qa_type = record.get("type", "simple")
        if qa_type == "negative":
            score = _negative_success(prediction)
        else:
            score = _token_overlap_score(prediction, record["answer"])
        stats.setdefault(qa_type, []).append(score)
    return {key: mean(values) if values else 0.0 for key, values in stats.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description="CargoHub RAG değerlendirme scripti")
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("data/index/tfidf_index.pkl"),
        help="RAG indeks dosyası",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/qa/test/test.jsonl"),
        help="Değerlendirilecek veri seti",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Retrieval top-k değeri",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.08,
        help="Minimum benzerlik eşiği",
    )
    args = parser.parse_args()

    dataset = _load_dataset(args.dataset)
    if not dataset:
        raise SystemExit("Veri seti boş")

    pipeline = RAGPipeline()
    pipeline.load(args.index)
    responder = HybridResponder(pipeline, min_score=args.min_score)

    results = _evaluate_split(responder, dataset)

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
