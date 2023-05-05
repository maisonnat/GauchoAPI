import datetime
from peewee import Model, SqliteDatabase, CharField, FloatField, DateTimeField
import os

db = SqliteDatabase('products.db')


class Product(Model):
    name = CharField()
    price = FloatField()
    url = CharField()
    image_url = CharField()
    timestamp = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


def create_tables():
    with db:
        db.create_tables([Product])


def initialize_database():
    if not os.path.exists('products.db'):
        create_tables()


if __name__ == "__main__":
    initialize_database()