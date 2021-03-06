from flask.ext.wtf import Form
from flask.ext.wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField, BooleanField, PasswordField, ValidationError
from wtforms.validators import InputRequired, Length, Regexp, EqualTo
from app.models import User


class SettingsForm(Form):
    namespace = StringField('Namespace', validators=[InputRequired()])
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


class ThemeForm(Form):
    theme = FileField('Theme', validators=[
        FileRequired(),
        FileAllowed(['zip'], 'Zip files only!')
    ])
    submit = SubmitField('Upload')
