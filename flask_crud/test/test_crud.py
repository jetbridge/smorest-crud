from flask.testing import FlaskClient


def test_list(client: FlaskClient, pets):
    res = client.get("/pets")
    assert res.status_code == 200
    assert len(res.json) == 10


def test_get(client: FlaskClient, pets):
    res = client.get(f"/pets/{pets[0].id}")
    assert res.status_code == 200
    pet = res.json
    assert "edible" in pet


def test_post(client: FlaskClient, pets):
    res = client.post(f"/pets", json={"species": "Felis"})
    assert res.status_code == 200
    pet = res.json
    assert "edible" in pet
