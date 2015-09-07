from itertools import groupby
from operator import itemgetter
import re
from flask import url_for, render_template_string, current_app
from flask.ext.login import UserMixin, LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from scss import Compiler
from sqlalchemy import desc
from werkzeug.security import check_password_hash, generate_password_hash

from app.upload import TextUploader, FileUploader

db = SQLAlchemy()
login_manager = LoginManager()


class Entity(db.Model):
    __tablename__ = 'entities'
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    name = db.Column(db.Unicode(64), unique=True)
    role = db.Column(db.Unicode(64))
    image = db.relationship("Image")
    description = db.Column(db.Text())
    link = db.Column(db.Unicode(128))
    image_id = db.Column(db.Integer, db.ForeignKey("images.id"))

    def __repr__(self):
        return u'{}'.format(self.name)


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
            return '[{}]'.format(','.join(refs)).replace('-1', '?')
        return replace_reference

cite_pattern = re.compile(r'\\cite\{(.*?)\}')


class Page(db.Model, TextUploader):
    __tablename__ = 'pages'
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    name = db.Column(db.String(64), unique=True)
    url = db.Column(db.String(64), unique=True)
    image = db.relationship("Image")
    image_id = db.Column(db.Integer, db.ForeignKey("images.id"))
    template = db.relationship("Template")
    template_id = db.Column(db.Integer, db.ForeignKey("templates.id"))
    sections = db.relationship('Section', backref='page', order_by='Section.position')

    @property
    def href(self):
        return url_for('main.wiki', path=self.url, namespace=current_app.config['NAMESPACE'])

    def __repr__(self):
        return u'{}'.format(self.name)

    def render(self):
        kw = {'sections': self.sections,
              'entities': Entity.query.order_by('position').all(),
              'main_menu': MenuItem.query.filter_by(parent=None).all() or Page.query.order_by('position').all(),
              'images': {image.name: image for image in Image.query.all()},
              'files': {f.name: f for f in File.query.all()},
              'image': self.image,
              'timeline': Timeline.query.order_by(desc(Timeline.date)).all(),
              'name': self.name,
              'css_files': [f[0] for f in CssFile.query.with_entities(CssFile.url).filter_by(active=True).order_by(CssFile.position).all()],
              'js_files': [f[0] for f in JsFile.query.with_entities(JsFile.url).filter_by(active=True).order_by(JsFile.position).all()],
              'namespace': current_app.config['NAMESPACE']}

        rendered_sections = []
        references = []
        for section in self.sections:
            if section.template:
                section_html = section.template.render(section=section, references=references, **kw)
                section_html = re.sub(cite_pattern, convert_references(references), section_html)
                rendered_sections.append(section_html)
        kw.update({'rendered_sections': rendered_sections})
        return self.template.render(**kw)

    def render_external(self):
        html = self.render()
        images = {image.name: image for image in Image.query.all()}
        files = {f.name: f for f in File.query.all()}

        for image in images.values():
            html = html.replace(url_for('static', filename=image.path), str(image.external_path))
        for f in files.values():
            html = html.replace(url_for('static', filename=f.path), str(f.external_path))

        return html


class StaticFile(TextUploader):
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    url = db.Column(db.String(64), unique=True)
    active = db.Column(db.Boolean)
    content = db.Column(db.UnicodeText(length=2**31))

    def __repr__(self):
        return u'{}'.format(self.url)

    def render(self):
        kw = {'files': {f.name: f for f in File.query.all()},
              'images': {image.name: image for image in Image.query.all()},
              'namespace': current_app.config['NAMESPACE']}

        return render_template_string(self.content, **kw)

    def render_external(self):
        html = self.render()
        images = {image.name: image for image in Image.query.all()}
        files = {f.name: f for f in File.query.all()}

        for image in images.values():
            html = html.replace(url_for('static', filename=image.path), str(image.external_path))
        for f in files.values():
            html = html.replace(url_for('static', filename=f.path), str(f.external_path))

        return html


class CssFile(db.Model, StaticFile):
    __tablename__ = 'css_files'

    def render(self):
        rendered = super(CssFile, self).render()
        return Compiler().compile_string(rendered)


class JsFile(db.Model, StaticFile):
    __tablename__ = 'js_files'


class Template(db.Model):
    __tablename__ = 'templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    content = db.Column(db.UnicodeText(length=2**31))

    def render(self, **kwargs):
        return render_template_string(self.content, **kwargs)

    def __repr__(self):
        return u'{}'.format(self.name)


class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    name = db.Column(db.String(64))
    url = db.Column(db.String(64))
    page_id = db.Column(db.Integer, db.ForeignKey("pages.id"))
    page = db.relationship('Page')
    parent_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"))
    parent = db.relationship('MenuItem', remote_side=[id], backref='children')

    def __repr__(self):
        if self.page:
            return u'{}'.format(self.page)
        return u'{}'.format(self.name)

    @property
    def href(self):
        if self.page:
            return self.page.href
        return u'{}'.format(self.url or "")


class Section(db.Model):
    __tablename__ = 'sections'
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    name = db.Column(db.String(64), unique=True)
    image = db.relationship("Image")
    image_id = db.Column(db.Integer, db.ForeignKey("images.id"))
    template = db.relationship('Template')
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'))
    html = db.Column(db.UnicodeText(length=2**31))
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'))

    def __repr__(self):
        return u'{}'.format(self.name)


class Image(db.Model, FileUploader):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, nullable=False)
    path = db.Column(db.Unicode(128), unique=True, nullable=False)
    external_path = db.Column(db.Unicode(128))

    def __repr__(self):
        return u'{}'.format(self.name)


class File(db.Model, FileUploader):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, nullable=False)
    path = db.Column(db.Unicode(128), unique=True, nullable=False)
    external_path = db.Column(db.Unicode(128))

    def __repr__(self):
        return u'{}'.format(self.name)


class Timeline(db.Model):
    __tablename__ = 'timeline'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    title = db.Column(db.String(64))
    html = db.Column(db.UnicodeText(length=2**31))

    def __repr__(self):
        return u'{}'.format(self.title)


class Reference(db.Model):
    __tablename__ = 'references'
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.UnicodeText(length=2**31))
    ref_id = db.Column(db.Unicode(32), unique=True)

    def __repr__(self):
        return u'{}'.format(self.reference)


# Login to the admin page etc..
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128))

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)