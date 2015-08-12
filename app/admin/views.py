import os
from flask import url_for, redirect, flash, current_app
from flask.ext.admin import AdminIndexView, expose
from flask.ext.login import current_user, login_user, logout_user
from wtforms import PasswordField
import yaml
from ..models import db, Section, User, Image, File, CssFile, JsFile, Page
from ..upload import wiki_login, wiki_logout
from .forms import LoginForm, RegistrationForm, UploadForm, SettingsForm
from .view_types import ModelImageView, ModelView, FileUploadView, BaseView, ImageUploadView


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


class TimeLineView(ModelView):
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
    @expose('/', methods=['GET', 'POST'])
    def index(self):

        page_choices = [(p.name, p.name) for p in Page.query.all()]

        image_choices = [(p.name, p.name) for p in Image.query.all()]
        file_choices = [(p.name, p.name) for p in File.query.all()]

        css_choices = [(p.url, p.url) for p in CssFile.query.filter_by(active=True).all()]
        js_choices = [(p.url, p.url) for p in JsFile.query.filter_by(active=True).all()]

        form = UploadForm(page_choices, image_choices, file_choices, css_choices, js_choices)

        if form.validate_on_submit():

            if wiki_login(form.username.data, form.password.data):

                for image_name in form.images.data:
                    image = Image.query.filter_by(name=image_name).first()
                    image.upload()

                for file_name in form.files.data:
                    f = File.query.filter_by(name=file_name).first()
                    f.upload()

                for css_name in form.css_files.data:
                    static_file = CssFile.query.filter_by(url=css_name).first()
                    static_file.upload()

                for js_name in form.js_files.data:
                    static_file = JsFile.query.filter_by(url=js_name).first()
                    static_file.upload()

                for page_name in form.pages.data:
                    page = Page.query.filter_by(name=page_name).first()
                    page.upload()

                wiki_logout()
            else:
                flash('Could not login to the iGEM wiki. Wrong credentials?')

        return self.render('admin/upload.html', form=form)


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