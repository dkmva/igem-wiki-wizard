# From Flask-Bootstrap
import os
import re

from flask import request, current_app
from jinja2.ext import Extension
from wtforms import HiddenField

from app.models import Setting


def is_hidden_field_filter(field):
    return isinstance(field, HiddenField)


def css_sanitizer(string):
    return re.sub('[^_a-zA-Z0-9-]*', '', string)


rx = re.compile(r'\{\%\s*wiki_include\s+(?P<tmpl>[^\s]+)\s*\%\}',
        re.IGNORECASE)


class WikiInclude(Extension):

    def preprocess(self, source, name, filename=None):
        lastpos = 0
        while 1:
            m = rx.search(source, lastpos)
            if not m:
                break

            lastpos = m.end()
            d = m.groupdict()
            if 'namespace' in request.view_args:
                tmpl = d['tmpl'].strip()
                tmpl = tmpl[0] + 'includes/' + tmpl[1:]
                replaced = '{% include theme(' + tmpl + ') %}'
            else:
                tmpl = d['tmpl'].strip()[1:-1]
                tmpl = os.path.splitext(tmpl)[0]
                replaced = '{{ \'{{\' }}' +\
                           'Team:{}/'.format(Setting.query.filter_by(name=u'namespace').first().value) +\
                           tmpl +\
                           '{{ \'}}\' }}'
            source = ''.join([
                source[:m.start()],
                replaced,
                source[m.end():]
                ])

        return source


def get_theme_folder(foldername):
    theme = Setting.query.filter_by(name=u'theme').first().value
    theme_folder = os.path.join(current_app.config['THEME_PATHS'][0], theme, foldername)
    return theme_folder
