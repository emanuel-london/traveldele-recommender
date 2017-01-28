"""Implements forms used in the dashboard Blueprint ui."""


from flask_wtf import FlaskForm
from wtforms import (
    StringField, SubmitField,
)
from wtforms.validators import Required


class ProfileFormMixin():
    """Base form for question management forms."""
    name = StringField('Name', validators=[Required()])


class NewProfileForm(FlaskForm, ProfileFormMixin):
    """Form to add a new question to the document database."""
    submit = SubmitField('Add profile')


class EditProfileForm(FlaskForm, ProfileFormMixin):
    """Form to edit an existing question in the document database."""
    submit = SubmitField('Save changes')
