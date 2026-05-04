from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask import Flask
import os
from app.settings import BASE_DIR
class Base(DeclarativeBase):
  pass


db = SQLAlchemy(model_class=Base)

def initialize_db(app: Flask):
    

    # Get and create the data folder 
    db_dir = os.path.join(BASE_DIR, 'data')
    os.makedirs(os.path.dirname(db_dir), exist_ok=True)

    db_path = os.path.join(db_dir, 'db.sqlite')
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
    db.init_app(app)
    with app.app_context():
        db.create_all()
