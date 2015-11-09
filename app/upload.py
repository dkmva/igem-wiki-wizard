import os
import re
from flask import render_template_string
import requests
from bs4 import BeautifulSoup
from app import models

from app.models import Setting, UploadedFile, Page, db, Entity, MenuItem
from app.utils import get_theme_folder

session = requests.Session()


def scrape_inputs(html):
    """Function to scrape input data needed to submit.
    The values input tags wpAutoSummary, wpEditToken and wpEdittime are needed to submit the edit text.
    wpEditToken, wpWatchthis, wpIgnoreWarning and wpUpload are needed to upload a file"""
    soup = BeautifulSoup(html, 'html.parser')
    return {inp['name']: inp['value'] for inp in soup.find_all('input') if inp['name'] in ['wpAutoSummary', 'wpEditToken', 'wpEdittime', 'wpWatchthis', 'wpIgnoreWarning', 'wpUpload']}


def wiki_login(username, password):
    """Function to log in into iGEM wiki.
    The iGEM wiki API is broken, so we need to use the normal website."""

    # Login form
    login_data = {'username':username,
                  'password':password,
                  'Login':'Log in'}

    response_code = 500
    while response_code != 200:
        response = session.post('http://www.igem.org/Login', login_data)
        response_code = response.status_code

    logged_in = 'successfully logged' in response.text

    return logged_in


def wiki_logout():
    """Log out of the iGEM wiki again"""
    response_code = 500
    while response_code != 200:
        response = session.get('http://igem.org/cgi/Logout.cgi')
        response_code = response.status_code

    return

theme_pattern = re.compile(r'(/_theme.*?|/static.*?)(?=[")])')


def upload_template(template):
    root = get_theme_folder('templates/includes')
    abs_path = os.path.join(root, template)
    basename = os.path.basename(abs_path)

    with open(abs_path) as f:
        content = f.read()

    ctx = {
            'entities': Entity.query.order_by('position').all(),
            'main_menu': MenuItem.query.filter_by(parent=None).order_by('position').all() or Page.query.order_by('position').all(),
            '_theme': Setting.query.filter_by(name=u'theme').first().value
        }
    content = render_template_string(content, **ctx)
    content = re.sub(theme_pattern, models.convert_external, content)

    path = os.path.splitext(basename)[0]

    return upload_wiki_text(content, path, prefix='Template:')


def upload_page(name):
    page = Page.query.filter_by(name=name).first()

    content = page.render_external()
    path = page.url

    return upload_wiki_text(content, path)


def upload_binary_file(root, path):
    abs_path = os.path.join(root, path)
    basename = os.path.basename(abs_path)

    base_url = Setting.query.filter_by(name='base_url').first().value
    namespace = Setting.query.filter_by(name='namespace').first().value

    response_code = 0
    while response_code != 200:
        response = session.get('http://{}/Special:Upload'.format(base_url))
        response_code = response.status_code

    data = scrape_inputs(response.text)

    data['wpDestFile'] = '{}_{}'.format(namespace, basename)
    files = {'wpUploadFile': open(abs_path, 'rb')}

    response_code = 0
    while response_code != 200:
        response = session.post('http://{}/Special:Upload'.format(base_url), data=data, files=files)
        response_code = response.status_code

    # Find the external path
    m = re.search('"(/wiki/images/.+?)"', response.text)
    external_path = m.group(1)

    uploaded_file = UploadedFile.query.filter_by(name=basename)
    if not uploaded_file:
        uploaded_file = UploadedFile(name=basename, external_path=external_path)
    uploaded_file.external_path = external_path
    db.session.add(uploaded_file)


file_pattern = re.compile(r'(?<=url\()([\'"]?.*?)(?=[?#\'")])')


def convert_external(match_obj):
    m = match_obj.groups()[0]
    m0 = ''
    if m[0] == '"' or m[0] == '\'':
        m0 = m[0]
        m = m[1:]
    return '{}{}'.format(m0, UploadedFile.query.filter_by(name=os.path.basename(m)).external_path) or m


def upload_text_file(root, path):
    abs_path = os.path.join(root, path)
    basename = os.path.basename(abs_path)

    with open(abs_path) as f:
        content = f.read()

    content = re.sub(file_pattern, convert_external, content)

    path = basename.replace('.', '')

    return upload_wiki_text(content, path)


def upload_wiki_text(content, path, prefix=''):
    base_url = Setting.query.filter_by(name=u'base_url').first().value
    namespace = Setting.query.filter_by(name=u'namespace').first().value

    edit_path = '{}Team:{}'.format(prefix, namespace)
    if path:
        edit_path += '/{}'.format(path)

    response_code = 0
    while response_code != 200:
        response = session.get('http://{}/wiki/index.php?title={}&action=edit'.format(base_url, edit_path))
        response_code = response.status_code

    data = scrape_inputs(response.text)
    data['wpTextbox1'] = content

    response_code = 0
    while response_code != 200:
        response = session.post("http://{}/wiki/index.php?title={}&action=submit".format(base_url, edit_path), data)
        response_code = response.status_code
    return