"""Implements forms used in the dashboard Blueprint ui."""


from flask_wtf import FlaskForm
from wtforms import (
    TextAreaField, SubmitField,
)
from wtforms.validators import Required


class StatementFormMixin():
    """Base form for statement management forms."""
    statement = TextAreaField('Statement', validators=[Required()])


class NewStatementForm(FlaskForm, StatementFormMixin):
    """Form to add a new statement to the document database."""
    submit = SubmitField('Add statement')


class EditStatementForm(FlaskForm, StatementFormMixin):
    """Form to edit an existing statement in the document database."""
    submit = SubmitField('Save changes')
