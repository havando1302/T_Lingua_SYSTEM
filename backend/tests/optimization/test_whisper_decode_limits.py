from app.ai.torch_whisper_adapter import max_decode_tokens


def test_short_audio_uses_small_decode_budget():
    assert max_decode_tokens(16000) == 32
    assert max_decode_tokens(32000) == 32


def test_decode_budget_scales_with_audio_duration():
    assert max_decode_tokens(5 * 16000) == 56
    assert max_decode_tokens(15 * 16000) == 136


def test_decode_budget_keeps_production_upper_bound():
    assert max_decode_tokens(30 * 16000) == 224
    assert max_decode_tokens(60 * 16000) == 224
