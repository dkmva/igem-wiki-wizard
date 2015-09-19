import os
import re
import requests

from flask import request, jsonify, current_app, send_from_directory, url_for, redirect
from werkzeug.exceptions import NotFound

from app.main import main
from app.models import Page, Setting


@main.route('/')
def index():
    return redirect(url_for('admin.index'))


@main.route('/Team:<namespace>')
@main.route('/Team:<namespace>/<path:path>')
def wiki(namespace, path=None):
    if namespace != Setting.query.filter_by(name=u'namespace').first().value:
        raise NotFound()
    page = Page.query.filter_by(url=path or '').first_or_404()

    return page.render()


def make_reference_link(reference):
    return '<a href="http://dx.doi.org/{}" target="_blank">{}</a>'.format(*reference.groups()[::-1])


@main.route('/jslibs/<path:path>')
def jslibs(path):
    full_path = os.path.join(current_app.root_path, 'jslibs', path)

    basename = os.path.basename(full_path)
    dirname = os.path.dirname(full_path)

    return send_from_directory(dirname, basename)


@main.route('/getref', methods=['POST'])
def getref():
    doi = request.get_json()['doi']
    status_code = 500
    while status_code == 500:
        r = requests.get('http://dx.doi.org/' + doi, headers={'accept': 'text/x-bibliography; style=apa'})
        status_code = r.status_code

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
