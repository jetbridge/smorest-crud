from typing import Optional, TypeVar, Type, Generic, Union
from smorest_crud import _crud

from flask_sqlalchemy import BaseQuery, Model
from flask import abort

T = TypeVar("T", bound=Model)


class AccessControlQuery(BaseQuery):
    """Base query class to use for access restriction."""

    def query_for_user(self, user: Type[T]) -> Type["AccessControlQuery"]:
        """Access control query for the given user instance."""
        raise NotImplementedError()


class AccessControlUser(Generic[T]):
    """A model mixin to implement access checks for a given model/user.

    Required on all models for views with access checks enabled.

    Example::

        class PetQuery(AccessControlQuery):
            def query_for_user(self, user) -> "PetQuery":
                return self.filter_by(owner=user)

        class Pet(Model, AccessControlUser):
            query_class = PetQuery

            def user_can_read(self, user) -> bool:
                return self.user_can_write(user) or self.owner.id == user.id

            def user_can_write(self, user) -> bool:
                return user.is_admin  # only administrators can edit pets
    """

    query_class: Type[AccessControlQuery]

    @classmethod
    def query_for_user(cls, user: "AccessControlUser") -> Optional[AccessControlQuery]:
        """Filter list of items for `user`, or None if disallowed."""
        if not hasattr(cls.query, "query_for_user"):
            return None
        return cls.query.query_for_user(user)

    @classmethod
    def get_for_user_or_404(
        cls: Type[Model], user: Type[T], id_value: Union[str, int]
    ) -> T:
        """
        Get instance by key if user allowed to read.
        :param user: user instance to check access for
        :param id_value: value of the key attribute for filtering
        """
        if not hasattr(cls, _crud.key_attr):
            raise AttributeError(
                f"class {cls.__name__} doesn't have attribute {_crud.key_attr}. Try to set CRUD_DEFAULT_KEY_COLUMN in configs."
            )

        obj = (
            cls.query.query_for_user(user)
            .filter(getattr(cls, _crud.key_attr) == id_value)
            .one_or_none()
        )
        if obj is None:
            abort(404)
        return obj

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
