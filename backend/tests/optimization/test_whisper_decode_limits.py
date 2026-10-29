import pytest
from json import JSONDecodeError
from safetensors import SafetensorError

from app.ai.torch_whisper_adapter import load_cached_first, max_decode_tokens


def test_short_audio_uses_small_decode_budget():
    assert max_decode_tokens(16000) == 32
    assert max_decode_tokens(32000) == 32


def test_decode_budget_scales_with_audio_duration():
    assert max_decode_tokens(5 * 16000) == 56
    assert max_decode_tokens(15 * 16000) == 136


def test_decode_budget_keeps_production_upper_bound():
    assert max_decode_tokens(30 * 16000) == 224
    assert max_decode_tokens(60 * 16000) == 224


class _CorruptThenHealthyLoader:
    calls = []

    @classmethod
    def from_pretrained(cls, model_id, **kwargs):
        cls.calls.append((model_id, kwargs))
        if len(cls.calls) == 1:
            raise SafetensorError("corrupt synthetic cache")
        return "recovered"


def test_corrupt_safetensors_cache_forces_fresh_download():
    _CorruptThenHealthyLoader.calls = []

    result = load_cached_first(
        _CorruptThenHealthyLoader,
        "synthetic/model",
        revision="immutable-revision",
    )

    assert result == "recovered"
    assert _CorruptThenHealthyLoader.calls[0][1]["local_files_only"] is True
    assert _CorruptThenHealthyLoader.calls[1][1]["local_files_only"] is False
    assert _CorruptThenHealthyLoader.calls[1][1]["force_download"] is True


def test_corrupt_cache_stays_offline_when_local_only_is_required():
    _CorruptThenHealthyLoader.calls = []

    with pytest.raises(SafetensorError):
        load_cached_first(
            _CorruptThenHealthyLoader,
            "synthetic/model",
            local_files_only=True,
            revision="immutable-revision",
        )

    assert len(_CorruptThenHealthyLoader.calls) == 1


class _BrokenJsonThenHealthyLoader:
    calls = []

    @classmethod
    def from_pretrained(cls, model_id, **kwargs):
        cls.calls.append((model_id, kwargs))
        if len(cls.calls) == 1:
            raise JSONDecodeError("empty synthetic tokenizer JSON", "", 0)
        return "recovered-tokenizer"


def test_corrupt_tokenizer_json_forces_fresh_download():
    _BrokenJsonThenHealthyLoader.calls = []

    result = load_cached_first(
        _BrokenJsonThenHealthyLoader,
        "synthetic/tokenizer",
        revision="immutable-revision",
    )

    assert result == "recovered-tokenizer"
    assert _BrokenJsonThenHealthyLoader.calls[0][1]["local_files_only"] is True
    assert _BrokenJsonThenHealthyLoader.calls[1][1]["local_files_only"] is False
    assert _BrokenJsonThenHealthyLoader.calls[1][1]["force_download"] is True
