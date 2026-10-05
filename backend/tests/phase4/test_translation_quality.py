import os
import unittest
from unittest.mock import patch
import numpy as np

_TEST_ENV = {
    "APP_ENV": "local",
    "DATABASE_URL": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "test-secret-key-phase4-tests-must-be-long-enough",
    "AUTH_REQUIRE_MFA": "false", "AUTH_REQUIRE_PRIVILEGED_MFA": "false",
}

with patch.dict(os.environ, _TEST_ENV):
    from app.services import translation_memory as tm
    from app.utils.dictionary import refine_text_rule_based
    from app.services.whisper_service import clean_stt_text, _is_hallucination
    from app.utils.text_utils import split_text_for_streaming
    from app.services.deepfilter_service import denoise_numpy
    from app.db.models import TranslationMemoryEntry, Base


class TranslationQualityTests(unittest.TestCase):
    def test_tm_direction_awareness_and_isolation(self):
        owner = "test-owner-p4"
        # Add Vietnamese -> English entry
        tm.add("chúc mừng", "congratulations", client_id=owner, source_lang="vi", target_lang="en")
        # Add English -> Vietnamese entry
        tm.add("two", "hai", client_id=owner, source_lang="en", target_lang="vi")

        # Lookup with correct direction succeeds
        self.assertEqual(
            tm.lookup("chúc mừng", client_id=owner, source_lang="vi", target_lang="en"),
            "congratulations"
        )
        self.assertEqual(
            tm.lookup("chúc mừng", client_id=owner, source_lang="vie_Latn", target_lang="eng_Latn"),
            "congratulations"
        )

        # Lookup with reversed direction fails (does not return mismatched translation)
        self.assertIsNone(
            tm.lookup("chúc mừng", client_id=owner, source_lang="en", target_lang="vi")
        )
        self.assertIsNone(
            tm.lookup("two", client_id=owner, source_lang="vi", target_lang="en")
        )

        # Lookup with untagged languages still retrieves the term
        self.assertEqual(
            tm.lookup("chúc mừng", client_id=owner),
            "congratulations"
        )

        # Clean up
        tm.delete("chúc mừng", client_id=owner)
        tm.delete("two", client_id=owner)

    def test_repository_pattern_interface(self):
        repo = tm.get_tm_repository()
        self.assertIsInstance(repo, tm.ITranslationMemoryRepository)

        owner = "test-repo-owner"
        self.assertTrue(repo.add("thử nghiệm", "test", client_id=owner, source_lang="vi", target_lang="en"))
        self.assertEqual(repo.count(owner), 1)
        self.assertEqual(repo.lookup("thử nghiệm", client_id=owner, source_lang="vi", target_lang="en"), "test")
        self.assertIn("thử nghiệm", repo.get_all(owner))

        self.assertTrue(repo.delete("thử nghiệm", client_id=owner))
        self.assertEqual(repo.count(owner), 0)

    def test_fuzzy_tm_is_conservative_direction_aware_and_unambiguous(self):
        owner = "test-fuzzy-owner"
        tm.add(
            "vui lòng gửi báo cáo trước thứ sáu", "please send the report before Friday",
            client_id=owner, source_lang="vi", target_lang="en",
        )
        try:
            self.assertEqual(
                tm.lookup_fuzzy(
                    "vui lòng gửi báo cáo trươc thứ sáu", client_id=owner,
                    source_lang="vi", target_lang="en",
                ),
                "please send the report before Friday",
            )
            self.assertIsNone(tm.lookup_fuzzy(
                "vui lòng gửi báo cáo trươc thứ sáu", client_id=owner,
                source_lang="en", target_lang="vi",
            ))
            self.assertIsNone(tm.lookup_fuzzy(
                "gửi báo cáo", client_id=owner, source_lang="vi", target_lang="en",
            ))
        finally:
            tm.delete("vui lòng gửi báo cáo trước thứ sáu", client_id=owner)

    def test_dictionary_preserves_industry_term(self):
        # "công nghiệp" must not be replaced with "công nghệ"
        phrase = "Cách mạng công nghiệp lần thứ tư"
        refined = refine_text_rule_based(phrase)
        self.assertEqual(refined, phrase)
        self.assertIn("công nghiệp", refined)

    def test_short_zoo_phrase_variants_are_corrected(self):
        variants = (
            ("Sjá þú.", "Sở thú."),
            ("Thở thú", "Sở thú"),
            ("Tờ Thu", "Sở thú"),
        )
        for variant, expected in variants:
            with self.subTest(variant=variant):
                self.assertEqual(refine_text_rule_based(variant), expected)

    def test_stt_preserves_decimal_comma(self):
        # Decimal numbers like 1,5 must keep the comma
        stt_output = clean_stt_text("Giá trị là 1,5 tỷ đồng")
        self.assertIn("1,5", stt_output)

        isolated_decimal = clean_stt_text("1,5")
        self.assertEqual(isolated_decimal, "1,5")

    def test_hallucination_preserves_legitimate_farewell(self):
        # "Hẹn gặp lại" is a legitimate conversation farewell and must not be discarded
        self.assertFalse(_is_hallucination("Hẹn gặp lại"))
        self.assertFalse(_is_hallucination("Hẹn gặp lại bạn ngày mai."))

        # Known hallucination pattern should still be flagged
        self.assertTrue(_is_hallucination("Cảm ơn các bạn đã theo dõi"))
        self.assertTrue(_is_hallucination("Nhớ like và subscribe"))

    def test_tts_chunk_bounding_on_long_unpunctuated_text(self):
        # 100 words without punctuation
        long_sentence = " ".join(["từ" for _ in range(100)])
        chunks = split_text_for_streaming(long_sentence)

        # Must split into multiple bounded chunks
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 150)
            self.assertGreaterEqual(len(chunk), 15)

        # Standard punctuated sentence preserves exact equality
        punct_text = "A synthetic first sentence. Another synthetic sentence!"
        punct_chunks = split_text_for_streaming(punct_text)
        self.assertEqual(" ".join(punct_chunks), punct_text)

    def test_deepfilter_resampling_safe_fallback(self):
        # 16kHz audio input (1 second of synthetic speech/silence)
        synthetic_16k = np.zeros(16000, dtype=np.float32)
        output = denoise_numpy(synthetic_16k, input_sr=16000)
        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(len(output), 16000)

    def test_short_commands_bypass_deepfilter(self):
        command = np.linspace(-0.1, 0.1, 2 * 16000, dtype=np.float32)
        with patch("app.services.deepfilter_service._get_deepfilter",
                   side_effect=AssertionError("DeepFilter must not run for a short command")):
            output = denoise_numpy(
                command, input_sr=16000, min_duration_seconds=3.0,
            )
        self.assertIs(output, command)

    def test_translation_memory_entry_db_schema(self):
        table = Base.metadata.tables.get("translation_memory_entries")
        self.assertIsNotNone(table)
        cols = {c.name for c in table.columns}
        self.assertTrue({"owner_id", "source_lang", "target_lang", "source_text_normalized"}.issubset(cols))


if __name__ == "__main__":
    unittest.main()
