"""Capture source, contracts and installed metadata without starting the backend."""
from __future__ import annotations

import ast
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .common import Phase1Error, artifact_path, reject_links, sha256_file, utc_now, write_json_new


SOURCE_DIRS = (
    "backend/app", "frontend/lib", "frontend/test", "frontend/android", "frontend/ios",
    "frontend/macos", "frontend/linux", "frontend/windows", "frontend/web", "admin_web/src",
    "scripts/phase1", "tests/phase1", "docs/phase1",
)
SOURCE_FILES = (
    ".gitignore", "README.md", "docker-compose.yml", "pyrightconfig.json",
    "run_backend.bat", "run_frontend.bat", "run_admin.bat", "scripts/__init__.py",
    "backend/requirements.txt", "backend/run.py", "backend/Dockerfile",
    "backend/docker-compose.yml", "backend/test_client.py", "backend/test_streaming.py",
    "backend/convert_audio.py", "backend/pyrightconfig.json",
    "frontend/pubspec.yaml", "frontend/pubspec.lock", "frontend/analysis_options.yaml",
    "admin_web/package.json", "admin_web/package-lock.json", "admin_web/Dockerfile",
    "admin_web/index.html", "admin_web/vite.config.ts", "admin_web/tsconfig.json",
    "admin_web/tsconfig.app.json", "admin_web/tsconfig.node.json",
    "admin_web/tailwind.config.js", "admin_web/postcss.config.js",
)
SKIP_DIRS = {".git", ".gradle", ".dart_tool", "build", "dist", "ephemeral", "Pods",
             "node_modules", "venv", ".venv", "__pycache__", "xcuserdata", "secrets", ".secrets",
             "credentials", ".ssh", ".aws"}
SOURCE_SUFFIXES = {".py", ".dart", ".ts", ".tsx", ".js", ".css", ".html", ".json", ".md",
                   ".yaml", ".yml", ".xml", ".plist", ".entitlements", ".kts", ".properties",
                   ".xcconfig", ".pbxproj", ".xcworkspacedata", ".xcsettings", ".xcscheme",
                   ".cmake", ".txt", ".cc", ".cpp", ".h", ".swift", ".kt", ".rc", ".manifest"}
MODEL_FIELDS = {"APP_ENV", "DEVICE", "WHISPER_MODEL", "WHISPER_COMPUTE_TYPE", "NLLB_MODEL",
                "TTS_MODEL_ENG", "TTS_MODEL_VIE", "ENABLE_DEEPFILTER", "STT_WORKER_POOL_SIZE",
                "TRANSLATION_WORKER_POOL_SIZE", "TTS_WORKER_POOL_SIZE"}


def _conventional_secret_name(path: Path) -> bool:
    name = path.name.lower()
    return (name.startswith(".env") or name == "key.properties"
            or (path.suffix.lower() == ".json" and any(marker in name for marker in
                ("credential", "secret", "service-account", "service_account"))))


def source_paths(repo_root: Path) -> list[Path]:
    from .recovery import _regular_file

    result = {repo_root / name for name in SOURCE_FILES if (repo_root / name).is_file()}
    for name in SOURCE_DIRS:
        base = repo_root / name
        if not base.exists():
            continue
        reject_links(base)
        for folder, directories, files in os.walk(base, followlinks=False):
            directories[:] = sorted(d for d in directories if d.lower() not in {s.lower() for s in SKIP_DIRS})
            for directory in directories:
                reject_links(Path(folder) / directory)
            for filename in files:
                candidate = Path(folder) / filename
                if not _conventional_secret_name(candidate) and candidate.suffix.lower() in SOURCE_SUFFIXES:
                    result.add(candidate)
    for path in result:
        _regular_file(path, limit=32 * 1024 * 1024)
    if len(result) > 10000 or sum(path.stat().st_size for path in result) > 256 * 1024 * 1024:
        raise Phase1Error("Source capture exceeds its file-count or total-byte limit.")
    return sorted(result)


def _literal_keywords(call: ast.Call) -> dict:
    values = {}
    for keyword in call.keywords:
        try:
            values[keyword.arg] = ast.literal_eval(keyword.value)
        except (ValueError, TypeError):
            continue
    return values


