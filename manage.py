from flask.ext.script import Manager
from app import create_app, db

app = create_app()
manager = Manager(app)

@manager.command
def create():
    "Creates database tables from sqlalchemy models"
    db.create_all()


if __name__ == '__main__':
    manager.run()