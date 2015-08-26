from flask.ext.admin import Admin
from .views import IndexView, PageView, SectionView, EntityView, TimeLineView, ImageView, FileView, \
    TemplateView, CssView, JsView, ThemeView, SettingsView, UploadView, MenuItemView, UserView, ReferenceView
from ..models import db, Page, Section, Entity, Timeline, Image, File, Template, CssFile, JsFile, MenuItem, User, \
    Reference

admin = Admin(name='Wiki Wizard', index_view=IndexView(), base_template='admin/my_master.html')

admin.add_view(PageView(Page, db.session, name='Pages', category='Content'))
admin.add_view(SectionView(Section, db.session, name='Sections', category='Content'))
admin.add_view(EntityView(Entity, db.session, name='Entities', category='Content'))
admin.add_view(TimeLineView(Timeline, db.session, category='Content'))
admin.add_view(MenuItemView(MenuItem, db.session, name='Menu', category='Content'))
admin.add_view(ReferenceView(Reference, db.session, name='References', category='Content'))

admin.add_view(ImageView(Image, db.session, name='Images', category='Files'))
admin.add_view(FileView(File, db.session, name='Files', category='Files'))

admin.add_view(TemplateView(Template, db.session, name='Templates', category='Theme'))
admin.add_view(CssView(CssFile, db.session, name='CSS Files', category='Theme'))
admin.add_view(JsView(JsFile, db.session, name='JavaScript Files', category='Theme'))
admin.add_view(ThemeView(name='Save/Load Theme', category='Theme'))

admin.add_view(SettingsView(name='Settings'))
admin.add_view(UploadView(name='Upload'))

admin.add_view(UserView(User, db.session, name='Users', category='Advanced'))