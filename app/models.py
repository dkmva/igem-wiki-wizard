from flask import url_for, render_template_string, current_app
from flask.ext.login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager
from app.upload import TextUploader, FileUploader


class Person(db.Model):
    __tablename__ = 'persons'
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    name = db.Column(db.Unicode(64), unique=True)
    role = db.Column(db.Unicode(64))
    image = db.relationship("Image")
    description = db.Column(db.Text())
    image_id = db.Column(db.Integer, db.ForeignKey("images.id"))

    def __repr__(self):
        return u'{}'.format(self.name)


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

    def __repr__(self):
        return u'{}'.format(self.name)

    def render(self):
        kw = {'sections': self.sections,
              'persons': Person.query.order_by('position').all(),
              'main_menu': Page.query.order_by('position').all(),
              'images': {image.name: image for image in Image.query.all()},
              'files': {f.name: f for f in File.query.all()},
              'adv_main_menu': MenuItem.query.filter_by(parent=None),
              'image': self.image,
              'timeline': sorted(Timeline.query.all(), key= lambda x: x.date, reverse=True),
              'name': self.name,
              'css_files': CssFile.query.filter_by(active=True).order_by(CssFile.position),
              'js_files': JsFile.query.filter_by(active=True).order_by(JsFile.position),
              'namespace': current_app.config['NAMESPACE']}

        #return render_template('base.html', **kw)
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
            return url_for('wiki', path=self.page.url, namespace=current_app.config['NAMESPACE'])
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
    name = db.Column(db.Unicode(64))
    path = db.Column(db.Unicode(128))
    external_path = db.Column(db.Unicode(128))

    def __repr__(self):
        return u'{}'.format(self.name)


class File(db.Model, FileUploader):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    path = db.Column(db.Unicode(128))
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