from itertools import groupby
from operator import itemgetter
import os
import re

from flask import url_for
from flask.ext.login import UserMixin, LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.themes2 import render_theme_template
from sqlalchemy import desc
from sqlalchemy.orm import backref
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()
login_manager = LoginManager()


class Timeline(db.Model):
    __tablename__ = 'timeline'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    title = db.Column(db.Unicode(64))
    html = db.Column(db.UnicodeText(length=2**31))

    def __repr__(self):
        return u'{}'.format(self.title)


class Section(db.Model):
    __tablename__ = 'sections'
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    name = db.Column(db.Unicode(64))
    image = db.Column(db.Unicode(64))
    template = db.Column(db.Unicode(64))
    html = db.Column(db.UnicodeText(length=2**31))
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'))

    def __repr__(self):
        return u'{}'.format(self.name)


class Page(db.Model):
    __tablename__ = 'pages'
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    name = db.Column(db.Unicode(64), unique=True)
    url = db.Column(db.Unicode(64), unique=True)
    image = db.Column(db.Unicode(64))
    template = db.Column(db.Unicode(64))
    sections = db.relationship('Section', backref='page', order_by='Section.position')

    def __unicode__(self):
        return self.name

    @property
    def href(self):
        return url_for('main.wiki', namespace=Setting.query.filter_by(name=u'namespace').first().value, path=self.url or None)

    def render(self):

        ctx = {
            'page': self,
            'entities': Entity.query.order_by('position').all(),
            'timeline': Timeline.query.order_by(desc('date')).all(),
            'main_menu': MenuItem.query.filter_by(parent=None).order_by('position').all() or Page.query.order_by('position').all(),
            'references': []
        }
        theme = Setting.query.filter_by(name=u'theme').first().value

        # Make reference list
        [re.sub(cite_pattern, convert_references(ctx['references']), sec.html) for sec in self.sections]

        rendered = render_theme_template(theme, 'pages/'+self.template, **ctx)
        rendered = re.sub(cite_pattern, convert_references(ctx['references']), rendered)
        return rendered

    def render_external(self):
        rendered = self.render()
        rendered = re.sub(theme_pattern, convert_external, rendered)
        return rendered


class Entity(db.Model):
    __tablename__ = 'entities'
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    name = db.Column(db.Unicode(64), unique=True)
    role = db.Column(db.Unicode(64))
    image = db.Column(db.Unicode(64))
    description = db.Column(db.Text())
    link = db.Column(db.Unicode(128))

    def __repr__(self):
        return u'{}'.format(self.name)


class Reference(db.Model):
    __tablename__ = 'references'
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.UnicodeText(length=2**31))
    ref_id = db.Column(db.Unicode(32), unique=True)

    def __repr__(self):
        return u'{}'.format(self.reference)


class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    name = db.Column(db.Unicode(64))
    url = db.Column(db.Unicode(64))
    page_id = db.Column(db.Integer, db.ForeignKey("pages.id"))
    page = db.relationship('Page')
    parent_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"))
    parent = db.relationship('MenuItem', remote_side=[id], backref=backref('children', order_by='MenuItem.position'))

    def __repr__(self):
        if self.page:
            return u'{}'.format(self.page)
        return u'{}'.format(self.name)

    @property
    def href(self):
        if self.page:
            return self.page.href
        return u'{}'.format(self.url or "")


class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(128))
    value = db.Column(db.Unicode(128))

    def __unicode__(self):
        return self.value


class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(128))
    external_path = db.Column(db.Unicode(256))

    def __unicode__(self):
        return self.name


# Login to the admin page etc..
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode(64), unique=True)
    password_hash = db.Column(db.Unicode(128))

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = unicode(generate_password_hash(password))

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


cite_pattern = re.compile(r'\\cite\{(.*?)\}')
theme_pattern = re.compile(r'(/_theme.*?|/static.*?)(?=[")])')


def convert_references(references):
    def replace_reference(matchobj):
        ids = matchobj.groups()[0].split(',')

        # Build list of references from ids.
        refs = []
        for id in ids:
            r = Reference.query.filter_by(ref_id=id).first()
            if r:
                refs.append(r.reference)
            else:
                refs.append(None)

        # Add new references to the reference list.
        for ref in refs:
            if ref and ref not in references:
                references.append(ref)

        # Sort references, change unknown references to ? and  compress 3 or more sequential references.
        refs = sorted([references.index(ref)+1 if ref else -1 for ref in refs])
        refs = [map(itemgetter(1), g) for k, g in groupby(enumerate(refs), lambda (i,x): i-x)]
        refs = ['{}-{}'.format(min(e), max(e)) if len(e) > 2 else ','.join([str(e) for e in e]) for e in refs]
        return '[{}]'.format(','.join(refs)).replace('-1,', '?,').replace('-1]', '?]')
    return replace_reference


def convert_external(match_obj):
    m = match_obj.groups()[0]
    if m.count('?'):
        m = '/'.join(m.split('/')[-2:]).replace('.', '')
        return '/Team:{}/{}'.format(Setting.query.filter_by(name=u'namespace').first().value, m)
    else:
        f = UploadedFile.query.filter_by(name=os.path.basename(m)).first()
        if f:
            return 'http://{}{}'.format(Setting.query.filter_by(name=u'base_url').first().value, f)
        else:
            return m
