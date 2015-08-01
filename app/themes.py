import os
import zipfile
from flask import current_app
import yaml
from .models import db, Template, Image, File, JsFile, CssFile


def compile_theme(theme_name):

    theme = {
        'templates': [],
        'css_files': [],
        'js_files': [],
        'images': [],
        'files': []
    }
    with zipfile.ZipFile(os.path.join(current_app.root_path, 'themes', '{}.zip'.format(theme_name)), 'w') as zf:

        for template in Template.query.all():
            zf.writestr(template.name, template.content.encode('utf-8'))
            theme['templates'].append(template.name)

        for css in CssFile.query.filter_by(active=True).all():
            zf.writestr(css.url, css.content.encode('utf-8'))
            theme['css_files'].append(css.url)

        for js in JsFile.query.filter_by(active=True).all():
            zf.writestr(js.url, js.content.encode('utf-8'))
            theme['js_files'].append(js.url)

        for image in Image.query.all():
            zf.write(os.path.join(current_app.static_folder, image.path), os.path.basename(image.name))
            theme['images'].append(image.name)

        for f in File.query.all():
            zf.write(os.path.join(current_app.static_folder, f.path), os.path.basename(f.name))
            theme['files'].append(f.name)

        zf.writestr('theme.yml', yaml.safe_dump(theme, default_flow_style=False))


def load_theme(theme_name):

    models = []

    with zipfile.ZipFile(os.path.join(current_app.root_path, 'themes', '{}.zip'.format(theme_name)), 'r') as zf:
        with zf.open('theme.yml') as yml:
            theme = yaml.load(yml)

        for e in theme['templates']:
            with zf.open(e) as f:
                models.append(Template(name=f.name, content=unicode(f.read())))

        for i, e in enumerate(theme['css_files'], 1):
            with zf.open(e) as f:
                models.append(CssFile(url=f.name, content=unicode(f.read()), position=i, active=True))

        for i, e in enumerate(theme['js_files'], 1):
            with zf.open(e) as f:
                models.append(JsFile(url=f.name, content=unicode(f.read()), position=i, active=True))

        for f in theme['images']:
            zf.extract(f, path=current_app.static_folder)
            models.append(Image(name=unicode(f), path=unicode(f)))

        for f in theme['files']:
            zf.extract(f, path=current_app.static_folder)
            models.append(File(name=unicode(f), path=unicode(f)))

    db.session.add_all(models)
    db.session.commit()
