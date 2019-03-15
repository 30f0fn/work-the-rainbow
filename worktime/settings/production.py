import os
from worktime.settings.base import *

SECRET_KEY=os.environ.get('SECRET_KEY')

# Parse database configuration from $DATABASE_URL
import dj_database_url

# DATABASE_URL = 'postgres://yfgrudrwvxsmzw:bfcfdf239cc077055d636616c5d3e7d3bc71a1b2636c4a4a90ad2cbca080a1d0@ec2-107-20-177-161.compute-1.amazonaws.com:5432/da0c2l3reqocrf'
# 'postgresql:///gentle-wildwood-51939'

DATABASES = {'default' : dj_database_url.config()}

import django_heroku
django_heroku.settings(locals())

