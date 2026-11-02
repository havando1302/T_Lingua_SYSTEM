"""Speech cleanup must preserve advisory intent before translation."""
import unittest
from unittest.mock import patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.services.semantic_service import build_glossary_prompt, correct_text_semantics
from app.utils.dictionary import refine_text_rule_based


class SemanticPunctuationTests(unittest.TestCase):
    def test_valid_words_and_meaning_are_not_corrupted_by_partial_typo_rules(self):
        for text in [
            "Tôi dạy học và sử dụng máy tính để phát triển ứng dụng.",
            "Bên bán có trách nhiệm giao hàng.",
            "Người bán đang kiểm tra hàng.",
            "Tờ thu tiền được lưu tại quầy.",
        ]:
            with self.subTest(text=text):
                self.assertEqual(refine_text_rule_based(text), text)

    def test_typo_cleanup_is_idempotent(self):
        text = "Tôi dùng máy tín và ứng dụn mới."
        once = refine_text_rule_based(text)
        self.assertEqual(once, "Tôi dùng máy tính và ứng dụng mới.")
        self.assertEqual(refine_text_rule_based(once), once)

    def test_advice_with_embedded_question_is_not_direct_question(self):
        text = "Bạn nên liên lạc với bên bảo hành để kiểm tra xem ống dẫn ga có rò rỉ hay không?"
        self.assertTrue(correct_text_semantics(text, "").endswith("."))

    def test_direct_question_keeps_question_mark(self):
        self.assertTrue(correct_text_semantics("Bạn có nên liên lạc với bên bảo hành hay không?", "").endswith("?"))

    def test_local_glossary_corrects_approved_proper_name_only(self):
        entries = [{
            "source_text": "Trường Đại học Phenikaa",
            "translated_text": "Phenikaa University",
            "source_lang": "vi",
            "target_lang": "en",
        }]
        with patch.dict("os.environ", {"SEMANTIC_CORRECTION_MODE": "local"}):
            corrected = correct_text_semantics(
                "Hôm nay tôi đi học tại trường Đại học Phenica.", "", entries,
            )
        self.assertEqual(
            corrected,
            "Hôm nay tôi đi học tại Trường Đại học Phenikaa.",
        )

    def test_glossary_prompt_is_bounded(self):
        entries = [
            {"source_text": f"Tên riêng {index}", "translated_text": "x"}
            for index in range(100)
        ]
        prompt = build_glossary_prompt(entries, max_chars=80)
        self.assertLessEqual(len(prompt), 80)
        self.assertTrue(prompt.startswith("Tên riêng 0"))

    def test_glossary_prompt_skips_oversized_and_duplicate_terms(self):
        entries = [
            {"source_text": "X" * 81},
            {"source_text": "Phenikaa"},
            {"source_text": "phenikaa"},
            {"source_text": "T-Lingua"},
        ]
        self.assertEqual(
            build_glossary_prompt(entries, max_chars=30),
            "Phenikaa, T-Lingua",
        )

    def test_context_selects_relevant_term_even_after_hundreds_of_entries(self):
        entries = [{"source_text": f"Thuật ngữ {i}"} for i in range(500)]
        entries.append({"source_text": "chuyển khoản ngân hàng"})
        prompt = build_glossary_prompt(entries, max_chars=30, context="Tôi cần chuyển khoản qua ngân hàng")
        self.assertTrue(prompt.startswith("chuyển khoản ngân hàng"))
        self.assertLessEqual(len(prompt), 30)

    def test_prompt_excludes_sentences_and_internal_markers(self):
        self.assertEqual(build_glossary_prompt([
            {"source_text": "một hai ba bốn năm sáu bảy tám chín"},
            {"source_text": "ZXQTL ENTITY 0 Q"},
            {"source_text": "Phenikaa"},
        ]), "Phenikaa")
