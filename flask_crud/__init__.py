from flask import current_app
from werkzeug.local import LocalProxy
import logging
from flask_sqlalchemy import SQLAlchemy

log = logging.getLogger(__name__)

# access initialized extension
_crud = LocalProxy(lambda: current_app.extensions["crud"])


class CRUD(object):
    db: SQLAlchemy

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app, identity_handler=None):
        if "sqlalchemy" not in app.extensions:
            raise Exception(
                "please initialize CRUD after initializing the Flask-SQLAlchemy extension"
            )

        # save sqla db object for later
        self.db = app.extensions["sqlalchemy"].db

        # save for localproxy
        app.extensions["crud"] = self


from flask_crud.view import ResourceView, CollectionView

__all__ = ("ResourceView", "CollectionView")
