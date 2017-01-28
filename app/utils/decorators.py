"""Defines decorators used throughout the Flask app."""


from functools import wraps
from threading import Thread


from flask import (
    abort, g, redirect, url_for,
)
from flask_login import current_user


from .models import Permission


def permission_required(permission):
    """Check that the current user has the requisite permissions to access the
    requested URL.
    """
    def decorator(func):
        """Decorator."""
        @wraps(func)
        def decorated_function(*args, **kwargs):
            """Decorated."""
            if not current_user.can(permission):
                abort(403)
            return func(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(func):
    """Check that the administrator role is required for access."""
    return permission_required(Permission.ADMINISTER_SITE)(func)


def confirmed_required(func):
    """Check that the current_user user has confirmed his/her account."""
    @wraps(func)
    def decorator(*args, **kwargs):
        """Decorator."""
        if not current_user.super_user() and not current_user.confirmed:
            return redirect(url_for('auth.unconfirmed'))
        return func(*args, **kwargs)
    return decorator


def async(func):
    """Function should be asynchronous."""
    def decorator(*args, **kwargs):
        """Decorator."""
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
    return decorator


def after_this_request(func):
    """Function to be executed after serving a request."""
    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(func)
    return func