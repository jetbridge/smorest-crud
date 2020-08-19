from flask import current_app
from werkzeug.local import LocalProxy
import logging
from flask_sqlalchemy import SQLAlchemy, BaseQuery
from flask import Flask
from typing import Optional, Callable

log = logging.getLogger(__name__)

# access initialized extension
_crud = LocalProxy(lambda: current_app.extensions["crud"])


class AccessControlUser:
    """A model mixin to implement access checks for a given model/user.

    Required on all models for views with access checks enabled.

    Example::

        class Pet(Model, AccessControlUser):
            @classmethod
            def query_for_user(cls, user) -> Optional[BaseQuery]:
                return cls.query.filter_by(owner=user)

            def user_can_read(self, user) -> bool:
                return self.user_can_write(user) or self.owner.id == user.id

            def user_can_write(self, user) -> bool:
                return user.is_admin  # only administrators can edit pets
    """

    @classmethod
    def query_for_user(cls, user: "AccessControlUser") -> Optional[BaseQuery]:
        """Filter list of items for `user`, or None if disallowed."""
        return None

    def user_can_read(self, user: "AccessControlUser") -> bool:
        """Check if `user` is allowed to access this object at all.

        Defaults to calling `self.user_can_write(user)`.
        """
        return self.user_can_write(user)

    def user_can_write(self, user: "AccessControlUser") -> bool:
        """Check if `user` can make any modifications to this object (update, delete)."""
        raise NotImplementedError(
            f"user_can_write(self, user) not implemented on {self}"
        )

    def user_can_create(self, user: "AccessControlUser", args: Optional[dict]) -> bool:
        """Check if `user` is allowed to create."""
        return True


class CRUD(object):
    """Flask extension to enable CRUD REST functionality.

    Sample full app configuration::

        from smorest_crud import CRUD
        from flask_jwt_extended import JWTManager, get_current_user

        app = Flask()
        JWTManager(app)
        CRUD(app)

        app.config.update(
            CRUD_GET_USER=get_current_user,
            CRUD_ACCESS_CHECKS_ENABLED=True,
            SECRET_KEY="wnt2die",
        )
    """

    db: SQLAlchemy
    app: Flask
    get_user: Optional[Callable]
    access_control_enabled: bool

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app, identity_handler=None):
        if "sqlalchemy" not in app.extensions:
            raise Exception(
                "Please initialize CRUD after initializing the "
                "Flask-SQLAlchemy extension on your app."
            )

        self.access_control_enabled = app.config.get("CRUD_ACCESS_CHECKS_ENABLED")
        if self.access_control_enabled:
            if "CRUD_GET_USER" in app.config:
                self.get_user = app.config["CRUD_GET_USER"]
            else:
                raise Exception("CRUD_GET_USER not found in configuration")

        # save sqla db object for later
        self.db = app.extensions["sqlalchemy"].db
        # save stuff for later
        self.app = app

        # save for localproxy
        app.extensions["crud"] = self


from smorest_crud.view import ResourceView, CollectionView

__all__ = ("ResourceView", "CollectionView", "CRUD", "AccessControlUser")
