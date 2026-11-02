"""Speech cleanup must preserve advisory intent before translation."""
import unittest
from unittest.mock import patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.services.semantic_service import build_glossary_prompt, correct_text_semantics


class SemanticPunctuationTests(unittest.TestCase):
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
