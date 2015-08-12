import os
from flask import url_for
from flask.ext.admin import BaseView
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.contrib.sqla.form import AdminModelConverter
from flask.ext.admin import form
from flask.ext.login import current_user
from markupsafe import Markup
from wtforms import TextAreaField
from wtforms.ext.sqlalchemy import orm
from wtforms.widgets import TextArea

static_folder = os.path.join(os.environ.get('OPENSHIFT_DATA_DIR', 'app'), 'static')


class CKTextArea(TextArea):
    def __call__(self, *args, **kwargs):
        return super(CKTextArea, self).__call__(class_='ckeditor', *args, **kwargs)


class CKTextAreaField(TextAreaField):
    widget = CKTextArea()


class CKModelConverter(AdminModelConverter):

    @orm.converts('Text')
    def conv_Text(self, field_args, **kwargs):
        return CKTextAreaField(**field_args)


# View Classes
class ModelView(ModelView):

    def is_accessible(self):
        return current_user.is_authenticated()


class BaseView(BaseView):

    def is_accessible(self):
        return current_user.is_authenticated()


class CKModelView(ModelView):

    model_form_converter = CKModelConverter

    create_template = 'admin/CK/create.html'
    edit_template = 'admin/CK/edit.html'


class ModelImageView(CKModelView):
    def _list_thumbnail(view, context, model, name):
        if not model.image or not model.image.path:
            return ''

        return Markup('<img src="{}">'.format(url_for('static',
                                                      filename=form.thumbgen_filename(model.image.path))))
    column_formatters = {
        'image': _list_thumbnail
    }


def rename(obj, file_data):
    parts = os.path.splitext(file_data.filename)
    return '{}{}'.format(obj, parts[-1])


class UploadView(ModelView):
    def on_model_change(self, form, model, is_created):
        if not is_created:
            ext = os.path.splitext(model.path)[-1]
            old_path = os.path.join(static_folder, model.path)
            old_thumb = os.path.join(static_folder, '{}_thumb{}'.format(*os.path.splitext(model.path)))
            new_path = os.path.join(static_folder, model.name+ext)
            new_thumb = os.path.join(static_folder, '{}_thumb{}'.format(model.name, ext))
            model.path = model.name+ext
            os.rename(old_path, new_path)
            os.rename(old_thumb, new_thumb)

    def on_model_delete(self, model):
        path = os.path.join(static_folder, model.path)
        thumb = os.path.join(static_folder, '{}_thumb{}'.format(*os.path.splitext(model.path)))
        os.remove(path)
        os.remove(thumb)

    def _prepend_namespace(view, context, model, name):
        return url_for('static', filename=model.path)

    def _list_thumbnail(view, context, model, name):
        if not model.path:
            return ''
        return Markup('<img src="{}">'.format(url_for('static',
                                                      filename=form.thumbgen_filename(model.path))))

    form_columns = ('name', 'path')
    column_formatters = {
        'image': _list_thumbnail,
        'path': _prepend_namespace
    }


class FileUploadView(UploadView):
    form_extra_fields = {
        'path': form.FileUploadField('File',
                                     base_path=static_folder,
                                     allowed_extensions=['pdf', 'ppt', 'txt', 'zip', 'mp3', 'mp4', 'webm', 'mov', 'swf', 'xls', 'm', 'ogg', 'gb', 'xls', 'tif', 'tiff', 'fcs', 'otf', 'eot', 'ttf', 'woff'],
                                     namegen=rename)
    }


class ImageUploadView(UploadView):
    form_extra_fields = {
        'path': form.ImageUploadField('Image',
                                      base_path=static_folder,
                                      thumbnail_size=(100, 100, True),
                                      allowed_extensions=['png', 'gif', 'jpg', 'jpeg'],
                                      namegen=rename)
    }

