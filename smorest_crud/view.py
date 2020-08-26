from typing import Iterable, Optional
from flask.views import MethodView
from flask_smorest import abort
from flask_sqlalchemy import BaseQuery, Model, SQLAlchemy
from sqlalchemy.orm import RelationshipProperty, joinedload
from functools import reduce
from flask_jwt_extended import jwt_required
from smorest_crud import _crud, AccessControlUser
import logging

log = logging.getLogger(__name__)

config_keys = dict(get_user="CRUD_GET_USER")


class CRUDView(MethodView):
    """Base class for collection and resource views.

    This works like `Flask MethodView <https://flask.palletsprojects.com/en/1.1.x/views/#method-views-for-apis>`_;
    python methods are named after HTTP verbs.
    """

    model: Model
    """SQLAlchemy model we are providing CRUD services for."""

    access_checks_enabled: bool = True
    """Whether or not to apply access checks to models.

    Requires `CRUD_ACCESS_CHECKS_ENABLED` configuration to be enabled."""

    decorators = [jwt_required]
    """List of decorators to apply to view functions.

    Applies `jwt_required <https://flask-jwt-extended.readthedocs.io/en/stable/api/#flask_jwt_extended.jwt_required>`_ by default to required authenticated requests.
    """

    def query(self) -> BaseQuery:
        """Return query for `model`."""
        return self._get_model().query

    def query_for_user(self) -> BaseQuery:
        """Produce a query for current model, filtered by `model.query_for_user(current_user)`."""
        model_cls = self._get_model()

        # try to filter the query by current user
        query = model_cls.query
        if hasattr(model_cls, "query_for_user"):
            # filter query by user
            user = self._get_current_user()
            query = model_cls.query_for_user(user)

            # we expect a query back unless check failed
            if not query:
                self._abort_access_check_failed(model_cls)

        elif self._access_checks_enabled():
            # can't filter by user
            raise NotImplementedError(
                f"{model_cls} does not implement query_for_user() and access control checks are enabled"
            )

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

    Example::

        from flask_smorest import Blueprint
        from smorest_crud import CollectionView

        pet_blp = Blueprint("pets", "pets", url_prefix="/pet")

        @pet_blp.route("")
        class PetCollection(CollectionView):
            model = Pet
            prefetch = [Pet.human, (Pet.human, Human.cars)]  # joinedload
            access_checks_enabled = False

            create_enabled = True
            list_enabled = True

            @pet_blp.response(PetSchema(many=True))
            def get(self):
                query = super().get()
                return query.filter_by(name='mischa')

            @pet_blp.arguments(PetSchema)
            @pet_blp.response(PetSchema(many=True))
            def post(self, args):
                return super().post(args)
    """

    list_enabled: bool = False
    """Enable GET."""

    create_enabled: bool = False
    """Enable POST."""

    prefetch: Iterable[RelationshipProperty] = []
    """List of relationships to `prefetch <https://docs.sqlalchemy.org/en/13/orm/loading_relationships.html#relationship-loading-with-loader-options>`_ when listing."""

    def get(self) -> BaseQuery:
        """List collection.

        :returns: query or iterable of `Model`s."""
        if not self.list_enabled:
            abort(405)

        query = self.query_for_user()

        query = self._add_prefetch(query)

        return query

    def post(self, args=None):
        """Create new model.

        :param args: Deserialized schema args.
        :returns: Newly-created model.
        """
        if not self.create_enabled:
            abort(405)

        # create
        item = self.model(**args)

        self._check_can_create(item, args=args)

        self._db.session.add(item)

        self._db.session.commit()
        return item

    def _add_prefetch(self, query: BaseQuery) -> BaseQuery:
        if self.prefetch:
            # apply joinedloaded rels
            for rels in self.prefetch:
                if _is_listy(rels):
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
    """Operations to perform on an item, identified in the URL route by a key.

    GET /pet/42 -- Fetch pet `42`.

    PATCH /pet/42 -- Update pet `42`.

    DELETE /pet/42 -- Delete pet `42`.

    Example::

        from flask_smorest import Blueprint
        from smorest_crud import ResourceView

        pet_blp = Blueprint("pets", "pets", url_prefix="/pet")

        @pet_blp.route("/<int:pk>")
        class PetResource(ResourceView):
            model = Pet

            access_checks_enabled = True
            get_enabled = True
            update_enabled = True
            delete_enabled = True

            @pet_blp.response(PetSchema)
            def get(self, pk):
                return super().get(pk)

            @pet_blp.arguments(PetSchema)
            @pet_blp.response(PetSchema)
            def patch(self, args, pk):
                return super().patch(args, pk)

            @pet_blp.response(PetSchema)
            def delete(self, pk):
                return super().delete(pk)

    """

    get_enabled: bool = False
    """Enable GET."""

    update_enabled: bool = False
    """Enable PATCH."""

    delete_enabled: bool = False
    """Enable DELETE."""

    def _lookup(self, pk):
        """Get model by primary key."""
        item = self.model.query.get_or_404(pk)
        return item

    def get(self, pk) -> BaseQuery:
        """Retreieve model by primary key.

        :param pk: Primary key identifier."""
        if not self.get_enabled:
            abort(405)

        item = self._lookup(pk)
        self._check_can_read(item)

        return item

    def patch(self, args=None, pk=None) -> BaseQuery:
        """Update model.

        :param args: Deserialized request model args.
        :param pk: Primary key identifier.
        :returns: Updated model.
        """
        if not self.update_enabled:
            abort(405)

        if not pk:
            raise Exception("pk not passed to patch()")

        item = self._lookup(pk)
        self._check_can_write(item)

        _update_attrs(item, args)
        self._db.session.commit()
        return item

    def delete(self, pk) -> BaseQuery:
        """Delete model.

        :param pk: Primary key identifier.
        """
        if not self.delete_enabled:
            abort(405)

        item = self._lookup(pk)
        self._check_can_write(item)

        self._db.session.delete(item)
        self._db.session.commit()


def _update_attrs(item, attrs):
    """Set a dictionary of attributes."""
    for attr, value in attrs.items():
        if hasattr(item, attr):
            setattr(item, attr, value)


def _is_listy(thing) -> bool:
    t = type(thing)
    return t is list or t is tuple or t is set
