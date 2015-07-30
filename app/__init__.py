import os
import yaml
from flask import Flask
from flask.ext.admin import Admin
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from sqlalchemy.exc import OperationalError, ProgrammingError
from wtforms import HiddenField

db = SQLAlchemy()
login_manager = LoginManager()
static_folder = os.path.join(os.environ.get('OPENSHIFT_DATA_DIR', ''), 'static')
# Requires db and login_manager
from app.models import MenuItem, JsFile, CssFile, Template, File, Image, Timeline, Person, Section, Page, User
from app.admin_views import UploadView, SettingsView, PageView, SectionView, CKModelView, ImageView, \
    FileView, TemplateView, CssView, JsView, ThemeView, ModelView, IndexView, PersonView
from app.install import install, make_config

admin = Admin(name='Wiki Wizard', index_view=IndexView(), base_template='admin/my_master.html')


# From Flask-Bootstrap
def is_hidden_field_filter(field):
        return isinstance(field, HiddenField)


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
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.abspath(os.path.join(app.root_path, '..', 'data-dev.sqlite'))

    # Database / Admin
    db.init_app(app)
    with app.app_context():
        try:
            User.query.all()
        except (OperationalError, ProgrammingError):
            db.create_all()
            install()

    admin.init_app(app)
    login_manager.init_app(app)

    # From Flask-Bootstrap
    app.jinja_env.globals['bootstrap_is_hidden_field'] =\
            is_hidden_field_filter

    # URL Rules / Blueprints
    import views
    app.add_url_rule('/', view_func=views.index)
    app.add_url_rule('/ckeditor/<path:path>', view_func=views.ckedit)
    app.add_url_rule('/images', view_func=views.images)
    app.add_url_rule('/Team:<namespace>', view_func=views.wiki, defaults={'path': None})
    app.add_url_rule('/Team:<namespace>/<path:path>', view_func=views.wiki)

    # Admin view
    admin.add_view(PageView(Page, db.session, name='Pages', category='Content'))
    admin.add_view(SectionView(Section, db.session, name='Sections', category='Content'))
    admin.add_view(PersonView(Person, db.session, name='Persons', category='Content'))
    admin.add_view(CKModelView(Timeline, db.session, category='Content'))

    admin.add_view(ImageView(Image, db.session, name='Images', category='Files'))
    admin.add_view(FileView(File, db.session, name='Files', category='Files'))

    admin.add_view(TemplateView(Template, db.session, name='Templates', category='Theme'))
    admin.add_view(CssView(CssFile, db.session, name='CSS Files', category='Theme'))
    admin.add_view(JsView(JsFile, db.session, name='JavaScript Files', category='Theme'))
    admin.add_view(ThemeView(name='Save/Load Theme', category='Theme'))

    admin.add_view(SettingsView(name='Settings'))
    admin.add_view(UploadView(name='Upload'))

    admin.add_view(ModelView(MenuItem, db.session, name='Menu', category='Advanced'))
    admin.add_view(ModelView(User, db.session, name='Users', category='Advanced'))

    return app
