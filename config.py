"""Application configuration file."""


__all__ = ['AppConfig']


import os


BASEDIR = os.path.abspath(os.path.dirname(__file__))
APP_PREFIX = 'KOOYARA'


class Config(object):
    """Base configuration class."""

    # Maintain reference to the base directory of the code base to be used
    # appliation wide.
    BASEDIR = BASEDIR

    # Path to directory where data files are stored.
    DATA_FILES = os.path.join(BASEDIR, 'data')

    # Application secret key and password salt to be use by cryptographic
    # libraries, sourced from environment variables.
    SECRET_KEY = os.environ.get('{0}_SECRET_KEY'.format(APP_PREFIX))
    SECURITY_PASSWORD_SALT = os.environ.get(
        '{0}_SECURITY_PASSWORD_SALT'.format(APP_PREFIX))

    # Admin user email and password
    _ADMIN = os.environ.get('{0}_ADMIN'.format(APP_PREFIX))
    _ADMIN_PASSWORD = os.environ.get('{0}_ADMIN_PASSWORD'.format(APP_PREFIX))

    # Site name for navbar.
    SITE_NAME = 'Kooyara'

    # Organisation name for copyright notice.
    ORG_NAME = 'Kooyara Inc'

    # Breadcrumbs root node.
    BREADCRUMBS_ROOT = 'bc'

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # OAuth2
    OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 60 * 5

    # Recommender system backend.
    RS_BACKEND = os.environ.get('{0}_RS_BACKEND'.format(APP_PREFIX)) or 'mongo'

    @staticmethod
    def init_app(app):
        """Configuration specific initialization."""
        pass


class DevelopmentConfig(Config):
    """Configuration class specific to the development environment."""

    # Set log level.
    LOG_LEVEL = 10

    # Enable debugging in the dev environment.
    # Note: this will output errors to the browser.
    DEBUG = True

    # SQL database for user management.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        '{0}_DEV_DATABASE_URL'.format(APP_PREFIX)) or \
        'sqlite:///{0}'.format(
            os.path.join(BASEDIR, 'storage', APP_PREFIX + '-dev.sqlite'))

    # MongoDB Document Store
    MONGO_URI = os.environ.get('{0}_MONGO_DEV_URI'.format(APP_PREFIX) or
                               'mongodb://localhost/kooyara-dev')


class TestingConfig(Config):
    """Configuration class specific to the testing environment."""

    # Set log level.
    LOG_LEVEL = 20

    # Set flag to indicate that it is a testing environment.
    TESTING = True

    # SQL database for user management.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        '{0}_TEST_DATABASE_URL'.format(APP_PREFIX)) or \
        'sqlite:///{0}'.format(
            os.path.join(BASEDIR, 'storage', APP_PREFIX + '-test.sqlite'))

    # MongoDB Document Store
    MONGO_URI = os.environ.get('{0}_MONGO_TEST_URI'.format(APP_PREFIX) or
                               'mongodb://localhost/kooyara-test')


class ProductionConfig(Config):
    """Configuration class specific to the production environment."""

    # Set log level.
    LOG_LEVEL = 30

    # SQL database for user management.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        '{0}_DATABASE_URL'.format(APP_PREFIX)) or \
        'sqlite:///{0}'.format(
            os.path.join(BASEDIR, 'storage', APP_PREFIX + '.sqlite'))

    # MongoDB Document Store
    MONGO_URI = os.environ.get('{0}_MONGO_URI'.format(APP_PREFIX) or
                               'mongodb://localhost/kooyara')


AppConfig = {
    'default': DevelopmentConfig,
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}
