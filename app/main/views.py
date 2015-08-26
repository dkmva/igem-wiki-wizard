import os
import re
from flask import url_for, redirect, current_app, render_template, send_from_directory, request, jsonify
import requests
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


def make_reference_link(reference):
    return '<a href="http://dx.doi.org/{}" target="_blank">{}</a>'.format(*reference.groups()[::-1])

@main.route('/getref', methods=['POST'])
def getref():
    doi = request.get_json()['doi']
    r = requests.get('http://dx.doi.org/' + doi, headers={'accept': 'text/x-bibliography; style=apa'})
    r.encoding = 'utf-8'
    reference = r.text

    try:
        firstauthor = reference.split(',')[0]
        year = re.search('\((\d*)\)', reference).groups()[0]
        id = '{}{}'.format(firstauthor, year)
        reference = re.sub('(doi:(.*))', make_reference_link, reference)
        response = jsonify({'reference': reference, 'id': id})
    except AttributeError:
        response = jsonify({'error': 'Could not resolve DOI.'})
        response.status_code = 404
    return response