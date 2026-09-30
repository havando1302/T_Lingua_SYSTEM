"""Isolated regressions: no live DB, TM file, model downloads, or GPU required."""
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import types
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

_BACKEND = Path(__file__).resolve().parents[2]
_ROOT = _BACKEND.parent
sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(_ROOT))
_LIVE_TM = os.path.normcase(str(_BACKEND / "data" / "translation_memory.json"))
_exists = os.path.exists


def _isolated_exists(path):
    if os.path.normcase(os.path.abspath(path)) == _LIVE_TM:
        return False
    return _exists(path)


with patch("os.path.exists", side_effect=_isolated_exists):
    from app.services import translation_memory as tm
from app.services.translation_cache import GLOBAL_TRANSLATION_CACHE, TranslationMemoryCache


def _load_service():
    fake_config = types.ModuleType("app.core.config")
    fake_config.DEVICE = "cpu"
    fake_config.SOURCE_LANG = "vie_Latn"
    fake_config.TARGET_LANG = "eng_Latn"
    fake_config.settings = types.SimpleNamespace(TRANSLATION_BEAM_SIZE=1)
    fake_torch = types.ModuleType("torch")
    fake_torch.inference_mode = contextlib.nullcontext
    spec = importlib.util.spec_from_file_location(
        "_optimization_translation_service", _BACKEND / "app/services/translation_service.py"
    )
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"app.core.config": fake_config, "torch": fake_torch}):
        spec.loader.exec_module(module)
    return module


service = _load_service()


class MemoryCacheTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.temp = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="tm-regression-")))
        for name in ("_memory", "_guest_memory", "_guest_expiry"):
            self.stack.enter_context(patch.object(tm, name, {}))
        self.path = self.temp / "translation_memory.json"
        self.stack.enter_context(patch.object(tm, "_TM_FILE", str(self.path)))
        self.stack.enter_context(patch.object(tm, "_DATA_DIR", str(self.temp)))
        GLOBAL_TRANSLATION_CACHE.clear()

    def add(self, text="shared", value="correct", owner="user:a", source="en", target="vi"):
        return tm.add(text, value, owner, source_lang=source, target_lang=target)

    def test_language_metadata_survives_reload_and_aliases(self):
        self.add("  Hello! ", "xin chào")
        tm._load()
        self.assertEqual(tm.lookup("hello", "user:a", "eng_Latn", "vie_Latn"), "xin chào")
        self.assertIsNone(tm.lookup("hello", "user:a", "vi", "en"))
        self.assertIsNone(tm.lookup("hello", "user:b", "en", "vi"))

    def test_same_source_distinct_pairs_and_exact_deletion(self):
        self.add(value="English to Vietnamese")
        self.add(value="Vietnamese to English", source="vi", target="en")
        tm._load()
        self.assertEqual(tm.count("user:a"), 2)
        self.assertEqual(tm.lookup("shared", "user:a", "en", "vi"), "English to Vietnamese")
        self.assertEqual(tm.lookup("shared", "user:a", "vi", "en"), "Vietnamese to English")
        self.assertFalse(tm.delete("shared", "user:a", "vi", "fr"))
        self.assertTrue(tm.delete("shared", "user:a", "en", "vi"))
        self.assertIsNone(tm.lookup("shared", "user:a", "en", "vi"))
        self.assertEqual(tm.lookup("shared", "user:a", "vi", "en"), "Vietnamese to English")
        self.assertTrue(tm.delete("shared", "user:a"))
        self.assertEqual(tm.count("user:a"), 0)

    def test_untagged_edit_preserves_unique_direction(self):
        self.add()
        tm.add("shared", "edited", "user:a")
        tm._load()
        self.assertEqual(tm.lookup("shared", "user:a", "en", "vi"), "edited")
        self.assertIsNone(tm.lookup("shared", "user:a", "vi", "en"))

    def test_ambiguous_untagged_edit_is_rejected_without_partial_write(self):
        self.add()
        self.add(value="reverse", source="vi", target="en")
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            tm.add("shared", "ambiguous", "user:a")
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(tm.count("user:a"), 2)

    def test_flat_legacy_migration_keeps_known_and_unknown_entries(self):
        self.path.write_text(json.dumps({"xin chào": "hello", "opaque term": "legacy"}), encoding="utf-8")
        tm._load()
        self.assertEqual(tm.lookup("xin chào", "default", "vi", "en"), "hello")
        self.assertIsNone(tm.lookup("xin chào", "default", "en", "vi"))
        self.assertEqual(tm.lookup("opaque term", "default", "en", "vi"), "legacy")
        tm.add("new", "mới", "default", source_lang="en", target_lang="vi")
        tm._load()
        self.assertEqual(tm.lookup("opaque term"), "legacy")

    def test_legacy_nested_reserved_source_is_literal_and_roundtrips(self):
        reserved_source = tm._key("secret", "en", "vi")
        self.path.write_text(json.dumps({"user:a": {reserved_source: "literal"}}), encoding="utf-8")
        tm._load()
        self.assertEqual(tm.lookup(reserved_source, "user:a"), "literal")
        self.assertIsNone(tm.lookup("secret", "user:a"))
        self.add()
        tm._load()
        self.assertEqual(tm.lookup(reserved_source, "user:a"), "literal")
        self.assertIsNone(tm.lookup("secret", "user:a"))

    def test_legacy_term_given_direction_loses_ambiguous_fallback(self):
        tm.add("opaque", "legacy", "user:a")
        self.add("opaque", "classified")
        tm._load()
        self.assertEqual(tm.count("user:a"), 1)
        self.assertEqual(tm.lookup("opaque", "user:a", "en", "vi"), "classified")
        self.assertIsNone(tm.lookup("opaque", "user:a", "vi", "en"))

    def test_listing_and_glossary_hide_storage_keys_and_other_owners(self):
        self.add(value="forward")
        self.add(value="reverse", source="vi", target="en")
        self.add("private other owner", "secret", owner="user:b")
        rows = tm.get_entries("user:a")
        self.assertEqual(len(rows), 2)
        self.assertEqual({row["source_text"] for row in rows}, {"shared"})
        self.assertEqual(tm.get_all("user:a"), {"shared": "reverse"})
        self.assertEqual(tm.get_all("user:a", "en", "vi"), {"shared": "forward"})
        self.assertEqual(tm.get_glossary_prompt("user:a"), "shared")
        self.assertNotIn("\0", str(rows))

    def test_atomic_import_saves_once_and_invalidates_injected_cache(self):
        cache = TranslationMemoryCache()
        cache.put("user:a", "en", "vi", "first", "old")
        before = cache.get_version_snapshot("user:a")
        with patch.object(tm, "_save", wraps=tm._save) as save:
            imported = tm.add_many([
                {"source_text": "first", "translated_text": "one"},
                {"source_text": "second", "translated_text": "two"},
            ], "user:a", source_lang="en", target_lang="vi")
        self.assertEqual(imported, 2)
        save.assert_called_once()
        after = cache.get_version_snapshot("user:a")
        self.assertEqual(after, (before[0] + 1, before[1]))
        self.assertIsNone(cache.get("user:a", "en", "vi", "first"))
        tm._load()
        self.assertEqual(tm.lookup("second", "user:a", "en", "vi"), "two")

    def test_import_validation_failure_never_persists_first_row(self):
        self.add()
        before = self.path.read_bytes()
        version = GLOBAL_TRANSLATION_CACHE.get_version_snapshot("user:a")
        with self.assertRaises(ValueError):
            tm.add_many([
                {"source_text": "valid", "translated_text": "valid"},
                {"source_text": "", "translated_text": "invalid"},
            ], "user:a")
        self.assertEqual(self.path.read_bytes(), before)
        self.assertIsNone(tm.lookup("valid", "user:a"))
        self.assertEqual(GLOBAL_TRANSLATION_CACHE.get_version_snapshot("user:a"), version)

    def test_failed_replace_rolls_back_add_delete_and_import(self):
        self.add()
        before = self.path.read_bytes()
        before_rows = tm.get_entries("user:a")
        cache = TranslationMemoryCache()
        cache.put("user:a", "en", "vi", "shared", "cached")
        operations = (
            lambda: self.add("new", "new"),
            lambda: tm.delete("shared", "user:a"),
            lambda: tm.add_many([{"source_text": "new", "translated_text": "new"}], "user:a"),
            lambda: self.add("new", "new", owner="user:new"),
        )
        for operation in operations:
            with self.subTest(operation=operation):
                with patch.object(tm.os, "replace", side_effect=OSError("simulated disk failure")):
                    with self.assertRaises(OSError):
                        operation()
                self.assertEqual(self.path.read_bytes(), before)
                self.assertEqual(tm.get_entries("user:a"), before_rows)
                self.assertEqual(tm.count("user:new"), 0)
                self.assertEqual(list(self.temp.glob(".tm-*.tmp")), [])
                self.assertEqual(cache.get("user:a", "en", "vi", "shared"), "cached")

    def test_corrupt_reload_preserves_existing_memory(self):
        self.add()
        self.path.write_text('{"invalid":', encoding="utf-8")
        with self.assertRaises(RuntimeError):
            tm._load()
        self.assertEqual(tm.lookup("shared", "user:a"), "correct")

    def test_guest_data_and_cache_are_forgotten_without_persistence(self):
        tm.register_guest("guest:a", datetime.now(timezone.utc) + timedelta(minutes=1))
        tm.add("guest", "private", "guest:a", volatile=True, source_lang="en", target_lang="vi")
        GLOBAL_TRANSLATION_CACHE.put("guest:a", "en", "vi", "guest", "private")
        self.assertFalse(self.path.exists())
        tm.forget_guest("guest:a")
        self.assertIsNone(tm.lookup("guest", "guest:a"))
        self.assertIsNone(GLOBAL_TRANSLATION_CACHE.get("guest:a", "en", "vi", "guest"))
        with self.assertRaises(ValueError):
            tm.add("late", "private", "guest:a", volatile=True)
        self.assertFalse(self.path.exists())

    def test_guest_capacity_is_atomic_and_expiry_invalidates_cache(self):
        tm.register_guest("guest:a", datetime.now(timezone.utc) + timedelta(minutes=1))
        rows = [{"source_text": str(i), "translated_text": str(i)} for i in range(51)]
        with self.assertRaises(ValueError):
            tm.add_many(rows, "guest:a", volatile=True)
        self.assertEqual(tm.count("guest:a"), 0)
        GLOBAL_TRANSLATION_CACHE.put("guest:a", "en", "vi", "guest", "cached")
        tm._guest_expiry["guest:a"] = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.assertEqual(tm.count("guest:a"), 0)
        self.assertIsNone(GLOBAL_TRANSLATION_CACHE.get("guest:a", "en", "vi", "guest"))

    def test_owner_and_language_boundaries_are_validated(self):
        for owner in ("", "*", "\0tm:format"):
            with self.subTest(owner=owner), self.assertRaises(ValueError):
                self.add(owner=owner)
        with self.assertRaises(ValueError):
            tm.add("word", "target", "user:a", source_lang="en")
        self.assertFalse(self.path.exists())

    def test_cache_owner_language_isolation_and_global_invalidation(self):
        cache = TranslationMemoryCache()
        cache.put("user:a", "eng_Latn", "vie_Latn", "source", "A")
        cache.put("user:b", "en", "vi", "source", "B")
        self.assertEqual(cache.get("user:a", "en", "vi", "source"), "A")
        self.assertIsNone(cache.get("user:a", "vi", "en", "source"))
        self.add()
        self.assertIsNone(cache.get("user:a", "en", "vi", "source"))
        self.assertEqual(cache.get("user:b", "en", "vi", "source"), "B")
        self.add(owner="global:approved")
        self.assertIsNone(cache.get("user:b", "en", "vi", "source"))

    def test_cache_rejects_inflight_writes_after_owner_global_or_clear_change(self):
        cache = TranslationMemoryCache()
        for invalidate in (lambda: cache.bump_version("user:a"), lambda: cache.bump_version("global:approved"), cache.clear):
            snapshot = cache.get_version_snapshot("user:a")
            invalidate()
            self.assertFalse(cache.put("user:a", "en", "vi", "source", "stale", expected_version=snapshot))
            self.assertIsNone(cache.get("user:a", "en", "vi", "source"))

    def test_cache_ttl_zero_expiry_lru_and_disabled_capacity(self):
        cache = TranslationMemoryCache(max_entries=2, default_ttl_s=5)
        with patch("app.services.translation_cache.time.monotonic", return_value=10):
            cache.put("a", "en", "vi", "first", "1")
            cache.put("a", "en", "vi", "second", "2")
            cache.get("a", "en", "vi", "first")
            cache.put("a", "en", "vi", "third", "3")
            self.assertIsNone(cache.get("a", "en", "vi", "second"))
            self.assertFalse(cache.put("a", "en", "vi", "zero", "0", ttl_s=0))
        with patch("app.services.translation_cache.time.monotonic", return_value=15):
            self.assertIsNone(cache.get("a", "en", "vi", "first"))
        self.assertFalse(TranslationMemoryCache(max_entries=0).put("a", "en", "vi", "x", "y"))

    def test_service_uses_only_owner_and_approved_global_then_cache(self):
        self.add(value="owner result")
        self.add(value="another owner", owner="user:b")
        self.add(value="unapproved legacy", owner="default")
        self.add(value="approved result", owner="global:approved")
        with patch.object(service, "_translate_nllb", side_effect=AssertionError("model must not run")):
            self.assertEqual(service.translate_text("shared", client_id="user:a", source_lang="en", target_lang="vi")["translated_text"], "owner result")
            self.assertEqual(service.translate_text("shared", client_id="user:c", source_lang="en", target_lang="vi")["translated_text"], "approved result")
            self.assertEqual(service.translate_text("shared", client_id="user:c", source_lang="en", target_lang="vi")["source"], "cache")
            self.assertEqual(service.translate_text("shared", source_lang="en", target_lang="vi")["translated_text"], "approved result")

    def test_service_respects_disabled_cache_and_does_not_use_other_owner_or_direction(self):
        self.add()
        with patch.object(service, "_translate_nllb", return_value="generated") as model:
            for _ in range(2):
                result = service.translate_text("shared", client_id="user:b", source_lang="vi", target_lang="en", use_cache=False)
                self.assertEqual(result["source"], "nllb_model")
            self.assertEqual(model.call_count, 2)
            self.assertIsNone(GLOBAL_TRANSLATION_CACHE.get("user:b", "vi", "en", "shared"))
            result = service.translate_text("shared", client_id="user:a", source_lang="vi", target_lang="en")
            self.assertEqual(result["translated_text"], "generated")

    def test_service_inference_finishing_after_dictionary_change_cannot_poison_cache(self):
        def mutate_during_inference(*args):
            self.add("fresh", "approved after generation started", owner="global:approved")
            return "outdated model result"
        with patch.object(service, "_translate_nllb", side_effect=mutate_during_inference) as model:
            first = service.translate_text("fresh", client_id="user:a", source_lang="en", target_lang="vi")
            self.assertEqual(first["translated_text"], "outdated model result")
            self.assertIsNone(GLOBAL_TRANSLATION_CACHE.get("user:a", "en", "vi", "fresh"))
            second = service.translate_text("fresh", client_id="user:a", source_lang="en", target_lang="vi")
            self.assertEqual(second["translated_text"], "approved after generation started")
            model.assert_called_once()

    def test_empty_text_never_enters_model_and_decimal_comma_is_preserved(self):
        with patch.object(service, "_translate_nllb") as model:
            with self.assertRaises(ValueError):
                service.translate_text(" \n ")
            model.assert_not_called()
        self.assertEqual(service._normalize_stt_text("Giá là 1,5 tỷ, đúng không??"), "Giá là 1,5 tỷ, đúng không?")

    def test_parallel_model_calls_cannot_switch_shared_tokenizer_direction(self):
        class Inputs(dict):
            def to(self, device):
                return self
        class Tokenizer:
            src_lang = None
            unk_token_id = -1
            def __call__(self, text, **kwargs):
                captured = self.src_lang
                time.sleep(0.01)
                if captured != self.src_lang:
                    raise AssertionError("Tokenizer direction changed during inference")
                return Inputs(language=captured)
            def convert_tokens_to_ids(self, language):
                return {"eng_Latn": 1, "vie_Latn": 2}[language]
            def batch_decode(self, tokens, **kwargs):
                return [tokens]
        class Model:
            def generate(self, language, **kwargs):
                return language
        with patch.object(service, "_get_nllb", return_value=(Model(), Tokenizer())):
            with ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(service.translate_text, "one", source_lang="en", target_lang="vi", use_cache=False)
                second = executor.submit(service.translate_text, "hai", source_lang="vi", target_lang="en", use_cache=False)
                self.assertEqual(first.result()["translated_text"], "eng_Latn")
                self.assertEqual(second.result()["translated_text"], "vie_Latn")

    def test_backup_validator_and_archive_preserve_metadata_and_all_pairs(self):
        from scripts.phase1.recovery import _validate_tm
        from scripts.backup_restore import create_backup, restore_backup
        self.add(value="forward")
        self.add(value="reverse", source="vi", target="en")
        metadata = _validate_tm(self.path)
        self.assertEqual(metadata["shape"], "client_mapping")
        self.assertEqual(metadata["entry_count"], 3)  # 2 entries plus storage format marker.
        archive = create_backup(self.temp, self.temp / "backup")
        restored = self.temp / "restored"
        self.assertTrue(restore_backup(archive, restored))
        self.assertEqual((restored / self.path.name).read_bytes(), self.path.read_bytes())
        with patch.object(tm, "_TM_FILE", str(restored / self.path.name)):
            tm._load()
        self.assertEqual(tm.lookup("shared", "user:a", "en", "vi"), "forward")
        self.assertEqual(tm.lookup("shared", "user:a", "vi", "en"), "reverse")

    def test_concurrent_private_imports_do_not_lose_entries(self):
        def write(index):
            self.add(f"word {index}", f"target {index}")
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(write, range(12)))
        tm._load()
        self.assertEqual(tm.count("user:a"), 12)
        self.assertEqual(tm.count("user:b"), 0)

    def test_use_case_injected_cache_tracks_global_dictionary_mutation(self):
        from app.application.use_cases import TranslateTurnUseCase
        from app.domain.entities import DomainTurn, LanguagePair
        stt, translator, tts = MagicMock(), MagicMock(), MagicMock()
        stt.transcribe.return_value = {"text": "shared"}
        translator.translate.return_value = {"translated_text": "model result", "source": "mock"}
        tts.synthesize.return_value = b"audio"
        cache = TranslationMemoryCache()
        use_case = TranslateTurnUseCase(stt, translator, tts, cache=cache)
        def run(index):
            turn = DomainTurn(str(index), "session", "me", LanguagePair.create("en", "vi"))
            return use_case.process_turn(turn, None, client_id="user:a")
        self.assertEqual(run(1)["translation_source"], "mock")
        self.assertEqual(run(2)["translation_source"], "cache")
        self.add(value="approved correction", owner="global:approved")
        self.assertEqual(run(3)["translated_text"], "approved correction")
        translator.translate.assert_called_once()
        self.assertTrue(tm.delete("shared", "global:approved", "en", "vi"))
        self.assertEqual(run(4)["translation_source"], "mock")

    def test_use_case_disabled_cache_and_nllb_adapter_do_not_double_cache(self):
        from app.application.use_cases import TranslateTurnUseCase
        from app.domain.entities import DomainTurn, LanguagePair
        from app.inference.adapters import NLLBTranslationAdapter
        stt, translator, tts = MagicMock(), MagicMock(), MagicMock()
        stt.transcribe.return_value = {"text": "shared"}
        translator.translate.return_value = {"translated_text": "model result", "source": "mock"}
        tts.synthesize.return_value = b"audio"
        cache = TranslationMemoryCache()
        use_case = TranslateTurnUseCase(stt, translator, tts, cache=cache, use_cache=False)
        for index in range(2):
            turn = DomainTurn(str(index), "session", "me", LanguagePair.create("en", "vi"))
            self.assertEqual(use_case.process_turn(turn, None, client_id="user:a")["translation_source"], "mock")
        self.assertEqual(translator.translate.call_count, 2)
        self.assertEqual(cache.stats()["size"], 0)
        with patch.dict(sys.modules, {"app.services.translation_service": service}):
            with patch.object(service, "translate_text", return_value={}) as translate:
                NLLBTranslationAdapter().translate("input", "eng_Latn", "vie_Latn", "user:a")
            self.assertFalse(translate.call_args.kwargs["use_cache"])


if __name__ == "__main__":
    unittest.main()
