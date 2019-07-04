from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_crud import ResourceView, CRUD, CollectionView
from flask_rest_api import Api, Blueprint
from marshmallow import fields as f, Schema


db = SQLAlchemy()
api = Api()


def create_app() -> Flask:
    app = Flask("CRUDTest")
    app.config.update(
        OPENAPI_VERSION="3.0.2",
        SQLALCHEMY_DATABASE_URI=f"sqlite://",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    api.init_app(app)
    CRUD(app)

    app.register_blueprint(blp)

    return app


class Pet(db.Model):  # noqa: T484
    id = db.Column(db.Integer, primary_key=True)
    genus = db.Column(db.String)
    species = db.Column(db.String)
    edible = db.Column(db.String)


class PetSchemaLite(Schema):
    id = f.Integer(dump_only=True)  # not editable
    genus = f.String()
    species = f.String()


class PetSchema(PetSchemaLite):
    edible = f.Boolean()


blp = Blueprint("pets", "pets", url_prefix="/pet", description="Operations on pets")


@blp.route("")
class PetCollection(CollectionView):
    model = Pet
    schema = PetSchemaLite
    prefetch = ["owners"]  # joinedload

    can_create = True
    can_list = True

    @blp.response(PetSchema(many=True))
    def get(self):
        return super().get()

    @blp.arguments(PetSchema)
    @blp.response(PetSchema)
    def post(self, args):
        return super().post(args)


@blp.route("/<int:pk>")
class PetResource(ResourceView):
    model = Pet
    schema = PetSchema

    can_update = True
    can_delete = True

    @blp.response(PetSchema)
    def get(self, pk):
        return super().get(pk)

    @blp.arguments(PetSchema)
    @blp.response(PetSchema)
    def patch(self, args, pk):
        return super().patch(args, pk)

    @blp.response(PetSchema)
    def delete(self, pk):
        return super().delete(pk)
