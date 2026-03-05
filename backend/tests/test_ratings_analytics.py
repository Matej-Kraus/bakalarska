from fastapi.testclient import TestClient

from .conftest import auth_headers, login_and_get_token


def test_save_and_list_ratings(client: TestClient):
    coach = login_and_get_token(client, "coach@demo.local", "coach")

    # match 1 has lineup from seed; ratings can only be saved after match is finished
    roster = client.get("/matches/1/roster-with-stats", headers=auth_headers(coach))
    assert roster.status_code == 200
    player_id = roster.json()[0]["player_id"]

    assert client.post("/matches/1/start", headers=auth_headers(coach)).status_code == 200
    assert client.post("/matches/1/finish", headers=auth_headers(coach)).status_code == 200

    res = client.put(
        "/matches/1/ratings",
        json={"items": [{"player_id": player_id, "rating": 8, "note": "Solid"}]},
        headers=auth_headers(coach),
    )
    assert res.status_code == 200, res.text

    res2 = client.get("/matches/1/ratings", headers=auth_headers(coach))
    assert res2.status_code == 200
    rows = res2.json()
    assert rows[0]["player_id"] == player_id
    assert rows[0]["rating"] == 8


def test_leaderboards_and_player_performance(client: TestClient):
    coach = login_and_get_token(client, "coach@demo.local", "coach")
    assistant = login_and_get_token(client, "assistant@demo.local", "assistant")

    # make match live and add one event so stats exist
    assert client.post("/matches/1/start", headers=auth_headers(coach)).status_code == 200
    roster = client.get("/matches/1/roster-with-stats", headers=auth_headers(assistant)).json()
    player_id = roster[0]["player_id"]
    client.post(
        "/matches/1/events",
        json={
            "player_id": player_id,
            "event_type": "goal",
            "delta": 1,
            "half": 1,
            "second_in_match": 5,
        },
        headers=auth_headers(assistant),
    )

    perf = client.get(f"/players/{player_id}/performance?season_id=1", headers=auth_headers(coach))
    assert perf.status_code == 200
    assert isinstance(perf.json(), list)

    lb = client.get("/seasons/1/leaderboards", headers=auth_headers(coach))
    assert lb.status_code == 200
    assert isinstance(lb.json(), list)

