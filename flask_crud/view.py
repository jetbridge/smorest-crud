from typing import Iterable
from flask.views import MethodView
from flask_rest_api import abort
from flask_sqlalchemy import BaseQuery, Model, SQLAlchemy
from sqlalchemy.orm import RelationshipProperty, joinedload
from functools import reduce
from flask_crud import _crud


class CRUDView(MethodView):
    """Base class for collection and resource views."""

    # define these, please
    model: Model

    def query(self) -> BaseQuery:
        return self._get_model().query

    def _get_model(self) -> Model:
        """Return model class this API is using."""
        if self.model:
            return self.model
        # otherwise... sorry
        raise Exception(f"no model class exists on {self}")

    @property
    def _db(self) -> SQLAlchemy:
        """For laziness."""
        return _crud.db


class CollectionView(CRUDView):
    """API view that can manage listing items in a collection or creating a new item.

    """

    create_enabled: bool = False
    list_enabled: bool = False

    prefetch: Iterable[RelationshipProperty] = []

    def get(self) -> BaseQuery:
        """List collection."""
        if not self.list_enabled:
            abort(405)

        query = self.query()
        # TODO: access check (in the form of a query filter)

        query = self._add_prefetch(query)

        return query

    def post(self, args=None):
        """Create new model."""
        if not self.create_enabled:
            abort(405)

        # TODO: access check

        # create
        item = self.model(**args)
        self._db.session.add(item)

        self._db.session.commit()
        return item

    def _add_prefetch(self, query: BaseQuery) -> BaseQuery:
        if self.prefetch:
            # apply joinedloaded rels
            for rels in self.prefetch:
                if is_listy(rels):
                    # list/tuple, construct chain of joinedloads
                    if len(rels) > 1:
                        opts = reduce(
                            lambda o, r: o.joinedload(r), rels[1:], joinedload(rels[0])
                        )
                    else:
                        opts = joinedload(rels[0])
                else:
                    # just a single relationship (not chained)
                    opts = joinedload(rels)

                query = query.options(opts)
        return query


class ResourceView(CRUDView):
    get_enabled: bool = True  # enabled by default
    update_enabled: bool = False
    delete_enabled: bool = False

    def _lookup(self, pk):
        """Get model by primary key."""
        item = self.model.query.get_or_404(pk)
        return item

    def get(self, pk) -> BaseQuery:
        if not self.get_enabled:
            abort(405)

        item = self._lookup(pk)
        # TODO: access check

        return item

    def patch(self, args=None, pk=None) -> BaseQuery:
        if not self.update_enabled:
            abort(405)

        if not pk:
            raise Exception("pk not passed to patch()")

        item = self._lookup(pk)
        # TODO: access check

        update_attrs(item, **args)
        self._db.session.commit()
        return item

    def delete(self, pk) -> BaseQuery:
        if not self.delete_enabled:
            abort(405)

        item = self._lookup(pk)
        # TODO: access check

        self._db.session.delete(item)
        self._db.session.commit()


def update_attrs(item, **kwargs):
    """Set a dictionary of attributes."""
    for attr, value in kwargs.items():
        if hasattr(item, attr):
            setattr(item, attr, value)


def is_listy(thing) -> bool:
    t = type(thing)
    return t is list or t is tuple or t is set
