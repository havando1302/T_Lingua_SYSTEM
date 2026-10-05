"""Reproducible large-dataset latency benchmark and cProfile for admin APIs."""
from __future__ import annotations

import cProfile
import io
import json
import logging
import os
import pstats
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
OUT = ROOT / "docs" / "progress_2026-09-24" / "evidence"
os.environ.update({
    "APP_ENV": "local", "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "api-benchmark-secret-key-that-is-long-enough",
    "AUTH_REQUIRE_MFA": "false", "AUTH_REQUIRE_PRIVILEGED_MFA": "false",
})

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_password_hash, issue_user_session
from app.db.database import get_db
from app.db.models import Base, TranslationLog, User
from app.main import app

logging.disable(logging.CRITICAL)


def percentile(values: list[float], ratio: float) -> float:
    ordered = sorted(values); position = (len(ordered) - 1) * ratio
    low = int(position); high = min(low + 1, len(ordered) - 1); fraction = position - low
    return ordered[low] + (ordered[high] - ordered[low]) * fraction


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(engine)
    db = Session()
    admin = User(username="benchmark-root", password_hash=get_password_hash("BenchmarkRoot@123"), role="superadmin", public_id=str(uuid.uuid4()), is_active=True)
    db.add(admin); db.flush()
    db.bulk_insert_mappings(User, [{
        "username": f"benchmark-user-{index:05d}", "password_hash": admin.password_hash,
        "role": "employee", "public_id": str(uuid.uuid4()), "is_active": True,
    } for index in range(5_000)])
    db.bulk_insert_mappings(TranslationLog, [{
        "client_id": f"synthetic-{index % 500}", "source_text": f"source {index}",
        "translated_text": f"translation {index}", "latency": 0.2 + (index % 20) / 100,
        "model_source": "nllb_model", "source_lang": "vi" if index % 2 == 0 else "en",
        "target_lang": "en" if index % 2 == 0 else "vi", "is_flagged": index % 17 == 0,
        "is_reviewed": index % 31 == 0,
    } for index in range(20_000)])
    db.commit()
    token = issue_user_session(admin, db)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    def override_db():
        session = Session()
        try: yield session
        finally: session.close()
    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    endpoints = {
        "dashboard": ("/admin/metrics/dashboard", 100),
        "quality_page_100": ("/admin/quality/logs?limit=100&skip=9900", 50),
        "users_page_100": ("/admin/users?limit=100&skip=4900", 50),
    }
    results = {}
    try:
        for name, (path, iterations) in endpoints.items():
            client.get(path, headers=headers)
            latencies = []
            for _ in range(iterations):
                started = time.perf_counter(); response = client.get(path, headers=headers)
                elapsed = (time.perf_counter() - started) * 1000
                if response.status_code != 200: raise RuntimeError(f"{path}: {response.status_code} {response.text}")
                latencies.append(elapsed)
            results[name] = {
                "iterations": iterations, "mean_ms": round(statistics.mean(latencies), 3),
                "p50_ms": round(percentile(latencies, .50), 3), "p95_ms": round(percentile(latencies, .95), 3),
                "p99_ms": round(percentile(latencies, .99), 3), "max_ms": round(max(latencies), 3),
                "throughput_rps_sequential": round(1000 / statistics.mean(latencies), 2),
            }
        profiler = cProfile.Profile(); profiler.enable()
        for _ in range(50): client.get("/admin/metrics/dashboard", headers=headers)
        profiler.disable(); profiler.dump_stats(str(OUT / "admin_api_profile.prof"))
        report = io.StringIO(); pstats.Stats(profiler, stream=report).sort_stats("cumulative").print_stats(35)
        (OUT / "admin_api_profile.txt").write_text(report.getvalue(), encoding="utf-8")
    finally:
        app.dependency_overrides.clear(); client.close(); db.close(); engine.dispose()
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "environment": "in-process FastAPI TestClient + SQLite in-memory, sequential requests",
        "dataset": {"users": 5_001, "translation_logs": 20_000}, "results": results,
        "limitations": [
            "Measures application/query latency without network, TLS, multi-process workers or production database.",
            "Sequential throughput is not a concurrency capacity claim.",
        ],
    }
    (OUT / "admin_api_large_dataset_benchmark.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
