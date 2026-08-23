from openai import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    RateLimitError,
)

from app.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    TEMPERATURE,
)


client = OpenAI(
    api_key=OPENAI_API_KEY,
)


def ask_llm(
    prompt: str,
    *,
    system_prompt: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
) -> str:
    """
    Shared LLM client for the AI Solutions Platform.

    All assistants should use this function.
    """

    model = model or OPENAI_MODEL
    temperature = (
        TEMPERATURE
        if temperature is None
        else temperature
    )

    input_messages = []

    if system_prompt:
        input_messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )

    input_messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    def _create_response(include_temperature: bool):
        kwargs = {
            "model": model,
            "input": input_messages,
        }

        if include_temperature:
            kwargs["temperature"] = temperature

        return client.responses.create(**kwargs)

    try:
        try:
            response = _create_response(
                include_temperature=True
            )

        except BadRequestError as error:
            # Some models (e.g. the o1/o3/o4 reasoning models, gpt-5)
            # reject a non-default temperature outright. Rather than
            # hardcoding a model list that will go stale, detect this
            # specific error and retry once without temperature.
            if "temperature" in str(error).lower():
                response = _create_response(
                    include_temperature=False
                )
            else:
                raise

        return response.output_text.strip()

    except AuthenticationError:
        return (
            "Authentication failed. "
            "Please verify your OpenAI API key."
        )

    except RateLimitError:
        return (
            "The OpenAI rate limit has been reached. "
            "Please try again shortly."
        )

    except BadRequestError as error:
        return (
            f"Bad request: {error}"
        )

    except APIConnectionError:
        return (
            "Unable to connect to OpenAI."
        )

    except APIError:
        return (
            "OpenAI returned an internal error."
        )

    except Exception as error:
        return (
            f"Unexpected error: {error}"
        )