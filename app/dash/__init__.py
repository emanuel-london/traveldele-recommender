"""Implements the dashboard ui."""


__all__ = ['dash']


from flask import Blueprint


dash = Blueprint('dash', __name__)


from . import (
    forms, views,
    question_forms, question_views,
    profile_forms, profile_views,
)
