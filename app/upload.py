import HTMLParser
import os
import re
import requests

from flask import current_app

session = requests.Session()


class MyHTMLParser(HTMLParser.HTMLParser):
    """Parser class to get the POST data needed to submit"""

    tags = {}

    def handle_starttag(self, tag, attributes):
        """Function to do the parsing.
        The values input tags wpAutoSummary, wpEditToken and wpEdittime are needed to submit the edit text.
        wpEditToken, wpWatchthis, wpIgnoreWarning and wpUpload are needed to upload a file"""

        if tag == 'input':
            # Convert list of tuples into dictionary.
            attributes = dict(attributes)
            # Store the name/value pair of the tag in self.tags.
            if attributes['name'] in ['wpAutoSummary', 'wpEditToken', 'wpEdittime', 'wpWatchthis', 'wpIgnoreWarning', 'wpUpload']:
                self.tags[attributes['name']] = attributes['value']


class TextUploader(object):
    """Used for uploading text based models.
    Subclasses must define the render_external function, which will be used to upload."""

    def upload(self):

        edit_path = 'Team:{}'.format(current_app.config['NAMESPACE'])
        if self.url:
            edit_path += '/{}'.format(self.url)

        response = session.get('{}/wiki/index.php?title={}&action=edit'.format(current_app.config.get('BASE_URL'), edit_path))

        parser = MyHTMLParser()
        parser.feed(response.text)
        data = parser.tags

        html = self.render_external()
        data['wpTextbox1'] = html

        session.post("{}/wiki/index.php?title={}&action=submit".format(current_app.config.get('BASE_URL'), edit_path), data)

        return

    def render_external(self):
        """Render function must be defined for upload function to work"""
        raise NotImplementedError("Subclasses should implement this!")


class FileUploader(object):
    """Used for uploading binary models. Subclasses must have path defined"""

    def upload(self):

        response = session.get('{}/Special:Upload'.format(current_app.config.get('BASE_URL')))

        parser = MyHTMLParser()
        parser.feed(response.text)
        data = parser.tags

        data['wpDestFile'] = "{}_{}".format(current_app.config['NAMESPACE'], self.name)
        abs_path = os.path.join(current_app.static_folder, self.path)
        files = {'wpUploadFile': open(abs_path, 'rb')}

        response = session.post('{}/Special:Upload'.format(current_app.config.get('BASE_URL')), data=data, files = files)
        #Find the external path
        m = re.search('"(/wiki/images/.+?)"', response.text)
        self.external_path = m.group(1)

        return


def wiki_login(username, password):
    """Function to log in into iGEM wiki.
    The iGEM wiki API is broken, so we need to use the normal website."""

    # Login form
    login_data = {'username':username,
                  'password':password,
                  'Login':'Log in'}

    response = session.post('http://www.igem.org/Login', login_data)

    logged_in = 'successfully logged' in response.text

    return logged_in


def wiki_logout():
    """Log out of the iGEM wiki again"""
    response = session.get('http://igem.org/cgi/Logout.cgi')

    return