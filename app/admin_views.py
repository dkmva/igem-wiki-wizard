import os
from flask.ext.login import current_user, login_user, logout_user
import yaml

from flask import url_for, current_app, redirect, flash
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.contrib.sqla.form import AdminModelConverter
from flask.ext.admin import form, BaseView, expose, AdminIndexView
from flask.ext.wtf import Form
from markupsafe import Markup
from wtforms import TextAreaField, StringField, PasswordField, SubmitField, SelectMultipleField, widgets, BooleanField, \
    ValidationError
from wtforms.ext.sqlalchemy import orm
from wtforms.validators import Required, EqualTo, Length, Regexp
from wtforms.widgets import TextArea

from app import db, static_folder
from app.models import Page, Section, Image, File, CssFile, JsFile, User
from app.upload import wiki_login, wiki_logout

basedir = os.path.abspath(os.path.dirname(__file__))
file_path = os.environ.get('OPENSHIFT_DATA_DIR', os.path.join(os.path.dirname(__file__), 'static'))


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class UploadForm(Form):

    def __init__(self, page_choices, image_choices, file_choices, css_choices, js_choices):
        super(UploadForm, self).__init__()
        self.pages.choices = page_choices
        self.images.choices = image_choices
        self.files.choices = file_choices
        self.css_files.choices = css_choices
        self.js_files.choices = js_choices

    pages = MultiCheckboxField('Pages')
    images = MultiCheckboxField('Images')
    files = MultiCheckboxField('Files')
    css_files = MultiCheckboxField('Css files')
    js_files = MultiCheckboxField('Js files')
    username = StringField('Username', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Submit')


class SettingsForm(Form):
    namespace = StringField('Namespace', validators=[Required()])
    login_url = StringField('Login URL', validators=[Required()])
    logout_url = StringField('Logout URL', validators=[Required()])
    base_url = StringField('Base URL', validators=[Required()])
    show_register_page = BooleanField('Show Admin Register Page')
    submit = SubmitField('Submit')


class LoginForm(Form):
    username = StringField('Username', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log in')


class RegistrationForm(Form):
    username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                                                     'Usernames must have only letters,'
                                                                                     ' numbers, dots or underscores')])
    password = PasswordField('Password', validators=[Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Register')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class ModelView(ModelView):

    def is_accessible(self):
        return current_user.is_authenticated()


class BaseView(BaseView):

    def is_accessible(self):
        return current_user.is_authenticated()


class CKTextArea(TextArea):
    def __call__(self, *args, **kwargs):
        return super(CKTextArea, self).__call__(class_='ckeditor', *args, **kwargs)


class CKTextAreaField(TextAreaField):
    widget = CKTextArea()


class CKModelConverter(AdminModelConverter):

    @orm.converts('Text')
    def conv_Text(self, field_args, **kwargs):
        return CKTextAreaField(**field_args)


class CKModelView(ModelView):

    model_form_converter = CKModelConverter

    create_template = 'admin/CK/create.html'
    edit_template = 'admin/CK/edit.html'


class MenuItemView(ModelView):

    column_default_sort = 'position'


class ModelImageView(CKModelView):
    def _list_thumbnail(view, context, model, name):
        if not model.image or not model.image.path:
            return ''

        return Markup('<img src="{}">'.format(url_for('static',
                                                      filename=form.thumbgen_filename(model.image.path))))
    column_formatters = {
        'image': _list_thumbnail
    }


class PersonView(ModelImageView):
    column_filters = ('role',)
    column_list = ('position', 'image', 'name', 'role', 'description')
    column_default_sort = 'position'


class SectionView(ModelImageView):
    column_filters = ('page.name',)
    column_list = ('position', 'image', 'name', 'page', 'template', 'html')
    column_default_sort = (Section.position, False)


class PageView(ModelImageView):
    inline_models = [(Section, dict(sort_column='position'))]
    column_list = ('position', 'image', 'name', 'url', 'template', 'sections')
    column_default_sort = 'position'


class FileView(ModelView):
    def _prepend_namespace(view, context, model, name):
        return url_for('static', filename=model.path)


    def _list_thumbnail(view, context, model, name):
        if not model.path:
            return ''

        return Markup('<img src="{}">'.format(url_for('static',
                                                      filename=form.thumbgen_filename(model.path))))
    column_formatters = {
        'image': _list_thumbnail,
        'path': _prepend_namespace
    }

    column_list = ('name', 'path', 'external_path')
    form_columns = ('name', 'path')


    # Alternative way to contribute field is to override it completely.
    # In this case, Flask-Admin won't attempt to merge various parameters for the field.
    form_extra_fields = {
        'path': form.FileUploadField('File',
                                     base_path=static_folder)
    }


class ImageView(FileView):
    column_list = ('image', 'name', 'path', 'external_path')

    form_extra_fields = {
        'path': form.ImageUploadField('Image',
                                      base_path=static_folder,
                                      thumbnail_size=(100, 100, True))
    }


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


class ThemeView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):

        return self.render('admin/theme.html')


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