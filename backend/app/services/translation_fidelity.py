"""Conservative n-best selection using reverse source likelihood, not references."""
import math
import re
from collections import Counter


def select_faithful_candidate(candidates, forward_scores, reverse_scores, risks, *, margin=0.50):
    """Never trade a protected fact for a better language-model score.

    Keep the forward winner unless reverse likelihood improves strongly;
    disallow further shortening as an omission remedy. Scores are model
    likelihoods, not calibrated confidence or guarantees of correctness.
    """
    if not candidates:
        raise ValueError("No translation candidates")
    best_risk = min(risks)
    eligible = [i for i, risk in enumerate(risks) if risk == best_risk and candidates[i].strip()]
    if not eligible:
        raise RuntimeError("NLLB returned empty candidates")
    baseline = max(eligible, key=lambda i: forward_scores[i])
    if len(reverse_scores) != len(candidates) or not math.isfinite(reverse_scores[baseline]):
        return baseline
    choices = [i for i in eligible
               if math.isfinite(reverse_scores[i])
               and len(candidates[i].split()) >= len(candidates[baseline].split())
               and forward_scores[i] >= forward_scores[baseline] - 0.3
               and reverse_scores[i] >= reverse_scores[baseline] + margin]
    return max(choices, key=lambda i: forward_scores[i] + reverse_scores[i]) if choices else baseline


_ENGLISH_FINITE = re.compile(
    r"\b(?:am|is|are|was|were|be|been|have|has|had|do|does|did|can|could|may|might|"
    r"must|shall|should|will|would|won't|can't|cannot|\w+ed)\b", re.IGNORECASE,
)
_ENGLISH_NOUN_PHRASE_START = re.compile(
    r"^(?:the|a|an|this|that|these|those|first|second|third|\w+['’]s)\b", re.IGNORECASE,
)


def looks_like_english_fragment(text):
    """Detect a conservative noun-phrase output with no finite predicate."""
    normalized = " ".join(text.strip().split())
    if not normalized or not _ENGLISH_NOUN_PHRASE_START.search(normalized):
        return False
    if _ENGLISH_FINITE.search(normalized):
        return False
    return bool(re.search(r"\b(?:to|at|in|on|for|from|with)\b", normalized, re.IGNORECASE))


def vietnamese_aspect_variants(text, *, max_variants=12):
    """Insert an explicit aspect marker at possible predicate boundaries.

    This is used only after English decoding produced a grammatical fragment;
    candidate selection still scores every repair against the unchanged source.
    """
    words = text.split()
    if len(words) < 3 or len(words) > max_variants + 2 or any(word.casefold() == "đã" for word in words):
        return []
    return [" ".join(words[:position] + ["đã"] + words[position:])
            for position in range(1, min(len(words), max_variants + 1))]


def select_fragment_repair(candidates, reverse_scores, risks, *, margin=0.35):
    """Choose a complete repair only with strong source-likelihood evidence."""
    if not candidates or len(candidates) != len(reverse_scores) or len(candidates) != len(risks):
        return 0
    baseline_words = len(candidates[0].split())
    best_risk = min(risks)
    eligible = [i for i in range(1, len(candidates))
                if risks[i] == best_risk and not looks_like_english_fragment(candidates[i])
                and len(candidates[i].split()) >= baseline_words
                and len(candidates[i].split()) <= baseline_words * 2
                and math.isfinite(reverse_scores[i])
                and reverse_scores[i] >= reverse_scores[0] + margin]
    # A fragment repair exists to recover missing predicates/arguments. Among
    # strongly supported candidates, prefer the one retaining more structure.
    return max(eligible, key=lambda i: (len(candidates[i].split()), reverse_scores[i])) if eligible else 0


def reverse_source_scores(model, tokenizer, source, candidates, source_lang, target_lang, device):
    """Score p(original source | candidate) in small teacher-forced batches.

    Caller holds the shared inference/tokenizer lock. No reference translation
    or training data is consulted, and no second model is loaded.
    """
    import torch
    bags = [Counter(re.findall(r"\w+", value.casefold())) for value in candidates]
    if bags and all(bag == bags[0] for bag in bags[1:]):
        return []  # Punctuation/word-order variants contain the same vocabulary.
    previous_source = tokenizer.src_lang
    previous_target = getattr(tokenizer, "tgt_lang", None)
    result = []
    try:
        tokenizer.src_lang, tokenizer.tgt_lang = target_lang, source_lang
        for start in range(0, len(candidates), 2):
            batch = candidates[start:start + 2]
            inputs = tokenizer(batch, text_target=[source] * len(batch), padding=True,
                               truncation=False, return_tensors="pt").to(device)
            labels = inputs.pop("labels")
            if labels.shape[-1] > 128 or inputs["input_ids"].shape[-1] > 256:
                return []  # Bound teacher-forced vocabulary logits on small GPUs.
            special = torch.tensor(tokenizer.all_special_ids, device=labels.device)
            valid = ~torch.isin(labels, special)
            # Retain language/EOS tokens in the teacher-forcing context; only
            # exclude them from the scored loss, never from decoder inputs.
            decoder_inputs = labels.new_full(labels.shape, model.config.pad_token_id)
            decoder_inputs[:, 0] = model.config.decoder_start_token_id
            decoder_inputs[:, 1:] = labels[:, :-1]
            decoder_inputs.masked_fill_(decoder_inputs == -100, model.config.pad_token_id)
            labels = labels.masked_fill(~valid, -100)
            with torch.inference_mode():
                # Avoid computing vocabulary cross-entropy twice inside HF and
                # here; only this per-example loss is needed for selection.
                logits = model(**inputs, decoder_input_ids=decoder_inputs, use_cache=False).logits
                losses = torch.nn.functional.cross_entropy(logits.float().transpose(1, 2), labels,
                                                          ignore_index=-100, reduction="none")
                result.extend((-(losses * valid).sum(1) / valid.sum(1).clamp(min=1)).cpu().tolist())
            del inputs, labels, logits, losses
        return result
    finally:
        tokenizer.src_lang = previous_source
        tokenizer.tgt_lang = previous_target
