import re

from app.schemas.evaluation import GroundednessResult

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "source",
    "the",
    "to",
    "with",
}


def score_groundedness(answer: str, contexts: list[str]) -> GroundednessResult:
    answer_tokens = _meaningful_tokens(answer)
    context_tokens = _meaningful_tokens(" ".join(contexts))

    if not answer_tokens:
        return GroundednessResult(score=1.0, explanation="The answer contains no unsupported factual tokens.")

    supported_tokens = answer_tokens.intersection(context_tokens)
    score = len(supported_tokens) / len(answer_tokens)
    unsupported_count = len(answer_tokens.difference(context_tokens))

    return GroundednessResult(
        score=round(score, 4),
        explanation=f"{len(supported_tokens)} supported tokens, {unsupported_count} unsupported tokens.",
    )


def _meaningful_tokens(text: str) -> set[str]:
    tokens = set(TOKEN_PATTERN.findall(text.lower()))
    normalized = set(tokens)
    for token in tokens:
        if token.endswith("s") and len(token) > 3:
            normalized.add(token[:-1])
    return {token for token in normalized if token not in STOP_WORDS and len(token) > 1}

