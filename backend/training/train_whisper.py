"""Fine-tune Whisper from the consent-filtered admin QA ZIP export."""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import json
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import librosa
import torch
from datasets import Dataset, DatasetDict
from transformers import (
    Seq2SeqTrainer, Seq2SeqTrainingArguments, WhisperForConditionalGeneration,
    WhisperProcessor, set_seed,
)


def safe_extract(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(source) as archive:
        root = destination.resolve()
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if root not in target.parents and target != root:
                raise ValueError("Unsafe path in Whisper dataset archive")
        archive.extractall(destination)


def load_rows(root: Path) -> DatasetDict:
    groups: dict[str, list[dict]] = {"train": [], "validation": [], "test": []}
    with (root / "manifest.jsonl").open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line); split = row.get("split")
            if split not in groups:
                raise ValueError(f"Line {number}: invalid split")
            audio = (root / row["audio"]).resolve()
            if root.resolve() not in audio.parents or not audio.is_file():
                raise ValueError(f"Line {number}: missing or unsafe audio")
            groups[split].append(row | {"audio_path": str(audio)})
    if not groups["train"] or not groups["validation"]:
        raise ValueError("Dataset requires non-empty train and validation splits")
    return DatasetDict({name: Dataset.from_list(rows) for name, rows in groups.items() if rows})


def evaluate_test_set(model: Any, processor: WhisperProcessor, rows: Dataset | None) -> dict[str, Any]:
    if rows is None:
        return {}
    if len(rows) == 0:
        return {}
    from jiwer import cer, wer

    predictions: list[str] = []
    references: list[str] = []
    languages: list[str] = []
    audio_seconds = 0.0
    started = time.perf_counter()
    model.eval()

    device = getattr(model, "device", next(model.parameters()).device if hasattr(model, "parameters") else torch.device("cpu"))
    is_cuda = getattr(device, "type", str(device)) == "cuda"
    autocast_ctx = torch.autocast(device_type="cuda", dtype=torch.float16) if is_cuda else nullcontext()

    for row in rows:
        audio, _ = librosa.load(row["audio_path"], sr=16000, mono=True)
        audio_seconds += len(audio) / 16000
        feat = processor.feature_extractor(audio, sampling_rate=16000, return_tensors="pt")
        features = feat["input_features"].to(device)
        with torch.inference_mode(), autocast_ctx:
            generated = model.generate(
                input_features=features, language=row["language"], task="transcribe", max_new_tokens=448,
            )
        decoded = processor.batch_decode(generated, skip_special_tokens=True)
        predictions.append(decoded[0].strip())
        references.append(str(row["text"]).strip())
        languages.append(str(row["language"]))
    elapsed = time.perf_counter() - started
    metrics: dict[str, Any] = {
        "test_wer": round(float(wer(reference=references, hypothesis=predictions)), 6) if references else 0.0,
        "test_cer": round(float(cer(reference=references, hypothesis=predictions)), 6) if references else 0.0,
        "test_samples": len(predictions),
        "realtime_factor": round(elapsed / audio_seconds, 6) if audio_seconds else None,
        "languages": {},
    }
    for language in sorted(set(languages)):
        indexes = [index for index, value in enumerate(languages) if value == language]
        language_references = [references[index] for index in indexes]
        language_predictions = [predictions[index] for index in indexes]
        metrics["languages"][language] = {
            "wer": round(float(wer(reference=language_references, hypothesis=language_predictions)), 6) if language_references else 0.0,
            "cer": round(float(cer(reference=language_references, hypothesis=language_predictions)), 6) if language_references else 0.0,
            "samples": len(indexes),
        }
    return metrics


@dataclass
class WhisperCollator:
    processor: WhisperProcessor

    def __call__(self, features: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
        inputs = [{"input_features": feature["input_features"]} for feature in features]
        batch = self.processor.feature_extractor.pad(inputs, return_tensors="pt")
        labels = self.processor.tokenizer.pad(
            [{"input_ids": feature["labels"]} for feature in features], return_tensors="pt"
        )
        label_ids = labels["input_ids"]
        attention_mask = labels.get("attention_mask") if isinstance(labels, dict) else getattr(labels, "attention_mask", None)
        if attention_mask is not None:
            label_ids = label_ids.masked_fill(attention_mask.ne(1), -100)
        bos_id = getattr(self.processor.tokenizer, "bos_token_id", None)
        if bos_id is not None and (label_ids[:, 0] == bos_id).all().cpu().item():
            label_ids = label_ids[:, 1:]
        batch["labels"] = label_ids
        return batch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True, help="whisper-training.zip")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="openai/whisper-large-v3-turbo")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--full-finetune", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("Output directory must be empty")
    set_seed(args.seed)
    with tempfile.TemporaryDirectory(prefix="tlingua-whisper-") as directory:
        root = Path(directory)
        safe_extract(args.dataset, root)
        raw = load_rows(root)
        processor = WhisperProcessor.from_pretrained(args.model)
        model = WhisperForConditionalGeneration.from_pretrained(args.model)
        model.config.use_cache = False
        model.generation_config.forced_decoder_ids = None
        if not args.full_finetune:
            from peft import LoraConfig, TaskType, get_peft_model
            model = get_peft_model(model, LoraConfig(
                task_type=TaskType.SEQ_2_SEQ_LM, r=16, lora_alpha=32, lora_dropout=0.05,
                target_modules=["q_proj", "v_proj"],
            ))

        def prepare(row: dict) -> dict:
            audio, _ = librosa.load(row["audio_path"], sr=16000, mono=True)
            feat = processor.feature_extractor(audio, sampling_rate=16000)
            features = feat["input_features"][0]
            processor.tokenizer.set_prefix_tokens(language=row["language"], task="transcribe")
            encoded = processor.tokenizer(row["text"], truncation=True, max_length=448)
            labels = encoded["input_ids"]
            return {"input_features": features, "labels": labels}

        tokenized = raw.map(prepare, remove_columns=raw["train"].column_names)
        trainer = Seq2SeqTrainer(
            model=model,
            args=Seq2SeqTrainingArguments(
                output_dir=str(args.output), num_train_epochs=args.epochs,
                per_device_train_batch_size=args.batch_size, per_device_eval_batch_size=args.batch_size,
                gradient_accumulation_steps=args.gradient_accumulation, learning_rate=args.learning_rate,
                eval_strategy="epoch", save_strategy="epoch", logging_steps=10,
                load_best_model_at_end=True, fp16=torch.cuda.is_available(), gradient_checkpointing=True,
                report_to=["tensorboard"], save_total_limit=2, seed=args.seed,
            ),
            train_dataset=tokenized["train"], eval_dataset=tokenized["validation"],
            data_collator=WhisperCollator(processor), processing_class=processor,
        )
        trainer.train()
        if not args.full_finetune:
            print("T_LINGUA_STAGE=merging_lora", flush=True)
            model = model.merge_and_unload()
        model.config.use_cache = True
        print("T_LINGUA_STAGE=evaluating", flush=True)
        test_metrics = evaluate_test_set(model, processor, raw.get("test"))
        print("T_LINGUA_STAGE=packaging", flush=True)
        args.output.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(args.output, safe_serialization=True)
        processor.save_pretrained(args.output)
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
