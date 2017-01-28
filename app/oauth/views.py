"""Implements OAuth2 authroization flow endpoints."""


from flask import (
    flash, redirect, render_template, request,
    url_for,
)
from flask_breadcrumbs import register_breadcrumb
from flask_login import (
    current_user, login_required,
)

from app import (
    oauth_provider as op, sql,
)
from app.confirm import confirm_required
from app.oauth import oauth
from app.oauth.forms import (
    NewClientForm, EditClientForm,
)
from app.utils.decorators import admin_required
from app.utils.models import OAuth2Client


@oauth.route('/authorize', methods=['GET', 'POST'])
@login_required
@op.authorize_handler
def authorize(*args, **kwargs):
    if request.method == 'GET':
        client_id = kwargs.get('client_id')
        client = OAuth2Client.query.filter_by(client_id=client_id).first()
        kwargs['client'] = client

        flash('Grant authorization to client "{0}"?'.format(
            client.name), 'warning')
        return render_template('oauth/authorize.html', **kwargs)

    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'


@oauth.route('/token', methods=['POST'])
@op.token_handler
def access_token():
    return None


@oauth.route('/revoke', methods=['POST'])
@op.revoke_handler
def revoke_token():
    pass


@oauth.route('/errors')
def error():
    page_vars = {
        'title': 'OAuth2 Error',
        'page_header': 'OAuth2 Error',
        'error': request.args['error'],
        'error_description': request.args['error_description']
    }
    return render_template('oauth/error.html', **page_vars)


@oauth.route('/clients')
@admin_required
@register_breadcrumb(oauth, 'bc.dash.oauthclients', 'OAuth2 Clients')
def clients():
    """Show list of authorized clients."""

    clients = OAuth2Client.query.all()

    page_vars = {
        'title': 'OAuth2 Clients',
        'navwell': True,
        'page_header': 'OAuth2 Clients',
        'clients': clients
    }
    return render_template('oauth/clients.html', **page_vars)


@oauth.route('/clients/new', methods=['GET', 'POST'])
@admin_required
@register_breadcrumb(oauth, 'bc.dash.oauthclients.new', 'New Client')
def new_client():
    """Render a form allowing the user to add an OAuth2 client."""

    form = NewClientForm()

    if form.validate_on_submit():
        client = OAuth2Client(
            name=form.name.data,
            description=form.description.data,
            user_id=current_user.id,
            client_id=OAuth2Client.generate_client_id(),
            client_secret=OAuth2Client.generate_client_secret(),
            is_confidential=form.confidential.data,
            _redirect_uris=form.redirect.data,
            _default_scopes=form.scopes.data
        )

        sql.session.add(client)
        sql.session.commit()

        flash('Client successfully added.', 'success')
        return redirect(url_for('oauth.client', cid=client.client_id))

    page_vars = {
        'title': 'New Client',
        'navwell': True,
        'page_header': 'New Client',
        'form': form
    }
    return render_template('oauth/new-client.html', **page_vars)


@oauth.route('/clients/<string:cid>/edit', methods=['GET', 'POST'])
@admin_required
@register_breadcrumb(oauth, 'bc.dash.oauthclients.edit', 'Edit Client')
def client(cid):
    """Render a form to edit an existing client."""
    client = OAuth2Client.query.filter_by(client_id=cid).first()
    form = EditClientForm()

    if form.validate_on_submit():
        client.name = form.name.data
        client.description = form.description.data
        client._redirect_uris = form.redirect.data
        client._default_scopes = form.scopes.data
        client.is_confidential = form.confidential.data

        sql.session.add(client)
        sql.session.commit()

        flash('Changes saved.', 'success')
        return redirect(url_for('oauth.client', cid=cid))

    form.name.data = client.name
    form.description.data = client.description
    form.redirect.data = client._redirect_uris
    form.scopes.data = client._default_scopes
    form.confidential.data = client.is_confidential

    page_vars = {
        'title': 'Edit Client',
        'navwell': True,
        'page_header': 'Edit Client',
        'form': form,
        'cid': cid
    }
    return render_template('oauth/edit-client.html', **page_vars)


@oauth.route('/clients/<string:cid>/delete')
@admin_required
@confirm_required(
    'Are you sure you want to delete this client?',
    'I am sure', 'oauth.client', ['cid'], 'danger'
)
def delete_client(cid):
    """Remove a client from the database."""
    client = OAuth2Client.query.filter_by(client_id=cid).first()
    sql.session.delete(client)
    sql.session.commit()

    flash('Client successfully deleted.', 'success')
    return redirect(url_for('oauth.clients'))


@oauth.route('/clients/<string:cid>/reset-secret')
@admin_required
@confirm_required(
    'Are you sure you want to reset the secret key for this client?',
    'I am sure', 'oauth.client', ['cid'], 'danger'
)
def reset_client_secret(cid):
    """Reset a client's secret key."""
    client = OAuth2Client.query.filter_by(client_id=cid).first()

    client.client_secret = OAuth2Client.generate_client_secret()

    sql.session.add(client)
    sql.session.commit()

    flash('Client secret successfully reset.', 'success')
    return redirect(url_for('oauth.client', cid=cid))


@oauth.route('/clients/<string:cid>/purge-grants')
@admin_required
@confirm_required(
    'Are you sure you want to purge grants for this client?',
    'I am sure', 'oauth.client', ['cid'], 'danger'
)
def purge_client_grants(cid):
    """Purge grants for a given client."""
    client = OAuth2Client.query.filter_by(client_id=cid).first()

    print(client.grants)

    for grant in client.grants:
        grant.delete()

    flash('Grants successfully purged.', 'success')
    return redirect(url_for('oauth.client', cid=cid))


@oauth.route('/clients/<string:cid>/purge-tokens')
@admin_required
@confirm_required(
    'Are you sure you want to purge tokens for this client?',
    'I am sure', 'oauth.client', ['cid'], 'danger'
)
def purge_client_tokens(cid):
    """Purge tokens for a given client."""
    client = OAuth2Client.query.filter_by(client_id=cid).first()

    for token in client.tokens:
        token.delete()

    flash('Tokens successfully purged.', 'success')
    return redirect(url_for('oauth.client', cid=cid))
