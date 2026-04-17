"""Tests for lineup save validation and substitution workflow."""

from fastapi.testclient import TestClient

from .conftest import auth_headers, login_and_get_token


def test_lineup_rejects_duplicate_player(client: TestClient):
    """Saving lineup with same player twice should return 400."""
    token = login_and_get_token(client, "coach@demo.local", "coach")
    # Seed creates match 1 with lineup; get one player_id
    roster = client.get("/matches/1/roster", headers=auth_headers(token))
    assert roster.status_code == 200
    players = roster.json()
    assert len(players) >= 1
    pid = players[0]["player_id"]

    # Same player as starter twice (duplicate player_id)
    payload = {
        "items": [
            {"player_id": pid, "jersey_number_match": 1, "role": "starter"},
            {"player_id": pid, "jersey_number_match": 2, "role": "starter"},
        ]
    }
    res = client.put("/matches/1/lineup", json=payload, headers=auth_headers(token))
    assert res.status_code == 400
    assert "duplicate" in res.text.lower()


def test_lineup_rejects_duplicate_jersey(client: TestClient):
    """Saving lineup with same jersey number twice should return 400."""
    token = login_and_get_token(client, "coach@demo.local", "coach")
    editor = client.get("/matches/1/lineup-editor", headers=auth_headers(token))
    assert editor.status_code == 200
    players = editor.json()["players"]
    pids = [p["player_id"] for p in players[:2]]

    payload = {
        "items": [
            {"player_id": pids[0], "jersey_number_match": 10, "role": "starter"},
            {"player_id": pids[1], "jersey_number_match": 10, "role": "sub"},
        ]
    }
    res = client.put("/matches/1/lineup", json=payload, headers=auth_headers(token))
    assert res.status_code == 400
    assert "jersey" in res.text.lower()


def test_substitution_valid(client: TestClient):
    """Start match, then valid substitution returns 200."""
    coach = login_and_get_token(client, "coach@demo.local", "coach")
    res = client.post("/matches/1/start", headers=auth_headers(coach))
    assert res.status_code == 200

    roster = client.get("/matches/1/roster", headers=auth_headers(coach))
    assert roster.status_code == 200
    rows = roster.json()
    starters = [r for r in rows if r["role"] == "starter"]
    subs = [r for r in rows if r["role"] == "sub"]
    assert len(starters) >= 1 and len(subs) >= 1
    player_out_id = starters[0]["player_id"]
    player_in_id = subs[0]["player_id"]

    res = client.post(
        "/matches/1/substitutions",
        json={
            "player_out_id": player_out_id,
            "player_in_id": player_in_id,
            "half": 1,
            "second_in_match": 120,
        },
        headers=auth_headers(coach),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["player_out_id"] == player_out_id and data["player_in_id"] == player_in_id


def test_event_validation_invalid_event_type(client: TestClient):
    """Invalid event_type should return 422 (Pydantic validation)."""
    coach = login_and_get_token(client, "coach@demo.local", "coach")
    client.post("/matches/1/start", headers=auth_headers(coach))
    roster = client.get("/matches/1/roster-with-stats", headers=auth_headers(coach))
    player_id = roster.json()[0]["player_id"]

    res = client.post(
        "/matches/1/events",
        json={
            "player_id": player_id,
            "event_type": "invalid_type",
            "delta": 1,
            "half": 1,
            "second_in_match": 10,
        },
        headers=auth_headers(coach),
    )
    assert res.status_code == 422


def test_event_validation_invalid_delta(client: TestClient):
    """delta other than +1 or -1 should return 422."""
    coach = login_and_get_token(client, "coach@demo.local", "coach")
    client.post("/matches/1/start", headers=auth_headers(coach))
    roster = client.get("/matches/1/roster-with-stats", headers=auth_headers(coach))
    player_id = roster.json()[0]["player_id"]

    res = client.post(
        "/matches/1/events",
        json={
            "player_id": player_id,
            "event_type": "goal",
            "delta": 2,
            "half": 1,
            "second_in_match": 10,
        },
        headers=auth_headers(coach),
    )
    assert res.status_code == 422
