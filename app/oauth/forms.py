"""Implements forms used in the OAuth2 configuration ui."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    StringField, SubmitField, TextAreaField,
)
from wtforms.validators import Required


class ClientFormMixin():
    """Base form for question management forms."""
    name = StringField('Name', validators=[Required()])
    description = TextAreaField('Description')
    redirect = TextAreaField('Redirect URIs', validators=[Required()])
    scopes = TextAreaField('Default Scopes', validators=[Required()])
    confidential = BooleanField('Confidential?')


class NewClientForm(FlaskForm, ClientFormMixin):
    """Form to add a new question to the document database."""
    submit = SubmitField('Add client')


class EditClientForm(FlaskForm, ClientFormMixin):
    """Form to edit an existing question in the document database."""
    submit = SubmitField('Save changes')