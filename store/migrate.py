from flask import Flask
from configuration import  Configuration
from flask_migrate import Migrate, init, migrate,upgrade
from models import db
from sqlalchemy_utils import database_exists, create_database

app = Flask(__name__)
app.config.from_object(Configuration)

migrateObj = Migrate(app, db)

connected = False

while (not connected):
    try:
        if(not database_exists(app.config["SQLALCHEMY_DATABASE_URI"])):
            create_database(app.config["SQLALCHEMY_DATABASE_URI"])

        db.init_app(app)

        with app.app_context() as context:
            init()
            migrate(message="Production migration")
            upgrade()

            connected = True
    except Exception as error:
        print(error)
