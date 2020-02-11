from flask.testing import FlaskClient


def test_create(client: FlaskClient):
    res = client.post(f"/human", json={"name": "fred"})
    assert res.status_code == 200

    # post with data that fails access check
    res = client.post(f"/human", json={"name": "fred", "not_allowed": "privileged"})
    assert res.status_code == 403


def test_update(client: FlaskClient, pets):
    update = {"species": "Canis"}
    res = client.patch(f"/pet/{pets[0].id}", json=update)
    assert res.status_code == 200
    pet = res.json
    assert pet["species"] == "Canis"
