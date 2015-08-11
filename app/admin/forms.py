from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField, widgets, BooleanField, ValidationError
from wtforms.validators import EqualTo, Length, Regexp, InputRequired
from ..models import User


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class UploadForm(Form):

    def __init__(self, page_choices, image_choices, file_choices, css_choices, js_choices):
        super(UploadForm, self).__init__()
        self.pages.choices = page_choices
        self.images.choices = image_choices
        self.files.choices = file_choices
        self.css_files.choices = css_choices
        self.js_files.choices = js_choices

    pages = MultiCheckboxField('Pages')
    images = MultiCheckboxField('Images')
    files = MultiCheckboxField('Files')
    css_files = MultiCheckboxField('Css files')
    js_files = MultiCheckboxField('Js files')
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Submit')


class SettingsForm(Form):
    namespace = StringField('Namespace', validators=[InputRequired()])
    login_url = StringField('Login URL', validators=[InputRequired()])
    logout_url = StringField('Logout URL', validators=[InputRequired()])
    base_url = StringField('Base URL', validators=[InputRequired()])
    show_register_page = BooleanField('Show Admin Register Page')
    submit = SubmitField('Submit')


class LoginForm(Form):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log in')


class RegistrationForm(Form):
    username = StringField('Username', validators=[InputRequired(),
                                                   Length(1, 64),
                                                   Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                          'Usernames must have only letters,'
                                                          ' numbers, dots or underscores')])
    password = PasswordField('Password', validators=[InputRequired(),
                                                     EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])
    submit = SubmitField('Register')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')