import os
from base import *

SECRET_KEY=os.environ.get('SECRET_KEY')


import django_heroku
django_heroku.settings(locals())
