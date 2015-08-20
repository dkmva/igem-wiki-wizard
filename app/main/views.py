import os
from flask import url_for, redirect, current_app, render_template, send_from_directory
from werkzeug.exceptions import NotFound
from app.main import main
from app.models import Page, JsFile, Image, File, CssFile


@main.route('/')
def index():

    return redirect(url_for('admin.index'))


@main.route('/Team:<namespace>')
@main.route('/Team:<namespace>/<path:path>')
def wiki(namespace, path=None):
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


@main.route('/images')
def file_server():

    images = Image.query.all()
    files = File.query.all()

    return render_template('images.html', images=images, files=files)


@main.route('/ckeditor/<path:path>')
def ckedit(path):
    full_path = os.path.join(current_app.root_path, 'ckeditor', path)

    basename = os.path.basename(full_path)
    dirname = os.path.dirname(full_path)

    return send_from_directory(dirname, basename)