"""Immutable upstream model revisions approved for inference and training."""
from types import MappingProxyType


PINNED_MODEL_REVISIONS = MappingProxyType({
    "facebook/nllb-200-distilled-600M": "f8d333a098d19b4fd9a8b18f94170487ad3f821d",
    "facebook/nllb-200-distilled-1.3B": "7be3e24664b38ce1cac29b8aeed6911aa0cf0576",
    "openai/whisper-small": "973afd24965f72e36ca33b3055d56a652f456b4d",
    "openai/whisper-large-v3-turbo": "41f01f3fe87f28c78e2fbf8b568835947dd65ed9",
    "openai/whisper-large-v3": "06f233fe06e710322aca913c1bc4249a0d71fce1",
    "facebook/mms-tts-eng": "c71de0fe7204c83f1c10820a7d696d0b450048ba",
    "facebook/mms-tts-vie": "b58928d033932a49aa8e3d6cf11625b25fe928d2",
})


def approved_revision(model_id: str) -> str:
    """Fail closed instead of silently downloading a moving upstream branch."""
    try:
        return PINNED_MODEL_REVISIONS[model_id]
    except KeyError as exc:
        raise ValueError("Model identifier is not in the pinned model registry") from exc
