import os
import yaml
from flask import Flask
from sqlalchemy.exc import OperationalError, ProgrammingError
from wtforms import HiddenField
from app.models import db, login_manager, User
from app.install import install_data, make_config


# From Flask-Bootstrap
def is_hidden_field_filter(field):
    return isinstance(field, HiddenField)


# Put static folder inside data folder on OpenShift, otherwise use standard.
static_folder = os.path.join(os.environ.get('OPENSHIFT_DATA_DIR', ''), 'static')


def create_app():
    app = Flask(__name__, static_url_path='/files', static_folder=static_folder)

    cfg_folder = os.environ.get('OPENSHIFT_DATA_DIR', app.root_path)

    if not os.path.exists(os.path.join(cfg_folder, 'config.yml')):
        os.mkdir(os.path.join(cfg_folder, 'static'))
        make_config(cfg_folder)

    with open(os.path.join(cfg_folder, 'config.yml')) as f:
        c = yaml.load(f)

    app.config.update(c['ADVANCED'])
    app.config.update(c['USER'])

    try:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['OPENSHIFT_MYSQL_DB_URL'] + os.environ['OPENSHIFT_APP_NAME']
    except KeyError:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{0}'.format(
            os.path.abspath(os.path.join(app.root_path, '..', 'data-dev.sqlite')))

    # Database / Admin
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        try:
            User.query.all()
        except (OperationalError, ProgrammingError):
            db.create_all()
            install_data()

    # From Flask-Bootstrap
    app.jinja_env.globals['bootstrap_is_hidden_field'] = is_hidden_field_filter

    # URL Rules / Blueprints
    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Admin view
    from admin import admin
    admin.init_app(app)

    return app