def extract_contracts(repo_root: Path) -> dict:
    """Document syntax-level contracts; do not mistake dependency names for proven auth."""
    main = ast.parse((repo_root / "backend/app/main.py").read_text(encoding="utf-8-sig"))
    router_imports = {}
    mounts = {}
    static_mounts = []
    for node in ast.walk(main):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "router" and node.module:
                    router_imports[alias.asname or alias.name] = node.module
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "include_router" and node.args and isinstance(node.args[0], ast.Name):
                mounts.setdefault(node.args[0].id, []).append(_literal_keywords(node).get("prefix", ""))
            if (node.func.attr == "mount" and node.args and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == "app"):
                static_mounts.append({"path": node.args[0].value, "file": "backend/app/main.py",
                                      "line": node.lineno, "scope": "static_mount_declaration"})
    routes = []
    events = []
    for path in sorted((repo_root / "backend/app").rglob("*.py")):
        reject_links(path)
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        module = ".".join(path.relative_to(repo_root / "backend").with_suffix("").parts)
        matching = [prefix for name, imported in router_imports.items()
                    if imported == module and name in mounts for prefix in mounts[name]]
        router_prefix = ""
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                if any(isinstance(t, ast.Name) and t.id == "router" for t in node.targets):
                    router_prefix = _literal_keywords(node.value).get("prefix", "")
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if not (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)
                            and isinstance(decorator.func.value, ast.Name)
                            and decorator.func.value.id == "router" and decorator.args):
                        continue
                    verb = decorator.func.attr.upper()
                    if verb not in {"GET", "POST", "PUT", "DELETE", "PATCH", "WEBSOCKET"}:
                        continue
                    route = ast.literal_eval(decorator.args[0])
                    dependencies = []
                    defaults = [*node.args.defaults, *node.args.kw_defaults]
                    for default in defaults:
                        if (isinstance(default, ast.Call) and isinstance(default.func, ast.Name)
                                and default.func.id == "Depends" and default.args):
                            dependencies.append(ast.unparse(default.args[0]))
                    for mount in matching:
                        routes.append({"method": verb, "path": mount + router_prefix + route,
                                       "handler": node.name, "dependencies": dependencies,
                                       "file": path.relative_to(repo_root).as_posix(), "line": node.lineno})
            if isinstance(node, ast.Dict):
                values = {key.value: value for key, value in zip(node.keys, node.values)
                          if isinstance(key, ast.Constant) and isinstance(key.value, str)}
                event = values.get("type")
                if isinstance(event, ast.Constant) and isinstance(event.value, str):
                    events.append({"type": event.value, "keys": sorted(values),
                                   "file": path.relative_to(repo_root).as_posix(), "line": node.lineno})
    return {"mode": "static_ast_inventory_not_runtime_openapi_or_authorization_test",
            "routes": sorted(routes, key=lambda row: (row["path"], row["method"])),
            "server_event_shapes": events,
            "static_mounts": static_mounts,
            "not_covered": ["dynamic dependencies", "middleware policy", "deployed proxy routes"]}


def _command_version(command: list[str]) -> dict:
    executable = shutil.which(command[0])
    if not executable:
        return {"status": "not_available"}
    try:
        result = subprocess.run([executable, *command[1:]], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=8, check=False)
        if result.returncode:
            return {"status": "not_available", "exit_code": result.returncode}
        return {"status": "observed", "value": result.stdout.strip()[:2000]}
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "not_available"}


def _package_metadata(path: Path) -> list[dict]:
    if not path.is_dir():
        return []
    return sorted(({"name": dist.metadata.get("Name", "unknown"), "version": dist.version}
                   for dist in importlib.metadata.distributions(path=[str(path)])),
                  key=lambda item: item["name"].lower())


def environment_inventory(repo_root: Path) -> dict:
    config = ast.parse((repo_root / "backend/app/core/config.py").read_text(encoding="utf-8-sig"))
    defaults = {}
    for node in ast.walk(config):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in MODEL_FIELDS:
                value = node.value
                # Pydantic settings commonly express constrained defaults as
                # ``Field(default=..., ge=..., le=...)``.  Capture only the
                # literal default and never evaluate the call itself.
                if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "Field":
                    default_keyword = next((item for item in value.keywords if item.arg == "default"), None)
                    value = default_keyword.value if default_keyword is not None else (value.args[0] if value.args else None)
                if value is not None:
                    try:
                        defaults[node.target.id] = ast.literal_eval(value)
                    except (ValueError, TypeError):
                        defaults[node.target.id] = "dynamic_default_not_captured"
    environments = {}
    for name in ("backend/venv", ".venv"):
        base = repo_root / name
        package_dirs = [base / "Lib/site-packages", *base.glob("lib/python*/site-packages")]
        packages = [item for path in package_dirs for item in _package_metadata(path)]
        environments[name] = {"present": base.exists(), "installed_distributions": packages,
                              "scope": "on_disk_metadata_not_running_server"}
    flutter = {"status": "not_available"}
    launcher = shutil.which("flutter")
    if launcher:
        metadata = Path(launcher).parent / "cache/flutter.version.json"
        if metadata.is_file():
            parsed = json.loads(metadata.read_text(encoding="utf-8-sig"))
            flutter = {"status": "on_disk_metadata", **{key: parsed.get(key) for key in
                       ("flutterVersion", "dartSdkVersion", "frameworkRevision", "channel")}}
    return {"collector_python": sys.version.split()[0], "os": platform.system(),
            "machine": platform.machine(), "node": _command_version(["node", "--version"]),
            "git": _command_version(["git", "--version"]), "flutter": flutter,
            "gpu": _command_version(["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
                                     "--format=csv,noheader,nounits"]),
            "python_environments": environments, "model_source_defaults": defaults,
            "effective_deployed_config": "not_observed", "model_cache_revisions": "not_observed",
            "secrets": {"backend_env_present": (repo_root / "backend/.env").is_file(),
                        "values_copied": False}}


