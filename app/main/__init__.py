"""Implements the main ui."""


__all__ = ['main']


from flask import Blueprint


main = Blueprint('main', __name__)


from . import (
    errors, views,
)
