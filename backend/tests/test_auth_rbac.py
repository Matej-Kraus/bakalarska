from fastapi.testclient import TestClient

from .conftest import auth_headers, login_and_get_token


def test_login_and_me(client: TestClient):
    token = login_and_get_token(client, "coach@demo.local", "coach")
    res = client.get("/auth/me", headers=auth_headers(token))
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "coach@demo.local"
    assert data["role"] == "coach"


def test_players_requires_auth(client: TestClient):
    res = client.get("/players")
    assert res.status_code == 401


def test_assistant_cannot_create_or_delete_player(client: TestClient):
    token = login_and_get_token(client, "assistant@demo.local", "assistant")

    res = client.post(
        "/players",
        json={"first_name": "A", "last_name": "B", "jersey_number": 77, "position": "MF"},
        headers=auth_headers(token),
    )
    assert res.status_code == 403

    # delete (player 1 exists from seed)
    res = client.delete("/players/1", headers=auth_headers(token))
    assert res.status_code == 403

