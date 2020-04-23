from flask.testing import FlaskClient


def test_create(client: FlaskClient, client_unauthenticated: FlaskClient):
    res = client.post(f"/human", json={"name": "fred"})
    assert res.status_code == 200

    # post with data that fails access check
    res = client.post(f"/human", json={"name": "fred", "not_allowed": "privileged"})
    assert res.status_code == 403

    # endpoint that requires authentication
    res = client_unauthenticated.post(f"/human", json={"name": "fred"})
    assert res.status_code == 401


def test_update(client: FlaskClient, pets):
    update = {"species": "Canis"}
    res = client.patch(f"/pet/{pets[0].id}", json=update)
    assert res.status_code == 200
    pet = res.json
    assert pet["species"] == "Canis"


def test_list_no_acl(client: FlaskClient):
    res = client.get("/human/car")
    assert res.status_code == 200
