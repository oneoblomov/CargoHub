"""LoRA fine-tuning pipeline for the CargoHub policy assistant."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List


def _lazy_imports():
    try:
        from datasets import Dataset  # type: ignore
        from peft import LoraConfig, TaskType, get_peft_model  # type: ignore
        from transformers import (  # type: ignore
            AutoModelForCausalLM,
            AutoTokenizer,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
        )
    except ImportError as exc:  # pragma: no cover - runtime guard
        raise SystemExit(
            "Bu script için 'datasets', 'peft' ve 'transformers' paketleri gereklidir."
        ) from exc

    return (
        Dataset,
        LoraConfig,
        TaskType,
        get_peft_model,
        AutoModelForCausalLM,
        AutoTokenizer,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    )


def load_records(jsonl_path: Path) -> List[dict]:
    with jsonl_path.open("r", encoding="utf-8") as fp:
        return [json.loads(line) for line in fp if line.strip()]


def build_prompt(record: dict) -> str:
    question = record["question"]
    answer = record["answer"]
    q_type = record.get("type", "simple")

    system = (
        "Sen CargoHub müşteri hizmetleri asistanısın. Politika ve süreç bilgilerini"
        " net, nazik ve kaynaklara atıf yaparak cevapla. Bilgi yoksa bunu açıkça belirt."
    )

    if q_type == "negative":
        extra = (
            "Bilgi mevcut değilse kullanıcıyı yanıltmadan nazikçe bilgiye ulaşılamadığını"
            " söylemelisin."
        )
    elif q_type == "complex":
        extra = (
            "Birden fazla politikayı birleştirirken farkları açıkça listele ve teslimat"
            " süreçlerine referans ver."
        )
    else:
        extra = ""

    return (
        f"<s>[SYSTEM] {system} {extra}\n"
        f"[USER] {question}\n"
        f"[ASSISTANT] {answer}</s>"
    )


def main() -> None:
    (
        Dataset,
        LoraConfig,
        TaskType,
        get_peft_model,
        AutoModelForCausalLM,
        AutoTokenizer,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    ) = _lazy_imports()

    parser = argparse.ArgumentParser(description="CargoHub LoRA fine-tuning scripti")
    parser.add_argument("--model", default="google/gemma-2b-it", help="Temel model")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/qa/train/train.jsonl"),
        help="Eğitim veri seti (JSONL)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("models/fine_tuned"),
        help="Çıktı dizini",
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--bf16", action="store_true", help="bfloat16 eğitim kullan")
    args = parser.parse_args()

    records = load_records(args.dataset)
    if not records:
        raise SystemExit("Eğitim veri seti boş görünüyor")

    prompts = [build_prompt(record) for record in records]
    dataset = Dataset.from_dict({"text": prompts})

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        device_map="auto",
        trust_remote_code=True,
    )

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=64,
        lora_alpha=16,
        lora_dropout=0.05,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
        ],
    )

    model = get_peft_model(model, lora_config)

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        logging_steps=10,
        save_strategy="epoch",
        bf16=args.bf16,
        optim="adamw_torch",
        warmup_ratio=0.1,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator,
    )

    trainer.train()
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)

    print(f"LoRA fine-tune işlemi tamamlandı. Çıktı: {output_dir}")


if __name__ == "__main__":
    main()
