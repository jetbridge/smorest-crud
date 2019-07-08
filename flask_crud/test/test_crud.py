from flask.testing import FlaskClient
from flask_crud.test.app import USER_NAME


def test_list(client: FlaskClient, pets):
    res = client.get("/human")
    assert res.status_code == 200

    res = res.json
    assert len(res) == 10

    assert res[0]["pets"][0]
    assert res[0]["pets"][0]["genus"]


def test_get(client: FlaskClient, pets, db):
    human = pets[0].human
    human.name = USER_NAME  # for access check
    db.session.commit()

    res = client.get(f"/human/{human.id}")
    assert res.status_code == 200
    human = res.json
    assert "name" in human

    prefetched = client.get(f"/pet").json["loaded"]
    assert prefetched["first.human"], "failed to prefetch rel 'human'"
    assert prefetched[
        "first.human.cars"
    ], "failed to prefetch secondary relationship 'human' -> 'car'"


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


def test_delete(client: FlaskClient, pets, db):
    res = client.delete(f"/pet/{pets[0].id}")
    assert res.status_code == 200

    res = client.get(f"/pet/{pets[0].id}")
    assert res.status_code == 404


def test_disallowed(client: FlaskClient, pets):
    # delete disabled
    assert client.delete("/human/2").status_code == 405

    # human has get_enabled
    assert client.get("/human/2000").status_code == 404

    # pointless doesn't allow anything
    assert client.post("/pointless").status_code == 405
    assert client.patch("/pointless/2").status_code == 405
    assert client.get("/pointless/1").status_code == 405
