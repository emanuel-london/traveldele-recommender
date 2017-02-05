"""Implements the dashboard ui."""


__all__ = ['dash']


from flask import Blueprint


dash = Blueprint('dash', __name__)


from . import (
    forms, views,
    category_forms, category_views,
    profile_forms, profile_views,
    statement_forms, statement_views,
)
