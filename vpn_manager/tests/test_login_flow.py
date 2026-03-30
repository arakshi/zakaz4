from fastapi.testclient import TestClient

from main import app


def test_login_redirects_on_success() -> None:
    client = TestClient(app)
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        allow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers.get("location") == "/"


def test_demo_admin_fallback_login() -> None:
    client = TestClient(app)
    response = client.post(
        "/login",
        data={"username": "admin", "password": "any-password-for-demo"},
        allow_redirects=False,
    )
    assert response.status_code == 303
