# Flask Smorest CRUD
_Why repeat yourself?_

# What is this?
Right now, a work in progress.

This library aims to tie together Flask-SQLAlchemy and Flask-Smorest to implement a sane default but easily customizable CRUD API based on SQLAlchemy models inside of Flask.

# Quickstart
In `create_app()`:
```python
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
```

CRUD View:
```python
from flask_smorest import Blueprint
from smorest_crud import ResourceView, CollectionView

pet_blp = Blueprint("pets", "pets", url_prefix="/pet")


@pet_blp.route("")
class PetCollection(CollectionView):
    model = Pet
    prefetch = [Pet.human, (Pet.human, Human.cars)]  # joinedload
    access_checks_enabled = False

    create_enabled = True
    list_enabled = True

    def get(self):
        query = super().get()
        return query.filter_by(name='mischa')

    @pet_blp.arguments(PetSchema)
    @pet_blp.response(PetSchema)
    def post(self, args):
        return super().post(args)


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
```

# Who is this for?
This library is only useful if your application uses:
* [Flask-Smorest](https://flask-smorest.readthedocs.io/en/stable/)
* [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
* [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/en/stable/)


# Where to look?
Look at `smorest_crud/test/app.py`


Feedback and comments welcome. What would you like to see? Open an issue or a PR with your thoughts.
