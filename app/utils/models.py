"""Object models used throughout the Flask app."""


from datetime import datetime
import os
import string


from flask import current_app
from flask_login import (
    UserMixin, AnonymousUserMixin,
)
from itsdangerous import (
    BadSignature, URLSafeTimedSerializer,
)
from werkzeug.security import (
    generate_password_hash, check_password_hash,
)


from app import (
    sql, login_manager,
)


class Permission(object):
    """Define user roles which are available in the application."""
    VIEW_CONTENT = 0x01
    CREATE_CONTENT = 0x04
    ADMINISTER_SITE = 0x80


class Role(sql.Model):
    """Database model for a role."""
    __tablename__ = 'roles'

    id = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(sql.String(64), unique=True)
    default = sql.Column(sql.Boolean, default=False, index=True)
    permissions = sql.Column(sql.Integer)
    users = sql.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def insert_roles():
        """Populate the roles table."""
        roles = {
            'administrator': (0xff, False)
        }
        for item in roles:
            role = Role.query.filter_by(name=item).first()
            if role is None:
                role = Role(name=item)
            role.permissions = roles[item][0]
            role.default = roles[item][1]
            sql.session.add(role)
        sql.session.commit()


class User(UserMixin, sql.Model):
    """Database model for a user."""
    __tablename__ = 'users'

    id = sql.Column(sql.Integer, primary_key=True)
    username = sql.Column(sql.String(32), unique=True, index=True)
    email = sql.Column(sql.String(64), unique=True, index=True, nullable=False)
    init = sql.Column(sql.String(64), index=True, nullable=False)
    password_hash = sql.Column(sql.String(128), nullable=False)
    role_id = sql.Column(sql.Integer, sql.ForeignKey('roles.id'),
                         server_default='0', nullable=False)
    registered_on = sql.Column(sql.DateTime, nullable=False)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    def __repr__(self):
        return '<User %r>' % self.username

    @staticmethod
    def insert_admin_user():
        """Create the admin user and insert into the database."""
        admin_user = User.query.filter_by(id=1).first()
        if admin_user is None:
            admin_user = User(username='admin',
                              email=current_app.config['_ADMIN'],
                              init=current_app.config['_ADMIN'],
                              password=current_app.config['_ADMIN_PASSWORD'],
                              registered_on=datetime.now())
            admin_user.role = Role.query.filter_by(permissions=0xff).first()
            sql.session.add(admin_user)
            sql.session.commit()

    @property
    @staticmethod
    def password():
        """Password not exposed."""
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """Generate hash based on password property."""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """Check supplied string against password hash"""
        return check_password_hash(self.password_hash, password)

    def can(self, permissions):
        """Check user permissions."""
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        """Check user is administrator"""
        return self.can(Permission.ADMINISTER_SITE)

    def super_user(self):
        """Check if user is the site super user."""
        return self.id == 1

    def generate_security_token(self):
        """Generate a security token."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(self.email,
                                salt=current_app.config[
                                    'SECURITY_PASSWORD_SALT'
                                ])

    def confirm_security_token(self, token, max_age=3600):
        """Validate a security token."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            self.email = serializer.loads(
                token,
                salt=current_app.config['SECURITY_PASSWORD_SALT'],
                max_age=max_age
            )
        except BadSignature:
            raise
        return self.email

    @staticmethod
    def confirm_password_reset_token(token, max_age=3600):
        """Validate password reset token."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(
                token,
                salt=current_app.config['SECURITY_PASSWORD_SALT'],
                max_age=max_age
            )
        except BadSignature:
            raise
        return email


class AnonymousUser(AnonymousUserMixin):
    """Define object for anonymous users."""
    @staticmethod
    def can(dummy_permissions):
        """Check permissions of anonymous user."""
        return False

    @staticmethod
    def is_administrator():
        """Check anonymous user is administrator."""
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    """Fetch user object from database."""
    return User.query.get(int(user_id))


class Profile(sql.Model):
    """User profiles to test the recommender system."""
    __tablename__ = 'profiles'

    id = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(sql.String(32), index=True)
    pushed = sql.Column(sql.Boolean, default=False)


class OAuth2Client(sql.Model):
    """Data model for an app that wants to use the resources of a user."""
    __tablename__ = 'oauth2_clients'

    # Human readable name, not required.
    name = sql.Column(sql.String(40))

    # Human readable description, not required.
    description = sql.Column(sql.String(400))

    # Creator of the client, not required.
    user_id = sql.Column(sql.ForeignKey('users.id'))
    # Required if you need to support client credential.
    user = sql.relationship('User')

    client_id = sql.Column(sql.String(40), primary_key=True)
    client_secret = sql.Column(
        sql.String(55), unique=True, index=True, nullable=False)

    # Public or Confidential.
    is_confidential = sql.Column(sql.Boolean)

    _redirect_uris = sql.Column(sql.Text)
    _default_scopes = sql.Column(sql.Text)

    grants = sql.relationship('OAuth2Grant', cascade='all, delete-orphan')
    tokens = sql.relationship('OAuth2Token', cascade='all, delete-orphan')

    @property
    def client_type(self):
        if self.is_confidential:
            return 'confidential'
        return public

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []

    @staticmethod
    def generate_client_id():
        chars = string.ascii_letters + string.digits
        return ''.join(chars[ord(os.urandom(1)) % len(chars)] for _ in range(15))

    @staticmethod
    def generate_client_secret():
        chars = string.ascii_letters + string.digits
        return ''.join(chars[ord(os.urandom(1)) % len(chars)] for _ in range(30))


class OAuth2Grant(sql.Model):
    """Data model for a grant token created in the authorization flow."""
    __tablename__ = 'oauth2_grants'

    id = sql.Column(sql.Integer, primary_key=True)

    user_id = sql.Column(
        sql.Integer, sql.ForeignKey('users.id'))
    user = sql.relationship('User')

    client_id = sql.Column(
        sql.String(40), sql.ForeignKey('oauth2_clients.client_id'), nullable=False)
    client = sql.relationship('OAuth2Client')

    code = sql.Column(sql.String(255), index=True, nullable=False)

    redirect_uri = sql.Column(sql.String(255))
    expires = sql.Column(sql.DateTime)

    _scopes = sql.Column(sql.Text)

    def delete(self):
        sql.session.delete(self)
        sql.session.commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


class OAuth2Token(sql.Model):
    """Data model for a bearer token used by a client."""
    __tablename__ = 'oauth2_tokens'

    id = sql.Column(sql.Integer, primary_key=True)

    client_id = sql.Column(
        sql.String(40), sql.ForeignKey('oauth2_clients.client_id'), nullable=False)
    client = sql.relationship('OAuth2Client')

    user_id = sql.Column(
        sql.Integer, sql.ForeignKey('users.id'))
    user = sql.relationship('User')

    # Currently only bearer is supported.
    token_type = sql.Column(sql.String(40))

    access_token = sql.Column(sql.String(255), unique=True)
    refresh_token = sql.Column(sql.String(255), unique=True)
    expires = sql.Column(sql.DateTime)
    _scopes = sql.Column(sql.Text)

    def delete(self):
        sql.session.delete(self)
        sql.session.commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []
