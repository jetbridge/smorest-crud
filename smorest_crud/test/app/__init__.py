import os
import sqlalchemy as sa
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_smorest import Blueprint, abort
from sqlalchemy import inspect
from flask_smorest import Api
from smorest_crud import CRUD, CollectionView, ResourceView
from smorest_crud.test.db import db
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from smorest_crud import AccessControlUser
from flask_sqlalchemy import BaseQuery
from marshmallow import fields as f, Schema
from jetkit.db.extid import ExtID


class HumanSchema(Schema):
    id = f.Integer(dump_only=True)  # not editable
    extid = f.UUID(dump_only=True)
    name = f.String()
    pets = f.Nested("PetSchemaLite", many=True, exclude=("human",))
    not_allowed = f.String(load_only=True)  # disallowed for create


class PetSchemaLite(Schema):
    id = f.Integer(dump_only=True)  # not editable
    extid =f.UUID(dump_only=True)
    genus = f.String()
    species = f.String()
    human = f.Nested(HumanSchema, exclude=("pets",))


class PetSchema(PetSchemaLite):
    edible = f.Boolean()


class Pet(db.Model, ExtID):  # noqa: T484
    id = Column(Integer, primary_key=True)
    genus = Column(Text)
    species = Column(Text)
    edible = Column(Text)
    human_id = Column(ForeignKey("human.id"))
    human = relationship("Human", back_populates="pets")
    cars = relationship("Car", secondary="human")

    @classmethod
    def query_for_user(cls, user) -> BaseQuery:
        return cls.query


Pet.add_create_uuid_extension_trigger()


class Human(db.Model, AccessControlUser, ExtID):  # noqa: T484
    id = Column(Integer, primary_key=True)
    name = Column(Text)

    pets = relationship("Pet", back_populates="human")
    cars = relationship("Car", back_populates="owner")

    # private
    not_allowed = Column(Text)

    def user_can_write(self, user) -> bool:
        return self.name == user.name

    @classmethod
    def query_for_user(cls, user) -> BaseQuery:
        return cls.query


Human.add_create_uuid_extension_trigger()


class Car(db.Model):  # noqa: T484
    id = Column(Integer, primary_key=True)

    owner_id = Column(ForeignKey("human.id"))
    owner = relationship("Human", back_populates="cars")


debug = bool(os.getenv("DEBUG"))

USER_NAME = "mischa"

DB_CONN = os.getenv(
    "SQLALCHEMY_DATABASE_URI", "postgresql:///smorest_crud_test".lower()
)
DB_OPTS = sa.engine.url.make_url(DB_CONN).translate_connect_args()
DB_VERSION = "11.5"
api = Api()
blp_pet = Blueprint("Pet", __name__, url_prefix="/pet")


@blp_pet.route("")
class PetCollection(CollectionView):
    model = Pet
    prefetch = [Pet.human, (Pet.human, Human.cars)]  # joinedload
    access_checks_enabled = False

    create_enabled = True
    list_enabled = True

    def get(self):
        query = super().get()

        # check prefetch worked
        first = query.first()

        return jsonify(
            {
                "loaded": {
                    "first.human": is_rel_loaded(first, "human"),
                    "first.human.cars": is_rel_loaded(first.human, "cars"),
                }
            }
        )

    @blp_pet.arguments(PetSchema)
    @blp_pet.response(PetSchema)
    def post(self, args):
        return super().post(args)


@blp_pet.route("/<int:pk>")
class PetResource(ResourceView):
    model = Pet

    access_checks_enabled = False
    get_enabled = True
    update_enabled = True
    delete_enabled = True

    @blp_pet.response(PetSchema)
    def get(self, pk):
        f = super().get(pk)
        return f

    @blp_pet.arguments(PetSchema)
    @blp_pet.response(PetSchema)
    def patch(self, args, pk):
        return super().patch(args, pk)

    @blp_pet.response(PetSchema)
    def delete(self, pk):
        return super().delete(pk)


def is_rel_loaded(item, attr_name):
    """Test if a relationship was prefetched."""
    ins = inspect(item)
    # not unloaded aka loaded aka chill
    return attr_name not in ins.unloaded


blp_human = Blueprint("Human", __name__, url_prefix="/human")


@blp_human.route("")
class HumanCollection(CollectionView):
    model = Human

    list_enabled = True
    create_enabled = True

    @blp_human.response(HumanSchema(many=True))
    def get(self):
        f = super().get().all()
        return f

    @blp_human.arguments(HumanSchema)
    @blp_human.response(HumanSchema)
    def post(self, args):
        if "not_allowed" in args:
            abort(403)

        return super().post(args)


@blp_human.route("/<string:pk>")
class HumanResource(ResourceView):
    model = Human

    update_enabled = True
    get_enabled = True

    @blp_human.response(HumanSchema)
    def get(self, pk):
        return super().get(pk)

    @blp_human.arguments(HumanSchema)
    @blp_human.response(HumanSchema)
    def patch(self, args, pk):
        return super().patch(args, pk)


blp_pointless = Blueprint(
    "pointless", "pointless", url_prefix="/pointless", description="No methods allowed"
)


@blp_pointless.route("")
class PointlessCollection(CollectionView):
    model = Car


@blp_pointless.route("/<int:pk>")
class PointlessResource(ResourceView):
    model = Car


def create_app() -> Flask:
    app = Flask("CRUDTest")
    app.config.update(
        OPENAPI_VERSION="3.0.2",
        SQLALCHEMY_DATABASE_URI=DB_CONN,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ECHO=debug,
        CRUD_GET_USER=lambda: Human(name=USER_NAME),
        CRUD_ACCESS_CHECKS_ENABLED=True,
        SECRET_KEY="wnt2die",
        TESTING=True,
    )
    JWTManager(app)
    db.init_app(app)
    api.init_app(app)
    app.register_blueprint(blp_pet)
    api.register_blueprint(blp_human)
    api.register_blueprint(blp_pointless)
    CRUD(app)

    return app
