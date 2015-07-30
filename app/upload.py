import HTMLParser
import cookielib
import os
import re
import urllib
import urllib2
import MultipartPostHandler
from flask import current_app

# Cookie for storing login
cookie = cookielib.CookieJar()
# Opener for login and submitting data.
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie), MultipartPostHandler.MultipartPostHandler)

file_path = os.environ.get('OPENSHIFT_DATA_DIR', os.path.join(os.path.dirname(__file__), 'static'))


class MyHTMLParser(HTMLParser.HTMLParser):
    """Parser class to get the POST data needed to submit"""

    tags = {}

    def handle_starttag(self, tag, attributes):
        """Function to do the parsing.
        The values input tags wpAutoSummary, wpEditToken and wpEdittime are needed to submit the edit form."""

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

        resp = opener.open('{}/wiki/index.php?title={}&action=edit'.format(current_app.config.get('BASE_URL'), edit_path))

        parser = MyHTMLParser()
        parser.feed(resp.read().decode('utf-8'))

        data = parser.tags

        html = self.render_external()
        data['wpTextbox1'] = html.encode('utf-8')

        encoded_data = urllib.urlencode(data)

        req = urllib2.Request("{}/wiki/index.php?title={}&action=submit".format(current_app.config.get('BASE_URL'), edit_path), encoded_data.encode('utf-8'))

        resp = opener.open(req)

    def render_external(self):
        """Render function must be defined for upload function to work"""
        return


class FileUploader(object):
    """Used for uploading binary models. Subclasses must have path defined"""

    def upload(self):

        resp = opener.open('{}/Special:Upload'.format(current_app.config.get('BASE_URL')))

        parser = MyHTMLParser()
        parser.feed(resp.read())

        data = parser.tags

        abs_path = os.path.join(file_path, self.path)

        with open(abs_path.encode('utf-8'), 'rb') as f:
            data['wpDestFile'] = "{}_{}".format(current_app.config['NAMESPACE'], self.name).encode('utf-8')
            data['wpUploadFile'] = f
            resp = opener.open('{}/Special:Upload'.format(current_app.config.get('BASE_URL')), data)

            #Find the external path
            html = resp.read()
            m = re.search('"(/wiki/images/.+?)"', html)
            self.external_path = m.group(1)

        return


def wiki_login(username, password):
    """Function to log in into iGEM wiki.
    The iGEM wiki API is broken, so we need to use the normal website."""

    # Login form
    login_data = {'username':username,
                  'password':password,
                  'Login':'Log in'}
    # Encode the data
    encoded_data = urllib.urlencode(login_data)
    # Make the request
    request = urllib2.Request(current_app.config.get('LOGIN_URL'), encoded_data.encode('utf-8'))
    # Do the login
    response = opener.open(request)

    response = response.read()

    logged_in = 'successfully logged' in response

    return logged_in


def wiki_logout():
    # Make the request
    request = urllib2.Request(current_app.config.get('LOGOUT_URL'))
    # Do the login
    response = opener.open(request)

    response = response.read()

    logged_out = 'successfully logged' in response

    return logged_out