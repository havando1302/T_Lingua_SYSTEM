"""Regression coverage for complete, low-latency NLLB sentence batching."""
from unittest.mock import patch

import torch

from app.services import translation_service as service


class _Inputs(dict):
    def __init__(self, batch):
        lengths = [max(2, len(text.split()) + 2) for text in batch]
        width = max(lengths)
        input_ids = torch.ones((len(batch), width), dtype=torch.long)
        attention_mask = torch.tensor(
            [[1] * length + [0] * (width - length) for length in lengths]
        )
        super().__init__(input_ids=input_ids, attention_mask=attention_mask)
        self.input_ids = input_ids
        self.attention_mask = attention_mask

    def to(self, _device):
        return self


class _Tokenizer:
    unk_token_id = -1

    def __init__(self):
        self.src_lang = None
        self.last_batch = []
        self.calls = []

    def convert_tokens_to_ids(self, _lang):
        return 42

    def __call__(self, batch, **kwargs):
        assert kwargs == {"return_tensors": "pt", "padding": True, "truncation": True}
        self.last_batch = list(batch)
        self.calls.append(self.last_batch)
        return _Inputs(batch)

    def batch_decode(self, _tokens, **_kwargs):
        return [f"translated:{text}" for text in self.last_batch]


class _Model:
    def __init__(self):
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return torch.ones((kwargs["input_ids"].shape[0], 2), dtype=torch.long)


def test_sentence_split_preserves_decimal_and_version_values():
    text = "Release 3.1 is ready. Value is 1.5! Continue?"
    assert service._split_translation_segments(text) == [
        "Release 3.1 is ready.", "Value is 1.5!", "Continue?"
    ]


def test_nllb_translates_all_sentences_in_bounded_batches():
    tokenizer, model = _Tokenizer(), _Model()
    text = "One. Two! Three? Four. Five."
    with patch.object(service, "_get_nllb", return_value=(model, tokenizer)), \
         patch.object(service.settings, "TRANSLATION_SENTENCE_BATCH_SIZE", 2):
        translated = service._translate_nllb(text, "eng_Latn", "vie_Latn")

    assert tokenizer.calls == [["One.", "Two!"], ["Three?", "Four."], ["Five."]]
    assert translated == (
        "translated:One. translated:Two! translated:Three? "
        "translated:Four. translated:Five."
    )
    assert all(call["num_beams"] == service.settings.TRANSLATION_BEAM_SIZE for call in model.calls)
    assert all("no_repeat_ngram_size" not in call for call in model.calls)
    assert all(24 <= call["max_new_tokens"] <= 128 for call in model.calls)


def test_token_budget_ignores_padding():
    inputs = _Inputs(["one", "one two three four five six"])
    budget = service._translation_token_budget(inputs.input_ids, inputs.attention_mask)
    assert budget == 24


def test_numeric_and_alphanumeric_entities_are_protected_and_restored():
    protected, entities = service._protect_translation_entities(
        "Room C34 opens at 08:30 and release 4.0 uses 15%."
    )
    assert "C34" not in protected
    assert "08:30" not in protected
    assert "4.0" not in protected
    assert "15%" not in protected
    assert [value for _, value in entities] == ["C34", "08:30", "4.0", "15%"]

    translated = protected.lower()
    assert service._restore_translation_entities(translated, entities) == (
        "Room C34 opens at 08:30 and release 4.0 uses 15%.".lower()
        .replace("c34", "C34")
    )


def test_entity_restoration_tolerates_marker_spacing_and_punctuation():
    protected, entities = service._protect_translation_entities("Discount is 12%.")
    mutated = protected.replace("ZXQTLENTITY0Q", "ZXQTL ENTITY-0 Q")
    assert service._restore_translation_entities(mutated, entities) == "Discount is 12%."


def test_glossary_with_number_is_protected_as_one_term():
    glossary = [{"source_text": "Building H3", "translated_text": "Building H3"}]
    protected, glossary_entities = service._protect_glossary_entities(
        "Building H3 is open.", glossary,
    )
    numeric_protected, numeric_entities = service._protect_translation_entities(protected)
    assert "ZXQTLGLOSSARY0Q" in numeric_protected
    assert numeric_entities == []
    assert service._restore_glossary_entities(numeric_protected, glossary_entities) == (
        "Building H3 is open."
    )


def test_unresolved_internal_placeholder_is_a_quality_issue():
    issues = service._translation_quality_issues(
        "Discount 12%.", "Discount ZXQTL ENTITY 0 Q.",
        "eng_Latn", "vie_Latn", [],
    )
    assert "unresolved_placeholder" in issues


def test_nllb_round_trip_preserves_codes_without_increasing_global_beam():
    tokenizer, model = _Tokenizer(), _Model()
    with patch.object(service, "_get_nllb", return_value=(model, tokenizer)), \
         patch.object(service.settings, "TRANSLATION_BEAM_SIZE", 1):
        translated = service._translate_nllb(
            "Building H3 recorded 18 kWh.", "eng_Latn", "vie_Latn"
        )

    assert "H3" in translated
    assert "18" in translated
    assert model.calls[0]["num_beams"] == 1
    assert model.calls[0]["use_cache"] is True


def test_nllb_protects_approved_glossary_target():
    tokenizer, model = _Tokenizer(), _Model()
    glossary = [{
        "source_text": "Trường Đại học Phenikaa",
        "translated_text": "Phenikaa University",
        "source_lang": "vi",
        "target_lang": "en",
    }]
    with patch.object(service, "_get_nllb", return_value=(model, tokenizer)):
        translated, warnings, retried = service._translate_nllb_with_quality(
            "Tôi học tại Trường Đại học Phenikaa.",
            "vie_Latn", "eng_Latn", glossary,
        )

    assert "Phenikaa University" in translated
    assert "Trường Đại học Phenikaa" not in tokenizer.calls[0][0]
    assert warnings == []
    assert retried is False


def test_missing_negation_triggers_bounded_quality_retry():
    tokenizer, model = _Tokenizer(), _Model()
    with patch.object(service, "_get_nllb", return_value=(model, tokenizer)), \
         patch.object(service.settings, "TRANSLATION_BEAM_SIZE", 1), \
         patch.object(service.settings, "TRANSLATION_RETRY_BEAM_SIZE", 3):
        _translated, warnings, retried = service._translate_nllb_with_quality(
            "Tôi không đồng ý.", "vie_Latn", "eng_Latn",
        )

    assert retried is True
    assert "missing_negation" in warnings
    assert [call["num_beams"] for call in model.calls] == [1, 3]
