import os
import shutil

from flask import Flask
from flask.ext.themes2 import Themes
from sqlalchemy.exc import OperationalError, ProgrammingError
import yaml

from app.install import make_config, install_data
from app.models import db, login_manager, Setting, Page, User
from app.utils import css_sanitizer, is_hidden_field_filter, WikiInclude


themes = Themes()
# Put static folder inside data folder on OpenShift, otherwise use standard.
static_folder = os.path.join(os.environ.get('OPENSHIFT_DATA_DIR', ''), 'static')


def create_app():
    app = Flask(__name__, static_folder=static_folder)

    try:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['OPENSHIFT_MYSQL_DB_URL'] + os.environ['OPENSHIFT_APP_NAME']
    except KeyError:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{0}'.format(
            os.path.abspath(os.path.join(app.root_path, '..', 'data-dev.sqlite')))

    app.config['THEME_PATHS'] = (os.path.join(os.environ.get('OPENSHIFT_DATA_DIR', app.root_path), 'themes'), )

    cfg_folder = os.environ.get('OPENSHIFT_DATA_DIR', app.root_path)

    if not os.path.exists(os.path.join(cfg_folder, 'config.yml')):
        make_config(cfg_folder)
        if 'OPENSHIFT_DATA_DIR' in os.environ:
            shutil.copytree(os.path.join(app.root_path, 'static'), os.path.join(cfg_folder, 'static'))
            shutil.copytree(os.path.join(app.root_path, 'themes'), os.path.join(cfg_folder, 'themes'))

    with open(os.path.join(cfg_folder, 'config.yml')) as f:
        app.config.update(yaml.load(f))

    # Database / Admin
    db.init_app(app)
    themes.init_themes(app, app_identifier='WikiWizard')
    login_manager.init_app(app)
    with app.app_context():
        try:
            User.query.all()
        except (OperationalError, ProgrammingError):
            db.create_all()
            install_data()
    # From Flask-Bootstrap
    app.jinja_env.globals['bootstrap_is_hidden_field'] = is_hidden_field_filter
    app.jinja_env.filters['css_sanitized'] = css_sanitizer
    app.jinja_env.add_extension(WikiInclude)

    # URL Rules / Blueprints
    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Admin view
    from admin import create_admin
    create_admin(app)

    return app
