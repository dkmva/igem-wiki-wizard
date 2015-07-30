import os
import random
import string
import yaml

from app import db
from app.models import MenuItem, Page, Section, Person
from app.themes import load_theme

pages = [
    ('Home', None),
    ('Team', 'Team'),
    ('Description', 'Description'),
    ('Experiments & Protocols', 'Experiments'),
    ('Results', 'Results'),
    ('Design', 'Design'),
    ('Team Parts', 'Parts'),
    ('Basic Parts', 'Basic_Part'),
    ('Composite Parts', 'Composite_Part'),
    ('Part Collection', 'Part_Collection'),
    ('Notebook', 'Notebook'),
    ('Attributions', 'Attributions'),
    ('Collaborations', 'Collaborations'),
    ('Human Practices', 'Practices'),
    ('Safety', 'Safety'),
    ('Modeling', 'Modeling'),
    ('Measurement', 'Measurement'),
    ('Software', 'Software'),
    ('Entrepreneurship', 'Entrepreneurship')]

menu = [
    (None, 1, None),
    (None, 2, None),
    ('Project', None, None),
    (None, 3, 3),
    (None, 4, 3),
    (None, 5, 3),
    (None, 6, 3),
    ('Parts', None, None),
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

default_cfg = {'USER': {'BASE_URL': 'http://2015.igem.org',
                        'LOGIN_URL': 'http://www.igem.org/Login',
                        'LOGOUT_URL': 'http://igem.org/cgi/Logout.cgi',
                        'NAMESPACE': None,
                        'SHOW_REGISTER_PAGE': True},
               'ADVANCED': {'DEBUG': True,
                            'SECRET_KEY': ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(50)]),
                            'SQLALCHEMY_COMMIT_ON_TEARDOWN': True
}}


def make_config(config_folder):
    with open(os.path.join(config_folder, 'config.yml'), 'w') as f:
        f.write(yaml.safe_dump(default_cfg, default_flow_style=False))


def install():

    load_theme('simple')
            
    for i, (name, url) in enumerate(pages, 1):
        page = Page(name=name, url=url, template_id=1, position=i)
        db.session.add(page)

    for i, (name, page_id, parent_id) in enumerate(menu, 1):
        menuitem = MenuItem(name=name, page_id=page_id, parent_id=parent_id, position=i)
        db.session.add(menuitem)


    sec1html = '<p>Content for pages can be written in the administration panel under Content -&gt; Pages or Content -&gt; Sections.</p>'

    section = Section(name='Introduction', html=sec1html, page_id=1, template_id=3, position=1)
    db.session.add(section)
    section = Section(name='Members', html='', page_id=2, template_id=2, position=1)
    db.session.add(section)

    mem1desc = '<p>Information about team members can be written in the administration panel under Content -&gt; Persons.</p><p>Persons with role assigned as Member will be shown here.</p>'
    member = Person(name='Team Member 1', description=mem1desc, role='Member', position=1)
    db.session.add(member)
    member = Person(name='Team Member 2', description='', role='Member', position=2)
    db.session.add(member)

    db.session.commit()