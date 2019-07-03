from flask.views import MethodView
from flask_sqlalchemy import Model, BaseQuery, SQLAlchemy
from marshmallow import Schema
from flask_rest_api import abort
from flask_crud import _crud  # access db through _crud.db


class CRUDView(MethodView):
    """Base class for collection and resource views."""

    # define these, please
    model: Model
    schema: Schema

    def query(self) -> BaseQuery:
        return self._get_model().query

    def _get_model(self):
        """Return model this API is using.

        Defaults to using the schema_class model if model isn't set.
        """
        if self.model:
            return self.model
        if self.schema and hasattr(self.schema.Meta, "model"):
            return self.schema.Meta.model
        # otherwise... sorry
        raise Exception(f"no model class exists on {self}")

    @property
    def _db(self) -> SQLAlchemy:
        """For laziness."""
        return _crud.db


class CollectionView(CRUDView):
    can_create = False
    can_list = False

    def get(self) -> BaseQuery:
        """List collection.

        Should support prefetching."""
        if not self.can_list:
            abort(405)

        # TODO: access check (in the form of a query filter)

        return self.query().all()

    def post(self, args):
        """Create new model."""
        if not self.can_create:
            abort(405)

        # TODO: access check
        item = self.model(**args)
        self._db.session.add(item)
        self._db.commit()
        return item


class ResourceView(CRUDView):
    can_update = False
    can_delete = False

    def _lookup(self, pk):
        item = self.model.query.get_or_404(pk)
        return item

    def get(self, pk) -> BaseQuery:
        item = self._lookup(pk)
        # TODO: access check

        return item

    def patch(self, pk, args) -> BaseQuery:
        if not self.can_update:
            abort(405)

        item = self._lookup(pk)
        # TODO: access check

        update_attrs(item, **args)
        self._db.commit()
        return item

    def delete(self, pk) -> BaseQuery:
        if not self.can_delete:
            abort(405)

        item = self._lookup(pk)
        # TODO: access check

        self._db.delete(item)
        self._db.commit()


def update_attrs(item, **kwargs):
    """Set a dictionary of attributes."""
    for attr, value in kwargs.items():
        if hasattr(item, attr):
            setattr(item, attr, value)
