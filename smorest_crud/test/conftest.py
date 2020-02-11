from smorest_crud.test.app import create_app, db as db_
from smorest_crud.test.app.model import Pet, Human
import pytest
from pytest_factoryboy import register
import factory
import random
from faker import Factory as FakerFactory
from flask_jwt_extended import create_access_token

faker: FakerFactory = FakerFactory.create()


@pytest.fixture
def app():
    app = create_app()

    with app.app_context():
        db_.create_all()
        yield app


@pytest.fixture
def client(app):
    """Get authenticated HTTP client."""
    client = app.test_client()
    access_token = create_access_token(identity={"id": 1})
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"
    return client


@pytest.fixture
def client_unauthenticated(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return db_


@pytest.fixture
def pets(pet_factory, db):
    pets = [pet_factory.create() for n in range(10)]
    db.session.add_all(pets)
    db.session.commit()
    yield pets


@register
class HumanFactory(factory.Factory):
    class Meta:
        model = Human

    name = factory.LazyAttribute(lambda x: faker.name())


@register
class PetFactory(factory.Factory):
    class Meta:
        model = Pet

    genus = factory.LazyAttribute(lambda x: faker.name())
    species = factory.LazyAttribute(lambda x: faker.name())
    edible = factory.LazyAttribute(lambda x: random.choice((True, False)))

    human = factory.SubFactory(HumanFactory)
