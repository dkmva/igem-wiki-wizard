from flask.ext.admin import Admin

from app.models import Page, Reference, Entity, MenuItem, User, UploadedFile, db, Section, Timeline
from app.admin.views import EntityView, PageView, StaticFiles, Theme, MenuItemView, ReferenceView, \
    SettingsView, UploadView, SelectThemeView, IndexView, UserView, UploadedFileView, SectionView, TimeLineView


def create_admin(app):
    admin = Admin(app, name='Wiki Wizard', template_mode='bootstrap3', base_template='admin/my_master.html', index_view=IndexView())

    admin.add_view(PageView(Page, db.session, name='Pages', category='Content'))
    admin.add_view(SectionView(Section, db.session, name='Sections', category='Content'))
    admin.add_view(EntityView(Entity, db.session, name='Entities', category='Content'))
    admin.add_view(TimeLineView(Timeline, db.session, category='Content'))
    admin.add_view(ReferenceView(Reference, db.session, name='References', category='Content'))
    admin.add_view(MenuItemView(MenuItem, db.session, name='Menu', category='Content'))
    admin.add_view(StaticFiles(app.static_folder, '/static/', name='Files'))
    admin.add_view(Theme(app.config['THEME_PATHS'][0], '/_themes/', name='Theme files', category='Theme'))

    admin.add_view(SettingsView(name='Settings'))
    admin.add_view(UploadView(name='Upload'))
    admin.add_view(SelectThemeView(name='Select Theme', category='Theme'))

    admin.add_view(UserView(User, db.session, name='Users', category='Advanced'))
    admin.add_view(UploadedFileView(UploadedFile, db.session, name='Uploaded Files', category='Advanced'))

    return admin
