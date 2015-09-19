from flask.ext.script import Manager, Server
from app import create_app, db

app = create_app()
manager = Manager(app)
manager.add_command("runserver", Server(port=8000))


@manager.command
def create():
    "Creates database tables from sqlalchemy models"
    db.create_all()


if __name__ == '__main__':
    manager.run()