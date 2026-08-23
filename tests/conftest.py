"""
Shared fixtures for the test suite.

These tests exercise the real FastAPI app against the real Postgres
container from docker-compose.yml (matching the app's own architecture:
raw psycopg2, no ORM, no test-double database) and the real local
embedding model / ChromaDB. Only the OpenAI call is mocked (see
test_assistant_rag.py), since that's the only external network
dependency.

Run `docker compose up -d db` and have a working `.env` (see
.env.example) before running these tests.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


@pytest.fixture
def make_user(client):
    """Factory fixture: registers + logs in a fresh user per call."""

    def _make(prefix: str = "user", password: str = "TestPass123!"):
        email = f"{_unique(prefix)}@example.com"

        register_response = client.post(
            "/auth/register",
            json={
                "email": email,
                "full_name": prefix.capitalize(),
                "password": password,
            },
        )
        assert register_response.status_code == 201, register_response.text

        login_response = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        assert login_response.status_code == 200, login_response.text

        token = login_response.json()["access_token"]

        return {
            "id": register_response.json()["id"],
            "email": email,
            "password": password,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }

    return _make


@pytest.fixture
def make_workspace(client):
    """Factory fixture: creates a workspace owned by the given user."""

    def _make(user: dict, prefix: str = "workspace"):
        payload = {
            "name": _unique(prefix),
            "company_name": "Test Co",
            "industry": "Tech",
            "description": "Workspace created by the test suite.",
            "enabled_modules": ["ai_knowledge_assistant"],
        }

        response = client.post(
            "/workspaces/",
            json=payload,
            headers=user["headers"],
        )
        assert response.status_code == 200, response.text

        return response.json()

    return _make
