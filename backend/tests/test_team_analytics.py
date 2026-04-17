"""Team season stats must count distinct matches, not sum over player rows."""

from fastapi.testclient import TestClient

from .conftest import auth_headers, login_and_get_token


def test_team_stats_games_is_distinct_matches_not_player_rows(client: TestClient):
    """
    After one match with stats for multiple players, `games` on team-stats
    must be 1, not the number of player-stat rows.
    """
    coach = login_and_get_token(client, "coach@demo.local", "coach")
    assistant = login_and_get_token(client, "assistant@demo.local", "assistant")

    assert client.post("/matches/1/start", headers=auth_headers(coach)).status_code == 200
    roster = client.get("/matches/1/roster-with-stats", headers=auth_headers(assistant)).json()
    assert len(roster) >= 2

    # Two different players get events -> two stat rows, same match
    for pid in (roster[0]["player_id"], roster[1]["player_id"]):
        r = client.post(
            "/matches/1/events",
            json={
                "player_id": pid,
                "event_type": "pass",
                "delta": 1,
                "half": 1,
                "second_in_match": 10,
            },
            headers=auth_headers(assistant),
        )
        assert r.status_code == 200, r.text

    res = client.get("/seasons/1/team-stats", headers=auth_headers(coach))
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["games"] == 1, "games should be distinct match count, not player rows"
    assert data["season_matches_total"] >= 1
    assert "season_matches_total" in data


def test_team_matches_breakdown_one_row_per_match(client: TestClient):
    coach = login_and_get_token(client, "coach@demo.local", "coach")
    res = client.get("/seasons/1/team-matches-breakdown", headers=auth_headers(coach))
    assert res.status_code == 200
    rows = res.json()
    ids = [r["match_id"] for r in rows]
    assert len(ids) == len(set(ids)), "breakdown must be one row per match"
