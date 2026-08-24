from typing import Any


def build_regeneration_context(
    messages: list[dict[str, Any]], limit: int = 10
) -> dict:
    if (
        len(messages) < 2
        or messages[-1].get("role") != "assistant"
        or messages[-2].get("role") != "user"
    ):
        raise ValueError("There is no completed assistant answer to regenerate.")

    previous_messages = messages[:-2][-max(1, min(limit, 100)) :]
    return {
        "assistant_message_id": messages[-1]["id"],
        "question": messages[-2]["content"],
        "conversation_history": [
            {"role": message["role"], "content": message["content"]}
            for message in previous_messages
            if message.get("role") in {"user", "assistant", "system"}
        ],
    }
