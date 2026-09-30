"""CLI entry point: python -B -m scripts.phase1 --help."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .common import Phase1Error, artifact_path, write_json_new
from .recovery import RecoveryError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 1: offline baseline and isolated recovery.")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture", help="Snapshot allowlisted source/contracts/version metadata.")
    capture.add_argument("--output", type=Path, required=True)
    source_verify = commands.add_parser("verify-capture", help="Verify captured source files against hashes.")
    source_verify.add_argument("--capture", type=Path, required=True)
    backup = commands.add_parser("backup", help="Backup known local SQLite/TM files without starting the app.")
    backup.add_argument("--output", type=Path, required=True)
    backup.add_argument("--include-audio", action="store_true")
    verify = commands.add_parser("verify", help="Validate backup hashes and data structure.")
    verify.add_argument("--backup", type=Path, required=True)
    restore = commands.add_parser("restore-drill", help="Restore into a NEW restore-drills directory only.")
    restore.add_argument("--backup", type=Path, required=True)
    restore.add_argument("--output", type=Path, required=True)
    regression = commands.add_parser("regression", help="Isolated behavior probes; exit 2 means known defects.")
    regression.add_argument("--output", type=Path, required=True)
    benchmark = commands.add_parser("benchmark-http", help="Send bounded synthetic traffic to a local backend.")
    benchmark.add_argument("--base-url", default="http://127.0.0.1:8000")
    benchmark.add_argument("--samples", type=int, default=3)
    benchmark.add_argument("--timeout", type=float, default=30)
    benchmark.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.repo.absolute()
    try:
        if args.command == "capture":
            from .inventory import capture_baseline
            report = capture_baseline(root, args.output)
            summary = {"status": report["status"], "source_files": len(report["source_files"]),
                       "routes": len(report["contracts"]["routes"])}
        elif args.command == "verify-capture":
            from .inventory import verify_capture
            summary = verify_capture(args.capture)
        elif args.command in {"backup", "verify", "restore-drill"}:
            from .recovery import create_backup, verify_backup, restore_backup
            if args.command == "backup":
                output = artifact_path(root, args.output)
                summary = create_backup(root, output, include_audio=args.include_audio)
            elif args.command == "verify":
                summary = verify_backup(args.backup)
            else:
                output = artifact_path(root, args.output)
                summary = restore_backup(args.backup, output)
        else:
            output = artifact_path(root, args.output)
            if args.command == "regression":
                from .regression import run_regression, regression_exit_code
                report = run_regression(root)
                write_json_new(output, report)
                print(json.dumps({"counts": report["counts"], "report": str(output)}, ensure_ascii=True))
                return regression_exit_code(report)
            from .benchmark import benchmark_http
            report = benchmark_http(args.base_url, samples=args.samples, timeout_seconds=args.timeout)
            write_json_new(output, report)
            print(json.dumps({"status": report["status"], "report": str(output)}, ensure_ascii=True))
            return 0 if report["status"] == "measured" else 1
        # Never print source snapshots, SQL rows, TM entries, credentials or response bodies.
        print(json.dumps(summary, ensure_ascii=True))
        return 0
    except Exception as error:
        # CLI boundary: parser/transport errors can embed source text or response data.
        if isinstance(error, (Phase1Error, RecoveryError)):
            print(str(error), file=sys.stderr)
        else:
            print(f"Phase 1 command failed ({type(error).__name__}); no live restore was attempted.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
