from flask import Flask
from configuration import  Configuration
from flask_migrate import Migrate, init, migrate,upgrade
from models import db, User, UserRole, Role
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

            adminR = Role(name="admin")
            kupacR = Role(name="kupac")
            magacionerR = Role(name="magacioner")

            db.session.add(adminR)
            db.session.add(kupacR)
            db.session.add(magacionerR)

            db.session.commit()

            admin = User(
                email="admin@admin.com",
                password="1",
                forename="admin",
                surname="admin",
                isCustomer=False
            )

            db.session.add(admin)
            db.session.commit()

            adminRole = UserRole(
                userId=admin.id,
                roleId=adminR.id
            )

            db.session.add(adminRole)
            db.session.commit()

            connected = True

    except Exception as error:
        print(error)
