import os
import random
import string
import yaml

from app.models import db, MenuItem, Page, Section, Entity, Setting

pages = [
    (u'Home', None),
    (u'Team', u'Team'),
    (u'Description', u'Description'),
    (u'Experiments & Protocols', u'Experiments'),
    (u'Results', u'Results'),
    (u'Design', u'Design'),
    (u'Team Parts', u'Parts'),
    (u'Basic Parts', u'Basic_Part'),
    (u'Composite Parts', u'Composite_Part'),
    (u'Part Collection', u'Part_Collection'),
    (u'Notebook', u'Notebook'),
    (u'Attributions', u'Attributions'),
    (u'Collaborations', u'Collaborations'),
    (u'Human Practices', u'Practices'),
    (u'Safety', u'Safety'),
    (u'Modeling', u'Modeling'),
    (u'Measurement', u'Measurement'),
    (u'Software', u'Software'),
    (u'Entrepreneurship', u'Entrepreneurship')]

menu = [
    (None, 1, None),
    (None, 2, None),
    (u'Project', None, None),
    (None, 3, 3),
    (None, 4, 3),
    (None, 5, 3),
    (None, 6, 3),
    (u'Parts', None, None),
    (None, 7, 8),
    (None, 8, 8),
    (None, 9, 8),
    (None, 10, 8),
    (None, 11, None),
    (None, 12, None),
    (None, 13, None),
    (None, 14, None),
    (None, 15, None),
    (None, 16, None),
    (None, 17, None),
    (None, 18, None),
    (None, 19, None)
]

default_cfg = {'DEBUG': True,
                'SECRET_KEY': ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(50)]),
                 'SQLALCHEMY_COMMIT_ON_TEARDOWN': True,
               }

default_settings = [
    Setting(name=u'namespace', value=u''),
    Setting(name=u'base_url', value=u'2015.igem.org'),
    Setting(name=u'show_register_page', value=u'true'),
    Setting(name=u'theme', value=u'simple')
]


def make_config(config_folder):
    with open(os.path.join(config_folder, 'config.yml'), 'w') as f:
        f.write(yaml.safe_dump(default_cfg, default_flow_style=False))


def install_data():

    for setting in default_settings:
        db.session.add(setting)

    for i, (name, url) in enumerate(pages, 1):
        page = Page(name=name, url=url, template=u'page.html', position=i)
        db.session.add(page)

    for i, (name, page_id, parent_id) in enumerate(menu, 1):
        menuitem = MenuItem(name=name, page_id=page_id, parent_id=parent_id, position=i)
        db.session.add(menuitem)

    sec1html = u'<p>Content for pages can be written in the administration panel' \
               u' under Content -&gt; Pages or Content -&gt; Sections.</p>'

    section = Section(name=u'Introduction', html=sec1html, page_id=1, template=u'section.html', position=1)
    db.session.add(section)
    section = Section(name=u'Members', html=u'', page_id=2, template=u'members.html', position=1)
    db.session.add(section)

    mem1desc = u'<p>Information about team members can be written in the administration panel' \
               u' under Content -&gt; Entities.</p><p>Entities with role assigned as Member will be shown here.</p>'
    member = Entity(name=u'Team Member 1', description=mem1desc, role=u'Member', position=1)
    db.session.add(member)
    member = Entity(name=u'Team Member 2', description=u'', role=u'Member', position=2)
    db.session.add(member)

    db.session.commit()
