upon pushing to heroku, do...

heroku run python manage.py migrate

heroku run python manage.py shell
for u in User.objects.all():
    for r in Role.objects.all():
        if r.accepts(u):
            u.role_set.add(r)
