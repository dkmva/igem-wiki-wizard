import os
import zipfile

from flask import request, current_app, url_for, flash, redirect, send_file, abort
from flask.ext.admin import BaseView, expose, AdminIndexView, helpers
from flask.ext.admin._compat import urljoin
from flask.ext.admin.babel import gettext
from flask.ext.admin.contrib.fileadmin import FileAdmin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.login import current_user, logout_user, login_user
from flask.ext.themes2 import get_themes_list
from werkzeug.utils import secure_filename
from wtforms import TextAreaField, StringField, PasswordField
from wtforms.widgets import TextArea

from app.admin.forms import SettingsForm, RegistrationForm, LoginForm, ThemeForm
from app.models import Setting, Page, User, db, Section, Entity, UploadedFile
from app.upload import upload_binary_file, upload_text_file, wiki_login, wiki_logout, upload_page, upload_template
from app.utils import get_theme_folder


# View Classes
class ModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def render(self, template, **kwargs):
        kwargs['namespace'] = Setting.query.filter_by(name=u'namespace').first().value
        return super(ModelView, self).render(template, **kwargs)


class BaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated

    def render(self, template, **kwargs):
        kwargs['namespace'] = Setting.query.filter_by(name=u'namespace').first().value
        return super(BaseView, self).render(template, **kwargs)


class FileAdmin(FileAdmin):
    def is_accessible(self):
        return current_user.is_authenticated

    def render(self, template, **kwargs):
        kwargs['namespace'] = Setting.query.filter_by(name=u'namespace').first().value
        return super(FileAdmin, self).render(template, **kwargs)


