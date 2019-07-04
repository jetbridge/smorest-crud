from flask.testing import FlaskClient


def test_list(client: FlaskClient, pets):
    res = client.get("/pet")
    assert res.status_code == 200
    assert len(res.json) == 10


def test_get(client: FlaskClient, pets):
    res = client.get(f"/pet/{pets[0].id}")
    assert res.status_code == 200
    pet = res.json
    assert "edible" in pet


def test_post(client: FlaskClient, pets):
    res = client.post(f"/pet", json={"species": "Felis"})
    assert res.status_code == 200
    pet = res.json
    assert "edible" in pet


def test_patch(client: FlaskClient, pets):
    update = {"species": "Canis"}
    res = client.patch(f"/pet/{pets[0].id}", json=update)
    assert res.status_code == 200
    pet = res.json
    assert pet['species'] == 'Canis'


def test_delete(client: FlaskClient, pets):
    res = client.delete(f"/pet/{pets[0].id}")
    assert res.status_code == 200

    res = client.get(f"/pet/{pets[0].id}")
    assert res.status_code == 404

    assert len(client.get("/pet").json) == len(pets) - 1
