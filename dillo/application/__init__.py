import redis
import bugsnag
import tweepy
from flask import Flask
from flask import session
from flask import Blueprint

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.cache import Cache
from flask_mail import Mail
from flask_oauthlib.client import OAuth
from imgurpython import ImgurClient
from flask_wtf.csrf import CsrfProtect
from bugsnag.flask import handle_exceptions
from flask_debugtoolbar import DebugToolbarExtension
from micawber.providers import bootstrap_basic
from micawber.providers import Provider

import config

app = Flask(__name__,
    template_folder='templates',
    static_folder='static')

app.config.from_object(config.Deployment)

db = SQLAlchemy(app)
mail = Mail(app)
oauth = OAuth(app)
CsrfProtect(app)
cache = Cache(app)
toolbar = DebugToolbarExtension(app)

registry = bootstrap_basic()
registry.register('http://monitor.eibriel.com/\S*',
    Provider('http://monitor.eibriel.com/api/job/oembed'))
registry.register('https?://sketchfab.com/models/*',
    Provider('https://sketchfab.com/oembed'))
registry.register('https?://p3d.in/*',
    Provider('https://p3d.in/oembed'))
registry.register('https?://vine.co/v/*',
    Provider('https://vine.co/oembed.json'))
registry.register('https?://instagram.com/p/*',
    Provider('http://api.instagram.com/oembed'))

redis_client = redis.StrictRedis(
    host=app.config['CACHE_REDIS_HOST'],
    port=app.config['CACHE_REDIS_PORT'])

bugsnag.configure(
  api_key = app.config['BUGSNAG_KEY'],
  project_root = app.config['BUGSNAG_APP_PATH']
)
handle_exceptions(app)

# auth = tweepy.OAuthHandler(
#     app.config.get('SOCIAL_TWITTER')['app_id'],
#     app.config.get('SOCIAL_TWITTER')['app_secret'])
# auth.set_access_token(
#     app.config.get('SOCIAL_TWITTER')['access_token'],
#     app.config.get('SOCIAL_TWITTER')['access_token_secret'])
# twitter_api = tweepy.API(auth)

# Config at https://console.developers.google.com/
google = oauth.remote_app(
    'google',
    consumer_key=app.config.get('SOCIAL_GOOGLE')['consumer_key'],
    consumer_secret=app.config.get('SOCIAL_GOOGLE')['consumer_secret'],
    request_token_params={
        'scope': 'https://www.googleapis.com/auth/userinfo.email'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

facebook = oauth.remote_app(
    'facebook',
    consumer_key=app.config.get('SOCIAL_FACEBOOK')['app_id'],
    consumer_secret=app.config.get('SOCIAL_FACEBOOK')['app_secret'],
    request_token_params={'scope': 'email'},
    base_url='https://graph.facebook.com',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth'
)


blender_id = oauth.remote_app(
    'blender_id',
    consumer_key=app.config.get('SOCIAL_BLENDER_ID')['app_id'],
    consumer_secret=app.config.get('SOCIAL_BLENDER_ID')['app_secret'],
    request_token_params={'scope': 'email'},
    base_url=app.config['BLENDER_ID_BASE_URL'],
    request_token_url=None,
    access_token_url=app.config['BLENDER_ID_BASE_ACCESS_TOKEN_URL'],
    authorize_url=app.config['BLENDER_ID_AUTHORIZE_URL']
)

imgur_client = ImgurClient(app.config['IMGUR_CLIENT_ID'], app.config['IMGUR_CLIENT_SECRET'])

from modules.admin import backend
from modules.pages import admin
from modules.users import admin, users
from modules.main import *
from modules.posts import posts
from modules.posts import admin
from modules.settings import settings
from modules.comments import comments
from modules.notifications import notifications


filemanager = Blueprint('filemanager', __name__, static_folder='static/files')
app.register_blueprint(filemanager)
app.register_blueprint(settings, url_prefix='/settings')
app.register_blueprint(posts)
app.register_blueprint(users, url_prefix='/u')
app.register_blueprint(comments, url_prefix='/comments')
app.register_blueprint(notifications, url_prefix='/notifications')

from modules.users.model import user_datastore

@app.context_processor
def inject_submit_post_form():
    from application.modules.posts.model import Category
    from application.modules.posts.forms import PostForm
    from application.modules.posts.model import PostType
    form = PostForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    form.post_type_id.choices = [(t.id, t.name) for t in PostType.query.all()]
    #form.post_type_id.data = 1
    return {'submit_post_form': form}

@app.context_processor
#@cache.cached(timeout=3600)
def inject_settings():
    """Global application settings"""
    from modules.admin.model import Setting
    alt = Setting.query.filter_by(name='logo_alt').first()
    image = Setting.query.filter_by(name='logo_image').first()
    settings = {}
    logo = dict(
        alt=alt.value,
        image=url_for('static', filename='images/' + image.value))
    settings['logo'] = logo
    return {'settings': settings}

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404