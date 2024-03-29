"""Flask application package.

Holds all modules related to the application functionality.
"""


__all_ = ['app', 'assets', 'breadcrumbs', 'sql']


import os


from flask import (
    Flask, g,
)
from flask_assets import (
    Bundle, Environment,
)
from flask_bootstrap import Bootstrap
from flask_breadcrumbs import Breadcrumbs
from flask_jsglue import JSGlue
from flask_login import LoginManager
from flask_mail import Mail
from flask_oauthlib.provider import OAuth2Provider
from flask_pymongo import PyMongo
from flask_sqlalchemy import SQLAlchemy
from pyspark import SparkContext, SparkConf
from werkzeug.contrib.cache import MemcachedCache


import config
from config import AppConfig


app = Flask(__name__)
assets = Environment()
bootstrap = Bootstrap()
breadcrumbs = Breadcrumbs()
cache = MemcachedCache(['127.0.0.1:11211'], default_timeout=60)
jsglue = JSGlue()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
login_manager.login_message = None
mailer = Mail()
mongo = PyMongo()
oauth_provider = OAuth2Provider()
sql = SQLAlchemy()


def create_app(config_name):
    """Create the application object.

    Blueprints, which are analogous to modules/plugins, are used to add
    functionality to the application.

    Parameters
    ----------
    config_name : str
        The environment context of the application.

    Returns
    -------
    app : object
    """

    # Create application configuration object.
    app.config.from_object(AppConfig[config_name])

    # Initialize application.
    AppConfig[config_name].init_app(app)
    assets.init_app(app)
    bootstrap.init_app(app)
    breadcrumbs.init_app(app)
    jsglue.init_app(app)
    login_manager.init_app(app)
    mailer.init_app(app)
    mongo.init_app(app)
    oauth_provider.init_app(app)
    sql.init_app(app)

    # Register Blueprints.
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api_v1_0 import api_v1_0 as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/1.0')

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .confirm import confirm as confirm_blueprint
    app.register_blueprint(confirm_blueprint, url_prefix='/confirm')

    from .dash import dash as dash_blueprint
    app.register_blueprint(dash_blueprint, url_prefix='/dash')

    from .oauth import oauth as oauth_blueprint
    app.register_blueprint(oauth_blueprint, url_prefix='/oauth')

    # Initialize spark.
    with app.app_context():
        if app.config['RS_BACKEND'] == 'mongo':
            from .rs.mongo import MongoRecommenderSystem
            app.rs = MongoRecommenderSystem()
        elif app.config['RS_BACKEND'] == 'spark':
            from .rs.spark import SparkRecommenderSystem
            app.rs = SparkRecommenderSystem(
                SparkContext(conf=SparkConf().setAppName("krs")))
            app.rs.load_data()

    # Register assets
    app_js = Bundle(
        'js/utils.js',
        'js/script.js',
        filters='closure_js',
        output='gen/packed.js'
    )
    assets.register('app_js', app_js)

    krs_js = Bundle(
        'js/oauth.js',
        'js/api.js',
        output='gen/krs.js'
    )
    assets.register('krs_js', krs_js)

    jui_js = Bundle(
        'bower_components/jquery-ui/jquery-ui.min.js',
        output='gen/jui.js'
    )
    assets.register('jui_js', jui_js)

    app_css = Bundle(
        'scss/style.scss',
        filters='pyscss,yui_css',
        output='gen/packed.css'
    )
    assets.register('app_css', app_css)

    jui_css = Bundle(
        'bower_components/jquery-ui/themes/smoothness/jquery-ui.min.css',
        'bower_components/jquery-ui/themes/smoothness/theme.css',
        output='gen/jui.css'
    )
    assets.register('jui_css', jui_css)

    if app.config['DEBUG']:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

    @app.after_request
    def call_after_request_callbacks(response):
        for callback in getattr(g, 'after_request_callbacks', ()):
            callback(response)
        return response

    return app


def get_app_prefix():
    """Return the application prefix."""
    return config.APP_PREFIX
