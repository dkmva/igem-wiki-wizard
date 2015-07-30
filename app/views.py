import os
from flask import render_template, current_app, redirect, url_for, send_from_directory
from werkzeug.exceptions import NotFound
from models import Page, Image, CssFile, JsFile, File


def index():

    return redirect(url_for('admin.index'))


def wiki(path, namespace):
    if namespace != current_app.config['NAMESPACE']:
        raise NotFound()

    page = Page.query.filter_by(url=path).first()
    css = CssFile.query.filter_by(url=path).first()
    js = JsFile.query.filter_by(url=path).first()

    try:
        content = next(item for item in [page, css, js] if item is not None)
    except StopIteration:
        raise NotFound()
    else:
        return content.render()


def images():

    images = Image.query.all()
    files = File.query.all()

    return render_template('images.html', images=images, files=files)


def ckedit(path):
    full_path = os.path.join(current_app.root_path, 'ckeditor', path)

    basename = os.path.basename(full_path)
    dirname = os.path.dirname(full_path)

    return send_from_directory(dirname, basename)