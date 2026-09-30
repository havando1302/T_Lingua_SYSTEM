# T-Langua offline training

Only QA rows with explicit training consent, a completed PII review and the
model-specific eligibility flag are included in exports.

1. In Admin QA, review the source transcript before the translation. Attach a
   mono PCM16 16 kHz WAV for voice samples.
2. Mark consent, PII status and `Use for Whisper` and/or `Use for NLLB`.
3. Download `nllb-training.jsonl` and `whisper-training.zip` from the QA page.
4. Create an isolated training environment:

   ```powershell
   python -m venv .venv-training
   .\.venv-training\Scripts\pip install -r backend\requirements-training.txt
   ```

5. Train NLLB on a CUDA training host:

   ```powershell
   python -m backend.training.train_nllb --dataset nllb-training.jsonl --output artifacts\nllb-v1
   ```

6. Train Whisper:

   ```powershell
   python -m backend.training.train_whisper --dataset whisper-training.zip --output artifacts\whisper-v1
   ```

The default jobs use LoRA and save a merged, standalone checkpoint. Keep the
export, training manifest, metrics and checkpoint together as one immutable
model release. Evaluate the locked test split before deployment.

Each trainer now evaluates the locked test split before packaging:

- NLLB writes corpus BLEU and chrF, including a breakdown by direction.
- Whisper writes WER, CER and realtime factor, including a breakdown by language.

The result is stored as `evaluation_metrics.json` and copied into the Model
Registry record by the worker. An empty metric file means the frozen dataset did
not contain a test split; such an artifact should not be promoted.

## Training Center worker

The Admin Training Center stores immutable datasets and durable jobs in the
application database. Training is intentionally executed by a separate process,
never by a FastAPI background task.

From the `backend` directory, install the training dependencies and run:

```powershell
python -m app.training_worker
```

Useful modes for a supervised Google Colab session:

```powershell
# Claim one specific queued job, then exit.
python -m app.training_worker --job-id JOB_UUID

# Drain all currently eligible jobs, then exit.
python -m app.training_worker --once
```

On a single Colab GPU, stop the inference backend before starting the worker.
For a two-model group, the NLLB job completes before the dependent Whisper job
becomes eligible. Do not start multiple GPU workers against the same queue.

Colab storage is ephemeral. Set `TRAINING_CONTROL_ROOT` to a private mounted
Drive directory before starting FastAPI or the worker, for example:

```text
/content/drive/MyDrive/T-Langua/training_control
```

The API and worker must use the same `DATABASE_URL` and
`TRAINING_CONTROL_ROOT`. Do not run SQLite directly on Drive while two
processes are writing it; on a single-GPU Colab workflow, stop FastAPI before
starting the worker, or use PostgreSQL for truly separate processes.

The worker verifies the frozen dataset checksum, invokes only the allowlisted
training module and arguments recorded by the control plane, registers the
result as a candidate artifact, and preserves events in the database. A web
request can request cancellation, but it never supplies a shell command.

To deploy after acceptance, point `NLLB_MODEL` and `WHISPER_TORCH_MODEL` at the
approved checkpoint directories, set `WHISPER_BACKEND=transformers`, and
restart the backend. The current model control-plane records do not hot-load a
checkpoint; a runtime restart is required.