def _git_state(repo_root: Path) -> dict:
    def run(args: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True,
                              timeout=15, check=False)
    try:
        revision = run(["rev-parse", "HEAD"])
        status = run(["status", "--porcelain=v1", "-z", "--untracked-files=all"])
        tracked = run(["ls-files", "-z", "--", "backend/data", "backend/outputs", "data"])
        if any(result.returncode for result in (revision, status, tracked)):
            return {"status": "unavailable"}
        return {"status": "observed", "head": revision.stdout.decode().strip(),
                "worktree_porcelain_z_entries": status.stdout.decode("utf-8", "replace").split("\0")[:-1],
                "tracked_runtime_paths": tracked.stdout.decode("utf-8", "replace").split("\0")[:-1],
                "remote_urls_and_patch_contents": "not_collected"}
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "unavailable"}


def capture_baseline(repo_root: Path, destination: Path) -> dict:
    reject_links(repo_root.absolute())
    root = repo_root.resolve()
    if not (root / "backend/app/main.py").is_file():
        raise Phase1Error("Repository root must contain backend/app/main.py.")
    destination = artifact_path(root, destination)
    destination.mkdir(mode=0o700)
    # Leave interrupted captures without report.json so they cannot be mistaken for complete.
    git = _git_state(root)
    entries = []
    initial_sources = source_paths(root)
    for source in initial_sources:
        relative = source.relative_to(root)
        before = sha256_file(source)
        output = destination / "source" / relative
        output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with source.open("rb") as stream, output.open("xb") as target:
            shutil.copyfileobj(stream, target)
        if sha256_file(source) != before or sha256_file(output) != before:
            raise Phase1Error("Source changed during capture; choose a new destination and retry.")
        entries.append({"path": relative.as_posix(), "sha256": before, "size_bytes": output.stat().st_size})
    contracts = extract_contracts(root)
    environment = environment_inventory(root)
    # Also detect a source edit occurring after that file was copied.
    if (source_paths(root) != initial_sources
            or any(sha256_file(root / entry["path"]) != entry["sha256"] for entry in entries)):
        raise Phase1Error("Source changed during capture; capture is incomplete.")
    report = {"format_version": 1, "created_at": utc_now(), "status": "captured",
              "scope": "allowlisted_worktree_source_not_full_machine_or_git_history",
              "source_files": entries, "git": git, "environment": environment, "contracts": contracts,
              "runtime_inventory": runtime_inventory(root),
              "exclusions": [".env and conventional credential filenames (not a secret scanner)",
                             ".git objects/history", "runtime data (use backup command)",
                             "model weights", "device Hive stores", "external deployment state"],
              "privacy": "Source can contain embedded secrets; keep snapshots private.",
              "application_started": False}
    write_json_new(destination / "report.json", report)
    return report


def runtime_inventory(repo_root: Path) -> dict:
    groups = {}
    for name in ("backend/data", "data", "backend/outputs", "outputs", "backend/temp", "temp"):
        base = repo_root / name
        reject_links(base)
        count = 0
        size = 0
        if base.is_dir():
            for folder, directories, files in os.walk(base, followlinks=False):
                for child in (*directories, *files):
                    reject_links(Path(folder) / child)
                for child in files:
                    count += 1
                    size += (Path(folder) / child).stat().st_size
        groups[name] = {"present": base.is_dir(), "files": count, "size_bytes": size,
                        "contents_read": False}
    return {"local_groups": groups, "device_hive_and_external_stores": "not_observed",
            "effective_database_location": "requires_operator_confirmation; do not infer from default path"}


def verify_capture(directory: Path) -> dict:
    from .recovery import _checked_path

    directory = _checked_path(directory)
    manifest = directory / "report.json"
    reject_links(manifest)
    if manifest.stat().st_size > 16 * 1024 * 1024:
        raise Phase1Error("Capture report exceeds its supported size.")
    report = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or report.get("format_version") != 1 or report.get("status") != "captured":
        raise Phase1Error("Capture report is incomplete or unsupported.")
    entries = report.get("source_files")
    if not isinstance(entries, list) or not 1 <= len(entries) <= 10000:
        raise Phase1Error("Capture file inventory is invalid.")
    sources = directory / "source"
    allowed = {path.relative_to(sources).as_posix() for path in source_paths(sources)}
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "size_bytes"}:
            raise Phase1Error("Capture file entry is invalid.")
        relative = entry["path"]
        if not isinstance(relative, str) or relative not in allowed or relative in seen:
            raise Phase1Error("Capture file is missing, duplicated or outside the source allowlist.")
        seen.add(relative)
        path = sources / relative
        if path.stat().st_size != entry["size_bytes"] or sha256_file(path) != entry["sha256"]:
            raise Phase1Error("Capture byte size or checksum verification failed.")
    actual = set()
    for folder, directories, files in os.walk(sources, followlinks=False):
        for name in (*directories, *files):
            reject_links(Path(folder) / name)
        actual.update((Path(folder) / name).relative_to(sources).as_posix() for name in files)
    if actual != seen:
        raise Phase1Error("Capture contains unexpected files.")
    return {"status": "source_capture_verified", "source_files": len(seen),
            "authenticity": "not_signed; trust only locally controlled captures"}
