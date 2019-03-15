import os
from worktime.settings.base import *

SECRET_KEY=os.environ.get('SECRET_KEY')


import django_heroku
django_heroku.settings(locals())

# DATABASES = {
#     'default': {
#         'ENGINE' : 'django.db.backends.postgresql_psycopg2',
#         'NAME' : 'worktime',
#         'USER' : 'mw',
#         'PASSWORD' : '30f0fnts',
#         'HOST' : 'localhost',
#         'PORT' : '',
#     }
# }
