from worktime.settings.base import *

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "worktime.settings.local")

SECRET_KEY = os.environ.get('SECRET_KEY')

EMAIL_HOST_PASSWORD=os.environ.get("EMAIL_HOST_PASSWORD")

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'nwnjhzz6di28p2ce8iwhh0swd5fajjb6fhdtae29imz1nw86u3'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = True

INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

STATIC_URL = '/static/'

INTERNAL_IPS = ['127.0.0.1']

GOOGLE_OAUTH_CLIENT_ID = '172679960487-7um12gthi9rcp40rtqfptm7ai59frm03.apps.googleusercontent.com'
GOOGLE_OAUTH_CLIENT_SECRET = 'vQdOqG8FIK4nCg8DPM0UAOL7'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE' : 'django.db.backends.postgresql_psycopg2',
        'NAME' : 'worktime',
        'USER' : 'mw',
        'PASSWORD' : '30f0fnts',
        'HOST' : 'localhost',
        'PORT' : '',
    }
}
