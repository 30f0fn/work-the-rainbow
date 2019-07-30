upon pushing to heroku, do

heroku run python manage.py migrate

heroku run python manage.py shell
from people.models import *
Role.update_all_membership()
