from smorest_crud.test.app import create_app, DB_OPTS, DB_VERSION, Human, Pet
import pytest
from pytest_factoryboy import register
import factory
import random
from faker import Factory as FakerFactory
from flask_jwt_extended import create_access_token
from pytest_postgresql.factories import DatabaseJanitor

from smorest_crud.test.db import db

faker: FakerFactory = FakerFactory.create()


@pytest.fixture(scope="session")
def database(request):
    """Create a Postgres database for the tests, and drop it when the tests are done."""
    host = DB_OPTS.get("host")
    port = DB_OPTS.get("port")
    user = DB_OPTS.get("username")
    db_name = DB_OPTS["database"]

    with DatabaseJanitor(user, host, port, db_name, DB_VERSION):
        yield


@pytest.fixture(scope="session")
def app(database):
    app = create_app()

    with app.app_context():
        yield app


@pytest.fixture(scope="session")
def _db(app):
    """Provide the transactional fixtures with access to the database via a Flask-SQLAlchemy database connection."""
    from smorest_crud.test.db import db

    # create all tables for test DB
    db.create_all()

    return db


@pytest.fixture(autouse=True)
def session(db_session):
    """Ensure every test is inside a subtransaction giving us a clean slate each test."""
    yield db_session


@pytest.fixture
def client(app, session):
    """Get authenticated HTTP client."""
    client = app.test_client()

    access_token = create_access_token(identity={"id": 1})
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"
    return client


@pytest.fixture
def client_unauthenticated(app):
    return app.test_client()


@pytest.fixture
def pets(pet_factory, db_session):
    pets = [pet_factory.create() for n in range(10)]

    db.session.add_all(pets)
    db.session.commit()
    return pets


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
