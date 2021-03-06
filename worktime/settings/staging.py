# STAGING SETTINGS

import os
from worktime.settings.base import *

SECRET_KEY=os.environ.get('DJANGO_SECRET_KEY')

# # todo config on heroku
# EMAIL_HOST_PASSWORD=os.environ.get("EMAIL_HOST_PASSWORD")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = True

INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# the directory where collectstatic will put static files in production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)




# INTERNAL_IPS = ['127.0.0.1']

# GOOGLE_OAUTH_CLIENT_ID = '172679960487-7um12gthi9rcp40rtqfptm7ai59frm03.apps.googleusercontent.com'
# GOOGLE_OAUTH_CLIENT_SECRET = 'vQdOqG8FIK4nCg8DPM0UAOL7'


# Parse database configuration from $DATABASE_URL
import dj_database_url

DATABASES = {'default' : dj_database_url.config()}

import django_heroku
django_heroku.settings(locals())

SECURE_SSL_REDIRECT = True
PREPEND_WWW = False
