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
from .. import static_folder


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


class UploadView(ModelView):
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
                                     base_path=static_folder)
    }


class ImageUploadView(UploadView):
    form_extra_fields = {
        'path': form.ImageUploadField('Image',
                                      base_path=static_folder,
                                      thumbnail_size=(100, 100, True))
    }

