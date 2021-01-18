from typing import Optional, Type

from smorest_crud.access_control.models import T
from smorest_crud.test.app import db
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from smorest_crud import AccessControlUser, AccessControlQuery
from flask_sqlalchemy import BaseQuery


class Pet(db.Model):  # noqa: T484
    id = Column(Integer, primary_key=True)
    genus = Column(Text)
    species = Column(Text)
    edible = Column(Text)

    human_id = Column(ForeignKey("human.id"))
    human = relationship("Human", back_populates="pets")
    cars = relationship("Car", secondary="human")

    @classmethod
    def query_for_user(cls, user) -> BaseQuery:
        return cls.query


class Human(db.Model, AccessControlUser):  # noqa: T484
    id = Column(Integer, primary_key=True)
    name = Column(Text)

    pets = relationship("Pet", back_populates="human")
    cars = relationship("Car", back_populates="owner")

    # private
    not_allowed = Column(Text)

    def user_can_write(self, user) -> bool:
        return self.name == user.name

    def user_can_create(self, user, args: Optional[dict]) -> bool:
        return self.name == user.name

    @classmethod
    def query_for_user(cls, user) -> BaseQuery:
        return cls.query


class CarQuery(AccessControlQuery):
    def query_for_user(self, user: Type[T]) -> "CarQuery":
        return self.filter_by(owner_id=user.id)


class Car(db.Model, AccessControlUser):  # noqa: T484
    query_class = CarQuery

    id = Column(Integer, primary_key=True)

    owner_id = Column(ForeignKey("human.id"))
    owner = relationship("Human", back_populates="cars")

    def user_can_write(self, user: "AccessControlUser") -> bool:
        return True
