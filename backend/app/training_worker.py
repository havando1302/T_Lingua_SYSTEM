"""Standalone durable worker for T-Langua training jobs.

Run from the backend directory with ``python -m app.training_worker``. The API
process never launches training itself, so a Colab operator can stop inference
before starting this worker and avoid GPU contention.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import queue
import re
import socket
import subprocess
import sys
import threading
import time

from app.db.database import SessionLocal
from app.db.models import ModelArtifact, TrainingDataset, TrainingJob, TrainingJobEvent
from app.services.training_control import (
    artifact_directory, directory_fingerprint, file_sha256, relative_storage_uri,
    resolve_storage_uri,
)


BACKEND_DIR = Path(__file__).resolve().parents[1]
FINAL_STATES = {"completed", "failed", "cancelled"}


def utcnow() -> datetime:
    return datetime.utcnow()


def add_event(db, job_id: str, message: str, event_type: str = "log", level: str = "info",
              metrics: dict | None = None) -> None:
    cleaned = "".join(char for char in message if char in "\t " or ord(char) >= 32).strip()
    cleaned = re.sub(r"\bhf_[A-Za-z0-9]{16,}\b", "[REDACTED_HF_TOKEN]", cleaned)
    cleaned = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", "Bearer [REDACTED]", cleaned)
    cleaned = re.sub(r"(https?://)[^/@\s:]+:[^/@\s]+@", r"\1[REDACTED]@", cleaned)
    if not cleaned:
        return
    db.add(TrainingJobEvent(
        job_id=job_id, level=level, event_type=event_type, message=cleaned[:1000],
        metrics_json=json.dumps(metrics or {}, ensure_ascii=True, separators=(",", ":")),
    ))


def fail_dependents(db, job_id: str) -> None:
    rows = db.query(TrainingJob).filter(
        TrainingJob.depends_on_job_id == job_id, TrainingJob.status == "queued"
    ).all()
    for row in rows:
        row.status = "failed"
        row.error_code = "DEPENDENCY_FAILED"
        row.error_message = "The preceding job in this group did not complete"
        row.finished_at = utcnow()
        add_event(db, row.id, row.error_message, event_type="failed", level="error")


def claim_job(worker_id: str, requested_id: str | None = None) -> str | None:
    with SessionLocal() as db:
        query = db.query(TrainingJob).filter(TrainingJob.status == "queued")
        if requested_id:
            query = query.filter(TrainingJob.id == requested_id)
        candidates = query.order_by(TrainingJob.created_at.asc()).limit(20).all()
        for candidate in candidates:
            if candidate.depends_on_job_id:
                dependency = db.get(TrainingJob, candidate.depends_on_job_id)
                if dependency is None or dependency.status in {"failed", "cancelled"}:
                    candidate.status = "failed"
                    candidate.error_code = "DEPENDENCY_FAILED"
                    candidate.error_message = "The preceding job did not complete"
                    candidate.finished_at = utcnow()
                    add_event(db, candidate.id, candidate.error_message, event_type="failed", level="error")
                    db.commit()
                    continue
                if dependency.status != "completed":
                    continue
            updated = db.query(TrainingJob).filter(
                TrainingJob.id == candidate.id, TrainingJob.status == "queued"
            ).update({
                TrainingJob.status: "preparing", TrainingJob.worker_id: worker_id,
                TrainingJob.started_at: utcnow(), TrainingJob.progress_percent: 2.0,
            }, synchronize_session=False)
            if updated:
                add_event(db, candidate.id, f"Worker {worker_id} claimed the job", event_type="preparing")
                db.commit()
                return candidate.id
        db.commit()
    return None


def command_for(job: TrainingJob, dataset_path: Path, output_path: Path) -> list[str]:
    config = json.loads(job.config_json)
    module = "training.train_nllb" if job.task == "nllb" else "training.train_whisper"
    command = [
        sys.executable, "-m", module, "--dataset", str(dataset_path), "--output", str(output_path),
        "--model", job.base_model, "--epochs", str(config["epochs"]),
        "--batch-size", str(config["batch_size"]),
        "--gradient-accumulation", str(config["gradient_accumulation"]),
        "--learning-rate", str(config["learning_rate"]), "--seed", str(config["seed"]),
    ]
    if job.task == "nllb":
        command += ["--max-source-length", str(config["max_source_length"]),
                    "--max-target-length", str(config["max_target_length"])]
    return command


def _read_output(stream, output_queue: queue.Queue[str]) -> None:
    try:
        for line in iter(stream.readline, ""):
            output_queue.put(line)
    finally:
        stream.close()


def _progress_from_line(line: str, epochs: float) -> tuple[float | None, dict]:
    metrics: dict = {}
    for key, pattern in {
        "epoch": r"['\"]epoch['\"]\s*:\s*([0-9.]+)",
        "loss": r"['\"]loss['\"]\s*:\s*([0-9.eE+-]+)",
        "eval_loss": r"['\"]eval_loss['\"]\s*:\s*([0-9.eE+-]+)",
    }.items():
        match = re.search(pattern, line)
        if match:
            try:
                metrics[key] = float(match.group(1))
            except ValueError:
                pass
    epoch = metrics.get("epoch")
    progress = min(88.0, 5.0 + (float(epoch) / max(epochs, 0.1)) * 80.0) if epoch is not None else None
    return progress, metrics


def _latest_metrics(output_path: Path) -> dict:
    result = {}
    evaluation_path = output_path / "evaluation_metrics.json"
    if evaluation_path.is_file():
        try:
            evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
            if isinstance(evaluation, dict):
                result.update(evaluation)
        except (OSError, ValueError):
            pass
    states = sorted(output_path.glob("checkpoint-*/trainer_state.json"), key=lambda path: path.stat().st_mtime)
    if not states:
        return result
    try:
        state = json.loads(states[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return result
    history = state.get("log_history") or []
    evaluation = next((item for item in reversed(history) if "eval_loss" in item), {})
    training = next((item for item in reversed(history) if "loss" in item), {})
    for source, target in ((training, "train_loss"), (evaluation, "validation_loss")):
        key = "loss" if target == "train_loss" else "eval_loss"
        if isinstance(source.get(key), (int, float)):
            result[target] = float(source[key])
    return result


def run_job(job_id: str, worker_id: str) -> None:
    with SessionLocal() as db:
        job = db.get(TrainingJob, job_id)
        dataset = db.get(TrainingDataset, job.dataset_id) if job else None
        if job is None or dataset is None:
            return
        try:
            dataset_path = resolve_storage_uri(dataset.storage_uri)
            if dataset.status != "frozen" or file_sha256(dataset_path) != dataset.sha256:
                raise RuntimeError("Frozen dataset is missing or its checksum changed")
            output_path = artifact_directory(job.id, job.output_version)
            if output_path.exists() and any(output_path.iterdir()):
                raise RuntimeError("Artifact output directory is not empty")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            job.status = "training"
            job.progress_percent = 5.0
            add_event(db, job.id, "Dataset checksum verified; starting the isolated trainer", event_type="training")
            db.commit()
            command = command_for(job, dataset_path, output_path)
            job_config = json.loads(job.config_json)
            epochs = float(job_config["epochs"])
            compute_target = job_config.get("runtime", "worker")
            if compute_target == "local_gpu" and not __import__("torch").cuda.is_available():
                raise RuntimeError("Job requires a local GPU, but CUDA is not available on this worker")
            process_env = os.environ.copy()
            if compute_target == "local_cpu":
                process_env["CUDA_VISIBLE_DEVICES"] = ""
            add_event(db, job.id, f"Compute target: {compute_target}", event_type="preparing")
        except Exception as exc:
            job.status = "failed"
            job.error_code = "PREPARE_FAILED"
            job.error_message = str(exc)[:500]
            job.finished_at = utcnow()
            add_event(db, job.id, job.error_message, event_type="failed", level="error")
            fail_dependents(db, job.id)
            db.commit()
            return

    process = subprocess.Popen(
        command, cwd=str(BACKEND_DIR), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", bufsize=1, env=process_env,
    )
    output_queue: queue.Queue[str] = queue.Queue()
    reader = threading.Thread(target=_read_output, args=(process.stdout, output_queue), daemon=True)
    reader.start()
    cancellation_sent = False
    cancellation_deadline: float | None = None
    while process.poll() is None or not output_queue.empty():
        try:
            line = output_queue.get(timeout=0.5)
        except queue.Empty:
            line = ""
        with SessionLocal() as db:
            job = db.get(TrainingJob, job_id)
            if job is None:
                if process.poll() is None:
                    process.terminate()
                return
            if line:
                progress, metrics = _progress_from_line(line, epochs)
                add_event(db, job.id, line, metrics=metrics)
                stage = line.strip().removeprefix("T_LANGUA_STAGE=") if line.strip().startswith("T_LANGUA_STAGE=") else None
                if stage in {"merging_lora", "evaluating", "packaging"}:
                    job.status = "converting" if stage == "packaging" else stage
                    job.progress_percent = {"merging_lora": 89.0, "evaluating": 92.0, "packaging": 96.0}[stage]
                if progress is not None:
                    job.progress_percent = progress
                if "epoch" in metrics:
                    job.current_epoch = metrics["epoch"]
                if "loss" in metrics:
                    job.train_loss = metrics["loss"]
                if "eval_loss" in metrics:
                    job.validation_loss = metrics["eval_loss"]
            if job.cancel_requested_at and process.poll() is None and not cancellation_sent:
                cancellation_sent = True
                cancellation_deadline = time.monotonic() + 15
                job.status = "cancelling"
                add_event(db, job.id, "Worker sent a termination request to the trainer", event_type="cancelling")
                process.terminate()
            elif cancellation_deadline and process.poll() is None and time.monotonic() >= cancellation_deadline:
                cancellation_deadline = None
                add_event(db, job.id, "Trainer did not stop within 15 seconds; forcing process exit",
                          event_type="cancelling", level="warning")
                process.kill()
            db.commit()
    reader.join(timeout=2)
    return_code = process.wait()

    with SessionLocal() as db:
        job = db.get(TrainingJob, job_id)
        dataset = db.get(TrainingDataset, job.dataset_id) if job else None
        if job is None or dataset is None:
            return
        output_path = artifact_directory(job.id, job.output_version)
        if job.cancel_requested_at:
            job.status = "cancelled"
            job.progress_percent = min(job.progress_percent, 99.0)
            job.finished_at = utcnow()
            add_event(db, job.id, "Training job cancelled", event_type="cancelled")
            fail_dependents(db, job.id)
            db.commit()
            return
        if return_code != 0:
            job.status = "failed"
            job.error_code = "TRAINER_EXIT"
            job.error_message = f"Trainer exited with code {return_code}"
            job.finished_at = utcnow()
            add_event(db, job.id, job.error_message, event_type="failed", level="error")
            fail_dependents(db, job.id)
            db.commit()
            return
        try:
            job.status = "converting"
            job.progress_percent = 97.0
            metrics = _latest_metrics(output_path)
            release = {
                "schema_version": 1, "job_id": job.id, "component": job.task,
                "version": job.output_version, "base_model": job.base_model,
                "dataset_id": dataset.id, "dataset_sha256": dataset.sha256,
                "method": job.method, "config": json.loads(job.config_json), "metrics": metrics,
                "worker_id": worker_id, "created_at": utcnow().isoformat() + "Z",
            }
            (output_path / "release_manifest.json").write_text(
                json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            digest, size = directory_fingerprint(output_path)
            artifact = ModelArtifact(
                component=job.task, version=job.output_version, base_model=job.base_model,
                dataset_id=dataset.id, job_id=job.id, format="transformers",
                storage_uri=relative_storage_uri(output_path), sha256=digest, size_bytes=size,
                status="candidate", metrics_json=json.dumps(metrics, separators=(",", ":")),
            )
            db.add(artifact)
            db.flush()
            job.artifact_id = artifact.id
            job.train_loss = metrics.get("train_loss", job.train_loss)
            job.validation_loss = metrics.get("validation_loss", job.validation_loss)
            job.status = "completed"
            job.progress_percent = 100.0
            job.finished_at = utcnow()
            add_event(db, job.id, "Training completed and a candidate artifact was registered",
                      event_type="completed", metrics=metrics)
            db.commit()
        except Exception as exc:
            db.rollback()
            job = db.get(TrainingJob, job_id)
            job.status = "failed"
            job.error_code = "PACKAGE_FAILED"
            job.error_message = str(exc)[:500]
            job.finished_at = utcnow()
            add_event(db, job.id, job.error_message, event_type="failed", level="error")
            fail_dependents(db, job.id)
            db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Exit when no eligible queued job remains")
    parser.add_argument("--job-id", help="Only claim this queued job")
    parser.add_argument("--poll-interval", type=float, default=5.0)
    args = parser.parse_args()
    if args.poll_interval < 0.5 or args.poll_interval > 300:
        parser.error("poll interval must be between 0.5 and 300 seconds")
    worker_id = f"{socket.gethostname()}-{os.getpid()}"
    while True:
        job_id = claim_job(worker_id, args.job_id)
        if job_id:
            run_job(job_id, worker_id)
            if args.job_id:
                return
            continue
        if args.once or args.job_id:
            return
        time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()
