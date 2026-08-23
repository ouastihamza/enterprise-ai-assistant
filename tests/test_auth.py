import uuid


def test_register_returns_new_user(client):
    email = f"auth-register-{uuid.uuid4().hex[:10]}@example.com"

    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "full_name": "Auth Register",
            "password": "TestPass123!",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == email
    assert body["workspace_ids"] == []
    assert body["is_superuser"] is False


def test_register_duplicate_email_is_rejected(client):
    email = f"auth-register-dup-{uuid.uuid4().hex[:10]}@example.com"

    payload = {
        "email": email,
        "full_name": "Dup User",
        "password": "TestPass123!",
    }

    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400


def test_login_with_correct_credentials_returns_token(make_user):
    user = make_user("login-ok")

    assert user["token"]


def test_login_with_wrong_password_is_rejected(client, make_user):
    user = make_user("login-wrong-pw")

    response = client.post(
        "/auth/login",
        json={"email": user["email"], "password": "not-the-password"},
    )

    assert response.status_code == 401


def test_login_with_unknown_email_is_rejected(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "does-not-exist@example.com",
            "password": "whatever",
        },
    )

    assert response.status_code == 401


def test_me_returns_current_user(client, make_user):
    user = make_user("me-user")

    response = client.get("/auth/me", headers=user["headers"])

    assert response.status_code == 200
    assert response.json()["email"] == user["email"]


def test_me_without_token_is_rejected(client):
    response = client.get("/auth/me")

    assert response.status_code in (401, 403)


def test_me_with_garbage_token_is_rejected(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401
