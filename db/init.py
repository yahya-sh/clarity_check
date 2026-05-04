from flask import Flask
from db import db

def initialize_db(app: Flask):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data/db.sqlite"
    with app.app_context():
        db.create_all()