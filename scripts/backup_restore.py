"""
Automated Backup and Restore Tool (Phase 6 Operations Lifecycle)
Sao lưu và phục hồi an toàn: SQLite/Database, Translation Memory, and System State.
Bao gồm kiểm tra tính toàn vẹn bằng mã băm SHA-256 và phục hồi nguyên tử.
"""
import os
import sys
import json
import shutil
import tarfile
import hashlib
import argparse
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "backend" / "data"
DEFAULT_BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"


def calculate_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def create_backup(data_dir: Path = DEFAULT_DATA_DIR, output_dir: Path = DEFAULT_BACKUP_DIR) -> Path:
    """Tạo file sao lưu nén tar.gz kèm metadata và checksum"""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_name = f"backup_tlangua_{timestamp}.tar.gz"
    archive_path = output_dir / archive_name

    files_to_backup = []
    for item in ["admin.db", "translation_memory.json"]:
        p = data_dir / item
        if p.exists():
            files_to_backup.append(p)

    metadata = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files": {},
        "version": "1.1.0",
    }

    # Tạo archive tạm
    temp_archive = output_dir / f".tmp_{archive_name}"
    with tarfile.open(temp_archive, "w:gz") as tar:
        for f in files_to_backup:
            tar.add(f, arcname=f.name)
            metadata["files"][f.name] = {
                "size_bytes": f.stat().st_size,
                "sha256": calculate_sha256(f),
            }

        # Lưu manifest vào archive
        manifest_data = json.dumps(metadata, indent=2).encode("utf-8")
        import io
        manifest_info = tarfile.TarInfo(name="manifest.json")
        manifest_info.size = len(manifest_data)
        manifest_info.mtime = int(datetime.now(timezone.utc).timestamp())
        tar.addfile(manifest_info, io.BytesIO(manifest_data))

    # Đổi tên nguyên tử
    temp_archive.replace(archive_path)
    print(f"[OK] Backup created successfully: {archive_path}")
    print(f"     Manifest: {json.dumps(metadata['files'], indent=2)}")
    return archive_path


def restore_backup(archive_path: Path, target_dir: Path = DEFAULT_DATA_DIR) -> bool:
    """Kiểm tra checksum và phục hồi dữ liệu an toàn vào target_dir"""
    archive_path = Path(archive_path)
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    if not archive_path.exists():
        print(f"[ERROR] Backup archive does not exist: {archive_path}")
        return False

    temp_extract = target_dir / f".tmp_restore_{int(datetime.now(timezone.utc).timestamp())}"
    temp_extract.mkdir(parents=True, exist_ok=True)

    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            # Ngăn Directory Traversal (Slip Attack)
            for member in tar.getmembers():
                if member.name.startswith(("/", "\\", "..")) or ".." in member.name:
                    raise SecurityError(f"Malicious member path detected: {member.name}")
            tar.extractall(path=temp_extract)

        manifest_file = temp_extract / "manifest.json"
        if not manifest_file.exists():
            raise ValueError("Archive is missing manifest.json")

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # Đối soát Checksum
        for fname, finfo in manifest.get("files", {}).items():
            extracted_file = temp_extract / fname
            if not extracted_file.exists():
                raise FileNotFoundError(f"File declared in manifest missing: {fname}")
            actual_sha = calculate_sha256(extracted_file)
            if actual_sha != finfo["sha256"]:
                raise ValueError(f"Checksum mismatch for {fname}: expected {finfo['sha256']}, got {actual_sha}")

        # Ghi đè nguyên tử vào target_dir
        for fname in manifest.get("files", {}):
            src = temp_extract / fname
            dest = target_dir / fname
            shutil.copy2(src, dest)
            print(f"[RESTORED] {fname} verified and written to {dest}")

        print(f"[OK] Restore completed successfully from {archive_path}")
        return True

    except Exception as err:
        print(f"[ERROR] Restore failed: {err}")
        return False
    finally:
        shutil.rmtree(temp_extract, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="T-Langua Backup and Recovery Utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup", help="Create a full system backup")
    backup_parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    backup_parser.add_argument("--output-dir", default=str(DEFAULT_BACKUP_DIR))

    restore_parser = subparsers.add_parser("restore", help="Restore from a backup archive")
    restore_parser.add_argument("--archive", required=True, help="Path to backup tar.gz archive")
    restore_parser.add_argument("--target-dir", default=str(DEFAULT_DATA_DIR))

    args = parser.parse_args()
    if args.command == "backup":
        create_backup(Path(args.data_dir), Path(args.output_dir))
    elif args.command == "restore":
        success = restore_backup(Path(args.archive), Path(args.target_dir))
        sys.exit(0 if success else 1)
