import os
from flask import url_for, redirect, flash, current_app, request
from flask.ext.admin import AdminIndexView, expose
from flask.ext.login import current_user, login_user, logout_user
from wtforms import PasswordField, StringField
import yaml
from app.models import db, Section, User, Image, File, CssFile, JsFile, Page
from app.upload import wiki_login, wiki_logout
from app.admin.forms import LoginForm, RegistrationForm, SettingsForm
from app.admin.view_types import ModelImageView, ModelView, FileUploadView, BaseView, ImageUploadView


class PageView(ModelImageView):
    inline_models = [(Section, dict(sort_column='position'))]
    column_list = ('position', 'image', 'name', 'url', 'template', 'sections')
    column_default_sort = 'position'


class SectionView(ModelImageView):
    column_filters = ('page.name',)
    column_list = ('position', 'image', 'name', 'page', 'template', 'html')
    column_default_sort = (Section.position, False)


class PersonView(ModelImageView):
    column_filters = ('role',)
    column_list = ('position', 'image', 'name', 'role', 'description')
    column_default_sort = 'position'


class TimeLineView(ModelImageView):
    column_default_sort = 'date'


class ImageView(ImageUploadView):
    column_list = ('image', 'name', 'path', 'external_path')


class FileView(FileUploadView):
    column_list = ('name', 'path', 'external_path')


class TemplateView(ModelView):
    create_template = 'admin/Ace/TemplateCreate.html'
    edit_template = 'admin/Ace/TemplateEdit.html'

    column_exclude_list = 'content'


class CssView(ModelView):
    create_template = 'admin/Ace/CssCreate.html'
    edit_template = 'admin/Ace/CssEdit.html'

    column_exclude_list = 'content'
    column_default_sort = 'position'


class JsView(ModelView):
    create_template = 'admin/Ace/JsCreate.html'
    edit_template = 'admin/Ace/JsEdit.html'

    column_exclude_list = 'content'
    column_default_sort = 'position'


class MenuItemView(ModelView):
    column_default_sort = 'position'


class UserView(ModelView):
    column_list = ('username',)
    form_columns = ('username', 'password')

    form_extra_fields = {
        'password': PasswordField('Password')
    }


# BaseViews
class IndexView(AdminIndexView):
    @expose('/')
    def index(self):

        if not current_user.is_authenticated():
            return redirect(url_for('.login_view'))
        link = '<p>Already have an account? <a href="' + url_for('.login_view') + '">Click here to log in.</a></p>'
        self._template_args['link'] = link
        return super(IndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is not None and user.verify_password(form.password.data):
                login_user(user, form.remember_me.data)
                return redirect(url_for('.index'))

            flash('Invalid username or password')
        link = '<p>Don\'t have an account? <a href="' + url_for('.register_view') + '">Click here to register.</a></p>'
        self._template_args['form'] = form
        if current_app.config['SHOW_REGISTER_PAGE'] or len(User.query.all()) == 0:
            self._template_args['link'] = link
            self._template_args['desc'] = 'In order to use the administration panel, you must log in.'
        return super(IndexView, self).index()

    @expose('/register/', methods=('GET', 'POST'))
    def register_view(self):

        if not current_app.config['SHOW_REGISTER_PAGE'] and len(User.query.all()) > 0:
            return redirect(url_for('.index'))

        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, password=form.password.data)

            db.session.add(user)

            flash('User named {} has been created'.format(form.username.data))
            return redirect(url_for('.login_view'))
        link = '<p>Already have an account? <a href="' + url_for('.login_view') + '">Click here to log in.</a></p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        self._template_args['desc'] = 'Register an account in order to log in.'
        return super(IndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        logout_user()
        return redirect(url_for('.index'))


class ThemeView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):

        return self.render('admin/theme.html')


class UploadView(BaseView):

    @expose('/wikilogin', methods=['POST'])
    def login(self):
        data = request.get_json()
        if wiki_login(data['username'], data['password']):
            return 'Success'
        return 'Error'

    @expose('/wikilogout')
    def logout(self):
        wiki_logout()
        return 'Logged Out'

    @expose('/pageupload', methods=['POST'])
    def pageupload(self):
        page = request.get_json()['page']
        Page.query.filter_by(name=page).first().upload()
        return 'Page Uploaded'

    @expose('/fileupload', methods=['POST'])
    def fileupload(self):
        file = request.get_json()['file']
        File.query.filter_by(name=file).first().upload()
        return 'File Uploaded'


    @expose('/imageupload', methods=['POST'])
    def imageupload(self):
        image = request.get_json()['image']
        Image.query.filter_by(name=image).first().upload()
        return 'Image Uploaded'

    @expose('/cssupload', methods=['POST'])
    def cssupload(self):
        css = request.get_json()['css']
        CssFile.query.filter_by(url=css).first().upload()
        return 'CSS Uploaded'


    @expose('/jsupload', methods=['POST'])
    def jsupload(self):
        js = request.get_json()['js']
        JsFile.query.filter_by(url=js).first().upload()
        return 'JS Uploaded'

    @expose('/', methods=['GET', 'POST'])
    def index(self):

        ctx = {
        'pages': Page.query.order_by('position').all(),
        'files': File.query.all(),
        'images': Image.query.all(),
        'css': CssFile.query.filter_by(active=True).all(),
        'js': JsFile.query.filter_by(active=True).all()
        }

        return self.render('admin/upload.html', **ctx)


class SettingsView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        cfg_folder = os.environ.get('OPENSHIFT_DATA_DIR', current_app.root_path)

        with open(os.path.join(cfg_folder, 'config.yml')) as f:
            yml = yaml.load(f)
            c = yml['USER']

        form = SettingsForm()

        if form.validate_on_submit():

            for k in c:
                c[k] = form[k.lower()].data
                current_app.config[k] = c[k]
            with open(os.path.join(cfg_folder, 'config.yml'), 'w') as f:
                f.write(yaml.safe_dump(yml, default_flow_style=False))
        elif not form.is_submitted():
            for k in c:
                form[k.lower()].data = current_app.config[k]

        return self.render('admin/settings.html', form=form)


class ReferenceView(ModelView):
    form_overrides = dict(reference=StringField)
    form_widget_args = {
        'reference': {
            'ng-model': 'reference'
        },
        'ref_id': {
            'ng-model': 'refID'
        }
    }


    create_template = 'admin/references/create.html'
    edit_template = 'admin/references/edit.html'
