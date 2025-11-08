from pathlib import Path

from cargo_ai.qa_generation import generate_datasets, generate_questions
from cargo_ai.rag_pipeline import HybridResponder, RAGPipeline


def test_generate_questions_and_datasets(tmp_path):
    qa_items, chunks = generate_questions(Path("docs/source_corpus"))

    assert len(qa_items) >= 9
    assert {item.qa_type for item in qa_items} == {"simple", "complex", "negative"}

    output_dir = tmp_path / "qa"
    generate_datasets(qa_items, output_dir)

    for split in ("train", "dev", "test"):
        path = output_dir / split / f"{split}.jsonl"
        assert path.exists(), f"Beklenen dataset oluşturulmadı: {path}"

    assert len(chunks) >= 5


def test_rag_pipeline_retrieval(tmp_path):
    qa_items, chunks = generate_questions(Path("docs/source_corpus"))

    pipeline = RAGPipeline()
    pipeline.build(chunks)

    responder = HybridResponder(pipeline, min_score=0.22)

    answer = responder.answer("Standart teslimat süresi ne kadar?")
    assert answer is not None
    assert "2-4 iş günü" in answer

    negative_answer = responder.answer("Ürünlerin fiyatı ne kadar?")
    assert negative_answer is None
