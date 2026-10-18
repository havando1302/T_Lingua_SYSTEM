import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_TEST_ENV = {
    "APP_ENV": "local",
    "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "translation-memory-database-test-secret-long-enough",
    "AUTH_REQUIRE_MFA": "false",
    "AUTH_REQUIRE_PRIVILEGED_MFA": "false",
}

with patch.dict(os.environ, _TEST_ENV):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.db.models import Base, SystemSetting, TranslationMemoryEntry
    from app.services import translation_memory as tm


class TranslationMemoryDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tm-database-")
        self.addCleanup(self.temp.cleanup)
        self.database_path = Path(self.temp.name) / "translation-memory.db"
        self.engine = create_engine(f"sqlite:///{self.database_path}")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.addCleanup(self.engine.dispose)

    def test_repository_survives_new_sessions(self):
        repository = tm.DatabaseTranslationMemoryRepository()
        with patch("app.db.database.SessionLocal", self.Session):
            self.assertTrue(repository.add(
                "Xin chào", "Hello", "global:approved",
                source_lang="vi", target_lang="en",
            ))

            # Every call without an injected session opens a new DB session,
            # equivalent to a later request or a restarted service process.
            self.assertEqual(repository.count("global:approved"), 1)
            self.assertEqual(
                repository.lookup("xin chào", "global:approved", "vi", "en"),
                "Hello",
            )

        with self.Session() as restarted_session:
            row = restarted_session.query(TranslationMemoryEntry).one()
            self.assertEqual(row.translated_text, "Hello")
            self.assertTrue(row.is_approved)

    def test_legacy_json_migration_is_atomic_backed_up_and_idempotent(self):
        legacy_path = Path(self.temp.name) / "translation_memory.json"
        legacy_path.write_text(json.dumps({
            tm._FORMAT_MARKER: tm._FORMAT_VALUE,
            "global:approved": {
                tm._key("xin chào", "vi", "en"): "hello",
            },
            "private-owner": {
                tm._key("hello", "en", "vi"): "xin chào",
            },
        }, ensure_ascii=False), encoding="utf-8")

        with patch.object(tm, "_TM_FILE", str(legacy_path)), patch.object(tm, "_memory", {}):
            with self.Session() as session:
                # Older builds could record a successful zero-row migration.
                # Restoring a non-empty JSON later must still recover the data.
                session.add(SystemSetting(
                    key="translation_memory_database_migration",
                    value='{"entries":0,"owners":0}',
                    description="historical empty migration",
                ))
                session.commit()
                result = tm.migrate_legacy_json_to_database(session)
                session.commit()
                self.assertTrue(result["applied"])
                self.assertEqual(result["entries"], 2)
                self.assertEqual(result["owners"], 2)
                self.assertTrue(Path(result["backup"]).exists())

            with self.Session() as restarted_session:
                self.assertEqual(restarted_session.query(TranslationMemoryEntry).count(), 2)
                marker = restarted_session.query(SystemSetting).filter(
                    SystemSetting.key == "translation_memory_database_migration"
                ).one()
                self.assertEqual(json.loads(marker.value)["entries"], 2)
                second = tm.migrate_legacy_json_to_database(restarted_session)
                self.assertFalse(second["applied"])
                self.assertEqual(restarted_session.query(TranslationMemoryEntry).count(), 2)


if __name__ == "__main__":
    unittest.main()
