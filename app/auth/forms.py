"""Implements forms used in the authentication ui."""


__all__ = ['LoginForm', 'PasswordForm', 'PasswordResetForm']


from flask_wtf import FlaskForm
from wtforms import (
    BooleanField, HiddenField, PasswordField,
    StringField, SubmitField,
)
from wtforms.fields.html5 import EmailField
from wtforms.validators import (
    Email, Required, ValidationError,
)


from app.utils.models import User


class LoginForm(FlaskForm):
    """Form used too login an existing user."""
    username = StringField('Username', validators=[Required()])

    password = PasswordField('Password', validators=[Required()])

    remember_me = BooleanField('Keep me logged in')

    submit = SubmitField('Login')


class PasswordForm(FlaskForm):
    """Form used to request a password reset link."""
    email = EmailField('Email address', validators=[Required(), Email()])

    submit = SubmitField('Reset Password')

    @staticmethod
    def validate_email(dummy_form, field):
        """Check that the email exists in the system."""
        user = User.query.filter_by(email=field.data).first()
        if user is None:
            raise ValidationError('The supplied email address is not \
                                  associated with any accounts.')


class PasswordResetForm(FlaskForm):
    """Form used to set a new password."""
    reset_token = HiddenField('Reset Token')
    password = PasswordField('New Password', validators=[Required()])
    confirm_password = PasswordField('Confirm New Password', validators=[
        Required()
    ])
    submit = SubmitField('Set Password')

    @staticmethod
    def validate_confirm_password(form, field):
        """Check that password fields match."""
        if field.data != form.password.data:
            raise ValidationError('Passwords must match.')
