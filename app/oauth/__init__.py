"""Implements the OAuth2 authorization flow."""


__all__ = ['oauth']


from flask import Blueprint


oauth = Blueprint('oauth', __name__)


from . import (
    forms, views,
)


from datetime import (
    datetime, timedelta,
)

from flask_login import current_user

from app import oauth_provider as op, sql
from app.utils.models import (
    OAuth2Client, OAuth2Grant, OAuth2Token,
    User,
)


@op.clientgetter
def load_client(client_id):
    return OAuth2Client.query.filter_by(client_id=client_id).first()


@op.grantgetter
def load_grant(client_id, code):
    return OAuth2Grant.query.filter_by(client_id=client_id, code=code).first()


@op.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    expires = datetime.utcnow() + timedelta(seconds=60)
    grant = OAuth2Grant(
        client_id=client_id,
        code=code['code'],
        redirect_uri=request.redirect_uri,
        _scopes=' '.join(request.scopes),
        user=current_user,
        expires=expires
    )
    sql.session.add(grant)
    sql.session.commit()
    return grant


@op.tokengetter
def load_token(access_token=None, refresh_token=None):
    if access_token:
        return OAuth2Token.query.filter_by(access_token=access_token).first()
    elif refresh_token:
        return OAuth2Token.query.filter_by(refresh_token=refresh_token).first()


@op.tokensetter
def save_token(token, request, *args, **kwargs):
    toks = OAuth2Token.query.filter_by(
        client_id=request.client.client_id, user_id=request.user.id)

    # Make sure that every client has only one token connected to a user
    for t in toks:
        sql.session.delete(t)

    expires_in = token.get('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)

    tok = OAuth2Token(
        access_token=token['access_token'],
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user_id=request.user.id
    )

    if request.body.get('grant_type') != 'client_credentials':
        tok.refresh_token = token['refresh_token']

    sql.session.add(tok)
    sql.session.commit()
    return tok


@op.usergetter
def get_user(username, password, *args, **kwargs):
    user = User.query.filter_by(username=username).first()
    if user.verify_password(password):
        return user
    return None
