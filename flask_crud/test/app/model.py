from flask_crud.test.app import db
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship


class Pet(db.Model):  # noqa: T484
    id = Column(Integer, primary_key=True)
    genus = Column(Text)
    species = Column(Text)
    edible = Column(Text)

    human_id = Column(ForeignKey("human.id"))
    human = relationship("Human", back_populates="pets")
    cars = relationship('Car', secondary='human')


class Human(db.Model):  # noqa: T484
    id = Column(Integer, primary_key=True)
    name = Column(Text)

    pets = relationship("Pet", back_populates="human")
    cars = relationship("Car", back_populates="owner")


class Car(db.Model):  # noqa: T484
    id = Column(Integer, primary_key=True)

    owner_id = Column(ForeignKey('human.id'))
    owner = relationship("Human", back_populates="cars")
