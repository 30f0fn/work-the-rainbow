import os
from worktime.settings.base import *

SECRET_KEY=os.environ.get('SECRET_KEY')

# Parse database configuration from $DATABASE_URL
import dj_database_url

DATABASE_URL = 'postgresql:///worktime'

DATABASES = {'default' : dj_database_url.config()}

import django_heroku
django_heroku.settings(locals())

