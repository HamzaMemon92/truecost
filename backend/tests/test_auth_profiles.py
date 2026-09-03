from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def isolated_database(tmp_path) -> Iterator[None]:
    test_engine = create_engine(f"sqlite:///{tmp_path / 'auth-test.db'}", connect_args={"check_same_thread": False})
    test_session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    test_engine.dispose()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def register(client: TestClient, email: str, password: str = "a-strong-password") -> dict:
    response = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201, response.text
    return response.json()


def test_register_login_and_me(client: TestClient) -> None:
    tokens = register(client, "person@example.com")
    assert tokens["token_type"] == "bearer"
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "person@example.com"
    login = client.post("/api/v1/auth/login", json={"email": "person@example.com", "password": "a-strong-password"})
    assert login.status_code == 200
    assert login.json()["access_token"] != tokens["access_token"]


def test_duplicate_registration_invalid_login_and_unauthenticated_access(client: TestClient) -> None:
    register(client, "person@example.com")
    assert client.post("/api/v1/auth/register", json={"email": "person@example.com", "password": "a-strong-password"}).status_code == 409
    assert client.post("/api/v1/auth/login", json={"email": "person@example.com", "password": "incorrect-password"}).status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/profiles/me").status_code == 401


def test_tampered_access_token_is_rejected(client: TestClient) -> None:
    tokens = register(client, "tamper@example.com")
    token = tokens["access_token"]
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered}"}).status_code == 401


def test_profile_update_refresh_and_logout(client: TestClient) -> None:
    tokens = register(client, "profile@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    update = client.put("/api/v1/profiles/me", json={"display_name": "Profile User", "preferences": {"currency": "INR"}}, headers=headers)
    assert update.status_code == 200
    assert update.json()["preferences"] == {"currency": "INR"}
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    assert client.post("/api/v1/auth/logout", json={"refresh_token": refreshed.json()["refresh_token"]}).status_code == 204
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": refreshed.json()["refresh_token"]}).status_code == 401


def test_profile_ownership_is_enforced_for_read_and_update(client: TestClient) -> None:
    first = register(client, "first@example.com")
    second = register(client, "second@example.com")
    second_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {second['access_token']}"}).json()
    headers = {"Authorization": f"Bearer {first['access_token']}"}
    assert client.get(f"/api/v1/profiles/{second_me['id']}", headers=headers).status_code == 403
    assert client.put(f"/api/v1/profiles/{second_me['id']}", json={"display_name": "Nope"}, headers=headers).status_code == 403
