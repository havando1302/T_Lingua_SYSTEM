# T-Langua Training Center on Google Colab

This workflow is designed for a supervised project/demo environment. Colab is
ephemeral: Drive stores datasets and artifacts, while inference and training
must not share a single GPU at the same time.

## One-time Drive layout

```text
MyDrive/T-Langua/
  training_control/
    datasets/
    artifacts/
  backups/
```

Keep this directory private because Whisper datasets can contain consent-bound
voice recordings.

## Start an Admin/API session

1. Mount Drive and clone or copy the repository into `/content`.
2. Set `TRAINING_CONTROL_ROOT` before importing the application:

   ```text
   /content/drive/MyDrive/T-Langua/training_control
   ```

3. Set `DATABASE_URL` to the runtime database. Restore a backup into `/content`
   first when using SQLite; do not serve SQLite directly from Drive.
4. Install `backend/requirements.txt`, initialize the database, and start the
   API normally.
5. Open `/training-center`, create a dataset, run **Validate**, then **Freeze**.
6. As superadmin, create a LoRA job and copy its job UUID.

## Switch to training mode

1. Stop the FastAPI inference process so Whisper/NLLB/TTS release GPU memory.
2. Install the training environment:

   ```bash
   cd /content/T_Langua_Test
   python -m pip install -r backend/requirements-training.txt
   cd backend
   ```

3. Claim the exact queued job:

   ```bash
   python -m app.training_worker --job-id JOB_UUID
   ```

The worker verifies the frozen dataset checksum, runs the allowlisted trainer,
and writes checkpoints plus the candidate artifact below
`TRAINING_CONTROL_ROOT`. A `both` job group runs NLLB before Whisper.

## Return to demo mode

1. Stop the worker after the job completes.
2. Restart FastAPI and open **Models & Deploy**.
3. Validate the new artifact checksum and manifest.
4. Use A/B evaluation when a separate candidate inference runner is available.
5. Stage/promote only after quality review. The current runtime requires an
   operator-controlled model path update and restart; the control plane does not
   claim that a hot swap occurred.
6. Back up the runtime database to the private Drive backup directory.

## Free Colab safety profile

- Run only one GPU process at a time.
- Use LoRA; never select full fine-tuning from the web UI.
- Whisper: batch 1, gradient accumulation 16.
- NLLB 1.3B: start with batch 1, accumulation 16, source/target length 128.
- If NLLB 1.3B does not fit, use the allowlisted 600M base model.
- Do not start multiple workers against a SQLite queue.
- Keep a recorded demo and smaller model profile for the defense session.
