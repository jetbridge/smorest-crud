from flask.testing import FlaskClient


def test_endpoints(client: FlaskClient, pets):
    res = client.get("/pets")
    assert res.status_code == 200
