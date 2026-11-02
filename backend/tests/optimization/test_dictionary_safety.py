"""Offline glossary data and dataset boundary regressions."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import contextlib
import io
import tempfile
from unittest.mock import patch

from app.utils.translation_safety import has_internal_placeholder, is_glossary_term


class DictionarySafetyTests(unittest.TestCase):
    def test_seed_apply_backs_up_preserves_existing_and_is_idempotent(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.db.models import Base, User, AuditLog
        from app.services.translation_memory import DatabaseTranslationMemoryRepository
        backend = Path(__file__).resolve().parents[2]
        spec = importlib.util.spec_from_file_location("_seed_apply", backend / "scripts/seed_dictionary.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            engine = create_engine(f"sqlite:///{root / 'test.db'}")
            self.addCleanup(engine.dispose)
            Base.metadata.create_all(engine)
            factory = sessionmaker(bind=engine, autoflush=False)
            repository = DatabaseTranslationMemoryRepository()
            with factory() as db:
                db.add(User(username="seed-admin", password_hash="unused", role="superadmin"))
                repository.add("Trí tuệ nhân tạo", "Existing approved value", "global:approved", source_lang="vi", target_lang="en", db=db)
                db.commit()
            with patch("app.db.database.SessionLocal", factory), patch("app.db.database.engine", engine), \
                 patch.object(module, "BACKEND", root), \
                 patch("sys.argv", ["seed_dictionary.py", "--apply", "--seed", str(backend / "resources/dictionary_seed500.json")]), \
                 contextlib.redirect_stdout(io.StringIO()):
                module.main()
                module.main()
            with factory() as db:
                self.assertEqual(repository.count("global:approved", db=db), 500)
                self.assertEqual(repository.lookup("Trí tuệ nhân tạo", "global:approved", "vi", "en", db=db), "Existing approved value")
                self.assertEqual(db.query(AuditLog).count(), 1)
            backups = list((root / "backups").glob("*.db"))
            self.assertEqual(len(backups), 1)
            import sqlite3
            with contextlib.closing(sqlite3.connect(str(backups[0]))) as snapshot:
                self.assertEqual(snapshot.execute("SELECT COUNT(*) FROM translation_memory_entries").fetchone()[0], 1)
            engine.dispose()

    def test_marker_mutations_are_detected(self):
        for value in ("ZXQTLENTITY0Q", "ZXQTL ENTITY-0 Q", "Z X Q T L G L O S S A R Y 12 Q", "zxqtl_entity"):
            with self.subTest(value=value):
                self.assertTrue(has_internal_placeholder(value))
        self.assertFalse(has_internal_placeholder("Phenikaa University, H3, 15%"))

    def test_sentence_is_not_a_glossary_term(self):
        self.assertFalse(is_glossary_term("one two three four five six seven eight nine"))
        self.assertTrue(is_glossary_term("Artificial Intelligence"))

    def test_seed_has_250_reversible_pairs_without_conflicts(self):
        backend = Path(__file__).resolve().parents[2]
        spec = importlib.util.spec_from_file_location("_seed_dictionary", backend / "scripts/seed_dictionary.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rows = module.load_seed(backend / "resources/dictionary_seed500.json")
        self.assertEqual(len(rows), 500)
        self.assertEqual(sum(row["source_lang"] == "en" for row in rows), 250)
        self.assertIn({"source_text": "Đại học Phenikaa", "translated_text": "Phenikaa University", "source_lang": "vi", "target_lang": "en", "domain": "education"}, rows)
        keys = {(row["source_lang"], row["target_lang"], row["source_text"]): row["translated_text"] for row in rows}
        for row in rows:
            self.assertEqual(keys[(row["target_lang"], row["source_lang"], row["translated_text"])], row["source_text"])

    def test_nllb_validation_and_qa_eligibility_reject_leaks(self):
        from app.services.training_control import _normalise_nllb_row, eligible_for_nllb
        row = dict(source="hello", target="ZXQTL ENTITY 0 Q", source_lang="en", target_lang="vi", split="train")
        with self.assertRaisesRegex(ValueError, "placeholder"):
            _normalise_nllb_row(row, 1)
        review = SimpleNamespace(consent_for_training=True, pii_status="clean", use_for_nllb=True,
                                 translation_status="corrected", corrected_text="xin chào", corrected_source_text=None)
        self.assertFalse(eligible_for_nllb(review, SimpleNamespace(source_text="ZXQTLENTITY0Q")))
        self.assertTrue(eligible_for_nllb(review, SimpleNamespace(source_text="hello")))


if __name__ == "__main__":
    unittest.main()
