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
