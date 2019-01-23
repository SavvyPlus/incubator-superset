# pylint: disable=C,R,W
"""Package's main module!"""
import json
import logging
from logging.handlers import TimedRotatingFileHandler
import os

from flask import Flask, redirect, g
from flask_appbuilder import AppBuilder, IndexView, SQLA
from flask_appbuilder.baseviews import expose
from flask_compress import Compress
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from werkzeug.contrib.fixers import ProxyFix

from superset import config
from superset.connectors.connector_registry import ConnectorRegistry
from superset.security import SupersetSecurityManager
from superset.utils.core import (
    get_update_perms_flag, pessimistic_connection_handling, setup_cache)

APP_DIR = os.path.dirname(__file__)
CONFIG_MODULE = os.environ.get('SUPERSET_CONFIG', 'superset.config')

if not os.path.exists(config.DATA_DIR):
    os.makedirs(config.DATA_DIR)

with open(APP_DIR + '/static/assets/backendSync.json', 'r', encoding='utf-8') as f:
    frontend_config = json.load(f)

app = Flask(__name__)
app.config.from_object(CONFIG_MODULE)
conf = app.config

#################################################################
# Handling manifest file logic at app start
#################################################################
MANIFEST_FILE = APP_DIR + '/static/assets/dist/manifest.json'
manifest = {}


def parse_manifest_json():
    global manifest
    try:
        with open(MANIFEST_FILE, 'r') as f:
            # the manifest inclues non-entry files
            # we only need entries in templates
            full_manifest = json.load(f)
            manifest = full_manifest.get('entrypoints', {})
    except Exception:
        print(Exception)
        pass


def get_js_manifest_files(filename):
    if app.debug:
        parse_manifest_json()
    entry_files = manifest.get(filename, {})
    return entry_files.get('js', [])


def get_css_manifest_files(filename):
    if app.debug:
        parse_manifest_json()
    entry_files = manifest.get(filename, {})
    return entry_files.get('css', [])


def get_unloaded_chunks(files, loaded_chunks):
    filtered_files = [f for f in files if f not in loaded_chunks]
    for f in filtered_files:
        loaded_chunks.add(f)
    return filtered_files


parse_manifest_json()


def is_solar_user():
    if not g.user.is_anonymous:
        for role in g.user.roles:
            if 'solar' in role.name:
                return True
    return False


@app.context_processor
def get_manifest():
    return dict(
        loaded_chunks=set(),
        get_unloaded_chunks=get_unloaded_chunks,
        js_manifest=get_js_manifest_files,
        css_manifest=get_css_manifest_files,
        is_solar=is_solar_user()
    )


#################################################################

for bp in conf.get('BLUEPRINTS'):
    try:
        print("Registering blueprint: '{}'".format(bp.name))
        app.register_blueprint(bp)
    except Exception as e:
        print('blueprint registration failed')
        logging.exception(e)

if conf.get('SILENCE_FAB'):
    logging.getLogger('flask_appbuilder').setLevel(logging.ERROR)

if app.debug:
    app.logger.setLevel(logging.DEBUG)  # pylint: disable=no-member
else:
    # In production mode, add log handler to sys.stderr.
    app.logger.addHandler(logging.StreamHandler())  # pylint: disable=no-member
    app.logger.setLevel(logging.INFO)  # pylint: disable=no-member
logging.getLogger('pyhive.presto').setLevel(logging.INFO)

db = SQLA(app)

if conf.get('WTF_CSRF_ENABLED'):
    csrf = CSRFProtect(app)
    csrf_exempt_list = conf.get('WTF_CSRF_EXEMPT_LIST', [])
    for ex in csrf_exempt_list:
        csrf.exempt(ex)

pessimistic_connection_handling(db.engine)

cache = setup_cache(app, conf.get('CACHE_CONFIG'))
tables_cache = setup_cache(app, conf.get('TABLE_NAMES_CACHE_CONFIG'))

migrate = Migrate(app, db, directory=APP_DIR + '/migrations')

# Logging configuration
logging.basicConfig(format=app.config.get('LOG_FORMAT'))
logging.getLogger().setLevel(app.config.get('LOG_LEVEL'))

if app.config.get('ENABLE_TIME_ROTATE'):
    logging.getLogger().setLevel(app.config.get('TIME_ROTATE_LOG_LEVEL'))
    handler = TimedRotatingFileHandler(
        app.config.get('FILENAME'),
        when=app.config.get('ROLLOVER'),
        interval=app.config.get('INTERVAL'),
        backupCount=app.config.get('BACKUP_COUNT'))
    logging.getLogger().addHandler(handler)

if app.config.get('ENABLE_CORS'):
    from flask_cors import CORS
    CORS(app, **app.config.get('CORS_OPTIONS'))

if app.config.get('ENABLE_PROXY_FIX'):
    app.wsgi_app = ProxyFix(app.wsgi_app)

if app.config.get('ENABLE_CHUNK_ENCODING'):

    class ChunkedEncodingFix(object):
        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            # Setting wsgi.input_terminated tells werkzeug.wsgi to ignore
            # content-length and read the stream till the end.
            if environ.get('HTTP_TRANSFER_ENCODING', '').lower() == u'chunked':
                environ['wsgi.input_terminated'] = True
            return self.app(environ, start_response)

    app.wsgi_app = ChunkedEncodingFix(app.wsgi_app)

if app.config.get('UPLOAD_FOLDER'):
    try:
        os.makedirs(app.config.get('UPLOAD_FOLDER'))
    except OSError:
        pass

for middleware in app.config.get('ADDITIONAL_MIDDLEWARE'):
    app.wsgi_app = middleware(app.wsgi_app)


class MyIndexView(IndexView):
    @expose('/')
    def index(self):
        entry_point = 'solar'
        if hasattr(g.user, 'roles'):
            for role in g.user.roles:
                if role.name == 'Admin':
                    entry_point ='superset'
                    break
        else:
            return redirect('/login')

        return redirect(f'/{entry_point}/welcome')



custom_sm = app.config.get('CUSTOM_SECURITY_MANAGER') or SupersetSecurityManager
if not issubclass(custom_sm, SupersetSecurityManager):
    raise Exception(
        """Your CUSTOM_SECURITY_MANAGER must now extend SupersetSecurityManager,
         not FAB's security manager.
         See [4565] in UPDATING.md""")

appbuilder = AppBuilder(
    app,
    db.session,
    base_template='superset/base.html',
    indexview=MyIndexView,
    security_manager_class=custom_sm,
    update_perms=get_update_perms_flag(),
)

security_manager = appbuilder.sm

results_backend = app.config.get('RESULTS_BACKEND')

# Registering sources
module_datasource_map = app.config.get('DEFAULT_MODULE_DS_MAP')
module_datasource_map.update(app.config.get('ADDITIONAL_MODULE_DS_MAP'))
ConnectorRegistry.register_sources(module_datasource_map)

# Flask-Compress
if conf.get('ENABLE_FLASK_COMPRESS'):
    Compress(app)

# Hook that provides administrators a handle on the Flask APP
# after initialization
flask_app_mutator = app.config.get('FLASK_APP_MUTATOR')
if flask_app_mutator:
    flask_app_mutator(app)

from superset import views  # noqa
