"""Content retention regressions independent of specific topic vocabulary."""
from unittest.mock import patch
import torch
from app.services.translation_fidelity import (
    looks_like_english_fragment, reverse_source_scores, select_faithful_candidate,
    select_fragment_repair, vietnamese_aspect_variants,
)
from app.services import translation_service as service


def test_selects_fuller_candidate_when_source_likelihood_improves_materially():
    choices = ["The second truck arrived safely.", "The second truck arrived at the warehouse safely."]
    assert select_faithful_candidate(choices, [-.27, -.30], [-2.35, -1.46], [(False,), (False,)]) == 1


def test_small_reverse_gain_does_not_rewrite_tense_or_shorten_output():
    choices = ["The server cannot save data.", "The server could not save data.", "It failed."]
    assert select_faithful_candidate(choices, [-.18, -.20, -.21], [-1, -.94, -.3], [(False,)]*3) == 0


def test_moderate_reverse_gain_does_not_rephrase_an_already_complete_sentence():
    choices = ["The bread is delicious.", "The bread was delicious."]
    assert select_faithful_candidate(choices, [-.39, -.42], [-.88, -.57], [(False,)] * 2) == 0


def test_large_reverse_gain_can_recover_a_missing_source_phrase():
    choices = ["The second truck arrived safely.", "The second truck arrived safely at the warehouse."]
    assert select_faithful_candidate(choices, [-.27, -.30], [-1.85, -.72], [(False,)] * 2) == 1


def test_detects_only_conservative_english_noun_phrase_fragments():
    assert looks_like_english_fragment("The first truck to the safe house.")
    assert not looks_like_english_fragment("The first truck arrived at the warehouse safely.")
    assert not looks_like_english_fragment("I want to go out.")
    assert not looks_like_english_fragment("Go to the warehouse.")


def test_aspect_variants_are_bounded_and_do_not_rewrite_existing_aspect():
    variants = vietnamese_aspect_variants("Xe tải thứ nhất đến kho an toàn.")
    assert "Xe tải thứ nhất đã đến kho an toàn." in variants
    assert vietnamese_aspect_variants("Xe tải đã đến kho an toàn.") == []
    assert vietnamese_aspect_variants(" ".join(["từ"] * 20)) == []


def test_fragment_repair_requires_complete_output_and_large_source_gain():
    choices = ["The first truck to the safe house.",
               "The first truck has arrived safely.",
               "The first truck has arrived safely at the warehouse."]
    risks = [(False,)] * 3
    assert select_fragment_repair(choices, [-1.74, -1.40, -.52], risks) == 2
    assert select_fragment_repair(choices, [-1.74, -1.45, -1.40], risks) == 0


def test_fragment_repair_prefers_retaining_more_supported_source_structure():
    choices = ["The first truck to the safe house.",
               "First truck to the warehouse is safe.",
               "The first truck has arrived safely at the warehouse."]
    assert select_fragment_repair(choices, [-1.74, -.30, -.52], [(False,)] * 3) == 2


def test_numeric_and_negation_safety_take_precedence_over_model_scores():
    choices = ["Send 16 items.", "Do not send 15 items."]
    assert select_faithful_candidate(choices, [-.1, -.4], [-.1, -2],
                                    [service._quality_risk(["missing_number_or_code", "missing_negation"]),
                                     service._quality_risk([])]) == 1


def test_long_unpunctuated_input_is_split_without_word_loss():
    original = " ".join(f"word{i}" for i in range(241))
    segments = service._split_translation_segments(original)
    assert " ".join(segments) == original
    assert max(len(segment.split()) for segment in segments) <= 80
    assert service._translation_token_budget(torch.ones((1, 180))) > 128


def test_masked_retry_failure_keeps_the_safe_natural_translation():
    with patch.object(service, "_translate_nllb_candidate", side_effect=[
        ("The shop is open.", [("marker", "shop", "approved shop")]), RuntimeError("fragment Q"),
    ]):
        result, issues, retried = service._translate_nllb_with_quality("The shop is open.", "eng_Latn", "vie_Latn", [])
    assert result == "The shop is open."
    assert "constraint_retry_failed" in issues and retried


def test_reverse_scoring_restores_tokenizer_language_after_failure():
    class Tokenizer:
        src_lang = "vie_Latn"
        tgt_lang = "eng_Latn"
        def __call__(self, *args, **kwargs):
            raise ValueError("synthetic failure")
    tokenizer = Tokenizer()
    try:
        reverse_source_scores(None, tokenizer, "source", ["first candidate", "second option"], "vie_Latn", "eng_Latn", "cpu")
    except ValueError:
        pass
    assert tokenizer.src_lang == "vie_Latn" and tokenizer.tgt_lang == "eng_Latn"


def test_reverse_scoring_keeps_language_tokens_in_decoder_context():
    from types import SimpleNamespace
    class Inputs(dict):
        def to(self, device):
            return self
    class Tokenizer:
        src_lang, tgt_lang = "vie_Latn", "eng_Latn"
        all_special_ids = [0, 1, 2]
        def __call__(self, batch, **kwargs):
            assert (self.src_lang, self.tgt_lang) == ("eng_Latn", "vie_Latn")
            return Inputs(input_ids=torch.tensor([[2, 3, 1]] * len(batch)),
                          labels=torch.tensor([[2, 3, 4, 1]] * len(batch)))
    class Model:
        config = SimpleNamespace(pad_token_id=0, decoder_start_token_id=1)
        def __call__(self, **kwargs):
            assert kwargs["decoder_input_ids"].tolist() == [[1, 2, 3, 4]] * 2
            assert "labels" not in kwargs
            return SimpleNamespace(logits=torch.zeros(2, 4, 6))
    tokenizer = Tokenizer()
    scores = reverse_source_scores(Model(), tokenizer, "source", ["first candidate", "second option"],
                                   "vie_Latn", "eng_Latn", "cpu")
    assert torch.allclose(torch.tensor(scores), torch.full((2,), -torch.log(torch.tensor(6.))))
    assert (tokenizer.src_lang, tokenizer.tgt_lang) == ("vie_Latn", "eng_Latn")


def test_final_chua_question_does_not_demand_an_english_negation():
    assert "missing_negation" not in service._translation_quality_issues(
        "Bạn cảm thấy bình tĩnh hơn chưa?", "Are you feeling calmer yet?", "vie_Latn", "eng_Latn", [],
    )
    assert "missing_negation" in service._translation_quality_issues(
        "Bạn chưa uống thuốc.", "You took the medicine.", "vie_Latn", "eng_Latn", [],
    )
