from flask.testing import FlaskClient


def test_list(client: FlaskClient, pets):
    res = client.get("/pet")
    assert res.status_code == 200

    res = res.json
    assert len(res) == 10

    assert res[0]["human"]
    assert res[0]["human"]["name"]


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
    assert pet["species"] == "Canis"


def test_delete(client: FlaskClient, pets):
    res = client.delete(f"/pet/{pets[0].id}")
    assert res.status_code == 200

    res = client.get(f"/pet/{pets[0].id}")
    assert res.status_code == 404

    assert len(client.get("/pet").json) == len(pets) - 1


def test_disallowed(client: FlaskClient, pets):
    assert client.get("/human").status_code == 405
    assert client.post("/human").status_code == 405
    assert client.patch("/human/2").status_code == 405
    assert client.delete("/human/2").status_code == 405
    assert client.get("/human/2").status_code == 200

    # human has get_enabled
    assert client.get("/human/2000").status_code == 404

    # pointless doesn't allow anything
    assert client.get("/pointless/1").status_code == 405
