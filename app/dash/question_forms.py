"""Implements forms used in the dashboard Blueprint ui."""


from flask_wtf import FlaskForm
from wtforms import (
    TextAreaField, SubmitField,
)
from wtforms.validators import Required


class QuestionFormMixin():
    """Base form for question management forms."""
    question = TextAreaField('Question', validators=[Required()])
    options = TextAreaField('Options', validators=[Required()])


class NewQuestionForm(FlaskForm, QuestionFormMixin):
    """Form to add a new question to the document database."""
    submit = SubmitField('Add question')


class EditQuestionForm(FlaskForm, QuestionFormMixin):
    """Form to edit an existing question in the document database."""
    submit = SubmitField('Save changes')
