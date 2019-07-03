from .app import create_app, db as db_, Pet
import pytest
from pytest_factoryboy import register
import factory
import random
from faker import Factory as FakerFactory

faker: FakerFactory = FakerFactory.create()


@pytest.fixture
def app():
    app = create_app()

    with app.app_context():
        db_.create_all()
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return db_


@pytest.fixture
def pets(pet_factory, db):
    pets = [pet_factory.create() for n in range(10)]
    db.session.add_all(pets)
    db.session.commit()


@register
class PetFactory(factory.Factory):
    class Meta:
        model = Pet

    genus = factory.LazyAttribute(lambda x: faker.name())
    species = factory.LazyAttribute(lambda x: faker.name())
    edible = factory.LazyAttribute(lambda x: random.choice((True, False)))
