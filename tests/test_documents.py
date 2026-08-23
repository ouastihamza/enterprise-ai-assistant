import io


def _upload(client, workspace_id, headers, filename, content: bytes):
    return client.post(
        f"/workspaces/{workspace_id}/documents",
        headers=headers,
        files={"file": (filename, io.BytesIO(content), "text/plain")},
    )


def test_upload_valid_document_is_indexed(client, make_user, make_workspace):
    user = make_user("doc-upload")
    workspace = make_workspace(user)

    response = _upload(
        client,
        workspace["id"],
        user["headers"],
        "notes.txt",
        b"The launch code is PINEAPPLE99.",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "notes.txt"
    assert body["indexed"] is True
    assert body["chunk_count"] >= 1


def test_upload_duplicate_filename_is_rejected(client, make_user, make_workspace):
    user = make_user("doc-dup")
    workspace = make_workspace(user)

    first = _upload(
        client, workspace["id"], user["headers"], "dup.txt", b"first version"
    )
    assert first.status_code == 201

    second = _upload(
        client, workspace["id"], user["headers"], "dup.txt", b"second version"
    )
    assert second.status_code == 409


def test_upload_unsupported_file_type_is_rejected(client, make_user, make_workspace):
    user = make_user("doc-bad-type")
    workspace = make_workspace(user)

    response = _upload(
        client, workspace["id"], user["headers"], "malware.exe", b"binary content"
    )

    assert response.status_code == 422


def test_upload_empty_file_is_rejected(client, make_user, make_workspace):
    user = make_user("doc-empty")
    workspace = make_workspace(user)

    response = _upload(client, workspace["id"], user["headers"], "empty.txt", b"")

    assert response.status_code == 422


def test_list_documents_returns_uploaded_document(client, make_user, make_workspace):
    user = make_user("doc-list")
    workspace = make_workspace(user)

    _upload(client, workspace["id"], user["headers"], "listed.txt", b"some content")

    response = client.get(
        f"/workspaces/{workspace['id']}/documents",
        headers=user["headers"],
    )

    assert response.status_code == 200
    names = [document["name"] for document in response.json()]
    assert "listed.txt" in names


def test_other_user_cannot_upload_to_foreign_workspace(
    client, make_user, make_workspace
):
    owner = make_user("doc-owner")
    outsider = make_user("doc-outsider")
    workspace = make_workspace(owner)

    response = _upload(
        client, workspace["id"], outsider["headers"], "intrusion.txt", b"content"
    )

    assert response.status_code == 403


def test_other_user_cannot_list_foreign_workspace_documents(
    client, make_user, make_workspace
):
    owner = make_user("doc-owner-2")
    outsider = make_user("doc-outsider-2")
    workspace = make_workspace(owner)

    response = client.get(
        f"/workspaces/{workspace['id']}/documents",
        headers=outsider["headers"],
    )

    assert response.status_code == 403


def test_delete_document_removes_it_from_registry(client, make_user, make_workspace):
    user = make_user("doc-delete")
    workspace = make_workspace(user)

    upload_response = _upload(
        client, workspace["id"], user["headers"], "to-delete.txt", b"content"
    )
    document_id = upload_response.json()["id"]

    delete_response = client.delete(
        f"/workspaces/{workspace['id']}/documents/{document_id}",
        headers=user["headers"],
    )
    assert delete_response.status_code == 204

    list_response = client.get(
        f"/workspaces/{workspace['id']}/documents",
        headers=user["headers"],
    )
    ids = [document["id"] for document in list_response.json()]
    assert document_id not in ids


def test_deleted_document_is_no_longer_retrievable_by_the_assistant(
    client, make_user, make_workspace
):
    """
    Regression test for a critical bug: deleting a document used to
    leave its vectors in ChromaDB, so it stayed fully searchable and
    citable by the assistant after "deletion".
    """

    user = make_user("doc-delete-vectors")
    workspace = make_workspace(user)

    upload_response = _upload(
        client,
        workspace["id"],
        user["headers"],
        "secret.txt",
        b"The secret code is WATERMELON7.",
    )
    document_id = upload_response.json()["id"]

    client.delete(
        f"/workspaces/{workspace['id']}/documents/{document_id}",
        headers=user["headers"],
    )

    chat_response = client.post(
        "/assistant/chat",
        json={
            "workspace_id": workspace["id"],
            "question": "What is the secret code?",
        },
        headers=user["headers"],
    )

    assert chat_response.status_code == 200
    assert chat_response.json()["sources"] == []


def test_delete_nonexistent_document_is_404(client, make_user, make_workspace):
    user = make_user("doc-delete-404")
    workspace = make_workspace(user)

    response = client.delete(
        f"/workspaces/{workspace['id']}/documents/999999999",
        headers=user["headers"],
    )

    assert response.status_code == 404
