from collections.abc import Iterator

from openai import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    RateLimitError,
)

from app.config import OPENAI_API_KEY, OPENAI_MODEL, TEMPERATURE


client = OpenAI(api_key=OPENAI_API_KEY)


def _build_input_messages(
    prompt: str,
    *,
    system_prompt: str | None,
    conversation_history: list[dict] | None,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    for message in conversation_history or []:
        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": prompt.strip()})
    return messages


def _safe_error_message(error: Exception) -> str:
    if isinstance(error, AuthenticationError):
        return (
            "The assistant is not connected right now. Please ask your "
            "workspace administrator to check the AI service."
        )
    if isinstance(error, RateLimitError):
        return "The assistant is busy right now. Please try again shortly."
    if isinstance(error, BadRequestError):
        return "The assistant could not process that question. Please rephrase it."
    if isinstance(error, APIConnectionError):
        return "The assistant could not connect to the AI service. Please try again."
    if isinstance(error, APIError):
        return "The AI service is temporarily unavailable. Please try again shortly."
    return "The assistant could not complete that request. Please try again shortly."


def ask_llm(
    prompt: str,
    *,
    system_prompt: str | None = None,
    conversation_history: list[dict] | None = None,
    model: str | None = None,
    temperature: float | None = None,
) -> str:
    """Generate a complete response while preserving the existing safe UX."""

    selected_model = model or OPENAI_MODEL
    selected_temperature = TEMPERATURE if temperature is None else temperature
    input_messages = _build_input_messages(
        prompt,
        system_prompt=system_prompt,
        conversation_history=conversation_history,
    )

    def create(include_temperature: bool):
        kwargs = {"model": selected_model, "input": input_messages}
        if include_temperature:
            kwargs["temperature"] = selected_temperature
        return client.responses.create(**kwargs)

    try:
        try:
            response = create(include_temperature=True)
        except BadRequestError as error:
            if "temperature" not in str(error).lower():
                raise
            response = create(include_temperature=False)
        return response.output_text.strip()
    except Exception as error:
        return _safe_error_message(error)


def stream_llm(
    prompt: str,
    *,
    system_prompt: str | None = None,
    conversation_history: list[dict] | None = None,
    model: str | None = None,
    temperature: float | None = None,
) -> Iterator[str]:
    """Yield provider deltas; emit the same safe messages on provider failure."""

    selected_model = model or OPENAI_MODEL
    selected_temperature = TEMPERATURE if temperature is None else temperature
    input_messages = _build_input_messages(
        prompt,
        system_prompt=system_prompt,
        conversation_history=conversation_history,
    )

    def iterate(include_temperature: bool) -> Iterator[str]:
        kwargs = {"model": selected_model, "input": input_messages}
        if include_temperature:
            kwargs["temperature"] = selected_temperature
        emitted = False
        with client.responses.stream(**kwargs) as stream:
            for event in stream:
                if event.type == "response.output_text.delta" and event.delta:
                    emitted = True
                    yield str(event.delta)
            if not emitted:
                final_text = stream.get_final_response().output_text.strip()
                if final_text:
                    yield final_text

    try:
        try:
            yield from iterate(include_temperature=True)
        except BadRequestError as error:
            if "temperature" not in str(error).lower():
                raise
            yield from iterate(include_temperature=False)
    except GeneratorExit:
        raise
    except Exception as error:
        yield _safe_error_message(error)
