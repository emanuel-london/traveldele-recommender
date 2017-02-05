"""Implements forms used in the category section of the dashboard Blueprint ui."""


from flask_wtf import FlaskForm
from wtforms import (
    StringField, SubmitField,
)
from wtforms.validators import Required


class CategoryFormMixin():
    """Base form for category management forms."""
    category = StringField('Name', validators=[Required()])
    weight = StringField("Weight", validators=[Required()])


class NewCategoryForm(FlaskForm, CategoryFormMixin):
    """Form to add a new category to the document database."""
    submit = SubmitField('Add category')


class EditCategoryForm(FlaskForm, CategoryFormMixin):
    """Form to edit an existing category in the document database."""
    submit = SubmitField('Save changes')
