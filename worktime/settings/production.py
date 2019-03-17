# PRODUCTION SETTINGS

import os
from worktime.settings.base import *

SECRET_KEY=os.environ.get('DJANGO_SECRET_KEY')

# todo config on heroku
EMAIL_HOST_PASSWORD=os.environ.get("EMAIL_HOST_PASSWORD")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = True

INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)


INTERNAL_IPS = ['127.0.0.1']

# GOOGLE_OAUTH_CLIENT_ID = '172679960487-7um12gthi9rcp40rtqfptm7ai59frm03.apps.googleusercontent.com'
# GOOGLE_OAUTH_CLIENT_SECRET = 'vQdOqG8FIK4nCg8DPM0UAOL7'


# Parse database configuration from $DATABASE_URL
import dj_database_url

# DATABASE_URL = 'postgres://yfgrudrwvxsmzw:bfcfdf239cc077055d636616c5d3e7d3bc71a1b2636c4a4a90ad2cbca080a1d0@ec2-107-20-177-161.compute-1.amazonaws.com:5432/da0c2l3reqocrf'
# 'postgresql:///gentle-wildwood-51939'

DATABASES = {'default' : dj_database_url.config()}

import django_heroku
django_heroku.settings(locals())

