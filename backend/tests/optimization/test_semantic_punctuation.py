"""Speech cleanup must preserve advisory intent before translation."""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.services.semantic_service import correct_text_semantics


class SemanticPunctuationTests(unittest.TestCase):
    def test_advice_with_embedded_question_is_not_direct_question(self):
        text = "Bạn nên liên lạc với bên bảo hành để kiểm tra xem ống dẫn ga có rò rỉ hay không?"
        self.assertTrue(correct_text_semantics(text, "").endswith("."))

    def test_direct_question_keeps_question_mark(self):
        self.assertTrue(correct_text_semantics("Bạn có nên liên lạc với bên bảo hành hay không?", "").endswith("?"))
