from fastapi.testclient import TestClient

from .conftest import auth_headers, login_and_get_token


def test_get_club(client: TestClient):
    token = login_and_get_token(client, "coach@demo.local", "coach")
    res = client.get("/club", headers=auth_headers(token))
    assert res.status_code == 200
    data = res.json()
    assert "name" in data
    assert data["name"] == "Demo Club"
    assert "id" in data


def test_coach_can_update_club(client: TestClient):
    token = login_and_get_token(client, "coach@demo.local", "coach")
    res = client.put(
        "/club",
        headers=auth_headers(token),
        json={
            "name": "FC Demo United",
            "short_name": "FDU",
            "city": "Praha",
            "home_venue": "Test Arena",
            "founded_year": 1995,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["name"] == "FC Demo United"
    assert data["short_name"] == "FDU"
    assert data["city"] == "Praha"


def test_assistant_cannot_update_club(client: TestClient):
    token = login_and_get_token(client, "assistant@demo.local", "assistant")
    res = client.put(
        "/club",
        headers=auth_headers(token),
        json={"name": "Hacked Name"},
    )
    assert res.status_code == 403
