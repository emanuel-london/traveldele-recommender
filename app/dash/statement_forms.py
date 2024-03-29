"""Implements forms used in the dashboard Blueprint ui."""


from flask_wtf import FlaskForm
from wtforms import (
    SelectField, StringField, SubmitField, TextAreaField,
)
from wtforms.validators import Required


class StatementFormMixin():
    """Base form for statement management forms."""
    statement = TextAreaField('Statement', validators=[Required()])
    category = SelectField('Category')
    tags = StringField('Tags')


class NewStatementForm(FlaskForm, StatementFormMixin):
    """Form to add a new statement to the document database."""
    submit = SubmitField('Add statement')


class EditStatementForm(FlaskForm, StatementFormMixin):
    """Form to edit an existing statement in the document database."""
    submit = SubmitField('Save changes')
