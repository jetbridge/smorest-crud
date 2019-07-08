from typing import Iterable, Optional
from flask.views import MethodView
from flask_rest_api import abort
from flask_sqlalchemy import BaseQuery, Model, SQLAlchemy
from sqlalchemy.orm import RelationshipProperty, joinedload
from functools import reduce
from flask_crud import _crud, AccessControlUser
import logging

log = logging.getLogger(__name__)

config_keys = dict(get_user="CRUD_GET_USER")


class CRUDView(MethodView):
    """Base class for collection and resource views."""

    # define these, please
    model: Model
    access_checks_enabled: bool = True

    def query(self) -> BaseQuery:
        return self._get_model().query

    def query_for_user(self) -> BaseQuery:
        model_cls = self._get_model()
        if not hasattr(model_cls, 'query_for_user'):
            raise NotImplementedError(f"{model_cls} does not implement query_for_user() and access control checks are enabled")

        user = self._get_current_user()
        # XXX: do we require user?

        query = model_cls.query_for_user(user)

        # assert we got a query back
        if not query:
            self._abort_access_check_failed(model_cls)

        return query

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

    def _get_current_user(self) -> Optional[AccessControlUser]:
        get_user_func = _crud.app.config.get(config_keys["get_user"])
        if not get_user_func:
            return None
        return get_user_func()

    def _access_checks_enabled(self) -> bool:
        return _crud.access_control_enabled and self.access_checks_enabled

    def _abort_access_check_failed(self, model: Model):
        """Abort with HTTP 403 if access control checks failed and log."""
        log.warning(
            f"Access check failed on {model} for user: {self._get_current_user()}"
        )
        abort(403)

    def _check_can(self, check: str, model: Model, *args, **kwargs):
        """Check if current user can do `check` on `model`."""
        if not self._access_checks_enabled():
            return

        user = self._get_current_user()
        if not user:
            self._abort_access_check_failed(model)

        # get check method
        chkmeth = f"user_can_{check}"
        if not hasattr(model, chkmeth):
            raise NotImplementedError(
                f"{chkmeth}() is not implemented on {model} but CRUD access checks are enabled"
            )
        chkmeth_callable = getattr(model, chkmeth)
        # call check method
        if not chkmeth_callable(user, *args, **kwargs):
            self._abort_access_check_failed(model)

    def _check_can_read(self, model: Model):
        return self._check_can("read", model)

    def _check_can_write(self, model: Model):
        return self._check_can("write", model)

    def _check_can_create(self, model: Model, args: Optional[dict]):
        return self._check_can("create", model=model, args=args)


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

        query = self.query_for_user()

        query = self._add_prefetch(query)

        return query

    def post(self, args=None):
        """Create new model."""
        if not self.create_enabled:
            abort(405)

        # create
        item = self.model(**args)

        # access check should be done in subclass (for now)
        # self._check_can_create(item, args=args)

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
    get_enabled: bool = False
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
        self._check_can_read(item)

        return item

    def patch(self, args=None, pk=None) -> BaseQuery:
        if not self.update_enabled:
            abort(405)

        if not pk:
            raise Exception("pk not passed to patch()")

        item = self._lookup(pk)
        self._check_can_write(item)

        update_attrs(item, **args)
        self._db.session.commit()
        return item

    def delete(self, pk) -> BaseQuery:
        if not self.delete_enabled:
            abort(405)

        item = self._lookup(pk)
        self._check_can_write(item)

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
