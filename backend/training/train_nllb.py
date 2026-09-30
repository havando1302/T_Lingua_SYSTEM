"""Fine-tune NLLB from the admin QA JSONL export.

Run this offline; it never connects to the production database.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from datasets import Dataset, DatasetDict
from transformers import (
    AutoModelForSeq2SeqLM, AutoTokenizer, DataCollatorForSeq2Seq,
    Seq2SeqTrainer, Seq2SeqTrainingArguments, set_seed,
)


LANG = {"vi": "vie_Latn", "en": "eng_Latn", "vie_Latn": "vie_Latn", "eng_Latn": "eng_Latn"}


def load_dataset(path: Path) -> DatasetDict:
    groups: dict[str, list[dict]] = {"train": [], "validation": [], "test": []}
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            split = row.get("split")
            if split not in groups:
                raise ValueError(f"Line {number}: invalid split")
            if row.get("source_lang") not in LANG or row.get("target_lang") not in LANG:
                raise ValueError(f"Line {number}: unsupported language")
            if not str(row.get("source", "")).strip() or not str(row.get("target", "")).strip():
                raise ValueError(f"Line {number}: empty source or target")
            groups[split].append(row)
    if not groups["train"] or not groups["validation"]:
        raise ValueError("Dataset requires non-empty train and validation splits")
    return DatasetDict({name: Dataset.from_list(rows) for name, rows in groups.items() if rows})


def evaluate_test_set(model, tokenizer, rows: Dataset | None,
                      max_source_length: int, max_target_length: int) -> dict:
    if rows is None or not len(rows):
        return {}
    import sacrebleu

    predictions: list[str] = []
    references: list[str] = []
    by_direction: dict[str, dict[str, list[str]]] = {}
    model.eval()
    for row in rows:
        source_lang, target_lang = LANG[row["source_lang"]], LANG[row["target_lang"]]
        tokenizer.src_lang = source_lang
        encoded = tokenizer(
            row["source"], return_tensors="pt", max_length=max_source_length, truncation=True,
        ).to(model.device)
        with torch.inference_mode():
            generated = model.generate(
                **encoded, forced_bos_token_id=tokenizer.convert_tokens_to_ids(target_lang),
                max_new_tokens=max_target_length, num_beams=1,
            )
        prediction = tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip()
        reference = row["target"].strip()
        predictions.append(prediction); references.append(reference)
        direction = f'{row["source_lang"]}->{row["target_lang"]}'
        bucket = by_direction.setdefault(direction, {"predictions": [], "references": []})
        bucket["predictions"].append(prediction); bucket["references"].append(reference)

    metrics = {
        "test_bleu": round(sacrebleu.corpus_bleu(predictions, [references]).score, 4),
        "test_chrf": round(sacrebleu.corpus_chrf(predictions, [references]).score, 4),
        "test_samples": len(predictions),
        "directions": {},
    }
    for direction, bucket in by_direction.items():
        metrics["directions"][direction] = {
            "bleu": round(sacrebleu.corpus_bleu(bucket["predictions"], [bucket["references"]]).score, 4),
            "chrf": round(sacrebleu.corpus_chrf(bucket["predictions"], [bucket["references"]]).score, 4),
            "samples": len(bucket["predictions"]),
        }
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="facebook/nllb-200-distilled-1.3B")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--gradient-accumulation", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--max-source-length", type=int, default=256)
    parser.add_argument("--max-target-length", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--full-finetune", action="store_true", help="Use only on a sufficiently large training GPU")
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("Output directory must be empty")
    set_seed(args.seed)
    raw = load_dataset(args.dataset)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model)
    if not args.full_finetune:
        from peft import LoraConfig, TaskType, get_peft_model
        model = get_peft_model(model, LoraConfig(
            task_type=TaskType.SEQ_2_SEQ_LM, r=16, lora_alpha=32, lora_dropout=0.05,
            target_modules=["q_proj", "v_proj"],
        ))

    def tokenize(batch: dict) -> dict:
        encoded = {"input_ids": [], "attention_mask": [], "labels": []}
        for source, target, source_lang, target_lang in zip(
            batch["source"], batch["target"], batch["source_lang"], batch["target_lang"]
        ):
            tokenizer.src_lang = LANG[source_lang]
            tokenizer.tgt_lang = LANG[target_lang]
            item = tokenizer(source, max_length=args.max_source_length, truncation=True)
            labels = tokenizer(text_target=target, max_length=args.max_target_length, truncation=True)["input_ids"]
            encoded["input_ids"].append(item["input_ids"])
            encoded["attention_mask"].append(item["attention_mask"])
            encoded["labels"].append(labels)
        return encoded

    tokenized = raw.map(tokenize, batched=True, remove_columns=raw["train"].column_names)
    trainer = Seq2SeqTrainer(
        model=model,
        args=Seq2SeqTrainingArguments(
            output_dir=str(args.output), num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size, per_device_eval_batch_size=args.batch_size,
            gradient_accumulation_steps=args.gradient_accumulation, learning_rate=args.learning_rate,
            eval_strategy="epoch", save_strategy="epoch", logging_steps=20,
            load_best_model_at_end=True, predict_with_generate=False, fp16=__import__("torch").cuda.is_available(),
            report_to=["tensorboard"], save_total_limit=2, seed=args.seed,
        ),
        train_dataset=tokenized["train"], eval_dataset=tokenized["validation"],
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model), processing_class=tokenizer,
    )
    trainer.train()
    if not args.full_finetune:
        print("T_LANGUA_STAGE=merging_lora", flush=True)
        model = model.merge_and_unload()
    print("T_LANGUA_STAGE=evaluating", flush=True)
    test_metrics = evaluate_test_set(
        model, tokenizer, raw.get("test"), args.max_source_length, args.max_target_length,
    )
    print("T_LANGUA_STAGE=packaging", flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(args.output, safe_serialization=True)
    tokenizer.save_pretrained(args.output)
    (args.output / "evaluation_metrics.json").write_text(
        json.dumps(test_metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output / "training_manifest.json").write_text(json.dumps({
        "base_model": args.model, "dataset": str(args.dataset.resolve()), "seed": args.seed,
        "train_samples": len(raw["train"]), "validation_samples": len(raw["validation"]),
        "test_samples": len(raw.get("test", [])), "method": "full" if args.full_finetune else "lora-merged",
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
