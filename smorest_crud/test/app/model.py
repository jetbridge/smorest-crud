from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from smorest_crud import AccessControlUser
from flask_sqlalchemy import BaseQuery
from jetkit.db.extid import ExtID
from smorest_crud.test.db import db


class Pet(db.Model, ExtID):  # noqa: T484
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


Pet.add_create_uuid_extension_trigger()


class Human(db.Model, AccessControlUser, ExtID):  # noqa: T484
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


Human.add_create_uuid_extension_trigger()


class Car(db.Model):  # noqa: T484
    id = Column(Integer, primary_key=True)

    owner_id = Column(ForeignKey("human.id"))
    owner = relationship("Human", back_populates="cars")