# https://gist.github.com/dengshuan/124b5c61f33bd33a26f3
class CKTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] += ' ckeditor'
        else:
            kwargs.setdefault('class', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKModelView(ModelView):
    create_template = 'admin/CK/create.html'
    edit_template = 'admin/CK/edit.html'

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        theme = Setting.query.filter_by(name=u'theme').first().value
        page_templates = os.path.join(current_app.config['THEME_PATHS'][0], theme, 'templates', 'pages')
        section_templates = os.path.join(current_app.config['THEME_PATHS'][0], theme, 'templates', 'sections')
        self._template_args['page_templates'] = [f for f in os.listdir(page_templates) if not f[:1] == '_']
        self._template_args['section_templates'] = [f for f in os.listdir(section_templates) if not f[:1] == '_']
        self._template_args['file_list'] = [f for f in os.listdir(current_app.static_folder) if os.path.splitext(f)[-1] in ['.png', '.gif', '.jpg', '.jpeg']]
        return super(CKModelView, self).edit_view()

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        theme = Setting.query.filter_by(name=u'theme').first().value
        page_templates = os.path.join(current_app.config['THEME_PATHS'][0], theme, 'templates', 'pages')
        section_templates = os.path.join(current_app.config['THEME_PATHS'][0], theme, 'templates', 'sections')
        self._template_args['page_templates'] = [f for f in os.listdir(page_templates) if not f[:1] == '_']
        self._template_args['section_templates'] = [f for f in os.listdir(section_templates) if not f[:1] == '_']
        self._template_args['file_list'] = [f for f in os.listdir(current_app.static_folder) if os.path.splitext(f)[-1] in ['.png', '.gif', '.jpg', '.jpeg']]
        return super(CKModelView, self).create_view()


class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()


class StaticFiles(FileAdmin):
    can_mkdir = False
    can_delete_dirs = False
    rename_modal = True
    upload_modal = True
    allowed_extensions = ('pdf', 'ppt', 'txt', 'zip', 'mp3', 'mp4', 'webm', 'mov', 'swf', 'xls', 'm', 'ogg', 'gb', 'xls', 'tif', 'tiff', 'fcs', 'otf', 'eot', 'ttf', 'woff', 'png', 'gif', 'jpg', 'jpeg')

    def is_accessible_path(self, path):
        if not path or os.path.isfile(os.path.join(self.base_path, path)):
            return True

    def on_rename(self, full_path, dir_base, filename):
        oldname = os.path.basename(full_path)

        to_update = []
        to_update += Page.query.filter_by(image=oldname).all()
        to_update += Section.query.filter_by(image=oldname).all()
        to_update += Entity.query.filter_by(image=oldname).all()

        for item in to_update:
            item.image = unicode(filename)

        uf = UploadedFile.query.filter_by(name=oldname).first()
        if uf:
            uf.name = unicode(filename)


class Theme(FileAdmin):
    rename_modal = True
    upload_modal = True
    editable_extensions = ('html', 'js', 'css', 'json')
    allowed_extensions = ('html', 'js', 'css', 'json', 'pdf', 'ppt', 'txt', 'zip', 'mp3', 'mp4', 'webm', 'mov', 'swf', 'xls', 'm', 'ogg', 'gb', 'xls', 'tif', 'tiff', 'fcs', 'otf', 'eot', 'ttf', 'woff', 'png', 'gif', 'jpg', 'jpeg')

    def get_base_path(self):
        path = FileAdmin.get_base_path(self)
        theme = Setting.query.filter_by(name=u'theme').first().value
        return os.path.join(path, theme)

    def get_base_url(self):
        theme = Setting.query.filter_by(name=u'theme').first().value
        url = '{}{}/'.format(self.base_url, theme)
        return url

    @expose('/download/<path:path>')
    def download(self, path=None):
        """
            Removing static from urls.
        """
        if not self.can_download:
            abort(404)

        base_path, directory, path = self._normalize_path(path)

        # backward compatibility with base_url
        base_url = self.get_base_url()
        if base_url:
            base_url = urljoin(self.get_url('.index'), base_url)
            if path[:7] == 'static/':
                path = path[7:]
            return redirect(urljoin(base_url, path))

        return send_file(directory)

    @expose('/edit/', methods=('GET', 'POST'))
    def edit(self):
        """
            Encode when writing file, rest is unchanged.
        """
        next_url = None

        path = request.args.getlist('path')
        if not path:
            return redirect(self.get_url('.index'))

        if len(path) > 1:
            next_url = self.get_url('.edit', path=path[1:])

        path = path[0]

        base_path, full_path, path = self._normalize_path(path)

        if not self.is_accessible_path(path) or not self.is_file_editable(path):
            flash(gettext('Permission denied.'), 'error')
            return redirect(self._get_dir_url('.index'))

        dir_url = self._get_dir_url('.index', os.path.dirname(path))
        next_url = next_url or dir_url

        form = self.edit_form()
        error = False

        if self.validate_form(form):
            form.process(request.form, content='')
            if form.validate():
                try:
                    with open(full_path, 'w') as f:
                        f.write(request.form['content'].encode('utf8'))
                except IOError:
                    flash(gettext("Error saving changes to %(name)s.", name=path), 'error')
                    error = True
                else:
                    self.on_edit_file(full_path, path)
                    flash(gettext("Changes to %(name)s saved successfully.", name=path))
                    return redirect(next_url)
        else:
            helpers.flash_errors(form, message='Failed to edit file. %(error)s')

            try:
                with open(full_path, 'rb') as f:
                    content = f.read()
            except IOError:
                flash(gettext("Error reading %(name)s.", name=path), 'error')
                error = True
            except:
                flash(gettext("Unexpected error while reading from %(name)s", name=path), 'error')
                error = True
            else:
                try:
                    content = content.decode('utf8')
                except UnicodeDecodeError:
                    flash(gettext("Cannot edit %(name)s.", name=path), 'error')
                    error = True
                except:
                    flash(gettext("Unexpected error while reading from %(name)s", name=path), 'error')
                    error = True
                else:
                    form.content.data = content

        return self.render(self.edit_template, dir_url=dir_url, path=path,
                           form=form, error=error,
                           modal=request.args.get('modal'))


class EntityView(CKModelView):
    form_overrides = dict(description=CKTextAreaField, name=StringField, role=StringField, link=StringField)


class SectionView(CKModelView):
    form_overrides = dict(html=CKTextAreaField)
    column_filters = ('page.name',)
    column_list = ('position', 'image', 'name', 'page', 'template', 'html')
    column_default_sort = (Section.position, False)


class TimeLineView(CKModelView):
    form_overrides = dict(html=CKTextAreaField)
    column_default_sort = 'date'


class PageView(CKModelView):
    form_overrides = dict(html=CKTextAreaField)
    inline_models = [(Section, dict(sort_column='position', form_overrides=dict(html=CKTextAreaField)))]
    column_default_sort = ('position', False)


class MenuItemView(ModelView):
    column_default_sort = ('position', False)


class UserView(ModelView):
    column_list = ('username',)
    form_columns = ('username', 'password')

    form_extra_fields = {
        'password': PasswordField('Password')
    }


class UploadedFileView(ModelView):
    pass


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


class UploadView(BaseView):

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        theme = Setting.query.filter_by(name=u'theme').first().value
        theme_folder = os.path.join(current_app.config['THEME_PATHS'][0], theme)
        theme_static = os.path.join(theme_folder, 'static')
        theme_includes = os.listdir(os.path.join(theme_folder, 'templates', 'includes'))
        theme_static_files = []
        for root, directories, filenames in os.walk(theme_static):
            for name in filenames:
                if os.path.basename(os.path.dirname(os.path.join(root, name))) == 'static' and name == 'preview.png':
                    continue
                theme_static_files.append(os.path.join(root[len(theme_static)+1:], name))

        ctx = {
            'pages': Page.query,
            'files': [f for f in os.listdir(current_app.static_folder) if os.path.isfile(os.path.join(current_app.static_folder, f))],
            'theme': theme_static_files,
            'includes': theme_includes,
        }

        return self.render('admin/upload.html', **ctx)

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
        upload_page(page)
        return 'Page uploaded'

    @expose('/fileupload', methods=['POST'])
    def fileupload(self):
        file = request.get_json()['file']
        upload_binary_file(current_app.static_folder, file)
        return 'File uploaded'

    @expose('/themeupload', methods=['POST'])
    def themeupload(self):
        theme_static = get_theme_folder('static')
        file = request.get_json()['file']
        ext = os.path.splitext(file)[-1]
        if ext in ['.css', '.js']:
            upload_text_file(theme_static, file)
        else:
            upload_binary_file(theme_static, file)
        return 'Theme file uploaded'

    @expose('/includeupload', methods=['POST'])
    def themeupload(self):
        file = request.get_json()['file']
        upload_template(file)
        return 'Theme file uploaded'


class SettingsView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):

        form = SettingsForm()
        ns = Setting.query.filter_by(name=u'namespace').first()
        bu = Setting.query.filter_by(name=u'base_url').first()
        rp = Setting.query.filter_by(name=u'show_register_page').first()
        rp_check = rp.value == 'true'

        if not form.is_submitted():
            form.namespace.data = ns.value
            form.base_url.data = bu.value
            form.show_register_page.data = rp_check

        if form.validate_on_submit():
            ns.value = form.namespace.data
            bu.value = form.base_url.data
            rp.value = str(form.show_register_page.data).lower()

        return self.render('admin/settings.html', form=form)


