"""Implements the action confirmation ui."""


__all__ = ['confirm', 'confirm_required']


from functools import wraps
import os
import string

from flask import (
    Blueprint, g, redirect, request,
    url_for,
)


confirm = Blueprint('confirm', __name__)


from . import (
    forms, views,
)


from app import cache


def confirm_required(message, agreement, back, back_args=None, severity='warning'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            chars = string.ascii_letters + string.digits + '+-'
            key = ''.join(chars[ord(os.urandom(1)) % len(chars)]
                          for _ in range(15))

            previous = None
            if back_args is not None:
                bargs = {}
                for k, val in kwargs.items():
                    if k in back_args:
                        bargs[k] = val
                previous = url_for(back, **bargs)
            else:
                previous = url_for(back)

            confirmed = cache.get(request.path)
            if confirmed is None:
                cache.set('{0}/message'.format(key), message)
                cache.set('{0}/agreement'.format(key), agreement)
                cache.set('{0}/severity'.format(key), severity)
                cache.set('{0}/previous'.format(key), previous)
                cache.set('{0}/next'.format(key), request.path)
                return redirect(url_for('confirm.index', key=key))
            cache.delete(request.path)
            return f(*args, **kwargs)

        return decorated_function

    return decorator
