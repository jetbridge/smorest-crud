from flask_crud.test.app import db
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from flask_crud import AccessControlUser
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

    @classmethod
    def query_for_user(cls, user) -> BaseQuery:
        return cls.query


class Car(db.Model):  # noqa: T484
    id = Column(Integer, primary_key=True)

    owner_id = Column(ForeignKey("human.id"))
    owner = relationship("Human", back_populates="cars")
