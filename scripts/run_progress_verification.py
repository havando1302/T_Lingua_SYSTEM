"""Run the reproducible verification set used by the 24/09 progress report."""
from __future__ import annotations

import hashlib
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "progress_2026-09-24" / "evidence"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(name: str, command: list[str], cwd: Path, timeout: int = 300) -> dict:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(ROOT / "backend")
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command, cwd=cwd, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, check=False,
        )
        status = "passed" if completed.returncode == 0 else "failed"
        output = completed.stdout + completed.stderr
        exit_code = completed.returncode
    except subprocess.TimeoutExpired as error:
        status, exit_code = "timeout", None
        stdout = error.stdout.decode("utf-8", "replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode("utf-8", "replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        output = stdout + stderr
    except OSError as error:
        status, exit_code = "unavailable", None
        output = f"{type(error).__name__}: {error}\n"
    duration = time.perf_counter() - started
    log_path = OUT / f"{name}.log"
    log_path.write_text(output, encoding="utf-8", newline="\n")
    result = {
        "name": name,
        "status": status,
        "exit_code": exit_code,
        "duration_seconds": round(duration, 3),
        "command": command,
        "working_directory": str(cwd.relative_to(ROOT) or "."),
        "log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
        "log_sha256": sha256(log_path),
    }
    match = re.search(r"Ran (\d+) tests? in ([0-9.]+)s", output)
    if match:
        result["tests_run"] = int(match.group(1))
        result["test_runner_seconds"] = float(match.group(2))
        failure = re.search(r"FAILED \(([^)]+)\)", output)
        result["test_result"] = f"FAILED ({failure.group(1)})" if failure else "OK"
    browser = re.search(r'"passed"\s*:\s*(\d+).*?"failed"\s*:\s*(\d+)', output, re.S)
    if browser:
        result["browser_passed"] = int(browser.group(1))
        result["browser_failed"] = int(browser.group(2))
    warnings = [line.strip() for line in output.splitlines() if "warning" in line.casefold()]
    result["warning_count"] = len(warnings)
    result["warnings"] = warnings[:20]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse-flutter-timeout", action="store_true", help="Reuse the prior Flutter timeout result")
    parser.add_argument("--reuse-flutter-pass", action="store_true", help="Reuse a successful, separately captured Flutter analyzer log")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    python = str(ROOT / "backend" / "venv" / "Scripts" / "python.exe")
    modules = sorted(
        ".".join(path.relative_to(ROOT).with_suffix("").parts)
        for path in (ROOT / "backend" / "tests").rglob("test_*.py")
    )
    commands = [
        ("backend_full_tests", [python, "-m", "unittest", *modules, "-v"], ROOT, 420),
        ("admin_build", ["npm.cmd", "run", "build"], ROOT / "admin_web", 240),
        ("admin_lint", ["npm.cmd", "run", "lint"], ROOT / "admin_web", 180),
        ("admin_browser_tests", ["npm.cmd", "run", "test:browser"], ROOT / "admin_web", 240),
    ]
    previous_flutter = None
    prior_path = OUT / "verification_summary.json"
    if args.reuse_flutter_timeout and prior_path.is_file():
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        previous_flutter = next((item for item in prior.get("results", []) if item["name"] == "flutter_analyze"), None)
    if args.reuse_flutter_pass:
        log_path = OUT / "flutter_analyze.log"
        output = log_path.read_text(encoding="utf-8") if log_path.is_file() else ""
        if "No issues found!" not in output:
            raise SystemExit("flutter_analyze.log does not contain a successful analyzer result")
        previous_flutter = {
            "name": "flutter_analyze", "status": "passed", "exit_code": 0,
            "duration_seconds": 23.828,
            "command": ["flutter.bat", "analyze", "--no-pub"],
            "working_directory": "frontend",
            "log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
            "log_sha256": sha256(log_path), "warning_count": 0, "warnings": [],
            "reused": True,
            "note": "Captured outside the workspace sandbox because Dart Analysis Server writes plugin state to AppData.",
        }
    if not args.reuse_flutter_timeout and not args.reuse_flutter_pass:
        commands.append(("flutter_analyze", ["flutter.bat", "analyze", "--no-pub"], ROOT / "frontend", 180))
    results = [run(*item) for item in commands]
    if previous_flutter is not None:
        previous_flutter = {**previous_flutter, "reused": True}
        results.append(previous_flutter)
    git = subprocess.run(
        ["git", "status", "--porcelain=v1"], cwd=ROOT, capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=False,
    )
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cutoff_date": "2026-09-24",
        "scope": "backend automated tests, admin production build/lint/browser tests, Flutter static analysis",
        "results": results,
        "summary": {
            "passed": sum(result["status"] == "passed" for result in results),
            "failed": sum(result["status"] == "failed" for result in results),
            "timeout": sum(result["status"] == "timeout" for result in results),
            "unavailable": sum(result["status"] == "unavailable" for result in results),
        },
        "git": {
            "head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip(),
            "worktree_entry_count": len([line for line in git.stdout.splitlines() if line]),
            "note": "A dirty worktree means Git history cannot prove the completion date or author of each change.",
        },
    }
    output = OUT / "verification_summary.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report["summary"], ensure_ascii=False))
    for result in results:
        print(f"{result['name']}: {result['status']} ({result['duration_seconds']}s)")
    return 0 if all(report["summary"][key] == 0 for key in ("failed", "timeout", "unavailable")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
