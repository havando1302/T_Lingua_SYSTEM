"""Fail-fast readiness check for a T-Lingua trial deployment."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def load_env(path: Path) -> dict[str, str]:
    values = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, default=ROOT / "backend" / ".env")
    args = parser.parse_args()
    checks = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    if not args.env.exists():
        check("environment_file", False, f"Missing {args.env}")
        values = {}
    else:
        values = load_env(args.env)
        check("environment_file", True, str(args.env.resolve()))

    production = values.get("APP_ENV") == "production"
    check("production_mode", production, f"APP_ENV={values.get('APP_ENV', '<missing>')}")
    for key in ("JWT_SECRET_KEY", "MFA_ENCRYPTION_KEY", "BACKUP_ENCRYPTION_KEY"):
        value = values.get(key, "")
        valid = len(value) >= 32 and "change" not in value.lower() and "replace" not in value.lower()
        check(key.lower(), valid, "configured" if valid else "missing, short, or placeholder")
    origins = [item.strip() for item in values.get("CORS_ORIGINS", "").split(",") if item.strip()]
    check("https_cors", bool(origins) and all(urlsplit(item).scheme == "https" for item in origins), ",".join(origins) or "missing")
    hosts = [item.strip() for item in values.get("TRUSTED_HOSTS", "").split(",") if item.strip()]
    check("trusted_hosts", bool(hosts) and all("*" not in item for item in hosts), ",".join(hosts) or "missing")
    check("fast_decode", values.get("WHISPER_BEAM_SIZE", "1") == "1" and values.get("TRANSLATION_BEAM_SIZE", "1") == "1", "beam sizes must both be 1")
    check("safe_tts_dtype", values.get("TTS_DTYPE", "float32") == "float32", f"TTS_DTYPE={values.get('TTS_DTYPE', '<default float32>')}")
    check("six_gb_tts_placement", values.get("TTS_DEVICE", "auto") in {"auto", "cpu"}, f"TTS_DEVICE={values.get('TTS_DEVICE', '<default auto>')}")
    docker = shutil.which("docker")
    check("docker", docker is not None, docker or "Docker CLI is not installed")
    nvidia = shutil.which("nvidia-smi")
    if nvidia:
        result = subprocess.run([nvidia, "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True)
        check("nvidia_gpu", result.returncode == 0, result.stdout.strip() or result.stderr.strip())
    else:
        check("nvidia_gpu", False, "nvidia-smi is unavailable")

    report = ROOT / "outputs" / "fresh500_optimized_20261014" / "before_after_optimization_report.json"
    check("optimized_benchmark", report.exists(), str(report))
    print(json.dumps({"ready": all(item["passed"] for item in checks), "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if all(item["passed"] for item in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
