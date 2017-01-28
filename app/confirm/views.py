"""Implements the confirmation ui endpoints."""


from flask import (
    flash, redirect, render_template,
)


from app import cache
from app.confirm import confirm
from app.confirm.forms import ConfirmationForm


@confirm.route('/<string:key>', methods=['GET', 'POST'])
def index(key):
    """Confirm with the user that the requested action is to be performed."""
    message = cache.get('{0}/message'.format(key))
    agreement = cache.get('{0}/agreement'.format(key))
    severity = cache.get('{0}/severity'.format(key))
    backward = cache.get('{0}/previous'.format(key))
    forward = cache.get('{0}/next'.format(key))

    form = ConfirmationForm()

    if form.validate_on_submit():
        if form.confirmed.data:
            cache.set(forward, True)
            return redirect(forward)
        else:
            return redirect(backward)

    form.confirmed.label.text = agreement
    flash(message, severity)
    page_vars = {
        'title': 'Confirm Action',
        'form': form,
        'cancel_path': backward
    }
    return render_template('confirm/index.html', **page_vars)
