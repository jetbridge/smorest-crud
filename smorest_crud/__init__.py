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
    """A model mixin to implement access checks for a given model/user."""

    @classmethod
    def query_for_user(cls, user: "AccessControlUser") -> Optional[BaseQuery]:
        """Filter list of items for `user`, or None if disallowed."""
        return None

    def user_can_read(self, user: "AccessControlUser") -> bool:
        """Can `user` view this object."""
        return self.user_can_write(user)

    def user_can_write(self, user: "AccessControlUser") -> bool:
        raise NotImplementedError(
            f"user_can_write(self, user) not implemented on {self}"
        )

    def user_can_create(self, user: "AccessControlUser", args: Optional[dict]) -> bool:
        # TODO: not needed right now - maybe can implement if needed
        raise NotImplementedError(
            f"user_can_create(self, user, args) not implemented on {self}"
        )


class CRUD(object):
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
