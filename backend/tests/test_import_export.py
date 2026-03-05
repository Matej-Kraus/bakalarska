from fastapi.testclient import TestClient

from .conftest import auth_headers, login_and_get_token


def test_export_players_csv(client: TestClient):
    coach = login_and_get_token(client, "coach@demo.local", "coach")
    res = client.get("/export/players.csv", headers=auth_headers(coach))
    assert res.status_code == 200
    text = res.text
    assert text.splitlines()[0].startswith("id,first_name,last_name,jersey_number")


def test_import_players_csv_upserts_by_jersey(client: TestClient):
    coach = login_and_get_token(client, "coach@demo.local", "coach")

    csv_data = (
        "first_name,last_name,jersey_number,position\n"
        "New,Player,50,MF\n"
        "Jan,Novák,1,GK\n"  # update existing player #1 position
    ).encode("utf-8")

    res = client.post(
        "/players/import",
        files={"file": ("players.csv", csv_data, "text/csv")},
        headers=auth_headers(coach),
    )
    assert res.status_code == 200, res.text
    out = res.json()
    assert out["ok"] is True
    assert out["created"] >= 1

    players = client.get("/players", headers=auth_headers(coach)).json()
    jerseys = {p["jersey_number"] for p in players}
    assert 50 in jerseys

