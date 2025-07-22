import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "email, password, status_code",
    [
        ("kot@pes.com", "kotopes", 200),
        ("kot@pes.com", "kot0pes", 409),
        ("pes@kot.com", "pesokot", 200),
        ("abcde", "pesokot", 422),
    ],
)
def test_register_user(email, password, status_code, client: TestClient):
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == status_code


@pytest.mark.parametrize(
    "email, password, status_code",
    [
        ("test@test.com", "test", 200),
        ("test@test.com", "wrong_password", 401),
        ("wrong@person.com", "test", 401),
    ],
)
def test_login_user(email, password, status_code, client: TestClient):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == status_code
