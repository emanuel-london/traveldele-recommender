"""Implements forms used in the confirmation ui."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField, SubmitField,
)


class ConfirmationForm(FlaskForm):
    """Confirm that a user wants to complete a given action."""
    confirmed = BooleanField('Yes')
    submit = SubmitField('Continue')