class SelectThemeView(BaseView):
    @expose('/')
    def index(self):
        themes = get_themes_list()
        theme = Setting.query.filter_by(name=u'theme').first().value
        return self.render('admin/theme.html', themes=themes, chosen_theme=theme)

    @expose('/select/<theme>')
    def select(self, theme):
        setting = Setting.query.filter_by(name=u'theme').first()
        setting.value = unicode(theme)
        return redirect(url_for('.index'))

    @expose('/install/', methods=['GET', 'POST'])
    def install(self):

        form = ThemeForm()

        if form.validate_on_submit():
            theme_base = current_app.config['THEME_PATHS'][0]
            filename = secure_filename(form.theme.data.filename)
            zname = os.path.join(theme_base, filename)
            form.theme.data.save(zname)

            with zipfile.ZipFile(zname, 'r') as z:
                z.extractall(theme_base)

            os.remove(zname)

            current_app.theme_manager.refresh()
            return redirect(url_for('.index'))

        return self.render('admin/theme.html', form=form)


class IndexView(AdminIndexView):

    def render(self, template, **kwargs):
        kwargs['namespace'] = Setting.query.filter_by(name=u'namespace').first().value
        return super(IndexView, self).render(template, **kwargs)

    @expose('/')
    def index(self):

        if not current_user.is_authenticated:
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
        if Setting.query.filter_by(name=u'show_register_page').first().value == 'true' or len(User.query.all()) == 0:
            self._template_args['link'] = link
            self._template_args['desc'] = 'In order to use the administration panel, you must log in.'
        return super(IndexView, self).index()

    @expose('/register/', methods=('GET', 'POST'))
    def register_view(self):

        if not Setting.query.filter_by(name=u'show_register_page').first().value == 'true' and len(User.query.all()) > 0:
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
