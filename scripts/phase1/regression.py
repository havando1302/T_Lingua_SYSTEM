"""Isolated behavior probes against existing functions, with synthetic inputs only.

These probes document known defects. They do not import the application or claim
to exercise real HTTP authentication, microphones, GPU models or deployed services.
"""
from __future__ import annotations

import __future__
import ast
import contextlib
import io
import re
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

from .common import sha256_file, utc_now


def _definitions(path: Path, names: tuple[str, ...], namespace: dict) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    selected = [node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name in names]
    if {node.name for node in selected} != set(names):
        raise ValueError("Probe target changed; review the baseline adapter.")
    # Execute only the selected definitions; module-level model/storage initialization is omitted.
    module = ast.Module(body=selected, type_ignores=[])
    exec(compile(module, str(path), "exec", flags=__future__.annotations.compiler_flag), namespace)
    return namespace


def _literal(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("Expected literal is unavailable.")


def _dictionary_probe(root: Path) -> bool:
    path = root / "backend/app/utils/dictionary.py"
    scope = _definitions(path, ("_preserve_capitalization", "refine_text_rule_based"),
                         {"re": re, "_REPLACEMENTS": _literal(path, "_REPLACEMENTS")})
    return scope["refine_text_rule_based"]("công nghiệp") == "công nghiệp"


def _whisper_scope(root: Path) -> dict:
    path = root / "backend/app/services/whisper_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    pattern = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "_HALLUCINATION_PATTERNS" for t in node.targets))
    if not (isinstance(pattern, ast.Call) and isinstance(pattern.func, ast.Attribute)
            and pattern.func.attr == "compile" and pattern.args):
        raise ValueError("Hallucination pattern interface changed.")
    return _definitions(path, ("_is_hallucination", "clean_stt_text"), {
        "re": re, "_HALLUCINATION_PATTERNS": re.compile(ast.literal_eval(pattern.args[0])),
        "INITIAL_PROMPT": _literal(path, "INITIAL_PROMPT"),
        "INITIAL_PROMPT_EN": _literal(path, "INITIAL_PROMPT_EN"),
    })


def _vad_probe(root: Path) -> bool:
    class SyntheticVad:
        def __init__(self, _aggressiveness):
            pass

        def is_speech(self, _frame, _sample_rate):
            return True

    from collections import deque
    scope = _definitions(root / "backend/app/services/vad_service.py", ("WebRtcVadStream",), {
        "deque": deque, "webrtcvad": SimpleNamespace(Vad=SyntheticVad),
        "SAMPLE_RATE": 16000, "CHANNELS": 1, "BYTES_PER_SAMPLE": 2,
        "VAD_FRAME_MS": 30, "VAD_AGGRESSIVENESS": 2, "VAD_SPEECH_PAD_MS": 120,
        "VAD_SILENCE_MS": 700,
    })
    stream = scope["WebRtcVadStream"]()
    # One bounded 31.2-second synthetic input reproduces the current no-silence overflow.
    finals, current, _ = stream.process(b"\x01\x00" * (16000 * 312 // 10))
    return bool(finals) and len(current) <= 16000 * 2 * 30


def _tm_direction_probe(root: Path) -> bool:
    class SyntheticMemory:
        @staticmethod
        def normalize_lang_code(code):
            return {"vie_Latn": "vi", "eng_Latn": "en"}.get(code, code)

        def lookup(self, text, client_id="default", source_lang=None, target_lang=None):
            if source_lang is None and target_lang is None:
                return "synthetic_cached_vi_to_en"
            if source_lang == "vie_Latn" and target_lang == "eng_Latn":
                return "synthetic_cached_vi_to_en"
            return None

    class Inputs(dict):
        def to(self, _device):
            return self

    class Tokenizer:
        src_lang = None

        def __call__(self, *args, **kwargs):
            return Inputs(input_ids=[1])

        def convert_tokens_to_ids(self, _language):
            return 2

        def batch_decode(self, *args, **kwargs):
            return ["synthetic_model_en_to_vi"]

    scope = _definitions(root / "backend/app/services/translation_service.py",
                         ("_normalize_stt_text", "_translate_nllb", "translate_text"), {
        "re": re, "time": time, "tm": SyntheticMemory(),
        "torch": SimpleNamespace(inference_mode=contextlib.nullcontext),
        "DEVICE": "cpu", "SOURCE_LANG": "vie_Latn", "TARGET_LANG": "eng_Latn",
        "settings": SimpleNamespace(TRANSLATION_BEAM_SIZE=1),
        "_NLLB_LANGUAGES": {"vi": "vie_Latn", "en": "eng_Latn"},
        "_inference_lock": contextlib.nullcontext(),
        "_get_nllb": lambda: (SimpleNamespace(generate=lambda **kwargs: [1]), Tokenizer()),
    })
    result = scope["translate_text"]("synthetic sample", source_lang="eng_Latn", target_lang="vie_Latn", use_cache=False)
    return result["translated_text"] != "synthetic_cached_vi_to_en"


def _admin_role_probe(root: Path) -> bool:
    class Denied(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code

    security_path = root / "backend/app/core/security.py"
    tree = ast.parse(security_path.read_text(encoding="utf-8-sig"))
    role_definition = next((node.value for node in tree.body if isinstance(node, ast.Assign)
                            and any(isinstance(t, ast.Name) and t.id == "PRIVILEGED_ROLES" for t in node.targets)), None)
    # Phase 2 centralizes this policy; read its literal elements without importing auth/DB.
    roles = frozenset({"admin", "superadmin"})
    if role_definition is not None:
        if not (isinstance(role_definition, ast.Call) and isinstance(role_definition.func, ast.Name)
                and role_definition.func.id == "frozenset" and len(role_definition.args) == 1):
            raise ValueError("Review the role-policy baseline adapter")
        roles = frozenset(ast.literal_eval(role_definition.args[0]))
    scope = _definitions(security_path, ("require_admin",), {
        "Depends": lambda dependency: None, "get_current_user": object(),
        "HTTPException": Denied, "status": SimpleNamespace(HTTP_403_FORBIDDEN=403),
        "PRIVILEGED_ROLES": roles,
    })
    require_admin = scope["require_admin"]
    for role in ("admin", "superadmin"):
        user = SimpleNamespace(role=role)
        if require_admin(user) is not user:
            return False
    try:
        require_admin(SimpleNamespace(role="employee"))
    except Denied as error:
        return error.status_code == 403
    return False


def _split_probe(root: Path) -> bool:
    path = root / "backend/app/utils/text_utils.py"
    scope = _definitions(path, ("split_text_for_streaming",),
                         {"re": re, "MIN_CHUNK_LENGTH": _literal(path, "MIN_CHUNK_LENGTH")})
    text = "A synthetic first sentence. Another synthetic sentence!"
    chunks = scope["split_text_for_streaming"](text)
    return " ".join(chunks) == text and scope["split_text_for_streaming"]("") == []


PROBES: tuple[tuple[str, str, bool, Callable[[Path], bool]], ...] = (
    ("valid_industry_term_preserved", "backend/app/utils/dictionary.py", True, _dictionary_probe),
    ("legitimate_farewell_not_discarded", "backend/app/services/whisper_service.py", True,
     lambda root: not _whisper_scope(root)["_is_hallucination"]("Hẹn gặp lại")),
    ("decimal_comma_preserved", "backend/app/services/whisper_service.py", True,
     lambda root: "1,5" in _whisper_scope(root)["clean_stt_text"]("1,5")),
    ("continuous_speech_bounded_at_30s", "backend/app/services/vad_service.py", True, _vad_probe),
    ("tm_respects_translation_direction", "backend/app/services/translation_service.py", True, _tm_direction_probe),
    ("admin_dependency_role_boundary", "backend/app/core/security.py", False, _admin_role_probe),
    ("tts_split_preserves_synthetic_text", "backend/app/utils/text_utils.py", False, _split_probe),
)


def run_regression(repo_root: Path) -> dict:
    results = []
    for name, source, known, probe in PROBES:
        start = time.perf_counter()
        record = {"id": name, "source": source, "known_at_audit": known}
        try:
            record["source_sha256"] = sha256_file(repo_root / source)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                passed = probe(repo_root)
            if sha256_file(repo_root / source) != record["source_sha256"]:
                raise ValueError("Probe source changed during execution.")
            record["status"] = "passed" if passed else "known_issue" if known else "unexpected_failure"
        except Exception as error:
            record.update(status="probe_error", error_type=type(error).__name__)
        record["probe_duration_ms"] = round((time.perf_counter() - start) * 1000, 3)
        results.append(record)
    counts = {state: sum(row["status"] == state for row in results)
              for state in ("passed", "known_issue", "unexpected_failure", "probe_error")}
    return {"format_version": 1, "created_at": utc_now(),
            "mode": "isolated_production_definitions_with_synthetic_dependencies",
            "counts": counts, "results": results,
            "production_latency_measured": False,
            "not_exercised": ["HTTP/WS authorization integration", "tenant storage isolation",
                              "Flutter microphone and playback", "real VAD classification",
                              "GPU/model inference", "concurrent session ordering"]}


def regression_exit_code(report: dict) -> int:
    counts = report["counts"]
    if counts["unexpected_failure"] or counts["probe_error"]:
        return 1
    return 2 if counts["known_issue"] else 0
