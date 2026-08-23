import io
from unittest.mock import patch


def _upload(client, workspace_id, headers, filename, content: bytes):
    return client.post(
        f"/workspaces/{workspace_id}/documents",
        headers=headers,
        files={"file": (filename, io.BytesIO(content), "text/plain")},
    )


def test_chat_answers_using_retrieved_context_with_mocked_llm(
    client, make_user, make_workspace
):
    user = make_user("rag-chat")
    workspace = make_workspace(user)

    _upload(
        client,
        workspace["id"],
        user["headers"],
        "policy.txt",
        b"Employees get 25 vacation days per year.",
    )

    with patch(
        "app.services.rag_service.ask_llm",
        return_value="Employees get 25 vacation days per year.",
    ) as mocked_ask_llm:
        response = client.post(
            "/assistant/chat",
            json={
                "workspace_id": workspace["id"],
                "question": "How many vacation days do employees get?",
            },
            headers=user["headers"],
        )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Employees get 25 vacation days per year."
    assert len(body["sources"]) >= 1
    assert body["sources"][0]["document_name"] == "policy.txt"
    mocked_ask_llm.assert_called_once()


def test_chat_with_no_documents_short_circuits_without_calling_llm(
    client, make_user, make_workspace
):
    user = make_user("rag-empty")
    workspace = make_workspace(user)

    with patch("app.services.rag_service.ask_llm") as mocked_ask_llm:
        response = client.post(
            "/assistant/chat",
            json={
                "workspace_id": workspace["id"],
                "question": "What is our refund policy?",
            },
            headers=user["headers"],
        )

    assert response.status_code == 200
    body = response.json()
    assert body["sources"] == []
    mocked_ask_llm.assert_not_called()


def test_chat_returns_conversation_id_for_history(client, make_user, make_workspace):
    user = make_user("rag-history")
    workspace = make_workspace(user)

    with patch("app.services.rag_service.ask_llm", return_value="mocked answer"):
        response = client.post(
            "/assistant/chat",
            json={
                "workspace_id": workspace["id"],
                "question": "Any question at all.",
            },
            headers=user["headers"],
        )

    assert response.status_code == 200
    assert response.json()["conversation_id"]


def test_other_user_cannot_chat_in_foreign_workspace(
    client, make_user, make_workspace
):
    owner = make_user("rag-owner")
    outsider = make_user("rag-outsider")
    workspace = make_workspace(owner)

    response = client.post(
        "/assistant/chat",
        json={
            "workspace_id": workspace["id"],
            "question": "Anything?",
        },
        headers=outsider["headers"],
    )

    assert response.status_code == 403


def test_chat_with_empty_question_is_rejected(client, make_user, make_workspace):
    user = make_user("rag-empty-question")
    workspace = make_workspace(user)

    response = client.post(
        "/assistant/chat",
        json={"workspace_id": workspace["id"], "question": "   "},
        headers=user["headers"],
    )

    assert response.status_code == 422
