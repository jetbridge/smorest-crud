from flask import current_app
from werkzeug.local import LocalProxy
import logging
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from typing import Optional, Callable

log = logging.getLogger(__name__)

# access initialized extension
_crud = LocalProxy(lambda: current_app.extensions["crud"])

config_keys = dict(get_user="CRUD_GET_USER")


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
from smorest_crud.access_control import (
    AccessControlUser,
    AccessControlQuery,
    get_for_current_user_or_404,
    query_for_current_user
)

__all__ = (
    "ResourceView",
    "CollectionView",
    "CRUD",
    "AccessControlUser",
    "AccessControlQuery",
    "get_for_current_user_or_404",
    "query_for_current_user"
)
