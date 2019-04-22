# PRODUCTION SETTINGS

import os
from worktime.settings.base import *

SECRET_KEY=os.environ.get('DJANGO_SECRET_KEY')

# # todo config on heroku
# EMAIL_HOST_PASSWORD=os.environ.get("EMAIL_HOST_PASSWORD")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEMPLATE_DEBUG = False

INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join("static"),
    # '/var/www/static/',
]


# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)


INTERNAL_IPS = ['127.0.0.1']

# GOOGLE_OAUTH_CLIENT_ID = '172679960487-7um12gthi9rcp40rtqfptm7ai59frm03.apps.googleusercontent.com'
# GOOGLE_OAUTH_CLIENT_SECRET = 'vQdOqG8FIK4nCg8DPM0UAOL7'


# Parse database configuration from $DATABASE_URL
import dj_database_url

DATABASES = {'default' : dj_database_url.config()}

import django_heroku
django_heroku.settings(locals())

SECURE_SSL_REDIRECT = True
