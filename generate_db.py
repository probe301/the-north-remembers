



import time
import os
import shutil
import re
from pylon import puts
from pylon import datalines
from pylon import enumrange
from datetime import datetime


# from peewee import *
from peewee import SqliteDatabase
from peewee import CharField
from peewee import DateField
from peewee import ForeignKeyField
from peewee import BooleanField
from peewee import Model
from peewee import fn
from peewee import JOIN
from datetime import date



db = SqliteDatabase('people.db')

class Person(Model):
  name = CharField()
  birthday = DateField()
  is_relative = BooleanField()

  class Meta:
    database = db # This model uses the "people.db" database.






class Pet(Model):
  owner = ForeignKeyField(Person, related_name='pets')
  name = CharField()
  animal_type = CharField()

  class Meta:
    database = db # this model uses the "people.db" database


def test_create_db():
  # pass
  db.connect()
  db.create_tables([Person, Pet])
  db.close()

def test_insert():
  uncle_bob = Person(name='Bob', birthday=date(1960, 1, 15), is_relative=True)
  uncle_bob.save() # bob is now stored in the database


  grandma = Person.create(name='Grandma', birthday=date(1935, 3, 1), is_relative=True)
  herb = Person.create(name='Herb', birthday=date(1950, 5, 5), is_relative=False)

  grandma.name = 'Grandma L.'
  grandma.save()

  bob_kitty = Pet.create(owner=uncle_bob, name='Kitty', animal_type='cat')
  herb_fido = Pet.create(owner=herb, name='Fido', animal_type='dog')
  herb_mittens = Pet.create(owner=herb, name='Mittens', animal_type='cat')
  herb_mittens_jr = Pet.create(owner=herb, name='Mittens Jr', animal_type='cat')

  herb_mittens.delete_instance()

  herb_fido.owner = uncle_bob
  herb_fido.save()
  bob_fido = herb_fido  # rename our variable for clarity



def test_retrieve():
  grandma = Person.select().where(Person.name == 'Grandma L.').get()
  print(grandma)

  for person in Person.select():
    print(person.name, person.is_relative)

  query = Pet.select().where(Pet.animal_type == 'cat')
  for pet in query:
    print(pet.name, pet.owner.name)  # will involve n+1 query


  query = (Pet.select(Pet, Person)
              .join(Person)          # better
              .where(Pet.animal_type == 'cat'))
  for pet in query:
    print(pet.name, pet.owner.name)

  for pet in Pet.select().where(Pet.owner == uncle_bob).order_by(Pet.name):
    print(pet.name)

  for person in Person.select().order_by(Person.birthday.desc()):
    print(person.name, person.birthday)


  d1940 = date(1940, 1, 1)
  d1960 = date(1960, 1, 1)
  query = (Person
           .select()
           .where((Person.birthday < d1940) | (Person.birthday > d1960)))


def test_join():
  subquery = Pet.select(fn.COUNT(Pet.id)).where(Pet.owner == Person.id)
  query = (Person
           .select(Person, Pet, subquery.alias('pet_count'))
           .join(Pet, JOIN.LEFT_OUTER)
           .order_by(Person.name))

  for person in query.aggregate_rows():  # Note the `aggregate_rows()` call.
    print(person.name, person.pet_count, 'pets')
    for pet in person.pets:
      print('    ', pet.name, pet.animal_type)

  # Bob 2 pets
  #      Kitty cat
  #      Fido dog
  # Grandma L. 0 pets
  # Herb 1 pets
  #      Mittens Jr cat

