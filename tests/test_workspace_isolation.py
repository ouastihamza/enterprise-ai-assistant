def test_creator_can_access_own_workspace(client, make_user, make_workspace):
    owner = make_user("ws-owner")
    workspace = make_workspace(owner)

    response = client.get(
        f"/workspaces/{workspace['id']}",
        headers=owner["headers"],
    )

    assert response.status_code == 200
    assert response.json()["id"] == workspace["id"]


def test_other_user_cannot_get_workspace(client, make_user, make_workspace):
    owner = make_user("ws-owner-2")
    other = make_user("ws-outsider")
    workspace = make_workspace(owner)

    response = client.get(
        f"/workspaces/{workspace['id']}",
        headers=other["headers"],
    )

    assert response.status_code == 403


def test_other_user_cannot_update_workspace(client, make_user, make_workspace):
    owner = make_user("ws-owner-3")
    other = make_user("ws-outsider-2")
    workspace = make_workspace(owner)

    response = client.put(
        f"/workspaces/{workspace['id']}",
        json={"description": "hijacked"},
        headers=other["headers"],
    )

    assert response.status_code == 403


def test_other_user_cannot_archive_workspace(client, make_user, make_workspace):
    owner = make_user("ws-owner-4")
    other = make_user("ws-outsider-3")
    workspace = make_workspace(owner)

    response = client.patch(
        f"/workspaces/{workspace['id']}/archive",
        headers=other["headers"],
    )

    assert response.status_code == 403


def test_list_workspaces_only_returns_own(client, make_user, make_workspace):
    user_a = make_user("ws-list-a")
    user_b = make_user("ws-list-b")

    workspace_a = make_workspace(user_a)
    workspace_b = make_workspace(user_b)

    response_a = client.get("/workspaces/", headers=user_a["headers"])
    ids_a = {workspace["id"] for workspace in response_a.json()}

    assert workspace_a["id"] in ids_a
    assert workspace_b["id"] not in ids_a


def test_two_users_creating_identically_named_workspaces_stay_isolated(
    client, make_user
):
    """
    Regression test for a critical bug: workspace creation used to
    deduplicate by name globally, so two different users creating a
    workspace with the same name (e.g. both frontends' hardcoded
    default workspace name) were silently merged into one shared
    workspace and could see each other's data.
    """

    user_a = make_user("dup-name-a")
    user_b = make_user("dup-name-b")

    payload = {
        "name": "company-x-workspace",
        "company_name": "Company X",
        "industry": "General Business",
        "description": "Default workspace.",
        "enabled_modules": ["ai_knowledge_assistant"],
    }

    workspace_a = client.post(
        "/workspaces/", json=payload, headers=user_a["headers"]
    ).json()

    workspace_b = client.post(
        "/workspaces/", json=payload, headers=user_b["headers"]
    ).json()

    assert workspace_a["id"] != workspace_b["id"]

    response_b = client.get(
        f"/workspaces/{workspace_a['id']}",
        headers=user_b["headers"],
    )
    assert response_b.status_code == 403


def test_get_workspace_requires_authentication(client, make_user, make_workspace):
    owner = make_user("ws-owner-noauth")
    workspace = make_workspace(owner)

    response = client.get(f"/workspaces/{workspace['id']}")

    assert response.status_code in (401, 403)


def test_get_nonexistent_workspace_is_404(client, make_user):
    user = make_user("ws-404")

    response = client.get(
        "/workspaces/00000000-0000-0000-0000-000000000000",
        headers=user["headers"],
    )

    assert response.status_code == 404
