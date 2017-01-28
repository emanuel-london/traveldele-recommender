"""Implements the Kooyara API version 1.0."""


__all__ = ['api_v1_0']


from flask import Blueprint


api_v1_0 = Blueprint('api_v1_0', __name__)


from . import endpoints
