from fastapi.testclient import TestClient

from .conftest import auth_headers, login_and_get_token


def test_add_event_updates_roster_stats(client: TestClient):
    coach = login_and_get_token(client, "coach@demo.local", "coach")
    assistant = login_and_get_token(client, "assistant@demo.local", "assistant")

    # Seed creates match 1 in planned state
    res = client.post("/matches/1/start", headers=auth_headers(coach))
    assert res.status_code == 200, res.text

    # Before
    roster_before = client.get("/matches/1/roster-with-stats", headers=auth_headers(assistant))
    assert roster_before.status_code == 200
    rows = roster_before.json()
    assert len(rows) > 0
    player_id = rows[0]["player_id"]
    goals_before = rows[0]["stats"]["goals"]

    # Add goal
    ev = client.post(
        "/matches/1/events",
        json={
            "player_id": player_id,
            "event_type": "goal",
            "delta": 1,
            "half": 1,
            "second_in_match": 10,
        },
        headers=auth_headers(assistant),
    )
    assert ev.status_code == 200, ev.text

    roster_after = client.get("/matches/1/roster-with-stats", headers=auth_headers(assistant))
    assert roster_after.status_code == 200
    rows2 = roster_after.json()
    p2 = next(r for r in rows2 if r["player_id"] == player_id)
    assert p2["stats"]["goals"] == goals_before + 1


def test_events_require_match_live(client: TestClient):
    assistant = login_and_get_token(client, "assistant@demo.local", "assistant")

    roster = client.get("/matches/1/roster-with-stats", headers=auth_headers(assistant))
    player_id = roster.json()[0]["player_id"]

    ev = client.post(
        "/matches/1/events",
        json={
            "player_id": player_id,
            "event_type": "goal",
            "delta": 1,
            "half": 1,
            "second_in_match": 10,
        },
        headers=auth_headers(assistant),
    )
    assert ev.status_code == 400
    assert "not live" in ev.text.lower()

