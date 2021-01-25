from unittest.mock import patch

import pytest
from flask.testing import FlaskClient

from smorest_crud import get_for_current_user_or_404, query_for_current_user
from smorest_crud.test.app import Car


def test_create(client: FlaskClient, client_unauthenticated: FlaskClient):
    res = client.post(f"/human", json={"name": "mischa"})
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


def test_get_for_user_or_404(car_factory, db):
    car_1, car_2 = car_factory.create_batch(2)
    db.session.add_all([car_1, car_2])
    db.session.commit()

    # getting instance with success
    car = Car.get_for_user_or_404(car_1.owner, car_1.id)
    assert car
    assert car == car_1

    car = Car.get_for_user_or_404(car_2.owner, car_2.id)
    assert car
    assert car == car_2

    # getting not accessible instance with aborting
    with patch("smorest_crud.access_control.models.abort") as abort_mock:
        car = Car.get_for_user_or_404(car_1.owner, car_2.id)
        assert car is None
        assert abort_mock.called_once_with(404)

    with patch("smorest_crud.access_control.models.abort") as abort_mock:
        car = Car.get_for_user_or_404(car_2.owner, car_1.id)
        assert car is None
        assert abort_mock.called_once_with(404)

    # trying to get not existing instance
    with patch("smorest_crud.access_control.models.abort") as abort_mock:
        car = Car.get_for_user_or_404(car_2.owner, car_2.id + 10)
        assert car is None
        assert abort_mock.called_once_with(404)


def test_get_for_user_or_404_no_attr(car_factory, db, app):
    car = car_factory()
    db.session.add(car)
    db.session.commit()

    # setting not existing column name in extension setup
    app.extensions["crud"].key_attr = "extid"

    # trying to get not existing column
    with pytest.raises(AttributeError) as e:
        Car.get_for_user_or_404(car.owner, car.id)
        assert "extid" in e  # checking column name presents
        assert "Car" in e  # checking class name presents


def test_get_for_current_user_or_404(car_factory, db):
    car_1, car_2 = car_factory.create_batch(2)
    db.session.add_all([car_1, car_2])
    db.session.commit()

    # getting instance with success
    with patch(
        "smorest_crud.access_control.utils._get_current_user"
    ) as get_current_user_mock:
        get_current_user_mock.return_value = car_1.owner
        car = get_for_current_user_or_404(Car, car_1.id)
        assert car
        assert car == car_1

    with patch(
        "smorest_crud.access_control.utils._get_current_user"
    ) as get_current_user_mock:
        get_current_user_mock.return_value = car_2.owner
        car = get_for_current_user_or_404(Car, car_2.id)
        assert car
        assert car == car_2

    # getting not accessible instance with aborting
    with patch(
        "smorest_crud.access_control.utils._get_current_user"
    ) as get_current_user_mock, patch(
        "smorest_crud.access_control.models.abort"
    ) as abort_mock:
        get_current_user_mock.return_value = car_2.owner
        car = get_for_current_user_or_404(Car, car_1.id)
        assert car is None
        assert abort_mock.called_once_with(404)

    with patch(
        "smorest_crud.access_control.utils._get_current_user"
    ) as get_current_user_mock, patch(
        "smorest_crud.access_control.models.abort"
    ) as abort_mock:
        get_current_user_mock.return_value = car_1.owner
        car = get_for_current_user_or_404(Car, car_2.id)
        assert car is None
        assert abort_mock.called_once_with(404)

    # trying to get not existing instance
    with patch(
        "smorest_crud.access_control.utils._get_current_user"
    ) as get_current_user_mock, patch(
        "smorest_crud.access_control.models.abort"
    ) as abort_mock:
        get_current_user_mock.return_value = car_1.owner
        car = get_for_current_user_or_404(Car, car_1.id + 10)
        assert car is None
        assert abort_mock.called_once_with(404)


def test_get_for_current_user_or_404_no_attr(car_factory, db, app):
    car = car_factory()
    db.session.add(car)
    db.session.commit()

    # setting not existing column name in extension setup
    app.extensions["crud"].key_attr = "extid"

    # trying to get not existing column
    with pytest.raises(AttributeError) as e, patch(
        "smorest_crud.access_control.utils._get_current_user"
    ) as get_current_user_mock:
        get_current_user_mock.return_value = car.owner
        get_for_current_user_or_404(Car, car.id)
        assert "extid" in e  # checking column name presents
        assert "Car" in e  # checking class name presents


def test_query_for_current_user(car_factory, db, human_factory):
    car_1, car_2 = car_factory.create_batch(2)
    db.session.add_all([car_1, car_2])
    db.session.commit()

    # success
    with patch(
        "smorest_crud.access_control.utils._get_current_user"
    ) as get_current_user_mock:
        get_current_user_mock.return_value = car_1.owner
        car = query_for_current_user(Car).all()
        assert len(car) == 1
        assert car[0] == car_1

        get_current_user_mock.return_value = car_2.owner
        car = query_for_current_user(Car).all()
        assert len(car) == 1
        assert car[0] == car_2

    # failure
    fake_human = human_factory()
    db.session.add(fake_human)
    db.session.commit()
    with patch(
        "smorest_crud.access_control.utils._get_current_user"
    ) as get_current_user_mock:
        get_current_user_mock.return_value = fake_human
        car = query_for_current_user(Car).all()
        assert len(car) == 0
