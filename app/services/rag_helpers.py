import re


MAX_DISPLAYED_CITATIONS = 3
MIN_CITATION_SCORE = 0.25
RELATIVE_CITATION_WINDOW = 0.20

CONTEXTUAL_FOLLOW_UP_PATTERN = re.compile(
    r"\b(it|its|they|them|their|this|that|those|these|same|previous)\b",
    flags=re.IGNORECASE,
)

SHORT_FOLLOW_UP_PATTERN = re.compile(
    r"^(and\b|also\b|what about\b|how about\b|why did\b|why was\b)",
    flags=re.IGNORECASE,
)


def build_retrieval_question(
    *,
    question: str,
    conversation_history: list[dict] | None,
) -> str:
    """Add the previous user turn only when a question is clearly contextual."""

    cleaned_question = question.strip()
    is_contextual = bool(
        CONTEXTUAL_FOLLOW_UP_PATTERN.search(cleaned_question)
        or (
            len(cleaned_question.split()) <= 12
            and SHORT_FOLLOW_UP_PATTERN.search(cleaned_question)
        )
    )

    if len(cleaned_question) > 240 or not is_contextual:
        return cleaned_question

    previous_user_message = next(
        (
            str(message.get("content", "")).strip()
            for message in reversed(conversation_history or [])
            if message.get("role") == "user"
            and str(message.get("content", "")).strip()
        ),
        "",
    )

    if not previous_user_message:
        return cleaned_question

    return (
        f"Previous question: {previous_user_message}\n"
        f"Follow-up question: {cleaned_question}"
    )


def prune_retrieved_chunks(retrieved_chunks: list[dict]) -> list[dict]:
    """Keep a concise, relevant and non-duplicative citation set."""

    unique: list[dict] = []
    seen: set[str] = set()

    for chunk in retrieved_chunks:
        text = str(chunk.get("text") or "").strip()
        metadata = chunk.get("metadata", {}) or {}
        if not text:
            continue
        key = (
            f"{metadata.get('source_file', '')}:"
            f"{metadata.get('chunk_id', chunk.get('id', ''))}:"
            f"{text[:120]}"
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(chunk)

    if not unique:
        return []

    top_score = max(
        (float(chunk.get("score") or 0.0) for chunk in unique),
        default=0.0,
    )
    score_floor = max(MIN_CITATION_SCORE, top_score - RELATIVE_CITATION_WINDOW)
    selected = [
        chunk
        for index, chunk in enumerate(unique)
        if index == 0
        or chunk.get("score") is None
        or float(chunk.get("score") or 0.0) >= score_floor
    ]
    return selected[:MAX_DISPLAYED_CITATIONS]
